# ORBIT TRADING - Versioning & Rollback Guide

## Current Version

Check current version with:
```bash
cat VERSION.txt
```

Shows the version and release notes.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.6.0 | 2026-06-21 | Dashboard title fix, IBKR broker, market context label, Trading CXO skill |
| v2.5.2 | 2026-03-08 | Never sell at loss (3-layer defense), P&L FIFO, neutral trades |
| v2.5.1 | 2026-03-07 | Security audit fixes (P0-P3), encryption, thread safety |
| v2.5.0 | 2026-02-16 | Panic stop, RMS cooldown, accurate counters, trade CSV export |

---

## Rollback Procedure

### Quick Rollback (Git)

If you need to roll back to a previous version:

```bash
# 1. Check available versions
git tag | grep "v2\."

# 2. Rollback to a specific version
git checkout v2.5.2

# 3. Create a rollback branch (don't modify main)
git checkout -b rollback-from-v2.6.0-to-v2.5.2

# 4. Update VERSION.txt
echo "v2.5.2" > VERSION.txt

# 5. Commit the rollback
git commit -am "rollback: Revert to v2.5.2 from v2.6.0"

# 6. Don't push to main without review!
```

### Full Rollback (Database + Code)

If v2.6.0 introduced database schema changes:

```bash
# 1. Backup current database
cp database/trades.db database/trades.db.backup.v2.6.0

# 2. Restore previous database backup (if available)
cp database/trades.db.backup.v2.5.2 database/trades.db

# 3. Rollback code
git checkout v2.5.2

# 4. Update VERSION.txt
echo "v2.5.2" > VERSION.txt

# 5. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# 6. Restart the application
python launcher.py
```

---

## Version Numbering

Format: **v{MAJOR}.{MINOR}.{PATCH}**

- **MAJOR**: Major features (UI overhaul, new markets, major trading changes)
- **MINOR**: Minor features, bug fixes, improvements
- **PATCH**: Hotfixes, critical bug patches

### Examples:
- v2.6.0 = v2 (ORBIT era) + .6 (features 6) + .0 (initial release of v2.6)
- v2.6.1 = v2 + .6 (same feature set) + .1 (hotfix)
- v3.0.0 = Major version upgrade

---

## Before Each Update

1. **Read VERSION.txt** for release notes
2. **Check BUG_REGISTRY.md** for known issues
3. **Run tests** before deploying:
   ```bash
   python test_v26_fixes.py
   pytest tests/test_regressions.py -v
   ```
4. **Backup data**:
   ```bash
   cp database/trades.db database/trades.db.backup.$(date +%Y%m%d)
   cp settings.json settings.json.backup.$(date +%Y%m%d)
   ```

---

## After Each Update

1. **Verify version**:
   ```bash
   python launcher.py  # Shows version at top
   ```

2. **Verify UI**:
   - Window title shows correct version
   - Dashboard shows v2.6.0 (not v2.0.3)
   - Disclaimer says "ORBIT TRADING"

3. **Run regression tests**:
   ```bash
   pytest tests/test_regressions.py -v
   ```

4. **Check logs**:
   ```bash
   tail -f logs/*.log
   ```

---

## Emergency Rollback (If Needed)

If the current version is broken:

```bash
# 1. Stop the application
# (Close the launcher/dashboard)

# 2. Quick rollback
git stash                    # Save any uncommitted changes
git checkout v2.5.2          # Go back to v2.5.2
git checkout -b rollback     # Create rollback branch

# 3. Update version file
echo "v2.5.2" > VERSION.txt

# 4. Restart
python launcher.py

# 5. Notify team
# (Let others know we rolled back)
```

---

## Git Tags for Versions

All released versions have a git tag:

```bash
# List all version tags
git tag | grep "^v"

# Rollback to a tag
git checkout v2.5.2

# Create your own tag (after major release)
git tag -a v2.6.0 -m "ORBIT Trading v2.6.0 - UX improvements"
git push origin v2.6.0
```

---

## Continuous Integration

When pushing to main:

1. ✅ All tests pass (`pytest tests/ -v`)
2. ✅ VERSION.txt is updated
3. ✅ Commit message mentions version
4. ✅ BUG_REGISTRY.md is updated (if bugs fixed)
5. ✅ Release notes in VERSION.txt are clear

---

**Last Updated**: 2026-06-21  
**Current Version**: v2.6.0  
**Stable Rollback**: v2.5.2 (if needed)
