from deploy.daily_summary import summarize


def rows(day, hb=0, gate=0, events=(), ticks=0, down=0):
    out = [{"ts_et": f"{day}T10:00:00", "kind": "hb", "symbol": ""} for _ in range(hb)]
    out += [{"ts_et": f"{day}T10:00:00", "kind": "gate_fail", "symbol": ""} for _ in range(gate)]
    out += [{"ts_et": f"{day}T10:00:00", "kind": "down", "symbol": ""} for _ in range(down)]
    out += [{"ts_et": f"{day}T10:00:00", "kind": "event", "symbol": s} for s in events]
    out += [{"ts_et": f"{day}T10:00:00", "kind": "tick", "symbol": "X"} for _ in range(ticks)]
    return out


def test_full_day_is_reported_ok_and_counts_distinct_stocks():
    msg = summarize(rows("2026-11-03", hb=70, events=("AAA", "AAA", "BBB"), ticks=5), "2026-11-03")
    assert "FULL DAY" in msg and "70/71" in msg and "events 3 on 2 stocks" in msg


def test_gaps_when_heartbeats_missing_or_gate_failed_and_other_days_ignored():
    assert "GAPS" in summarize(rows("2026-11-03", hb=40), "2026-11-03")
    assert "GAPS" in summarize(rows("2026-11-03", hb=70, gate=1), "2026-11-03")
    assert "Heartbeats 0/71" in summarize(rows("2026-11-02", hb=70), "2026-11-03")


def test_max_lines_from_heartbeat_notes_is_reported_and_flags_a_full_cap():
    from deploy.daily_summary import max_lines
    hb = lambda n: {"ts_et": "2026-11-03T10:00:00", "kind": "hb", "symbol": "", "note": f"scan=50 lines={n}"}
    assert max_lines([hb(3), hb(17), {"ts_et": "x", "kind": "tick", "symbol": ""}]) == 17
    assert max_lines([{"ts_et": "x", "kind": "hb", "symbol": ""}]) == 0       # old rows without a note
    from research.spike_logger import MAX_LINES
    msg = summarize(rows("2026-11-03", hb=70) + [hb(MAX_LINES)], "2026-11-03")
    assert f"lines {MAX_LINES}/{MAX_LINES}" in msg and "CAP" in msg
