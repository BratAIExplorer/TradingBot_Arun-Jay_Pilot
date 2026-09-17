"""Broker factory — routes a market code to a concrete broker implementation."""
from __future__ import annotations

from .interface import BrokerInterface


def get_broker(market: str) -> BrokerInterface:
    """
    market: "IN" (India/mStock, default) or "US" (Interactive Brokers).
    Raises ValueError for anything else.
    """
    market = (market or "IN").upper()

    if market == "IN":
        from .mstock_adapter import MStockBroker
        return MStockBroker()

    if market == "US":
        from .ibkr_broker import IBKRBroker
        return IBKRBroker()

    raise ValueError(f"Unknown market: {market!r} (expected 'IN' or 'US')")
