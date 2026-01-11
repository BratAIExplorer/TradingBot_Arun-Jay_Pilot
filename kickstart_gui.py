import threading
import queue
import customtkinter as ctk
from tkinter import END, ttk
from kickstart import run_cycle, fetch_market_data, config_dict, SYMBOLS_TO_TRACK, calculate_intraday_rsi_tv, is_system_online, safe_get_positions, safe_get_live_positions_merged
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

class TradingGUI:
    def __init__(self):
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Main window
        self.root = ctk.CTk()
        self.root.title("📈 ARUN")
        self.root.geometry("1200x750")
        self.root.configure(cursor="arrow")

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

        # ---------------- Performance Summary (Phase 0A) ----------------
        if DATABASE_AVAILABLE:
            summary_frame = ctk.CTkFrame(self.root, fg_color="transparent")
            summary_frame.pack(pady=10, fill="x", padx=10)
            
            # Configure grid columns to expand equally
            for i in range(5):
                summary_frame.grid_columnconfigure(i, weight=1)
                
            # Get performance data
            perf = db.get_performance_summary()
            
            # Portfolio Card
            portfolio_card = ctk.CTkFrame(summary_frame, fg_color="#1E1E1E", corner_radius=10)
            portfolio_card.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
            ctk.CTkLabel(portfolio_card, text="💼 Portfolio", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10, 0))
            self.portfolio_value_label = ctk.CTkLabel(
                portfolio_card, 
                text=f"₹{perf.get('total_net_pnl', 0):,.0f}",
                font=("Arial", 22, "bold")
            )
            self.portfolio_value_label.pack(pady=(5, 15))
            
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

        self.stop_btn = ctk.CTkButton(button_frame, text="⏹ Stop Bot", command=self.stop_bot, state="disabled", cursor="hand2")
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            button_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            cursor="hand2",
            fg_color="gray",
            hover_color="darkgray"
        )
        self.settings_btn.grid(row=0, column=2, padx=5)

        # ---------------- Log Area ----------------
        self.log_area = ctk.CTkTextbox(self.root, width=1100, height=200, cursor="xterm")
        self.log_area.pack(padx=10, pady=10, fill="both", expand=True)

        # Redirect stdout/stderr
        import sys
        sys.stdout.write = self.write_log
        sys.stderr.write = self.write_log

        # ---------------- Dashboard ----------------
        dashboard_frame = ctk.CTkFrame(self.root)
        dashboard_frame.pack(pady=10, fill="both", expand=True)

        # Live Positions Table
        self.positions_label = ctk.CTkLabel(dashboard_frame, text="📊 Live Positions", font=("Arial", 16, "bold"))
        self.positions_label.pack(anchor="w", padx=10, pady=5)

        pos_frame = ctk.CTkFrame(dashboard_frame)
        pos_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.positions_table = ttk.Treeview(
            pos_frame,
            columns=("Symbol", "Qty", "Entry", "Last", "PnL"),
            show="headings",
            style="NoHighlight.Treeview"
        )
        for col in ("Symbol", "Qty", "Entry", "Last", "PnL"):
            self.positions_table.heading(col, text=col, command=lambda c=col: self.sort_table(self.positions_table, c, False))
            self.positions_table.column(col, width=120, stretch=True, anchor="center")
        
        self.positions_table.grid(row=0, column=0, sticky="nsew")
        pos_frame.grid_rowconfigure(0, weight=1)
        pos_frame.grid_columnconfigure(0, weight=1)

        # Recent Trades Table (Phase 0A)
        if DATABASE_AVAILABLE:
            self.trades_label = ctk.CTkLabel(dashboard_frame, text="📝 Recent Trades", font=("Arial", 16, "bold"))
            self.trades_label.pack(anchor="w", padx=10, pady=5)
            
            trades_frame = ctk.CTkFrame(dashboard_frame)
            trades_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
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
        self.rsi_label = ctk.CTkLabel(dashboard_frame, text="📈 RSI Monitor (Live)", font=("Arial", 16, "bold"))
        self.rsi_label.pack(anchor="w", padx=10, pady=5)

        rsi_frame = ctk.CTkFrame(dashboard_frame)
        rsi_frame.pack(fill="both", expand=True, padx=10, pady=5)

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

        # Start dashboard updates
        self.update_dashboard()

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
                                tag = "profit" if pnl >= 0 else "loss"

                                if self.positions_table.exists(iid):
                                    self.positions_table.item(iid, values=(sym_str, qty, price, last_price, pnl), tags=(tag,))
                                else:
                                    self.positions_table.insert("", "end", iid=iid, values=(sym_str, qty, price, last_price, pnl), tags=(tag,))

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
            import subprocess
            subprocess.Popen(["python", "settings_gui.py"], shell=False)
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
            perf = db.get_performance_summary()
            
            # Update labels
            if hasattr(self, 'portfolio_value_label'):
                self.portfolio_value_label.configure(text=f"₹{perf.get('total_net_pnl', 0):,.0f}")
            
                if hasattr(self, 'total_profit_label'):
                    self.total_profit_label.configure(
                        text=f"₹{perf.get('total_net_pnl', 0):,.0f}",
                        text_color="#2ECC71" if perf.get('total_net_pnl', 0) >= 0 else "#E74C3C"
                    )
                
                if hasattr(self, 'today_pnl_label'):
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
    gui = TradingGUI()
    gui.run()