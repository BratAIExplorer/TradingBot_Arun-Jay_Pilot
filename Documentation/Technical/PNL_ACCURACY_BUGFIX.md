# P&L Accuracy Bug Fix — Complete Handover Document
**Created:** 2026-03-06
**Status:** ALL 5 BUGS RESOLVED ✓ — Last updated 2026-03-08
**Priority:** COMPLETE

### Final P&L State (post-fix)
| Metric | Value |
|--------|-------|
| Real SELL trades | 34 |
| P&L populated | 33/34 (97%) |
| Still NULL | 1 (CANBK ID:51 — no buy in mstock_statement) |
| Net P&L (all real sells) | ₹-36,617 |
| Win rate | 24.2% (8 winners, 25 losers) |

- BUG-01/02/04/05: Fixed in `database/trades_db.py` (2026-03-07)
- BUG-03: Backfill run (2026-03-08) — 21 rows updated, 1 unmatched
- `database/backfill_pnl.py`: Kept with `DRY_RUN=True` for future re-runs if needed

---

## CONTEXT FOR INCOMING AI

This document describes **5 confirmed P&L accuracy bugs** in the ARUN Trading Bot.
All bugs were diagnosed by Claude Sonnet 4.6 on 2026-03-06 by cross-referencing:
- `database/trades_db.py` — the trade logging and P&L calculation code
- `full_trade_export.csv` — all 50+ trades exported from the SQLite DB
- `reconcile_unmatched_bot.csv` — sells where no matching buy was found in DB
- `reconcile_unmatched_mstock.csv` — the official mStock broker trade statement
- `manual_pnl_analysis.csv` — manual P&L calculation done outside the bot

**Do NOT touch any other files.** Only `database/trades_db.py` needs code changes.
A one-time backfill script `database/backfill_pnl.py` needs to be **created** (new file).

---

## ENVIRONMENT

- **Python:** 3.11, Windows 11
- **DB file:** `database/trades.db` (SQLite)
- **Shell:** bash (even on Windows — the project uses Git Bash)
- **Working directory:** `C:\Antigravity\TradingBots-Aruns Project`
- **Backup before any change:** `copy database\trades_db.py database\trades_db.py.bak2 /Y`

---

## BUG INVENTORY

### BUG-01 — CRITICAL: LIFO instead of FIFO buy price lookup
**Severity:** Critical
**File:** `database/trades_db.py`
**Line:** 226–230

**Current broken code:**
```python
cursor.execute("""
    SELECT price, net_amount, quantity FROM trades
    WHERE symbol = ? AND action = 'BUY'
    ORDER BY timestamp DESC LIMIT 1
""", (symbol,))
```

**Problem:** `ORDER BY timestamp DESC` returns the MOST RECENT buy.
Indian accounting and capital gains tax use FIFO (First In, First Out).
If a stock was bought at ₹728 (Jan), then ₹589 (Feb), a Feb sell should match
against the ₹728 buy first — but the current code matches against ₹589, making
the trade look like a near-breakeven when it was actually a loss.

**Fix — change only the ORDER BY and add broker filter:**
```python
cursor.execute("""
    SELECT price, net_amount, quantity FROM trades
    WHERE symbol = ? AND action = 'BUY' AND broker != 'PAPER'
    ORDER BY timestamp ASC LIMIT 1
""", (symbol,))
```

**Additional change needed at line ~224:** pass broker into the method and use it:
- The `insert_trade` call already receives `broker` as a parameter.
- So the fix is purely in the SQL string — no signature change needed.
- For PAPER sells, use: `AND broker = 'PAPER'` instead.

**Logic for PAPER vs real:**
```python
if broker.upper() == 'PAPER':
    broker_filter = "broker = 'PAPER'"
else:
    broker_filter = "broker != 'PAPER'"

cursor.execute(f"""
    SELECT price, net_amount, quantity FROM trades
    WHERE symbol = ? AND action = 'BUY' AND {broker_filter}
    ORDER BY timestamp ASC LIMIT 1
""", (symbol,))
```

---

### BUG-02 — CRITICAL: Paper trades contaminate real trade P&L
**Severity:** Critical
**File:** `database/trades_db.py`
**Line:** 226 (same query as BUG-01)

**Problem:** When calculating P&L for a real (mstock) SELL, the query has no
broker filter. A PAPER BUY at a different price gets picked up as the entry price
for a real trade, corrupting pnl_gross, pnl_net, pnl_pct_gross, pnl_pct_net.

**Evidence in data:**
- TATSILV: Real buy was @ ₹28.39. Paper buy was @ ₹32.52.
  Real sell P&L was computed using ₹32.52 as entry → wrong P&L.

**Fix:** Resolved by BUG-01 fix above (the broker filter addition).
No additional code change needed beyond BUG-01.

---

### BUG-03 — CRITICAL: ~60% of SELL trades have NULL P&L
**Severity:** Critical
**File:** `database/trades_db.py`
**Line:** 236–251 (the P&L calculation block)

**Problem:** Many positions were opened before the database was initialized
(or before a DB reset). When these positions are sold, `last_buy = cursor.fetchone()`
returns None, `fallback_entry_price` is 0, so the `if buy_price > 0:` block is
skipped and all four P&L fields remain NULL.

**Affected trades (confirmed NULL pnl in full_trade_export.csv):**
HINDCOPPER (rows 30, 39, 43), GOLDCASE (row 35), SILVERCASE (row 31),
WALCHANNAG (rows 42, 43), APOLLO (rows 32, 36, 44), CANBK (rows 34, 38, 45, 49),
TATSILV (row 29), GRSE (row 46), NETWEB (row 47), ANGELONE (row 48),
BSE (rows 33, 37, 40), MON100, NIFTYBEES.

**Consequence in `get_performance_summary()` (line 398–400):**
```python
winning_trades = len(sells[sells['pnl_net'] > 0])   # NULLs are excluded → wrong count
losing_trades = len(sells[sells['pnl_net'] < 0])    # NULLs are excluded → wrong count
net_profit = sells['pnl_net'].sum()                  # NaN propagates → wrong total
```
The dashboard win rate and net profit are computed on a minority of trades.

**Fix — Two-part:**

**Part A:** Forward-fix in `insert_trade` — when no matching buy found in DB,
log a warning but do NOT silently skip. Set pnl fields to `None` explicitly
(already done) and add a print warning:
```python
if not last_buy and fallback_entry_price <= 0:
    print(f"WARNING: No matching BUY found for SELL {symbol}. P&L will be NULL. "
          f"Run backfill_pnl.py to reconcile using mstock_statement.csv.")
```

**Part B:** Create `database/backfill_pnl.py` — a one-time script that:
1. Reads `mstock_statement.csv` (skip first 16 rows — header garbage)
2. Builds a FIFO buy queue per symbol from the mStock statement
3. For each SELL in the trades DB where pnl_gross IS NULL:
   - Match by symbol + date (allow ±1 day tolerance for timezone drift)
   - Find the earliest unmatched BUY from the mStock statement for that symbol
   - Calculate pnl_gross, pnl_net (net_amount - estimated_buy_cost), pnl_pct
   - UPDATE the DB row with these values
4. Print a reconciliation report: how many rows updated, how many still unmatched

**mstock_statement.csv format (data starts at row 17, 0-indexed row 16):**
```
Trade Date, Exchange, Buy / Sell, Scrip / Contract, Qty, Price, Trade Id
02-03-2026, NSEEQ,    Buy,        APEX-EQ,           3,   377.00, 7462150
```
Date format: `DD-MM-YYYY`
Symbol mapping: `APEX-EQ` → strip `-EQ`, `-A`, `-BE`, `-IF` suffixes → `APEX`

---

### BUG-04 — Duplicate SELL records from partial broker fills
**Severity:** Medium
**File:** `database/trades_db.py`
**Line:** `insert_trade` method

**Problem:** mStock sometimes fills a single order in multiple partial fills
(e.g., 60 HINDCOPPER filled as 1+59, or 40+60 in two chunks). Each partial fill
triggers a separate `insert_trade` call, resulting in duplicate SELL records
with identical or near-identical timestamps.

**Evidence:**
- Rows 18 & 19 in full_trade_export.csv: Identical MICEL BSE SELL at ₹38.94,
  timestamps differ by milliseconds — clearly the same execution.
- HINDCOPPER: Two SELL records on 13-02-2026 for 60 shares each.

**Fix — add duplicate guard at the start of `insert_trade`:**
```python
# Near start of insert_trade, before the INSERT:
cursor.execute("""
    SELECT id FROM trades
    WHERE symbol = ? AND action = ? AND quantity = ?
      AND ABS(price - ?) < 0.01
      AND datetime(timestamp) >= datetime('now', '-10 seconds')
""", (symbol, action, quantity, price))
if cursor.fetchone():
    print(f"DUPLICATE GUARD: Skipping duplicate {action} {symbol} @ {price}")
    return -1  # caller must handle -1 as "not inserted"
```

**Callers of insert_trade** — check how the return value is used in `kickstart.py`.
Search for `insert_trade(` and ensure `-1` return doesn't break anything.
The caller typically does `trade_id = db.insert_trade(...)` and may log the ID —
that's fine, just skip the log if trade_id == -1.

---

### BUG-05 — Performance summary miscounts NULLs
**Severity:** Medium (consequence of BUG-03, partially fixed by backfill)
**File:** `database/trades_db.py`
**Line:** 396–405

**Current broken code:**
```python
winning_trades = len(sells[sells['pnl_net'] > 0])
losing_trades = len(sells[sells['pnl_net'] < 0])
```

**Problem:** pandas comparisons on NaN return False — so all NULL-P&L trades
are silently dropped from both counts. Total trades = all sells, but
winning + losing < total → the math doesn't add up.

**Fix — add explicit NA handling:**
```python
winning_trades = len(sells[sells['pnl_net'].fillna(0) > 0])
losing_trades = len(sells[sells['pnl_net'].fillna(0) < 0])
neutral_trades = int(sells['pnl_net'].isna().sum())  # add this to summary dict
```

Also fix the net_profit sum:
```python
net_profit = sells['pnl_net'].sum(skipna=True) if 'pnl_net' in sells.columns else 0
# pandas sum() already skips NaN by default, but be explicit:
net_profit = float(sells['pnl_net'].dropna().sum())
```

Add `'trades_with_no_pnl': neutral_trades` to the returned dict so the
dashboard can optionally display a warning like "X trades have no P&L data".

---

## IMPLEMENTATION ORDER

Execute in this exact order:

```
STEP 1: Backup
  copy "database\trades_db.py" "database\trades_db.py.bak_pre_pnl_fix" /Y

STEP 2: Fix BUG-01 + BUG-02 (same code location, trades_db.py line 226)
  → Change ORDER BY DESC to ASC
  → Add broker filter (PAPER vs real logic)

STEP 3: Fix BUG-04 (duplicate guard at top of insert_trade)
  → Add the 10-second dedup check

STEP 4: Fix BUG-05 (performance summary NULL handling)
  → fillna(0) on pnl_net comparisons
  → add neutral_trades to return dict

STEP 5: Create database/backfill_pnl.py (new file)
  → FIFO matching from mstock_statement.csv
  → UPDATE existing NULL P&L rows in trades.db
  → Print reconciliation report

STEP 6: Run the backfill
  python database/backfill_pnl.py

STEP 7: Verify
  python database/trades_db.py   (runs the built-in test at __main__)
  → Check: SELL trades now have pnl_gross populated
  → Check: performance summary win_rate looks reasonable
  → Check: no duplicate trades inserted

STEP 8: Commit
  git add database/trades_db.py database/backfill_pnl.py
  git commit -m "fix(pnl): FIFO buy matching, paper isolation, NULL backfill, dedup guard"
```

---

## STOPPING POINT FOR AI

**Stop before Step 6 (running the backfill)** and show the user the reconciliation
preview (what would be updated) before writing to the live DB.
The backfill script should have a `DRY_RUN = True` flag at the top — default True,
user sets to False when happy with the preview output.

---

## VERIFICATION CHECKLIST

After implementation, the following must be true:

- [ ] `full_trade_export.csv` (regenerated) shows pnl_gross populated for ALL SELL rows
- [ ] TATSILV real sell P&L is based on ₹28.39 entry, not ₹32.52 (paper)
- [ ] HINDCOPPER earliest lot (Jan 29 @ ₹728) shows as a loss position
- [ ] `get_performance_summary()` winning + losing + neutral = total_trades
- [ ] No duplicate MICEL rows in the DB after re-running the bot
- [ ] `backfill_pnl.py` DRY_RUN mode prints a preview without modifying DB

---

## FILES CHANGED

| File | Action | Why |
|------|--------|-----|
| `database/trades_db.py` | MODIFY | Fix BUG-01/02/04/05 |
| `database/backfill_pnl.py` | CREATE NEW | Fix BUG-03 retroactively |

**Do NOT modify:**
- `kickstart.py` — unless insert_trade callers break on `-1` return (check first)
- `sensei_v1_dashboard.py` — the dashboard reads from DB, will auto-benefit from fix
- Any `.bak` files
- `mstock_statement.csv`, `full_trade_export.csv` — source data, read-only

---

## KEY DATA FACTS FOR BACKFILL SCRIPT

### mstock_statement.csv
- Skip first **16 rows** (rows 0–15) — they are bank header garbage
- Header is on row index 16: `Trade Date, Exchange, Buy / Sell, Scrip / Contract, Qty, Price, Trade Id`
- Date format: `DD-MM-YYYY` → parse with `pd.to_datetime(df['Trade Date'], format='%d-%m-%Y')`
- Symbol cleanup: strip suffixes `-EQ`, `-A`, `-BE`, `-IF`, `-X` from `Scrip / Contract`
  - e.g. `APEX-EQ` → `APEX`, `PNB-A` → `PNB`, `BIRET-IF` → `BIRET`
  - Use: `symbol = re.sub(r'-(EQ|A|BE|IF|X)$', '', scrip)`
- Buy/Sell values: `'Buy'` and `'Sell'` (capitalised first letter only)

### trades.db SELL rows needing backfill
- Condition: `action = 'SELL' AND pnl_gross IS NULL AND broker != 'PAPER'`
- Key fields for matching: `symbol`, `DATE(timestamp)`, `quantity`, `price`
- Allow ±1 day date tolerance (broker settlement can be T+1)

### Fee estimation for backfill P&L
When computing pnl_net for a backfilled row, you don't have the original
buy fees since the buy is not in the DB. Use this simplified estimate:
```
estimated_buy_fees = 20.0 + (buy_gross * 0.001)  # ₹20 flat + 0.1% approximate
pnl_net = (sell_net_amount) - (buy_gross + estimated_buy_fees)
```
Mark these rows with `strategy = strategy + ' [backfilled]'` so they're
distinguishable from precisely-calculated rows.

---

## CURRENT ACCURATE P&L PICTURE (Manual Calculation)

From `manual_pnl_analysis.csv` — for context / sanity check after fix:

**Confirmed Winners:**
- BSE: +₹9,835 (biggest winner)
- MTARTECH: +₹1,280
- NETWEB: +₹897
- IDEA (multiple cycles): net positive overall
- DATAPATTNS: +₹847 across cycles
- MOSCHIP Jan cycle: +₹137

**Confirmed Losers:**
- WALCHANNAG: -₹1,230 total across 3 exit legs
- ANGELONE: -₹387 total
- ITBEES: -₹346
- KERNEX: -₹251
- CANBK Feb 13 exits: -₹408 (matched against wrong buy dates)

**Orphan P&L (needs backfill to get real numbers):**
- GOLDCASE 300 shares @ ₹24 — bought @ ₹27.67 (Jan 29) + ₹27.06 (Jan 30) → estimated loss ~₹930
- SILVERCASE 300 shares @ ₹24.8 — bought @ ₹37.75 (Jan 29) + ₹36.29 (Jan 30) → loss ~₹3,870
- HINDCOPPER Jan lots (₹728–₹741 buy) sold Feb/Mar → significant losses unrecorded

---

*Document created by Claude Sonnet 4.6 on 2026-03-06.*
*Next AI: implement Steps 1–8, stop before Step 6, show dry-run preview first.*
