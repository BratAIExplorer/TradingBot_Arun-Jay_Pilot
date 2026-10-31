"""IBKR Broker stub - Phase 0 placeholder, Phase 2 full implementation.

Satisfies BrokerInterface structurally so Protocol conformance passes.
All methods raise NotImplementedError — implementation in Phase 2 when ib_insync is wired.
"""

from typing import Any


class IBKRBroker:
    """
    Phase 0: Stub implementation of IBKR broker.
    Exists only to satisfy BrokerInterface Protocol (method names match).
    All methods raise NotImplementedError('IBKR Phase 2').

    Phase 2: Will replace these with real ib_insync/IB Gateway integration.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize IBKR broker config (Phase 0: not used)."""
        self._cfg = kwargs

    def get_funds(self) -> float:
        """Phase 2: Get available cash balance in USD."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")

    def get_holdings(self) -> list[dict[str, Any]]:
        """Phase 2: Get list of all holdings."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")

    def get_positions(self) -> list[dict[str, Any]]:
        """Phase 2: Get list of open positions."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")

    def get_orders(self) -> list[dict[str, Any]]:
        """Phase 2: Get list of pending orders."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")

    def get_quote(self, symbol: str, exchange: str) -> dict[str, Any] | None:
        """Phase 2: Get quote for symbol on exchange."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")

    def place_order(
        self,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        price: float = 0,
        trigger_price: float = 0,
        product: str = "CNC",
        validity: str = "DAY",
        variety: str = "regular",
        instrument_token: Any = None,
    ) -> Any:
        """Phase 2: Place an order."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")

    def get_historical_data(
        self,
        exchange: str,
        instrument_token: Any,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> dict[str, Any] | None:
        """Phase 2: Get historical OHLC data."""
        raise NotImplementedError("IBKR implementation pending (Phase 2)")
