# 🧪 Testing Guide for Non-Technical Users

**For**: Anyone who wants to test the bot (no coding knowledge needed)
**Time**: 10 minutes
**Prerequisites**: Completed WINDOWS_SETUP_GUIDE.md

---

## 🎯 What You'll Test

- ✅ Bot daemon (background bot)
- ✅ Mobile dashboard (web monitoring)
- ✅ Desktop GUI (existing app)
- ✅ All features working together

**Goal**: Make sure everything works before you use it for real trading

---

## ⚡ Quick Test (10 Minutes)

### Test 1: Start the Bot (2 minutes)

1. **Open File Explorer**
2. **Go to**: `C:\Antigravity\TradingBots-Aruns Project`
3. **Double-click**: `LAUNCH_BOT_DAEMON.bat`
4. **You'll see**: Black window with green text
5. **Look for**: "✅ Bot started successfully!"
6. **Wait 5 seconds**, then **close the window**

**✅ Success**: Bot is now running in background

**❌ If Error**: See "Troubleshooting" section

---

### Test 2: Check Bot Status (1 minute)

1. **Double-click**: `CHECK_BOT_STATUS.bat`
2. **You'll see**: "Bot RUNNING (PID: XXXX)"
3. **Close the window**

**✅ Success**: Bot is active

**❌ If "NOT running"**: Repeat Test 1

---

### Test 3: Open Mobile Dashboard (3 minutes)

1. **Double-click**: `LAUNCH_DASHBOARD.bat`
2. **Wait 10-15 seconds**
3. **Browser opens automatically** to http://localhost:8501
4. **Login screen appears**
5. **Type password**: `arun2026`
6. **Press Tab** (not Enter - this triggers login)

**You should see**:
- Dashboard tab (with cards showing stats)
- Sidebar with 5 options: Dashboard, Positions, Trades History, System Logs, Settings

**Test Each Tab**:
- Click "Positions" → See positions table (may be empty)
- Click "Trades History" → See trades list (may be empty if just started)
- Click "System Logs" → See daemon.log contents
- Click "Settings" → See your configuration

**✅ Success**: All tabs load without errors

**❌ If Error**: See "Troubleshooting" section

---

### Test 4: Desktop GUI (2 minutes)

1. **In another window**, double-click: `LAUNCH_DESKTOP_GUI.bat`
2. **Wait 5-10 seconds**
3. **Desktop app opens** (the one you're used to)
4. **Check**: All tabs load (Dashboard, Strategies, Knowledge, Settings)

**✅ Success**: Desktop app works as before

---

### Test 5: Stop the Bot (1 minute)

1. **Close desktop GUI** (click X)
2. **Close browser** (dashboard)
3. **Double-click**: `STOP_BOT.bat`
4. **You'll see**: "✅ Bot stopped successfully!"
5. **Close window**

**✅ Success**: Bot stopped cleanly

---

### Test 6: Verify Bot Stopped (1 minute)

1. **Double-click**: `CHECK_BOT_STATUS.bat`
2. **You'll see**: "Bot NOT running"
3. **Close window**

**✅ Success**: Everything works!

---

## 🎉 All Tests Passed?

**Congratulations!** Your bot is ready to use.

**What You Just Tested**:
- ✅ Bot starts and stops correctly
- ✅ Mobile dashboard accessible
- ✅ Desktop GUI still works
- ✅ No conflicts between components

---

## 📱 Bonus Test: Access from Phone

**If you want to test mobile access**:

### Step 1: Find Your Computer's IP

1. Press `Windows + R`
2. Type: `cmd`
3. Press Enter
4. Type: `ipconfig`
5. Look for "IPv4 Address" (example: `192.168.1.100`)
6. **Write it down**: _______________

### Step 2: Start Dashboard on Computer

1. **On computer**: Double-click `LAUNCH_DASHBOARD.bat`
2. **Wait for browser to open**

### Step 3: Access from Phone

1. **On phone**: Connect to **same WiFi** as computer
2. **Open browser** (Chrome, Safari, etc.)
3. **Type in address bar**: `http://YOUR_IP:8501`
   - Example: `http://192.168.1.100:8501`
4. **Press Go**
5. **Login**: `arun2026`

**✅ Success**: You can monitor bot from your phone!

---

## 🛡️ Safety Check

Before using for real trading, verify these:

### Check 1: Paper Trading Mode

1. **Open File Explorer**
2. **Go to**: `C:\Antigravity\TradingBots-Aruns Project`
3. **Right-click**: `settings.json`
4. **Click**: "Open with" → "Notepad"
5. **Find line**: `"paper_trading_mode"`
6. **Verify**: It says `true`
7. **If false**: Change to `true`, Save (Ctrl+S), Close

**Why?**: Paper mode = no real trades, safe testing

### Check 2: Database is Clean

**First time running?** This is normal:
- Trades History tab: Empty
- Positions tab: Empty
- Dashboard: Shows $0

**After running for a while** (in paper mode):
- Trades History: Shows simulated trades
- Positions: Shows simulated positions
- Dashboard: Shows simulated P&L

**This is expected!** Paper mode creates fake data for testing.

---

## 🚀 Daily Usage (Simple)

### Morning Routine (1 minute):

1. **Start bot**: Double-click `LAUNCH_BOT_DAEMON.bat`
2. **Check status**: Double-click `CHECK_BOT_STATUS.bat`
3. **Done!** Bot is running

### During the Day (Anytime):

**Option A**: Use Mobile Dashboard
1. Double-click `LAUNCH_DASHBOARD.bat`
2. Browser opens, login, check P&L

**Option B**: Use Desktop GUI
1. Double-click `LAUNCH_DESKTOP_GUI.bat`
2. GUI opens, see everything

**Option C**: Use Phone (Same WiFi)
1. Start dashboard on computer
2. Access from phone: `http://YOUR_IP:8501`

### Evening Routine (1 minute):

1. **Stop bot**: Double-click `STOP_BOT.bat`
2. **Verify**: Double-click `CHECK_BOT_STATUS.bat` (should say "NOT running")
3. **Done!** Bot is stopped

---

## ⚠️ Troubleshooting

### Problem: "Python is not recognized"

**Fix**:
1. Install Python (see WINDOWS_SETUP_GUIDE.md)
2. Make sure you checked ☑️ "Add Python to PATH" during installation
3. Restart computer
4. Try again

### Problem: "streamlit is not recognized"

**Fix**:
1. Open Command Prompt (Windows + R, type `cmd`, Enter)
2. Type:
   ```
   cd "C:\Antigravity\TradingBots-Aruns Project"
   pip install streamlit
   ```
3. Wait for installation
4. Try again

### Problem: Dashboard won't open in browser

**Fix**:
1. Close all Command Prompt windows
2. Double-click `STOP_BOT.bat`
3. Wait 5 seconds
4. Double-click `LAUNCH_DASHBOARD.bat`
5. Manually open browser and go to: http://localhost:8501

### Problem: "Port 8501 already in use"

**Fix**:
1. Close all browser tabs
2. Close all Command Prompt windows
3. Wait 10 seconds
4. Try again

### Problem: Can't access from phone

**Fix**:
1. **Check WiFi**: Phone and computer on same network?
2. **Check IP**: Did you use correct IP address?
3. **Check firewall**: Windows Firewall might be blocking
   - Go to Windows Defender Firewall
   - Click "Allow an app through firewall"
   - Find "Python" and check both Private and Public
   - Click OK
4. Try again

### Problem: Bot won't start

**Fix**:
1. Double-click `STOP_BOT.bat`
2. Open File Explorer
3. Go to: `C:\Antigravity\TradingBots-Aruns Project`
4. Delete file: `bot_daemon.pid` (if it exists)
5. Double-click `LAUNCH_BOT_DAEMON.bat`

### Problem: Desktop GUI won't open

**Fix**:
1. Check paper_trading_mode is `true` in settings.json
2. Try launching from Command Prompt instead:
   ```
   cd "C:\Antigravity\TradingBots-Aruns Project"
   python dashboard_v2.py
   ```
3. Look for error messages
4. Share error with support

---

## 📞 Need Help?

**Before asking for help**, try these:

1. **Close everything**:
   - All Command Prompt windows
   - All browser tabs
   - Desktop GUI

2. **Restart bot**:
   - Double-click `LAUNCH_BOT_DAEMON.bat`
   - Double-click `CHECK_BOT_STATUS.bat` (verify running)

3. **Check logs**:
   - Open File Explorer
   - Go to: `C:\Antigravity\TradingBots-Aruns Project`
   - Open file: `daemon.log`
   - Look for errors (lines with "ERROR" or "FAIL")

4. **Still stuck?**:
   - Screenshot the error
   - Note which launcher you used
   - Report issue with details

---

## ✅ You're Ready!

**What you know now**:
- ✅ How to start/stop bot (single-click)
- ✅ How to check status
- ✅ How to use mobile dashboard
- ✅ How to use desktop GUI
- ✅ How to access from phone
- ✅ How to troubleshoot common issues

**Next Steps**:
1. **Practice**: Start/stop bot a few times
2. **Explore**: Click around the dashboard, get familiar
3. **Monitor**: Let bot run for a day in paper mode
4. **Decide**: Keep using locally, or deploy to VPS?

---

## 🎓 When to Switch to Live Trading

**DO NOT** switch to live trading until:
- ✅ You've tested in paper mode for at least 1 week
- ✅ You understand how the bot works
- ✅ You're comfortable with all the launchers
- ✅ You've seen it handle different market conditions
- ✅ You trust the bot's decisions

**To switch to live trading** (when ready):
1. Open `settings.json`
2. Change: `"paper_trading_mode": false`
3. Add your real broker credentials
4. Save and close
5. Restart bot

**WARNING**: Live trading uses real money. Start with small amounts!

---

**Version**: 1.0
**Last Updated**: January 18, 2026
**For**: Non-technical users
