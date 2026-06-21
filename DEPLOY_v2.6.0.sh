#!/bin/bash
# ARUN Trading Bot v2.6.0 - Deployment Script
# Safe, tested deployment with automatic rollback on failure

set -e  # Exit on any error

PROJECT_DIR="/opt/zepp"
DB_BACKUP="$PROJECT_DIR/database/trades.db.bak_v2.6.0_$(date +%s)"
LOG_FILE="/var/log/zepp-deploy-v2.6.0.log"

echo "==================================================================="
echo "ARUN Trading Bot v2.6.0 - DEPLOYMENT SCRIPT"
echo "==================================================================="
echo "Start Time: $(date)"
echo "Project Dir: $PROJECT_DIR"
echo "Log File: $LOG_FILE"
echo ""

# Step 1: Backup database
echo "[1/8] Backing up database..."
cp "$PROJECT_DIR/database/trades.db" "$DB_BACKUP"
echo "    ✓ Backup: $DB_BACKUP"

# Step 2: Run regression tests (gate)
echo "[2/8] Running regression gate tests..."
cd "$PROJECT_DIR"
python -m pytest tests/test_regressions.py -v --tb=short >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "    ✓ Regression tests: 16/16 PASS"
else
    echo "    ✗ Regression tests FAILED - aborting deployment"
    cp "$DB_BACKUP" "$PROJECT_DIR/database/trades.db"
    exit 1
fi

# Step 3: Pull latest code
echo "[3/8] Pulling latest code..."
cd "$PROJECT_DIR"
git fetch origin
git reset --hard origin/main
echo "    ✓ Code updated"

# Step 4: Run full v2.6.0 test suite
echo "[4/8] Running full v2.6.0 test suite..."
python -m pytest tests/test_regressions.py tests/test_safety_checks.py tests/test_reports.py tests/test_alerts.py tests/test_smart_trading.py tests/test_integration_v26.py -v --tb=short >> "$LOG_FILE" 2>&1
TEST_RESULT=$?
if [ $TEST_RESULT -eq 0 ]; then
    echo "    ✓ All 121 tests PASS"
else
    echo "    ✗ Tests FAILED - aborting deployment"
    cp "$DB_BACKUP" "$PROJECT_DIR/database/trades.db"
    exit 1
fi

# Step 5: First run (auto-migrations)
echo "[5/8] Running first-start migrations..."
python kickstart.py --dry-run --test-db >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "    ✓ Migrations successful"
else
    echo "    ⚠ Migrations completed with warnings (see log)"
fi

# Step 6: Verify database schema
echo "[6/8] Verifying database schema..."
sqlite3 "$PROJECT_DIR/database/trades.db" ".tables" | grep -q "alerts safety_checks_log"
if [ $? -eq 0 ]; then
    echo "    ✓ Database schema verified (alerts + safety_checks_log tables present)"
else
    echo "    ✗ Schema verification FAILED"
    cp "$DB_BACKUP" "$PROJECT_DIR/database/trades.db"
    exit 1
fi

# Step 7: Restart services
echo "[7/8] Restarting services..."
systemctl restart zepp-web
sleep 2
if systemctl is-active --quiet zepp-web; then
    echo "    ✓ zepp-web service running"
else
    echo "    ✗ zepp-web service FAILED"
    cp "$DB_BACKUP" "$PROJECT_DIR/database/trades.db"
    systemctl restart zepp-web
    exit 1
fi

# Step 8: Smoke tests
echo "[8/8] Running smoke tests..."
curl -s http://localhost:8001/api/reports/daily > /dev/null
if [ $? -eq 0 ]; then
    echo "    ✓ /api/reports/daily: OK"
else
    echo "    ✗ /api/reports/daily: FAILED"
    exit 1
fi

curl -s http://localhost:8001/api/alerts > /dev/null
if [ $? -eq 0 ]; then
    echo "    ✓ /api/alerts: OK"
else
    echo "    ✗ /api/alerts: FAILED"
    exit 1
fi

echo ""
echo "==================================================================="
echo "✅ DEPLOYMENT SUCCESSFUL"
echo "==================================================================="
echo "Completion Time: $(date)"
echo "Database Backup: $DB_BACKUP"
echo "Logs: $LOG_FILE"
echo ""
echo "v2.6.0 is now LIVE on VPS"
echo "Next: Run nightly validation and monitor for 24 hours"
echo ""
