"""ONE-TIME manual script: sells full existing positions in a list of symbols at MARKET.

Same safety spirit as buy_with_target.py — shows the plan, one CONFIRM gate, then sends.

Usage:
    python -m brokers.sell_positions
    SELL_SYMBOLS=AXTI,GSAT python -m brokers.sell_positions
"""
import os

from brokers.ibkr_broker import IBKRBroker, IBKR_PORT

SYMBOLS = [s.strip() for s in os.environ.get("SELL_SYMBOLS", "AXTI,GSAT").split(",") if s.strip()]
EXCHANGE = os.environ.get("SELL_EXCHANGE", "SMART")
CURRENCY = os.environ.get("SELL_CURRENCY", "USD")
# "market" or "limit". Limit sends bid - SELL_LIMIT_BUFFER, so it clears the current bid
# on a thin book instead of resting above it and never filling.
ORDER_MODE = os.environ.get("SELL_ORDER_MODE", "limit").lower()
LIMIT_BUFFER = float(os.environ.get("SELL_LIMIT_BUFFER", "0.02"))

_LIVE_PORTS = {4001, 7496}


def main():
    if IBKR_PORT in _LIVE_PORTS:
        print("⚠️  LIVE ACCOUNT — every order below, if confirmed, is REAL money.")
    else:
        print("Paper account port — safe, no real money regardless of what happens below.")

    b = IBKRBroker(client_id=9)
    try:
        b.connect()
        positions = b.get_positions()

        print("--- PLAN ---")
        to_sell = []
        for sym in SYMBOLS:
            pos = positions.get(sym)
            if not pos or not pos.get("qty"):
                print(f"  {sym}: ❌ no open position found — SKIPPED")
                continue
            qty = pos["qty"]

            if ORDER_MODE == "limit":
                q = b.get_quote(sym, EXCHANGE, CURRENCY)
                bid = q.get("bid") if q else None
                if not bid:
                    print(f"  {sym}: ❌ no live bid available — SKIPPED (rerun with SELL_ORDER_MODE=market if needed)")
                    continue
                limit_price = round(bid - LIMIT_BUFFER, 2)
                print(f"  {sym}: SELL {qty} @ LIMIT {limit_price} (bid {bid} - {LIMIT_BUFFER})")
                to_sell.append((sym, qty, limit_price))
            else:
                print(f"  {sym}: SELL {qty} @ MARKET (closes full position)")
                to_sell.append((sym, qty, None))
        print("------------\n")

        if not to_sell:
            print("Nothing to sell — stopping.")
            return

        typed = input('Type CONFIRM (all caps, exactly) to send all sells above, anything else cancels: ')
        if typed.strip() != "CONFIRM":
            print("Cancelled — nothing was sent.")
            return

        for sym, qty, limit_price in to_sell:
            print(f"\n=== {sym} ===")
            if limit_price:
                print(f"Sending SELL {qty} @ LIMIT {limit_price}...")
                trade = b.place_order(sym, EXCHANGE, qty, "SELL", price=limit_price, currency=CURRENCY)
            else:
                print(f"Sending SELL {qty} (market)...")
                trade = b.place_order(sym, EXCHANGE, qty, "SELL", currency=CURRENCY)

            waited = 0.0
            while trade.orderStatus.status not in ("Filled", "Cancelled", "ApiCancelled") and waited < 60:
                b._ib.sleep(1)
                waited += 1
            print(f"  Status: {trade.orderStatus.status}  filled: {trade.orderStatus.filled}  "
                  f"avg price: {trade.orderStatus.avgFillPrice}")

    except ImportError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        b.disconnect()


if __name__ == "__main__":
    main()
