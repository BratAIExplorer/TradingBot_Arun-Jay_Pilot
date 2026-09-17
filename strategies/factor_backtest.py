"""
Factor / rotation backtest engine — clean, self-contained, separate from the
small-cap rope strategy.

This is the "what actually works over 10-15 years" harness. It tests monthly
rebalance strategies (trend-timing, dual momentum, cross-sectional momentum)
against buy-and-hold, net of a conservative round-trip cost, on US and India
tradable instruments.

Data: Yahoo monthly bars, auto_adjust=True (so ETF prices are total-return —
distributions reinvested). Cash = 0% return (conservative; no risk-free credit).

Why monthly: the strategies tested here are monthly by design (Faber 10-mo SMA,
Antonacci 12-mo lookback, Jegadeesh-Titman 12-1 momentum). Monthly bars also make
the cost model honest — turnover is measured in round-trips per year.

Honesty rules baked in:
- Signals use only data available at the signal date (t's close -> t+1's return).
- Round-trip cost is charged on every change in holdings.
- Benchmark is the tradable index ETF itself (SPY / NIFTYBEES), not a sterile
  price index that ignores dividends.
- Cash earns 0%: a strategy that sits in cash has to beat buy-and-hold by a lot
  on drawdown to be worth it, and we don't flatter it with a phony cash yield.

Run:  python -m strategies.factor_backtest
"""
from __future__ import annotations

import argparse
import os
import warnings
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_CACHE = os.path.join(os.path.dirname(__file__), ".px_cache")

# ---- instrument universes (tradable, liquid, 15y history) -------------------

US_INDEX = "SPY"
US_UNIVERSE = ["SPY", "QQQ", "EFA", "TLT", "GLD"]       # dual-momentum basket
IN_INDEX = "NIFTYBEES.NS"
IN_UNIVERSE = ["NIFTYBEES.NS", "JUNIORBEES.NS", "GOLDBEES.NS", "LIQUIDBEES.NS"]

# conservative round-trip cost assumptions (bps of notional)
# US: commission-free + tight ETF spreads. India: STT + spread + a little impact.
COSTS = {"US": 8.0, "India": 20.0}


# ---- data -------------------------------------------------------------------

def load_monthly(tickers: list[str]) -> pd.DataFrame:
    """Monthly closes, one column per ticker, total-return (auto_adjust)."""
    os.makedirs(_CACHE, exist_ok=True)
    out = {}
    for t in tickers:
        cf = os.path.join(_CACHE, f"{t}_1mo.pkl")
        if os.path.exists(cf) and (datetime.now().timestamp() - os.path.getmtime(cf)) < 86_400 * 30:
            s = pd.read_pickle(cf)
        else:
            import yfinance as yf

            d = yf.download(t, period="15y", interval="1mo", progress=False, auto_adjust=True)
            if d is None or d.empty:
                continue
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
            s = d["Close"].dropna()
            s.to_pickle(cf)
        out[t] = s
    df = pd.DataFrame(out)
    df = df.dropna(how="all")
    return df


# ---- strategy weight generators (pure; take price history -> weight at t) ---

def faber_weights(prices: pd.Series, ma_months: int = 10) -> pd.Series:
    """1.0 when price > trailing MA, else 0 (cash). Classic Faber 2007."""
    ma = prices.rolling(ma_months).mean()
    return (prices > ma).astype(float)


def momentum_score(prices: pd.DataFrame, lookback: int = 12, skip_last: int = 0) -> pd.DataFrame:
    """Trailing total return over `lookback` months, optionally skipping the
    most recent `skip_last` months (Jegadeesh-Titman style)."""
    if skip_last:
        return prices.shift(skip_last) / prices.shift(lookback) - 1.0
    return prices / prices.shift(lookback) - 1.0


def dual_momentum_weights(prices: pd.DataFrame, lookback: int = 12, top_n: int = 1) -> pd.DataFrame:
    """Each month, hold the `top_n` assets with the highest trailing return,
    but only if that return is positive (absolute filter); else cash.
    Equal-weight across the top_n. Antonacci-style absolute + relative."""
    ret = momentum_score(prices, lookback)
    w = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    for t in prices.index:
        r = ret.loc[t].dropna()
        if r.empty:
            continue
        pos = r[r > 0].sort_values(ascending=False)
        if pos.empty:
            continue
        for name in pos.index[:top_n]:
            w.loc[t, name] = 1.0 / top_n
    return w


# ---- portfolio engine -------------------------------------------------------

@dataclass
class Result:
    label: str
    total_return: float
    cagr: float
    vol: float
    sharpe: float
    max_dd: float
    calmar: float
    round_trips_per_year: float
    pct_time_invested: float
    equity: pd.Series = field(repr=False)


def _run(weights: pd.DataFrame, prices: pd.DataFrame, cost_bps: float,
         label: str) -> Result:
    """weights[t] held into prices[t+1]. Cash (sum<1) earns 0%."""
    w = weights.shift(1)                       # signal at t -> held through t+1
    asset_ret = prices.pct_change()
    w = w.reindex_like(asset_ret).fillna(0.0)

    # cash weight
    cash_w = (1.0 - w.sum(axis=1)).clip(lower=0.0)

    gross = (w * asset_ret).sum(axis=1)
    # turnover cost: how much the weights changed each period, priced at cost_bps
    delta = w.diff().abs().sum(axis=1)
    cost = delta * cost_bps / 10_000.0
    net = gross - cost

    equity = (1.0 + net.fillna(0.0)).cumprod()
    equity = equity / equity.iloc[0] * 100.0

    n = 12.0
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / 100.0) ** (1.0 / years) - 1.0
    mret = net.fillna(0.0)
    vol = mret.std() * np.sqrt(n)
    sharpe = mret.mean() / mret.std() * np.sqrt(n) if mret.std() > 0 else 0.0
    dd = equity / equity.cummax() - 1.0
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0.0
    rtpy = delta.fillna(0.0).mean() * n          # round-trips per year (proxy)
    invested = (w.sum(axis=1) > 0.99).mean()

    return Result(label, float(equity.iloc[-1] / 100.0 - 1.0), cagr, vol, sharpe,
                  max_dd, calmar, rtpy, float(invested), equity)


def bench_result(prices: pd.DataFrame, ticker: str, cost_bps: float) -> Result:
    w = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    w[ticker] = 1.0
    return _run(w, prices, cost_bps, f"Buy & hold {ticker}")


# ---- reporting --------------------------------------------------------------

def print_table(results: list[Result]) -> None:
    hdr = (f"{'Strategy':<34}{'TotRet':>9}{'CAGR':>9}{'Vol':>7}{'Sharpe':>8}"
           f"{'MaxDD':>8}{'Calmar':>8}{'RT/yr':>7}{'%Inv':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(results, key=lambda x: x.calmar, reverse=True):
        print(f"{r.label:<34}{r.total_return*100:>8.0f}%{r.cagr*100:>8.1f}%"
              f"{r.vol*100:>6.1f}%{r.sharpe:>8.2f}{r.max_dd*100:>7.0f}%"
              f"{r.calmar:>8.2f}{r.round_trips_per_year:>7.1f}{r.pct_time_invested*100:>5.0f}%")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback", type=int, default=12)
    ap.add_argument("--ma", type=int, default=10)
    ap.add_argument("--top-n", type=int, default=1)
    args = ap.parse_args()

    for region, universe, idx in (("US", US_UNIVERSE, US_INDEX),
                                  ("India", IN_UNIVERSE, IN_INDEX)):
        print(f"\n{'='*92}\n{region}  ({universe})   round-trip cost = {COSTS[region]} bps\n{'='*92}")
        prices = load_monthly(universe)
        if idx not in prices.columns:
            print(f"  !! {idx} missing, skipping")
            continue
        first = prices.index[0].date()
        last = prices.index[-1].date()
        print(f"  window: {first} -> {last}  ({len(prices)} months)")

        # shared index column for single-asset trend timing
        idx_series = prices[idx]

        results = [
            bench_result(prices, idx, COSTS[region]),
            _run(pd.DataFrame({"x": faber_weights(idx_series, args.ma)}),
                 pd.DataFrame({"x": idx_series}), COSTS[region],
                 f"Faber {args.ma}-mo SMA on {idx}"),
            _run(dual_momentum_weights(prices, args.lookback, args.top_n),
                 prices, COSTS[region],
                 f"Dual momentum (top {args.top_n}, {args.lookback}mo)"),
        ]
        print_table(results)
        print(f"\n  (cash earns 0%; cost charged on every turnover)")

    print("\nDone.")


if __name__ == "__main__":
    main()
