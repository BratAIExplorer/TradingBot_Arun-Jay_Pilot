from datetime import datetime
from zoneinfo import ZoneInfo

from deploy.gateway_watch import REPEAT_SECS, decide, logger_silent

ET = ZoneInfo("America/New_York")

T = 1_000_000.0


def test_down_in_session_alerts_once_then_repeats_after_two_hours():
    msgs, s = decide(True, False, False, {}, T, "d")
    assert len(msgs) == 1 and "DOWN" in msgs[0]
    assert decide(True, False, False, s, T + 60, "d")[0] == []
    assert len(decide(True, False, False, s, T + REPEAT_SECS, "d")[0]) == 1


def test_down_outside_session_is_quiet():
    assert decide(False, False, False, {}, T, "d")[0] == []


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


def test_gate_fail_alerts_once_per_day():
    msgs, s = decide(True, True, True, {}, T, "2026-11-02")
    assert "gate" in msgs[0].lower()
    assert decide(True, True, True, s, T + 300, "2026-11-02")[0] == []
    assert len(decide(True, True, True, s, T + 300, "2026-11-03")[0]) == 1
