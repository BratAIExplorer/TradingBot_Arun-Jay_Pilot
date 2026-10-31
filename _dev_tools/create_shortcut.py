
import os
import sys
import winshell
from win32com.client import Dispatch

def create_shortcut():
    """
    Creates a desktop shortcut for the ARUN Bot.
    Supports two modes:
    1. Dist Mode: Points to the compiled EXE in /dist (if it exists)
    2. Source Mode: Points to the .venv python executable running kickstart_gui.py
    """
    try:
        desktop = winshell.desktop()
        current_dir = os.getcwd()
        
        # Check for Virtual Environment first (Source Mode)
        venv_python = os.path.join(current_dir, ".venv", "Scripts", "pythonw.exe")
        venv_python_alt = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
        
        # Check for compiled EXE (Dist Mode)
        dist_dir = os.path.join(current_dir, "dist")
        exe_path = None
        
        if os.path.exists(dist_dir):
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    if file.startswith("ARUN_Bot") and file.endswith(".exe"):
                        exe_path = os.path.join(root, file)
                        break
                if exe_path:
                    break

        target_path = ""
        arguments = ""
        icon_path = ""
        description = "ARUN Trading Bot"

        if exe_path:
            # Mode 1: Compiled EXE
            print(f"📦 Found compiled EXE: {exe_path}")
            target_path = exe_path
            icon_path = exe_path
        elif os.path.exists(venv_python):
            # Mode 2: Venv Python (Windowless)
            print(f"🐍 Found Virtual Environment: {venv_python}")
            target_path = venv_python
            arguments = f'"{os.path.join(current_dir, "kickstart_gui.py")}"'
            # Try to find an icon
            possible_icon = os.path.join(current_dir, "icon.ico")
            if os.path.exists(possible_icon):
                icon_path = possible_icon
            else:
                icon_path = sys.executable # Fallback to python icon
        elif os.path.exists(venv_python_alt):
             # Mode 2b: Venv Python (Standard)
            print(f"🐍 Found Virtual Environment (Standard): {venv_python_alt}")
            target_path = venv_python_alt
            arguments = f'"{os.path.join(current_dir, "kickstart_gui.py")}"'
            icon_path = sys.executable
        else:
            # Mode 3: Global Python (Fall back)
            print("⚠️ No venv or exe found. Using system python.")
            target_path = sys.executable
            arguments = f'"{os.path.join(current_dir, "kickstart_gui.py")}"'
            icon_path = sys.executable


        # ---------------------------------------------------------
        # Path Resolution
        # ---------------------------------------------------------
        # Method 1: winshell (sometimes fails with OneDrive)
        desktop_paths = [winshell.desktop()]
        
        # Method 2: os.path.expanduser (Standard)
        home = os.path.expanduser("~")
        desktop_paths.append(os.path.join(home, "Desktop"))
        
        # Method 3: OneDrive (Common on Windows 10/11)
        one_drive = os.path.join(home, "OneDrive", "Desktop")
        if os.path.exists(one_drive):
            desktop_paths.append(one_drive)
            
        desktop_paths = list(set(desktop_paths)) # Unique

        link_name = "ARUN Bot.lnk"
        
        # 1. Create in Current Directory (Backup)
        local_shortcut = os.path.join(current_dir, "LAUNCH_ARUN.lnk")
        create_link(local_shortcut, target_path, arguments, current_dir, icon_path, description)
        print(f"✅ Created local shortcut: {local_shortcut}")

        # 2. Create on Desktop(s)
        success = False
        for d in desktop_paths:
            if os.path.exists(d):
                shortcut_path = os.path.join(d, link_name)
                try:
                    create_link(shortcut_path, target_path, arguments, current_dir, icon_path, description)
                    print(f"✅ Created Desktop shortcut: {shortcut_path}")
                    success = True
                except Exception as e:
                    print(f"⚠️ Failed to create on {d}: {e}")
        
        if not success:
            print("❌ Could not create shortcut on any detected Desktop.")

    except Exception as e:
        print(f"❌ Failed to create shortcut: {e}")
        import time
        time.sleep(5)

def create_link(path, target, args, cwd, icon, desc):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(path)
    shortcut.TargetPath = target
    shortcut.Arguments = args
    shortcut.WorkingDirectory = cwd
    if icon:
        shortcut.IconLocation = icon
    shortcut.Description = desc
    shortcut.save()

if __name__ == "__main__":
    create_shortcut()
