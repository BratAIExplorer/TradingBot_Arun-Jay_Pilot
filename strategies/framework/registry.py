"""
name -> Strategy instance.

One place the runner and the dashboard look up a strategy by its config name.
Register a new strategy with one line here; nothing else in the framework needs
to know it exists.
"""
from __future__ import annotations

from strategies.framework.config import StrategyConfig, load_strategy_config
from strategies.small_cap_dryrun import SmallCapDryRun

# config name -> class that takes a StrategyConfig
_STRATEGIES = {
    SmallCapDryRun.name: SmallCapDryRun,
}


def available() -> list:
    """Registered strategy names."""
    return sorted(_STRATEGIES)


def build(config: StrategyConfig):
    """Instantiate the strategy named by config.name with that config."""
    try:
        cls = _STRATEGIES[config.name]
    except KeyError:
        raise KeyError(f"no strategy registered as {config.name!r}; "
                       f"known: {', '.join(available()) or '(none)'}")
    return cls(config)


def load(config_path: str):
    """Read a strategy JSON and return its ready-to-run Strategy instance."""
    return build(load_strategy_config(config_path))
