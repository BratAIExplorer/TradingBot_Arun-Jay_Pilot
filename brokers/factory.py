"""Broker factory - routes market code to concrete broker implementation."""

from typing import Any

from .interface import BrokerInterface


def get_broker(market: str, **creds: Any) -> BrokerInterface | None:
    """
    Get a broker instance for a given market.

    Phase 0: Routes 'IN' (India) to mStock, 'US' (US) to stub.
    Phase 2+: Both are fully implemented.

    Args:
        market: Market code ('IN' for India/mStock, 'US' for USA/IBKR)
        **creds: Broker-specific credentials
            For mStock: api_key, access_token, client_code, login_callback
            For IBKR: (phase 2 - not yet defined)

    Returns:
        BrokerInterface instance or None if broker creation fails.

    Raises:
        ValueError: If market code is unknown.
    """
    market = (market or "IN").upper()

    if market == "IN":
        # Lazy import preserves existing import timing in kickstart.py
        from broker_api import BrokerAPI

        return BrokerAPI(
            api_key=creds.get("api_key"),
            access_token=creds.get("access_token"),
            client_code=creds.get("client_code"),
            login_callback=creds.get("login_callback"),
        )

    if market == "US":
        # Phase 0: stub. Phase 2: replaced with real IBKRBroker.
        from .ibkr_stub import IBKRBroker

        return IBKRBroker(**creds)

    raise ValueError(f"Unknown market: {market!r} (expected 'IN' or 'US')")
