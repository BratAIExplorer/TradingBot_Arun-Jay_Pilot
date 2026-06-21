"""BrokerInterface Protocol - structural contract for dual-market broker abstraction."""

from typing import Any, Protocol, runtime_checkable

# Phase 0: Keep return types exactly as mStock implements them (DO NOT reshape yet).
Quote = dict[str, Any] | None  # get_quote returns inner dict or None
OrderResponse = Any  # mStock returns requests.Response; callers do .json()
HistoricalData = dict[str, Any] | None  # raw mStock JSON or None


@runtime_checkable
class BrokerInterface(Protocol):
    """
    Structural contract satisfied by any broker implementation (mStock, IBKR, etc.).

    Uses Protocol (duck-typed) so existing BrokerAPI stays byte-for-byte unchanged.
    Methods extracted from broker_api.py actual signatures — zero reshaping in Phase 0.
    """

    def get_funds(self) -> float:
        """Return available cash balance (INR for mStock, USD for IBKR)."""
        ...

    def get_holdings(self) -> list[dict[str, Any]]:
        """Return list of all holdings (stocks held)."""
        ...

    def get_positions(self) -> list[dict[str, Any]]:
        """Return list of open positions."""
        ...

    def get_orders(self) -> list[dict[str, Any]]:
        """Return list of pending/active orders."""
        ...

    def get_quote(self, symbol: str, exchange: str) -> Quote:
        """
        Get quote for a symbol on an exchange.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE" for mStock, "AAPL" for IBKR)
            exchange: Exchange code (e.g., "NSE", "BSE" for mStock, "SMART" for IBKR)

        Returns:
            dict with quote data or None on failure.
        """
        ...

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
    ) -> OrderResponse:
        """
        Place an order.

        NOTE (Phase 1 gotcha): Returns requests.Response-like object (mStock).
        IBKR implementation must mimic or normalize in Phase 1.

        Args:
            symbol: Stock symbol
            exchange: Exchange code
            side: "BUY" or "SELL"
            quantity: Order quantity
            price: Limit price (0 = market)
            trigger_price: Stop-loss trigger price
            product: "CNC" (cash), "MIS" (intraday)
            validity: "DAY", "IOC", "FOK"
            variety: "regular", "amo" (after-market)
            instrument_token: Numeric token (mStock specific, IBKR N/A)

        Returns:
            OrderResponse (requests.Response for mStock, similar structure for IBKR).
        """
        ...

    def get_historical_data(
        self,
        exchange: str,
        instrument_token: Any,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> HistoricalData:
        """
        Get historical OHLC data.

        Args:
            exchange: Exchange code
            instrument_token: Numeric token (mStock requires this; IBKR uses symbol)
            interval: "minute", "5minute", "30minute", "hour", "day"
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            dict with OHLC data or None on failure.
        """
        ...
