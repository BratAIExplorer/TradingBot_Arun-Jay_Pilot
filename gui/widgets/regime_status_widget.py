#!/usr/bin/env python3
"""
Regime Status Widget - Always-Visible Market Regime Display
============================================================

Displays current market regime status in the main trading GUI.
Updates automatically and shows:
- Current regime (CRISIS, BEARISH, VOLATILE, SIDEWAYS, BULLISH)
- Trading status (CONTINUE, REDUCE, HALT)
- Position size adjustment
- Override status if active

Part of MVP v1.0 - Week 1 Foundation

Author: Claude AI (Anthropic)
Date: January 18, 2026
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: CustomTkinter not installed. Install with: pip install customtkinter")
    CTK_AVAILABLE = False
    ctk = None

from typing import Optional, Callable
from datetime import datetime


class RegimeStatusWidget(ctk.CTkFrame if CTK_AVAILABLE else object):
    """
    Widget that displays current regime status in the main GUI
    """

    # Color schemes for different regime states
    REGIME_COLORS = {
        'CRISIS': {'bg': '#8B0000', 'text': '#FFFFFF', 'emoji': '🚨'},      # Dark red
        'BEARISH': {'bg': '#DC143C', 'text': '#FFFFFF', 'emoji': '🐻'},     # Crimson
        'VOLATILE': {'bg': '#FF8C00', 'text': '#000000', 'emoji': '⚡'},     # Dark orange
        'SIDEWAYS': {'bg': '#4682B4', 'text': '#FFFFFF', 'emoji': '➡️'},    # Steel blue
        'BULLISH': {'bg': '#228B22', 'text': '#FFFFFF', 'emoji': '🐂'},     # Forest green
    }

    ACTION_COLORS = {
        'HALT': {'bg': '#8B0000', 'text': '#FFFFFF', 'icon': '🛑'},
        'REDUCE': {'bg': '#FF8C00', 'text': '#000000', 'icon': '⚠️'},
        'CONTINUE': {'bg': '#228B22', 'text': '#FFFFFF', 'icon': '✅'},
    }

    def __init__(
        self,
        parent,
        on_override_click: Optional[Callable] = None,
        on_details_click: Optional[Callable] = None,
        compact: bool = False
    ):
        """
        Initialize regime status widget

        Args:
            parent: Parent widget
            on_override_click: Callback when override button clicked
            on_details_click: Callback when details button clicked
            compact: If True, show compact version
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required for RegimeStatusWidget")

        super().__init__(parent, corner_radius=10)

        self.on_override_click = on_override_click
        self.on_details_click = on_details_click
        self.compact = compact

        # Current status
        self.current_regime = "SIDEWAYS"
        self.current_action = "CONTINUE"
        self.position_multiplier = 1.0
        self.has_override = False
        self.override_expires_at = None
        self.risk_profile = "CONSERVATIVE"

        # Build UI
        self.setup_ui()

    def setup_ui(self):
        """Build the widget UI"""
        if self.compact:
            self.setup_compact_ui()
        else:
            self.setup_full_ui()

    def setup_full_ui(self):
        """Build full version of the widget"""
        # Configure grid
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="📊 Market Regime Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")

        # Current regime display
        self.regime_frame = ctk.CTkFrame(self, corner_radius=8)
        self.regime_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            self.regime_frame,
            text="Regime",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray"
        ).pack(pady=(5, 0))

        self.regime_label = ctk.CTkLabel(
            self.regime_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.regime_label.pack(pady=(0, 5))

        # Trading action display
        self.action_frame = ctk.CTkFrame(self, corner_radius=8)
        self.action_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            self.action_frame,
            text="Trading Status",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray"
        ).pack(pady=(5, 0))

        self.action_label = ctk.CTkLabel(
            self.action_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.action_label.pack(pady=(0, 5))

        # Position size display
        self.position_frame = ctk.CTkFrame(self, corner_radius=8)
        self.position_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            self.position_frame,
            text="Position Size",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray"
        ).pack(pady=(5, 0))

        self.position_label = ctk.CTkLabel(
            self.position_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.position_label.pack(pady=(0, 5))

        # Override status / buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=(0, 10), sticky="ew")

        self.override_label = ctk.CTkLabel(
            self.button_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="orange"
        )
        self.override_label.pack(side="left", padx=10)

        # Override button
        self.override_btn = ctk.CTkButton(
            self.button_frame,
            text="🔓 Override",
            width=100,
            height=28,
            command=self._on_override_clicked,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.override_btn.pack(side="right", padx=5)

        # Details button
        if self.on_details_click:
            self.details_btn = ctk.CTkButton(
                self.button_frame,
                text="ℹ️ Details",
                width=100,
                height=28,
                command=self._on_details_clicked,
                fg_color="gray",
                hover_color="darkgray"
            )
            self.details_btn.pack(side="right", padx=5)

    def setup_compact_ui(self):
        """Build compact version (single line)"""
        # Single row display
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Regime
        self.regime_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.regime_label.grid(row=0, column=0, padx=5, pady=5)

        # Action
        self.action_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.action_label.grid(row=0, column=1, padx=5, pady=5)

        # Position
        self.position_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.position_label.grid(row=0, column=2, padx=5, pady=5)

        # Override button
        self.override_btn = ctk.CTkButton(
            self,
            text="Override",
            width=80,
            height=24,
            command=self._on_override_clicked,
            fg_color="orange"
        )
        self.override_btn.grid(row=0, column=3, padx=5, pady=5)

    def update_status(self, status_dict: dict):
        """
        Update widget with new status

        Args:
            status_dict: Dictionary from RegimeEngine.get_status_summary()
        """
        self.current_regime = status_dict.get('regime', 'SIDEWAYS')
        self.current_action = status_dict.get('action', 'CONTINUE')
        self.position_multiplier = status_dict.get('position_multiplier', 1.0)
        self.has_override = status_dict.get('has_override', False)
        self.override_expires_at = status_dict.get('override_expires_at')
        self.risk_profile = status_dict.get('risk_profile', 'CONSERVATIVE')

        self._update_display()

    def _update_display(self):
        """Update the visual display"""
        # Get colors
        regime_colors = self.REGIME_COLORS.get(self.current_regime, self.REGIME_COLORS['SIDEWAYS'])
        action_colors = self.ACTION_COLORS.get(self.current_action, self.ACTION_COLORS['CONTINUE'])

        # Update regime
        regime_text = f"{regime_colors['emoji']} {self.current_regime}"
        self.regime_label.configure(text=regime_text)

        if not self.compact and hasattr(self, 'regime_frame'):
            self.regime_frame.configure(fg_color=regime_colors['bg'])

        # Update action
        action_text = f"{action_colors['icon']} {self.current_action}"
        self.action_label.configure(text=action_text)

        if not self.compact and hasattr(self, 'action_frame'):
            self.action_frame.configure(fg_color=action_colors['bg'])

        # Update position size
        position_text = f"{self.position_multiplier:.0%}"
        self.position_label.configure(text=position_text)

        if not self.compact and hasattr(self, 'position_frame'):
            # Color code position frame based on multiplier
            if self.position_multiplier == 0.0:
                pos_color = "#8B0000"  # Dark red for 0%
            elif self.position_multiplier < 1.0:
                pos_color = "#FF8C00"  # Orange for reduced
            else:
                pos_color = "#228B22"  # Green for 100%
            self.position_frame.configure(fg_color=pos_color)

        # Update override status
        if self.has_override:
            if hasattr(self, 'override_label'):
                if self.override_expires_at:
                    expires = self.override_expires_at.strftime('%I:%M %p')
                    self.override_label.configure(text=f"🔓 Override active until {expires}")
                else:
                    self.override_label.configure(text="🔓 Override active")

            self.override_btn.configure(text="❌ Clear Override", fg_color="red")
        else:
            if hasattr(self, 'override_label'):
                self.override_label.configure(text="")

            # Only show override button if trading is halted
            if self.current_action == 'HALT':
                self.override_btn.configure(
                    text="🔓 Override",
                    fg_color="orange",
                    state="normal"
                )
            else:
                if not self.compact:
                    self.override_btn.configure(state="disabled")

    def _on_override_clicked(self):
        """Handle override button click"""
        if self.on_override_click:
            self.on_override_click(self.has_override)

    def _on_details_clicked(self):
        """Handle details button click"""
        if self.on_details_click:
            self.on_details_click()


# Test the widget standalone
if __name__ == "__main__":
    import time

    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("Regime Status Widget - Test")
    root.geometry("600x300")

    def on_override(is_active):
        print(f"Override button clicked! Currently active: {is_active}")

    def on_details():
        print("Details button clicked!")

    # Create widget
    widget = RegimeStatusWidget(
        root,
        on_override_click=on_override,
        on_details_click=on_details,
        compact=False
    )
    widget.pack(fill="both", expand=True, padx=20, pady=20)

    # Test different scenarios
    test_scenarios = [
        {
            'regime': 'BULLISH',
            'action': 'CONTINUE',
            'position_multiplier': 1.0,
            'has_override': False,
            'risk_profile': 'CONSERVATIVE'
        },
        {
            'regime': 'VOLATILE',
            'action': 'REDUCE',
            'position_multiplier': 0.5,
            'has_override': False,
            'risk_profile': 'CONSERVATIVE'
        },
        {
            'regime': 'CRISIS',
            'action': 'HALT',
            'position_multiplier': 0.0,
            'has_override': False,
            'risk_profile': 'CONSERVATIVE'
        },
        {
            'regime': 'CRISIS',
            'action': 'HALT',
            'position_multiplier': 0.0,
            'has_override': True,
            'override_expires_at': datetime.now(),
            'risk_profile': 'CONSERVATIVE'
        }
    ]

    scenario_idx = [0]  # Mutable container to track index

    def cycle_scenarios():
        scenario = test_scenarios[scenario_idx[0]]
        widget.update_status(scenario)
        print(f"\nShowing scenario {scenario_idx[0] + 1}/{len(test_scenarios)}")
        print(f"Regime: {scenario['regime']}, Action: {scenario['action']}")

        scenario_idx[0] = (scenario_idx[0] + 1) % len(test_scenarios)
        root.after(3000, cycle_scenarios)  # Change every 3 seconds

    # Start cycling
    root.after(100, cycle_scenarios)

    print("=" * 80)
    print("Regime Status Widget - Interactive Test")
    print("=" * 80)
    print("The widget will cycle through different scenarios every 3 seconds.")
    print("Click the buttons to test callbacks.")
    print("=" * 80)

    root.mainloop()
