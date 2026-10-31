# ARUN Trading Bot — System Architecture Document
**Created:** 2026-03-07
**Author:** Claude Sonnet 4.6 (Senior Architect role)
**Status:** CURRENT — reflects live system as of v2.5.2 + Zepp v1.0

---

## 1. System Overview

A three-tier automated trading system with a single source of truth on the VPS.
Every client (desktop or web) reads from and writes to the same data layer
through a controlled API gateway.

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                           │
│              mStock Broker API (api.mstock.trade)               │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS Orders / Market Data
┌─────────────────────────▼───────────────────────────────────────┐
│                    HOSTINGER VPS  76.13.179.32                   │
│                                                                 │
│  ┌─────────────────┐      ┌──────────────────────────────────┐  │
│  │  kickstart.py   │      │        web_api.py (Zepp)         │  │
│  │  Trading Engine │      │        FastAPI :8001             │  │
│  │  (zepp-trading) │      │        (zepp-web)                │  │
│  └────────┬────────┘      └───────────────┬──────────────────┘  │
│           │  write                        │ read (WAL)          │
│           └──────────┬────────────────────┘                     │
│                      ▼                                          │
│         ┌─────────────────────────┐                             │
│         │  database/trades.db     │  settings.json              │
│         │  SQLite (WAL mode)      │  (shared config)            │
│         └─────────────────────────┘                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST :8001
          ┌────────────────┴────────────────┐
          │                                 │
┌─────────▼──────────┐           ┌──────────▼──────────┐
│   Web Browser      │           │   Desktop GUI        │
│   (Zepp HTML)      │           │   sensei_v1_         │
│   Phone / Tablet   │           │   dashboard.py       │
│   Any device       │           │   Windows Laptop     │
└────────────────────┘           └─────────────────────┘
```

---

## 2. Component Responsibilities

| Component | File | Responsibility | Location |
|---|---|---|---|
| Trading Engine | kickstart.py | RSI logic, orders, risk management, DB writes | VPS (target) / Laptop (current) |
| Zepp API Gateway | web_api.py | REST API, auth, settings, panic stop | VPS (LIVE) |
| Web Dashboard | Served by web_api.py | Mobile monitoring, trend filter, panic button | VPS (LIVE) |
| Desktop GUI | sensei_v1_dashboard.py | Full control panel, settings, scanner | Windows laptop |
| Database | database/trades.db | Single source of truth — all trades, positions | VPS (target) |
| Config Store | settings.json | Strategy settings, capital, risk — shared | VPS (target) |
| State Store | state_manager.py JSON | Crash recovery, position state | VPS (target) |
| Broker Layer | mStock API | Order execution, portfolio data | External HTTPS |

---

## 3. Architecture Principles

**1. Single Write Source**
Only kickstart.py inserts trade records. No other component writes to the trades table.

**2. API Gateway for All Reads**
Both desktop and web read through web_api.py. No direct SQLite connections from clients (target state).

**3. Control via system_control Table**
Panic stop, start, and settings changes write to the DB system_control table.
The engine polls it. No direct process signals needed.

---

## 4. Connection Flows

### Current State (laptop-centric)
```
Laptop: kickstart.py → local trades.db ← sensei_v1_dashboard.py
VPS:    web_api.py   → VPS trades.db   (empty — no live trading data yet)
```

### Target State (VPS-centric)
```
VPS: kickstart.py → VPS trades.db ← web_api.py ← [any browser / phone]
                         ↑
              sensei_v1_dashboard.py (via API, not direct DB)
```

### Desktop Dashboard — Migration Path
```python
# Feature flag — zero breaking change
USE_REMOTE_API = settings.get("app_settings.use_remote_api", False)

if USE_REMOTE_API:
    data = zepp_api_client.get_positions()   # HTTP call to VPS
else:
    data = trades_db.get_open_positions()    # local SQLite (existing, unchanged)
```

### Panic Stop Flow (critical path)
```
User taps PANIC on phone or desktop
  → POST /api/panic  {pin: "xxxx"}
  → web_api.py verifies PIN
  → writes system_control: bot_status = 'STOP'
  → kickstart.py polls system_control every ~30s
  → kickstart.py sees STOP → halts trading cycle
  → no orders placed, positions preserved
```

---

## 5. Concurrent Access Strategy

### Dashboard + Web simultaneously: YES, safe

Both are read-only clients (except panic/settings).
Trading engine is the only writer to the trades table.

**SQLite WAL Mode** (enabled in web_api.py):
Multiple simultaneous readers + one writer without blocking.

**Settings Race Condition Prevention:**
Add file lock on PUT /api/settings/* endpoints:
```python
import fcntl
with open(SETTINGS_PATH, "r+") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    json.dump(data, f, indent=2)
    fcntl.flock(f, fcntl.LOCK_UN)
```

**Duplicate Order Guard:** Already in trades_db.py (BUG-04):
```python
SELECT id FROM trades WHERE symbol=? AND action=? AND quantity=?
  AND ABS(price-?) < 0.01
  AND datetime(timestamp) >= datetime('now', '-10 seconds')
```

**Control Command Ordering:**
RUNNING/STOP is a simple flag. Last writer wins. Correct behavior.
Engine reads it at start of each cycle — no race condition.

---

## 6. Dashboard Safety Strategy

### Layer 1 — Feature Flag (zero-risk migration)
```json
"app_settings": {
    "use_remote_api": false
}
```
false = local DB (current behavior). true = Zepp API. Flip when ready. Revert instantly.

### Layer 2 — Git Branch Strategy
```
main              ← production (running on laptop today)
feature/zepp      ← web/API development
feature/api-mode  ← desktop API migration
```
Nothing merges to main until tested on feature branch.

### Layer 3 — Backup Before Every Deployment
```bash
# VPS — run before any update:
cp /opt/zepp/database/trades.db /opt/zepp/database/trades.db.bak.$(date +%Y%m%d)
cp /opt/zepp/settings.json /opt/zepp/settings.json.bak.$(date +%Y%m%d)
```

### Layer 4 — API Versioning
Current endpoints: /api/status, /api/positions, etc.
Future: /api/v1/status — add versioning before clients depend on structure.
Unversioned endpoints become aliases to v1 for backward compatibility.

### Layer 5 — Rollback Plan
| Scenario | Rollback |
|---|---|
| VPS trading engine crashes | systemctl stop zepp-trading → restart kickstart.py on laptop |
| Zepp API breaks | systemctl stop zepp-web → desktop falls back to local DB (use_remote_api: false) |
| Settings corrupted | cp settings.json.bak.DATE settings.json |
| trades.db corrupted | cp trades.db.bak.DATE trades.db → verify row count |
| Wrong code deployed | git checkout main → re-deploy |

---

## 7. Implementation Roadmap

### Phase 1 — COMPLETE (2026-03-07)
- Zepp web_api.py built and deployed on VPS
- Web dashboard live at http://76.13.179.32:8001
- Trend filter wired into kickstart.py, configurable from web
- BUG-01/02/04/05 fixed in trades_db.py
- Architecture documented

### Phase 2 — COMPLETE (2026-03-08)
**P&L Backfill** — 21/34 historical SELL trades backfilled using mstock_statement.csv
Result: 97% P&L coverage, net ₹-36,617, win rate 24.2%
Script: database/backfill_pnl.py (kept, DRY_RUN=True)

### Phase 3 — NEXT (after Phase 2 verified)
**Move trading engine to VPS**
- Copy local trades.db to /opt/zepp/database/trades.db
- Copy local settings.json to /opt/zepp/settings.json
- Stop local kickstart.py on laptop
- systemctl start zepp-trading (paper mode first, 1-day observation)
- Verify Zepp web dashboard shows live trade data

### Phase 4 — STABILIZATION
**Desktop GUI API mode**
- Add use_remote_api flag + zepp_api_client.py
- sensei_v1_dashboard.py reads from VPS API
- Both desktop and web show identical live data

### Phase 5 — SECURITY HARDENING
- Domain + Let's Encrypt HTTPS
- Cloudflare DNS
- JWT token auth (30-min expiry, replacing PIN)

### Phase 6 — REAL-TIME UPDATES
- WebSocket endpoint in web_api.py
- Dashboard updates in real time (5s push vs 30s poll)

### Phase 7 — MOBILE PWA
- manifest.json + service worker
- "Add to Home Screen" installable app
- Push notifications via Telegram (already built)

---

## 8. Architecture Decision Record

| Decision | Choice | Reason |
|---|---|---|
| Database | SQLite (not PostgreSQL) | Zero ops overhead, sufficient for single-user, WAL handles concurrency |
| API framework | FastAPI | Async, auto-docs, Pydantic validation, production-grade |
| Auth | PIN in request body | Personal tool, no user accounts, fast to implement |
| Deployment | systemd (not Docker) | Simpler, no container overhead, direct filesystem access for SQLite |
| Frontend | Vanilla JS HTML (not React) | No build step, single file, works offline, fast mobile load |
| DB access from API | Direct sqlite3 (not ORM) | Full control, matches existing codebase style |

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Trading engine crashes on VPS mid-trade | Low | High | systemd auto-restart (30s), state_manager.py crash recovery |
| VPS down during market hours | Very Low | High | Hostinger SLA 99.9%. Bot stops cleanly, no orphaned orders |
| mStock API token expires mid-session | Medium | High | TOTP auto-refresh already implemented in kickstart.py |
| Conflicting settings from web + desktop | Low | Medium | File lock on settings writes (to be added Phase 4) |
| trades.db corruption | Very Low | High | Daily backup cron job on VPS (to be set up Phase 3) |

---

## 10. Related Documents

| Document | Path | Purpose |
|---|---|---|
| P&L Bug Fix Spec | Documentation/Technical/PNL_ACCURACY_BUGFIX.md | 5 bugs, implementation order, backfill spec |
| Zepp Deployment | Documentation/Technical/ZEPP_WEB_HANDOVER.md | VPS setup, trend filter wiring, stopping points |
| Security Audit | Documentation/Technical/SECURITY_ARCHITECTURE_AUDIT_v2.5.0.md | All P0-P3 fixes |
| Error Log | Documentation/Technical/ERROR_LOG_AND_FIXES.md | Historical fixes |
| AI Handover | Documentation/Technical/AI_HANDOVER.md | General AI session handover |
| Project Status | Documentation/Technical/PROJECT_STATUS.md | Current version, feature status |
