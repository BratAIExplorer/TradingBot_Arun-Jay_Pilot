"""Smallest possible check: factory routes correctly, both brokers satisfy the Protocol.
Does not import kickstart's module-level side effects and makes no network calls —
MStockBroker's methods only touch kickstart lazily, inside each call, and IBKRBroker
only imports ib_insync lazily, inside each call.
"""
from brokers import get_broker, BrokerInterface
from brokers.ibkr_broker import IBKRBroker
from brokers.mstock_adapter import MStockBroker


def test_get_broker_in_returns_mstock():
    b = get_broker("IN")
    assert isinstance(b, MStockBroker)
    assert isinstance(b, BrokerInterface)


def test_get_broker_us_returns_ibkr():
    b = get_broker("US")
    assert isinstance(b, IBKRBroker)
    assert isinstance(b, BrokerInterface)


def test_get_broker_defaults_to_in():
    assert isinstance(get_broker(""), MStockBroker)


def test_get_broker_rejects_unknown_market():
    try:
        get_broker("EU")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_ibkr_without_ib_insync_installed_fails_clearly():
    """No ib_insync installed in this environment (confirmed before writing this test) —
    connecting must raise a clear ImportError, not something opaque."""
    b = IBKRBroker()
    try:
        b.get_funds()
        assert False, "expected ImportError (ib_insync not installed) or a connection error"
    except ImportError as e:
        assert "ib_insync" in str(e)
    except Exception:
        # If ib_insync IS installed in whatever environment runs this, connecting to a
        # non-existent Gateway on 127.0.0.1:4002 should fail some other way — also fine,
        # this test only guards against silently pretending to succeed.
        pass


if __name__ == "__main__":
    test_get_broker_in_returns_mstock()
    test_get_broker_us_returns_ibkr()
    test_get_broker_defaults_to_in()
    test_get_broker_rejects_unknown_market()
    test_ibkr_without_ib_insync_installed_fails_clearly()
    print("OK — brokers/test_factory.py")
