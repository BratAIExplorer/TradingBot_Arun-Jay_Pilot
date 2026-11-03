"""
TDD tests for advance_rope() — the persisted-state contract for the trailing rope.

decide() only *reads* Position rope fields and returns an Action. advance_rope()
is the pure function the runner calls to compute the *next* Position state:
ratchet the high-water mark, recompute the floor, track MAE, and on a scale-out
decrement the tranche counter / lock the second-half trigger.

Run:  python -m pytest strategies/tests/test_rope_state.py -q
"""
from strategies.framework.config import ExitConfig
from strategies.framework.base import Position, Action
from strategies.small_cap_dryrun import advance_rope

_EXIT = ExitConfig()   # giveback 2%, floor 2%, step 3%


def _pos(**over):
    base = dict(ticker="X.NS", exchange="NSE", qty=10, avg_entry=100.0, tranches=1,
                entry_cross_date="01-Jan-2020", opened_at="2026-09-01T10:00:00",
                high_water_mark=None, trailing_floor=None, exit_tranches_remaining=2,
                locked_half2_price=None, mae_pct=None)
    base.update(over)
    return Position(**base)


def test_hwm_ratchets_up_on_a_higher_close():
    upd = advance_rope(_pos(high_water_mark=120.0), Action("HOLD", "x"), close=131.0, low=129.0, cfg_exit=_EXIT)
    assert upd["high_water_mark"] == 131.0
    assert upd["trailing_floor"] == 131.0 * 0.98


def test_hwm_does_not_ratchet_down():
    upd = advance_rope(_pos(high_water_mark=120.0), Action("HOLD", "x"), close=110.0, low=108.0, cfg_exit=_EXIT)
    assert upd["high_water_mark"] == 120.0


def test_mae_records_the_worst_drawdown_seen():
    # entry 100, today's low 82 -> -18% ; worse than a prior -5%
    upd = advance_rope(_pos(mae_pct=-5.0), Action("HOLD", "x"), close=90.0, low=82.0, cfg_exit=_EXIT)
    assert upd["mae_pct"] == -18.0


def test_mae_keeps_the_prior_worst_when_today_is_milder():
    upd = advance_rope(_pos(mae_pct=-18.0), Action("HOLD", "x"), close=98.0, low=95.0, cfg_exit=_EXIT)
    assert upd["mae_pct"] == -18.0


def test_first_scale_out_locks_the_second_trigger_and_decrements():
    pos = _pos(high_water_mark=120.0, exit_tranches_remaining=2)
    upd = advance_rope(pos, Action("SCALE_OUT", "half", fraction=0.5), close=117.0, low=116.0, cfg_exit=_EXIT)
    assert upd["exit_tranches_remaining"] == 1
    # rope 117.6, second trigger = 117.6 * (1 - 0.03)
    assert round(upd["locked_half2_price"], 3) == round(120.0 * 0.98 * 0.97, 3)


def test_second_scale_out_zeroes_the_counter():
    pos = _pos(high_water_mark=120.0, exit_tranches_remaining=1, locked_half2_price=114.07)
    upd = advance_rope(pos, Action("SCALE_OUT", "rest", fraction=1.0), close=114.0, low=113.0, cfg_exit=_EXIT)
    assert upd["exit_tranches_remaining"] == 0


def test_hold_does_not_touch_tranche_state():
    pos = _pos(high_water_mark=120.0, exit_tranches_remaining=2, locked_half2_price=None)
    upd = advance_rope(pos, Action("HOLD", "above rope"), close=119.0, low=118.0, cfg_exit=_EXIT)
    assert "exit_tranches_remaining" not in upd or upd["exit_tranches_remaining"] == 2
    assert upd.get("locked_half2_price") is None
