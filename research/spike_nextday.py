"""Next-day follow-up test on spike_log.csv events. Rules: Documentation/NEXTDAY_TEST_RULES.md  (python -m research.spike_nextday spike_log.csv)."""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timedelta

from research.spike_scorer import COMMISSION, NOTIONAL, SLIPPAGE_CASES, _net_pct, summarize, unresolved_trade, verdict

FIRST_DAY = "2026-11-03"      # earlier rows are excluded (see SPIKE_TEST_RULES.md amendment 2026-11-02)
HORIZONS = (1, 2, 3)          # trading days after the flag day; T+1 is the verdict horizon
PENDING_DAYS = 5              # younger than this and no next bar yet -> pending, not unresolved
VARIANTS = {                  # frozen, see rules file
    "ALL": lambda b: True,
    "HOLD": lambda b: b["close"] >= b["prev_close"] * 1.30,
    "STRONG": lambda b: b["close"] >= b["high"] * 0.90,
}


def flagged_days(path: str) -> dict[tuple[str, str], str]:
    """(day, symbol) -> first event time. One stock-day per stock per day, whatever the level."""
    out: dict[tuple[str, str], str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            day = r["ts_et"][:10]
            if r["kind"] == "event" and day >= FIRST_DAY:
                out.setdefault((day, r["symbol"]), r["ts_et"])
    return out


def trade_from_bars(bars: list[dict] | None, day: str, slippage: float, horizon: int = 1, today: str | None = None) -> dict | None:
    """bars: ascending [{date, open, high, close, prev_close}] (date = 'YYYY-MM-DD').
    Returns a trade dict, None for 'pending' (too recent to score), or an unresolved trade."""
    idx = next((i for i, b in enumerate(bars or []) if b["date"] == day), None)
    if idx is not None and idx + horizon < len(bars):
        fill = bars[idx]["close"] * (1 + slippage)
        net = _net_pct(bars[idx + horizon]["close"], fill, slippage, COMMISSION, NOTIONAL)
        gap = bars[idx + 1]["open"] < bars[idx]["close"] * 0.90
        return {"net_pct": net, "unresolved": False, "halt_trapped": False, "gap_down": gap, "bar": bars[idx]}
    now = date.fromisoformat(today or datetime.now().date().isoformat())
    current = bool(bars) and (now - date.fromisoformat(bars[-1]["date"])).days <= 4   # feed is up to date, so a missing exit bar is just not here yet
    young = (now - date.fromisoformat(day)).days < PENDING_DAYS
    if idx is not None and current or (idx is None and young):
        return None
    return {**unresolved_trade(), "gap_down": False, "bar": bars[idx] if idx is not None else None}


def fetch_bars(symbol: str, first: str, last: str) -> list[dict] | None:
    import yfinance as yf          # imported here so the tests need no network library
    try:
        df = yf.download(symbol.replace(" ", "-"), start=(date.fromisoformat(first) - timedelta(days=7)).isoformat(),
                         end=(date.fromisoformat(last) + timedelta(days=10)).isoformat(), auto_adjust=False, progress=False, multi_level_index=False)
    except Exception:              # a failed download is an unresolved trade, never a dropped one
        return None
    if df is None or df.empty:
        return None
    closes = df["Close"].tolist()
    return [{"date": ix.date().isoformat(), "open": float(r["Open"]), "high": float(r["High"]), "close": float(r["Close"]),
             "prev_close": closes[i - 1] if i else float(r["Close"])} for i, (ix, r) in enumerate(df.iterrows())]


def score(path: str, fetch=fetch_bars, today: str | None = None) -> dict:
    stock_days = flagged_days(path)
    days = sorted({d for d, _ in stock_days})
    bars_by_sym = {s: fetch(s, days[0], days[-1]) for s in sorted({s for _, s in stock_days})} if days else {}
    result: dict = {"pending": 0}
    for slip in SLIPPAGE_CASES:
        for h in HORIZONS:
            for name, keep in VARIANTS.items():
                trades = []
                for (day, sym) in stock_days:
                    t = trade_from_bars(bars_by_sym[sym], day, slip, h, today)
                    if t is None:
                        result["pending"] = result["pending"] + 1 if slip == SLIPPAGE_CASES[0] and h == 1 and name == "ALL" else result["pending"]
                        continue
                    if t["bar"] is None or keep(t["bar"]):          # no bar = cannot filter, so it stays in as unresolved
                        trades.append({**t, "day": day, "symbol": sym})
                result[(name, h, slip)] = trades
    return result


if __name__ == "__main__":
    res = score(sys.argv[1] if len(sys.argv) > 1 else "spike_log.csv")
    print(f"pending (too recent): {res['pending']}")
    for name in VARIANTS:
        lo, hi = SLIPPAGE_CASES[0], SLIPPAGE_CASES[-1]
        for h in HORIZONS:
            s = summarize(res[(name, h, hi)])
            print(f"{name} T+{h} slippage {hi:.0%}: n={s['n']} unresolved={s['n_unresolved']} median={s['median']} "
                  f"ex_top2={s['median_ex_top2']} cons={s['median_cons']} mean={s['mean']} stock_days={s['stock_days']} days={s['days']}")
        t1 = res[(name, 1, hi)]
        gaps = sum(t["gap_down"] for t in t1)
        print(f"{name} T+1 verdict: {verdict(summarize(res[(name, 1, lo)]), summarize(t1))}  (gap-down >=10% at next open: {gaps} of {len(t1)})")
