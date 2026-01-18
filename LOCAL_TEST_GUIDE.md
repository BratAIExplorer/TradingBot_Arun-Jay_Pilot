# 🏠 Local Testing Guide - No VPS Required

**Purpose**: Test all Phase 4 features on your local machine (laptop/desktop)
**Requirements**: Python 3.8+, your computer, NO VPS needed
**Time**: 20-30 minutes
**Works On**: Windows, Mac, Linux

---

## ✅ What You Can Test Locally

**Everything!** Including:
- ✅ Bot daemon (headless mode)
- ✅ Mobile dashboard (Streamlit UI)
- ✅ Desktop GUI (existing)
- ✅ Settings tabs (Google AI's work)
- ✅ Symbol validator
- ✅ Paper trading mode
- ✅ Live trading (if you have credentials)
- ✅ Integration between all components

**What You CAN'T Test Locally**:
- ❌ 24/7 operation (computer must stay on)
- ❌ Systemd service (Linux VPS feature)
- ❌ Remote access from outside your home network

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone and Setup
```bash
# If you haven't already
git clone https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git
cd TradingBot_Arun-Jay_Pilot

# Switch to testing branch
git checkout claude/sync-github-remote-3461O

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Enable Paper Trading
```bash
# Edit settings.json
# Set "paper_trading_mode": true

# Or use this command:
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
```

### Step 3: Test Daemon (Locally)
```bash
# Start daemon in foreground (for testing)
python bot_daemon.py run

# Press Ctrl+C after 1 minute to stop

# OR run in background
python bot_daemon.py start
python bot_daemon.py status
python bot_daemon.py stop
```

### Step 4: Test Mobile Dashboard (Locally)
```bash
# Start dashboard
streamlit run mobile_dashboard.py

# Open browser automatically
# Or manually: http://localhost:8501

# Login: arun2026 (default password)

# Check all 5 tabs work
```

### Step 5: Done! ✅
All core features tested locally in 5 minutes.

---

## 📱 Bonus: Access Dashboard from Your Phone (Same WiFi)

### Find Your Computer's Local IP:

**Windows**:
```cmd
ipconfig | findstr IPv4
```

**Mac/Linux**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Example Output**: `192.168.1.100`

### Access from Phone:
1. Ensure phone is on **same WiFi** as your computer
2. Start dashboard on computer:
   ```bash
   streamlit run mobile_dashboard.py --server.address 0.0.0.0 --server.port 8501
   ```
3. On phone browser: `http://YOUR_COMPUTER_IP:8501`
   - Example: `http://192.168.1.100:8501`

**Works perfectly without VPS!** 🎉

---

## 🧪 Comprehensive Local Testing (30 Minutes)

### Test 1: Claude AI - Bot Daemon (5 min)
```bash
# Switch to Claude's branch
git checkout claude/sync-github-remote-3461O

# Start daemon
python bot_daemon.py start

# Check it's running
python bot_daemon.py status
# Should show: "Bot RUNNING (PID: XXXX)"

# View logs
tail -20 daemon.log

# Check for activity (wait 2 minutes)
tail -f daemon.log
# Press Ctrl+C

# Stop daemon
python bot_daemon.py stop

# Verify stopped
python bot_daemon.py status
# Should show: "Bot NOT running"
```

**✅ Pass Criteria**: Starts, runs, stops cleanly

---

### Test 2: Claude AI - Mobile Dashboard (5 min)
```bash
# Start dashboard (same branch)
streamlit run mobile_dashboard.py --server.port 8501

# Browser opens automatically to http://localhost:8501

# Test each tab:
# 1. Dashboard - Check P&L displays
# 2. Positions - Check active positions table
# 3. Trades History - Filter by symbol, date
# 4. System Logs - Search for "BUY" or "SELL"
# 5. Settings - Verify read-only config display

# Try auto-refresh (5-second updates)
# Try CSV export from Trades tab

# Stop: Press Ctrl+C in terminal
```

**✅ Pass Criteria**: All 5 tabs load, no errors

---

### Test 3: Google AI - Settings Tabs (10 min)
```bash
# Switch to Google's branch
git checkout google/enhanced-settings-gui

# Test each tab individually:

# Tab 1: Regime Monitor
python gui/settings_tabs/regime_tab.py
# GUI opens - check settings load
# Close window

# Tab 2: Stop Loss Settings
python gui/settings_tabs/stop_loss_tab.py
# GUI opens - adjust stop loss %
# Save settings
# Close window

# Tab 3: Paper/Live Trading Toggle
python gui/settings_tabs/paper_live_tab.py
# GUI opens - toggle mode
# Check warning appears
# Close window

# Tab 4: API Test
python gui/settings_tabs/api_test_tab.py
# GUI opens - test connection
# (May fail if no credentials - that's OK)
# Close window

# Test imports
python -c "
from gui.settings_tabs import RegimeTab, StopLossTab, PaperLiveTab, APITestTab
print('✅ All tabs import successfully')
"
```

**✅ Pass Criteria**: All 4 tabs open without crashes

---

### Test 4: Google AI - Symbol Validator (2 min)
```bash
# Still on Google's branch
python -c "
from symbol_validator import validate_symbol

# Test invalid symbol
result = validate_symbol('FAKESTK', 'NSE')
print(f'FAKESTK (invalid): {result}')  # Should be False

# Test valid symbol
result = validate_symbol('RELIANCE', 'NSE')
print(f'RELIANCE (valid): {result}')  # Should be True

print('✅ Validator working correctly')
"
```

**✅ Pass Criteria**: FAKESTK=False, RELIANCE=True

---

### Test 5: Integration Test (8 min)
```bash
# Create test integration branch
git checkout -b local-integration-test
git merge claude/sync-github-remote-3461O
git merge google/enhanced-settings-gui

# Should merge cleanly (no conflicts)

# Test 1: Start daemon
python bot_daemon.py start

# Test 2: Start dashboard (in new terminal)
streamlit run mobile_dashboard.py --server.port 8501 &

# Test 3: Open desktop GUI (in new terminal)
python dashboard_v2.py &

# Let all three run for 5 minutes
sleep 300

# Check logs for errors
grep -i "error\|traceback" daemon.log

# Stop all
python bot_daemon.py stop
# Kill streamlit and GUI (Ctrl+C or pkill)

# Clean up test branch
git checkout claude/sync-github-remote-3461O
git branch -D local-integration-test
```

**✅ Pass Criteria**: All 3 components run simultaneously, no conflicts

---

## 📊 Local Test Results Checklist

**Claude AI Components**:
- [ ] Daemon starts/stops correctly
- [ ] Daemon logs activity to daemon.log
- [ ] Mobile dashboard loads all 5 tabs
- [ ] Dashboard shows real data (if daemon running)
- [ ] Dashboard accessible from phone (same WiFi)

**Google AI Components**:
- [ ] All 4 settings tabs import successfully
- [ ] Each tab opens without errors
- [ ] Settings save and persist
- [ ] Symbol validator correctly identifies valid/invalid stocks

**Integration**:
- [ ] No conflicts when merging branches
- [ ] Daemon + Dashboard run together
- [ ] All components use same settings.json
- [ ] No database conflicts

**Paper Trading Safety**:
- [ ] Paper mode enabled in settings
- [ ] No real broker API calls made
- [ ] Mock prices used for simulation
- [ ] Trades logged with simulation flag

---

## 🎯 Common Issues & Solutions

### Issue: "Module not found: streamlit"
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

### Issue: "Port 8501 already in use"
```bash
# Solution: Kill existing streamlit process
pkill streamlit

# Or use different port:
streamlit run mobile_dashboard.py --server.port 8502
```

### Issue: "Can't access dashboard from phone"
```bash
# Solution: Use 0.0.0.0 to allow external access
streamlit run mobile_dashboard.py --server.address 0.0.0.0 --server.port 8501

# Ensure phone is on SAME WiFi network
```

### Issue: "Daemon won't start"
```bash
# Solution: Check if already running
python bot_daemon.py status

# If stuck, remove PID file
rm bot_daemon.pid

# Try again
python bot_daemon.py start
```

### Issue: "Settings tabs won't open"
```bash
# Solution: Switch to correct branch
git checkout google/enhanced-settings-gui

# Verify files exist
ls -la gui/settings_tabs/
```

---

## 🚀 Advanced Local Testing

### Test Daemon Auto-Restart (Linux/Mac Only)
```bash
# Create local systemd-style service (for testing)
# This simulates VPS behavior on your local machine

# Create service file (Linux only)
sudo nano /etc/systemd/system/arun-bot-local.service

# Paste:
[Unit]
Description=ARUN Bot Local Test
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/TradingBot_Arun-Jay_Pilot
ExecStart=$HOME/TradingBot_Arun-Jay_Pilot/.venv/bin/python bot_daemon.py run
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable arun-bot-local
sudo systemctl start arun-bot-local

# Check status
sudo systemctl status arun-bot-local

# View logs
journalctl -u arun-bot-local -f

# Stop
sudo systemctl stop arun-bot-local
```

**Note**: This is optional and only works on Linux. Skip if on Windows/Mac.

---

## 📱 Mobile Testing Without VPS

### Setup Local Network Access:
1. **Start Dashboard with External Access**:
   ```bash
   streamlit run mobile_dashboard.py \
     --server.address 0.0.0.0 \
     --server.port 8501
   ```

2. **Find Your Computer's IP** (see earlier section)

3. **Test from Phone**:
   - Connect phone to same WiFi
   - Open browser: `http://YOUR_IP:8501`
   - Login with password
   - Test all tabs

4. **Test Mobile Responsiveness**:
   - Portrait mode ✓
   - Landscape mode ✓
   - Pinch to zoom ✓
   - Scrolling ✓
   - Button taps ✓

**Works perfectly on local network!** No VPS needed.

---

## 🎓 When Do You Actually Need VPS?

**You DON'T need VPS if**:
- ✅ You only trade during market hours (9:15 AM - 3:30 PM)
- ✅ You can keep your computer on during trading hours
- ✅ You're OK manually starting/stopping the bot
- ✅ You're testing or developing features

**You DO need VPS if**:
- ❌ You want bot to run 24/7 without your computer
- ❌ You travel frequently
- ❌ You want guaranteed uptime (99.9%)
- ❌ You want professional-grade deployment

**Bottom Line**: VPS is a **production deployment option**, not a testing requirement!

---

## ✅ Local Testing Complete!

After completing this guide, you will have tested:
- ✅ Bot daemon (headless mode)
- ✅ Mobile dashboard (Streamlit UI)
- ✅ Settings tabs (Google AI's work)
- ✅ Symbol validator
- ✅ Integration between components
- ✅ Mobile access from phone (same WiFi)

**All without any VPS!** 🎉

---

## 📞 Next Steps

**If Local Tests Pass**:
1. ✅ Mark Phase 4 as validated
2. ✅ Optionally deploy to VPS (see VPS_DEPLOYMENT.md)
3. ✅ Start using in paper mode locally
4. ✅ Switch to live trading when confident

**If You Want VPS Deployment**:
1. Follow `Documentation/VPS_DEPLOYMENT.md`
2. Use this local setup as a reference
3. VPS deployment is essentially the same, just on a cloud server

**For Your Friends**:
- Share this LOCAL_TEST_GUIDE.md
- They can test everything on their laptops
- No VPS costs or complexity

---

**Version**: 1.0
**Last Updated**: January 18, 2026
**Works On**: Windows, Mac, Linux (local machines)
