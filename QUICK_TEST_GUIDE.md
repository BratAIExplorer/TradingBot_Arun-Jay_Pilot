# ⚡ Quick Test Guide - 15-Minute Validation

**Purpose**: Fast validation of Phase 4 work (both Claude AI + Google AI)
**Time**: ~15 minutes
**Where**: 🏠 **Your Local Machine** (laptop/desktop) - **NO VPS NEEDED!**
**For Comprehensive Testing**: See `Documentation/TEST_PLAN.md` or `LOCAL_TEST_GUIDE.md`

---

## 🚀 Quick Start

### 1. Setup (2 minutes)
```bash
cd ~/TradingBot_Arun-Jay_Pilot

# Ensure paper trading mode enabled
python -c "
import json
with open('settings.json', 'r+') as f:
    s = json.load(f)
    s['app_settings']['paper_trading_mode'] = True
    f.seek(0)
    json.dump(s, f, indent=2)
    f.truncate()
print('✅ Paper mode enabled')
"

# Install dependencies
pip install -r requirements.txt
```

---

## ✅ Claude AI Tests (8 minutes)

### Test 1: Bot Daemon (3 minutes)
```bash
# Switch to Claude's branch
git checkout claude/sync-github-remote-3461O

# Start daemon
python bot_daemon.py start

# Check status (should show RUNNING)
python bot_daemon.py status

# View logs (let it run for 2 minutes)
tail -f daemon.log
# Press Ctrl+C after 2 minutes

# Stop daemon
python bot_daemon.py stop

# ✅ PASS if: Started successfully, logs show activity, stopped gracefully
```

### Test 2: Mobile Dashboard (3 minutes)
```bash
# Start dashboard
streamlit run mobile_dashboard.py --server.port 8501 &

# Open browser: http://localhost:8501
# Login with password: arun2026

# Quick checks:
# - Dashboard tab loads ✓
# - Positions tab loads ✓
# - Trades tab shows data ✓
# - Logs tab displays daemon.log ✓
# - Settings tab shows config ✓

# Stop dashboard (Ctrl+C in terminal)

# ✅ PASS if: All 5 tabs load without errors
```

### Test 3: Critical Fix (2 minutes)
```bash
# Check fix is present
grep -A 3 "never_sell_at_loss" kickstart.py

# Verify setting
python -c "
import json
with open('settings.json') as f:
    s = json.load(f)
    print(f'Never Sell at Loss: {s[\"risk\"][\"never_sell_at_loss\"]}')
"

# ✅ PASS if: Setting exists and is True
```

---

## ✅ Google AI Tests (5 minutes)

### Test 4: Settings GUI Tabs (3 minutes)
```bash
# Switch to Google's branch
git checkout google/enhanced-settings-gui

# Check files exist
ls -la gui/settings_tabs/

# Test imports
python -c "
from gui.settings_tabs import RegimeTab, StopLossTab, PaperLiveTab, APITestTab
print('✅ All imports successful')
"

# Test each tab standalone (30 sec each)
python gui/settings_tabs/regime_tab.py
# (GUI opens - close it)

python gui/settings_tabs/stop_loss_tab.py
# (GUI opens - close it)

python gui/settings_tabs/paper_live_tab.py
# (GUI opens - close it)

python gui/settings_tabs/api_test_tab.py
# (GUI opens - close it)

# ✅ PASS if: All 4 tabs open without errors
```

### Test 5: Symbol Validator (2 minutes)
```bash
# Test validator
python -c "
from symbol_validator import validate_symbol

# Invalid symbol
result = validate_symbol('FAKESTK', 'NSE')
print(f'FAKESTK: {result}')  # Should be False

# Valid symbol
result = validate_symbol('RELIANCE', 'NSE')
print(f'RELIANCE: {result}')  # Should be True
"

# ✅ PASS if: FAKESTK=False, RELIANCE=True
```

---

## 🎯 Quick Results

**Claude AI** (3 tests):
- [ ] Daemon works
- [ ] Dashboard works
- [ ] Critical fix present

**Google AI** (2 tests):
- [ ] Settings tabs load
- [ ] Validator fixed

**Overall**: ___/5 tests passed

---

## ⚠️ If Any Test Fails

1. Check error messages in terminal
2. Review `daemon.log` for errors
3. Verify Python version (3.8+)
4. Ensure all dependencies installed
5. See full `Documentation/TEST_PLAN.md` for detailed troubleshooting

---

## 📊 Next Steps After Testing

**If All Tests Pass**:
1. Mark Phase 4 as production-ready ✅
2. Optionally deploy to VPS (see `VPS_DEPLOYMENT.md`)
3. Start Phase 4.1 or Phase 5 work

**If Tests Fail**:
1. Document failing tests
2. Check `Documentation/TEST_PLAN.md` for detailed debugging
3. Report issues if needed

---

**Quick Test Complete!** 🎉

## 📚 More Testing Resources

- **Local Testing (No VPS)**: See `LOCAL_TEST_GUIDE.md` - Most users start here!
- **Comprehensive Testing**: See `Documentation/TEST_PLAN.md`
- **VPS Deployment** (Optional): See `Documentation/VPS_DEPLOYMENT.md`

**Remember**: VPS is ONLY needed for 24/7 automated trading. Everything else works on your local machine! 🏠
