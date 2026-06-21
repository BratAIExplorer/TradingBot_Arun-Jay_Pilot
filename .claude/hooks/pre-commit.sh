#!/bin/bash
# Pre-Commit Hook - Prevent Known Bugs from Being Committed
#
# This hook runs before each commit to check for patterns that could
# reintroduce known bugs from BUG_REGISTRY.md
#
# Usage: .claude/hooks/pre-commit.sh

set -e

FAILED=0
WARNINGS=0

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🔍 Running pre-commit bug prevention checks..."
echo ""

# ============================================================================
# BUG-005: Hardcoded Credentials Check
# ============================================================================

echo "📋 Checking for hardcoded credentials (BUG-005)..."

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

for file in $STAGED_FILES; do
    # Skip .env and .venv files
    if [[ "$file" == ".env" ]] || [[ "$file" == ".venv"* ]]; then
        continue
    fi

    # Skip certain file types
    if [[ "$file" == *".pyc" ]] || [[ "$file" == *".pyo" ]]; then
        continue
    fi

    # Check for suspicious credential patterns
    if git diff --cached "$file" | grep -qE "(token=|AUTH_KEY=|password=|api_key=|secret_key=)" && \
       [[ "$file" != *".env"* ]]; then
        echo -e "${RED}❌ ERROR: Hardcoded credentials found in $file${NC}"
        echo "   Move credentials to .env file"
        FAILED=$((FAILED + 1))
    fi

    # Check for specific hardcoded tokens (common mistakes)
    if git diff --cached "$file" | grep -qE "(Bearer |token.*=.*['\"][a-zA-Z0-9_-]+['\"])" && \
       [[ "$file" != *"test"* ]]; then
        echo -e "${RED}❌ ERROR: Possible hardcoded token in $file${NC}"
        echo "   Store tokens in environment variables"
        FAILED=$((FAILED + 1))
    fi
done

# ============================================================================
# BUG-001: SCRIP LIMIT Error Pattern
# ============================================================================

echo "📋 Checking for SCRIP LIMIT hardcoding (BUG-001)..."

if git diff --cached | grep -q "SCRIP LIMIT INSUFFICIENT" && \
   ! git diff --cached | grep -q "except.*SCRIP LIMIT"; then
    echo -e "${YELLOW}⚠️  WARNING: SCRIP LIMIT error string found${NC}"
    echo "   Make sure this is part of error handling logic, not hardcoded"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# BUG-002: Database Schema Check
# ============================================================================

echo "📋 Checking database schema initialization (BUG-002)..."

if git diff --cached "**/trades_db.py" | grep -q "CREATE TABLE.*trades" && \
   ! git diff --cached "**/trades_db.py" | grep -q "system_control"; then
    echo -e "${YELLOW}⚠️  WARNING: Missing system_control table in schema${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# BUG-004: P&L Aggregation Check
# ============================================================================

echo "📋 Checking P&L aggregations for .fillna(0) (BUG-004)..."

for file in $STAGED_FILES; do
    if [[ "$file" == *".py" ]]; then
        # Check for P&L aggregations
        if git diff --cached "$file" | grep -q "\.sum()\|\.mean()\|\.agg(" && \
           git diff --cached "$file" | grep -q "pnl\|P&L\|profit" && \
           ! git diff --cached "$file" | grep -q "\.fillna(0)"; then
            echo -e "${YELLOW}⚠️  WARNING: P&L aggregation without .fillna(0) in $file${NC}"
            echo "   Add .fillna(0) to handle missing values"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
done

# ============================================================================
# BUG-006: SQL Query ORDER BY Check
# ============================================================================

echo "📋 Checking SQL queries for FIFO ordering (BUG-006)..."

for file in $STAGED_FILES; do
    if [[ "$file" == *".py" ]]; then
        # Look for trades queries
        if git diff --cached "$file" | grep -qE "FROM trades|FROM.*trades" && \
           ! git diff --cached "$file" | grep -q "ORDER BY"; then
            echo -e "${YELLOW}⚠️  WARNING: trades query without ORDER BY in $file${NC}"
            echo "   Add ORDER BY entry_time ASC for FIFO consistency"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
done

# ============================================================================
# BUG-007: Duplicate Protection Check
# ============================================================================

echo "📋 Checking for duplicate trade protection (BUG-007)..."

if git diff --cached "**/kickstart.py" | grep -q "def.*place_order\|def.*safe_place_order" && \
   ! git diff --cached "**/kickstart.py" | grep -q "_last_trade\|dedup\|duplicate"; then
    echo -e "${YELLOW}⚠️  WARNING: place_order function missing duplicate protection${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# BUG-008: Neutral Trades Check
# ============================================================================

echo "📋 Checking performance summary for neutral trades (BUG-008)..."

if git diff --cached "**/trades_db.py" | grep -q "performance_summary\|get_performance" && \
   ! git diff --cached "**/trades_db.py" | grep -q "neutral"; then
    echo -e "${YELLOW}⚠️  WARNING: performance_summary missing neutral_trades key${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# BUG-009: Never Sell at Loss Check
# ============================================================================

echo "📋 Checking never_sell_at_loss enforcement (BUG-009)..."

SELL_AT_LOSS_COUNT=$(git diff --cached "**/kickstart.py" | grep -c "never_sell_at_loss" || true)

if [ "$SELL_AT_LOSS_COUNT" -lt 3 ]; then
    echo -e "${YELLOW}⚠️  WARNING: never_sell_at_loss checked in < 3 places${NC}"
    echo "   Should have checks in: place_order, risk_manager, broker_order"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# Final Report
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ COMMIT BLOCKED: $FAILED critical issue(s)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) detected (non-blocking)${NC}"
    echo ""
    echo "Review the warnings above and decide:"
    echo "  - To commit anyway: git commit --no-verify"
    echo "  - To fix first: address the warnings and try again"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi
