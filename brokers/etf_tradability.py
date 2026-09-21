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


OUT = "etf_tradability.csv"
ERROR_WAIT = 0.6  # seconds; ponytail: fixed wait, raise if late errors still slip through
COLUMNS = ["symbol", "exchange", "currency", "status", "note", "name", "isin", "conId", "primary_exchange",
           "category", "subcategory", "min_size", "trading_hours", "commission_1sh", "min_commission",
           "commission_ccy", "warning"]


def _num(v):
    """IBKR sends 1.79e308 for 'no value' (e.g. market closed) — blank it."""
    return "" if isinstance(v, float) and v > 1e300 else v


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
        # tif + account must be set explicitly or whatIf returns an empty list.
        order = MarketOrder("BUY", 1, tif="DAY", account=ib.managedAccounts()[0])
        state = ib.whatIfOrder(c, order)
        # Rejections (e.g. 201 "minimum 2000 USD") can arrive AFTER whatIf returns an OrderState,
        # so wait for them or the row is wrongly OK and the error lands on the next row.
        ib.sleep(ERROR_WAIT)
        info.update({
            "commission_1sh": _num(getattr(state, "commission", "")), "min_commission": _num(getattr(state, "minCommission", "")),
            "commission_ccy": getattr(state, "commissionCurrency", ""), "warning": getattr(state, "warningText", ""),
        })
        # whatIf is answered with an OrderState; restrictions arrive as error events.
        blocking = [e for e in errors if not e.startswith(("2103", "2104", "2105", "2106", "2107", "2108", "2158", "10349"))]
        if blocking:
            note = " | ".join(blocking)
            # 201 "equity with loan..." / "minimum 2000 USD to buy on margin" (e.g. no cash in that currency)
            # = a cash issue, NOT a product restriction.
            return {**info, "status": "NO_FUNDS" if ("EQUITY WITH LOAN" in note.upper() or "MINIMUM OF 2000" in note.upper()) else "BLOCKED", "note": note}
        if hasattr(state, "status"):
            return {**info, "status": "OK", "note": ""}
        return {**info, "status": "UNKNOWN", "note": "empty whatIf"}
    finally:
        ib.errorEvent -= handler


def _split():
    """OUT -> etf_tradable.csv (status OK) + etf_excluded.csv (everything else, with the reason)."""
    with open(OUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for name, keep in (("etf_tradable.csv", [r for r in rows if r["status"] == "OK"]),
                       ("etf_excluded.csv", [r for r in rows if r["status"] != "OK"])):
        with open(name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, restval="")
            w.writeheader()
            w.writerows(keep)
        print(f"{name}: {len(keep)} rows")


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

    # Resume: rows already in the output file are skipped, so a crash loses nothing.
    done = set()
    try:
        with open(OUT, newline="") as f:
            done = {(r["symbol"], r["exchange"], r["currency"]) for r in csv.DictReader(f)}
    except FileNotFoundError:
        pass
    new_file = not done

    b = IBKRBroker(client_id=11)
    try:
        b.connect()
        with open(OUT, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, restval="")
            if new_file:
                w.writeheader()
            for i, r in enumerate(rows, 1):
                sym, exch, cur = r["symbol"].strip(), r.get("exchange", "").strip(), r.get("currency", "USD").strip()
                if (sym, exch, cur) in done:
                    continue
                if not b._ib.isConnected():
                    print("Gateway connection lost — rerun to resume.")
                    return
                try:
                    res = _check(b._ib, sym, exch, cur)
                except Exception as e:
                    res = {"status": "ERROR", "note": str(e)}
                print(f"[{i}/{len(rows)}] {sym} {exch or 'SMART'} {cur}: {res['status']} {res['note']}")
                w.writerow({"symbol": sym, "exchange": exch, "currency": cur, **res})
                f.flush()
                b._ib.sleep(0.05)  # ponytail: crude pacing, IBKR allows ~50 msgs/sec
    finally:
        b.disconnect()
    print(f"Done -> {OUT}")
    _split()


if __name__ == "__main__":
    main()
