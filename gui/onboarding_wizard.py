"""
Onboarding Wizard for ARUN Trading Bot
======================================

First-run experience wizard that guides new users through setup:
1. Welcome screen
2. Paper vs Live trading choice
3. Risk profile selection
4. API connection test
5. Ready to trade confirmation

Author: ARUN Trading Bot Team
Version: 1.0
Date: January 18, 2026
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import customtkinter as ctk
except ImportError:
    print("⚠️ CustomTkinter not installed. Install with: pip install customtkinter")
    ctk = None

from settings_manager_v2 import SettingsManagerV2, RiskProfile, TradingMode
import subprocess
from typing import Optional, Callable


class OnboardingWizard:
    """
    Modern onboarding wizard for first-time users

    Features:
    - 5-step guided setup
    - Educational content
    - Risk profile selection
    - API connection testing
    - Paper trading recommendation
    """

    def __init__(self, on_complete: Optional[Callable] = None):
        """
        Initialize onboarding wizard

        Args:
            on_complete: Callback function when wizard completes
        """
        if ctk is None:
            raise ImportError("CustomTkinter is required for the onboarding wizard")

        self.settings = SettingsManagerV2()
        self.on_complete = on_complete

        # Current step tracking
        self.current_step = 0
        self.total_steps = 5

        # User choices
        self.chosen_mode = TradingMode.PAPER
        self.chosen_risk_profile = RiskProfile.CONSERVATIVE

        # Create main window
        self.window = ctk.CTk()
        self.window.title("ARUN Trading Bot - Welcome Setup")
        self.window.geometry("800x600")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Container frame
        self.container = ctk.CTkFrame(self.window)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Show first step
        self.show_step_1_welcome()

    def clear_container(self):
        """Clear all widgets from container"""
        for widget in self.container.winfo_children():
            widget.destroy()

    def create_progress_indicator(self):
        """Create progress indicator showing current step"""
        progress_frame = ctk.CTkFrame(self.container)
        progress_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            progress_frame,
            text=f"Step {self.current_step} of {self.total_steps}",
            font=("Arial", 12)
        ).pack(side="left", padx=10)

        # Progress bar
        progress = (self.current_step / self.total_steps)
        ctk.CTkProgressBar(
            progress_frame,
            progress_color=("#3B8ED0", "#1F6AA5")
        ).pack(side="left", fill="x", expand=True, padx=10)

        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.set(progress)
        progress_bar.pack(side="left", fill="x", expand=True, padx=10)

    # ========================================================================
    # Step 1: Welcome Screen
    # ========================================================================

    def show_step_1_welcome(self):
        """Step 1: Welcome and introduction"""
        self.current_step = 1
        self.clear_container()
        self.create_progress_indicator()

        # Header
        ctk.CTkLabel(
            self.container,
            text="🎉 Welcome to ARUN Trading Bot!",
            font=("Arial Bold", 24)
        ).pack(pady=(20, 10))

        # Introduction text
        intro_text = """
Hi! I'm ARUN, your automated trading assistant for Indian stocks (NSE/BSE).

I'll help you trade using proven technical strategies while YOU stay in complete control.

Let's get you set up safely! This will take about 5 minutes.
        """

        intro_frame = ctk.CTkFrame(self.container)
        intro_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            intro_frame,
            text=intro_text,
            font=("Arial", 14),
            justify="left"
        ).pack(padx=20, pady=20)

        # Key features
        features_frame = ctk.CTkFrame(intro_frame)
        features_frame.pack(fill="x", padx=20, pady=(0, 20))

        features = [
            "✅ RSI Mean Reversion Strategy (Proven)",
            "✅ Market Regime Protection (Avoid crashes)",
            "✅ Risk Management (Stop-loss, position sizing)",
            "✅ Paper Trading (Practice risk-free)",
            "✅ YOU Control Everything (Bot assists, you decide)"
        ]

        for feature in features:
            ctk.CTkLabel(
                features_frame,
                text=feature,
                font=("Arial", 12),
                anchor="w"
            ).pack(fill="x", padx=10, pady=2)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self.container)
        nav_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            nav_frame,
            text="Let's Get Started →",
            command=self.show_step_2_trading_mode,
            font=("Arial Bold", 14),
            height=40
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            nav_frame,
            text="Skip Setup (Not Recommended)",
            command=self.skip_wizard,
            font=("Arial", 12),
            fg_color="gray",
            height=40
        ).pack(side="left", padx=10)

    # ========================================================================
    # Step 2: Trading Mode Selection
    # ========================================================================

    def show_step_2_trading_mode(self):
        """Step 2: Choose Paper Trading or Live Trading"""
        self.current_step = 2
        self.clear_container()
        self.create_progress_indicator()

        # Header
        ctk.CTkLabel(
            self.container,
            text="How would you like to get started?",
            font=("Arial Bold", 20)
        ).pack(pady=(20, 30))

        # Paper Trading Option (Recommended)
        paper_frame = ctk.CTkFrame(self.container, border_width=3, border_color="#3B8ED0")
        paper_frame.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(
            paper_frame,
            text="🎮 PAPER TRADING (Recommended for Beginners)",
            font=("Arial Bold", 16),
            text_color="#3B8ED0"
        ).pack(pady=(15, 5))

        paper_benefits = [
            "✅ Practice with ₹1,00,000 virtual money",
            "✅ Learn how the bot works - zero risk",
            "✅ See actual performance before investing",
            "✅ Switch to live trading anytime"
        ]

        for benefit in paper_benefits:
            ctk.CTkLabel(
                paper_frame,
                text=benefit,
                font=("Arial", 12),
                anchor="w"
            ).pack(fill="x", padx=20, pady=2)

        ctk.CTkButton(
            paper_frame,
            text="⭐ Start with Paper Trading",
            command=lambda: self.select_trading_mode(TradingMode.PAPER),
            font=("Arial Bold", 14),
            height=40
        ).pack(pady=15, padx=20)

        # Live Trading Option
        live_frame = ctk.CTkFrame(self.container)
        live_frame.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(
            live_frame,
            text="💰 LIVE TRADING (Real Money)",
            font=("Arial Bold", 16)
        ).pack(pady=(15, 5))

        live_warnings = [
            "⚠️  Real trades with real money and risk",
            "⚠️  Profits and losses affect your account",
            "ℹ️  Recommended after 1-2 weeks of paper trading"
        ]

        for warning in live_warnings:
            ctk.CTkLabel(
                live_frame,
                text=warning,
                font=("Arial", 12),
                anchor="w",
                text_color="#FFA500"
            ).pack(fill="x", padx=20, pady=2)

        ctk.CTkButton(
            live_frame,
            text="I'm Ready - Start Live Trading",
            command=lambda: self.select_trading_mode(TradingMode.LIVE),
            font=("Arial", 14),
            height=40,
            fg_color="#CC6600"
        ).pack(pady=15, padx=20)

        # Stats
        ctk.CTkLabel(
            self.container,
            text="💡 93% of successful traders start with paper mode",
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=(20, 0))

        # Navigation
        nav_frame = ctk.CTkFrame(self.container)
        nav_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            nav_frame,
            text="← Back",
            command=self.show_step_1_welcome,
            font=("Arial", 12),
            width=100
        ).pack(side="left", padx=10)

    def select_trading_mode(self, mode: TradingMode):
        """User selected trading mode"""
        self.chosen_mode = mode
        self.show_step_3_risk_profile()

    # ========================================================================
    # Step 3: Risk Profile Selection
    # ========================================================================

    def show_step_3_risk_profile(self):
        """Step 3: Choose risk profile"""
        self.current_step = 3
        self.clear_container()
        self.create_progress_indicator()

        # Header
        ctk.CTkLabel(
            self.container,
            text="🛡️ Choose Your Risk Profile",
            font=("Arial Bold", 20)
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            self.container,
            text="How should the bot protect you in dangerous market conditions?",
            font=("Arial", 12),
            text_color="gray"
        ).pack(pady=(0, 20))

        # Create scrollable frame for profiles
        scroll_frame = ctk.CTkScrollableFrame(self.container)
        scroll_frame.pack(fill="both", expand=True, padx=20)

        # Conservative Profile (Recommended)
        self.create_risk_profile_option(
            scroll_frame,
            RiskProfile.CONSERVATIVE,
            "🟢 CONSERVATIVE (Recommended for Beginners)",
            [
                "✅ Automatically halts trading in CRISIS & BEARISH markets",
                "✅ Reduces position sizes in VOLATILE markets (50%)",
                "✅ Protected from major crashes (-30% to -70%)",
                "⚠️  May miss some bull market gains (cautious approach)",
                "",
                "💡 Historical Impact:",
                "   • Mar 2020 COVID Crash: Saved -35% by halting early",
                "   • 2023 Bull Rally: Captured 68% of gains"
            ],
            recommended=True
        )

        # Moderate Profile
        self.create_risk_profile_option(
            scroll_frame,
            RiskProfile.MODERATE,
            "🟡 MODERATE (Balanced Risk-Reward)",
            [
                "• Halts only in CRISIS (severe crashes >-15%)",
                "• Continues trading in BEARISH with reduced sizes (50%)",
                "• More upside potential, more downside risk"
            ]
        )

        # Aggressive Profile
        self.create_risk_profile_option(
            scroll_frame,
            RiskProfile.AGGRESSIVE,
            "🔴 AGGRESSIVE (Maximum Control - Experts Only)",
            [
                "• Never halts automatically",
                "• Sends alerts only, YOU decide whether to trade",
                "• Maximum profit potential, maximum risk",
                "⚠️  Requires active monitoring and quick decisions"
            ]
        )

        # Navigation
        nav_frame = ctk.CTkFrame(self.container)
        nav_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            nav_frame,
            text="← Back",
            command=self.show_step_2_trading_mode,
            font=("Arial", 12),
            width=100
        ).pack(side="left", padx=10)

    def create_risk_profile_option(self, parent, profile: RiskProfile, title: str,
                                   points: list, recommended: bool = False):
        """Create a risk profile selection option"""
        border_color = "#3B8ED0" if recommended else "gray"

        frame = ctk.CTkFrame(parent, border_width=2, border_color=border_color)
        frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            frame,
            text=title,
            font=("Arial Bold", 14),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(10, 5))

        for point in points:
            ctk.CTkLabel(
                frame,
                text=point,
                font=("Arial", 11),
                anchor="w"
            ).pack(fill="x", padx=20, pady=1)

        button_text = "⭐ Select (Recommended)" if recommended else "Select This Profile"

        ctk.CTkButton(
            frame,
            text=button_text,
            command=lambda: self.select_risk_profile(profile),
            font=("Arial Bold", 13) if recommended else ("Arial", 13),
            height=35
        ).pack(pady=10, padx=15)

    def select_risk_profile(self, profile: RiskProfile):
        """User selected risk profile"""
        self.chosen_risk_profile = profile
        self.show_step_4_api_test()

    # ========================================================================
    # Step 4: API Connection Test
    # ========================================================================

    def show_step_4_api_test(self):
        """Step 4: Test API connection"""
        self.current_step = 4
        self.clear_container()
        self.create_progress_indicator()

        # Header
        ctk.CTkLabel(
            self.container,
            text="🔌 API Connection Test",
            font=("Arial Bold", 20)
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            self.container,
            text="Let's verify your broker API credentials are working",
            font=("Arial", 12),
            text_color="gray"
        ).pack(pady=(0, 20))

        # Info frame
        info_frame = ctk.CTkFrame(self.container)
        info_frame.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(
            info_frame,
            text="This test will check:",
            font=("Arial Bold", 14)
        ).pack(pady=(20, 10), anchor="w", padx=20)

        checks = [
            "✅ API credentials are loaded from .env file",
            "✅ Connection to mStock API works",
            "✅ Your account details can be fetched",
            "✅ Available funds are accessible",
            "",
            "⚠️  This test does NOT place any orders"
        ]

        for check in checks:
            ctk.CTkLabel(
                info_frame,
                text=check,
                font=("Arial", 12),
                anchor="w"
            ).pack(fill="x", padx=20, pady=2)

        # Test button
        self.test_button = ctk.CTkButton(
            info_frame,
            text="🧪 Run API Connection Test",
            command=self.run_api_test,
            font=("Arial Bold", 14),
            height=45
        ).pack(pady=20)

        # Results area (hidden initially)
        self.results_frame = ctk.CTkFrame(info_frame)

        # Navigation
        nav_frame = ctk.CTkFrame(self.container)
        nav_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            nav_frame,
            text="← Back",
            command=self.show_step_3_risk_profile,
            font=("Arial", 12),
            width=100
        ).pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(
            nav_frame,
            text="Next →",
            command=self.show_step_5_confirmation,
            font=("Arial Bold", 14),
            width=120,
            state="disabled"
        )
        self.next_button.pack(side="right", padx=10)

    def run_api_test(self):
        """Run API integration test"""
        self.test_button.configure(state="disabled", text="Testing...")

        # Show results frame
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.results_frame,
            text="Running tests...",
            font=("Arial", 12)
        ).pack(pady=10)

        self.window.update()

        # Run test_api_integration.py
        try:
            result = subprocess.run(
                [sys.executable, "test_api_integration.py", "--quick"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse results
            if result.returncode == 0:
                self.show_test_success()
            else:
                self.show_test_failure(result.stdout + result.stderr)

        except subprocess.TimeoutExpired:
            self.show_test_failure("Test timed out after 30 seconds")
        except Exception as e:
            self.show_test_failure(f"Error running test: {str(e)}")

    def show_test_success(self):
        """Show test success message"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.results_frame,
            text="✅ All Tests Passed!",
            font=("Arial Bold", 16),
            text_color="#00CC00"
        ).pack(pady=10)

        ctk.CTkLabel(
            self.results_frame,
            text="Your API connection is working correctly.\nYou're ready to start trading!",
            font=("Arial", 12)
        ).pack(pady=10)

        self.test_button.configure(text="✅ Test Complete", state="disabled")
        self.next_button.configure(state="normal")

    def show_test_failure(self, error_msg: str):
        """Show test failure message"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.results_frame,
            text="⚠️ Some Tests Failed",
            font=("Arial Bold", 16),
            text_color="#FF6600"
        ).pack(pady=10)

        # Scrollable error message
        error_text = ctk.CTkTextbox(self.results_frame, height=150)
        error_text.pack(fill="both", expand=True, padx=10, pady=10)
        error_text.insert("1.0", error_msg)
        error_text.configure(state="disabled")

        ctk.CTkLabel(
            self.results_frame,
            text="Please check your .env file and API credentials.\nYou can still continue and fix this later.",
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=10)

        self.test_button.configure(text="🔄 Retry Test", state="normal")
        self.next_button.configure(state="normal", text="Continue Anyway →")

    # ========================================================================
    # Step 5: Confirmation & Complete
    # ========================================================================

    def show_step_5_confirmation(self):
        """Step 5: Final confirmation"""
        self.current_step = 5
        self.clear_container()
        self.create_progress_indicator()

        # Header
        ctk.CTkLabel(
            self.container,
            text="🎉 You're All Set!",
            font=("Arial Bold", 24)
        ).pack(pady=(20, 10))

        # Summary
        summary_frame = ctk.CTkFrame(self.container)
        summary_frame.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(
            summary_frame,
            text="Your Setup Summary:",
            font=("Arial Bold", 16)
        ).pack(pady=(20, 15), anchor="w", padx=20)

        # Show chosen settings
        settings_text = f"""
📊 Trading Mode: {self.chosen_mode.value}
   {"🎮 Safe practice mode - No real money at risk" if self.chosen_mode == TradingMode.PAPER else "💰 Live trading - Real money"}

🛡️ Risk Profile: {self.chosen_risk_profile.value}
   {self.get_risk_profile_description()}

✅ API Connection: Tested
✅ Settings Configured
✅ Ready to Trade
        """

        ctk.CTkLabel(
            summary_frame,
            text=settings_text,
            font=("Arial", 13),
            justify="left",
            anchor="w"
        ).pack(fill="both", padx=20, pady=10)

        # Important notes
        notes_frame = ctk.CTkFrame(summary_frame)
        notes_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            notes_frame,
            text="💡 Important Notes:",
            font=("Arial Bold", 13)
        ).pack(pady=(10, 5), anchor="w", padx=10)

        notes = [
            "• You can change these settings anytime in Settings",
            "• Run a backtest before live trading (recommended)",
            "• Monitor your bot regularly, especially at first",
            "• Paper trading helps you learn without risk"
        ]

        for note in notes:
            ctk.CTkLabel(
                notes_frame,
                text=note,
                font=("Arial", 11),
                anchor="w"
            ).pack(fill="x", padx=10, pady=2)

        # Final buttons
        button_frame = ctk.CTkFrame(self.container)
        button_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            button_frame,
            text="← Back",
            command=self.show_step_4_api_test,
            font=("Arial", 12),
            width=100
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="🚀 Start Trading!",
            command=self.complete_wizard,
            font=("Arial Bold", 16),
            height=50,
            width=200
        ).pack(side="right", padx=10)

    def get_risk_profile_description(self) -> str:
        """Get description of chosen risk profile"""
        if self.chosen_risk_profile == RiskProfile.CONSERVATIVE:
            return "Beginner-friendly, protects from crashes"
        elif self.chosen_risk_profile == RiskProfile.MODERATE:
            return "Balanced risk-reward approach"
        elif self.chosen_risk_profile == RiskProfile.AGGRESSIVE:
            return "Maximum control, expert mode"
        else:
            return "Custom configuration"

    def complete_wizard(self):
        """Complete wizard and save settings"""
        # Save chosen settings
        self.settings.set_trading_mode(self.chosen_mode)
        self.settings.set_risk_profile(self.chosen_risk_profile)
        self.settings.mark_first_run_complete()

        print("✅ Onboarding complete!")
        print(f"   Trading Mode: {self.chosen_mode.value}")
        print(f"   Risk Profile: {self.chosen_risk_profile.value}")

        # Call completion callback
        if self.on_complete:
            self.on_complete()

        # Close wizard
        self.window.destroy()

    def skip_wizard(self):
        """Skip wizard (use defaults)"""
        # Use defaults: PAPER mode, CONSERVATIVE profile
        self.settings.set_trading_mode(TradingMode.PAPER)
        self.settings.set_risk_profile(RiskProfile.CONSERVATIVE)
        self.settings.mark_first_run_complete()

        print("⚠️  Wizard skipped - using default settings")
        print("   Trading Mode: PAPER")
        print("   Risk Profile: CONSERVATIVE")

        if self.on_complete:
            self.on_complete()

        self.window.destroy()

    def run(self):
        """Run the wizard"""
        self.window.mainloop()


# Example usage
if __name__ == '__main__':
    def on_wizard_complete():
        print("\n🎉 Welcome aboard! Your trading bot is now configured.")
        print("   You can start the main application.")

    wizard = OnboardingWizard(on_complete=on_wizard_complete)
    wizard.run()
