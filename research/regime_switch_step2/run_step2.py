"""
STEP 2 - would a Nifty market-regime on/off switch have cut the bots' losses?
READ-ONLY. Reads ../../full_trade_export.csv, writes only here.
Regime rule is MY SIMPLE ASSUMPTION (not the bot's / momentum_trader's exact code):
  UP = close > SMA20 > SMA50 ; DOWN = close < SMA50 ; else CAUTION.   Index = ^NSEI daily close.
Attribution: each real SELL with pnl_net is matched to the latest earlier BUY of same symbol+exchange;
the regime on that BUY's date decides if the switch would have blocked the trade (DOWN = blocked).
Paper rows excluded. Exact duplicate SELL rows (same symbol, price, pnl) counted once.
"""
import pandas as pd, yfinance as yf
t = pd.read_csv("../../full_trade_export.csv", parse_dates=["timestamp"])
t = t[t.broker != "PAPER"].copy()
n = yf.download("^NSEI", start="2025-06-01", progress=False, auto_adjust=True)["Close"].squeeze()
reg = pd.DataFrame({"c": n, "s20": n.rolling(20).mean(), "s50": n.rolling(50).mean()})
reg["regime"] = "CAUTION"
reg.loc[(reg.c > reg.s20) & (reg.s20 > reg.s50), "regime"] = "UP"
reg.loc[reg.c < reg.s50, "regime"] = "DOWN"
def rg(ts):
    d = reg.loc[:ts.normalize()].iloc[-1]; return d.regime
sells = t[(t.action == "SELL") & t.pnl_net.notna()].drop_duplicates(["symbol", "price", "pnl_net"])
rows = []
for _, s in sells.iterrows():
    b = t[(t.action == "BUY") & (t.symbol == s.symbol) & (t.exchange == s.exchange) & (t.timestamp < s.timestamp)]
    if b.empty: rows.append((s.symbol, s.timestamp.date(), None, s.pnl_net)); continue
    rows.append((s.symbol, s.timestamp.date(), rg(b.iloc[-1].timestamp), s.pnl_net))
r = pd.DataFrame(rows, columns=["symbol", "sell_date", "entry_regime", "pnl_net"])
print(r.to_string()); print()
print(r.groupby("entry_regime", dropna=False).pnl_net.agg(["count", "sum"]))
print("total pnl", r.pnl_net.sum(), "| trades", len(r))
print("regime on each day in window:"); print(reg.loc["2026-01-20":"2026-02-17"].regime.value_counts())
r.to_csv("step2_trades_by_regime.csv", index=False)
