"""Broker abstraction layer for multi-market support (mStock + IBKR)."""

from .factory import get_broker
from .interface import BrokerInterface

__all__ = ["get_broker", "BrokerInterface"]
