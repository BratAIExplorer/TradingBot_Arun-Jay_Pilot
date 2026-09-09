"""
One log-only cycle of the small-cap strategy.

Ties the pieces together: scan_and_store -> for every candidate not held, run
decide() with the liquidity + fundamentals screens and plan_entry()'s budget
gate, then a LOG-ONLY buy; for every holding, decide() -> advance_rope() ->
persist, then a LOG-ONLY scale-out. Writes a one-line status file.

Nothing here sends a real order: that is the broker's job and only when
orders_enabled is true with a live session. `trades.db` is never opened.
"""
from __future__ import annotations

from datetime import datetime

from strategies.framework.base import Position
from strategies.framework.sizing import plan_entry
from strategies.scan_and_store import scan_and_store
from strategies.small_cap_dryrun import advance_rope


def _row_to_position(r: dict) -> Position:
    return Position(
        ticker=r["ticker"], exchange=r["exchange"], qty=r["qty"], avg_entry=r["avg_entry"],
        tranches=r.get("tranches", 1), entry_cross_date=r.get("entry_cross_date", ""),
        opened_at=r.get("opened_at", ""), first_red_date=r.get("first_red_date"),
        high_water_mark=r.get("high_water_mark"), trailing_floor=r.get("trailing_floor"),
        exit_tranches_remaining=r.get("exit_tranches_remaining", 2),
        locked_half2_price=r.get("locked_half2_price"), stranded=bool(r.get("stranded", 0)),
        mae_pct=r.get("mae_pct"), last_quote_date=r.get("last_quote_date"),
    )


def run_cycle(strategy, store, broker, *, account_value, candle_provider,
              universe_scanner=None, fundamentals=None, status_path=None) -> dict:
    name = strategy.name
    cfg = strategy.cfg
    fundamentals = fundamentals or {}
    now = datetime.now()

    ranked = scan_and_store(strategy, store, scanner=universe_scanner)

    held = {r["ticker"]: r for r in store.open_positions(name)}
    deployed = sum(r["qty"] * r["avg_entry"] for r in held.values())
    open_names = len(held)
    bought = sold = 0

    # --- entries ---------------------------------------------------------- #
    for cand in ranked:
        tkr = cand["ticker"]
        if tkr in held:
            continue
        candles = candle_provider(tkr)
        if candles is None or len(candles) < 30:
            continue
        row = fundamentals.get(tkr)
        adv = getattr(row, "avg_daily_value_cr", None) or cand.get("extra", {}).get("avg_daily_value_cr")
        act = strategy.decide(tkr, candles, None, fundamentals=row, avg_daily_value_cr=adv)
        if act.kind != "BUY":
            continue
        price = float(candles["Close"].iloc[-1])
        plan = plan_entry(account_value=account_value, price=price, position=None, cfg=cfg,
                          open_names=open_names, deployed=deployed)
        if not plan.allowed:
            continue
        fill = broker.place_order(tkr, cand.get("exchange", "NSE"), "BUY", plan.qty, price)
        store.record_fill(name, tkr, cand.get("exchange", "NSE"), "BUY", plan.qty,
                          fill["fill_price"], act.reason, fill["orders_enabled"],
                          order_value=fill["order_value"], qty_after=plan.qty,
                          fee_estimate=fill.get("fee_estimate"))
        store.upsert_position(name, tkr, cand.get("exchange", "NSE"), plan.qty,
                              fill["fill_price"], 1, cand.get("extra", {}).get("macd_cross_date", ""),
                              now.isoformat())
        deployed += fill["order_value"]
        open_names += 1
        bought += 1

    # --- exits ---------------------------------------------------------- #
    for tkr, r in held.items():
        candles = candle_provider(tkr)
        if candles is None or len(candles) < 2:
            continue
        pos = _row_to_position(r)
        close = float(candles["Close"].iloc[-1])
        low = float(candles["Low"].iloc[-1])
        act = strategy.decide(tkr, candles, pos)
        upd = advance_rope(pos, act, close, low, cfg.exit)
        store.update_position_metrics(name, tkr, **upd)
        if act.kind != "SCALE_OUT":
            continue
        qty_sell = pos.qty if act.fraction >= 1.0 else max(1, pos.qty // 2)
        fill = broker.place_order(tkr, r["exchange"], "SELL", qty_sell, close)
        realised = round((fill["fill_price"] - pos.avg_entry) * qty_sell, 2)
        qty_after = pos.qty - qty_sell
        store.record_fill(name, tkr, r["exchange"], "SELL", qty_sell, fill["fill_price"],
                          act.reason, fill["orders_enabled"], order_value=fill["order_value"],
                          qty_after=qty_after, realised_pnl=realised,
                          fee_estimate=fill.get("fee_estimate"))
        if qty_after <= 0:
            store.close_position(name, tkr, now.isoformat())
        else:
            store.upsert_position(name, tkr, r["exchange"], qty_after, pos.avg_entry, 1,
                                  r.get("entry_cross_date", ""), r.get("opened_at", now.isoformat()))
            store.update_position_metrics(name, tkr, exit_tranches_remaining=upd.get(
                "exit_tranches_remaining", pos.exit_tranches_remaining))
        sold += 1

    still_held = store.open_positions(name)
    deployed_now = sum(p["qty"] * p["avg_entry"] for p in still_held)
    store.save_snapshot(name, now.strftime("%Y-%m-%d"), account_value, deployed_now,
                        account_value - deployed_now, 0, 0, 0)

    summary = {"scanned": len(ranked), "bought": bought, "sold": sold,
               "held": len(still_held), "deployed": round(deployed_now, 2),
               "budget": cfg.budget.total_budget}
    if status_path:
        with open(status_path, "w", encoding="utf-8") as fh:
            fh.write(f"{now.isoformat()}  scanned={summary['scanned']} bought={bought} "
                     f"sold={sold} held={summary['held']} "
                     f"deployed=Rs {summary['deployed']:g} / Rs {cfg.budget.total_budget:g} "
                     f"(orders_enabled={cfg.orders_enabled})\n")
    return summary
