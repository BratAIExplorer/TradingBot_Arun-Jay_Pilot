"""Offline scoring of spike_log.csv. Rules: Documentation/SPIKE_TEST_RULES.md  (python -m research.spike_scorer)."""
from __future__ import annotations

import csv
import math
import statistics
import sys
from collections import defaultdict

SLIPPAGE_CASES = (0.02, 0.05)      # per side; verdict uses the worst
STOP_PCT, NOTIONAL, COMMISSION = 0.10, 500.0, 1.0
TRAIL_PCT = 0.15                   # the one registered challenger (amendment 2026-11-02): reported, never used for the verdict
PENALTY_NET = -50.0                # conservative stand-in for a trade that could not be sold (halted to the close / no bid); a judgement, not data
MIN_STOCK_DAYS, MIN_DAYS, MAX_HALT_SHARE = 100, 10, 0.10
RTH_START = "09:30"                # ET, string-compared against ts_et[11:16]


def _net_pct(exit_bid: float, fill: float, slippage: float, commission_usd: float, notional: float) -> float:
    return (exit_bid * (1 - slippage) / fill - 1) * 100 - 2 * commission_usd / notional * 100


def unresolved_trade(halt_trapped: bool = False, best_case_pct: float | None = None) -> dict:
    """A trade that was entered but has no valid exit price. It is counted, never dropped."""
    return {"net_pct": None, "exit": "unresolved", "unresolved": True, "gap_through": False,
            "halt_trapped": halt_trapped, "best_case_pct": best_case_pct}


def simulate_trade(entry_ask: float, ticks: list[dict], *, slippage: float, stop_pct: float = STOP_PCT,
                   commission_usd: float = COMMISSION, notional: float = NOTIONAL,
                   trail_pct: float | None = None) -> dict | None:
    """Buy at ask+slippage, then walk ticks: sell at the bid once bid <= stop, else at the last tick.
    trail_pct (challenger): the stop trails that far below the highest bid since entry instead of sitting 10% below the fill.
    Halted ticks cannot be sold into; a gap through the stop exits at the real (lower) bid.
    If the position is still halted (or has no bid) at the last tick, or was halted throughout, it is 'unresolved'
    (best_case_pct = what the old pre-halt-bid shortcut would have reported). None only when there are no ticks at all."""
    if not ticks:
        return None
    fill = entry_ask * (1 + slippage)
    stop = fill * (1 - (trail_pct or stop_pct))
    peak = fill
    halt_trapped, exit_bid, how = False, None, "forced"
    for t in ticks:
        if t["halted"]:
            halt_trapped = True
            continue
        bid = t["bid"]
        if bid is None:                        # no quote: cannot evaluate or sell
            continue
        if trail_pct:
            peak = max(peak, bid)
            stop = peak * (1 - trail_pct)
        if bid <= stop:
            exit_bid, how = bid, "trail" if trail_pct else "stop"
            break
        exit_bid = bid
    last = ticks[-1]
    if how == "forced" and (exit_bid is None or last["halted"] or last["bid"] is None):
        best = None if exit_bid is None else _net_pct(exit_bid, fill, slippage, commission_usd, notional)
        return unresolved_trade(halt_trapped, best)
    return {"net_pct": _net_pct(exit_bid, fill, slippage, commission_usd, notional), "exit": how, "unresolved": False,
            "gap_through": how in ("stop", "trail") and exit_bid < stop * 0.99, "halt_trapped": halt_trapped}


def _median(xs: list[float]):
    return statistics.median(xs) if xs else None


def summarize(trades: list[dict]) -> dict:
    """Realized numbers, plus a conservative view where every unresolved trade counts as PENALTY_NET.
    n counts all entered trades; stock_days counts unresolved ones too (they are evidence)."""
    realized = sorted(t["net_pct"] for t in trades if not t.get("unresolved"))
    n_un = len(trades) - len(realized)
    cons = sorted(realized + [PENALTY_NET] * n_un)
    wins, losses = sum(x for x in realized if x > 0), -sum(x for x in realized if x < 0)
    return {"n": len(trades), "n_realized": len(realized), "n_unresolved": n_un,
            "median": _median(realized), "median_ex_top2": _median(realized[:-2]),
            "median_cons": _median(cons), "median_ex_top2_cons": _median(cons[:-2]),
            "mean": statistics.fmean(realized) if realized else None,
            "total_pnl_usd": sum(realized) / 100 * NOTIONAL, "total_pnl_cons_usd": sum(cons) / 100 * NOTIONAL,
            "profit_factor": wins / losses if losses else None,
            "worst5": statistics.fmean(cons[:max(1, math.ceil(len(cons) * 0.05))]) if cons else None,
            "stock_days": len({(t["day"], t["symbol"]) for t in trades}), "days": len({t["day"] for t in trades}),
            "halt_share": sum(t["halt_trapped"] for t in trades) / len(trades) if trades else 0,
            "unresolved_share": n_un / len(trades) if trades else 0}


def verdict(low_slip: dict, worst_slip: dict) -> str:
    """Passing only ever means 'continue paper' -- never 'go live'. Must pass on realized trades AND with unresolved ones at PENALTY_NET."""
    if worst_slip["stock_days"] < MIN_STOCK_DAYS or worst_slip["days"] < MIN_DAYS:
        return "no conclusion"
    medians = (worst_slip[k] for k in ("median", "median_ex_top2", "median_cons", "median_ex_top2_cons"))
    ok = (all(m is not None and m > 0 for m in medians)
          and max(worst_slip["halt_share"], worst_slip["unresolved_share"]) <= MAX_HALT_SHARE)
    return "continue paper" if ok else "retire or re-tune within budget"


def score_file(path: str, slippage: float, level: str, trail_pct: float | None = None) -> tuple[list[dict], int]:
    """One trade per (stock, day) at the given trigger level: entry at the event ask, then that stock's later ticks.
    Returns (trades, skipped_no_ask). Every event with an ask becomes a trade; none is dropped."""
    events, ticks = [], defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["kind"] == "event" and r["level"] == level:
                events.append(r)
            elif r["kind"] == "tick":
                ticks[(r["ts_et"][:10], r["symbol"])].append(r)
    out, seen, skipped = [], set(), 0
    for e in events:
        day, sym = e["ts_et"][:10], e["symbol"]
        if (day, sym) in seen:
            continue
        if not e["ask"]:
            skipped += 1
            continue
        seen.add((day, sym))
        later = [{"bid": float(t["bid"]) if t["bid"] else None, "halted": t["halted"] == "1"} for t in ticks[(day, sym)]
                 if t["ts_et"] > e["ts_et"]]
        trade = simulate_trade(float(e["ask"]), later, slippage=slippage, trail_pct=trail_pct) or unresolved_trade()
        out.append({**trade, "day": day, "symbol": sym,
                    "session": "premarket" if e["ts_et"][11:16] < RTH_START else "regular"})
    return out, skipped


def _brief(s: dict) -> str:
    f = lambda v, d=2: "n/a" if v is None else f"{v:.{d}f}"
    return (f"n={s['n']} (unresolved {s['n_unresolved']}) median {f(s['median'])} / cons {f(s['median_cons'])} "
            f"mean {f(s['mean'])} total ${f(s['total_pnl_usd'], 0)} (cons ${f(s['total_pnl_cons_usd'], 0)}) "
            f"PF {f(s['profit_factor'])} worst5 {f(s['worst5'])}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "spike_log.csv"
    for level in ("30", "50", "100"):      # all three reported; none picked after the fact
        scored = {s: score_file(path, s, level) for s in SLIPPAGE_CASES}
        res = {s: summarize(trades) for s, (trades, _) in scored.items()}
        for s, r in res.items():
            print(f"+{level}% trigger, slippage {s:.0%}: {r}")
        print(f"+{level}% verdict:", verdict(res[SLIPPAGE_CASES[0]], res[SLIPPAGE_CASES[-1]]))
        worst = SLIPPAGE_CASES[-1]
        trades, skipped = scored[worst]
        print(f"  skipped (no ask at trigger): {skipped}")
        for sess in ("premarket", "regular"):   # diagnostic split, not a tuned variant
            print(f"  {sess}: {_brief(summarize([t for t in trades if t['session'] == sess]))}")
        print(f"  challenger {TRAIL_PCT:.0%} trailing stop (report only, not the verdict): "
              f"{_brief(summarize(score_file(path, worst, level, TRAIL_PCT)[0]))}")
