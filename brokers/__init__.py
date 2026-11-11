"""Broker abstraction — routes a market code to a concrete broker implementation.

Ported in shape from Project Vayu's brokers/ (Protocol-based, get_broker(market) factory).
Additive only: nothing in kickstart.py has been changed to use this yet. The live bot
still calls place_order()/fetch_funds()/etc. directly. Wiring kickstart.py's call sites
behind get_broker() is deferred to when IBKR is implemented and tested in paper mode —
touching the live order-placement path is the risky part, and it should happen once,
alongside real IBKR code, not twice.
"""
from .factory import get_broker
from .interface import BrokerInterface

__all__ = ["get_broker", "BrokerInterface"]
