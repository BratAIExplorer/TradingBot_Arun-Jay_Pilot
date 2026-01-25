"""
🎨 ARUN TITAN V2 - The "Titan" UI Update
Matches the precise mockup: Dark Neon, Top Nav, Grid Layout.
"""

import threading
import queue
import customtkinter as ctk
from tkinter import END, ttk, messagebox
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# --- Core Logic Imports ---
try:
    from kickstart import run_cycle, fetch_market_data, config_dict, SYMBOLS_TO_TRACK, calculate_intraday_rsi_tv, is_system_online, safe_get_positions, safe_get_live_positions_merged, reload_config
    from knowledge_center import TOOLTIPS, STRATEGY_GUIDES, get_strategy_guide, get_contextual_tip
    from market_sentiment import MarketSentiment
    from settings_manager import SettingsManager
    from state_manager import StateManager
    state_mgr = StateManager()
    
    # Reload config to ensure fresh access token from settings.json
    reload_config()
    # Import positions fetching from kickstart
    try:
        from kickstart import safe_get_live_positions_merged
    except ImportError:
        safe_get_live_positions_merged = lambda: {}
    # Database (optional)
    try:
        from database.trades_db import TradesDatabase
        db = TradesDatabase()
        DATABASE_AVAILABLE = True
    except ImportError:
        db = None
        DATABASE_AVAILABLE = False
except ImportError as e:
    print(f"CRITICAL: Could not import core modules. ({e})")
    sys.exit(1)

# --- UI CONSTANTS (DARK NEON THEME) ---
COLOR_BG = "#0f0f23"      # Deep Navy Background
COLOR_CARD = "#1a1a2e"    # Dark Card Surface
COLOR_ACCENT = "#00d4ff"  # Neon Cyan
COLOR_DANGER = "#ff4757"  # Soft Red
COLOR_SUCCESS = "#00ff88" # Bright Green
COLOR_WARN = "#ffa502"    # Warm Orange
COLOR_TEXT = "#e4e4e7"    # High Contrast Text
COLOR_TEXT_DIM = "#6b7280" # Muted Text
COLOR_BORDER = "#2f2f46"  # Subtle Dark Border

FONT_MONO = ("JetBrains Mono", 11)   # For prices, numbers
FONT_MAIN = ("Inter", 12)            # Body text
FONT_HEADER = ("Inter", 14, "bold")  # Section titles
FONT_BIG = ("Inter", 32, "bold")     # Hero numbers

class TitanCard(ctk.CTkFrame):
    """A standardized Titan-style card with clean borders"""
    def __init__(self, parent, title=None, border_color=COLOR_BORDER, **kwargs):
        super().__init__(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=border_color, **kwargs)
        if title:
            # Title Bar
            self.title_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
            self.title_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            # Accent Pill
            ctk.CTkFrame(self.title_frame, width=4, height=16, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
            
            ctk.CTkLabel(self.title_frame, text=title.upper(), font=FONT_HEADER, text_color=COLOR_TEXT_DIM).pack(side="left", padx=10)

class DashboardV2:
    def __init__(self, root):
        # 1. Setup Window (Root passed from main)
        self.root = root
        self.root.title("ARUN TITAN V2")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=COLOR_BG)
        
        self.settings_mgr = SettingsManager()
        self.sentiment_engine = MarketSentiment()
        
        # Internals
        self.stop_update_flag = threading.Event()
        self.data_queue = queue.Queue(maxsize=100)
        self.running = False
        self.alerts_list = [] # Store recent alerts
        
        # Trade Activity Tracking
        self.trade_stats = {'attempts': 0, 'success': 0, 'failed': 0}
        self.all_positions_data = {}  # Store for filtering
        self.cached_perf = {}         # Prevent UI flickering
        self.cached_wallet = {}       # Store wallet state

        # Log redirection (Safely redirect stdout, leave stderr for crash visibility)
        sys.stdout.write = self.write_log
        # sys.stderr.write = self.write_log  # Temporarily disabled to catch startup crashes

        # --- LAYOUT CONSTRUCTION ---
        self.build_header()
        
        # Main Container (Switched by Nav)
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Build Views
        self.view_dashboard = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_strategies = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_settings = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_knowledge = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_logs = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_start = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_hybrid = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_trades = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        self.build_dashboard_view()
        self.build_strategies_view()
        self.build_settings_view()
        self.build_knowledge_view()
        self.build_logs_view()
        self.build_start_here_view()
        self.build_hybrid_view()
        self.build_trades_view()
        
        # Default View (show START HERE for new users, else Dashboard)
        if self.settings_mgr.get("capital.allocated_limit", 0) <= 0:
            self.show_view("DASHBOARD") # Forced for now to see screen
        else:
            self.show_view("DASHBOARD")

        # Start Logic
        self.start_background_threads()
        self.update_ui_loop()

        # Initial balance load (delayed to allow UI to render)
        self.root.after(2000, self.refresh_balance)

        # Auto-refresh balance every 15 minutes
        self.balance_refresh_timer()

    def start_background_threads(self):
        """Start background worker threads for data fetching"""
        # Ensure logs are connected if not already
        sys.stdout.write = self.write_log
        
        self.write_log("ℹ Monitoring Modules Active. Engine is STOPPED. Waiting for Command.\n")
        # INSTANT: Load cached holdings before anything else
        self.load_cached_holdings()
        
        threading.Thread(target=self.sentiment_worker, daemon=True).start()
        threading.Thread(target=self.positions_worker, daemon=True).start()

    def update_ui_loop(self):
        """Main UI Update Loop (Consumer)"""
        try:
            # 1. Update Monitor Timestamp (Visual Heartbeat)
            now_dt = datetime.now()
            now = now_dt.strftime("%H:%M:%S")
            if hasattr(self, 'positions_label'):
                self.positions_label.configure(text=f"📊 Live Positions (Last Check: {now})")
            
            # 2. Consume Data Queue (Limit per loop to avoid blocking)
            updates_processed = 0
            while not self.data_queue.empty() and updates_processed < 50:
                try:
                    msg = self.data_queue.get_nowait()
                    kind, data = msg
                    if kind == "positions":
                        self.update_positions(data)
                    elif kind == "sentiment":
                        self.update_sentiment(data)
                    updates_processed += 1
                except queue.Empty:
                    break
        except Exception as e:
            # Avoid logging on every tick if it's a minor error
            if "invalid command name" not in str(e):
                # We use sys.__stderr__ here because stdout/stderr might be redirected
                print(f"UI Loop Error: {e}", file=sys.__stderr__)
            
        # Loop every 1 second
        self.root.after(1000, self.update_ui_loop)

    def load_cached_holdings(self):
        """Loads positions from local cache/db to show initial UI instantly"""
        try:
            # Try to get from StateManager if it has them
            cached = state_mgr.state.get('last_positions', {})
            if cached:
                self.update_positions(cached)
                self.write_log("ℹ Loaded cached portfolio holdings.\n")
        except (AttributeError, KeyError, TypeError) as e:
            # BUG-004 FIX: Log specific state loading errors
            self.write_log(f"⚠️ Could not load cached positions: {e}\n")
        except Exception as e:
            # BUG-004 FIX: Catch unexpected errors
            self.write_log(f"⚠️ Unexpected error loading positions: {e}\n")

    def update_sentiment(self, data):
        """No-op for compatibility"""
        pass

    def balance_refresh_timer(self):
        """Refresh balance every 15 minutes automatically"""
        self.refresh_balance()
        self.root.after(900000, self.balance_refresh_timer)

    def refresh_bot_settings(self):
        """Callback to reload settings when saved in GUI"""
        if self.settings_mgr.load():
             self.write_log("✅ Settings Reloaded Successfully.\n")
             # Re-sync allocated capital limit
             reload_config()
        else:
             self.write_log("❌ Failed to reload settings.\n")

    def show_view(self, view_name):
        # List of all views to ensure clean switching
        all_views = [
            self.view_dashboard, self.view_strategies, self.view_settings, 
            self.view_knowledge, self.view_logs, self.view_start, self.view_hybrid,
            self.view_trades
        ]
        
        # Hide everything
        for view in all_views:
            view.pack_forget()
        
        # Show selected
        if view_name == "DASHBOARD":
            self.view_dashboard.pack(fill="both", expand=True)
        elif view_name == "STRATEGIES":
            self.view_strategies.pack(fill="both", expand=True)
        elif view_name == "SETTINGS":
            self.view_settings.pack(fill="both", expand=True)
        elif view_name == "KNOWLEDGE":
            self.view_knowledge.pack(fill="both", expand=True)
        elif view_name == "LOGS":
            self.view_logs.pack(fill="both", expand=True)
            self.refresh_technical_logs()
        elif view_name == "START HERE":
            self.view_start.pack(fill="both", expand=True)
        elif view_name == "HYBRID":
            self.view_hybrid.pack(fill="both", expand=True)
            self.refresh_hybrid_holdings()
        elif view_name == "TRADES":
            self.view_trades.pack(fill="both", expand=True)

        # Update Nav Bar SegmentedButton for consistency if changed programmatically
        if hasattr(self, 'nav_bar'):
            self.nav_bar.set(view_name)

    def build_header(self):
        """Top Navigation Bar & Branding - Optimized for Width"""
        self.header = ctk.CTkFrame(self.root, height=60, fg_color=COLOR_CARD, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.header.pack(fill="x", side="top")
        
        # Left: Branding
        brand_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        brand_frame.pack(side="left", padx=(25, 10))
        
        ctk.CTkLabel(brand_frame, text="ARUN", font=("Inter", 20, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        ctk.CTkLabel(brand_frame, text="TITAN V2", font=("Inter", 12), text_color=COLOR_TEXT_DIM).pack(side="left", padx=10, pady=(5,0))
        
        # Middle: Nav Buttons
        self.nav_bar = ctk.CTkSegmentedButton(self.header, 
                                             values=["DASHBOARD", "HYBRID", "TRADES", "KNOWLEDGE", "STRATEGIES", "SETTINGS", "LOGS"],
                                             command=self.show_view,
                                             font=("Inter", 11, "bold"),
                                             height=32,
                                             dynamic_resizing=True,
                                             selected_color=COLOR_ACCENT,
                                             unselected_color=COLOR_BG,
                                             selected_hover_color="#00b4d4",
                                             unselected_hover_color="#222233",
                                             text_color=COLOR_TEXT)
        self.nav_bar.pack(side="left", fill="x", expand=True, padx=40)
        self.nav_bar.set("DASHBOARD")
        
        # Right: Account Summary (Quick View)
        balance_frame = ctk.CTkFrame(self.header, fg_color=COLOR_BG, height=35, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        balance_frame.pack(side="right", padx=(10, 25), pady=12)
        
        ctk.CTkLabel(balance_frame, text="BALANCE:", font=("Inter", 10, "bold"), text_color=COLOR_TEXT_DIM).pack(side="left", padx=(15,5))
        self.lbl_total_balance = ctk.CTkLabel(balance_frame, text="₹0.00", font=("JetBrains Mono", 14, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_total_balance.pack(side="left", padx=(0,15))

    def build_dashboard_view(self):
        """Redesigned Dashboard v2: Professional 3-Column Layout"""
        for widget in self.view_dashboard.winfo_children():
            widget.destroy()

        # 1. Top Section: Compact Engine Commander
        commander_frame = ctk.CTkFrame(self.view_dashboard, fg_color=COLOR_CARD, height=60, border_width=1, border_color=COLOR_BORDER)
        commander_frame.pack(fill="x", pady=(0, 15))
        
        # Status & Regime (Left)
        status_frame = ctk.CTkFrame(commander_frame, fg_color="transparent")
        status_frame.pack(side="left", fill="y", padx=20)
        
        self.lbl_engine_status = ctk.CTkLabel(status_frame, text="STATUS: STOPPED", font=("Inter", 12, "bold"), text_color=COLOR_DANGER)
        self.lbl_engine_status.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(status_frame, text="|", text_color=COLOR_BORDER).pack(side="left")
        
        self.lbl_market_regime = ctk.CTkLabel(status_frame, text="REGIME: ANALYSIS PENDING", font=("Inter", 12), text_color=COLOR_TEXT_DIM)
        self.lbl_market_regime.pack(side="left", padx=15)

        # Controls (Right)
        # Start/Stop Button (Compact)
        self.btn_start = ctk.CTkButton(commander_frame, text="▶ START SYSTEM", font=("Inter", 12, "bold"),
                                      fg_color=COLOR_SUCCESS, hover_color="#00C853", text_color="#000", height=32, width=140,
                                      command=self.toggle_bot)
        self.btn_start.pack(side="right", padx=20, pady=12)

        # 2. Main Workspace (Grid: Left 75% | Right 25%)
        grid_frame = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure(0, weight=3) # Main Monitor + Logs
        grid_frame.grid_columnconfigure(1, weight=1) # Sidebar
        grid_frame.grid_rowconfigure(0, weight=1)

        # --- LEFT COLUMN (Monitoring + Activity) ---
        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # 2.1 Live Position Monitor (Top 60%)
        monitor_card = TitanCard(left_col, title="Live Position Monitor")
        monitor_card.pack(fill="both", expand=True, pady=(0, 15))
        
        # Stats Row
        stats_row = ctk.CTkFrame(monitor_card, fg_color="transparent")
        stats_row.pack(fill="x", padx=15, pady=(5, 10))
        self.lbl_position_stats = ctk.CTkLabel(stats_row, text="🟢 Live --:-- • 0 positions (Bot: 0 | Manual: 0)", 
                                             font=("Inter", 11), text_color=COLOR_TEXT_DIM)
        self.lbl_position_stats.pack(side="left")
        
        self.build_positions_table(monitor_card)

        # 2.2 Activity Stream (Bottom 40%) - Expanded
        log_frame = TitanCard(left_col, title="Activity Stream")
        log_frame.pack(fill="both", expand=True) # expand=True ensures it fills space
        
        self.trade_log = ctk.CTkTextbox(log_frame, font=("JetBrains Mono", 11), fg_color="transparent", 
                                       text_color=COLOR_TEXT_DIM, border_width=0, activate_scrollbars=True)
        self.trade_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.trade_log.configure(state="disabled")

        # --- RIGHT COLUMN (Sidebar Summary) ---
        right_panel = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # 2.3 Performance Summary
        pnl_card = TitanCard(right_panel, title="Performance Summary", height=160)
        pnl_card.pack(fill="x", pady=(0, 15))
        
        self.lbl_pnl = ctk.CTkLabel(pnl_card, text="₹0.00", font=("JetBrains Mono", 32, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_pnl.pack(pady=(20, 5))
        ctk.CTkLabel(pnl_card, text="TOTAL NET P&L", font=("Inter", 10, "bold"), text_color=COLOR_TEXT_DIM).pack()
        
        stats_grid = ctk.CTkFrame(pnl_card, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=15)
        
        self.lbl_trade_count = ctk.CTkLabel(stats_grid, text="0 trades", font=("Inter", 11), text_color=COLOR_TEXT_DIM)
        self.lbl_trade_count.pack(side="left")
        
        self.lbl_win_rate = ctk.CTkLabel(stats_grid, text="0% Win", font=("Inter", 11, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_win_rate.pack(side="right")

        # 2.4 Quick Stats (New Actionable Metrics)
        quick_card = TitanCard(right_panel, title="Quick Stats")
        quick_card.pack(fill="x", pady=(0, 15))
        
        self.quick_stats_frame = ctk.CTkFrame(quick_card, fg_color="transparent")
        self.quick_stats_frame.pack(fill="x", padx=15, pady=10)
        # Placeholders for now
        ctk.CTkLabel(self.quick_stats_frame, text="Risk Level: LOW", font=FONT_MAIN, text_color=COLOR_SUCCESS).pack(anchor="w")
        ctk.CTkLabel(self.quick_stats_frame, text="Next Action: MONITOR", font=FONT_MAIN, text_color=COLOR_ACCENT).pack(anchor="w")

        # 2.5 Bot Wallet Breakdown
        wallet_card = TitanCard(right_panel, title="Bot Wallet Breakdown")
        wallet_card.pack(fill="both", expand=True) # Fills remaining height
        
        # Allocated
        self.lbl_total_allocated = ctk.CTkLabel(wallet_card, text="₹0", font=("JetBrains Mono", 20, "bold"), text_color=COLOR_TEXT)
        self.lbl_total_allocated.pack(pady=(20, 2))
        ctk.CTkLabel(wallet_card, text="LIMIT ALLOCATED", font=("Inter", 10, "bold"), text_color=COLOR_TEXT_DIM).pack()
        
        # Usage Bar
        self.wallet_progress = ctk.CTkProgressBar(wallet_card, height=8, fg_color="#111", progress_color=COLOR_ACCENT)
        self.wallet_progress.pack(fill="x", padx=20, pady=20)
        self.wallet_progress.set(0)
        
        usage_row = ctk.CTkFrame(wallet_card, fg_color="transparent")
        usage_row.pack(fill="x", padx=20)
        
        self.lbl_deployed = ctk.CTkLabel(usage_row, text="₹0 Deployed", font=("Inter", 11), text_color=COLOR_WARN)
        self.lbl_deployed.pack(side="left")
        
        self.lbl_available_wallet = ctk.CTkLabel(usage_row, text="₹0 Available", font=("Inter", 11), text_color=COLOR_TEXT_DIM)
        self.lbl_available_wallet.pack(side="right")

        # Start refresh loops
        self.refresh_quick_monitor()

    def build_positions_table(self, parent):
        # Filter/View Toggle
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent", height=35)
        filter_frame.pack(fill="x", padx=10, pady=(5, 0))

        ctk.CTkLabel(filter_frame, text="FILTER:", font=("Inter", 10, "bold"), text_color=COLOR_TEXT_DIM).pack(side="left", padx=(5, 10))

        self.holdings_filter_var = ctk.StringVar(value="ALL")
        filter_segment = ctk.CTkSegmentedButton(filter_frame, 
                                             values=["ALL", "BOT", "MANUAL"],
                                             variable=self.holdings_filter_var,
                                             command=self.filter_positions_display,
                                             font=("Inter", 10, "bold"),
                                             height=24,
                                             selected_color=COLOR_ACCENT,
                                             unselected_color="#222",
                                             selected_hover_color="#00b4d4",
                                             text_color=COLOR_TEXT)
        filter_segment.pack(side="left")

        # Treeview styling - Dark Neon
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background=COLOR_CARD, 
                        foreground=COLOR_TEXT, 
                        fieldbackground=COLOR_CARD, 
                        borderwidth=0,
                        rowheight=35,
                        font=FONT_MONO)
        style.configure("Treeview.Heading", 
                        background="#0a0a1a", 
                        foreground=COLOR_TEXT_DIM, 
                        borderwidth=0,
                        font=FONT_HEADER)
        style.map("Treeview", 
                  background=[('selected', COLOR_ACCENT)], 
                  foreground=[('selected', '#000')])

        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        cols = ("SYMBOL", "SOURCE", "QTY", "AVG PRICE", "LTP", "P&L", "P&L %")
        self.pos_table = ttk.Treeview(table_frame, columns=cols, show="headings", style="Treeview")
        
        for col in cols:
            self.pos_table.heading(col, text=col)
            self.pos_table.column(col, anchor="center", width=100)
            
        self.pos_table.column("SYMBOL", anchor="w", width=150)
        
        # Tags for colors
        self.pos_table.tag_configure("green", foreground=COLOR_SUCCESS)
        self.pos_table.tag_configure("red", foreground=COLOR_DANGER)
        self.pos_table.tag_configure("bot", background="#141426") # Slightly darker for bot rows
        
        self.pos_table.pack(fill="both", expand=True)

    def build_strategies_view(self):
        """Mockup for managing algorithm strategies"""
        scroll = ctk.CTkScrollableFrame(self.view_strategies, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="⚡ TRADING STRATEGIES", font=("Inter", 24, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, 20))
        
        # Strategy Filter/Config
        control_frame = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, height=60)
        control_frame.pack(fill="x", pady=(0, 20))
        
        # Sector Panic Sell
        ctk.CTkLabel(control_frame, text="SECTOR CONTROL:", font=("Roboto", 11, "bold")).pack(side="left", padx=20)
        sector_var = ctk.StringVar(value="Select Sector")
        sector_opt = ctk.CTkOptionMenu(control_frame, values=["IT", "BANKING", "AUTO", "PHARMA", "METAL"], variable=sector_var, width=150)
        sector_opt.pack(side="left", padx=10)
        
        ctk.CTkButton(control_frame, text="SELL SECTOR", fg_color=COLOR_DANGER, width=120, command=lambda: self.panic_sell_sector(sector_var.get())).pack(side="left", padx=10)

        # Strategy Library
        self.build_strategies_grid(scroll)

    def build_strategies_grid(self, scroll_frame):
        """Grid of strategy cards with toggles"""
        algo_grid = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        algo_grid.pack(fill="x")
        algo_grid.grid_columnconfigure(0, weight=1)
        algo_grid.grid_columnconfigure(1, weight=1)

        # Helper to make cards
        def make_strat_card(parent, title, desc, col, row):
            card = TitanCard(parent, title=title, height=150)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
            ctk.CTkLabel(card, text=desc, font=("Roboto", 12), text_color="#CCC", wraplength=350, justify="left").pack(anchor="w", padx=15, pady=5)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkSwitch(btn_frame, text="Active").pack(side="right")
            ctk.CTkButton(btn_frame, text="Configure", width=80, height=24, fg_color="#333", hover_color="#444").pack(side="left")

        # Strategies
        make_strat_card(algo_grid, "RSI MEAN REVERSION", "Classic Overbought/Oversold logic optimized for 15m charts.", 0, 0)
        make_strat_card(algo_grid, "MOMENTUM CHASER", "Trend following on volume breakouts with VWAP confirmation.", 1, 0)
        make_strat_card(algo_grid, "DEEP DIP BUYER", "Buys aggressive dips below Bollinger bands during bull markets.", 0, 1)
        make_strat_card(algo_grid, "SCALP MASTER", "High-frequency in-out trades across liquid counters.", 1, 1)

    def build_settings_view(self):
        """Settings View Content"""
        from settings_gui import SettingsGUI
        try:
             self.settings_gui_instance = SettingsGUI(parent=self.view_settings, on_save_callback=self.refresh_bot_settings)
        except Exception as e:
             ctk.CTkLabel(self.view_settings, text=f"Error loading Settings: {e}").pack()

    def build_knowledge_view(self):
        """Knowledge Base / Help Tab"""
        scroll = ctk.CTkScrollableFrame(self.view_knowledge, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="🧠 KNOWLEDGE INTELLIGENCE", font=("Roboto", 24, "bold"), text_color="white").pack(anchor="w", pady=(0, 20))
        
        # Load Tips
        tips = []
        try:
            import json
            if os.path.exists("strategies/trading_tips.json"):
                with open("strategies/trading_tips.json", "r") as f:
                    tips = json.load(f)
            else:
                 tips = [{"title": "Welcome", "content": "Trading tips will appear here once JSON is populated."}]
        except Exception:
            tips = [{"title": "Welcome", "content": "Trading tips will appear here."}]
            
        import random
        daily_tip = random.choice(tips) if tips else {"title": "Welcome", "content": "Keep learning!"}
        
        # Tip of the Day
        tip_card = TitanCard(scroll, title=f"💡 TIP OF THE DAY: {daily_tip['title']}", height=120, border_color="#FFD700")
        tip_card.pack(fill="x", pady=10)
        ctk.CTkLabel(tip_card, text=daily_tip['content'], font=("Roboto", 14), text_color="#EEE", 
                     wraplength=800, justify="left").pack(padx=20, pady=20, anchor="w")
                     
        # Library
        ctk.CTkLabel(scroll, text="TRADING LIBRARY", font=("Roboto", 18, "bold"), text_color="#AAA").pack(anchor="w", pady=(20, 10))
        for tip in tips:
            card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, corner_radius=6, border_width=1, border_color="#333")
            card.pack(fill="x", pady=5)
            ctk.CTkLabel(card, text=tip['title'], font=("Roboto", 12, "bold"), text_color="white").pack(anchor="w", padx=10, pady=(10,0))
            ctk.CTkLabel(card, text=tip['content'], font=("Roboto", 11), text_color="#888", wraplength=800, justify="left").pack(anchor="w", padx=10, pady=(0,10))

    def build_logs_view(self):
        """Technical Logs View - Optimized for readability"""
        header = ctk.CTkFrame(self.view_logs, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        # Title with accent
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkFrame(title_frame, width=4, height=24, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
        ctk.CTkLabel(title_frame, text=" TECHNICAL LOG STREAM", font=("Inter", 20, "bold"), text_color=COLOR_TEXT).pack(side="left", padx=10)
        
        ctk.CTkButton(header, text="🔄 REFRESH LOGS", width=140, height=32, command=self.refresh_technical_logs, 
                      fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER, 
                      hover_color="#1a2e3e", text_color=COLOR_ACCENT, font=("Inter", 11, "bold")).pack(side="right")
        
        # Log Content - High Contrast Cyan on Deep Navy
        self.log_viewer = ctk.CTkTextbox(self.view_logs, font=("JetBrains Mono", 12), 
                                         text_color=COLOR_ACCENT, fg_color=COLOR_BG, 
                                         border_width=1, border_color=COLOR_BORDER)
        self.log_viewer.pack(fill="both", expand=True)
        
    def refresh_technical_logs(self):
        """Read 200 lines from bot.log"""
        try:
            log_path = os.path.join("logs", "bot.log")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    content = "".join(lines[-200:])
                    self.log_viewer.delete("1.0", "end")
                    self.log_viewer.insert("1.0", content)
                    self.log_viewer.see("end")
            else:
                self.log_viewer.insert("1.0", "No log file found at logs/bot.log")
        except Exception as e:
            self.log_viewer.insert("end", f"\nError reading logs: {e}")

    def build_start_here_view(self):
        """Onboarding Guide Tab"""
        header = ctk.CTkFrame(self.view_start, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="🚀 START HERE: Quick Setup Guide", font=("Roboto", 24, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
        
        steps_frame = ctk.CTkScrollableFrame(self.view_start, fg_color="transparent")
        steps_frame.pack(fill="both", expand=True, padx=40)
        
        def add_step(parent, num, title, desc, btn_text, target):
            card = TitanCard(parent, title=f"STEP {num}: {title}", height=130)
            card.pack(fill="x", pady=10)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="both", expand=True, padx=20, pady=10)
            ctk.CTkLabel(row, text=desc, font=("Arial", 12), text_color="#CCC", justify="left").pack(side="left", anchor="w")
            ctk.CTkButton(row, text=btn_text, width=150, command=lambda: self.nav_bar.set(target) or self.show_view(target)).pack(side="right")

        add_step(steps_frame, 1, "CONNECT BROKER", "Go to Settings > Broker tab. Enter API Key & Secret.", "Broker Settings", "SETTINGS")
        add_step(steps_frame, 2, "ALLOCATE FUNDS", "Set your capital limit in Settings > Capital.", "Capital Settings", "SETTINGS")
        add_step(steps_frame, 3, "SELECT STOCKS", "Choose symbols in Settings > Stocks.", "Strategy Settings", "STRATEGIES")
        add_step(steps_frame, 4, "LAUNCH ENGINE", "Click START ENGINE on the Dashboard.", "Go to Dashboard", "DASHBOARD")

    def build_hybrid_view(self):
        """View for managing existing holdings with the Butler Toggle"""
        scroll = ctk.CTkScrollableFrame(self.view_hybrid, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header Section
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="🤝 HYBRID PORTFOLIO TAKE-OVER", font=("Inter", 24, "bold"), text_color=COLOR_ACCENT).pack(anchor="w")
        
        # Butler Note
        note_frame = ctk.CTkFrame(scroll, fg_color="#1a2e3e", border_width=1, border_color=COLOR_ACCENT, corner_radius=8)
        note_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(note_frame, text="🔔 BUTLER FUNCTIONALITY", font=("Inter", 12, "bold"), text_color=COLOR_ACCENT).pack(pady=(10, 2))
        ctk.CTkLabel(note_frame, text="Manually added positions tracked here will use Global Risk Settings for automated exit logic.\nEnable 'Butler Mode' to let the engine monitor your manual trades.",
                     font=("Inter", 11), text_color=COLOR_TEXT).pack(pady=(0, 10), padx=20)

        self.hybrid_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.hybrid_list_frame.pack(fill="both", expand=True)
        
        self.refresh_hybrid_holdings()

    def refresh_hybrid_holdings(self):
        """Repopulate the hybrid management list from state/api"""
        for widget in self.hybrid_list_frame.winfo_children():
            widget.destroy()
            
        try:
            positions = self.all_positions_data or safe_get_live_positions_merged()
            manual_stocks = {k: v for k, v in positions.items() if v.get('source') == 'MANUAL'}
            
            watched = self.settings_mgr.get("app_settings.watched_manual_positions", [])
            
            if not manual_stocks:
                ctk.CTkLabel(self.hybrid_list_frame, text="No manual holdings found in your broker account.", 
                             font=("Inter", 14), text_color=COLOR_TEXT_DIM).pack(pady=50)
                return
                
            for key, pos in manual_stocks.items():
                sym = key[0] if isinstance(key, tuple) else str(key)
                row = TitanCard(self.hybrid_list_frame, border_color=COLOR_BORDER, height=60)
                row.pack(fill="x", pady=5)
                
                # Symbol Info
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", padx=20, fill="y")
                ctk.CTkLabel(info, text=sym, font=("Inter", 16, "bold"), text_color=COLOR_TEXT).pack(side="left")
                ctk.CTkLabel(info, text=f"({pos.get('exchange', 'NSE')})", font=("Inter", 11), text_color=COLOR_TEXT_DIM).pack(side="left", padx=5)
                
                # Butler Switch
                is_on = sym in watched
                sw = ctk.CTkSwitch(row, text="Butler Mode", progress_color=COLOR_SUCCESS, 
                                   command=lambda s=sym: self.toggle_butler_mode(s))
                if is_on: sw.select()
                sw.pack(side="right", padx=20)
                
                # Context Label
                ctk.CTkLabel(row, text="AUTOPILOT EXIT" if is_on else "MANUAL ONLY", 
                             font=("Inter", 10, "bold"), 
                             text_color=COLOR_SUCCESS if is_on else COLOR_TEXT_DIM).pack(side="right", padx=10)
        except Exception as e:
            self.write_log(f"⚠️ Error refreshing hybrid holdings: {e}\n")

    def toggle_butler_mode(self, symbol):
        """Add/Remove symbol from manual watch list"""
        watched = self.settings_mgr.get("app_settings.watched_manual_positions", [])
        if symbol in watched:
            watched.remove(symbol)
            self.write_log(f"🤝 Butler Mode DISABLED for {symbol}. Position is now manual-only.\n")
        else:
            watched.append(symbol)
            self.write_log(f"🤝 Butler Mode ENABLED for {symbol}. Engine will use Global Risk settings to monitor exit.\n")
        
        self.settings_mgr.set("app_settings.watched_manual_positions", watched)
        self.refresh_hybrid_holdings()

    def build_trades_view(self):
        """Dedicated view for monitoring LIVE trade requests and execution stats"""
        # Header
        header = ctk.CTkFrame(self.view_trades, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20), padx=20)
        
        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkFrame(title_frame, width=4, height=24, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
        ctk.CTkLabel(title_frame, text=" LIVE TRADE MONITOR", font=("Inter", 20, "bold"), text_color=COLOR_TEXT).pack(side="left", padx=10)

        # 1. Counter Row
        counter_row = ctk.CTkFrame(self.view_trades, fg_color="transparent")
        counter_row.pack(fill="x", pady=(0, 20), padx=20)
        
        def make_count_box(parent, title, color):
            box = TitanCard(parent, title=title, border_color=COLOR_BORDER)
            box.pack(side="left", fill="both", expand=True, padx=5)
            # Override title color to match box theme
            lbl = ctk.CTkLabel(box, text="0", font=("JetBrains Mono", 36, "bold"), text_color=color)
            lbl.pack(pady=20)
            return lbl

        self.lbl_trades_attempts = make_count_box(counter_row, "TOTAL ATTEMPTS", COLOR_ACCENT)
        self.lbl_trades_success = make_count_box(counter_row, "SUCCESS EXECUTIONS", COLOR_SUCCESS)
        self.lbl_trades_failed = make_count_box(counter_row, "FAILED / REJECTED", COLOR_DANGER)

        # 2. Execution Log
        log_card = TitanCard(self.view_trades, title="ORDER EXECUTION STREAM")
        log_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.trades_log_viewer = ctk.CTkTextbox(log_card, font=("JetBrains Mono", 12), 
                                               fg_color=COLOR_BG, text_color=COLOR_ACCENT,
                                               border_width=0)
        self.trades_log_viewer.pack(fill="both", expand=True, padx=10, pady=10)
        self.trades_log_viewer.configure(state="disabled")

    def toggle_bot(self):
        if not self.running: self.start_bot()
        else: self.stop_bot()

    def start_bot(self):
        import kickstart
        kickstart.reset_stop_flag()
        kickstart.set_log_callback(self.write_log)
        kickstart.initialize_from_csv()
        self.running = True
        self.btn_start.configure(text="🛑 STOP ENGINE", fg_color=COLOR_DANGER, hover_color="#D50000")
        self.write_log("🚀 ENGINE STARTED. Waiting for data...\n")
        threading.Thread(target=self.engine_loop, daemon=True).start()

    def stop_bot(self):
        if messagebox.askyesno("STOP", "Stop Trading Engine?"):
            import kickstart
            kickstart.request_stop()
            self.running = False
            self.btn_start.configure(text="▶ START ENGINE", fg_color=COLOR_SUCCESS, hover_color="#00C853")
            self.write_log("🛑 Engine Stopped.\n")

    def engine_loop(self):
        import kickstart
        while not self.stop_update_flag.is_set() and self.running:
            try:
                kickstart.run_cycle()
            except Exception as e:
                self.write_log(f"Engine Cycle Error: {e}\n")
            time.sleep(1)

    def refresh_quick_monitor(self):
        """Refresh Quick Monitor labels using non-blocking thread"""
        def background_refresh():
            try:
                perf = db.get_performance_summary(days=1) if DATABASE_AVAILABLE else {}
                recent = db.get_recent_trades(limit=5) if DATABASE_AVAILABLE else []
                counters = state_mgr.get_trade_counters()

                # Retrieve allocated capital
                allocated = self.settings_mgr.get("capital.allocated_limit", 0)

                self.root.after(0, lambda: self._update_quick_monitor_ui(perf, recent, counters, allocated))
            except (AttributeError, KeyError, RuntimeError) as e:
                # BUG-004 FIX: Handle specific refresh errors
                self.write_log(f"⚠️ Monitor refresh error: {e}\n")
            except Exception as e:
                # BUG-004 FIX: Catch unexpected errors
                self.write_log(f"⚠️ Unexpected refresh error: {e}\n")
        threading.Thread(target=background_refresh, daemon=True).start()
        self.root.after(5000, self.refresh_quick_monitor) # Faster refresh (5s)

    def _update_quick_monitor_ui(self, perf, recent_trades, counters, allocated_limit):
        """Full threadsafe update for all summary widgets"""
        try:
            # 1. Update P&L Summary (With Caching to prevent flickering)
            if not perf and self.cached_perf:
                perf = self.cached_perf # Use cache if DB returns empty temporarily
            elif perf:
                self.cached_perf = perf
                
            if perf:
                net_profit = perf.get('net_profit', 0)
                if hasattr(self, 'lbl_pnl'):
                    color = COLOR_SUCCESS if net_profit >= 0 else COLOR_DANGER
                    self.lbl_pnl.configure(text=f"₹{net_profit:,.2f}", text_color=color)
                
                if hasattr(self, 'lbl_trade_count'):
                    self.lbl_trade_count.configure(text=f"{perf.get('total_trades', 0)} trades today")
                
                if hasattr(self, 'lbl_win_rate'):
                    self.lbl_win_rate.configure(text=f"{perf.get('win_rate', 0)}% Win")

            # 2. Update Wallet / Allocation Logic
            # Calculate deployed capital from positions
            deployed = 0
            if self.all_positions_data:
                for pos in self.all_positions_data.values():
                    if pos.get('source') == 'BOT':
                         qty = float(pos.get('qty', 0))
                         price = float(pos.get('avg_price', 0) or pos.get('price', 0))
                         deployed += (qty * price)
            
            available = max(0, allocated_limit - deployed)
            
            if hasattr(self, 'lbl_total_allocated'):
                self.lbl_total_allocated.configure(text=f"₹{allocated_limit:,.0f}")
                
            if hasattr(self, 'lbl_deployed'):
                self.lbl_deployed.configure(text=f"₹{deployed:,.0f} Deployed")
                
            if hasattr(self, 'lbl_available_wallet'):
                self.lbl_available_wallet.configure(text=f"₹{available:,.0f} Available")
                
            if hasattr(self, 'wallet_progress') and allocated_limit > 0:
                progress = min(1.0, deployed / allocated_limit)
                self.wallet_progress.set(progress)
                
            # 3. Update Balance Badge
            self.refresh_balance()

            # 4. Update Trades Tab Counters
            if counters:
                if hasattr(self, 'lbl_trades_attempts'):
                    self.lbl_trades_attempts.configure(text=str(counters.get('attempts', 0)))
                if hasattr(self, 'lbl_trades_success'):
                    self.lbl_trades_success.configure(text=str(counters.get('success', 0)))
                if hasattr(self, 'lbl_trades_failed'):
                    self.lbl_trades_failed.configure(text=str(counters.get('failed', 0)))

        except Exception as e:
            print(f"Quick Monitor UI Refresh Error: {e}", file=sys.__stderr__)

    def filter_positions_display(self, filter_val):
        self.update_positions(self.all_positions_data)

    def update_positions(self, data):
        self.all_positions_data = data
        for item in self.pos_table.get_children():
            self.pos_table.delete(item)
        
        filter_val = self.holdings_filter_var.get()
        total_pnl = 0
        
        for sym, pos in data.items():
            source = pos.get("source", "BOT")
            if filter_val != "ALL" and source != filter_val: continue
            
            pnl = pos.get("pnl", 0)
            total_pnl += pnl
            tag = "green" if pnl >= 0 else "red"
            s = f"{sym[0]}" if isinstance(sym, tuple) else str(sym)
            
            self.pos_table.insert("", "end", values=(s, source, pos.get('qty',0), pos.get('price',0), pos.get('ltp',0), f"₹{pnl:.2f}", "0%"), tags=(tag,))
        
        if hasattr(self, 'lbl_pnl'):
            self.lbl_pnl.configure(text=f"₹{total_pnl:,.2f}", text_color=COLOR_SUCCESS if total_pnl >= 0 else COLOR_DANGER)

        if hasattr(self, 'lbl_position_stats'):
             bot_count = len([p for p in data.values() if p.get('source') == 'BOT'])
             manual_count = len(data) - bot_count
             timestamp = datetime.now().strftime("%H:%M:%S")
             self.lbl_position_stats.configure(text=f"🟢 Live {timestamp} • {len(data)} positions (Bot: {bot_count} | Manual: {manual_count})")

    def refresh_balance(self):
        from kickstart import fetch_funds
        def bg():
            try:
                bal = fetch_funds()
                self.root.after(0, lambda: self.lbl_total_balance.configure(text=f"₹{bal:,.2f}"))
            except (AttributeError, KeyError, ValueError, RuntimeError) as e:
                # BUG-004 FIX: Handle specific balance fetch errors
                self.write_log(f"⚠️ Balance refresh error: {e}\n")
            except Exception as e:
                # BUG-004 FIX: Catch unexpected errors
                self.write_log(f"⚠️ Unexpected balance error: {e}\n")
        threading.Thread(target=bg, daemon=True).start()

    def write_log(self, text):
        """Robust stream writer for UI logging"""
        if not text: return 0
        try:
            # 1. Fallback to original stderr for file/console logging
            sys.__stderr__.write(text)

            # 2. Schedule UI update
            # We don't strip() here because logs need newlines to look right
            self.root.after(0, lambda: self._write_log_main_thread(text))
            return len(text)
        except (RuntimeError, AttributeError) as e:
            # BUG-004 FIX: Handle specific UI threading errors
            # Silently fail to avoid log recursion
            return 0
        except Exception as e:
            # BUG-004 FIX: Catch unexpected errors
            return 0

    def _write_log_main_thread(self, text):
        clean_text = text.strip()
        if not clean_text: return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Check if text already starts with a timestamp to avoid duplicates
        if "|" in clean_text and clean_text[:2].isdigit():
             formatted = clean_text
        else:
             formatted = f"{timestamp} | {clean_text}"
             
        if hasattr(self, 'trade_log'):
            self.trade_log.configure(state="normal", text_color="#eee") # Readable White
            self.trade_log.insert("0.0", formatted + "\n")
            self.trade_log.configure(state="disabled")
            
        # Duplicate trade-related logs to the dedicated Trades tab
        if hasattr(self, 'trades_log_viewer'):
            msg_lower = clean_text.lower()
            if any(key in msg_lower for key in ["order", "placed", "failed", "rejected", "trying", "attempt", "butler", "risk trigger"]):
                 self.trades_log_viewer.configure(state="normal")
                 self.trades_log_viewer.insert("0.0", formatted + "\n")
                 self.trades_log_viewer.configure(state="disabled")

    def positions_worker(self):
        while not self.stop_update_flag.is_set():
            try:
                data = safe_get_live_positions_merged()
                if data: self.data_queue.put(("positions", data))
            except (AttributeError, KeyError, RuntimeError) as e:
                # BUG-004 FIX: Handle specific position fetch errors
                self.write_log(f"⚠️ Position worker error: {e}\n")
            except Exception as e:
                # BUG-004 FIX: Catch unexpected errors
                self.write_log(f"⚠️ Unexpected position error: {e}\n")
            time.sleep(10)

    def sentiment_worker(self):
        while not self.stop_update_flag.is_set():
            try:
                data = self.sentiment_engine.fetch_sentiment()
                if data: self.data_queue.put(("sentiment", data))
            except: pass
            time.sleep(300)

    def panic_sell_sector(self, sector):
        self.write_log(f"🚨 Sector Panic Sell Triggered: {sector}\n")

    def emergency_exit(self):
        if messagebox.askyesno("CONFIRM", "Panic Sell All?"):
             import kickstart
             kickstart.panic_button()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        ctk.set_appearance_mode("light")
        root = ctk.CTk()
        
        def start_dashboard():
            app = DashboardV2(root)
        
        # Show dashboard directly for now to verify fix, can re-enable disclaimer later
        start_dashboard()
        root.mainloop()
        
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w") as f:
            traceback.print_exc(file=f)
