#!/usr/bin/env python3
"""
Wex Operating System - First Boot Setup Wizard
Author: Wex OS Project
"""

import sys
import os
import re
import time
import subprocess
import getpass
import argparse
from typing import List, Dict, Optional, Tuple

WEX_BANNER = r"""
                                                               /$$                        
                                                              | $$                        
 /$$  /$$  /$$  /$$$$$$  /$$   /$$        /$$$$$$$  /$$$$$$  /$$$$$$   /$$   /$$  /$$$$$$ 
| $$ | $$ | $$ /$$__  $$|  $$ /$$/       /$$_____/ /$$__  $$|_  $$_/  | $$  | $$ /$$__  $$
| $$ | $$ | $$| $$$$$$$$ \  $$$$/       |  $$$$$$ | $$$$$$$$  | $$    | $$  | $$| $$  \ $$
| $$ | $$ | $$| $$_____/  >$$  $$        \____  $$| $$_____/  | $$ /$$| $$  | $$| $$  | $$
|  $$$$$/$$$$/|  $$$$$$$ /$$/\  $$       /$$$$$$$/|  $$$$$$$  |  $$$$/|  $$$$$$/| $$$$$$$/
 \_____/\___/  \_______/|__/  \__/      |_______/  \_______/   \___/   \______/ | $$____/ 
                                                                                | $$      
                                                                                | $$      
                                                                                |__/      
"""

# Available Desktop Environments and their package configurations (Debian 12 base)
DESKTOP_ENVIRONMENTS = {
    "GNOME": {
        "name": "GNOME Desktop",
        "packages": ["gnome-core", "gdm3", "gnome-terminal", "firefox-esr"],
        "display_manager": "gdm3",
    },
    "XFCE": {
        "name": "XFCE Lightweight Desktop",
        "packages": ["xfce4", "lightdm", "xfce4-terminal", "firefox-esr"],
        "display_manager": "lightdm",
    },
    "COSMIC": {
        "name": "COSMIC Desktop (System76)",
        "packages": ["cosmic-session", "cosmic-term", "firefox-esr"],
        "display_manager": "cosmic-greeter",
        "repo_needed": "system76-dev/stable",
    },
    "KDE": {
        "name": "KDE Plasma Desktop",
        "packages": ["kde-plasma-desktop", "sddm", "konsole", "firefox-esr"],
        "display_manager": "sddm",
    },
    "CINNAMON": {
        "name": "Cinnamon Desktop",
        "packages": ["cinnamon-core", "lightdm", "gnome-terminal", "firefox-esr"],
        "display_manager": "lightdm",
    },
    "MATE": {
        "name": "MATE Desktop",
        "packages": ["mate-desktop-environment-core", "lightdm", "mate-terminal", "firefox-esr"],
        "display_manager": "lightdm",
    },
    "LXQT": {
        "name": "LXQt Lightweight Desktop",
        "packages": ["lxqt-core", "sddm", "qterminal", "firefox-esr"],
        "display_manager": "sddm",
    },
}


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    """Print the official Wex Setup banner."""
    clear_screen()
    print(WEX_BANNER)


def prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """Prompt user for Yes/No. Returns True if Yes, False if No."""
    default_hint = "[Y/n]" if default_yes else "[y/N]"
    while True:
        try:
            print(f"{prompt} {default_hint}")
            choice = input().strip().lower()
        except EOFError:
            return default_yes

        if choice == "":
            return default_yes
        if choice in ["y", "yes"]:
            return True
        if choice in ["n", "no"]:
            return False
        print("Please answer 'y' or 'n'.")


def get_secure_password(username: str) -> str:
    """Prompt for user password with confirmation."""
    while True:
        try:
            p1 = getpass.getpass(f"Set password for {username}: ")
            if not p1:
                print("Password cannot be empty. Please try again.")
                continue
            p2 = getpass.getpass(f"Confirm password for {username}: ")
            if p1 != p2:
                print("Passwords do not match. Please try again.")
                continue
            return p1
        except EOFError:
            return "wex"


def validate_username(username: str) -> bool:
    """Check if username matches standard POSIX naming conventions."""
    return bool(re.match(r"^[a-z_][a-z0-9_-]{0,31}$", username))


def create_user_account(full_name: str, username: str, password: str, enable_sudo: bool, simulate: bool = False):
    """Create a new system user account and optionally assign sudo privileges."""
    if simulate:
        print(f"[Simulation] Created user '{username}' (Full Name: {full_name}, Sudo: {enable_sudo})")
        return

    try:
        # Create user with home directory and bash shell
        subprocess.run(
            ["useradd", "-m", "-s", "/bin/bash", "-c", full_name, username],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Set password
        proc = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.communicate(input=f"{username}:{password}\n".encode())

        if enable_sudo:
            subprocess.run(["usermod", "-aG", "sudo", username], check=True)
    except Exception as e:
        print(f"Warning: Could not create user {username}: {e}")


def check_ethernet(simulate: bool = False) -> Optional[str]:
    """Check for active Ethernet connection and return its IP address if found."""
    if simulate:
        # In simulation mode, simulate an ethernet or no ethernet
        return "192.168.1.105"

    try:
        # Check network devices using ip route/addr or nmcli
        # Try finding non-wireless interface with an IPv4 address
        result = subprocess.run(
            ["ip", "-o", "-4", "addr", "show"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                iface = parts[1]
                ip_cidr = parts[3]
                ip = ip_cidr.split("/")[0]
                # Filter out loopback and wireless
                if not iface.startswith("lo") and not iface.startswith("wl"):
                    if "state UP" in line or "UP" in parts[2]:
                        return ip
    except Exception:
        pass

    return None


def scan_wifi(simulate: bool = False) -> List[Dict[str, str]]:
    """Scan for Wi-Fi networks and return a list of networks."""
    if simulate:
        return [
            {"ssid": "McDonalds_Wifi", "security": "Open", "band": "2.4G"},
            {"ssid": "Home_WiFi", "security": "WPA2", "band": "5G"},
            {"ssid": "Starbucks_Guest", "security": "WPA2", "band": "2.4G"},
        ]

    networks: List[Dict[str, str]] = []
    try:
        cmd = ["nmcli", "-t", "-f", "SSID,SECURITY,CHAN,FREQ", "dev", "wifi", "list"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

        seen_ssids = set()
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 3:
                ssid = parts[0].strip()
                if not ssid or ssid in seen_ssids:
                    continue
                seen_ssids.add(ssid)
                sec = parts[1].strip() if parts[1].strip() else "Open"
                freq_str = parts[-1].strip()
                band = "5G" if "5" in freq_str else "2.4G"
                networks.append({"ssid": ssid, "security": sec, "band": band})
    except Exception:
        pass

    return networks


def connect_wifi(ssid: str, security: str, simulate: bool = False) -> bool:
    """Connect to the selected Wi-Fi network."""
    password = ""
    if security.upper() != "OPEN":
        try:
            password = getpass.getpass(f"Enter password for Wi-Fi '{ssid}': ")
        except EOFError:
            password = ""

    if simulate:
        print(f"[Simulation] Connected to Wi-Fi: {ssid}")
        return True

    print(f"Connecting to {ssid}...")
    try:
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if password:
            cmd.extend(["password", password])
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print(f"Successfully connected to {ssid}!")
            return True
        else:
            print(f"Failed to connect: {res.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Error connecting to Wi-Fi: {e}")
        return False


def configure_timezone(tz_input: str, simulate: bool = False) -> bool:
    """Parse timezone input (e.g. GMT+5:30, Asia/Kolkata, UTC) and set system timezone."""
    tz_input = tz_input.strip()
    if simulate:
        print(f"[Simulation] Time zone set to: {tz_input}")
        return True

    matched_tz = None

    if os.path.exists(f"/usr/share/zoneinfo/{tz_input}"):
        matched_tz = tz_input
    elif tz_input.upper() in ["UTC", "GMT"]:
        matched_tz = "UTC"
    else:
        m = re.match(r"^(?:GMT|UTC)?\s*([+-])(\d{1,2})(?::(\d{2}))?$", tz_input, re.IGNORECASE)
        if m:
            sign = m.group(1)
            hours = int(m.group(2))
            minutes = int(m.group(3)) if m.group(3) else 0

            if sign == "+" and hours == 5 and minutes == 30:
                matched_tz = "Asia/Kolkata"
            elif sign == "+" and hours == 8 and minutes == 0:
                matched_tz = "Asia/Singapore"
            elif sign == "+" and hours == 9 and minutes == 0:
                matched_tz = "Asia/Tokyo"
            elif sign == "+" and hours == 1 and minutes == 0:
                matched_tz = "Europe/Paris"
            elif sign == "-" and hours == 5 and minutes == 0:
                matched_tz = "America/New_York"
            elif sign == "-" and hours == 8 and minutes == 0:
                matched_tz = "America/Los_Angeles"
            else:
                posix_sign = "-" if sign == "+" else "+"
                matched_tz = f"Etc/GMT{posix_sign}{hours}"
        else:
            if os.path.exists("/usr/share/zoneinfo"):
                for root, _, files in os.walk("/usr/share/zoneinfo"):
                    for f in files:
                        full_rel = os.path.relpath(os.path.join(root, f), "/usr/share/zoneinfo")
                        if f.lower() == tz_input.lower() or full_rel.lower() == tz_input.lower():
                            matched_tz = full_rel
                            break
                    if matched_tz:
                        break

    if not matched_tz:
        matched_tz = "UTC"

    try:
        subprocess.run(["timedatectl", "set-timezone", matched_tz], check=False)
        if os.path.exists(f"/usr/share/zoneinfo/{matched_tz}"):
            if os.path.exists("/etc/localtime"):
                os.remove("/etc/localtime")
            os.symlink(f"/usr/share/zoneinfo/{matched_tz}", "/etc/localtime")
            with open("/etc/timezone", "w") as f:
                f.write(f"{matched_tz}\n")
        print(f"Time zone configured: {matched_tz}")
        return True
    except Exception as e:
        print(f"Warning: Unable to set timezone: {e}")
        return False


def mark_setup_done(simulate: bool = False):
    """Write the sentinel file that prevents wex-setup from running again on reboot."""
    if simulate:
        print("[Simulation] Wrote /etc/wex-setup-done (setup will not run again after reboot)")
        return
    try:
        with open("/etc/wex-setup-done", "w") as f:
            f.write("Wex OS first-boot setup completed.\n")
        # Belt-and-suspenders: also disable the service unit
        subprocess.run(["systemctl", "disable", "wex-setup.service"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Warning: Could not write sentinel file: {e}")


def install_desktop_environment(de_choice: str, simulate: bool = False):
    """Install the user's chosen desktop environment, browser, and terminal."""
    de_key = de_choice.strip().upper()
    de_info = DESKTOP_ENVIRONMENTS.get(de_key)

    if not de_info:
        for k, v in DESKTOP_ENVIRONMENTS.items():
            if k in de_key or de_key in k:
                de_info = v
                de_key = k
                break

    if not de_info:
        print(f"Selected desktop '{de_choice}' will be installed as custom package.")
        de_info = {
            "name": de_choice,
            "packages": [de_choice.lower(), "lightdm", "xterm", "firefox"],
            "display_manager": "lightdm",
        }

    print(f"\n=======================================================")
    print(f" Installing {de_info['name']} & Essential Applications...")
    print(f" Packages: {', '.join(de_info['packages'])}")
    print(f"=======================================================\n")

    if simulate:
        print(f"[Simulation] Updating package catalogs (apt update)...")
        for pkg in de_info["packages"]:
            print(f"[Simulation] Installing package: {pkg}...")
        print(f"[Simulation] Setting display manager: {de_info['display_manager']}")
        print(f"[Simulation] Setting graphical target as default...")
        mark_setup_done(simulate=True)
        return

    try:
        if de_info.get("repo_needed"):
            subprocess.run(
                ["add-apt-repository", "-y", f"ppa:{de_info['repo_needed']}"],
                check=False,
            )

        print("Updating package lists...")
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        subprocess.run(["apt-get", "update", "-y"], env=env, check=False)

        print(f"Installing {de_info['name']} and applications...")
        cmd = ["apt-get", "install", "-y", "--no-install-recommends"] + de_info["packages"]
        subprocess.run(cmd, env=env, check=True)

        subprocess.run(["systemctl", "set-default", "graphical.target"], check=False)

        dm = de_info.get("display_manager")
        if dm:
            subprocess.run(["systemctl", "enable", dm], check=False)

    except Exception as e:
        print(f"Installation encountered an error: {e}")
        input("Press Enter to continue anyway...")
    finally:
        # Always mark setup as done so it never runs again on reboot
        mark_setup_done(simulate=False)



def main():
    parser = argparse.ArgumentParser(description="Wex OS First Boot Setup Wizard")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation/demo mode")
    parser.add_argument("--test", action="store_true", help="Alias for --simulate")
    args = parser.parse_args()

    simulate = args.simulate or args.test

    # 1. Print Banner
    print_banner()

    # 2. First Account Creation
    full_name = ""
    while not full_name:
        try:
            print("Enter your name:")
            full_name = input().strip()
        except EOFError:
            full_name = "Wex User"

    username = ""
    while not username:
        try:
            print(f"Enter a username for {full_name}: ")
            u_input = input().strip()
            if not u_input:
                u_input = full_name.lower().replace(" ", "")
            if validate_username(u_input):
                username = u_input
            else:
                print("Username must start with a lowercase letter and contain only lowercase letters, digits, '_' or '-'.")
        except EOFError:
            username = "wexuser"

    password = get_secure_password(username)
    create_user_account(full_name, username, password, enable_sudo=True, simulate=simulate)

    # 3. Optional Second Account
    make_new_account = prompt_yes_no("Do you want to make a new account?", default_yes=True)
    if make_new_account:
        name2 = ""
        while not name2:
            try:
                print("Enter the name")
                name2 = input().strip()
            except EOFError:
                name2 = "Second User"

        user2 = ""
        while not user2:
            try:
                print(f"Enter the username for {name2}:")
                u2_input = input().strip()
                if not u2_input:
                    u2_input = name2.lower().replace(" ", "")
                if validate_username(u2_input):
                    user2 = u2_input
                else:
                    print("Username must start with a lowercase letter and contain only lowercase letters, digits, '_' or '-'.")
            except EOFError:
                user2 = "seconduser"

        pw2 = get_secure_password(user2)
        enable_sudo2 = prompt_yes_no(f"Do you want to enable sudo in {name2} ({user2})?", default_yes=True)
        create_user_account(name2, user2, pw2, enable_sudo=enable_sudo2, simulate=simulate)

        if enable_sudo2:
            print("Done.")
        else:
            print("Ok.")

    # A1: Network configuration
    print("\nNetwork configuration:")
    print("Please wait, we are checking the ethernet...")
    if not simulate:
        time.sleep(1.5)

    eth_ip = check_ethernet(simulate=simulate)
    network_connected = False
    use_ethernet = False

    if eth_ip:
        print("Ethernet found!")
        print(f"IP: {eth_ip}")
        use_ethernet = prompt_yes_no("Do you want to use it?", default_yes=True)
        if use_ethernet:
            network_connected = True
    else:
        print("No ethernet found.")

    if not use_ethernet:
        print("Checking Wi-Fi (IEEE 802.11)...")
        if not simulate:
            time.sleep(1.2)
        wifi_list = scan_wifi(simulate=simulate)

        if wifi_list:
            for idx, net in enumerate(wifi_list, 1):
                ssid_col = net["ssid"].ljust(40)
                sec_col = net["security"].ljust(35)
                band_col = net["band"]
                print(f"{idx}. {ssid_col}{sec_col}{band_col}")

            chosen_idx = None
            prompt_str = f"Choose: 1/{len(wifi_list)}:"
            while chosen_idx is None:
                try:
                    print(prompt_str)
                    c_input = input().strip()
                    if c_input.isdigit():
                        val = int(c_input)
                        if 1 <= val <= len(wifi_list):
                            chosen_idx = val - 1
                            break
                except EOFError:
                    chosen_idx = 0
                    break

            selected_wifi = wifi_list[chosen_idx]
            if connect_wifi(selected_wifi["ssid"], selected_wifi["security"], simulate=simulate):
                network_connected = True
        else:
            print("No Wi-Fi networks found.")

    # Time zone
    print("\nEnter your time zone:")
    print("           ex.: GMT+5:30")
    try:
        tz_input = input().strip()
    except EOFError:
        tz_input = "GMT+5:30"
    if not tz_input:
        tz_input = "GMT+5:30"
    configure_timezone(tz_input, simulate=simulate)

    # Desktop Environment — only if network is available (needed for apt install)
    if not network_connected:
        print("\n=======================================================")
        print(" No network connection available.")
        print(" Wex OS will boot to the command-line interface (CLI).")
        print(" You can install a desktop environment later by running:")
        print("   sudo apt install gnome-core   (or xfce4, kde-plasma-desktop, …)")
        print("=======================================================\n")
        if not simulate:
            subprocess.run(["systemctl", "set-default", "multi-user.target"], check=False)
        else:
            print("[Simulation] Set default target to multi-user.target (CLI)")
        mark_setup_done(simulate=simulate)
    else:
        # Desktop Environment selection
        print("\nPlease enter your preferred Desktop Environment [GNOME/XFCE/COSMIC/<and all other desktop environments>]")
        try:
            de_choice = input().strip()
        except EOFError:
            de_choice = "GNOME"
        if not de_choice:
            de_choice = "GNOME"

        install_desktop_environment(de_choice, simulate=simulate)

    # Final step: Reboot
    print("\n=======================================================")
    print(" Setup complete! Wex OS is ready.")
    if network_connected:
        print(" Rebooting system to start your desktop environment...")
    else:
        print(" Rebooting system to the command-line interface...")
    print("=======================================================\n")
    if not simulate:
        time.sleep(2)
        subprocess.run(["reboot"], check=False)
    else:
        print("[Simulation] System reboot triggered.")




if __name__ == "__main__":
    main()
