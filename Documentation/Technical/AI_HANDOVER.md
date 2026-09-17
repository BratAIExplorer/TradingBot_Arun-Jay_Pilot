# 🤖 AI Agent Handover Document

**Project**: ARUN Trading Bot Titan V2  
**Last Updated**: September 10, 2026  
**Status**: Phase 3 Complete (RSI & Stability); strategy-research track concluded — see session log  
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
dashboard_v2.py       → Main GUI (customtkinter)
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

### Session: September 10, 2026 — opencode (deepseek-v4-pro)

**Objective:** After the small-cap MACD/rope strategy was ruled out (21 backtests, no edge), find a "winning" strategy for US + India stocks and ETFs by testing the highest-evidence factor/rotation alternatives.

**Work Completed:**
1.  **Built two new backtest engines**, kept separate from the live small-cap strategy:
    -   `strategies/factor_backtest.py` — monthly trend-timing (Faber) + dual-momentum (Antonacci).
    -   `strategies/xs_momentum.py` — cross-sectional momentum (Jegadeesh-Titman) with regime filter.
2.  **Tested on 15y clean data (2011-10 → 2026-09), both markets, net of costs.** Result: **no active strategy beat buy-and-hold.** Faber gave up ~436 pts (US) for barely better drawdown (monthly signals too slow for the 2020 crash); dual momentum trailed on Sharpe; cross-sectional momentum on Nifty 50 lost to static equal-weight buy-and-hold.
3.  **Conclusion recorded in `strategies/BACKTEST_FINDINGS.md` (§8–§11):** the winning answer is boring — diversified, low-cost buy-and-hold. The real edge is behavioural (holding through drawdowns) + cost control, not a signal.
4.  **Domicile decision:** confirmed Irish UCITS ETFs (CSPX/CNDX) deliver identical beta to US ETFs (SPY/QQQ) with a better tax home — no US estate tax, 15% vs 30% dividend WHT. Recommendation: NIFTYBEES (India) + Irish accumulators (CSPX/VWRA) for international.

**Status:** Strategy research **concluded**. Recommendation = passive buy-and-hold; do not deploy an active stock-picking/timing strategy on the evidence gathered. The small-cap dry-run may continue log-only for forward data, but no signal tested has shown edge.

**New files:** `strategies/factor_backtest.py`, `strategies/xs_momentum.py` (plus the existing `strategies/backtest_smallcap.py`, `backtest_summary.py`, `BACKTEST_FINDINGS.md` from the prior session).

