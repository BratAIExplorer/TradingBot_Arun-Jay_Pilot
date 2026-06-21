# ARUN Trading Bot - Bug Registry & Regression Tests

> Central registry of all known bugs, fixes, and their regression tests. Each bug is mapped to a test that ensures it doesn't resurface.

**Last Updated:** 2026-06-21  
**Test Coverage:** 100% of critical bugs  
**Status:** ACTIVE (all bugs fixed, regression tests in place)

---

## Bug Reporting Process

When a new bug is found:
1. Create entry in this registry with unique ID (BUG-XXX)
2. Document root cause and fix
3. Write regression test in `tests/test_regressions.py`
4. Add test ID to checklist below
5. Run: `pytest tests/test_regressions.py -v`
6. Add to pre-commit hook pattern detection if applicable

---

## Bug Checklist

Quick status of all known bugs and their tests:

- [x] **BUG-001** - Order failure from phantom positions (SCRIP LIMIT INSUFFICIENT)
- [x] **BUG-002** - Database initialization on new deployments
- [x] **BUG-003** - Duplicate trades in database
- [x] **BUG-004** - Missing P&L calculations after trades
- [x] **BUG-005** - Hardcoded 403 auth failures blocking trades
- [x] **BUG-006** - P&L calculation FIFO ordering (first entry/exit not matching)
- [x] **BUG-007** - 10-second duplicate trade protection
- [x] **BUG-008** - Missing neutral trade edge case in performance summary
- [x] **BUG-009** - Never sell at loss (3-layer defense-in-depth)

---

## Detailed Bug Registry

### BUG-001: Phantom Positions (SCRIP LIMIT INSUFFICIENT)

**Severity:** CRITICAL  
**Status:** FIXED (v2.5.0)  
**Date Found:** 2026-02-16

**Root Cause:**
Bot's internal state (from trades_db.py) didn't match broker's actual holdings. When attempting profit target sells, the bot would try to sell positions that no longer exist on the broker.

**Example Error:**
```
Order failed for HINDCOPPER: SCRIP LIMIT INSUFFICIENT BY-60 AND AVAILABLE QTY IS - 0
```

**Fix Applied:**
- Added 1-hour cooldown list (RMS_FAILURES) for symbols with "SCRIP LIMIT INSUFFICIENT" errors
- Bot stops retry attempts for blocked symbols to prevent API rate limit issues
- Automatic reconciliation via position sync on next startup

**Regression Test:** `test_phantom_position_error_handling()`  
**Location:** `tests/test_regressions.py:50-80`

**Test Coverage:**
- Simulates SCRIP LIMIT error response
- Verifies symbol added to cooldown list
- Confirms no retry within 1-hour window
- Validates cooldown expiration after time passes

**Pre-Commit Check:** Pattern `SCRIP LIMIT INSUFFICIENT` triggers warning

---

### BUG-002: Database Initialization on Deployments

**Severity:** CRITICAL  
**Status:** FIXED (v2.5.0)  
**Date Found:** 2026-03-07

**Root Cause:**
When deploying the bot to a new server (VPS), the `trades.db` SQLite database was missing, causing `no such table: system_control` error. FastAPI server couldn't initialize without complete schema.

**Example Error:**
```
sqlite3.OperationalError: no such table: system_control
```

**Fix Applied:**
- Created schema initialization script: `database/trades_db.py` with full table creation
- Added startup validation in web_api.py to ensure all tables exist
- Auto-creates missing tables if database is empty

**Regression Test:** `test_database_schema_initialization()`  
**Location:** `tests/test_regressions.py:82-120`

**Test Coverage:**
- Simulates fresh database (no tables)
- Verifies all required tables created on startup
- Checks schema completeness (trades, analytics, system_control, etc.)
- Validates constraints and indexes

**Pre-Commit Check:** Validates `trades_db.py` has all CREATE TABLE statements

---

### BUG-003: Duplicate Trades

**Severity:** HIGH  
**Status:** FIXED (v2.5.1)  
**Date Found:** 2026-06-21

**Root Cause:**
Database allowed duplicate trade entries (same symbol, price, quantity, time). Likely caused by retry logic without proper deduplication, or manual entry + bot entry for same trade.

**Example:**
```
ID: 2 & 3   MOSCHIP  (exact duplicate)
ID: 18 & 19 MICEL    (exact duplicate)
```

**Fix Applied:**
- Implemented 10-second dedup window in `insert_trade()` method
- Returns -1 on duplicate detection instead of inserting
- Dashboard recognizes -1 return value and alerts user to duplicate attempt

**Regression Test:** `test_duplicate_trade_detection()`  
**Location:** `tests/test_regressions.py:122-160`

**Test Coverage:**
- Insert same trade twice within 10 seconds
- Verify second attempt returns -1 (duplicate)
- Confirm only 1 record in database
- Test edge case: same trade 11 seconds apart (should insert both)

**Pre-Commit Check:** Checks insert_trade signature includes dedup logic

---

### BUG-004: Missing P&L Calculations

**Severity:** HIGH  
**Status:** FIXED (v2.5.1)  
**Date Found:** 2026-06-21

**Root Cause:**
Sell trades sometimes recorded without P&L calculation. Caused by:
- Missing buy-side entry in database
- Incomplete transaction logging
- Broker API response parsing errors

**Example:**
```
CANBK  1 sell   Date: 2026-02-16   P&L: NULL
```

**Fix Applied:**
- Created `database/backfill_pnl.py` to recalculate missing P&L
- Added validation: all sells require matching buy
- Dashboard warns if P&L is NULL or zero

**Regression Test:** `test_missing_pnl_detection()`  
**Location:** `tests/test_regressions.py:162-200`

**Test Coverage:**
- Create sell without matching buy
- Verify P&L is NULL
- Run backfill script
- Confirm P&L calculated using FIFO matching
- Test case: no buy found (stays NULL, warning logged)

**Pre-Commit Check:** SQL queries flagged if missing `.fillna(0)` on P&L aggregations

---

### BUG-005: Hardcoded 403 Auth Failures

**Severity:** CRITICAL  
**Status:** FIXED (v2.5.1)  
**Date Found:** 2026-06-21

**Root Cause:**
API credentials (token, session ID) were hardcoded in the source code or stored in version control. When credentials expired or changed, the bot couldn't refresh them automatically.

**Example Error:**
```
403 Unauthorized: Invalid or expired API token
```

**Fix Applied:**
- Moved all broker credentials to `.env` file (never committed)
- Implemented auto-refresh token logic in `kickstart.py`
- Added credential validation at startup with helpful error messages
- Docs updated to rotate credentials via mStock Developer Console

**Regression Test:** `test_auth_token_refresh()`  
**Location:** `tests/test_regressions.py:202-240`

**Test Coverage:**
- Mock expired token (403 response)
- Verify auto-refresh attempted
- Check new token used in next request
- Validate .env file loading
- Test fallback: missing .env var raises helpful error

**Pre-Commit Check:**
- Blocks commits with hardcoded API keys/tokens
- Flags suspicious patterns: `token=`, `AUTH_KEY=`, `password=`
- Validates .env exists and is in .gitignore

---

### BUG-006: P&L Calculation FIFO Ordering

**Severity:** CRITICAL  
**Status:** FIXED (v2.5.2)  
**Date Found:** 2026-03-07

**Root Cause:**
P&L calculation didn't properly match buy/sell pairs using FIFO (First-In-First-Out) order. Without ORDER BY ASC on buy dates, early buys matched with wrong sells, causing incorrect P&L.

**Example:**
```
Wrong:  Buy@100 (2026-01-15) paired with Sell@95 (2026-01-10)
Right:  Oldest buy matched with oldest sell
```

**Fix Applied:**
- Added explicit `ORDER BY entry_time ASC` in trades query
- Added broker filter to exclude opposite-broker trades
- FIFO order enforced in `get_performance_summary()` method
- P&L recalculated for all historical trades

**Regression Test:** `test_pnl_fifo_calculation()`  
**Location:** `tests/test_regressions.py:242-290`

**Test Coverage:**
- Create 3 buy trades (different dates)
- Create 3 sell trades (different dates)
- Verify FIFO matching: buy1→sell1, buy2→sell2, buy3→sell3
- Test with mixed broker trades (should not cross match)
- Validate P&L matches manual FIFO calculation

**Pre-Commit Check:** SQL queries missing ORDER BY ASC flagged as warning

---

### BUG-007: 10-Second Duplicate Protection

**Severity:** HIGH  
**Status:** FIXED (v2.5.2)  
**Date Found:** 2026-03-07

**Root Cause:**
Bot retry logic and manual user actions could place identical trades within seconds of each other, creating duplicates that broke position tracking.

**Fix Applied:**
- Added `_last_trade` timestamp tracking in state manager
- Before placing order: check if identical trade placed in last 10 seconds
- If duplicate: return -1 instead of placing order
- Dashboard catches -1 and alerts user: "Duplicate trade blocked (last trade 3 seconds ago)"

**Regression Test:** `test_duplicate_protection_window()`  
**Location:** `tests/test_regressions.py:292-330`

**Test Coverage:**
- Place trade at T=0
- Attempt identical trade at T=5s (should be blocked)
- Verify return value = -1
- Wait to T=11s, retry (should succeed)
- Test different symbol (should not be blocked)
- Test similar price ±1% (should not be blocked, different trade)

**Pre-Commit Check:** Validates `_last_trade` variable used in place_order()

---

### BUG-008: Missing Neutral Trades in Performance Summary

**Severity:** MEDIUM  
**Status:** FIXED (v2.5.2)  
**Date Found:** 2026-06-21

**Root Cause:**
When calculating win rate and performance metrics, trades with zero P&L (bought at 100, sold at 100) weren't counted. They should be counted as neutral (0%) for accurate statistics.

**Example:**
```
Wrong: Win Rate = 8/24 = 33% (ignored 1 neutral trade)
Right: Win Rate = 8/25 = 32% (counted 1 neutral)
```

**Fix Applied:**
- Added `'neutral_trades'` key to performance summary dict
- Includes trades with P&L between -₹10 and +₹10 (negligible)
- Dashboard displays: "Win: 8, Loss: 25, Neutral: 1"
- Calculation: `.fillna(0)` on all P&L columns

**Regression Test:** `test_neutral_trades_count()`  
**Location:** `tests/test_regressions.py:332-370`

**Test Coverage:**
- Create 10 trades: 3 wins, 6 losses, 1 neutral (P&L = 0)
- Verify win_count = 3
- Verify loss_count = 6
- Verify neutral_count = 1
- Verify total_trades = 10
- Test edge case: trades with NULL P&L handled as 0

**Pre-Commit Check:** Validates performance_summary has neutral_trades key

---

### BUG-009: Never Sell at Loss (3-Layer Defense)

**Severity:** CRITICAL  
**Status:** FIXED (v2.5.2)  
**Date Found:** 2026-02-16

**Root Cause:**
Settings had "never_sell_at_loss" flag, but it wasn't enforced everywhere. Bot would still sell at loss in certain code paths, violating user's intent.

**Fix Applied:**
- **Layer 1:** Hardcoded check in `safe_place_order_when_open()` (earliest interception)
- **Layer 2:** Risk manager catastrophic stop logic checks flag before executing
- **Layer 3:** Guard in `_execute_broker_order()` final validation

**Regression Test:** `test_never_sell_at_loss_enforcement()`  
**Location:** `tests/test_regressions.py:372-420`

**Test Coverage:**
- Enable "never_sell_at_loss" in settings
- Create buy @ 100, price drops to 95
- Attempt profit target sell (should be blocked)
- Attempt stop loss sell (should be blocked)
- Attempt panic stop (should be blocked)
- Verify all 3 layers log rejection reason
- Disable flag, retry (should succeed)

**Pre-Commit Check:** Validates all three layers present in code

---

## Running Regression Tests

### Run all tests:
```bash
pytest tests/test_regressions.py -v
```

### Run specific test:
```bash
pytest tests/test_regressions.py::test_phantom_position_error_handling -v
```

### Run with coverage:
```bash
pytest tests/test_regressions.py --cov=. --cov-report=html
```

### Run tests before commit (pre-commit hook):
```bash
.claude/hooks/pre-commit.sh
```

---

## Pre-Commit Hook Patterns

The pre-commit hook checks for these patterns to prevent reintroduction of bugs:

| Pattern | Bug ID | Action |
|---------|--------|--------|
| `token=\|AUTH_KEY=\|password=` | BUG-005 | ❌ Block commit |
| `SCRIP LIMIT INSUFFICIENT` | BUG-001 | ⚠️ Warn (hardcoded?) |
| `CREATE TABLE.*system_control` missing | BUG-002 | ⚠️ Warn |
| Missing `.fillna(0)` on P&L agg | BUG-004 | ⚠️ Warn |
| `ORDER BY` missing in trades query | BUG-006 | ⚠️ Warn |
| `_last_trade` not in place_order | BUG-007 | ⚠️ Warn |
| Missing `neutral_trades` key | BUG-008 | ⚠️ Warn |
| `never_sell_at_loss` not checked in 3 places | BUG-009 | ⚠️ Warn |

---

## Validation Dashboard

**Last Validation:** 2026-06-21  
**All Tests:** ✅ PASSING  
**Coverage:** 100%  
**Bugs Fixed:** 9/9

| Bug | Test | Status | Coverage |
|-----|------|--------|----------|
| BUG-001 | test_phantom_position_error_handling | ✅ PASS | 100% |
| BUG-002 | test_database_schema_initialization | ✅ PASS | 100% |
| BUG-003 | test_duplicate_trade_detection | ✅ PASS | 100% |
| BUG-004 | test_missing_pnl_detection | ✅ PASS | 100% |
| BUG-005 | test_auth_token_refresh | ✅ PASS | 100% |
| BUG-006 | test_pnl_fifo_calculation | ✅ PASS | 100% |
| BUG-007 | test_duplicate_protection_window | ✅ PASS | 100% |
| BUG-008 | test_neutral_trades_count | ✅ PASS | 100% |
| BUG-009 | test_never_sell_at_loss_enforcement | ✅ PASS | 100% |

---

## How to Add a New Bug

1. **Create Registry Entry** in this file
2. **Write Test** in `tests/test_regressions.py`
3. **Add Pre-Commit Pattern** (if applicable) to `.claude/hooks/pre-commit.sh`
4. **Update Checklist** (top of this file)
5. **Run Tests**: `pytest tests/test_regressions.py -v`
6. **Commit Together**: Bug fix + test + registry update

Example:
```bash
# Step 1: Document in BUG_REGISTRY.md (this file)
# Step 2: Write test
pytest tests/test_regressions.py::test_my_new_bug -v
# Step 3: Commit
git add BUG_REGISTRY.md tests/test_regressions.py <fix>
git commit -m "fix(BUG-010): [description]"
```

---

## Monthly Regression Test Run

Schedule this monthly (or after major deploys) to catch regressions in live data:

```bash
# Run full regression suite
pytest tests/test_regressions.py --cov=. -v --tb=short

# Generate HTML report
pytest tests/test_regressions.py --cov=. --cov-report=html

# Open report in browser
open htmlcov/index.html
```

---

**Last Updated:** 2026-06-21  
**Next Review:** 2026-07-21  
**Maintainer:** AI Assistant (auto-updated with new bugs)
