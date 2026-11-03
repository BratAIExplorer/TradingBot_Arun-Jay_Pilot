"""Read-only symbol lookup — shows every contract IBKR has for a ticker, with its
exchange and currency. Run this BEFORE placing an order on anything that isn't a
plain US stock (ETFs especially can be cross-listed in multiple currencies/exchanges),
so exchange/currency get set correctly instead of guessed.

Usage:
    $env:SYMBOL="IUIT"; python -m brokers.lookup_symbol
"""
import os

from brokers.ibkr_broker import IBKRBroker

SYMBOL = os.environ.get("SYMBOL", "")


def main():
    if not SYMBOL:
        print('Set SYMBOL first, e.g.: $env:SYMBOL="IUIT"; python -m brokers.lookup_symbol')
        return

    b = IBKRBroker()
    try:
        b.connect()
        print(f"Looking up '{SYMBOL}'...\n")
        matches = b._ib.reqMatchingSymbols(SYMBOL)
        if not matches:
            print("No matches found.")
            return
        for m in matches:
            c = m.contract
            print(f"  symbol={c.symbol!r}  secType={c.secType}  exchange={c.primaryExchange!r}  "
                  f"currency={c.currency!r}  description={getattr(m, 'derivativeSecTypes', '')}")
    except ImportError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        b.disconnect()


if __name__ == "__main__":
    main()
