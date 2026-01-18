# Version Control & Code Safety Guidelines

**Document Purpose:** Ensure safe code modifications with rollback capability  
**For:** AI Agents (Gemini, Claude Code) and Human Developers  
**Last Updated:** January 18, 2026

---

## 🎯 Core Principle: "Do No Harm"

**Before modifying ANY existing file, create a safety checkpoint.**

---

## 📋 Version Control Workflow for AI Agents

### **Phase 1: Before Making Changes**

#### Step 1: Check Git Status
```powershell
# Check current branch
git branch

# Check if there are uncommitted changes
git status
```

#### Step 2: Create Feature Branch
```powershell
# Create descriptive branch name
git checkout -b feature/regime-monitor-integration

# Example naming convention:
# feature/[component-name]-[action]
# feature/regime-monitor-integration
# bugfix/paper-trading-exit
# enhancement/dashboard-charts
```

#### Step 3: Commit Current State (Baseline)
```powershell
# If there are uncommitted changes, commit them first
git add .
git commit -m "baseline: Save current working state before regime monitor integration"
```

---

### **Phase 2: Making Changes**

#### Incremental Commits Strategy

**Rule:** Commit after each logical change, not at the end of the day.

**Good commit pattern:**
```powershell
# Step 1: Import regime monitor
git add kickstart.py
git commit -m "feat: Import RegimeMonitor in kickstart.py"

# Step 2: Initialize monitor
git add kickstart.py
git commit -m "feat: Initialize regime_monitor instance in main()"

# Step 3: Add regime check
git add kickstart.py
git commit -m "feat: Add regime check in trading loop with halt logic"

# Step 4: Test
# (run tests, verify nothing breaks)
git commit -m "test: Verified regime monitor integration in paper mode"
```

**Bad commit pattern (DON'T DO THIS):**
```powershell
# One giant commit at end of day
git add .
git commit -m "added regime monitor stuff"  # ❌ Too vague, can't rollback granularly
```

---

### **Phase 3: Testing & Validation**

#### Before Merging to Main

**Checklist:**
- [ ] ✅ Code runs without errors
- [ ] ✅ Paper trading mode still works
- [ ] ✅ Existing features unchanged (start bot, view dashboard, change settings)
- [ ] ✅ New feature works as intended (regime monitor halts in BEARISH)
- [ ] ✅ No new console errors or warnings

**Test Command:**
```powershell
# Run in paper trading mode
python dashboard_v2.py

# Check:
# 1. Bot starts successfully
# 2. No crash on regime monitor fetch
# 3. Regime status appears in logs
# 4. Trading halts if bearish (test by mocking)
```

---

### **Phase 4: Rollback if Needed**

#### Quick Rollback (Last Commit)
```powershell
# Undo last commit, keep changes in working directory
git reset --soft HEAD~1

# Undo last commit AND discard changes (DANGER!)
git reset --hard HEAD~1
```

#### Rollback to Specific Commit
```powershell
# View commit history
git log --oneline

# Example output:
# a1b2c3d feat: Add regime check in trading loop
# e4f5g6h feat: Initialize regime_monitor instance
# i7j8k9l feat: Import RegimeMonitor
# m0n1o2p baseline: Save current working state

# Rollback to baseline (before all regime monitor changes)
git reset --hard m0n1o2p

# Or rollback just one step
git reset --hard i7j8k9l  # Back to after import, before initialization
```

---

### **Phase 5: Merging to Main**

#### After All Tests Pass
```powershell
# Switch to main branch
git checkout main

# Merge feature branch
git merge feature/regime-monitor-integration

# Push to remote (if using GitHub/GitLab)
git push origin main

# Optional: Delete feature branch (cleanup)
git branch -d feature/regime-monitor-integration
```

---

## 🔄 Alternative: Manual Backup (If Not Using Git)

### Before Modifying kickstart.py

```powershell
# Create timestamped backup
copy "C:\Antigravity\TradingBots-Aruns Project\kickstart.py" "C:\Antigravity\TradingBots-Aruns Project\kickstart.py.backup-2026-01-18"

# Or create backups folder
mkdir "C:\Antigravity\TradingBots-Aruns Project\backups"
copy "kickstart.py" "backups\kickstart-before-regime-monitor.py"
```

### Restore from Backup if Needed
```powershell
# Restore original
copy "backups\kickstart-before-regime-monitor.py" "kickstart.py"
```

---

## 📝 Documentation Requirements for AI Agents

### **After Every Code Change Session**

Update `AI_HANDOVER.md` with:

1. **What was changed** (file names, line numbers)
2. **Why it was changed** (purpose, reasoning)
3. **How to test** (verification steps)
4. **How to rollback** (git commit hash or backup filename)

**Example Entry:**
```markdown
### Session: Jan 18, 2026 - Regime Monitor Integration
**Files Modified:**
- `kickstart.py` (lines 45-48: import, lines 1450-1460: integration)

**Changes:**
- Added RegimeMonitor import
- Initialized monitor in main()
- Added regime check before trading loop

**Test Results:**
- ✅ Paper mode: Bot starts, no errors
- ✅ Regime detection: Successfully halted trading in mocked BEARISH scenario
- ✅ Existing features: Dashboard, settings, notifications all work

**Rollback Info:**
- Git commit before changes: `a1b2c3d`
- Backup file: `backups/kickstart-before-regime-monitor.py`
- Command: `git reset --hard a1b2c3d`
```

---

## ⚠️ RED FLAGS (When to STOP and Ask Human)

### Stop Immediately If:

1. **Import errors** after adding new code
2. **Existing features break** (bot won't start, dashboard crashes)
3. **Database schema conflicts** (trades_db.py errors)
4. **API authentication fails** after changes
5. **Uncertain about impact** of a change

### Escalation Protocol:
```markdown
**In AI_HANDOVER.md:**
> ⚠️ BLOCKER ENCOUNTERED
> **Issue:** [describe problem]
> **What was attempted:** [what you tried]
> **Current state:** [is code broken or safe?]
> **Recommendation:** [human review needed, rollback suggested, etc.]
```

---

## 🎓 Best Practices Summary

### DO:
✅ Create feature branches for each major change  
✅ Commit frequently with descriptive messages  
✅ Test in paper mode before live trading  
✅ Update AI_HANDOVER.md after each session  
✅ Keep backups of critical files  

### DON'T:
❌ Modify multiple core files in one commit  
❌ Skip testing after changes  
❌ Delete old code without commenting out first  
❌ Merge untested features to main  
❌ Assume "it should work" without verification  

---

## 📊 Risk Assessment Template

Before modifying any file, rate the risk:

| Risk Level | Description | Action Required |
|------------|-------------|-----------------|
| 🟢 **LOW** | New file, no dependencies | Commit & proceed |
| 🟡 **MEDIUM** | Modify existing file, isolated change | Create branch, test before merge |
| 🔴 **HIGH** | Modify core trading logic, database schema | Human review required + extensive testing |
| ⚫ **CRITICAL** | Change order execution, risk management | STOP - Mandatory human approval |

**Regime Monitor Integration Risk:** 🟡 **MEDIUM**
- Modifies `kickstart.py` (core file)
- Change is isolated (one if-check in loop)
- Easily reversible
- **Action:** Feature branch + paper mode testing required

---

**Document Owner:** AI Collaboration Team  
**Review Frequency:** After each major feature  
**Last Verified:** January 18, 2026
