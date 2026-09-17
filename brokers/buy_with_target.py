"""ONE-TIME manual test: buys 1 share each of a list of symbols (Market order), waits
for each to actually FILL, then places a GTC Limit sell at TARGET_PCT above the real
fill price for each.

Separate from test_live_order.py (single-symbol, no auto-sell) — this one chains a buy
and a profit-target sell together, and handles several symbols in one run.

Safety design, same spirit as test_live_order.py:
  - Shows the FULL plan for every symbol before sending anything.
  - One CONFIRM gate for the whole batch — these are small, identical-shape actions,
    not worth a separate prompt per symbol.
  - Buys use SMART routing (IBKR's own best-price routing) — avoids the direct-routing
    fee issue hit with IUIT; fine for ordinary US-listed stocks.
  - Waits for an actual "Filled" status (not just PendingSubmit) before computing the
    sell target — the target price depends on the REAL fill price, not the quote.
  - Sell targets are GTC (good-till-cancelled) — they'll sit resting on IBKR's books
    until either they fill or you cancel them by hand. This script does not track or
    cancel them later; that's on you (or future code) to manage.

Usage:
    python -m brokers.buy_with_target
"""
import os

from brokers.ibkr_broker import IBKRBroker, IBKR_PORT

SYMBOLS = [s.strip() for s in os.environ.get("BATCH_SYMBOLS", "HL,PATH,FRSH").split(",") if s.strip()]
QTY = int(os.environ.get("BATCH_QTY", "1"))
TARGET_PCT = float(os.environ.get("BATCH_TARGET_PCT", "15"))  # percent above fill price
EXCHANGE = os.environ.get("BATCH_EXCHANGE", "SMART")
CURRENCY = os.environ.get("BATCH_CURRENCY", "USD")
# One symbol in the batch can use a Limit buy instead of Market, to validate that path
# with a real fill (the earlier IUIT limit order never got the chance — it was cancelled
# by the direct-routing precaution before it could fill). Limit price = current quote +
# this many cents, so it should fill promptly, same as the earlier "$0.01 above ask" advice.
LIMIT_SYMBOL = os.environ.get("BATCH_LIMIT_SYMBOL", "")
LIMIT_BUFFER = float(os.environ.get("BATCH_LIMIT_BUFFER", "0.05"))

_LIVE_PORTS = {4001, 7496}


def main():
    if IBKR_PORT in _LIVE_PORTS:
        print("⚠️  LIVE ACCOUNT — every order below, if confirmed, is REAL money.")
    else:
        print("Paper account port — safe, no real money regardless of what happens below.")

    b = IBKRBroker(client_id=9)
    try:
        b.connect()
        print(f"✅ Connected. Plan: BUY {QTY} share(s) each of {', '.join(SYMBOLS)}, "
              f"then a GTC LIMIT SELL at +{TARGET_PCT}% of each real fill price.\n")

        quotes = {}
        print("--- PLAN ---")
        for sym in SYMBOLS:
            q = b.get_quote(sym, EXCHANGE, CURRENCY)
            price = q.get("last_price") if q else None
            quotes[sym] = price
            if not price:
                print(f"  {sym}: ❌ could not get a price — this symbol will be SKIPPED")
                continue
            target = round(price * (1 + TARGET_PCT / 100), 2)
            if sym == LIMIT_SYMBOL:
                buy_limit = round(price + LIMIT_BUFFER, 2)
                print(f"  {sym}: BUY {QTY} @ LIMIT {buy_limit:.2f} {CURRENCY} (current ~{price:.2f}), "
                      f"then SELL {QTY} @ LIMIT {target:.2f} {CURRENCY} GTC")
            else:
                print(f"  {sym}: BUY {QTY} @ MARKET (~{price:.2f} {CURRENCY}), "
                      f"then SELL {QTY} @ LIMIT {target:.2f} {CURRENCY} GTC")
        print("------------\n")

        tradeable = [s for s in SYMBOLS if quotes.get(s)]
        if not tradeable:
            print("Nothing tradeable — stopping.")
            return

        typed = input('Type CONFIRM (all caps, exactly) to send all buys above, anything else cancels: ')
        if typed.strip() != "CONFIRM":
            print("Cancelled — nothing was sent.")
            return

        results = []
        for sym in tradeable:
            print(f"\n=== {sym} ===")
            if sym == LIMIT_SYMBOL:
                buy_limit = round(quotes[sym] + LIMIT_BUFFER, 2)
                print(f"Sending BUY (limit @ {buy_limit})...")
                trade = b.place_order(sym, EXCHANGE, QTY, "BUY", price=buy_limit, currency=CURRENCY)
            else:
                print("Sending BUY (market)...")
                trade = b.place_order(sym, EXCHANGE, QTY, "BUY", currency=CURRENCY)

            waited = 0.0
            while trade.orderStatus.status not in ("Filled", "Cancelled", "ApiCancelled") and waited < 60:
                b._ib.sleep(1)
                waited += 1
            status = trade.orderStatus.status
            filled_qty = trade.orderStatus.filled
            fill_price = trade.orderStatus.avgFillPrice

            print(f"  Buy status: {status}  filled: {filled_qty}  avg price: {fill_price}")

            # Commission report can arrive a moment after the fill itself — wait briefly
            # rather than grab an empty value.
            commission = None
            for _ in range(5):
                if trade.fills and trade.fills[-1].commissionReport.commission:
                    commission = trade.fills[-1].commissionReport
                    break
                b._ib.sleep(1)
            if commission:
                print(f"  Commission: {commission.commission:.2f} {commission.currency}")
            else:
                print("  Commission: not reported yet (check IBKR's own trade confirmation later)")

            if status != "Filled" or filled_qty < QTY:
                print(f"  ❌ Not fully filled — skipping the sell target for {sym}.")
                if trade.log:
                    for entry in trade.log:
                        print(f"    {entry.time} [{entry.status}] {entry.message}")
                results.append({"symbol": sym, "buy_status": status, "sell_target": None,
                                 "commission": commission.commission if commission else None})
                continue

            target_price = round(fill_price * (1 + TARGET_PCT / 100), 2)
            print(f"  Placing GTC LIMIT SELL at {target_price} {CURRENCY}...")
            sell_trade = b.place_order(sym, EXCHANGE, QTY, "SELL", price=target_price,
                                        currency=CURRENCY, tif="GTC")
            b._ib.sleep(1)
            print(f"  Sell target status: {sell_trade.orderStatus.status}")
            results.append({"symbol": sym, "buy_status": status, "fill_price": fill_price,
                             "sell_target": target_price, "sell_status": sell_trade.orderStatus.status})

        print("\n--- SUMMARY ---")
        for r in results:
            print(f"  {r}")

    except ImportError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        b.disconnect()


if __name__ == "__main__":
    main()
