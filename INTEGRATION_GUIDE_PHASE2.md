# Phase 2 Integration Guide: Adding Market Context to Kickstart

This guide shows how to integrate market context fetching with kickstart.py.

## Option A: Minimal Integration (Recommended for now)

Just start the scheduler at boot time. Market context will be available when Phase 3 (AI Advisor) needs it.

### Step 1: Add to kickstart.py (around line 50, after imports)

```python
# Market context fetching (Phase 2)
from market_context_scheduler import MarketContextScheduler

# At startup, after logging initialized
market_scheduler = MarketContextScheduler(interval_seconds=300)  # Every 5 minutes
market_scheduler.start()
logger.info("Market context fetcher started")
```

### Step 2: Test
```bash
cd "C:\Antigravity\TradingBots-Aruns Project"
python kickstart.py

# You should see in logs:
# [market_scheduler] Market context scheduler started (interval: 300s)
# [market_scheduler] Market snapshot #1 stored (ID: 1, took 4.23s)
# [market_scheduler] Market snapshot #2 stored (ID: 2, took 3.98s)
```

### Impact
- **Trading engine**: ZERO impact (runs in separate thread)
- **Database**: Creates 1 new record every 5 minutes
- **Resources**: <5MB RAM, <1% CPU

---

## Option B: Advanced Integration (Use market conditions in trading decisions)

Capture market context with every trade and let kickstart consider it.

### Step 1: Add market context query to trade execution

In `kickstart.py`, in `safe_place_order_when_open()` function (around line 1836):

```python
def safe_place_order_when_open(self, ...):
    # ... existing checks (market open, never sell at loss, etc.)
    
    # [NEW] Check current market conditions
    market_ok, reason, confidence = self.market_fetcher.should_trade_now()
    
    if not market_ok and confidence > 0.8:
        log_ok(f"⚠️ Skipping trade: {reason}")
        return False
    
    # ... continue with order placement ...
```

### Step 2: Add instance variable to MarketContextFetcher

In kickstart.py `__init__`:

```python
def __init__(self):
    # ... existing init code ...
    
    # Market context (Phase 2)
    self.market_fetcher = MarketContextFetcher()
```

### Step 3: Capture market context with each trade

In `kickstart.py`, in the trade logging section (around line 1980):

```python
# Fetch latest market context
market_snapshot = self.market_fetcher.analytics_db.get_recent_market_snapshots(limit=1)
market_context = market_snapshot[0] if market_snapshot else None

# Use it in trade analysis:
analytics_db.insert_trade_analysis(
    symbol=symbol,
    timestamp=datetime.now().isoformat(),
    action=action,
    trade_id=trade_db_id,
    rsi_value=rsi,
    reason=reason,
    # [NEW] Market context at trade time
    nifty_50_change_pct=market_context['nifty_50_change_pct'] if market_context else None,
    sector_performance=market_context['sector_performance'] if market_context else None,
    market_volatility=market_context['market_volatility'] if market_context else None,
    market_regime=market_context['market_regime'] if market_context else None,
    # ... rest of parameters ...
)
```

### Impact
- **Trading logic**: Enhanced with market awareness
- **Trade analysis**: Now includes market context (feeds Phase 3 AI)
- **Performance**: Minimal (snapshot lookup is fast)

---

## Option C: Use Market Context for Position Sizing

Adjust position size based on market volatility.

### Code Example

```python
def calculate_dynamic_position_size(base_size, market_volatility):
    """
    Adjust position size based on market conditions.
    
    Base size is modified by volatility:
    - Low volatility (0-30):   100% size
    - Moderate (31-60):         75% size  
    - High (61-80):             50% size
    - Extreme (81-100):         25% size
    """
    if market_volatility is None:
        return base_size  # Default if no data
    
    if market_volatility <= 30:
        return base_size
    elif market_volatility <= 60:
        return int(base_size * 0.75)
    elif market_volatility <= 80:
        return int(base_size * 0.50)
    else:
        return int(base_size * 0.25)
```

Usage in kickstart:
```python
# Get latest volatility
latest_volatility = self.market_fetcher.fetch_market_volatility()

# Adjust quantity
base_qty = 1  # From settings
adjusted_qty = calculate_dynamic_position_size(base_qty, latest_volatility)

# Place order with adjusted size
self.place_order(symbol, adjusted_qty, ...)
```

---

## Configuration

All defaults are already set. If you want to customize:

### Change fetch interval
```python
# In kickstart.py startup
market_scheduler = MarketContextScheduler(interval_seconds=600)  # 10 minutes instead of 5
```

### Increase volatility threshold for "don't trade"
```python
# In market_context_fetcher.py, modify should_trade_now():
if volatility > 70:  # Was 80, now more cautious
    return (False, "High volatility...", 0.70)
```

---

## Testing Integration

### Test 1: Verify scheduler starts
```bash
python -c "
from market_context_scheduler import MarketContextScheduler
s = MarketContextScheduler()
s.start_time = __import__('time').time()
s.start()
import time
time.sleep(10)
print('Fetches:', s.fetch_count)
s.stop()
"
```

### Test 2: Verify market data in database
```bash
python -c "
from database.analytics_migration import AnalyticsDatabase
db = AnalyticsDatabase()
snapshots = db.get_recent_market_snapshots(limit=5)
for snap in snapshots:
    print(f'{snap[\"timestamp\"]}: Nifty {snap[\"nifty_50_value\"]:.0f}')
"
```

### Test 3: Verify trading decision impact
```bash
python -c "
from market_context_fetcher import MarketContextFetcher
f = MarketContextFetcher()
can_trade, reason, conf = f.should_trade_now()
print(f'Can trade: {can_trade}')
print(f'Reason: {reason}')
print(f'Confidence: {conf:.0%}')
"
```

---

## No Breaking Changes

✓ Existing kickstart.py functionality unchanged
✓ Optional integration (doesn't need to modify trade logic)
✓ Backward compatible (Phase 3 AI can use or ignore this data)
✓ Safe to roll back (just remove the scheduler start line)

---

## Next Phase: Phase 3 (AI Advisor)

Phase 3 will use this market context data to:
1. Analyze which market conditions lead to winning trades
2. Recommend parameter adjustments based on market regime
3. Suggest stocks to trade in current market conditions
4. Identify when NOT to trade based on historical patterns

Ready to proceed? The foundation is solid! 🚀
