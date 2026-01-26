"""
Quick test script for the GUI installer
Run this to see the installer window without needing the batch file
"""
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import and run the installer
from installer_gui import InstallerGUI

if __name__ == "__main__":
    print("Launching ARUN Bot Installer GUI...")
    print("This is a TEST - it will perform a real installation!")
    print("-" * 50)
    
    app = InstallerGUI()
    app.mainloop()
    
    print("\nInstaller closed.")
