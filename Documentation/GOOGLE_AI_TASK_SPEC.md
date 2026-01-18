# 🤖 Google AI Task Specification: Enhanced Settings GUI

**Project:** ARUN Trading Bot - MVP v1.0
**Task Owner:** Google AI
**Parallel Task:** Claude AI is building Regime Monitor Integration
**Branch:** Create and work on `google/enhanced-settings-gui`
**Estimated Time:** 3 hours
**Status:** Ready to Start

---

## 🎯 STRICT INSTRUCTIONS - READ CAREFULLY

### ✅ What You MUST Do:
1. Create 5 NEW files in `gui/settings_tabs/` directory (see File Specifications below)
2. Follow the EXACT code patterns and architecture shown below
3. Use `SettingsManagerV2` from `settings_manager_v2.py` (already exists)
4. Use CustomTkinter (ctk) for all GUI components
5. Follow the 3 Design Principles (user-customizable, modern/robust, smart GUI)
6. Test each component as you build it
7. Commit frequently with clear messages
8. Update `Documentation/AI_AGENT_HANDOVER.md` with your progress

### ❌ What You MUST NOT Do:
1. **DO NOT modify `kickstart.py`** - Claude AI is modifying it in parallel
2. **DO NOT modify `settings_manager_v2.py`** - It's complete and tested
3. **DO NOT modify `regime_monitor.py`** - It's being integrated by Claude AI
4. **DO NOT create `enhanced_settings_window.py` yet** - Wait for integration phase
5. **DO NOT modify any existing GUI files** - Only create new files in `gui/settings_tabs/`

---

## 📋 Context: What You Need to Know

### Existing Codebase You'll Use:

**1. SettingsManagerV2** (`settings_manager_v2.py`) - Your data layer:
```python
from settings_manager_v2 import SettingsManagerV2, RiskProfile, StopLossMode, TradingMode

# Initialize
settings = SettingsManagerV2()

# Risk Profile API
settings.get_risk_profile()  # Returns RiskProfile enum
settings.set_risk_profile(RiskProfile.MODERATE)
settings.get_regime_behavior('BEARISH')  # Returns {'action': 'REDUCE', 'position_multiplier': 0.5}

# Stop-Loss API
settings.get_stop_loss_mode()  # Returns StopLossMode enum
settings.set_stop_loss_mode(StopLossMode.AUTO)
settings.get_stop_loss_confirmation_threshold()  # Returns 50000 (₹50k)

# Trading Mode API
settings.get_trading_mode()  # Returns TradingMode enum
settings.set_trading_mode(TradingMode.PAPER)
settings.is_paper_trading()  # Returns True/False

# Regime Override API
settings.can_override_halt()  # Returns True if user can override
settings.has_active_override()  # Returns True if override active
settings.set_regime_override('CRISIS', duration_hours=24)
settings.clear_regime_override()
settings.get_override_info()  # Returns {'regime': 'CRISIS', 'expires_at': '...'}

# Generic get/set
settings.get('risk_profile.selected')  # Dot notation
settings.set('trading_mode.show_mode_banner', False)
settings.save()  # Always save after changes
```

**2. Risk Profiles** (3 user options):
```python
class RiskProfile(Enum):
    CONSERVATIVE = "CONSERVATIVE"  # Default - Halts in CRISIS/BEARISH
    MODERATE = "MODERATE"          # Reduces in BEARISH, halts in CRISIS
    AGGRESSIVE = "AGGRESSIVE"      # Continues in all regimes
    CUSTOM = "CUSTOM"              # User-defined rules
```

**3. Market Regimes** (5 states):
- **CRISIS** - Market crash, VIX > 35
- **BEARISH** - Downtrend, negative momentum
- **VOLATILE** - High volatility, choppy
- **SIDEWAYS** - Range-bound, low volatility
- **BULLISH** - Uptrend, positive momentum

**4. Stop-Loss Modes**:
```python
class StopLossMode(Enum):
    AUTO = "AUTO"              # Auto-execute all stop-losses
    SMART_AUTO = "SMART_AUTO"  # Auto for small, confirm for large (>₹50k)
    ALERT_ONLY = "ALERT_ONLY"  # Never auto-execute, always alert
```

**5. Trading Modes**:
```python
class TradingMode(Enum):
    PAPER = "PAPER"  # Default - Virtual money
    LIVE = "LIVE"    # Real money - DANGER ZONE
```

---

## 📁 File Specifications - Create These 5 Files

### File 1: `gui/settings_tabs/regime_tab.py`

**Purpose:** Allow users to view and customize regime behaviors

**Requirements:**
- Display current risk profile with description
- Show all 5 regimes with their behaviors (action + position multiplier)
- Radio buttons to select CONSERVATIVE / MODERATE / AGGRESSIVE
- "Customize Rules" button for CUSTOM profile (future feature, just show message)
- Visual indicators: 🔴 HALT, 🟡 REDUCE, 🟢 CONTINUE
- Update UI when risk profile changes
- Save changes immediately

**Code Pattern:**
```python
#!/usr/bin/env python3
"""
Regime Settings Tab - Risk Profile and Regime Behavior Configuration
Part of Enhanced Settings GUI for MVP v1.0
"""

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
```

---

### File 2: `gui/settings_tabs/stop_loss_tab.py`

**Purpose:** Configure stop-loss execution behavior

**Requirements:**
- Display 3 stop-loss modes with descriptions
- Show confirmation threshold (₹50,000 for SMART_AUTO)
- Allow changing threshold
- Visual warnings for ALERT_ONLY mode
- Save changes immediately

**Code Pattern:**
```python
#!/usr/bin/env python3
"""
Stop-Loss Settings Tab - Configure Stop-Loss Execution Behavior
Part of Enhanced Settings GUI for MVP v1.0
"""

import customtkinter as ctk
from tkinter import messagebox
from settings_manager_v2 import SettingsManagerV2, StopLossMode

class StopLossSettingsTab(ctk.CTkFrame):
    """Tab for configuring stop-loss execution mode"""

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
            text="🛑 Stop-Loss Execution Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Description
        desc = ctk.CTkLabel(
            self,
            text="Choose how the bot handles stop-loss triggers",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        desc.pack(pady=(0, 20))

        # Stop-Loss Mode Selection
        self.create_mode_selection_section()

        # Threshold Configuration (for SMART_AUTO)
        self.create_threshold_section()

    def create_mode_selection_section(self):
        """Create stop-loss mode radio buttons"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="Select Stop-Loss Mode:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10)

        # Radio button variable
        self.stop_loss_mode_var = ctk.StringVar(value=StopLossMode.SMART_AUTO.value)

        # AUTO mode
        auto_frame = ctk.CTkFrame(frame, border_width=2, border_color="gray")
        auto_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkRadioButton(
            auto_frame,
            text="⚡ AUTO - Execute all stop-losses automatically",
            variable=self.stop_loss_mode_var,
            value=StopLossMode.AUTO.value,
            command=self.on_mode_changed,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=10, padx=10, anchor="w")

        ctk.CTkLabel(
            auto_frame,
            text="• Instant execution when stop-loss is hit\n"
                 "• No manual confirmation required\n"
                 "• Best for small positions and fast markets",
            font=ctk.CTkFont(size=11),
            text_color="lightgray",
            justify="left"
        ).pack(pady=(0, 10), padx=30, anchor="w")

        # SMART_AUTO mode (Recommended)
        smart_frame = ctk.CTkFrame(frame, border_width=3, border_color="#3B8ED0")
        smart_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkRadioButton(
            smart_frame,
            text="🧠 SMART_AUTO (Recommended) - Auto for small, confirm for large",
            variable=self.stop_loss_mode_var,
            value=StopLossMode.SMART_AUTO.value,
            command=self.on_mode_changed,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=10, padx=10, anchor="w")

        ctk.CTkLabel(
            smart_frame,
            text="• Auto-execute stop-losses < ₹50,000\n"
                 "• Ask for confirmation for large positions\n"
                 "• Balanced approach for safety and speed",
            font=ctk.CTkFont(size=11),
            text_color="lightgray",
            justify="left"
        ).pack(pady=(0, 10), padx=30, anchor="w")

        # ALERT_ONLY mode
        alert_frame = ctk.CTkFrame(frame, border_width=2, border_color="orange")
        alert_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkRadioButton(
            alert_frame,
            text="🔔 ALERT_ONLY - Never auto-execute, always alert",
            variable=self.stop_loss_mode_var,
            value=StopLossMode.ALERT_ONLY.value,
            command=self.on_mode_changed,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=10, padx=10, anchor="w")

        ctk.CTkLabel(
            alert_frame,
            text="⚠️ WARNING: You must manually execute all stop-losses\n"
                 "• Bot will only send alerts\n"
                 "• Risk of larger losses if you're not available\n"
                 "• Only use if you actively monitor positions",
            font=ctk.CTkFont(size=11),
            text_color="orange",
            justify="left"
        ).pack(pady=(0, 10), padx=30, anchor="w")

    def create_threshold_section(self):
        """Create threshold configuration for SMART_AUTO"""
        self.threshold_frame = ctk.CTkFrame(self)
        self.threshold_frame.pack(fill="x", padx=20, pady=10)

        label = ctk.CTkLabel(
            self.threshold_frame,
            text="SMART_AUTO Confirmation Threshold:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10)

        desc = ctk.CTkLabel(
            self.threshold_frame,
            text="Positions larger than this amount will require manual confirmation",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        desc.pack(pady=(0, 10))

        # Threshold input
        input_frame = ctk.CTkFrame(self.threshold_frame)
        input_frame.pack(pady=10)

        ctk.CTkLabel(
            input_frame,
            text="₹",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=5)

        self.threshold_entry = ctk.CTkEntry(
            input_frame,
            width=150,
            font=ctk.CTkFont(size=14)
        )
        self.threshold_entry.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(
            input_frame,
            text="Save",
            width=100,
            command=self.save_threshold
        )
        save_btn.pack(side="left", padx=5)

        # Show/hide based on mode
        self.update_threshold_visibility()

    def update_threshold_visibility(self):
        """Show threshold section only for SMART_AUTO"""
        mode = self.stop_loss_mode_var.get()
        if mode == StopLossMode.SMART_AUTO.value:
            self.threshold_frame.pack(fill="x", padx=20, pady=10)
        else:
            self.threshold_frame.pack_forget()

    def on_mode_changed(self):
        """Handle stop-loss mode change"""
        mode_name = self.stop_loss_mode_var.get()
        mode = StopLossMode[mode_name]

        # Show warning for ALERT_ONLY
        if mode == StopLossMode.ALERT_ONLY:
            response = messagebox.askyesno(
                "⚠️ Warning: ALERT_ONLY Mode",
                "ALERT_ONLY mode means the bot will NEVER automatically execute stop-losses.\n\n"
                "You must manually execute all stop-loss orders.\n\n"
                "This increases the risk of larger losses if you're not available.\n\n"
                "Are you sure you want to use ALERT_ONLY mode?",
                icon="warning"
            )
            if not response:
                # Revert to previous mode
                current_mode = self.settings.get_stop_loss_mode()
                self.stop_loss_mode_var.set(current_mode.value)
                return

        # Update settings
        self.settings.set_stop_loss_mode(mode)
        self.settings.save()

        # Update UI
        self.update_threshold_visibility()

        # Show confirmation
        messagebox.showinfo(
            "Stop-Loss Mode Updated",
            f"Stop-loss mode changed to {mode_name}.\n\n"
            "The bot will now follow the new execution behavior."
        )

    def save_threshold(self):
        """Save confirmation threshold"""
        try:
            threshold = float(self.threshold_entry.get())

            if threshold < 1000:
                messagebox.showerror(
                    "Invalid Threshold",
                    "Threshold must be at least ₹1,000"
                )
                return

            self.settings.set('stop_loss.confirmation_threshold', threshold)
            self.settings.save()

            messagebox.showinfo(
                "Threshold Updated",
                f"Confirmation threshold set to ₹{threshold:,.0f}\n\n"
                "Positions larger than this will require manual confirmation."
            )
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid number (e.g., 50000)"
            )

    def load_current_settings(self):
        """Load current settings from SettingsManagerV2"""
        current_mode = self.settings.get_stop_loss_mode()
        self.stop_loss_mode_var.set(current_mode.value)

        threshold = self.settings.get_stop_loss_confirmation_threshold()
        self.threshold_entry.delete(0, 'end')
        self.threshold_entry.insert(0, str(int(threshold)))

        self.update_threshold_visibility()


# Test this tab standalone
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("Stop-Loss Settings Tab - Test")
    root.geometry("800x700")

    settings = SettingsManagerV2(settings_file="test_settings.json", auto_migrate=False)

    tab = StopLossSettingsTab(root, settings)
    tab.pack(fill="both", expand=True)

    root.mainloop()
```

---

### File 3: `gui/settings_tabs/paper_live_tab.py`

**Purpose:** Toggle between Paper Trading and Live Trading

**Requirements:**
- Big visual toggle between PAPER and LIVE modes
- Show current mode prominently
- Warning dialog when switching to LIVE mode
- Show virtual balance for paper trading
- Banner toggle setting
- Save changes immediately

**Code Pattern:**
```python
#!/usr/bin/env python3
"""
Paper/Live Trading Tab - Switch Between Paper and Live Trading
Part of Enhanced Settings GUI for MVP v1.0
"""

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
```

---

### File 4: `gui/settings_tabs/api_test_tab.py`

**Purpose:** Run API tests from within the settings GUI

**Requirements:**
- Button to run quick API test
- Button to run full API test
- Display test results
- Show market status
- Export results option

**Code Pattern:**
```python
#!/usr/bin/env python3
"""
API Test Tab - Run API Integration Tests from GUI
Part of Enhanced Settings GUI for MVP v1.0
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import os

class APITestTab(ctk.CTkFrame):
    """Tab for running API integration tests"""

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()

    def setup_ui(self):
        """Build the UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="🔌 API Integration Test",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Description
        desc = ctk.CTkLabel(
            self,
            text="Test your mStock API connection without placing real orders",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        desc.pack(pady=(0, 20))

        # Test buttons
        self.create_test_buttons()

        # Output display
        self.create_output_display()

    def create_test_buttons(self):
        """Create test action buttons"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)

        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(pady=20)

        # Quick test button
        quick_btn = ctk.CTkButton(
            button_frame,
            text="⚡ Quick Test (30 seconds)",
            width=200,
            height=50,
            font=ctk.CTkFont(size=14),
            fg_color="#3B8ED0",
            command=self.run_quick_test
        )
        quick_btn.pack(side="left", padx=10)

        # Full test button
        full_btn = ctk.CTkButton(
            button_frame,
            text="🔬 Full Test (2-3 minutes)",
            width=200,
            height=50,
            font=ctk.CTkFont(size=14),
            command=self.run_full_test
        )
        full_btn.pack(side="left", padx=10)

        # Export button
        export_btn = ctk.CTkButton(
            button_frame,
            text="💾 Export Results",
            width=150,
            height=50,
            font=ctk.CTkFont(size=12),
            fg_color="gray",
            command=self.export_results
        )
        export_btn.pack(side="left", padx=10)

    def create_output_display(self):
        """Create output text display"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="Test Output:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10, anchor="w", padx=10)

        # Use scrolled text for output
        self.output_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial message
        self.output_text.insert("1.0", "Click a test button to run API integration tests.\n\n"
                                       "Quick Test: Basic connectivity and authentication\n"
                                       "Full Test: Comprehensive test suite (all 7 tests)\n\n"
                                       "Note: No real orders will be placed!")

    def run_quick_test(self):
        """Run quick API test"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "Starting Quick Test...\n\n")

        # Run in background thread
        threading.Thread(target=self._run_test, args=("--quick",), daemon=True).start()

    def run_full_test(self):
        """Run full API test"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "Starting Full Test...\n\n")

        # Run in background thread
        threading.Thread(target=self._run_test, args=(), daemon=True).start()

    def _run_test(self, *args):
        """Run the test (in background thread)"""
        try:
            cmd = ["python3", "test_api_integration.py"]
            if args:
                cmd.extend(args)

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout
            )

            # Display output
            output = result.stdout if result.returncode == 0 else result.stderr

            # Update UI (must be done in main thread)
            self.after(0, self._update_output, output, result.returncode == 0)

        except subprocess.TimeoutExpired:
            self.after(0, self._update_output, "❌ Test timed out after 3 minutes", False)
        except FileNotFoundError:
            self.after(0, self._update_output, "❌ Error: test_api_integration.py not found", False)
        except Exception as e:
            self.after(0, self._update_output, f"❌ Error: {str(e)}", False)

    def _update_output(self, text, success):
        """Update output text (called in main thread)"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)

        if success:
            messagebox.showinfo("✅ Test Complete", "API test completed successfully!\n\nCheck the output for details.")
        else:
            messagebox.showerror("❌ Test Failed", "API test encountered errors.\n\nCheck the output for details.")

    def export_results(self):
        """Export test results"""
        if os.path.exists("api_test_results.json"):
            messagebox.showinfo(
                "Results Exported",
                "Test results saved to:\napi_test_results.json\n\n"
                "You can share this file with support if needed."
            )
        else:
            messagebox.showwarning(
                "No Results",
                "No test results found.\n\nRun a test first to generate results."
            )


# Test this tab standalone
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("API Test Tab - Test")
    root.geometry("900x600")

    from settings_manager_v2 import SettingsManagerV2
    settings = SettingsManagerV2(settings_file="test_settings.json", auto_migrate=False)

    tab = APITestTab(root, settings)
    tab.pack(fill="both", expand=True)

    root.mainloop()
```

---

### File 5: `gui/settings_tabs/__init__.py`

**Purpose:** Package initialization file

**Content:**
```python
"""
Settings Tabs Package
Enhanced Settings GUI for MVP v1.0
"""

from .regime_tab import RegimeSettingsTab
from .stop_loss_tab import StopLossSettingsTab
from .paper_live_tab import PaperLiveTab
from .api_test_tab import APITestTab

__all__ = [
    'RegimeSettingsTab',
    'StopLossSettingsTab',
    'PaperLiveTab',
    'APITestTab'
]
```

---

## 🧪 Testing Requirements

**Test Each Tab Standalone:**
```bash
# Test regime tab
python3 gui/settings_tabs/regime_tab.py

# Test stop-loss tab
python3 gui/settings_tabs/stop_loss_tab.py

# Test paper/live tab
python3 gui/settings_tabs/paper_live_tab.py

# Test API test tab
python3 gui/settings_tabs/api_test_tab.py
```

**Verify:**
1. UI renders correctly (no crashes)
2. Settings load from SettingsManagerV2
3. Changes are saved when buttons are clicked
4. Warnings/confirmations appear appropriately
5. All buttons and controls work

---

## 📝 Git Workflow

**1. Create Your Branch:**
```bash
git checkout -b google/enhanced-settings-gui
```

**2. Commit Frequently:**
```bash
git add gui/settings_tabs/regime_tab.py
git commit -m "feat: Add Regime Settings Tab with risk profile selection"

git add gui/settings_tabs/stop_loss_tab.py
git commit -m "feat: Add Stop-Loss Settings Tab with mode selection"

# ... etc for each file
```

**3. Push When Done:**
```bash
git push -u origin google/enhanced-settings-gui
```

**4. Update Documentation:**
Add to `Documentation/AI_AGENT_HANDOVER.md` under a new section:

```markdown
## Session X: Enhanced Settings GUI (Google AI)

**Date:** [Current Date]
**Branch:** google/enhanced-settings-gui
**Status:** ✅ Complete

### Files Created:
- `gui/settings_tabs/regime_tab.py` (350 lines) - Risk profile and regime behavior configuration
- `gui/settings_tabs/stop_loss_tab.py` (380 lines) - Stop-loss execution mode settings
- `gui/settings_tabs/paper_live_tab.py` (320 lines) - Paper/Live trading mode toggle
- `gui/settings_tabs/api_test_tab.py` (200 lines) - API test integration in GUI
- `gui/settings_tabs/__init__.py` (15 lines) - Package initialization

### Testing Done:
- [x] All tabs tested standalone
- [x] Settings load correctly
- [x] Changes save successfully
- [x] Warnings/confirmations work
- [x] UI renders properly

### Next Steps:
- Integrate tabs into main settings window
- Test with Claude AI's Regime Monitor integration
```

---

## ⚠️ Important Notes

1. **DO NOT modify kickstart.py** - Claude AI is working on it
2. **Use settings_manager_v2.py as-is** - It's complete and tested
3. **Follow the code patterns EXACTLY** - They've been designed to match the project
4. **Test each file standalone first** - Make sure it works before moving on
5. **Commit frequently** - Don't wait until everything is done
6. **Update documentation** - Keep AI_AGENT_HANDOVER.md current

---

## 🎨 Design Principles to Follow

1. **User-Customizable:** Everything must be configurable, nothing forced
2. **Modern/Robust:** Use CustomTkinter, proper error handling, clean code
3. **Smart GUI:** Clear labels, helpful descriptions, visual warnings, confirmations for dangerous actions

---

## 📞 Questions?

If you encounter issues:
1. Check if `settings_manager_v2.py` exists and works
2. Verify CustomTkinter is installed: `pip install customtkinter`
3. Test the settings manager standalone first
4. Document any issues in AI_AGENT_HANDOVER.md

---

## ✅ Acceptance Criteria

Your work is complete when:
- [x] All 5 files created and tested
- [x] Each tab works standalone
- [x] Settings save/load correctly
- [x] All warnings/confirmations work
- [x] Code follows the patterns shown
- [x] Git commits are clear and descriptive
- [x] Documentation updated in AI_AGENT_HANDOVER.md

---

**Ready to Start? Good luck! 🚀**
