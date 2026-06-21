# CLAUDE.md - ARUN Trading Bot Guidelines

This file documents how to prevent bugs from resurfacing and maintain code quality.

---

## Quick Start: Prevent Bugs from Resurfacing

The ARUN Trading Bot has a **3-layer defense system** against known bugs:

### Layer 1: Pre-Commit Hook (Prevents commit)
Runs before every `git commit`. Blocks commits with hardcoded secrets, checks code patterns.

```bash
# Automatically runs on commit
git commit -m "fix: something"
# ✅ If clean: commit proceeds
# ❌ If issues: commit blocked with helpful message
```

### Layer 2: Regression Tests (Prevents deployment)
Manual test suite that validates all known bugs are fixed.

```bash
# Run before pushing to VPS
pytest tests/test_regressions.py -v
```

### Layer 3: Nightly Validation (Catches live issues)
Runs every night to detect if bugs have resurfaced in production.

```bash
# Runs automatically (or on-demand)
python scripts/nightly_validation.py
```

---

## Understanding the System

### BUG_REGISTRY.md
**Location:** `BUG_REGISTRY.md`

Central registry of all known bugs:
- **BUG-001**: Phantom positions (SCRIP LIMIT)
- **BUG-002**: Database initialization on new deployments
- **BUG-003**: Duplicate trades
- **BUG-004**: Missing P&L calculations
- **BUG-005**: Hardcoded auth failures
- **BUG-006**: P&L FIFO ordering (wrong buy/sell matching)
- **BUG-007**: 10-second duplicate protection
- **BUG-008**: Neutral trades not counted in stats
- **BUG-009**: Never sell at loss enforcement

Each bug maps to:
- Root cause analysis
- Fix that was applied
- Regression test that validates fix
- Pre-commit patterns that prevent reintroduction

### test_regressions.py
**Location:** `tests/test_regressions.py`

100+ tests covering all known bugs. Each test:
1. Reproduces the original bug scenario
2. Verifies the fix prevents it
3. Tests edge cases
4. Validates error handling

**Run:**
```bash
pytest tests/test_regressions.py -v              # Run all tests
pytest tests/test_regressions.py::test_BUG001 -v # Run specific test
pytest tests/test_regressions.py --cov=. -v     # With coverage
```

### pre-commit.sh Hook
**Location:** `.claude/hooks/pre-commit.sh`

Git pre-commit hook that checks for:
- ❌ Hardcoded API keys/tokens (blocks commit)
- ❌ Missing database schema patterns (warns)
- ⚠️  P&L queries without `.fillna(0)` (warns)
- ⚠️  SQL queries without ORDER BY (warns)
- ⚠️  Duplicate protection patterns missing (warns)

**Install:**
```bash
# Make executable
chmod +x .claude/hooks/pre-commit.sh

# Link as git hook (macOS/Linux)
ln -sf ../../.claude/hooks/pre-commit.sh .git/hooks/pre-commit

# Windows (PowerShell as admin)
New-Item -ItemType SymbolicLink -Path .git/hooks/pre-commit `
  -Target ..\..\\.claude\\hooks\\pre-commit.sh -Force
```

### nightly_validation.py
**Location:** `scripts/nightly_validation.py`

Runtime validation that checks:
- Database schema integrity
- Duplicate trades in live database
- Missing P&L entries
- Trade timestamp ordering (FIFO)
- Settings validation

**Run:**
```bash
python scripts/nightly_validation.py              # Standard check
python scripts/nightly_validation.py --db <path> # Custom database
```

**Schedule** (e.g., with cron on VPS):
```bash
0 2 * * * cd /opt/zepp && python scripts/nightly_validation.py >> /var/log/zepp-validation.log
```

---

## Workflow: Preventing Bug Reintroduction

### When Fixing a Bug

1. **Document in BUG_REGISTRY.md**
   - Add new BUG-XXX entry with root cause
   - Describe the fix
   - Note which test validates it

2. **Write Regression Test**
   ```python
   # tests/test_regressions.py
   @pytest.mark.regression
   def test_my_new_bug():
       """BUG-XXX: Description"""
       # Setup
       # Assert fix prevents bug
   ```

3. **Add Pre-Commit Pattern** (if applicable)
   ```bash
   # .claude/hooks/pre-commit.sh
   if git diff --cached | grep -q "suspicious_pattern"; then
       echo "❌ ERROR: BUG-XXX pattern detected"
       FAILED=$((FAILED + 1))
   fi
   ```

4. **Commit Together**
   ```bash
   git add BUG_REGISTRY.md tests/test_regressions.py <fix> ...
   git commit -m "fix(BUG-XXX): [description]"
   ```

### Before Pushing to VPS

```bash
# 1. Run all regression tests
pytest tests/test_regressions.py -v

# 2. Check coverage
pytest tests/test_regressions.py --cov=. --cov-report=html

# 3. Run pre-commit hook manually
.claude/hooks/pre-commit.sh

# 4. Deploy
git push origin main
ssh vps "cd /opt/zepp && git pull && systemctl restart zepp-web"

# 5. Run nightly validation on VPS
ssh vps "python scripts/nightly_validation.py"
```

### Monthly Validation

Run this every month (or after major deploys):

```bash
# Full regression test with detailed report
pytest tests/test_regressions.py --cov=. --cov-report=html -v

# Generate and review coverage report
open htmlcov/index.html

# Check live system
python scripts/nightly_validation.py

# If any issues found, investigate and update BUG_REGISTRY.md
```

---

## Common Tasks

### I Found a New Bug

1. **Add to BUG_REGISTRY.md:**
   ```markdown
   ### BUG-XXX: [Title]
   **Severity:** [CRITICAL|HIGH|MEDIUM]
   **Status:** INVESTIGATING
   **Date Found:** [date]
   
   **Root Cause:** [explanation]
   **Fix Applied:** [what we did]
   **Regression Test:** test_xxx()
   ```

2. **Write the test:**
   ```bash
   pytest tests/test_regressions.py::test_xxx -v
   ```

3. **Commit:**
   ```bash
   git commit -m "docs(BUG-XXX): [description]"
   ```

### A Test is Failing

1. **Understand why:**
   ```bash
   pytest tests/test_regressions.py::test_failing -vv
   ```

2. **Check if fix is still in place:**
   ```bash
   grep -r "fix_pattern" kickstart.py database/
   ```

3. **If fix was lost, restore it:**
   ```bash
   git log --grep="BUG-XXX" --oneline
   git show <commit>
   ```

4. **Update test if needed:**
   ```bash
   # Edit tests/test_regressions.py
   pytest tests/test_regressions.py::test_failing -v
   ```

### Pre-Commit Hook is Blocking My Commit

```bash
# 1. Review the warning
# 2. Fix the issue or
# 3. Commit bypassing hook (use only if intentional!)
git commit --no-verify -m "message"
```

### I Want to Run Validation Manually

```bash
# Full validation with verbose output
python scripts/nightly_validation.py

# Check specific database
python scripts/nightly_validation.py --db /path/to/trades.db

# See what it checks
grep "def check_" scripts/nightly_validation.py
```

---

## Testing Strategy

### Three Levels of Testing

| Level | Tool | Runs | Purpose |
|-------|------|------|---------|
| Unit Tests | `pytest tests/` | Before commit | Verify code logic |
| Regression Tests | `test_regressions.py` | Before deploy | Prevent bug resurfacing |
| Nightly Tests | `nightly_validation.py` | Every night | Catch live issues |

### Coverage Goals

- **Unit Tests:** 80%+ coverage of core logic
- **Regression Tests:** 100% coverage of known bugs
- **Nightly Tests:** Check real database state

### What Each Test Does

**Unit Tests** (existing):
```bash
pytest tests/test_core_logic.py    # RSI calculations
pytest tests/test_positions.py     # Position tracking
pytest tests/test_offline.py       # Offline mode
```

**Regression Tests** (new):
```bash
pytest tests/test_regressions.py   # All 9 known bugs
```

**Nightly Validation** (new):
```bash
python scripts/nightly_validation.py  # Live system check
```

---

## Critical Gotchas

### Gotcha 1: Database Initialization
**BUG-002**

When deploying to new VPS, create tables:
```bash
python -c "from database.trades_db import TradesDatabase; \
           db = TradesDatabase('database/trades.db')"
```

### Gotcha 2: Hardcoded Credentials
**BUG-005**

NEVER commit secrets. Use .env file:
```bash
# ❌ WRONG
token = "abc123"

# ✅ RIGHT
import os
token = os.getenv("MSTOCK_API_TOKEN")
```

### Gotcha 3: P&L Aggregation
**BUG-004**

Always use `.fillna(0)` on P&L calculations:
```python
# ❌ WRONG
pnl_sum = df['pnl'].sum()

# ✅ RIGHT
pnl_sum = df['pnl'].fillna(0).sum()
```

### Gotcha 4: Trade FIFO Ordering
**BUG-006**

Always ORDER BY timestamp when calculating P&L:
```sql
-- ❌ WRONG
SELECT * FROM trades WHERE symbol='APPLE'

-- ✅ RIGHT
SELECT * FROM trades WHERE symbol='APPLE' ORDER BY timestamp ASC
```

### Gotcha 5: Never Sell at Loss
**BUG-009**

Check setting in THREE places:
1. `safe_place_order_when_open()` — earliest interception
2. `risk_manager.execute()` — catastrophic stop
3. `_execute_broker_order()` — final guard

---

## Monitoring & Alerts

### Daily Checks
- Regression tests pass ✅
- Pre-commit hook active ✅

### Weekly Checks
- No new bugs reported ✅
- Nightly validation clean ✅

### Monthly Checks
- Full regression test suite ✅
- Code coverage > 80% ✅
- Review BUG_REGISTRY.md for patterns ✅

### Alert Triggers
- **RED**: Any test fails → investigate immediately
- **YELLOW**: Nightly validation warnings → review next day
- **GREEN**: All tests pass → good to deploy

---

## Resources

| Resource | Purpose | Location |
|----------|---------|----------|
| BUG_REGISTRY.md | Bug documentation | Root |
| test_regressions.py | Regression tests | tests/ |
| pre-commit.sh | Git hook | .claude/hooks/ |
| nightly_validation.py | Runtime validation | scripts/ |

---

## Questions?

If you're unsure:
1. Check **BUG_REGISTRY.md** for what tests what
2. Look at **test_regressions.py** for examples
3. Run **nightly_validation.py** to check system health
4. Review **pre-commit.sh** to see what patterns are blocked

---

**Last Updated:** 2026-06-21  
**Test Coverage:** 100% of known bugs  
**Status:** ACTIVE (all bugs fixed, regression tests in place)
