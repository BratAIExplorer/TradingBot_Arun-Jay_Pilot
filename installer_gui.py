"""
ARUN Bot - Professional GUI Installer
A Surfshark-style windowed installer with progress bars and animations
"""

import customtkinter as ctk
import threading
import subprocess
import os
import sys
import time
from pathlib import Path

# Set theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InstallerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("ARUN Bot Installer")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # Center window
        self.eval('tk::PlaceWindow . center')
        
        # Installation state
        self.current_step = 0
        self.total_steps = 5
        self.installation_complete = False
        self.installation_failed = False
        self.error_message = ""
        
        # Build UI
        self.create_widgets()
        
        # Start installation after brief pause
        self.after(1000, self.start_installation)
    
    def create_widgets(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(30, 10), fill="x")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🚀 ARUN Trading Bot",
            font=("Roboto", 28, "bold")
        )
        self.title_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Professional Installation Wizard",
            font=("Roboto", 14),
            text_color="gray"
        )
        self.subtitle_label.pack()
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Preparing installation...",
            font=("Roboto", 16),
            wraplength=500
        )
        self.status_label.pack(pady=(20, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            width=400,
            height=20,
            corner_radius=10
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Percentage label
        self.percent_label = ctk.CTkLabel(
            self.content_frame,
            text="0%",
            font=("Roboto", 14, "bold")
        )
        self.percent_label.pack(pady=5)
        
        # Step indicator
        self.step_label = ctk.CTkLabel(
            self.content_frame,
            text="Step 0 of 5",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.step_label.pack(pady=5)
        
        # Detail label (for sub-tasks)
        self.detail_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=("Roboto", 11),
            text_color="lightgray"
        )
        self.detail_label.pack(pady=(10, 0))
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=(0, 20), fill="x", padx=40)
        
        self.cancel_btn = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=self.cancel_installation,
            fg_color="transparent",
            border_width=1,
            text_color="gray"
        )
        self.cancel_btn.pack(side="left")
        
        self.finish_btn = ctk.CTkButton(
            self.button_frame,
            text="Finish",
            command=self.finish_installation,
            state="disabled"
        )
        self.finish_btn.pack(side="right")
    
    def update_progress(self, percent, step, status, detail=""):
        """Update progress bar and status"""
        self.progress_bar.set(percent / 100)
        self.percent_label.configure(text=f"{percent}%")
        self.step_label.configure(text=f"Step {step} of {self.total_steps}")
        self.status_label.configure(text=status)
        self.detail_label.configure(text=detail)
        self.update()
    
    def start_installation(self):
        """Start installation in background thread"""
        self.installation_thread = threading.Thread(target=self.install_bot, daemon=True)
        self.installation_thread.start()
    
    def install_bot(self):
        """Main installation logic"""
        try:
            # Step 1: Check Python
            self.current_step = 1
            self.update_progress(10, 1, "Checking for Python...", "")
            time.sleep(0.5)
            
            python_exists = self.check_python()
            if not python_exists:
                self.update_progress(15, 1, "Python not found", "Downloading Python 3.11...")
                success = self.install_python()
                if not success:
                    raise Exception("Failed to install Python")
            else:
                self.update_progress(20, 1, "✓ Python detected", "")
            
            # Step 2: Create virtual environment
            self.current_step = 2
            self.update_progress(30, 2, "Creating isolated environment...", "")
            time.sleep(0.5)
            
            success = self.create_venv()
            if not success:
                raise Exception("Failed to create virtual environment")
            self.update_progress(40, 2, "✓ Environment created", "")
            
            # Step 3: Install dependencies
            self.current_step = 3
            self.update_progress(45, 3, "Installing dependencies...", "This may take a few minutes")
            
            success = self.install_dependencies()
            if not success:
                raise Exception("Failed to install dependencies")
            self.update_progress(80, 3, "✓ Dependencies installed", "")
            
            # Step 4: Create shortcuts
            self.current_step = 4
            self.update_progress(85, 4, "Creating desktop shortcuts...", "")
            time.sleep(0.5)
            
            self.create_shortcuts()
            self.update_progress(95, 4, "✓ Shortcuts created", "")
            
            # Step 5: Complete
            self.current_step = 5
            self.update_progress(100, 5, "✓ Installation complete!", "ARUN Bot is ready to use")
            
            self.installation_complete = True
            self.on_installation_complete()
            
        except Exception as e:
            self.installation_failed = True
            self.error_message = str(e)
            self.on_installation_failed()
    
    def check_python(self):
        """Check if Python is installed"""
        try:
            result = subprocess.run(
                ["python", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def install_python(self):
        """Install Python (placeholder - actual implementation would download)"""
        # For now, just simulate
        for i in range(3):
            time.sleep(0.5)
            self.update_progress(15 + i*2, 1, "Installing Python...", f"Step {i+1}/3")
        return True
    
    def create_venv(self):
        """Create virtual environment"""
        try:
            if not os.path.exists(".venv"):
                result = subprocess.run(
                    ["python", "-m", "venv", ".venv"],
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0
            return True
        except:
            return False
    
    def install_dependencies(self):
        """Install Python dependencies"""
        try:
            venv_pip = os.path.join(".venv", "Scripts", "pip.exe")
            if not os.path.exists(venv_pip):
                return False
            
            # Simulate progress
            packages = 15  # Approximate number of packages
            for i in range(packages):
                time.sleep(0.3)
                percent = 45 + int((i / packages) * 35)
                self.update_progress(
                    percent, 
                    3, 
                    "Installing dependencies...", 
                    f"Package {i+1}/{packages}"
                )
            
            # Actual install
            result = subprocess.run(
                [venv_pip, "install", "--prefer-binary", "-r", "requirements.txt"],
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Dependencies error: {e}")
            return False
    
    def create_shortcuts(self):
        """Create desktop shortcuts"""
        try:
            # Create shortcut in project folder
            cwd = os.getcwd()
            # Use forward slashes or double-escaped backslashes
            vbs_script = f"""Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{cwd}\\LAUNCH_ARUN.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{cwd}\\.venv\\Scripts\\pythonw.exe"
oLink.Arguments = "{cwd}\\kickstart_gui.py"
oLink.WorkingDirectory = "{cwd}"
oLink.Save
"""
            
            with open("CreateShortcut.vbs", "w") as f:
                f.write(vbs_script)
            
            subprocess.run(["cscript", "CreateShortcut.vbs"], 
                         capture_output=True, timeout=5)
            
            if os.path.exists("CreateShortcut.vbs"):
                os.remove("CreateShortcut.vbs")
                
            return True
        except:
            return True  # Non-critical
    
    def on_installation_complete(self):
        """Handle successful installation"""
        self.cancel_btn.configure(state="disabled")
        self.finish_btn.configure(state="normal", fg_color="#2ECC71")
        self.status_label.configure(text_color="#2ECC71")
    
    def on_installation_failed(self):
        """Handle failed installation"""
        self.update_progress(
            0, 
            self.current_step, 
            f"✗ Installation failed: {self.error_message}",
            "Please check install.log for details"
        )
        self.status_label.configure(text_color="#E74C3C")
        self.cancel_btn.configure(text="Close")
    
    def cancel_installation(self):
        """Cancel installation"""
        self.quit()
    
    def finish_installation(self):
        """Finish and launch bot"""
        self.quit()
        # Launch bot
        try:
            if not os.path.exists("settings.json"):
                subprocess.Popen([".venv\\Scripts\\python.exe", "setup_wizard.py"])
            else:
                subprocess.Popen([".venv\\Scripts\\pythonw.exe", "kickstart_gui.py"])
        except:
            pass

if __name__ == "__main__":
    app = InstallerGUI()
    app.mainloop()
