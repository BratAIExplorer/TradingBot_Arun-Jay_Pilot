"""
Tests for framework/registry.py — name -> Strategy lookup.

Run:  python -m pytest strategies/tests/test_registry.py -q
"""
import json

import pytest

from strategies.framework import registry
from strategies.small_cap_dryrun import SmallCapDryRun


def test_available_lists_the_small_cap_strategy():
    assert "small_cap_dryrun" in registry.available()


def test_build_returns_the_right_class():
    cfg = _min_config()
    strat = registry.build(cfg)
    assert isinstance(strat, SmallCapDryRun)
    assert strat.cfg is cfg


def test_unknown_name_raises_with_a_helpful_message():
    cfg = _min_config()
    object.__setattr__(cfg, "name", "does_not_exist")
    with pytest.raises(KeyError, match="no strategy registered"):
        registry.build(cfg)


def test_load_round_trips_from_a_json_file(tmp_path):
    p = tmp_path / "small_cap_dryrun.json"
    p.write_text(json.dumps({
        "name": "small_cap_dryrun",
        "enabled": True,
        "budget": {"per_stock_amount": 10000, "total_budget": 30000,
                   "max_names_cap": 10, "pct_of_account_cap": 2.0},
        "replay_stop_levels_pct": [5, 8, 10],
        "universe": "starter",
    }))
    strat = registry.load(str(p))
    assert isinstance(strat, SmallCapDryRun)
    assert strat.cfg.budget.max_names == 3


def _min_config():
    from strategies.framework.config import load_strategy_config
    import tempfile
    import os
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, json.dumps({
        "name": "small_cap_dryrun",
        "enabled": True,
        "budget": {"per_stock_amount": 10000, "total_budget": 30000,
                   "max_names_cap": 10, "pct_of_account_cap": 2.0},
        "replay_stop_levels_pct": [5, 8, 10],
        "universe": "starter",
    }).encode())
    os.close(fd)
    try:
        return load_strategy_config(path)
    finally:
        os.unlink(path)
