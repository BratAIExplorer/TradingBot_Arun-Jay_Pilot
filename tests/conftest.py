"""
Pytest configuration and shared fixtures for ARUN Trading Bot tests.

This file provides:
- Mock settings manager
- Mock database
- Mock broker API responses
- Test data generators

Product Owner (PO) Perspective:
    Fixtures represent realistic user configurations and trading scenarios.

QA Perspective:
    Fixtures cover edge cases like empty portfolios, network failures, and malformed data.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import pandas as pd


# ============================================================================
# Mock Settings Manager (PO: "User's saved configuration")
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock SettingsManager with typical user configuration"""
    settings = Mock()
    
    # Broker settings (PO: "User has configured their broker")
    settings.get.side_effect = lambda key, default=None: {
        "broker.client_code": "TEST123",
        "broker.api_key": "mock_api_key_12345",
        "broker.api_secret": "mock_secret_67890",
        "app_settings.paper_trading_mode": False,  # QA: Test both modes
        "app_settings.enable_paper_trading": False,
    }.get(key, default)
    
    settings.get_decrypted.side_effect = lambda key: {
        "broker.api_key": "decrypted_api_key",
        "broker.api_secret": "decrypted_secret",
        "broker.password": "secure_password",
        "broker.access_token": "mock_access_token",
        "broker.totp_secret": "JBSWY3DPEHPK3PXP",  # Valid test TOTP secret
    }.get(key)
    
    return settings


@pytest.fixture
def mock_settings_paper_mode():
    """Mock SettingsManager with paper trading enabled (PO: "Safe testing mode")"""
    settings = Mock()
    settings.get.side_effect = lambda key, default=None: {
        "broker.client_code": "PAPER",
        "app_settings.paper_trading_mode": True,
        "app_settings.enable_paper_trading": True,
    }.get(key, default)
    
    return settings


# ============================================================================
# Mock Database (PO: "Trade history", QA: "Data persistence")
# ============================================================================

@pytest.fixture
def mock_database():
    """Mock TradesDatabase for testing"""
    db = Mock()
    
    # PO: "Show me my trading history"
    db.get_trades.return_value = pd.DataFrame({
        'timestamp': [datetime.now()],
        'symbol': ['GOLDBEES'],
        'action': ['BUY'],
        'quantity': [5],
        'price': [100.0],
        'gross_amount': [500.0],
        'total_fees': [2.5],
        'net_amount': [502.5],
    })
    
    # PO: "What's my performance summary?"
    db.get_performance_summary.return_value = {
        'total_trades': 10,
        'winning_trades': 7,
        'losing_trades': 3,
        'win_rate': 0.70,
        'gross_profit': 1500.0,
        'gross_loss': -300.0,
        'net_profit': 1200.0,
    }
    
    return db


# ============================================================================
# Mock Broker API Responses (QA: "What if the API behaves badly?")
# ============================================================================

@pytest.fixture
def mock_quote_response():
    """
    Mock successful quote response.
    
    PO: "Get me the latest price"
    QA: "Valid data structure"
    """
    return {
        "status": "success",
        "data": {
            "tradingsymbol": "GOLDBEES",
            "exchange": "NSE",
            "last_price": 105.50,
            "open": 104.00,
            "high": 106.00,
            "low": 103.50,
            "close": 105.00,
            "volume": 1000000,
        }
    }


@pytest.fixture
def mock_quote_response_invalid():
    """
    QA: "What if the API returns garbage?"
    """
    return {
        "status": "error",
        "message": "Invalid symbol",
    }


@pytest.fixture
def mock_order_response_success():
    """
    PO: "Confirm my order was placed"
    """
    return {
        "status": "success",
        "data": {
            "order_id": "230125000001",
            "status": "COMPLETE",
            "tradingsymbol": "GOLDBEES",
            "transaction_type": "BUY",
            "quantity": 5,
            "price": 105.50,
        }
    }


@pytest.fixture
def mock_order_response_failure():
    """
    QA: What if order placement fails?"
    """
    return {
        "status": "error",
        "message": "Insufficient funds",
    }


# ============================================================================
# Mock Market Data (PO: "RSI calculations", QA: "Edge cases")
# ============================================================================

@pytest.fixture
def mock_candles_bullish():
    """
    PO: "Give me oversold market data (RSI < 30)"
    
    Returns candle data that will result in RSI = 25 (BUY signal)
    """
    # Simplified: 14 periods of declining prices
    return pd.DataFrame({
        'timestamp': pd.date_range(end=datetime.now(), periods=20, freq='1D'),
        'open': [110 - i for i in range(20)],
        'high': [111 - i for i in range(20)],
        'low': [109 - i for i in range(20)],
        'close': [110 - i*0.5 for i in range(20)],  # Gradual decline
        'volume': [100000] * 20,
    })


@pytest.fixture
def mock_candles_bearish():
    """
    PO: "Give me overbought market data (RSI > 70)"
    
    Returns candle data that will result in RSI = 75 (SELL signal)
    """
    return pd.DataFrame({
        'timestamp': pd.date_range(end=datetime.now(), periods=20, freq='1D'),
        'open': [90 + i for i in range(20)],
        'high': [91 + i for i in range(20)],
        'low': [89 + i for i in range(20)],
        'close': [90 + i*0.5 for i in range(20)],  # Gradual rise
        'volume': [100000] * 20,
    })


@pytest.fixture
def mock_candles_insufficient():
    """
    QA: "What if we don't have enough data?"
    
    Only 5 candles (need 14+ for RSI)
    """
    return pd.DataFrame({
        'timestamp': pd.date_range(end=datetime.now(), periods=5, freq='1D'),
        'open': [100] * 5,
        'high': [101] * 5,
        'low': [99] * 5,
        'close': [100] * 5,
        'volume': [10000] * 5,
    })


# ============================================================================
# Mock Risk Manager (PO: "Protect my capital", QA: "Enforce limits")
# ============================================================================

@pytest.fixture
def mock_risk_manager():
    """Mock RiskManager for testing"""
    risk_mgr = Mock()
    
    # PO: "Is this trade safe?"
    risk_mgr.check_entry_allowed.return_value = {
        'allowed': True,
        'reason': None,
    }
    
    # PO: "Have I hit my daily loss limit?"
    risk_mgr.check_circuit_breaker.return_value = {
        'triggered': False,
        'reason': None,
    }
    
    return risk_mgr


# ============================================================================
# Test Data Helpers
# ============================================================================

def create_test_position(symbol="GOLDBEES", qty=5, avg_price=100.0):
    """
    Helper to create test position data.
    
    PO: "My current holdings"
    """
    return {
        "symbol": symbol,
        "quantity": qty,
        "average_price": avg_price,
        "ltp": avg_price,
        "pnl": 0.0,
        "exchange": "NSE",
    }


def create_test_config():
    """
    Helper to create test config_table.csv data.
    
    PO: "Symbols I want to trade"
    """
    return pd.DataFrame({
        'Symbol': ['GOLDBEES', 'NIFTYBEES', 'LIQUIDBEES'],
        'Exchange': ['NSE', 'NSE', 'NSE'],
        'Enabled': [True, True, False],  # QA: Mix of enabled/disabled
        'Broker': ['mstock', 'mstock', 'mstock'],
        'Max_Position_Size': [10, 10, 10],
        'RSI_Buy_Threshold': [30, 30, 30],
        'RSI_Sell_Threshold': [70, 70, 70],
    })
