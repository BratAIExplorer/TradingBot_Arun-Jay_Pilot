# 🤖 AI AGENT HANDOVER DOCUMENT
## ARUN Stock Trading Bot - Strategic Direction & Implementation Roadmap

**Last Updated:** January 17, 2026
**Version:** 1.0
**Status:** Strategic Planning Complete - Ready for Implementation

---

## 📋 TABLE OF CONTENTS

1. [Project Context & Clarity](#1-project-context--clarity)
2. [Strategic Decisions Made](#2-strategic-decisions-made)
3. [Architecture Overview](#3-architecture-overview)
4. [Priority Implementation Roadmap](#4-priority-implementation-roadmap)
5. [Component Specifications](#5-component-specifications)
6. [Do NOT Build (Defer/Delete)](#6-do-not-build-deferdelete)
7. [Success Criteria](#7-success-criteria)
8. [Technical Constraints](#8-technical-constraints)

---

## 1. PROJECT CONTEXT & CLARITY

### 1.1 Project Identity

**CRITICAL CLARIFICATION:**

- **THIS Repository:** ARUN Stock Trading Bot for Indian markets (NSE/BSE)
- **NOT:** Crypto trading bot (separate project, separate repo)
- **Scope:** Indian equity trading ONLY

### 1.2 Reference Documents Clarification

**Files in `Documentation/Reference/CryptoBot_Intelligence_Inspiration/`:**

These are **REFERENCE DOCUMENTS** from a separate crypto bot project, included as:
- ✅ **Architectural inspiration** for intelligence layer design
- ✅ **Feature examples** to adapt for stock trading
- ❌ **NOT** to be implemented as crypto functionality

**Key Concepts to Adapt:**
1. **3-Pillar Architecture** → Long-term SIP, Active Trading, IPO/Small-cap Screening
2. **4-Layer Confluence** → Technical + Fundamental + Macro + News scoring
3. **30-Day Waiting Room** → IPO vetting period, small-cap quality filter
4. **Regime Monitor** → Nifty 50 bull/bear/sideways detection
5. **News Veto System** → Corporate announcements integration
6. **Per-Asset Crash Detection** → Stock circuit breaker logic

---

## 2. STRATEGIC DECISIONS MADE

### 2.1 Feature Priority Matrix

| Feature | Status | Priority | Timeline | Rationale |
|---------|--------|----------|----------|-----------|
| **Regime Monitor** | ❌ Not Built | **P0 - CRITICAL** | Week 1-2 | Prevents 30-70% losses in bear markets |
| **Backtest Engine** | ❌ Not Built | **P0 - CRITICAL** | Week 1-2 | Cannot launch without historical validation |
| **Desktop GUI Improvements** | ✅ Exists | **P1 - High** | Week 3-4 | Add regime status, backtest results tabs |
| **Paper Trading v2.0** | ⏸️ On Hold | **P2 - Medium** | Week 5-8 | Build comprehensive simulation BEFORE live launch |
| **Cloud Dashboard** | ❌ Not Built | **P2 - Medium** | Week 5-8 | Mobile monitoring (read-only) |
| **News Integration** | ❌ Not Built | **P3 - Low** | Month 3+ | MoneyControl/ET Now API for announcements |
| **4-Layer Confluence** | ❌ Not Built | **P3 - Low** | Month 3+ | Advanced intelligence, defer until MVP validated |

### 2.2 Architecture Decisions

**GUI Strategy:** Hybrid (Desktop + Cloud Dashboard)
- **Desktop App** (CustomTkinter): Full control, local execution, privacy ✅
- **Cloud Dashboard** (Streamlit): Read-only mobile monitoring, lightweight 🔄
- **Rationale:** Serves 90% of market, minimal cloud costs (₹0.70/user/month)

**Trading Execution:** Local (User's Computer)
- Credentials stay on user's machine ✅
- Fast, private, no monthly cloud costs ✅
- User can trade 24/7 by keeping desktop app running

**Data Strategy:** SQLite Local + Optional Cloud Sync
- Trade history stored locally (SQLite)
- Summary stats pushed to cloud dashboard every 5 minutes
- Privacy preserved, convenience gained

---

## 3. ARCHITECTURE OVERVIEW

### 3.1 Current State (What EXISTS)

```
ARUN Stock Bot - Current Implementation (v1.0 MVP)
═══════════════════════════════════════════════════════════

✅ COMPLETE Components:
├── Core Trading Engine (kickstart.py - 1,381 lines)
│   ├── RSI Mean Reversion Strategy ✅
│   ├── Risk Management Framework ✅
│   │   ├── Stop-loss detection ✅
│   │   ├── Profit target detection ✅
│   │   ├── Daily loss circuit breaker ✅
│   │   └── Position sizing (10% max per stock) ✅
│   ├── State Manager (crash recovery) ✅
│   └── Database Logging (SQLite) ✅
│
├── GUI Layer (1,590 lines total)
│   ├── Dashboard (kickstart_gui.py - 755 lines) ✅
│   │   └── Real-time P&L, positions, logs
│   └── Settings (settings_gui.py - 835 lines) ✅
│       └── Broker config, capital, risk limits, stock list
│
├── Configuration Management ✅
│   ├── settings.json (encrypted credentials) ✅
│   └── config_table.csv (stock symbols, RSI thresholds) ✅
│
└── Support Modules ✅
    ├── getRSI.py (TradingView-exact calculation) ✅
    ├── notifications.py (Email, Telegram) ✅
    └── symbol_validator.py (yfinance validation) ✅

⚠️ PARTIALLY IMPLEMENTED:
├── Regime Monitor
│   └── nifty50.py exists (just a symbol list, NOT a regime monitor)
│
└── Paper Trading Mode
    └── settings.json flag exists, NO implementation

❌ NOT IMPLEMENTED:
├── Backtesting Framework
├── Cloud Dashboard
├── News Integration
├── 4-Layer Confluence
├── Multi-Strategy Support (QGLP, Value, etc.)
└── Stop-Loss Auto-Execution (detection works, execution missing!)
```

### 3.2 Target State (After Implementation)

```
ARUN Stock Bot - Target Architecture (v1.5)
═══════════════════════════════════════════════════════════

User's Desktop                          Cloud Server (Lightweight)
┌──────────────────────────────┐       ┌──────────────────────────┐
│                              │       │                          │
│  🖥️  Desktop App             │       │  📱 Cloud Dashboard      │
│  ┌────────────────────────┐  │       │  (Streamlit)             │
│  │                        │  │       │                          │
│  │  Trading Engine        │  │ Push  │  ┌────────────────────┐  │
│  │  ┌──────────────────┐  │  │ Stats │  │ Portfolio Summary  │  │
│  │  │ Regime Monitor   │  │──┼───────┼─►│ Positions          │  │
│  │  │ (Nifty 50)       │  │  │       │  │ Recent Trades      │  │
│  │  └──────────────────┘  │  │       │  │ Risk Metrics       │  │
│  │  ┌──────────────────┐  │  │       │  └────────────────────┘  │
│  │  │ RSI Strategy     │  │  │       │                          │
│  │  │ + Risk Manager   │  │  │       │  📱 Access from mobile   │
│  │  └──────────────────┘  │  │       │  (READ-ONLY)             │
│  │  ┌──────────────────┐  │  │       └──────────────────────────┘
│  │  │ Backtest Engine  │  │  │
│  │  │ (Historical)     │  │  │
│  │  └──────────────────┘  │  │
│  └────────────────────────┘  │
│            ↓                 │
│  🖥️  GUI Dashboard           │
│  ┌────────────────────────┐  │
│  │ Tab 1: Live Trading    │  │
│  │ Tab 2: Backtest Results│  │
│  │ Tab 3: Regime Monitor  │  │
│  │ Tab 4: Settings        │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
            ↓
       Broker API (mstock)
```

---

## 4. PRIORITY IMPLEMENTATION ROADMAP

### Phase 1: Critical Foundation (Weeks 1-2) - P0

**Goal:** Build safety systems to prevent catastrophic losses

#### Task 1.1: Regime Monitor (3-4 days)

**File to Create:** `regime_monitor.py`

**Requirements:**
- Fetch Nifty 50 index data (^NSEI) via yfinance
- Calculate 50 DMA and 200 DMA
- Determine regime:
  - **BULLISH:** Price > 200 DMA AND 200 DMA slope positive → Trade normally
  - **BEARISH:** Price < 200 DMA AND 200 DMA slope negative → HALT trading
  - **SIDEWAYS:** Price near 200 DMA, weak trend → Reduce position sizes by 25%
  - **VOLATILE:** High volatility (>25% annualized) → Reduce sizes by 50%
  - **CRISIS:** Drawdown >15% OR Volatility >35% → EMERGENCY STOP
- Calculate ADX (Average Directional Index) for trend strength
- Cache results for 60 minutes (avoid API spam)
- Return:
  ```python
  {
      'regime': MarketRegime.BULLISH,
      'should_trade': True,
      'position_size_multiplier': 1.0,
      'confidence': 85,
      'reason': "Nifty above 200 DMA with positive slope (+2.3%)",
      'indicators': {...}
  }
  ```

**Integration:**
- Import in `kickstart.py`
- Check regime BEFORE any trading signal
- If `should_trade == False`, skip all symbols
- Adjust position sizes by `position_size_multiplier`

**Testing:**
- Backtest on 2020 COVID crash (should detect CRISIS)
- Backtest on 2022 bear market (should detect BEARISH)
- Verify in 2023 bull market (should detect BULLISH)

**Deliverable:** Regime monitor prevents trading in adverse markets, saves 30-70% losses

---

#### Task 1.2: Backtest Engine (4-5 days)

**File to Create:** `backtesting/backtest_engine.py`

**Requirements:**
- Run RSI strategy on historical data (3-5 years)
- Fetch OHLC data from yfinance (15-minute or daily candles)
- Simulate buy/sell signals based on RSI thresholds
- Calculate REALISTIC fees:
  - Brokerage: max(₹20, 0.03% of value)
  - STT: 0.1% on buy, 0.1% on sell
  - Exchange fees: 0.03%
  - GST: 18% on brokerage
  - SEBI turnover fee: 0.0001%
  - Stamp duty: 0.015% on buy
- Track all trades with entry/exit prices, hold duration, P&L
- Calculate performance metrics:
  - Total return %
  - Win rate (% of profitable trades)
  - Average win vs average loss
  - Profit factor (gross wins / gross losses)
  - Max drawdown (peak-to-valley)
  - Sharpe ratio (risk-adjusted returns)

**Output Format:**
```
═══════════════════════════════════════════════════════════════
              BACKTEST RESULTS: MICEL (2022-2025)
═══════════════════════════════════════════════════════════════
Starting Capital:        ₹50,000
Ending Capital:          ₹61,750
Total Return:            +23.5%
Annual Return (CAGR):    +7.3%

Total Trades:            37
Winning Trades:          24 (64.9%)
Losing Trades:           13 (35.1%)

Average Win:             +8.32%
Average Loss:            -4.21%
Profit Factor:           1.87

Max Drawdown:            -12.34%
Sharpe Ratio:            1.12

Total Fees Paid:         ₹1,250.50
Net Profit:              ₹11,750

✅ Strategy PASSES validation
   (Sharpe > 1.0, Max DD < 15%, Win Rate > 55%)

═══════════════════════════════════════════════════════════════

Trade-by-Trade Details:
1. MICEL | 2022-02-15 BUY @ ₹145.30 → 2022-02-28 SELL @ ₹159.80 | +9.98% (₹483.33) | 13 days | PROFIT_TARGET
2. MICEL | 2022-03-22 BUY @ ₹138.70 → 2022-03-24 SELL @ ₹131.76 | -5.00% (-₹231.33) | 2 days | STOP_LOSS
...
```

**Integration:**
- Add "Backtest" tab to desktop GUI
- User selects symbol, date range, parameters
- Click "Run Backtest" → Show results in GUI
- Export to CSV/PDF for documentation

**Testing:**
- Backtest MICEL and MOSCHIP (current symbols)
- Verify RSI calculation matches TradingView exactly
- Confirm fee calculations are realistic
- Test on both bull and bear market periods

**Deliverable:** Users can validate strategy BEFORE deploying real money

---

### Phase 2: GUI Enhancements (Weeks 3-4) - P1

#### Task 2.1: Add Regime Monitor Display (1-2 days)

**File to Modify:** `kickstart_gui.py`

**Requirements:**
- Add "Market Regime" card to dashboard
- Show current regime with color coding:
  - 🟢 BULLISH (green)
  - 🔴 BEARISH (red)
  - 🟡 SIDEWAYS (yellow)
  - 🟣 VOLATILE (purple)
  - ⚫ CRISIS (black)
- Display confidence %, reason, and key indicators (price vs 200 DMA, ADX)
- Update every 60 minutes (same as regime cache)

**Visual Mock:**
```
╔═══════════════════════════════════════════════════════╗
║            📊 Market Regime Monitor                   ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Current Regime:  🟢 BULLISH                          ║
║  Confidence:      85%                                 ║
║  Trading Status:  ✅ ACTIVE (Full position sizes)     ║
║                                                       ║
║  Nifty 50:        21,750 (Above 200 DMA: 20,900)     ║
║  Trend Strength:  ADX 32.5 (Strong trend)            ║
║  Volatility:      18.2% (Normal)                     ║
║                                                       ║
║  Reason: Nifty above 200 DMA with positive slope     ║
║          (+2.3%). Strong uptrend confirmed.          ║
║                                                       ║
║  Last Updated:    2026-01-17 14:30:00                ║
╚═══════════════════════════════════════════════════════╝
```

**Edge Cases:**
- If regime changes from BULLISH → BEARISH, show alert notification
- If CRISIS detected, show EMERGENCY STOP message

---

#### Task 2.2: Add Backtest Results Tab (2-3 days)

**File to Modify:** `kickstart_gui.py`

**Requirements:**
- New tab in main window: "Backtesting"
- Form to configure backtest:
  - Symbol (dropdown from config_table.csv)
  - Start Date (date picker)
  - End Date (date picker)
  - Buy RSI (number input, default 35)
  - Sell RSI (number input, default 65)
  - Profit Target % (number input, default 10)
  - Stop Loss % (number input, default 5)
- "Run Backtest" button
- Results display:
  - Summary metrics (total return, win rate, Sharpe ratio)
  - Trade list (scrollable table)
  - Equity curve chart (optional, using matplotlib)
- "Export to CSV" button

**Integration:**
- Call `backtest_engine.run_backtest()` when button clicked
- Show loading spinner during backtest (can take 30-60 seconds)
- Display results in formatted text + table
- Save results to `backtests/` folder for future reference

---

### Phase 3: Paper Trading v2.0 (Weeks 5-8) - P2

#### Task 3.1: Build Paper Trading Engine (3-4 days)

**File to Create:** `paper_trading/paper_engine.py`

**Requirements:**
- Intercept order execution when `paper_trading_mode == True`
- Simulate order execution with realistic slippage:
  - BUY: Execute 0.05-0.15% above current LTP
  - SELL: Execute 0.05-0.15% below current LTP
- Calculate same fees as live trading
- Log to separate `paper_trades` database table
- Track paper capital separately (virtual ₹50,000)
- Generate comparison report: Paper vs Backtest performance

**Integration:**
- Modify `kickstart.py` to check `paper_trading_mode` before calling broker API
- If paper mode:
  - Skip real API call
  - Call `paper_engine.execute_trade()` instead
  - Log to paper database
  - Update paper capital (NOT real balance)

**Safety:**
- Add prominent "PAPER MODE" indicator to GUI
- Show paper capital in different color (orange)
- Require user confirmation to switch to live mode

---

#### Task 3.2: Readiness Checklist (1-2 days)

**File to Create:** `readiness_checker.py`

**Requirements:**
- Before user can switch from paper → live, validate:
  - ✅ Backtest ran successfully (Sharpe > 1.0, Max DD < 15%)
  - ✅ Paper trading ran for 30+ days
  - ✅ Paper performance within 20% of backtest
  - ✅ No catastrophic errors in logs
  - ✅ Regime monitor configured
  - ✅ Risk limits set (stop-loss, profit target)
  - ✅ Notifications configured
  - ✅ User read disclaimers
- Display checklist in GUI with progress bar
- Block "Start Live Trading" button until 100% pass

**Output:**
```
╔══════════════════════════════════════════════════════╗
║     LIVE TRADING READINESS CHECKLIST                 ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  BACKTESTING:                      [████████] 100%   ║
║  ✅ Ran 3-year backtest                              ║
║  ✅ Sharpe ratio > 1.0 (1.12)                        ║
║  ✅ Max drawdown < 15% (12.34%)                      ║
║  ✅ Win rate > 55% (64.9%)                           ║
║                                                      ║
║  PAPER TRADING:                    [████████] 100%   ║
║  ✅ Ran for 30+ days (45 days)                       ║
║  ✅ Performance matches backtest (within 15%)        ║
║  ✅ No catastrophic errors                           ║
║                                                      ║
║  CONFIGURATION:                    [███████░] 87%    ║
║  ✅ Risk limits configured                           ║
║  ✅ Regime monitor enabled                           ║
║  ✅ Notifications configured                         ║
║  ❌ Practiced manual intervention (REQUIRED)         ║
║                                                      ║
║  OVERALL READINESS:                [███████░] 92%    ║
║                                                      ║
║  ⚠️  You are NOT ready for live trading yet.        ║
║      Complete: Manual intervention practice          ║
║                                                      ║
║  [CONTINUE PAPER TRADING]   [SKIP (RISKY)]          ║
╚══════════════════════════════════════════════════════╝
```

---

### Phase 4: Cloud Dashboard (Weeks 5-8, Parallel with Phase 3) - P2

#### Task 4.1: Build Cloud Sync API (2 days)

**File to Create:** `cloud_sync/dashboard_sync.py`

**Requirements:**
- Push summary stats to cloud API every 5 minutes
- Data to sync:
  ```python
  {
      'user_token': 'abc123xyz',  # Unique per user
      'timestamp': '2026-01-17T14:30:00',
      'portfolio_value': 52150.00,
      'total_pnl': 2150.00,
      'total_pnl_pct': 4.3,
      'today_pnl': 450.00,
      'open_positions': [
          {'symbol': 'MICEL', 'qty': 10, 'entry': 145.30, 'ltp': 159.80, 'pnl': 145.00},
          ...
      ],
      'recent_trades': [
          {'date': '2026-01-15', 'symbol': 'INFY', 'action': 'BUY', 'qty': 5, 'price': 1520.00},
          ...
      ],
      'regime_status': {
          'regime': 'BULLISH',
          'confidence': 85,
          'reason': '...'
      },
      'bot_status': 'RUNNING'
  }
  ```
- Handle network failures gracefully (silent skip, don't interrupt trading)
- Encrypt data in transit (HTTPS)

**Cloud API Endpoint:**
```
POST https://api.arunbot.com/dashboard/update
Headers: Authorization: Bearer {user_token}
Body: JSON (stats above)
```

---

#### Task 4.2: Build Streamlit Dashboard (3 days)

**File to Create:** `cloud_dashboard/streamlit_app.py`

**Requirements:**
- Simple authentication (user token input)
- Fetch stats from cloud API
- Display:
  - Portfolio value, P&L (total and today)
  - Regime status with color coding
  - Open positions table
  - Recent trades table
  - Bot status (RUNNING / STOPPED)
- Auto-refresh every 60 seconds
- Mobile-responsive design
- READ-ONLY (no trading controls)

**Deployment:**
- Host on Streamlit Cloud (FREE for public, ₹500/month for private)
- Domain: `https://dashboard.arunbot.com`
- SSL certificate (Let's Encrypt FREE)

**User Access:**
```
1. User opens mobile browser
2. Goes to dashboard.arunbot.com
3. Enters personal token (generated in desktop app)
4. Views portfolio, positions, trades
5. Cannot start/stop bot or change settings (must use desktop)
```

---

## 5. COMPONENT SPECIFICATIONS

### 5.1 Regime Monitor - Complete Spec

**File:** `regime_monitor.py`

**Class:** `RegimeMonitor`

**Methods:**

```python
class RegimeMonitor:
    def __init__(self, index_symbol="^NSEI", cache_duration_minutes=60):
        """
        Initialize regime monitor

        Args:
            index_symbol: Yahoo Finance symbol for Nifty 50 (^NSEI)
            cache_duration_minutes: How long to cache regime before recalculating
        """

    def get_market_regime(self) -> dict:
        """
        Get current market regime

        Returns:
            {
                'regime': MarketRegime (enum: BULLISH/BEARISH/SIDEWAYS/VOLATILE/CRISIS),
                'should_trade': bool,
                'position_size_multiplier': float (0.0-1.0),
                'confidence': int (0-100),
                'reason': str,
                'indicators': {
                    'price': float,
                    'sma_50': float,
                    'sma_200': float,
                    'price_vs_200dma': str ('ABOVE'/'BELOW'),
                    'sma_200_slope': float (% change),
                    'volatility_20d': float (% annualized),
                    'adx': float (0-100),
                    'drawdown_from_peak': float (%)
                },
                'timestamp': datetime
            }
        """

    def _fetch_index_data(self) -> pd.DataFrame:
        """Fetch 1 year of Nifty 50 daily data via yfinance"""

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate all regime indicators (MA, volatility, ADX, drawdown)"""

    def _determine_regime(self, indicators: dict) -> dict:
        """
        Determine regime using decision tree:

        1. CRISIS: Drawdown > -15% OR Volatility > 35%
           → should_trade=False, multiplier=0.0

        2. BEARISH: Price < 200 DMA AND 200 DMA slope < 0
           → should_trade=False, multiplier=0.0

        3. VOLATILE: ADX < 20 AND Volatility > 25%
           → should_trade=True, multiplier=0.5

        4. SIDEWAYS: ADX < 25 AND |Drawdown| < 5%
           → should_trade=True, multiplier=0.75

        5. BULLISH: Price > 200 DMA AND 200 DMA slope > 0
           → should_trade=True, multiplier=1.0
        """

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index (trend strength indicator)"""

    def _is_cache_valid(self) -> bool:
        """Check if cached regime is still valid (within cache duration)"""
```

**Decision Logic Flow Chart:**

```
Start
  ↓
Fetch Nifty 50 data (1 year, daily)
  ↓
Calculate Indicators:
  - 50 DMA, 200 DMA
  - 200 DMA slope (% change over 50 days)
  - Volatility (20-day, annualized)
  - ADX (trend strength)
  - Drawdown from peak
  ↓
Check CRISIS?
  → Drawdown < -15% OR Volatility > 35%
     YES → Return CRISIS (HALT ALL TRADING)
     NO → Continue
  ↓
Check BEARISH?
  → Price < 200 DMA AND 200 DMA slope < 0
     YES → Return BEARISH (HALT ALL TRADING)
     NO → Continue
  ↓
Check VOLATILE?
  → ADX < 20 AND Volatility > 25%
     YES → Return VOLATILE (Trade with 50% position sizes)
     NO → Continue
  ↓
Check SIDEWAYS?
  → ADX < 25 AND |Drawdown| < 5%
     YES → Return SIDEWAYS (Trade with 75% position sizes)
     NO → Continue
  ↓
Default → Return BULLISH (Trade normally, 100% position sizes)
```

**Testing Scenarios:**

| Scenario | Expected Regime | Validation Method |
|----------|----------------|-------------------|
| 2020 March COVID Crash | CRISIS | Nifty dropped -38%, volatility >40% |
| 2022 Bear Market | BEARISH | Nifty below 200 DMA for 6+ months |
| 2023 Bull Rally | BULLISH | Nifty above 200 DMA, ADX >25 |
| 2024 Sideways Range | SIDEWAYS | Nifty oscillating ±3% around 200 DMA |

---

### 5.2 Backtest Engine - Complete Spec

**File:** `backtesting/backtest_engine.py`

**Class:** `BacktestEngine`

**Methods:**

```python
class BacktestEngine:
    def __init__(self, initial_capital=50000, stop_loss_pct=5, profit_target_pct=10):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital in INR
            stop_loss_pct: Stop-loss percentage (default 5%)
            profit_target_pct: Profit target percentage (default 10%)
        """

    def run_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        buy_rsi: int = 35,
        sell_rsi: int = 65,
        timeframe: str = '1d'  # '15m' or '1d'
    ) -> dict:
        """
        Run backtest on symbol

        Args:
            symbol: Stock symbol (e.g., 'MICEL')
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            buy_rsi: RSI threshold for buy (default 35)
            sell_rsi: RSI threshold for sell (default 65)
            timeframe: Candle interval ('1d' or '15m')

        Returns:
            {
                'symbol': str,
                'start_date': str,
                'end_date': str,
                'initial_capital': float,
                'final_capital': float,
                'total_return_pct': float,
                'annual_return_cagr': float,
                'num_trades': int,
                'winning_trades': int,
                'losing_trades': int,
                'win_rate': float,
                'avg_win': float,
                'avg_loss': float,
                'profit_factor': float,
                'max_drawdown': float,
                'sharpe_ratio': float,
                'total_fees_paid': float,
                'net_profit': float,
                'trades': List[Trade],
                'equity_curve': List[float],
                'validation_passed': bool
            }
        """

    def calculate_metrics(self, trades: List[Trade], final_capital: float) -> dict:
        """
        Calculate performance metrics from trades

        Returns:
            Dictionary with win rate, profit factor, Sharpe, max drawdown, etc.
        """

    def calculate_fees(self, gross_value: float, action: str) -> float:
        """
        Calculate realistic trading fees

        BUY Fees:
            - Brokerage: max(₹20, 0.03% of value)
            - STT: 0.1%
            - Exchange: 0.03%
            - GST: 18% on brokerage
            - Stamp duty: 0.015%

        SELL Fees:
            - Brokerage: max(₹20, 0.03% of value)
            - STT: 0.1%
            - Exchange: 0.03%
            - SEBI: 0.0001%
            - GST: 18% on brokerage

        Returns:
            Total fees in INR
        """

    def validate_strategy(self, metrics: dict) -> bool:
        """
        Validate if strategy passes minimum requirements

        Criteria:
            - Sharpe ratio > 1.0
            - Max drawdown < 15%
            - Win rate > 55%
            - Profit factor > 1.5

        Returns:
            True if all criteria pass, False otherwise
        """

    def print_report(self, results: dict):
        """Print formatted backtest report to console"""

    def export_to_csv(self, results: dict, filepath: str):
        """Export backtest results to CSV file"""
```

**Fee Calculation Details:**

```python
def calculate_fees(gross_value: float, action: str) -> float:
    """
    Example for ₹10,000 trade:

    BUY:
        Brokerage: max(₹20, 10000 * 0.0003) = ₹30
        STT: 10000 * 0.001 = ₹10
        Exchange: 10000 * 0.0003 = ₹3
        GST: 30 * 0.18 = ₹5.40
        Stamp Duty: 10000 * 0.00015 = ₹1.50

        Total BUY fees: ₹49.90 (0.50%)

    SELL:
        Brokerage: ₹30
        STT: ₹10
        Exchange: ₹3
        SEBI: 10000 * 0.000001 = ₹0.01
        GST: ₹5.40

        Total SELL fees: ₹48.41 (0.48%)

    ROUND-TRIP (Buy + Sell): ₹98.31 (0.98%)
    """

    brokerage = max(20, gross_value * 0.0003)

    if action == "BUY":
        stt = gross_value * 0.001
        exchange = gross_value * 0.0003
        gst = brokerage * 0.18
        stamp = gross_value * 0.00015
        return brokerage + stt + exchange + gst + stamp

    else:  # SELL
        stt = gross_value * 0.001
        exchange = gross_value * 0.0003
        sebi = gross_value * 0.000001
        gst = brokerage * 0.18
        return brokerage + stt + exchange + sebi + gst
```

---

## 6. DO NOT BUILD (Defer/Delete)

### 6.1 Features to DEFER (Build Later)

**DO NOT implement these until MVP is validated and profitable:**

1. ❌ **Multi-Strategy Support** (QGLP, Value, Magic Formula)
   - Reason: RSI strategy must prove profitable first
   - Defer to: Month 6+ (after 1,000 users)

2. ❌ **4-Layer Confluence Engine**
   - Reason: Complex, time-consuming, unproven value
   - Defer to: Month 6+ (if users request)

3. ❌ **Native Mobile App** (iOS/Android)
   - Reason: Expensive (3-6 months), cloud dashboard suffices
   - Defer to: Year 2 (after ₹50L+ ARR)

4. ❌ **News Integration** (MoneyControl API)
   - Reason: Nice-to-have, not essential for MVP
   - Defer to: Month 3+ (if critical news events occur)

5. ❌ **Social Features** (Share portfolio, leaderboards)
   - Reason: Not core value, distraction
   - Defer to: Year 2+ (if community grows)

6. ❌ **Multi-Broker Support** (Zerodha, Upstox)
   - Reason: Complexity, stick to mstock for MVP
   - Defer to: Month 6+ (if users demand)

### 6.2 Files/Folders to REORGANIZE (Not Delete)

**Crypto Reference Docs:**
- ✅ Move to `Documentation/Reference/CryptoBot_Intelligence_Inspiration/`
- ✅ Add README explaining purpose (architectural inspiration only)
- ✅ Keep for reference when building intelligence layer later
- ❌ DO NOT implement crypto trading functionality

**Files to Move:**
```bash
mv Documentation/REFERENCE_*.md Documentation/Reference/CryptoBot_Intelligence_Inspiration/
mv Documentation/cryptobot_investment_analysis.md Documentation/Reference/CryptoBot_Intelligence_Inspiration/
```

### 6.3 Code to FIX (Not Delete)

**Stop-Loss Auto-Execution:**
- **Current:** Detection works, but does NOT execute sell order
- **Fix:** Wire `risk_manager.py` alerts to actual order execution in `kickstart.py`
- **Priority:** P1 (Critical safety issue)

**Paper Trading Flag:**
- **Current:** Flag exists in settings.json, but NO implementation
- **Fix:** Build full paper trading engine (Phase 3)
- **DO NOT:**  Leave half-implemented (dangerous illusion of safety)

---

## 7. SUCCESS CRITERIA

### 7.1 Phase 1 Success Criteria (Weeks 1-2)

**Regime Monitor:**
- ✅ Correctly identifies BULLISH regime in current market (2026 Jan)
- ✅ Would have detected 2020 COVID crash as CRISIS
- ✅ Would have detected 2022 bear market as BEARISH
- ✅ Halts trading when `should_trade == False`
- ✅ Updates regime status in GUI every 60 minutes

**Backtest Engine:**
- ✅ Backtests MICEL on 2022-2025 data in < 60 seconds
- ✅ Results match manual calculation (within 1%)
- ✅ Fee calculations are realistic (0.98% round-trip)
- ✅ Generates formatted report with all metrics
- ✅ Exports results to CSV

### 7.2 Phase 2 Success Criteria (Weeks 3-4)

**GUI Enhancements:**
- ✅ Regime monitor card displays current status with color coding
- ✅ Backtest tab allows user to run backtests on any symbol
- ✅ Results display in formatted table
- ✅ No crashes or UI glitches

### 7.3 Phase 3 Success Criteria (Weeks 5-8)

**Paper Trading v2.0:**
- ✅ Paper mode executes simulated trades (NO real API calls)
- ✅ Paper capital tracked separately from real balance
- ✅ Slippage simulation is realistic (0.05-0.15%)
- ✅ Paper performance can be compared to backtest
- ✅ Readiness checklist validates all criteria before live mode

**Cloud Dashboard:**
- ✅ Desktop app pushes stats to cloud every 5 minutes
- ✅ Mobile browser displays dashboard (read-only)
- ✅ Authentication works (user token)
- ✅ Auto-refreshes every 60 seconds
- ✅ Mobile-responsive design

### 7.4 Overall MVP Success Criteria (End of Week 8)

**Before Public Launch:**
- ✅ Regime monitor operational and tested
- ✅ Backtest engine shows strategy is profitable (Sharpe > 1.0)
- ✅ Paper trading runs for 30+ days with positive results
- ✅ Stop-loss auto-execution works (critical safety fix)
- ✅ Cloud dashboard accessible from mobile
- ✅ All documentation updated (README, Getting Started, Troubleshooting)
- ✅ 10 beta users test successfully for 2 weeks
- ✅ Zero critical bugs in logs

---

## 8. TECHNICAL CONSTRAINTS

### 8.1 Language & Frameworks

- **Python 3.9+** (current codebase)
- **Desktop GUI:** CustomTkinter (continue using)
- **Cloud Dashboard:** Streamlit (new)
- **Database:** SQLite (local), PostgreSQL (cloud - optional)
- **Data Source:** yfinance (Yahoo Finance)
- **Broker API:** mstock (Indian broker)

### 8.2 Performance Requirements

- **Regime Monitor:** Update every 60 minutes, < 5 seconds calculation time
- **Backtest Engine:** 3 years of daily data in < 60 seconds
- **GUI Responsiveness:** < 100ms for button clicks, < 1s for data refresh
- **Cloud Sync:** Push stats every 5 minutes, < 2 seconds API call

### 8.3 Security Constraints

- **Credentials:** NEVER send to cloud (local encryption only)
- **Cloud Dashboard:** Read-only access (NO trading controls)
- **API Communication:** HTTPS only, token-based authentication
- **Data Privacy:** Minimal data synced (summary stats only, not trade details)

### 8.4 Cost Constraints

- **Cloud Hosting:** < ₹1,000/month total (for all users combined)
- **Per-User Cost:** < ₹1/user/month
- **Target:** Achieve profitability at ₹2,999/month subscription

---

## 9. DELIVERABLES CHECKLIST

### Week 1-2 Deliverables:
- [ ] `regime_monitor.py` created and tested
- [ ] `backtesting/backtest_engine.py` created and tested
- [ ] Integration of regime monitor into `kickstart.py`
- [ ] Stop-loss auto-execution fixed
- [ ] Documentation updated (AI_AGENT_HANDOVER.md, README.md)

### Week 3-4 Deliverables:
- [ ] Regime monitor card added to GUI
- [ ] Backtest tab added to GUI
- [ ] Backtest results export to CSV working
- [ ] User can run backtests on any symbol from GUI

### Week 5-8 Deliverables:
- [ ] `paper_trading/paper_engine.py` created
- [ ] Paper mode fully functional (no real trades)
- [ ] `readiness_checker.py` validates live trading prerequisites
- [ ] `cloud_sync/dashboard_sync.py` pushes stats to cloud
- [ ] `cloud_dashboard/streamlit_app.py` deployed and accessible
- [ ] Mobile dashboard tested on iOS and Android browsers

### Final Deliverables (End of Week 8):
- [ ] All tests passing (regime, backtest, paper trading)
- [ ] 10 beta users successfully trading for 2+ weeks
- [ ] Zero critical bugs
- [ ] Documentation complete (Getting Started, Troubleshooting, FAQ)
- [ ] Cloud dashboard operational at dashboard.arunbot.com
- [ ] Ready for public launch

---

## 10. CONTACT & ESCALATION

**For Questions/Clarifications:**
- Strategic decisions: Escalate to Product Owner (Arun)
- Technical implementation: AI Agent autonomous
- Architecture changes: Discuss before implementing

**Progress Reporting:**
- Daily: Commit code with descriptive messages
- Weekly: Update this document with progress notes
- Blockers: Flag immediately, don't wait

---

**Document Version:** 1.0
**Last Updated:** January 17, 2026
**Next Review:** End of Week 2 (after Phase 1 completion)

**Status:** ✅ READY FOR IMPLEMENTATION

---
