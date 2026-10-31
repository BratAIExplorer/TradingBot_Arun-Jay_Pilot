"""
Risk Manager for ARUN Trading Bot
Monitors positions and enforces risk controls (stop-loss, profit targets, daily limits)
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging


class RiskManager:
    """
    Manages risk controls: stop-loss, profit targets, daily loss limits
    """
    
    def __init__(self, settings, database, market_data_fetcher, state_manager=None):
        self.settings = settings
        self.db = database
        self.fetch_market_data = market_data_fetcher
        self.state_mgr = state_manager
        
        # Risk settings
        self.stop_loss_pct = settings.get('risk_controls.default_stop_loss_pct', 5)
        self.profit_target_pct = settings.get('risk_controls.default_profit_target_pct', 10)
        self.catastrophic_stop_pct = settings.get('risk_controls.catastrophic_stop_pct', 20)
        self.daily_loss_limit_pct = settings.get('capital.daily_loss_limit_pct', 10)
        
        # Tracking
        self.daily_start_capital = settings.get('capital.total_capital', 0)
        self.circuit_breaker_triggered = False
        
        logging.info(f"✅ RiskManager initialized: SL={self.stop_loss_pct}%, PT={self.profit_target_pct}%")
    
    def check_all_positions(self) -> List[Dict]:
        """
        Check all open positions for stop-loss or profit target hits
        
        Returns list of actions to take: [{'symbol': 'HDFC', 'action': 'SELL', 'reason': 'Stop Loss Hit'}]
        """
        actions = []
        
        # Get open positions from database
        db_positions = self.db.get_open_positions()
        
        # Get managed holdings from state manager (Butler Mode)
        managed_positions = []
        if self.state_mgr:
            managed_holdings = self.state_mgr.state.get('managed_holdings', {})
            cached_holdings = self.state_mgr.get_cached_holdings().get('data', {})
            
            for key_str, is_enabled in managed_holdings.items():
                if not is_enabled:
                    continue
                
                # key_str is likely "(symbol, exchange)" or "symbol:exchange" 
                # depending on how StateManager serializes it.
                # Let's try to parse it.
                try:
                    # state_manager.py line 271 uses "BAJFINANCE:NSE" format for serialization
                    if ':' in key_str:
                        symbol, exchange = key_str.split(':')
                    else:
                        # Fallback for old format or tuple string Repr
                        import ast
                        result = ast.literal_eval(key_str)
                        if isinstance(result, (list, tuple)):
                            symbol, exchange = result[0], result[1]
                        else:
                            symbol, exchange = str(result), 'NSE'
                    
                    symbol = symbol.upper()
                    exchange = exchange.upper()
                    
                    # Fetch quantity and avg price from cached holdings
                    pos_data = cached_holdings.get((symbol, exchange))
                    if pos_data:
                        managed_positions.append({
                            'symbol': symbol,
                            'exchange': exchange,
                            'avg_entry_price': float(pos_data.get('price', 0)),
                            'net_quantity': int(pos_data.get('qty', 0)),
                            'source': 'BUTLER'
                        })
                except Exception as e:
                    logging.warning(f"⚠️ Failed to parse managed holding key {key_str}: {e}")

        all_positions = db_positions + managed_positions
        
        if not all_positions:
            return actions
        
        logging.info(f"📊 Checking {len(all_positions)} positions (DB: {len(db_positions)}, Managed: {len(managed_positions)}) for risk triggers...")
        
        for position in all_positions:
            symbol = position['symbol']
            exchange = position['exchange']
            entry_price = position['avg_entry_price']
            quantity = position['net_quantity']
            
            # Fetch current price
            market_data = self.fetch_market_data(symbol, exchange)
            
            if not market_data:
                logging.warning(f"⚠️ Could not fetch price for {symbol}, skipping risk check")
                continue
            
            current_price = market_data.get('lp', 0)  # Last price
            
            if current_price == 0:
                continue
            
            # Calculate P&L
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            pnl_amount = (current_price - entry_price) * quantity
            
            logging.info(f"  {symbol}: Entry ₹{entry_price:.2f} → Current ₹{current_price:.2f} = {pnl_pct:+.2f}%")
            
            # Check catastrophic stop (ALWAYS takes priority)
            if pnl_pct <=-self.catastrophic_stop_pct:
                actions.append({
                    'symbol': symbol,
                    'exchange': exchange,
                    'quantity': quantity,
                    'action': 'SELL',
                    'reason': f'🛑 CATASTROPHIC STOP ({pnl_pct:.1f}%)',
                    'priority': 'CRITICAL',
                    'pnl_pct': pnl_pct,
                    'pnl_amount': pnl_amount,
                    'current_price': current_price
                })
                logging.error(f"  🛑 CATASTROPHIC STOP: {symbol} down {pnl_pct:.1f}%!")
                continue
            
            # Check stop-loss (with never-sell-at-loss override)
            if pnl_pct <= -self.stop_loss_pct:
                # Check if never-sell-at-loss is enabled
                never_sell_at_loss = self.settings.get('risk.never_sell_at_loss', False)
                
                if never_sell_at_loss and pnl_pct < 0:
                    logging.warning(f"  ⚠️ Stop-loss ignored for {symbol} ({pnl_pct:.1f}%) - Never Sell at Loss enabled")
                    continue  # Skip stop-loss, position remains open
                
                # Proceed with normal stop-loss
                actions.append({
                    'symbol': symbol,
                    'exchange': exchange,
                    'quantity': quantity,
                    'action': 'SELL',
                    'reason': f'⛔ Stop Loss Hit ({pnl_pct:.1f}%)',
                    'priority': 'HIGH',
                    'pnl_pct': pnl_pct,
                    'pnl_amount': pnl_amount,
                    'current_price': current_price
                })
                logging.warning(f"  ⛔ STOP LOSS: {symbol} down {pnl_pct:.1f}%")
                continue
            
            # Check profit target
            if pnl_pct >= self.profit_target_pct:
                actions.append({
                    'symbol': symbol,
                    'exchange': exchange,
                    'quantity': quantity,
                    'action': 'SELL',
                    'reason': f'🎯 Profit Target Hit ({pnl_pct:.1f}%)',
                    'priority': 'NORMAL',
                    'pnl_pct': pnl_pct,
                    'pnl_amount': pnl_amount,
                    'current_price': current_price
                })
                logging.info(f"  🎯 PROFIT TARGET: {symbol} up {pnl_pct:.1f}%!")
        
        if actions:
            logging.info(f"⚠️ Risk Manager found {len(actions)} positions to close")
        else:
            logging.info(f"✅ All positions within acceptable risk")
        
        return actions
    
    def check_daily_loss_limit(self, current_portfolio_value: float) -> bool:
        """
        Check if daily loss limit has been hit
        
        Returns True if circuit breaker should activate
        """
        daily_pnl = current_portfolio_value - self.daily_start_capital
        daily_pnl_pct = (daily_pnl / self.daily_start_capital) * 100
        
        if daily_pnl_pct <= -self.daily_loss_limit_pct:
            if not self.circuit_breaker_triggered:
                self.circuit_breaker_triggered = True
                logging.error(f"🚨 DAILY LOSS LIMIT HIT: {daily_pnl_pct:.1f}% (Limit: {self.daily_loss_limit_pct}%)")
                logging.error(f"🛑 CIRCUIT BREAKER ACTIVATED - No more trades today!")
            return True
        
        # Log progress towards limit
        limit_used_pct = abs(daily_pnl_pct / self.daily_loss_limit_pct) * 100
        if daily_pnl < 0:
            logging.info(f"📊 Daily loss: {daily_pnl_pct:.2f}% ({limit_used_pct:.0f}% of limit used)")
        
        return False
    
    def is_circuit_breaker_active(self) -> bool:
        """
        Check if circuit breaker is currently active
        """
        return self.circuit_breaker_triggered
    
    def reset_daily_limits(self):
        """
        Reset daily tracking (call at start of new trading day)
        """
        self.daily_start_capital = self.settings.get('capital.total_capital', 0)
        self.circuit_breaker_triggered = False
        logging.info(f"🔄 Daily limits reset. Start capital: ₹{self.daily_start_capital:,.2f}")
    
    def get_position_risk_summary(self, symbol: str, exchange: str) -> Optional[Dict]:
        """
        Get risk metrics for a specific position
        """
        positions = self.db.get_open_positions()
        
        for position in positions:
            if position['symbol'] == symbol and position['exchange'] == exchange:
                entry_price = position['avg_entry_price']
                quantity = position['net_quantity']
                
                # Fetch current price
                market_data = self.fetch_market_data(symbol, exchange)
                if not market_data:
                    return None
                
                current_price = market_data.get('lp', 0)
                
                # Calculate levels
                stop_loss_price = entry_price * (1 - self.stop_loss_pct / 100)
                profit_target_price = entry_price * (1 + self.profit_target_pct / 100)
                catastrophic_stop_price = entry_price * (1 - self.catastrophic_stop_pct / 100)
                
                current_pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Distance to triggers
                dist_to_sl = ((current_price - stop_loss_price) / entry_price) * 100
                dist_to_pt = ((profit_target_price - current_price) / entry_price) * 100
                
                return {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'quantity': quantity,
                    'current_pnl_pct': current_pnl_pct,
                    'stop_loss_price': stop_loss_price,
                    'profit_target_price': profit_target_price,
                    'catastrophic_stop_price': catastrophic_stop_price,
                    'distance_to_stop_loss_pct': dist_to_sl,
                    'distance_to_profit_target_pct': dist_to_pt,
                    'risk_status': self._get_risk_status(current_pnl_pct)
                }
        
        return None
    
    def _get_risk_status(self, pnl_pct: float) -> str:
        """
        Determine risk status based on P&L
        """
        if pnl_pct <= -self.catastrophic_stop_pct:
            return "CRITICAL"
        elif pnl_pct <= -self.stop_loss_pct * 0.8:  # 80% of stop-loss
            return "WARNING"
        elif pnl_pct >= self.profit_target_pct * 0.8:  # 80% of profit target
            return "NEAR_TARGET"
        elif pnl_pct >= 0:
            return "PROFIT"
        else:
            return "NORMAL"


if __name__ == "__main__":
    # Test Risk Manager
    print("\n=== Testing Risk Manager ===\n")
    
    # Mock dependencies
    from settings_manager import SettingsManager
    from database.trades_db import TradesDatabase
    
    settings = SettingsManager()
    db = TradesDatabase("database/test_trades.db")
    
    # Mock market data fetcher
    def mock_fetch_market_data(symbol, exchange):
        # Simulate price data
        prices = {
            'HDFCBANK': {'lp': 1520},  # Down from 1600 entry = -5% (stop-loss!)
            'TCS': {'lp': 3850},       # Up from 3500 entry = +10% (profit target!)
        }
        return prices.get(symbol, {'lp': 0})
    
    # Create risk manager
    risk_mgr = RiskManager(settings, db, mock_fetch_market_data)
    
    # Add some test positions to database
    db.insert_trade(
        symbol="HDFCBANK",
        exchange="NSE",
        action="BUY",
        quantity=10,
        price=1600,
        gross_amount=16000,
        total_fees=30,
        net_amount=16030
    )
    
    db.insert_trade(
        symbol="TCS",
        exchange="NSE",
        action="BUY",
        quantity=5,
        price=3500,
        gross_amount=17500,
        total_fees=35,
        net_amount=17535
    )
    
    # Check all positions
    print("\n--- Risk Check ---")
    actions = risk_mgr.check_all_positions()
    
    for action in actions:
        print(f"\n{action['reason']}")
        print(f"  Symbol: {action['symbol']}")
        print(f"  P&L: {action['pnl_pct']:.2f}% (₹{action['pnl_amount']:.2f})")
        print(f"  Action: {action['action']} {action['quantity']} @ ₹{action['current_price']:.2f}")
        print(f"  Priority: {action['priority']}")
    
    # Check daily loss limit
    print("\n--- Daily Loss Limit Check ---")
    current_portfolio = 48000  # Down ₹2,000 from ₹50,000 = -4%
    circuit_breaker = risk_mgr.check_daily_loss_limit(current_portfolio)
    print(f"Circuit Breaker Active: {circuit_breaker}")
    
    # Get position risk summary
    print("\n--- Position Risk Summary (HDFCBANK) ---")
    risk_summary = risk_mgr.get_position_risk_summary("HDFCBANK", "NSE")
    if risk_summary:
        for key, value in risk_summary.items():
            print(f"{key}: {value}")
    
    db.close()
