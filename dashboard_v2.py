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

# --- UI CONSTANTS ---
COLOR_BG = "#050505"      # Pitch Black Background
COLOR_CARD = "#121212"    # Dark Card Background
COLOR_ACCENT = "#00F0FF"  # Cyber Cyan (Primary)
COLOR_DANGER = "#FF003C"  # Cyber Red (danger/loss)
COLOR_SUCCESS = "#00E676" # Neon Green (profit/gain)
COLOR_WARN = "#FFB74D"    # Orange (warning/monitor)
FONT_MAIN = ("Roboto Medium", 12)
FONT_HEADER = ("Roboto", 14, "bold")
FONT_BIG = ("Roboto", 32, "bold")

class TitanCard(ctk.CTkFrame):
    """A standardized Titan-style card with glowing borders"""
    def __init__(self, parent, title=None, border_color="#222", **kwargs):
        super().__init__(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=border_color, **kwargs)
        if title:
            # Title Bar
            self.title_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
            self.title_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            # Accent Pill
            ctk.CTkFrame(self.title_frame, width=4, height=16, fg_color=COLOR_ACCENT, corner_radius=2).pack(side="left")
            
            ctk.CTkLabel(self.title_frame, text=title.upper(), font=("Roboto", 11, "bold"), text_color="#AAA").pack(side="left", padx=10)

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

        # Log redirection
        sys.stdout.write = self.write_log
        sys.stderr.write = self.write_log

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
        
        self.build_dashboard_view()
        self.build_strategies_view()
        self.build_settings_view()
        self.build_knowledge_view()
        self.build_logs_view()
        self.build_start_here_view()
        
        # Default View (show START HERE for new users, else Dashboard)
        if self.settings_mgr.get("capital.allocated_limit", 0) <= 0:
            self.show_view("START HERE")
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
        # INSTANT: Load cached holdings before anything else
        self.load_cached_holdings()
        
        threading.Thread(target=self.sentiment_worker, daemon=True).start()
        threading.Thread(target=self.positions_worker, daemon=True).start()

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
            time.sleep(30)  # Refresh every 30 seconds

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
        ctk.CTkLabel(logo_frame, text="ARUN", font=("Roboto", 20, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        ctk.CTkLabel(logo_frame, text="TITAN", font=("Roboto", 20, "bold"), text_color="white").pack(side="left", padx=5)

        # Navigation (Segmented Button Style)
        self.nav_var = ctk.StringVar(value="DASHBOARD")
        self.nav_bar = ctk.CTkSegmentedButton(
            header, 
            values=["START HERE", "DASHBOARD", "KNOWLEDGE", "STRATEGIES", "SETTINGS", "LOGS"],
            command=self.show_view,
            font=("Roboto", 12, "bold"),
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT,
            unselected_color="#000",
            unselected_hover_color="#222",
            text_color="white",
            fg_color="#000",
            height=32,
            width=550
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
             # Could also refresh UI elements if needed
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

    def build_dashboard_view(self):
        """Replicates the Titan Mockup Grid with Enhanced Balance & Capital Tracking"""
        # Grid Layout
        self.view_dashboard.grid_columnconfigure(0, weight=1) # Left Col
        self.view_dashboard.grid_columnconfigure(1, weight=1) # Right Col

        # --- ROW 0: ACCOUNT BALANCE & BOT WALLET ---
        row0 = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        row0.pack(fill="x", pady=(0, 5))

        # 1. Account Balance Card
        self.card_balance = TitanCard(row0, title="ACCOUNT BALANCE", width=400, height=180, border_color=COLOR_ACCENT)
        self.card_balance.pack(side="left", fill="both", expand=True, padx=(0, 10))

        balance_content = ctk.CTkFrame(self.card_balance, fg_color="transparent")
        balance_content.pack(fill="both", expand=True, padx=15, pady=10)

        # Balance Display
        self.lbl_total_balance = ctk.CTkLabel(balance_content, text="₹0.00", font=("Roboto", 36, "bold"), text_color="white")
        self.lbl_total_balance.pack(anchor="w", pady=(5, 0))

        # Breakdown
        breakdown_frame = ctk.CTkFrame(balance_content, fg_color="transparent")
        breakdown_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(breakdown_frame, text="Available Cash:", font=("Roboto", 11), text_color="#AAA").grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_available_cash = ctk.CTkLabel(breakdown_frame, text="₹0.00", font=("Roboto", 11, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_available_cash.grid(row=0, column=1, sticky="e", padx=(10, 0), pady=2)

        ctk.CTkLabel(breakdown_frame, text="Allocated to Bots:", font=("Roboto", 11), text_color="#AAA").grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_allocated = ctk.CTkLabel(breakdown_frame, text="₹0.00", font=("Roboto", 11, "bold"), text_color=COLOR_WARN)
        self.lbl_allocated.grid(row=1, column=1, sticky="e", padx=(10, 0), pady=2)

        ctk.CTkLabel(breakdown_frame, text="In Open Positions:", font=("Roboto", 11), text_color="#AAA").grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_in_positions = ctk.CTkLabel(breakdown_frame, text="₹0.00", font=("Roboto", 11, "bold"), text_color=COLOR_DANGER)
        self.lbl_in_positions.grid(row=2, column=1, sticky="e", padx=(10, 0), pady=2)

        breakdown_frame.grid_columnconfigure(1, weight=1)

        # Refresh Button & Timestamp
        refresh_frame = ctk.CTkFrame(self.card_balance, fg_color="transparent")
        refresh_frame.place(relx=0.95, rely=0.05, anchor="ne")

        self.btn_refresh_balance = ctk.CTkButton(
            refresh_frame, text="🔄", width=30, height=25,
            fg_color="#222", hover_color="#333",
            command=self.refresh_balance,
            font=("Arial", 14)
        )
        self.btn_refresh_balance.pack()

        self.lbl_balance_timestamp = ctk.CTkLabel(self.card_balance, text="Updated: --:--", font=("Roboto", 9), text_color="#666")
        self.lbl_balance_timestamp.place(relx=0.02, rely=0.95, anchor="sw")

        # 2. Bot Wallet Breakdown Card
        self.card_wallet = TitanCard(row0, title="BOT CAPITAL ALLOCATION", width=400, height=180, border_color=COLOR_WARN)
        self.card_wallet.pack(side="left", fill="both", expand=True, padx=(10, 0))

        wallet_content = ctk.CTkFrame(self.card_wallet, fg_color="transparent")
        wallet_content.pack(fill="both", expand=True, padx=15, pady=10)

        # Total Allocated
        alloc_row = ctk.CTkFrame(wallet_content, fg_color="transparent")
        alloc_row.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(alloc_row, text="Total Allocated:", font=("Roboto", 11), text_color="#AAA").pack(side="left")
        self.lbl_total_allocated = ctk.CTkLabel(alloc_row, text="₹50,000", font=("Roboto", 18, "bold"), text_color="white")
        self.lbl_total_allocated.pack(side="right")

        # Deployment Progress
        deploy_frame = ctk.CTkFrame(wallet_content, fg_color="transparent")
        deploy_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(deploy_frame, text="Currently Deployed:", font=("Roboto", 10), text_color="#AAA").pack(anchor="w")
        self.wallet_progress = ctk.CTkProgressBar(deploy_frame, height=12, progress_color=COLOR_SUCCESS)
        self.wallet_progress.set(0.6)  # Default 60%
        self.wallet_progress.pack(fill="x", pady=5)

        progress_labels = ctk.CTkFrame(deploy_frame, fg_color="transparent")
        progress_labels.pack(fill="x")

        self.lbl_deployed = ctk.CTkLabel(progress_labels, text="₹30,000 (60%)", font=("Roboto", 10, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_deployed.pack(side="left")

        self.lbl_available_wallet = ctk.CTkLabel(progress_labels, text="₹20,000 (40%) Available", font=("Roboto", 10), text_color="#888")
        self.lbl_available_wallet.pack(side="right")

        # Per-Bot Allocation (Placeholder for future)
        bots_frame = ctk.CTkFrame(wallet_content, fg_color="#0A0A0A", corner_radius=8)
        bots_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(bots_frame, text="Per-Bot Breakdown:", font=("Roboto", 9, "bold"), text_color="#666").pack(anchor="w", padx=8, pady=(5, 2))
        self.lbl_bot_breakdown = ctk.CTkLabel(bots_frame, text="• All Bots: ₹50,000 (Shared Pool)", font=("Roboto", 9), text_color="#888")
        self.lbl_bot_breakdown.pack(anchor="w", padx=8, pady=(0, 5))

        # --- ROW 1: PROFIT & SENTIMENT ---
        row1 = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        # 1. Total Profit (Big Graph Style)
        self.card_profit = TitanCard(row1, title="TOTAL PROFIT", width=500, height=220, border_color=COLOR_ACCENT)
        self.card_profit.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.lbl_pnl = ctk.CTkLabel(self.card_profit, text="₹0.00", font=("Roboto", 42, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_pnl.pack(anchor="w", padx=25, pady=(20, 0))
        
        # Placeholder Graph Line
        self.graph_canvas = ctk.CTkCanvas(self.card_profit, height=80, bg=COLOR_CARD, highlightthickness=0)
        self.graph_canvas.pack(fill="x", padx=2, pady=10, side="bottom")
        self.draw_mock_graph(self.graph_canvas, COLOR_SUCCESS) # Initial draw

        # Safety Box / Capital Usage Bar
        self.cap_frame = ctk.CTkFrame(self.card_profit, fg_color="transparent")
        self.cap_frame.place(relx=0.95, rely=0.1, anchor="ne")
        
        ctk.CTkLabel(self.cap_frame, text="SAFETY BOX USED", font=("Roboto", 10, "bold"), text_color="#AAA").pack(anchor="e")
        self.cap_bar = ctk.CTkProgressBar(self.cap_frame,width=120, height=8, progress_color=COLOR_ACCENT)
        self.cap_bar.set(0.1) # Mock 10%
        self.cap_bar.pack(anchor="e", pady=2)
        self.lbl_cap_usage = ctk.CTkLabel(self.cap_frame, text="₹15k / ₹50k", font=("Roboto", 10), text_color="#888")
        self.lbl_cap_usage.pack(anchor="e")

        # 2. Market Sentiment (Meter)
        self.card_sentiment = TitanCard(row1, title="MARKET SENTIMENT METER", width=400, height=220, border_color="#FF9800")
        self.card_sentiment.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # Meter Canvas
        self.meter_canvas = ctk.CTkCanvas(self.card_sentiment, height=100, bg=COLOR_CARD, highlightthickness=0)
        self.meter_canvas.pack(fill="x", pady=20)
        self.lbl_sentiment_val = ctk.CTkLabel(self.card_sentiment, text="50", font=("Roboto", 24, "bold"), text_color="white")
        self.lbl_sentiment_val.place(relx=0.5, rely=0.55, anchor="center") # Overlay number
        self.draw_meter(50) # Initial draw
        
        self.lbl_sentiment_reason = ctk.CTkLabel(self.card_sentiment, text="WHY? Low Volatility", text_color="#FF9800", font=("Roboto", 11))
        self.lbl_sentiment_reason.pack(pady=5)

        # --- ROW 2: ALERTS/TIPS & POSITIONS ---
        row2 = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        row2.pack(fill="both", expand=True, pady=10)
        
        # Left Column (Alerts + Knowledge)
        left_col = ctk.CTkFrame(row2, fg_color="transparent", width=350)
        left_col.pack(side="left", fill="y", padx=(0, 10))
        
        # Recent Alerts
        self.card_alerts = TitanCard(left_col, title="RECENT ALERTS", height=200)
        self.card_alerts.pack(fill="x", pady=(0, 10))
        self.alert_box = ctk.CTkTextbox(self.card_alerts, height=150, fg_color="transparent", font=("Roboto", 11), text_color="#CCC")
        self.alert_box.pack(fill="both", padx=10, pady=5)
        self.alert_box.insert("0.0", "⚠ System Initialized\n⚠ Connecting to Market Data...\n")
        
        # Knowledge Intelligence
        self.card_knowledge = TitanCard(left_col, title="KNOWLEDGE INTELLIGENCE", height=200, border_color=COLOR_ACCENT)
        self.card_knowledge.pack(fill="x", pady=(10, 0))
        
        # glowing bulb icon placeholder (text for now)
        ctk.CTkLabel(self.card_knowledge, text="💡", font=("Arial", 48)).pack(pady=10)
        self.lbl_tip = ctk.CTkLabel(self.card_knowledge, text="AI Tip: Market is choppy. Consider tightening stops.", wraplength=250, font=("Roboto", 12), text_color="#DDD")
        self.lbl_tip.pack(pady=10)

        # Right Column (Active Positions)
        self.card_positions = TitanCard(row2, title="ACTIVE POSITIONS", border_color=COLOR_ACCENT)
        self.card_positions.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        self.build_positions_table(self.card_positions)

        # --- ROW 3: CONTROLS ---
        row3 = ctk.CTkFrame(self.view_dashboard, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        # Control Panel Wrapper
        self.card_controls = TitanCard(row3, title="ENGINE COMMANDER", height=100, border_color=COLOR_ACCENT)
        self.card_controls.pack(fill="both", expand=True)

        inner_controls = ctk.CTkFrame(self.card_controls, fg_color="transparent")
        inner_controls.pack(fill="both", expand=True, padx=20, pady=15)
        
        # 1. Toggle Button (Start/Stop)
        self.btn_start = ctk.CTkButton(inner_controls, text="▶ START ENGINE", command=self.toggle_bot, 
                                     fg_color=COLOR_SUCCESS, hover_color="#00C853", height=50, 
                                     font=("Roboto", 16, "bold"), text_color="black")
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        # 2. Panic Button
        self.btn_panic = ctk.CTkButton(inner_controls, text="🚨 PANIC STOP", command=self.emergency_exit, 
                                     fg_color=COLOR_DANGER, hover_color="#B71C1C", height=50, width=200,
                                     font=("Roboto", 14, "bold"))
        self.btn_panic.pack(side="right")
        
        # Log Area (Mini) - Moved to right side of row3 outside card
        # Or maybe putting it below? User liked "Logs view".
        # Let's keep mini-log minimal or remove if redundant with LOGS tab.
        # Keeping it hidden for now as we have a dedicated LOGS tab.

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
            ctk.CTkLabel(card, text="Exposure: ₹0", font=("Roboto", 11), text_color="#AAA").pack(anchor="w", padx=15, pady=(5,0))
            ctk.CTkLabel(card, text="PnL: 0.0%", font=("Roboto", 14, "bold"), text_color="white").pack(anchor="w", padx=15, pady=2)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=10)
            ctk.CTkSwitch(btn_frame, text="Trade", width=40).pack(side="right")
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
            
            ctk.CTkLabel(card, text=desc, font=("Roboto", 12), text_color="#CCC", wraplength=300, justify="left").pack(anchor="w", padx=15, pady=5)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkSwitch(btn_frame, text="Active").pack(side="right")
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
        
        ctk.CTkLabel(scroll, text="🧠 KNOWLEDGE INTELLIGENCE", font=("Roboto", 24, "bold"), text_color="white").pack(anchor="w", pady=(0, 20))
        
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
        
        ctk.CTkLabel(tip_card, text=daily_tip['content'], font=("Roboto", 14), text_color="#EEE", 
                     wraplength=800, justify="left").pack(padx=20, pady=20, anchor="w")
                     
        # Library
        ctk.CTkLabel(scroll, text="TRADING LIBRARY", font=("Roboto", 18, "bold"), text_color="#AAA").pack(anchor="w", pady=(20, 10))
        
        for tip in tips:
            if tip == daily_tip: continue
            
            card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, corner_radius=6, border_width=1, border_color="#333")
            card.pack(fill="x", pady=5)
            
            ctk.CTkLabel(card, text=tip['title'], font=("Roboto", 12, "bold"), text_color="white").pack(anchor="w", padx=10, pady=(10,0))
            ctk.CTkLabel(card, text=tip['content'], font=("Roboto", 11), text_color="#888", wraplength=800, justify="left").pack(anchor="w", padx=10, pady=(0,10))

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
        
        ctk.CTkLabel(header, text="🚀 START HERE: Quick Setup Guide", font=("Roboto", 24, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
        ctk.CTkLabel(header, text="Follow these 4 simple steps to get your bot running!", font=("Roboto", 14), text_color="#AAA").pack()
        
        # Steps Container
        steps_frame = ctk.CTkScrollableFrame(self.view_start, fg_color="transparent")
        steps_frame.pack(fill="both", expand=True, padx=40)
        
        # --- Step 1: Broker ---
        s1 = TitanCard(steps_frame, title="STEP 1: CONNECT BROKER", height=150, border_color="#3498DB")
        s1.pack(fill="x", pady=10)
        
        row1 = ctk.CTkFrame(s1, fg_color="transparent")
        row1.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row1, text="1️⃣", font=("Arial", 30)).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row1, text="Configure API Credentials", font=("Roboto", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(row1, text="Go to Settings > Broker tab. Enter your API Key, Secret, and User ID.\nEnable 'Auto-Login' by adding your TOTP secret (recommended).",
                     font=("Arial", 12), text_color="#CCC", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row1, text="Go to Broker Settings", width=150, fg_color="#3498DB", 
                      command=lambda: self.nav_bar.set("SETTINGS") or self.show_view("SETTINGS")).pack(side="right")

        # --- Step 2: Capital ---
        s2 = TitanCard(steps_frame, title="STEP 2: ALLOCATE FUNDS", height=150, border_color="#2ECC71")
        s2.pack(fill="x", pady=10)
        
        row2 = ctk.CTkFrame(s2, fg_color="transparent")
        row2.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row2, text="2️⃣", font=("Arial", 30)).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row2, text="Set Capital Limits (Safety Box)", font=("Roboto", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(row2, text="Go to Settings > Capital tab.\nSet 'Allocated Capital' (e.g., ₹50,000). This is the maximum the bot can touch.\nYour main broker balance remains safe.",
                     font=("Arial", 12), text_color="#CCC", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row2, text="Go to Capital Settings", width=150, fg_color="#2ECC71", 
                      command=lambda: self.nav_bar.set("SETTINGS") or self.show_view("SETTINGS")).pack(side="right")

        # --- Step 3: Select Stocks ---
        s3 = TitanCard(steps_frame, title="STEP 3: CHOOSE STOCKS", height=150, border_color="#9B59B6")
        s3.pack(fill="x", pady=10)
        
        row3 = ctk.CTkFrame(s3, fg_color="transparent")
        row3.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row3, text="3️⃣", font=("Arial", 30)).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row3, text="Select Strategy & Stocks", font=("Roboto", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(row3, text="Review 'Strategies' tab to see active logic (e.g., RSI).\nGo to Settings > Stocks to add/remove symbols you want to trade.",
                     font=("Arial", 12), text_color="#CCC", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row3, text="Go to Strategies", width=150, fg_color="#9B59B6", 
                      command=lambda: self.nav_bar.set("STRATEGIES") or self.show_view("STRATEGIES")).pack(side="right")

        # --- Step 4: Launch ---
        s4 = TitanCard(steps_frame, title="STEP 4: LAUNCH", height=150, border_color=COLOR_ACCENT)
        s4.pack(fill="x", pady=10)
        
        row4 = ctk.CTkFrame(s4, fg_color="transparent")
        row4.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(row4, text="🚀", font=("Arial", 30)).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row4, text="Start the Engine", font=("Roboto", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(row4, text="Go to DASHBOARD tab.\nClick 'START ENGINE' (Green Button).\nMonitor the 'Market Regime' and 'Logs' for activity.",
                     font=("Arial", 12), text_color="#CCC", justify="left").pack(anchor="w", pady=5)
        ctk.CTkButton(row4, text="Go to Dashboard", width=150, fg_color=COLOR_ACCENT, text_color="black", 
                      font=("Arial", 12, "bold"), command=lambda: self.nav_bar.set("DASHBOARD") or self.show_view("DASHBOARD")).pack(side="right")

    def build_positions_table(self, parent):
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
            font=("Roboto", 10),
            height=25,
            fg_color="#222",
            selected_color=COLOR_ACCENT,
            unselected_color="#111"
        )
        filter_segment.pack(side="left")

        # Summary Stats
        self.lbl_position_stats = ctk.CTkLabel(
            filter_frame,
            text="Positions: 0 • Bot: 0 • Manual: 0",
            font=("Roboto", 9),
            text_color="#666"
        )
        self.lbl_position_stats.pack(side="right", padx=10)

        # Table Frame
        table_frame = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=2, pady=5)

        cols = ("Symbol", "Source", "Qty", "Entry", "LTP", "P&L", "P&L %")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#111", foreground="white", fieldbackground="#111", rowheight=35, borderwidth=0, font=("Roboto", 10))
        style.configure("Treeview.Heading", background="#1A1A1A", foreground="#888", font=("Roboto", 9, "bold"), borderwidth=0)

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

    # --- DRAWING UTILS ---
    def draw_mock_graph(self, canvas, color):
        """Draws a random-looking line graph"""
        w = 500
        h = 80
        coords = [0, h]
        import random
        prev_y = h
        for x in range(0, w, 10):
            y = prev_y + random.randint(-15, 15)
            y = max(10, min(h-10, y))
            coords.extend([x, y])
            prev_y = y
        canvas.create_line(coords, fill=color, width=2, smooth=True)

    def draw_meter(self, value):
        """Draws a semi-circle meter"""
        self.meter_canvas.delete("all")
        # Draw arc background
        self.meter_canvas.create_arc(50, 20, 350, 320, start=0, extent=180, outline="#333", width=15, style="arc")
        # Draw value arc (inverted logic for Tkinter arcs)
        # 0 is 3 o'clock. 180 is 9 o'clock.
        # We want 0-100 mapped to 180-0 degrees.
        angle = 180 - (value / 100 * 180)
        
        # Color based on value
        color = COLOR_DANGER if value < 40 else (COLOR_SUCCESS if value > 60 else COLOR_WARN)
        
        self.meter_canvas.create_arc(50, 20, 350, 320, start=180, extent=-(180-angle), outline=color, width=15, style="arc")

    # --- LOGIC ---
    def toggle_bot(self):
        if not self.running: self.start_bot()
        else: self.stop_bot()

    def start_bot(self):
        self.running = True
        self.stop_update_flag.clear()
        self.btn_start.configure(text="🛑 STOP ENGINE", fg_color=COLOR_DANGER, hover_color="#D50000")
        self.write_log("🚀 ENGINE STARTED. Waiting for data...\n")
        threading.Thread(target=self.run_cycle_wrapper, daemon=True).start()
        threading.Thread(target=self.rsi_worker, daemon=True).start()

    def stop_bot(self):
        if messagebox.askyesno("STOP", "Stop Trading Engine?"):
            self.running = False
            self.stop_update_flag.set()
            self.btn_start.configure(text="▶ START ENGINE", fg_color=COLOR_SUCCESS, hover_color="#00C853")
            self.write_log("🛑 Engine Stopped.\n")

    def run_cycle_wrapper(self):
        while not self.stop_update_flag.is_set():
            try:
                if not self.running: break
                run_cycle()
                positions = safe_get_live_positions_merged()
                self.data_queue.put(("positions", positions))
            except Exception as e:
                self.write_log(f"Cycle Error: {e}\n")
            time.sleep(15)

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
            conf = config_dict.get((symbol, exchange), {})
            interval = tf_map.get(conf.get("Timeframe", "15T"), "15m")
            md, _ = fetch_market_data(symbol, exchange) # Now simulates if needed
            ltp = md.get("last_price") if md else None
            _, rsi_val, _ = calculate_intraday_rsi_tv(ticker=symbol, period=14, interval=interval, live_price=ltp, exchange=exchange)
            if rsi_val: self.data_queue.put(("rsi", (symbol, rsi_val)))
         except: pass

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
                elif dtype == "rsi": pass # Update rsi list if we had one
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
        self.draw_meter(data['score'])
        self.lbl_sentiment_val.configure(text=str(int(data['score'])))
        self.lbl_sentiment_reason.configure(text=f"WHY? {data['details']}")

    def refresh_balance(self):
        """Fetch real-time balance from broker API"""
        try:
            from kickstart import fetch_funds, ALLOCATED_CAPITAL

            # Show loading state
            self.btn_refresh_balance.configure(text="⏳", state="disabled")

            # Fetch balance in background thread to avoid UI freeze
            def fetch_and_update():
                try:
                    available_cash = fetch_funds()  # Real-time API call

                    # Get allocated capital from settings
                    allocated = float(ALLOCATED_CAPITAL) if ALLOCATED_CAPITAL else 50000.0

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
                finally:
                    self.root.after(0, lambda: self.btn_refresh_balance.configure(text="🔄", state="normal"))

            # Run in background
            threading.Thread(target=fetch_and_update, daemon=True).start()

        except Exception as e:
            self.write_log(f"❌ Balance refresh failed: {e}\n")
            self.btn_refresh_balance.configure(text="🔄", state="normal")

    def update_balance_display(self, total, available, allocated, in_positions):
        """Update Account Balance Card with new data"""
        try:
            # Update labels
            self.lbl_total_balance.configure(text=f"₹{total:,.2f}")
            self.lbl_available_cash.configure(text=f"₹{available:,.2f}")
            self.lbl_allocated.configure(text=f"₹{allocated:,.2f}")
            self.lbl_in_positions.configure(text=f"₹{in_positions:,.2f}")

            # Update timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.lbl_balance_timestamp.configure(text=f"Updated: {now}")

            # Also update bot wallet
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

    def write_log(self, text):
        """Redirect print/logs to UI Console and Alert Box"""
        if not text.strip(): return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"{timestamp} | {text}"
        
        # 1. Technical Log (Bottom) - Show Everything
        try:
            self.log_area.configure(state="normal")
            self.log_area.insert("end", formatted + "\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")
        except: pass
        
        # 2. Recent Alerts (Top Left) - FILTERED
        # Only show High-Level Events: Trades, Signals, System Changes
        # Filter out: "ERROR", "Failed", "Exception", "delisted" (unless critical)
        should_alert = False
        is_error = any(x in text for x in ["ERROR", "Exception", "Failed", "Expecting value", "delisted", "No price data"])
        
        if any(x in text for x in ["✅", "🚨", "BUY", "SELL", "Order", "Triggered", "System", "Engine"]):
             should_alert = True
        elif "⚠" in text and not is_error:
             # Show warnings like "Circuit Breaker" or "High Volatility", but hide API spam
             should_alert = True
             
        if should_alert:
            try:
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

