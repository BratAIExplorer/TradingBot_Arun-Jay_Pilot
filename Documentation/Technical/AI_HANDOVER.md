# 🤖 AI Agent Handover Document

**Project**: ARUN Trading Bot Titan V2 + VPS Deployment
**Last Updated**: January 18, 2026
**Status**: Phase 2 Complete + Phase 4 Infrastructure Sprint ✅ COMPLETE
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
   - **NEW**: "Never Sell Below Entry Price" enforcement (kickstart.py:1584-1590)
4. **Smart UX**:
   - Market Sentiment Meter with AI Reasoning
   - Knowledge Tab (trading education)
   - Sector-based "Baskets" for panic exits
5. **Simulation Mode**: Realistic random-walk prices for paper trading

### Recent Critical Fix (Jan 18, 2026) 🔧
**Issue**: RSI sell signals could trigger even when price was below entry (potential loss)
**Fix**: Added strict enforcement of `risk.never_sell_at_loss` setting
- Location: `kickstart.py:1584-1590`
- Behavior: When RSI ≥ sell_threshold but current_price ≤ entry_price, bot HOLDS
- User Control: Configurable via `settings.json` (`risk.never_sell_at_loss`, default: `true`)
- Compliance: Satisfies trading conditions requirement "Never sell below entry price"
- Gap Analysis: See `Documentation/GAP_ANALYSIS.md` for full details

### Phase 4 Infrastructure Sprint ✅ COMPLETE (Jan 18, 2026)
**Achievement**: 24/7 VPS deployment and mobile monitoring

**New Components**:
1. **bot_daemon.py** (441 lines): Headless VPS runner
   - Commands: start, stop, restart, status, run
   - PID file management, logging with rotation
   - Graceful shutdown (SIGTERM/SIGINT)
   - Systemd service integration

2. **mobile_dashboard.py** (614 lines): Streamlit web UI
   - Password-protected remote monitoring
   - Real-time P&L and performance metrics
   - Active positions and trades history
   - System logs viewer with search
   - Mobile-responsive design (Titan theme)

3. **Documentation/VPS_DEPLOYMENT.md** (650 lines): Cloud deployment guide
   - Step-by-step VPS setup (DigitalOcean, AWS, Linode)
   - Systemd service configuration
   - Security and firewall setup
   - Troubleshooting and maintenance

**See**: `Documentation/Technical/OPTION_B_IMPLEMENTATION_PLAN.md` for implementation details

### File Structure
```
kickstart.py          → Core trading logic (headless-capable)
bot_daemon.py         → NEW: Headless VPS runner (Phase 4)
dashboard_v2.py       → Main GUI (customtkinter)
mobile_dashboard.py   → NEW: Streamlit mobile monitor (Phase 4)
settings_gui.py       → Configuration panel (embedded in dashboard)
market_sentiment.py   → Sentiment analysis (yfinance + fallback)
database/trades_db.py → SQLite trade logging
strategies/          → sector_map.py, trading_tips.json
Documentation/
  VPS_DEPLOYMENT.md   → NEW: Cloud deployment guide (Phase 4)
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
- [x] "Never Sell Below Entry" compliance fix (Jan 18, 2026)

### ✅ Phase 4: Infrastructure Sprint ✅ COMPLETE (Jan 18, 2026)
**Achievement**: Headless Core + Mobile Dashboard (Option B)

**Completed Components**:
- [x] **bot_daemon.py**: Headless daemon for VPS deployment
  - Runs kickstart.py without GUI ✅
  - Systemd service integration ✅
  - Graceful start/stop controls ✅
  - PID file management ✅
  - Logging with rotation ✅

- [x] **mobile_dashboard.py**: Streamlit web UI for mobile monitoring
  - Real-time P&L and positions ✅
  - Trades history with filters ✅
  - Password-protected read-only access ✅
  - System logs viewer ✅
  - Mobile-responsive Titan theme ✅

- [x] **VPS_DEPLOYMENT.md**: Step-by-step cloud deployment guide
  - VPS provider comparison ✅
  - Complete setup instructions ✅
  - Systemd service configuration ✅
  - Security and firewall setup ✅
  - Troubleshooting guide ✅

**Files Added**: bot_daemon.py, mobile_dashboard.py, Documentation/VPS_DEPLOYMENT.md
**Dependencies Added**: streamlit>=1.30.0, psutil>=5.9.0
**Implementation Plan**: See `Documentation/Technical/OPTION_B_IMPLEMENTATION_PLAN.md`

### ✅ Collaboration Testing Session (Jan 18, 2026 - Evening)
**Purpose**: Testing collaboration workflow, resolver branch conflicts, define launcher architecture

**Key Decisions**:
1. **Branch Strategy**:
   - Main branch: `claude/sync-github-remote-3461O` (contains all latest features)
   - User's working directory: `C:\Antigravity\TradingBots-Aruns Project`
   - Branch switching requires: `git stash` → `git checkout` → `git stash pop`
   
2. **Launcher Simplification** (BACKLOG - Post Testing):
   - **Current State**: 11 different .bat files (confusing for users)
   - **Target State**: 1-2 essential launchers
   - **Solution**: `START_ARUN.bat` with smart first-run setup
     - First run: Install dependencies + create desktop shortcut
     - Subsequent runs: Quick validation (2s) + launch
   - **Cleanup Plan**: Move dev tools to `_dev_tools/`, delete deprecated launchers

3. **Architecture: Hybrid Foreground Bot + Web Dashboard**:
   - **Decision**: NO daemon mode (for now)
   - **Rationale**: 
     - User doesn't need 24/7 bot operation
     - Simpler UX: Close GUI = Bot stops
     - Mobile monitoring via web dashboard (read-only)
   - **Components**:
     - `START_ARUN.bat`: Launches desktop GUI + web dashboard simultaneously
     - Desktop GUI: Full control (read-write)
     - Web dashboard: Mobile monitoring via local WiFi (read-only)
     - Access from phone: `http://192.168.x.x:8501` (same WiFi)
   - **No STOP_ARUN.bat needed**: Just close GUI window

4. **Dependency Conflicts Fixed**:
   - Issue: `cachetools` version conflict (python-telegram-bot 13.15 requires 4.2.2, streamlit 1.53.0 requires >=5.5)
   - Status: Known conflict, both packages installed and working
   - Future: Consider updating python-telegram-bot or isolating dependencies

**Files to Clean Up** (Post-Testing Backlog):
- Remove: `LAUNCH_ARUN.bat`, `LAUNCH_V1_BACKUP.bat`, `LAUNCH_V2.bat`, `LAUNCH_BOT_DAEMON.bat`, `LAUNCH_DASHBOARD.bat`, `LAUNCH_DESKTOP_GUI.bat`, `CHECK_BOT_STATUS.bat`
- Keep: `START_ARUN.bat` (unified launcher)
- Move to `_dev_tools/`: `build_installer.bat`, `test_installer_gui.bat`

### 🔜 Phase 4.1 (Next)
- [ ] Implement unified `START_ARUN.bat` launcher
- [ ] Clean up deprecated .bat files
- [ ] Smart Order Suggestions ("Grammarly for Trading")
- [ ] Hybrid Holding Management
- [ ] Mobile push notifications

### 🔜 Phase 5 (Future)
- [ ] Daemon mode (optional checkbox in settings)
- [ ] Confluence Scoring Engine (0-100 stock scoring)
- [ ] Smart SIP module
- [ ] News Sentiment Engine

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
