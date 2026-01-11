"""
🎨 ARUN Bot - Settings GUI
Visual configuration interface using CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from settings_manager import SettingsManager
import json
from typing import Dict, Any

class SettingsGUI:
    def __init__(self):
        # Initialize settings manager
        self.settings_mgr = SettingsManager()
        self.settings_mgr.load()
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Main window
        self.root = ctk.CTk()
        self.root.title("⚙️ ARUN Bot - Settings")
        self.root.geometry("900x700")
        
        # Header
        header = ctk.CTkLabel(
            self.root, 
            text="⚙️ Settings", 
            font=("Arial", 24, "bold")
        )
        header.pack(pady=20)
        
        # Create tabbed interface
        self.tabview = ctk.CTkTabview(self.root, width=850, height=550)
        self.tabview.pack(padx=20, pady=10)
        
        # Add tabs
        self.tabview.add("Broker")
        self.tabview.add("Capital")
        self.tabview.add("Risk Controls")
        self.tabview.add("Stocks")
        
        # Build each tab
        self.build_broker_tab()
        self.build_capital_tab()
        self.build_risk_tab()
        self.build_stocks_tab()
        
        # Bottom buttons
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10)
        
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save All Settings",
            command=self.save_settings,
            width=200,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.save_btn.grid(row=0, column=0, padx=10)
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self.root.destroy,
            width=120,
            height=40,
            font=("Arial", 14),
            fg_color="gray",
            hover_color="darkgray"
        )
        self.cancel_btn.grid(row=0, column=1, padx=10)
    
    def build_broker_tab(self):
        """Broker credentials configuration"""
        tab = self.tabview.tab("Broker")
        
        # Get broker settings
        broker = self.settings_mgr.get("broker", {})
        
        # Broker selection
        broker_label = ctk.CTkLabel(tab, text="Select Broker:", font=("Arial", 14, "bold"))
        broker_label.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        self.broker_var = ctk.StringVar(value=broker.get("name", "mstock"))
        broker_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.broker_var,
            values=["mstock", "zerodha", "other"],
            width=200
        )
        broker_menu.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # API Key
        api_label = ctk.CTkLabel(tab, text="API Key:", font=("Arial", 12))
        api_label.grid(row=1, column=0, sticky="w", padx=20, pady=10)
        
        self.api_key_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter API Key", show="*")
        self.api_key_entry.insert(0, self.settings_mgr.get_decrypted("broker.api_key", ""))
        self.api_key_entry.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        # API Secret
        secret_label = ctk.CTkLabel(tab, text="API Secret:", font=("Arial", 12))
        secret_label.grid(row=2, column=0, sticky="w", padx=20, pady=10)
        
        self.api_secret_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter API Secret", show="*")
        self.api_secret_entry.insert(0, self.settings_mgr.get_decrypted("broker.api_secret", ""))
        self.api_secret_entry.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        
        # Client Code
        client_label = ctk.CTkLabel(tab, text="Client Code:", font=("Arial", 12))
        client_label.grid(row=3, column=0, sticky="w", padx=20, pady=10)
        
        self.client_code_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter Client Code")
        self.client_code_entry.insert(0, broker.get("client_code", ""))
        self.client_code_entry.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        
        # Password
        password_label = ctk.CTkLabel(tab, text="Password:", font=("Arial", 12))
        password_label.grid(row=4, column=0, sticky="w", padx=20, pady=10)
        
        self.password_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter Password", show="*")
        self.password_entry.insert(0, self.settings_mgr.get_decrypted("broker.password", ""))
        self.password_entry.grid(row=4, column=1, sticky="w", padx=10, pady=10)
        
        # Show password toggle
        self.show_pass_var = ctk.BooleanVar(value=False)
        show_pass_check = ctk.CTkCheckBox(
            tab,
            text="Show API keys & passwords",
            variable=self.show_pass_var,
            command=lambda: self.toggle_password_visibility()
        )
        show_pass_check.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # Info label
        info = ctk.CTkLabel(
            tab,
            text="🔐 Tip: All sensitive credentials are encrypted and stored securely in settings.json",
            font=("Arial", 10),
            text_color="gray"
        )
        info.grid(row=6, column=0, columnspan=2, padx=20, pady=20)
    
    def build_capital_tab(self):
        """Capital management configuration"""
        tab = self.tabview.tab("Capital")
        
        capital = self.settings_mgr.get("capital", {})
        
        # Total capital
        total_label = ctk.CTkLabel(tab, text="Total Capital (₹):", font=("Arial", 14, "bold"))
        total_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.total_capital_entry = ctk.CTkEntry(tab, width=200, placeholder_text="50000")
        self.total_capital_entry.insert(0, str(capital.get("total_capital", 50000)))
        self.total_capital_entry.grid(row=0, column=1, sticky="w", padx=10, pady=15)
        
        # Per-trade capital %
        per_trade_label = ctk.CTkLabel(tab, text="Per-Trade Capital (%):", font=("Arial", 12))
        per_trade_label.grid(row=1, column=0, sticky="w", padx=20, pady=10)
        
        self.per_trade_var = ctk.DoubleVar(value=capital.get("per_trade_pct", 10.0))
        per_trade_slider = ctk.CTkSlider(
            tab,
            from_=1,
            to=50,
            number_of_steps=49,
            variable=self.per_trade_var,
            width=300,
            command=lambda val: per_trade_value_label.configure(text=f"{val:.1f}%")
        )
        per_trade_slider.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        per_trade_value_label = ctk.CTkLabel(tab, text=f"{self.per_trade_var.get():.1f}%", font=("Arial", 12, "bold"))
        per_trade_value_label.grid(row=1, column=2, sticky="w", padx=5)
        
        # Maximum positions
        max_pos_label = ctk.CTkLabel(tab, text="Max Positions:", font=("Arial", 12))
        max_pos_label.grid(row=2, column=0, sticky="w", padx=20, pady=10)
        
        self.max_positions_var = ctk.IntVar(value=capital.get("max_positions", 5))
        max_pos_slider = ctk.CTkSlider(
            tab,
            from_=1,
            to=20,
            number_of_steps=19,
            variable=self.max_positions_var,
            width=300,
            command=lambda val: max_pos_value_label.configure(text=f"{int(val)}")
        )
        max_pos_slider.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        
        max_pos_value_label = ctk.CTkLabel(tab, text=str(self.max_positions_var.get()), font=("Arial", 12, "bold"))
        max_pos_value_label.grid(row=2, column=2, sticky="w", padx=5)
        
        # Compound profits
        self.compound_var = ctk.BooleanVar(value=capital.get("compound_profits", False))
        compound_check = ctk.CTkCheckBox(
            tab,
            text="Compound profits (reinvest gains)",
            variable=self.compound_var,
            font=("Arial", 12)
        )
        compound_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=15)
        
        # Info section
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=20, sticky="ew")
        
        info_title = ctk.CTkLabel(info_frame, text="💡 Capital Allocation Example:", font=("Arial", 12, "bold"))
        info_title.pack(anchor="w", padx=10, pady=5)
        
        # Calculate example
        total_cap = float(self.total_capital_entry.get() or 50000)
        per_trade_pct = self.per_trade_var.get()
        per_trade_amount = total_cap * (per_trade_pct / 100)
        
        info_text = ctk.CTkLabel(
            info_frame,
            text=f"• Total Capital: ₹{total_cap:,.0f}\n"
                 f"• Per Trade: ₹{per_trade_amount:,.0f} ({per_trade_pct:.1f}%)\n"
                 f"• Max Positions: {self.max_positions_var.get()}\n"
                 f"• Max Deployed: ₹{per_trade_amount * self.max_positions_var.get():,.0f}\n\n"
                 f"💡 How Quantity Works:\n"
                 f"  • CSV Quantity = 0: Calculate shares from capital %\n"
                 f"  • CSV Quantity > 0: Buy exactly that many shares (ignore %)\n"
                 f"  • Max Positions limits total # of different stocks held",
            font=("Arial", 10),
            justify="left"
        )
        info_text.pack(anchor="w", padx=10, pady=5)
    
    def build_risk_tab(self):
        """Risk controls configuration"""
        tab = self.tabview.tab("Risk Controls")
        
        risk = self.settings_mgr.get("risk", {})
        
        # Stop-loss %
        sl_label = ctk.CTkLabel(tab, text="Stop-Loss (%):", font=("Arial", 14, "bold"))
        sl_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.stop_loss_var = ctk.DoubleVar(value=risk.get("stop_loss_pct", 5.0))
        sl_slider = ctk.CTkSlider(
            tab,
            from_=1,
            to=20,
            number_of_steps=38,
            variable=self.stop_loss_var,
            width=300,
            command=lambda val: sl_value_label.configure(text=f"{val:.1f}%")
        )
        sl_slider.grid(row=0, column=1, sticky="w", padx=10, pady=15)
        
        sl_value_label = ctk.CTkLabel(tab, text=f"{self.stop_loss_var.get():.1f}%", font=("Arial", 12, "bold"), text_color="red")
        sl_value_label.grid(row=0, column=2, sticky="w", padx=5)
        
        # Profit target %
        tp_label = ctk.CTkLabel(tab, text="Profit Target (%):", font=("Arial", 14, "bold"))
        tp_label.grid(row=1, column=0, sticky="w", padx=20, pady=15)
        
        self.profit_target_var = ctk.DoubleVar(value=risk.get("profit_target_pct", 10.0))
        tp_slider = ctk.CTkSlider(
            tab,
            from_=2,
            to=50,
            number_of_steps=48,
            variable=self.profit_target_var,
            width=300,
            command=lambda val: tp_value_label.configure(text=f"{val:.1f}%")
        )
        tp_slider.grid(row=1, column=1, sticky="w", padx=10, pady=15)
        
        tp_value_label = ctk.CTkLabel(tab, text=f"{self.profit_target_var.get():.1f}%", font=("Arial", 12, "bold"), text_color="green")
        tp_value_label.grid(row=1, column=2, sticky="w", padx=5)
        
        # Catastrophic stop %
        cat_label = ctk.CTkLabel(tab, text="Catastrophic Stop (%):", font=("Arial", 12))
        cat_label.grid(row=2, column=0, sticky="w", padx=20, pady=10)
        
        self.cat_stop_var = ctk.DoubleVar(value=risk.get("catastrophic_stop_loss_pct", 15.0))
        cat_slider = ctk.CTkSlider(
            tab,
            from_=10,
            to=50,
            number_of_steps=40,
            variable=self.cat_stop_var,
            width=300,
            command=lambda val: cat_value_label.configure(text=f"{val:.1f}%")
        )
        cat_slider.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        
        cat_value_label = ctk.CTkLabel(tab, text=f"{self.cat_stop_var.get():.1f}%", font=("Arial", 12, "bold"))
        cat_value_label.grid(row=2, column=2, sticky="w", padx=5)
        
        # Daily loss limit %
        daily_label = ctk.CTkLabel(tab, text="Daily Loss Limit (%):", font=("Arial", 12))
        daily_label.grid(row=3, column=0, sticky="w", padx=20, pady=10)
        
        self.daily_loss_var = ctk.DoubleVar(value=risk.get("daily_loss_limit_pct", 10.0))
        daily_slider = ctk.CTkSlider(
            tab,
            from_=5,
            to=30,
            number_of_steps=25,
            variable=self.daily_loss_var,
            width=300,
            command=lambda val: daily_value_label.configure(text=f"{val:.1f}%")
        )
        daily_slider.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        
        daily_value_label = ctk.CTkLabel(tab, text=f"{self.daily_loss_var.get():.1f}%", font=("Arial", 12, "bold"))
        daily_value_label.grid(row=3, column=2, sticky="w", padx=5)
        
        # Never sell at loss option
        never_sell_frame = ctk.CTkFrame(tab, fg_color="#2B2B2B")
        never_sell_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=15, sticky="ew")
        
        self.never_sell_at_loss_var = ctk.BooleanVar(value=risk.get("never_sell_at_loss", False))
        never_sell_check = ctk.CTkCheckBox(
            never_sell_frame,
            text="⛔ Never Sell at Loss (Override Stop-Loss)",
            variable=self.never_sell_at_loss_var,
            font=("Arial", 13, "bold"),
            command=self.on_never_sell_at_loss_toggled
        )
        never_sell_check.pack(anchor="w", padx=15, pady=(15, 5))
        
        never_sell_warning = ctk.CTkLabel(
            never_sell_frame,
            text="⚠️ WARNING: When enabled, stop-loss will NOT trigger if position is in loss.\n"
                 "This could lead to unlimited losses if market keeps dropping.\n"
                 "Catastrophic stop will still work as final safety measure.",
            font=("Arial", 10),
            text_color="#FFB84D",
            justify="left"
        )
        never_sell_warning.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Risk summary section
        warning_frame = ctk.CTkFrame(tab, fg_color="darkred")
        warning_frame.grid(row=5, column=0, columnspan=3, padx=20, pady=20, sticky="ew")
        
        warning_label = ctk.CTkLabel(
            warning_frame,
            text="⚠️ RISK PROTECTION ACTIVE\n"
                 "Bot will automatically sell if:\n"
                 f"• Position loss exceeds {self.stop_loss_var.get():.1f}% (Stop-Loss)\n"
                 f"• Position profit reaches {self.profit_target_var.get():.1f}% (Take Profit)\n"
                 f"• Position loss exceeds {self.cat_stop_var.get():.1f}% (Emergency Stop)\n"
                 f"• Daily portfolio loss exceeds {self.daily_loss_var.get():.1f}% (Circuit Breaker)",
            font=("Arial", 11),
            justify="left"
        )
        warning_label.pack(padx=15, pady=15)
    
    def build_stocks_tab(self):
        """Stock configuration - Simple view/edit interface"""
        tab = self.tabview.tab("Stocks")
        
        # Info label
        info_label = ctk.CTkLabel(
            tab,
            text="📊 Stock Configuration\n(Currently managed via config_table.csv)",
            font=("Arial", 14, "bold")
        )
        info_label.pack(pady=20)
        
        # Coming soon message
        coming_soon = ctk.CTkLabel(
            tab,
            text="🚧 Visual Stock Editor Coming Soon!\n\n"
                 "For now, edit stocks in: config_table.csv\n"
                 "Next update will add:\n"
                 "• Stock search & add\n"
                 "• Per-stock RSI thresholds\n"
                 "• Enable/disable individual stocks\n"
                 "• Timeframe selection",
            font=("Arial", 12),
            text_color="gray",
            justify="center"
        )
        coming_soon.pack(pady=30)
        
        # Open CSV button
        open_csv_btn = ctk.CTkButton(
            tab,
            text="📄 Open config_table.csv",
            command=self.open_config_csv,
            width=200,
            height=40
        )
        open_csv_btn.pack(pady=10)
    
    def toggle_password_visibility(self):
        """Toggle password and API key field visibility"""
        show = self.show_pass_var.get()
        self.api_key_entry.configure(show="" if show else "*")
        self.api_secret_entry.configure(show="" if show else "*")
        self.password_entry.configure(show="" if show else "*")
    
    def on_never_sell_at_loss_toggled(self):
        """Handle never-sell-at-loss toggle with confirmation dialog"""
        if self.never_sell_at_loss_var.get():
            from tkinter import messagebox
            result = messagebox.askokcancel(
                "⚠️ Warning: Never Sell at Loss",
                "You are about to enable 'Never Sell at Loss'.\n\n"
                "This will OVERRIDE your stop-loss protection when positions are in loss.\n\n"
                "Risk:\n"
                "• Losses could accumulate indefinitely\n"
                "• Capital could be tied up in losing positions\n"
                "• Catastrophic stop is your only safety net\n\n"
                "Are you sure you want to enable this?",
                icon='warning'
            )
            if not result:
                # User clicked Cancel, revert the checkbox
                self.never_sell_at_loss_var.set(False)
    
    def open_config_csv(self):
        """Open config CSV in default editor"""
        import os
        import subprocess
        csv_path = "config_table.csv"
        if os.path.exists(csv_path):
            try:
                os.startfile(csv_path)  # Windows
            except:
                try:
                    subprocess.call(["open", csv_path])  # macOS
                except:
                    messagebox.showinfo("Info", f"Please manually open: {csv_path}")
        else:
            messagebox.showerror("Error", "config_table.csv not found!")
    
    def save_settings(self):
        """Save all settings to JSON"""
        try:
            # Build settings dictionary
            new_settings = {
                "broker": {
                    "name": self.broker_var.get(),
                    "api_key": self.api_key_entry.get(),
                    "api_secret": self.api_secret_entry.get(),
                    "client_code": self.client_code_entry.get(),
                    "password": self.password_entry.get()
                },
                "capital": {
                    "total_capital": float(self.total_capital_entry.get()),
                    "per_trade_pct": self.per_trade_var.get(),
                    "max_positions": self.max_positions_var.get(),
                    "compound_profits": self.compound_var.get()
                },
                "risk": {
                    "stop_loss_pct": self.stop_loss_var.get(),
                    "profit_target_pct": self.profit_target_var.get(),
                    "catastrophic_stop_loss_pct": self.cat_stop_var.get(),
                    "daily_loss_limit_pct": self.daily_loss_var.get(),
                    "never_sell_at_loss": self.never_sell_at_loss_var.get()
                }
            }
            
            # Merge with existing settings (preserve other sections)
            current_settings = self.settings_mgr.settings
            current_settings.update(new_settings)
            
            # Save to JSON
            self.settings_mgr.save(current_settings)
            
            messagebox.showinfo(
                "✅ Success",
                "Settings saved successfully!\n\nRestart the bot for changes to take effect."
            )
            
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to save settings:\n{str(e)}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = SettingsGUI()
    app.run()
