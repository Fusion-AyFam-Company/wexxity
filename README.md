# Wex OS (Genesis 1.0)

```
                                  
                                  
 /$$  /$$  /$$  /$$$$$$  /$$   /$$
| $$ | $$ | $$ /$$__  $$|  $$ /$$/
| $$ | $$ | $$| $$$$$$$$ \  $$$$/ 
| $$ | $$ | $$| $$_____/  >$$  $$ 
|  $$$$$/$$$$/|  $$$$$$$ /$$/\  $$
 \_____/\___/  \_______/|__/  \__/
                                  
                                  
                                  
```

**Wex** is a modern, modular Linux operating system based on **Debian 13 (Trixie)**, engineered for flexibility, speed, and personalized setup. On its first boot, Wex features a custom terminal-based setup experience (`wex-setup`) that walks you through user creation, network configuration (Ethernet & Wi-Fi scanning), timezone selection, and desktop environment installation.

---

## 🌟 Key Features

1. **Custom First-Boot Experience**:
   - Iconic Wex 3D ASCII art welcome banner.
   - Primary and secondary user creation with optional `sudo` administrative rights.
   - Automatic Ethernet link detection and IP presentation.
   - Live IEEE 802.11 Wi-Fi scanning with formatted SSID, security, and frequency band display (2.4G/5G).
   - Timezone configuration supporting offsets (e.g. `GMT+5:30`) and standard Olson database names (e.g. `Asia/Kolkata`, `UTC`).
2. **On-Demand Desktop Environment Selection**:
   - Choose your favorite desktop environment during initial setup:
     - **GNOME** (`gnome-core`, `gdm3`, `firefox-esr`)
     - **XFCE** (`xfce4`, `lightdm`, `firefox-esr`)
     - **COSMIC** (System76 COSMIC desktop environment)
     - **KDE Plasma** (`kde-plasma-desktop`, `sddm`, `firefox-esr`)
     - **Cinnamon** (`cinnamon-core`, `lightdm`, `firefox-esr`)
     - **MATE** (`mate-desktop-environment-core`, `lightdm`, `firefox-esr`)
     - **LXQt** (`lxqt-core`, `sddm`, `firefox-esr`)
   - Automatically installs essential tools: terminal emulator, web browser (Firefox ESR), audio (`pipewire`), and display manager.
   - Seamless transition: disables the setup wizard upon completion and reboots straight into your desktop environment.
3. **Automated ISO Generation**:
   - Hybrid UEFI + BIOS bootable ISO images ready for physical PCs (USB drive) and virtual machines (VirtualBox, VMware, QEMU).

---

## 📂 Repository Structure

```
c:\Wex\
├── config\                      # OS Branding and system identity
│   ├── os-release               # Wex OS identification (/etc/os-release)
│   ├── issue                    # TTY login banner (/etc/issue)
│   ├── issue.net                # Remote banner (/etc/issue.net)
│   └── hostname                 # Default hostname (wex)
├── scripts\                     # ISO build and provisioning scripts
│   ├── build-wex-iso.sh         # Master hybrid ISO builder
│   └── setup-wex-chroot.sh      # Chroot setup and package provisioner
├── src\
│   └── wex-setup\               # First-boot setup wizard
│       ├── wex_setup.py         # Main wizard implementation
│       └── wex-setup.service    # Systemd service unit for /dev/tty1
├── test\                        # Automated test suites
│   ├── test_wizard.py           # Unit tests
│   └── test_e2e_flow.py         # End-to-end interactive flow simulation tests
├── run_demo.py                  # Interactive test runner (simulation mode)
├── run_demo.bat                 # Windows shortcut runner
└── README.md                    # Project documentation
```

---

## 🚀 Trying the Setup Wizard Now (Simulation Mode)

You can preview the first-boot experience on Windows or Linux right now without booting into an ISO:

### On Windows (PowerShell / Command Prompt):
```powershell
python run_demo.py
# or double click run_demo.bat
```

### On Linux / WSL:
```bash
python3 src/wex-setup/wex_setup.py --simulate
```

---

## 🧪 Running Automated Tests

Run the unit test suite and E2E simulation tests:

```bash
# Run unit tests
python test/test_wizard.py

# Run end-to-end flow tests
python test/test_e2e_flow.py
```

---

## 💿 Building the Wex Bootable ISO
 
To generate the bootable `wex-os-debian13-amd64.iso` image:
 
### Prerequisites (inside Ubuntu / Debian / WSL):
- `debootstrap`
- `squashfs-tools`
- `xorriso`
- `grub-pc-bin`
- `grub-efi-amd64-bin`
- `mtools`
- `dosfstools`
 
*(The build script will automatically detect and install missing tools if executed with root privileges).*
 
### Build Command:
```bash
sudo ./scripts/build-wex-iso.sh
```
 
Upon completion, the bootable ISO will be generated in:
`out/wex-os-debian13-amd64.iso`
 
### Testing in QEMU:
```bash
qemu-system-x86_64 -m 4G -enable-kvm -cdrom out/wex-os-debian13-amd64.iso -boot d
```

---

## ⚙️ How First-Boot Integration Works

1. **Systemd Service**: `wex-setup.service` is installed to `/etc/systemd/system/wex-setup.service` and enabled.
2. **TTY1 Attachment**: The service is configured with `StandardInput=tty`, `StandardOutput=tty`, and `TTYPath=/dev/tty1`. It runs before `getty@tty1` and `display-manager.service`.
3. **Execution**: On first boot, the user is greeted by the Wex ASCII banner and guided through the questionnaire.
4. **Self-Deactivation**: Once the chosen Desktop Environment and dependencies are installed, `wex_setup.py` runs `systemctl disable wex-setup.service`, enables the target display manager (e.g. `gdm3`, `lightdm`, `sddm`), and issues a reboot command. Subsequent boots land directly at the graphical user login.
