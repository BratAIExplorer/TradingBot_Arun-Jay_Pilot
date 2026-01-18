#!/usr/bin/env python3
"""
Regime Alert Dialog - Smart Alerts for Market Regime Changes
=============================================================

Shows user-friendly alerts when:
- Market regime changes (BULLISH → BEARISH, etc.)
- Trading is halted due to regime
- User attempts to trade when halted
- Override is about to expire

Part of MVP v1.0 - Week 1 Foundation

Author: Claude AI (Anthropic)
Date: January 18, 2026
"""

try:
    import customtkinter as ctk
    from tkinter import messagebox
    CTK_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: CustomTkinter not installed. Install with: pip install customtkinter")
    CTK_AVAILABLE = False
    ctk = None
    messagebox = None

from typing import Optional, Callable
from datetime import datetime


class RegimeAlertDialog:
    """
    Smart dialog for regime-related alerts
    """

    REGIME_INFO = {
        'CRISIS': {
            'emoji': '🚨',
            'title': 'CRISIS Market Regime',
            'color': '#8B0000',
            'description': 'Market is in severe distress with high volatility and sharp declines.',
            'recommendation': 'It is strongly recommended to halt all new trading until conditions improve.'
        },
        'BEARISH': {
            'emoji': '🐻',
            'title': 'BEARISH Market Regime',
            'color': '#DC143C',
            'description': 'Market is trending downward with negative momentum.',
            'recommendation': 'Consider reducing position sizes or halting new trades.'
        },
        'VOLATILE': {
            'emoji': '⚡',
            'title': 'VOLATILE Market Regime',
            'color': '#FF8C00',
            'description': 'Market is experiencing high volatility and choppy price action.',
            'recommendation': 'Trade with caution and consider smaller position sizes.'
        },
        'SIDEWAYS': {
            'emoji': '➡️',
            'title': 'SIDEWAYS Market Regime',
            'color': '#4682B4',
            'description': 'Market is range-bound with no clear trend.',
            'recommendation': 'Normal trading conditions. Watch for breakouts.'
        },
        'BULLISH': {
            'emoji': '🐂',
            'title': 'BULLISH Market Regime',
            'color': '#228B22',
            'description': 'Market is trending upward with positive momentum.',
            'recommendation': 'Favorable conditions for trading with trend-following strategies.'
        }
    }

    @staticmethod
    def show_regime_change_alert(
        old_regime: str,
        new_regime: str,
        new_action: str,
        position_multiplier: float,
        risk_profile: str
    ) -> bool:
        """
        Show alert when market regime changes

        Args:
            old_regime: Previous regime
            new_regime: New regime
            new_action: New trading action (CONTINUE, REDUCE, HALT)
            position_multiplier: New position size multiplier
            risk_profile: User's risk profile

        Returns:
            True if user acknowledged
        """
        if not CTK_AVAILABLE:
            print(f"Regime changed: {old_regime} → {new_regime}")
            return True

        info = RegimeAlertDialog.REGIME_INFO.get(new_regime, RegimeAlertDialog.REGIME_INFO['SIDEWAYS'])

        # Create custom dialog
        dialog = ctk.CTkToplevel()
        dialog.title("Market Regime Change")
        dialog.geometry("500x400")
        dialog.transient()
        dialog.grab_set()

        # Header with color
        header = ctk.CTkFrame(dialog, fg_color=info['color'], corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=f"{info['emoji']} {info['title']}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(pady=15)

        # Content frame
        content = ctk.CTkFrame(dialog)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Regime change
        change_label = ctk.CTkLabel(
            content,
            text=f"Market regime changed from {old_regime} to {new_regime}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        change_label.pack(pady=(10, 5))

        # Description
        desc_label = ctk.CTkLabel(
            content,
            text=info['description'],
            font=ctk.CTkFont(size=12),
            wraplength=400
        )
        desc_label.pack(pady=(0, 15))

        # Action being taken
        action_frame = ctk.CTkFrame(content)
        action_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            action_frame,
            text=f"📋 Action per {risk_profile} risk profile:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))

        if new_action == "HALT":
            action_text = "🛑 Trading HALTED - No new positions will be opened"
            action_color = "red"
        elif new_action == "REDUCE":
            action_text = f"⚠️ Position sizes REDUCED to {position_multiplier:.0%} of normal"
            action_color = "orange"
        else:
            action_text = "✅ Trading continues normally"
            action_color = "green"

        ctk.CTkLabel(
            action_frame,
            text=action_text,
            font=ctk.CTkFont(size=13),
            text_color=action_color
        ).pack(pady=(0, 10))

        # Recommendation
        rec_label = ctk.CTkLabel(
            content,
            text=f"💡 Recommendation: {info['recommendation']}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=400
        )
        rec_label.pack(pady=(10, 0))

        # OK button
        result = [False]

        def on_ok():
            result[0] = True
            dialog.destroy()

        ok_btn = ctk.CTkButton(
            dialog,
            text="OK, I Understand",
            command=on_ok,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        ok_btn.pack(pady=20)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.wait_window()
        return result[0]

    @staticmethod
    def show_trading_halted_alert(
        regime: str,
        risk_profile: str,
        can_override: bool
    ) -> Optional[str]:
        """
        Show alert when user tries to trade but trading is halted

        Args:
            regime: Current regime
            risk_profile: User's risk profile
            can_override: Whether user can override the halt

        Returns:
            'override' if user wants to override, None otherwise
        """
        if not CTK_AVAILABLE:
            response = input("Trading is halted. Override? (y/n): ")
            return 'override' if response.lower() == 'y' else None

        info = RegimeAlertDialog.REGIME_INFO.get(regime, RegimeAlertDialog.REGIME_INFO['SIDEWAYS'])

        # Create dialog
        dialog = ctk.CTkToplevel()
        dialog.title("Trading Halted")
        dialog.geometry("500x450")
        dialog.transient()
        dialog.grab_set()

        # Header
        header = ctk.CTkFrame(dialog, fg_color=info['color'], corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=f"🛑 Trading Halted",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(pady=15)

        # Content
        content = ctk.CTkFrame(dialog)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Message
        ctk.CTkLabel(
            content,
            text=f"Trading is currently halted due to {regime} market regime.",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            content,
            text=f"Your {risk_profile} risk profile prevents new trades in this regime.",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 15))

        # Regime info
        info_frame = ctk.CTkFrame(content)
        info_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            info_frame,
            text=f"{info['emoji']} {info['description']}",
            font=ctk.CTkFont(size=12),
            wraplength=400
        ).pack(pady=10)

        # Recommendation
        ctk.CTkLabel(
            content,
            text=f"💡 {info['recommendation']}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=400
        ).pack(pady=(10, 15))

        result = [None]

        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)

        def on_cancel():
            result[0] = None
            dialog.destroy()

        def on_override():
            result[0] = 'override'
            dialog.destroy()

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="OK, Don't Trade",
            command=on_cancel,
            width=150,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="left", padx=10)

        # Override button (only if allowed)
        if can_override:
            override_btn = ctk.CTkButton(
                button_frame,
                text="🔓 Override (24h)",
                command=on_override,
                width=150,
                height=40,
                fg_color="orange",
                hover_color="darkorange"
            )
            override_btn.pack(side="left", padx=10)

            # Warning about override
            ctk.CTkLabel(
                content,
                text="⚠️ Override will allow trading for 24 hours despite regime warning.",
                font=ctk.CTkFont(size=10),
                text_color="orange",
                wraplength=400
            ).pack(pady=(0, 5))

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.wait_window()
        return result[0]

    @staticmethod
    def show_override_confirmation(duration_hours: int = 24) -> bool:
        """
        Confirm user wants to set override

        Args:
            duration_hours: How long override will last

        Returns:
            True if user confirms
        """
        if not CTK_AVAILABLE:
            response = input(f"Set override for {duration_hours} hours? (y/n): ")
            return response.lower() == 'y'

        return messagebox.askyesno(
            "Confirm Override",
            f"Set regime override for {duration_hours} hours?\n\n"
            "This will allow the bot to continue trading despite the current regime warning.\n\n"
            "Are you sure you want to proceed?",
            icon="warning"
        )

    @staticmethod
    def show_override_expiring_soon(minutes_remaining: int) -> Optional[str]:
        """
        Alert that override is expiring soon

        Args:
            minutes_remaining: Minutes until override expires

        Returns:
            'extend' to extend, 'clear' to clear now, None to do nothing
        """
        if not CTK_AVAILABLE:
            print(f"Override expiring in {minutes_remaining} minutes")
            return None

        response = messagebox.askyesnocancel(
            "Override Expiring Soon",
            f"Your regime override will expire in {minutes_remaining} minutes.\n\n"
            "What would you like to do?\n\n"
            "Yes = Extend for another 24 hours\n"
            "No = Clear override now\n"
            "Cancel = Do nothing",
            icon="warning"
        )

        if response is True:
            return 'extend'
        elif response is False:
            return 'clear'
        else:
            return None


# Test the dialog standalone
if __name__ == "__main__":
    if not CTK_AVAILABLE:
        print("CustomTkinter not available, cannot test dialogs")
        sys.exit(1)

    ctk.set_appearance_mode("dark")

    # Create a root window (required for dialogs)
    root = ctk.CTk()
    root.withdraw()  # Hide root window

    print("=" * 80)
    print("Regime Alert Dialog - Interactive Test")
    print("=" * 80)

    # Test 1: Regime change alert
    print("\nTest 1: Showing regime change alert (BULLISH → BEARISH)")
    RegimeAlertDialog.show_regime_change_alert(
        old_regime="BULLISH",
        new_regime="BEARISH",
        new_action="REDUCE",
        position_multiplier=0.5,
        risk_profile="CONSERVATIVE"
    )
    print("✅ Test 1 complete")

    # Test 2: Trading halted alert (with override option)
    print("\nTest 2: Showing trading halted alert (with override)")
    result = RegimeAlertDialog.show_trading_halted_alert(
        regime="CRISIS",
        risk_profile="CONSERVATIVE",
        can_override=True
    )
    print(f"User choice: {result}")
    print("✅ Test 2 complete")

    # Test 3: Override confirmation
    print("\nTest 3: Showing override confirmation")
    confirmed = RegimeAlertDialog.show_override_confirmation(duration_hours=24)
    print(f"User confirmed: {confirmed}")
    print("✅ Test 3 complete")

    # Test 4: Override expiring soon
    print("\nTest 4: Showing override expiring soon")
    choice = RegimeAlertDialog.show_override_expiring_soon(minutes_remaining=15)
    print(f"User choice: {choice}")
    print("✅ Test 4 complete")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 80)

    root.destroy()
