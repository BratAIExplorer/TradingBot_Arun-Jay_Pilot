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
        self.settings_mgr = SettingsManager()

        # Check if already accepted
        if self.settings_mgr.get("app_settings.disclaimer_accepted", False):
            self.on_accept()
            return

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("⚠️ Important Disclaimer")
        self.root.geometry("600x500")
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
        IMPORTANT: READ CAREFULLY

        1. NOT INVESTMENT ADVICE
        The ARUN Trading Bot ("Software") is a technical tool for algorithmic execution. It does not provide financial, investment, legal, or tax advice. You are solely responsible for configuring the strategy parameters (RSI, Profit Targets, etc.).

        2. HIGH RISK WARNING
        Trading in financial markets (Stocks, Options, Derivatives) involves a high degree of risk. You could lose some or all of your capital. Past performance of any strategy does not guarantee future results.

        3. SOFTWARE "AS IS"
        This Software is provided "AS IS", without warranty of any kind. The developers make no guarantees regarding uptime, bug-free operation, or profit generation. We are not liable for any financial losses incurred due to software errors, broker API failures, internet connectivity issues, or market volatility.

        4. USER RESPONSIBILITY
        By clicking "I ACCEPT", you acknowledge that:
        - You understand the risks of algorithmic trading.
        - You are using this tool at your own discretion.
        - You agree to test strategies in "Paper Trading" mode before risking real capital.
        """

        textbox = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 13))
        textbox.insert("0.0", disclaimer_text)
        textbox.configure(state="disabled")
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(pady=30)

        self.accept_btn = ctk.CTkButton(
            btn_frame,
            text="I ACCEPT & UNDERSTAND RISKS",
            command=self.accept,
            fg_color="#27AE60",
            hover_color="#1E8449",
            width=250,
            height=40,
            font=("Arial", 13, "bold")
        )
        self.accept_btn.grid(row=0, column=0, padx=10)

        self.decline_btn = ctk.CTkButton(
            btn_frame,
            text="DECLINE (EXIT)",
            command=self.decline,
            fg_color="#C0392B",
            hover_color="#922B21",
            width=150,
            height=40
        )
        self.decline_btn.grid(row=0, column=1, padx=10)

    def accept(self):
        self.settings_mgr.set("app_settings.disclaimer_accepted", True)
        self.root.destroy()
        self.on_accept()

    def decline(self):
        sys.exit(0)

if __name__ == "__main__":
    # Test run
    def start_app():
        print("Disclaimer Accepted - Starting App...")

    DisclaimerGUI(start_app)
