import pytest
import logging
from unittest.mock import Mock, patch
from risk_manager import RiskManager

def test_daily_loss_limit_trigger(mock_settings):
    """
    PO Perspective: Ensure capital is protected when loss limit is hit.
    QA Perspective: Verify transition to circuit-breaker state.
    """
    # Setup: 10% loss limit, 1,00,000 capital
    mock_settings.get.side_effect = lambda key, default=None: {
        'risk_controls.daily_loss_limit_pct': 10,
        'capital.allocated_limit': 100000,
        'risk_controls.stop_loss_pct': 5,
        'risk_controls.profit_target_pct': 10,
        'risk_controls.catastrophic_stop_loss_pct': 20
    }.get(key, default)
    
    risk_mgr = RiskManager(mock_settings, Mock(), Mock())
    
    # Action: Portfolio drops to 85,000 (15% loss)
    triggered = risk_mgr.check_daily_loss_limit(85000)
    
    # Expectation: Circuit breaker triggered
    assert triggered is True
    assert risk_mgr.is_circuit_breaker_active() is True

def test_daily_loss_limit_safe(mock_settings):
    """
    PO Perspective: Don't stop trading if losses are within limits.
    """
    mock_settings.get.side_effect = lambda key, default=None: {
        'risk_controls.daily_loss_limit_pct': 10,
        'capital.allocated_limit': 100000,
        'risk_controls.stop_loss_pct': 5,
        'risk_controls.profit_target_pct': 10,
        'risk_controls.catastrophic_stop_loss_pct': 20
    }.get(key, default)
    
    risk_mgr = RiskManager(mock_settings, Mock(), Mock())
    
    # Action: Portfolio drops to 95,000 (5% loss, within 10% limit)
    triggered = risk_mgr.check_daily_loss_limit(95000)
    
    # Expectation: Circuit breaker NOT triggered
    assert triggered is False
    assert risk_mgr.is_circuit_breaker_active() is False

def test_stop_loss_detection(mock_settings):
    """
    PO Perspective: Automatically exit losing trades to prevent further decay.
    QA Perspective: Correct calculation of P&L % and trigger matching.
    """
    mock_settings.get.side_effect = lambda key, default=None: {
        'risk_controls.stop_loss_pct': 5,
        'risk_controls.profit_target_pct': 10,
        'risk_controls.catastrophic_stop_loss_pct': 20
    }.get(key, default)
    
    mock_db = Mock()
    # Mock position: Entry at 100
    mock_db.get_open_positions.return_value = [
        {'symbol': 'GOLDBEES', 'exchange': 'NSE', 'avg_entry_price': 100.0, 'net_quantity': 10}
    ]
    
    # Mock market data: Price at 94 (6% loss)
    mock_fetcher = Mock(return_value={'last_price': 94.0})
    
    risk_mgr = RiskManager(mock_settings, mock_db, mock_fetcher)
    
    # Action: Check positions
    # Need to patch kickstart and state_mgr because check_all_positions imports them
    with patch('kickstart.safe_get_live_positions_merged', return_value={}):
        actions = risk_mgr.check_all_positions()
    
    # Expectation: SELL action triggered for GOLDBEES due to Stop Loss
    assert len(actions) == 1
    assert actions[0]['symbol'] == 'GOLDBEES'
    assert actions[0]['action'] == 'SELL'
    assert "Stop Loss" in actions[0]['reason']

def test_profit_target_detection(mock_settings):
    """
    PO Perspective: Lock in profits when target is reached.
    """
    mock_settings.get.side_effect = lambda key, default=None: {
        'risk_controls.stop_loss_pct': 5,
        'risk_controls.profit_target_pct': 10,
        'risk_controls.catastrophic_stop_loss_pct': 20
    }.get(key, default)
    
    mock_db = Mock()
    # Mock position: Entry at 100
    mock_db.get_open_positions.return_value = [
        {'symbol': 'GOLDBEES', 'exchange': 'NSE', 'avg_entry_price': 100.0, 'net_quantity': 10}
    ]
    
    # Mock market data: Price at 111 (11% gain)
    mock_fetcher = Mock(return_value={'last_price': 111.0})
    
    risk_mgr = RiskManager(mock_settings, mock_db, mock_fetcher)
    
    with patch('kickstart.safe_get_live_positions_merged', return_value={}):
        actions = risk_mgr.check_all_positions()
    
    # Expectation: SELL action triggered for GOLDBEES due to Profit Target
    assert len(actions) == 1
    assert "Profit Target" in actions[0]['reason']

def test_handle_market_data_none(mock_settings):
    """
    QA Perspective: Test resilience to missing market data.
    """
    mock_db = Mock()
    mock_db.get_open_positions.return_value = [{'symbol': 'X', 'exchange': 'Y', 'avg_entry_price': 100, 'net_quantity': 1}]
    
    mock_fetcher = Mock(return_value=None)  # API Failure
    
    risk_mgr = RiskManager(mock_settings, mock_db, mock_fetcher)
    
    with patch('kickstart.safe_get_live_positions_merged', return_value={}):
        actions = risk_mgr.check_all_positions()
    
    # Expectation: No actions (can't determine risk without data), no crash
    assert len(actions) == 0
