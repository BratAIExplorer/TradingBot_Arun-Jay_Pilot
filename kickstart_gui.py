import threading
import queue
import customtkinter as ctk
import os
import sys
import atexit
from pathlib import Path

# ---------------- SINGLE INSTANCE LOCK ----------------
# Prevent multiple instances to avoid duplicate trades and database conflicts
LOCK_FILE = "arun_bot.lock"

def cleanup_lock():
    """Remove lock file on exit"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

def check_single_instance():
    """Ensure only one instance of the bot is running"""
    if os.path.exists(LOCK_FILE):
        try:
            # Check if the lock file is stale (process crashed without cleanup)
            import time
            lock_age = time.time() - os.path.getmtime(LOCK_FILE)
            
            # If lock is older than 5 minutes, assume stale and remove
            if lock_age > 300:
                print("⚠️ Removing stale lock file...")
                os.remove(LOCK_FILE)
            else:
                # Active lock - another instance is running
                print("=" * 60)
                print("⚠️  ARUN Bot is already running!")
                print("=" * 60)
                print()
                print("Another instance of the bot is currently active.")
                print("Running multiple instances can cause:")
                print("  • Duplicate trades (buying/selling the same stock twice)")
                print("  • Database corruption")
                print("  • API rate limit issues")
                print()
                print("Please close the existing instance first, or check Task Manager")
                print("if you don't see it running (it might be minimized).")
                print()
                input("Press Enter to exit...")
                sys.exit(1)
        except Exception as e:
            print(f"Warning: Could not check lock file: {e}")
    
    # Create lock file
    try:
        with open(LOCK_FILE, 'w') as f:
            import time
            f.write(f"ARUN Bot Instance\nStarted: {time.ctime()}\nPID: {os.getpid()}")
        atexit.register(cleanup_lock)
    except Exception as e:
        print(f"Warning: Could not create lock file: {e}")

# Check for single instance FIRST (before any GUI or heavy imports)
check_single_instance()

#---------------- MANDATORY DISCLAIMER ----------------
# Show legal disclaimer EVERY time the GUI launches
try:
    from disclaimer_gui import DisclaimerGUI
    disclaimer_accepted = False
    
    def on_disclaimer_accept():
        global disclaimer_accepted
        disclaimer_accepted = True
    
    print("⚠️ Showing mandatory disclaimer...")
    DisclaimerGUI(on_disclaimer_accept)
    
    if not disclaimer_accepted:
        print("Disclaimer declined. Exiting.")
        cleanup_lock()  # Remove lock if user declines
        sys.exit(0)
        
except Exception as e:
    print(f"⚠️ Error showing disclaimer: {e}")
    # Continue anyway - don't block on disclaimer errors

# ---------------- INSTALLER CHECK ----------------
# If settings.json is missing, this is likely a first run.
# Launch the Setup Wizard automatically.
if not os.path.exists("settings.json") and not os.path.exists("settings_default.json"): 
    # Logic: If default exists, user might have just built it but not configured.
    # Actually, we rely on settings.json being the active config.
    try:
        import setup_wizard
        print("ℹ️ Configuration missing. Launching Setup Wizard...")
        app = setup_wizard.SetupWizard()
        app.mainloop()
        
        # Check again if settings were created
        if not os.path.exists("settings.json"):
            print("⚠️ Setup cancelled. Exiting.")
            sys.exit(0)
    except ImportError:
        print("⚠️ setup_wizard.py not found. Continuing with risky default...")
    except Exception as e:
        print(f"⚠️ Error launching Setup Wizard: {e}")

from tkinter import END, ttk
from kickstart import run_cycle, fetch_market_data, config_dict, SYMBOLS_TO_TRACK, calculate_intraday_rsi_tv, is_system_online, safe_get_positions, safe_get_live_positions_merged
from knowledge_center import TOOLTIPS, STRATEGY_GUIDES, get_strategy_guide
from tkinter import messagebox
import time
from concurrent.futures import ThreadPoolExecutor

# Database integration (Phase 0A)
try:
    from database.trades_db import TradesDatabase
    db = TradesDatabase()
    DATABASE_AVAILABLE = True
except ImportError:
    db = None
    DATABASE_AVAILABLE = False
    print("⚠️ Database not available, trade history disabled")

class StartupTour:
    def __init__(self, parent_root, on_close_callback=None):
        self.root = ctk.CTkToplevel(parent_root)
        self.root.title("👋 Welcome to ARUN")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        # Make it modal
        self.root.transient(parent_root)
        self.root.grab_set()
        
        self.on_close_callback = on_close_callback
        self.steps = [
            ("👋 Welcome!", "Welcome to the ARUN Trading Bot.\n\nThis tool is designed to help you automate your trading strategies safely and efficiently.\n\nClick 'Next' to take a quick tour of the features."),
            ("📊 Dashboard", "The Dashboard is your main Command Center.\n\n• Live Positions: See your active trades and P&L.\n• Market Status: Check if the market is Open/Closed.\n• RSI Monitor: Watch momentum signals in real-time."),
            ("📖 Orders", "The Orders Tab is your Ledger.\n\nIt tracks every single order sent to the broker.\n• Open Orders: Waiting to be filled.\n• Executed: Trades that happened.\n• Use 'Resync' if you trade on your phone."),
            ("🧪 Simulation", "The Simulation Tab (Backtester) is your Lab.\n\n• Test ideas without risking a rupee.\n• Run strategies on past data (e.g., 'What if I traded Reliance last year?').\n• Always backtest before going live!"),
            ("⚙️ Safety & Settings", "Safety First!\n\n• Capital Limits: Set max loss per day.\n• Panic Button: One-click exit for emergencies.\n• Paper Trading: Enabled by default. Switching to REAL money requires conscious effort in Settings."),
            ("🚀 Ready?", "You are all set!\n\nWe highly recommend reading the 'Knowledge Center' guides for detailed strategy explanations.\n\nHappy Trading!")
        ]
        self.current_step = 0
        
        # UI Elements
        self.title_label = ctk.CTkLabel(self.root, text="", font=("Arial", 24, "bold"))
        self.title_label.pack(pady=(30, 20))
        
        self.desc_label = ctk.CTkLabel(self.root, text="", font=("Arial", 16), wraplength=500, justify="left")
        self.desc_label.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Navigation
        self.btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.btn_frame.pack(pady=30, fill="x", padx=40)
        
        self.next_btn = ctk.CTkButton(self.btn_frame, text="Next ▶", command=self.next_step, width=120)
        self.next_btn.pack(side="right")
        
        self.skip_btn = ctk.CTkButton(self.btn_frame, text="Skip Tour", command=self.close_tour, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.skip_btn.pack(side="left")
        
        # Don't show again checkbox
        self.dont_show_var = ctk.BooleanVar(value=True)
        self.dont_show_checkbox = ctk.CTkCheckBox(self.root, text="Don't show this again", variable=self.dont_show_var)
        self.dont_show_checkbox.pack(pady=(0, 20))
        
        self.update_slide()

    def update_slide(self):
        title, text = self.steps[self.current_step]
        self.title_label.configure(text=title)
        self.desc_label.configure(text=text)
        
        if self.current_step == len(self.steps) - 1:
            self.next_btn.configure(text="Finish 🏁")
        else:
            self.next_btn.configure(text="Next ▶")

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_slide()
        else:
            self.close_tour()

    def close_tour(self):
        if self.dont_show_var.get():
            if self.on_close_callback:
                self.on_close_callback()
        self.root.destroy()

class TradingGUI:
    def __init__(self):
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Main window
        self.root = ctk.CTk()
        self.root.title("📈 ARUN")
        print("✅ STARTING GUI V3.0.1 (Emergency Fixes)")
        self.root.geometry("1200x750")
        self.root.configure(cursor="arrow")
        
        # Initialize Settings Manager (needed for capital allocation, etc.)
        from settings_manager import SettingsManager
        self.settings_mgr = SettingsManager()
        
        # CHECK FOR FIRST RUN TOUR
        self.root.after(1000, self.check_first_run)

        # Configure Treeview style to disable selection highlight
        style = ttk.Style()
        style.configure(
            "NoHighlight.Treeview",
            background=style.lookup("Treeview", "background"),
            foreground=style.lookup("Treeview", "foreground"),
            fieldbackground=style.lookup("Treeview", "fieldbackground")
        )
        style.map(
            "NoHighlight.Treeview",
            background=[("selected", style.lookup("Treeview", "background"))],
            foreground=[("selected", style.lookup("Treeview", "foreground"))]
        )

        # ---------------- Status Bar (Phase 1) ----------------
        self.status_bar_frame = ctk.CTkFrame(self.root, height=30, fg_color="#1E1E1E")
        self.status_bar_frame.pack(fill="x", padx=0, pady=(0, 5))
        
        # API Status
        self.api_status_label = ctk.CTkLabel(self.status_bar_frame, text="API: ●", font=("Arial", 12, "bold"), text_color="gray")
        self.api_status_label.pack(side="left", padx=(10, 5))
        
        self.latency_label = ctk.CTkLabel(self.status_bar_frame, text="-- ms", font=("Arial", 12), text_color="gray")
        self.latency_label.pack(side="left", padx=(0, 15))
        
        # Market Status
        self.market_status_label = ctk.CTkLabel(self.status_bar_frame, text="MARKET: --", font=("Arial", 12, "bold"), text_color="gray")
        self.market_status_label.pack(side="right", padx=10)

        # ---------------- Performance Summary (Phase 0A) ----------------
        if DATABASE_AVAILABLE:
            summary_frame = ctk.CTkFrame(self.root, fg_color="transparent")
            summary_frame.pack(pady=10, fill="x", padx=10)
            
            # Configure grid columns to expand equally
            for i in range(5):
                summary_frame.grid_columnconfigure(i, weight=1)
                
            # Get performance data
            perf = db.get_performance_summary()
            
            # Funds Card (Allocated vs Real)
            portfolio_card = ctk.CTkFrame(summary_frame, fg_color="#1E1E1E", corner_radius=10)
            portfolio_card.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
            ctk.CTkLabel(portfolio_card, text="💼 Funds (Allocated / Real)", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10, 0))
            
            # Allocated
            self.allocated_label = ctk.CTkLabel(portfolio_card, text="Alloc: --", font=("Arial", 14, "bold"), text_color="#3498DB")
            self.allocated_label.pack(pady=(2, 0))
            
            # Real
            self.real_funds_label = ctk.CTkLabel(portfolio_card, text="Real: --", font=("Arial", 14, "bold"), text_color="#E67E22")
            self.real_funds_label.pack(pady=(0, 10))
            
            # Total Profit Card
            profit_card = ctk.CTkFrame(summary_frame, fg_color="#1E1E1E", corner_radius=10)
            profit_card.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
            ctk.CTkLabel(profit_card, text="💰 Total Profit", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10, 0))
            total_profit = perf.get('total_net_pnl', 0)
            profit_color = "#2ECC71" if total_profit >= 0 else "#E74C3C"
            self.total_profit_label = ctk.CTkLabel(
                profit_card,
                text=f"₹{total_profit:,.0f}",
                font=("Arial", 22, "bold"),
                text_color=profit_color
            )
            self.total_profit_label.pack(pady=(5, 15))
            
            # Today's P&L Card
            today_card = ctk.CTkFrame(summary_frame, fg_color="#1E1E1E", corner_radius=10)
            today_card.grid(row=0, column=2, padx=10, pady=5, sticky="nsew")
            ctk.CTkLabel(today_card, text="📅 Today's P&L", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10, 0))
            today_pnl = perf.get('total_net_pnl', 0) # Simplified
            pnl_color = "#2ECC71" if today_pnl >= 0 else "#E74C3C"
            self.today_pnl_label = ctk.CTkLabel(
                today_card,
                text=f"₹{today_pnl:,.0f}",
                font=("Arial", 22, "bold"),
                text_color=pnl_color
            )
            self.today_pnl_label.pack(pady=(5, 15))
            
            # Total Trades Card
            trades_card = ctk.CTkFrame(summary_frame, fg_color="#1E1E1E", corner_radius=10)
            trades_card.grid(row=0, column=3, padx=10, pady=5, sticky="nsew")
            ctk.CTkLabel(trades_card, text="📊 Total Trades", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10, 0))
            self.total_trades_label = ctk.CTkLabel(
                trades_card,
                text=str(perf.get('total_trades', 0)),
                font=("Arial", 22, "bold")
            )
            self.total_trades_label.pack(pady=(5, 15))
            
            # Win Rate Card
            winrate_card = ctk.CTkFrame(summary_frame, fg_color="#1E1E1E", corner_radius=10)
            winrate_card.grid(row=0, column=4, padx=10, pady=5, sticky="nsew")
            ctk.CTkLabel(winrate_card, text="🏆 Win Rate", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10, 0))
            win_rate = perf.get('win_rate', 0)
            winrate_color = "#2ECC71" if win_rate >= 50 else "#F39C12"
            self.win_rate_label = ctk.CTkLabel(
                winrate_card,
                text=f"{win_rate:.1f}%",
                font=("Arial", 22, "bold"),
                text_color=winrate_color
            )
            self.win_rate_label.pack(pady=(5, 15))

        # ---------------- Buttons ----------------
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(button_frame, text="▶ Start Bot", command=self.start_bot, cursor="hand2")
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ctk.CTkButton(button_frame, text="⏸️ Pause Bot", command=self.stop_bot, state="disabled", cursor="hand2", fg_color="#E74C3C", hover_color="#C0392B")
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Panic Button (Phase 4)
        self.panic_btn = ctk.CTkButton(
            button_frame,
            text="🚨 PANIC (EXIT ALL)",
            command=self.emergency_exit,
            fg_color="#8B0000",
            hover_color="#FF0000",
            text_color="white",
            width=140
        )
        self.panic_btn.grid(row=0, column=4, padx=(20, 5))
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            button_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            cursor="hand2",
            fg_color="#2C3E50",
            hover_color="#34495E"
        )
        self.settings_btn.grid(row=0, column=2, padx=5)

        # Knowledge Center button
        self.help_btn = ctk.CTkButton(
            button_frame,
            text="📖 Knowledge Center",
            command=self.show_knowledge_center,
            cursor="hand2",
            fg_color="#3498DB",
            hover_color="#2980B9"
        )
        self.help_btn.grid(row=0, column=3, padx=5)

        # ---------------- Main Tabview ----------------
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.dashboard_tab = self.tabview.add("📊 Dashboard")
        self.orders_tab = self.tabview.add("📖 Orders")
        self.simulation_tab = self.tabview.add("🧪 Simulation")
        self.logs_tab = self.tabview.add("📜 Technical Logs")

        # ---------------- Log Area (In Logs Tab) ----------------
        self.log_area = ctk.CTkTextbox(self.logs_tab, cursor="xterm")
        self.log_area.pack(padx=10, pady=10, fill="both", expand=True)
        
        # ---------------- Orders Tab (Phase 2) ----------------
        orders_container = ctk.CTkFrame(self.orders_tab, fg_color="transparent")
        orders_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Controls (Sync Button)
        orders_ctrl_frame = ctk.CTkFrame(orders_container, fg_color="transparent")
        orders_ctrl_frame.pack(fill="x", pady=(0, 10))
        
        self.sync_btn = ctk.CTkButton(
            orders_ctrl_frame, 
            text="🔄 Resync with Broker", 
            fg_color="#F39C12", 
            hover_color="#D35400",
            command=self.resync_broker_data
        )
        self.sync_btn.pack(side="right")
        
        ctk.CTkLabel(orders_ctrl_frame, text="📖 Order Book (Open Orders)", font=("Arial", 16, "bold")).pack(side="left")

        # Orders Table
        orders_table_frame = ctk.CTkFrame(orders_container)
        orders_table_frame.pack(fill="both", expand=True)
        
        self.orders_table = ttk.Treeview(
            orders_table_frame,
            columns=("Time", "Symbol", "Type", "Side", "Qty", "Price", "Status"),
            show="headings",
            style="NoHighlight.Treeview"
        )
        for col in ("Time", "Symbol", "Type", "Side", "Qty", "Price", "Status"):
            self.orders_table.heading(col, text=col)
            width = 100 if col not in ["Time", "Symbol"] else 120
            self.orders_table.column(col, width=width, anchor="center")
            
        self.orders_table.pack(fill="both", expand=True)

        # Redirect stdout/stderr
        import sys
        sys.stdout.write = self.write_log
        sys.stderr.write = self.write_log

        # ---------------- Dashboard (In Dashboard Tab) ----------------
        dashboard_container = ctk.CTkScrollableFrame(self.dashboard_tab, fg_color="transparent")
        dashboard_container.pack(fill="both", expand=True)

        # Live Positions Table
        pos_header_frame = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        pos_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.positions_label = ctk.CTkLabel(pos_header_frame, text="📊 Live Positions", font=("Arial", 16, "bold"))
        self.positions_label.pack(side="left")

        pos_frame = ctk.CTkFrame(dashboard_container)
        pos_frame.pack(fill="x", padx=10, pady=5)

        self.positions_table = ttk.Treeview(
            pos_frame,
            columns=("Symbol", "Mode", "Qty", "Entry", "Last", "PnL"),
            show="headings",
            style="NoHighlight.Treeview"
        )
        for col in ("Symbol", "Mode", "Qty", "Entry", "Last", "PnL"):
            self.positions_table.heading(col, text=col, command=lambda c=col: self.sort_table(self.positions_table, c, False))
            self.positions_table.column(col, width=120, stretch=True, anchor="center")
        
        self.positions_table.grid(row=0, column=0, sticky="nsew")
        pos_frame.grid_rowconfigure(0, weight=1)
        pos_frame.grid_columnconfigure(0, weight=1)

        # Bind Right Click
        self.positions_table.bind("<Button-3>", self.show_position_context_menu)

        # Recent Trades Table (Phase 0A)
        if DATABASE_AVAILABLE:
            trades_header_frame = ctk.CTkFrame(dashboard_container, fg_color="transparent")
            trades_header_frame.pack(fill="x", padx=10, pady=(20, 5))
            
            self.trades_label = ctk.CTkLabel(trades_header_frame, text="📝 Recent Trades", font=("Arial", 16, "bold"))
            self.trades_label.pack(side="left")
            
            self.export_btn = ctk.CTkButton(
                trades_header_frame, 
                text="📥 Export to Excel", 
                width=120, 
                height=28,
                fg_color="#27AE60",
                hover_color="#1E8449",
                command=self.export_trades_to_excel
            )
            self.export_btn.pack(side="right")
            
            trades_frame = ctk.CTkFrame(dashboard_container)
            trades_frame.pack(fill="x", padx=10, pady=5)
            
            self.trades_table = ttk.Treeview(
                trades_frame,
                columns=("Time", "Symbol", "Action", "Qty", "Price", "Gross", "Fees", "Net"),
                show="headings",
                style="NoHighlight.Treeview",
                height=5
            )
            for col in ("Time", "Symbol", "Action", "Qty", "Price", "Gross", "Fees", "Net"):
                self.trades_table.heading(col, text=col)
                width = 80 if col in ["Time", "Symbol", "Action", "Qty"] else 100
                self.trades_table.column(col, width=width, stretch=True, anchor="center")
            
            self.trades_table.grid(row=0, column=0, sticky="nsew")
            trades_frame.grid_rowconfigure(0, weight=1)
            trades_frame.grid_columnconfigure(0, weight=1)
            
            # Load recent trades
            self.update_trades_table()

        # RSI Monitor Table
        rsi_header_frame = ctk.CTkFrame(dashboard_container, fg_color="transparent")
        rsi_header_frame.pack(fill="x", padx=10, pady=(20, 5))
        
        self.rsi_label = ctk.CTkLabel(rsi_header_frame, text="📈 RSI Monitor (Live)", font=("Arial", 16, "bold"))
        self.rsi_label.pack(side="left")

        rsi_frame = ctk.CTkFrame(dashboard_container)
        rsi_frame.pack(fill="x", padx=10, pady=5)

        self.rsi_table = ttk.Treeview(
            rsi_frame,
            columns=("Symbol", "RSI", "Buy", "Sell"),
            show="headings",
            style="NoHighlight.Treeview"
        )
        for col in ("Symbol", "RSI", "Buy", "Sell"):
            self.rsi_table.heading(col, text=col, command=lambda c=col: self.sort_table(self.rsi_table, c, False))
            self.rsi_table.column(col, width=120, stretch=True, anchor="center")
        
        self.rsi_table.grid(row=0, column=0, sticky="nsew")
        rsi_frame.grid_rowconfigure(0, weight=1)
        rsi_frame.grid_columnconfigure(0, weight=1)

        # ---------------- Disclaimer Footer ----------------
        disclaimer_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        disclaimer_frame.pack(side="bottom", fill="x", pady=(0, 5))
        
        disclaimer_text = (
            "⚠️ DISCLAIMER: ARUN is a technical tool for algorithmic scanning and execution. It does NOT provide investment advice. "
            "Users are solely responsible for their trading decisions, financial actions, and any resulting gains or losses. "
            "Past performance does not guarantee future results. Trade responsibly."
        )
        
        disclaimer_label = ctk.CTkLabel(
            disclaimer_frame, 
            text=disclaimer_text,
            font=("Arial", 10),
            text_color="#888888",
            wraplength=1100,
            justify="center"
        )
        disclaimer_label.pack(pady=5)

        # ---------------- Internals ----------------
        self.thread = None
        self.update_thread = None
        self.stop_update_flag = threading.Event()
        self.data_queue = queue.Queue(maxsize=100)  # Limit queue size to prevent overflow
        self.rsi_workers = {}
        self.last_update = {}  # Track last update time for each symbol

        # Initialize RSI table with symbol and exchange
        for symbol, exchange in SYMBOLS_TO_TRACK:
            self.rsi_table.insert("", END, values=(f"{symbol} ({exchange})", "N/A", "N/A", "N/A"), tags=("neutral",))

        # Build Simulation Tab (New MVP1 Feature)
        self.build_simulation_tab()
        
        # Start dashboard updates
        self.update_dashboard()

    def check_first_run(self):
        """Check if we need to show the Welcome Tour"""
        try:
            # Check settings
            prompts_shown = self.settings_mgr.get("app_settings.first_run_prompts_shown", False)
            if not prompts_shown:
                # Callback to save settings when tour finishes
                def save_tour_complete():
                    self.settings_mgr.set("app_settings.first_run_prompts_shown", True)
                    self.settings_mgr.save()
                    print("✅ Tour completed, marked as shown.")
                
                StartupTour(self.root, save_tour_complete)
        except Exception as e:
            print(f"⚠️ Error checking first run: {e}")

    def write_log(self, text):
        self.log_area.configure(state="normal")
        self.log_area.insert(END, text)
        self.log_area.see(END)
        lines = self.log_area.get("1.0", END).splitlines()
        if len(lines) > 1000:
            self.log_area.delete("1.0", f"{len(lines)-500}.0")
        self.log_area.configure(state="disabled")  # Disable after writing to prevent user edits

    def start_bot(self):
        if not is_system_online():
            self.write_log("🔴 Cannot start bot: System is offline\n")
            return
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.write_log("🟢 Starting bot\n")
        self.stop_update_flag.clear()
        
        # Reset Global Stop Flag
        import kickstart
        kickstart.STOP_REQUESTED = False
        
        self.thread = threading.Thread(target=self.run_cycle_thread, daemon=True)
        self.thread.start()
        self.update_thread = threading.Thread(target=self.update_data_in_background, daemon=True)
        self.update_thread.start()

        # Use thread pool for RSI calculations
        def rsi_batch_worker():
            tf_map = {"1T":"1m","3T":"3m","5T":"5m","10T":"10m","15T":"15m","30T":"30m","1H":"1h","1D":"1d"}
            with ThreadPoolExecutor(max_workers=4) as executor:
                while not self.stop_update_flag.is_set():
                    futures = []
                    for symbol, exchange in SYMBOLS_TO_TRACK:
                        futures.append(executor.submit(self.compute_rsi_for_symbol, symbol, exchange, tf_map))
                    for future in futures:
                        try:
                            future.result(timeout=10)
                        except Exception as e:
                            self.write_log(f"RSI worker error: {e}\n")
                    time.sleep(30)  # Batch process every 30 seconds

        self.rsi_batch_thread = threading.Thread(target=rsi_batch_worker, daemon=True)
        self.rsi_batch_thread.start()
        
    def compute_rsi_for_symbol(self, symbol, exchange, tf_map):
        try:
            now = time.time()
            last = self.last_update.get((symbol, exchange), 0)
            if now - last < 30:
                return
            conf = config_dict.get((symbol, exchange), {})
            buy_rsi = conf.get("Buy RSI", "N/A")
            sell_rsi = conf.get("Sell RSI", "N/A")
            tf = conf.get("Timeframe", "15T")
            interval = tf_map.get(tf, "15m")
            md, _ = fetch_market_data(symbol, exchange)
            ltp = md.get("last_price") if md else None
            ts_str, rsi_val, _ = calculate_intraday_rsi_tv(
                ticker=symbol, period=14, interval=interval, live_price=ltp, exchange=exchange
            )
            self.data_queue.put(("rsi", ((symbol, exchange), rsi_val, buy_rsi, sell_rsi, None)))
            self.last_update[(symbol, exchange)] = now
        except queue.Full:
            self.write_log(f"Queue full for {symbol} ({exchange}), skipping RSI update\n")
        except Exception as e:
            self.data_queue.put(("rsi", ((symbol, exchange), None, buy_rsi, sell_rsi, str(e))))
            self.last_update[(symbol, exchange)] = now

    def stop_bot(self):
        self.stop_update_flag.set()
        
        # Signal Global Stop
        import kickstart
        kickstart.STOP_REQUESTED = True
        
        self.write_log("\n⏹ Bot stopped by user\n")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def sort_table(self, table, col, reverse):
        try:
            data = [(table.set(k, col), k) for k in table.get_children("")]
            try:
                data.sort(key=lambda t: float(t[0]) if t[0] not in ("N/A", "Error", "") else float("-inf"), reverse=reverse)
            except ValueError:
                data.sort(key=lambda t: t[0], reverse=reverse)

            for index, (val, k) in enumerate(data):
                table.move(k, "", index)

            table.heading(col, command=lambda: self.sort_table(table, col, not reverse))
        except Exception as e:
            self.write_log(f"Error sorting {col}: {e}\n")

    def run_cycle_thread(self):
        while not self.stop_update_flag.is_set():
            run_cycle()
            time.sleep(15)  # Brief pause to prevent CPU overload

    def rsi_worker(self, symbol, exchange):
        tf_map = {"1T":"1m","3T":"3m","5T":"5m","10T":"10m","15T":"15m","30T":"30m","1H":"1h","1D":"1d"}
        while not self.stop_update_flag.is_set():
            try:
                now = time.time()
                last = self.last_update.get((symbol, exchange), 0)
                if now - last < 10:  # Throttle to every 10 seconds
                    time.sleep(1)
                    continue

                conf = config_dict.get((symbol, exchange), {})
                buy_rsi = conf.get("Buy RSI", "N/A")
                sell_rsi = conf.get("Sell RSI", "N/A")
                tf = conf.get("Timeframe", "15T")
                interval = tf_map.get(tf, "15m")
                md, _ = fetch_market_data(symbol, exchange)
                ltp = md.get("last_price") if md else None
                ts_str, rsi_val, _ = calculate_intraday_rsi_tv(
                    ticker=symbol, period=14, interval=interval, live_price=ltp, exchange=exchange
                )
                self.data_queue.put(("rsi", ((symbol, exchange), rsi_val, buy_rsi, sell_rsi, None)))
                self.last_update[(symbol, exchange)] = now
            except queue.Full:
                self.write_log(f"Queue full for {symbol} ({exchange}), skipping RSI update\n")
                time.sleep(1)
            except Exception as e:
                self.data_queue.put(("rsi", ((symbol, exchange), None, buy_rsi, sell_rsi, str(e))))
                self.last_update[(symbol, exchange)] = now
            time.sleep(1)  # Minimum pause to prevent tight loop

    def update_dashboard(self):
        try:
            processed = 0
            max_updates = 10  # Limit updates per cycle to prevent GUI freeze
            while processed < max_updates:
                try:
                    data_type, data = self.data_queue.get_nowait()
                    processed += 1
                    if data_type == "positions":
                        desired_iids = set()
                        def remove_placeholder():
                            if self.positions_table.exists("__empty__"):
                                self.positions_table.delete("__empty__")

                        if data:
                            for sym, pos in data.items():
                                if isinstance(sym, tuple):
                                    sym_str = f"{sym[0]} ({sym[1]})"
                                else:
                                    sym_str = str(sym)
                                iid = sym_str
                                desired_iids.add(iid)

                                qty = pos.get("qty", 0)
                                price = pos.get("price", 0.0)
                                last_price = pos.get("ltp", 0.0)
                                pnl = pos.get("pnl", 0.0)
                                is_paper = pos.get("is_paper", False)
                                mode_str = "PAPER 🧪" if is_paper else "REAL 💵"
                                tag = "profit" if pnl >= 0 else "loss"
                                if is_paper: tag = "paper"

                                if self.positions_table.exists(iid):
                                    self.positions_table.item(iid, values=(sym_str, mode_str, qty, price, last_price, pnl), tags=(tag,))
                                else:
                                    self.positions_table.insert("", "end", iid=iid, values=(sym_str, mode_str, qty, price, last_price, pnl), tags=(tag,))

                            remove_placeholder()
                            for iid in list(self.positions_table.get_children()):
                                if iid not in desired_iids:
                                    self.positions_table.delete(iid)
                        else:
                            for iid in list(self.positions_table.get_children()):
                                self.positions_table.delete(iid)
                            self.positions_table.insert("", "end", iid="__empty__", values=("No active positions", "-", "-", "-", "-"), tags=("neutral",))
                    elif data_type == "rsi":
                        sym, rsi_val, buy_rsi, sell_rsi, error = data
                        sym_str = f"{sym[0]} ({sym[1]})" if isinstance(sym, tuple) else sym
                        for row in self.rsi_table.get_children():
                            if self.rsi_table.set(row, "Symbol") == sym_str:
                                tag = "buy" if not error and rsi_val is not None and rsi_val <= float(buy_rsi) else "sell" if not error and rsi_val is not None and rsi_val >= float(sell_rsi) else "neutral"
                                rsi_display = f"{rsi_val:.2f}" if rsi_val is not None else f"Error: {error}"
                                self.rsi_table.item(row, values=(sym_str, rsi_display, buy_rsi, sell_rsi), tags=(tag,))
                                break
                except queue.Empty:
                    break
        except Exception as e:
            self.write_log(f"Dashboard update error: {e}\n")

        self.positions_table.tag_configure("profit", foreground="green")
        self.positions_table.tag_configure("loss", foreground="red")
        self.positions_table.tag_configure("paper", foreground="#3498DB") # Blue for paper trades
        self.positions_table.tag_configure("neutral", foreground="black")
        self.rsi_table.tag_configure("buy", foreground="black")
        self.rsi_table.tag_configure("sell", foreground="black")
        self.rsi_table.tag_configure("neutral", foreground="black")

        self.root.after(2000, self.update_dashboard)  # Update every 2 seconds

    def update_data_in_background(self):
        while not self.stop_update_flag.is_set():
            if not is_system_online():
                self.write_log("🔴 System offline, skipping data update\n")
                time.sleep(30)  # Increased to reduce load when offline
                continue

            try:
                positions = safe_get_live_positions_merged()
                try:
                    self.data_queue.put(("positions", positions), timeout=1)
                except queue.Full:
                    self.write_log("Queue full, skipping position update\n")
            except Exception as e:
                self.write_log(f"Background update error: {e}\n")
            time.sleep(30)  # Update every 30 seconds to reduce load

    def open_settings(self):
        """Open settings GUI"""
        try:
            # Singleton Check
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.root.winfo_exists():
                self.settings_window.root.lift()
                self.settings_window.root.focus_force()
                return

            from settings_gui import SettingsGUI
            # Pass main root to make it a dependent window (Toplevel)
            self.settings_window = SettingsGUI(self.root)
            # Note: We do NOT call .run() here because the main loop is already running
        except Exception as e:
            self.write_log(f"❌ Failed to open Settings: {e}\n")
    
    def update_trades_table(self):
        """Update recent trades table from database"""
        if not DATABASE_AVAILABLE or not hasattr(self, 'trades_table'):
            return
        
        try:
            # Clear existing
            for item in self.trades_table.get_children():
                self.trades_table.delete(item)
            
            # Get recent trades (last 10)
            recent_trades = db.get_recent_trades(limit=10)
            
            for trade in recent_trades:
                # Format time
                timestamp = trade.get('timestamp', '')[:16]  # YYYY-MM-DD HH:MM
                symbol = trade.get('symbol', '')
                action = trade.get('action', '')
                qty = trade.get('quantity', 0)
                price = f"₹{trade.get('price', 0):,.2f}"
                gross = f"₹{trade.get('gross_amount', 0):,.2f}"
                fees = f"₹{trade.get('total_fees', 0):.2f}"
                net = f"₹{trade.get('net_amount', 0):,.2f}"
                
                # Color code by action
                tag = 'buy' if action == 'BUY' else 'sell'
                self.trades_table.insert("", "end", values=(
                    timestamp, symbol, action, qty, price, gross, fees, net
                ), tags=(tag,))
            
            # Color coding
            self.trades_table.tag_configure('buy', foreground='green')
            self.trades_table.tag_configure('sell', foreground='red')
            
        except Exception as e:
            self.write_log(f"⚠️ Failed to update trades table: {e}\n")
    
    def update_performance_summary(self):
        """Update performance summary cards"""
        if not DATABASE_AVAILABLE:
            return
        
        try:
             # --- Update Status Bar (Phase 1) ---
            import kickstart
            if hasattr(self, 'api_status_label'):
                # Market Status
                mkt_status = kickstart.get_market_status_display()
                mkt_color = "#2ECC71" if "OPEN" in mkt_status and "PRE" not in mkt_status else "#95A5A6"
                if "CLOSED" in mkt_status: mkt_color = "#E74C3C"
                self.market_status_label.configure(text=f"MARKET: {mkt_status}", text_color=mkt_color)
                
                # Connectivity & Latency
                is_connected, latency = kickstart.check_connectivity_latency()
                conn_color = "#2ECC71" if is_connected else "#E74C3C"
                diff_text = "● Connected" if is_connected else "● Disconnected"
                self.api_status_label.configure(text=f"API: {diff_text}", text_color=conn_color)
                
                lat_color = "#2ECC71" if latency < 200 else ("#F39C12" if latency < 500 else "#E74C3C")
                self.latency_label.configure(text=f"{latency} ms", text_color=lat_color)

            perf = db.get_performance_summary()
            
            # Update orders table (Phase 2)
            self.update_orders_table()
            
            # Update labels
            # Update labels
            if hasattr(self, 'allocated_label') and hasattr(self, 'real_funds_label'):
                # Allocated
                alloc = self.settings_mgr.get("capital.total_capital", 0.0)
                self.allocated_label.configure(text=f"Alloc: ₹{alloc:,.0f}")
                
                # Real
                import kickstart
                real = kickstart.fetch_funds()
                real_color = "#E74C3C" if real < alloc else "#2ECC71"
                self.real_funds_label.configure(
                    text=f"Real: ₹{real:,.0f}",
                    text_color=real_color
                )
            
                # Update deprecated label if exists (backwards compatibility)
                if hasattr(self, 'portfolio_value_label'):
                     # We removed it, but in case of partial update or other refs
                     pass
            
                if hasattr(self, 'total_profit_label'):
                    self.total_profit_label.configure(
                        text=f"₹{perf.get('total_net_pnl', 0):,.0f}",
                        text_color="#2ECC71" if perf.get('total_net_pnl', 0) >= 0 else "#E74C3C"
                    )
                
                if hasattr(self, 'today_pnl_label'):
                    # In a real scenario, this would be daily P&L. 
                    # For now, we'll use a placeholder or the same net PnL if it's a fresh db
                    today_pnl = perf.get('total_net_pnl', 0)
                    pnl_color = "#2ECC71" if today_pnl >= 0 else "#E74C3C"
                    self.today_pnl_label.configure(
                        text=f"₹{today_pnl:,.0f}",
                        text_color=pnl_color
                    )
            
            if hasattr(self, 'total_trades_label'):
                self.total_trades_label.configure(text=str(perf.get('total_trades', 0)))
            
                if hasattr(self, 'win_rate_label'):
                    win_rate = perf.get('win_rate', 0)
                    winrate_color = "#2ECC71" if win_rate >= 50 else "#F39C12"
                    self.win_rate_label.configure(
                        text=f"{win_rate:.1f}%",
                        text_color=winrate_color
                    )
            
            # Update trades table
            self.update_trades_table()
            
        except Exception as e:
            self.write_log(f"⚠️ Failed to update performance: {e}\n")

    def update_orders_table(self):
        """Fetch and display open orders"""
        if not hasattr(self, 'orders_table'): return
        
        try:
            import kickstart
            orders = kickstart.fetch_orders()
            
            # Clear existing
            for item in self.orders_table.get_children():
                self.orders_table.delete(item)
                
            # Filter and Insert
            # Note: Adjust field names based on actual API response
            for order in orders:
                status = order.get("orderStatus", "UNKNOWN")
                if status not in ["COMPLETE", "REJECTED", "CANCELLED"]: # Show active only
                    # Parse timestamp (if available) or use current
                    ts = order.get("orderTime", "--")
                    sym = order.get("tradingSymbol", order.get("symbol", "??"))
                    typ = order.get("productType", "--")
                    side = order.get("transactionType", "--")
                    qty = f"{order.get('filledQuantity', 0)}/{order.get('quantity', 0)}"
                    price = order.get("price", 0)
                    
                    self.orders_table.insert("", "end", values=(ts, sym, typ, side, qty, price, status))
                    
        except Exception as e:
            # self.write_log(f"⚠️ Order fetch error: {e}\n") # Too noisy if frequent
            pass

    def resync_broker_data(self):
        """Sync missing trades from Broker to Local DB"""
        if not DATABASE_AVAILABLE:
            from tkinter import messagebox
            messagebox.showerror("Error", "Database not available.")
            return
            
        try:
            import kickstart
            from datetime import datetime
            from tkinter import messagebox
            
            orders = kickstart.fetch_orders()
            completed_orders = [o for o in orders if o.get("orderStatus") == "COMPLETE"]
            
            if not completed_orders:
                messagebox.showinfo("Sync", "No completed orders found in Broker today.")
                return
                
            # Get local trades
            local_trades = db.get_today_trades(is_paper=False)
            local_sigs = set()
            if not local_trades.empty:
                # Create simple signature: Symbol-Action-Qty
                for _, row in local_trades.iterrows():
                    sig = f"{row['symbol']}-{row['action']}-{row['quantity']}"
                    local_sigs.add(sig)
            
            synced_count = 0
            for order in completed_orders:
                sym = order.get("tradingSymbol", order.get("symbol", ""))
                side = order.get("transactionType", "BUY") # Default to BUY if missing
                qty = int(order.get("quantity", 0))
                price = float(order.get("averagePrice", order.get("price", 0)))
                
                sig = f"{sym}-{side}-{qty}"
                
                if sig not in local_sigs:
                    # Record Trade
                    gross = qty * price
                    # Approx fees (0.1% placeholder)
                    fees = gross * 0.001 
                    net = gross + fees if side == "BUY" else gross - fees
                    
                    db.insert_trade(
                        symbol=sym,
                        exchange=order.get("exchange", "NSE"),
                        action=side,
                        quantity=qty,
                        price=price,
                        gross_amount=gross,
                        total_fees=fees,
                        net_amount=net,
                        strategy="MANUAL/SYNC",
                        reason="Resync from Broker",
                        broker=kickstart.CLIENT_CODE
                    )
                    synced_count += 1
                    local_sigs.add(sig) # Prevent dup if broker sends dups
            
            messagebox.showinfo("Sync Complete", f"Synced {synced_count} missing trades from Broker.")
            self.update_trades_table() # Refresh UI
            self.update_performance_summary()
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Sync Failed", f"Error: {e}")

    def export_trades_to_excel(self):
        """Export all trades from database to Excel"""
        if not DATABASE_AVAILABLE:
            from tkinter import messagebox
            messagebox.showwarning("Database Not Available", "Trade database is not initialized.")
            return
            
        try:
            import pandas as pd
            import os
            from datetime import datetime
            from tkinter import filedialog, messagebox
            
            trades = db.get_recent_trades(limit=1000) # Get more for export
            if not trades:
                messagebox.showinfo("Export", "No trades found in the database to export.")
                return
                
            df = pd.DataFrame(trades)
            
            # Save dialog
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"ARUN_Trade_Report_{timestamp}.xlsx"
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_name,
                title="Export Trades to Excel"
            )
            
            if save_path:
                df.to_excel(save_path, index=False)
                messagebox.showinfo("Export Successful", f"Trade report saved to:\n{save_path}")
                self.write_log(f"📊 Exported {len(df)} trades to {save_path}\n")
                
        except Exception as e:
            self.write_log(f"❌ Export failed: {e}\n")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to export trades: {e}")

    def show_position_context_menu(self, event):
        """Show context menu for positions table"""
        item = self.positions_table.identify_row(event.y)
        if item:
            self.positions_table.selection_set(item)
            
            # Create menu
            import tkinter as tk
            menu = tk.Menu(self.root, tearoff=0, background='#2B2B2B', foreground='white', activebackground='#1E88E5')
            
            symbol_str = self.positions_table.item(item, "values")[0]
            
            menu.add_command(label=f"🔴 Close Position: {symbol_str}", command=lambda: self.close_position(item))
            menu.add_separator()
            menu.add_command(label="⚠️ Emergency Exit: Close ALL", command=self.emergency_exit, foreground='red')
            
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def close_position(self, item):
        """Manually close a specific position via market order"""
        from tkinter import messagebox
        values = self.positions_table.item(item, "values")
        if not values or values[0] == "No active positions":
            return
            
        symbol_full = values[0] # e.g. "RELIANCE (NSE)"
        qty = int(values[1])
        
        # Parse symbol and exchange
        try:
            import re
            match = re.search(r"(.+)\s\((.+)\)", symbol_full)
            if match:
                symbol = match.group(1)
                exchange = match.group(2)
            else:
                symbol = symbol_full
                exchange = "NSE"
        except:
            symbol = symbol_full
            exchange = "NSE"
            
        confirm = messagebox.askyesno(
            "Confirm Close", 
            f"Are you sure you want to CLOSE {symbol} ({exchange})?\n\nQuantity: {qty}\nType: Market SELL",
            icon='warning'
        )
        
        if confirm:
            self.write_log(f"🚀 Manual Intervention: Closing {symbol} ({qty} qty)...\n")
            from kickstart import safe_place_order_when_open
            
            # Need instrument_token if available, but for CNC Market Sell it might work with 0 placeholder if the API handles it
            # In kickstart.py, instrument_token is passed to place_order. 
            # We might need to fetch it or pass 0.
            
            success = safe_place_order_when_open(symbol, exchange, qty, "SELL", "0", use_amo=False)
            if success:
                messagebox.showinfo("Success", f"Sell order placed for {symbol}.")
            else:
                messagebox.showerror("Error", f"Failed to place sell order for {symbol}.")

    def emergency_exit(self):
        """Panic Mode: Cancel all orders and close all positions"""
        from tkinter import messagebox
        import kickstart
        
        confirm = messagebox.askyesno(
            "⚠️ EMERGENCY PANIC SWITCH", 
            f"CRITICAL: This will attempt to:\n1. CANCEL all pending orders.\n2. MARKET SELL all open positions.\n\nUse this only in emergencies!\n\nAre you sure?",
            icon='error'
        )
        
        if confirm:
            self.write_log("🚨 EMERGENCY PROTOCOL INITIATED...\n")
            
            # 1. Cancel Orders
            cancelled = kickstart.cancel_all_orders()
            self.write_log(f"🚨 Cancelled {cancelled} pending orders.\n")
            
            # 2. Square off Positions
            closed = kickstart.square_off_all_positions()
            self.write_log(f"🚨 Squared off {closed} active positions.\n")
            
            messagebox.showwarning("Panic Mode Executed", f"Report:\nCancelled Orders: {cancelled}\nClosed Positions: {closed}\n\nPlease verify manually in Broker App!")
            
            # Refresh all data
            self.update_dashboard()
            self.update_orders_table()

    def close_position_silent(self, item):
        """Helper to close position without individual confirmation"""
        values = self.positions_table.item(item, "values")
        symbol_full = values[0]
        qty = int(values[1])
        try:
            import re
            match = re.search(r"(.+)\s\((.+)\)", symbol_full)
            symbol = match.group(1) if match else symbol_full
            exchange = match.group(2) if match else "NSE"
        except:
            symbol = symbol_full
            exchange = "NSE"
            
        from kickstart import safe_place_order_when_open
        safe_place_order_when_open(symbol, exchange, qty, "SELL", "0", use_amo=False)

    def build_simulation_tab(self):
        """Simulation/Backtesting UI"""
        tab = self.simulation_tab
        
        ctk.CTkLabel(tab, text="🔍 Strategy Backtester (Simulate)", font=("Arial", 18, "bold")).pack(pady=20)
        
        input_frame = ctk.CTkFrame(tab)
        input_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(input_frame, text="Symbol (e.g. RELIANCE.NS):").grid(row=0, column=0, padx=10, pady=10)
        self.bt_symbol_entry = ctk.CTkEntry(input_frame, width=150)
        self.bt_symbol_entry.insert(0, "RELIANCE.NS")
        self.bt_symbol_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Buy RSI:").grid(row=1, column=0, padx=10, pady=10)
        self.bt_buy_entry = ctk.CTkEntry(input_frame, width=60)
        self.bt_buy_entry.insert(0, "35")
        self.bt_buy_entry.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Sell RSI:").grid(row=1, column=2, padx=10, pady=10)
        self.bt_sell_entry = ctk.CTkEntry(input_frame, width=60)
        self.bt_sell_entry.insert(0, "65")
        self.bt_sell_entry.grid(row=1, column=3, sticky="w", padx=10, pady=10)
        
        self.run_bt_btn = ctk.CTkButton(tab, text="🚀 Run Backtest", command=self.run_historical_backtest)
        self.run_bt_btn.pack(pady=20)
        
        self.bt_result_area = ctk.CTkTextbox(tab, width=500, height=200)
        self.bt_result_area.pack(pady=10)
        self.bt_result_area.insert("0.0", "Results will appear here...")

    def run_historical_backtest(self):
        """Invoke the backtester module"""
        symbol = self.bt_symbol_entry.get()
        buy_rsi = int(self.bt_buy_entry.get())
        sell_rsi = int(self.bt_sell_entry.get())
        
        self.run_bt_btn.configure(state="disabled", text="⏳ Running...")
        self.bt_result_area.delete("0.0", "end")
        self.bt_result_area.insert("0.0", f"Fetching data for {symbol}...\n")
        
        def run():
            try:
                from backtester import run_backtest
                results = run_backtest(symbol, buy_rsi=buy_rsi, sell_rsi=sell_rsi)
                
                self.root.after(0, lambda: self.show_bt_results(results))
            except Exception as e:
                self.root.after(0, lambda: self.bt_result_area.insert("end", f"Error: {e}"))
                self.root.after(0, lambda: self.run_bt_btn.configure(state="normal", text="🚀 Run Backtest"))

        threading.Thread(target=run, daemon=True).start()

    def show_bt_results(self, results):
        self.run_bt_btn.configure(state="normal", text="🚀 Run Backtest")
        self.bt_result_area.delete("0.0", "end")
        if "error" in results:
            self.bt_result_area.insert("0.0", f"❌ Error: {results['error']}")
            return
            
        res_text = "📊 BACKTEST RESULTS\n" + "="*30 + "\n"
        for k, v in results.items():
            res_text += f"{k}: {v}\n"
        self.bt_result_area.insert("0.0", res_text)

    def show_knowledge_center(self):
        """Show the Knowledge Center / Strategy Guide modal"""
        guide_dialog = ctk.CTkToplevel(self.root)
        guide_dialog.title("📖 ARUN Knowledge Center")
        guide_dialog.geometry("1100x800")
        guide_dialog.grab_set()

        ctk.CTkLabel(guide_dialog, text="🎓 Strategy Guides", font=("Arial", 26, "bold")).pack(pady=20)
        
        # Guide Selection
        guide_frame = ctk.CTkScrollableFrame(guide_dialog, width=1050, height=650)
        guide_frame.pack(padx=20, pady=10, fill="both", expand=True)

        for name, guide in STRATEGY_GUIDES.items():
            card = ctk.CTkFrame(guide_frame, fg_color="#2B2B2B", corner_radius=10)
            card.pack(fill="x", pady=10, padx=5)
            
            ctk.CTkLabel(card, text=guide['title'], font=("Arial", 18, "bold"), text_color="#3498DB").pack(anchor="w", padx=15, pady=(10, 5))
            ctk.CTkLabel(card, text=guide['summary'], font=("Arial", 14), wraplength=800, justify="left").pack(anchor="w", padx=15, pady=5)
            
            steps = "\n".join([f"• {step}" for step in guide['how_it_works']])
            ctk.CTkLabel(card, text=f"How it works:\n{steps}", font=("Arial", 13), text_color="gray", justify="left").pack(anchor="w", padx=25, pady=(5, 10))

        ctk.CTkButton(guide_dialog, text="Close", command=guide_dialog.destroy).pack(pady=10)

    def run(self):
        # Periodic performance update
        def update_periodically():
            while True:
                time.sleep(30)  # Update every 30 seconds
                try:
                    self.update_performance_summary()
                except:
                    pass
        
        if DATABASE_AVAILABLE:
            import threading
            update_thread = threading.Thread(target=update_periodically, daemon=True)
            update_thread.start()
        
        self.root.mainloop()

if __name__ == "__main__":
    # Check Disclaimer first
    from disclaimer_gui import DisclaimerGUI

    def start_main_gui():
        gui = TradingGUI()
        gui.run()

    # Launch Disclaimer -> then Main GUI
    DisclaimerGUI(start_main_gui)