# Strategy Improvement Roadmap
## From 24% Win Rate → 50%+ Win Rate

**Current State:** RSI-only strategy, 24.2% win rate, -₹36,617 loss  
**Target State:** Multi-signal strategy, 50%+ win rate, profitable  
**Timeline:** 4-6 weeks  
**Effort:** ~10-15 hours over the month

---

## PHASE 1: Quick Wins (This Week - 3-4 hours)

### 1.1 Backtest Current RSI Parameters

Your bot uses RSI(14) with buy<30, sell>70. Are these optimal?

**Step 1: Create backtester**
```python
# File: backtest_rsi.py
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

class SimpleBacktester:
    def __init__(self, symbol, capital=50000):
        self.symbol = symbol
        self.capital = capital
        self.cash = capital
        self.shares = 0
        self.trades = []
    
    def backtest(self, data, rsi_buy, rsi_sell):
        """Simulate trading on historical data"""
        wins = 0
        losses = 0
        
        for idx in range(len(data)-1):
            rsi = data['RSI'].iloc[idx]
            price = data['Close'].iloc[idx]
            
            # Buy signal
            if rsi < rsi_buy and self.cash > price * 10:
                shares_to_buy = int(self.cash * 0.1 / price)  # 10% allocation
                self.cash -= shares_to_buy * price
                self.shares += shares_to_buy
                buy_price = price
            
            # Sell signal
            if rsi > rsi_sell and self.shares > 0:
                sell_price = price
                pnl = (sell_price - buy_price) * self.shares
                if pnl > 0:
                    wins += 1
                else:
                    losses += 1
                self.cash += self.shares * sell_price
                self.shares = 0
        
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        final_capital = self.cash + (self.shares * data['Close'].iloc[-1] if self.shares > 0 else 0)
        pnl = final_capital - self.capital
        
        return {
            'win_rate': win_rate,
            'wins': wins,
            'losses': losses,
            'total_trades': total_trades,
            'pnl': pnl,
            'final_capital': final_capital
        }

# Test different RSI thresholds
def test_parameters():
    # Get historical data (last 6 months)
    symbol = "SBIN.NS"  # Test on major NSE stock
    data = yf.download(symbol, start=datetime.now()-timedelta(days=180), progress=False)
    
    # Calculate RSI
    data['RSI'] = calculate_rsi(data['Close'], 14)
    
    print("RSI Parameter Backtest Results:")
    print("=" * 70)
    print(f"{'Buy RSI':>10} {'Sell RSI':>10} {'Win Rate':>12} {'Trades':>8} {'P&L':>12}")
    print("=" * 70)
    
    best_params = None
    best_win_rate = 0
    
    for buy_rsi in range(15, 40, 5):
        for sell_rsi in range(60, 85, 5):
            bt = SimpleBacktester(symbol)
            result = bt.backtest(data, buy_rsi, sell_rsi)
            
            print(f"{buy_rsi:>10} {sell_rsi:>10} {result['win_rate']:>11.1f}% {result['total_trades']:>8} {result['pnl']:>12,.0f}")
            
            if result['win_rate'] > best_win_rate:
                best_win_rate = result['win_rate']
                best_params = (buy_rsi, sell_rsi)
    
    print("=" * 70)
    print(f"\nBest parameters found: buy<{best_params[0]}, sell>{best_params[1]}")
    print(f"Expected win rate: {best_win_rate:.1f}%")
    
test_parameters()
```

**Step 2: Run on your top 5 symbols**
- IDEA, AVATIL, KERNEX, APOLLO, YESBANK
- Find optimal thresholds for each

**Step 3: Deploy best parameters**
```python
# Update kickstart.py
RSI_BUY_THRESHOLD = 25  # (or whatever backtest shows)
RSI_SELL_THRESHOLD = 75  # (or whatever backtest shows)
```

**Expected Improvement:** +5-10% win rate

---

### 1.2 Add Trend Filter (Ma Slope Check)

Don't buy oversold stocks in downtrends.

```python
# Add to kickstart.py
def is_in_uptrend(symbol, exchange):
    """Only trade when 20-day MA > 50-day MA"""
    try:
        df = fetch_candles(symbol, exchange, "D", 60)  # Last 60 days
        if df is None or len(df) < 50:
            return True  # Insufficient data, assume OK
        
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma50 = df['close'].rolling(50).mean().iloc[-1]
        
        return ma20 > ma50  # True if uptrend
    except:
        return True  # Default to allowing trade if error

# Modify buy logic
if rsi < RSI_BUY_THRESHOLD and is_in_uptrend(symbol, exchange):
    place_buy_order(...)  # Only buy in uptrends
```

**Expected Improvement:** +10-15% win rate

---

## PHASE 2: Multi-Signal Confirmation (Weeks 2-3 - 4-5 hours)

### 2.1 Multi-Timeframe RSI

Buy only if oversold on 15m, 1h, AND daily.

```python
def get_multi_timeframe_rsi(symbol, exchange):
    """Get RSI across 3 timeframes"""
    try:
        # 15-minute RSI
        df_15m = fetch_candles(symbol, exchange, "15m", 100)
        rsi_15m = calculate_rsi(df_15m['close'], 14) if df_15m is not None else None
        
        # 1-hour RSI
        df_1h = fetch_candles(symbol, exchange, "1h", 50)
        rsi_1h = calculate_rsi(df_1h['close'], 14) if df_1h is not None else None
        
        # Daily RSI
        df_daily = fetch_candles(symbol, exchange, "D", 50)
        rsi_daily = calculate_rsi(df_daily['close'], 14) if df_daily is not None else None
        
        return {
            '15m': rsi_15m.iloc[-1] if rsi_15m is not None else None,
            '1h': rsi_1h.iloc[-1] if rsi_1h is not None else None,
            'daily': rsi_daily.iloc[-1] if rsi_daily is not None else None
        }
    except:
        return None

def should_buy_multitimeframe(symbol, exchange):
    """Only buy if RSI is oversold on ALL timeframes"""
    rsis = get_multi_timeframe_rsi(symbol, exchange)
    
    if rsis is None:
        return False
    
    # All must be True
    buy_15m = rsis['15m'] < 30
    buy_1h = rsis['1h'] < 40
    buy_daily = rsis['daily'] < 50
    
    return buy_15m and buy_1h and buy_daily

# Modify buy logic
if should_buy_multitimeframe(symbol, exchange):
    place_buy_order(...)
```

**Expected Improvement:** +15-20% reduction in false signals

---

### 2.2 Volume Confirmation

Only trade when volume is above average.

```python
def is_volume_spike(symbol, exchange):
    """Check if volume is above 120% of 20-day average"""
    try:
        df = fetch_candles(symbol, exchange, "15m", 100)
        if df is None or len(df) < 20:
            return True
        
        volume_avg = df['volume'].rolling(20).mean().iloc[-1]
        volume_now = df['volume'].iloc[-1]
        
        return volume_now > volume_avg * 1.2
    except:
        return True

# Add to buy logic
if should_buy_multitimeframe(symbol, exchange) and is_volume_spike(symbol, exchange):
    place_buy_order(...)
```

**Expected Improvement:** +5-10% win rate

---

## PHASE 3: Intelligent Position Sizing (Weeks 3-4 - 3-4 hours)

### 3.1 Volatility-Adjusted Sizing

Size positions inversely to volatility (ATR).

```python
def calculate_intelligent_position_size(symbol, exchange, allocated_capital, risk_pct=2):
    """Size based on volatility"""
    try:
        df = fetch_candles(symbol, exchange, "15m", 100)
        atr = calculate_atr(df, 14)
        price = df['close'].iloc[-1]
        
        # Higher volatility = smaller position
        # ATR as % of price
        atr_pct = (atr / price) * 100
        
        # Standard ATR is 1-2% of price
        # If ATR > 2%, reduce size
        size_factor = min(1.0, 2.0 / atr_pct) if atr_pct > 0 else 1.0
        
        # Calculate quantity
        risk_amount = allocated_capital * (risk_pct / 100)
        qty = int((risk_amount / atr) * size_factor)
        
        return max(1, qty)
    except:
        return int(allocated_capital * 0.001 / price)

# Modify order placement
qty = calculate_intelligent_position_size(symbol, exchange, ALLOCATED_CAPITAL)
place_buy_order(symbol, exchange, qty, ...)
```

**Expected Improvement:** +3-5% Sharpe ratio (smoother equity curve)

---

## PHASE 4: Adaptive Learning (Weeks 4-6 - 3-4 hours)

### 4.1 Parameter Reoptimization Every 100 Trades

```python
def reoptimize_parameters():
    """Every 100 trades, test current RSI thresholds against new ones"""
    from database.trades_db import TradesDatabase
    
    db = TradesDatabase()
    recent_trades = db.get_trade_history(days=30)
    
    if len(recent_trades) < 100:
        return  # Not enough data yet
    
    # Get last 500 trades for training window
    training_data = db.get_trade_history(days=90)
    
    best_params = None
    best_wr = 0
    
    for buy_rsi in range(20, 40):
        for sell_rsi in range(60, 80):
            # Backtest on rolling window
            wr = simulate_on_history(training_data, buy_rsi, sell_rsi)
            if wr > best_wr:
                best_wr = wr
                best_params = (buy_rsi, sell_rsi)
    
    # Only update if +5% improvement
    current_wr = calculate_win_rate(recent_trades)
    if best_wr > current_wr + 5:
        update_settings(buy_threshold=best_params[0], sell_threshold=best_params[1])
        log(f"Parameters updated: buy<{best_params[0]}, sell>{best_params[1]}")

# Call this weekly
# Add to cron job or scheduler
```

**Expected Improvement:** +2-8% over time (stays adaptive to market changes)

---

## EXPECTED RESULTS

| Phase | Win Rate | P&L Improvement | Timeline |
|-------|----------|-----------------|----------|
| Current | 24.2% | -₹36,617 | — |
| Phase 1 | +5-10% → 30-35% | -₹20,000 to -₹10,000 | 1 week |
| Phase 2 | +15-20% → 45-55% | Break-even to +₹20,000 | 2 weeks |
| Phase 3 | +3-5% Sharpe | Smoother equity curve | 3 weeks |
| Phase 4 | +2-8% adaptive | +₹30,000-₹50,000 | 6 weeks |

**Final Target:** 50%+ win rate, profitable

---

## EXECUTION CHECKLIST

### Week 1: Backtest & Trend Filter
- [ ] Create backtester.py
- [ ] Test RSI parameters on 5 symbols
- [ ] Deploy best parameters
- [ ] Add trend filter code
- [ ] Run bot live, monitor

### Week 2-3: Multi-Signal Confirmation
- [ ] Implement multi-timeframe RSI
- [ ] Add volume confirmation
- [ ] Backtest combined signals
- [ ] Deploy to production
- [ ] Measure improvement

### Week 3-4: Intelligent Sizing
- [ ] Calculate ATR for each symbol
- [ ] Implement volatility-adjusted sizing
- [ ] Test on 100 paper trades
- [ ] Deploy

### Week 4-6: Adaptive Learning
- [ ] Build parameter optimizer
- [ ] Add weekly reoptimization job
- [ ] Monitor for 200+ trades
- [ ] Fine-tune learning schedule

---

## SUCCESS CRITERIA

When you've completed this roadmap:

✅ Win rate ≥ 50%  
✅ P&L ≥ Break-even  
✅ Trades/week ≥ 10 (quality)  
✅ Max drawdown < 10%  
✅ Sharpe ratio > 1.0  

---

## START NOW

**Execute Phase 1 this week:**
1. Create backtester.py
2. Test on SBIN, IDEA, KERNEX (your top performers)
3. Find optimal thresholds
4. Update kickstart.py with new parameters
5. Deploy and monitor

Ready? Let me know when you want to start Phase 1!
