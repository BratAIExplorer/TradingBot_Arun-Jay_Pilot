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

# --- UI COLOR CONSTANTS (DARK NEON) ---
COLOR_BG = "#0f0f23"      # Deep Navy Background
COLOR_CARD = "#1a1a2e"    # Dark Card Surface
COLOR_ACCENT = "#00d4ff"  # Neon Cyan
COLOR_DANGER = "#ff4757"  # Soft Red
COLOR_SUCCESS = "#00ff88" # Bright Green
COLOR_WARN = "#ffa502"    # Warm Orange
COLOR_TEXT = "#e4e4e7"    # High Contrast Text
COLOR_TEXT_DIM = "#6b7280" # Muted Text
COLOR_BORDER = "#2f2f46"  # Subtle Dark Border

FONT_MONO = ("JetBrains Mono", 11)
FONT_MAIN = ("Inter", 12)
FONT_HEADER = ("Inter", 14, "bold")
FONT_BIG = ("Inter", 32, "bold")

class SettingsSection(ctk.CTkFrame):
    """Reusable settings card wrapper with title and accent pill"""
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER, **kwargs)
        
        # Title Bar
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        # Accent Pill
        ctk.CTkFrame(title_frame, width=4, height=16, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
        
        ctk.CTkLabel(title_frame, text=title.upper(), font=FONT_HEADER, text_color=COLOR_TEXT).pack(side="left", padx=10)

class SettingsGUI:
    def __init__(self, root=None, parent=None, on_save_callback=None):
        # Initialize settings manager
        self.settings_mgr = SettingsManager()
        self.settings_mgr.load()
        self.on_save_callback = on_save_callback
        
        # Theme
        ctk.set_appearance_mode("dark")
        
        self.is_embedded = False
        self.is_toplevel = False
        
        # Validation Cache
        self.validation_cache = {}
        self.load_validation_cache()

        # Window logic
        if parent:
            self.is_embedded = True
        elif root:
            self.is_toplevel = True
        
        if self.is_embedded:
            # When embedded, use a frame instead of making it scrollable here 
            # as the parent container usually handles scrolling for the whole view
            self.root = ctk.CTkFrame(parent, fg_color="transparent")
            self.root.pack(fill="both", expand=True)
        elif self.is_toplevel:
            self.root = ctk.CTkToplevel(root)
            self.root.title("⚙️ Settings")
            self.root.geometry("1000x850")
            self.root.configure(fg_color=COLOR_BG)
        else:
            self.root = ctk.CTk()
            self.root.title("⚙️ Settings Engine")
            self.root.geometry("1000x850")
            self.root.configure(fg_color=COLOR_BG)

        # Tabbed interface - Modern Cyan/Dark styling
        self.tabview = ctk.CTkTabview(self.root, 
                                     segmented_button_selected_color=COLOR_ACCENT,
                                     segmented_button_selected_hover_color="#00b4d4",
                                     segmented_button_unselected_color="#131326",
                                     text_color=COLOR_TEXT,
                                     fg_color="transparent")
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("Broker")
        self.tabview.add("Capital")
        self.tabview.add("Risk Controls")
        self.tabview.add("Notifications")
        self.tabview.add("Buckets & Strategies")
        
        # Build tabs
        self.build_broker_tab()
        self.build_capital_tab()
        self.build_risk_tab()
        self.build_notifications_tab()
        self.build_buckets_tab()
        
        # Bottom Control Bar
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=20, side="bottom")
        
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="💾 SAVE CONFIGURATION",
            command=self.save_settings,
            width=250,
            height=45,
            font=("Inter", 14, "bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#00D477",
            text_color="#000"
        )
        self.save_btn.grid(row=0, column=0, padx=10)
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ CANCEL",
            command=self.on_cancel,
            width=120,
            height=45,
            font=("Inter", 12, "bold"),
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_DIM
        )
        self.cancel_btn.grid(row=0, column=1, padx=10)

        # Bottom Disclaimer
        disclaimer = ctk.CTkLabel(
            self.root,
            text="⚠️ ARUN TITAN ENGINE: Automated utility. User assumes 100% risk for financial outcomes.",
            font=("Inter", 10),
            text_color=COLOR_TEXT_DIM
        )
        disclaimer.pack(side="bottom", pady=(0, 10))

    def load_validation_cache(self):
        """Load validated stocks from cache"""
        try:
            if os.path.exists("validated_stocks.json"):
                with open("validated_stocks.json", "r") as f:
                    self.validation_cache = json.load(f)
        except Exception: pass

    def save_validation_cache(self):
        """Save validated stocks to cache"""
        try:
            with open("validated_stocks.json", "w") as f:
                json.dump(self.validation_cache, f)
        except Exception: pass
    
    def on_cancel(self):
        """Handle Cancel Action"""
        if self.is_embedded:
            # In embedded mode, reload settings and show message
            self.settings_mgr.load()
            messagebox.showinfo("Cancelled", "Changes discarded. Settings not saved.")
        else:
            self.root.destroy()
    
    def build_broker_tab(self):
        """Broker credentials configuration with modernized layout"""
        tab = self.tabview.tab("Broker")
        
        # Main scrollable container for the tab
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        broker = self.settings_mgr.get("broker", {})
        self.broker_var = ctk.StringVar(value=broker.get("name", "mstock"))

        # --- Section: Trading Modes ---
        mode_section = SettingsSection(scroll, title="Engine Operating Modes")
        mode_section.pack(fill="x", pady=10)
        
        # Paper Mode
        self.paper_mode_var = ctk.BooleanVar(value=self.settings_mgr.get("app_settings.paper_trading_mode", True))
        ctk.CTkCheckBox(mode_section, text="SIMULATION MODE (Paper Trading)", variable=self.paper_mode_var,
                        font=FONT_MAIN, text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(mode_section, text="Execute trades in virtual environment using real market data.",
                     font=("Inter", 11), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=50, pady=(0, 10))

        # Nifty 50 Filter
        self.nifty_filter_var = ctk.BooleanVar(value=self.settings_mgr.get("app_settings.nifty_50_only", False))
        ctk.CTkCheckBox(mode_section, text="NIFTY 50 SAFETY FILTER", variable=self.nifty_filter_var,
                        font=FONT_MAIN, text_color=COLOR_SUCCESS).pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(mode_section, text="Restricts the engine to highly liquid Blue Chip stocks only.",
                     font=("Inter", 11), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=50, pady=(0, 15))

        # --- Section: API Credentials ---
        auth_section = SettingsSection(scroll, title="Broker Authenticator")
        auth_section.pack(fill="x", pady=10)
        
        # Grid for Auth Fields
        fields_frame = ctk.CTkFrame(auth_section, fg_color="transparent")
        fields_frame.pack(fill="x", padx=20, pady=10)
        fields_frame.grid_columnconfigure(1, weight=1)

        def add_field(row, label, key, placeholder="", is_pass=True):
            ctk.CTkLabel(fields_frame, text=label, font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=row, column=0, sticky="w", pady=8)
            entry = ctk.CTkEntry(fields_frame, width=300, height=35, placeholder_text=placeholder, 
                                 show="*" if is_pass else "", fg_color="#0a0a1a", border_color=COLOR_BORDER)
            entry.insert(0, self.settings_mgr.get_decrypted(f"broker.{key}", "") if is_pass else broker.get(key, ""))
            entry.grid(row=row, column=1, sticky="w", padx=20, pady=8)
            return entry

        self.api_key_entry = add_field(0, "API KEY", "api_key", "mStock API Key")
        self.api_secret_entry = add_field(1, "API SECRET", "api_secret", "mStock secret")
        self.client_code_entry = add_field(2, "CLIENT ID", "client_code", "Your User ID", is_pass=False)
        self.password_entry = add_field(3, "PASSWORD", "password", "Login Password")
        self.totp_entry = add_field(4, "TOTP SECRET", "totp_secret", "2FA 16-digit-secret")

        # Session Override
        ctk.CTkLabel(fields_frame, text="ACCESS TOKEN", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=5, column=0, sticky="w", pady=8)
        self.access_token_entry = ctk.CTkEntry(fields_frame, width=300, height=35, placeholder_text="Manual override", 
                                              show="*", fg_color="#0a0a1a", border_color=COLOR_BORDER)
        self.access_token_entry.insert(0, self.settings_mgr.get_decrypted("broker.access_token", ""))
        self.access_token_entry.grid(row=5, column=1, sticky="w", padx=20, pady=8)

        # Controls Row
        ctrl_row = ctk.CTkFrame(auth_section, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=20, pady=(0, 20))
        
        self.show_pass_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrl_row, text="Reveal credentials", variable=self.show_pass_var, 
                        command=self.toggle_password_visibility, font=("Inter", 11)).pack(side="left")
        
        ctk.CTkButton(ctrl_row, text="📡 TEST CONNECTIVITY", command=self.test_broker_connection,
                      width=180, height=32, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_ACCENT,
                      hover_color="#1a2e3e", text_color=COLOR_ACCENT).pack(side="right")

    def build_capital_tab(self):
        """Capital management configuration with professional layout"""
        tab = self.tabview.tab("Capital")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        capital = self.settings_mgr.get("capital", {})

        # --- Section: Safety Box ---
        box_section = SettingsSection(scroll, title="Strategy Capital Limit")
        box_section.pack(fill="x", pady=10)
        
        ctk.CTkLabel(box_section, text="Limit the maximum total funds the bot is allowed to deploy at once.",
                     font=("Inter", 11), text_color=COLOR_TEXT_DIM, justify="left").pack(anchor="w", padx=20, pady=(5, 5))
        
        entry_frame = ctk.CTkFrame(box_section, fg_color="transparent")
        entry_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(entry_frame, text="₹", font=("Inter", 18, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        self.allocated_capital_entry = ctk.CTkEntry(entry_frame, width=200, height=40, font=("Inter", 16, "bold"),
                                                   placeholder_text="50000", fg_color="#0a0a1a", border_color=COLOR_ACCENT)
        self.allocated_capital_entry.insert(0, str(capital.get("allocated_limit", 50000)))
        self.allocated_capital_entry.pack(side="left", padx=10)

        # --- Section: Sizing Strategy ---
        sizing_section = SettingsSection(scroll, title="Position Sizing")
        sizing_section.pack(fill="x", pady=10)

        inner = ctk.CTkFrame(sizing_section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        # Method Selection
        self.sizing_method_var = ctk.StringVar(value=capital.get("max_per_stock_type", "percentage"))
        
        method_frame = ctk.CTkFrame(inner, fg_color="transparent")
        method_frame.pack(side="left", fill="y")
        
        ctk.CTkRadioButton(method_frame, text="Portfolio %", variable=self.sizing_method_var, 
                           value="percentage", font=FONT_MAIN).pack(anchor="w", pady=5)
        ctk.CTkRadioButton(method_frame, text="Fixed Amount", variable=self.sizing_method_var, 
                           value="fixed", font=FONT_MAIN).pack(anchor="w", pady=5)

        # Dynamic Sizing Controls (Slider/Entry)
        dynamics = ctk.CTkFrame(inner, fg_color="transparent")
        dynamics.pack(side="right", fill="both", expand=True, padx=(40, 0))

        # Slider for %
        self.per_trade_var = ctk.DoubleVar(value=capital.get("per_trade_pct", 10.0))
        slider_row = ctk.CTkFrame(dynamics, fg_color="transparent")
        slider_row.pack(fill="x")
        ctk.CTkSlider(slider_row, from_=1, to=50, variable=self.per_trade_var, width=200, 
                      progress_color=COLOR_ACCENT, button_color=COLOR_ACCENT,
                      command=lambda val: val_pct.configure(text=f"{val:.1f}%")).pack(side="left")
        val_pct = ctk.CTkLabel(slider_row, text=f"{self.per_trade_var.get():.1f}%", font=("Inter", 12, "bold"), width=60)
        val_pct.pack(side="left", padx=10)

        # Entry for Fixed
        entry_row = ctk.CTkFrame(dynamics, fg_color="transparent")
        entry_row.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(entry_row, text="OR ₹", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).pack(side="left")
        self.fixed_amount_entry = ctk.CTkEntry(entry_row, width=120, height=30, placeholder_text="5000",
                                              fg_color="#0a0a1a", border_color=COLOR_BORDER)
        self.fixed_amount_entry.insert(0, str(capital.get("max_per_stock_fixed_amount", 5000)))
        self.fixed_amount_entry.pack(side="left", padx=10)

        # --- Limits & Reinvestment ---
        limit_section = SettingsSection(scroll, title="Strategy Limits")
        limit_section.pack(fill="x", pady=10)
        
        lim_inner = ctk.CTkFrame(limit_section, fg_color="transparent")
        lim_inner.pack(fill="x", padx=20, pady=15)

        # Max Positions
        ctk.CTkLabel(lim_inner, text="MAX OPEN POSITIONS", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).pack(anchor="w")
        self.max_positions_var = ctk.IntVar(value=capital.get("max_positions", 5))
        max_pos_row = ctk.CTkFrame(lim_inner, fg_color="transparent")
        max_pos_row.pack(fill="x", pady=(5, 15))
        ctk.CTkSlider(max_pos_row, from_=1, to=30, variable=self.max_positions_var, width=300,
                      progress_color=COLOR_SUCCESS, button_color=COLOR_SUCCESS,
                      command=lambda val: val_pos.configure(text=str(int(val)))).pack(side="left")
        val_pos = ctk.CTkLabel(max_pos_row, text=str(self.max_positions_var.get()), font=("Inter", 12, "bold"), width=40)
        val_pos.pack(side="left", padx=10)

        # Compound Toggle
        self.compound_var = ctk.BooleanVar(value=capital.get("compound_profits", False))
        ctk.CTkCheckBox(lim_inner, text="REINVEST PROFITS (Compounding)", variable=self.compound_var,
                        font=FONT_MAIN, text_color=COLOR_SUCCESS).pack(anchor="w")

        # Info Box (Summary)
        info_frame = ctk.CTkFrame(scroll, fg_color="#131326", corner_radius=8)
        info_frame.pack(fill="x", pady=10, padx=5)
        
        self.diag_label = ctk.CTkLabel(info_frame, text="", font=("Inter", 11), text_color=COLOR_TEXT_DIM, justify="left")
        self.diag_label.pack(padx=20, pady=15)
        
        def update_diag(*args):
            try:
                cap = float(self.allocated_capital_entry.get() or 0)
                pct = self.per_trade_var.get()
                max_pos = self.max_positions_var.get()
                per_trade = cap * (pct / 100)
                total_req = per_trade * max_pos
                self.diag_label.configure(text=(
                    f"💡 CALCULATION SUMMARY:\n"
                    f"• Per Trade Allocation: ₹{per_trade:,.2f} ({pct:.1f}%)\n"
                    f"• Max Portfolio Exposure: ₹{total_req:,.2f} across {max_pos} positions\n\n"
                    f"Note: Manual CSV quantities override percentage sizing."
                ))
            except: pass
            
        self.allocated_capital_entry.bind("<KeyRelease>", update_diag)
        self.per_trade_var.trace_add("write", update_diag)
        self.max_positions_var.trace_add("write", update_diag)
        update_diag()

    def build_risk_tab(self):
        """Risk controls configuration with professional safety-first layout"""
        tab = self.tabview.tab("Risk Controls")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        risk = self.settings_mgr.get("risk_controls", {})

        # --- Section: Butler Mode / Manual stocks Global Note ---
        butler_note = ctk.CTkFrame(scroll, fg_color="#1a2e3e", border_width=1, border_color=COLOR_ACCENT, corner_radius=8)
        butler_note.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(butler_note, text="🔔 BUTLER MODE ACTIVE", font=("Inter", 12, "bold"), text_color=COLOR_ACCENT).pack(pady=(10, 2))
        ctk.CTkLabel(butler_note, text="Note: Manually added stocks in the Hybrid Tab use these Global Risk Settings\n(Stop Loss & Profit Target) for exit logic.",
                     font=("Inter", 11), text_color=COLOR_TEXT).pack(pady=(0, 10), padx=20)

        # --- Section: Basic Risk Guards ---
        basic_section = SettingsSection(scroll, title="Strategy Exit Logic")
        basic_section.pack(fill="x", pady=10)
        
        inner = ctk.CTkFrame(basic_section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        def add_risk_slider(row, title, key, default, from_val, to_val, color):
            ctk.CTkLabel(inner, text=title.upper(), font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=row, column=0, sticky="w", pady=10)
            var = ctk.DoubleVar(value=risk.get(key, default))
            slider = ctk.CTkSlider(inner, from_=from_val, to=to_val, variable=var, width=250, 
                                   progress_color=color, button_color=color,
                                   command=lambda val: val_lbl.configure(text=f"{val:.1f}%"))
            slider.grid(row=row, column=1, sticky="w", padx=20, pady=10)
            val_lbl = ctk.CTkLabel(inner, text=f"{var.get():.1f}%", font=("Inter", 12, "bold"), width=60)
            val_lbl.grid(row=row, column=2, sticky="w")
            return var

        self.stop_loss_var = add_risk_slider(0, "Stop Loss", "stop_loss_pct", 5.0, 1, 20, COLOR_DANGER)
        self.profit_target_var = add_risk_slider(1, "Profit Target", "profit_target_pct", 10.0, 2, 50, COLOR_SUCCESS)
        self.cat_stop_var = add_risk_slider(2, "Catastrophic Stop", "catastrophic_stop_loss_pct", 15.0, 10, 50, "#8b0000")
        self.daily_loss_var = add_risk_slider(3, "Daily Drawdown Limit", "daily_loss_limit_pct", 10.0, 5, 30, COLOR_WARN)

        # --- Section: Safety Overrides ---
        safe_section = SettingsSection(scroll, title="Hard Safety Overrides")
        safe_section.pack(fill="x", pady=10)
        
        safe_inner = ctk.CTkFrame(safe_section, fg_color="transparent")
        safe_inner.pack(fill="x", padx=20, pady=15)

        # Never sell at loss
        self.never_sell_at_loss_var = ctk.BooleanVar(value=risk.get("never_sell_at_loss", False))
        ctk.CTkCheckBox(safe_inner, text="NEVER SELL AT LOSS (Ignore Stop-Loss)", variable=self.never_sell_at_loss_var,
                        font=FONT_MAIN, text_color=COLOR_DANGER, command=self.on_never_sell_at_loss_toggled).pack(anchor="w", pady=5)
        ctk.CTkLabel(safe_inner, text="Forces the bot to hold until price recovers. HIGH RISK of capital lockup.",
                     font=("Inter", 10), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=30, pady=(0, 10))

        # 10% Risk Limit
        self.use_10_pct_risk_var = ctk.BooleanVar(value=self.settings_mgr.get("risk_controls.use_10_pct_portfolio_limit", True))
        ctk.CTkCheckBox(safe_inner, text="10% PORTFOLIO EXPOSURE LIMIT", variable=self.use_10_pct_risk_var,
                        font=FONT_MAIN, text_color=COLOR_WARN).pack(anchor="w", pady=5)
        ctk.CTkLabel(safe_inner, text="Prevents any single trade from exceeding 10% of total allocated capital.",
                     font=("Inter", 10), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=30)
    
    def build_buckets_tab(self):
        """Buckets & Strategies configuration with modernized layout"""
        tab = self.tabview.tab("Buckets & Strategies")
        
        # Main scrollable container
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Section: Global Optimization ---
        global_section = SettingsSection(scroll, title="Global Strategy Engine")
        global_section.pack(fill="x", pady=10)
        
        self.use_200_bar_var = ctk.BooleanVar(value=self.settings_mgr.get("strategies.rsi_mean_reversion.use_200_bar_stabilization", True))
        ctk.CTkCheckBox(global_section, text="200-BAR RSI STABILIZATION (Precision Mode)", variable=self.use_200_bar_var,
                        font=FONT_MAIN, text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(global_section, text="Uses 200 bars of historical data for mathematically precise RSI output.",
                     font=("Inter", 11), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=50, pady=(0, 15))

        # --- Section: Stock Buckets ---
        stock_section = SettingsSection(scroll, title="Active Trading Buckets")
        stock_section.pack(fill="both", expand=True, pady=10)

        # Table Control Row
        table_ctrl = ctk.CTkFrame(stock_section, fg_color="transparent")
        table_ctrl.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(table_ctrl, text="INDIVIDUAL SYMBOL RULES", font=("Inter", 11, "bold"), text_color=COLOR_TEXT_DIM).pack(side="left")
        
        # Action Buttons (New compact style)
        def add_btn(text, cmd, color, icon):
            return ctk.CTkButton(table_ctrl, text=text, command=cmd, width=80, height=28, 
                                 fg_color=COLOR_CARD, border_width=1, border_color=color,
                                 hover_color="#1a2e3e", text_color=color, font=("Inter", 11, "bold"))

        add_btn("➕ ADD", self.on_add_stock, COLOR_SUCCESS, "").pack(side="right", padx=5)
        add_btn("✏️ EDIT", self.on_edit_stock, COLOR_ACCENT, "").pack(side="right", padx=5)
        add_btn("🗑 REMOVE", self.on_delete_stock, COLOR_DANGER, "").pack(side="right", padx=5)

        # Treeview (Styled for Dark Neon)
        table_frame = ctk.CTkFrame(stock_section, fg_color="#0a0a1a", corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#0a0a1a", 
                        foreground=COLOR_TEXT, 
                        fieldbackground="#0a0a1a",
                        borderwidth=0,
                        font=("Inter", 10))
        style.configure("Treeview.Heading", 
                        background="#1a1a2e", 
                        foreground=COLOR_ACCENT, 
                        borderwidth=0,
                        font=("Inter", 10, "bold"))
        style.map("Treeview", background=[('selected', '#1e3a5f')])

        self.stock_table = ttk.Treeview(
            table_frame,
            columns=("Symbol", "Exchange", "Enabled", "Strategy", "Timeframe", "Buy RSI", "Sell RSI", "Qty", "Target %", "Status"),
            show="headings",
            height=10
        )
        # Configure headings
        headings = ["Symbol", "Exch", "ON", "Mode", "TF", "Buy", "Sell", "Qty", "Profit %", "Status"]
        for i, col in enumerate(self.stock_table["columns"]):
            self.stock_table.heading(col, text=headings[i])
            self.stock_table.column(col, width=60, anchor="center")
        
        self.stock_table.column("Symbol", width=90)
        self.stock_table.column("Status", width=90)
        self.stock_table.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.stock_table.yview)
        sb.pack(side="right", fill="y")
        self.stock_table.configure(yscrollcommand=sb.set)

        self.refresh_stock_table()
        
        # Validation Row
        val_row = ctk.CTkFrame(stock_section, fg_color="transparent")
        val_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self.validate_btn = ctk.CTkButton(val_row, text="🔍 SCAN & VALIDATE SYMBOLS", command=self.on_validate_symbols,
                                         width=250, height=35, fg_color=COLOR_ACCENT, text_color="#000", font=("Inter", 12, "bold"))
        self.validate_btn.pack(side="left")

    def build_notifications_tab(self):
        """Telegram notifications configuration with modernized layout"""
        tab = self.tabview.tab("Notifications")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        notif = self.settings_mgr.get("notifications", {})

        # --- Section: Telegram Config ---
        tg_section = SettingsSection(scroll, title="Telegram Alert Guard")
        tg_section.pack(fill="x", pady=10)
        
        self.tg_enabled_var = ctk.BooleanVar(value=notif.get("enabled", False))
        ctk.CTkCheckBox(tg_section, text="ENABLE MOBILE ALERTS (Push Notifications)", variable=self.tg_enabled_var,
                        font=FONT_MAIN, text_color=COLOR_SUCCESS).pack(anchor="w", padx=20, pady=(15, 10))

        fields = ctk.CTkFrame(tg_section, fg_color="transparent")
        fields.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(fields, text="BOT TOKEN", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=0, column=0, sticky="w", pady=10)
        self.tg_token_entry = ctk.CTkEntry(fields, width=400, height=35, placeholder_text="Enter API Token from @BotFather",
                                           show="*", fg_color="#0a0a1a", border_color=COLOR_BORDER)
        self.tg_token_entry.insert(0, self.settings_mgr.get_decrypted("notifications.telegram_bot_token", ""))
        self.tg_token_entry.grid(row=0, column=1, sticky="w", padx=20, pady=10)

        ctk.CTkLabel(fields, text="CHAT ID", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=1, column=0, sticky="w", pady=10)
        self.tg_chat_id_entry = ctk.CTkEntry(fields, width=400, height=35, placeholder_text="Enter your Chat ID",
                                             fg_color="#0a0a1a", border_color=COLOR_BORDER)
        self.tg_chat_id_entry.insert(0, str(notif.get("telegram_chat_id", "")))
        self.tg_chat_id_entry.grid(row=1, column=1, sticky="w", padx=20, pady=10)

        # Help Footer
        help_frame = ctk.CTkFrame(tg_section, fg_color="#131326", corner_radius=0)
        help_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(help_frame, text="❓ HOW TO CONNECT: Message @BotFather to create a bot. Get your Chat ID from @userinfobot.",
                     font=("Inter", 11), text_color=COLOR_TEXT_DIM).pack(pady=10)

    def refresh_stock_table(self):
        """Load symbols from CSV into the table"""
        # Clear existing items
        for item in self.stock_table.get_children():
            self.stock_table.delete(item)
        
        csv_path = 'config_table.csv'
        if not os.path.exists(csv_path):
            return
            
        try:
            df = pd.read_csv(csv_path)
            for idx, row in df.iterrows():
                try:
                    values = (
                        row['Symbol'], 
                        row['Exchange'], 
                        "Yes" if str(row['Enabled']).upper() == 'TRUE' else "No",
                        row.get('Strategy', 'TRADE'),
                        row['Timeframe'],
                        row['Buy RSI'],
                        row['Sell RSI'],
                        row['Quantity'],
                        row['Profit Target %'],
                        "Pending"
                    )
                    self.stock_table.insert("", "end", values=values)
                except Exception: pass
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load stocks: {e}")

    def test_broker_connection(self):
        """Test API credentials and fetch balance with enhanced debugging"""
        import datetime
        api_key = self.api_key_entry.get().strip()
        totp_secret = self.totp_entry.get().strip()

        if not api_key or not totp_secret:
            messagebox.showwarning("Missing Data", "Please enter API Key and TOTP Secret to test connection.")
            return

        debug_log = ["🚀 Starting Connectivity Test..."]
        try:
            # 1. Generate TOTP
            totp = pyotp.TOTP(totp_secret)
            otp_code = totp.now()
            debug_log.append(f"✅ TOTP Generated: {otp_code[:2]}****")

            # 2. Verify TOTP
            url = "https://api.mstock.trade/openapi/typea/session/verifytotp"
            payload = {"api_key": api_key, "totp": otp_code}
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Mirae-Version": "1"
            }
            resp = requests.post(url, data=payload, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                messagebox.showerror("Connection Failed", f"Status: {resp.status_code}\nResponse: {resp.text[:200]}")
                return

            data = resp.json()
            if data.get("status") == "success":
                access_token = data["data"]["access_token"]
                self.access_token_entry.delete(0, "end")
                self.access_token_entry.insert(0, access_token)
                
                messagebox.showinfo("✅ Success", "API Connection Successful!\nSession token generated and filled.")
            else:
                messagebox.showerror("Failed", f"mStock Error: {data.get('message', 'Unknown Error')}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Connection Test Failed: {str(e)}")

    def toggle_password_visibility(self):
        """Toggle password and API key field visibility"""
        show = self.show_pass_var.get()
        self.api_key_entry.configure(show="" if show else "*")
        self.api_secret_entry.configure(show="" if show else "*")
        self.password_entry.configure(show="" if show else "*")
        self.access_token_entry.configure(show="" if show else "*")

    def on_validate_symbols(self):
        """Validate all symbols in the table with robust error handling and summary"""
        self.validate_btn.configure(state="disabled", text="VALIDATING...")
        self.root.update_idletasks()
        
        items = self.stock_table.get_children()
        total = len(items)
        valid_count = 0
        errors = []
        
        for i, item in enumerate(items):
            values = list(self.stock_table.item(item, "values"))
            if len(values) < 2: continue
                
            symbol = values[0]
            exchange = values[1]
            key = f"{symbol}_{exchange}"
            
            # Update status to searching
            new_values = list(values)
            new_values[9] = "⏳"
            self.stock_table.item(item, values=new_values)
            self.root.update_idletasks()
            
            # Validate
            is_valid, message = validate_symbol(symbol, exchange)
            
            if is_valid:
                # If it's a "Likely Valid" or other nuanced success, show it
                if "Valid" not in message:
                    status_icon = f"✅ {message}"
                else:
                    status_icon = "✅ Valid"
                valid_count += 1
                self.validation_cache[key] = True
            else:
                if "Found on" in message:
                    status_icon = f"⚠️ {message}"
                else:
                    status_icon = f"❌ {message[:30]}"
                errors.append(f"{symbol}: {message}")
                if key in self.validation_cache: del self.validation_cache[key]
            
            new_values[9] = status_icon
            self.stock_table.item(item, values=new_values)
            self.root.update_idletasks()
        
        self.save_validation_cache()
        self.validate_btn.configure(state="normal", text="🔍 SCAN & VALIDATE SYMBOLS")
        
        if errors:
            error_detail = "\n".join(errors[:5])
            if len(errors) > 5: error_detail += f"\n... and {len(errors) - 5} more"
            messagebox.showwarning("Validation Summary", 
                                f"Validated {total} symbols.\nSuccess: {valid_count}\nFailed: {total - valid_count}\n\nErrors:\n{error_detail}")
        else:
            messagebox.showinfo("Success", f"✅ All {total} symbols validated successfully!")

    def save_settings(self):
        """Save all settings to JSON"""
        try:
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
                    "per_trade_pct": self.per_trade_var.get(),
                    "max_per_stock_fixed_amount": float(self.fixed_amount_entry.get()),
                    "max_positions": self.max_positions_var.get(),
                    "compound_profits": self.compound_var.get()
                },
                "risk_controls": {
                    "stop_loss_pct": self.stop_loss_var.get(),
                    "profit_target_pct": self.profit_target_var.get(),
                    "catastrophic_stop_loss_pct": self.cat_stop_var.get(),
                    "daily_loss_limit_pct": self.daily_loss_var.get(),
                    "never_sell_at_loss": self.never_sell_at_loss_var.get(),
                    "use_10_pct_portfolio_limit": self.use_10_pct_risk_var.get()
                },
                "notifications": {
                    "enabled": self.tg_enabled_var.get(),
                    "telegram_bot_token": self.tg_token_entry.get(),
                    "telegram_chat_id": self.tg_chat_id_entry.get()
                },
                "strategies": {
                    "rsi_mean_reversion": {
                        "use_200_bar_stabilization": self.use_200_bar_var.get()
                    }
                }
            }
            
            # Update and save
            self.settings_mgr.settings.update(new_settings)
            self.settings_mgr.save()
            
            if self.on_save_callback:
                self.on_save_callback()
                messagebox.showinfo("✅ Success", "Settings applied successfully!")
            else:
                if messagebox.askyesno("✅ Success", "Settings saved!\n\nRestart bot to apply changes?"):
                    self.restart_application()
                else:
                    self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to save: {str(e)}")

    def restart_application(self):
        """Restart current process"""
        if os.path.exists("arun_bot.lock"):
            try: os.remove("arun_bot.lock")
            except: pass
        os.startfile(sys.argv[0]) if sys.platform == 'win32' else os.execl(sys.executable, sys.executable, *sys.argv)
        sys.exit(0)

    def show_stock_dialog(self, edit_values=None):
        """Modernized dialog for adding/editing symbols"""
        parent_window = self.root.winfo_toplevel()
        dialog = ctk.CTkToplevel(parent_window)
        dialog.title("SYM ENGINE" if not edit_values else "EDIT SYMBOL")
        dialog.geometry("450x700")
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()//2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height()//2) - 350
        dialog.geometry(f"+{x}+{y}")
        
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        def add_dialog_field(label, var_val, is_opt=False, opts=None):
            ctk.CTkLabel(scroll, text=label, font=FONT_MAIN, text_color=COLOR_TEXT_DIM).pack(anchor="w", pady=(10, 0))
            if is_opt:
                var = ctk.StringVar(value=var_val)
                ctk.CTkOptionMenu(scroll, values=opts, variable=var, fg_color="#0a0a1a", border_width=1, border_color=COLOR_BORDER).pack(fill="x", pady=5)
                return var
            else:
                entry = ctk.CTkEntry(scroll, placeholder_text=label, fg_color="#0a0a1a", border_color=COLOR_BORDER)
                entry.insert(0, str(var_val))
                entry.pack(fill="x", pady=5)
                return entry

        # Fields
        sym_entry = add_dialog_field("SYMBOL (e.g. TATASTEEL)", edit_values[0] if edit_values else "")
        exch_var = add_dialog_field("EXCHANGE", edit_values[1] if edit_values else "NSE", True, ["NSE", "BSE"])
        strat_var = add_dialog_field("STRATEGY MODE", edit_values[3] if edit_values else "TRADE", True, ["TRADE", "INVEST", "SIP"])
        tf_var = add_dialog_field("TIMEFRAME", edit_values[4] if edit_values else "15T", True, ["1T", "5T", "15T", "1H", "1D"])
        
        rsi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        rsi_row.pack(fill="x", pady=10)
        
        ctk.CTkLabel(rsi_row, text="BUY RSI", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=0, column=0, sticky="w")
        buy_rsi_e = ctk.CTkEntry(rsi_row, width=80, fg_color="#0a0a1a", border_color=COLOR_BORDER)
        buy_rsi_e.insert(0, edit_values[5] if edit_values else "35")
        buy_rsi_e.grid(row=1, column=0, pady=5, padx=(0, 20))
        
        ctk.CTkLabel(rsi_row, text="SELL RSI", font=FONT_MAIN, text_color=COLOR_TEXT_DIM).grid(row=0, column=1, sticky="w")
        sell_rsi_e = ctk.CTkEntry(rsi_row, width=80, fg_color="#0a0a1a", border_color=COLOR_BORDER)
        sell_rsi_e.insert(0, edit_values[6] if edit_values else "999")
        sell_rsi_e.grid(row=1, column=1, pady=5)

        qty_entry = add_dialog_field("QUANTITY (0 = AUTO)", edit_values[7] if edit_values else "0")
        target_entry = add_dialog_field("PROFIT TARGET %", edit_values[8] if edit_values else "10.0")
        
        enabled_var = ctk.BooleanVar(value=True if not edit_values or edit_values[2] == "Yes" else False)
        ctk.CTkCheckBox(scroll, text="ENABLE FOR TRADING", variable=enabled_var, font=FONT_MAIN, text_color=COLOR_SUCCESS).pack(pady=20)

        def save_internal():
            symbol = sym_entry.get().upper().strip()
            if not symbol: return
            
            try:
                new_row = {
                    'Symbol': symbol, 'Broker': 'mstock', 'Enabled': enabled_var.get(),
                    'Strategy': strat_var.get(), 'Timeframe': tf_var.get(),
                    'Buy RSI': int(buy_rsi_e.get()), 'Sell RSI': int(sell_rsi_e.get()),
                    'Profit Target %': float(target_entry.get()), 'Quantity': int(qty_entry.get()),
                    'Exchange': exch_var.get()
                }
                
                csv_path = 'config_table.csv'
                df = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
                
                if edit_values:
                    df = df[~((df['Symbol'] == edit_values[0]) & (df['Exchange'] == edit_values[1]))]
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(csv_path, index=False)
                
                self.refresh_stock_table()
                dialog.destroy()
                messagebox.showinfo("Success", f"{symbol} updated!")
            except Exception as e:
                messagebox.showerror("Error", f"Save failed: {e}")

        ctk.CTkButton(scroll, text="💾 SAVE SYMBOL", command=save_internal, height=40, fg_color=COLOR_SUCCESS, text_color="#000", font=("Inter", 12, "bold")).pack(fill="x", pady=10)
        ctk.CTkButton(scroll, text="CANCEL", command=dialog.destroy, height=40, fg_color="transparent", border_width=1, border_color=COLOR_BORDER).pack(fill="x")

    def on_add_stock(self): self.show_stock_dialog()
    def on_edit_stock(self):
        sel = self.stock_table.selection()
        if sel: self.show_stock_dialog(self.stock_table.item(sel[0], "values"))
    def on_delete_stock(self):
        sel = self.stock_table.selection()
        if not sel: return
        vals = self.stock_table.item(sel[0], "values")
        if messagebox.askyesno("Delete", f"Remove {vals[0]}?"):
            df = pd.read_csv('config_table.csv')
            df = df[~((df['Symbol'] == vals[0]) & (df['Exchange'] == vals[1]))]
            df.to_csv('config_table.csv', index=False)
            self.refresh_stock_table()

    def run(self): self.root.mainloop()

if __name__ == "__main__":
    app = SettingsGUI()
    app.run()
