"""Daily Telegram scorecard for the spike logger: did we capture the whole session? Cron on the VPS, Mon-Fri after close:
  10 21 * * 1-5 /opt/voyager/venv/bin/python /opt/voyager/deploy/daily_summary.py >> /opt/voyager/logs/daily_summary.log 2>&1
(21:10 UTC = 16:10 ET while US is on standard time; shift to 20:10 UTC during US daylight time.)
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy.gateway_watch import ET, LOG_CSV, send  # noqa: E402
from research.spike_logger import MAX_LINES  # noqa: E402

EXPECTED_HB = 71          # 04:00-15:55 ET = 715 min / 10 min heartbeat
MIN_HB = 60               # fewer than this = a real gap (Gateway logout, crash, restart)


def max_lines(mine: list[dict]) -> int:
    """Most market-data lines held at any heartbeat today (hb note looks like 'scan=50 lines=17'); 0 if none recorded."""
    seen = [int(m.group(1)) for r in mine if r["kind"] == "hb" for m in [re.search(r"lines=(\d+)", r.get("note") or "")] if m]
    return max(seen, default=0)


def summarize(rows: list[dict], day: str) -> str:
    mine = [r for r in rows if r["ts_et"][:10] == day]
    kinds = Counter(r["kind"] for r in mine)
    stocks = {r["symbol"] for r in mine if r["kind"] == "event"}
    hb, gate, down = kinds["hb"], kinds["gate_fail"], kinds["down"]
    lines = max_lines(mine)
    cap = f" - CAP HIT, new spikes may be unseen" if lines >= MAX_LINES else ""
    ok = hb >= MIN_HB and gate == 0
    verdict = "FULL DAY captured" if ok else "GAPS - tell Claude (Gateway logout? data gate?)"
    return (f"Voyager spike log {day}: {verdict}. Heartbeats {hb}/{EXPECTED_HB}, gate_fail {gate}, down {down}, "
            f"events {kinds['event']} on {len(stocks)} stocks, ticks {kinds['tick']}, lines {lines}/{MAX_LINES}{cap}.")


def main() -> None:
    day = datetime.now(ET).date().isoformat()
    with open(LOG_CSV, newline="", encoding="utf-8") as f:
        msg = summarize(list(csv.DictReader(f)), day)
    send(msg)
    print(msg)


if __name__ == "__main__":
    main()
