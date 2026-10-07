#!/usr/bin/env python3
"""
End-to-End flow simulation tests for Wex OS First Boot Setup
"""

import sys
import os
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "wex-setup")))

import wex_setup


class TestWexE2EFlow(unittest.TestCase):

    @patch("wex_setup.clear_screen")
    @patch("wex_setup.getpass.getpass")
    @patch("builtins.input")
    @patch("sys.stdout", new_callable=StringIO)
    def test_full_flow_with_second_account_and_ethernet(self, mock_stdout, mock_input, mock_getpass, mock_clear):
        """Test full setup flow:
        - Primary user: Jisha
        - Secondary user: Alice (with sudo -> Done.)
        - Ethernet: Yes
        - Timezone: GMT+5:30
        - DE: GNOME
        """
        mock_getpass.side_effect = ["pass123", "pass123", "pass456", "pass456"]
        mock_input.side_effect = [
            "Jisha",           # Enter your name
            "jisha",           # Enter a username for Jisha
            "Y",               # Do you want to make a new account?
            "Alice",           # Enter the name
            "alice",           # Enter the username for Alice
            "Y",               # Do you want to enable sudo in Alice (alice)? -> Done.
            "Y",               # Ethernet found! Do you want to use it?
            "GMT+5:30",        # Enter your time zone
            "GNOME",           # Preferred Desktop Environment
        ]

        # Run in simulation mode
        with patch("sys.argv", ["wex_setup.py", "--simulate"]):
            wex_setup.main()

        output = mock_stdout.getvalue()

        # Check key dialog strings
        self.assertIn("Enter your name:", output)
        self.assertIn("Enter a username for Jisha:", output)
        self.assertIn("Do you want to make a new account? [Y/n]", output)
        self.assertIn("Enter the name", output)
        self.assertIn("Enter the username for Alice:", output)
        self.assertIn("Do you want to enable sudo in Alice (alice)? [Y/n]", output)
        self.assertIn("Done.", output)
        self.assertIn("Network configuration:", output)
        self.assertIn("Please wait, we are checking the ethernet...", output)
        self.assertIn("Ethernet found!", output)
        self.assertIn("IP: 192.168.1.105", output)
        self.assertIn("Enter your time zone:", output)
        self.assertIn("ex.: GMT+5:30", output)
        self.assertIn("Please enter your preferred Desktop Environment", output)
        self.assertIn("Installing GNOME Desktop", output)
        self.assertIn("Setup complete! Wex OS is ready.", output)

    @patch("wex_setup.clear_screen")
    @patch("wex_setup.getpass.getpass")
    @patch("builtins.input")
    @patch("sys.stdout", new_callable=StringIO)
    def test_full_flow_no_second_account_and_wifi(self, mock_stdout, mock_input, mock_getpass, mock_clear):
        """Test setup flow:
        - Primary user: Bob
        - No second account -> n
        - Ethernet: n -> checks Wi-Fi
        - Choose Wi-Fi: 2 (Home_WiFi)
        - Timezone: Asia/Tokyo
        - DE: COSMIC
        """
        mock_getpass.side_effect = ["bobpass", "bobpass", "wifipass"]
        mock_input.side_effect = [
            "Bob",             # Enter your name
            "bob",             # Enter a username for Bob
            "n",               # Do you want to make a new account? -> n (go to A1)
            "n",               # Ethernet found! Do you want to use it? -> n
            "2",               # Choose: 1/3 (Home_WiFi)
            "Asia/Tokyo",      # Enter your time zone
            "COSMIC",          # Preferred Desktop Environment
        ]

        with patch("sys.argv", ["wex_setup.py", "--simulate"]):
            wex_setup.main()

        output = mock_stdout.getvalue()

        # Check key strings
        self.assertIn("Enter your name:", output)
        self.assertIn("Enter a username for Bob:", output)
        self.assertIn("Checking Wi-Fi (IEEE 802.11)...", output)
        self.assertIn("1. McDonalds_Wifi", output)
        self.assertIn("2. Home_WiFi", output)
        self.assertIn("Open", output)
        self.assertIn("WPA2", output)
        self.assertIn("Choose: 1/3:", output)
        self.assertIn("Connected to Wi-Fi: Home_WiFi", output)
        self.assertIn("Time zone set to: Asia/Tokyo", output)
        self.assertIn("Installing COSMIC Desktop (System76)", output)

    @patch("wex_setup.clear_screen")
    @patch("wex_setup.getpass.getpass")
    @patch("builtins.input")
    @patch("sys.stdout", new_callable=StringIO)
    def test_wifi_invalid_selection_retry(self, mock_stdout, mock_input, mock_getpass, mock_clear):
        """Test that invalid Wi-Fi selection re-prompts until valid."""
        mock_getpass.side_effect = ["charliepass", "charliepass"]
        mock_input.side_effect = [
            "Charlie",         # Name
            "charlie",         # Username
            "n",               # Second account? No
            "n",               # Use ethernet? No
            "99",              # Invalid Wi-Fi index -> should re-prompt
            "invalid_choice",  # Invalid Wi-Fi string -> should re-prompt
            "1",               # Valid choice (McDonalds_Wifi)
            "UTC",             # Time zone
            "XFCE",            # DE
        ]

        with patch("sys.argv", ["wex_setup.py", "--simulate"]):
            wex_setup.main()

        output = mock_stdout.getvalue()
        # Count occurrences of prompt
        self.assertGreaterEqual(output.count("Choose: 1/3:"), 3)
        self.assertIn("Installing XFCE Lightweight Desktop", output)


if __name__ == "__main__":
    unittest.main()
