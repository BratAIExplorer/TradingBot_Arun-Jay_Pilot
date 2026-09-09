"""
Fundamentals gate data — curated CSV primary, yfinance auto-fill, blank -> excluded.

The CSV (strategies/configs/fundamentals.csv) is the source of truth. Refresh it
each quarter with:

    python -m strategies.framework.fundamentals

That pulls what yfinance has for every universe ticker and writes the CSV.
yfinance small-cap Indian coverage is PARTIAL: any field it can't provide is left
blank, and a blank required field makes the name fail the gate (can't verify ->
don't trade). Swap in a paid backend (e.g. EODHD — legal to automate) by passing
a different `fetch` to build_csv; do NOT scrape screener.in (ToS + brittle).
"""
from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

_FIELDS = ["ticker", "roe_pct", "debt_equity", "positive_earnings",
           "market_cap_cr", "avg_daily_value_cr", "source", "as_of"]


@dataclass(frozen=True)
class FundamentalsRow:
    ticker: str
    roe_pct: Optional[float]
    debt_equity: Optional[float]
    positive_earnings: Optional[bool]
    market_cap_cr: Optional[float]
    avg_daily_value_cr: Optional[float]
    source: str
    as_of: str


def fetch_yf(ticker: str) -> dict:
    """Best-effort fundamentals from yfinance. Missing keys are simply absent."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info or {}
    except Exception:
        return {}

    roe = info.get("returnOnEquity")
    de = info.get("debtToEquity")            # yfinance reports this as a PERCENT (e.g. 45.6)
    mcap = info.get("marketCap")
    eps = info.get("trailingEps")
    ni = info.get("netIncomeToCommon")
    px = info.get("currentPrice") or info.get("previousClose")
    vol = info.get("averageVolume")

    pos_earn: Optional[bool] = None
    if eps is not None:
        pos_earn = eps > 0
    elif ni is not None:
        pos_earn = ni > 0

    out: dict = {}
    if roe is not None:
        out["roe_pct"] = round(roe * 100, 2)
    if de is not None:
        out["debt_equity"] = round(de / 100.0, 3)   # ponytail: /100 — yfinance gives %, gate wants a ratio
    if pos_earn is not None:
        out["positive_earnings"] = pos_earn
    if mcap:
        out["market_cap_cr"] = round(mcap / 1e7, 1)
    if px and vol:
        out["avg_daily_value_cr"] = round(px * vol / 1e7, 2)
    return out


def build_csv(tickers: list, path: str,
              fetch: Callable[[str], dict] = fetch_yf, sleep: float = 0.3) -> int:
    """Write one row per ticker. Blank cell = field unavailable. Returns row count."""
    today = date.today().isoformat()
    rows = []
    for t in tickers:
        d = fetch(t) or {}
        rows.append({
            "ticker": t,
            "roe_pct": d.get("roe_pct", ""),
            "debt_equity": d.get("debt_equity", ""),
            "positive_earnings": "" if d.get("positive_earnings") is None else int(bool(d["positive_earnings"])),
            "market_cap_cr": d.get("market_cap_cr", ""),
            "avg_daily_value_cr": d.get("avg_daily_value_cr", ""),
            "source": "yfinance" if d else "unverified",
            "as_of": today,
        })
        if sleep:
            time.sleep(sleep)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _num(s: str) -> Optional[float]:
    s = (s or "").strip()
    return float(s) if s else None


def load_csv(path: str) -> dict:
    """ticker -> FundamentalsRow. Empty cells become None."""
    out: dict = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pe = (r.get("positive_earnings") or "").strip()
            out[r["ticker"]] = FundamentalsRow(
                ticker=r["ticker"],
                roe_pct=_num(r.get("roe_pct")),
                debt_equity=_num(r.get("debt_equity")),
                positive_earnings=None if pe == "" else bool(int(pe)),
                market_cap_cr=_num(r.get("market_cap_cr")),
                avg_daily_value_cr=_num(r.get("avg_daily_value_cr")),
                source=r.get("source", ""),
                as_of=r.get("as_of", ""),
            )
    return out


def passes_gate(row: Optional[FundamentalsRow], gate,
                min_cap_cr: float, max_cap_cr: float) -> tuple:
    """(ok, plain-English reason). A missing required field -> not ok."""
    if not gate.enabled:
        return True, "fundamentals gate off"
    if row is None:
        return False, "no fundamentals row — excluded"

    if row.roe_pct is None:
        return False, "ROE unknown — excluded"
    if row.roe_pct < gate.min_roe:
        return False, f"ROE {row.roe_pct:.1f}% below the {gate.min_roe:g}% minimum"

    if row.debt_equity is None:
        return False, "debt/equity unknown — excluded"
    if row.debt_equity > gate.max_debt_equity:
        return False, f"D/E {row.debt_equity:.2f} above the {gate.max_debt_equity:g} ceiling"

    if gate.require_positive_earnings:
        if row.positive_earnings is None:
            return False, "earnings sign unknown — excluded"
        if not row.positive_earnings:
            return False, "negative earnings"

    if row.market_cap_cr is None:
        return False, "market cap unknown — excluded"
    if not (min_cap_cr <= row.market_cap_cr <= max_cap_cr):
        return False, f"market cap Rs {row.market_cap_cr:.0f}cr outside the Rs {min_cap_cr:g}-{max_cap_cr:g}cr band"

    return True, "passes"


if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from strategies.small_cap_universe import SMALLCAP_TICKERS

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "configs", "fundamentals.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    n = build_csv(list(SMALLCAP_TICKERS), out_path)
    rows = load_csv(out_path)
    filled = sum(1 for r in rows.values() if r.roe_pct is not None and r.debt_equity is not None)
    print(f"wrote {n} rows -> {out_path}")
    print(f"{filled}/{n} have both ROE and D/E from yfinance "
          f"({n - filled} will be excluded by the gate until filled in by hand or a paid feed)")
