#!/usr/bin/env python3
"""
Regime Settings Tab - Risk Profile and Regime Behavior Configuration
Part of Enhanced Settings GUI for MVP v1.0
"""

import sys
import os
# Add parent directory to path for standalone testing
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import customtkinter as ctk
from tkinter import messagebox
from settings_manager_v2 import SettingsManagerV2, RiskProfile

class RegimeSettingsTab(ctk.CTkFrame):
    """Tab for configuring risk profile and regime behaviors"""

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
            text="🎯 Risk Profile & Regime Behavior",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Description
        desc = ctk.CTkLabel(
            self,
            text="Choose how the bot responds to different market conditions",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        desc.pack(pady=(0, 20))

        # Risk Profile Selection
        self.create_risk_profile_section()

        # Regime Behavior Display
        self.create_regime_behavior_section()

    def create_risk_profile_section(self):
        """Create risk profile radio buttons"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="Select Risk Profile:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10)

        # Radio button variable
        self.risk_profile_var = ctk.StringVar(value=RiskProfile.CONSERVATIVE.value)

        # Conservative
        conservative = ctk.CTkRadioButton(
            frame,
            text="🛡️ CONSERVATIVE (Recommended) - Halts trading in CRISIS/BEARISH",
            variable=self.risk_profile_var,
            value=RiskProfile.CONSERVATIVE.value,
            command=self.on_risk_profile_changed
        )
        conservative.pack(pady=5, padx=20, anchor="w")

        # Moderate
        moderate = ctk.CTkRadioButton(
            frame,
            text="⚖️ MODERATE - Reduces position sizes in risky regimes",
            variable=self.risk_profile_var,
            value=RiskProfile.MODERATE.value,
            command=self.on_risk_profile_changed
        )
        moderate.pack(pady=5, padx=20, anchor="w")

        # Aggressive
        aggressive = ctk.CTkRadioButton(
            frame,
            text="🚀 AGGRESSIVE - Continues trading in all regimes",
            variable=self.risk_profile_var,
            value=RiskProfile.AGGRESSIVE.value,
            command=self.on_risk_profile_changed
        )
        aggressive.pack(pady=5, padx=20, anchor="w")

        # Custom (future feature)
        custom_btn = ctk.CTkButton(
            frame,
            text="⚙️ Customize Rules (Advanced)",
            command=self.show_custom_message,
            fg_color="gray",
            hover_color="darkgray"
        )
        custom_btn.pack(pady=10)

    def create_regime_behavior_section(self):
        """Display regime behaviors based on selected profile"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="How the Bot Will Behave:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10)

        # Table header
        header_frame = ctk.CTkFrame(frame)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            header_frame,
            text="Regime",
            font=ctk.CTkFont(weight="bold"),
            width=150
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            header_frame,
            text="Action",
            font=ctk.CTkFont(weight="bold"),
            width=150
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            header_frame,
            text="Position Size",
            font=ctk.CTkFont(weight="bold"),
            width=150
        ).pack(side="left", padx=10)

        # Regime rows (will be populated dynamically)
        self.regime_display_frame = ctk.CTkFrame(frame)
        self.regime_display_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.update_regime_display()

    def update_regime_display(self):
        """Update regime behavior display based on current profile"""
        # Clear existing rows
        for widget in self.regime_display_frame.winfo_children():
            widget.destroy()

        # Get current profile
        profile_name = self.risk_profile_var.get()
        profile = RiskProfile[profile_name]

        # Display behaviors for each regime
        regimes = ['CRISIS', 'BEARISH', 'VOLATILE', 'SIDEWAYS', 'BULLISH']

        for regime in regimes:
            behavior = self.settings.get_regime_behavior(regime)

            row_frame = ctk.CTkFrame(self.regime_display_frame)
            row_frame.pack(fill="x", pady=2)

            # Regime name
            ctk.CTkLabel(
                row_frame,
                text=regime,
                width=150,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)

            # Action with icon
            action = behavior['action']
            icon = {'HALT': '🔴', 'REDUCE': '🟡', 'CONTINUE': '🟢'}[action]

            ctk.CTkLabel(
                row_frame,
                text=f"{icon} {action}",
                width=150,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)

            # Position multiplier
            multiplier = behavior['position_multiplier']
            ctk.CTkLabel(
                row_frame,
                text=f"{multiplier:.0%}",
                width=150,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)

    def on_risk_profile_changed(self):
        """Handle risk profile change"""
        profile_name = self.risk_profile_var.get()
        profile = RiskProfile[profile_name]

        # Update settings
        self.settings.set_risk_profile(profile)
        self.settings.save()

        # Update display
        self.update_regime_display()

        # Show confirmation
        messagebox.showinfo(
            "Risk Profile Updated",
            f"Risk profile changed to {profile_name}.\n\n"
            "The bot will now follow the new regime behaviors."
        )

    def show_custom_message(self):
        """Show message for custom rules (future feature)"""
        messagebox.showinfo(
            "Coming Soon",
            "Custom regime rules will be available in a future update.\n\n"
            "For now, choose CONSERVATIVE, MODERATE, or AGGRESSIVE."
        )

    def load_current_settings(self):
        """Load current settings from SettingsManagerV2"""
        current_profile = self.settings.get_risk_profile()
        self.risk_profile_var.set(current_profile.value)
        self.update_regime_display()


# Test this tab standalone
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("Regime Settings Tab - Test")
    root.geometry("800x600")

    settings = SettingsManagerV2(settings_file="test_settings.json", auto_migrate=False)

    tab = RegimeSettingsTab(root, settings)
    tab.pack(fill="both", expand=True)

    root.mainloop()
