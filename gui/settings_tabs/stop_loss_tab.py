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
