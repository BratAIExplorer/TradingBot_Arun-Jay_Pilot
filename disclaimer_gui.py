"""
Disclaimer GUI for ARUN Trading Bot
Forces user to accept terms before proceeding.
"""

import customtkinter as ctk
from settings_manager import SettingsManager
import sys

class DisclaimerGUI:
    def __init__(self, on_accept_callback):
        self.on_accept = on_accept_callback
        
        # ALWAYS show disclaimer on every launch for legal protection
        # (Removed the settings check that skipped it after first acceptance)
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("⚠️ Important Disclaimer")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (600 // 2)
        y = (screen_height // 2) - (500 // 2)
        self.root.geometry(f"+{x}+{y}")

        self.build_ui()
        self.root.mainloop()

    def build_ui(self):
        # Icon/Header
        header = ctk.CTkLabel(
            self.root,
            text="⚠️ ARUN TRADING BOT",
            font=("Arial", 24, "bold"),
            text_color="#E74C3C"
        )
        header.pack(pady=(30, 10))

        subheader = ctk.CTkLabel(
            self.root,
            text="User Responsibility Agreement",
            font=("Arial", 16)
        )
        subheader.pack(pady=(0, 20))

        # Scrollable Text
        text_frame = ctk.CTkFrame(self.root, fg_color="#2B2B2B")
        text_frame.pack(fill="both", expand=True, padx=30, pady=10)

        disclaimer_text = """
        ⚠️ CRITICAL WARNING - READ BEFORE PROCEEDING ⚠️

        1. NOT FINANCIAL ADVICE
        The ARUN Trading Bot is a SOFTWARE TOOL ONLY. It does NOT provide investment, financial, legal, or tax advice. You are solely responsible for:
        • Configuring all strategy parameters
        • Deciding which stocks to trade
        • Determining position sizes and risk levels
        
        2. HIGH RISK - POTENTIAL TOTAL LOSS
        Trading stocks and derivatives involves significant risk. You could lose SOME or ALL of your invested capital. Past performance does NOT guarantee future results.
        
        3. USER RESPONSIBILITY & LIABILITY
        By using this software, you acknowledge:
        • YOU are responsible for all trading decisions
        • YOU accept full liability for any profits OR losses
        • The developers are NOT liable for any financial losses
        • Software bugs, API failures, or connectivity issues may occur
        
        4. SOFTWARE PROVIDED "AS IS"
        No warranties of any kind. No guarantees of uptime, accuracy, or profitability.
        
        5. PAPER TRADING FIRST
        You MUST test your strategies in "Paper Trading" mode before risking real money.
        
        By clicking "I ACCEPT", you confirm you understand these risks and accept full responsibility for your trading activities.
        """

        textbox = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 12))
        textbox.insert("0.0", disclaimer_text)
        textbox.configure(state="disabled")
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.accept_btn = ctk.CTkButton(
            btn_frame,
            text="I ACCEPT & UNDERSTAND RISKS",
            command=self.accept,
            fg_color="#27AE60",
            hover_color="#1E8449",
            width=280,
            height=45,
            font=("Arial", 14, "bold")
        )
        self.accept_btn.grid(row=0, column=0, padx=10)

        self.decline_btn = ctk.CTkButton(
            btn_frame,
            text="DECLINE (EXIT)",
            command=self.decline,
            fg_color="#C0392B",
            hover_color="#922B21",
            width=150,
            height=45,
            font=("Arial", 12, "bold")
        )
        self.decline_btn.grid(row=0, column=1, padx=10)

    def accept(self):
        # Remove settings save - just proceed to app
        self.root.destroy()
        self.on_accept()

    def decline(self):
        sys.exit(0)

if __name__ == "__main__":
    # Test run
    def start_app():
        print("Disclaimer Accepted - Starting App...")

    DisclaimerGUI(start_app)
