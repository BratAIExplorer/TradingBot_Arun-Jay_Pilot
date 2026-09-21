"""Backtest of the Voyager dip rule on the 15 seed names (daily bars, yfinance).
Rule = brokers/dip_engine.decide(): flat + close <= N-day high*(1-dip%) -> buy at that close;
held -> GTC limit sell at cost*(1+sell%). Optional stop at cost*(1-stop%), cooldown after a sell.
Same-day target+stop both touched -> assume STOP first (pessimistic). Open positions at end marked to last close.
No commissions/slippage. Survivorship bias: these are today's names."""
import itertools
import sys
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
SYMS = "HPQ CMCSA PYPL T VZ F NKE SBUX KO KHC PFE VTRS BAC WFC OXY".split()
YEARS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
COST = float(sys.argv[2]) / 100 if len(sys.argv) > 2 else 0.0  # round-trip cost per trade, as a fraction

raw = yf.download(SYMS, period=f"{YEARS}y", auto_adjust=True, progress=False)
C, H, L = raw["Close"], raw["High"], raw["Low"]


def run(sym, dip, sell, stop, cool, lookback=20):
    c, h, l = C[sym].dropna(), H[sym].dropna(), L[sym].dropna()
    ref = c.rolling(lookback).max()  # engine uses daily-bar high; close-high is a close proxy
    ref = h.rolling(lookback).max()
    trades, pos, cd_until = [], None, -1
    idx = c.index
    for i in range(lookback, len(c)):
        if pos:
            tgt, stp = pos["cost"] * (1 + sell / 100), (pos["cost"] * (1 - stop / 100) if stop else None)
            if stp and l.iloc[i] <= stp:
                trades.append((stp / pos["cost"] - 1, i - pos["i"], "stop")); pos, cd_until = None, i + cool
            elif h.iloc[i] >= tgt:
                trades.append((sell / 100, i - pos["i"], "target")); pos, cd_until = None, i + cool
        elif i >= cd_until and c.iloc[i] <= ref.iloc[i - 1] * (1 - dip / 100):
            pos = {"cost": c.iloc[i], "i": i}
    if pos:
        trades.append((c.iloc[-1] / pos["cost"] - 1, len(c) - 1 - pos["i"], "open"))
    return trades, c.iloc[-1] / c.iloc[0] - 1


def summarize(dip, sell, stop, cool):
    allt, bh = [], []
    for s in SYMS:
        t, b = run(s, dip, sell, stop, cool)
        allt += t; bh.append(b)
    if not allt:
        return None
    r = np.array([x[0] - COST for x in allt]); d = np.array([x[1] for x in allt])
    closed = [x for x in allt if x[2] != "open"]
    rc = np.array([x[0] - COST for x in closed]) if closed else np.array([0.0])
    return dict(dip=dip, sell=sell, stop=stop or "none", cool=cool, trades=len(r),
                win=round((rc > 0).mean() * 100), avg_ret=round(r.mean() * 100, 2), worst=round(r.min() * 100, 1),
                avg_days=round(d.mean(), 1), stops=sum(x[2] == "stop" for x in allt), open=sum(x[2] == "open" for x in allt),
                # capital-weighted: total return / total capital-days, annualised (252d) -> compare to buy&hold
                ann_on_capital=round((r.sum() / d.sum()) * 252 * 100, 1),
                pnl_vs_bh=round(r.sum() / len(SYMS) * 100, 1),  # total return on equal reserved capital ($100 per name)
                bh_avg=round(np.mean(bh) * 100, 1))


rows = []
for dip, sell, stop, cool in itertools.product([5, 10, 15], [8, 15], [0, 5, 10, 15], [0, 5]):
    if not stop and cool:  # cooldown only matters after sells; keep grid small
        continue
    r = summarize(dip, sell, stop, cool)
    if r: rows.append(r)
df = pd.DataFrame(rows)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
print(f"{YEARS}y window, {len(SYMS)} names. Buy&hold avg total return over window: {df.bh_avg.iloc[0]}%")
print(f"round-trip cost {COST*100:.1f}%")
df = df[df.cool == 0]
print(df[["dip","sell","stop","trades","win","avg_ret","stops","open","pnl_vs_bh"]].to_string(index=False))
print("configs beating buy&hold on equal capital:", int((df.pnl_vs_bh > df.bh_avg).sum()), "of", len(df))
