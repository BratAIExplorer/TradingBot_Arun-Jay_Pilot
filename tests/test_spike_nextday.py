import csv

from research.spike_nextday import flagged_days, score, trade_from_bars

BARS = [
    {"date": "2026-11-03", "open": 1.0, "high": 1.5, "close": 1.4, "prev_close": 1.0},
    {"date": "2026-11-04", "open": 1.3, "high": 1.6, "close": 1.5, "prev_close": 1.4},
    {"date": "2026-11-05", "open": 1.5, "high": 1.5, "close": 1.2, "prev_close": 1.5},
]


def test_net_matches_hand_calc():
    t = trade_from_bars(BARS, "2026-11-03", 0.0, 1)
    assert abs(t["net_pct"] - ((1.5 / 1.4 - 1) * 100 - 0.4)) < 1e-9     # $1 per side on $500 = 0.2% each way
    assert trade_from_bars(BARS, "2026-11-03", 0.0, 2)["net_pct"] < 0


def test_gap_down_flag():
    bars = [BARS[0], {**BARS[1], "open": 1.0}]
    assert trade_from_bars(bars, "2026-11-03", 0.0, 1)["gap_down"]
    assert not trade_from_bars(BARS, "2026-11-03", 0.0, 1)["gap_down"]


def test_missing_data_is_unresolved_when_old_and_pending_when_new():
    assert trade_from_bars(None, "2026-11-03", 0.05, 1, today="2026-11-20")["unresolved"]
    assert trade_from_bars(BARS[:1], "2026-11-03", 0.05, 1, today="2026-11-04") is None
    assert trade_from_bars(BARS, "2026-11-05", 0.05, 1, today="2026-11-06") is None          # feed current, exit bar not yet printed
    assert trade_from_bars(BARS, "2026-11-05", 0.05, 1, today="2026-12-20")["unresolved"]     # feed stale for weeks: really missing


def test_score_counts_every_flagged_day(tmp_path):
    p = tmp_path / "log.csv"
    rows = [("2026-11-02T10:00:00", "event", "OLD"), ("2026-11-03T10:00:00", "event", "AAA"),
            ("2026-11-03T10:05:00", "event", "AAA"), ("2026-11-03T10:00:00", "event", "BBB"), ("2026-11-03T10:00:00", "tick", "AAA")]
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts_et", "kind", "symbol"])
        w.writerows(rows)
    assert set(flagged_days(str(p))) == {("2026-11-03", "AAA"), ("2026-11-03", "BBB")}
    res = score(str(p), fetch=lambda s, a, b: BARS if s == "AAA" else None, today="2026-11-20")
    all_t1 = res[("ALL", 1, 0.05)]
    assert len(all_t1) == 2 and sum(t["unresolved"] for t in all_t1) == 1     # BBB has no bars -> kept as unresolved
    assert len(res[("HOLD", 1, 0.05)]) == 2                                   # AAA closed +40% so it passes; BBB stays as unresolved
