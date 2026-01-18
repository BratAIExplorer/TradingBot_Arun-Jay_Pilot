# ⚡ ARUN Bot - Quick Reference Card

**Print this and keep it handy!**

---

## 🚀 Daily Commands (Single-Click)

| What You Want | Double-Click This File |
|---------------|------------------------|
| **Start bot** | `LAUNCH_BOT_DAEMON.bat` |
| **Check if running** | `CHECK_BOT_STATUS.bat` |
| **Open dashboard** | `LAUNCH_DASHBOARD.bat` |
| **Open desktop app** | `LAUNCH_DESKTOP_GUI.bat` |
| **Stop bot** | `STOP_BOT.bat` |

---

## 📱 Access from Phone

1. **Find computer IP**:
   - Windows + R → `cmd` → `ipconfig`
   - Look for "IPv4 Address"

2. **On phone browser**:
   - `http://YOUR_IP:8501`
   - Example: `http://192.168.1.100:8501`

3. **Login**: `arun2026`

---

## 🛠️ Quick Fixes

| Problem | Solution |
|---------|----------|
| **Dashboard won't open** | Close all windows, double-click `STOP_BOT.bat`, try again |
| **Bot won't start** | Delete `bot_daemon.pid` file, try again |
| **Port already in use** | Close browser tabs, wait 10 seconds, try again |
| **Can't find commands** | Reinstall Python with "Add to PATH" checked |

---

## 📂 File Locations

**Bot folder**: `C:\Antigravity\TradingBots-Aruns Project`

**Important files**:
- `settings.json` - Your configuration
- `daemon.log` - Bot activity logs
- `database/trades.db` - Trade history

---

## 🔒 Safety Checklist

Before real trading:
- [ ] Paper mode enabled (`settings.json`)
- [ ] Tested for 1+ week
- [ ] Understand bot decisions
- [ ] Start with small amounts

---

## 📞 Support

**Before asking for help**:
1. Close everything
2. Double-click `STOP_BOT.bat`
3. Double-click `LAUNCH_BOT_DAEMON.bat`
4. Try again

**Still stuck?**:
- Check `daemon.log` for errors
- Screenshot the problem
- Note which launcher you used

---

## 🌳 Branch Info

**Use this branch**: `claude/sync-github-remote-3461O`

**To verify**:
```
cd "C:\Antigravity\TradingBots-Aruns Project"
git branch
```
Look for `*` next to the branch name.

---

## 🎯 Quick Test (5 min)

1. Double-click `LAUNCH_BOT_DAEMON.bat` ✓
2. Double-click `CHECK_BOT_STATUS.bat` (should say "RUNNING") ✓
3. Double-click `LAUNCH_DASHBOARD.bat` ✓
4. Login: `arun2026` ✓
5. Check all 5 tabs work ✓
6. Double-click `STOP_BOT.bat` ✓

**All passed?** You're ready! 🎉

---

**Last Updated**: January 18, 2026
