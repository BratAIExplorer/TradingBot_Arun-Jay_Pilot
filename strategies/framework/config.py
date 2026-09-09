"""
Per-strategy configuration: one JSON file -> one frozen dataclass.

Every tunable a strategy exposes lives in its JSON (strategies/configs/<name>.json)
so it can be changed without editing Python. Unknown top-level keys are ignored;
missing required keys raise KeyError naming the key.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

# Single source of truth for the small-cap market-cap band (₹ crore).
# strategies/small_cap_universe.py imports this; the fundamentals gate reads the
# same numbers so the universe filter and the gate can never drift apart.
MARKET_CAP_BAND_CR = (500.0, 5000.0)


@dataclass(frozen=True)
class BudgetConfig:
    per_stock_amount: float      # rupees for one full position (no adds)
    total_budget: float          # rupees the whole strategy may deploy
    max_names_cap: int           # hard cap on distinct names, whatever the budget allows
    pct_of_account_cap: float    # optional extra ceiling, % of account value
    max_names: int               # derived: min(total_budget // per_stock_amount, max_names_cap)


@dataclass(frozen=True)
class ExitConfig:
    trail_giveback_pct: float = 2.0      # rope = high_water_mark * (1 - this/100)
    min_profit_floor_pct: float = 2.0    # never sell a tranche below entry * (1 + this/100)
    scale_out_step_pct: float = 3.0      # second half triggers this far below the rope
    hard_stop_pct: float | None = None   # OFF by default; if set, sell all at entry*(1-this/100)
    never_sell_at_loss: bool = True
    strand_final_half: bool = True       # True: hold a final half whose trigger is below the
                                         # floor (dad sells it manually). False: sell it anyway
                                         # at the trigger. This is the "stranded half" choice.


@dataclass(frozen=True)
class CostsConfig:
    """Zerodha delivery cost model. Defaults are ZERO ('best' fill) so an
    unconfigured strategy behaves exactly as the old gross floor. A real config
    JSON sets the realistic numbers (stt 0.1, entry slippage 40bps, thin-book
    exit slippage 300bps)."""
    brokerage_flat: float = 0.0          # rupees per order (Zerodha delivery = 0)
    stt_pct: float = 0.0                 # % of turnover, both legs
    entry_slippage_bps: float = 0.0      # buy fills this many bps worse
    exit_slippage_bps_thin: float = 0.0  # sell fills this many bps worse on a thin book
    fill_assumption: str = "best"        # "best" | "realistic" (label only, for the dashboard)


@dataclass(frozen=True)
class EntryConfig:
    fresh_cross_max_age_days: int = 1     # MACD cross must be within this many trading days
    require_200ema_uptrend: bool = True   # CMP > 200 EMA AND 50 EMA > 200 EMA


@dataclass(frozen=True)
class LiquidityConfig:
    enabled: bool = True
    min_avg_daily_value_cr: float = 1.0   # applied to entry AND exit; not wired to a sell yet


@dataclass(frozen=True)
class FundamentalsConfig:
    enabled: bool = True
    min_roe: float = 10.0             # %
    max_debt_equity: float = 1.0      # ratio
    require_positive_earnings: bool = True
    # market-cap band is shared — see MARKET_CAP_BAND_CR / StrategyConfig.min_market_cap_cr


@dataclass(frozen=True)
class RulesConfig:
    ma_period: int = 50
    rsi_period: int = 14
    divergence_lookback: int = 10
    swing_fractal_bars: int = 5
    circuit_band_pct: float = 10.0    # heuristic daily price limit; if the whole day trades
                                      # locked at/below entry-band, treat as a frozen lower
                                      # circuit (no bid) and never emit a sell that day


@dataclass(frozen=True)
class StrategyConfig:
    name: str
    enabled: bool
    budget: BudgetConfig
    rules: RulesConfig
    replay_stop_levels_pct: list
    universe: str
    exit: ExitConfig = field(default_factory=ExitConfig)
    entry: EntryConfig = field(default_factory=EntryConfig)
    liquidity: LiquidityConfig = field(default_factory=LiquidityConfig)
    fundamentals: FundamentalsConfig = field(default_factory=FundamentalsConfig)
    costs: CostsConfig = field(default_factory=CostsConfig)
    min_market_cap_cr: float = MARKET_CAP_BAND_CR[0]
    max_market_cap_cr: float = MARKET_CAP_BAND_CR[1]
    orders_enabled: bool = False    # the live-money switch; log-only until True AND keys present


def _req(d: dict, key: str):
    if key not in d:
        raise KeyError(f"config missing required key: {key!r}")
    return d[key]


def _derive_max_names(per_stock_amount: float, total_budget: float, max_names_cap: int) -> int:
    if per_stock_amount <= 0:
        raise ValueError(f"budget.per_stock_amount must be > 0, got {per_stock_amount}")
    by_budget = int(total_budget // per_stock_amount)
    max_names = min(by_budget, int(max_names_cap))
    if max_names < 1:
        raise ValueError(
            f"budget resolves to {max_names} names "
            f"(total_budget {total_budget:g} / per_stock_amount {per_stock_amount:g} "
            f"= {by_budget}, capped at {max_names_cap}) — the strategy would never buy anything"
        )
    return max_names


def load_strategy_config(path: str) -> StrategyConfig:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    b = _req(raw, "budget")
    r = raw.get("rules", {})
    e = raw.get("exit", {})
    en = raw.get("entry", {})
    lq = raw.get("liquidity_gate", {})
    fg = raw.get("fundamentals_gate", {})
    co = raw.get("costs", {})

    per_stock_amount = _req(b, "per_stock_amount")
    total_budget = _req(b, "total_budget")
    max_names_cap = _req(b, "max_names_cap")

    return StrategyConfig(
        name=_req(raw, "name"),
        enabled=bool(_req(raw, "enabled")),
        budget=BudgetConfig(
            per_stock_amount=per_stock_amount,
            total_budget=total_budget,
            max_names_cap=max_names_cap,
            pct_of_account_cap=_req(b, "pct_of_account_cap"),
            max_names=_derive_max_names(per_stock_amount, total_budget, max_names_cap),
        ),
        rules=RulesConfig(
            ma_period=r.get("ma_period", 50),
            rsi_period=r.get("rsi_period", 14),
            divergence_lookback=r.get("divergence_lookback", 10),
            swing_fractal_bars=r.get("swing_fractal_bars", 5),
            circuit_band_pct=r.get("circuit_band_pct", 10.0),
        ),
        exit=ExitConfig(
            trail_giveback_pct=e.get("trail_giveback_pct", 2.0),
            min_profit_floor_pct=e.get("min_profit_floor_pct", 2.0),
            scale_out_step_pct=e.get("scale_out_step_pct", 3.0),
            hard_stop_pct=e.get("hard_stop_pct", None),
            never_sell_at_loss=bool(e.get("never_sell_at_loss", True)),
            strand_final_half=bool(e.get("strand_final_half", True)),
        ),
        costs=CostsConfig(
            brokerage_flat=co.get("brokerage_flat", 0.0),
            stt_pct=co.get("stt_pct", 0.0),
            entry_slippage_bps=co.get("entry_slippage_bps", 0.0),
            exit_slippage_bps_thin=co.get("exit_slippage_bps_thin", 0.0),
            fill_assumption=co.get("fill_assumption", "best"),
        ),
        entry=EntryConfig(
            fresh_cross_max_age_days=int(en.get("fresh_cross_max_age_days", 1)),
            require_200ema_uptrend=bool(en.get("require_200ema_uptrend", True)),
        ),
        liquidity=LiquidityConfig(
            enabled=bool(lq.get("enabled", True)),
            min_avg_daily_value_cr=lq.get("min_avg_daily_value_cr", 1.0),
        ),
        fundamentals=FundamentalsConfig(
            enabled=bool(fg.get("enabled", True)),
            min_roe=fg.get("min_roe", 10.0),
            max_debt_equity=fg.get("max_debt_equity", 1.0),
            require_positive_earnings=bool(fg.get("require_positive_earnings", True)),
        ),
        replay_stop_levels_pct=list(_req(raw, "replay_stop_levels_pct")),
        universe=_req(raw, "universe"),
        min_market_cap_cr=fg.get("min_market_cap_cr", MARKET_CAP_BAND_CR[0]),
        max_market_cap_cr=fg.get("max_market_cap_cr", MARKET_CAP_BAND_CR[1]),
        orders_enabled=bool(raw.get("orders_enabled", False)),
    )
