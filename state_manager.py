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
