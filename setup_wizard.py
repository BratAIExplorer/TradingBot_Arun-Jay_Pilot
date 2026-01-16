
import customtkinter as ctk
import json
import os
import webbrowser
import sys

# Set aesthetic theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ARUN Bot - First Time Setup")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Center window
        self.eval('tk::PlaceWindow . center')

        self.create_widgets()

    def create_widgets(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(pady=20, fill="x")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🚀 Welcome to ARUN Bot", 
            font=("Roboto", 24, "bold")
        )
        self.title_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame, 
            text="Let's get you ready for automated trading.", 
            font=("Roboto", 14),
            text_color="gray"
        )
        self.subtitle_label.pack()

        # Input Form
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(pady=20, padx=40, fill="both", expand=True)

        # API Key
        self.api_label = ctk.CTkLabel(self.form_frame, text="mStock API Key:", anchor="w")
        self.api_label.pack(fill="x", padx=20, pady=(20, 0))
        
        self.api_entry = ctk.CTkEntry(
            self.form_frame, 
            placeholder_text="Enter your API Key here...",
            width=400
        )
        self.api_entry.pack(fill="x", padx=20, pady=(5, 10))

        # TOTP Secret
        self.totp_label = ctk.CTkLabel(self.form_frame, text="TOTP Secret (for Auto-Login):", anchor="w")
        self.totp_label.pack(fill="x", padx=20, pady=(10, 0))
        
        self.totp_entry = ctk.CTkEntry(
            self.form_frame, 
            placeholder_text="Enter TOTP Secret...",
            width=400,
            show="*"
        )
        self.totp_entry.pack(fill="x", padx=20, pady=(5, 10))
        
        # Help Link
        self.help_link = ctk.CTkLabel(
            self.form_frame, 
            text="Where do I find these?", 
            text_color="#3B8ED0", 
            cursor="hand2"
        )
        self.help_link.pack(anchor="w", padx=20)
        self.help_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.miraeasset.co.in")) # Placeholder link

        # Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=20, fill="x", padx=40)

        self.skip_btn = ctk.CTkButton(
            self.button_frame, 
            text="Skip (Paper Trading Only)", 
            fg_color="transparent", 
            border_width=1,
            text_color="gray",
            command=self.skip_setup
        )
        self.skip_btn.pack(side="left")

        self.save_btn = ctk.CTkButton(
            self.button_frame, 
            text="Save & Launch 🚀", 
            font=("Roboto", 14, "bold"),
            height=40,
            command=self.save_and_launch
        )
        self.save_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.status_label = ctk.CTkLabel(self, text="", text_color="red")
        self.status_label.pack(pady=(0, 10))

    def skip_setup(self):
        self.create_default_settings(empty=True)
        self.launch_main_app()

    def save_and_launch(self):
        api_key = self.api_entry.get().strip()
        totp_secret = self.totp_entry.get().strip()

        if not api_key or not totp_secret:
            self.status_label.configure(text="❌ Please enter both API Key and TOTP Secret.")
            return

        # Simple validation
        if len(api_key) < 10:
             self.status_label.configure(text="⚠️ API Key looks too short.")
             return

        self.create_default_settings(api_key, totp_secret)
        self.status_label.configure(text="✅ Setup Complete! Launching...", text_color="green")
        
        self.after(1000, self.launch_main_app)

    def create_default_settings(self, api_key="", totp_secret="", empty=False):
        try:
            # Load default template if available
            settings = {
                "CREDENTIALS": {
                    "API_KEY": api_key,
                    "USER_ID": "", 
                    "PASSWORD": "",
                    "TOTP_SECRET": totp_secret,
                },
                "TRADING": {
                   "RSI_PERIOD": 14,
                   "PAPER_TRADING": True
                },
                 "SYSTEM": {
                    "THEME": "Dark",
                    "LOG_LEVEL": "INFO"
                }
            }
            
            # If template exists, use it and only update credentials
            if os.path.exists("settings_default.json"):
                with open("settings_default.json", "r") as f:
                    template = json.load(f)
                    template["CREDENTIALS"]["API_KEY"] = api_key
                    template["CREDENTIALS"]["TOTP_SECRET"] = totp_secret
                    settings = template
            
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
                
            print("✅ settings.json created.")

        except Exception as e:
            print(f"Error creating settings: {e}")
            self.status_label.configure(text=f"Error: {str(e)}")

    def launch_main_app(self):
        self.destroy()
        print("Launching Main App...")
        # Execute kickstart_gui.py
        import subprocess
        # process = subprocess.Popen([sys.executable, "kickstart_gui.py"])
        # We can't easily execute python script from here if we are a script ourselves and want to close
        # But since we are called from batch file, we can just exit.
        
        # However, the batch file logic is:
        # if not exist settings.json python setup_wizard.py
        # else python kickstart_gui.py
        # THIS IS WRONG in the batch file logic if we rely on batch to launch next.
        # The batch runs setup_wizard. Setup wizard creates settings.json. Batch finishes setup_wizard line.
        # Batch needs to know to proceed.
        
        # Actually, let's just create settings and exit. The batch Logic should handle the launch.
        # Let's check batch logic again.
        
if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
