"""
6-month backtest for the Small-Cap Dry-Run strategy.

Walks daily bars one day at a time and calls the SAME SmallCapDryRun.decide()
and advance_rope() the live runner uses, so entry/rope/scale-out/never-sell-at-loss
behave identically. Only sizing + fill accounting is re-implemented here.

ponytail: fundamentals gate is SKIPPED (no point-in-time ROE/D-E/market-cap data
from yfinance — using today's values would be lookahead). Universe is whatever
survives today, so trapped-capital ("stuck") counts are understated by
survivorship. One 6-month window = one weather report, not the climate.

Run:  python -m strategies.backtest_smallcap
      python -m strategies.backtest_smallcap --months 6 --history 2y
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from datetime import datetime

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.framework.base import Position                       # noqa: E402
from strategies.framework.config import load_strategy_config, EntryConfig  # noqa: E402
from strategies.framework.costs import net_buy_cost, net_sell_proceeds  # noqa: E402
from strategies.small_cap_dryrun import SmallCapDryRun, advance_rope, fresh_macd_cross  # noqa: E402
from strategies.small_cap_universe import SMALLCAP_TICKERS            # noqa: E402

CFG_PATH = os.path.join(os.path.dirname(__file__), "configs", "small_cap_dryrun.json")
MIN_BARS = 210  # need a real 200-EMA before we trust the trend filter
_CACHE = os.path.join(os.path.dirname(__file__), ".px_cache")  # daily bars, reused across runs


def _load_prices(ticker: str, period: str) -> pd.DataFrame | None:
    os.makedirs(_CACHE, exist_ok=True)
    cf = os.path.join(_CACHE, f"{ticker}_{period}.pkl")
    if os.path.exists(cf) and (datetime.now().timestamp() - os.path.getmtime(cf)) < 86_400:
        df = pd.read_pickle(cf)
    else:
        import yfinance as yf

        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        df.to_pickle(cf)
    return df if len(df) >= MIN_BARS else None


def _run_one(ticker: str, df: pd.DataFrame, start: pd.Timestamp, strat, cfg,
             fund: dict | None = None) -> list[dict]:
    window = df.index[df.index >= start]
    pos: Position | None = None
    buy_cost = 0.0
    proceeds = 0.0
    entry_date = None
    last_exit_cross = None
    stranded_days = 0
    rope_inactive_days = 0
    trades: list[dict] = []

    for d in window:
        candles = df.loc[:d]
        if len(candles) < MIN_BARS:
            continue
        close = float(candles["Close"].iloc[-1])
        low = float(candles["Low"].iloc[-1])
        adv_cr = float((candles["Close"] * candles["Volume"]).tail(20).mean()) / 1e7

        action = strat.decide(
            ticker, candles, pos,
            avg_daily_value_cr=adv_cr, fundamentals=(fund or {}).get(ticker),
            last_exit_cross_date=last_exit_cross,
        )

        if pos is None:
            if action.kind == "BUY":
                qty = int(cfg.budget.per_stock_amount // close)
                if qty < 1:
                    continue
                _, cross_date = fresh_macd_cross(candles, within_bars=cfg.entry.fresh_cross_max_age_days)
                buy_cost = net_buy_cost(close, qty, cfg.costs)
                proceeds = 0.0
                entry_date = d
                pos = Position(
                    ticker=ticker, exchange="NSE", qty=qty, avg_entry=close, tranches=1,
                    entry_cross_date=cross_date or d.strftime("%d-%b-%Y"),
                    opened_at=d.isoformat(), high_water_mark=close, exit_tranches_remaining=2,
                )
            continue

        # managing an open position
        if "STRANDED HALF" in action.reason:
            stranded_days += 1
        if "rope inactive" in action.reason:
            rope_inactive_days += 1

        if action.kind == "SCALE_OUT":
            sell_qty = pos.qty if action.fraction >= 1.0 else pos.qty // 2
            sell_qty = max(sell_qty, 1)
            proceeds += net_sell_proceeds(close, sell_qty, cfg.costs, thin=True)
            rem = pos.qty - sell_qty
            upd = advance_rope(pos, action, close, low, cfg.exit)
            if rem <= 0:
                trades.append(_close_row(ticker, entry_date, d, pos, buy_cost, proceeds,
                                         "scaled_out", stranded_days, rope_inactive_days))
                last_exit_cross = pos.entry_cross_date
                pos = None
                continue
            pos = replace(pos, qty=rem, **upd)
        else:
            upd = advance_rope(pos, action, close, low, cfg.exit)
            pos = replace(pos, **upd)

    if pos is not None:  # still open at window end -> mark to market
        last_close = float(df["Close"].iloc[-1])
        mtm = net_sell_proceeds(last_close, pos.qty, cfg.costs, thin=True)
        reason = "stuck_at_loss" if (proceeds + mtm - buy_cost) < 0 else "open_in_profit"
        trades.append(_close_row(ticker, entry_date, df.index[-1], pos, buy_cost,
                                 proceeds + mtm, reason, stranded_days, rope_inactive_days,
                                 still_open=True))
    return trades


def _close_row(ticker, entry_date, exit_date, pos, buy_cost, proceeds, reason,
               stranded_days, rope_inactive_days, still_open=False) -> dict:
    pnl = proceeds - buy_cost
    return {
        "ticker": ticker,
        "entry_date": entry_date.date().isoformat(),
        "exit_date": exit_date.date().isoformat(),
        "hold_days": (exit_date - entry_date).days,
        "entry_px": round(pos.avg_entry, 2),
        "buy_cost": round(buy_cost, 0),
        "proceeds": round(proceeds, 0),
        "pnl": round(pnl, 0),
        "pnl_pct": round(pnl / buy_cost * 100, 2) if buy_cost else 0.0,
        "outcome": reason,
        "still_open": still_open,
        "stranded_days": stranded_days,
        "rope_inactive_days": rope_inactive_days,
    }


def _apply_overrides(cfg, hard_stop: float | None, total_budget: float | None,
                     per_stock: float | None, fresh_cross_days: int | None = None,
                     trail_giveback: float | None = None):
    """Return cfg with a hard stop / budget / per-stock size / entry-age / rope
    width overridden WITHOUT touching the live JSON — backtest what-ifs only."""
    ex, bud, en = cfg.exit, cfg.budget, cfg.entry
    if hard_stop is not None:
        ex = replace(ex, hard_stop_pct=hard_stop)
    if trail_giveback is not None:
        ex = replace(ex, trail_giveback_pct=trail_giveback)
    if fresh_cross_days is not None:
        en = replace(en, fresh_cross_max_age_days=fresh_cross_days)
        cfg = replace(cfg, entry=en)
    per = per_stock if per_stock is not None else bud.per_stock_amount
    tot = total_budget if total_budget is not None else bud.total_budget
    if per_stock is not None or total_budget is not None:
        max_names = min(int(tot // per), bud.max_names_cap)
        bud = replace(bud, per_stock_amount=per, total_budget=tot, max_names=max_names)
    return replace(cfg, exit=ex, budget=bud)


def _run_portfolio(frames: dict, start: pd.Timestamp, strat, cfg, fund: dict | None = None):
    """One shared book: <= cfg.budget.max_names names at once. Each day: run exits
    on held names first (frees slots), then fill free slots from that day's BUY
    signals. ponytail: when signals > slots, rank by least-extended above the
    200-EMA (a cheap proxy; the live bot ranks by the scanner confluence score)."""
    slots = cfg.budget.max_names
    days = sorted({d for df in frames.values() for d in df.index[df.index >= start]})
    held: dict = {}
    last_exit_cross: dict = {}
    trades: list[dict] = []
    full_days = 0

    for d in days:
        for tk in list(held):
            df = frames[tk]
            if d not in df.index:
                continue
            h = held[tk]
            c = df.loc[:d]
            close, low = float(c["Close"].iloc[-1]), float(c["Low"].iloc[-1])
            adv = float((c["Close"] * c["Volume"]).tail(20).mean()) / 1e7
            a = strat.decide(tk, c, h["pos"], avg_daily_value_cr=adv,
                             fundamentals=None, last_exit_cross_date=last_exit_cross.get(tk))
            if "STRANDED HALF" in a.reason:
                h["stranded"] += 1
            if "rope inactive" in a.reason:
                h["rope_inactive"] += 1
            if a.kind == "SCALE_OUT":
                sell_qty = h["pos"].qty if a.fraction >= 1.0 else max(h["pos"].qty // 2, 1)
                h["proceeds"] += net_sell_proceeds(close, sell_qty, cfg.costs, thin=True)
                rem = h["pos"].qty - sell_qty
                upd = advance_rope(h["pos"], a, close, low, cfg.exit)
                if rem <= 0:
                    trades.append(_close_row(tk, h["entry_date"], d, h["pos"], h["buy_cost"],
                                             h["proceeds"], "scaled_out", h["stranded"],
                                             h["rope_inactive"]))
                    last_exit_cross[tk] = h["pos"].entry_cross_date
                    del held[tk]
                else:
                    h["pos"] = replace(h["pos"], qty=rem, **upd)
            else:
                h["pos"] = replace(h["pos"], **advance_rope(h["pos"], a, close, low, cfg.exit))

        free = slots - len(held)
        if free <= 0:
            full_days += 1
            continue
        buys = []
        for tk, df in frames.items():
            if tk in held or d not in df.index:
                continue
            c = df.loc[:d]
            if len(c) < MIN_BARS:
                continue
            close = float(c["Close"].iloc[-1])
            adv = float((c["Close"] * c["Volume"]).tail(20).mean()) / 1e7
            a = strat.decide(tk, c, None, avg_daily_value_cr=adv,
                             fundamentals=(fund or {}).get(tk),
                             last_exit_cross_date=last_exit_cross.get(tk))
            if a.kind == "BUY":
                ext = close / c["Close"].ewm(span=200, adjust=False).mean().iloc[-1] - 1.0
                buys.append((ext, tk, close, c))
        buys.sort(key=lambda t: t[0])
        for _, tk, close, c in buys[:free]:
            qty = int(cfg.budget.per_stock_amount // close)
            if qty < 1:
                continue
            _, cd = fresh_macd_cross(c, within_bars=cfg.entry.fresh_cross_max_age_days)
            held[tk] = {
                "pos": Position(ticker=tk, exchange="NSE", qty=qty, avg_entry=close, tranches=1,
                                entry_cross_date=cd or d.strftime("%d-%b-%Y"), opened_at=d.isoformat(),
                                high_water_mark=close, exit_tranches_remaining=2),
                "buy_cost": net_buy_cost(close, qty, cfg.costs), "proceeds": 0.0,
                "entry_date": d, "stranded": 0, "rope_inactive": 0,
            }

    for tk, h in held.items():
        last_close = float(frames[tk]["Close"].iloc[-1])
        mtm = net_sell_proceeds(last_close, h["pos"].qty, cfg.costs, thin=True)
        reason = "stuck_at_loss" if (h["proceeds"] + mtm - h["buy_cost"]) < 0 else "open_in_profit"
        trades.append(_close_row(tk, h["entry_date"], frames[tk].index[-1], h["pos"], h["buy_cost"],
                                 h["proceeds"] + mtm, reason, h["stranded"], h["rope_inactive"],
                                 still_open=True))
    return trades, full_days, len(days)


def _report(rows: list[dict], skipped: int, extra: list[str]) -> None:
    out = os.path.join(os.path.dirname(__file__), "backtest_smallcap_trades.csv")
    print("\n")
    if not rows:
        print("No trades triggered in the window.")
        print(f"(data missing/short for {skipped} names)")
        return
    res = pd.DataFrame(rows)
    res.to_csv(out, index=False)

    closed = res[~res.still_open]
    open_ = res[res.still_open]
    wins = closed[closed.pnl > 0]
    losses = closed[closed.pnl <= 0]
    stuck = res[res.outcome == "stuck_at_loss"]

    print("=" * 60)
    print(f"Potential trades (entries triggered) : {len(res)}")
    print(f"  closed in window                   : {len(closed)}")
    print(f"  still open at window end           : {len(open_)}")
    print(f"    - of those, stuck at a loss      : {len(stuck)}")
    print(f"    - open but in profit             : {len(open_) - len(stuck)}")
    print("-" * 60)
    print(f"Closed win rate                      : {len(wins)}/{len(closed)}"
          f"  ({100*len(wins)/len(closed):.0f}%)" if len(closed) else "Closed win rate: n/a")
    print(f"Total P&L (closed + MTM open), net   : Rs {res.pnl.sum():,.0f}")
    print(f"  realised (closed only)             : Rs {closed.pnl.sum():,.0f}")
    print(f"  unrealised (open, if sold today)   : Rs {open_.pnl.sum():,.0f}")
    if len(wins):
        print(f"Avg win                             : Rs {wins.pnl.mean():,.0f}  (+{wins.pnl_pct.mean():.1f}%)")
    if len(losses):
        print(f"Avg loss                            : Rs {losses.pnl.mean():,.0f}  ({losses.pnl_pct.mean():.1f}%)")
        worst = losses.loc[losses.pnl.idxmin()]
        print(f"Worst trade                         : {worst.ticker} Rs {worst.pnl:,.0f} ({worst.pnl_pct}%)")
    print(f"Avg hold (days)                      : {res.hold_days.mean():.0f}")
    print(f"Names with a 'stranded half' flag    : {(res.stranded_days > 0).sum()}")
    print(f"Names where rope never activated     : {(res.rope_inactive_days > 0).sum()}")
    print(f"Data missing/short (excluded)        : {skipped} names")
    for line in extra:
        print(line)
    print("=" * 60)
    print(f"per-trade detail -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument("--history", default="2y")
    ap.add_argument("--limit", type=int, default=0, help="only first N tickers (debug)")
    ap.add_argument("--portfolio", action="store_true",
                    help="shared book with the slot cap (else each name in isolation)")
    ap.add_argument("--hard-stop", type=float, default=None,
                    help="hard stop-loss %% below entry, e.g. 2 (default: config = none)")
    ap.add_argument("--total-budget", type=float, default=None,
                    help="override budget.total_budget (sets the slot count)")
    ap.add_argument("--per-stock", type=float, default=None,
                    help="override budget.per_stock_amount (any currency; %%-based costs are scale-free)")
    ap.add_argument("--universe-file", default=None,
                    help="text file, one ticker per line (else the built-in SMALLCAP_TICKERS)")
    ap.add_argument("--fresh-cross-days", type=int, default=None,
                    help="override entry.fresh_cross_max_age_days (MACD cross recency)")
    ap.add_argument("--trail-giveback", type=float, default=None,
                    help="override exit.trail_giveback_pct (rope width)")
    ap.add_argument("--fundamentals-now", action="store_true",
                    help="apply the ROE/D-E/earnings gate using TODAY's yfinance values "
                         "(LOOKAHEAD-BIASED — direction only); market-cap band is widened off")
    args = ap.parse_args()

    cfg = _apply_overrides(load_strategy_config(CFG_PATH), args.hard_stop,
                           args.total_budget, args.per_stock,
                           args.fresh_cross_days, args.trail_giveback)
    if args.fundamentals_now:
        cfg = replace(cfg, fundamentals=replace(cfg.fundamentals, enabled=True),
                      min_market_cap_cr=0.0, max_market_cap_cr=1e15)
    strat = SmallCapDryRun(cfg)
    start = pd.Timestamp.now().normalize() - pd.DateOffset(months=args.months)
    if args.universe_file:
        with open(args.universe_file, encoding="utf-8") as fh:
            tickers = [ln.strip() for ln in fh if ln.strip()]
    else:
        tickers = list(SMALLCAP_TICKERS)
    if args.limit:
        tickers = tickers[: args.limit]

    print(f"Backtest window: {start.date()} -> {datetime.now().date()}  ({len(tickers)} names)")
    print(f"Mode: {'PORTFOLIO (shared book)' if args.portfolio else 'per-ticker (isolated)'}"
          f" | universe={os.path.basename(args.universe_file) if args.universe_file else 'IN_smallcap'}"
          f" | hard_stop={cfg.exit.hard_stop_pct} | slots={cfg.budget.max_names}"
          f" | per_stock={cfg.budget.per_stock_amount:g} | budget={cfg.budget.total_budget:g}")
    print("NO fundamentals gate | survivorship-biased universe | single window\n")

    frames: dict = {}
    skipped = 0
    for i, tk in enumerate(tickers, 1):
        try:
            df = _load_prices(tk, args.history)
        except Exception as e:  # noqa: BLE001
            df = None
            print(f"  [{i}/{len(tickers)}] {tk}: fetch error {e}")
        if df is None:
            skipped += 1
        else:
            frames[tk] = df
        print(f"  [{i}/{len(tickers)}] {tk}: {'ok' if df is not None else 'skip'}", end="\r")

    fund: dict | None = None
    if args.fundamentals_now:
        from strategies.framework.fundamentals import FundamentalsRow, fetch_yf
        fund = {}
        for tk in frames:
            d = fetch_yf(tk)
            fund[tk] = FundamentalsRow(
                ticker=tk, roe_pct=d.get("roe_pct"), debt_equity=d.get("debt_equity"),
                positive_earnings=d.get("positive_earnings"),
                market_cap_cr=d.get("market_cap_cr", 1.0),
                avg_daily_value_cr=d.get("avg_daily_value_cr"), source="yf_now", as_of="now")
        passed = sum(1 for r in fund.values()
                     if r.roe_pct is not None and r.roe_pct >= cfg.fundamentals.min_roe
                     and r.debt_equity is not None and r.debt_equity <= cfg.fundamentals.max_debt_equity
                     and r.positive_earnings)
        print(f"[fundamentals-now] {passed}/{len(fund)} names clear the ROE/D-E/earnings gate "
              f"on today's numbers\n")

    extra: list[str] = []
    if args.portfolio:
        rows, full_days, n_days = _run_portfolio(frames, start, strat, cfg, fund)
        extra.append(f"Days with every slot full            : {full_days}/{n_days}")
    else:
        rows = []
        for tk, df in frames.items():
            rows.extend(_run_one(tk, df, start, strat, cfg, fund))

    _report(rows, skipped, extra)


if __name__ == "__main__":
    main()
