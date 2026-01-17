# 🤖 AI Agent Handover Document

**Project**: ARUN Trading Bot Titan V2  
**Last Updated**: January 17, 2026  
**Status**: Phase 2 Complete (UX Intelligence)  
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
- See `Founder_Package/mobile_architecture.md`

---

## 🐛 Known Issues / Tech Debt

### 1. yfinance Spam (Cosmetic)
- `market_sentiment.py` logs VIX errors when market closed
- Already suppressed with `warnings.filterwarnings("ignore")`
- Harmless (falls back to simulation)

### 2. Settings Embedded Height
- Settings view is scrollable when embedded
- Save button at bottom (user must scroll)
- Working as designed

### 3. Hardcoded Credentials
- User must manually edit `settings.json` for API keys
- Encrypted storage exists (`settings_manager.py`)
- TOTP auto-login implemented

---

## 📂 Key Files Explained

### `kickstart.py` (1880 lines)
**PURPOSE**: Headless trading engine  
**ENTRY**: `run_cycle()` - fetches data, calculates RSI, places orders  
**CRITICAL GLOBALS**:
- `ALLOCATED_CAPITAL` - max capital bot can use
- `MOCK_PRICES` - simulation state (random walk)
- `config_dict` - loaded from `stocks.csv`

**DEPENDENCIES**: `settings_manager`, `database`, `risk_manager`

### `dashboard_v2.py` (715 lines)
**PURPOSE**: Main GUI window (Titan design)  
**KEY METHODS**:
- `build_dashboard_view()` - 4-card grid layout
- `build_strategies_view()` - Bento baskets + algo cards
- `build_knowledge_view()` - Tips of the day
- `sell_sector_positions(sector)` - Panic exit for sector

**THREADING**: 
- `sentiment_worker()` - fetches VIX data every 5 mins
- `update_ui_loop()` - refreshes UI every 1 sec

### `settings_gui.py` (1182 lines)
**PURPOSE**: Settings panel (5 tabs)  
**TABS**: Broker, Capital, Risk, Notifications, Stocks  
**NEW FEATURE**: "Safety Box" slider in Capital tab (line 301)

### `market_sentiment.py` (129 lines)
**PURPOSE**: Fear/Greed meter logic  
**DATA SOURCE**: Yahoo Finance (^NSEI, ^INDIAVIX)  
**FALLBACK**: Random walk when offline

### `database/trades_db.py` (144 lines)
**PURPOSE**: SQLite trade logger  
**SCHEMA**: `trades` table with `source` column (BOT/MANUAL)  
**MIGRATIONS**: Auto-runs on init (backward compatible)

---

## 🔮 Roadmap (What's Next)

### ✅ Phase 2 Complete
- [x] Bento Grid (Sector Baskets)
- [x] AI Reasoning Engine
- [x] Knowledge Tab
- [x] Capital Safety Box
- [x] Position Tagging
- [x] Simulation Refinement

### 🔜 Phase 4 (Deferred)
- [ ] Mobile Companion App (Streamlit)
- [ ] Smart Order Suggestions ("Grammarly for Trading")
- [ ] Smart SIP module

---

## 🛠️ Development Guide

### Running Locally
```bash
# Windows
LAUNCH_ARUN.bat

# Python directly
.venv\Scripts\python dashboard_v2.py
```

### Testing Simulation Mode
1. Settings → App Settings → Enable "Paper Trading Mode"
2. Start Engine
3. Prices will random-walk (no real API calls)

### Adding a New Feature
1. Update `task.md` in brain folder
2. If backend: modify `kickstart.py`
3. If UI: modify `dashboard_v2.py` or `settings_gui.py`
4. Test in Paper Mode first
5. Update `walkthrough.md`

### Color Palette (Titan Theme)
```python
COLOR_BG = "#050505"      # Background
COLOR_CARD = "#121212"    # Cards
COLOR_ACCENT = "#00F0FF"  # Cyan (primary)
COLOR_DANGER = "#FF003C"  # Red
COLOR_SUCCESS = "#00E676" # Green
```

---

## 📞 External Dependencies

### APIs
- **mStock API** (Type A): Market data, orders, positions
- **Yahoo Finance**: Nifty/VIX sentiment (via `yfinance`)

### Python Packages
- `customtkinter` - GUI framework
- `pandas` - Data processing
- `requests` - HTTP calls
- `sqlite3` - Database (built-in)
- `pyotp` - 2FA/TOTP

---

## 🎓 Founder Preferences

### Communication Style
- User prefers **clear, honest feedback**
- "Do not sugarcoat" - direct answers
- Wants to understand WHY, not just WHAT

### UX Philosophy
- "Human-first" - explain technical terms
- Safety > Speed (capital protection is #1)
- Mobile is future but desktop is priority

### Code Quality
- Stability over features
- "Do No Harm" policy (don't break working code)
- Test in Paper Mode before Live

---

## 🚀 Quick Start for Next AI

1. Read `Founder_Package/roadmap_and_state.md`
2. Check `task.md` for current status
3. Run `LAUNCH_ARUN.bat` to see live system
4. Test changes in Paper Trading Mode first
5. Update this handover when done

**Good luck! 🤖**
