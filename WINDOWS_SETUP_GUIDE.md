# 🪟 Windows Setup Guide - For Non-Technical Users

**For**: Windows users who want to test the bot locally
**Time**: 15-20 minutes (one-time setup)
**After Setup**: Single-click to launch!

---

## 📋 Prerequisites (One-Time Setup)

### Step 1: Install Python (If Not Installed)

1. **Check if Python is installed**:
   - Press `Windows + R`
   - Type: `cmd`
   - Press Enter
   - Type: `python --version`
   - Press Enter

2. **If you see "Python 3.X.X"**: ✅ Skip to Step 2

3. **If you see error**: Install Python:
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.12.X" (latest version)
   - Run the installer
   - **IMPORTANT**: Check ☑️ "Add Python to PATH"
   - Click "Install Now"
   - Wait for installation
   - Restart your computer

### Step 2: Install Git (If Not Installed)

1. **Check if Git is installed**:
   - Press `Windows + R`
   - Type: `cmd`
   - Press Enter
   - Type: `git --version`
   - Press Enter

2. **If you see "git version X.X.X"**: ✅ Skip to Step 3

3. **If you see error**: Install Git:
   - Go to: https://git-scm.com/download/win
   - Download "64-bit Git for Windows Setup"
   - Run the installer
   - Keep clicking "Next" (default options are fine)
   - Click "Finish"
   - Restart your computer

---

## 🚀 Setup Instructions (Follow Exactly)

### Step 1: Create Your Project Folder

1. **Open File Explorer** (Windows + E)
2. **Navigate to**: `C:\Antigravity\`
3. **If "Antigravity" folder doesn't exist**:
   - Right-click in C:\ drive
   - Click "New" → "Folder"
   - Name it: `Antigravity`
   - Press Enter

4. **Check if you already have files**:
   - Open `C:\Antigravity\TradingBots-Aruns Project`
   - If folder is **empty** or doesn't exist: Continue
   - If folder has **files already**: See "Already Have Files?" section below

---

### Step 2: Download the Bot Code

**Open Command Prompt**:
1. Press `Windows + R`
2. Type: `cmd`
3. Press Enter

**Navigate to Your Folder**:
```cmd
cd C:\Antigravity
```

**Download the Code** (choose ONE option):

**Option A: Fresh Download (Recommended)**
```cmd
git clone https://github.com/BratAIExplorer/TradingBot_Arun-Jay_Pilot.git "TradingBots-Aruns Project"
cd "TradingBots-Aruns Project"
```

**Option B: If Folder Already Exists with Old Code**
```cmd
cd "TradingBots-Aruns Project"
git pull origin main
```

---

### Step 3: Switch to the Testing Branch

**Important**: The latest code is on `claude/sync-github-remote-3461O` branch, not `main`.

```cmd
git fetch --all
git checkout claude/sync-github-remote-3461O
```

**You'll see**: `Switched to branch 'claude/sync-github-remote-3461O'`

---

### Step 4: Install Dependencies (Automatic)

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Wait**: This takes 2-5 minutes. You'll see packages installing.

**When done**, you'll see: `Successfully installed...`

---

### Step 5: Configure Settings (First Time Only)

**Check if settings.json exists**:
```cmd
dir settings.json
```

**If file exists**: Skip to Step 6

**If file doesn't exist**: Create it:
```cmd
copy settings_template.json settings.json
```

**Edit Settings** (Important!):
1. Right-click `settings.json`
2. Click "Open with" → "Notepad"
3. Find line: `"paper_trading_mode": false`
4. Change to: `"paper_trading_mode": true`
5. Save (Ctrl+S)
6. Close Notepad

**Why?**: Paper mode = safe testing, no real trades

---

### Step 6: Create Single-Click Launchers

**I'll create these files for you**. Just copy-paste into Notepad and save:

**File 1: LAUNCH_BOT_DAEMON.bat**
```batch
@echo off
title ARUN Bot Daemon
color 0A
echo ====================================
echo   ARUN Trading Bot - Daemon Launcher
echo ====================================
echo.

cd /d "C:\Antigravity\TradingBots-Aruns Project"

echo Starting bot daemon...
python bot_daemon.py start

echo.
echo ✅ Bot started successfully!
echo.
echo To check status: python bot_daemon.py status
echo To stop: python bot_daemon.py stop
echo.
pause
```

**How to Create**:
1. Open Notepad
2. Copy-paste the above code
3. Click "File" → "Save As"
4. Navigate to: `C:\Antigravity\TradingBots-Aruns Project`
5. File name: `LAUNCH_BOT_DAEMON.bat`
6. Save as type: "All Files (*.*)"
7. Click "Save"

---

**File 2: LAUNCH_DASHBOARD.bat**
```batch
@echo off
title ARUN Mobile Dashboard
color 0B
echo ====================================
echo   ARUN Bot - Mobile Dashboard
echo ====================================
echo.

cd /d "C:\Antigravity\TradingBots-Aruns Project"

echo Starting mobile dashboard...
echo.
echo Dashboard will open in your browser at:
echo http://localhost:8501
echo.
echo Password: arun2026
echo.
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run mobile_dashboard.py --server.port 8501

pause
```

**How to Create**: Same as above, but save as `LAUNCH_DASHBOARD.bat`

---

**File 3: LAUNCH_DESKTOP_GUI.bat**
```batch
@echo off
title ARUN Desktop GUI
color 0E
echo ====================================
echo   ARUN Bot - Desktop GUI
echo ====================================
echo.

cd /d "C:\Antigravity\TradingBots-Aruns Project"

echo Starting desktop application...
python dashboard_v2.py

pause
```

**How to Create**: Same as above, but save as `LAUNCH_DESKTOP_GUI.bat`

---

**File 4: CHECK_BOT_STATUS.bat**
```batch
@echo off
title ARUN Bot Status
color 0C
echo ====================================
echo   ARUN Bot - Status Checker
echo ====================================
echo.

cd /d "C:\Antigravity\TradingBots-Aruns Project"

python bot_daemon.py status

echo.
pause
```

**How to Create**: Same as above, but save as `CHECK_BOT_STATUS.bat`

---

**File 5: STOP_BOT.bat**
```batch
@echo off
title ARUN Bot - Stop
color 0C
echo ====================================
echo   ARUN Bot - Stop Daemon
echo ====================================
echo.

cd /d "C:\Antigravity\TradingBots-Aruns Project"

python bot_daemon.py stop

echo.
echo ✅ Bot stopped successfully!
echo.
pause
```

**How to Create**: Same as above, but save as `STOP_BOT.bat`

---

## ✅ You're Done! Now You Can Launch

**Your folder now has**:
```
C:\Antigravity\TradingBots-Aruns Project\
├── LAUNCH_BOT_DAEMON.bat      ← Double-click to start bot
├── LAUNCH_DASHBOARD.bat        ← Double-click to open web dashboard
├── LAUNCH_DESKTOP_GUI.bat      ← Double-click to open desktop app
├── CHECK_BOT_STATUS.bat        ← Double-click to check if running
├── STOP_BOT.bat                ← Double-click to stop bot
├── (all other project files)
```

**Single-Click Launch**:
1. Open File Explorer
2. Navigate to: `C:\Antigravity\TradingBots-Aruns Project`
3. **Double-click**: `LAUNCH_BOT_DAEMON.bat`
4. **Double-click**: `LAUNCH_DASHBOARD.bat`

**That's it!** 🎉

---

## 📱 How to Use

### Daily Usage (Single-Click):

**Morning** (Start Bot):
1. Double-click: `LAUNCH_BOT_DAEMON.bat`
2. Window opens, says "Bot started"
3. Close window (bot runs in background)

**Monitor from Computer**:
1. Double-click: `LAUNCH_DASHBOARD.bat`
2. Browser opens automatically
3. Login: `arun2026`
4. Check P&L, trades, positions

**OR Use Desktop App**:
1. Double-click: `LAUNCH_DESKTOP_GUI.bat`
2. GUI opens (same as before)

**Check Status**:
1. Double-click: `CHECK_BOT_STATUS.bat`
2. Shows if bot is running

**Evening** (Stop Bot):
1. Double-click: `STOP_BOT.bat`
2. Bot stops gracefully

---

## 🌐 Access from Phone (Same WiFi)

### Find Your Computer's IP:

1. Press `Windows + R`
2. Type: `cmd`
3. Press Enter
4. Type: `ipconfig`
5. Press Enter
6. Look for "IPv4 Address": Example: `192.168.1.100`

### Access from Phone:

1. Connect phone to **same WiFi** as computer
2. Start dashboard on computer: Double-click `LAUNCH_DASHBOARD.bat`
3. On phone browser, go to: `http://YOUR_IP:8501`
   - Example: `http://192.168.1.100:8501`
4. Login: `arun2026`

**Works perfectly!** No VPS needed.

---

## 🔧 Troubleshooting

### Error: "python is not recognized"
**Fix**:
1. Reinstall Python
2. Make sure to check ☑️ "Add Python to PATH"
3. Restart computer

### Error: "git is not recognized"
**Fix**:
1. Install Git (see Step 2 in Prerequisites)
2. Restart computer

### Error: "streamlit is not recognized"
**Fix**:
```cmd
cd "C:\Antigravity\TradingBots-Aruns Project"
pip install streamlit
```

### Error: Port 8501 already in use
**Fix**:
1. Close all browser tabs showing the dashboard
2. Try again

### Dashboard won't open
**Fix**:
1. Stop bot: Double-click `STOP_BOT.bat`
2. Close all Command Prompt windows
3. Restart: Double-click `LAUNCH_DASHBOARD.bat`

---

## 📚 What Each Launcher Does

| File | What It Does | When to Use |
|------|--------------|-------------|
| **LAUNCH_BOT_DAEMON.bat** | Starts trading bot in background | Every morning (or when you want bot to run) |
| **LAUNCH_DASHBOARD.bat** | Opens web monitoring dashboard | When you want to check P&L, trades, positions |
| **LAUNCH_DESKTOP_GUI.bat** | Opens desktop application | When you want full desktop experience |
| **CHECK_BOT_STATUS.bat** | Shows if bot is running | Anytime you're unsure if bot is active |
| **STOP_BOT.bat** | Stops the trading bot | Every evening (or when you're done) |

---

## 🎓 Understanding Branches (Simple Explanation)

### What's a Branch?

Think of branches like **different versions** of your bot:

- **main** = Old stable version (before Phase 4)
- **claude/sync-github-remote-3461O** = My latest work (VPS deployment)
- **google/enhanced-settings-gui** = Google's latest work (new settings tabs)

### Which Branch Should You Use?

**For Testing Everything**: `claude/sync-github-remote-3461O` ← **THIS ONE**

**Why?**: It has all my latest work (daemon, dashboard, critical fixes)

### Will "main" Branch Be Overwritten?

**No!** Branches are separate. Think of them like folders:

```
Your Repository (like a big folder)
├── main/ (old version - still there, unchanged)
├── claude/sync-github-remote-3461O/ (my work - this is what you're using)
└── google/enhanced-settings-gui/ (Google's work - separate)
```

When ready, we'll **merge** (combine) the branches into `main`. But for now, they're all separate and safe.

---

## 🔄 How to Update Code Later

**If we push new changes**:

1. Open Command Prompt
2. Navigate to your folder:
   ```cmd
   cd "C:\Antigravity\TradingBots-Aruns Project"
   ```
3. Download updates:
   ```cmd
   git pull
   ```
4. Install any new dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
5. Done! Your launchers still work.

---

## ✅ You're All Set!

**Your Setup**:
- ✅ Code downloaded to: `C:\Antigravity\TradingBots-Aruns Project`
- ✅ Using branch: `claude/sync-github-remote-3461O` (latest)
- ✅ Single-click launchers created
- ✅ No VPS needed (runs on your computer)
- ✅ Can access from phone (same WiFi)

**Next Steps**:
1. Test the bot (see next guide: "TESTING_FOR_NON_TECHIES.md")
2. Use it daily with single-click launchers
3. When happy, optionally deploy to VPS (for 24/7)

---

**Version**: 1.0
**Last Updated**: January 18, 2026
**For**: Windows users (non-technical)
