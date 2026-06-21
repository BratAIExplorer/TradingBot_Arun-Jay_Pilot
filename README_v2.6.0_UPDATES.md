# ARUN Trading Bot v2.6.0 — README UPDATES

## Quick Start

**v2.6.0 introduces 4 major features:**

1. **Safety Checks** — Real-time validation prevents known bugs
2. **Alert System** — Smart notifications with daily deduplication  
3. **Reports API** — Live P&L dashboards for web + mobile
4. **Smart Trading Rules** — Per-stock risk configuration

---

## Installation & Setup

### Requirements
```
Python 3.8+
SQLite3
pytest (for testing)
customtkinter (GUI)
FastAPI (web API)
```

### Quick Setup
```bash
# Clone repo
git clone <repo> && cd TradingBots-Aruns-Project

# Install deps
pip install -r requirements.txt

# Run all tests (should be 121/121 GREEN)
pytest tests/ -v

# Start trading engine
python kickstart.py

# Start web dashboard (separate terminal)
python web_api.py  # http://localhost:8001
```

---

## New in v2.6.0

### Safety Checks API

```python
from safety_checks import SafetyChecker

# Prevent duplicate trades, position mismatches, P&L violations
checker = SafetyChecker(db=db, settings=settings)
results = checker.run_all(
    symbol="HDFCBANK",
    broker_positions=broker_positions,
    allocated_capital=100000,
    total_capital=150000,
    deployed_capital=30000,
    daily_pnl=daily_pnl,
    daily_loss_limit_pct=5.0
)

# Returns list of CheckResult objects
for result in results:
    if result.severity == "CRITICAL":
        logger.error(f"ALERT: {result.message}")
```

### Alert System

```python
from notifications import NotificationManager

notifier = NotificationManager(settings)

# Automatically deduped (same alert/day = 1 email)
notifier.send_alert(
    event_type="TRADE_EXECUTED",
    severity="INFO",
    message="Bought 10 HDFCBANK @ ₹1500",
    symbol="HDFCBANK",
    value=1500.0
)

# Check alerts in database
cursor.execute("SELECT * FROM alerts WHERE unacknowledged = 1")
for alert in cursor.fetchall():
    print(f"[{alert['severity']}] {alert['message']}")
```

### Reports API

```bash
# Daily P&L series (for charts)
curl http://localhost:8001/api/reports/daily?days=30

# Cumulative equity curve
curl http://localhost:8001/api/reports/equity?days=90

# Per-symbol performance
curl http://localhost:8001/api/reports/by-symbol?days=30

# Recent alerts
curl http://localhost:8001/api/alerts?limit=50&unack=true

# Acknowledge alert (PIN-protected)
curl -X POST http://localhost:8001/api/alerts/ack \
  -H "Content-Type: application/json" \
  -d '{"pin": "your-pin", "alert_id": 123}'
```

### Smart Trading Rules

Add to your `settings.json` stocks:

```json
{
  "stocks": [
    {
      "symbol": "HDFCBANK",
      "exchange": "NSE",
      "risk_tier": "aggressive",           // aggressive|moderate|conservative
      "min_volume": 100000,                // Skip BUY if volume < this
      "trend_filter_override": true        // null=global, true/false=override
    },
    {
      "symbol": "INFY",
      "exchange": "NSE",
      "risk_tier": "conservative",
      "min_volume": 50000
    }
  ]
}
```

**Risk Tiers Impact:**
```
aggressive:    15% per-trade, 8% stop-loss, 1.5x profit target
moderate:      10% per-trade, 5% stop-loss, 1.0x profit target (DEFAULT)
conservative:  5% per-trade, 3% stop-loss, 0.75x profit target
```

---

## Testing

### Run All Tests
```bash
pytest tests/ -v --cov=. --cov-report=html

# By category
pytest tests/test_regressions.py -v        # 16 tests: Known bugs prevention
pytest tests/test_safety_checks.py -v      # 24 tests: Safety layer
pytest tests/test_reports.py -v            # 16 tests: Reports API
pytest tests/test_alerts.py -v             # 19 tests: Alert system
pytest tests/test_smart_trading.py -v      # 21 tests: Trading rules
pytest tests/test_integration_v26.py -v    # 22 tests: End-to-end flows

# Regression gate (must pass before any deployment)
pytest tests/test_regressions.py -v
```

### Coverage
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Database

### New Tables (v2.6.0)

**alerts** — Stores all system alerts with deduplication
```sql
id, timestamp, event_type, severity, symbol, message, 
dedup_key, delivered_email, acknowledged
```

**safety_checks_log** — Audit trail of safety validations
```sql
id, timestamp, check_name, passed, severity, message, data_json
```

Both tables created automatically on first run via migrations.

### Backup & Restore

```bash
# Backup before deploy
cp database/trades.db database/trades.db.bak_v2.6.0_$(date +%s)

# Restore if needed
cp database/trades.db.bak_v2.6.0_1234567890 database/trades.db
```

---

## Deployment

### VPS Deployment

```bash
# Automated (recommended)
bash DEPLOY_v2.6.0.sh

# Manual
git pull origin main
pytest tests/test_regressions.py -v           # Gate check
systemctl restart zepp-web
curl http://localhost:8001/api/reports/daily  # Smoke test
```

### Verify Installation

```bash
# Check tables exist
sqlite3 database/trades.db ".tables"
# Should show: alerts safety_checks_log trades...

# Test API endpoints
curl http://localhost:8001/api/reports/daily
curl http://localhost:8001/api/alerts

# Run nightly validation
python scripts/nightly_validation.py
```

---

## Configuration

### settings.json New Keys

```json
{
  "alerts": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your-email@gmail.com",
    "smtp_password": "app-password"   // Use app password, not gmail password
  },
  "safety": {
    "enabled": true,
    "fail_open": true                 // Fail-open on non-critical checks
  },
  "stocks": [
    {
      "symbol": "HDFCBANK",
      "risk_tier": "moderate",
      "min_volume": 100000
    }
  ]
}
```

### Environment Variables

```bash
# Optional: Override SMTP via env
export ZEPP_SMTP_SERVER=smtp.gmail.com
export ZEPP_SMTP_USER=your-email@gmail.com
export ZEPP_SMTP_PASSWORD=app-password
```

---

## Monitoring

### Web Dashboard

```
http://localhost:8001

Tabs (new in v2.6.0):
- Reports: Daily P&L charts, per-symbol breakdown
- Alerts: Recent notifications, acknowledgement
- Settings: Configure risk tiers, volume checks
```

### Nightly Validation

```bash
# Run daily to catch bugs early
python scripts/nightly_validation.py

# Checks:
# - Database schema integrity
# - Duplicate trades in live DB
# - Missing P&L entries
# - Trade timestamp ordering (FIFO)
# - Settings validation
```

### Alert Monitoring

```bash
# List recent unacknowledged alerts
sqlite3 database/trades.db "SELECT * FROM alerts WHERE acknowledged = 0 LIMIT 10"

# Acknowledge alert
sqlite3 database/trades.db "UPDATE alerts SET acknowledged = 1 WHERE id = 123"
```

---

## Troubleshooting

**Q: Tests failing?**  
A: Run `pytest tests/test_regressions.py -v` to verify known bugs are protected. If that passes, your system is safe.

**Q: Alerts not sending?**  
A: Check SMTP settings in settings.json. Use app-specific password for Gmail. Verify network access to SMTP server.

**Q: API returning 500?**  
A: Check `/opt/zepp/logs/zepp-web.log` for errors. Run database validation: `python scripts/nightly_validation.py`

**Q: Duplicate alerts?**  
A: Check `dedup_key` format. Same key on same day = no duplicate (by design).

**Q: Reports showing zeros?**  
A: Normal if no trades today. Reports use on-demand calculation. Check `/api/reports/daily?days=30` for historical data.

---

## Performance

### Query Optimization

```sql
-- Daily P&L (indexed by timestamp)
SELECT DATE(timestamp), SUM(pnl_net) FROM trades 
GROUP BY DATE(timestamp)
ORDER BY timestamp DESC LIMIT 30;

-- Per-symbol breakdown (indexed by symbol)
SELECT symbol, COUNT(*), SUM(pnl_net) FROM trades
GROUP BY symbol
ORDER BY pnl_net DESC;
```

### Database Maintenance

```bash
# Analyze indices (monthly)
sqlite3 database/trades.db "ANALYZE;"

# Vacuum (cleanup, quarterly)
sqlite3 database/trades.db "VACUUM;"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.5.2 | 2026-02-16 | Never Sell at Loss (3-layer defense) |
| v2.5.1 | 2026-02-01 | Security audit fixes |
| v2.5.0 | 2026-01-20 | Panic stop, RMS cooldown |
| **v2.6.0** | **2026-06-21** | **Safety checks, alerts, reports, smart rules** |

---

## Support

**Documentation:** See `CLAUDE_v2.6.0_ADDENDUM.md` for detailed docs  
**Tests:** `pytest tests/ -v` for full test output  
**Issues:** Check `BUG_REGISTRY.md` for known issues  
**Logs:** `/var/log/zepp-web.log` (VPS), `logs/kickstart.log` (local)

---

**Status:** ✅ Production Ready  
**Confidence:** 101%  
**Last Updated:** 2026-06-21
