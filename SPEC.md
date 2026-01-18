# ARUN Trading Bot - Technical Specification

**Project**: ARUN (Autonomous Retail Unit) Trading Bot
**Repository**: BratAIExplorer/TradingBot_Arun-Jay_Pilot
**Branch**: claude/sync-github-remote-3461O
**Last Updated**: January 18, 2026
**Status**: Phase 2 Complete (Titan V2 UX)

---

## 1. Project Overview

ARUN is an algorithmic trading bot for the Indian stock market (NSE/BSE) with a focus on:
- **Safety**: Capital allocation limits, position tagging, risk management
- **Intelligence**: RSI mean reversion strategy, AI-powered market sentiment
- **User Experience**: Titan V2 dark theme dashboard, knowledge center, sector baskets

**Core Value Proposition**: "Safe, smart, and user-friendly algorithmic trading for retail investors"

---

## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Dashboard (GUI)                         │
│                   dashboard_v2.py                           │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │Dashboard │Strategies│Knowledge │Settings (embedded)    │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Trading Engine (Headless)                      │
│                   kickstart.py                              │
│  ┌──────────────┬──────────────┬──────────────────────┐   │
│  │Data Fetcher  │RSI Calculator│Order Executor         │   │
│  │(Live/Mock)   │              │(Real/Simulation)      │   │
│  └──────────────┴──────────────┴──────────────────────┘   │
└───────┬──────────────────────────────────┬─────────────────┘
        │                                  │
        ▼                                  ▼
┌───────────────────┐            ┌──────────────────────┐
│ External APIs     │            │ Local Database       │
│ - mStock Broker   │            │ SQLite (trades.db)   │
│ - Yahoo Finance   │            │ - trades table       │
└───────────────────┘            └──────────────────────┘
```

### 2.2 Technology Stack

**Frontend (GUI)**:
- CustomTkinter (desktop GUI framework)
- Dark theme (Titan V2 design)

**Backend (Trading Engine)**:
- Python 3.x
- Pandas (data processing)
- Requests (HTTP client)

**Database**:
- SQLite3 (local storage)
- Schema: trades table with columns (symbol, action, quantity, price, timestamp, source)

**External APIs**:
- mStock API (Type A) - market data, order placement, positions
- Yahoo Finance API - market sentiment (VIX, Nifty indices)

---

## 3. Core Features

### 3.1 Trading Strategy
**Algorithm**: RSI Mean Reversion
- **Entry**: Buy when RSI < 30 (oversold)
- **Exit**: Sell when RSI > 70 (overbought) or profit/loss targets hit
- **Parameters**: 14-period RSI, configurable per stock

### 3.2 Safety Features

**Capital Allocation ("Safety Box")**:
- User sets maximum capital bot can use
- Prevents bot from trading entire account
- Configurable per session

**Position Tagging**:
- Tags: BOT (automated) vs MANUAL (user-initiated)
- Prevents bot from selling manual positions
- Tracked in database `source` column

**Risk Management**:
- Stop loss percentage (default: 2%)
- Profit target percentage (default: 5%)
- Max positions per stock

### 3.3 Simulation Mode (Paper Trading)

**24/7 Operation**:
- Works offline without real market data
- Random walk price generation
- Realistic bid/ask spreads

**Implementation**:
- `MOCK_PRICES` dictionary tracks simulated prices
- `should_simulate` flag in settings
- Fallback when API unavailable

### 3.4 User Interface (Titan V2)

**Dashboard View**:
- 4-card Bento grid layout
- Real-time P&L display
- Market sentiment meter with AI reasoning
- System status indicators

**Strategies View**:
- Sector-based "Baskets" (IT, Banking, Energy, etc.)
- Panic sell button per sector
- Algorithm cards with performance metrics

**Knowledge Center**:
- Trading education tips
- Strategy explanations
- Risk management guides

**Settings Panel**:
- 5 tabs: Broker, Capital, Risk, Notifications, Stocks
- Hot-reload (no restart required)
- Encrypted credential storage

---

## 4. File Structure

```
TradingBot_Arun-Jay_Pilot/
├── kickstart.py              # Trading engine (1880 lines)
├── dashboard_v2.py           # Main GUI (715 lines)
├── settings_gui.py           # Settings panel (1182 lines)
├── market_sentiment.py       # Sentiment analysis (129 lines)
├── settings_manager.py       # Config loader/saver
├── risk_manager.py           # Risk calculations
├── database/
│   └── trades_db.py          # SQLite handler (144 lines)
├── strategies/
│   ├── sector_map.py         # Sector classifications
│   └── trading_tips.json     # Knowledge center content
├── Documentation/
│   ├── Technical/
│   │   ├── AI_HANDOVER.md    # Developer guide
│   │   └── PROJECT_STATUS.md # Current state
│   └── Product/
│       ├── BACKLOG.md        # Product roadmap
│       └── roadmap_and_state.md
├── settings.json             # User configuration
├── stocks.csv                # Trading universe
└── LAUNCH_ARUN.bat          # Windows launcher
```

---

## 5. API Specifications

### 5.1 mStock API Integration

**Base URL**: Configured in settings.json

**Key Endpoints**:

1. **Market Data**
   - Method: GET
   - Purpose: Fetch LTP (Last Traded Price)
   - Response: `{ "symbol": "RELIANCE", "ltp": 2450.50 }`

2. **Order Placement**
   - Method: POST
   - Payload: `{ "symbol": "...", "quantity": 1, "order_type": "MARKET", "action": "BUY/SELL" }`
   - Response: `{ "order_id": "...", "status": "COMPLETE" }`

3. **Positions**
   - Method: GET
   - Purpose: Fetch open positions
   - Response: `[{ "symbol": "...", "quantity": 1, "avg_price": 2450.50 }]`

**Authentication**:
- API Key (header: `X-API-Key`)
- TOTP-based auto-login (pyotp)

### 5.2 Yahoo Finance Integration

**Library**: yfinance (Python package)

**Data Sources**:
- `^NSEI` - Nifty 50 index
- `^INDIAVIX` - India VIX (volatility)

**Purpose**: Calculate market sentiment (Fear/Greed meter)

---

## 6. Database Schema

### 6.1 Trades Table

```sql
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'BUY' or 'SELL'
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    source TEXT DEFAULT 'BOT'  -- 'BOT' or 'MANUAL'
);
```

**Migration Strategy**:
- Auto-migrations on app start
- Uses `ALTER TABLE IF NOT EXISTS` (backward compatible)
- Never drops columns (preserves existing data)

---

## 7. Configuration

### 7.1 settings.json Structure

```json
{
    "broker_config": {
        "api_key": "...",
        "totp_secret": "...",
        "should_simulate": false
    },
    "capital_config": {
        "allocated_capital": 50000,
        "max_position_size": 10000
    },
    "risk_config": {
        "stop_loss_pct": 2.0,
        "profit_target_pct": 5.0,
        "max_positions_per_stock": 1
    },
    "notification_config": {
        "email_enabled": false,
        "webhook_url": ""
    }
}
```

### 7.2 stocks.csv Structure

```csv
symbol,quantity,rsi_period,rsi_buy_threshold,rsi_sell_threshold
RELIANCE,1,14,30,70
TCS,1,14,30,70
INFY,1,14,30,70
```

---

## 8. Development Guide

### 8.1 Running Locally

**Windows**:
```bash
LAUNCH_ARUN.bat
```

**Direct Python**:
```bash
.venv\Scripts\python dashboard_v2.py
```

### 8.2 Testing Flow

1. Enable Paper Trading Mode (Settings → App Settings)
2. Start Engine
3. Verify simulation prices are updating
4. Place test orders
5. Check trades.db for logged trades

### 8.3 Adding New Features

**Backend Changes** (kickstart.py):
1. Modify `run_cycle()` function
2. Test in simulation mode first
3. Ensure backward compatibility

**UI Changes** (dashboard_v2.py):
1. Update relevant `build_*_view()` method
2. Preserve Titan theme colors
3. Test responsiveness

**Settings Changes** (settings_gui.py):
1. Add new tab or section
2. Implement hot-reload callback
3. Update settings.json schema

### 8.4 Critical Rules

**DO NOT**:
- Break simulation mode (must work offline)
- Drop database columns (breaks existing installs)
- Remove hot-reload functionality
- Hardcode API credentials in code

**DO**:
- Test in Paper Mode first
- Use fallbacks for external APIs
- Follow Titan color palette
- Update AI_HANDOVER.md when done

---

## 9. Color Palette (Titan Theme)

```python
COLOR_BG = "#050505"      # Background
COLOR_CARD = "#121212"    # Cards
COLOR_ACCENT = "#00F0FF"  # Cyan (primary)
COLOR_DANGER = "#FF003C"  # Red
COLOR_SUCCESS = "#00E676" # Green
COLOR_TEXT = "#E0E0E0"    # Light grey
COLOR_TEXT_DIM = "#888888" # Dim grey
```

---

## 10. Known Issues

### 10.1 yfinance Spam (Cosmetic)
- **Issue**: Logs VIX errors when market closed
- **Status**: Suppressed with warnings filter
- **Impact**: None (falls back to simulation)

### 10.2 Settings Scrolling
- **Issue**: Save button requires scrolling when embedded
- **Status**: Working as designed
- **Impact**: Minor UX inconvenience

### 10.3 Manual Credential Entry
- **Issue**: User must edit settings.json for first-time setup
- **Status**: Settings GUI available in app
- **Impact**: One-time setup friction

---

## 11. Roadmap

### ✅ Phase 1 Complete
- RSI trading strategy
- mStock API integration
- Basic GUI

### ✅ Phase 2 Complete (Titan V2)
- Bento Grid layout
- Market sentiment AI
- Knowledge center
- Capital Safety Box
- Position tagging
- 24/7 simulation mode

### 🔜 Phase 3 (Next)
- Multi-strategy support
- Advanced charting
- Backtesting module

### 🔜 Phase 4 (Future)
- Mobile companion app (Streamlit)
- Smart order suggestions
- Smart SIP module

---

## 12. Dependencies

### 12.1 Python Packages
```
customtkinter==5.2.1
pandas==2.1.4
requests==2.31.0
yfinance==0.2.33
pyotp==2.9.0
Pillow==10.1.0
```

### 12.2 System Requirements
- Python 3.8+
- Windows 10/11 (primary), Linux (tested), macOS (untested)
- 4GB RAM minimum
- Internet connection (for live trading)

---

## 13. Contact & Support

**Founder**: Arun (BratAIExplorer)
**GitHub**: https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot
**Branch**: claude/sync-github-remote-3461O

For AI agents: Read `Documentation/Technical/AI_HANDOVER.md` before making changes.

---

**Last Updated**: January 18, 2026
**Specification Version**: 1.0
