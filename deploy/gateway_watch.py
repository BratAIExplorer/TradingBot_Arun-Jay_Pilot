"""Telegram alert when the Voyager Gateway (port 4001) is down, or the spike logger's real-time data gate fails.

Read-only: connects to nothing but the local port and Telegram. Run from cron every 5 minutes on the VPS:
  */5 * * * * /opt/voyager/venv/bin/python /opt/voyager/deploy/gateway_watch.py >> /opt/voyager/logs/gateway_watch.log 2>&1
Bot token + chat id live in ALERT_ENV (default /opt/voyager/alert.env, chmod 600), written once by deploy/setup_alert.py.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, time as dtime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.spike_logger import ET, in_session  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.environ.get("ALERT_ENV", "/opt/voyager/alert.env")
STATE = os.environ.get("ALERT_STATE", os.path.join(ROOT, "logs", "gateway_watch.json"))
LOG_CSV = os.environ.get("SPIKE_LOG", os.path.join(ROOT, "spike_log.csv"))
PORT = int(os.environ.get("IBKR_PORT", "4001"))
GATEWAY_PARK = os.path.join(os.path.dirname(STATE), "gateway_parked")  # touch while the Gateway is deliberately stopped (e.g. user needs the IBKR login); mutes all alerts
PARK_FLAG = os.path.join(os.path.dirname(STATE), "spike_parked")  # touch this when the spike logger is deliberately stopped; mutes the silent-logger alert
REPEAT_SECS = 7200  # re-alert a persistent outage every 2 hours
SKIP_LIMIT = 8  # consecutive failed engine cycles (15 min each = 2 h) before alerting
ENGINE_STATE = os.environ.get("ENGINE_STATE", os.path.join(ROOT, "voyager_engine_state.json"))


def decide(in_sess: bool, port_open: bool, gate_failing: bool, state: dict, now: float, today: str, silent: bool = False):
    """Pure: returns (messages, new_state). Alerts only during the US session so weekends stay quiet."""
    msgs, s = [], dict(state)
    if port_open and s.get("down_alert"):
        msgs.append("Voyager Gateway is back up.")
        s["down_alert"] = 0
    if not port_open and in_sess and now - s.get("down_alert", 0) >= REPEAT_SECS:
        msgs.append("Voyager Gateway is DOWN (port 4001 closed): the spike logger is blind. "
                    "Likely logged out - approve the IBKR phone 2FA / tell Claude.")
        s["down_alert"] = now
    if port_open and in_sess and gate_failing and s.get("gate_day") != today:
        msgs.append("Spike logger data gate FAILED: quotes are not real-time, so nothing is being logged. "
                    "The 3-week clock has not started.")
        s["gate_day"] = today
    if port_open and in_sess and silent and s.get("silent_day") != today:
        msgs.append("Spike logger has written no rows for 30+ minutes while the market is open (Gateway is up): "
                    "it is not collecting data. Tell Claude.")
        s["silent_day"] = today
    return msgs, s


def engine_skips(eng: dict | None, state: dict, limit: int = SKIP_LIMIT):
    """Pure, any hour: counts consecutive failed engine cycles (each new engine `ts` counted once).
    One alert at `limit` skips in a row, one message when a cycle succeeds again. Stopped engine = quiet."""
    s, msgs = dict(state), []
    if not eng or not eng.get("running"):
        return msgs, s
    if eng.get("ts") != s.get("skip_ts"):
        s["skip_ts"] = eng.get("ts")
        s["skips"] = s.get("skips", 0) + 1 if eng.get("error") else 0
    if s.get("skips", 0) >= limit and not s.get("skip_alert"):
        msgs.append(f"Voyager dip engine has skipped {s['skips']} cycles in a row (last error: {str(eng.get('error'))[:120]}). "
                    "Usually the Gateway is logged out. Orders are not affected.")
        s["skip_alert"] = 1
    if not s.get("skips") and s.get("skip_alert"):
        msgs.append("Voyager dip engine is running cycles again.")
        s["skip_alert"] = 0
    return msgs, s


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return True
    except OSError:
        return False


def gate_failing(path: str, now_et: datetime, window_min: int = 15) -> bool:
    """True if the newest spike_log row (within window_min) is a gate_fail."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 8192))
            last = f.read().decode("utf-8", "replace").strip().splitlines()[-1].split(",")
        ts = datetime.fromisoformat(last[0]).replace(tzinfo=ET)
    except (OSError, IndexError, ValueError):
        return False
    return last[1] == "gate_fail" and now_et - ts <= timedelta(minutes=window_min)


def logger_silent(path: str, now_et: datetime, minutes: int = 30) -> bool:
    """True if no proof-of-life row (anything but 'down': hb, gate_fail, event, tick, up) in the last `minutes`.
    Skips the first 30 min of the session, when the newest row is still yesterday's."""
    if now_et.time() < dtime(4, 30):
        return False
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 65536))
            rows = [l.split(",") for l in f.read().decode("utf-8", "replace").strip().splitlines()]
        alive = [r for r in rows if len(r) > 1 and r[1] != "down"]
        return not alive or now_et - datetime.fromisoformat(alive[-1][0]).replace(tzinfo=ET) > timedelta(minutes=minutes)
    except (OSError, ValueError):
        return True


def _env(path: str) -> dict:
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.strip().split("=", 1)
            out[k] = v.strip().strip("'\"")
    return out


def send(text: str) -> None:
    env = _env(ENV_FILE)
    token, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise SystemExit(f"no TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in {ENV_FILE}")
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data), timeout=15).read()


def main() -> None:
    now = datetime.now(ET)
    try:
        state = json.load(open(STATE))
    except (OSError, ValueError):
        state = {}
    msgs, new = decide(in_session(now) and not os.path.exists(GATEWAY_PARK), port_open(PORT), gate_failing(LOG_CSV, now), state, time.time(),
                       now.date().isoformat(), logger_silent(LOG_CSV, now) and not os.path.exists(PARK_FLAG))
    try:
        eng = json.load(open(ENGINE_STATE))
    except (OSError, ValueError):
        eng = None
    more, new = engine_skips(eng, new)
    msgs += more
    for m in msgs:
        send(m)  # raises on failure -> state not saved -> retried next run
    if new != state:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(new, open(STATE, "w"))
    print(now.strftime("%F %T"), "sent" if msgs else "ok", msgs)


if __name__ == "__main__":
    main()
