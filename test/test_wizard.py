#!/usr/bin/env python3
"""
Unit tests for Wex OS First Boot Setup Wizard
"""

import sys
import os
import unittest
from io import StringIO
from unittest.mock import patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "wex-setup")))

import wex_setup


class TestWexSetup(unittest.TestCase):

    def test_banner_contains_ascii(self):
        """Verify the banner contains the exact ASCII letters for Wex Setup."""
        banner = wex_setup.WEX_BANNER
        self.assertIn("/$$$$$$", banner)
        self.assertIn("/$$__  $$", banner)
        self.assertIn(r"\  $$$$/", banner)

    def test_username_validation(self):
        """Verify username validation rules."""
        self.assertTrue(wex_setup.validate_username("jisha"))
        self.assertTrue(wex_setup.validate_username("wex_user"))
        self.assertTrue(wex_setup.validate_username("admin1"))
        self.assertFalse(wex_setup.validate_username("1admin"))  # Cannot start with digit
        self.assertFalse(wex_setup.validate_username("User"))    # No uppercase
        self.assertFalse(wex_setup.validate_username("user@home")) # Invalid char

    def test_timezone_configuration_simulation(self):
        """Verify timezone parsing in simulation mode."""
        self.assertTrue(wex_setup.configure_timezone("GMT+5:30", simulate=True))
        self.assertTrue(wex_setup.configure_timezone("UTC", simulate=True))
        self.assertTrue(wex_setup.configure_timezone("America/New_York", simulate=True))

    def test_desktop_environments_available(self):
        """Verify the supported desktop environments are configured."""
        des = wex_setup.DESKTOP_ENVIRONMENTS
        self.assertIn("GNOME", des)
        self.assertIn("XFCE", des)
        self.assertIn("COSMIC", des)
        self.assertIn("KDE", des)
        self.assertIn("CINNAMON", des)
        self.assertIn("MATE", des)
        self.assertIn("LXQT", des)

        # Ensure every DE has packages, display manager, and a browser
        for de_name, config in des.items():
            self.assertIn("packages", config)
            self.assertIn("display_manager", config)
            self.assertIn("firefox-esr", config["packages"])

    def test_wifi_scan_simulation(self):
        """Verify Wi-Fi scan produces expected list in simulation mode."""
        wifi_list = wex_setup.scan_wifi(simulate=True)
        self.assertEqual(len(wifi_list), 3)
        self.assertEqual(wifi_list[0]["ssid"], "McDonalds_Wifi")
        self.assertEqual(wifi_list[0]["security"], "Open")
        self.assertEqual(wifi_list[0]["band"], "2.4G")
        self.assertEqual(wifi_list[1]["ssid"], "Home_WiFi")
        self.assertEqual(wifi_list[1]["security"], "WPA2")
        self.assertEqual(wifi_list[1]["band"], "5G")

    def test_ethernet_check_simulation(self):
        """Verify ethernet check returns IP in simulation mode."""
        ip = wex_setup.check_ethernet(simulate=True)
        self.assertEqual(ip, "192.168.1.105")


if __name__ == "__main__":
    unittest.main()
