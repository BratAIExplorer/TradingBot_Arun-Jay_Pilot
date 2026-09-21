"""Buy-the-dip / sell-at-% rules for Voyager (IBKR). Rules live in voyager_rules.json, edited from the dashboard.

Per enabled rule:
  no position, no resting BUY, price <= recent_high * (1 - dip_pct%)  -> BUY usd/price shares (whole shares)
  position held, no resting SELL                                       -> GTC LIMIT SELL at avg_cost * (1 + sell_pct%)
Orders are only SENT when env VOYAGER_ORDERS_ENABLED=1 (file/env only, never from the UI). Otherwise dry-run.

Run the loop:  python -m brokers.dip_engine   (every VOYAGER_INTERVAL_MIN minutes, default 15)
"""
from __future__ import annotations

import json
import math
import os
import time

RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voyager_rules.json")
MAX_RULES = 25
_DEFAULTS = {"dip_pct": 10.0, "sell_pct": 15.0, "usd": 100.0, "lookback_days": 20, "enabled": True}


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
            if k == "enabled":
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


def run_once(broker, rules: list[dict] | None = None, live: bool = False) -> list[dict]:
    """Evaluate every rule; send orders only if live. Returns one result row per rule."""
    rules = load_rules() if rules is None else rules
    held, resting = broker.get_portfolio(), broker.get_open_orders()
    rows = []
    for rule in rules:
        sym = rule["symbol"]
        row = {"symbol": sym, "action": None, "sent": False, "note": ""}
        try:
            q = broker.get_quote(sym) or {}
            price = q.get("last_price") or q.get("ask")
            high = broker.get_reference_high(sym, rule["lookback_days"])
            row.update(price=price, ref_high=high)
            act = decide(rule, price, high, held.get(sym), resting.get(sym, set()))
            row["action"] = act
            if act and live:
                broker.place_order(sym, "SMART", act["qty"], act["side"], price=act["price"] or 0,
                                   tif="GTC" if act["side"] == "SELL" else "DAY")
                row["sent"] = True
            elif not act:
                row["note"] = "waiting"
        except Exception as e:  # one bad symbol must not stop the rest
            row["note"] = f"error: {e}"
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
    from brokers.ibkr_broker import IBKRBroker
    live = orders_enabled()
    print("LIVE — orders will be sent" if live else "DRY RUN — set VOYAGER_ORDERS_ENABLED=1 to send orders")
    while True:
        b = IBKRBroker(client_id=int(os.environ.get("VOYAGER_CLIENT_ID", "11")))
        try:
            b.connect()
            for r in run_once(b, live=live):
                print(time.strftime("%H:%M:%S"), r)
        except Exception as e:
            print("cycle failed:", e)
        finally:
            b.disconnect()
        time.sleep(float(os.environ.get("VOYAGER_INTERVAL_MIN", "15")) * 60)
