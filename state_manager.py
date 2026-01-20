"""
State Manager for ARUN Trading Bot
Persists bot state to survive restarts and crashes
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging


class StateManager:
    """
    Manages persistent bot state
    Saves to JSON file for crash recovery
    """
    
    def __init__(self, state_file: str = "bot_state.json"):
        self.state_file = state_file
        self.state = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """
        Load state from file or initialize empty
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logging.info(f"✅ State restored from {self.state_file}")
                    logging.info(f"   Last update: {state.get('last_update', 'Unknown')}")
                    return state
            except Exception as e:
                logging.error(f"❌ Error loading state: {e}")
                return self._empty_state()
        else:
            logging.info(f"📝 No existing state found, starting fresh")
            return self._empty_state()
    
    def _empty_state(self) -> Dict[str, Any]:
        """
        Create empty state structure
        """
        return {
            'positions': {},
            'portfolio_value': 0.0,
            'circuit_breaker_active': False,
            'daily_start_capital': 0.0,
            'last_update': None,
            'bot_started_at': datetime.now().isoformat(),
            'total_trades_today': 0
        }
    
    def save(self):
        """
        Save current state to file
        """
        try:
            self.state['last_update'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            logging.debug(f"💾 State saved to {self.state_file}")
            
        except Exception as e:
            logging.error(f"❌ Error saving state: {e}")
    
    def update_position(self, symbol: str, data: Dict[str, Any]):
        """
        Update position and auto-save
        """
        self.state['positions'][symbol] = {
            **data,
            'updated_at': datetime.now().isoformat()
        }
        self.save()
    
    def remove_position(self, symbol: str):
        """
        Remove position (after sell)
        """
        if symbol in self.state['positions']:
            del self.state['positions'][symbol]
            self.save()
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get position data for symbol
        """
        return self.state['positions'].get(symbol)
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """
        Get all positions
        """
        return self.state['positions']
    
    def update_portfolio_value(self, value: float):
        """
        Update total portfolio value
        """
        self.state['portfolio_value'] = value
        self.save()
    
    def set_circuit_breaker(self, active: bool):
        """
        Set circuit breaker status
        """
        self.state['circuit_breaker_active'] = active
        self.save()
    
    def is_circuit_breaker_active(self) -> bool:
        """
        Check if circuit breaker is active
        """
        return self.state['circuit_breaker_active']
    
    def reset_daily(self, start_capital: float):
        """
        Reset daily tracking (call at market open)
        """
        self.state['daily_start_capital'] = start_capital
        self.state['circuit_breaker_active'] = False
        self.state['total_trades_today'] = 0
        self.save()
        logging.info(f"🔄 Daily state reset. Start capital: ₹{start_capital:,.2f}")
    
    def increment_trade_count(self):
        """
        Increment today's trade counter
        """
        self.state['total_trades_today'] = self.state.get('total_trades_today', 0) + 1
        self.save()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get state summary for display
        """
        return {
            'positions_count': len(self.state['positions']),
            'portfolio_value': self.state.get('portfolio_value', 0),
            'circuit_breaker': self.state.get('circuit_breaker_active', False),
            'trades_today': self.state.get('total_trades_today', 0),
            'last_update': self.state.get('last_update'),
            'uptime': self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> str:
        """
        Calculate bot uptime
        """
        started_at = self.state.get('bot_started_at')
        if not started_at:
            return "Unknown"
        
        started = datetime.fromisoformat(started_at)
        now = datetime.now()
        delta = now - started
        
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if delta.days > 0:
            return f"{delta.days}d {hours}h {minutes}m"
        else:
            return f"{hours}h {minutes}m"
    
    # ============== HOLDINGS CACHE (MVP - Smart Session Persistence) ==============
    
    def cache_holdings(self, holdings_data: dict):
        """
        Cache broker holdings for instant display on next startup.
        Called after each successful API fetch.
        """
        self.state['broker_holdings'] = {
            'data': holdings_data,
            'fetched_at': datetime.now().isoformat(),
            'source': 'mStock API'
        }
        self.save()
        logging.debug(f"💾 Cached {len(holdings_data)} holdings")
    
    def get_cached_holdings(self) -> Dict[str, Any]:
        """
        Get cached holdings with staleness info.
        Returns: {'data': {...}, 'is_stale': bool, 'age_minutes': float}
        """
        cached = self.state.get('broker_holdings', {})
        if not cached or not cached.get('data'):
            return {'data': {}, 'is_stale': True, 'age_minutes': 999, 'fetched_at': None}
        
        fetched_at = cached.get('fetched_at')
        age_minutes = 999
        is_stale = True
        
        if fetched_at:
            try:
                fetched_dt = datetime.fromisoformat(fetched_at)
                age_seconds = (datetime.now() - fetched_dt).total_seconds()
                age_minutes = round(age_seconds / 60, 1)
                is_stale = age_minutes > 5  # Stale if > 5 minutes old
            except Exception:
                pass
        
        return {
            'data': cached.get('data', {}),
            'is_stale': is_stale,
            'age_minutes': age_minutes,
            'fetched_at': fetched_at
        }
    
    # ============== TOKEN VALIDATION TRACKING ==============
    
    def mark_token_validated(self):
        """
        Record successful token validation.
        Called after any successful API call that proves token is valid.
        """
        self.state['token_validation'] = {
            'last_validated': datetime.now().isoformat(),
            'validated_date': datetime.now().strftime('%Y-%m-%d')
        }
        self.save()
        logging.debug("🔐 Token marked as validated for today")
    
    def is_token_validated_today(self) -> bool:
        """
        Check if token was already validated today.
        Used to skip redundant validation on startup.
        """
        tv = self.state.get('token_validation', {})
        return tv.get('validated_date') == datetime.now().strftime('%Y-%m-%d')
    
    def get_token_validation_status(self) -> Dict[str, Any]:
        """
        Get detailed token validation status for UI display.
        """
        tv = self.state.get('token_validation', {})
        validated_today = self.is_token_validated_today()
        return {
            'validated_today': validated_today,
            'last_validated': tv.get('last_validated'),
            'status': '✅ Valid' if validated_today else '⚠️ Needs validation'
        }


# Global state instance
state = StateManager()


if __name__ == "__main__":
    # Test state manager
    print("\n=== Testing State Manager ===\n")
    
    # Create test instance
    test_state = StateManager("test_state.json")
    
    # Update position
    test_state.update_position("HDFCBANK", {
        'entry_price': 1600,
        'quantity': 10,
        'exchange': 'NSE'
    })
    
    # Update another
    test_state.update_position("TCS", {
        'entry_price': 3500,
        'quantity': 5,
        'exchange': 'NSE'
    })
    
    # Get position
    hdfc = test_state.get_position("HDFCBANK")
    print(f"HDFC Position: {hdfc}")
    
    # Get all
    all_positions = test_state.get_all_positions()
    print(f"\nAll Positions ({len(all_positions)}):")
    for symbol, data in all_positions.items():
        print(f"  {symbol}: {data}")
    
    # Set circuit breaker
    test_state.set_circuit_breaker(True)
    print(f"\nCircuit Breaker: {test_state.is_circuit_breaker_active()}")
    
    # Get summary
    summary = test_state.get_summary()
    print(f"\nState Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Remove position
    test_state.remove_position("TCS")
    print(f"\nPositions after removing TCS: {len(test_state.get_all_positions())}")
