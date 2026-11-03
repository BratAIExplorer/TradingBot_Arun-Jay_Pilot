"""Adds catastrophic-stop and (conditionally) regular stop-loss protection to existing
IBKR positions, alongside their current profit-target sell — mirrors risk_manager.py's
mStock logic (catastrophic always fires; regular stop-loss is skippable via a
never_sell_at_loss flag) using resting IBKR OCA-linked orders instead of a polling loop,
since no continuous IBKR engine exists yet (unlike kickstart.py's run_cycle).

Settings reused as-is from settings.json (same values mStock's RiskManager reads):
  risk_controls.default_stop_loss_pct   (currently 5)
  risk_controls.catastrophic_stop_pct   (currently 20)
  risk.never_sell_at_loss               (currently true — this SUPPRESSES the regular
                                          stop-loss leg; only catastrophic gets placed)

For each symbol:
  1. Cancels the existing lone profit-target GTC sell (if one is found resting).
  2. Places a fresh OCA-linked group: profit-target LMT (always) + catastrophic STP
     (always) + regular stop-loss STP (only if never_sell_at_loss is false).
  3. Filling any one leg auto-cancels the others (ocaType=1).

Known limitation, stated plainly: once placed, these are static resting orders. If
never_sell_at_loss changes in settings.json later, it does NOT retroactively add/remove
a resting order for positions already bracketed — re-run this script to pick up a
changed setting.

Usage:
    python -m brokers.add_protective_bracket
"""
import json
import os

from brokers.ibkr_broker import IBKRBroker, IBKR_PORT

SYMBOLS = [s.strip() for s in os.environ.get("BRACKET_SYMBOLS", "HL,PATH,FRSH").split(",") if s.strip()]
PROFIT_TARGET_PCT = float(os.environ.get("BRACKET_PROFIT_TARGET_PCT", "15"))  # matches the GTC sells already placed
EXCHANGE = os.environ.get("BRACKET_EXCHANGE", "SMART")
CURRENCY = os.environ.get("BRACKET_CURRENCY", "USD")

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")
_LIVE_PORTS = {4001, 7496}


def _load_risk_settings():
    with open(_SETTINGS_PATH, encoding="utf-8") as fh:
        s = json.load(fh)
    return {
        "stop_loss_pct": s.get("risk_controls", {}).get("default_stop_loss_pct", 5),
        "catastrophic_stop_pct": s.get("risk_controls", {}).get("catastrophic_stop_pct", 20),
        "never_sell_at_loss": s.get("risk", {}).get("never_sell_at_loss", False),
    }


def main():
    risk = _load_risk_settings()
    print(f"Risk settings (from settings.json): stop_loss={risk['stop_loss_pct']}%, "
          f"catastrophic={risk['catastrophic_stop_pct']}%, "
          f"never_sell_at_loss={risk['never_sell_at_loss']}")
    if risk["never_sell_at_loss"]:
        print("  -> never_sell_at_loss is TRUE: regular stop-loss will be SKIPPED. "
              "Only the catastrophic floor will be placed.")
    print()

    if IBKR_PORT in _LIVE_PORTS:
        print("⚠️  LIVE ACCOUNT — every order below, if confirmed, is REAL money.")
    else:
        print("Paper account port — safe, no real money regardless of what happens below.")

    b = IBKRBroker(client_id=9)
    try:
        b.connect()
        portfolio = b.get_portfolio()

        print("\n--- PLAN ---")
        plans = {}
        for sym in SYMBOLS:
            pos = portfolio.get(sym)
            if not pos:
                print(f"  {sym}: ❌ not found in portfolio — skipping")
                continue
            avg_cost = pos["avg_cost"]
            profit_price = round(avg_cost * (1 + PROFIT_TARGET_PCT / 100), 2)
            catastrophic_price = round(avg_cost * (1 - risk["catastrophic_stop_pct"] / 100), 2)
            stop_loss_price = None if risk["never_sell_at_loss"] else \
                round(avg_cost * (1 - risk["stop_loss_pct"] / 100), 2)
            plans[sym] = {
                "qty": pos["qty"], "avg_cost": avg_cost, "profit_price": profit_price,
                "catastrophic_price": catastrophic_price, "stop_loss_price": stop_loss_price,
            }
            print(f"  {sym}: avg cost {avg_cost:.2f} {CURRENCY}, qty {pos['qty']}")
            print(f"    -> cancel existing profit-target order (if any resting)")
            print(f"    -> PLACE (OCA group): profit-target LMT {profit_price}, "
                  f"catastrophic STP {catastrophic_price}"
                  + (f", stop-loss STP {stop_loss_price}" if stop_loss_price else " (no stop-loss leg — never_sell_at_loss)"))

        if not plans:
            print("Nothing to do — no matching positions found.")
            return

        typed = input('\nType CONFIRM (all caps, exactly) to cancel existing orders and place the brackets above, anything else cancels: ')
        if typed.strip() != "CONFIRM":
            print("Cancelled — nothing was sent.")
            return

        # Cancel existing resting sell orders for these symbols first
        b._ib.reqOpenOrders()
        b._ib.sleep(2)
        for t in b._ib.openTrades():
            if t.contract.symbol in plans and t.order.action == "SELL":
                print(f"Cancelling existing order: {t.contract.symbol} {t.order.orderType} @ "
                      f"{getattr(t.order, 'lmtPrice', getattr(t.order, 'auxPrice', '?'))}")
                b._ib.cancelOrder(t.order)
        b._ib.sleep(2)

        for sym, p in plans.items():
            oca = f"bracket_{sym}_{IBKR_PORT}"
            print(f"\n=== {sym}: placing OCA bracket ===")
            legs = []
            t1 = b.place_order(sym, EXCHANGE, p["qty"], "SELL", price=p["profit_price"],
                                currency=CURRENCY, tif="GTC", oca_group=oca)
            legs.append(("profit-target LMT", p["profit_price"], t1))
            t2 = b.place_order(sym, EXCHANGE, p["qty"], "SELL", order_type="STP",
                                stop_price=p["catastrophic_price"], currency=CURRENCY,
                                tif="GTC", oca_group=oca)
            legs.append(("catastrophic STP", p["catastrophic_price"], t2))
            if p["stop_loss_price"]:
                t3 = b.place_order(sym, EXCHANGE, p["qty"], "SELL", order_type="STP",
                                    stop_price=p["stop_loss_price"], currency=CURRENCY,
                                    tif="GTC", oca_group=oca)
                legs.append(("stop-loss STP", p["stop_loss_price"], t3))

            b._ib.sleep(2)
            for name, price, trade in legs:
                print(f"  {name} @ {price}: status={trade.orderStatus.status}")

    except ImportError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        b.disconnect()


if __name__ == "__main__":
    main()
