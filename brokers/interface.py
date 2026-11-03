"""BrokerInterface Protocol — structural contract for the dual-market (IN/US) broker split.

Ported from Project Vayu's brokers/interface.py. Return types match what kickstart.py's
existing mStock functions actually return today (dict/list/tuple) — zero reshaping, so
wrapping them costs nothing and breaks nothing.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

Quote = dict[str, Any] | None
OrderResponse = Any  # mStock: requests.Response-like; callers do .json()
Funds = float | None


@runtime_checkable
class BrokerInterface(Protocol):
    """Contract satisfied by any broker implementation (mStock, IBKR, ...)."""

    def get_funds(self) -> Funds:
        """Available cash balance (INR for mStock, USD for IBKR)."""
        ...

    def get_positions(self) -> dict[Any, dict[str, Any]]:
        """Open positions, keyed the same way kickstart.py's live_positions is."""
        ...

    def get_quote(self, symbol: str, exchange: str) -> Quote:
        """Latest market data for a symbol on an exchange."""
        ...

    def place_order(
        self,
        symbol: str,
        exchange: str,
        qty: int,
        side: str,
        instrument_token: Any,
        price: float = 0,
        use_amo: bool = False,
    ) -> OrderResponse:
        """Place an order. Signature matches kickstart.py's place_order() exactly."""
        ...
