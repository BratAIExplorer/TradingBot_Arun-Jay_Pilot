"""READ-ONLY: checks which ETFs from a list your IBKR account can actually buy.

IBKR's API has no "list all ETFs" call (scanner caps at 50 rows). So step 1 is manual:
export the ETF table from IBKR's Product Listings page (interactivebrokers.com >
Trading > Products > Exchange Listings > ETFs) into a CSV with columns:
    symbol,exchange,currency        (exchange may be blank -> SMART)
Step 2 is this script: for each row it confirms the contract is an ETF and sends a
whatIf BUY of 1 share. whatIf never places an order — IBKR just answers "would this
be accepted?" or returns the restriction (PRIIPs/KID, no permission, etc.).

Usage:
    python -m brokers.etf_tradability etfs.csv            # writes etf_tradability.csv
"""
import csv
import sys

from brokers.ibkr_broker import IBKRBroker


COLUMNS = ["symbol", "exchange", "currency", "status", "note", "name", "isin", "conId", "primary_exchange",
           "category", "subcategory", "min_size", "trading_hours", "commission_1sh", "min_commission",
           "commission_ccy", "warning"]


def _check(ib, sym, exch, cur):
    from ib_insync import Stock, MarketOrder
    errors = []
    handler = lambda reqId, code, msg, contract: errors.append(f"{code}: {msg}")
    ib.errorEvent += handler
    try:
        details = ib.reqContractDetails(Stock(sym, exch or "SMART", cur))
        if not details:
            return {"status": "NOT_FOUND", "note": "no contract details"}
        d = details[0]
        c = d.contract
        info = {
            "name": d.longName, "isin": next((x.value for x in d.secIdList or [] if x.tag == "ISIN"), ""),
            "conId": c.conId, "primary_exchange": c.primaryExchange,
            "category": d.category, "subcategory": d.subcategory,
            "min_size": d.minSize, "trading_hours": (d.liquidHours or "")[:60],
        }
        if d.stockType != "ETF":
            return {**info, "status": "NOT_ETF", "note": d.stockType}
        state = ib.whatIfOrder(c, MarketOrder("BUY", 1))
        info.update({
            "commission_1sh": getattr(state, "commission", ""), "min_commission": getattr(state, "minCommission", ""),
            "commission_ccy": getattr(state, "commissionCurrency", ""), "warning": getattr(state, "warningText", ""),
        })
        # whatIf is answered with an OrderState; restrictions arrive as error events.
        blocking = [e for e in errors if not e.startswith(("2104", "2106", "2158"))]
        if blocking:
            return {**info, "status": "BLOCKED", "note": " | ".join(blocking)}
        if state and state.initMarginChange != "":
            return {**info, "status": "OK", "note": ""}
        return {**info, "status": "UNKNOWN", "note": "empty whatIf"}
    finally:
        ib.errorEvent -= handler


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m brokers.etf_tradability etfs.csv")
        return
    try:
        with open(sys.argv[1], newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"{sys.argv[1]} not found. Create it with header: symbol,exchange,currency")
        return

    b = IBKRBroker(client_id=11)
    out = []
    try:
        b.connect()
        for i, r in enumerate(rows, 1):
            sym, exch, cur = r["symbol"].strip(), r.get("exchange", "").strip(), r.get("currency", "USD").strip()
            try:
                res = _check(b._ib, sym, exch, cur)
            except Exception as e:
                res = {"status": "ERROR", "note": str(e)}
            print(f"[{i}/{len(rows)}] {sym} {exch or 'SMART'} {cur}: {res['status']} {res['note']}")
            out.append({"symbol": sym, "exchange": exch, "currency": cur, **res})
            b._ib.sleep(0.05)  # ponytail: crude pacing, IBKR allows ~50 msgs/sec
    finally:
        b.disconnect()

    with open("etf_tradability.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, restval="")
        w.writeheader()
        w.writerows(out)
    print(f"\nOK: {sum(o['status'] == 'OK' for o in out)} / {len(out)}  -> etf_tradability.csv")


if __name__ == "__main__":
    main()
