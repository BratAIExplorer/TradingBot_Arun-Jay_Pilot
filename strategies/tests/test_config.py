"""
TDD tests for per-strategy JSON config loading.

Run:  python -m pytest strategies/tests/test_config.py -q
"""
import json
import pytest

from strategies.framework.config import (
    load_strategy_config, StrategyConfig, MARKET_CAP_BAND_CR,
)


def _write(tmp_path, obj):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return str(p)


def _full(**over):
    base = {
        "name": "small_cap_dryrun",
        "enabled": True,
        "budget": {
            "per_stock_amount": 10000,
            "total_budget": 30000,          # -> 3 names
            "max_names_cap": 10,
            "pct_of_account_cap": 2.0,
        },
        "rules": {"ma_period": 50, "rsi_period": 14, "divergence_lookback": 10, "swing_fractal_bars": 5},
        "entry": {"fresh_cross_max_age_days": 1, "require_200ema_uptrend": True},
        "exit": {"trail_giveback_pct": 2.0, "min_profit_floor_pct": 2.0, "scale_out_step_pct": 3.0,
                 "hard_stop_pct": None, "never_sell_at_loss": True},
        "liquidity_gate": {"enabled": True, "min_avg_daily_value_cr": 1.0},
        "fundamentals_gate": {"enabled": True, "min_roe": 10.0, "max_debt_equity": 1.0,
                              "require_positive_earnings": True,
                              "min_market_cap_cr": 500, "max_market_cap_cr": 5000},
        "replay_stop_levels_pct": [5, 8, 10],
        "universe": "starter",
    }
    base.update(over)
    return base


def test_loads_all_fields(tmp_path):
    cfg = load_strategy_config(_write(tmp_path, _full()))
    assert isinstance(cfg, StrategyConfig)
    assert cfg.name == "small_cap_dryrun"
    assert cfg.enabled is True
    assert cfg.budget.per_stock_amount == 10000
    assert cfg.budget.total_budget == 30000
    assert cfg.budget.max_names_cap == 10
    assert cfg.budget.pct_of_account_cap == 2.0
    assert cfg.rules.ma_period == 50
    assert cfg.replay_stop_levels_pct == [5, 8, 10]
    assert cfg.universe == "starter"


def test_max_names_is_derived_from_budget_math(tmp_path):
    cfg = load_strategy_config(_write(tmp_path, _full()))
    assert cfg.budget.max_names == 3                       # 30000 // 10000

    capped = load_strategy_config(_write(tmp_path, _full(
        budget={"per_stock_amount": 1000, "total_budget": 999999,
                "max_names_cap": 4, "pct_of_account_cap": 2.0})))
    assert capped.budget.max_names == 4                    # budget allows 999, cap wins


def test_zero_names_errors_loudly(tmp_path):
    bad = _full(budget={"per_stock_amount": 10000, "total_budget": 5000,
                        "max_names_cap": 10, "pct_of_account_cap": 2.0})
    with pytest.raises(ValueError, match="never buy"):
        load_strategy_config(_write(tmp_path, bad))


def test_market_cap_band_mirrors_the_shared_constant(tmp_path):
    # gate block absent -> falls back to the single-source-of-truth band
    cfg = load_strategy_config(_write(tmp_path, _full(fundamentals_gate={})))
    assert (cfg.min_market_cap_cr, cfg.max_market_cap_cr) == MARKET_CAP_BAND_CR

    from strategies.small_cap_universe import DEFAULT_MIN_CR, DEFAULT_MAX_CR
    assert (DEFAULT_MIN_CR, DEFAULT_MAX_CR) == MARKET_CAP_BAND_CR


def test_entry_and_exit_and_liquidity_and_fundamentals_blocks_round_trip(tmp_path):
    cfg = load_strategy_config(_write(tmp_path, _full()))
    assert cfg.entry.fresh_cross_max_age_days == 1
    assert cfg.entry.require_200ema_uptrend is True
    assert cfg.exit.trail_giveback_pct == 2.0
    assert cfg.exit.scale_out_step_pct == 3.0
    assert cfg.exit.hard_stop_pct is None
    assert cfg.liquidity.enabled is True
    assert cfg.liquidity.min_avg_daily_value_cr == 1.0
    assert cfg.fundamentals.min_roe == 10.0
    assert cfg.fundamentals.max_debt_equity == 1.0
    assert cfg.fundamentals.require_positive_earnings is True


def test_optional_blocks_fall_back_to_dataclass_defaults(tmp_path):
    raw = _full()
    del raw["entry"]
    del raw["liquidity_gate"]
    cfg = load_strategy_config(_write(tmp_path, raw))
    assert cfg.entry.fresh_cross_max_age_days == 1     # dataclass default
    assert cfg.liquidity.min_avg_daily_value_cr == 1.0


def test_rules_block_uses_defaults_when_keys_missing(tmp_path):
    cfg = load_strategy_config(_write(tmp_path, _full(rules={"ma_period": 20})))
    assert cfg.rules.ma_period == 20
    assert cfg.rules.rsi_period == 14
    assert cfg.rules.divergence_lookback == 10
    assert cfg.rules.swing_fractal_bars == 5


def test_missing_required_budget_key_raises_clear_error(tmp_path):
    bad = _full()
    del bad["budget"]["per_stock_amount"]
    with pytest.raises(KeyError, match="per_stock_amount"):
        load_strategy_config(_write(tmp_path, bad))


def test_config_is_frozen(tmp_path):
    cfg = load_strategy_config(_write(tmp_path, _full()))
    with pytest.raises(Exception):
        cfg.enabled = False
