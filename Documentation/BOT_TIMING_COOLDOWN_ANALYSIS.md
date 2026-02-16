# Bot Timing and Cooldown Analysis

**Date**: February 16, 2026
**Issue**: Why bots aren't running 24/7 with 15-minute cooldowns after trades

---

## Current Bot Timing Architecture

### 1. Main Loop Cycle Frequency

**Code Location**: `kickstart.py:2809-2921` (`main_loop()`)

```python
def main_loop():
    while not STOP_REQUESTED:
        run_cycle()  # Run trading cycle

        # Sleep 0.5 seconds between cycles
        for _ in range(5):  # 0.5s total (5 x 0.1s)
            if STOP_REQUESTED: break
            time.sleep(0.1)
```

**Current Behavior**:
- Bot cycles every **0.5 seconds** (2 times per second)
- This is **HARDCODED** in the main loop
- No cooldown after trades
- Runs continuously as long as market is "open"

### 2. Engine Beat Setting (IGNORED)

**Code Location**: `kickstart.py:451`

```python
ENGINE_BEAT_SECONDS = float(settings.get("app_settings.engine_beat_seconds", 2.0))
log_ok(f"💓 Engine Beat Frequency: {ENGINE_BEAT_SECONDS}s")
```

**Settings Files**:
- `settings_default.json:120`: `"engine_beat_seconds": 2`
- `settings_new_test.json:118`: `"engine_beat_seconds": 2`

**CRITICAL BUG**:
- Setting is loaded and logged ✅
- But **NEVER USED** in the main loop ❌
- Main loop uses hardcoded `time.sleep(0.1)` loops instead
- This is a configuration desync issue

### 3. Market Hours Restriction

**Code Location**: `kickstart.py:1663-1678` (`is_market_open_now_ist()`)

```python
def is_market_open_now_ist() -> bool:
    # 24/7 Override for Testing (ONLY if configured)
    if settings and settings.get("app_settings.paper_trading_mode", False):
        return True  # ← Paper mode: Always open

    # Live mode: Only during market hours
    now = now_ist()
    t = now.time()

    # Weekends
    if now.weekday() >= 5:  # Sat or Sun
        return False

    start_time = dtime(9, 15)   # 9:15 AM IST
    end_time = dtime(15, 30)     # 3:30 PM IST

    return start_time <= t <= end_time
```

**Impact**:
- **Paper Mode**: Bot runs 24/7 (ignores market hours)
- **Live Mode**: Bot only runs Mon-Fri, 9:15 AM - 3:30 PM IST
- Outside market hours: Bot waits silently (no logging, no activity)

### 4. Market Closed Waiting Logic

**Code Location**: `kickstart.py:1708-1731` (`wait_for_market_open()`)

```python
def wait_for_market_open():
    global LOG_SUPPRESS
    try:
        LOG_SUPPRESS = True
        while not is_market_open_now_ist():
            if is_market_open_now_ist():
                break
            time.sleep(1)  # ← Wakes up every 1 second to check
        log_ok("\n🟢 Market open — resuming", flush=True, force=True)
    finally:
        LOG_SUPPRESS = False
```

**Behavior When Market Closed**:
- Suppresses all logging
- Checks every 1 second if market opened
- Resumes trading when market opens
- **Does NOT exit** - stays running 24/7 in waiting mode

---

## Current Cooldown Mechanisms

### 1. No Post-Trade Cooldown

**Search Results**: NO cooldown logic exists after successful trades

**What This Means**:
- After BUY order succeeds: Bot **immediately** starts next cycle (0.5s later)
- After SELL order succeeds: Bot **immediately** starts next cycle (0.5s later)
- Could potentially buy same symbol multiple times in rapid succession
- No rate limiting on order placement

### 2. RMS Cooldown (v2.5.0)

**Code Location**: `kickstart.py:1256-1276` (documented in CHANGELOG)

```python
# 1-hour cooldown for "Insufficient Quantity" RMS errors
if "Insufficient Quantity" in error:
    LAST_RMS_ERROR_TIME = time.time()
    # Block selling for 1 hour
```

**Applies To**:
- Only "Insufficient Quantity" errors
- Only blocks SELL operations
- Duration: 1 hour
- Does NOT affect buy operations

### 3. API Rate Limiting (Minimal)

**Code Locations**:
- `scanner_engine.py:318`: `time.sleep(1.0)` between batches
- `scanner_engine.py:354`: `time.sleep(0.2)` between direct requests
- `settings_gui.py:826`: `time.sleep(0.5)` during validation
- `BOT Scrapper/market_scanner_full.py:484`: `time.sleep(0.1)` for Yahoo Finance

**Trading Engine**: **NO API rate limiting** exists

---

## Why Bot Doesn't Run 24/7 with Cooldowns

### Problem 1: Market Hours Hard Stop (Live Mode)

**Code**: `is_market_open_now_ist()` returns `False` outside 9:15-15:30 IST

**Why It Exists**:
- Indian stock market (NSE/BSE) is physically closed outside these hours
- No trading possible after 3:30 PM
- No market data available (APIs return stale data)
- Order placement would fail with "Market Closed" errors

**What Happens**:
- Bot calls `wait_for_market_open()`
- Sits idle checking every 1 second
- Resumes at 9:15 AM next trading day
- **Technically runs 24/7**, but does nothing outside market hours

### Problem 2: No Post-Trade Cooldown

**User Expectation**: 15-minute cooldown after successful buy/sell

**Current Reality**: 0.5-second cycle frequency (no cooldown)

**Risk**:
```
9:15:00 - Buy RELIANCE @ ₹2500
9:15:01 - Check RELIANCE again (RSI still low)
9:15:02 - Buy RELIANCE again @ ₹2502 ← DUPLICATE BUY
9:15:03 - Buy RELIANCE again @ ₹2505 ← DUPLICATE BUY
```

**Current Protection**:
- `check_existing_orders()` (kickstart.py:1193-1210) prevents duplicate buys
- Only checks if order already exists for that symbol
- Does NOT implement time-based cooldown

### Problem 3: Engine Beat Setting Ignored

**Expected**: `"engine_beat_seconds": 2` should control cycle frequency

**Actual**: Hardcoded 0.5 seconds in main loop

**Impact**: Cannot control bot speed via configuration

---

## Technical Constraints: Why 24/7 Trading is Limited

### Indian Stock Market Hours
- **NSE/BSE**: 9:15 AM - 3:30 PM IST (Mon-Fri)
- **After-Hours Trading**: Not available for retail traders
- **Pre-Market**: 9:00 AM - 9:15 AM (only for price discovery, limited volume)

### API Availability
- **mStock OHLC API**: Returns stale data outside market hours
- **Order Placement API**: Rejects orders outside market hours
- **Position API**: Works 24/7 (can check holdings anytime)
- **Login API**: Works 24/7

### What CAN Be Done 24/7
1. ✅ Monitor existing positions
2. ✅ Calculate P&L
3. ✅ Prepare watchlists
4. ✅ Run technical analysis on historical data
5. ✅ Send notifications
6. ✅ Update dashboards

### What CANNOT Be Done Outside Market Hours
1. ❌ Place buy/sell orders
2. ❌ Get real-time price quotes
3. ❌ Execute trades
4. ❌ Get live RSI (based on real-time data)

---

## Recommended Solutions

### Solution 1: Implement Post-Trade Cooldown (HIGH PRIORITY)

**Goal**: 15-minute cooldown after each successful trade (per symbol)

**Implementation**:

```python
# Global state for cooldowns
TRADE_COOLDOWNS = {}  # {symbol: timestamp_of_last_trade}
COOLDOWN_MINUTES = 15

def is_symbol_in_cooldown(symbol):
    """Check if symbol is still in cooldown period"""
    if symbol not in TRADE_COOLDOWNS:
        return False

    last_trade_time = TRADE_COOLDOWNS[symbol]
    elapsed = time.time() - last_trade_time
    cooldown_seconds = COOLDOWN_MINUTES * 60

    if elapsed < cooldown_seconds:
        remaining = cooldown_seconds - elapsed
        log_ok(f"⏳ {symbol} in cooldown ({remaining/60:.1f} min remaining)")
        return True
    else:
        # Cooldown expired, remove entry
        del TRADE_COOLDOWNS[symbol]
        return False

def place_order_mstock(symbol, side, qty, price=0, exchange="NSE"):
    # Check cooldown BEFORE placing order
    if is_symbol_in_cooldown(symbol):
        log_ok(f"❌ {symbol} skipped - in 15-min cooldown")
        return False

    # ... existing order placement logic ...

    # After SUCCESSFUL trade, set cooldown
    if order_success:
        TRADE_COOLDOWNS[symbol] = time.time()
        log_ok(f"✅ Trade successful - {symbol} cooldown started (15 min)")

    return order_success
```

**Benefits**:
- Prevents rapid-fire duplicate trades
- Gives price time to move after position entry
- Reduces API calls and broker fees
- More realistic trading behavior

**File Location**: Add to `kickstart.py` near `place_order_mstock()` (line 2304)

### Solution 2: Honor Engine Beat Setting (MEDIUM PRIORITY)

**Goal**: Use `engine_beat_seconds` from settings instead of hardcoded 0.5s

**Current Code** (`kickstart.py:2914-2917`):
```python
# Hardcoded 0.5s sleep
for _ in range(5):  # 0.5s total
    if STOP_REQUESTED: break
    time.sleep(0.1)
```

**Fixed Code**:
```python
# Use configurable ENGINE_BEAT_SECONDS (loaded at line 451)
sleep_chunks = int(ENGINE_BEAT_SECONDS * 10)  # 10 chunks per second
for _ in range(sleep_chunks):
    if STOP_REQUESTED: break
    time.sleep(0.1)
```

**Example**:
- If `"engine_beat_seconds": 2.0` → sleeps 2 seconds between cycles
- If `"engine_beat_seconds": 5.0` → sleeps 5 seconds between cycles
- If `"engine_beat_seconds": 0.5` → sleeps 0.5 seconds (current behavior)

**Benefits**:
- Configuration actually works
- Users can tune bot speed
- Can slow down for conservative trading
- Can speed up for high-frequency testing

**File Location**: `kickstart.py:2914-2917`

### Solution 3: 24/7 Monitoring Mode (OPTIONAL)

**Goal**: Bot runs 24/7 but only trades during market hours

**Current Behavior**: Already does this! Bot waits during closed hours.

**Enhancement**: Add activity during off-hours

```python
def main_loop():
    while not STOP_REQUESTED:
        if is_market_open_now_ist():
            # TRADING MODE (current behavior)
            run_cycle()
            sleep(ENGINE_BEAT_SECONDS)
        else:
            # OFF-HOURS MODE (new)
            run_maintenance_tasks()
            time.sleep(60)  # Check every minute

def run_maintenance_tasks():
    """Activities to do outside market hours"""
    try:
        # 1. Update P&L for existing positions
        update_pnl_calculations()

        # 2. Prepare watchlist for next day
        prepare_tomorrow_watchlist()

        # 3. Clean up expired cooldowns
        cleanup_cooldowns()

        # 4. Send end-of-day summary
        if datetime.now(ist).hour == 16:  # 4 PM
            send_daily_summary()

        log_ok("🌙 Maintenance tasks completed")
    except Exception as e:
        log_ok(f"⚠️ Maintenance error: {e}")
```

**Benefits**:
- Bot stays active 24/7
- Useful monitoring and prep work
- Positions tracked continuously
- Ready to trade when market opens

**File Location**: `kickstart.py:2809` (main_loop modification)

### Solution 4: Symbol-Specific Cooldowns (ADVANCED)

**Goal**: Different cooldowns for different symbols/strategies

**Configuration** (`settings.json`):
```json
{
  "strategies": {
    "rsi_mean_reversion": {
      "name": "RSI Mean Reversion",
      "enabled": true,
      "cooldown_minutes": 15  // ← NEW
    },
    "qglp_filter": {
      "name": "QGLP Quality Filter",
      "enabled": false,
      "cooldown_minutes": 1440  // ← 24 hours (long-term holds)
    }
  }
}
```

**Implementation**:
```python
STRATEGY_COOLDOWNS = {
    # (symbol, strategy): timestamp
}

def get_cooldown_for_strategy(strategy_name):
    """Get cooldown minutes for a strategy"""
    if not settings:
        return 15  # Default fallback

    strategy_path = f"strategies.{strategy_name}.cooldown_minutes"
    return settings.get(strategy_path, 15)

def is_symbol_strategy_in_cooldown(symbol, strategy):
    """Check cooldown for symbol+strategy combo"""
    key = (symbol, strategy)
    if key not in STRATEGY_COOLDOWNS:
        return False

    cooldown_min = get_cooldown_for_strategy(strategy)
    elapsed = time.time() - STRATEGY_COOLDOWNS[key]

    return elapsed < (cooldown_min * 60)
```

**Benefits**:
- Intraday strategies: Short cooldown (15 min)
- Swing strategies: Long cooldown (24+ hours)
- Prevents strategy interference
- More professional trade management

---

## Implementation Priority

### P0 (Must Have) - Immediate Implementation

**1. Post-Trade Cooldown (15 minutes)**
- **Impact**: Prevents duplicate trades, improves capital efficiency
- **Effort**: 30 minutes coding + testing
- **File**: `kickstart.py` (add cooldown logic to `place_order_mstock()`)

**2. Honor Engine Beat Setting**
- **Impact**: Makes configuration actually work
- **Effort**: 10 minutes (1 line change)
- **File**: `kickstart.py:2914-2917`

### P1 (Should Have) - Next Sprint

**3. Symbol-Specific Cooldowns**
- **Impact**: Better multi-strategy support
- **Effort**: 1-2 hours
- **Files**: `kickstart.py`, `settings_default.json`

**4. Cooldown Dashboard Display**
- **Impact**: User visibility into when symbols can be traded again
- **Effort**: 2 hours
- **File**: `sensei_v1_dashboard.py`

### P2 (Nice to Have) - Future

**5. 24/7 Maintenance Mode**
- **Impact**: Better use of off-hours time
- **Effort**: 4-6 hours
- **File**: `kickstart.py` (new `run_maintenance_tasks()`)

**6. Dynamic Cooldown Adjustment**
- **Impact**: Adapt cooldown based on market volatility
- **Effort**: 8+ hours
- **File**: New `cooldown_manager.py` module

---

## Testing Plan

### Test 1: Verify Cooldown Works
```
1. Set paper_trading_mode = true
2. Buy RELIANCE
3. Immediately try to buy RELIANCE again
4. Expected: "RELIANCE in cooldown (14.9 min remaining)"
5. Wait 15 minutes
6. Try to buy RELIANCE again
7. Expected: Order succeeds (cooldown expired)
```

### Test 2: Verify Engine Beat Setting
```
1. Set "engine_beat_seconds": 5.0
2. Start bot
3. Monitor logs for cycle frequency
4. Expected: Cycles every 5 seconds (not 0.5s)
```

### Test 3: Verify 24/7 Operation
```
1. Start bot outside market hours (e.g., 6 PM)
2. Expected: Bot waits, logs "Market closed, waiting..."
3. Check process is still running (not crashed)
4. At 9:15 AM next day: Bot resumes trading
```

### Test 4: Verify Multi-Symbol Cooldowns
```
1. Buy RELIANCE (cooldown starts)
2. Buy INFY (should succeed - different symbol)
3. Try to buy RELIANCE again
4. Expected: RELIANCE blocked, INFY not affected
```

---

## Configuration Changes Needed

### settings_default.json (Add)
```json
{
  "strategies": {
    "rsi_mean_reversion": {
      "cooldown_minutes": 15  // ← NEW
    }
  },
  "app_settings": {
    "engine_beat_seconds": 2,  // ← Already exists, make sure it's used
    "global_cooldown_enabled": true,  // ← NEW
    "global_cooldown_minutes": 15  // ← NEW
  }
}
```

### kickstart.py (Modify)
```python
# Global variables (add near top)
TRADE_COOLDOWNS = {}
COOLDOWN_MINUTES = 15

# Load from settings (in initialize_globals())
if settings:
    COOLDOWN_MINUTES = settings.get("app_settings.global_cooldown_minutes", 15)

# Fix main loop sleep (line 2914)
sleep_chunks = int(ENGINE_BEAT_SECONDS * 10)
for _ in range(sleep_chunks):
    if STOP_REQUESTED: break
    time.sleep(0.1)
```

---

## FAQ

### Q1: Why can't bot trade 24/7 like crypto bots?

**A**: Indian stock market (NSE/BSE) is only open 9:15 AM - 3:30 PM IST on weekdays. Broker APIs reject orders outside these hours. Crypto markets are 24/7, but equities are not.

### Q2: What does the bot do outside market hours?

**A**: Currently, it waits silently checking every 1 second for market to open. With recommended enhancements, it can do maintenance tasks (P&L updates, watchlist prep, summaries).

### Q3: Why is engine_beat_seconds ignored?

**A**: Bug in v2.5.2. The setting is loaded but the main loop uses hardcoded `time.sleep(0.1)` loops. Fix: Use ENGINE_BEAT_SECONDS variable in main_loop().

### Q4: How does paper mode run 24/7?

**A**: Paper mode overrides `is_market_open_now_ist()` to return True always. This allows testing/simulation outside market hours, but uses fabricated data (not real-time prices).

### Q5: Will cooldown affect stop-loss exits?

**A**: **NO** - Cooldown should only apply to NEW entry orders. Stop-loss/profit-target exits should bypass cooldown (emergency exits).

**Recommended Logic**:
```python
def is_symbol_in_cooldown(symbol, order_type="ENTRY"):
    if order_type == "EXIT":
        return False  # Never block exits
    # ... normal cooldown check for entries ...
```

### Q6: Can I disable cooldown for testing?

**A**: Yes, add configuration:
```json
{
  "app_settings": {
    "global_cooldown_enabled": false  // ← Disable all cooldowns
  }
}
```

---

## Summary

**Current State**:
- Bot cycles every 0.5 seconds (hardcoded)
- No post-trade cooldown (risk of duplicate trades)
- Engine beat setting exists but ignored
- Only trades during market hours (9:15-15:30 IST)
- Waits silently outside market hours

**Recommended State**:
- Bot cycles every 2 seconds (configurable via `engine_beat_seconds`)
- 15-minute cooldown after each trade (per symbol)
- Cooldown configurable per strategy
- Trades during market hours only (API constraint)
- Runs maintenance tasks outside market hours

**Implementation Effort**: ~4 hours total (P0 + P1 features)

**Impact**: Prevents duplicate trades, improves capital efficiency, makes configuration actually work.

**Next Step**: Implement P0 changes (cooldown + engine beat fix) and test.
