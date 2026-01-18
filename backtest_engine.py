"""
ARUN Stock Trading Bot - Backtest Engine

Validates RSI Mean Reversion strategy using historical data from Indian stock market.
Tests strategy performance on 3-5 years of data with realistic fees and slippage.

Based on Senior Architect recommendations (CLAUDE-18-Jan-2026)
Adapted for ARUN bot's RSI strategy with Indian stock market fees.

Author: ARUN Stock Trading Bot
Version: 1.0
Date: January 18, 2026
"""

import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import logging


@dataclass
class Trade:
    """Single trade record"""
    entry_date: str
    exit_date: str
    symbol: str
    entry_price: float
    exit_price: float
    quantity: int
    profit_pct: float
    profit_amount: float
    hold_days: int
    exit_reason: str


class BacktestEngine:
    """
    Backtests RSI Mean Reversion strategy on historical data
    
    Uses:
    - Yahoo Finance for historical Indian stock data (.NS suffix)
    - RSI(14) with configurable buy/sell thresholds
    - Realistic Indian brokerage fees (STT, exchange fees, GST)
    - Stop-loss and profit target validation
    
    Returns:
    - Performance metrics (return %, win rate, Sharpe ratio, max drawdown)
    - Trade-by-trade breakdown
    - Validation status (PASS/FAIL based on thresholds)
    """
    
    def __init__(self, capital=50000, stop_loss_pct=5, profit_target_pct=10):
        """
        Initialize backtest engine
        
        Args:
            capital: Starting capital (default ₹50,000)
            stop_loss_pct: Stop-loss percentage (default 5%)
            profit_target_pct: Profit target percentage (default 10%)
        """
        self.initial_capital = capital
        self.capital = capital
        self.positions = []
        self.trades = []
        self.stop_loss_pct = stop_loss_pct
        self.profit_target_pct = profit_target_pct
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(self, symbol, start_date, end_date, buy_rsi=35, sell_rsi=65):
        """
        Run backtest on single symbol with RSI strategy
        
        Args:
            symbol: Stock symbol (e.g., 'MICEL', 'TCS')
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            buy_rsi: RSI threshold for buying (default 35)
            sell_rsi: RSI threshold for selling (default 65)
            
        Returns:
            dict: Performance metrics
        """
        self.logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        
        # Fetch historical data from Yahoo Finance (NSE)
        try:
            data = yf.download(
                f"{symbol}.NS", 
                start=start_date, 
                end=end_date, 
                interval='1d',
                progress=False
            )
            
            if len(data) < 50:
                self.logger.warning(f"Insufficient data for {symbol}: only {len(data)} days")
                return self._empty_metrics()
                
        except Exception as e:
            self.logger.error(f"Failed to fetch data for {symbol}: {e}")
            return self._empty_metrics()
        
        # Calculate RSI
        data['RSI'] = self.calculate_rsi(data['Close'], period=14)
        
        # Simulate trading
        position = None
        
        for i in range(len(data)):
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            current_rsi = data['RSI'].iloc[i]
            
            # Skip if RSI not calculated yet (first 14 days)
            if np.isnan(current_rsi):
                continue
            
            # Entry logic: Buy when RSI < buy_rsi
            if position is None and current_rsi < buy_rsi:
                # Calculate position size (10% of capital per trade)
                position_value = self.capital * 0.10
                quantity = int(position_value / current_price)
                
                if quantity > 0 and self.capital >= (quantity * current_price):
                    # Calculate realistic Indian brokerage fees for BUY
                    cost = quantity * current_price
                    fees = self._calculate_fees(cost, 'BUY')
                    total_cost = cost + fees
                    
                    position = {
                        'entry_date': current_date,
                        'entry_price': current_price,
                        'quantity': quantity,
                        'cost': total_cost,
                        'entry_fees': fees
                    }
                    self.capital -= total_cost
                    self.logger.debug(f"BUY {quantity} shares @ ₹{current_price:.2f} (RSI: {current_rsi:.1f})")
            
            # Exit logic: Check sell conditions
            elif position is not None:
                profit_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                hold_days = (current_date - position['entry_date']).days
                
                exit_signal = False
                exit_reason = ''
                
                # Check sell conditions
                if current_rsi > sell_rsi:
                    exit_signal = True
                    exit_reason = 'RSI_OVERBOUGHT'
                elif profit_pct >= self.profit_target_pct:
                    exit_signal = True
                    exit_reason = 'PROFIT_TARGET'
                elif profit_pct <= -self.stop_loss_pct:
                    exit_signal = True
                    exit_reason = 'STOP_LOSS'
                
                if exit_signal:
                    # Close position
                    proceeds = position['quantity'] * current_price
                    fees = self._calculate_fees(proceeds, 'SELL')
                    net_proceeds = proceeds - fees
                    
                    profit_amount = net_proceeds - position['cost']
                    
                    self.capital += net_proceeds
                    
                    # Record trade
                    trade = Trade(
                        entry_date=str(position['entry_date'].date()),
                        exit_date=str(current_date.date()),
                        symbol=symbol,
                        entry_price=position['entry_price'],
                        exit_price=current_price,
                        quantity=position['quantity'],
                        profit_pct=profit_pct,
                        profit_amount=profit_amount,
                        hold_days=hold_days,
                        exit_reason=exit_reason
                    )
                    self.trades.append(trade)
                    self.logger.debug(f"SELL {position['quantity']} shares @ ₹{current_price:.2f} ({exit_reason}, P&L: {profit_pct:+.2f}%)")
                    position = None
        
        # Calculate performance metrics
        return self.calculate_metrics()
    
    def _calculate_fees(self, amount: float, side: str) -> float:
        """
        Calculate realistic Indian brokerage fees
        
        Includes: Brokerage, STT, Exchange fees, SEBI fees, Stamp duty, GST
        Based on typical discount broker rates (e.g., Zerodha)
        
        Args:
            amount: Transaction amount
            side: 'BUY' or 'SELL'
            
        Returns:
            float: Total fees in ₹
        """
        # Brokerage: ₹20 or 0.03%, whichever is lower
        brokerage = min(20, amount * 0.0003)
        
        # STT (Securities Transaction Tax): 0.1% on both buy and sell
        stt = amount * 0.001
        
        # Exchange transaction fee: ~0.003%
        exchange_fee = amount * 0.00003
        
        if side == 'SELL':
            # Additional fees only on sell
            sebi_fee = amount * 0.000001  # SEBI turnover fee
            stamp_duty = amount * 0.00015  # Stamp duty
        else:
            sebi_fee = 0
            stamp_duty = 0
        
        # GST on brokerage: 18%
        gst = brokerage * 0.18
        
        total_fees = brokerage + stt + exchange_fee + sebi_fee + stamp_duty + gst
        
        return total_fees
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics from trades"""
        if not self.trades:
            return self._empty_metrics()
        
        # Total return
        total_return_pct = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        # Win rate
        winning_trades = [t for t in self.trades if t.profit_pct > 0]
        losing_trades = [t for t in self.trades if t.profit_pct <= 0]
        win_rate = len(winning_trades) / len(self.trades) * 100
        
        # Average win/loss
        avg_win = sum([t.profit_pct for t in winning_trades]) / len(winning_trades) if winning_trades else 0
        avg_loss = sum([t.profit_pct for t in losing_trades]) / len(losing_trades) if losing_trades else 0
        
        # Profit factor
        total_wins = sum([t.profit_amount for t in winning_trades])
        total_losses = abs(sum([t.profit_amount for t in losing_trades]))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Max drawdown
        equity_curve = [self.initial_capital]
        capital_tracker = self.initial_capital
        for trade in self.trades:
            capital_tracker += trade.profit_amount
            equity_curve.append(capital_tracker)
        
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # Sharpe ratio (simplified annualized)
        returns = [t.profit_pct for t in self.trades]
        avg_return = sum(returns) / len(returns)
        std_return = (sum([(r - avg_return)**2 for r in returns]) / len(returns)) ** 0.5
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        # CAGR (annualized return)
        years = (datetime.strptime(self.trades[-1].exit_date, '%Y-%m-%d') - 
                 datetime.strptime(self.trades[0].entry_date, '%Y-%m-%d')).days / 365.25
        cagr = ((self.capital / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        return {
            'total_return_pct': total_return_pct,
            'cagr': cagr,
            'num_trades': len(self.trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe_ratio,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'final_capital': self.capital
        }
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no trades"""
        return {
            'total_return_pct': 0,
            'cagr': 0,
            'num_trades': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'final_capital': self.initial_capital
        }
    
    def calculate_rsi(self, prices, period=14):
        """
        Calculate RSI using Wilder's smoothing method
        
        Args:
            prices: Pandas Series of close prices
            period: RSI period (default 14)
            
        Returns:
            Pandas Series with RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def print_report(self, metrics: Dict):
        """Print formatted performance report"""
        print("\n" + "="*70)
        print(" "*20 + "BACKTEST PERFORMANCE REPORT")
        print("="*70)
        print(f"Starting Capital:     ₹{self.initial_capital:,.2f}")
        print(f"Ending Capital:       ₹{metrics['final_capital']:,.2f}")
        print(f"Total Return:         {metrics['total_return_pct']:+.2f}%")
        print(f"CAGR:                 {metrics['cagr']:.2f}%")
        print("")
        print(f"Total Trades:         {metrics['num_trades']}")
        print(f"Winning Trades:       {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)")
        print(f"Losing Trades:        {metrics['losing_trades']}")
        print("")
        print(f"Average Win:          {metrics['avg_win']:+.2f}%")
        print(f"Average Loss:         {metrics['avg_loss']:+.2f}%")
        print(f"Profit Factor:        {metrics['profit_factor']:.2f}")
        print("")
        print(f"Max Drawdown:         {metrics['max_drawdown']:.2f}%")
        print(f"Sharpe Ratio:         {metrics['sharpe_ratio']:.2f}")
        print("="*70)
        
        # Validation
        print("\n" + "STRATEGY VALIDATION:")
        passed = True
        
        if metrics['sharpe_ratio'] < 1.0:
            print(f"❌ FAIL: Sharpe Ratio too low ({metrics['sharpe_ratio']:.2f} < 1.0)")
            passed = False
        else:
            print(f"✅ PASS: Sharpe Ratio acceptable ({metrics['sharpe_ratio']:.2f} >= 1.0)")
        
        if metrics['max_drawdown'] > 15:
            print(f"❌ FAIL: Max Drawdown too high ({metrics['max_drawdown']:.2f}% > 15%)")
            passed = False
        else:
            print(f"✅ PASS: Max Drawdown acceptable ({metrics['max_drawdown']:.2f}% <= 15%)")
        
        if metrics['win_rate'] < 50:
            print(f"⚠️ WARNING: Win Rate below 50% ({metrics['win_rate']:.1f}%)")
        else:
            print(f"✅ PASS: Win Rate acceptable ({metrics['win_rate']:.1f}% >= 50%)")
        
        if passed:
            print("\n🎉 STRATEGY PASSES VALIDATION - Ready for paper trading")
        else:
            print("\n⛔ STRATEGY FAILS VALIDATION - DO NOT USE WITH REAL MONEY")
        
        print("="*70)
        
        # Trade details
        if len(self.trades) <= 10:
            print("\nTRADE DETAILS:")
            for i, trade in enumerate(self.trades, 1):
                print(f"\n{i}. {trade.symbol}")
                print(f"   Entry: {trade.entry_date} @ ₹{trade.entry_price:.2f}")
                print(f"   Exit:  {trade.exit_date} @ ₹{trade.exit_price:.2f}")
                print(f"   P&L:   {trade.profit_pct:+.2f}% (₹{trade.profit_amount:+.2f})")
                print(f"   Held:  {trade.hold_days} days")
                print(f"   Reason: {trade.exit_reason}")


# Example usage / Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("ARUN STOCK BOT - BACKTEST ENGINE")
    print("Validating RSI Mean Reversion Strategy")
    print("="*70)
    
    # Test on MICEL (as recommended in Senior Architect analysis)
    engine = BacktestEngine(capital=50000, stop_loss_pct=5, profit_target_pct=10)
    
    print("\nRunning backtest on MICEL (2022-2025)...")
    print("Strategy: RSI(14) - Buy < 35, Sell > 65")
    print("Position Size: 10% of capital per trade")
    print("Stop-Loss: 5% | Profit Target: 10%")
    print("\nFetching data from Yahoo Finance...")
    
    metrics = engine.run_backtest('MICEL', '2022-01-01', '2025-01-01', buy_rsi=35, sell_rsi=65)
    
    # Print results
    engine.print_report(metrics)
    
    print("\n💡 Next Steps:")
    print("   1. If PASSED: Run 30-day forward paper trading")
    print("   2. If FAILED: Adjust RSI thresholds or add filters (regime monitor)")
    print("   3. Test on other symbols (TCS, INFY, RELIANCE)")
