import pytest
from datetime import datetime
from unittest.mock import MagicMock
from strategies.nifty_sip import NiftySIPStrategy

@pytest.fixture
def strategy():
    return NiftySIPStrategy(MagicMock())

def test_sip_day_trigger(strategy, monkeypatch):
    """
    PO Perspective: Ensure the bot buys on the specified SIP day.
    """
    # Force 'now' to be a Monday
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 1) # Jan 1, 2024 was a Monday
            
    monkeypatch.setattr('strategies.nifty_sip.datetime', MockDatetime)
    
    strategy.sip_day = "Monday"
    should_buy, reason = strategy.should_buy(250.0)
    
    assert should_buy is True
    assert "Weekly SIP Day" in reason

def test_dip_trigger(strategy, monkeypatch):
    """
    PO Perspective: Buy more if the price drops by the threshold (e.g., 2%).
    """
    # Force 'now' to be a Tuesday (not SIP day)
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)
            
    monkeypatch.setattr('strategies.nifty_sip.datetime', MockDatetime)
    
    strategy.sip_day = "Monday"
    strategy.dip_threshold = 2.0
    
    # Drops from 100 to 97 (3% drop > 2% threshold)
    should_buy, reason = strategy.should_buy(current_price=97.0, last_buy_price=100.0)
    
    assert should_buy is True
    assert "Buy the Dip" in reason

def test_no_trigger_on_normal_day(strategy, monkeypatch):
    """
    PO Perspective: Don't waste capital on random days without a dip.
    """
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2) # Tuesday
            
    monkeypatch.setattr('strategies.nifty_sip.datetime', MockDatetime)
    
    strategy.sip_day = "Monday"
    strategy.dip_threshold = 2.0
    
    # No dip (price increased)
    should_buy, reason = strategy.should_buy(current_price=105.0, last_buy_price=100.0)
    
    assert should_buy is False

def test_quantity_calculation(strategy):
    """
    QA Perspective: Verify integer math for share quantity calculation.
    """
    # 10,000 capital / 250 price = 40 shares
    assert strategy.calculate_quantity(10000, 250) == 40
    
    # 10,000 capital / 300 price = 33 shares (check truncation)
    assert strategy.calculate_quantity(10000, 300) == 33

def test_zero_price_handling(strategy):
    """
    QA Perspective: Handle the edge case of zero price gracefully.
    """
    assert strategy.calculate_quantity(10000, 0) == 0
    should_buy, reason = strategy.should_buy(0)
    assert should_buy is False
