#!/usr/bin/env bash
# ==============================================================================
# Wex OS - Debian 13 (Trixie) Chroot Provisioning Script
# Configures the base Wex system inside Debian 13 (Trixie) chroot environment
# ==============================================================================

set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C

echo "===> [Wex OS] Configuring Debian 13 (Trixie) base inside chroot..."

# 1. Configure Debian 13 APT sources
cat << 'EOF' > /etc/apt/sources.list
deb http://deb.debian.org/debian/ trixie main contrib non-free non-free-firmware
deb http://deb.debian.org/debian/ trixie-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware
EOF

# 2. Update and install kernel, live-boot, and essential system packages
apt-get update
apt-get install -y --no-install-recommends \
    systemd-sysv \
    udev \
    dbus \
    linux-image-amd64 \
    live-boot \
    grub-pc-bin \
    grub-efi-amd64-bin \
    network-manager \
    wpasupplicant \
    wireless-tools \
    iproute2 \
    sudo \
    curl \
    wget \
    python3 \
    locales \
    tzdata \
    ca-certificates \
    apt-transport-https \
    pciutils \
    usbutils

# 3. Setup Locales
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
locale-gen
update-locale LANG=en_US.UTF-8

# 4. Setup Hostname & Hosts
echo "wex" > /etc/hostname
cat << 'EOF' > /etc/hosts
127.0.0.1   localhost
127.0.1.1   wex

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

# 5. Configure NetworkManager to manage all devices
mkdir -p /etc/NetworkManager/conf.d
cat << 'EOF' > /etc/NetworkManager/conf.d/10-globally-managed-devices.conf
[keyfile]
unmanaged-devices=none
EOF

systemctl enable NetworkManager

# 6. Install Wex First-Boot Setup Wizard
install -m 755 /tmp/wex_setup.py /usr/local/bin/wex-setup
install -m 644 /tmp/wex-setup.service /etc/systemd/system/wex-setup.service
systemctl enable wex-setup.service

# 7. Apply Wex Branding
install -m 644 /tmp/os-release /etc/os-release
install -m 644 /tmp/issue /etc/issue
install -m 644 /tmp/issue.net /etc/issue.net
echo "13 (Wex 1.0 Genesis)" > /etc/debian_version

# 8. Update Initramfs with live-boot hooks
update-initramfs -u -k all

# 9. Clean up APT cache to keep image compact
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

echo "===> [Wex OS] Debian 13 (Trixie) chroot configuration completed successfully!"
