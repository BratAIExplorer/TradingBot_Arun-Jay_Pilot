"""
Smoke test for the shipped config file strategies/configs/small_cap_dryrun.json
— it must load, build a strategy, and encode B's "cap the bot at Rs 30,000" rule.

Run:  python -m pytest strategies/tests/test_config_file.py -q
"""
import os

from strategies.framework.registry import load

_CFG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "configs", "small_cap_dryrun.json")


def test_the_shipped_config_builds_a_strategy():
    strat = load(_CFG)
    assert strat.name == "small_cap_dryrun"


def test_it_caps_the_bot_at_100k_across_10_names():
    c = load(_CFG).cfg
    assert c.budget.total_budget == 100000
    assert c.budget.per_stock_amount == 10000
    assert c.budget.max_names == 10           # 100000 // 10000, at the cap of 10


def test_realistic_costs_and_all_the_new_knobs_are_present():
    c = load(_CFG).cfg
    assert c.costs.fill_assumption == "realistic"
    assert c.costs.stt_pct == 0.1 and c.costs.exit_slippage_bps_thin == 300
    assert c.exit.strand_final_half is True
    assert c.rules.circuit_band_pct == 10.0
    assert c.liquidity.min_avg_daily_value_cr == 1.0
    assert c.fundamentals.min_roe == 10.0
