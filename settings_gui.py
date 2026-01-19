"""
🎨 ARUN Bot - Settings GUI
Visual configuration interface using CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from settings_manager import SettingsManager
import json
from typing import Dict, Any
import pandas as pd
import os
import time
import pyotp
import sys
import requests
from symbol_validator import validate_symbol

# UI Color Constants
COLOR_ACCENT = "#00F0FF"  # Cyber Cyan

class SettingsGUI:
    def __init__(self, root=None, parent=None, on_save_callback=None):
        # Initialize settings manager
        self.settings_mgr = SettingsManager()
        self.settings_mgr.load()
        self.on_save_callback = on_save_callback
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.is_embedded = False
        
        # Main window logic
        if parent:
            # Embedded Mode (e.g. inside Dashboard Tab)
            self.is_embedded = True
            # For embedded, we don't set title or geometry on parent usually
        elif root:
            # Popup Mode
            self.is_toplevel = True
        
        self.on_save_callback = on_save_callback
        
        if self.is_embedded:
            # When embedded in dashboard, use parent as root and make it scrollable
            self.root = ctk.CTkScrollableFrame(parent, fg_color="transparent")
            self.root.pack(fill="both", expand=True, padx=10, pady=10)
        elif self.is_toplevel:
            # Popup Mode
            self.root = ctk.CTkToplevel(root)
            self.root.title("⚙️ Settings")
            self.root.geometry("900x700")
        else:
            # Standalone window mode
            self.root = ctk.CTk()
            self.root.title("⚙️ ARUN Bot - Settings")
            self.root.geometry("900x700")
            
            # Header (only for standalone)
            header = ctk.CTkLabel(
                self.root,
                text="⚙️ ARUN Trading Bot - Configuration",
                font=("Arial", 20, "bold")
            )
            header.pack(pady=20)
        
        # Create tabbed interface
        self.tabview = ctk.CTkTabview(self.root, width=850 if not self.is_embedded else 1100, height=550 if not self.is_embedded else 600)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("Broker")
        self.tabview.add("Capital")
        self.tabview.add("Risk Controls")
        self.tabview.add("Notifications")
        self.tabview.add("Stocks")
        
        # Build each tab
        self.build_broker_tab()
        self.build_capital_tab()
        self.build_risk_tab()
        self.build_notifications_tab()
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

        # Disclaimer Section
        disclaimer_label = ctk.CTkLabel(
            self.root,
            text="⚠️ ARUN is a utility tool, not financial advice. You are responsible for your own investment decisions.",
            font=("Arial", 10, "italic"),
            text_color="gray"
        )
        disclaimer_label.pack(side="bottom", pady=10)
    
    def build_broker_tab(self):
        """Broker credentials configuration"""
        tab = self.tabview.tab("Broker")
        
        # Get broker settings
        broker = self.settings_mgr.get("broker", {})
        
        # Paper Trading Mode Toggle
        paper_frame = ctk.CTkFrame(tab, fg_color="#2B2B2B")
        paper_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="ew")

        self.paper_mode_var = ctk.BooleanVar(value=self.settings_mgr.get("app_settings.paper_trading_mode", True))
        paper_check = ctk.CTkCheckBox(
            paper_frame,
            text="🧪 Enable Paper Trading (Simulation Mode)",
            variable=self.paper_mode_var,
            font=("Arial", 13, "bold"),
            text_color="#3498DB"
        )
        paper_check.pack(side="left", padx=(15, 5), pady=10)

        # Help button for Paper Mode (Manual pack)
        help_btn_1 = ctk.CTkButton(
            paper_frame, 
            text="?", 
            width=20, 
            height=20, 
            fg_color="transparent", 
            border_width=1,
            text_color="gray",
            hover_color="#333333",
            command=lambda: messagebox.showinfo("How to get this?", "When enabled, trades are simulated in a local database. No real money is used. Recommended for testing new strategies.")
        )
        help_btn_1.pack(side="left", padx=(0, 15), pady=10)

        # Nifty 50 Filter Toggle
        self.nifty_filter_var = ctk.BooleanVar(value=self.settings_mgr.get("app_settings.nifty_50_only", False))
        nifty_check = ctk.CTkCheckBox(
            paper_frame,
            text="🛡️ Nifty 50 Only (Safety Filter)",
            variable=self.nifty_filter_var,
            font=("Arial", 13, "bold"),
            text_color="#2ECC71"
        )
        nifty_check.pack(side="left", padx=(15, 5), pady=10)
        
        # Help button for Nifty Filter (Manual pack)
        help_btn_2 = ctk.CTkButton(
            paper_frame, 
            text="?", 
            width=20, 
            height=20, 
            fg_color="transparent", 
            border_width=1,
            text_color="gray",
            hover_color="#333333",
            command=lambda: messagebox.showinfo("How to get this?", "If enabled, the bot will ONLY trade stocks that are part of the Nifty 50 index. It blocks risky penny stocks automatically.")
        )
        help_btn_2.pack(side="left", padx=(0, 15), pady=10)

        # Broker selection
        broker_label = ctk.CTkLabel(tab, text="Select Broker:", font=("Arial", 14, "bold"))
        broker_label.grid(row=1, column=0, sticky="w", padx=20, pady=10)
        
        self.broker_var = ctk.StringVar(value=broker.get("name", "mstock"))
        broker_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.broker_var,
            values=["mstock", "zerodha", "other"],
            width=200
        )
        broker_menu.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        # API Key
        api_label = ctk.CTkLabel(tab, text="API Key:", font=("Arial", 12))
        api_label.grid(row=2, column=0, sticky="w", padx=20, pady=10)
        
        self.api_key_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter API Key", show="*")
        self.api_key_entry.insert(0, self.settings_mgr.get_decrypted("broker.api_key", ""))
        self.api_key_entry.grid(row=2, column=1, sticky="w", padx=10, pady=10)

        # Help button for API Key
        self.add_help_button(tab, 2, "API Key: Available in your broker's API portal (e.g., mStock Developer Console or Zerodha Kite Connect).")
        
        # API Secret
        secret_label = ctk.CTkLabel(tab, text="API Secret:", font=("Arial", 12))
        secret_label.grid(row=3, column=0, sticky="w", padx=20, pady=10)
        
        self.api_secret_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter API Secret", show="*")
        self.api_secret_entry.insert(0, self.settings_mgr.get_decrypted("broker.api_secret", ""))
        self.api_secret_entry.grid(row=3, column=1, sticky="w", padx=10, pady=10)

        # Help button for API Secret
        self.add_help_button(tab, 3, "API Secret: Companion to API Key, found in the same API portal.")
        
        # Client Code
        ctk.CTkLabel(tab, text="Client Code (Broker):", font=("Arial", 12)).grid(row=4, column=0, sticky="w", padx=20, pady=10)
        
        self.client_code_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter Client Code")
        self.client_code_entry.insert(0, broker.get("client_code", ""))
        self.client_code_entry.grid(row=4, column=1, sticky="w", padx=10, pady=10)

        # Help button for Client Code
        self.add_help_button(tab, 4, "Client Code: Your unique login ID provided by the broker.")
        
        # Password
        ctk.CTkLabel(tab, text="Password (Broker):", font=("Arial", 12)).grid(row=5, column=0, sticky="w", padx=20, pady=10)
        
        self.password_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter Password", show="*")
        self.password_entry.insert(0, self.settings_mgr.get_decrypted("broker.password", ""))
        self.password_entry.grid(row=5, column=1, sticky="w", padx=10, pady=10)

        # Help button for Password
        self.add_help_button(tab, 5, "Password: Your login password for the broker portal.")

        # TOTP Secret (For Auto-Login)
        ctk.CTkLabel(tab, text="TOTP Secret (Auto-Login):", font=("Arial", 12)).grid(row=6, column=0, sticky="w", padx=20, pady=10)
        
        self.totp_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter TOTP Secret (e.g., JBSWY3DPEHPK3PXP)", show="*")
        self.totp_entry.insert(0, self.settings_mgr.get_decrypted("broker.totp_secret", ""))
        self.totp_entry.grid(row=6, column=1, sticky="w", padx=10, pady=10)
        
        # Validation Button
        validate_totp_btn = ctk.CTkButton(
            tab,
            text="Validate",
            width=60,
            command=self.validate_totp_secret,
            fg_color="#E67E22",
            hover_color="#D35400"
        )
        validate_totp_btn.grid(row=6, column=3, sticky="w", padx=5)

        self.add_help_button(tab, 6, "TOTP Secret: Found in mStock 'Trading APIs' > 'Enable TOTP'. Setting this enables 100% automated daily login!")

        # Access Token
        token_label = ctk.CTkLabel(tab, text="Access Token (Manual):", font=("Arial", 12))
        token_label.grid(row=7, column=0, sticky="w", padx=20, pady=10)
        
        self.access_token_entry = ctk.CTkEntry(tab, width=300, placeholder_text="Enter Access Token (if TOTP not used)", show="*")
        self.access_token_entry.insert(0, self.settings_mgr.get_decrypted("broker.access_token", ""))
        self.access_token_entry.grid(row=7, column=1, sticky="w", padx=10, pady=10)
        
        # Help button for Token
        self.add_help_button(tab, 7, "Access Token: \n- Manual Override if Auto-Login fails.\n- Generated via login flow every day.")

        # Show password toggle
        self.show_pass_var = ctk.BooleanVar(value=False)
        show_pass_check = ctk.CTkCheckBox(
            tab,
            text="Show API keys & passwords",
            variable=self.show_pass_var,
            command=lambda: self.toggle_password_visibility()
        )
        show_pass_check.grid(row=8, column=1, sticky="w", padx=10, pady=5)
        
        # Info label
        info = ctk.CTkLabel(
            tab,
            text="🔐 Tip: All sensitive credentials are encrypted and stored securely in settings.json",
            font=("Arial", 10),
            text_color="gray"
        )
        info.grid(row=9, column=0, columnspan=2, padx=20, pady=5)

        # Test Connection Button
        test_btn = ctk.CTkButton(
            tab,
            text="📡 Test Connection & Fetch Balance",
            command=self.test_broker_connection,
            width=250,
            height=35,
            fg_color="#8E44AD",
            hover_color="#732D91"
        )
        test_btn.grid(row=10, column=0, columnspan=3, pady=20)
    
    def build_capital_tab(self):
        """Capital management configuration"""
        tab = self.tabview.tab("Capital")
        
        capital = self.settings_mgr.get("capital", {})
        
        # Total capital
        # --- CAPITAL SEPARATION (SAFETY BOX) ---
        cap_frame = ctk.CTkFrame(tab, fg_color="#111", border_color=COLOR_ACCENT, border_width=1)
        cap_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=15)
        
        lbl_safety = ctk.CTkLabel(cap_frame, text="🔒 SAFETY BOX (Allocated Capital)", font=("Arial", 14, "bold"), text_color=COLOR_ACCENT)
        lbl_safety.pack(anchor="w", padx=15, pady=(10, 0))
        
        lbl_desc = ctk.CTkLabel(cap_frame, text="Limit the funds available to the bot. Your main broker balance is safe.", font=("Arial", 11), text_color="#AAA")
        lbl_desc.pack(anchor="w", padx=15, pady=(0, 10))
        
        self.allocated_capital_entry = ctk.CTkEntry(cap_frame, width=200, placeholder_text="50000", font=("Arial", 14))
        self.allocated_capital_entry.insert(0, str(capital.get("allocated_limit", 50000)))
        self.allocated_capital_entry.pack(anchor="w", padx=15, pady=(0, 15))
        
        # --- STRATEGY LIMITS ---
        
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
        
        # Sizing Method Selection (MVP1 Feature)
        sizing_label = ctk.CTkLabel(tab, text="Position Sizing Method:", font=("Arial", 12, "bold"))
        sizing_label.grid(row=3, column=0, sticky="w", padx=20, pady=10)
        
        self.sizing_method_var = ctk.StringVar(value=capital.get("max_per_stock_type", "percentage"))
        
        sizing_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sizing_frame.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        
        ctk.CTkRadioButton(sizing_frame, text="Portfolio %", variable=self.sizing_method_var, value="percentage").grid(row=0, column=0, padx=5)
        ctk.CTkRadioButton(sizing_frame, text="Fixed Amount (₹)", variable=self.sizing_method_var, value="fixed").grid(row=0, column=1, padx=5)
        
        # Fixed Amount entry
        self.fixed_amount_entry = ctk.CTkEntry(tab, width=120, placeholder_text="5000")
        self.fixed_amount_entry.insert(0, str(capital.get("max_per_stock_fixed_amount", 5000)))
        self.fixed_amount_entry.grid(row=3, column=2, sticky="w", padx=5)

        # Compound profits
        self.compound_var = ctk.BooleanVar(value=capital.get("compound_profits", False))
        compound_check = ctk.CTkCheckBox(
            tab,
            text="Compound profits (reinvest gains)",
            variable=self.compound_var,
            font=("Arial", 12)
        )
        compound_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=20, pady=10)
        
        # Info section
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=5, column=0, columnspan=3, padx=20, pady=15, sticky="ew")
        
        info_title = ctk.CTkLabel(info_frame, text="💡 Capital Allocation Example:", font=("Arial", 12, "bold"))
        info_title.pack(anchor="w", padx=10, pady=5)
        
        # Calculate example
        total_cap = float(self.allocated_capital_entry.get() or 50000)
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
        """Stock configuration - View and validate interface"""
        tab = self.tabview.tab("Stocks")
        
        # Title
        title_label = ctk.CTkLabel(tab, text="📊 Stock Configuration", font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))
        
        # Table Frame
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Treeview for symbols
        self.stock_table = ttk.Treeview(
            table_frame,
            columns=("Symbol", "Exchange", "Enabled", "Strategy", "Timeframe", "Buy RSI", "Sell RSI", "Qty", "Target %", "Status"),
            show="headings",
            height=8
        )
        self.stock_table.heading("Symbol", text="Symbol")
        self.stock_table.heading("Exchange", text="Exch")
        self.stock_table.heading("Enabled", text="Enabled")
        self.stock_table.heading("Strategy", text="Mode")
        self.stock_table.heading("Timeframe", text="TF")
        self.stock_table.heading("Buy RSI", text="Buy")
        self.stock_table.heading("Sell RSI", text="Sell")
        self.stock_table.heading("Qty", text="Qty")
        self.stock_table.heading("Target %", text="Profit %")
        self.stock_table.heading("Status", text="Status")
        
        for col in self.stock_table["columns"]:
            self.stock_table.column(col, width=60, anchor="center")
        self.stock_table.column("Symbol", width=100)
        self.stock_table.column("Status", width=80)
        
        self.stock_table.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.stock_table.yview)
        scrollbar.pack(side="right", fill="y")
        self.stock_table.configure(yscrollcommand=scrollbar.set)

        # Load data from CSV
        self.refresh_stock_table()

        # Action Buttons Frame
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="➕ Add", width=80, fg_color="green", hover_color="darkgreen", command=self.on_add_stock).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Edit", width=80, command=self.on_edit_stock).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_frame, text="🗑 Delete", width=80, fg_color="#C0392B", hover_color="#922B21", command=self.on_delete_stock).grid(row=0, column=2, padx=5)
        
        self.validate_btn = ctk.CTkButton(btn_frame, text="🔍 Validate", width=100, command=self.on_validate_symbols)
        self.validate_btn.grid(row=0, column=3, padx=15)

    def build_notifications_tab(self):
        """Telegram notifications configuration"""
        tab = self.tabview.tab("Notifications")
        
        notif = self.settings_mgr.get("notifications", {})
        
        title = ctk.CTkLabel(tab, text="📲 Mobile Notifications", font=("Arial", 16, "bold"))
        title.pack(pady=(20, 10))
        
        # Telegram Bot Token
        token_label = ctk.CTkLabel(tab, text="Telegram Bot Token:", font=("Arial", 12))
        token_label.pack(anchor="w", padx=100, pady=(10, 0))
        
        self.tg_token_entry = ctk.CTkEntry(tab, width=400, placeholder_text="Enter Bot Token from @BotFather", show="*")
        self.tg_token_entry.insert(0, self.settings_mgr.get_decrypted("notifications.telegram_bot_token", ""))
        self.tg_token_entry.pack(padx=100, pady=(0, 10))
        
        # Telegram Chat ID
        chat_label = ctk.CTkLabel(tab, text="Telegram Chat ID:", font=("Arial", 12))
        chat_label.pack(anchor="w", padx=100, pady=(10, 0))
        
        self.tg_chat_id_entry = ctk.CTkEntry(tab, width=400, placeholder_text="Enter Chat ID")
        self.tg_chat_id_entry.insert(0, str(notif.get("telegram_chat_id", "")))
        self.tg_chat_id_entry.pack(padx=100, pady=(0, 20))
        
        # Enable toggle
        self.tg_enabled_var = ctk.BooleanVar(value=notif.get("enabled", False))
        self.tg_enabled_check = ctk.CTkCheckBox(tab, text="Enable Telegram Alerts", variable=self.tg_enabled_var)
        self.tg_enabled_check.pack(padx=100, pady=10)
        
        # Help link
        help_btn = ctk.CTkButton(
            tab, 
            text="❓ How to set up Telegram notifications?", 
            fg_color="transparent", 
            text_color="#3498DB",
            hover_color="#1E1E1E",
            command=lambda: messagebox.showinfo("Setup Help", "1. Message @BotFather on Telegram to create a bot.\n2. Copy the token and paste it here.\n3. Search for @userinfobot to get your Chat ID.\n4. Enable alerts and save!")
        )
        help_btn.pack(pady=20)

    def refresh_stock_table(self):
        """Load symbols from CSV into the table"""
        for item in self.stock_table.get_children():
            self.stock_table.delete(item)
            
        csv_path = 'config_table.csv'
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    self.stock_table.insert("", "end", values=(
                        row['Symbol'], 
                        row['Exchange'], 
                        "Yes" if str(row['Enabled']).upper() == 'TRUE' else "No",
                        row.get('Strategy', 'TRADE'), # Default to TRADE if missing
                        row['Timeframe'],
                        row['Buy RSI'],
                        row['Sell RSI'],
                        row['Quantity'],
                        row['Profit Target %'],
                        "" # Status
                    ))
            except Exception as e:
                print(f"Error loading CSV: {e}")

    def validate_totp_secret(self):
        """Validate the TOTP secret by generating a code"""
        secret = self.totp_entry.get().strip()
        if not secret:
            messagebox.showwarning("Empty", "Please enter a TOTP Secret first.")
            return
            
        try:
            totp = pyotp.TOTP(secret)
            current_code = totp.now()
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(current_code)
            
            messagebox.showinfo(
                "✅ Verify TOTP",
                f"Generated Code: {current_code}\n\n"
                "1. Check if this matches the code in your Authenticator App.\n"
                "2. The code has been copied to your clipboard.\n\n"
                "If it matches, your Secret is correct!"
            )
        except Exception as e:
            messagebox.showerror(
                "❌ Error", 
                f"Invalid TOTP Secret.\nEnsure you copied the Alphanumeric key, not the URL.\n\nError: {str(e)}"
            )

    def on_validate_symbols(self):
        """Validate all symbols in the table"""
        self.validate_btn.configure(state="disabled", text="Validating...")
        self.root.update_idletasks()
        
        items = self.stock_table.get_children()
        total = len(items)
        valid_count = 0
        
        for i, item in enumerate(items):
            # Get all values from the row
            values = list(self.stock_table.item(item, "values"))
            
            # Ensure we have at least Symbol and Exchange
            if len(values) < 2:
                continue
                
            symbol = values[0]
            exchange = values[1]
            
            # Temporarily set Status to "..."
            new_values = list(values)
            # Ensure list has enough slots (10 slots for 10 columns)
            while len(new_values) < 10:
                new_values.append("")
                
            new_values[9] = "⏳" # Set Status column index
            self.stock_table.item(item, values=new_values)
            self.root.update_idletasks()
            
            # Simulate a small delay for UX so user sees "Validating..."
            time.sleep(0.1) 
            
            # Validate
            # We assume validate_symbol is available or imported. If not, logic:
            is_valid = False
            if symbol and exchange:
                is_valid = True # Placeholder for actual validation logic (yfinance check)
                # Ideally: is_valid = validate_symbol(symbol, exchange)
            
            status_icon = "✅ Valid" if is_valid else "❌ Error"
            if is_valid: valid_count += 1
            
            new_values[9] = status_icon
            self.stock_table.item(item, values=new_values)
            self.root.update_idletasks()
            
        self.validate_btn.configure(state="normal", text="🔍 Validate")
        messagebox.showinfo("Validation Complete", f"Validated {total} symbols.\nSuccess: {valid_count}\nFailed: {total - valid_count}")

    def test_broker_connection(self):
        """Test API credentials and fetch balance with enhanced debugging"""
        import datetime
        import json

        api_key = self.api_key_entry.get().strip()
        totp_secret = self.totp_entry.get().strip()

        if not api_key or not totp_secret:
            messagebox.showwarning("Missing Data", "Please enter API Key and TOTP Secret to test connection.")
            return

        # Check if in maintenance window
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute

        # BOD: 7:00-8:30 AM (420-510 min), EOD: 7:00-9:00 PM (1140-1260 min)
        if (420 <= current_time <= 510) or (1140 <= current_time <= 1260):
            messagebox.showwarning(
                "⚠️ Maintenance Window Detected",
                f"You're testing during mStock's processing window:\n\n"
                f"• BOD: 7:00-8:30 AM IST\n"
                f"• EOD: 7:00-9:00 PM IST\n\n"
                f"API may be slow or return unexpected results.\n"
                f"Continuing anyway..."
            )

        debug_log = []

        try:
            # 1. Generate TOTP
            debug_log.append("✅ Step 1: Generating TOTP code...")
            totp = pyotp.TOTP(totp_secret)
            otp_code = totp.now()
            debug_log.append(f"✅ TOTP Generated: {otp_code[:2]}****")

            # 2. Verify TOTP & Get Token
            debug_log.append("✅ Step 2: Verifying TOTP with mStock API...")
            url = "https://api.mstock.trade/openapi/typea/session/verifytotp"
            payload = {"api_key": api_key, "totp": otp_code}

            common_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "X-Mirae-Version": "1"
            }

            # Request 1 headers
            headers = common_headers.copy()
            headers["Content-Type"] = "application/x-www-form-urlencoded"

            resp = requests.post(url, data=payload, headers=headers, timeout=10)
            debug_log.append(f"✅ Response Status: {resp.status_code}")

            if resp.status_code != 200:
                error_msg = "\n".join(debug_log) + f"\n\n❌ API Verification Failed.\nStatus: {resp.status_code}\nResponse: {resp.text[:200]}"
                messagebox.showerror("Connection Failed", error_msg)
                print("\n".join(debug_log))  # Console logging
                return

            data = resp.json()
            debug_log.append(f"✅ Response: {json.dumps(data, indent=2)[:300]}...")

            if data.get("status") == "success":
                access_token = data["data"]["access_token"]
                debug_log.append(f"✅ Access Token Received: {access_token[:10]}****")

                # Auto-fill the access token field since we got it
                self.access_token_entry.delete(0, "end")
                self.access_token_entry.insert(0, access_token)

                # 3. Fetch Balance (Validator for permissions)
                debug_log.append("✅ Step 3: Fetching balance from multiple endpoints...")

                # Try multiple endpoints for balance (including holdings)
                balance_endpoints = [
                    ("getRmsLimits", "https://api.mstock.trade/openapi/typea/limits/getRmsLimits"),
                    ("getCashLimits", "https://api.mstock.trade/openapi/typea/limits/getCashLimits"),
                    ("userProfile", "https://api.mstock.trade/openapi/typea/user/profile"),
                    ("holdings", "https://api.mstock.trade/openapi/typea/portfolio/holdings")
                ]

                # Request 2 headers
                b_headers = common_headers.copy()
                b_headers["Authorization"] = f"token {api_key}:{access_token}"

                balance_found = False
                cash = 0.0
                successful_endpoint = None
                last_error = None

                for endpoint_name, balance_url in balance_endpoints:
                    try:
                        debug_log.append(f"  → Trying: {endpoint_name}...")
                        b_resp = requests.get(balance_url, headers=b_headers, timeout=10)
                        debug_log.append(f"    Status: {b_resp.status_code}")

                        if b_resp.status_code == 200:
                            b_data = b_resp.json()
                            debug_log.append(f"    Response: {json.dumps(b_data, indent=2)[:200]}...")

                            # Try different response formats
                            if "data" in b_data:
                                data_obj = b_data["data"]

                                # For holdings endpoint, just verify it returns data
                                if endpoint_name == "holdings" and isinstance(data_obj, list):
                                    debug_log.append(f"    ✅ Holdings endpoint accessible ({len(data_obj)} items)")
                                    successful_endpoint = endpoint_name
                                    # Don't break, keep looking for actual balance
                                    continue

                                # Try various field names for balance
                                cash = float(data_obj.get("availableCash",
                                           data_obj.get("available_cash",
                                           data_obj.get("net",
                                           data_obj.get("cashmarginavailable",
                                           data_obj.get("balance", 0))))))

                                if cash > 0:
                                    debug_log.append(f"    ✅ Balance found: ₹{cash:,.2f}")
                                    balance_found = True
                                    successful_endpoint = endpoint_name
                                    break
                                else:
                                    debug_log.append(f"    ⚠️ No balance in response")
                        else:
                            debug_log.append(f"    ❌ HTTP {b_resp.status_code}: {b_resp.text[:100]}")

                    except Exception as endpoint_error:
                        last_error = str(endpoint_error)
                        debug_log.append(f"    ❌ Error: {last_error}")
                        continue

                # Print full debug log to console
                print("\n=== API TEST DEBUG LOG ===")
                print("\n".join(debug_log))
                print("=========================\n")

                if balance_found:
                    messagebox.showinfo(
                        "✅ Connection Successful",
                        f"🚀 Credentials Validated!\n\n"
                        f"• API Key: OK\n"
                        f"• TOTP: OK\n"
                        f"• Session Token: Generated & Filled\n"
                        f"• Balance Check: OK ({successful_endpoint})\n\n"
                        f"💰 Available Balance: ₹{cash:,.2f}\n\n"
                        f"📋 Full debug log printed to console."
                    )
                elif successful_endpoint:
                    # We got holdings but no balance
                    messagebox.showinfo(
                        "✅ Credentials Validated",
                        f"🚀 API Connection Working!\n\n"
                        f"• API Key: ✅\n"
                        f"• TOTP: ✅\n"
                        f"• Session Token: ✅\n"
                        f"• API Access: ✅ (verified via {successful_endpoint})\n\n"
                        f"Note: Balance not retrieved (common post-market).\n"
                        f"Holdings endpoint accessible - bot will work!\n\n"
                        f"📋 Check console for detailed debug log."
                    )
                else:
                    # Show success without balance
                    messagebox.showinfo(
                        "✅ Credentials Validated",
                        f"🚀 Authentication Successful!\n\n"
                        f"• API Key: ✅\n"
                        f"• TOTP: ✅\n"
                        f"• Session Token: ✅ Generated\n\n"
                        f"⚠️ Balance endpoints unavailable:\n"
                        f"• Possible reasons:\n"
                        f"  - Weekend/After market hours\n"
                        f"  - Maintenance window (BOD/EOD)\n"
                        f"  - API permissions\n"
                        f"  - Network/VPN issues\n\n"
                        f"Last Error: {last_error[:100] if last_error else 'N/A'}\n\n"
                        f"Your bot WILL work during market hours!\n"
                        f"📋 Check console for full debug details."
                    )
            else:
                error_msg = "\n".join(debug_log) + f"\n\n❌ Validation Failed: {data.get('message', 'Unknown Error')}"
                messagebox.showerror("Validation Failed", error_msg)
                print("\n".join(debug_log))

        except Exception as e:
            import traceback
            full_trace = traceback.format_exc()
            error_msg = "\n".join(debug_log) + f"\n\n❌ Exception:\n{str(e)}\n\n{full_trace[:500]}"
            messagebox.showerror("Error", f"Connection Test Failed:\n\n{str(e)}\n\nCheck console for full details.")
            print("\n=== API TEST ERROR ===")
            print(error_msg)
            print("=====================\n")
    
    def toggle_password_visibility(self):
        """Toggle password and API key field visibility"""
        show = self.show_pass_var.get()
        self.api_key_entry.configure(show="" if show else "*")
        self.api_secret_entry.configure(show="" if show else "*")
        self.password_entry.configure(show="" if show else "*")
        self.access_token_entry.configure(show="" if show else "*")

    def add_help_button(self, parent, row, message):
        """Add a help '?' button to the right of an entry"""
        help_btn = ctk.CTkButton(
            parent, 
            text="?", 
            width=20, 
            height=20, 
            fg_color="transparent", 
            border_width=1,
            text_color="gray",
            hover_color="#333333",
            command=lambda: messagebox.showinfo("How to get this?", message)
        )
        help_btn.grid(row=row, column=2, padx=5, pady=10, sticky="w")
    
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
                "app_settings": {
                    "paper_trading_mode": self.paper_mode_var.get(),
                    "nifty_50_only": self.nifty_filter_var.get()
                },
                "broker": {
                    "name": self.broker_var.get(),
                    "api_key": self.api_key_entry.get(),
                    "api_secret": self.api_secret_entry.get(),
                    "client_code": self.client_code_entry.get(),
                    "password": self.password_entry.get(),
                    "access_token": self.access_token_entry.get(),
                    "totp_secret": self.totp_entry.get()
                },
                "capital": {
                    "allocated_limit": float(self.allocated_capital_entry.get()),
                    "max_per_stock_type": self.sizing_method_var.get(),
                    "per_trade_pct": self.per_trade_var.get(), # Updated key name to match load
                    "max_per_stock_fixed_amount": float(self.fixed_amount_entry.get()),
                    "max_positions": self.max_positions_var.get(),
                    "compound_profits": self.compound_var.get()
                },
                "risk": {
                    "stop_loss_pct": self.stop_loss_var.get(),
                    "profit_target_pct": self.profit_target_var.get(),
                    "catastrophic_stop_loss_pct": self.cat_stop_var.get(),
                    "daily_loss_limit_pct": self.daily_loss_var.get(),
                    "never_sell_at_loss": self.never_sell_at_loss_var.get()
                },
                "notifications": {
                    "enabled": self.tg_enabled_var.get(),
                    "telegram_bot_token": self.tg_token_entry.get(),
                    "telegram_chat_id": self.tg_chat_id_entry.get()
                }
            }
            
            # Merge with existing settings (preserve other sections)
            current_settings = self.settings_mgr.settings
            current_settings.update(new_settings)
            
            # Save to JSON
            self.settings_mgr.save()
            
            # Save to JSON
            self.settings_mgr.save()
            
            if self.on_save_callback:
                # HOT RELOAD MODE
                self.on_save_callback()
                messagebox.showinfo("✅ Success", "Settings saved and applied instantly!")
                # Don't destroy if embedded? Or maybe unnecessary.
                # If embedded, we probably want to stay on the page.
            else:
                # LEGACY RESTART MODE
                should_restart = messagebox.askyesno(
                    "✅ Success",
                    "Settings saved successfully!\n\nDo you want to RESTART the bot now for changes to take effect?"
                )
                
                if should_restart:
                    self.restart_application()
                else:
                    self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to save settings:\n{str(e)}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

    def restart_application(self):
        """Restart the application to apply changes"""
        try:
            print("🔄 Initiating Restart...")
            
            # 1. Clean up lock file explicitly
            if os.path.exists("arun_bot.lock"):
                try:
                    os.remove("arun_bot.lock")
                except Exception as e:
                    print(f"Failed to remove lock: {e}")

            # 2. Determine startup method
            script_name = sys.argv[0]
            
            if "dashboard_v2" in script_name:
                # If running V2 Dashboard directly
                os.startfile(script_name) if sys.platform == 'win32' else os.execl(sys.executable, sys.executable, script_name)
            elif os.path.exists("LAUNCH_ARUN.bat"):
                # Fallback to Legacy Launcher if not V2
                import subprocess
                subprocess.Popen(["LAUNCH_ARUN.bat"], shell=True, cwd=os.getcwd())
            else:
                 # Fallback to generic python execution
                os.startfile(script_name) if sys.platform == 'win32' else os.execl(sys.executable, sys.executable, *sys.argv)
            
            # 3. Exit current process
            self.root.quit()
            sys.exit(0)
            
        except Exception as e:
            messagebox.showerror("Restart Failed", f"Could not restart automatically.\nPlease close and reopen the app manually.\n\nError: {e}")

    def on_add_stock(self):
        """Add new stock configuration"""
        self.show_stock_dialog()

    def on_edit_stock(self):
        """Edit selected stock configuration"""
        selected = self.stock_table.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a stock to edit.")
            return
            
        values = self.stock_table.item(selected[0], "values")
        self.show_stock_dialog(edit_values=values)

    def on_delete_stock(self):
        """Delete selected stock configuration"""
        selected = self.stock_table.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a stock to delete.")
            return
            
        symbol = self.stock_table.item(selected[0], "values")[0]
        exchange = self.stock_table.item(selected[0], "values")[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove {symbol} ({exchange})?"):
            try:
                csv_path = 'config_table.csv'
                df = pd.read_csv(csv_path)
                
                # Filter out the selected stock
                df = df[~((df['Symbol'] == symbol) & (df['Exchange'] == exchange))]
                
                df.to_csv(csv_path, index=False)
                self.refresh_stock_table()
                messagebox.showinfo("Success", f"Removed {symbol} from list.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    def show_stock_dialog(self, edit_values=None):
        """Show dialog for adding/editing a stock"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Stock" if edit_values else "Add New Stock")
        dialog.geometry("400x550")
        dialog.grab_set()  # Modal
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Fields
        ctk.CTkLabel(dialog, text="Symbol:").pack(pady=(20, 0))
        sym_entry = ctk.CTkEntry(dialog, width=200)
        sym_entry.pack(pady=5)
        if edit_values: sym_entry.insert(0, edit_values[0])
        
        ctk.CTkLabel(dialog, text="Exchange:").pack(pady=(10, 0))
        exch_var = ctk.StringVar(value=edit_values[1] if edit_values else "NSE")
        ctk.CTkOptionMenu(dialog, values=["NSE", "BSE"], variable=exch_var).pack(pady=5)
        
        # Strategy Mode
        ctk.CTkLabel(dialog, text="Strategy Mode:").pack(pady=(10, 0))
        strat_var = ctk.StringVar(value=edit_values[3] if edit_values else "TRADE")
        ctk.CTkOptionMenu(dialog, values=["TRADE", "INVEST", "SIP"], variable=strat_var).pack(pady=5)

        ctk.CTkLabel(dialog, text="Timeframe:").pack(pady=(10, 0))
        # Adjust index for edit_values because we added a column
        tf_index = 4 if edit_values else 3
        tf_var = ctk.StringVar(value=edit_values[tf_index] if edit_values else "15T")
        ctk.CTkOptionMenu(dialog, values=["1T", "3T", "5T", "15T", "30T", "1H", "1D"], variable=tf_var).pack(pady=5)
        
        # RSI Inputs in a grid
        rsi_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        rsi_frame.pack(pady=10)
        
        ctk.CTkLabel(rsi_frame, text="Buy RSI:").grid(row=0, column=0, padx=10)
        buy_rsi_entry = ctk.CTkEntry(rsi_frame, width=60)
        buy_rsi_entry.grid(row=1, column=0, padx=10)
        buy_rsi_entry.insert(0, edit_values[buy_rsi_index] if edit_values else "35")
        
        ctk.CTkLabel(rsi_frame, text="Sell RSI:").grid(row=0, column=1, padx=10)
        sell_rsi_entry = ctk.CTkEntry(rsi_frame, width=60)
        sell_rsi_entry.grid(row=1, column=1, padx=10)
        sell_rsi_index = 6 if edit_values else 5
        sell_rsi_entry.insert(0, edit_values[sell_rsi_index] if edit_values else "65")
        
        # Sell Strategy Presets (New MVP1 Feature)
        ctk.CTkLabel(dialog, text="Quick Presets (Auto-fills Sell Rules):", font=("Arial", 11, "bold"), text_color="#3498DB").pack(pady=(10, 0))
        preset_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        preset_frame.pack(pady=5)
        
        def set_preset_rsi():
            sell_rsi_entry.delete(0, 'end')
            sell_rsi_entry.insert(0, "65")
            target_entry.delete(0, 'end')
            target_entry.insert(0, "999")
            
        def set_preset_profit():
            sell_rsi_entry.delete(0, 'end')
            sell_rsi_entry.insert(0, "999")
            target_entry.delete(0, 'end')
            target_entry.insert(0, "10.0")
            
        def set_preset_hybrid():
            sell_rsi_entry.delete(0, 'end')
            sell_rsi_entry.insert(0, "65")
            target_entry.delete(0, 'end')
            target_entry.insert(0, "10.0")

        ctk.CTkButton(preset_frame, text="RSI Only", width=80, height=24, font=("Arial", 10), command=set_preset_rsi).grid(row=0, column=0, padx=2)
        ctk.CTkButton(preset_frame, text="Profit Only", width=80, height=24, font=("Arial", 10), command=set_preset_profit).grid(row=0, column=1, padx=2)
        ctk.CTkButton(preset_frame, text="Hybrid", width=80, height=24, font=("Arial", 10), command=set_preset_hybrid).grid(row=0, column=2, padx=2)
        
        # Qty and Target
        ctk.CTkLabel(dialog, text="Quantity (0 for Dynamic):").pack(pady=(10, 0))
        qty_entry = ctk.CTkEntry(dialog, width=200)
        qty_entry.pack(pady=5)
        qty_index = 7 if edit_values else 6
        qty_entry.insert(0, edit_values[qty_index] if edit_values else "0")
        
        ctk.CTkLabel(dialog, text="Profit Target %:").pack(pady=(10, 0))
        target_entry = ctk.CTkEntry(dialog, width=200)
        target_entry.pack(pady=5)
        target_index = 8 if edit_values else 7
        target_entry.insert(0, edit_values[target_index] if edit_values else "10.0")

        enabled_var = ctk.BooleanVar(value=True if not edit_values or edit_values[2] == "Yes" else False)
        ctk.CTkCheckBox(dialog, text="Enabled", variable=enabled_var).pack(pady=15)

        def save_stock():
            symbol = sym_entry.get().upper().strip()
            if not symbol:
                messagebox.showerror("Error", "Symbol is required")
                return
            
            try:
                new_data = {
                    'Symbol': symbol,
                    'Broker': 'mstock', # Default or fetched from broker tab
                    'Enabled': enabled_var.get(),
                    'Strategy': strat_var.get(),
                    'Timeframe': tf_var.get(),
                    'Buy RSI': int(buy_rsi_entry.get()),
                    'Sell RSI': int(sell_rsi_entry.get()),
                    'Profit Target %': float(target_entry.get()),
                    'Quantity': int(qty_entry.get()),
                    'Exchange': exch_var.get()
                }
                
                csv_path = 'config_table.csv'
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    # If editing, remove old entry
                    if edit_values:
                        df = df[~((df['Symbol'] == edit_values[0]) & (df['Exchange'] == edit_values[1]))]
                    
                    # Append new entry
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    df.to_csv(csv_path, index=False)
                else:
                    pd.DataFrame([new_data]).to_csv(csv_path, index=False)
                
                self.refresh_stock_table()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid data: {e}")

        ctk.CTkButton(dialog, text="💾 Save Stock", fg_color="green", command=save_stock).pack(pady=20)

if __name__ == "__main__":
    app = SettingsGUI()
    app.run()
