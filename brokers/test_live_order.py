"""ONE-TIME manual test: places a single small real order on your live IBKR account.

This is deliberately separate from check_ibkr_connection.py (which never places
orders) so there's no chance of running this by accident.

Requires Read-Only API to be OFF in Gateway (you already did this).

Safety design:
  - You set SYMBOL and BUDGET_USD below, by hand, before running.
  - The script fetches a real quote, computes quantity, and prints the FULL order
    details — then STOPS and waits for you to type CONFIRM at the keyboard.
    Nothing is sent to IBKR until you type that.
  - Whole shares only (no fractional-share complexity) — if BUDGET_USD can't buy at
    least 1 share, it stops and tells you, rather than guessing.
  - Market order — fills at whatever the current price is, same as any market order.

Usage:
    python -m brokers.test_live_order
"""
import os
import math

from brokers.ibkr_broker import IBKRBroker, IBKR_PORT

# --- SET THESE BEFORE RUNNING ---
SYMBOL = os.environ.get("TEST_ORDER_SYMBOL", "")  # e.g. "SPY" — set via env var, not hardcoded here
EXCHANGE = os.environ.get("TEST_ORDER_EXCHANGE", "SMART")
CURRENCY = os.environ.get("TEST_ORDER_CURRENCY", "USD")
BUDGET = float(os.environ.get("TEST_ORDER_BUDGET", "50"))  # in CURRENCY, not necessarily USD
# Limit price, in CURRENCY. Unset/0 = Market order (fills instantly, price unpredictable).
# Set this for a lump-sum buy — caps what you'll actually pay, at the cost of maybe not
# filling instantly if the market moves away from your price.
LIMIT_PRICE = float(os.environ.get("TEST_ORDER_LIMIT_PRICE", "0"))
# ---------------------------------

_LIVE_PORTS = {4001, 7496}


def main():
    if not SYMBOL:
        print("❌ Set TEST_ORDER_SYMBOL first, e.g.:")
        print('   $env:TEST_ORDER_SYMBOL="SPY"; python -m brokers.test_live_order')
        return

    if IBKR_PORT in _LIVE_PORTS:
        print("⚠️  LIVE ACCOUNT — this order, if confirmed, is REAL. Real money.")
    else:
        print("Paper account port — safe, no real money regardless of what happens below.")

    b = IBKRBroker()
    try:
        b.connect()
        print(f"✅ Connected. Fetching a delayed quote for {SYMBOL} ({EXCHANGE}, {CURRENCY})...")
        quote = b.get_quote(SYMBOL, EXCHANGE, CURRENCY)
        last_price = quote.get("last_price") if quote else None
        if not last_price:
            print(f"❌ Could not get a price for {SYMBOL} — stopping, no order placed. Quote: {quote}")
            return

        is_limit = LIMIT_PRICE > 0
        # Size against the limit price when there is one — that's the actual worst-case
        # cost. Sizing against last_price for a limit order could understate cost if the
        # market's moved, or leave money on the table if it hasn't.
        sizing_price = LIMIT_PRICE if is_limit else last_price

        qty = math.floor(BUDGET / sizing_price)
        if qty < 1:
            print(f"❌ {BUDGET} {CURRENCY} isn't enough for 1 share of {SYMBOL} at ~{sizing_price:.2f} {CURRENCY}. Stopping — no order placed.")
            return

        est_cost = qty * sizing_price
        print("\n--- ORDER TO BE PLACED ---")
        print(f"  Symbol:        {SYMBOL} ({EXCHANGE}, {CURRENCY})")
        print(f"  Side:          BUY")
        print(f"  Quantity:      {qty} whole share(s)")
        print(f"  Current price: {last_price:.2f} {CURRENCY} (delayed quote)")
        if is_limit:
            print(f"  Order type:    LIMIT at {LIMIT_PRICE:.2f} {CURRENCY} (will NOT pay more than this)")
        else:
            print(f"  Order type:    MARKET (fills at current price, not exactly {last_price:.2f} {CURRENCY})")
        print(f"  Max cost:      ~{est_cost:.2f} {CURRENCY}  (budget was {BUDGET} {CURRENCY})")
        print("---------------------------\n")

        typed = input('Type CONFIRM (all caps, exactly) to actually send this order, anything else cancels: ')
        if typed.strip() != "CONFIRM":
            print("Cancelled — nothing was sent.")
            return

        print("Sending order...")
        trade = b.place_order(SYMBOL, EXCHANGE, qty, "BUY", price=LIMIT_PRICE, currency=CURRENCY)

        # Do NOT disconnect immediately — an order that hasn't been fully acknowledged
        # downstream can be discarded if the API connection that placed it drops too
        # soon. Wait here until the status moves past PendingSubmit/Submitted, or a
        # generous timeout, whichever comes first.
        print("Waiting for a real status update before disconnecting...")
        waited = 0.0
        while trade.orderStatus.status in ("PendingSubmit", "PreSubmitted") and waited < 30:
            b._ib.sleep(1)
            waited += 1
            print(f"  ...status: {trade.orderStatus.status} ({waited:.0f}s)")

        print(f"\nFinal status: {trade.orderStatus.status}")
        print(f"Filled: {trade.orderStatus.filled}  Avg fill price: {trade.orderStatus.avgFillPrice}")
        if trade.log:
            print("Order log:")
            for entry in trade.log:
                print(f"  {entry.time} [{entry.status}] {entry.message}")

    except ImportError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        b.disconnect()


if __name__ == "__main__":
    main()
