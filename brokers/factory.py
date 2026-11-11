"""Broker factory — routes a market code to a concrete broker implementation.

Two callers share this on the merged branch, told apart by whether credentials are passed:
  - main's kickstart.py engine passes credentials:  get_broker("IN", **mstock_cfg) / get_broker("US", **ibkr_cfg)
        IN -> broker_api.BrokerAPI (what that engine expects)
        US -> ibkr_stub.IBKRBroker (raises NotImplementedError — the engine path can never send a real IBKR order)
  - Voyager's dashboard/tests pass none:             get_broker("IN") / get_broker("US")
        IN -> MStockBroker adapter,  US -> the real ib_insync IBKRBroker (never auto-connects)
"""
from __future__ import annotations

from typing import Any

from .interface import BrokerInterface


def get_broker(market: str = "IN", **creds: Any) -> BrokerInterface:
    """market: "IN" (India/mStock, default) or "US" (Interactive Brokers). Raises ValueError for anything else."""
    market = (market or "IN").upper()

    if market == "IN":
        if creds:
            from broker_api import BrokerAPI
            return BrokerAPI(
                api_key=creds.get("api_key"),
                access_token=creds.get("access_token"),
                client_code=creds.get("client_code"),
                login_callback=creds.get("login_callback"),
            )
        from .mstock_adapter import MStockBroker
        return MStockBroker()

    if market == "US":
        if creds:
            from .ibkr_stub import IBKRBroker as IBKRStub
            return IBKRStub(**creds)
        from .ibkr_broker import IBKRBroker
        return IBKRBroker()

    raise ValueError(f"Unknown market: {market!r} (expected 'IN' or 'US')")
