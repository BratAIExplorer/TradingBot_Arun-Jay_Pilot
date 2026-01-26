# 🤖 AI Agent Handover Document

**Project**: ARUN Trading Bot Titan V2  
**Last Updated**: January 26, 2026  
**Status**: Phase 3 Complete (RSI & Stability)  
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
