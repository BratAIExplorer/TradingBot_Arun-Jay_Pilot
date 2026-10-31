"""Log-only intraday spike logger (IBKR scanner -> CSV). NEVER places orders. Rules: Documentation/SPIKE_TEST_RULES.md

Refuses to log events unless quotes are real-time (marketDataType 1) -- delayed prices would be fiction.
Run:  IBKR_READONLY=1 IBKR_PORT=4001 IBKR_CLIENT_ID=11 python -m research.spike_logger
"""
from __future__ import annotations

import csv
import logging
import os
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
LEVELS = (30, 50, 100)
OPEN, CLOSE = dtime(4, 0), dtime(15, 55)            # premarket through the forced-exit time
LOG_PATH = os.environ.get("SPIKE_LOG", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spike_log.csv"))
FIELDS = ["ts_et", "kind", "symbol", "level", "pct", "last", "bid", "ask", "volume", "halted", "mdtype", "note"]
MAX_LINES = 40                                      # ponytail: IBKR default is ~100 market-data lines; verify before raising
POLL_SECS = 5
log = logging.getLogger("spike_logger")


def crossed_levels(prev_pct: float | None, pct: float, levels=LEVELS) -> list[int]:
    return [lv for lv in levels if pct >= lv and (prev_pct is None or prev_pct < lv)]


def is_realtime(market_data_type) -> bool:
    return market_data_type == 1


def in_session(now: datetime) -> bool:
    now = now.astimezone(ET)
    return now.weekday() < 5 and OPEN <= now.time() < CLOSE   # ponytail: ignores US holidays (no ticks arrive anyway)


def _num(v):
    return None if v is None or v != v or v == -1 else v        # NaN / IBKR's -1 "no data"


def write_row(kind: str, symbol: str = "", level="", pct="", last="", bid="", ask="", volume="", halted="",
              mdtype="", note="", path: str = LOG_PATH) -> None:
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(FIELDS)
        w.writerow([datetime.now(ET).strftime("%Y-%m-%dT%H:%M:%S"), kind, symbol, level, pct, last, bid, ask,
                    volume, halted, mdtype, note])


def _session(ib) -> None:
    """One connected session. Raises on disconnect; the caller logs the downtime and reconnects."""
    from ib_insync import ScannerSubscription, Stock
    ib.reqMarketDataType(1)
    probe = ib.reqMktData(Stock("SPY", "SMART", "USD"), "", False, False)
    scan = ib.reqScannerSubscription(ScannerSubscription(instrument="STK", locationCode="STK.US.MAJOR",
                                                         scanCode="TOP_PERC_GAIN", abovePrice=1, belowPrice=20,
                                                         numberOfRows=50))
    lines, prev, fired, day = {}, {}, set(), ""
    while True:
        ib.sleep(POLL_SECS)
        if not in_session(datetime.now(ET)):
            continue
        if not is_realtime(probe.marketDataType):                # the data gate
            write_row("gate_fail", mdtype=probe.marketDataType, note="quotes are not real-time; not logging events")
            ib.sleep(300)
            continue
        today = datetime.now(ET).date().isoformat()
        if today != day:                                          # new day: release every line, forget yesterday
            for t in lines.values():
                ib.cancelMktData(t.contract)
            lines.clear(), prev.clear(), fired.clear()
            day = today
        on_scan = {row.contractDetails.contract.symbol for row in scan}
        for sym in [s for s in lines if s not in on_scan and not any(k[:2] == (today, s) for k in fired)]:
            ib.cancelMktData(lines.pop(sym).contract)             # free lines held by names that fell off, unless flagged
        for row in scan:
            sym = row.contractDetails.contract.symbol
            if sym not in lines and len(lines) < MAX_LINES:
                lines[sym] = ib.reqMktData(row.contractDetails.contract, "", False, False)
        for sym, t in lines.items():
            last, close = _num(t.last), _num(t.close)
            if not last or not close:
                continue
            pct = (last / close - 1) * 100
            fields = dict(symbol=sym, pct=round(pct, 2), last=last, bid=_num(t.bid) or "", ask=_num(t.ask) or "",
                          volume=_num(t.volume) or "", halted=int(bool(t.halted and t.halted > 0)), mdtype=t.marketDataType)
            for lv in crossed_levels(prev.get(sym), pct):
                if (today, sym, lv) not in fired:
                    fired.add((today, sym, lv))
                    write_row("event", level=lv, **fields)
            if any(k[:2] == (today, sym) for k in fired):        # keep ticking any stock flagged today
                write_row("tick", **fields)
            prev[sym] = pct


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    from ib_insync import IB
    host, port = os.environ.get("IBKR_HOST", "127.0.0.1"), int(os.environ.get("IBKR_PORT", "4001"))
    cid = int(os.environ.get("IBKR_CLIENT_ID", "11"))
    while True:
        ib = IB()
        try:
            ib.connect(host, port, clientId=cid, readonly=True)  # readonly=True: this process can never send an order
            write_row("up", note=f"connected {host}:{port} clientId={cid}")
            _session(ib)
        except Exception as exc:                                  # noqa: BLE001 -- log the gap, then reconnect
            log.warning("session ended: %s", exc)
            write_row("down", note=str(exc)[:200])
        finally:
            if ib.isConnected():
                ib.disconnect()
        time.sleep(30)


if __name__ == "__main__":
    main()
