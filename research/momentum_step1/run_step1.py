"""
STEP 1 - cheapest edge test: "top 8 by HQM score, rebalance weekly" vs buy-and-hold index.

READ-ONLY research script. Touches no bot file. Writes only inside research/momentum_step1/.

Known bias (deliberate, documented): universe = TODAY's index members (survivorship bias).
That bias can only FLATTER the strategy. So:
  - FAIL here  => conclusive, strategy is dead.
  - PASS here  => inconclusive, go to Step 2 (point-in-time universe).

Rules (copied from the momentum_trader README, no tuning):
  score = mean of cross-sectional percentile ranks of 1M/3M/6M/1Y returns (21/63/126/252 days)
  drop any stock with a percentile < 25 in ANY period; top 8 by score, equal weight
  signal on Friday-ish close (last trading day of week), FILL AT NEXT DAY OPEN (no same-day fill)
  cost 0.10% per side on traded notional
Variant B: same but 1M excluded from score/filter (momentum literature skips latest month).

Usage: python run_step1.py US|IN
"""
import sys, io, json
import numpy as np, pandas as pd

MKT = sys.argv[1] if len(sys.argv) > 1 else "US"
START, END = "2015-06-01", None
N, COST, MIN_PCT = 8, 0.001, 25


def universe():
    if MKT == "US":
        import requests
        r = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        t = pd.read_html(io.StringIO(r.text))[0]
        return [s.replace(".", "-") for s in t["Symbol"]], "QQQ"
    syms = pd.read_csv("../../nifty500.csv")["Symbol"].astype(str).str.strip()
    return [s + ".NS" for s in syms], "^NSEI"


def load(tickers, bench):
    import yfinance as yf
    frames_o, frames_c = [], []
    allt = tickers + [bench]
    for i in range(0, len(allt), 100):
        d = yf.download(allt[i:i + 100], start=START, end=END, auto_adjust=True,
                        progress=False, group_by="column", threads=True)
        frames_o.append(d["Open"]); frames_c.append(d["Close"])
    o = pd.concat(frames_o, axis=1); c = pd.concat(frames_c, axis=1)
    return o.loc[:, ~o.columns.duplicated()], c.loc[:, ~c.columns.duplicated()]


def scores(c, lookbacks):
    pct = []
    for lb in lookbacks:
        r = c / c.shift(lb) - 1
        pct.append(r.rank(axis=1, pct=True) * 100)
    pct = np.stack([p.values for p in pct])          # (L, T, S)
    score = np.nanmean(pct, axis=0)
    ok = np.all(pct >= MIN_PCT, axis=0)              # NaN compares False -> excluded
    score = np.where(ok, score, np.nan)
    return pd.DataFrame(score, index=c.index, columns=c.columns)


def backtest(o, c, bench, lookbacks, cash_when_empty=True):
    stocks = [x for x in c.columns if x != bench]
    sc = scores(c[stocks], lookbacks)
    idx = c.index
    wk = pd.Series(idx, index=idx).groupby([idx.isocalendar().year, idx.isocalendar().week]).last().values
    wk = [d for d in wk if idx.get_loc(d) + 1 < len(idx)]
    weights = {}
    for d in wk:
        row = sc.loc[d].dropna().sort_values(ascending=False).head(N)
        fill = idx[idx.get_loc(d) + 1]               # next-day open fill
        weights[fill] = pd.Series(1.0 / len(row), index=row.index) if len(row) else pd.Series(dtype=float)
    # daily returns: hold from fill-open to next fill-open (open-to-open), costs at each rebalance
    ro = o[stocks].pct_change(fill_method=None).shift(-1)   # open[t]->open[t+1] return, indexed at t
    fills = sorted(weights)
    rets, prev = [], pd.Series(dtype=float)
    for k, f in enumerate(fills):
        nxt = fills[k + 1] if k + 1 < len(fills) else idx[-1]
        w = weights[f]
        seg = ro.loc[f:nxt].iloc[:-1] if nxt != idx[-1] else ro.loc[f:nxt]
        if len(seg) == 0: continue
        g = (seg[w.index].fillna(0) * w).sum(axis=1) if len(w) else pd.Series(0.0, index=seg.index)
        turn = (w.reindex(prev.index.union(w.index)).fillna(0) -
                prev.reindex(prev.index.union(w.index)).fillna(0)).abs().sum()
        g.iloc[0] -= turn * COST                      # cost: buy+sell notional * 0.10% per side
        rets.append(g); prev = w
    s = pd.concat(rets)
    b = o[bench].pct_change(fill_method=None).shift(-1).reindex(s.index).fillna(0)
    return s, b


def stats(r):
    r = r.fillna(0); eq = (1 + r).cumprod()
    yrs = len(r) / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else np.nan
    dd = (eq / eq.cummax() - 1).min()
    sh = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    return dict(CAGR=round(cagr * 100, 1), MaxDD=round(dd * 100, 1), Sharpe=round(sh, 2))


def main():
    tk, bench = universe()
    o, c = load(tk, bench)
    c = c.dropna(how="all"); o = o.reindex(c.index)
    n_ok = int(c.drop(columns=[bench], errors="ignore").notna().any().sum())
    out = {"market": MKT, "bench": bench, "tickers_requested": len(tk), "tickers_with_data": n_ok,
           "data_from": str(c.index[0].date()), "data_to": str(c.index[-1].date())}
    for name, lb in [("A_full_1m3m6m12m", [21, 63, 126, 252]), ("B_skip_1m", [63, 126, 252])]:
        s, b = backtest(o, c, bench, lb)
        s = s[s.index >= "2016-07-01"]; b = b.reindex(s.index)
        res = {"strategy": stats(s), "bench": stats(b), "slices": []}
        for y0 in range(2016, 2026, 2):
            m = (s.index >= f"{y0}-07-01") & (s.index < f"{y0 + 2}-01-01") if y0 == 2016 else \
                (s.index >= f"{y0}-01-01") & (s.index < f"{y0 + 2}-01-01")
            if m.sum() < 100: continue
            ss, bb = stats(s[m]), stats(b[m])
            res["slices"].append({"from": str(s.index[m][0].date()), "to": str(s.index[m][-1].date()),
                                  "strat": ss, "bench": bb,
                                  "beats_return": bool(ss["CAGR"] > bb["CAGR"]), "beats_dd": bool(ss["MaxDD"] > bb["MaxDD"])})
        out[name] = res
    json.dump(out, open(f"results_{MKT}.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


main()
