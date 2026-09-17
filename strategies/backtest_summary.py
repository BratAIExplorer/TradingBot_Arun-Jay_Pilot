"""
Roll every bt_*.csv into one comparison table + equal-weight buy-and-hold
benchmarks from the price cache. Read-only; no network.

    python -m strategies.backtest_summary
"""
from __future__ import annotations

import glob
import os

import pandas as pd

HERE = os.path.dirname(__file__)
CACHE = os.path.join(HERE, ".px_cache")
BOOK = 1000.0  # every run: 10 slots x per_stock 100


def _tag(path: str) -> str:
    return os.path.basename(path)[3:-4]  # strip "bt_" and ".csv"


def summarise() -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "bt_*.csv"))):
        d = pd.read_csv(f)
        if d.empty:
            continue
        closed = d[~d.still_open]
        rows.append({
            "run": _tag(f),
            "trades": len(d),
            "closed": len(closed),
            "win%_all": round(100 * (d.pnl > 0).mean()),
            "mean_trade_%": round(d.pnl_pct.mean(), 1),
            "median_trade_%": round(d.pnl_pct.median(), 1),
            "stuck_open": int((d.outcome == "stuck_at_loss").sum()),
            "book_return_%": round(d.pnl.sum() / BOOK * 100, 1),
            "avg_hold_d": round(d.hold_days.mean()),
        })
    return pd.DataFrame(rows)


def buy_hold(universe_file: str | None, months: int, history: str) -> float:
    if universe_file:
        tickers = [x.strip() for x in open(os.path.join(HERE, universe_file)) if x.strip()]
    else:
        from strategies.small_cap_universe import SMALLCAP_TICKERS
        tickers = list(SMALLCAP_TICKERS)
    start = pd.Timestamp.now().normalize() - pd.DateOffset(months=months)
    rets = []
    for t in tickers:
        cf = os.path.join(CACHE, f"{t}_{history}.pkl")
        if not os.path.exists(cf):
            continue
        px = pd.read_pickle(cf)
        w = px[px.index >= start]
        if len(w) < 20:
            continue
        rets.append(w["Close"].iloc[-1] / w["Close"].iloc[0] - 1.0)
    return round(100 * sum(rets) / len(rets), 1) if rets else float("nan")


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 100)
    print("\n=== STRATEGY RUNS (book_return_% = P&L / $1000 over the run window) ===")
    print(summarise().to_string(index=False))

    print("\n=== EQUAL-WEIGHT BUY-AND-HOLD BENCHMARK (same universes/windows) ===")
    for label, uf, m, h in [
        ("IN small  6mo", None, 6, "2y"),
        ("IN small 24mo", None, 24, "5y"),
        ("US small  6mo", "univ_us_small_sp600.txt", 6, "2y"),
        ("US small 24mo", "univ_us_small_sp600.txt", 24, "5y"),
        ("US mid    6mo", "univ_us_mid_sp400.txt", 6, "2y"),
    ]:
        print(f"  {label:14s}: {buy_hold(uf, m, h):+.1f}%")
