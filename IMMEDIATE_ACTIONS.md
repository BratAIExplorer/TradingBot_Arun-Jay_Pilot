# ARUN Trading Bot - Immediate Action Plan
**Generated:** 2026-06-21  
**Audit Status:** COMPLETE ✓  
**Critical Issues:** 3  
**Time to Fix:** ~30 minutes

---

## 📋 ACTION CHECKLIST (In Order)

### ✅ ACTION 1: REMOVE DUPLICATE TRADES (2 minutes)

You have 4 duplicate trades in your database. Remove them:

**Method A - Python (Recommended)**
```python
# Run this in Python console or script
import sqlite3

conn = sqlite3.connect(r'C:\Antigravity\TradingBots-Aruns Project\database\trades.db')
cursor = conn.cursor()

# Delete the duplicate records (keep first, delete duplicates)
cursor.execute("DELETE FROM trades WHERE id IN (19, 3)")
conn.commit()

print("✓ Deleted 2 duplicate records")
print(f"  - MICEL (ID 19)")
print(f"  - MOSCHIP (ID 3)")

conn.close()
```

**Method B - Command Line**
```bash
cd "C:\Antigravity\TradingBots-Aruns Project"
python << EOF
import sqlite3
conn = sqlite3.connect('database/trades.db')
conn.execute("DELETE FROM trades WHERE id IN (19, 3)")
conn.commit()
print("Deleted duplicates")
conn.close()
EOF
```

**Verify:**
```bash
python << EOF
import sqlite3
conn = sqlite3.connect('database/trades.db')
dup_count = conn.execute("SELECT COUNT(*) FROM trades WHERE id IN (19, 3)").fetchone()[0]
print(f"Remaining duplicates: {dup_count} (should be 0)")
conn.close()
EOF
```

---

### ✅ ACTION 2: BACKFILL MISSING P&L (5 minutes)

You have 1 sell trade missing P&L calculation. Backfill it:

```bash
cd "C:\Antigravity\TradingBots-Aruns Project"
python database/backfill_pnl.py
```

**What it does:**
- Reads CANBK sell on 2026-02-16
- Finds matching buy in mstock_statement.csv
- Calculates P&L
- Updates database

**Expected output:**
```
DRY_RUN: True (showing preview, no changes)
Matches found: 1
Rows to update: 1

Ready to apply? Change DRY_RUN = False and re-run
```

---

### ✅ ACTION 3: FIX THE 403 AUTH ERRORS (5 minutes)

Your logs show repeated 403 errors (token expired). Fix this:

**Option A - Auto-Login (If TOTP is set up)**
```bash
cd "C:\Antigravity\TradingBots-Aruns Project"
python << EOF
from kickstart import perform_auto_login
result = perform_auto_login()
if result:
    print("SUCCESS: Token refreshed")
else:
    print("FAILED: Check TOTP secret in settings.json")
EOF
```

**Option B - Manual Credentials Update**
1. Go to: https://developer.mstock.trade/
2. Login with your mStock account
3. Navigate to: Settings → API Credentials
4. Copy: API Key and API Secret
5. Update `.env` file:
   ```
   MSTOCK_API_KEY=your_new_key_here
   MSTOCK_API_SECRET=your_new_secret_here
   ```
6. Delete old token from `settings.json`:
   ```json
   "access_token": "",
   "token_refresh_timestamp": ""
   ```
7. Restart the dashboard:
   ```bash
   python sensei_v1_dashboard.py
   ```

**Verify:** No more 403 errors in logs

---

### ⚠️ ACTION 4: UNDERSTAND YOUR TRADING DATA (CRITICAL!)

**READ THIS CAREFULLY:**

Your audit found:
- **mStock statement:** 1,568 trades (Jan-Jun 2026)
- **Local database:** 50 trades
- **Data gap:** 96.8%

**QUESTION:** Which of these is true?

- [ ] **"These 1,568 mStock trades are MANUAL trades I placed myself (not the bot)"**
  - ➜ Then the database is fine - it tracks bot trades only
  - ➜ Skip to ACTION 5

- [ ] **"These 1,568 mStock trades are BOT trades that didn't get recorded"**
  - ➜ Then we have a catastrophic database failure
  - ➜ Need to import all trades from mStock (4-hour job)
  - ➜ STOP and let me know

- [ ] **"I'm not sure / Mix of both"**
  - ➜ Check your mStock activity
  - ➜ Count how many you actually placed manually
  - ➜ Let me know the split

---

### ✅ ACTION 5: VERIFY DATABASE AFTER FIXES

After completing Actions 1-3, verify the database:

```bash
cd "C:\Antigravity\TradingBots-Aruns Project"
python << EOF
import sqlite3

conn = sqlite3.connect('database/trades.db')
cursor = conn.cursor()

# Count trades
cursor.execute("SELECT COUNT(*) FROM trades WHERE broker != 'PAPER'")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL' AND pnl_gross IS NULL")
missing_pnl = cursor.fetchone()[0]

# Check for duplicates
cursor.execute("""
SELECT COUNT(*) FROM (
  SELECT symbol, action, quantity, price, date, 
         COUNT(*) as cnt FROM trades 
  GROUP BY symbol, action, quantity, price, date 
  HAVING cnt > 1
)
""")
duplicates = cursor.fetchone()[0]

conn.close()

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)
print(f"Total trades: {total} (was 50)")
print(f"Missing P&L: {missing_pnl} (should be 0 after backfill)")
print(f"Duplicates: {duplicates} (should be 0 after cleanup)")
print("=" * 60)

if missing_pnl == 0 and duplicates == 0:
    print("✓ DATABASE CLEAN - All fixes applied successfully")
else:
    print("⚠ Issues remain - check logs above")
EOF
```

---

## 📊 AUDIT SUMMARY

Generated files (in project root):

```
AUDIT_FINAL_REPORT.md           ← Full audit report (read this!)
AUDIT_complete.py               ← Audit script (for reference)
AUDIT_orphaned_trades.csv       ← 1,568 mStock trades not in DB
AUDIT_duplicate_trades.csv      ← 4 duplicate records (will be fixed)
AUDIT_missing_pnl.csv           ← 1 sell without P&L (will be fixed)
```

---

## 🎯 YOUR TRADING PERFORMANCE (Current Data)

Based on 33 sell trades with P&L:

| Metric | Value | Status |
|--------|-------|--------|
| Win Rate | 24.2% | ❌ Below 50% target |
| Total P&L | -₹36,617 | ❌ Negative |
| Avg Loss/Trade | -₹1,110 | ❌ Wrong direction |
| Best Trade | +₹405 | ⚠️ Small profit |
| Worst Trade | -₹9,014 | ⚠️ Large loss |

**Takeaway:** RSI-only strategy with current parameters is **not profitable**.

---

## ⏱️ ESTIMATED TIME REQUIRED

| Action | Time | Critical |
|--------|------|----------|
| Remove duplicates | 2 min | Yes |
| Backfill P&L | 5 min | Yes |
| Fix auth errors | 5 min | Yes |
| Verify database | 3 min | Yes |
| **TOTAL** | **15 min** | **Quick win** |

---

## 📋 NEXT STEPS AFTER FIXES

### Week 1 (This Week)
- [ ] Complete 5 actions above
- [ ] Make decision on 1,568 mStock trades (ACTION 4)
- [ ] Run dashboard and verify no more 403 errors

### Week 2 (Next Week)
- [ ] Analyze why win rate is 24% (should be 50%+)
- [ ] Consider RSI parameter optimization
- [ ] Test multi-timeframe confirmation (reduce false signals)

### Week 3-4 (This Month)
- [ ] Implement trend filter (don't buy in downtrends)
- [ ] Add backtester for parameter validation
- [ ] Target: improve win rate to 40%+

---

## ⚡ CRITICAL NOTES

1. **Do NOT ignore the 403 errors** — they're blocking your bot from trading
2. **Do NOT skip the duplicate cleanup** — dashboard metrics will be wrong
3. **Do NOT worry about the data gap yet** — first clarify if those are manual trades
4. **DO test backfill in DRY_RUN mode first** — don't modify DB without preview

---

## 🆘 IF YOU GET STUCK

**"Backfill script won't run"**
```bash
pip install pandas openpyxl  # Make sure dependencies are installed
```

**"403 errors persist after fixing credentials"**
```bash
# Clear all auth caches
del settings.json  # It will regenerate on restart
python sensei_v1_dashboard.py  # Will auto-login
```

**"Not sure what the 1,568 mStock trades are"**
```bash
# Check your mStock app:
# Profile → Trade History → Date range 2026-01-01 to 2026-06-21
# Count: ~1,568 trades. Are these all yours?
# Or did a family member use the account?
```

---

## ✅ COMPLETION CHECKLIST

When you've completed all 5 actions, confirm:

- [ ] Duplicates removed (2 records deleted)
- [ ] P&L backfilled (1 CANBK trade updated)
- [ ] Auth errors fixed (can see positions in dashboard)
- [ ] Database verified (CLEAN status shown)
- [ ] Decision made on 1,568 mStock trades

**Time required:** ~30-45 minutes  
**Difficulty:** Low (copy-paste commands)  
**Impact:** High (fixes data integrity + auth issues)

---

**Ready to start?** Begin with ACTION 1 above.  
**Questions?** Refer to AUDIT_FINAL_REPORT.md for detailed analysis.
