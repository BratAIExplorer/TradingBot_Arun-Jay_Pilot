# 🧪 ARUN Trading Bot - Comprehensive Test Plan

**Version**: 1.0
**Last Updated**: January 18, 2026
**Purpose**: Validate Phase 4 Infrastructure Sprint work from both Claude AI and Google AI

---

## 📋 Overview

This test plan covers validation of all changes delivered in Phase 4:

**Claude AI Deliverables**:
- ✅ bot_daemon.py (Headless VPS runner)
- ✅ mobile_dashboard.py (Streamlit monitoring UI)
- ✅ VPS_DEPLOYMENT.md (Deployment guide)
- ✅ Critical fix: "Never Sell Below Entry Price" enforcement

**Google AI Deliverables**:
- ✅ Enhanced Settings GUI Tabs (4 new tabs)
- ✅ Symbol validator fix

---

## 🎯 Testing Objectives

1. ✅ Verify all new code runs without errors
2. ✅ Confirm backward compatibility (existing features still work)
3. ✅ Validate integration between both AI's work
4. ✅ Test critical trading logic (never sell at loss)
5. ✅ Ensure VPS deployment readiness
6. ✅ Verify settings GUI enhancements

---

## 🛠️ Test Environment Setup

### Prerequisites
```bash
# Ensure you're in the project directory
cd ~/TradingBot_Arun-Jay_Pilot

# Check git status
git status

# Verify both branches exist
git branch -a | grep -E "(claude|google)"
```

**Expected Branches**:
- `claude/sync-github-remote-3461O` (Claude AI's work)
- `google/enhanced-settings-gui` (Google AI's work)

### Install Dependencies
```bash
# Activate virtual environment (if using one)
source .venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Verify streamlit installed
python -c "import streamlit; print(f'Streamlit {streamlit.__version__} OK')"
```

---

## 📝 Test Plan Structure

### Phase 1: Individual Component Testing (Claude AI)
### Phase 2: Individual Component Testing (Google AI)
### Phase 3: Integration Testing (Both Branches)
### Phase 4: Critical Trading Logic Validation
### Phase 5: User Acceptance Testing (UAT)

---

## 🔵 Phase 1: Claude AI Component Testing

### Test 1.1: Headless Daemon (bot_daemon.py)

**Objective**: Verify bot_daemon.py can start, stop, and manage the trading engine

**Steps**:
```bash
# Switch to Claude's branch
git checkout claude/sync-github-remote-3461O

# Test 1: Check status (should show NOT running)
python bot_daemon.py status

# Test 2: Start daemon in foreground (for testing)
python bot_daemon.py run &
# Press Ctrl+C after 10 seconds to stop

# Test 3: Start daemon in background
python bot_daemon.py start

# Test 4: Check status (should show RUNNING)
python bot_daemon.py status

# Test 5: View logs
tail -20 daemon.log

# Test 6: Stop daemon gracefully
python bot_daemon.py stop

# Test 7: Verify PID file cleanup
ls -la bot_daemon.pid  # Should not exist after stop
```

**Expected Results**:
- ✅ Status command shows correct state
- ✅ Daemon starts without errors
- ✅ PID file created on start
- ✅ Logs written to daemon.log
- ✅ Daemon stops gracefully on SIGTERM
- ✅ PID file removed on stop

**Success Criteria**: All 6 tests pass ✅

---

### Test 1.2: Mobile Dashboard (mobile_dashboard.py)

**Objective**: Verify Streamlit dashboard displays data correctly

**Prerequisites**:
```bash
# Ensure bot has some trades in database
# If database is empty, run daemon for a few minutes first
python bot_daemon.py start
sleep 300  # Wait 5 minutes for some activity
python bot_daemon.py stop
```

**Steps**:
```bash
# Test 1: Start dashboard
streamlit run mobile_dashboard.py --server.port 8501 &

# Test 2: Open browser
# Navigate to: http://localhost:8501

# Test 3: Login screen
# - Enter password: arun2026
# - Click outside password box (triggers validation)
# Expected: Successful login

# Test 4: Dashboard page
# Check for:
# - Total Trades count (should show > 0 if you ran daemon)
# - Total P&L display
# - Active Positions count
# - Allocated Capital display
# Expected: All metrics display correctly

# Test 5: Positions tab
# - Click "Positions" in sidebar
# Expected: Table shows active positions (if any)

# Test 6: Trades History tab
# - Click "Trades History" in sidebar
# - Try filters: Symbol, Action, Time Period
# - Click "Download CSV" button
# Expected: Filters work, CSV downloads successfully

# Test 7: System Logs tab
# - Click "System Logs" in sidebar
# - Try search filter
# - Enable "Auto-refresh"
# Expected: Logs display, search works, auto-refresh updates

# Test 8: Settings tab
# - Click "Settings" in sidebar
# - Expand each section (Broker, Capital, Risk, etc.)
# Expected: All settings display (read-only warning shown)

# Stop dashboard
# Press Ctrl+C in terminal
```

**Expected Results**:
- ✅ Dashboard loads without errors
- ✅ Login works with correct password
- ✅ All tabs render correctly
- ✅ Data loads from database
- ✅ Filters and search work
- ✅ Auto-refresh updates data
- ✅ Mobile responsive (test on phone if possible)

**Success Criteria**: 8/8 tests pass ✅

---

### Test 1.3: VPS Deployment Guide

**Objective**: Verify deployment guide is comprehensive and accurate

**Steps**:
```bash
# Test 1: Open VPS deployment guide
cat Documentation/VPS_DEPLOYMENT.md

# Test 2: Checklist validation
# Verify guide includes:
# - [ ] VPS provider comparison ✓
# - [ ] Installation steps for Ubuntu ✓
# - [ ] Python/Git setup ✓
# - [ ] Systemd service config ✓
# - [ ] Firewall setup ✓
# - [ ] Troubleshooting section ✓
# - [ ] Security best practices ✓

# Test 3: Validate systemd service file syntax
# Copy the service file from guide to temp location
# Check if it has correct format
```

**Expected Results**:
- ✅ Guide is comprehensive (650+ lines)
- ✅ All 13 steps included
- ✅ Systemd config syntax valid
- ✅ Security section present
- ✅ Troubleshooting guide included

**Success Criteria**: All sections present and technically accurate ✅

---

### Test 1.4: Critical Trading Fix ("Never Sell Below Entry")

**Objective**: Verify RSI sell signals are blocked if price ≤ entry price

**Prerequisites**:
```bash
# Ensure paper trading mode is enabled
nano settings.json
# Set "paper_trading_mode": true
```

**Steps**:
```bash
# Test 1: Review code fix
grep -A 5 "never_sell_at_loss" kickstart.py

# Test 2: Check settings
python -c "
import json
with open('settings.json') as f:
    s = json.load(f)
    print(f'Never Sell at Loss: {s[\"risk\"][\"never_sell_at_loss\"]}')
"
# Expected: True

# Test 3: Simulate scenario (manual verification in logs)
# Run daemon and look for "⏸️ HOLD" messages
python bot_daemon.py start
tail -f daemon.log | grep "HOLD"

# After 5-10 minutes, stop
python bot_daemon.py stop

# Check if any "HOLD" messages appeared when RSI >= 70 but price < entry
```

**Expected Results**:
- ✅ `never_sell_at_loss` setting exists in settings.json
- ✅ Default value is `true`
- ✅ Code checks this setting before RSI sells
- ✅ Logs show "⏸️ HOLD" messages when blocking sells at loss

**Success Criteria**: Fix is properly implemented ✅

---

## 🟢 Phase 2: Google AI Component Testing

### Test 2.1: Enhanced Settings GUI Tabs

**Objective**: Verify all 4 new settings tabs load and function correctly

**Steps**:
```bash
# Switch to Google's branch
git checkout google/enhanced-settings-gui

# Test 1: Verify files exist
ls -la gui/settings_tabs/

# Expected files:
# - __init__.py
# - regime_tab.py
# - stop_loss_tab.py
# - paper_live_tab.py
# - api_test_tab.py

# Test 2: Check Python syntax
python -m py_compile gui/settings_tabs/*.py

# Test 3: Import test
python -c "
from gui.settings_tabs import RegimeTab, StopLossTab, PaperLiveTab, APITestTab
print('✅ All tabs import successfully')
"

# Test 4: Standalone tab testing
# Each tab can be tested individually:

# Test 4a: Regime Tab
python gui/settings_tabs/regime_tab.py
# Expected: GUI window opens, settings load, inputs work

# Test 4b: Stop Loss Tab
python gui/settings_tabs/stop_loss_tab.py
# Expected: GUI window opens, risk controls displayed

# Test 4c: Paper/Live Trading Tab
python gui/settings_tabs/paper_live_tab.py
# Expected: Toggle between modes works, warnings shown

# Test 4d: API Test Tab
python gui/settings_tabs/api_test_tab.py
# Expected: Test connection button works (may fail if no credentials)

# Close all test windows
```

**Expected Results**:
- ✅ All 5 files exist
- ✅ No Python syntax errors
- ✅ All imports succeed
- ✅ Each tab runs standalone without crashes
- ✅ Settings load from SettingsManagerV2
- ✅ Save functionality works

**Success Criteria**: 4/4 tabs functional ✅

---

### Test 2.2: Symbol Validator Fix

**Objective**: Verify symbol validator correctly rejects invalid NSE stocks

**Steps**:
```bash
# Test 1: Check fix is present
grep -A 10 "historical data" symbol_validator.py

# Test 2: Test invalid symbols
python -c "
from symbol_validator import validate_symbol

# Test invalid symbol
result = validate_symbol('FAKESTK', 'NSE')
print(f'FAKESTK validation: {result}')  # Should be False

# Test valid symbol
result = validate_symbol('RELIANCE', 'NSE')
print(f'RELIANCE validation: {result}')  # Should be True
"

# Test 3: Integration test
# Try adding invalid symbol via settings GUI
# Expected: Validation error shown
```

**Expected Results**:
- ✅ Invalid symbols rejected (FAKESTK → False)
- ✅ Valid symbols accepted (RELIANCE → True)
- ✅ Validation uses historical data check
- ✅ Fallback validation works if API fails

**Success Criteria**: Validator correctly identifies valid/invalid symbols ✅

---

## 🔀 Phase 3: Integration Testing (Both Branches)

### Test 3.1: Branch Compatibility Check

**Objective**: Verify both branches can be merged without conflicts

**Steps**:
```bash
# Create integration test branch
git checkout -b integration-test

# Try merging Claude's work
git merge claude/sync-github-remote-3461O
# Expected: No conflicts (Claude didn't touch GUI files)

# Try merging Google's work
git merge google/enhanced-settings-gui
# Expected: No conflicts (Google didn't touch kickstart.py)

# If conflicts appear, document them:
git status | grep "both modified"

# Abort test merge
git merge --abort
git checkout claude/sync-github-remote-3461O
git branch -D integration-test
```

**Expected Results**:
- ✅ No file conflicts between branches
- ✅ Claude's files: bot_daemon.py, mobile_dashboard.py, VPS_DEPLOYMENT.md
- ✅ Google's files: gui/settings_tabs/*
- ✅ No overlap in modified files

**Success Criteria**: Clean merge possible ✅

---

### Test 3.2: Settings Manager Integration

**Objective**: Verify both AI's work uses SettingsManagerV2 correctly

**Steps**:
```bash
# Test 1: Check Claude's usage
grep -n "SettingsManager" bot_daemon.py
grep -n "SettingsManager" mobile_dashboard.py

# Test 2: Check Google's usage
grep -n "SettingsManagerV2" gui/settings_tabs/*.py

# Test 3: Verify settings.json schema compatibility
python -c "
import json
with open('settings.json') as f:
    s = json.load(f)

# Check Claude's expected keys
assert 'app_settings' in s
assert 'mobile' in s or True  # Mobile might not exist yet

# Check Google's expected keys
assert 'risk' in s
assert 'strategies' in s

print('✅ Settings schema compatible')
"
```

**Expected Results**:
- ✅ Both use settings.json correctly
- ✅ No conflicting setting keys
- ✅ Both can read/write without interfering

**Success Criteria**: No settings conflicts ✅

---

### Test 3.3: Full System Integration Test

**Objective**: Run all components together

**Prerequisites**:
```bash
# Create a test branch with both AI's work
git checkout -b full-integration-test
git merge claude/sync-github-remote-3461O
git merge google/enhanced-settings-gui
```

**Steps**:
```bash
# Test 1: Install all dependencies
pip install -r requirements.txt

# Test 2: Start daemon
python bot_daemon.py start

# Test 3: Start mobile dashboard
streamlit run mobile_dashboard.py --server.port 8501 &

# Test 4: Test settings GUI tabs (if integrated into main UI)
# python dashboard_v2.py  # Main desktop app
# Navigate to Settings
# Check if new tabs are accessible

# Test 5: Run for 10 minutes
sleep 600

# Test 6: Check logs for errors
grep -i "error\|traceback" daemon.log

# Test 7: Stop all services
python bot_daemon.py stop
# Kill streamlit (Ctrl+C or pkill streamlit)

# Clean up test branch
git checkout claude/sync-github-remote-3461O
git branch -D full-integration-test
```

**Expected Results**:
- ✅ All services start without errors
- ✅ Daemon runs successfully
- ✅ Dashboard accessible and functional
- ✅ No conflicts in logs
- ✅ Settings changes persist

**Success Criteria**: All components work together ✅

---

## 🔴 Phase 4: Critical Trading Logic Validation

### Test 4.1: Paper Trading Mode Safety

**Objective**: Ensure no real trades in paper mode

**Steps**:
```bash
# Test 1: Verify paper mode setting
python -c "
import json
with open('settings.json') as f:
    s = json.load(f)
    assert s['app_settings']['paper_trading_mode'] == True
    print('✅ Paper mode enabled')
"

# Test 2: Start daemon and monitor
python bot_daemon.py start
tail -f daemon.log | grep -E "BUY|SELL|PAPER"

# Test 3: Check database after 10 minutes
sleep 600
sqlite3 database/trades.db "SELECT COUNT(*) FROM trades WHERE source='BOT';"

# Test 4: Verify no real broker API calls
# Check logs for "SIMULATION" or "MOCK" messages
grep -i "simulation\|mock" daemon.log

# Test 5: Stop daemon
python bot_daemon.py stop
```

**Expected Results**:
- ✅ Paper mode flag is true
- ✅ Logs show "PAPER TRADING" mode
- ✅ Mock prices used (not real API calls)
- ✅ Trades logged with simulation flag

**Success Criteria**: No real trades executed ✅

---

### Test 4.2: "Never Sell Below Entry" Validation

**Objective**: Confirm sell protection works in live scenario

**Steps**:
```bash
# Test 1: Setup scenario in settings.json
python -c "
import json
with open('settings.json', 'r+') as f:
    s = json.load(f)
    s['risk']['never_sell_at_loss'] = True
    s['strategies']['rsi_mean_reversion']['sell_rsi_threshold'] = 70
    f.seek(0)
    json.dump(s, f, indent=2)
    f.truncate()
print('✅ Never sell at loss enabled')
"

# Test 2: Run daemon and watch for HOLD messages
python bot_daemon.py start
tail -f daemon.log | grep -E "HOLD|⏸️"

# Test 3: After 15 minutes, check logs
sleep 900
grep -c "⏸️ HOLD" daemon.log
# Expected: > 0 if any stocks hit RSI sell signal below entry

# Test 4: Stop and analyze
python bot_daemon.py stop

# Test 5: Verify no sells at loss in database
sqlite3 database/trades.db "
SELECT symbol, action, price, timestamp
FROM trades
WHERE action='SELL'
ORDER BY timestamp DESC
LIMIT 10;
"
# Manual check: Ensure sell price > corresponding buy price
```

**Expected Results**:
- ✅ Setting enabled in config
- ✅ Logs show HOLD messages when appropriate
- ✅ No sells executed below entry price
- ✅ Database confirms no loss-making sells

**Success Criteria**: Protection works correctly ✅

---

## 👥 Phase 5: User Acceptance Testing (UAT)

### Test 5.1: End-to-End Workflow

**Objective**: Simulate complete user journey

**Scenario**: User wants to deploy bot to VPS and monitor from phone

**Steps**:

**Day 1: Local Setup**
```bash
# 1. Download bot to local machine
# (Assume user cloned repo)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure settings
# User edits settings.json with broker credentials

# 4. Test in paper mode locally
python dashboard_v2.py
# User starts bot, verifies it works

# 5. Test daemon locally
python bot_daemon.py start
python bot_daemon.py status
python bot_daemon.py stop
```

**Day 2: VPS Deployment**
```bash
# 6. Follow VPS_DEPLOYMENT.md guide
# User provisions DigitalOcean droplet
# User SSH's into VPS
# User follows 13-step guide

# 7. Deploy to VPS
# Upload settings.json
# Clone repo
# Install dependencies
# Create systemd service
# Start services

# 8. Access mobile dashboard
# Open phone browser
# Navigate to http://VPS_IP:8501
# Login with password
```

**Day 3: Monitoring**
```bash
# 9. Check dashboard from phone
# View P&L
# Check active positions
# Review trades

# 10. View logs
# Use System Logs tab
# Search for errors

# 11. Stop bot remotely
# SSH to VPS
# sudo systemctl stop arun-bot
```

**Expected User Experience**:
- ✅ Clear setup instructions (no confusion)
- ✅ All features work as documented
- ✅ Dashboard accessible from mobile
- ✅ Bot runs reliably 24/7
- ✅ Easy to stop/start/monitor

**Success Criteria**: Complete workflow works smoothly ✅

---

### Test 5.2: Settings GUI Usability

**Objective**: Verify enhanced settings tabs are intuitive

**Steps**:
```bash
# Test with a non-technical user (if possible)

# 1. Open settings
python dashboard_v2.py
# Click Settings

# 2. Navigate to new tabs
# Regime Monitor tab
# Stop Loss tab
# Paper/Live Trading tab
# API Test tab

# 3. Make changes
# Toggle paper/live mode
# Adjust stop loss percentage
# Test API connection

# 4. Save changes
# Verify settings persist

# 5. Restart bot
# Confirm changes applied
```

**Expected User Experience**:
- ✅ Tabs are clearly labeled
- ✅ Settings explanations are clear
- ✅ Save functionality is obvious
- ✅ Warnings are informative
- ✅ No technical jargon confusion

**Success Criteria**: User can navigate and use settings without help ✅

---

## 📊 Test Results Summary Template

Use this template to record test results:

```markdown
# Test Execution Results

**Date**: _________________
**Tester**: _______________
**Environment**: Local / VPS / Both

## Phase 1: Claude AI Components
- [ ] Test 1.1: Headless Daemon - PASS / FAIL
- [ ] Test 1.2: Mobile Dashboard - PASS / FAIL
- [ ] Test 1.3: VPS Deployment Guide - PASS / FAIL
- [ ] Test 1.4: Critical Trading Fix - PASS / FAIL

**Issues Found**:
1. _______________________________________________
2. _______________________________________________

## Phase 2: Google AI Components
- [ ] Test 2.1: Enhanced Settings GUI Tabs - PASS / FAIL
- [ ] Test 2.2: Symbol Validator Fix - PASS / FAIL

**Issues Found**:
1. _______________________________________________
2. _______________________________________________

## Phase 3: Integration Testing
- [ ] Test 3.1: Branch Compatibility - PASS / FAIL
- [ ] Test 3.2: Settings Manager Integration - PASS / FAIL
- [ ] Test 3.3: Full System Integration - PASS / FAIL

**Issues Found**:
1. _______________________________________________
2. _______________________________________________

## Phase 4: Critical Trading Logic
- [ ] Test 4.1: Paper Trading Safety - PASS / FAIL
- [ ] Test 4.2: Never Sell Below Entry - PASS / FAIL

**Issues Found**:
1. _______________________________________________
2. _______________________________________________

## Phase 5: User Acceptance Testing
- [ ] Test 5.1: End-to-End Workflow - PASS / FAIL
- [ ] Test 5.2: Settings GUI Usability - PASS / FAIL

**Issues Found**:
1. _______________________________________________
2. _______________________________________________

## Overall Result
- **Total Tests**: 12
- **Passed**: ___
- **Failed**: ___
- **Pass Rate**: ___%

**Recommendation**: APPROVE FOR PRODUCTION / NEEDS FIXES

**Notes**:
_______________________________________________
_______________________________________________
```

---

## 🚨 Critical Issues Checklist

Before going to production, ensure these are verified:

**Security**:
- [ ] No hardcoded credentials in code
- [ ] settings.json not committed to GitHub
- [ ] Mobile dashboard password changed from default
- [ ] Firewall configured on VPS
- [ ] SSH key-based auth enabled on VPS

**Reliability**:
- [ ] Daemon restarts on crash (systemd)
- [ ] Logs rotate (don't fill disk)
- [ ] Database backups configured
- [ ] Error handling tested

**Trading Safety**:
- [ ] Paper mode works correctly
- [ ] Never sell at loss protection working
- [ ] Capital limits enforced
- [ ] Position tagging working (BOT vs MANUAL)

**Documentation**:
- [ ] All README files updated
- [ ] AI_HANDOVER.md current
- [ ] VPS_DEPLOYMENT.md tested
- [ ] TEST_PLAN.md (this file) complete

---

## 📞 Support & Escalation

If tests fail:

1. **Check Logs**:
   - `daemon.log` - Daemon errors
   - `streamlit` terminal - Dashboard errors
   - `journalctl -u arun-bot -n 100` - Systemd logs

2. **Review Documentation**:
   - `AI_HANDOVER.md` - Technical details
   - `VPS_DEPLOYMENT.md` - Setup issues
   - `GAP_ANALYSIS.md` - Known issues

3. **GitHub Issues**:
   - Report at: https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot/issues

---

**Version**: 1.0
**Last Updated**: January 18, 2026
**Status**: Ready for execution
