"""
📈 Trend Filter - Prevent Buying in Downtrends  
Only buy stocks trading above 200-day Moving Average

Author: AI Agent (Google Gemini)
Date: January 18, 2026  
Design Principle: User control first, safe by default  

Senior Architect Recommendation (Lines 4241-4266):
> "Only buy when price above 200 DMA - reduces losses in bear markets by 40%"
"""

from typing import Tuple, Optional
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def check_trend_filter(
    symbol: str,
    exchange: str,
    current_price: float,
    settings: Optional[object] = None
) -> Tuple[bool, str]:
    """
    Check if stock price is above 200-day moving average
    
    Args:
        symbol: Stock symbol (e.g., "TCS")
        exchange: Exchange (e.g., "NSE")
        current_price: Current market price
        settings: Settings manager instance
    
    Returns:
        (can_buy, reason)
        - can_buy: True if allowed to buy, False if in downtrend
        - reason: Human-readable explanation
    
    Examples:
        >>> check_trend_filter("TCS.NS", "NSE", 3500, None)
        (True, "Price above 200 DMA (bullish trend)")
        
        >>> check_trend_filter("DOWNTREND.NS", "NSE", 100, None)
        (False, "Price below 200 DMA: ₹100 < ₹120 (bearish trend)")
    """
    
    # 1. Check if trend filter is enabled
    if settings:
        trend_filter_enabled = settings.get("risk.trend_filter_enabled", True)
    else:
        trend_filter_enabled = True  # Safe default
    
    if not trend_filter_enabled:
        return (True, "Trend filter disabled by user")
    
    try:
        # 2. Build yfinance ticker symbol
        # NSE stocks need .NS suffix, BSE needs .BO
        if exchange == "NSE":
            ticker_symbol = f"{symbol}.NS"
        elif exchange == "BSE":
            ticker_symbol = f"{symbol}.BO"
        else:
            ticker_symbol = symbol
        
        # 3. Fetch 250 days of data (need 200+ for 200 DMA)
        ticker = yf.Ticker(ticker_symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=250)
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 200:
            # Not enough data - allow trade (fail-open)
            reason = f"Insufficient data for 200 DMA ({len(hist)} days)"
            logger.warning(f"⚠️ TREND FILTER: {symbol} - {reason}")
            return (True, reason)
        
        # 4. Calculate 200-day moving average
        ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        
        # 5. Compare current price to 200 DMA
        if current_price > ma_200:
            reason = f"Price above 200 DMA: ₹{current_price:.2f} > ₹{ma_200:.2f} (bullish)"
            logger.info(f"✅ TREND FILTER: {symbol} - {reason}")
            return (True, reason)
        else:
            # Below 200 DMA - downtrend, don't buy
            pct_below = ((ma_200 - current_price) / ma_200) * 100
            reason = f"Price below 200 DMA: ₹{current_price:.2f} < ₹{ma_200:.2f} (-{pct_below:.1f}%)"
            logger.warning(f"❌ TREND FILTER: {symbol} blocked - {reason}")
            return (False, reason)
    
    except Exception as e:
        # Error fetching data - fail-open (allow trade)
        reason = f"Trend filter error: {str(e)[:100]}"
        logger.error(f"⚠️ TREND FILTER: {symbol} - {reason}")
        return (True, reason)


# Example usage / Testing
if __name__ == "__main__":
    print("🧪 Testing Trend Filter...")
    
    # Test 1: TCS (usually in uptrend)
    result = check_trend_filter("TCS", "NSE", 3500, None)
    print(f"\nTest 1 (TCS): {result}")
    
    # Test 2: INFY
    result = check_trend_filter("INFY", "NSE", 1500, None)
    print(f"\nTest 2 (INFY): {result}")
    
    # Test 3: Invalid symbol (should gracefully handle)
    result = check_trend_filter("INVALID123", "NSE", 100, None)
    print(f"\nTest 3 (Invalid): {result}")
    
    print("\n✅ Trend filter tests complete!")
