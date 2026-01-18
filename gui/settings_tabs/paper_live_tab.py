#!/usr/bin/env python3
"""
Paper/Live Trading Tab - Switch Between Paper and Live Trading
Part of Enhanced Settings GUI for MVP v1.0
"""

import sys
import os
# Add parent directory to path for standalone testing
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import customtkinter as ctk
from tkinter import messagebox
from settings_manager_v2 import SettingsManagerV2, TradingMode

class PaperLiveTab(ctk.CTkFrame):
    """Tab for switching between paper and live trading"""

    def __init__(self, parent, settings: SettingsManagerV2):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        """Build the UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="🎮 Trading Mode",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Current mode display (big and prominent)
        self.create_mode_display()

        # Mode toggle buttons
        self.create_mode_toggle()

        # Additional settings
        self.create_additional_settings()

    def create_mode_display(self):
        """Create prominent current mode display"""
        self.mode_display_frame = ctk.CTkFrame(self, height=150)
        self.mode_display_frame.pack(fill="x", padx=20, pady=10)

        self.mode_label = ctk.CTkLabel(
            self.mode_display_frame,
            text="",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.mode_label.pack(pady=20)

        self.mode_desc = ctk.CTkLabel(
            self.mode_display_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.mode_desc.pack(pady=(0, 20))

        self.update_mode_display()

    def update_mode_display(self):
        """Update mode display based on current mode"""
        current_mode = self.settings.get_trading_mode()

        if current_mode == TradingMode.PAPER:
            self.mode_display_frame.configure(border_color="#3B8ED0", border_width=3)
            self.mode_label.configure(
                text="📝 PAPER TRADING MODE",
                text_color="#3B8ED0"
            )
            self.mode_desc.configure(
                text="Trading with virtual money - No real money at risk",
                text_color="lightgray"
            )
        else:
            self.mode_display_frame.configure(border_color="red", border_width=3)
            self.mode_label.configure(
                text="🔴 LIVE TRADING MODE",
                text_color="red"
            )
            self.mode_desc.configure(
                text="⚠️ DANGER: Trading with REAL money!",
                text_color="orange"
            )

    def create_mode_toggle(self):
        """Create mode toggle buttons"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=20)

        label = ctk.CTkLabel(
            frame,
            text="Switch Trading Mode:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10)

        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(pady=10)

        # Paper Trading Button
        paper_btn = ctk.CTkButton(
            button_frame,
            text="📝 Switch to PAPER Trading\n(Virtual Money - Safe)",
            width=250,
            height=80,
            font=ctk.CTkFont(size=14),
            fg_color="#3B8ED0",
            hover_color="#2E7AB8",
            command=lambda: self.switch_mode(TradingMode.PAPER)
        )
        paper_btn.pack(side="left", padx=10)

        # Live Trading Button
        live_btn = ctk.CTkButton(
            button_frame,
            text="🔴 Switch to LIVE Trading\n⚠️ REAL MONEY - DANGER",
            width=250,
            height=80,
            font=ctk.CTkFont(size=14),
            fg_color="red",
            hover_color="darkred",
            command=lambda: self.switch_mode(TradingMode.LIVE)
        )
        live_btn.pack(side="left", padx=10)

    def create_additional_settings(self):
        """Create additional settings"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="Additional Settings:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10)

        # Show mode banner checkbox
        self.banner_var = ctk.BooleanVar(value=True)

        banner_check = ctk.CTkCheckBox(
            frame,
            text="Show trading mode banner on main screen",
            variable=self.banner_var,
            command=self.save_banner_setting,
            font=ctk.CTkFont(size=12)
        )
        banner_check.pack(pady=5)

        # Paper trading balance (display only)
        if self.settings.is_paper_trading():
            balance_frame = ctk.CTkFrame(frame)
            balance_frame.pack(pady=10)

            ctk.CTkLabel(
                balance_frame,
                text="Virtual Trading Balance:",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="left", padx=10)

            balance = self.settings.get('capital.total_capital', 100000)
            ctk.CTkLabel(
                balance_frame,
                text=f"₹{balance:,.0f}",
                font=ctk.CTkFont(size=14),
                text_color="#3B8ED0"
            ).pack(side="left", padx=10)

    def switch_mode(self, new_mode: TradingMode):
        """Switch trading mode with confirmation"""
        current_mode = self.settings.get_trading_mode()

        if current_mode == new_mode:
            messagebox.showinfo(
                "Already in This Mode",
                f"You are already in {new_mode.value} trading mode."
            )
            return

        if new_mode == TradingMode.LIVE:
            # Show serious warning for live trading
            response = messagebox.askyesno(
                "⚠️ DANGER: LIVE TRADING MODE",
                "You are about to switch to LIVE TRADING mode.\n\n"
                "This means:\n"
                "• All trades will use REAL MONEY from your broker account\n"
                "• Losses will be REAL losses from your account\n"
                "• There is NO undo button\n\n"
                "Are you ABSOLUTELY SURE you want to enable live trading?\n\n"
                "We recommend staying in Paper Trading mode until you are confident.",
                icon="warning"
            )
            if not response:
                return

            # Second confirmation
            response2 = messagebox.askyesno(
                "⚠️ FINAL WARNING",
                "This is your FINAL WARNING.\n\n"
                "Switching to LIVE mode will enable REAL MONEY trading.\n\n"
                "Click YES only if you:\n"
                "✅ Have tested the bot thoroughly in paper trading mode\n"
                "✅ Understand all the risks involved\n"
                "✅ Are ready to trade with real money\n\n"
                "Proceed to LIVE trading?",
                icon="warning"
            )
            if not response2:
                return
        else:
            # Switching to paper trading (safe)
            response = messagebox.askyesno(
                "Switch to Paper Trading?",
                "Switch to Paper Trading mode?\n\n"
                "You will trade with virtual money (no real money at risk).\n\n"
                "This is the safe way to practice and test strategies.",
                icon="question"
            )
            if not response:
                return

        # Switch mode
        self.settings.set_trading_mode(new_mode)
        self.settings.save()

        # Update UI
        self.update_mode_display()

        # Show confirmation
        if new_mode == TradingMode.PAPER:
            messagebox.showinfo(
                "✅ Switched to Paper Trading",
                "You are now in PAPER TRADING mode.\n\n"
                "All trades will use virtual money.\n"
                "Your real money is safe!"
            )
        else:
            messagebox.showwarning(
                "⚠️ LIVE Trading Enabled",
                "LIVE TRADING mode is now ACTIVE.\n\n"
                "All trades will use REAL MONEY.\n\n"
                "Trade carefully and monitor your positions!"
            )

    def save_banner_setting(self):
        """Save banner setting"""
        show_banner = self.banner_var.get()
        self.settings.set('trading_mode.show_mode_banner', show_banner)
        self.settings.save()

    def load_current_settings(self):
        """Load current settings"""
        show_banner = self.settings.get('trading_mode.show_mode_banner', True)
        self.banner_var.set(show_banner)

        self.update_mode_display()


# Test this tab standalone
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("Paper/Live Trading Tab - Test")
    root.geometry("700x600")

    settings = SettingsManagerV2(settings_file="test_settings.json", auto_migrate=False)

    tab = PaperLiveTab(root, settings)
    tab.pack(fill="both", expand=True)

    root.mainloop()
