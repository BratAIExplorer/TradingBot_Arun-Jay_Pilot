"""Offline scoring of spike_log.csv. Rules: Documentation/SPIKE_TEST_RULES.md  (python -m research.spike_scorer)."""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict

SLIPPAGE_CASES = (0.02, 0.05)      # per side; verdict uses the worst
STOP_PCT, NOTIONAL, COMMISSION = 0.10, 500.0, 1.0
MIN_STOCK_DAYS, MIN_DAYS, MAX_HALT_SHARE = 100, 10, 0.10


def simulate_trade(entry_ask: float, ticks: list[dict], *, slippage: float, stop_pct: float = STOP_PCT,
                   commission_usd: float = COMMISSION, notional: float = NOTIONAL) -> dict | None:
    """Buy at ask+slippage, then walk ticks: sell at the bid once bid <= stop, else at the last tick.
    Halted ticks cannot be sold into; a gap through the stop exits at the real (lower) bid."""
    if not ticks:
        return None
    fill = entry_ask * (1 + slippage)
    stop = fill * (1 - stop_pct)
    halt_trapped, exit_bid, how = False, None, "forced"
    for t in ticks:
        if t["halted"]:
            halt_trapped = True
            continue
        if t["bid"] <= stop:
            exit_bid, how = t["bid"], "stop"
            break
        exit_bid = t["bid"]
    if exit_bid is None:                       # halted the whole time: nothing to sell into
        return None
    gross = exit_bid * (1 - slippage) / fill - 1
    return {"net_pct": gross * 100 - 2 * commission_usd / notional * 100, "exit": how,
            "gap_through": how == "stop" and exit_bid < stop * 0.99, "halt_trapped": halt_trapped}


def summarize(trades: list[dict]) -> dict:
    nets = sorted(t["net_pct"] for t in trades)
    ex_top2 = nets[:-2]
    return {"n": len(nets), "median": statistics.median(nets) if nets else None,
            "median_ex_top2": statistics.median(ex_top2) if ex_top2 else None,
            "stock_days": len({(t["day"], t["symbol"]) for t in trades}), "days": len({t["day"] for t in trades}),
            "halt_share": sum(t["halt_trapped"] for t in trades) / len(trades) if trades else 0}


def verdict(low_slip: dict, worst_slip: dict) -> str:
    """Passing only ever means 'continue paper' -- never 'go live'."""
    if worst_slip["stock_days"] < MIN_STOCK_DAYS or worst_slip["days"] < MIN_DAYS:
        return "no conclusion"
    ok = (worst_slip["median"] > 0 and worst_slip["median_ex_top2"] > 0 and worst_slip["halt_share"] <= MAX_HALT_SHARE)
    return "continue paper" if ok else "retire or re-tune within budget"


def score_file(path: str, slippage: float, level: str) -> list[dict]:
    """One trade per (stock, day) at the given trigger level: entry at the event ask, then that stock's later ticks."""
    events, ticks = [], defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["kind"] == "event" and r["level"] == level:
                events.append(r)
            elif r["kind"] == "tick":
                ticks[(r["ts_et"][:10], r["symbol"])].append(r)
    out, seen = [], set()
    for e in events:
        day, sym = e["ts_et"][:10], e["symbol"]
        if (day, sym) in seen or not e["ask"]:
            continue
        seen.add((day, sym))
        later = [{"bid": float(t["bid"]), "halted": t["halted"] == "1"} for t in ticks[(day, sym)]
                 if t["ts_et"] > e["ts_et"] and t["bid"]]
        trade = simulate_trade(float(e["ask"]), later, slippage=slippage)
        if trade:
            out.append({**trade, "day": day, "symbol": sym})
    return out


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "spike_log.csv"
    for level in ("30", "50", "100"):      # all three reported; none picked after the fact
        res = {s: summarize(score_file(path, s, level)) for s in SLIPPAGE_CASES}
        for s, r in res.items():
            print(f"+{level}% trigger, slippage {s:.0%}: {r}")
        print(f"+{level}% verdict:", verdict(res[SLIPPAGE_CASES[0]], res[SLIPPAGE_CASES[-1]]))
