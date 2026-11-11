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
FIELDS = ["ts_et", "kind", "symbol", "level", "pct", "last", "bid", "ask", "volume", "halted", "mdtype", "note",
          "bid_size", "ask_size"]                           # sizes added 2026-11-02 (amendment): is a $500 fill plausible at the quote?
MAX_LINES = 90                                      # was 40 (filled by 11-02: flagged names hold a line all day). IBKR default ~100; SPY probe + dip engine use a few. Raised 2026-11-03, before Day 1
POLL_SECS = 5
SCAN_SECS = 30                                      # scanner snapshot refresh (a long-lived subscription died silently on a reconnect, 2026-11-02)
log =logging.getLogger("spike_logger")


def crossed_levels(prev_pct: float | None, pct: float, levels=LEVELS) -> list[int]:
    return [lv for lv in levels if pct >= lv and (prev_pct is None or prev_pct < lv)]


def is_realtime(market_data_type, last=None) -> bool:
    """Live type 1 AND a real SPY price. ib_insync's Ticker defaults to type 1, so a failed subscription (IBKR 10089) must not pass."""
    return market_data_type == 1 and last is not None and last == last and last > 0


def heartbeat_due(last_hb: float | None, now: float, secs: int = 600) -> bool:
    return last_hb is None or now - last_hb >= secs


def in_session(now: datetime) -> bool:
    now = now.astimezone(ET)
    return now.weekday() < 5 and OPEN <= now.time() < CLOSE   # ponytail: ignores US holidays (no ticks arrive anyway)


def _num(v):
    return None if v is None or v != v or v == -1 else v        # NaN / IBKR's -1 "no data"


def _size(v):
    n = _num(v)
    return "" if n is None else n                               # 0 is a real size (empty book side), keep it


_header_checked: set[str] = set()


def _ensure_header(path: str) -> None:
    """An existing file with an older header would silently swallow the new columns, so set it aside (data kept) once per run."""
    if path in _header_checked:
        return
    _header_checked.add(path)
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            first = next(csv.reader(f), None)
        if first != FIELDS:
            os.replace(path, f"{path}.pre-{datetime.now(ET).strftime('%Y%m%dT%H%M%S')}")


def write_row(kind: str, symbol: str = "", level="", pct="", last="", bid="", ask="", volume="", halted="",
              mdtype="", note="", bid_size="", ask_size="", path: str = LOG_PATH) -> None:
    _ensure_header(path)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(FIELDS)
        w.writerow([datetime.now(ET).strftime("%Y-%m-%dT%H:%M:%S"), kind, symbol, level, pct, last, bid, ask,
                    volume, halted, mdtype, note, bid_size, ask_size])


def _session(ib) -> None:
    """One connected session. Raises on disconnect; the caller logs the downtime and reconnects."""
    from ib_insync import ScannerSubscription, Stock
    ib.reqMarketDataType(1)
    spy = Stock("SPY", "SMART", "USD")
    probe = ib.reqMktData(spy, "", False, False)
    sub = ScannerSubscription(instrument="STK", locationCode="STK.US.MAJOR", scanCode="TOP_PERC_GAIN",
                              abovePrice=1, belowPrice=20, numberOfRows=50)
    lines, prev, fired, day = {}, {}, set(), ""
    contracts, last_scan, last_hb = {}, 0.0, None
    while True:
        ib.sleep(POLL_SECS)
        if not in_session(datetime.now(ET)):
            continue
        if not is_realtime(probe.marketDataType, _num(probe.last)):   # the data gate
            write_row("gate_fail", mdtype=probe.marketDataType, last=_num(probe.last) or "",
                      note="quotes are not real-time; not logging events")
            ib.cancelMktData(spy)                                 # resubscribe so a newly bought feed is noticed without a restart
            probe = ib.reqMktData(spy, "", False, False)
            ib.sleep(300)
            continue
        if time.time() - last_scan >= SCAN_SECS:
            rows = ib.reqScannerData(sub, [], [])                 # snapshot, not a subscription
            contracts = {r.contractDetails.contract.symbol: r.contractDetails.contract for r in rows}
            last_scan = time.time()
        if heartbeat_due(last_hb, time.time()):                   # positive proof of life, read by deploy/gateway_watch.py
            write_row("hb", last=_num(probe.last) or "", mdtype=probe.marketDataType,
                      note=f"scan={len(contracts)} lines={len(lines)}")
            last_hb = time.time()
        today = datetime.now(ET).date().isoformat()
        if today != day:                                          # new day: release every line, forget yesterday
            for t in lines.values():
                ib.cancelMktData(t.contract)
            lines.clear(), prev.clear(), fired.clear()
            day = today
        for sym in [s for s in lines if s not in contracts and not any(k[:2] == (today, s) for k in fired)]:
            ib.cancelMktData(lines.pop(sym).contract)             # free lines held by names that fell off, unless flagged
        for sym, contract in contracts.items():
            if sym not in lines and len(lines) < MAX_LINES:
                lines[sym] = ib.reqMktData(contract, "", False, False)
        for sym, t in lines.items():
            last, close = _num(t.last), _num(t.close)
            if not last or not close:
                continue
            pct = (last / close - 1) * 100
            fields = dict(symbol=sym, pct=round(pct, 2), last=last, bid=_num(t.bid) or "", ask=_num(t.ask) or "",
                          volume=_num(t.volume) or "", halted=int(bool(t.halted and t.halted > 0)), mdtype=t.marketDataType,
                          bid_size=_size(t.bidSize), ask_size=_size(t.askSize))
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
