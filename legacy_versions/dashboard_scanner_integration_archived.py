"""
🔍 SCANNER INTEGRATION PATCH FOR DASHBOARD_V2.PY
═══════════════════════════════════════════════════════════════════════════════

ADD THIS CODE TO YOUR dashboard_v2.py

Instructions:
1. Find the __init__ method around line 108
2. Add: self.view_scanner = ctk.CTkFrame(self.main_container, fg_color="transparent")
3. Add: self.build_scanner_view()
4. Update navigation bar values to include "SCANNER"
5. Copy all methods below into your DashboardV2 class

═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: ADD TO __init__ (around line 108)
# ═══════════════════════════════════════════════════════════════════════
"""
self.view_scanner = ctk.CTkFrame(self.main_container, fg_color="transparent")
self.build_scanner_view()

# Scanner state
self.scanner_running = False
self.scanner_results = []
self.scanner_thread = None
"""

# ═══════════════════════════════════════════════════════════════════════
# STEP 2: UPDATE NAVIGATION BAR (around line 232)
# ═══════════════════════════════════════════════════════════════════════
"""
CHANGE:
values=["DASHBOARD", "HYBRID", "TRADES", "KNOWLEDGE", "STRATEGIES", "SETTINGS", "LOGS"]

TO:
values=["DASHBOARD", "SCANNER", "HYBRID", "TRADES", "KNOWLEDGE", "STRATEGIES", "SETTINGS", "LOGS"]
"""

# ═══════════════════════════════════════════════════════════════════════
# STEP 3: UPDATE show_view METHOD (around line 265)
# ═══════════════════════════════════════════════════════════════════════
"""
ADD TO show_view():

self.view_scanner.pack_forget()  # In hide section

elif view_name == "SCANNER":
    self.view_scanner.pack(fill="both", expand=True)
"""

# ═══════════════════════════════════════════════════════════════════════
# STEP 4: ADD THESE METHODS TO DashboardV2 CLASS
# ═══════════════════════════════════════════════════════════════════════

def build_scanner_view(self):
    """
    🔍 MACD SCANNER TAB - One-click market scanning
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
    ctk.CTkLabel(title_frame, text=" MARKET SCANNER (MACD + Confluence)", font=("Roboto", 20, "bold"), text_color="white").pack(side="left", padx=10)

    # Info Card
    info_card = TitanCard(self.view_scanner, title="HOW IT WORKS", border_color="#333")
    info_card.pack(fill="x", padx=20, pady=(0, 10))

    info_text = """
    🔍 Scans 300 most liquid NSE/BSE stocks for MACD bullish crossovers
    📊 Filters signals using confluence score (MACD + Moving Averages + RSI)
    ⚡ Runs in background - takes 8-10 minutes
    🎯 Shows only actionable opportunities (STRONG BUY / BUY)

    Confluence Score Explained:
    • 75-100: STRONG BUY (MACD + Above 20MA + Above 50MA + Healthy RSI + Fresh signal)
    • 60-74:  BUY (MACD + Some trend confirmation)
    • Below 60: Filtered out (not shown)
    """

    ctk.CTkLabel(info_card, text=info_text, font=("Roboto", 11), text_color="#CCC", justify="left").pack(anchor="w", padx=20, pady=10)

    # Control Panel
    control_card = TitanCard(self.view_scanner, title="SCAN CONTROLS", border_color=COLOR_ACCENT)
    control_card.pack(fill="x", padx=20, pady=(0, 10))

    control_inner = ctk.CTkFrame(control_card, fg_color="transparent")
    control_inner.pack(fill="x", padx=20, pady=15)

    # Scan Mode Selector
    scan_mode_frame = ctk.CTkFrame(control_inner, fg_color="transparent")
    scan_mode_frame.pack(side="left", padx=(0, 20))

    ctk.CTkLabel(scan_mode_frame, text="Scan Mode:", font=("Roboto", 12, "bold"), text_color="#AAA").pack(side="left", padx=(0, 10))

    self.scan_mode_var = ctk.StringVar(value="QUICK")
    scan_mode_selector = ctk.CTkSegmentedButton(
        scan_mode_frame,
        values=["QUICK (300)", "MEDIUM (800)", "FULL (1200+)"],
        variable=self.scan_mode_var,
        font=("Roboto", 11),
        height=32,
        fg_color="#222",
        selected_color=COLOR_ACCENT,
        text_color="white"
    )
    scan_mode_selector.pack(side="left")

    # Start/Stop Button
    self.btn_start_scan = ctk.CTkButton(
        control_inner,
        text="🔍 START SCAN",
        command=self.start_scanner,
        fg_color=COLOR_SUCCESS,
        hover_color="#00C853",
        height=40,
        width=180,
        font=("Roboto", 14, "bold"),
        text_color="black"
    )
    self.btn_start_scan.pack(side="left", padx=10)

    # Stop Button (initially hidden)
    self.btn_stop_scan = ctk.CTkButton(
        control_inner,
        text="⏹ STOP",
        command=self.stop_scanner,
        fg_color=COLOR_DANGER,
        hover_color="#B71C1C",
        height=40,
        width=120,
        font=("Roboto", 14, "bold")
    )
    # Don't pack yet - will show when scanning

    # Last Scan Info
    self.lbl_last_scan = ctk.CTkLabel(
        control_inner,
        text="No scans run yet",
        font=("Roboto", 10),
        text_color="#666"
    )
    self.lbl_last_scan.pack(side="right")

    # Progress Card
    self.progress_card = TitanCard(self.view_scanner, title="SCAN PROGRESS", border_color="#444")
    self.progress_card.pack(fill="x", padx=20, pady=(0, 10))
    self.progress_card.pack_forget()  # Hide initially

    progress_inner = ctk.CTkFrame(self.progress_card, fg_color="transparent")
    progress_inner.pack(fill="x", padx=20, pady=15)

    self.scan_progress_bar = ctk.CTkProgressBar(
        progress_inner,
        height=12,
        progress_color=COLOR_ACCENT,
        fg_color="#333"
    )
    self.scan_progress_bar.pack(fill="x", pady=(0, 8))
    self.scan_progress_bar.set(0)

    self.lbl_scan_status = ctk.CTkLabel(
        progress_inner,
        text="Preparing scan...",
        font=("Roboto", 11),
        text_color="white"
    )
    self.lbl_scan_status.pack(anchor="w")

    # Results Table
    results_card = TitanCard(self.view_scanner, title="SCAN RESULTS", border_color=COLOR_SUCCESS)
    results_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    # Filter Row
    filter_frame = ctk.CTkFrame(results_card, fg_color="transparent")
    filter_frame.pack(fill="x", padx=15, pady=(10, 5))

    ctk.CTkLabel(filter_frame, text="Show:", font=("Roboto", 10), text_color="#AAA").pack(side="left", padx=5)

    self.scanner_filter_var = ctk.StringVar(value="ALL")
    filter_selector = ctk.CTkSegmentedButton(
        filter_frame,
        values=["ALL", "STRONG BUY", "BUY"],
        variable=self.scanner_filter_var,
        command=self.filter_scanner_results,
        font=("Roboto", 10),
        height=28
    )
    filter_selector.pack(side="left")

    self.lbl_scanner_stats = ctk.CTkLabel(
        filter_frame,
        text="Results: 0",
        font=("Roboto", 9),
        text_color="#666"
    )
    self.lbl_scanner_stats.pack(side="right", padx=10)

    # Treeview Table
    table_frame = ctk.CTkFrame(results_card, fg_color="#1a1a1a")
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    cols = ("Symbol", "Company", "Price", "Signal", "Score", "Cross Date", "Days", "20MA", "50MA", "RSI")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Scanner.Treeview", background="#111", foreground="white", fieldbackground="#111", rowheight=32, font=("Roboto", 10))
    style.configure("Scanner.Treeview.Heading", background="#1A1A1A", foreground="#888", font=("Roboto", 10, "bold"))

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
        "Symbol": 100,
        "Company": 200,
        "Price": 80,
        "Signal": 100,
        "Score": 70,
        "Cross Date": 100,
        "Days": 60,
        "20MA": 60,
        "50MA": 60,
        "RSI": 60
    }

    for col in cols:
        self.scanner_table.heading(col, text=col.upper())
        self.scanner_table.column(col, anchor="center", width=col_widths.get(col, 80))

    self.scanner_table.column("Company", anchor="w")

    # Grid layout
    self.scanner_table.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    h_scroll.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # Configure tags for coloring
    self.scanner_table.tag_configure("strong_buy", background="#0A2A0A", foreground=COLOR_SUCCESS)
    self.scanner_table.tag_configure("buy", background="#1A1A0A", foreground=COLOR_WARN)

    # Check if scanner available
    if not self.scanner_available:
        self.btn_start_scan.configure(state="disabled", text="❌ Scanner Not Available")
        error_card = TitanCard(self.view_scanner, border_color=COLOR_DANGER)
        error_card.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(
            error_card,
            text=f"⚠️ Scanner engine not found. Error: {error_msg}\nMake sure scanner_engine.py is in the project folder.",
            font=("Roboto", 11),
            text_color=COLOR_DANGER
        ).pack(padx=20, pady=15)

def start_scanner(self):
    """Start background scanner"""
    if self.scanner_running:
        return

    try:
        from scanner_engine import MACDScanner

        # Get scan mode
        mode = self.scan_mode_var.get()
        if "300" in mode:
            max_stocks = 300
        elif "800" in mode:
            max_stocks = 800
        else:
            max_stocks = None  # Full scan

        # UI updates
        self.scanner_running = True
        self.btn_start_scan.pack_forget()
        self.btn_stop_scan.pack(side="left", padx=10)
        self.progress_card.pack(fill="x", padx=20, pady=(0, 10))

        # Clear previous results
        for item in self.scanner_table.get_children():
            self.scanner_table.delete(item)

        self.write_log(f"🔍 Starting market scan ({mode} mode)...\n")

        # Create scanner instance
        scanner = MACDScanner(progress_callback=self.scanner_progress_update)

        # Run in background thread
        def scan_worker():
            try:
                results = scanner.scan_market(max_stocks=max_stocks)
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
    """Progress callback from scanner"""
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

    # Sort by confluence score (highest first)
    sorted_results = sorted(results, key=lambda x: x['confluence_score'], reverse=True)

    # Apply filter
    filter_val = self.scanner_filter_var.get()

    strong_buy_count = 0
    buy_count = 0

    for r in sorted_results:
        # Filter
        if filter_val != "ALL" and r['signal'] != filter_val:
            continue

        # Count
        if r['signal'] == 'STRONG BUY':
            strong_buy_count += 1
        else:
            buy_count += 1

        # Tag for coloring
        tag = "strong_buy" if r['signal'] == "STRONG BUY" else "buy"

        # Insert row
        self.scanner_table.insert(
            "", END,
            values=(
                r['ticker'],
                r['company'][:30],  # Truncate long names
                f"₹{r['price']}",
                r['signal'],
                r['confluence_score'],
                r['macd_cross_date'],
                r['days_ago'],
                r['above_20ma'],
                r['above_50ma'],
                r['rsi']
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
    self.populate_scanner_results(self.scanner_results)


# ═══════════════════════════════════════════════════════════════════════
# END OF INTEGRATION CODE
# ═══════════════════════════════════════════════════════════════════════

"""
SUMMARY OF CHANGES:
═══════════════════════════════════════════════════════════════════════════════

1. Add self.view_scanner to __init__
2. Add "SCANNER" to navigation bar
3. Update show_view() to handle scanner view
4. Copy all methods above into DashboardV2 class

TESTING:
1. Launch dashboard: python dashboard_v2.py
2. Click "SCANNER" tab
3. Select "QUICK (300)" mode
4. Click "START SCAN"
5. Wait 8-10 minutes
6. View results in table

DONE! ✅
"""
