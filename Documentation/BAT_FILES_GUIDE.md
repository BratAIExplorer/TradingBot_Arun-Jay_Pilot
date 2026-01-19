# 🚀 BAT Files Quick Reference Guide

**ARUN Trading Bot - Windows Launcher Collection**

---

## 📋 Available BAT Files

### **1. START_HERE.bat** ⭐ First Time Setup
**Use when:** First time installing or fresh setup

**What it does:**
- ✅ Installs Python if missing
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Creates desktop shortcuts
- ✅ Launches the bot

**Command:**
```cmd
START_HERE.bat
```

**Time:** ~5-10 minutes (first run)

---

### **2. LAUNCH_DASHBOARD_ENHANCED.bat** ⭐ Recommended Daily Use
**Use when:** You want to launch the enhanced dashboard with all checks

**What it does:**
- ✅ Pre-flight system checks
- ✅ Checks for updates (optional)
- ✅ Validates Python syntax
- ✅ Verifies dependencies
- ✅ Activates virtual environment
- ✅ Launches enhanced dashboard with:
  - 💰 Account Balance Card
  - 📊 Bot Wallet Breakdown
  - 🔍 Holdings Filter (BOT/MANUAL)
- ✅ Creates session log

**Command:**
```cmd
LAUNCH_DASHBOARD_ENHANCED.bat
```

**Time:** ~5-10 seconds

**Features:**
- Auto-update check with user prompt
- Comprehensive error reporting
- Session logging
- Graceful error handling

---

### **3. QUICK_LAUNCH.bat** ⚡ Fast Start
**Use when:** You're in a hurry and everything is already set up

**What it does:**
- ⚡ Activates environment
- ⚡ Launches dashboard immediately
- ⚡ No checks, no delays

**Command:**
```cmd
QUICK_LAUNCH.bat
```

**Time:** ~2 seconds

**⚠️ Warning:** No error checking - use only if you're confident everything works

---

### **4. UPDATE_AND_FIX.bat** 🔧 Auto-Updater
**Use when:** You see merge conflicts or want to pull latest changes

**What it does:**
- ✅ Fetches latest code from GitHub
- ✅ **Auto-resolves merge conflicts**
- ✅ Validates Python syntax
- ✅ Checks documentation
- ✅ Prepares for launch

**Command:**
```cmd
UPDATE_AND_FIX.bat
```

**Time:** ~5-15 seconds

**Special:** Automatically resolves conflicts by accepting incoming changes for:
- `dashboard_v2.py`
- `settings_gui.py`

---

### **5. LAUNCH_ARUN.bat** (Original)
**Use when:** You want the original launcher (backward compatible)

**What it does:**
- Activates virtual environment
- Launches dashboard_v2.py
- Simple and straightforward

**Command:**
```cmd
LAUNCH_ARUN.bat
```

**Time:** ~2-3 seconds

---

## 🎯 Recommended Workflow

### **First Time User:**
```
1. START_HERE.bat           (One-time setup)
2. LAUNCH_DASHBOARD_ENHANCED.bat  (Daily use)
```

### **Daily Trader:**
```
Morning: LAUNCH_DASHBOARD_ENHANCED.bat
         (Checks for updates automatically)

Subsequent launches: QUICK_LAUNCH.bat
                     (Fast restart if needed)
```

### **After Seeing "Merge Conflict" Error:**
```
1. Close dashboard
2. UPDATE_AND_FIX.bat       (Auto-resolve conflicts)
3. LAUNCH_DASHBOARD_ENHANCED.bat  (Relaunch)
```

### **When Updates Available:**
```
Option 1 (Automatic):
  - LAUNCH_DASHBOARD_ENHANCED.bat will prompt you

Option 2 (Manual):
  1. UPDATE_AND_FIX.bat
  2. LAUNCH_DASHBOARD_ENHANCED.bat
```

---

## 🔧 Troubleshooting

### Issue: "Python not found"
**Solution:** Run `START_HERE.bat` to install Python

### Issue: "Virtual environment not found"
**Solution:** Run `START_HERE.bat` to create environment

### Issue: "Merge conflict in dashboard_v2.py"
**Solution:** Run `UPDATE_AND_FIX.bat` to auto-resolve

### Issue: Dashboard crashes immediately
**Solution:**
1. Check `settings.json` exists
2. Run `LAUNCH_DASHBOARD_ENHANCED.bat` (not QUICK_LAUNCH)
3. Check the session log file for errors

### Issue: "Dependencies missing"
**Solution:**
```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📊 Feature Comparison

| Feature | START_HERE | ENHANCED | QUICK | UPDATE_FIX | ORIGINAL |
|---------|------------|----------|-------|------------|----------|
| **First-time setup** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **System checks** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Update check** | ❌ | ✅ | ❌ | ✅ | ❌ |
| **Auto-fix conflicts** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Session logging** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Speed** | Slow | Medium | Fast | Medium | Fast |
| **Error reporting** | ✅ | ✅ | ❌ | ✅ | ⚠️ |

---

## 🎨 Dashboard Features (Enhanced Version)

When you launch `LAUNCH_DASHBOARD_ENHANCED.bat`, you get:

### **New Features:**

1. **💰 Account Balance Card**
   - Real-time balance from mStock API
   - Available cash display
   - Allocated capital tracking
   - Manual refresh button (🔄)
   - Auto-refresh every 15 minutes

2. **📊 Bot Wallet Breakdown**
   - Total allocated capital
   - Currently deployed amount
   - Visual progress bar
   - Color-coded warnings:
     - 🟢 Green (<70%): Healthy
     - 🟠 Orange (70-90%): Warning
     - 🔴 Red (>90%): Critical

3. **🔍 Enhanced Holdings Filter**
   - Filter: ALL / BOT / MANUAL
   - Icon indicators: 🤖 BOT / 👤 MANUAL
   - Color-coded backgrounds
   - Position statistics
   - P&L percentage column

### **How to Use:**

- **Refresh Balance:** Click the 🔄 button in top-right of balance card
- **Filter Holdings:** Click ALL / BOT / MANUAL buttons above table
- **Check Capital:** Watch the progress bar in Bot Wallet card
- **View Manual Stocks:** Click MANUAL filter to see non-bot holdings

---

## 📝 Session Logs

**Location:** Project root directory
**Format:** `dashboard_session_YYYYMMDD_HHMM.log`

**Contains:**
- Launch time
- All console output
- Error messages
- Exit code

**Example:**
```
dashboard_session_20260119_1530.log
```

---

## 🆘 Quick Help

### Run Dashboard with Enhanced Features:
```cmd
LAUNCH_DASHBOARD_ENHANCED.bat
```

### Fix Merge Conflicts:
```cmd
UPDATE_AND_FIX.bat
```

### Fast Launch (No Checks):
```cmd
QUICK_LAUNCH.bat
```

### Full Reinstall:
```cmd
del /q .venv
START_HERE.bat
```

---

## 📞 Support

**For issues:**
1. Check the session log file
2. Run `LAUNCH_DASHBOARD_ENHANCED.bat` for detailed diagnostics
3. Check `Documentation/DASHBOARD_ENHANCEMENTS.md` for feature documentation

**Common Log Locations:**
- Install log: `install.log`
- Session logs: `dashboard_session_*.log`
- Git output: Console window

---

**Last Updated:** January 19, 2026
**Version:** ARUN Titan V2 - Enhanced Dashboard Edition
