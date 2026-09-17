"""Wraps kickstart.py's existing mStock functions behind BrokerInterface.

Pure wrapper — does not change kickstart.py. Every method here just calls the
already-live function of the same behavior. Not wired into run_cycle() yet.
"""
from __future__ import annotations

from typing import Any


class MStockBroker:
    def get_funds(self) -> float | None:
        import kickstart
        return kickstart.fetch_funds()

    def get_positions(self) -> dict[Any, dict[str, Any]]:
        import kickstart
        return kickstart.safe_get_live_positions_merged()

    def get_quote(self, symbol: str, exchange: str):
        import kickstart
        md, _ = kickstart.fetch_market_data(symbol, exchange)
        return md

    def place_order(self, symbol, exchange, qty, side, instrument_token, price=0, use_amo=False):
        import kickstart
        return kickstart.place_order(symbol, exchange, qty, side, instrument_token, price, use_amo)
