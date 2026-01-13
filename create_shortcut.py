
import os
import sys
import winshell
from win32com.client import Dispatch

def create_shortcut():
    """
    Creates a desktop shortcut for the ARUN Bot EXE.
    """
    try:
        # Define paths
        desktop = winshell.desktop()

        # Look for the EXE in the dist folder
        # We need to find the specific version folder or just the EXE if onefile
        # The build script will pass the version, but let's try to find it dynamically or assume a path

        # Expecting structure: dist/ARUN_Bot_v1.0.0/ARUN_Bot_v1.0.0.exe (if onedir)
        # OR dist/ARUN_Bot_v1.0.0.exe (if onefile)

        # We will search in dist for the .exe
        dist_dir = os.path.join(os.getcwd(), "dist")

        if not os.path.exists(dist_dir):
            print(f"❌ Dist folder not found at: {dist_dir}")
            return

        exe_path = None
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                if file.startswith("ARUN_Bot") and file.endswith(".exe"):
                    exe_path = os.path.join(root, file)
                    break
            if exe_path:
                break

        if not exe_path:
            print("❌ Could not find ARUN_Bot EXE in dist folder.")
            return

        target_exe = exe_path
        link_name = "ARUN Bot.lnk"
        shortcut_path = os.path.join(desktop, link_name)

        # Create shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_exe
        shortcut.WorkingDirectory = os.path.dirname(target_exe)
        shortcut.IconLocation = target_exe
        shortcut.save()

        print(f"✅ Shortcut created successfully: {shortcut_path}")
        print(f"   Target: {target_exe}")

    except Exception as e:
        print(f"❌ Failed to create shortcut: {e}")

if __name__ == "__main__":
    create_shortcut()
