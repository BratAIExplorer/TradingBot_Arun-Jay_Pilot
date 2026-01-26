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
    
    @property
    def stop_loss_pct(self):
        return self.settings.get('risk_controls.stop_loss_pct', 5)

    @property
    def profit_target_pct(self):
        return self.settings.get('risk_controls.profit_target_pct', 10)

    @property
    def catastrophic_stop_pct(self):
        return self.settings.get('risk_controls.catastrophic_stop_loss_pct', 20)

    @property
    def daily_loss_limit_pct(self):
        return self.settings.get('risk_controls.daily_loss_limit_pct', 10)

    def __init__(self, settings, database, market_data_fetcher):
        self.settings = settings
        self.db = database
        self.fetch_market_data = market_data_fetcher
        
        # Tracking
        self.daily_start_capital = settings.get('capital.allocated_limit', 0)
        self.circuit_breaker_triggered = False
        
        logging.info(f"✅ RiskManager initialized and synced to dynamic settings.")
    
    def check_all_positions(self) -> List[Dict]:
        """
        Check all open positions (Bot-initiated and Butler Mode manual positions)
        for stop-loss or profit target hits
        
        Returns list of actions to take.
        """
        actions = []
        
        # 1. Get BOT positions from database (respect paper trading mode)
        is_paper = self.settings.get("app_settings.paper_trading_mode", False) if self.settings else False
        db_positions = self.db.get_open_positions(is_paper=is_paper) if self.db else []
        
        # 2. Identify Manual positions to watch (Butler Mode)
        watched_symbols = self.settings.get("app_settings.watched_manual_positions", [])
        
        # We need live market data for all these as well
        # In a real environment, we'd fetch live holdings from the broker
        # For simplicity, we assume kickstart provides a way to get 'live_positions' 
        # but since RiskManager is independent, we check what it has.
        
        # If we have a way to get live holdings, we should use it.
        # Let's assume the caller (kickstart) might pass positions, 
        # or we fetch them here if we have access to the broker API.
        
        # CURRENT STRATEGY: 
        # The RiskManager currently focuses on DB positions.
        # To support Butler Mode, we need the live holdings details (avg price, qty).
        # We'll rely on the 'fetch_market_data' to get current prices,
        # but we still need the 'ENTRY price' for manual holdings.
        
        # Since manual holdings are NOT in the DB, we must fetch them from the broker.
        # This requires an update to the RiskManager constructor or a new method.
        # However, to keep it simple and within the current flow:
        # We will iterate through DB positions first.
        
        final_positions_to_check = []
        for p in db_positions:
            final_positions_to_check.append({
                'symbol': p['symbol'],
                'exchange': p['exchange'],
                'avg_entry_price': p['avg_entry_price'],
                'net_quantity': p['net_quantity'],
                'source': 'BOT'
            })
            
        # 3. Add Butler Mode positions if they exist in live holdings
        # HACK: In this context, we need to know what the live holdings are.
        # We can try to get them from kickstart (global) or fetch them.
        import kickstart
        try:
            live_holdings = kickstart.safe_get_live_positions_merged()
            for key, pos in live_holdings.items():
                sym = key[0] if isinstance(key, tuple) else str(key)
                if sym.upper() in [s.upper() for s in watched_symbols] and pos.get('source') == 'MANUAL':
                    # Check if already added via DB (shouldn't be, but safety first)
                    if not any(p['symbol'].upper() == sym.upper() for p in final_positions_to_check):
                        final_positions_to_check.append({
                            'symbol': sym,
                            'exchange': key[1] if isinstance(key, tuple) else 'NSE',
                            'avg_entry_price': pos.get('price', 0),
                            'net_quantity': pos.get('qty', 0),
                            'source': 'BUTLER'
                        })
        except Exception as e:
            logging.warning(f"⚠️ RiskManager: Could not fetch manual holdings for Butler Mode: {e}")

        if not final_positions_to_check:
            return actions
        
        logging.info(f"📊 Checking {len(final_positions_to_check)} positions (Bot + Butler) for risk triggers...")
        
        for pos_check in final_positions_to_check:
            symbol = pos_check['symbol']
            exchange = pos_check['exchange']
            entry_price = pos_check['avg_entry_price']
            quantity = pos_check['net_quantity']
            source = pos_check['source']
            
            if entry_price <= 0 or quantity == 0:
                continue

            # Fetch current price
            raw_data = self.fetch_market_data(symbol, exchange)
            if isinstance(raw_data, tuple): market_data = raw_data[0]
            else: market_data = raw_data
            
            if not market_data:
                continue
            
            current_price = market_data.get('lp', market_data.get('last_price', 0))
            if current_price == 0:
                continue
            
            # Calculate P&L
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            pnl_amount = (current_price - entry_price) * quantity
            
            # Risk Checks
            # 1. Catastrophic Stop
            if pnl_pct <= -self.catastrophic_stop_pct:
                actions.append({
                    'symbol': symbol, 'exchange': exchange, 'quantity': quantity,
                    'action': 'SELL', 'reason': f'🛑 CATASTROPHIC [{source}] ({pnl_pct:.1f}%)',
                    'priority': 'CRITICAL', 'current_price': current_price
                })
                continue
                
            # 2. Stop Loss
            # 2. Stop Loss
            if pnl_pct <= -self.stop_loss_pct:
                if self.settings.get('risk_controls.never_sell_at_loss', False) and pnl_pct < 0:
                    continue
                actions.append({
                    'symbol': symbol, 'exchange': exchange, 'quantity': quantity,
                    'action': 'SELL', 'reason': f'⛔ Stop Loss [{source}] ({pnl_pct:.1f}%)',
                    'priority': 'HIGH', 'current_price': current_price
                })
                continue
                
            # 3. Profit Target
            if pnl_pct >= self.profit_target_pct:
                actions.append({
                    'symbol': symbol, 'exchange': exchange, 'quantity': quantity,
                    'action': 'SELL', 'reason': f'🎯 Profit Target [{source}] ({pnl_pct:.1f}%)',
                    'priority': 'NORMAL', 'current_price': current_price
                })
        
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
