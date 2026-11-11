# Voyager — US Markets (IBKR) Status

**Last updated:** 2026-09-21 (dip-rules engine + dashboard tab added; see section 8)
**What this is:** the IBKR/US-markets module living inside `TradingBot` — a separate
broker and account from the existing mStock engine, sharing this codebase but nothing
else. Named Voyager for the same reason it exists: reaching beyond the home market.

**Not a separate project.** Same repo, same rules — see the top-level `CLAUDE.md`
money-risk guidance. Deliberately kept in `TradingBot` instead of a new folder, to avoid
the twin-project risk the project's own rules warn about.

---

## 1. What's actually live right now

- **Real IBKR account connected and validated.** Account `U19352250`, live (not paper —
  the paper account application is still pending IBKR approval as of this writing).
- **Real positions held**, opened during testing:
  - `HL` — 1 share, Market order, filled at $18.905
  - `PATH` — 1 share, Market order, filled at $13.9395
  - `FRSH` — 1 share, **Limit** order, filled at $12.788
  - Each has a **GTC Limit sell order resting at +15%** of its fill price
    (HL $21.74 / PATH $16.03 / FRSH $14.71) — confirmed independently via both the
    API and Gateway's own log, not just trusted from script output.
- **Pre-existing positions** (from before this work started): CDE, GSAT, RSSS, AXTI,
  IVES, CHPY.
- **Web dashboard IBKR tab**, live at `/dashboard` → IBKR, showing real balance,
  positions, live P&L (unrealized + realized), market price/value, and best-effort
  purchase date.

## 2. Architecture

```
brokers/
  interface.py       BrokerInterface Protocol — the contract both brokers satisfy
  factory.py          get_broker("IN"|"US") — routes to the right implementation
  mstock_adapter.py    Wraps kickstart.py's existing functions, unchanged
  ibkr_broker.py        Real ib_insync implementation — connect/funds/positions/
                         portfolio/quote/place_order
  test_factory.py       Self-test: Protocol conformance, no live calls
  check_ibkr_connection.py   Manual read-only check (funds/positions/quote)
  lookup_symbol.py       Read-only: what exchange/currency does IBKR have for a ticker
  test_live_order.py      Single-symbol order test, Market or Limit, CONFIRM-gated
  buy_with_target.py       Batch: buy N symbols, auto-place GTC profit-target sells
```

**Deliberately NOT done:** `kickstart.py` is not wired to `get_broker()`. The mStock
engine still calls its own functions directly. Rewiring it is saved for later —
touching the live engine's order path is the risky part, done once, not twice.

```
deploy/
  setup_ibgateway.sh              Installs Xvfb + IB Gateway + IBC on the VPS
  ibgateway-headless.service      systemd unit: Xvfb + IBC-driven Gateway login
  ibc/config.ini.template         IBC login config — copy, fill in, keep off git
  backup_db.sh                    sqlite .backup (not cp) of all 3 DBs, 30-day retention
  tradingbot-backup.service/.timer   Runs backup_db.sh every 6h via systemd
```

**Backup guardrails (setup.sh + backup_db.sh):** `sqlite3 .backup` instead of a raw
file copy, so a live write mid-backup can't produce a torn/corrupt file. The retention
sweep only deletes files it wrote itself, inside `backups/`, never the live
`database/` files. `*.db` is already git-ignored. Local-disk only — for real
disaster recovery, `backups/` still needs an off-box copy (rsync/scp), not done here.

## 3. Connection details (for whoever runs this next)

- **TWS API via `ib_insync`**, socket connection to **IB Gateway** (not TWS, not the
  Client Portal REST API) — chosen because Project Vayu already hit Malaysia-region
  access restrictions on the Client Portal/Flex path; this VPS is also Malaysia-based.
- **Ports**: 4001 = Gateway live, 4002 = Gateway paper, 7496/7497 = TWS equivalents.
  Set via `IBKR_PORT` env var — **must be set in the environment of whichever process
  connects**, read once at import time. Forgetting this on a service restart causes a
  silent, confusing "connection refused" even when Gateway is running fine (hit this
  twice during testing — see Bugs Found, below).
- **clientId**: manual scripts use `7`, the dashboard uses `9` — kept different on
  purpose so they don't collide (IBKR allows one connection per clientId).
- **Read-Only API**: a Gateway setting that blocks all order-placement server-side,
  independent of the code. Was ON for read-only validation, deliberately turned OFF
  by the user before any real order was placed.

## 4. Real bugs found and fixed during this work

1. **Event loop crash calling IBKR from a web request.** `ib_insync` needs an asyncio
   event loop in whatever thread it runs in; FastAPI's worker threads don't have one
   by default. Fixed in `IBKRBroker.connect()` — creates one if missing.
2. **Order silently discarded after a fast disconnect.** The original `test_live_order.py`
   disconnected immediately after `place_order()` returned; an order not yet fully
   acknowledged downstream can get dropped. Fixed by waiting for a real status update
   (Filled/Cancelled/Submitted) before disconnecting.
3. **`IBKR_PORT` not propagating to the dashboard's server process.** The variable is
   read once at import time — a server started without it set silently defaults to
   4002 (paper) and every IBKR call fails with "connection refused," even with Gateway
   running fine on 4001. Fixed locally (restart with the var set) and in
   `deploy/setup.sh` (the VPS `.env` template now includes it) — otherwise this exact
   bug would have resurfaced, harder to diagnose, on the VPS.
4. **`₹` shown on real USD amounts.** The dashboard's money formatter was hardcoded
   for the mStock tabs' rupees; the IBKR tab reused it blindly. Fixed with a separate
   USD formatter.
5. **NaN crashing the Stocks API endpoint** (mStock side, found while building the
   dashboard, unrelated to IBKR specifically) — blank CSV cells become pandas `NaN`,
   which isn't valid JSON. Nulled before returning.

## 5. Known gaps — real, not hidden

- **Direct-routing fee on European-listed ETFs.** IUIT and EQQQ (Ireland-domiciled
  UCITS ETFs) hit an IBKR Precautionary Setting blocking direct-routed orders to
  `LSEETF` (real fee difference found: $4 smart-routed vs. $6 direct-routed minimum
  commission for a 1-share order). Parked, unresolved — needs a decision on whether
  the fee tradeoff is worth it, and possibly a fix to route through Smart Routing
  instead of forcing the primary listing's exchange code.
- **No stop-loss on the three new positions.** The GTC sells are profit targets only
  — nothing protects the downside if HL/PATH/FRSH move against you instead.
- **Purchase date is best-effort, not a lot-level record.** Built from the earliest
  BUY execution found via `reqExecutions()`, which only returns the *current
  session's* history — positions opened before today (CDE, GSAT, RSSS, AXTI, IVES,
  CHPY) show "unknown." A full history needs an IBKR Flex Query report, not built.
- **IBKR uses average-cost accounting**, not per-lot (FIFO/LIFO) tracking. Realized
  P&L and cost basis blend across all purchases of a symbol — fine for a glance-at
  dashboard, not precise enough for tax reporting if that's ever needed.
- **IB Gateway headless-on-VPS is scripted but not yet deployed/verified.**
  `deploy/setup_ibgateway.sh` + `deploy/ibgateway-headless.service` +
  `deploy/ibc/config.ini.template` install Xvfb + IB Gateway + IBC and run Gateway
  as a systemd service. Needs a real run on the actual VPS (fill in
  `ibc/config.ini` with real IBKR login, verify `check_ibkr_connection.py` goes
  green) before this gap can be marked closed.
- **RSI / day-change / position-weight** — not shown on the IBKR tab yet. RSI
  specifically requires pulling historical bars and computing it ourselves; IBKR
  doesn't provide it.

## 6. Dashboard tabs — what's mStock-only vs. IBKR

| Tab | Broker |
|---|---|
| mStock, Capital, Risk, Setup, Logs, Stocks, Trades | mStock only — no IBKR equivalent exists for any of these |
| IBKR | IBKR only |

These were never mixed — the mStock tabs simply hadn't been labeled that way until
the confusion surfaced during testing (they were all still called generic names like
"Home" before this).

## 7. Suggested next steps, roughly in order of what unblocks what

1. Decide: direct-routing fee tradeoff for IUIT/EQQQ — pay it, or find another route.
   **Trading decision — not done here, needs a human to place the order.**
2. Add a stop-loss leg to the three open positions, if wanted.
   **Trading decision — not done here, needs a human to place the order.**
3. IB Gateway unattended on the VPS — **DONE, running live (2026-09-21).**
   Stand-alone on the shared VPS `76.13.179.32`: `Voyager` branch in `/opt/voyager`,
   services `voyager-gateway` (IB Gateway 10.45 + IBC in `/opt/voyager-ibc`, live port
   4001; read-only via `ReadOnlyApi=yes` in `/opt/voyager-ibc/config.ini` — NOTE `ReadOnlyLogin` is NOT supported by Gateway and does nothing; verified in the IBC log) and `voyager-web` (dashboard on
   `127.0.0.1:8011`), both enabled at boot. View via
   `ssh -L 8011:127.0.0.1:8011 root@76.13.179.32` → http://localhost:8011/dashboard.
   Port 4001 is firewalled from outside. Needs IBKR-mobile 2FA approval on each
   Gateway (re)start, including IBKR's daily restart. One live session per IBKR user:
   the laptop Gateway cannot run while the VPS holds it. 2FA sometimes completes with no new phone prompt (IBKR accepts a recent approval); check IBKR Client Portal login history if unsure. Dashboard refresh takes ~4s because Gateway pops a harmless "write access" dialog per connect; `IBKR_READONLY=1` env switch exists in `brokers/ibkr_broker.py` but is untested (left off). Extra apt package needed:
   `libxtst6 libxi6 libxrender1`. PR #8 is a draft that never merges (`main` = desktop tool).
4. `kickstart.py` → `get_broker()` rewiring — **deliberately not started.** This
   touches the live mStock engine's order path; per `HANDOVER_HEADLESS_VPS.md`
   Phase 4, it must be done in paper mode first, by someone who can watch it run.
5. Flex Query integration for full purchase-history / lot tracking — **blocked on
   IBKR account setup** (a Flex Query report + token must be created in the IBKR
   web portal first; nothing to build in code until that exists).

## 8. Dip rules — buy-the-dip / sell-at-% engine (added 2026-09-21)

**Status: deployed in DRY-RUN only. No real orders. Pass 2 (stop-loss/cooldown) was dropped — see 8.5.**

### 8.1 What it does
Per rule (max 25 stocks, edited on the dashboard **Dip Rules** tab): no position and no resting BUY and
price <= N-day high x (1 - dip%) -> BUY `$ per buy` worth of whole shares at market; position held and no
resting SELL -> GTC limit SELL at avg cost x (1 + sell%). Checked every `VOYAGER_INTERVAL_MIN` (default 15).

### 8.2 Files
```
brokers/dip_engine.py         rules + pure decide() + run_once() + the loop (python -m brokers.dip_engine)
backend/voyager_routes.py     /api/voyager/{rules,state,preview}; PUT /rules is PIN-gated (TRADINGBOT_PIN)
backend/static/dashboard.html Dip Rules tab: status strip, filter counters, one card per stock, save bar
tests/test_dip_engine.py      9 pytest tests (safety guards, state file, validation)
deploy/voyager-engine.service systemd unit, dry-run by default (NOT installed automatically)
research/bt_voyager_dip.py    the backtest behind the Pass 2 decision (python research/bt_voyager_dip.py 5 0.3)
voyager_rules.json            the rules (written by the dashboard)          [runtime, not in git]
voyager_engine_state.json     what the engine did last cycle (dashboard reads it) [runtime, git-ignored]
voyager_dip_state.json        engine memory: shares it owns, pending buys    [runtime, git-ignored]
```

### 8.3 Safety guards (all tested)
- **Live orders need BOTH** `VOYAGER_ORDERS_ENABLED=1` **and** `IBKR_READONLY` unset. With `IBKR_READONLY` set the
  engine forces dry-run. There is no way to enable live orders from the dashboard.
- **A live cycle that can't read positions/open orders is skipped** (never run on empty data). Only the dashboard
  Preview may degrade to "prices and triggers only".
- **The engine only sells shares it bought itself** (`owned` in `voyager_dip_state.json`). Shares you already hold
  show "Holding - not managed" unless the rule's *manage existing shares* box is ticked.
- **No double-buy:** after a BUY is sent, the same stock is blocked for 30 min (or until the position appears).
- **Saving rules needs the PIN**; the starter list (15 stocks under $100) is added switched OFF.
- **Status honesty:** the badge comes from the engine's own state file, not the web server's env. Health =
  running / stale (silent > 2 cycles) / stopped (clean exit) / none.

### 8.4 Deployed setup (VPS `76.13.179.32`, `/opt/voyager`) and runbook
- Engine service: `voyager-engine` (from `deploy/voyager-engine.service`). Deliberately has **no `Wants=` on
  `voyager-gateway`** — starting the Gateway needs phone 2FA and kicks other sessions.
- Watch it: dashboard -> Dip Rules (status strip), or `tail -f /opt/voyager/logs/dip_engine.log`.
- Stop: `systemctl stop voyager-engine` (writes `running:false`). Start: `systemctl start voyager-engine`.
- If the Gateway is down the engine keeps running and shows "Last check was skipped: ..." — that is expected.
- **Go-live checklist (do NOT do casually):** (1) real money — decide this is worth it, see 8.5; (2) Gateway login must be
  non-read-only (`ReadOnlyApi=no`); (3) unset `IBKR_READONLY`; (4) uncomment `Environment=VOYAGER_ORDERS_ENABLED=1`
  in the unit, `daemon-reload`, restart; (5) start with 1-2 rules and `$ per buy` you can lose.
- The VPS `.env` has a PIN set, so the PIN gate is active there. `voyager-web` gets `IBKR_READONLY=1` from the
  drop-in `voyager-web.service.d/gateway.conf`; the engine unit sets it too (remove that line to go live). The engine
  is dry-run on two counts: `VOYAGER_ORDERS_ENABLED` is unset AND `IBKR_READONLY=1`.

### 8.5 Backtest result — why Pass 2 (stop-loss/cooldown/OCA) was NOT built
Run 2026-09-21, 5 years daily bars (yfinance), the 15 starter stocks, engine's own rule, dip 5/10/15% x sell 8/15% x
stop none/5/10/15%. Equal-capital benchmark: buy-and-hold returned **+27.4%**.

| Round-trip cost per trade | Configs beating buy-and-hold (of 24) |
|---|---|
| 0% (perfect fills) | 6 |
| 0.3% (spread + slippage) | **0** |
| 2% (~$1 commission/side on a $100 buy — IBKR fee for this account NOT verified) | **0**, most negative |

- No-stop variants look 100% "win" only because 5-15 losing positions stay open (worst -79%, held 6-12 months).
- Stops trigger constantly (up to 591 of 1,046 trades), win rate 28-45%, average trade +0.2-0.7% — costs erase it.
- Results are noisy (neighbouring settings swing widely; a 5-day cooldown changed one result 8.5% -> 3.3%).
- Biases that flatter the strategy: survivorship (today's names), mostly-bull window, close-price entries,
  stops filled exactly at the stop price (no gap-through). No commissions unless the cost column says so.
- **Conclusion: no demonstrated edge. Consistent with the small-cap finding (`strategies/BACKTEST_FINDINGS.md`).** Keep the engine
  as an observation tool in dry-run. Re-open Pass 2 only with a new idea and a fresh backtest.

### 8.6 Known gaps
- Never run against a real Gateway from this code path yet (`voyager-gateway` was inactive at deploy time and is left for the user to start with 2FA; verified locally with fakes/mocks and a browser).
- Whole shares only: at $100/buy, stocks above ~$100 can never fire (the card warns).
- Quotes may be delayed depending on market-data subscriptions (not verified for this account).
- `Documentation/VOYAGER_STATUS.html` was not regenerated from this file.

## 9. Spike shadow test — log-only (added 2026-10-31)

Tests whether "catch same-day +30/50/100% micro-cap spikes" has any edge, **without trading**. Frozen rules, verdict
logic and limits: `Documentation/SPIKE_TEST_RULES.md`. Files: `research/spike_logger.py`, `research/spike_scorer.py`,
`tests/test_spike.py`, `deploy/voyager-spike-logger.service`.
- Runs on the existing Gateway (port 4001, clientId 11, `readonly=True` — it cannot send an order).
- **Data gate:** logs events only when SPY's quote type is real-time; otherwise `gate_fail` rows. This account was
  believed to have delayed data only (`brokers/ibkr_broker.py` `get_quote`) — the 3-week clock starts only once that is fixed.
- Output `spike_log.csv` (git-ignored). Score: `python -m research.spike_scorer spike_log.csv`.
- Stop: `systemctl stop voyager-spike-logger`. Log: `/opt/voyager/logs/spike_logger.log`.
- Not yet built: gap-down-reversion re-check (its "passed testing" backtest was not found in the repo).

### 9.1 Update 2026-11-02 — Gateway fixed, alert added
- Gateway had been stuck on "Unrecognized Username or Password" since 2026-10-27; password in `/opt/voyager-ibc/config.ini`
  was updated by the user (helper `/root/set_ibc_pw.py`), Gateway restarted once, phone 2FA approved, port 4001 open, logger connected.
- **Data gate still unverified:** IBKR error 10089 on the SPY probe. Account subscriptions: only "US Real-Time Non Consolidated
  Streaming Quotes" (no NYSE/NASDAQ/Arca consolidated). The real answer is the first `gate_fail` / event rows after 17:00 MYT.
- **Finding 2026-11-02 22:47 MYT (logger NOT collecting):** scanner rejected (IBKR error 162, `STK.US.MAJOR`), so no stocks are
  watched; and the data gate false-passes because `ib_insync` `Ticker.marketDataType` defaults to 1 when SPY's request fails
  (error 10089). No `gate_fail` rows and no events since the 05:35 UTC `up` row. 3-week clock NOT started. Fix pending: gate must
  require a real SPY tick; try other scanner locations; add a "nothing logged for 2 h in session" alert.
- **Fixed 2026-11-02 22:52 MYT (deployed, verified live):** (1) gate = type 1 AND a valid SPY last (`is_realtime(mdt, last)`),
  resubscribes SPY every 5 min while failing; (2) scanner is now a 30 s snapshot (`reqScannerData`) — a probe showed
  `STK.US.MAJOR` and 5 other locations all return rows, the old long-lived subscription had died on an IBKR reconnect (1100/1102);
  (3) logger writes an `hb` row every 10 min (scorer ignores it); (4) `gateway_watch.py` alerts if no non-`down` row for 30+ min
  in session (once/day). Live result: `gate_fail` rows now written, Telegram "data gate FAILED" alert received at 09:55 ET.
  **Probe facts:** SPY real-time (type 1) returns no price on this account (error 10089); delayed (type 3) returns last/close
  only, bid = NaN. So the test cannot run on the current subscriptions: needs US Level 1 (NYSE/Arca/NASDAQ) or parking the test.
  Backups on VPS: `research/spike_logger.py.bak-2026-11-02`, `deploy/gateway_watch.py.bak-2026-11-02`.
- **PARKED 2026-11-02 ~23:00 MYT (user decision):** no real-time US data on this account. `voyager-spike-logger` stopped and
  disabled; `/opt/voyager/logs/spike_parked` mutes the silent-logger alert (gate alert stops by itself). Gateway, dip engine,
  dashboard and the Gateway-down alert are unchanged. **To resume:** buy US Level 1 feeds (NYSE, NASDAQ, NYSE American/Arca,
  non-professional) in the IBKR portal, restart `voyager-gateway` (phone 2FA), then
  `rm /opt/voyager/logs/spike_parked && systemctl enable --now voyager-spike-logger`; the 3-week clock starts at the first day
  with no `gate_fail` rows.
- **RESUMED 2026-11-02 ~23:38 MYT:** user subscribed to NASDAQ (Network C), NYSE (Network A) and Network B L1 (non-pro,
  3 × $1.50/month, charged at activation; review/unsubscribe if the test shows no edge). Gateway restarted (phone 2FA),
  probe: SPY type 1 with real last/bid/ask; all 6 scanner locations return rows. Parked flags removed, `voyager-spike-logger`
  enabled and started; verified live: ticks with `mdtype=1` and real bid/ask, `event` rows, heartbeat, watcher `ok`.
  **Day 1 of the 3 weeks = 2026-11-03** (today has `gate_fail` rows and the logger started mid-session at 10:36 ET, so today's
  events are stale entries: score with `grep -v '^2026-11-02' spike_log.csv > scored.csv` first). Harmless log noise: IBKR
  error 162 "scanner subscription cancelled" every 30 s (just the snapshot closing).
- **Gateway deliberately stopped 2026-11-02 ~23:05 MYT** (now restored, see above) (user needed the single live IBKR session for the website/app).
  `/opt/voyager/logs/gateway_parked` mutes every `gateway_watch.py` alert. **Restore:**
  `rm /opt/voyager/logs/gateway_parked && systemctl start voyager-gateway`, then approve the phone 2FA (close web/app first).
  Dashboard and dip engine show no live data while it is stopped.
- **Telegram alert (live):** `deploy/gateway_watch.py` (+ `tests/test_gateway_watch.py`, 4 pass), cron `*/5` on the VPS, log
  `/opt/voyager/logs/gateway_watch.log`. Alerts only in the US session: Gateway down (repeat 2 h, "back up" on recovery) and
  data-gate failure (once/day). Bot @alerts_ibkr_bot; token+chat id in `/opt/voyager/alert.env` (chmod 600), written by
  `deploy/setup_alert.py` (hidden prompt; token never passes through chat). Root crontab backup: `/root/crontab.bak-2026-11-02`.
  **Added 2026-11-03 (DEPLOYED to VPS 2026-11-03, backup `deploy/gateway_watch.py.bak-2026-11-03`; first run `ok`, skip counter 0):** `engine_skips()` reads `voyager_engine_state.json` and alerts
  once at 8 failed dip-engine cycles in a row (~2 h), at any hour, plus one "running again" message. Quiet if the engine is stopped.
  Tests: 7 pass. Engine code untouched. Known limit: counts cycles the watcher sees (it runs every 5 min, engine every 15), so none missed.
- Cleanup done 2026-11-02: `/root/set_ibc_pw.py` and `/opt/voyager-ibc/config.ini.bak-2026-11-02` (old password) deleted. Still on the VPS, harmless: `*.py.bak-2026-11-02` code backups and `/root/crontab.bak-2026-11-02` (root-only, contains a cron secret).
- **Daily scorecard (live 2026-11-02):** `deploy/daily_summary.py` (+ `tests/test_daily_summary.py`), VPS cron `10 21 * * 1-5` (21:10 UTC = 16:10 ET while US is on standard time; **change to `10 20` when US daylight time starts, mid-March 2027**), log `/opt/voyager/logs/daily_summary.log`. Telegram message after each session: heartbeats x/71, gate_fail, down, events, ticks; "FULL DAY captured" if heartbeats >= 60 and no gate_fail, else "GAPS". Crontab backup: `/root/crontab.bak2-2026-11-02`.
- A one-time review is scheduled in the Claude app for 2026-11-23 09:00 MYT (verdict + decide whether to keep paying USD 4.50/month for the three US data feeds).
- **Progress dashboard (2026-11-02):** private Claude artifact "Voyager daily progress" https://claude.ai/artifact/B3VnY7PPEYEyPYQpy1zqtK. Data = `Documentation/voyager_progress.json` (one row per session, added by hand from the Telegram scorecard) and `Documentation/voyager_milestones.json`; re-upload both after editing. Not auto-updated yet.

### 9.2 Update 2026-11-03 — pre-Day-1 scorer and logger amendment (committed 0810fa4, DEPLOYED 2026-11-02 23:00 UTC)
- Full text and reasons: `Documentation/SPIKE_TEST_RULES.md`, "Amendment 2026-11-03". Short version: no trade is ever dropped (unresolved = counted), verdict must pass realized AND with unresolved at -50%, extra metrics (mean, total P&L, profit factor, worst-5%, premarket/regular), one 15% trailing-stop challenger (report only), `bid_size`/`ask_size` columns, scorecard shows `lines X/90` (was /40 until 2026-11-03).
- Files changed: `research/spike_scorer.py`, `research/spike_logger.py`, `deploy/daily_summary.py`, `tests/test_spike.py`, `tests/test_daily_summary.py`. Spike + scorecard + gateway tests pass (35). Whole-suite failures are the same 103 as before the change (old live-broker scripts), none in spike code.
- **Deployed 2026-11-02 23:00 UTC (18:00 ET, after the Nov 2 close):** three files installed on the VPS (backups `*.bak-2026-11-03` beside each), `voyager-spike-logger` restarted (Gateway untouched, no 2FA). The old log was set aside intact as `/opt/voyager/spike_log.csv.pre-20261102T180013` (3 MB, Nov 2, excluded from scoring); the new `spike_log.csv` starts with the 14-column header and an `up` row. Verified: files match staged hashes; logger + Gateway active; new scorer and scorecard run on the real Nov 2 file (scorecard text printed, not sent); crons unchanged. **Not yet verified (markets closed):** that `bid_size`/`ask_size` fill with real values. Check after 04:00 ET Nov 3 (17:00 MYT): `tail spike_log.csv` should show numbers in the last two columns.
- **FINDING (Nov 2 data, scorecard now shows it): `lines 40/40 - CAP HIT`.** The 40-line cap was full during the partial Nov 2 session, so new spikes were unseen. Cause: flagged stocks keep their line all day. **DECIDED 2026-11-03: `MAX_LINES` 40 -> 90 in `research/spike_logger.py` (local edit; must be deployed to the VPS and the logger restarted before Day 1).** IBKR's real limit for this account is still unverified (default ~100; SPY probe and dip engine also use lines), so watch for refused-line errors and the `lines X/90` scorecard figure.
- Nov 2 partial-day dry run, +30% trigger, 5% slippage (14 stocks, one partial day, **not evidence**): median -15.5%, 15% trailing challenger -19.5%. Also `down 70` rows that day (about 35 min of reconnect attempts while the Gateway was being fixed).
- **Day 1 morning check (2026-11-03 07:46 ET, read-only):** 3 services active, port 4001 listening, `gate_fail` 0, 23 heartbeats / 8 events / 11,356 ticks so far, no ticker-limit / error 101 / market-data lines since midnight (only those 3 phrases searched). Latest heartbeat `scan=50 lines=50`: 50 is the scanner `numberOfRows` (`spike_logger.py:88`); `MAX_LINES=90` (line 21, enforced at line 119) only bites once flagged names accumulate past 50, so 90 is untested until the session fills. Logger restarted 01:48 UTC, Gateway started 01:49 UTC, 0 restarts. **2FA:** IBC log shows "Second Factor Authentication initiated" 01:49:32 and the dialog closed 01:49:51 (~19 s), login completed 01:49:57, so a phone approval was needed (or accepted instantly) at that start. Still unverified: `bid_size`/`ask_size` values (first event row shows 1100/400, so they do fill).
- **Checked 2026-11-04 02:14 UTC (after Day 1):** (1) `MAX_LINES` was already raised 40 -> 90 before Day 1 (commit 120530b, deployed); Day 1 peaked at 64/90 lines and no IBKR ticker-limit errors, so the cap did not censor Day 1. A request to "raise to 80" was NOT applied (it would have lowered 90). (2) `bid_size`/`ask_size` are filled on all 128,320 Day 1 ticks. (3) Day 1 scorecard: FULL DAY, 72/71 heartbeats, gate_fail 0, 53 events on 35 stocks.
- **OPEN RISK: the Gateway shuts itself down every day at 23:45 UTC (18:45 ET).** IBC log: "Exit Session Setting" (IB auto-logoff) at 23:40, clean exit status 0 at 23:45:05, so systemd (`Restart=on-failure`) does not restart it, and `AutoRestartTime=` is blank. Day 1 worked only because it was restarted at 01:49 UTC. Without a restart + phone 2FA before 09:00 UTC (17:00 MYT) the logger gets no data on Day 2, and every day after. Fix options: start it by hand each day, or set IBC `AutoRestartTime` so it restarts itself (behaviour with 2FA not verified). Not changed.
- **Day 2 (2026-11-04) gap, handled 09:59 UTC:** the Gateway stayed off after the 23:45 UTC auto-logoff, so the logger saw nothing from 04:00 to 04:59 ET (598 `down` rows). The Telegram "Gateway DOWN" alerts DID fire (18:45 ET Nov 3 and 04:00 ET Nov 4); the Gateway was started by hand at 09:59:04 UTC (04:59 ET), port 4001 open in 60 s, logger reconnected 04:59:09, SPY real-time 759.62, ticks with sizes flowing. **Effect on scoring:** events logged right after the reconnect (e.g. DKI, CRIS, already +64% / +85%) are stale entries at a later, higher ask; the scorecard will still say FULL DAY (about 65 heartbeats, threshold 60). Recommended rule, same logic as Nov 2 (NOT yet applied, needs Bharat's OK): drop Day 2 events whose timestamp is within 60 s after the 04:59:09 `up` row, and note Day 2 as a partial premarket day.
- **Day 2 second gap (10:38-10:40 UTC = 05:38-05:40 ET):** the config rollback restarted the Gateway mid-session; phone 2FA approved, port 4001 open 10:40:32 UTC, logger reconnected and ticks flowing (verified). The reconnect re-fired stale events (e.g. DKI +47% at 05:40:55). **Day 2 scoring rule to apply (pending Bharat's OK):** drop events written within 60 s after ANY `up` row on 2026-11-04 (04:59:09 ET and the ~05:40 ET reconnect); Day 2 is a partial premarket day.
- **Gateway auto-restart attempt (2026-11-04) - REVERTED, NOT in effect:** Bharat set `AutoRestartTime=11:30 PM` in `/opt/voyager-ibc/config.ini` at 10:36 UTC (the running Gateway had started at 09:58 and never loaded it). At 10:38:12 UTC `config.ini` was replaced by the original (489 B, `AutoRestartTime=` blank; consistent with the documented rollback `cp -p` of the backup) and `voyager-gateway` restarted at the same second, so it was DOWN mid-session waiting for the phone 2FA. The backup `config.ini.bak-2026-11-04` (password copy) was then deleted. Current state: blank setting, no backup. To retry: set the line again with `sed -i 's/^AutoRestartTime=.*/AutoRestartTime=11:30 PM/' /opt/voyager-ibc/config.ini` and restart the Gateway after the US close; test = Gateway still active and port 4001 open at 23:50 UTC with no phone prompt. Fallback: cron `30 8 * * 1-5 systemctl is-active --quiet voyager-gateway || systemctl start voyager-gateway`.
- **Tonight (2026-11-04) the 23:45 UTC logoff still happens;** Day 3 needs the manual start before 09:00 UTC (17:00 MYT) on 2026-11-05.
- (older note) the daily 23:45 UTC Gateway logoff will repeat tonight (Day 3 will have the same gap unless restarted before 09:00 UTC, or `AutoRestartTime` is set in `/opt/voyager-ibc/config.ini`).**
- Not built: auto-updating dashboard and a per-trade table (the scorer can now produce the numbers, but nothing exports them yet).
- **PARKED 2026-11-04 (day-trader-skill, 11 skills):** not added to the live test. Verdicts from README only, code not read. Only idea kept: a one-off **news vs no-news split of the spikes**, run in `C:\Antigravity\sandbox\` on a COPY of `spike_log.csv` (read-only, no broker, no VPS), **after Day 10 and only if the main verdict is still negative**. Write the question down first ("do news spikes lose less?"), one question only, result is a hint for a separate dry run, never a verdict. Skip trader-broker (Alpaca, real money). Day 1 alone (35 stocks) is too small to split.

## 10. If something breaks - how to revive (added 2026-11-03)

Each service restarts itself after a crash (`Restart=on-failure`). The one thing that cannot self-heal is the **Gateway
login (needs your phone 2FA)**. Telegram tells you: during the US session every 2 h while it is down, and (added 2026-11-03,
deployed) once per outage on any weekday after hours too, because the Gateway exited at 18:45 ET on 2026-11-02 and no alert
fired. Weekends and the `gateway_parked` flag stay quiet. The Gateway's exit cause (fixed clock vs ~8 h after start) and whether
each restart needs phone 2FA are still being measured (checks scheduled 2026-11-03 17:10 and 23:10 MYT).

**How code reaches the VPS (decided 2026-11-03): by hand, never `git pull`.** `/opt/voyager` is a clone stuck at `189baab` with
copied-in files on top, on purpose. The Voyager branch contains a merge of `main` (desktop-tool code: `backend/`, `zepp-*.service`,
`brokers/factory.py` changes, `.encryption_key_new_test`, ...) that must not land on the shared VPS. Deploy = back up the old file
(`cp x x.bak-DATE`), `scp` the file, restart the one affected service, then run `bash deploy/verify_sync.sh` from the repo root
(hashes the 11 files Voyager actually runs/tests, ignoring CRLF; exit 0 = VPS matches the committed branch). Known, accepted
differences: VPS `brokers/factory.py` is the older version (works; the newer one needs `ibkr_stub.py`, not deployed); the engine's
client ID 12 comes from the systemd drop-in `/etc/systemd/system/voyager-engine.service.d/clientid.conf`, not the repo unit;
`*.bak-*` files and `alert.env`/`spike_log.csv` live only on the VPS. VPS tests (46) pass with `SPIKE_LOG`/`ALERT_STATE` pointed
at /tmp so they cannot touch the live log.

| Symptom | Fix (on the VPS: `ssh root@76.13.179.32`) |
|---|---|
| Telegram "Gateway is DOWN" | `systemctl restart voyager-gateway`, approve IBKR phone 2FA, close the IBKR website/app first (one live login only). Port 4001 opens when it works: `ss -ltn \| grep 4001` |
| Logger silent / "GAPS" scorecard | `systemctl restart voyager-spike-logger`. Missed minutes are not recoverable; a day with 60+ of 71 heartbeats still counts |
| Engine shows "skipped" | Almost always the Gateway is down. Fix the Gateway; the engine resumes by itself next cycle |
| Wrong password (stuck since 27 Oct) | edit `/opt/voyager-ibc/config.ini`, restart Gateway, approve 2FA |

Health in one line: `systemctl is-active voyager-gateway voyager-engine voyager-spike-logger voyager-web` (all four = active).
**clientIds must differ:** dashboard 9, spike logger 11, engine 12 (set by `VOYAGER_CLIENT_ID=12`; before 2026-11-03 the engine
also used 11 and fought the logger for the connection). VPS venv also needs `pip install tzdata` (ib_insync reads `US/Eastern`).

**Backup of `spike_log.csv` (added 2026-11-03, VPS-only, not in git):** `/opt/voyager/backup_spike_log.sh` gzips it into
`/opt/voyager/backups/` (30-day cleanup, only its own files). Cron `30 21 * * 1-5` (after the 21:10 scorecard), log
`/opt/voyager/logs/backup_spike_log.log`. Crontab backup: `/root/crontab.bak3-2026-11-03`. The TradingBot sqlite backup timer
(`deploy/backup_db.sh`) was never installed on this VPS. Same disk as the original, so it does not survive a dead disk: copy the
file to the laptop now and then. Pre-Nov-3 log is also in `backups/` as `spike_log.pre-20261102.csv.gz`.

- **Morning Gateway start (added 2026-11-05):** `deploy/morning_start.sh`, VPS cron `0 8 * * 1-5` (08:00 UTC = 16:00 MYT). If port 4001 is closed and `logs/gateway_parked` is absent it runs `systemctl start voyager-gateway` (triggers the 2FA push) and sends a Telegram. Log `logs/morning_start.log`; `DRY=1` = test message only. Dry run OK (Telegram 200, Gateway untouched). Starting it logs out your IBKR web/app session; it also fires on US holidays. Crontab backup `/root/crontab.bak4-2026-11-05`. Remove = delete the cron line. First real run: 2026-11-05 08:00 UTC.

## 11. Next-day follow-up test (added 2026-11-11, log-only)
"After a spike, does buying near the close and selling 1-3 days later pay, net of costs?" Frozen rules: `Documentation/NEXTDAY_TEST_RULES.md`.
Code `research/spike_nextday.py` (reuses `spike_scorer` maths) + `tests/test_spike_nextday.py` (4 pass). Reads the existing `spike_log.csv`
events, daily bars from yfinance. Nothing runs on the VPS and nothing is ordered. Three variants fixed in advance (ALL, HOLD, STRONG),
verdict at T+1 with 5% slippage. Smoke-tested 2026-11-11 on 233 stock-days (plumbing only; results deliberately not read before the
frozen first run). First scoring: scheduled once for 2026-11-24 09:00 MYT (Claude scheduled task `nextday-test-first-scoring`; first attempt was refused, the retry on 2026-11-11 worked). Run by hand:
`scp` the log, keep header + event rows, `python -m research.spike_nextday ev.csv`.
