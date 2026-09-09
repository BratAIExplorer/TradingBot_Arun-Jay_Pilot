"""
Entry sizing + gating — shared money/count rules for every strategy.

The strategy decides whether a BUY signal fired. This layer answers: how many
shares, and do the budget / account-ceiling / name-count rules allow it?
One full position per name — there are no add-on tranches. Pure, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntryPlan:
    allowed: bool
    qty: int
    reason: str


def plan_entry(
    *,
    account_value: float,
    price: float,
    position,                     # None for a new name; anything truthy means "already held"
    cfg,                          # StrategyConfig
    open_names: int,              # distinct names this strategy currently holds
    deployed: float,             # rupees this strategy currently has in the market
    last_fill_date_for_name=None,  # kept for call-site compatibility; unused (no adds)
    today: str = "",              # kept for call-site compatibility; unused (no adds)
) -> EntryPlan:
    # One full position per name, no adds — budget math sizes exactly one buy.
    if position is not None:
        return EntryPlan(False, 0, "already held — no adds, one full position per name")

    if price <= 0:
        return EntryPlan(False, 0, "invalid price")

    qty = int(cfg.budget.per_stock_amount // price)
    if qty < 1:
        return EntryPlan(False, 0, "position budget too small for this price")

    ceiling = account_value * cfg.budget.pct_of_account_cap / 100.0
    if deployed + qty * price > ceiling:
        return EntryPlan(False, 0, f"blocked by {cfg.budget.pct_of_account_cap}% account ceiling")

    if open_names >= cfg.budget.max_names:
        return EntryPlan(False, 0, f"max names ({cfg.budget.max_names}) already held")
    return EntryPlan(True, qty, "entry: full position")
