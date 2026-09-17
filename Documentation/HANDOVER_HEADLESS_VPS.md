# Handover — ARUN Titan (mStock) headless + VPS

**Scope note:** this doc covers the mStock engine's VPS/headless migration only. The
IBKR (US markets) work — broker abstraction, live order validation, the web dashboard —
grew into its own thing and is tracked separately in
[VOYAGER_STATUS.md](VOYAGER_STATUS.md). Read that one for anything IBKR-related.

**Status:** verified against code on 2026-09-17. Read this before touching anything.
**Live code.** The bot trades real money. `settings.json:77` = `"paper_trading_mode": false`.
Do not run `python kickstart.py` unattended without flipping that flag.

---

## 1. What the code actually is (corrects the previous plan)

| Previous plan said | Actual (verified) |
|---|---|
| "Zerodha bot" | **mStock** — `kickstart.py` calls `api.mstock.trade` inline everywhere |
| "no headless mode exists" | Headless entry already exists: `kickstart.py:2404 main_loop()` → `run_cycle()` loop, launched by `:2431 if __name__ == "__main__": main_loop()`. No tkinter import anywhere in `kickstart.py`. |
| "introduce a flag file" | Persisted stop flag already exists: `state_manager.py:354 set_stop_requested()` / `:362 is_stop_requested()`; the live `run_cycle` reads it at `:2255`. |
| "extract the engine (3–5 days)" | Already extracted. Only a thin wiring fix + one dead block to delete remain. |
| "IBKR slots in as a 3rd engine instance" | IBKR needs a broker-abstraction refactor (see Phase 4). Not a plugin. |

Broker note: both `TradingBot` and `Project Vayu` are forks of the same mStock bot
(shared verbatim code strings). **TradingBot is the live one.** Vayu is the fork that
already built web-control + systemd + IBKR — use it as a reference, not a second live bot.

---

## 2. Phase 2 result — dead vs live map of `kickstart.py` (756–2249)

Full function index confirmed. The answer is simpler than first thought:

**DEAD (safe to delete):**
- `run_cycle()` **#1 at lines 756–895** — one contiguous block.
  - Proof it's dead: shadowed by `run_cycle()` #2 at `:2252` (Python keeps the last
    module-level definition, so every caller resolves to #2).
  - Further proof: it calls `execute_order(...)` at `:870/:875/:887` — a function that
    **no longer exists** anywhere in the file. It is orphaned code from a prior version.

**NOT dead (do not touch):**
- `kickstart.py:1045–1050` — I previously flagged a "second `__main__` block" here. That
  was **wrong**. It is a nested, module-level **access-token gate**:
  ```
  if not ACCESS_TOKEN:
      if __name__ == "__main__":
          if not handle_token_exception_and_refresh_token():
              sys.exit(1)
      else:
          log_ok("...token missing...")
  ```
  It is LIVE and runs at import/run time. Do not remove it.
- `kickstart.py:338 STOP_REQUESTED = False` — redundant re-init of the `:11` global.
  Harmless; leave it (surgical-changes rule).
- Everything else in 756–2249 is **live** and referenced by `run_cycle` #2, `main_loop`,
  `dashboard_v2.py`, or `backend/`:
  - `perform_auto_login` (`:896`), `handle_token_exception_and_refresh_token` (`:984`)
  - positions: `get_positions` (`:1135`), `safe_get_positions` (`:1228`),
    `safe_get_live_positions_merged` (`:1422`) — imported by `dashboard_v2.py:18`
  - RSI: `get_stabilized_rsi` (`:1489`) and helpers
  - market hours: `is_market_open_now_ist` (`:1606`), `wait_for_market_open` (`:1630`)
  - strategy: `check_existing_orders` (`:1841`), `process_market_data` (`:1889`)
  - orders: `place_order` (`:2125`, contains nested `attempt_place_order` at `:2184`)

**Conclusion: the single deletion for Phase 2 is `kickstart.py:756–895`.**

---

## 3. Phase 0 result — headless entry point (verified statically, not executed)

- Entry point confirmed: `python kickstart.py` → `main_loop()` (`:2404`) → auto-login
  (`:2406 perform_auto_login`) → state load (`:2410`) → `while True: run_cycle()` (`:2423`).
- **Not executed here** because `paper_trading_mode: false` (live money) and mStock
  session credentials are required.

**Safe manual check (for a human, not an agent):**
1. Back up `settings.json`.
2. Set `"paper_trading_mode": true` (line 77).
3. Run `python kickstart.py`, watch `logs/` for `🕒 Scheduler started` and cycle output.
4. Confirm trades land in `database/trades.db` as paper, then **flip the flag back** and
   restore settings.

**Headless gotcha (deployment-critical):** the token gate at `:1045–1050` runs at module
load, *before* the TOTP auto-login at `:2406`. If `ACCESS_TOKEN` is missing/expired on a
fresh machine, `handle_token_exception_and_refresh_token()` hits `input("📩 Enter OTP...")`
at `:1017` — which **blocks a headless process** — or `sys.exit(1)` at `:1048`. A clean
headless start requires either a cached valid token in settings, or TOTP auto-login to
complete before the gate matters. Flag this before VPS first-run.

---

## 4. Final corrected plan

**Status update 2026-09-17: Phases 1 and 2 are done** (verified in code —
`backend/main.py` uses `state_mgr.is_stop_requested()`/`set_stop_requested()`,
and the dead `run_cycle` block at the old `:756-895` is deleted). Phase 3 is
scripted (`deploy/setup_ibgateway.sh`, `.service`, `ibc/config.ini.template`)
but not yet run on the real VPS. Phase 4 is untouched — deliberately, see below.

### Phase 1 — fix web control wiring (2 edits in `backend/main.py`)
The live engine reads `state_mgr.is_stop_requested()`, but the API writes `bot_status` to
the DB (read by the *dead* `run_cycle` #1 only). So `/api/control/*` is currently a no-op.

- `backend/main.py:83` — `/api/control/status`: replace
  `db.get_control_flag("bot_status", default="STOPPED")` with
  `state_mgr.is_stop_requested()` → return `"STOPPED"` / `"RUNNING"`.
- `backend/main.py:99` — `/api/control/set`: replace
  `db.set_control_flag("bot_status", new_status)` with
  `state_mgr.set_stop_requested(new_status == "STOPPED")`.
- Add imports to `main.py`:
  `from state_manager import state as state_mgr` (pattern confirmed at
  `state_manager.py:374`). Optionally also `import kickstart` to use
  `request_stop()` / `reset_stop_flag()` instead of the raw state call.

### Phase 2 — delete dead code (1 contiguous block)
Delete `kickstart.py:756–895` (the shadowed `run_cycle` #1). Verify nothing else
references `execute_order` first (it shouldn't — it's undefined). Surgical; no other lines.

### Phase 3 — VPS deploy (cherry-pick from Vayu)
Port `C:\Antigravity\Project Vayu\deploy\vayu-trading.service` (and `vayu-web.service`,
`nginx-vayu.conf`, `setup.sh`) to TradingBot paths. Core is:
`ExecStart=<venv>/bin/python kickstart.py`, `Restart=on-failure`, `RestartSec=30`.
That `Restart=on-failure` is the crash-safety the whole exercise is about.

### Phase 4 — IBKR (honest scope: a refactor, not a plugin)
Vayu's IBKR (`brokers/factory.py`, `interface.py`, `ibkr_api.py`, `ibkr_client_portal.py`,
`ibkr_stub.py`) only works because Vayu refactored `kickstart.py` behind
`get_broker("IN"/"US")`. TradingBot has inline mStock calls. So IBKR =
1. port Vayu's `brokers/`,
2. refactor `kickstart.py`'s quote/order paths behind `get_broker(...)`.

This touches order placement on live money. Sequence last; run paper-mode first.

---

## 5. Risks / do-not-do

- **Do not run `python kickstart.py` while `paper_trading_mode: false`.** Live orders.
- **Do not delete `:1045–1050`** (live token gate, misread earlier as a second `__main__`).
- **Do not touch `:338`** (redundant but harmless).
- The duplicate-control-flag problem is two flags: `bot_status` (DB, orphaned) vs
  `stop_requested` (state JSON, live). Phase 1 fixes this. Do not add a third flag file.
- `dashboard_v2.py` spawns the engine as a daemon thread from a GUI button
  (`dashboard_v2.py:1023`). That's the single-point-of-failure being retired — but
  `dashboard_v2.py` can remain the local monitor after Phase 1, reading the same state.
