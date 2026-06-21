"""Test broker interface conformance - Phase 0 validation."""

import pytest

from brokers.factory import get_broker
from brokers.interface import BrokerInterface
from brokers.ibkr_stub import IBKRBroker


class TestBrokerInterfaceConformance:
    """Verify both BrokerAPI (mStock) and IBKRBroker satisfy BrokerInterface Protocol."""

    def test_broker_api_conforms_to_interface(self):
        """BrokerAPI (mStock) satisfies BrokerInterface structurally."""
        from broker_api import BrokerAPI

        # Create a dummy instance (won't connect without credentials)
        mock_broker = BrokerAPI(
            api_key="test",
            access_token="test",
            client_code="test",
            login_callback=None,
        )

        # Runtime check: all required methods exist with correct signatures
        assert isinstance(mock_broker, BrokerInterface), (
            "BrokerAPI must satisfy BrokerInterface Protocol"
        )

        # Verify each method is callable
        assert callable(mock_broker.get_funds)
        assert callable(mock_broker.get_holdings)
        assert callable(mock_broker.get_positions)
        assert callable(mock_broker.get_orders)
        assert callable(mock_broker.get_quote)
        assert callable(mock_broker.place_order)
        assert callable(mock_broker.get_historical_data)

    def test_ibkr_stub_conforms_to_interface(self):
        """IBKRBroker (stub) satisfies BrokerInterface structurally."""
        ibkr = IBKRBroker()

        # Runtime check
        assert isinstance(ibkr, BrokerInterface), (
            "IBKRBroker must satisfy BrokerInterface Protocol"
        )

        # Verify each method exists
        assert callable(ibkr.get_funds)
        assert callable(ibkr.get_holdings)
        assert callable(ibkr.get_positions)
        assert callable(ibkr.get_orders)
        assert callable(ibkr.get_quote)
        assert callable(ibkr.place_order)
        assert callable(ibkr.get_historical_data)

    def test_factory_routes_to_mstock_for_india(self):
        """get_broker('IN') returns mStock BrokerAPI conforming to interface."""
        from broker_api import BrokerAPI

        broker = get_broker(
            "IN",
            api_key="test",
            access_token="test",
            client_code="test",
            login_callback=None,
        )

        assert isinstance(broker, BrokerInterface)
        assert isinstance(broker, BrokerAPI), "IN market should route to BrokerAPI"

    def test_factory_routes_to_stub_for_us(self):
        """get_broker('US') returns IBKR stub conforming to interface."""
        broker = get_broker("US")

        assert isinstance(broker, BrokerInterface)
        assert isinstance(broker, IBKRBroker), "US market should route to IBKRBroker"

    def test_factory_case_insensitive(self):
        """get_broker('in') and get_broker('IN') both work."""
        broker_lower = get_broker("in")
        broker_upper = get_broker("IN")

        assert isinstance(broker_lower, BrokerInterface)
        assert isinstance(broker_upper, BrokerInterface)

    def test_factory_defaults_to_india(self):
        """get_broker(None) defaults to India market."""
        broker = get_broker(None)
        assert isinstance(broker, BrokerInterface)

    def test_factory_rejects_unknown_market(self):
        """get_broker('XX') raises ValueError for unknown market."""
        with pytest.raises(ValueError, match="Unknown market"):
            get_broker("XX")

    def test_ibkr_stub_raises_on_method_calls(self):
        """All IBKRBroker methods raise NotImplementedError (Phase 0)."""
        ibkr = IBKRBroker()

        with pytest.raises(NotImplementedError):
            ibkr.get_funds()

        with pytest.raises(NotImplementedError):
            ibkr.get_holdings()

        with pytest.raises(NotImplementedError):
            ibkr.get_positions()

        with pytest.raises(NotImplementedError):
            ibkr.get_orders()

        with pytest.raises(NotImplementedError):
            ibkr.get_quote("TEST", "SMART")

        with pytest.raises(NotImplementedError):
            ibkr.place_order(
                "TEST",
                "SMART",
                "BUY",
                100,
            )

        with pytest.raises(NotImplementedError):
            ibkr.get_historical_data("SMART", None, "1min", "2025-01-01", "2025-01-31")
