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

## 🎯 Core Design Principles (January 2026 Update)

### 1. User Control First
**Philosophy:** Give users full control over ALL strategies, risk management, and conditions.

**How to Implement:**
- ✅ Make every safety feature **toggleable** (with checkboxes in Settings)
- ✅ Provide clear **warnings** about consequences of disabling safety features
- ✅ Use **tooltips** (? buttons) to explain technical features in plain language
- ✅ **Default to safe** (features enabled), but allow expert users to override

**Example:**
- Regime Monitor: Enabled by default, but user can disable via Settings → Broker
- Stop-Loss: Configured in Settings → Risk Controls with warning about "Never Sell at Loss"
- Paper Trading: Toggle in Settings with clear explanation

### 2. Before Building New Features
**Process:**
1. **Check Senior Architect document first** - Code may already exist
2. **Reuse existing code** where possible (don't reinvent the wheel)
3. **Make it configurable** - Add settings UI, not hardcode values
4. **Test with user** - Get feedback before building more

**Already Customizable in ARUN:**
- ✅ All broker credentials (Settings → Broker)
- ✅ Capital allocation & position sizing (Settings → Capital)
- ✅ Stop-loss, profit targets, daily limits (Settings → Risk Controls)
- ✅ Paper trading mode (Settings → Broker)
- ✅ Nifty 50 filter (Settings → Broker)
- ✅ **Regime Monitor** (Settings → Broker - NEW!)
- ✅ Stock configurations (Settings → Stocks)
- ✅ Telegram notifications (Settings → Notifications)

**AI Agents: Always check if feature needs Settings UI before hardcoding!**

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

---

## 📝 SESSION LOG (AI Collaboration Tracking)

### Session: January 18, 2026 - Google Gemini (Antigravity)
**Objective:** Project foundation setup + Regime Monitor implementation

**Work Completed:**
1. ✅ Reviewed existing AI_HANDOVER.md (this file)
2. ✅ Confirmed Documentation structure (Technical/, Product/ folders exist)
3. ✅ Created Reference/CryptoBot_Intelligence_Inspiration/ folder
4. ✅ Moved crypto reference docs:
   - REFERENCE_confluence.md → Reference/CryptoBot_Intelligence_Inspiration/
   - REFERENCE_final_summary.md → Reference/CryptoBot_Intelligence_Inspiration/
   - REFERENCE_intelligence.md → Reference/CryptoBot_Intelligence_Inspiration/ 
   - cryptobot_investment_analysis.md → Reference/CryptoBot_Intelligence_Inspiration/
5. ✅ Created README.md in Reference folder clarifying these are STOCK trading inspiration (not crypto implementation)
6. ✅ Implemented Regime Monitor (`regime_monitor.py` - 430 lines)
   - ✅ Nifty 50 index data fetching via yfinance
   - ✅ 50/200 SMA trend detection
   - ✅ ADX calculation for trend strength
   - ✅ Volatility (20-day) and drawdown metrics
   - ✅ Regime classification (BULLISH/BEARISH/SIDEWAYS/VOLATILE/CRISIS)
   - ✅ Caching mechanism (1-hour default)
   - ✅ Fallback handling when data unavailable
   - ✅ Tested successfully (runs without errors)
7. ✅ **Integrated Regime Monitor into kickstart.py** (CRITICAL MILESTONE)
   - ✅ Added import and initialization
   - ✅ Added regime check before trading loop (line ~1840)
   - ✅ Trading HALTS during BEARISH/CRISIS conditions
   - ✅ Position sizes reduced during VOLATILE/SIDEWAYS (50-75% of normal)
   - ✅ Graceful fallback if regime monitor fails
   - ✅ Committed to git with full documentation
8. ✅ Created VERSION_CONTROL_GUIDELINES.md for safe development
9. ✅ Verified Paper Trading mode implementation (already exists, working correctly)
10. ✅ **Built Backtest Engine** (backtest_engine.py - 480 lines)
   - ✅ Reused code from Senior Architect document (efficient development)
   - ✅ Historical data fetching via yfinance (.NS suffix for NSE)
   - ✅ RSI(14) strategy simulation with configurable thresholds
   - ✅ Realistic Indian brokerage fees (STT, exchange, SEBI, stamp duty, GST)
   - ✅ Performance metrics (return %, CAGR, win rate, Sharpe, max drawdown)
   - ✅ Trade-by-trade breakdown and validation (PASS/FAIL criteria)
   - ✅ Committed to git

**Next Steps:**
- [x] Implement Regime Monitor (regime_monitor.py) ✅ COMPLETE
- [x] Integrate Regime Monitor into kickstart.py ✅ COMPLETE
- [x] Build Backtest Engine (backtest_engine.py) ✅ COMPLETE
- [x] Make Regime Monitor user-configurable ✅ COMPLETE
- [ ] **READY FOR USER TESTING** (All P0 features complete)

**Status:** ✅ ALL P0 FEATURES COMPLETE - Ready for Comprehensive Testing

**Git Commits (All on feature/safety-features-integration branch):**
1. `18a6fbf` - Regime Monitor module + documentation reorganization
2. `acd9a07` - Regime Monitor integration into trading cycle
3. `baf9a46` - AI_HANDOVER documentation update (Phase 1)
4. `4b5f0f7` - Backtest Engine implementation
5. `2382f80` - AI_HANDOVER final update (Phase 2)
6. `[latest]` - Make Regime Monitor user-configurable

**Handoff Notes for Next AI:**
> **🎉 MAJOR MILESTONE ACHIEVED!**
>
> All critical P0 safety features are now complete and follow the core design principle:
> **"User control first, with clear warnings"**
>
> **What's Ready:**
> 1. ✅ Regime Monitor - Prevents bear market losses (user can disable)
> 2. ✅ Backtest Engine - Validates strategies on historical data
> 3. ✅ User-configurable everything - All features toggleable in Settings
> 4. ✅ Paper Trading - Already working (confirmed)
> 5. ✅ Version Control Guidelines - Safe development documented
>
> **Testing Checklist:**
> ```bash
> # 1. Test Regime Monitor standalone
> python regime_monitor.py
>
> # 2. Test Backtest Engine
> python backtest_engine.py
>
> # 3. Test Settings GUI
> python dashboard_v2.py
> # → Go to Settings → Broker
> # → Verify "Enable Regime Monitor" checkbox exists
> # → Try toggling it on/off and save
>
> # 4. Test Full Bot
> # → Enable Paper Trading Mode
> # → Start bot and check logs for regime status
> # → Verify trading halts if regime is BEARISH (or not if disabled)
> ```
>
> **Design Principle for Future Development:**
> Before building ANY new feature:
> 1. Check Senior Architect document for existing code
> 2. Make it user-configurable (Settings UI)
> 3. Add clear warnings/tooltips
> 4. Default to safe, allow expert override
>
> **Next Session Should:**
> - Run comprehensive tests on all components
> - Backtest strategy on user's actual symbols (MICEL, TCS, INFY, etc.)
> - Create deployment checklist
> - Merge feature branch to main after user approval
