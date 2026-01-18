"""
Base Strategy Interface for ARUN Trading Bot
All trading strategies must inherit from this base class.
This ensures consistency and enables multi-strategy support in the future.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Provides common interface and utilities that all strategies must implement.
    This enables the bot to run multiple strategies simultaneously and track
    performance independently.
    """
    
    def __init__(self, name: str, settings: Any, risk_manager: Any):
        """
        Initialize the strategy.
        
        Args:
            name: Unique identifier for this strategy (e.g., "RSI_MEAN_REVERSION")
            settings: SettingsManager instance for configuration
            risk_manager: RiskManager instance for position sizing and limits
        """
        self.name = name
        self.settings = settings
        self.risk_manager = risk_manager
        self.enabled = True
        
        # Performance tracking
        self.positions_opened = 0
        self.positions_closed = 0
        self.total_pnl = 0.0
        self.wins = 0
        self.losses = 0
    
    @abstractmethod
    def should_buy(self, symbol: str, exchange: str, market_data: Dict) -> bool:
        """
        Determine if this strategy should buy the given symbol.
        
        Args:
            symbol: Stock symbol (e.g., "HDFC")
            exchange: Exchange name (e.g., "NSE")
            market_data: Dict containing price, volume, indicators, etc.
        
        Returns:
            True if strategy signals BUY, False otherwise
        """
        pass
    
    @abstractmethod
    def should_sell(self, symbol: str, exchange: str, position: Dict, market_data: Dict) -> bool:
        """
        Determine if this strategy should sell an existing position.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange name
            position: Dict containing entry_price, quantity, entry_time, etc.
            market_data: Current market data
        
        Returns:
            True if strategy signals SELL, False otherwise
        """
        pass
    
    def get_position_size(self, symbol: str, price: float, allocated_capital: float) -> float:
        """
        Calculate position size for this trade.
        
        Default implementation uses strategy's allocation percentage.
        Strategies can override for custom position sizing logic.
        
        Args:
            symbol: Stock symbol
            price: Current price
            allocated_capital: Total capital allocated to this strategy
        
        Returns:
            Position size in rupees
        """
        try:
            # Default: use per-stock percentage from settings
            per_stock_pct = float(self.settings.get("capital.max_per_stock_value", 10.0))
            return (per_stock_pct / 100.0) * allocated_capital
        except:
            # Fallback: 10% of allocated capital
            return 0.10 * allocated_capital
    
    def get_stop_loss(self, entry_price: float) -> float:
        """
        Calculate stop-loss price for this position.
        
        Args:
            entry_price: Entry price of position
        
        Returns:
            Stop-loss price
        """
        try:
            sl_pct = float(self.settings.get("risk.stop_loss_pct", 5.0))
            return entry_price * (1 - sl_pct / 100.0)
        except:
            return entry_price * 0.95  # Default 5% SL
    
    def get_profit_target(self, entry_price: float) -> float:
        """
        Calculate profit target price for this position.
        
        Args:
            entry_price: Entry price of position
        
        Returns:
            Profit target price
        """
        try:
            pt_pct = float(self.settings.get("risk.profit_target_pct", 10.0))
            return entry_price * (1 + pt_pct / 100.0)
        except:
            return entry_price * 1.10  # Default 10% PT
    
    def update_performance(self, trade_result: float):
        """
        Update strategy performance metrics after a trade.
        
        Args:
            trade_result: P&L from the closed trade
        """
        self.positions_closed += 1
        self.total_pnl += trade_result
        
        if trade_result > 0:
            self.wins += 1
        else:
            self.losses += 1
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.positions_closed == 0:
            return 0.0
        return (self.wins / self.positions_closed) * 100.0
    
    def get_performance_summary(self) -> Dict:
        """
        Get performance summary for this strategy.
        
        Returns:
            Dict with performance metrics
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "positions_opened": self.positions_opened,
            "positions_closed": self.positions_closed,
            "total_pnl": self.total_pnl,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.get_win_rate()
        }
    
    def __str__(self):
        return f"Strategy({self.name}, Enabled={self.enabled}, P&L=₹{self.total_pnl:.2f})"


# Example: RSI Mean Reversion Strategy (to be extracted from kickstart.py later)
class RSIMeanReversionStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy
    
    Buy when RSI < buy_threshold (oversold)
    Sell when RSI > sell_threshold (overbought)
    """
    
    def __init__(self, settings, risk_manager):
        super().__init__("RSI_MEAN_REVERSION", settings, risk_manager)
        
        # Load strategy-specific settings
        self.buy_threshold = float(settings.get("strategies.rsi_mean_reversion.buy_rsi_threshold", 35))
        self.sell_threshold = float(settings.get("strategies.rsi_mean_reversion.sell_rsi_threshold", 65))
        self.rsi_period = int(settings.get("strategies.rsi_mean_reversion.rsi_period", 14))
    
    def should_buy(self, symbol: str, exchange: str, market_data: Dict) -> bool:
        """Buy when RSI is oversold (< buy_threshold)"""
        try:
            rsi = market_data.get("rsi", None)
            if rsi is None:
                return False
            
            return rsi < self.buy_threshold
        except:
            return False
    
    def should_sell(self, symbol: str, exchange: str, position: Dict, market_data: Dict) -> bool:
        """Sell when RSI is overbought (> sell_threshold)"""
        try:
            rsi = market_data.get("rsi", None)
            if rsi is None:
                return False
            
            # Check if RSI signals sell
            if rsi < self.sell_threshold:
                return False
            
            # Additional check: Never sell below entry price (if enabled)
            never_sell_at_loss = self.settings.get("risk.never_sell_at_loss", False)
            if never_sell_at_loss:
                current_price = market_data.get("ltp", 0)
                entry_price = position.get("entry_price", 0)
                if current_price <= entry_price:
                    return False  # Hold, don't sell at loss
            
            return True
        except:
            return False
