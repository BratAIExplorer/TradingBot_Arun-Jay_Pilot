# Zepp Web Dashboard — AI Handover Document
**Created:** 2026-03-07
**Status:** PHASE 1 COMPLETE — needs deployment + kickstart.py trend filter wiring
**Assigned To:** Gemini (next AI session)
**Priority:** HIGH — web_api.py is built, VPS is ready, needs final wiring

---

## CONTEXT FOR INCOMING AI

"Zepp" is the web dashboard + remote control layer for the ARUN Trading Bot.
It runs on a Hostinger VPS (IP: 76.13.179.32, Ubuntu Linux).

**What Claude built in this session:**
- `web_api.py` — complete FastAPI server with mobile HTML dashboard
- `deploy/zepp-web.service` — systemd service file
- `deploy/zepp-trading.service` — systemd service file
- `deploy/nginx-zepp.conf` — nginx config (optional)
- `deploy/setup.sh` — one-shot VPS setup script

**What is NOT done yet (your job):**
1. Deploy code to VPS (`/opt/zepp/`)
2. Wire trend filter settings into `kickstart.py`
3. Add `requirements-zepp.txt` (optional — setup.sh handles deps directly)

---

## VPS FACTS (DO NOT CHANGE THESE)

| Property | Value |
|---|---|
| IP | 76.13.179.32 |
| OS | Ubuntu Linux |
| Zepp folder | `/opt/zepp/` (NEW — isolated) |
| Zepp port | **8001** (verified free) |
| Existing port 8000 | Already in use — DO NOT use |
| Existing services | nginx, cloudflared, uvicorn (port 8000), docker, postgresql |
| SSH user | root |

**Critical rule:** Do NOT modify any existing nginx config, services, or files outside `/opt/zepp/`.

---

## WHAT'S ALREADY RUNNING ON THE VPS

From `systemctl` output verified by the user:
- `nginx.service` — running, has existing sites
- `cloudflared` — Cloudflare tunnel for another project
- `uvicorn` (PID 1625430, port unknown but NOT 8001)
- `docker.service` — Docker containers running
- `postgresql@16-main.service` — PostgreSQL database

**Zepp uses port 8001 only.** It does not interact with any of these.

---

## FILES CREATED (all in the project root on Windows machine)

```
web_api.py                              ← FastAPI app (main file to deploy)
deploy/
├── setup.sh                            ← Run on VPS to set up /opt/zepp/
├── zepp-web.service                    ← systemd service for web_api.py
├── zepp-trading.service                ← systemd service for kickstart.py
└── nginx-zepp.conf                     ← Optional nginx proxy config
```

---

## WHAT web_api.py DOES

**Endpoints:**

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | Mobile HTML dashboard | None |
| GET | `/api/status` | Bot status, last trade, trades today | None |
| GET | `/api/positions` | Open positions (real trades only) | None |
| GET | `/api/trades` | Trade history, filterable | None |
| GET | `/api/performance` | Win rate, P&L summary (30d) | None |
| GET | `/api/settings` | Current settings (NO credentials) | None |
| POST | `/api/panic` | Emergency stop → sets DB flag | PIN |
| POST | `/api/control` | Start or stop bot | PIN |
| PUT | `/api/settings/trend-filter` | Update trend filter settings | PIN |
| GET | `/api/docs` | Auto-generated Swagger UI | None |

**Auth:** PIN is set in `/opt/zepp/.env` as `ZEPP_PIN=xxxxx`. Sent in POST body.

**DB access:** Reads `database/trades.db` via sqlite3 directly (NOT via TradesDatabase class).
Uses WAL journal mode to avoid locking conflicts with kickstart.py.

**Settings access:** Reads/writes `settings.json` directly via `json.load/dump`.

---

## DEPLOYMENT STEPS FOR GEMINI

### Step 1: Run setup.sh on the VPS
```bash
# SSH into VPS
ssh root@76.13.179.32

# Create the zepp directory first (setup.sh can also do this)
mkdir -p /opt/zepp

# Exit SSH, then upload setup.sh from Windows
# On Windows (in project directory):
scp deploy/setup.sh root@76.13.179.32:/tmp/setup.sh
ssh root@76.13.179.32 "bash /tmp/setup.sh"
```

### Step 2: Upload all project files to /opt/zepp/
```bash
# From Windows project directory (Git Bash):
# IMPORTANT: Use rsync or scp to exclude venv, __pycache__, .git, backups
scp -r web_api.py kickstart.py settings.json settings_manager.py \
    risk_manager.py state_manager.py utils.py constants.py \
    getRSI.py scanner_engine.py notifications.py secure_credentials.py \
    root@76.13.179.32:/opt/zepp/

# Upload database folder (empty DB will be created if not exists)
ssh root@76.13.179.32 "mkdir -p /opt/zepp/database /opt/zepp/logs"

# Upload strategy files
scp -r strategies/ root@76.13.179.32:/opt/zepp/strategies/
scp -r database/trades_db.py database/__init__.py root@76.13.179.32:/opt/zepp/database/
```

### Step 3: Set the PIN
```bash
ssh root@76.13.179.32 "nano /opt/zepp/.env"
# Change: ZEPP_PIN=CHANGE_THIS_PIN
# To:     ZEPP_PIN=yourActualPin123
```

### Step 4: Open firewall port 8001
**Manual step for the user — cannot be done via SSH:**
Go to Hostinger panel → VPS → Firewall → Add Rule:
- Protocol: TCP
- Port: 8001
- Source: Anywhere (0.0.0.0/0)

### Step 5: Start the web service
```bash
ssh root@76.13.179.32
systemctl start zepp-web
systemctl enable zepp-web
systemctl status zepp-web
```

### Step 6: Test
Open from phone: `http://76.13.179.32:8001`
Should show the Zepp dashboard with loading spinners, then live data.

### Step 7 (Optional): nginx proxy for port 80 access
Only if user wants `http://76.13.179.32/zepp/` instead of `:8001`:
```bash
cp /opt/zepp/deploy/nginx-zepp.conf /etc/nginx/sites-available/zepp
ln -s /etc/nginx/sites-available/zepp /etc/nginx/sites-enabled/zepp
nginx -t   # MUST test first — if this fails, do NOT reload
systemctl reload nginx
```

---

## REMAINING CODE WORK (kickstart.py)

### Trend Filter Wiring (kickstart.py ~line 2402)

The web API can already UPDATE the trend filter settings in settings.json.
But kickstart.py does NOT yet READ and APPLY them during trading decisions.

**Find this block in kickstart.py (around line 2402):**
```python
if (ignore_rsi or last_rsi <= buy_rsi) and is_market_open_now_ist() and not check_existing_orders(...):
```

**Add BEFORE this block:**
```python
# --- Trend Filter (configurable from Zepp web dashboard) ---
tf_config = settings.get('strategies', {}).get('trend_filter', {}) if settings else {}
trend_filter_on = tf_config.get('enabled', False)
in_uptrend = True  # default: filter off = always allow buy

if trend_filter_on and df is not None and not df.empty:
    ma_period = int(tf_config.get('ma_period', 50))
    ma_type = tf_config.get('ma_type', 'SMA')
    try:
        if ma_type == 'EMA':
            ma_value = df['close'].ewm(span=ma_period, adjust=False).mean().iloc[-1]
        else:
            ma_value = df['close'].tail(ma_period).mean()
        in_uptrend = current_close > ma_value
        if not in_uptrend:
            log_ok(f"[TrendFilter] {symbol} SKIPPED: Price ₹{current_close:.2f} < {ma_type}{ma_period} ₹{ma_value:.2f}")
    except Exception as e:
        log_ok(f"[TrendFilter] WARNING: Could not compute MA for {symbol}: {e}")
        in_uptrend = True  # fail open — don't block trades if MA calc fails
```

**Then modify the buy condition:**
```python
# Change FROM:
if (ignore_rsi or last_rsi <= buy_rsi) and is_market_open_now_ist() and not check_existing_orders(...):

# Change TO:
if (ignore_rsi or last_rsi <= buy_rsi) and in_uptrend and is_market_open_now_ist() and not check_existing_orders(...):
```

**Critical notes:**
- `df` must be in scope at line ~2402 — check it is (it's the historical OHLC dataframe)
- `settings` is the settings dict loaded by settings_manager — already in scope
- `current_close` is already in scope at that point
- `log_ok` is the logging function already used throughout kickstart.py

---

## COLOR / STYLE REFERENCE (for any UI additions)

The Zepp dashboard uses the same color theme as the desktop Titan V2 GUI:
```
--bg:      #EFEBE3  (warm parchment background)
--card:    #FFFFFF  (white cards)
--accent:  #479FB6  (teal — primary color)
--success: #10B981  (green — profits, running)
--danger:  #EF4444  (red — losses, stopped, panic)
--warn:    #F59E0B  (amber — warnings)
```
Font: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto` (system fonts, no import needed)

---

## SETTINGS.JSON ADDITIONS NEEDED

The trend filter key needs to exist for the web API's GET /api/settings to return it.
Add this to `settings.json` under `"strategies"`:

```json
"trend_filter": {
    "enabled": false,
    "ma_period": 50,
    "ma_type": "SMA"
}
```

The web API will create it automatically when the user first saves from the dashboard.
But adding it upfront makes GET /api/settings return it correctly from day 1.

---

## STOPPING POINT FOR GEMINI

**DO NOT start the trading engine (zepp-trading.service) on the VPS
until the user explicitly asks you to.**

The user currently runs kickstart.py on their local Windows machine.
Moving it to the VPS is a separate decision. For now:
- Start ONLY `zepp-web.service` (read-only dashboard)
- The DB on the VPS will be empty initially — that is fine
- The user can copy their local trades.db to VPS later if they want history

---

## TESTING CHECKLIST

- [ ] `http://76.13.179.32:8001` loads on phone browser
- [ ] Dashboard shows "Bot Status: UNKNOWN" (empty DB is fine)
- [ ] Trend filter toggle + slider + dropdown respond correctly
- [ ] Panic stop prompts for PIN, sends request, gets response
- [ ] `/api/docs` loads Swagger UI
- [ ] `systemctl status zepp-web` shows "active (running)"
- [ ] `tail -f /opt/zepp/logs/web.log` shows request logs
- [ ] Existing services still running: `systemctl status nginx cloudflared docker`

---

*Document created by Claude Sonnet 4.6 on 2026-03-07.*
*Zepp v1.0 — web_api.py complete. Deploy to VPS, then wire trend filter in kickstart.py.*
