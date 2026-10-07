#!/usr/bin/env python3
"""
Quick interactive test runner for Wex OS Setup Wizard.
Runs the first-boot setup wizard in simulation mode.
"""

import sys
import os

# Add src/wex-setup to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "wex-setup")))

import wex_setup

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--simulate"]
    wex_setup.main()
