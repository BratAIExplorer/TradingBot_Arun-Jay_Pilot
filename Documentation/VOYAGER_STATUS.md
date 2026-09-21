# Voyager — US Markets (IBKR) Status

**Last updated:** 2026-09-21
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
