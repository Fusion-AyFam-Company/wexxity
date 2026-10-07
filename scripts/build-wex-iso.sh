#!/usr/bin/env bash
# ==============================================================================
# Wex OS - Bootable Hybrid ISO Generator (Debian 13 Trixie Base)
# Builds a bootable UEFI + BIOS ISO for Wex OS on top of Debian 13
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Use native ext4 in WSL for build directory to ensure full Linux filesystem semantics and speed
WORK_DIR="/var/tmp/wex-build"
CHROOT_DIR="${WORK_DIR}/chroot"
IMAGE_DIR="${WORK_DIR}/image"
OUT_DIR="${ROOT_DIR}/out"

CODENAME="trixie"
MIRROR="http://deb.debian.org/debian/"
KEYRING="/usr/share/keyrings/debian-archive-keyring.gpg"
ISO_NAME="wex-os-debian13-amd64-secureboot.iso"

echo "======================================================="
echo " Building Wex Linux 1.0 (Debian 13 Trixie Base)"
echo " Work Directory: ${WORK_DIR}"
echo " Output ISO:     ${OUT_DIR}/${ISO_NAME}"
echo "======================================================="

# Ensure root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root." >&2
    exit 1
fi

# Ensure output directory exists
mkdir -p "${OUT_DIR}"
mkdir -p "${WORK_DIR}"

# 1. Debootstrap Debian Base System if not already present
if [ ! -d "${CHROOT_DIR}/bin" ]; then
    echo "===> [1/7] Running debootstrap for Debian 13 (${CODENAME})..."
    rm -rf "${CHROOT_DIR}"
    mkdir -p "${CHROOT_DIR}"
    debootstrap \
        --arch=amd64 \
        --keyring="${KEYRING}" \
        --include=apt-transport-https,ca-certificates,gnupg \
        "${CODENAME}" \
        "${CHROOT_DIR}" \
        "${MIRROR}"
else
    echo "===> [1/7] Base Debian chroot already exists. Reusing existing debootstrap."
fi

# 2. Copy Provisioning Files into Chroot
echo "===> [2/7] Injecting Wex components into chroot..."
mkdir -p "${CHROOT_DIR}/tmp"
cp "${ROOT_DIR}/src/wex-setup/wex_setup.py" "${CHROOT_DIR}/tmp/wex_setup.py"
cp "${ROOT_DIR}/src/wex-setup/wex-setup.service" "${CHROOT_DIR}/tmp/wex-setup.service"
cp "${ROOT_DIR}/config/os-release" "${CHROOT_DIR}/tmp/os-release"
cp "${ROOT_DIR}/config/issue" "${CHROOT_DIR}/tmp/issue"
cp "${ROOT_DIR}/config/issue.net" "${CHROOT_DIR}/tmp/issue.net"
cp "${SCRIPT_DIR}/setup-wex-chroot.sh" "${CHROOT_DIR}/tmp/setup-wex-chroot.sh"
chmod +x "${CHROOT_DIR}/tmp/setup-wex-chroot.sh"

# 3. Mount pseudo-filesystems and provision Debian chroot if not already provisioned
if [ ! -f "${CHROOT_DIR}/etc/debian_version" ]; then
    echo "===> [3/7] Provisioning Wex packages, kernel, live-boot & services..."
    cleanup_mounts() {
        umount "${CHROOT_DIR}/sys" 2>/dev/null || true
        umount "${CHROOT_DIR}/proc" 2>/dev/null || true
        umount "${CHROOT_DIR}/dev/pts" 2>/dev/null || true
        umount "${CHROOT_DIR}/run" 2>/dev/null || true
        umount "${CHROOT_DIR}/dev" 2>/dev/null || true
    }
    trap cleanup_mounts EXIT

    mount --bind /dev "${CHROOT_DIR}/dev"
    mount --bind /run "${CHROOT_DIR}/run"
    mount -t devpts devpts "${CHROOT_DIR}/dev/pts"
    mount -t proc proc "${CHROOT_DIR}/proc"
    mount -t sysfs sysfs "${CHROOT_DIR}/sys"

    chroot "${CHROOT_DIR}" /tmp/setup-wex-chroot.sh

    cleanup_mounts
    trap - EXIT
else
    echo "===> [3/7] Debian chroot already provisioned. Reusing existing packages."
fi

# 4. Prepare Live Image Directory Structure
echo "===> [4/7] Preparing ISO image directories..."
mkdir -p "${IMAGE_DIR}/live"
mkdir -p "${IMAGE_DIR}/boot/grub"
mkdir -p "${IMAGE_DIR}/EFI/BOOT"
mkdir -p "${IMAGE_DIR}/isolinux"

# Extract Kernel and Initramfs for Live Boot
VMLINUZ="$(ls -1 "${CHROOT_DIR}/boot"/vmlinuz* | sort -V | tail -n 1)"
INITRD="$(ls -1 "${CHROOT_DIR}/boot"/initrd.img* | sort -V | tail -n 1)"

echo "Found Kernel:  ${VMLINUZ}"
echo "Found Initrd:  ${INITRD}"
cp "${VMLINUZ}" "${IMAGE_DIR}/live/vmlinuz"
cp "${INITRD}" "${IMAGE_DIR}/live/initrd.img"

# 5. Compress Root Filesystem into SquashFS if not already created
if [ ! -f "${IMAGE_DIR}/live/filesystem.squashfs" ]; then
    echo "===> [5/7] Generating SquashFS filesystem..."
    mksquashfs "${CHROOT_DIR}" "${IMAGE_DIR}/live/filesystem.squashfs" \
        -comp xz \
        -e "${CHROOT_DIR}/boot" \
        -e "${CHROOT_DIR}/tmp/*" \
        -e "${CHROOT_DIR}/root/*" \
        -noappend
else
    echo "===> [5/7] Reusing existing SquashFS filesystem."
fi

# 6. Configure Bootloaders (BIOS & UEFI)
echo "===> [6/7] Configuring BIOS & UEFI bootloaders..."

# A. BIOS Bootloader (ISOLINUX)
cp /usr/lib/ISOLINUX/isolinux.bin "${IMAGE_DIR}/isolinux/"
cp /usr/lib/syslinux/modules/bios/ldlinux.c32 "${IMAGE_DIR}/isolinux/" 2>/dev/null || true
for f in libcom32.c32 libutil.c32 vesamenu.c32 menu.c32; do
    if [ -f "/usr/lib/syslinux/modules/bios/$f" ]; then
        cp "/usr/lib/syslinux/modules/bios/$f" "${IMAGE_DIR}/isolinux/"
    fi
done

cat << 'EOF' > "${IMAGE_DIR}/isolinux/isolinux.cfg"
UI vesamenu.c32
PROMPT 0
TIMEOUT 50
MENU TITLE Wex OS 1.0 (Genesis) - Debian 13 Base

LABEL wex
  MENU LABEL Boot Wex OS 1.0 (First Boot Setup)
  KERNEL /live/vmlinuz
  APPEND initrd=/live/initrd.img boot=live components quiet splash console=tty1

LABEL wex-safe
  MENU LABEL Boot Wex OS 1.0 (Safe Graphics)
  KERNEL /live/vmlinuz
  APPEND initrd=/live/initrd.img boot=live components nomodeset quiet splash console=tty1
EOF

# B. UEFI Bootloader (GRUB)
# Use 'search --label' so GRUB locates the ISO volume regardless of device numbering.
# Without this, GRUB tries /live/vmlinuz on the EFI partition (efi.img) and fails
# with "attempt to read or write outside of disk 'cd0'".
cat << 'EOF' > "${IMAGE_DIR}/boot/grub/grub.cfg"
insmod part_gpt
insmod part_msdos
insmod iso9660
insmod all_video
insmod search_label
insmod search

set default=0
set timeout=5

set color_normal=light-gray/black
set color_highlight=cyan/black

# Locate the ISO by its volume label so ($root) points to the ISO filesystem
search --no-floppy --label --set=root WEX_OS

menuentry "Boot Wex OS 1.0 (First Boot Setup)" {
    search --no-floppy --label --set=root WEX_OS
    linux ($root)/live/vmlinuz boot=live components quiet splash console=tty1
    initrd ($root)/live/initrd.img
}

menuentry "Boot Wex OS 1.0 (Safe Graphics)" {
    search --no-floppy --label --set=root WEX_OS
    linux ($root)/live/vmlinuz boot=live components nomodeset quiet splash console=tty1
    initrd ($root)/live/initrd.img
}
EOF

# Copy GRUB config to EFI directory as well
mkdir -p "${IMAGE_DIR}/EFI/BOOT"
cp "${IMAGE_DIR}/boot/grub/grub.cfg" "${IMAGE_DIR}/EFI/BOOT/grub.cfg"

# Install signed Shim and GRUB if available (for UEFI Secure Boot), else fallback to grub-mkstandalone
if [ -f "/usr/lib/shim/shimx64.efi.signed" ] && [ -f "/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed" ]; then
    echo "===> Installing Microsoft-signed Shim and GRUB for UEFI Secure Boot..."
    cp "/usr/lib/shim/shimx64.efi.signed" "${IMAGE_DIR}/EFI/BOOT/BOOTX64.EFI"
    cp "/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed" "${IMAGE_DIR}/EFI/BOOT/grubx64.efi"
else
    echo "===> Building standalone GRUB EFI binary..."
    grub-mkstandalone \
        --format=x86_64-efi \
        --output="${IMAGE_DIR}/EFI/BOOT/BOOTX64.EFI" \
        --locales="" \
        --fonts="" \
        "boot/grub/grub.cfg=${IMAGE_DIR}/boot/grub/grub.cfg"
fi

# Create FAT EFI boot image
truncate -s 10M "${IMAGE_DIR}/boot/grub/efi.img"
mkfs.vfat "${IMAGE_DIR}/boot/grub/efi.img"
mmd -i "${IMAGE_DIR}/boot/grub/efi.img" ::/EFI ::/EFI/BOOT
mcopy -i "${IMAGE_DIR}/boot/grub/efi.img" "${IMAGE_DIR}/EFI/BOOT/"* ::/EFI/BOOT/

# 7. Generate Bootable Hybrid ISO with xorriso
echo "===> [7/7] Generating hybrid UEFI + BIOS ISO image..."
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "WEX_OS" \
    -eltorito-boot isolinux/isolinux.bin \
    -eltorito-catalog isolinux/boot.cat \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -eltorito-alt-boot \
    -e boot/grub/efi.img \
    -no-emul-boot \
    -isohybrid-gpt-basdat \
    -output "${OUT_DIR}/${ISO_NAME}" \
    "${IMAGE_DIR}"

echo "======================================================="
echo " SUCCESS! Wex OS ISO built successfully:"
echo " Path: ${OUT_DIR}/${ISO_NAME}"
ls -lh "${OUT_DIR}/${ISO_NAME}"
echo "======================================================="
