"""
TDD tests for entry sizing + gating (money/count rules shared by all strategies).

The strategy decides IF a BUY signal fired. This layer decides how many shares
and whether budget/limits allow it. One full position per name — no adds.

Run:  python -m pytest strategies/tests/test_sizing.py -q
"""
from strategies.framework.config import StrategyConfig, BudgetConfig, RulesConfig
from strategies.framework.sizing import plan_entry, EntryPlan


def _cfg(per_stock=5000, cap_pct=2.0, max_names=5):
    return StrategyConfig(
        name="t", enabled=True,
        budget=BudgetConfig(
            per_stock_amount=per_stock, total_budget=per_stock * max_names,
            max_names_cap=max_names, pct_of_account_cap=cap_pct, max_names=max_names,
        ),
        rules=RulesConfig(),
        replay_stop_levels_pct=[5, 8, 10], universe="starter",
    )


class _Pos:
    tranches = 1


def test_full_position_qty_is_budget_div_price():
    p = plan_entry(account_value=1_000_000, price=250, position=None, cfg=_cfg(per_stock=5000),
                   open_names=0, deployed=0)
    assert isinstance(p, EntryPlan)
    assert p.allowed is True
    assert p.qty == 20                       # 5000 / 250


def test_blocked_when_price_exceeds_whole_budget():
    p = plan_entry(account_value=1_000_000, price=6000, position=None, cfg=_cfg(per_stock=5000),
                   open_names=0, deployed=0)
    assert p.allowed is False
    assert "budget" in p.reason.lower()


def test_blocked_by_2pct_account_ceiling():
    p = plan_entry(account_value=100_000, price=100, position=None, cfg=_cfg(per_stock=5000, cap_pct=2.0),
                   open_names=1, deployed=1800)
    assert p.allowed is False
    assert "ceiling" in p.reason.lower()


def test_blocked_when_the_buy_would_push_deployed_past_total_budget():
    # account 100k, total_budget = 5000*5 = 25k. Already 22k deployed across 2 names;
    # a 5k buy would take it to 27k > 25k. Name count (2 < 5) and the 2% ceiling
    # (25k*... ) do not bind here — only the rupee budget should stop it.
    cfg = _cfg(per_stock=5000, cap_pct=90.0, max_names=5)
    p = plan_entry(account_value=100_000, price=100, position=None, cfg=cfg,
                   open_names=2, deployed=22_000)
    assert p.allowed is False
    assert "budget" in p.reason.lower() and "25" in p.reason


def test_buy_that_stays_within_total_budget_is_allowed():
    cfg = _cfg(per_stock=5000, cap_pct=90.0, max_names=5)
    p = plan_entry(account_value=100_000, price=100, position=None, cfg=cfg,
                   open_names=2, deployed=15_000)
    assert p.allowed is True                     # 15k + 5k = 20k <= 25k


def test_blocked_when_max_names_reached():
    p = plan_entry(account_value=1_000_000, price=100, position=None, cfg=_cfg(max_names=5),
                   open_names=5, deployed=0)
    assert p.allowed is False
    assert "names" in p.reason.lower()


def test_any_existing_position_is_rejected_no_adds():
    p = plan_entry(account_value=1_000_000, price=100, position=_Pos(), cfg=_cfg(),
                   open_names=3, deployed=0)
    assert p.allowed is False
    assert p.qty == 0
    assert "no adds" in p.reason.lower()
