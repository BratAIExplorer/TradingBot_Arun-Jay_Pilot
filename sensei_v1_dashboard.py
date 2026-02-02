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
import atexit
import tempfile
try:
    import psutil
except ImportError:
    psutil = None

# --- Core Logic Imports ---
try:
    from kickstart import run_cycle, fetch_market_data, config_dict, SYMBOLS_TO_TRACK, calculate_intraday_rsi_tv, is_system_online, safe_get_positions, safe_get_live_positions_merged, reload_config
    from knowledge_center import TOOLTIPS, STRATEGY_GUIDES, get_strategy_guide, get_contextual_tip
    from market_sentiment import MarketSentiment
    from settings_manager import SettingsManager
    from state_manager import state as state_mgr
    
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

# --- UI CONSTANTS (ARUN TITAN LIGHT THEME) ---
# Matching mockup: Soft Cream Background, High Contrast Text, Cyan Accents
COLOR_BG = "#EFEBE3"      # Soft Cream / Zinc-50 alternative
COLOR_CARD = "#FFFFFF"    # Pure White Cards (Elevated)
COLOR_ACCENT = "#479FB6"  # Soft Cyan-600
COLOR_DANGER = "#EF4444"  # Red-500
COLOR_SUCCESS = "#10B981" # Emerald-500
COLOR_WARN = "#F59E0B"    # Amber-500
FONT_MAIN = ("Roboto Medium", 14)        # Increased from 12
FONT_HEADER = ("Roboto", 16, "bold")     # Increased from 14
FONT_BIG = ("Roboto", 34, "bold")        # Increased from 32

class TitanCard(ctk.CTkFrame):
    """A standardized Sensei-style card"""
    def __init__(self, parent, title=None, border_color="#D1D5DB", **kwargs):
        super().__init__(parent, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=border_color, **kwargs)
        if title:
            # Title Bar
            self.title_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
            self.title_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            # Accent Pill
            ctk.CTkFrame(self.title_frame, width=4, height=16, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
            
            ctk.CTkLabel(self.title_frame, text=title.upper(), font=("Roboto", 13, "bold"), text_color="#1a1a1a").pack(side="left", padx=10)

class DashboardV2:
    def __init__(self, root):
        # 1. Setup Window (Root passed from main)
        self.root = root
        self.root.title("ARUN TITAN V2 - Release v2.0.2 (Light Mode)")
        self.root.geometry("1450x900") # Expanded slightly for larger fonts
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

        # Scanner state
        self.scanner_running = False
        self.scanner_results = []
        self.scanner_thread = None

        # Log redirection (DISABLED - Can cause GUI freeze)
        # sys.stdout.write = self.write_log
        # sys.stderr.write = self.write_log

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
        self.view_start = ctk.CTkFrame(self.main_container, fg_color="transparent") # Restored to prevent crash
        self.view_hybrid = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_trades = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_stocks = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_scanner = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        self.build_dashboard_view()
        self.build_strategies_view()
        self.build_settings_view()
        self.build_knowledge_view()
        self.build_logs_view()
        self.build_hybrid_view()
        self.build_trades_view()
        self.build_stocks_view()
        self.build_scanner_view()
        
        # Default View (Always Dashboard for Sensei V1)
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
        self.write_log("ℹ Monitoring Modules Active. Engine is STOPPED. Waiting for Command.\n")
        # INSTANT: Load cached holdings before anything else
        self.load_cached_holdings()
        
        threading.Thread(target=self.sentiment_worker, daemon=True).start()
        threading.Thread(target=self.positions_worker, daemon=True).start()
        
    def update_ui_loop(self):
        """Main UI Update Loop (Consumer)"""
        try:
            # 1. Update Monitor Timestamp (Visual Heartbeat)
            now = datetime.now().strftime("%H:%M:%S")
            if hasattr(self, 'positions_label'):
                self.positions_label.configure(text=f"📊 Live Positions (Last Check: {now})")
            
            # 2. Consume Data Queue
            updates_processed = 0
            while not self.data_queue.empty() and updates_processed < 20:
                try:
                    msg = self.data_queue.get_nowait()
                    kind, data = msg
                    if kind == "positions":
                        self.all_positions_data = data
                        # Use existing filter method to refresh view
                        if hasattr(self, 'filter_positions_display'):
                             self.filter_positions_display(self.holdings_filter_var.get() if hasattr(self, 'holdings_filter_var') else None)
                    updates_processed += 1
                except queue.Empty:
                    break
        except Exception as e:
            print(f"UI Loop Error: {e}")
            
        # Loop every 1 second
        self.root.after(1000, self.update_ui_loop)

    def load_cached_holdings(self):
        """Load cached holdings for instant display on startup"""
        try:
            cached = state_mgr.get_cached_holdings()
            if cached.get('data'):
                self.update_positions(cached['data'])
                age = cached.get('age_minutes', 0)
                if cached.get('is_stale'):
                    self.lbl_position_stats.configure(
                        text=f"🟡 Cached {age:.0f}m ago • Refreshing..."
                    )
                else:
                    self.lbl_position_stats.configure(
                        text=f"🟢 Loaded {age:.0f}m ago"
                    )
                self.write_log(f"📦 Loaded {len(cached['data'])} cached holdings\n")
            else:
                self.write_log("📦 No cached holdings - waiting for API fetch...\n")
        except Exception as e:
            print(f"Cache load error: {e}")

    def positions_worker(self):
        """Background worker to fetch and update positions every 30 seconds"""
        self.write_log("🔄 Starting positions fetch...\n")
        while not self.stop_update_flag.is_set():
            try:
                positions = safe_get_live_positions_merged()
                if positions:
                    # Cache holdings for next startup
                    state_mgr.cache_holdings(positions)
                    self.data_queue.put(("positions", positions))
                    self.write_log(f"✅ Fetched {len(positions)} holdings from API\n")
                else:
                    self.write_log("⚠️ No positions returned from API\n")
            except Exception as e:
                self.write_log(f"❌ Positions fetch error: {e}\n")
            time.sleep(10)  # Refresh every 10 seconds

    def balance_refresh_timer(self):
        """Auto-refresh balance every 15 minutes"""
        self.refresh_balance()
        # Schedule next refresh (15 minutes = 900000 ms)
        self.root.after(900000, self.balance_refresh_timer)

    # ... (Rest of class methods remain same, will rely on backup or merge context) ...

    # We need to include the rest of the methods here or use replace wisely. 
    # Since I cannot see the whole file in "ReplacementContent" unless I paste it all, 
    # I should use a targeted replace for __init__ first, then fix __main__.
    
    # Actually, the user's previous code was fully overwritten by me in step 335.
    # So I have the full content in my context.
    # I will replace the __init__ and __main__ blocks separately for safety.

    # This tool call handles __init__ refactor.


    def build_header(self):
        """Top Navigation Bar"""
        header = ctk.CTkFrame(self.root, height=60, fg_color=COLOR_CARD, corner_radius=0)
        header.pack(fill="x", side="top")
        
        # Logo Area
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=20)
        ctk.CTkLabel(logo_frame, text="ARUN", font=("Roboto", 22, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        ctk.CTkLabel(logo_frame, text="TITAN", font=("Roboto", 22, "bold"), text_color="#333").pack(side="left", padx=5)
        ctk.CTkLabel(logo_frame, text="v2.0.2", font=("Roboto", 10, "bold"), text_color="#333").pack(side="left", padx=5, pady=(5,0))

        # Navigation (Segmented Button Style)
        self.nav_var = ctk.StringVar(value="DASHBOARD")
        self.nav_bar = ctk.CTkSegmentedButton(
            header, 
            values=["DASHBOARD", "HYBRID", "TRADES", "SCANNER", "STOCKS", "KNOWLEDGE", "STRATEGIES", "SETTINGS", "LOGS"],
            command=self.show_view,
            font=("Roboto", 14, "bold"), # Increased
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT,
            unselected_color="#E0E0E0",
            unselected_hover_color="#D1D5DB",
            text_color="black",
            fg_color="#F3F4F6",
            height=36,
            width=800  # Accommodate extra tab
        )
        self.nav_bar.pack(side="left", padx=50, pady=14)
        self.nav_bar.set("DASHBOARD") # Set default

        # User Profile & Notification (Far Right)
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(user_frame, text="ARUN ADMIN", font=("Roboto", 12, "bold"), text_color="#AAA").pack(side="left", padx=10)
        ctk.CTkLabel(user_frame, text="🔔", font=("Arial", 16)).pack(side="left", padx=5)

    def refresh_bot_settings(self):
        """Callback for SettingsGUI to hot-reload config"""
        from kickstart import reload_config
        success = reload_config()
        if success:
             self.write_log("✅ Settings Reloaded & Applied.\n")
             # Trigger immediate Capital/Balance refresh
             self.refresh_balance()
        else:
             self.write_log("❌ Failed to reload settings.\n")

    def show_view(self, view_name):
        # Hide all
        self.view_dashboard.pack_forget()
        self.view_strategies.pack_forget()
        self.view_settings.pack_forget()
        self.view_knowledge.pack_forget()
        self.view_logs.pack_forget()
        self.view_start.pack_forget()
        self.view_trades.pack_forget()
        self.view_hybrid.pack_forget() 
        self.view_stocks.pack_forget()
        self.view_scanner.pack_forget()
        
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
        elif view_name == "STOCKS":
            self.view_stocks.pack(fill="both", expand=True)
        elif view_name == "SCANNER":
            self.view_scanner.pack(fill="both", expand=True)

    def build_dashboard_view(self):
        """Redesigned Dashboard v2: Enhanced Quick Monitor + Compact Engine Commander"""
        for widget in self.view_dashboard.winfo_children():
            widget.destroy()

        # Grid Layout: Left (30%) | Right (70%)
        self.view_dashboard.grid_columnconfigure(0, weight=3)
        self.view_dashboard.grid_columnconfigure(1, weight=7)
        self.view_dashboard.grid_rowconfigure(0, weight=1)

        # === LEFT COLUMN: QUICK STATS & CONTROLS ===
        left_col = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # 1. Enhanced Quick Monitor Card
        self.card_stats = TitanCard(left_col, title="QUICK MONITOR", border_color=COLOR_ACCENT)
        self.card_stats.pack(fill="x", pady=(0, 10))
        
        stats_in = ctk.CTkFrame(self.card_stats, fg_color="transparent")
        stats_in.pack(fill="x", padx=15, pady=10)
        
        # 💰 Live Wallet Balance (from mStock API)
        ctk.CTkLabel(stats_in, text="💰 WALLET BALANCE", font=("Roboto", 10, "bold"), text_color="#1a1a1a").pack(anchor="w")
        self.lbl_total_balance = ctk.CTkLabel(stats_in, text="₹--,---", font=("Roboto", 24, "bold"), text_color="#1a1a1a")
        self.lbl_total_balance.pack(anchor="w", pady=(0, 8))
        
        # 📊 Bot Capital with Progress Bar
        ctk.CTkLabel(stats_in, text="📊 BOT CAPITAL", font=("Roboto", 10, "bold"), text_color="#1a1a1a").pack(anchor="w")
        capital_row = ctk.CTkFrame(stats_in, fg_color="transparent")
        capital_row.pack(fill="x", pady=(0, 3))
        self.lbl_total_allocated = ctk.CTkLabel(capital_row, text="₹10,000", font=("Roboto", 18, "bold"), text_color="#2c3e50")
        self.lbl_total_allocated.pack(side="left")
        self.lbl_deployed = ctk.CTkLabel(capital_row, text="Used: ₹0", font=("Roboto", 11, "bold"), text_color="#2c3e50")
        self.lbl_deployed.pack(side="right")
        
        # Progress bar for capital usage
        self.wallet_progress = ctk.CTkProgressBar(stats_in, height=8, progress_color=COLOR_ACCENT, fg_color="#D1D5DB")
        self.wallet_progress.pack(fill="x", pady=(0, 3))
        self.wallet_progress.set(0)
        self.lbl_available_wallet = ctk.CTkLabel(stats_in, text="₹10,000 (100%) Available", font=("Roboto", 11, "bold"), text_color="#2c3e50")
        self.lbl_available_wallet.pack(anchor="w", pady=(0, 8))
        
        # 📈 Today's P&L
        ctk.CTkLabel(stats_in, text="📈 TODAY'S P&L", font=("Roboto", 10, "bold"), text_color="#1a1a1a").pack(anchor="w")
        self.lbl_pnl = ctk.CTkLabel(stats_in, text="₹0.00", font=("Roboto", 22, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_pnl.pack(anchor="w", pady=(0, 3))
        self.lbl_trade_count = ctk.CTkLabel(stats_in, text="0 trades today", font=("Roboto", 11, "bold"), text_color="#333")
        self.lbl_trade_count.pack(anchor="w", pady=(0, 8))
        
        # 🎯 Win Rate
        ctk.CTkLabel(stats_in, text="🎯 WIN RATE", font=("Roboto", 10, "bold"), text_color="#1a1a1a").pack(anchor="w")
        self.lbl_win_rate = ctk.CTkLabel(stats_in, text="--% (0W / 0L)", font=("Roboto", 16, "bold"), text_color="#1a1a1a")
        self.lbl_win_rate.pack(anchor="w", pady=(0, 8))
        
        # 🔄 Recent Trades (Last 5)
        ctk.CTkLabel(stats_in, text="🔄 RECENT TRADES", font=("Roboto", 10, "bold"), text_color="#1a1a1a").pack(anchor="w", pady=(0, 2))
        self.recent_trades_frame = ctk.CTkFrame(stats_in, fg_color="transparent")
        self.recent_trades_frame.pack(fill="x", pady=(0, 5))
        
        # Placeholder for trades - will be populated by refresh_quick_monitor
        self.lbl_last_trade = ctk.CTkLabel(self.recent_trades_frame, text="Waiting for trades...", font=("Roboto", 11, "bold"), text_color="#333")
        self.lbl_last_trade.pack(anchor="w")

        # 2. Engine Commander (Compact)
        self.card_controls = TitanCard(left_col, title="ENGINE", border_color=COLOR_WARN)
        self.card_controls.pack(fill="x")
        
        ctrl_in = ctk.CTkFrame(self.card_controls, fg_color="transparent")
        ctrl_in.pack(fill="x", padx=15, pady=10)
        
        self.btn_start = ctk.CTkButton(ctrl_in, text="▶ START", command=self.toggle_bot, 
                                     fg_color=COLOR_SUCCESS, hover_color="#00C853", height=36, 
                                     font=("Roboto", 14, "bold"), text_color="black")
        self.btn_start.pack(fill="x", pady=(0, 5))
        
        self.lbl_engine_status = ctk.CTkLabel(ctrl_in, text="STOPPED 🔴", font=("Roboto", 10, "bold"), text_color=COLOR_DANGER)
        self.lbl_engine_status.pack()
        
        # 3. Engine Heartbeat (Visual confirmation of activity)
        self.lbl_heartbeat = ctk.CTkLabel(ctrl_in, text="Engine Idle", font=("Roboto", 11, "bold"), text_color="gray")
        self.lbl_heartbeat.pack(pady=(5, 5))

        # === RIGHT COLUMN: TABS ===
        right_col = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", pady=10)
        
        self.dash_tabs = ctk.CTkTabview(right_col, fg_color=COLOR_CARD, 
                                      segmented_button_selected_color=COLOR_ACCENT,
                                      segmented_button_selected_hover_color=COLOR_ACCENT,
                                      segmented_button_unselected_color="#D1D5DB",
                                      text_color="black")
        self.dash_tabs.pack(fill="both", expand=True)
        self.dash_tabs._segmented_button.configure(font=("Roboto", 15, "bold"), height=38)
        self.dash_tabs._segmented_button.grid(sticky="ew", padx=10, pady=5)
        
        self.dash_tabs.add("ACTIVE POSITIONS")
        self.dash_tabs.add("LIVE EXECUTION") # Renamed from Trade Activity Monitor
        
        # -- TAB 1: POSITIONS --
        pos_tab = self.dash_tabs.tab("ACTIVE POSITIONS")
        pos_wrapper = ctk.CTkFrame(pos_tab, fg_color="transparent")
        pos_wrapper.pack(fill="both", expand=True)
        self.build_positions_table(pos_wrapper)
        
        # -- TAB 2: LIVE EXECUTION --
        act_tab = self.dash_tabs.tab("LIVE EXECUTION")
        
        # 1. Big Counters
        counters_frame = ctk.CTkFrame(act_tab, fg_color="transparent")
        counters_frame.pack(fill="x", pady=10, padx=10)
        
        def make_big_counter(parent, label, value, color):
            f = ctk.CTkFrame(parent, fg_color="#F3F4F6", corner_radius=8, border_width=1, border_color="#D1D5DB")
            f.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(f, text=label, font=("Roboto", 13, "bold"), text_color="#4B5563").pack(pady=(10,0))
            lbl = ctk.CTkLabel(f, text=str(value), font=("Roboto", 34, "bold"), text_color=color)
            lbl.pack(pady=(0,10))
            return lbl

        self.lbl_attempt_count = make_big_counter(counters_frame, "TOTAL ATTEMPTS", "0", "#1a1a1a")
        self.lbl_success_count = make_big_counter(counters_frame, "SUCCESSFUL", "0", COLOR_SUCCESS)
        self.lbl_fail_count = make_big_counter(counters_frame, "FAILED", "0", COLOR_DANGER)
        
        # 2. Activity Log
        ctk.CTkLabel(act_tab, text="LIVE EXECUTION STREAM", font=("Roboto", 12, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=15, pady=(15,5))
        
        self.trade_log = ctk.CTkTextbox(act_tab, fg_color="#050505", font=("Consolas", 12), text_color="#CCC", activate_scrollbars=True)
        self.trade_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.trade_log.insert("0.0", "--- Trade Execution Monitor Initialized ---\n")
        self.trade_log.configure(state="disabled")
        
        # Schedule Quick Monitor refresh
        self.root.after(1000, self.refresh_quick_monitor)


    def build_positions_table(self, parent):
        # Filter/View Toggle
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent", height=35)
        filter_frame.pack(fill="x", padx=10, pady=(5, 0))

        ctk.CTkLabel(filter_frame, text="Show:", font=("Roboto", 10, "bold"), text_color="#AAA").pack(side="left", padx=(5, 10))

        self.holdings_filter_var = ctk.StringVar(value="ALL")
        filter_segment = ctk.CTkSegmentedButton(
            filter_frame,
            values=["ALL", "BOT", "MANUAL"],
            variable=self.holdings_filter_var,
            command=self.filter_positions_display,
            font=("Roboto", 13, "bold"),
            height=32,
            fg_color="#333",
            selected_color=COLOR_ACCENT,
            selected_hover_color="#00E5FF",
            unselected_color="#222",
            unselected_hover_color="#444",
            corner_radius=6
        )
        filter_segment.pack(side="left")

        # Summary Stats
        self.lbl_position_stats = ctk.CTkLabel(
            filter_frame,
            text="Positions: 0 • Bot: 0 • Manual: 0",
            font=("Roboto", 11),
            text_color="#CCC"
        )
        self.lbl_position_stats.pack(side="right", padx=10)

        # Table Frame
        table_frame = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=2, pady=5)

        cols = ("Symbol", "Source", "Qty", "Entry", "LTP", "P&L", "P&L %")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#111", foreground="white", fieldbackground="#111", rowheight=35, borderwidth=0, font=("Roboto", 10))
        style.configure("Treeview.Heading", background="#1A1A1A", foreground="#DDD", font=("Roboto", 9, "bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', COLOR_ACCENT)], foreground=[('selected', '#000')])

        self.pos_table = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.pos_table.heading(col, text=col.upper())
            self.pos_table.column(col, anchor="center")

        self.pos_table.column("Source", width=70)
        self.pos_table.column("Symbol", width=100)
        self.pos_table.column("Qty", width=60)
        self.pos_table.column("Entry", width=80)
        self.pos_table.column("LTP", width=80)
        self.pos_table.column("P&L", width=90)
        self.pos_table.column("P&L %", width=70)

        self.pos_table.pack(fill="both", expand=True)
        self.pos_table.tag_configure("green", foreground=COLOR_SUCCESS)
        self.pos_table.tag_configure("red", foreground=COLOR_DANGER)
        self.pos_table.tag_configure("bot", background="#0A2A0A") 
        self.pos_table.tag_configure("manual", background="#2A2A0A") 

        # Store all positions for filtering
        self.all_positions_data = {}

    def build_trades_view(self):
        """Dedicated view for monitoring LIVE trade requests and execution stats"""
        # Header
        header = ctk.CTkFrame(self.view_trades, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20), padx=20)
        
        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkFrame(title_frame, width=4, height=24, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
        ctk.CTkLabel(title_frame, text=" TRADE HISTORY & METRICS", font=("Roboto", 20, "bold"), text_color="#1a1a1a").pack(side="left", padx=10)

        # 1. Counter Row
        counter_row = ctk.CTkFrame(self.view_trades, fg_color="transparent")
        counter_row.pack(fill="x", pady=(0, 20), padx=20)
        
        def make_count_box(parent, title, color):
            box = TitanCard(parent, title=title, border_color="#333")
            box.pack(side="left", fill="both", expand=True, padx=5)
            # Override title color to match box theme
            lbl = ctk.CTkLabel(box, text="0", font=("Roboto", 36, "bold"), text_color=color)
            lbl.pack(pady=20)
            return lbl

        self.lbl_trades_attempts = make_count_box(counter_row, "TOTAL TRADES (30D)", COLOR_ACCENT)
        self.lbl_trades_success = make_count_box(counter_row, "PROFITABLE TRADES", COLOR_SUCCESS)
        self.lbl_trades_failed = make_count_box(counter_row, "LOSS TRADES", COLOR_DANGER)

        # 2. Execution Table
        log_card = TitanCard(self.view_trades, title="ORDER EXECUTION HISTORY")
        log_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Create Treeview for Trades
        style = ttk.Style()
        style.theme_use("default")
        # Glassy Table Appearance
        style.configure("Treeview", background="#FFF", foreground="#1a1a1a", fieldbackground="#FFF", rowheight=35, borderwidth=0, font=("Arial", 12))
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[('selected', COLOR_ACCENT)], foreground=[('selected', '#FFF')])
        
        cols = ("TIME", "SYMBOL", "ACTION", "QTY", "PRICE", "RSI", "P&L", "STRATEGY")
        self.trades_table = ttk.Treeview(log_card, columns=cols, show="headings", style="Treeview")
        
        for col in cols:
            self.trades_table.heading(col, text=col)
            self.trades_table.column(col, anchor="center", width=100)
        
        self.trades_table.column("TIME", width=140)
        self.trades_table.column("STRATEGY", width=150)
        
        self.trades_table.pack(fill="both", expand=True, padx=10, pady=10)

    def build_stocks_view(self):
        """Promoted Top-Level Stocks Configuration View"""
        container = ctk.CTkFrame(self.view_stocks, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header Info
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="📦 SYMBOL CONFIGURATION", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(header, text="Manage your trading universe and RSI rules", font=("Roboto", 12), text_color="#666").pack(side="left", padx=20, pady=(8,0))
        
        # Integration with SettingsGUI instance
        if not hasattr(self, 'settings_gui_instance'):
            from settings_gui import SettingsGUI
            try:
                 self.settings_gui_instance = SettingsGUI(parent=self.view_settings, on_save_callback=self.refresh_bot_settings)
            except: pass

        if hasattr(self, 'settings_gui_instance'):
            # Standard Stock Table from SettingsGUI
            table_card = TitanCard(container, title="ACTIVE TRADING LIST")
            table_card.pack(fill="both", expand=True)
            
            # We rebuild the table specifically in this view for better sizing
            table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
            table_frame.pack(fill="both", expand=True, padx=15, pady=15)
            
            columns=("Symbol", "Exchange", "Enabled", "Strategy", "Timeframe", "Buy RSI", "Sell RSI", "Qty", "Target %", "Price", "Status")
            self.settings_gui_instance.stock_table = ttk.Treeview(
                table_frame,
                columns=columns,
                show="headings",
                height=15,
                style="Treeview"
            )
            for col in columns:
                self.settings_gui_instance.stock_table.heading(col, text=col)
                self.settings_gui_instance.stock_table.column(col, width=80, anchor="center")
            self.settings_gui_instance.stock_table.column("Symbol", width=120)
            self.settings_gui_instance.stock_table.pack(side="left", fill="both", expand=True)
            
            scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.settings_gui_instance.stock_table.yview)
            scroll.pack(side="right", fill="y")
            self.settings_gui_instance.stock_table.configure(yscrollcommand=scroll.set)
            
            # Initial Load
            self.settings_gui_instance.refresh_stock_table()
            
            # Action Row
            btn_row = ctk.CTkFrame(container, fg_color="transparent")
            btn_row.pack(fill="x", pady=10)
            
            ctk.CTkButton(btn_row, text="+ ADD", command=self.settings_gui_instance.on_add_stock, fg_color=COLOR_SUCCESS, font=("Roboto", 11, "bold"), height=32, width=80).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="✏ EDIT", command=self.settings_gui_instance.on_edit_stock, fg_color="#3498DB", font=("Roboto", 11, "bold"), height=32, width=80).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="🗑 DEL", command=self.settings_gui_instance.on_delete_stock, fg_color=COLOR_DANGER, font=("Roboto", 11), height=32, width=80).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_row, text="🔍 SMART VALIDATE", command=self.settings_gui_instance.on_validate_symbols, fg_color="#555", font=("Roboto", 11, "bold"), height=32).pack(side="right", padx=5)
            ctk.CTkButton(btn_row, text="🔄 FORCE REFRESH", command=lambda: self.settings_gui_instance.on_validate_symbols(force=True), fg_color="#777", font=("Roboto", 11), height=32).pack(side="right", padx=5)
            
        # Refresh Button
        ctk.CTkButton(header, text="🔄 REFRESH DATA", command=self.settings_gui_instance.refresh_stock_table if hasattr(self, 'settings_gui_instance') else None, height=30, 
                      fg_color=COLOR_CARD, border_width=1, border_color=COLOR_ACCENT, text_color=COLOR_ACCENT).pack(side="right")

        # --- STATUS BAR INTEGRATION ---
        # Add a status label to the bottom of the Stocks view
        self.stocks_status_label = ctk.CTkLabel(container, text="Ready", font=("Consolas", 11), text_color="gray", anchor="w")
        self.stocks_status_label.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Divert SettingsGUI status updates to this label
        if hasattr(self, 'settings_gui_instance'):
            def diverted_update(msg, color="gray"):
                try:
                    self.stocks_status_label.configure(text=msg, text_color=color)
                    self.stocks_status_label.update()
                except: pass
            
            # Monkey-patch the instance method
            self.settings_gui_instance.update_status = diverted_update

    def refresh_trades_history(self):
        """Fetch recent trades from DB and populate table"""
        if not DATABASE_AVAILABLE or not db:
            return
            
        try:
            # Clear table
            for item in self.trades_table.get_children():
                self.trades_table.delete(item)
                
            trades = db.get_recent_trades(limit=50) # Use DB method
            
            pnl_wins = 0
            pnl_loss = 0
            
            for t in trades:
                ts = t.get('timestamp', '').replace('T', ' ')[:19]
                sym = t.get('symbol')
                action = t.get('action')
                qty = t.get('quantity')
                price = t.get('price')
                try:
                    rsi_raw = t.get('rsi')
                    rsi = float(rsi_raw) if rsi_raw is not None else 0.0
                except: rsi = 0.0
                
                rsi_str = f"{rsi:.1f}" if rsi > 0 else "-"
                
                try:
                    pnl_raw = t.get('pnl_net')
                    pnl = float(pnl_raw) if pnl_raw is not None else 0.0
                except: pnl = 0.0

                strat = t.get('strategy', 'Manual')
                
                if pnl > 0: pnl_wins += 1
                elif pnl < 0: pnl_loss += 1
                
                pnl_str = f"₹{pnl:.2f}" if pnl != 0 else "-"
                tag = "green" if pnl > 0 else ("red" if pnl < 0 else "")
                
                self.trades_table.insert("", END, values=(ts, sym, action, qty, f"₹{price:.2f}", rsi_str, pnl_str, strat), tags=(tag,))
            
            # Update counters
            self.lbl_trades_attempts.configure(text=str(len(trades)))
            self.lbl_trades_success.configure(text=str(pnl_wins))
            self.lbl_trades_failed.configure(text=str(pnl_loss))
            
            # Configure tags
            self.trades_table.tag_configure("green", foreground=COLOR_SUCCESS)
            self.trades_table.tag_configure("red", foreground=COLOR_DANGER)
            
        except Exception as e:
            self.write_log(f"Error refreshing trades history: {e}\n")

    def build_strategies_view(self):
        """Strategies View Content - Baskets & Strategies"""
        
        scroll_frame = ctk.CTkScrollableFrame(self.view_strategies, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- SECTION 1: SECTOR BASKETS ---
        ctk.CTkLabel(scroll_frame, text="SECTOR BASKETS (BUCKETS)", font=("Roboto", 16, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        
        basket_grid = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        basket_grid.pack(fill="x", pady=(0, 20))
        basket_grid.grid_columnconfigure(0, weight=1)
        basket_grid.grid_columnconfigure(1, weight=1)
        basket_grid.grid_columnconfigure(2, weight=1)
        
        sectors = ["FINANCIALS", "IT", "ENERGY", "AUTO", "PHARMA", "FMCG"]
        
        def make_basket_card(parent, title, col, row):
            card = TitanCard(parent, title=title, height=140, border_color="#444")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            # Stats Placeholder
            ctk.CTkLabel(card, text="Exposure: ₹0", font=("Roboto", 11, "bold"), text_color="#333").pack(anchor="w", padx=15, pady=(5,0))
            ctk.CTkLabel(card, text="PnL: 0.0%", font=("Roboto", 14, "bold"), text_color="#1a1a1a").pack(anchor="w", padx=15, pady=2)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=10)
            ctk.CTkSwitch(btn_frame, text="Trade", width=40, text_color="#1a1a1a").pack(side="right")
            ctk.CTkButton(btn_frame, text="Sell All", width=60, height=20, fg_color=COLOR_DANGER, hover_color="#B71C1C", 
                          command=lambda: self.sell_sector_positions(title)).pack(side="left")

        for i, sec in enumerate(sectors):
            r = i // 3
            c = i % 3
            make_basket_card(basket_grid, sec, c, r)
            
    def sell_sector_positions(self, sector_name):
        """Sell all positions belonging to a specific sector"""
        if not messagebox.askyesno("Confirm Sell", f"Sell ALL positions in {sector_name} sector?"):
            return
            
        try:
            from strategies.sector_map import get_sector
            positions = safe_get_live_positions_merged() # from kickstart
            count = 0
            
            for key, pos in positions.items():
                sym = key[0] if isinstance(key, tuple) else key
                ex = key[1] if isinstance(key, tuple) else "NSE"
                qty = pos.get("qty", 0)
                
                if qty > 0 and get_sector(sym) == sector_name:
                    self.write_log(f"📉 SELLING {sym} ({sector_name}) - Panic Exit\n")
                    place_order(sym, ex, qty, "SELL", "0") # market order
                    count += 1
            
            if count > 0:
                self.write_log(f"✅ Sold {count} positions in {sector_name}\n")
            else:
                self.write_log(f"⚠️ No active positions found in {sector_name}\n")
                
        except Exception as e:
            self.write_log(f"❌ Error selling sector {sector_name}: {e}\n")

        # --- SECTION 2: ALGO STRATEGIES ---
        ctk.CTkLabel(scroll_frame, text="ALGO STRATEGIES", font=("Roboto", 16, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        
        algo_grid = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        algo_grid.pack(fill="x")
        algo_grid.grid_columnconfigure(0, weight=1)
        algo_grid.grid_columnconfigure(1, weight=1)

        # Helper to make cards
        def make_strat_card(parent, title, desc, col, row):
            card = TitanCard(parent, title=title, height=150)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
            ctk.CTkLabel(card, text=desc, font=("Roboto", 12), text_color="#333", wraplength=300, justify="left").pack(anchor="w", padx=15, pady=5)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkSwitch(btn_frame, text="Active", text_color="#1a1a1a").pack(side="right")
            ctk.CTkButton(btn_frame, text="Configure", width=80, height=24, fg_color="#333", hover_color="#444").pack(side="left")

        # Strategies
        make_strat_card(algo_grid, "RSI MEAN REVERSION", "Classic Overbought/Oversold logic.", 0, 0)
        make_strat_card(algo_grid, "MOMENTUM CHASER", "Trend following on volume breakouts.", 1, 0)
        make_strat_card(algo_grid, "DEEP DIP BUYER", "Buys aggressive dips below Bollinger bands.", 0, 1)
        make_strat_card(algo_grid, "SCALP MASTER", "Quick in-out trades.", 1, 1)

    def build_settings_view(self):
        """Settings View Content"""
        # Embed SettingsGUI
        from settings_gui import SettingsGUI
        try:
             self.settings_gui_instance = SettingsGUI(parent=self.view_settings, on_save_callback=self.refresh_bot_settings)
        except Exception as e:
             ctk.CTkLabel(self.view_settings, text=f"Error: {e}").pack()

    def build_knowledge_view(self):
        """Knowledge Base / Help Tab"""
        scroll = ctk.CTkScrollableFrame(self.view_knowledge, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="🧠 KNOWLEDGE INTELLIGENCE", font=("Roboto", 24, "bold"), text_color="#1a1a1a").pack(anchor="w", pady=(0, 20))
        
        # Load Tips
        tips = []
        try:
            import json
            with open("strategies/trading_tips.json", "r") as f:
                tips = json.load(f)
        except Exception:
            tips = [{"title": "Welcome", "content": "Trading tips will appear here."}]
            
        import random
        daily_tip = random.choice(tips)
        
        # Tip of the Day
        tip_card = TitanCard(scroll, title=f"💡 TIP OF THE DAY: {daily_tip['title']}", height=150, border_color="#FFD700")
        tip_card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(tip_card, text=daily_tip['content'], font=("Roboto", 14), text_color="#333", 
                     wraplength=800, justify="left").pack(padx=20, pady=20, anchor="w")
                     
        # Library
        ctk.CTkLabel(scroll, text="TRADING LIBRARY", font=("Roboto", 18, "bold"), text_color="#333").pack(anchor="w", pady=(20, 10))
        
        for tip in tips:
            if tip == daily_tip: continue
            
            card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, corner_radius=6, border_width=1, border_color="#D1D5DB")
            card.pack(fill="x", pady=5)
            
            ctk.CTkLabel(card, text=tip['title'], font=("Roboto", 12, "bold"), text_color="#1a1a1a").pack(anchor="w", padx=10, pady=(10,0))
            ctk.CTkLabel(card, text=tip['content'], font=("Roboto", 11), text_color="#333", wraplength=800, justify="left").pack(anchor="w", padx=10, pady=(0,10))

    def build_logs_view(self):
        """Technical Logs View"""
        import os
        
        # Header
        header = ctk.CTkFrame(self.view_logs, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text="📜 TECHNICAL LOGS", font=("Roboto", 20, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        
        ctk.CTkButton(header, text="🔄 Refresh", width=100, command=self.refresh_technical_logs).pack(side="right")
        ctk.CTkButton(header, text="📂 Open Log File", width=120, command=lambda: os.startfile("logs\\bot.log") if os.name == 'nt' else None, fg_color="#333").pack(side="right", padx=10)

        # Log Content
        self.log_viewer = ctk.CTkTextbox(self.view_logs, font=("Consolas", 12), text_color="#DDD", fg_color="#111")
        self.log_viewer.pack(fill="both", expand=True)
        
    def refresh_technical_logs(self):
        """Read 200 lines from bot.log"""
        import os
        try:
            log_path = os.path.join("logs", "bot.log")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    last_lines = lines[-200:]
                    content = "".join(last_lines)
                    self.log_viewer.delete("1.0", "end")
                    self.log_viewer.insert("1.0", content)
                    self.log_viewer.see("end")
            else:
                self.log_viewer.insert("1.0", "No log file found at logs/bot.log")
        except Exception as e:
            self.log_viewer.insert("end", f"\nError reading logs: {e}")

    def build_start_here_view(self):
        """Onboarding Guide Tab"""
        # Header
        header = ctk.CTkFrame(self.view_start, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="🚀 START HERE: Quick Setup Guide", font=("Roboto", 24, "bold"), text_color="#1a1a1a").pack(pady=10)
        ctk.CTkLabel(header, text="Follow these 4 simple steps to get your bot running!", font=("Roboto", 14, "bold"), text_color="#333").pack()
        
        # Steps Container
        steps_frame = ctk.CTkScrollableFrame(self.view_start, fg_color="transparent")
        steps_frame.pack(fill="both", expand=True, padx=40)
        
        # --- Step 1: Broker ---
        s1 = TitanCard(steps_frame, title="STEP 1: CONNECT BROKER", height=150, border_color="#3498DB")
        s1.pack(fill="x", pady=10)
        
        row1 = ctk.CTkFrame(s1, fg_color="transparent")
        row1.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row1, text="1️⃣", font=("Arial", 30), text_color="#1a1a1a").pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row1, text="Configure API Credentials", font=("Roboto", 16, "bold"), text_color="#1a1a1a").pack(anchor="w")
        ctk.CTkLabel(row1, text="Go to Settings > Broker tab. Enter your API Key, Secret, and User ID.\nEnable 'Auto-Login' by adding your TOTP secret (recommended).",
                     font=("Arial", 12, "bold"), text_color="#333", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row1, text="Go to Broker Settings", width=150, fg_color="#3498DB", 
                      command=lambda: self.nav_bar.set("SETTINGS") or self.show_view("SETTINGS")).pack(side="right")

        # --- Step 2: Capital ---
        s2 = TitanCard(steps_frame, title="STEP 2: ALLOCATE FUNDS", height=150, border_color="#2ECC71")
        s2.pack(fill="x", pady=10)
        
        row2 = ctk.CTkFrame(s2, fg_color="transparent")
        row2.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row2, text="2️⃣", font=("Arial", 30), text_color="#1a1a1a").pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row2, text="Set Capital Limits (Safety Box)", font=("Roboto", 16, "bold"), text_color="#1a1a1a").pack(anchor="w")
        ctk.CTkLabel(row2, text="Go to Settings > Capital tab.\nSet 'Allocated Capital' (e.g., ₹50,000). This is the maximum the bot can touch.\nYour main broker balance remains safe.",
                     font=("Arial", 12, "bold"), text_color="#333", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row2, text="Go to Capital Settings", width=150, fg_color="#2ECC71", 
                      command=lambda: self.nav_bar.set("SETTINGS") or self.show_view("SETTINGS")).pack(side="right")

        # --- Step 3: Select Stocks ---
        s3 = TitanCard(steps_frame, title="STEP 3: CHOOSE STOCKS", height=150, border_color="#9B59B6")
        s3.pack(fill="x", pady=10)
        
        row3 = ctk.CTkFrame(s3, fg_color="transparent")
        row3.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row3, text="3️⃣", font=("Arial", 30), text_color="#1a1a1a").pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row3, text="Select Strategy & Stocks", font=("Roboto", 16, "bold"), text_color="#1a1a1a").pack(anchor="w")
        ctk.CTkLabel(row3, text="Review 'Strategies' tab to see active logic (e.g., RSI).\nGo to Settings > Stocks to add/remove symbols you want to trade.",
                     font=("Arial", 12, "bold"), text_color="#333", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row3, text="Go to Strategies", width=150, fg_color="#9B59B6", 
                      command=lambda: self.nav_bar.set("STRATEGIES") or self.show_view("STRATEGIES")).pack(side="right")

        # --- Step 4: Launch ---
        s4 = TitanCard(steps_frame, title="STEP 4: LAUNCH", height=150, border_color=COLOR_ACCENT)
        s4.pack(fill="x", pady=10)
        
        row4 = ctk.CTkFrame(s4, fg_color="transparent")
        row4.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row4, text="🚀", font=("Arial", 30), text_color="#1a1a1a").pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row4, text="Start the Engine", font=("Roboto", 16, "bold"), text_color="#1a1a1a").pack(anchor="w")
        ctk.CTkLabel(row4, text="Go to DASHBOARD tab.\nClick 'START ENGINE' (Green Button).\nMonitor the 'Market Regime' and 'Logs' for activity.",
                     font=("Arial", 12, "bold"), text_color="#333", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row4, text="Go to Dashboard", width=150, fg_color=COLOR_ACCENT, text_color="black", 
                      font=("Arial", 12, "bold"), command=lambda: self.nav_bar.set("DASHBOARD") or self.show_view("DASHBOARD")).pack(side="right")

    # --- Scanner Methods (Integrated from Patch v2.0.1) ---

    def build_scanner_view(self):
        """
        🔍 MACD SCANNER TAB - One-click market scanning (v2.0.1 Light Theme)
        """
        # Import scanner engine
        try:
            from scanner_engine import MACDScanner
            self.scanner_available = True
        except ImportError as e:
            self.scanner_available = False
            error_msg = str(e)

        # Header
        header = ctk.CTkFrame(self.view_scanner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10), padx=20)

        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkFrame(title_frame, width=4, height=24, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
        ctk.CTkLabel(
            title_frame,
            text=" MARKET SCANNER (MACD + Confluence)",
            font=("Roboto", 20, "bold"),
            text_color="#1a1a1a"  # High contrast
        ).pack(side="left", padx=10)

        # Info Card
        info_card = TitanCard(self.view_scanner, title="HOW IT WORKS", border_color="#D1D5DB")
        info_card.pack(fill="x", padx=20, pady=(0, 10))

        info_text = """
        🔍 Scans 1200+ PRE-FILTERED high-liquidity NSE/BSE stocks
        📊 MACD bullish crossovers + Confluence scoring (MA + RSI filters)
        ⚡ Runs in background - FULL scan takes 30-40 minutes
        🎯 Shows only actionable opportunities (STRONG BUY / BUY)

        Confluence Score Explained:
        • 75-100: STRONG BUY (MACD + Above 20MA + Above 50MA + Healthy RSI + Fresh signal)
        • 60-74:  BUY (MACD + Some trend confirmation)
        • Below 60: Filtered out (not shown)

        💡 Start with FULL scan to see baseline results, then adjust filters if needed
        """

        ctk.CTkLabel(
            info_card,
            text=info_text,
            font=("Roboto", 13),  # +2pt accessibility
            text_color="#2c3e50",  # High contrast
            justify="left"
        ).pack(anchor="w", padx=20, pady=10)

        # Control Panel
        control_card = TitanCard(self.view_scanner, title="SCAN CONTROLS", border_color=COLOR_ACCENT)
        control_card.pack(fill="x", padx=20, pady=(0, 10))

        control_inner = ctk.CTkFrame(control_card, fg_color="transparent")
        control_inner.pack(fill="x", padx=20, pady=15)

        # Scan Mode Selector
        scan_mode_frame = ctk.CTkFrame(control_inner, fg_color="transparent")
        scan_mode_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            scan_mode_frame,
            text="Scan Mode:",
            font=("Roboto", 14, "bold"),  # +2pt
            text_color="#1a1a1a"
        ).pack(side="left", padx=(0, 10))

        self.scan_mode_var = ctk.StringVar(value="FULL")
        scan_mode_selector = ctk.CTkSegmentedButton(
            scan_mode_frame,
            values=["QUICK (300)", "FULL (1200+)"],
            variable=self.scan_mode_var,
            font=("Roboto", 13),  # +2pt
            height=36,
            fg_color="#F3F4F6",
            selected_color=COLOR_ACCENT,
            text_color="#1a1a1a"
        )
        scan_mode_selector.pack(side="left")

        # Start/Stop Buttons
        self.btn_start_scan = ctk.CTkButton(
            control_inner,
            text="🔍 START SCAN",
            command=self.start_scanner,
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            height=42,  # Larger for accessibility
            width=180,
            font=("Roboto", 16, "bold"),  # +2pt
            text_color="white"
        )
        self.btn_start_scan.pack(side="left", padx=10)

        self.btn_stop_scan = ctk.CTkButton(
            control_inner,
            text="⏹ STOP",
            command=self.stop_scanner,
            fg_color=COLOR_DANGER,
            hover_color="#DC2626",
            height=42,
            width=120,
            font=("Roboto", 16, "bold")
        )
        # Don't pack yet - will show when scanning

        # Last Scan Info
        self.lbl_last_scan = ctk.CTkLabel(
            control_inner,
            text="No scans run yet",
            font=("Roboto", 12),  # +2pt
            text_color="#6B7280"
        )
        self.lbl_last_scan.pack(side="right")

        # Progress Card (Hidden initially)
        self.progress_card = TitanCard(self.view_scanner, title="SCAN PROGRESS", border_color="#D1D5DB")
        self.progress_card.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_card.pack_forget()

        progress_inner = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=20, pady=15)

        self.scan_progress_bar = ctk.CTkProgressBar(
            progress_inner,
            height=14,  # Slightly larger
            progress_color=COLOR_ACCENT,
            fg_color="#E5E7EB"
        )
        self.scan_progress_bar.pack(fill="x", pady=(0, 8))
        self.scan_progress_bar.set(0)

        self.lbl_scan_status = ctk.CTkLabel(
            progress_inner,
            text="Preparing scan...",
            font=("Roboto", 13),  # +2pt
            text_color="#1a1a1a"
        )
        self.lbl_scan_status.pack(anchor="w")

        # Results Table
        results_card = TitanCard(self.view_scanner, title="SCAN RESULTS", border_color=COLOR_SUCCESS)
        results_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Filter Row
        filter_frame = ctk.CTkFrame(results_card, fg_color="transparent")
        filter_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            filter_frame,
            text="Show:",
            font=("Roboto", 12),  # +2pt
            text_color="#6B7280"
        ).pack(side="left", padx=5)

        self.scanner_filter_var = ctk.StringVar(value="ALL")
        filter_selector = ctk.CTkSegmentedButton(
            filter_frame,
            values=["ALL", "STRONG BUY", "BUY"],
            variable=self.scanner_filter_var,
            command=self.filter_scanner_results,
            font=("Roboto", 12),  # +2pt
            height=32,
            fg_color="#F3F4F6",
            selected_color=COLOR_ACCENT,
            text_color="#1a1a1a"
        )
        filter_selector.pack(side="left")

        self.lbl_scanner_stats = ctk.CTkLabel(
            filter_frame,
            text="Results: 0",
            font=("Roboto", 11),  # +2pt
            text_color="#6B7280"
        )
        self.lbl_scanner_stats.pack(side="right", padx=10)

        # Treeview Table
        table_frame = ctk.CTkFrame(results_card, fg_color="#F9FAFB")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("Symbol", "Price", "Signal", "Cross Date", "20 DMA", "50 DMA")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Scanner.Treeview",
            background="#FFFFFF",
            foreground="#1a1a1a",  # High contrast
            fieldbackground="#FFFFFF",
            rowheight=36,  # Larger for readability
            font=("Roboto", 13)  # +2pt
        )
        style.configure(
            "Scanner.Treeview.Heading",
            background="#F3F4F6",
            foreground="#1a1a1a",
            font=("Roboto", 14, "bold")  # +2pt
        )

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical")
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal")

        self.scanner_table = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            style="Scanner.Treeview",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        v_scroll.config(command=self.scanner_table.yview)
        h_scroll.config(command=self.scanner_table.xview)

        # Configure columns
        col_widths = {
            "Symbol": 120,
            "Price": 100,
            "Signal": 150,
            "Cross Date": 120,
            "20 DMA": 80,
            "50 DMA": 80
        }

        for col in cols:
            self.scanner_table.heading(col, text=col.upper())
            self.scanner_table.column(col, anchor="center", width=col_widths.get(col, 80))



        # Grid layout
        self.scanner_table.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Configure tags for coloring (Light theme appropriate)
        self.scanner_table.tag_configure("strong_buy", background="#D1FAE5", foreground="#065F46")  # Green tint
        self.scanner_table.tag_configure("buy", background="#FEF3C7", foreground="#92400E")  # Yellow tint

        # Check if scanner available
        if not self.scanner_available:
            self.btn_start_scan.configure(state="disabled", text="❌ Scanner Not Available")
            error_card = TitanCard(self.view_scanner, border_color=COLOR_DANGER)
            error_card.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(
                error_card,
                text=f"⚠️ Scanner engine not found.\nMake sure scanner_engine.py is in the project folder.",
                font=("Roboto", 13),
                text_color=COLOR_DANGER
            ).pack(padx=20, pady=15)

    def start_scanner(self):
        """Start background scanner (Non-blocking)"""
        if self.scanner_running:
            return

        try:
            from scanner_engine import MACDScanner

            # Get scan mode
            mode_str = self.scan_mode_var.get()
            if "300" in mode_str:
                mode = "QUICK"
                max_stocks = None  # Let scanner handle it
            else:
                mode = "FULL"  # 1200+ stocks (RECOMMENDED)
                max_stocks = None

            # UI updates
            self.scanner_running = True
            self.btn_start_scan.pack_forget()
            self.btn_stop_scan.pack(side="left", padx=10)
            self.progress_card.pack(fill="x", padx=20, pady=(0, 10))

            # Clear previous results
            for item in self.scanner_table.get_children():
                self.scanner_table.delete(item)

            self.write_log(f"🔍 Starting market scan ({mode_str} mode)...\n")

            # Create scanner instance
            scanner = MACDScanner(progress_callback=self.scanner_progress_update)

            # Run in background thread (NON-BLOCKING)
            def scan_worker():
                try:
                    results = scanner.scan_market(max_stocks=max_stocks, mode=mode)
                    self.root.after(0, lambda: self.scanner_complete(results))
                except Exception as e:
                    self.root.after(0, lambda: self.scanner_error(str(e)))

            self.scanner_thread = threading.Thread(target=scan_worker, daemon=True)
            self.scanner_thread.start()

        except Exception as e:
            self.write_log(f"❌ Scanner start error: {e}\n")
            self.scanner_running = False

    def stop_scanner(self):
        """Stop running scanner"""
        self.scanner_running = False
        self.write_log("⏹ Stopping scanner...\n")

        # Reset UI
        self.btn_stop_scan.pack_forget()
        self.btn_start_scan.pack(side="left", padx=10)
        self.progress_card.pack_forget()

    def scanner_progress_update(self, current, total, message):
        """Progress callback from scanner (Thread-safe)"""
        try:
            progress = current / total
            self.scan_progress_bar.set(progress)

            pct = int(progress * 100)
            self.lbl_scan_status.configure(text=f"[{pct}%] {message}")
        except:
            pass

    def scanner_complete(self, results):
        """Scanner finished successfully"""
        self.scanner_running = False

        # Store results
        self.scanner_results = results

        # Update UI
        self.btn_stop_scan.pack_forget()
        self.btn_start_scan.pack(side="left", padx=10)
        self.progress_card.pack_forget()

        # Update last scan timestamp
        self.lbl_last_scan.configure(
            text=f"Last scan: {datetime.now().strftime('%d-%b %H:%M')} • Found {len(results)} opportunities"
        )

        # Populate table
        self.populate_scanner_results(results)

        # Log
        self.write_log(f"✅ Scan complete! Found {len(results)} actionable stocks.\n")

        # Show summary
        strong_buy = len([r for r in results if r['signal'] == 'STRONG BUY'])
        buy = len([r for r in results if r['signal'] == 'BUY'])
        self.write_log(f"   🟢 STRONG BUY: {strong_buy} | 🟡 BUY: {buy}\n")

    def scanner_error(self, error_msg):
        """Scanner failed"""
        self.scanner_running = False
        self.btn_stop_scan.pack_forget()
        self.btn_start_scan.pack(side="left", padx=10)
        self.progress_card.pack_forget()

        self.write_log(f"❌ Scanner error: {error_msg}\n")

    def populate_scanner_results(self, results):
        """Populate scanner table with results"""
        # Clear table
        for item in self.scanner_table.get_children():
            self.scanner_table.delete(item)

        # No sorting needed or simple sort by Signal
        # Sort so STRONG BUY is first
        sorted_results = sorted(results, key=lambda x: 0 if x['SIGNAL'] == "STRONG BUY" else 1)

        # Apply filter
        filter_val = self.scanner_filter_var.get() if hasattr(self, 'scanner_filter_var') else "ALL"

        strong_buy_count = 0
        buy_count = 0

        for r in sorted_results:
            signal = r.get('SIGNAL', 'WATCH')
            
            # Filter
            if filter_val != "ALL" and signal != filter_val:
                continue

            # Count
            if signal == 'STRONG BUY':
                strong_buy_count += 1
            else:
                buy_count += 1

            # Tag for coloring
            tag = "strong_buy" if signal == "STRONG BUY" else "buy"
            
            # Values from New Batch Scanner (Keys: SYMBOL, LTP, SIGNAL, CROSS DATE, 20 DMA, 50 DMA)
            self.scanner_table.insert(
                "", END,
                values=(
                    r.get('SYMBOL', 'N/A'),
                    f"₹{r.get('LTP', 0)}",
                    signal,
                    r.get('CROSS DATE', '-'),
                    r.get('20 DMA', '-'),
                    r.get('50 DMA', '-')
                ),
                tags=(tag,)
            )

        # Update stats
        total = strong_buy_count + buy_count
        self.lbl_scanner_stats.configure(
            text=f"Results: {total} • STRONG BUY: {strong_buy_count} • BUY: {buy_count}"
        )

    def filter_scanner_results(self, value=None):
        """Re-populate table with current filter"""
        if hasattr(self, 'scanner_results'):
            self.populate_scanner_results(self.scanner_results)
        # Filter/View Toggle
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent", height=35)
        filter_frame.pack(fill="x", padx=10, pady=(5, 0))

        ctk.CTkLabel(filter_frame, text="Show:", font=("Roboto", 10), text_color="#AAA").pack(side="left", padx=(5, 10))

        self.holdings_filter_var = ctk.StringVar(value="ALL")
        filter_segment = ctk.CTkSegmentedButton(
            filter_frame,
            values=["ALL", "BOT", "MANUAL"],
            variable=self.holdings_filter_var,
            command=self.filter_positions_display,
            font=("Roboto", 15, "bold"), # Increased
            height=36,
            fg_color="#F3F4F6", # Light background
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT,
            unselected_color="#D1D5DB",
            unselected_hover_color="#BCBBBB",
            text_color="black",
            corner_radius=6
        )
        filter_segment.pack(side="left")

        # Summary Stats
        self.lbl_position_stats = ctk.CTkLabel(
            filter_frame,
            text="Positions: 0 • Bot: 0 • Manual: 0",
            font=("Roboto", 11, "bold"), # Increased & Bold
            text_color="#1a1a1a"         # Fixed Visibility
        )
        self.lbl_position_stats.pack(side="right", padx=10)

        # Table Frame - Light & Glassy
        table_frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#D1D5DB")
        table_frame.pack(fill="both", expand=True, padx=2, pady=5)

        cols = ("Symbol", "Source", "Qty", "Entry", "LTP", "P&L", "P&L %")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#FFF", foreground="#1a1a1a", fieldbackground="#FFF", rowheight=38, borderwidth=0, font=("Arial", 12))
        style.configure("Treeview.Heading", background="#F3F4F6", foreground="#374151", font=("Arial", 12, "bold"), borderwidth=0)

        self.pos_table = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.pos_table.heading(col, text=col.upper())
            self.pos_table.column(col, anchor="center")

        self.pos_table.column("Source", width=70)
        self.pos_table.column("Symbol", width=100)
        self.pos_table.column("Qty", width=60)
        self.pos_table.column("Entry", width=80)
        self.pos_table.column("LTP", width=80)
        self.pos_table.column("P&L", width=90)
        self.pos_table.column("P&L %", width=70)

        self.pos_table.pack(fill="both", expand=True)
        self.pos_table.tag_configure("green", foreground=COLOR_SUCCESS)
        self.pos_table.tag_configure("red", foreground=COLOR_DANGER)
        self.pos_table.tag_configure("bot", background="#0A2A0A")  # Dark green tint for BOT
        self.pos_table.tag_configure("manual", background="#2A2A0A")  # Dark yellow tint for MANUAL

        # Store all positions for filtering
        self.all_positions_data = {}

    def filter_positions_display(self, filter_value=None):
        """Filter positions table by source (ALL/BOT/MANUAL)"""
        try:
            filter_val = self.holdings_filter_var.get()

            # Clear table
            for item in self.pos_table.get_children():
                self.pos_table.delete(item)

            # Re-populate based on filter
            total_pnl = 0
            bot_count = 0
            manual_count = 0

            for sym, pos in self.all_positions_data.items():
                source = pos.get("source", "BOT")

                # Apply filter
                if filter_val != "ALL" and source != filter_val:
                    continue

                # Count
                if source == "BOT":
                    bot_count += 1
                else:
                    manual_count += 1

                s = f"{sym[0]}" if isinstance(sym, tuple) else str(sym)
                pnl = pos.get("pnl", 0)
                qty = pos.get("qty", 0)
                avg = pos.get("price", 0)
                ltp = pos.get("ltp", 0)
                if ltp is None: ltp = 0

                # Calculate P&L percentage
                pnl_pct = ((ltp - avg) / avg * 100) if avg > 0 else 0

                total_pnl += pnl
                tag = "green" if pnl >= 0 else "red"
                source_tag = "bot" if source == "BOT" else "manual"

                # Icon prefix for source
                source_icon = "🤖" if source == "BOT" else "👤"

                self.pos_table.insert(
                    "", END,
                    values=(s, f"{source_icon} {source}", qty, f"₹{avg:.2f}", f"₹{ltp:.2f}", f"₹{pnl:.2f}", f"{pnl_pct:+.1f}%"),
                    tags=(tag, source_tag)
                )

            # Update stats
            total_positions = bot_count + manual_count
            self.lbl_position_stats.configure(
                text=f"Positions: {total_positions} • Bot: {bot_count} • Manual: {manual_count}"
            )

        except Exception as e:
            self.write_log(f"❌ Filter error: {e}\n")

    def build_hybrid_view(self):
        """View for managing existing holdings with the "Butler" toggle"""
        scroll = ctk.CTkScrollableFrame(self.view_hybrid, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="🤝 HYBRID PORTFOLIO TAKE-OVER", font=("Roboto", 24, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(scroll, text="Let the bot manage your manual holdings. Enable 'Butler Mode' to apply RSI/Profit rules to existing stocks.", font=("Roboto", 13), text_color="#AAA").pack(anchor="w", pady=(0, 20))
        
        self.hybrid_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.hybrid_list_frame.pack(fill="both", expand=True)
        
        self.refresh_hybrid_holdings()

    def refresh_hybrid_holdings(self):
        """Repopulate the hybrid management list from state/api"""
        for widget in self.hybrid_list_frame.winfo_children():
            widget.destroy()
            
        try:
            # Get latest positions
            positions = self.all_positions_data or safe_get_live_positions_merged()
            
            # Group by manual vs bot (Butler mode typically applies to MANUAL)
            manual_stocks = {k: v for k, v in positions.items() if v.get('source') == 'MANUAL'}
            
            if not manual_stocks:
                ctk.CTkLabel(self.hybrid_list_frame, text="No manual holdings found in mStock portfolio.", font=("Roboto", 14), text_color="#666").pack(pady=50)
                return

            # Header
            header = ctk.CTkFrame(self.hybrid_list_frame, fg_color="#F3F4F6", height=45, border_width=1, border_color="#D1D5DB")
            header.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(header, text="STOCK", font=("Roboto", 13, "bold"), text_color="#374151", width=150, anchor="w").pack(side="left", padx=20)
            ctk.CTkLabel(header, text="UNITS", font=("Roboto", 13, "bold"), text_color="#374151", width=100).pack(side="left")
            ctk.CTkLabel(header, text="AVG PRICE", font=("Roboto", 13, "bold"), text_color="#374151", width=120).pack(side="left")
            ctk.CTkLabel(header, text="BUTLER MODE (AUTO-SELL)", font=("Roboto", 13, "bold"), text_color="#374151").pack(side="right", padx=20)

            # Rows
            for key, pos in manual_stocks.items():
                row = TitanCard(self.hybrid_list_frame, border_color="#D1D5DB", height=55)
                row.pack(fill="x", pady=2)
                
                sym = key[0] if isinstance(key, tuple) else str(key)
                qty = pos.get('qty', 0)
                avg = pos.get('price', 0)
                
                # Check if already managed (from state)
                is_managed = state_mgr.state.get('managed_holdings', {}).get(str(key), False)
                
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="both", expand=True, padx=20)
                
                ctk.CTkLabel(inner, text=sym, font=("Roboto", 16, "bold"), text_color="#1a1a1a", width=150, anchor="w").pack(side="left")
                ctk.CTkLabel(inner, text=str(qty), font=("Roboto", 15), text_color="#333", width=100).pack(side="left")
                ctk.CTkLabel(inner, text=f"₹{avg:,.2f}", font=("Roboto", 15), text_color="#333", width=120).pack(side="left")
                
                sw = ctk.CTkSwitch(inner, text="Enabled" if is_managed else "Disabled", 
                                  command=lambda s=key, v=is_managed: self.toggle_butler_mode(s),
                                  progress_color=COLOR_SUCCESS)
                sw.pack(side="right")
                if is_managed: sw.select()

        except Exception as e:
            self.write_log(f"❌ Hybrid refresh error: {e}\n")

    def toggle_butler_mode(self, symbol_key):
        """Enable/Disable bot management for a specific manual holding"""
        try:
            current_managed = state_mgr.state.get('managed_holdings', {})
            key_str = str(symbol_key)
            
            new_state = not current_managed.get(key_str, False)
            current_managed[key_str] = new_state
            
            state_mgr.state['managed_holdings'] = current_managed
            state_mgr.save()
            
            status_text = "ENABLED" if new_state else "DISABLED"
            self.write_log(f"🤝 Butler Mode {status_text} for {symbol_key}\n")
            
            # Redraw to update text
            self.refresh_hybrid_holdings()
            
        except Exception as e:
            self.write_log(f"❌ butler toggle error: {e}\n")

    # --- DRAWING UTILS (Stubbed for v2) ---
    def draw_mock_graph(self, canvas, color):
        pass

    def draw_meter(self, value):
        pass

    # --- LOGIC ---
    def toggle_bot(self):
        if not self.running: self.start_bot()
        else: self.stop_bot()

    def start_bot(self):
        import kickstart
        kickstart.reset_stop_flag()
        kickstart.set_log_callback(self.write_log)  # Connect logs to UI
        kickstart.set_log_callback(self.write_log)  # Connect logs to UI
        kickstart.initialize_stock_configs()             # Load Symbols (Migrated from CSV)
        
        self.running = True
        self.stop_update_flag.clear()
        self.btn_start.configure(text="🛑 STOP ENGINE", fg_color=COLOR_DANGER, hover_color="#D50000")
        self.write_log("--- Trade Execution Monitor Initialized ---\n")
        # Force scroll to monitor tab if possible (needs specialized logic, but at least ensure log sees it)
        try: 
            if hasattr(self, 'trade_log'): self.trade_log.see("0.0") 
        except: pass

        if hasattr(self, 'lbl_engine_status'):
             self.lbl_engine_status.configure(text="STATUS: RUNNING 🟢", text_color=COLOR_SUCCESS)
        
        self.write_log("🚀 ENGINE STARTED. Waiting for data...\n")
        threading.Thread(target=self.engine_loop, daemon=True).start()
        threading.Thread(target=self.rsi_worker, daemon=True).start()

    def stop_bot(self):
        if messagebox.askyesno("STOP", "Stop Trading Engine?"):
            import kickstart
            kickstart.request_stop()
            
            self.running = False
            self.stop_update_flag.set()
            self.btn_start.configure(text="▶ START ENGINE", fg_color=COLOR_SUCCESS, hover_color="#00C853")
            
            if hasattr(self, 'lbl_engine_status'):
                 self.lbl_engine_status.configure(text="STATUS: STOPPED 🔴", text_color=COLOR_DANGER)
            
            self.write_log("🛑 Engine Stopped.\n")
            self.write_log("--- Trade Execution Monitor Stopped ---\n")

    def engine_loop(self):
        try:
            import kickstart
        except Exception as import_err:
            self.write_log(f"❌ Failed to import kickstart: {import_err}\n")
            return
        
        while not self.stop_update_flag.is_set():
            try:
                if not self.running:
                    break
                kickstart.run_cycle()
            except Exception as e:
                import traceback
                self.write_log(f"❌ Engine Cycle Error: {e}\n")
            time.sleep(0.5)

    def rsi_worker(self):
        # ... logic similar to previous ...
        tf_map = {"1T":"1m","3T":"3m","5T":"5m","10T":"10m","15T":"15m","30T":"30m","1H":"1h","1D":"1d"}
        while not self.stop_update_flag.is_set():
            with ThreadPoolExecutor(max_workers=4) as executor:
                for symbol, exchange in SYMBOLS_TO_TRACK:
                     executor.submit(self._rsi_task, symbol, exchange, tf_map)
            time.sleep(30)
            
    def _rsi_task(self, symbol, exchange, tf_map):
         try:
            from kickstart import get_stabilized_rsi, config_dict, fetch_market_data
            conf = config_dict.get((symbol, exchange), {})
            timeframe = conf.get("Timeframe", "15T")
            instrument_token = conf.get("instrument_token")
            
            if not instrument_token:
                 # Skip if no token, don't crash the loop
                 return

            md, _ = fetch_market_data(symbol, exchange) 
            ltp = md.get("last_price") if md else None
            
            ts, rsi_val = get_stabilized_rsi(symbol, exchange, timeframe, instrument_token, live_price=ltp)
            if rsi_val: 
                self.data_queue.put(("rsi", (symbol, rsi_val, ltp)))
         except Exception as e:
            # print(f"RSI Task Error for {symbol}: {e}")
            pass

    def sentiment_worker(self):
        while not self.stop_update_flag.is_set():
            try:
                data = self.sentiment_engine.fetch_sentiment()
                if data: self.data_queue.put(("sentiment", data))
            except: pass
            time.sleep(300)

    def update_ui_loop(self):
        try:
            while not self.data_queue.empty():
                dtype, data = self.data_queue.get_nowait()
                if dtype == "positions": self.update_positions(data)
                elif dtype == "sentiment": self.update_sentiment(data)
                elif dtype == "rsi": 
                    # data = (symbol, rsi_val, ltp)
                    sym, rsi_val, ltp = data
                    # Update LTP in all_positions_data if it exists
                    updated = False
                    for key in self.all_positions_data:
                        if (isinstance(key, tuple) and key[0] == sym) or str(key) == sym:
                            self.all_positions_data[key]['ltp'] = ltp
                            updated = True
                    
                    if updated:
                        # Refresh display (throttled/batched)
                        self.filter_positions_display(self.holdings_filter_var.get() if hasattr(self, 'holdings_filter_var') else "ALL")
        except queue.Empty: pass
        finally: self.root.after(1000, self.update_ui_loop)

    def update_positions(self, data):
        # Store all positions data for filtering
        self.all_positions_data = data

        # Clear table
        for item in self.pos_table.get_children():
            self.pos_table.delete(item)

        total_pnl = 0
        used_capital = 0
        bot_count = 0
        manual_count = 0

        filter_val = self.holdings_filter_var.get()

        for sym, pos in data.items():
            source = pos.get("source", "BOT")

            # Apply filter
            if filter_val != "ALL" and source != filter_val:
                continue

            # Count
            if source == "BOT":
                bot_count += 1
            else:
                manual_count += 1

            s = f"{sym[0]}" if isinstance(sym, tuple) else str(sym)
            pnl = pos.get("pnl", 0)
            qty = pos.get("qty", 0)
            avg = pos.get("price", 0)
            ltp = pos.get("ltp", 0)

            # Calculate P&L percentage
            pnl_pct = ((ltp - avg) / avg * 100) if avg > 0 else 0

            # Calculate metrics
            invested = qty * avg
            if source == "BOT":
                used_capital += invested

            total_pnl += pnl
            tag = "green" if pnl >= 0 else "red"
            source_tag = "bot" if source == "BOT" else "manual"

            # Icon prefix for source
            source_icon = "🤖" if source == "BOT" else "👤"

            self.pos_table.insert(
                "", END,
                values=(s, f"{source_icon} {source}", qty, f"₹{avg:.2f}", f"₹{ltp:.2f}", f"₹{pnl:.2f}", f"{pnl_pct:+.1f}%"),
                tags=(tag, source_tag)
            )

        # Update Summary Stats Label
        if hasattr(self, 'lbl_position_stats'):
            self.lbl_position_stats.configure(
                text=f"Positions: {len(data)} • Bot: {bot_count} • Manual: {manual_count}"
            )

        # Update position stats with Live indicator
        total_positions = bot_count + manual_count
        now_str = datetime.now().strftime("%H:%M")
        self.lbl_position_stats.configure(
            text=f"🟢 Live {now_str} • {total_positions} positions (Bot: {bot_count} | Manual: {manual_count})"
        )

        self.lbl_pnl.configure(text=f"₹{total_pnl:,.2f}", text_color=COLOR_SUCCESS if total_pnl >= 0 else COLOR_DANGER)
        
        # Update Safety Box Bar
        try:
            from kickstart import ALLOCATED_CAPITAL
            limit = ALLOCATED_CAPITAL
            if limit > 0:
                pct = min(1.0, used_capital / limit)
                self.cap_bar.set(pct)
                self.lbl_cap_usage.configure(text=f"₹{used_capital:,.0f} / ₹{limit:,.0f}")
        except: pass

    def update_sentiment(self, data):
        # self.draw_meter(data['score']) # Removed
        # self.lbl_sentiment_val.configure(text=f"{int(data.get('score', 50))} - {data.get('zone', 'NEUTRAL')}") # Removed in Quick Monitor redesign
        # self.lbl_sentiment_reason.configure(text=f"WHY? {data['details']}")
        pass  # Function kept for compatibility but sentiment display removed

    def refresh_balance(self):
        """Fetch real-time balance from broker API"""
        try:
            from kickstart import fetch_funds, ALLOCATED_CAPITAL
            
            # Hot-reload settings to ensure capital is current
            if hasattr(self, 'settings_mgr'):
                self.settings_mgr.load()
                # Priority: allocated_limit (user setting) -> total_capital (default) -> Hardcoded
                val = self.settings_mgr.get("capital.allocated_limit", 0)
                if val <= 0:
                    val = self.settings_mgr.get("capital.total_capital", 50000.0)
                allocation_setting = val
                # DEBUG LOG
                self.write_log(f"DEBUG: Allocation Setting Read: {allocation_setting}\n")
            else:
                allocation_setting = 50000.0

            # Fetch balance in background thread to avoid UI freeze
            def fetch_and_update():
                try:
                    available_cash = fetch_funds()  # Real-time API call

                    # Prefer setting over global if they mismatch
                    allocated = float(allocation_setting)

                    # Get currently deployed capital from positions
                    positions = safe_get_live_positions_merged()
                    deployed = 0.0
                    for sym, pos in positions.items():
                        source = pos.get("source", "BOT")
                        if source == "BOT":
                            qty = pos.get("qty", 0)
                            avg_price = pos.get("price", 0)
                            deployed += qty * avg_price

                    # Calculate total balance
                    total_balance = available_cash + deployed

                    # Update UI on main thread
                    self.root.after(0, lambda: self.update_balance_display(
                        total_balance, available_cash, allocated, deployed
                    ))

                except Exception as e:
                    self.root.after(0, lambda: self.write_log(f"❌ Balance fetch error: {e}\n"))

            # Run in background
            threading.Thread(target=fetch_and_update, daemon=True).start()

        except Exception as e:
            self.write_log(f"❌ Balance refresh failed: {e}\n")

    def update_balance_display(self, total, available, allocated, in_positions):
        """Update Account Balance Card with new data"""
        try:
            # Update labels (Match names in build_dashboard_view)
            if hasattr(self, 'lbl_total_balance'):
                self.lbl_total_balance.configure(text=f"₹{total:,.2f}")
            
            if hasattr(self, 'lbl_total_allocated'):
                self.lbl_total_allocated.configure(text=f"₹{allocated:,.0f}")
                
            if hasattr(self, 'lbl_pnl'):
                # PnL is optional here if not passed, but usually handled by position loop
                pass

            # Update timestamp if label exists
            if hasattr(self, 'lbl_balance_timestamp'):
                now = datetime.now().strftime("%H:%M:%S")
                self.lbl_balance_timestamp.configure(text=f"Updated: {now}")

            # Also update bot wallet if method exists
            if hasattr(self, 'update_wallet_display'):
                self.update_wallet_display(allocated, in_positions)

        except Exception as e:
            self.write_log(f"❌ Display update error: {e}\n")

    def update_wallet_display(self, allocated, deployed):
        """Update Bot Wallet Breakdown Card"""
        try:
            # Update total allocated
            self.lbl_total_allocated.configure(text=f"₹{allocated:,.0f}")

            # Calculate percentages
            if allocated > 0:
                pct_deployed = (deployed / allocated) * 100
                pct_available = 100 - pct_deployed
                available = allocated - deployed

                # Update progress bar
                self.wallet_progress.set(min(1.0, deployed / allocated))

                # Update labels
                self.lbl_deployed.configure(text=f"₹{deployed:,.0f} ({pct_deployed:.0f}%)")
                self.lbl_available_wallet.configure(text=f"₹{available:,.0f} ({pct_available:.0f}%) Available")

                # Change color based on usage
                if pct_deployed > 90:
                    self.wallet_progress.configure(progress_color=COLOR_DANGER)
                elif pct_deployed > 70:
                    self.wallet_progress.configure(progress_color=COLOR_WARN)
                else:
                    self.wallet_progress.configure(progress_color=COLOR_SUCCESS)

        except Exception as e:
            self.write_log(f"❌ Wallet update error: {e}\n")

    def refresh_quick_monitor(self):
        """Refresh Quick Monitor with live data from database and API (Background Thread)"""
        
        def fetch_worker():
            try:
                # 1. Fetch Wallet Balance (API - Slow)
                wallet_balance = 0.0
                try:
                    from kickstart import fetch_funds
                    wallet_balance = fetch_funds()
                except Exception:
                    wallet_balance = -1 # Indicate failure

                # 2. Fetch DB Stats (Fast but still I/O)
                perf_data = {}
                recent_trades_list = []
                today_trades_list = []
                
                if DATABASE_AVAILABLE and db:
                    perf_data = db.get_performance_summary(days=1)
                    recent_trades_list = db.get_recent_trades(limit=5)
                    today_trades_list = db.get_today_trades()

                # 3. Fetch Positions (API - Shared with engine)
                live_pos_data = {}
                try:
                    from kickstart import safe_get_live_positions_merged
                    live_pos_data = safe_get_live_positions_merged()
                except: pass

                # 4. Schedule UI Update
                self.root.after(0, lambda: self._update_quick_monitor_ui(
                    wallet_balance, perf_data, recent_trades_list, today_trades_list, live_pos_data
                ))
            except Exception as e:
                # self.write_log(f"Quick Monitor Fetch Error: {e}\n")
                pass

        threading.Thread(target=fetch_worker, daemon=True).start()
        
        # Schedule next refresh (every 10 seconds)
        self.root.after(10000, self.refresh_quick_monitor)

    def _update_quick_monitor_ui(self, balance, perf, recent_trades, today_trades, live_pos):
        """Update UI elements on main thread"""
        try:
            # 1. Update Positions Table
            if live_pos:
                self.update_positions(live_pos)
            
            # 1b. Update Trades History Table (Live Sync)
            self.refresh_trades_history()

                
            # 2. Update Wallet Balance with change detection
            if balance != -1 and hasattr(self, 'lbl_total_balance'):
                new_balance = f"₹{balance:,.2f}"
                if getattr(self.lbl_total_balance, "_current_text", "") != new_balance:
                    self.lbl_total_balance.configure(text=new_balance)
                    self.lbl_total_balance._current_text = new_balance

            # 3. Update Bot Capital Usage (Sync with Settings)
            try:
                # Hot-reload settings to ensure capital is current
                self.settings_mgr.load()
                allocated = self.settings_mgr.get("capital.allocated_limit", 0)
                if allocated <= 0:
                    allocated = self.settings_mgr.get("capital.total_capital", 50000.0)
                
                # Calculate currently deployed (BOT only)
                deployed = 0.0
                if live_pos:
                    for sym, pos in live_pos.items():
                        if pos.get("source") == "BOT":
                            deployed += pos.get("qty", 0) * pos.get("price", 0)

                # Update Bot Capital labels with change detection
                if hasattr(self, 'lbl_total_allocated'):
                    new_alloc_txt = f"₹{allocated:,.0f}"
                    if getattr(self.lbl_total_allocated, "_current_text", "") != new_alloc_txt:
                        self.lbl_total_allocated.configure(text=new_alloc_txt)
                        self.lbl_total_allocated._current_text = new_alloc_txt

                if hasattr(self, 'lbl_deployed'):
                    new_dep_txt = f"Used: ₹{deployed:,.0f}"
                    if getattr(self.lbl_deployed, "_current_text", "") != new_dep_txt:
                        self.lbl_deployed.configure(text=new_dep_txt)
                        self.lbl_deployed._current_text = new_dep_txt

                if hasattr(self, 'wallet_progress') and allocated > 0:
                    new_prog = min(1.0, deployed / allocated)
                    if getattr(self, "_current_prog", -1) != new_prog:
                        self.wallet_progress.set(new_prog)
                        self._current_prog = new_prog
                        
                        # Dynamic color
                        pct = new_prog * 100
                        color = COLOR_SUCCESS if pct < 70 else COLOR_WARN if pct < 90 else COLOR_DANGER
                        self.wallet_progress.configure(progress_color=color)

                if hasattr(self, 'lbl_available_wallet') and allocated > 0:
                    avail = max(0, allocated - deployed)
                    avail_pct = max(0, 100 - (deployed/allocated*100))
                    new_avail_txt = f"₹{avail:,.0f} ({avail_pct:.0f}%) Available"
                    if getattr(self.lbl_available_wallet, "_current_text", "") != new_avail_txt:
                        self.lbl_available_wallet.configure(text=new_avail_txt)
                        self.lbl_available_wallet._current_text = new_avail_txt
            except: pass

            # 4. Update P&L
            net_profit = perf.get('net_profit', 0)
            if hasattr(self, 'lbl_pnl'):
                color = COLOR_SUCCESS if net_profit >= 0 else COLOR_DANGER
                prefix = "+" if net_profit > 0 else ""
                new_text = f"{prefix}₹{net_profit:,.2f}"
                if getattr(self.lbl_pnl, "_current_text", "") != new_text:
                    self.lbl_pnl.configure(text=new_text, text_color=color)
                    self.lbl_pnl._current_text = new_text
            
            # 5. Update Trade Count
            if hasattr(self, 'lbl_trade_count'):
                count = len(today_trades) if today_trades is not None else 0
                new_text = f"{count} trades today"
                if getattr(self.lbl_trade_count, "_current_text", "") != new_text:
                    self.lbl_trade_count.configure(text=new_text, text_color="#333")
                    self.lbl_trade_count._current_text = new_text
            
            # 6. Update Win Rate
            if hasattr(self, 'lbl_win_rate'):
                win = perf.get('winning_trades', 0)
                lose = perf.get('losing_trades', 0)
                rate = perf.get('win_rate', 0)
                new_text = f"{rate}% ({win}W / {lose}L)"
                if getattr(self.lbl_win_rate, "_current_text", "") != new_text:
                    self.lbl_win_rate.configure(text=new_text, text_color="#1a1a1a")
                    self.lbl_win_rate._current_text = new_text
            
            # 7. Update Recent Trades (Smart Refresh)
            if hasattr(self, 'recent_trades_frame') and recent_trades:
                current_top_id = f"{recent_trades[0].get('symbol')}_{recent_trades[0].get('timestamp')}"
                if getattr(self, "_prev_top_trade_id", "") != current_top_id:
                    for widget in self.recent_trades_frame.winfo_children():
                        widget.destroy()
                    
                    for trade in recent_trades:
                        action = trade.get('action', '?').upper()
                        symbol = trade.get('symbol', '?')
                        qty = trade.get('quantity', 0)
                        price = trade.get('price', 0)
                        
                        action_icon = "🟢" if action == "BUY" else "🔴"
                        color = COLOR_SUCCESS if action == "BUY" else COLOR_DANGER
                        
                        row = ctk.CTkFrame(self.recent_trades_frame, fg_color="transparent")
                        row.pack(fill="x", pady=1)
                        ctk.CTkLabel(row, text=f"{action_icon} {action}", font=("Roboto", 10, "bold"), text_color=color).pack(side="left")
                        ctk.CTkLabel(row, text=f" {symbol} {qty} @ ₹{price:.1f}", font=("Roboto", 11, "bold"), text_color="#1a1a1a").pack(side="left")
                    
                    self._prev_top_trade_id = current_top_id

            # 8. Update Live Execution Counters from StateManager (Source of Truth)
            try:
                from state_manager import state as state_mgr
                counters = state_mgr.get_trade_counters()
                
                # Sync local trade_stats for consistency
                self.trade_stats['attempts'] = counters.get('attempts', 0)
                self.trade_stats['success'] = counters.get('success', 0)
                self.trade_stats['failed'] = counters.get('failed', 0)

                for key, attr in [('attempts', 'lbl_attempt_count'), ('success', 'lbl_success_count'), ('failed', 'lbl_fail_count')]:
                    if hasattr(self, attr):
                        lbl = getattr(self, attr)
                        val = str(counters.get(key, 0))
                        if getattr(lbl, "_current_val", "") != val:
                            lbl.configure(text=val)
                            lbl._current_val = val
                
                # 9. Update Engine Heartbeat
                if hasattr(self, 'lbl_heartbeat') and self.running:
                    # We can use state.get('last_update') which is updated every cycle
                    last_upd = state_mgr.state.get('last_update')
                    if last_upd:
                        # Extract time component: 2026-02-02T13:28:26.123 -> 13:28:26
                        t_part = last_upd.split('T')[-1].split('.')[0]
                        self.lbl_heartbeat.configure(text=f"Last Cycle: {t_part}", text_color=COLOR_ACCENT)
                    else:
                        self.lbl_heartbeat.configure(text="Engine Active... 💓", text_color=COLOR_ACCENT)
                elif hasattr(self, 'lbl_heartbeat'):
                    self.lbl_heartbeat.configure(text="Engine Idle", text_color="gray")

            except Exception as e:
                import sys
                print(f"DEBUG: Counter Sync Error: {e}", file=sys.__stderr__)
        except Exception as e:
            pass # Silent fail to prevent UI lockup in loop
            
        except Exception as e:
            print(f"UI Update Error: {e}")

    def write_log(self, text):
        """Redirect print/logs to UI Console and Alert Box (Thread-Safe)"""
        # Schedule the update on the main thread
        self.root.after(0, lambda: self._write_log_main_thread(text))

    def _write_log_main_thread(self, text):
        if not text.strip(): return
        
        # Avoid redundancy: if the text already contains a timestamp or level tag, don't wrap it again
        if "|" in text and any(x in text for x in ["INFO", "ERROR", "WARNING", "DEBUG"]):
            formatted = text.strip()
            timestamp = formatted.split("|")[0].strip()[:8] # Extract existing time if possible
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted = f"{timestamp} | {text.strip()}"
        
        # 1. Technical Log (Bottom/Logs Tab) - Show Everything
        try:
            if hasattr(self, 'log_area'):
                self.log_area.configure(state="normal")
                self.log_area.insert("end", formatted + "\n")
                self.log_area.see("end")
                self.log_area.configure(state="disabled")
        except: pass
        
        # 2. Trade Activity Monitor (Tab 2) - LIVE EXECUTION TRACKING
        text_lower = text.lower()
        
        # ONLY show actual trade actions: BUY, SELL, Orders placed/executed
        # Exclude: debug messages, allocation settings, engine status, RSI readings
        is_trade_action = any(x in text_lower for x in [
            "attempting buy", "attempting sell",  # Trade attempts
            "buy order", "sell order",             # Order placement
            "executed", "filled", "placed",        # Successful trades
            "order rejected", "order failed",      # Failed trades
            "stop loss triggered", "profit target hit",  # Exit conditions
            "⚡ signal",                            # Trade signals
            "initialized", "status", "bot started", "monitoring", # System Status
            "paper trade", "buy", "sell"           # Explicit Actions
        ])
        is_failure = any(x in text_lower for x in ["failed", "rejected", "insufficient"])
        is_success = any(x in text_lower for x in ["placed", "executed", "filled"])
        
        # Skip debug messages, engine status, allocation settings
        is_noise = any(x in text_lower for x in ["debug", "allocation", "module", "cycle start"])
        
        if is_trade_action and not is_noise:
            try:
                # UPDATE: Counters are now synchronized directly with StateManager in _update_quick_monitor_ui
                # to ensure data integrity across components and restarts.
                
                # Update Activity Log Textbox
                if hasattr(self, 'trade_log'):
                    self.trade_log.configure(state="normal")
                    prefix = "❌ " if is_failure else "✅ " if is_success else "ℹ "
                    self.trade_log.insert("0.0", f"{timestamp} {prefix} {text}\n") # Insert at top
                    self.trade_log.configure(state="disabled")
            except Exception as e:
                print(f"UI Update Error: {e}", file=sys.__stderr__) # Fallback

        # 3. Recent Alerts (Top Left) - High Level Only
        should_alert = False
        is_tech_error = any(x in text for x in ["Exception", "Expecting value", "No price data"])
        
        if is_trade_action and not is_tech_error:
             should_alert = True
        elif "⚠" in text and not is_tech_error:
             should_alert = True
             
        if should_alert:
            try:
                if hasattr(self, 'alert_box'):
                    self.alert_box.insert("0.0", f"{text}\n")
                    # Optional: Limit length
                    content = self.alert_box.get("0.0", "end")
                    if len(content.splitlines()) > 50:
                        self.alert_box.delete("50.0", "end")
            except: pass
    
    def emergency_exit(self):
        if messagebox.askyesno("CONFIRM", "Panic Sell All?"):
             import kickstart
             kickstart.panic_button()

    def run(self):
        self.root.mainloop()

# --- UTILS for Startup ---
# --- UTILS for Startup ---
def check_single_instance():
    LOCK_FILE = "arun_bot.lock"
    if os.path.exists(LOCK_FILE):
        try: os.remove(LOCK_FILE)
        except: pass

def show_disclaimer(root, on_accept):
    """Shows disclaimer on the provided root window"""
    # Clear root
    for widget in root.winfo_children():
        widget.destroy()
        
    root.title("⚠️ Important Disclaimer")
    root.geometry("650x550")
    
    # Center logic (roughly)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (600 // 2)
    y = (screen_height // 2) - (500 // 2)
    root.geometry(f"+{int(x)}+{int(y)}")

    ctk.CTkLabel(root, text="⚠️ ARUN TRADING BOT", font=("Arial", 24, "bold"), text_color="#E74C3C").pack(pady=(30, 10))
    ctk.CTkLabel(root, text="User Responsibility Agreement", font=("Arial", 16)).pack(pady=(0, 20))

    text_frame = ctk.CTkFrame(root, fg_color="#2B2B2B")
    text_frame.pack(fill="both", expand=True, padx=30, pady=10)

    disclaimer_text = """
    ⚠️ CRITICAL WARNING - READ BEFORE PROCEEDING ⚠️

    1. NOT FINANCIAL ADVICE
    The ARUN Trading Bot is a SOFTWARE TOOL ONLY. It does NOT provide investment, financial, legal, or tax advice.
    
    2. HIGH RISK - POTENTIAL TOTAL LOSS
    Trading stocks and derivatives involves significant risk. You could lose SOME or ALL of your invested capital.
    
    3. USER RESPONSIBILITY
    • YOU are responsible for all trading decisions
    • YOU accept full liability for any profits OR losses
    • The developers are NOT liable for any financial losses
    
    4. PAPER TRADING FIRST
    You MUST test your strategies in "Paper Trading" mode before risking real money.
    
    By clicking "I ACCEPT", you confirm you understand these risks.
    """
    
    textbox = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 12))
    textbox.insert("0.0", disclaimer_text)
    textbox.configure(state="disabled")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)

    def accept():
        # Clear disclaimer widgets
        for widget in root.winfo_children():
            widget.destroy()
        on_accept()

    def decline():
        sys.exit(0)

    btn_frame = ctk.CTkFrame(root, fg_color="transparent")
    btn_frame.pack(pady=20)
    
    ctk.CTkButton(btn_frame, text="I ACCEPT", command=accept, fg_color="#27AE60", font=("Arial", 14, "bold"), width=200).grid(row=0, column=0, padx=10)
    ctk.CTkButton(btn_frame, text="DECLINE", command=decline, fg_color="#C0392B", font=("Arial", 14, "bold"), width=150).grid(row=0, column=1, padx=10)


def check_single_instance():
    """
    Ensure only one instance of the dashboard is running via lock file.
    Handles stale locks by checking process existence.
    """
    lock_file = os.path.join(tempfile.gettempdir(), "sensei_v1.lock")
    
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            if psutil:
                is_running = psutil.pid_exists(pid)
            else:
                # Fallback to os.kill if psutil is somehow missing later
                if os.name == 'nt':
                    try:
                        # On Windows, os.kill(pid, 0) can fail with WinError 87
                        # if the PID is invalid or already half-dead.
                        # We use a broader try-except.
                        os.kill(pid, 0) 
                        is_running = True
                    except (OSError, SystemError):
                        is_running = False
                else:
                    try:
                        os.kill(pid, 0)
                        is_running = True
                    except OSError:
                        is_running = False
            
            if is_running:
                # Check if it's OUR process (paranoid check) - skipped for simplicity
                # Alert user and exit
                root = ctk.CTk()
                root.withdraw() # Hide main window
                messagebox.showerror("Already Running", "An instance of Sensei Dashboard is already open.")
                sys.exit(0)
            else:
                # Stale lock, remove it
                try:
                    os.remove(lock_file)
                except: pass
                
        except (ValueError, OSError):
            # Corrupt lock file or other error, remove it
            try:
                os.remove(lock_file)
            except: pass

    # Create new lock
    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        
        # Register cleanup
        def cleanup_lock():
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except: pass
            
        atexit.register(cleanup_lock)
        
    except Exception as e:
        print(f"Failed to create lock file: {e}")

if __name__ == "__main__":
    try:
        check_single_instance()
        
        # Initialize Root ONCE
        ctk.set_appearance_mode("dark")
        root = ctk.CTk()
        root.title("ARUN TITAN V2 - Launcher")
        
        def start_dashboard():
            # This runs after disclaimer accept
            app = DashboardV2(root)
            # No need to call app.run() since we have root.mainloop() below
        
        # Show Disclaimer first
        show_disclaimer(root, start_dashboard)
        
        root.mainloop()
        
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)

