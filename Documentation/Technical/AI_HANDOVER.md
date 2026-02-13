# 🤖 AI Agent Handover Document

**Project**: ARUN Trading Bot Titan V2.4.2
**Last Updated**: February 13, 2026  
**Status**: v2.4.2 - Risk UI & Stability Fixes  
**Next Agent**: Please read this before making ANY code changes

---

## 🎯 Project Mission
Build a **safe, smart, and user-friendly** algorithmic trading bot for the Indian stock market (NSE/BSE) using the mStock broker API.

---

## 📦 Current State (What Works)

### Core Features ✅
1. **Trading Engine**: RSI Mean Reversion strategy in `kickstart.py`
2. **Dashboard**: Titan V2 dark UI with Bento Grid (`dashboard_v2.py`)
3. **Safety Features**:
   - Capital Allocation ("Safety Box") - limits bot to specific funds
   - Position Tagging (BOT vs MANUAL trades)
   - Stop Loss / Profit Target automation
4. **Smart UX**:
   - Market Sentiment Meter with AI Reasoning
   - Knowledge Tab (trading education)
   - Sector-based "Baskets" for panic exits
5. **Simulation Mode**: Realistic random-walk prices for paper trading

### File Structure
```
kickstart.py          → Core trading logic (headless-capable)
sensei_v1_dashboard.py -> Main GUI (customtkinter) - CURRENT
settings_gui.py       → Configuration panel (embedded in dashboard)
market_sentiment.py   → Sentiment analysis (yfinance + fallback)
database/trades_db.py → SQLite trade logging
strategies/          → sector_map.py, trading_tips.json
```

---

## 🚨 Critical Rules (DO NOT VIOLATE)

### 1. Never Break Simulation Mode
- `kickstart.py` MUST work offline (Paper Trading)
- Always fallback to mock data if API fails
- Check `should_simulate` flag before showing errors

### 2. Preserve Hot-Reload Logic
- `settings_gui.py` uses `on_save_callback` to reload without restart
- `kickstart.reload_config()` re-reads settings dynamically

### 3. Database Schema is Sacred
- Migrations in `database/trades_db.py` use `ALTER TABLE IF NOT EXISTS`
- NEVER drop columns (breaks existing installs)
- New columns must have DEFAULT values

### 4. GUI is Desktop-Only (CustomTkinter)
- This is NOT a web app
- Mobile requires Streamlit (Phase 4, deferred)

---

## 🐛 Known Issues / Tech Debt

### 1. yfinance Spam (Cosmetic)
- `market_sentiment.py` logs VIX errors when market closed

### 2. Settings Embedded Height
- Settings view is scrollable when embedded
- Save button at bottom (user must scroll)

### 3. Hardcoded Credentials
- User must manually edit `settings.json` for API keys

---

## 📂 Key Files Explained

### `kickstart.py`
**PURPOSE**: Headless trading engine  
**ENTRY**: `run_cycle()` - fetches data, calculates RSI, places orders  

### `dashboard_v2.py`
**PURPOSE**: Main GUI window (Titan design)  

---

## 🚀 Quick Start for Next AI

1. Read `Documentation/roadmap_and_state.md`
2. Check `Documentation/task.md` for current status
3. Run `LAUNCH_ARUN.bat` to see live system
4. Test changes in Paper Trading Mode first

---

## 📝 SESSION LOG (AI Collaboration Tracking)

### Session: January 26, 2026 - Google Gemini (Antigravity)
**Objective:** RSI Logic Integration, Dashboard Enhancements, and Stability Fixes

**Work Completed:**
1.  **Metric Integration (RSI)**:
    -   **Database**: Added `rsi` column to `trades` table.
    -   **Execution**: Patched `kickstart.py` to capture RSI during order placement.
    -   **Dashboard**: Upgraded "Trades View" to a full Treeview table and added RSI columns.
2.  **UI/UX Stability**:
    -   **Fixed Flicker**: Resolved issue where PnL flickered to 0 by returning `None` correctly on API errors.
    -   **Stats Update**: Implemented auto-refresh loop for trade history statistics.
3.  **Project Maintenance**:
    -   **Decluttered Project Root**: Moved legacy files to `Documentation/Legacy_Launchers/` and `_dev_tools/`.
    -   **Dependency Fix**: Restored `getRSI.py` and `nifty50.py` to root.
    -   **Launcher Fix**: Restored `LAUNCH_ARUN.bat` and recreated `.venv` from scratch following a "path not found" crash.

**Status:** Phase 3 Complete ✅

### Session: January 28, 2026 - Google Gemini (Antigravity)
**Objective:** Resolve "Possibly Delisted" / "Expecting Value" Errors

**Issue:**
- `yfinance` (v0.2.40) failed to fetch data for standard tickers (`^NSEI`, `^INDIAVIX`), returning 403 or JSON decode errors.
- **Root Cause:** Yahoo Finance tightened API restrictions, requiring a valid browser `User-Agent`.

**Work Completed:**
1.  **Library Upgrade**: Upgraded `yfinance` to `v1.1.0+` which handles new Yahoo API requirements natively.
2.  **Robustness Patch**: Added `get_yfinance_session()` helper in `utils.py` and patched `market_sentiment.py`, `regime_monitor.py`, and `getRSI.py` to inject browser-like headers (best practice even with newer lib).
3.  **Verification**: Confirmed successful data fetch for Nifty and VIX.

**Status:** v2.0.1 stable ✅

---

### Session: January 28, 2026 - Claude Sonnet 4.5 (Anthropic)
**Objective:** Integrate MACD Scanner + Dual-Bot Strategy Architecture Review

**Work Completed:**
1.  **Strategic Analysis**: Conducted comprehensive architectural review of dual-bot strategy proposal:
    -   Identified critical risks: signal conflicts, capital fragmentation, timeframe mismatch
    -   Recommended "Unified Strategy Orchestrator" pattern instead of independent bots
    -   Designed confluence scoring system (MACD + MA + RSI + Volume + Regime)
    -   Provided phased implementation roadmap (Display → Orchestrator → Execution)

2.  **MACD Scanner Engine** (`scanner_engine.py`):
    -   Lightweight scanner for 300-1200+ NSE/BSE stocks
    -   MACD crossover detection with latest-date filtering
    -   Confluence scoring (0-100 scale) combining multiple indicators
    -   Background thread execution (non-blocking)
    -   NO external dependencies (Google Sheets removed - fully embedded)

3.  **Dashboard Integration** (v2.0.1 Light Theme):
    -   Created `SCANNER_INTEGRATION_PATCH_v2.0.1.py` for safe integration
    -   Designed scanner tab matching Light Theme (#EFEBE3 bg, #479FB6 accent)
    -   High contrast text (#1a1a1a) for accessibility
    -   Increased font sizes (+2pt) per v2.0.1 standards
    -   One-click operation (no manual CSV/Google Sheets workflow)

4.  **User Experience Improvements**:
    -   Eliminated manual workflows (scanner runs on button click)
    -   Progress bar with real-time status updates
    -   Result filtering (ALL / STRONG BUY / BUY)
    -   Sorted by confluence score (highest first)
    -   Color-coded results (green/yellow tints for light theme)

**Files Created:**
-   `scanner_engine.py` - Core scanning logic
-   `dashboard_scanner_integration.py` - Integration guide (legacy, superseded)
-   `SCANNER_INTEGRATION_PATCH_v2.0.1.py` - Production-ready patch

**Status:** Ready for integration ⏸️ (Awaiting manual merge)

**Next Steps:**
1.  Apply patch to `sensei_v1_dashboard.py` (follow checklist in patch file)
2.  Test scanner functionality (8-10 min scan of 300 stocks)
3.  Verify no regression in existing tabs
4.  Optional: Implement Strategy Orchestrator (Phase 2 - see architectural review)


### Session: January 28, 2026 - Google Gemini (Antigravity)
**Objective:** Fix "No Data" Validation, Dashboard Price Updates, and Duplicate Sells

**Issue:**
- **Symbol Validation**: `yfinance` failed with "No Data" due to missing user-agent headers and strict WAF rules.
- **Dashboard Prices**: Live prices weren't updating due to simulation fallback triggered by API errors and slow refresh rates.
- **Duplicate Sells**: Redundant profit target logic in both `kickstart.py` and `RiskManager` caused double selling (e.g., MICEL).

**Work Completed:**
1.  **Validation Fix**: Added browser headers to `symbol_validator.py` and implemented `history()` fallback.
2.  **Dashboard Live Updates**: 
    - Integrated RSI worker's live price fetch into the dashboard UI loop.
    - Increased `positions_worker` refresh rate to 10s (was 30s).
3.  **Sell Logic Consolidation**: 
    - Removed redundant profit target check in `kickstart.py`.
    - Added `check_existing_orders` guard to prevent duplicate risk-triggered orders.

**Status:** Validation & Live Updates Fixed ✅

### Session: January 30, 2026 - Google Gemini (Antigravity)
**Objective:** Architecture Upgrade: "Headless Anywhere" Mode + Web Dashboard

**Work Completed:**
1.  **Architecture Migration (Headless)**:
    -   **Backend**: Created `backend/` using FastAPI (Python). This wraps the original `kickstart.py` logic in a background thread.
    -   **Frontend**: Built a new `web-frontend/` using Next.js 14, TailwindCSS, and Shadcn UI.
    -   **Connection**: Linked Frontend to Backend via REST API.

2.  **Core Integration**:
    -   Modified `kickstart.py` to be "Control Aware" (`STOP_REQUESTED` flag).
    -   Created `START_HEADLESS.bat` for one-click launching.

3.  **Features Added**:
    -   **Web Dashboard**: View live P&L, Active Positions, and Bot Status (localhost:3000).
    -   **Remote Control**: "Start/Stop Engine" buttons in web UI.
    -   **Live Logs**: Streamed logs to web interface.

**Status:** Phase 4 (Headless) Complete ✅

### Session: February 1, 2026 - Google Gemini (Antigravity)
**Objective:** P0 Security Hardening for VPS Deployment

**Work Completed:**
1.  **JWT Authentication** (`backend/auth.py`):
    -   Added `python-jose` + `passlib[bcrypt]` for secure token generation
    -   `/api/auth/login` endpoint for obtaining tokens
    -   All `/api/*` endpoints now require Bearer token (except `/health`)
    -   Frontend login page at `/login` with token management

2.  **Rate Limiting** (`backend/main.py`):
    -   Added `slowapi` for DoS protection
    -   Configurable limits via middleware

3.  **HTTPS Preparation**:
    -   `ARUN_SSL_KEYFILE` / `ARUN_SSL_CERTFILE` env vars for SSL
    -   Configurable CORS via `ARUN_CORS_ORIGINS` env var

4.  **Environment Variable Security** (`settings_manager.py`):
    -   Encryption key now reads from `ARUN_ENCRYPTION_KEY` (priority over file)
    -   JWT secret via `ARUN_JWT_SECRET`
    -   Admin credentials via `ARUN_ADMIN_USER` / `ARUN_ADMIN_PASSWORD`

5.  **New API Endpoints**:
    -   `GET /api/pnl` - Today's P&L summary
    -   `GET /api/capital` - Capital allocation summary

6.  **Frontend Updates** (`web-frontend/`):
    -   Auth-protected dashboard with redirect to `/login`
    -   Real P&L and Capital data (no more mocked ₹0.00)
    -   Dark theme with logout button

**Files Modified (Additive - No Core Logic Changed):**
-   `backend/auth.py` (NEW)
-   `backend/api/routes.py` (added auth + new endpoints)
-   `backend/main.py` (rate limiting, CORS config)
-   `backend/requirements.txt` (security deps)
-   `settings_manager.py` (env var priority)
-   `web-frontend/lib/api.ts` (token management)
-   `web-frontend/app/login/page.tsx` (NEW)
-   `web-frontend/components/dashboard-view.tsx` (auth guard, real data)

**Backward Compatibility:** ✅ Core `kickstart.py` unchanged. Desktop GUI unaffected.

**Status**: v2.1.0 - Security Hardening Complete ✅

### Session: February 2, 2026 - Google Gemini (Antigravity)
**Objective:** Dashboard Data Fidelity, RSI Capture, and strict "Never Sell at Loss" Enforcement

**Work Completed:**
1.  **P&L Calculation Logic** (`database/trades_db.py`):
    -   Implemented automatic P&L calculation (Gross/Net/%) within `insert_trade` for `SELL` actions.
    -   SELL trades now automatically find their matching BUY to determine profitability.
    -   **Data Backfill**: Ran `fix_missing_pnl.py` to retroactively calculate P&L for all historical trades in the database.

2.  **RSI Fidelity** (`kickstart.py`):
    -   Modified `safe_place_order_when_open` to capture and record the exact RSI value at the time of trade execution.
    -   Updated all buy/sell triggers to pass the current RSI value to the logging database.

3.  **Strict Safety Enforcement** (`kickstart.py`):
    -   **Never Sell at Loss**: Added an explicit check in the RSI sell loop. Previously, RSI signals could trigger a loss trade if they bypassed RiskManager. Now, RSI sells are strictly blocked if `LTP < EntryPrice` when `never_sell_at_loss` is enabled.
    -   Added shield icon `🛡️` logging for blocked loss-sells for better transparency.

4.  **Desktop Dashboard v2.0.2** (`sensei_v1_dashboard.py`):
    -   **Heartbeat Visibility**: Enhanced the "Last Cycle" indicator with better fonts and placement on the Engine card.
    -   **Source of Truth**: Optimized counter synchronization to pull directly from `state_mgr` instead of log parsing.
    -   **Version Bump**: Updated UI to v2.0.2 to distinguish from older, less accurate versions.

5.  **Web API Sync**: Updated `/api/pnl` to return real profitability metrics based on the new database-calculated `pnl_net`.

**Status:** v2.2.0 - Dashboard Fidelity Complete ✅

---

### Session: February 2, 2026 (Evening) - Stability Redux (v2.2.1)
**Objective**: Fix dashboard regressions and refine engine connectivity.

**Key Changes**:
- **Engine UI Fix**: Sidebar converted to `ScrollableFrame` to prevent "Start/Stop" buttons from being hidden on smaller screens or card overflows.
- **Connectivity Hardening**: Updated `is_system_online` in `kickstart.py` to prioritize the **Broker API** endpoint. This prevents false "Offline" status if Google/Cloudflare are temporarily unreachable.
- **Unified Logic**:
    - "Monitoring X strategies" log now correctly sums both **Stocks list (7)** and **Hybrid holdings (4)**.
    - Dashboard counters for "Today's Attempts/Success" now sync with the database daily trades for absolute fidelity.
- **Bug Fix**: Patch for `The truth value of a DataFrame is ambiguous` error in the dashboard's background update loop.

**Status**: v2.2.1 - Stability & Connectivity Hardening ✅

### Session: February 3, 2026 - Google Gemini (Antigravity)
**Objective**: Fix REIT Symbols (400 Errors) and Balance Reporting Inflation

**Issue**:
- **REIT Symbols**: mStock OHLC API rejected symbols like `EMBASSY` and `BIRET` by name, causing 400 errors and missing prices.
- **Balance Discrepancy**: "Used" capital was inflated because manual holdings in "Butler" mode were tagged as `BOT` and added to the capital summation.

**Work Completed**:
1.  **REIT Price Fallback** (`kickstart.py`):
    - Added `REIT_TOKEN_MAP` to map symbols to their numeric Scrip Master tokens (e.g., EMBASSY: 9383).
    - Implemented a robust price fallback: if the OHLC API fails for a symbol, the bot now pulls the LTP directly from your live holdings.
2.  **Strict Capital Summation** (`kickstart.py` & `sensei_v1_dashboard.py`):
    - Updated `merge_positions_and_orders` to tag managed holdings as `BUTLER` instead of `BOT`.
    - Patched the dashboard logic to strictly sum only `BOT` and `BOT (SETTLING)` tags for the "Used Capital" display.
3.  **Connectivity Hardening**:
    - Standardized browser-like headers in `safe_request` to avoid WAF blocks.
    - Refined offline detection to prevent the bot from pausing indefinitely during transient API hiccups.

**Status**: v2.3.0 - REIT & Balance Fix Complete ✅

### Session: February 13, 2026 - Claude Opus 4.6 (Anthropic)
**Objective**: Fix REIT OHLC API 400 Errors & Scanner Key Case Bug

**Issue**:
- **REIT OHLC 400 Errors**: The `REIT_TOKEN_MAP` mapped EMBASSY→`9383`, BIRET→`2203` (numeric Scrip Master tokens) for the OHLC API, but this API expects **scrip names**, not numeric tokens. The API interpreted `9383` as a scrip name and returned "Invalid symbol. Scrip Name '9383' not found in exchange file." These errors spammed the log every ~1.5 minutes during the engine heartbeat cycle.
- **Scanner Key Case Bug**: `scanner_complete()` in `sensei_v1_dashboard.py` used `r['signal']` (lowercase) but `scanner_engine.py` returns `r['SIGNAL']` (uppercase), causing a silent KeyError that prevented the STRONG BUY/BUY summary counts from displaying.

**Root Cause Analysis**:
- REITs (EMBASSY, BIRET) are listed as **RR series** (REIT Receipts) on NSE, not EQ (Equity). The mStock OHLC API does not recognize RR series instruments by scrip name on NSE.
- On **BSE**, these same symbols are listed as regular **Equity (EQ)** series (EMBASSY: token 542602, BIRET: token 543261), which the OHLC API can resolve.
- The numeric token approach (`NSE:9383`) was wrong because the OHLC API parameter `i=EXCHANGE:SCRIP_NAME` treats the second part as a scrip name, not a numeric token.

**Work Completed**:
1. **`fetch_market_data_once()` (kickstart.py:~231)**: Removed REIT_TOKEN_MAP usage for OHLC API. Now tries BSE first for REIT symbols (where they're listed as equity), then falls back to NSE. Silences log spam for known REIT failures.
2. **`fetch_market_data()` (kickstart.py:~504)**: Same fix - tries BSE for REITs, silently falls through to holdings LTP fallback on failure.
3. **`scanner_complete()` (sensei_v1_dashboard.py:~1335)**: Fixed `r['signal']` → `r.get('SIGNAL')` to match scanner engine's uppercase keys.

**Important Notes for Next Agent**:
- The `REIT_TOKEN_MAP` is still used correctly in `resolve_instrument_token()` (line ~829) and historical data API (line ~1974) where numeric tokens ARE needed. Do NOT remove it entirely.
- The scanner (scanner_engine.py) uses **Yahoo Finance** exclusively for data - it does NOT call mStock. Scanner errors are unrelated to mStock API errors.
- If more REIT/InvIT symbols are added in the future, they should be added to `REIT_TOKEN_MAP` in `constants.py` AND verified that their BSE listing exists as EQ series.

**Status**: v2.3.1 - REIT OHLC & Scanner Fix ✅

### Session: February 13, 2026 (Continued) - Claude Opus 4.6 (Anthropic)
**Objective**: Modernize Scanner UI + Add Track-to-Stocks Feature

**Work Completed**:
1. **Scanner UI Modernization** (`sensei_v1_dashboard.py:build_scanner_view()`):
   - Replaced verbose "HOW IT WORKS" info card with compact inline hint badge
   - Streamlined control bar with mode selector, separator, and pill-shaped buttons
   - Compact inline progress bar (replaces separate TitanCard)
   - Modern results section with colored pill badges for STRONG BUY / BUY counts
   - Improved table styling with selection highlighting and flat headings
   - Added empty state message when no results
   - Added "tracked" tag (blue tint) for stocks already in portfolio

2. **Track-to-Stocks Feature** (new `on_scanner_track_click()` method):
   - Added "Action" column (7th column, labeled "TRACK") to scanner results table
   - Shows "+ Track" for untracked stocks, "Tracked" for already-configured ones
   - Single-click on Action column adds stock to `settings.json` via `settings_mgr.add_stock_config()`
   - Row updates to "Tracked" (blue tint) immediately after adding
   - Toast notification shows confirmation message for 3 seconds
   - Refreshes STOCKS tab table automatically
   - Default config: RSI 35/65, 15T timeframe, dynamic quantity, 10% profit target

3. **Dead Code Cleanup**:
   - Removed ~50 lines of orphaned code inside `filter_scanner_results()` that referenced undefined `parent` variable (positions table duplicate that was never reachable)
   - Fixed `filter_scanner_results()` to be clean 3-line method

4. **First Run Wizard Fix** (`first_run_wizard.py`):
   - Fixed mousewheel `TclError: invalid command name` by checking `winfo_exists()` before scrolling

**Widget Names Preserved** (for handler compatibility):
`self.scanner_running`, `self.scan_mode_var`, `self.btn_start_scan`, `self.btn_stop_scan`,
`self.progress_card`, `self.scanner_table`, `self.scan_progress_bar`, `self.lbl_scan_status`,
`self.scanner_results`, `self.lbl_last_scan`, `self.scanner_filter_var`

**New Widgets Added**:
`self.lbl_strong_buy_badge`, `self.lbl_buy_badge`, `self.lbl_scanner_empty`, `self.lbl_scanner_toast`

### Session: February 13, 2026 - Google Gemini (Antigravity)
**Objective**: Fix Duplicate Buys, Config Corruption, and Modernize Risk UI

**Issue**:
- **Duplicate Buys**: The bot was placing buy orders for the same symbol on both NSE and BSE because the check was exchange-specific.
- **Config Corruption**: `settings.json` contained `NaN` values for the "Strategy" field, causing UI display errors.
- **Outdated UI**: The "Risk Controls" tab was basic and lacked visual feedback.

**Work Completed**:
1.  **Duplicate Buy Prevention** (`kickstart.py`):
    -   Modified `check_existing_orders` to be **symbol-aware** for BUY orders. If a symbol exists on ANY exchange (holdings or pending orders), a new BUY is blocked.
    -   SELL orders remain exchange-specific (you can only sell what you hold on that specific exchange).

2.  **Config Repair** (`settings.json`):
    -   Identified and replaced `NaN` values in the `strategy` field with `"TRADE"`.
    -   Ensured the file is valid JSON to prevent "nan" display in the UI.

3.  **UI Modernization** (`settings_gui.py`):
    -   **Risk Controls Redesign**: Completely overhauled the tab with grouped cards ("Primary Protection", "Safety Nets", "Advanced Overrides").
    -   **Visual Sliders**: Added color-coded sliders for Stop-Loss (Red), Profit Target (Green), etc.
    -   **Safety Toggles**: improved the "Never Sell at Loss" switch with a clear warning and `COLOR_DANGER` styling.
    -   **Fix**: Added missing `COLOR_DANGER` and `COLOR_SUCCESS` constants.

**Status**: v2.4.2 - Risk UI & Stability Fixes ✅

