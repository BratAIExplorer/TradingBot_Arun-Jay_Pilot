"""
📊 Performance Analytics - Calculate Trading Metrics
Reuses database queries and adds benchmark comparison

Author: AI Agent (Google Gemini)  
Date: January 18, 2026
Design: Lean - only essential metrics, reuse existing code
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd


def get_nifty50_returns(days: int = 30) -> Dict:
    """
    Fetch Nifty 50 returns for benchmark comparison
    
    Args:
        days: Number of days lookback
    
    Returns:
        Dict with nifty returns and data
    """
    try:
        # Fetch Nifty 50 data
        nifty = yf.Ticker("^NSEI")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 5)  # Extra buffer
        
        hist = nifty.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 2:
            return {
                'available': False,
                'return_pct': 0,
                'error': 'Insufficient data'
            }
        
        # Calculate return
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        return_pct = ((end_price - start_price) / start_price) * 100
        
        return {
            'available': True,
            'return_pct': round(return_pct, 2),
            'start_price': round(start_price, 2),
            'end_price': round(end_price, 2),
            'days': len(hist)
        }
    
    except Exception as e:
        return {
            'available': False,
            'return_pct': 0,
            'error': str(e)[:100]
        }


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.06) -> float:
    """
    Calculate Sharpe Ratio (annualized)
    
    Args:
        returns: Series of daily returns
        risk_free_rate: Annual risk-free rate (default 6% for India)
    
    Returns:
        Sharpe ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # Annualize
    daily_rf = risk_free_rate / 252  # 252 trading days
    excess_returns = returns - daily_rf
    
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()
    
    if std_excess == 0:
        return 0.0
    
    sharpe = (mean_excess / std_excess) * (252 ** 0.5)  # Annualize
    return round(sharpe, 2)


def get_analytics_summary(db, days: int = 30) -> Dict:
    """
    Get comprehensive analytics summary
    Reuses database methods + adds calculations
    
    Args:
        db: TradesDatabase instance
        days: Lookback period
    
    Returns:
        Dict with all analytics
    """
    # 1. Get basic performance from database (REUSE!)
    perf = db.get_performance_summary(days=days)
    
    # 2. Get trade history for advanced metrics
    df = db.get_trade_history(days=days)
    
    # 3. Calculate daily P&L
    daily_pnl = {}
    if not df.empty and 'pnl_net' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        sells = df[df['action'] == 'SELL']
        daily_pnl = sells.groupby('date')['pnl_net'].sum().to_dict()
    
    # 4. Calculate Sharpe ratio
    sharpe = 0.0
    if daily_pnl:
        returns_series = pd.Series(list(daily_pnl.values()))
        sharpe = calculate_sharpe_ratio(returns_series)
    
    # 5. Get Nifty 50 benchmark
    nifty_data = get_nifty50_returns(days=days)
    
    # 6. Calculate outperformance
    bot_return = 0.0
    if perf['net_profit'] != 0 and 'total_invested' in locals():
        # Approximate total return (rough estimate)
        bot_return = perf['net_profit'] / 50000 * 100  # Assume ₹50k capital
    
    outperformance = bot_return - nifty_data.get('return_pct', 0) if nifty_data['available'] else 0
    
    # 7. Combine all metrics
    analytics = {
        # From database (reused)
        'total_trades': perf['total_trades'],
        'winning_trades': perf['winning_trades'],
        'losing_trades': perf['losing_trades'],
        'win_rate': perf['win_rate'],
        'net_profit': perf['net_profit'],
        'total_fees': perf['total_fees'],
        
        # Calculated
        'sharpe_ratio': sharpe,
        'nifty50_return': nifty_data.get('return_pct', 0),
        'bot_return': round(bot_return, 2),
        'outperformance': round(outperformance, 2),
        'benchmark_available': nifty_data['available'],
        
        # Period info
        'period_days': days,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    return analytics


# Testing
if __name__ == "__main__":
    print("🧪 Testing Analytics Module...\n")
    
    # Test 1: Nifty 50 returns
    print("Test 1: Nifty 50 Returns (30 days)")
    nifty = get_nifty50_returns(30)
    print(f"  Available: {nifty['available']}")
    if nifty['available']:
        print(f"  Return: {nifty['return_pct']}%")
    else:
        print(f"  Error: {nifty.get('error', 'Unknown')}")
    
    # Test 2: Sharpe ratio
    print("\nTest 2: Sharpe Ratio Calculation")
    test_returns = pd.Series([0.5, -0.2, 0.3, 0.1, -0.1, 0.4])
    sharpe = calculate_sharpe_ratio(test_returns)
    print(f"  Sharpe Ratio: {sharpe}")
    
    # Test 3: Full analytics (requires database)
    print("\nTest 3: Full Analytics")
    try:
        from database.trades_db import TradesDatabase
        db = TradesDatabase()
        analytics = get_analytics_summary(db, days=30)
        
        print("  Analytics Summary:")
        for key, value in analytics.items():
            print(f"    {key}: {value}")
    except Exception as e:
        print(f"  Skipped (no database): {e}")
    
    print("\n✅ Analytics module tests complete!")
