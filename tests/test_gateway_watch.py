from datetime import datetime
from zoneinfo import ZoneInfo

from deploy.gateway_watch import REPEAT_SECS, decide, engine_skips, logger_silent

ET = ZoneInfo("America/New_York")

T = 1_000_000.0


def test_down_in_session_alerts_once_then_repeats_after_two_hours():
    msgs, s = decide(True, False, False, {}, T, "d")
    assert len(msgs) == 1 and "DOWN" in msgs[0]
    assert decide(True, False, False, s, T + 60, "d")[0] == []
    assert len(decide(True, False, False, s, T + REPEAT_SECS, "d")[0]) == 1


def test_down_outside_session_is_quiet():
    assert decide(False, False, False, {}, T, "d")[0] == []


def test_down_after_hours_on_a_weekday_alerts_once_per_outage_not_every_two_hours():
    msgs, s = decide(False, False, False, {}, T, "d", weekday_ok=True)
    assert len(msgs) == 1 and "DOWN" in msgs[0]
    assert decide(False, False, False, s, T + 3 * REPEAT_SECS, "d", weekday_ok=True)[0] == []   # no overnight nagging
    assert len(decide(True, False, False, s, T + REPEAT_SECS, "d", weekday_ok=True)[0]) == 1    # reminder once the session opens
    assert decide(False, False, False, {}, T, "d", weekday_ok=False)[0] == []                   # weekend / parked: quiet


def test_recovery_message_only_after_an_alert():
    assert decide(True, True, False, {}, T, "d")[0] == []
    msgs, s = decide(True, True, False, {"down_alert": T}, T + 5, "d")
    assert "back up" in msgs[0] and s["down_alert"] == 0


def test_silent_logger_alerts_once_per_day_when_gateway_is_up():
    msgs, s = decide(True, True, False, {}, T, "2026-11-02", silent=True)
    assert "no rows" in msgs[0].lower()
    assert decide(True, True, False, s, T + 300, "2026-11-02", silent=True)[0] == []
    assert decide(False, True, False, {}, T, "2026-11-02", silent=True)[0] == []   # out of session: quiet
    assert decide(True, False, False, {}, T, "2026-11-02", silent=True)[0][0].startswith("Voyager Gateway is DOWN")


def test_logger_silent_reads_proof_of_life_rows(tmp_path):
    f = tmp_path / "spike_log.csv"
    now = datetime(2026, 11, 2, 10, 0, tzinfo=ET)
    f.write_text("ts_et,kind\n2026-11-02T09:45:00,hb\n2026-11-02T09:59:00,down\n")
    assert not logger_silent(str(f), now)                       # hb 15 min ago; 'down' rows do not count as life
    f.write_text("ts_et,kind\n2026-11-02T09:15:00,hb\n2026-11-02T09:59:00,down\n")
    assert logger_silent(str(f), now)                           # newest proof of life is 45 min old
    assert logger_silent(str(tmp_path / "missing.csv"), now)    # no file at all is silent
    assert not logger_silent(str(f), datetime(2026, 11, 2, 4, 10, tzinfo=ET))   # first 30 min of session: skipped


def test_engine_skips_alert_once_at_limit_then_recover():
    s, sent = {}, []
    for i in range(1, 12):   # 11 failed cycles, each with a new ts
        m, s = engine_skips({"running": True, "ts": i, "error": "api connect"}, s)
        sent += m
        m, s = engine_skips({"running": True, "ts": i, "error": "api connect"}, s)   # same ts re-read: not double counted
        assert m == []
    assert len(sent) == 1 and "8 cycles" in sent[0]
    m, s = engine_skips({"running": True, "ts": 99, "error": None}, s)
    assert "again" in m[0] and s["skips"] == 0
    assert engine_skips({"running": False, "ts": 100, "error": "x"}, {})[0] == []   # stopped engine: quiet
    assert engine_skips(None, {})[0] == []


def test_gate_fail_alerts_once_per_day():
    msgs, s = decide(True, True, True, {}, T, "2026-11-02")
    assert "gate" in msgs[0].lower()
    assert decide(True, True, True, s, T + 300, "2026-11-02")[0] == []
    assert len(decide(True, True, True, s, T + 300, "2026-11-03")[0]) == 1
