"""Buy-the-dip / sell-at-% rules for Voyager (IBKR). Rules live in voyager_rules.json, edited from the dashboard.

Per enabled rule:
  no position, no resting BUY, price <= recent_high * (1 - dip_pct%)  -> BUY usd/price shares (whole shares)
  position held, no resting SELL                                       -> GTC LIMIT SELL at avg_cost * (1 + sell_pct%)
Orders are only SENT when env VOYAGER_ORDERS_ENABLED=1 (file/env only, never from the UI) AND IBKR_READONLY is unset.
Otherwise dry-run. A live cycle that cannot read positions/open orders is skipped, never run on empty data.
The engine only sells shares it bought itself (tracked in voyager_dip_state.json) unless a rule sets manage_existing.
Each cycle it writes voyager_engine_state.json so the dashboard can show what it is doing.

Run the loop:  python -m brokers.dip_engine   (every VOYAGER_INTERVAL_MIN minutes, default 15)
"""
from __future__ import annotations

import json
import math
import os
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(_ROOT, "voyager_rules.json")
STATE_PATH = os.path.join(_ROOT, "voyager_engine_state.json")      # what the engine is doing (dashboard reads it)
DIP_STATE_PATH = os.path.join(_ROOT, "voyager_dip_state.json")     # engine memory: owned / pending buys
MAX_RULES = 25
PENDING_BUY_SECS = 30 * 60
_DEFAULTS = {"dip_pct": 10.0, "sell_pct": 15.0, "usd": 100.0, "lookback_days": 20, "enabled": True,
             "manage_existing": False}
_BOOLS = ("enabled", "manage_existing")


def clean_rules(raw) -> list[dict]:
    """Validate a list of rules from the UI/file. Raises ValueError with a readable message."""
    if not isinstance(raw, list) or not 0 <= len(raw) <= MAX_RULES:
        raise ValueError(f"need a list of at most {MAX_RULES} rules")
    out, seen = [], set()
    for r in raw:
        sym = str(r.get("symbol", "")).strip().upper()
        if not sym.replace(".", "").replace("-", "").isalnum():
            raise ValueError(f"bad symbol: {sym!r}")
        if sym in seen:
            raise ValueError(f"duplicate symbol: {sym}")
        seen.add(sym)
        rule = {"symbol": sym}
        for k, dflt in _DEFAULTS.items():
            v = r.get(k, dflt)
            if k in _BOOLS:
                rule[k] = bool(v)
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"{sym}: {k} must be a number")
            if not (0 < v <= (100 if k.endswith("_pct") else 1e6 if k == "usd" else 365)):
                raise ValueError(f"{sym}: {k} out of range")
            rule[k] = int(v) if k == "lookback_days" else v
        out.append(rule)
    return out


def load_rules(path: str = RULES_PATH) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            return clean_rules(json.load(f))
    except FileNotFoundError:
        return []


def save_rules(rules: list[dict], path: str = RULES_PATH) -> list[dict]:
    rules = clean_rules(rules)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
    os.replace(tmp, path)
    return rules


def _write_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None


def readonly() -> bool:
    return os.environ.get("IBKR_READONLY", "").lower() in ("1", "true", "yes")


def write_state(mode: str, rows: list[dict], interval_min: float, running: bool = True,
                error: str | None = None, now: float | None = None, path: str = STATE_PATH) -> None:
    _write_json(path, {"mode": mode, "ts": time.time() if now is None else now, "interval_min": interval_min,
                       "running": running, "error": error, "rows": rows})


def read_state(path: str = STATE_PATH) -> dict | None:
    return _read_json(path)


def engine_health(state: dict | None, now: float | None = None) -> str:
    """'none' (never ran) | 'stopped' (clean exit) | 'stale' (silent for > 2 cycles) | 'running'."""
    if not state:
        return "none"
    if not state.get("running"):
        return "stopped"
    now = time.time() if now is None else now
    return "stale" if now - state["ts"] > 2 * state["interval_min"] * 60 + 120 else "running"


def load_dip_state(path: str = DIP_STATE_PATH) -> dict:
    s = _read_json(path) or {}
    return {"owned": dict(s.get("owned", {})), "pending_buy": dict(s.get("pending_buy", {})),
            "prev_held": list(s.get("prev_held", []))}


def next_dip_state(state: dict, rows: list[dict], now: float) -> dict:
    """Pure. owned = symbols the engine bought and still holds (or is waiting to fill); pending_buy = BUYs
    sent in the last PENDING_BUY_SECS that haven't shown up as a position yet."""
    held_now = {r["symbol"] for r in rows if r.get("held_qty", 0) > 0}
    sent = {r["symbol"] for r in rows if r.get("sent") and r["action"]["side"] == "BUY"}
    pending = {s: t for s, t in state["pending_buy"].items() if now - t < PENDING_BUY_SECS and s not in held_now}
    pending.update({s: now for s in sent})
    owned = {s: t for s, t in {**state["owned"], **{s: now for s in sent}}.items() if s in held_now or s in pending}
    return {"owned": owned, "pending_buy": pending, "prev_held": sorted(held_now)}


def decide(rule: dict, price: float | None, ref_high: float | None, held: dict | None, resting: set[str]) -> dict | None:
    """Pure: return {'side','qty','price'|None,'why'} or None. held = {'qty','avg_cost'} or None."""
    if not rule["enabled"]:
        return None
    qty = held["qty"] if held else 0
    if qty > 0:
        if "SELL" in resting:
            return None
        target = round(held["avg_cost"] * (1 + rule["sell_pct"] / 100), 2)
        return {"side": "SELL", "qty": int(qty), "price": target, "why": f"target +{rule['sell_pct']}% of cost"}
    if "BUY" in resting or not price or not ref_high:
        return None
    trigger = ref_high * (1 - rule["dip_pct"] / 100)
    shares = math.floor(rule["usd"] / price)
    if price <= trigger and shares >= 1:
        return {"side": "BUY", "qty": shares, "price": None,
                "why": f"price {price:.2f} <= {trigger:.2f} ({rule['dip_pct']}% below {rule['lookback_days']}d high {ref_high:.2f})"}
    return None


def _fetch_account(broker, preview: bool) -> tuple[dict, dict, bool]:
    """(held, resting, ok). Only Preview may degrade to empty; a live cycle must not run on missing data."""
    try:
        return broker.get_portfolio(), broker.get_open_orders(), True
    except Exception:
        if not preview:
            raise
        return {}, {}, False


def run_once(broker, rules: list[dict] | None = None, live: bool = False, state: dict | None = None,
             preview: bool = False, now: float | None = None) -> list[dict]:
    """Evaluate every rule; send orders only if live. Returns one result row per rule.
    Raises if positions/open orders can't be read (unless preview) so the caller skips the cycle."""
    rules = load_rules() if rules is None else rules
    state = state or {"owned": {}, "pending_buy": {}, "prev_held": []}
    now = time.time() if now is None else now
    held, resting, ok = _fetch_account(broker, preview)
    rows = []
    for rule in rules:
        sym = rule["symbol"]
        pos = held.get(sym)
        qty = pos["qty"] if pos else 0
        sides = resting.get(sym, set())
        row = {"symbol": sym, "enabled": rule["enabled"], "stage": "watching", "action": None, "sent": False,
               "note": "", "held_qty": qty, "avg_cost": pos.get("avg_cost") if pos else None,
               "resting": sorted(sides), "account_ok": ok}
        try:
            q = broker.get_quote(sym) or {}
            price = q.get("last_price") or q.get("ask")
            high = broker.get_reference_high(sym, rule["lookback_days"])
            row.update(price=price, ref_high=high)
            if not rule["enabled"]:
                row["stage"] = "off"
            elif qty > 0 and sym not in state["owned"] and not rule["manage_existing"]:
                row.update(stage="unmanaged", note="you already hold shares the engine didn't buy - left alone")
            elif qty == 0 and now - state["pending_buy"].get(sym, 0) < PENDING_BUY_SECS:
                row.update(stage="pending", note="buy sent - waiting for it to fill")
            else:
                act = decide(rule, price, high, pos, sides)
                row["action"] = act
                if act and live:
                    broker.place_order(sym, "SMART", act["qty"], act["side"], price=act["price"] or 0,
                                       tif="GTC" if act["side"] == "SELL" else "DAY")
                    row["sent"] = True
                row["stage"] = "holding" if qty > 0 else "armed" if act else "pending" if "BUY" in sides else "watching"
        except Exception as e:  # one bad symbol must not stop the rest
            row.update(stage="error", note=f"error: {e}")
        rows.append(row)
    return rows


def orders_enabled() -> bool:
    return os.environ.get("VOYAGER_ORDERS_ENABLED", "") == "1"


def _demo():
    r = {"symbol": "X", "dip_pct": 10, "sell_pct": 15, "usd": 100, "lookback_days": 20, "enabled": True}
    assert decide(r, 89, 100, None, set())["side"] == "BUY"
    assert decide(r, 95, 100, None, set()) is None
    assert decide(r, 89, 100, None, {"BUY"}) is None
    assert decide(r, 500, 600, None, set()) is None  # $100 can't buy a whole share
    s = decide(r, 50, 100, {"qty": 3, "avg_cost": 20}, set())
    assert (s["side"], s["qty"], s["price"]) == ("SELL", 3, 23.0)
    assert decide(r, 50, 100, {"qty": 3, "avg_cost": 20}, {"SELL"}) is None
    assert decide({**r, "enabled": False}, 89, 100, None, set()) is None
    assert clean_rules([{"symbol": "aapl"}])[0]["symbol"] == "AAPL"
    for bad in ([{"symbol": "A B"}], [{"symbol": "A"}, {"symbol": "A"}], [{"symbol": "A", "dip_pct": 0}]):
        try:
            clean_rules(bad)
            raise SystemExit("should have failed")
        except ValueError:
            pass
    print("ok")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        _demo()
        raise SystemExit
    import signal
    from brokers.ibkr_broker import IBKRBroker
    interval = float(os.environ.get("VOYAGER_INTERVAL_MIN", "15"))
    live = orders_enabled() and not readonly()
    if orders_enabled() and readonly():
        print("IBKR_READONLY is set - forcing DRY RUN (the Gateway would reject orders anyway)")
    mode = "live" if live else "dry-run"
    print("LIVE - orders will be sent" if live else "DRY RUN - set VOYAGER_ORDERS_ENABLED=1 to send orders")

    def _term(*_):
        raise SystemExit

    signal.signal(signal.SIGTERM, _term)  # systemd stop -> clean exit, state file says running:false
    write_state(mode, [], interval)
    last_rows: list[dict] = []
    try:
        while True:
            error = None
            b = IBKRBroker(client_id=int(os.environ.get("VOYAGER_CLIENT_ID", "11")))
            try:
                b.connect()
                st = load_dip_state()
                rows = run_once(b, live=live, state=st)
                for r in rows:
                    print(time.strftime("%H:%M:%S"), r)
                last_rows = rows
                if live:
                    _write_json(DIP_STATE_PATH, next_dip_state(st, rows, time.time()))
            except Exception as e:
                error = str(e)
                print("cycle failed (skipped):", e)
            finally:
                b.disconnect()
            write_state(mode, last_rows, interval, error=error)
            time.sleep(interval * 60)
    except (KeyboardInterrupt, SystemExit):
        write_state(mode, last_rows, interval, running=False)
