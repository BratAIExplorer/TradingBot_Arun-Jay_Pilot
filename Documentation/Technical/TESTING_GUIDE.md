# 🚀 ARUN Bot - Launch & Testing Guide

**Version:** 2.1 (P1 & P2 Features)  
**Branch:** `feature/p1-p2-enhancements`  
**Date:** January 18, 2026

---

## 📋 Pre-Launch Checklist

### ✅ Prerequisites
- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Git repository up to date
- [ ] On correct branch: `feature/p1-p2-enhancements`

---

## 🚀 Launch Steps (Step-by-Step)

### **Step 1: Verify Installation**
```powershell
# Navigate to project folder
cd "C:\Antigravity\TradingBots-Aruns Project"

# Check git branch
git branch
# Should show: * feature/p1-p2-enhancements

# Verify all new files exist
dir volume_filter.py
dir trend_filter.py
dir performance_analytics.py
```

**Expected Output:** All files found ✅

---

### **Step 2: Test Standalone Modules**

```powershell
# Test Volume Filter
python volume_filter.py
# Expected: All 3 tests pass ✅

# Test Trend Filter
python trend_filter.py
# Expected: Fetches Nifty 50 data, tests complete ✅

# Test Performance Analytics
python performance_analytics.py
# Expected: Analytics summary generated ✅
```

**What to Look For:**
- ✅ No errors or exceptions
- ✅ "All tests passed" messages
- ✅ Data fetched successfully

---

### **Step 3: Configure Settings (First Time)**

```powershell
# Launch dashboard
python dashboard_v2.py
```

**In the GUI:**
1. Click **"SETTINGS"** tab
2. Navigate to **"Capital"** tab
   - ✅ Verify Volume Filter section visible
   - ✅ Keep "Enable Volume Filter" checked (default)
   - ✅ Min Volume: 50,000 shares (default)
   - ✅ Min Turnover: ₹5,00,000 (default)

3. Navigate to **"Risk Controls"** tab
   - ✅ Verify Trend Filter section visible
   - ✅ Keep "Enable Trend Filter (200 DMA)" checked (default)
   - ✅ Keep "Auto-Execute Stop-Loss" checked (default)

4. Navigate to **"Broker"** tab
   - ✅ Enable Paper Trading Mode
   - ✅ Keep "Enable Regime Monitor" checked

5. Click **"Save All Settings"**

**Expected:** Settings saved successfully ✅

---

### **Step 4: Test Paper Trading Mode**

```powershell
# With dashboard still open
# 1. Click "START ENGINE" button in Dashboard tab
```

**What Happens:**
1. Bot initializes
2. Regime Monitor checks market (may take 10-20 seconds)
3. Volume Filter loads
4. Trend Filter initializes
5. Logs appear in bottom console

**Watch for in Logs:**
```
📊 Market Regime: BULLISH (Confidence: 75%)
   → Market above 200 DMA, volatility normal

ℹ️ Regime Monitor ENABLED by user (via Settings). Trading normally.

🧪 PAPER TRADE: BUY MICEL Qty: 10 @ ₹245.50
✅ Paper trade logged (execution: ₹245.62, fees: ₹26.51)
```

**OR if filters block:**
```
🛑 VOLUME FILTER BLOCKED: SMALLCAP - Low liquidity: 25,000 < 50,000 shares/day
```

```
🛑 TREND FILTER BLOCKED: DOWNSTOCK - Price below 200 DMA: ₹100 < ₹120 (-16.7%)
```

---

### **Step 5: Verify Dashboard Regime Widget**

In **Dashboard** tab:
- Look for **3rd card** in top row (purple border)
- Should show:
  ```
  MARKET REGIME
  [BULLISH/BEARISH/etc]
  Confidence: XX%
  ✅ TRADING or ⛔ HALTED
  Last update: HH:MM
  ```

**Expected:** Regime displays correctly ✅

---

### **Step 6: Test Settings Persistence**

```powershell
# Close dashboard (stop bot first)
# Re-launch
python dashboard_v2.py

# Go to Settings → Capital
# Go to Settings → Risk Controls
```

**Expected:** 
- Volume Filter settings retained ✅
- Trend Filter settings retained ✅

---

### **Step 7: Test Filter Overrides**

**Scenario A: Disable Volume Filter**
1. Settings → Capital → Uncheck "Enable Volume Filter"
2. Save Settings
3. Start Engine
4. Attempt to trade low-volume stock

**Expected:** Trade proceeds (filter disabled) ✅

**Scenario B: Disable Trend Filter**
1. Settings → Risk → Uncheck "Enable Trend Filter"
2. Save Settings
3. Start Engine
4. Attempt to buy stock below 200 DMA

**Expected:** Trade proceeds (filter disabled) ✅

---

### **Step 8: Check Database Logs**

```powershell
# View recent trades
python -c "from database.trades_db import TradesDatabase; db = TradesDatabase(); print(db.get_recent_trades(5))"
```

**Expected:**
- Paper trades visible
- `broker="PAPER"` field set
- Realistic fees logged
- Slippage noted in reason field

---

### **Step 9: Test Performance Analytics**

```powershell
# Get analytics summary
python -c "from performance_analytics import get_analytics_summary; from database.trades_db import TradesDatabase; db = TradesDatabase(); print(get_analytics_summary(db, 30))"
```

**Expected Output:**
```python
{
  'total_trades': X,
  'win_rate': XX.X,
  'net_profit': ₹XXX,
  'sharpe_ratio': X.XX,
  'nifty50_return': X.XX,
  'bot_return': X.XX,
  'outperformance': X.XX,
  'benchmark_available': True/False
}
```

---

### **Step 10: Test Telegram Notifications** (Optional)

If Telegram configured:

1. Enable in Settings → Notifications
2. Save Settings
3. Trigger a trade

**Expected:**
- Telegram message received ✅
- Message includes volume/trend filter status
- Formatting correct (HTML)

---

## 🧪 User Testing Checklist

### **Test 1: Volume Filter Functionality**
- [ ] Stock with volume > 50K → Trade allowed
- [ ] Stock with volume < 50K → Trade blocked
- [ ] Clear log message explaining block
- [ ] Telegram alert sent (if enabled)
- [ ] Disable filter → Trade proceeds

### **Test 2: Trend Filter Functionality**
- [ ] Stock above 200 DMA → Buy allowed
- [ ] Stock below 200 DMA → Buy blocked
- [ ] SELL orders always allowed
- [ ] Clear log message explaining block
- [ ] Telegram alert sent (if enabled)
- [ ] Disable filter → Trade proceeds

### **Test 3: Combined Filters**
- [ ] Both filters enabled
- [ ] Stock passes both checks → Trade executes
- [ ] Stock fails volume → Blocked at volume check
- [ ] Stock fails trend → Blocked at trend check
- [ ] Logs show which filter blocked

### **Test 4: Paper Trading v2.0**
- [ ] Realistic slippage (0.05-0.15%) applied
- [ ] Indian fees calculated (STT, brokerage, GST, etc.)
- [ ] No real orders executed
- [ ] Database shows broker="PAPER"
- [ ] Virtual capital accurate

### **Test 5: Regime Monitor**
- [ ] Dashboard widget displays current regime
- [ ] Updates hourly (check timestamp)
- [ ] Trading halted in BEARISH/CRISIS
- [ ] Position sizes reduced in VOLATILE/SIDEWAYS
- [ ] User can disable via Settings

### **Test 6: Settings Persistence**
- [ ] Save settings
- [ ] Close app
- [ ] Reopen app
- [ ] All settings retained

### **Test 7: Performance Analytics**
- [ ] Sharpe ratio calculates
- [ ] Nifty 50 data fetches
- [ ] Outperformance computed
- [ ] No errors in calculation

### **Test 8: Telegram Enhancements** (if configured)
- [ ] Generic alerts work (filter blocks)
- [ ] Regime change alerts work
- [ ] Daily summary format correct

---

## 🐛 Known Issues & Troubleshooting

### Issue 1: "Volume filter not available"
**Cause:** Module not in Python path  
**Fix:** Ensure `volume_filter.py` is in project root

### Issue 2: "Trend filter error: Expecting value"
**Cause:** yfinance API rate limit or network issue  
**Fix:** Filter fails open (trade proceeds), no action needed

### Issue 3: "Regime Monitor shows UNKNOWN"
**Cause:** First run, cache building  
**Fix:** Wait 1-2 minutes for data fetch

### Issue 4: Nifty 50 benchmark unavailable
**Cause:** Yahoo Finance API issue  
**Fix:** Analytics still work, benchmark shows 0%

---

## ✅ Success Criteria

**All tests pass when:**
- ✅ Filters block appropriate trades
- ✅ Settings save and reload correctly
- ✅ Paper trades never execute real orders
- ✅ Dashboard displays regime status
- ✅ Logs are clear and informative
- ✅ No Python errors/exceptions
- ✅ Telegram notifications arrive (if configured)

---

## 📊 Performance Benchmarks

**Expected Behavior:**
- Dashboard load time: < 3 seconds
- Regime check: < 20 seconds (first run with cache)
- Volume filter check: < 1 second
- Trend filter check: < 2 seconds (fetches 200 DMA)
- Order placement: < 2 seconds (total including filters)

---

## 🔄 Next Steps After Testing

1. **If all tests pass:**
   ```powershell
   git checkout main
   git merge feature/p1-p2-enhancements
   git tag v2.1-strategy-enhancement
   git push origin main --tags
   ```

2. **If issues found:**
   - Document in GitHub Issues
   - Fix on feature branch
   - Re-test
   - Then merge

---

## 📞 Support & Questions

**Common Questions:**

**Q: Can I disable all filters?**  
A: Yes! Each filter has toggle in Settings. Bot respects your choices.

**Q: Do filters apply to SELL orders?**  
A: No. Filters only check BUY orders. SELL (exits) always allowed.

**Q: What if yfinance API fails?**  
A: Filters fail-open. Trade proceeds with warning logged.

**Q: How do I know which filter blocked?**  
A: Clear log messages: "🛑 VOLUME FILTER BLOCKED" or "🛑 TREND FILTER BLOCKED"

**Q: Can I override for specific stocks?**  
A: Yes! Per-symbol override planned for next version. Use global disable for now.

---

**Happy Testing! 🚀**
