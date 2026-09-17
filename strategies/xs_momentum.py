"""
Cross-sectional momentum with an optional index regime filter.

The one candidate that directly fixes the *selection* flaw: every month, rank a
liquid large-cap universe by trailing 12-month return (skipping the most recent
month — Jegadeesh-Titman), hold the top N equal-weight, rebalance monthly.
Optionally gate the whole book on the index being above its 10-month SMA
(the regime filter that historically avoids momentum crashes).

Honest benchmark: BOTH the tradable cap-weighted index ETF (NIFTYBEES/SPY) and a
static equal-weight buy-and-hold of the same universe. If momentum can't beat the
equal-weight universe, it has no selection edge — that's the test.

Survivorship caveat: universes are today's constituents. Recent listings (e.g.
HDFCLIFE, SBILIFE, ADANIENT) have no data before their IPO, so early years use a
smaller, older, survivors-only subset. This FLATTERS momentum (survivors won),
so read any edge as an upper bound.

Run:  python -m strategies.xs_momentum
"""
from __future__ import annotations

import argparse
import os
import sys
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nifty50 import NIFTY_50  # noqa: E402

_CACHE = os.path.join(os.path.dirname(__file__), ".px_cache")


def _load_monthly(ticker: str) -> pd.Series | None:
    os.makedirs(_CACHE, exist_ok=True)
    cf = os.path.join(_CACHE, f"{ticker}_1mo.pkl")
    if os.path.exists(cf) and (datetime.now().timestamp() - os.path.getmtime(cf)) < 86_400 * 30:
        return pd.read_pickle(cf)
    import yfinance as yf

    d = yf.download(ticker, period="15y", interval="1mo", progress=False, auto_adjust=True)
    if d is None or d.empty:
        return None
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    s = d["Close"].dropna()
    s.to_pickle(cf)
    return s


def load_universe(tickers: list[str]) -> pd.DataFrame:
    cols = {}
    for t in tickers:
        s = _load_monthly(t)
        if s is not None and len(s) >= 13:
            cols[t] = s
    return pd.DataFrame(cols).dropna(how="all")


def momentum_weights(prices: pd.DataFrame, n_hold: int, lookback: int = 12,
                     skip_last: int = 1, index: pd.Series | None = None,
                     ma_months: int = 10) -> pd.DataFrame:
    mom = prices.shift(skip_last) / prices.shift(lookback) - 1.0
    above = None
    if index is not None:
        above = (index > index.rolling(ma_months).mean()).reindex(prices.index)
    w = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    for t in prices.index:
        if above is not None:
            a = above.loc[t]
            if pd.isna(a) or not bool(a):
                continue
        m = mom.loc[t].dropna()
        if m.empty:
            continue
        top = m.nlargest(n_hold).index
        w.loc[t, top] = 1.0 / n_hold
    return w


def _run(weights: pd.DataFrame, prices: pd.DataFrame, cost_bps: float, label: str) -> dict:
    w = weights.shift(1)
    asset_ret = prices.pct_change()
    w = w.reindex_like(asset_ret).fillna(0.0)
    cash_w = (1.0 - w.sum(axis=1)).clip(lower=0.0)
    gross = (w * asset_ret).sum(axis=1)
    delta = w.diff().abs().sum(axis=1)
    cost = delta * cost_bps / 10_000.0
    net = (gross - cost).fillna(0.0)
    equity = (1.0 + net).cumprod()
    equity = equity / equity.iloc[0] * 100.0

    n = 12.0
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / 100.0) ** (1.0 / years) - 1.0
    mret = net
    vol = mret.std() * np.sqrt(n)
    sharpe = mret.mean() / mret.std() * np.sqrt(n) if mret.std() > 0 else 0.0
    dd = equity / equity.cummax() - 1.0
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0.0
    rtpy = delta.fillna(0.0).mean() * n
    invested = (w.sum(axis=1) > 0.99).mean()
    return dict(label=label, tot=float(equity.iloc[-1] / 100.0 - 1.0), cagr=cagr,
                vol=vol, sharpe=sharpe, maxdd=max_dd, calmar=calmar, rtpy=rtpy,
                invested=float(invested), equity=equity)


def static_ew_weights(prices: pd.DataFrame) -> pd.DataFrame:
    """Buy all names equal-weight once, never touch it. The truest no-skill bench."""
    valid = prices.notna()
    n = valid.sum(axis=1)
    w = valid.div(n, axis=0)
    return w.fillna(0.0)


def monthly_ew_weights(prices: pd.DataFrame) -> pd.DataFrame:
    """Equal-weight, rebalanced monthly (forces buying everything, zero selection)."""
    valid = prices.notna()
    n = valid.sum(axis=1)
    w = valid.div(n, axis=0)
    return w.fillna(0.0)


def print_rows(rows: list[dict]) -> None:
    hdr = (f"{'Strategy':<38}{'TotRet':>9}{'CAGR':>8}{'Vol':>7}{'Sharpe':>8}"
           f"{'MaxDD':>8}{'Calmar':>8}{'RT/yr':>7}{'%Inv':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: x["calmar"], reverse=True):
        print(f"{r['label']:<38}{r['tot']*100:>8.0f}%{r['cagr']*100:>7.1f}%"
              f"{r['vol']*100:>6.1f}%{r['sharpe']:>8.2f}{r['maxdd']*100:>7.0f}%"
              f"{r['calmar']:>8.2f}{r['rtpy']:>7.1f}{r['invested']*100:>5.0f}%")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-hold", type=int, default=15)
    ap.add_argument("--lookback", type=int, default=12)
    ap.add_argument("--ma", type=int, default=10)
    args = ap.parse_args()

    # ---- India: Nifty 50 ----
    print("\n" + "=" * 92)
    print(f"INDIA — Nifty 50 cross-sectional momentum (top {args.n_hold}, "
          f"{args.lookback}-1mo, cost 40bps RT)")
    print("=" * 92)
    nifty = [f"{t}.NS" for t in sorted(NIFTY_50)]
    prices = load_universe(nifty)
    print(f"  universe: {len(prices.columns)} names with >=13mo of data  "
          f"window {prices.index[0].date()} -> {prices.index[-1].date()}")

    idx = _load_monthly("NIFTYBEES.NS")
    idx = idx.reindex(prices.index)

    rows = [
        _run(static_ew_weights(prices), prices, 40.0, "Static EW buy-&-hold (all 50)"),
        _run(momentum_weights(prices, args.n_hold, args.lookback, 1, None),
             prices, 40.0, f"XS momentum (no filter)"),
        _run(momentum_weights(prices, args.n_hold, args.lookback, 1, idx, args.ma),
             prices, 40.0, f"XS momentum + {args.ma}-mo regime filter"),
    ]
    print_rows(rows)

    # ---- US: S&P 500 ----
    print("\n" + "=" * 92)
    print(f"US — S&P 500 cross-sectional momentum (top {args.n_hold}, "
          f"{args.lookback}-1mo, cost 10bps RT)")
    print("=" * 92)
    sp500 = fetch_sp500()
    if not sp500:
        print("  !! could not fetch S&P 500 constituents; skipping US")
    else:
        us_prices = load_universe(sp500)
        print(f"  universe: {len(us_prices.columns)} names  "
              f"window {us_prices.index[0].date()} -> {us_prices.index[-1].date()}")
        spx = _load_monthly("SPY")
        spx = spx.reindex(us_prices.index)
        us_rows = [
            _run(static_ew_weights(us_prices), us_prices, 10.0, "Static EW buy-&-hold (all)"),
            _run(momentum_weights(us_prices, args.n_hold, args.lookback, 1, None),
                 us_prices, 10.0, f"XS momentum (no filter)"),
            _run(momentum_weights(us_prices, args.n_hold, args.lookback, 1, spx, args.ma),
                 us_prices, 10.0, f"XS momentum + {args.ma}-mo regime filter"),
        ]
        print_rows(us_rows)
    print("\nDone.")


def fetch_sp500() -> list[str]:
    """S&P 500 constituents from Wikipedia (today's list; survivorship caveat)."""
    try:
        import requests

        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                         headers=h, timeout=30)
        tables = pd.read_html(r.text)
        for df in tables:
            if "Symbol" in df.columns:
                syms = [str(s).replace(".", "-") for s in df["Symbol"].tolist()]
                return [s for s in syms if s and s != "nan"]
    except Exception as e:  # noqa: BLE001
        print(f"  (fetch_sp500 failed: {e})")
    return []


if __name__ == "__main__":
    main()
