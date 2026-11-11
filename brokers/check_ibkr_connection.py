"""Run this once IB Gateway is installed and logged in (paper mode) to confirm the
broker class can actually talk to it. Not part of any test suite — a manual check,
same spirit as the handover doc's "safe manual check" for kickstart.py.

Usage:
    python -m brokers.check_ibkr_connection

Does nothing destructive — connects, prints account funds and open positions, then
disconnects. Never places an order.
"""
from brokers.ibkr_broker import IBKRBroker, IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID


_PAPER_PORTS = {4002, 7497}
_LIVE_PORTS = {4001, 7496}

def main():
    print(f"Connecting to IB Gateway at {IBKR_HOST}:{IBKR_PORT} (clientId={IBKR_CLIENT_ID})...")
    if IBKR_PORT in _LIVE_PORTS:
        print("⚠️  LIVE ACCOUNT PORT — this is your real account, not paper.")
        print("    This script only reads funds/positions — it never calls place_order,")
        print("    so nothing gets bought or sold. Still, know which account you're on.")
    elif IBKR_PORT in _PAPER_PORTS:
        print("Paper account port — safe to use freely, no real money involved.")
    else:
        print(f"⚠️  Port {IBKR_PORT} isn't a recognized default (paper: 4002/7497, live: 4001/7496).")
    b = IBKRBroker()
    try:
        b.connect()
        print("✅ Connected.")
        funds = b.get_funds()
        print(f"USD cash balance: {funds if funds is not None else '(not found in accountSummary — check account has USD)'}")
        positions = b.get_positions()
        print(f"Open positions: {len(positions)}")
        for sym, p in positions.items():
            print(f"  {sym}: {p}")

        if positions:
            test_symbol = next(iter(positions))
            test_exchange = positions[test_symbol].get("exchange") or "SMART"
            print(f"\nFetching a live quote for {test_symbol} ({test_exchange})...")
            quote = b.get_quote(test_symbol, test_exchange)
            print(f"  {quote}")
    except ImportError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Could not connect — is IB Gateway running and logged in? {e}")
    finally:
        b.disconnect()


if __name__ == "__main__":
    main()
