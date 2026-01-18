"""
🔊 Volume Filter - Liquidity Protection Module
Prevents trading low-liquidity stocks with wide spreads

Author: AI Agent (Google Gemini)
Date: January 18, 2026
Design Principle: User control first, safe by default
"""

from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def check_volume_filter(
    symbol: str,
    exchange: str,
    quantity: int,
    market_data: dict,  
    settings: Optional[object] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Check if stock meets minimum volume requirements
    
    Args:
        symbol: Stock symbol (e.g., "MICEL")
        exchange: Exchange (e.g., "NSE")
        quantity: Number of shares to trade
        market_data: Dict with volume data from fetch_market_data_once()
        settings: Settings manager instance
    
    Returns:
        (can_trade, reason, adjusted_quantity)
        - can_trade: True if trade allowed, False if blocked
        - reason: Human-readable explanation
        - adjusted_quantity: Modified qty if needed, None if unchanged
    
    Examples:
        >>> check_volume_filter("TCS", "NSE", 100, {"volume": 1000000}, settings)
        (True, "Volume checks passed", None)
        
        >>> check_volume_filter("SMALLCAP", "NSE", 100, {"volume": 10000}, settings)
        (False, "Low liquidity: 10,000 < 50,000 shares/day", None)
    """
    
    # 1. Check if volume filter is enabled globally
    if settings:
        volume_filter_enabled = settings.get("capital.volume_filter_enabled", True)
    else:
        volume_filter_enabled = True  # Safe default
    
    if not volume_filter_enabled:
        return (True, "Volume filter disabled by user", None)
    
    # 2. Get volume thresholds from settings
    if settings:
        min_volume_shares = settings.get("capital.min_volume_shares", 50000)
        min_volume_value = settings.get("capital.min_volume_value", 500000)
    else:
        # Fallback defaults
        min_volume_shares = 50000
        min_volume_value = 500000
    
    # 3. Extract volume data from market_data
    # Prefer avg_volume_30d, fallback to today's volume
    avg_volume = market_data.get("avg_volume_30d", 0)
    if avg_volume == 0:
        avg_volume = market_data.get("volume", 0
)
    
    current_price = market_data.get("last_price", 0)
    
    # 4. Check minimum shares threshold
    if avg_volume < min_volume_shares:
        reason = f"Low liquidity: {avg_volume:,} < {min_volume_shares:,} shares/day"
        logger.warning(f"❌ VOLUME FILTER: {symbol} blocked - {reason}")
        return (False, reason, None)
    
    # 5. Check minimum turnover (value) threshold
    if current_price > 0:
        daily_turnover = avg_volume * current_price
        if daily_turnover < min_volume_value:
            reason = f"Low turnover: ₹{daily_turnover:,.0f} < ₹{min_volume_value:,.0f}/day"
            logger.warning(f"❌ VOLUME FILTER: {symbol} blocked - {reason}")
            return (False, reason, None)
    
    # 6. Check if order size is reasonable (< 5% of daily volume)
    max_order_pct = 0.05  # 5% of daily volume
    max_qty = int(avg_volume * max_order_pct)
    
    if quantity > max_qty:
        # Auto-reduce quantity to avoid moving the market
        adjusted_qty = max_qty
        reason = (
            f"Order size reduced: {quantity} → {adjusted_qty} shares "
            f"(max {max_order_pct*100}% of daily volume)"
        )
        logger.info(f"⚠️ VOLUME FILTER: {symbol} quantity adjusted - {reason}")
        return (True, reason, adjusted_qty)
    
    # 7. All checks passed
    return (True, "Volume checks passed", None)


# Example usage / Testing
if __name__ == "__main__":
    # Test 1: High volume stock (should pass)
    test_data_1 = {
        "volume": 1000000,
        "avg_volume_30d": 950000,
        "last_price": 1500
    }
    result = check_volume_filter("TCS", "NSE", 100, test_data_1, None)
    print(f"Test 1 (High Volume): {result}")
    assert result[0] == True
    
    # Test 2: Low volume stock (should fail)
    test_data_2 = {
        "volume": 25000,
        "avg_volume_30d": 30000,
        "last_price": 150
    }
    result = check_volume_filter("SMALLCAP", "NSE", 100, test_data_2, None)
    print(f"Test 2 (Low Volume): {result}")
    assert result[0] == False
    
    # Test 3: Large order size (should adjust)
    test_data_3 = {
        "volume": 100000,
        "avg_volume_30d": 100000,
        "last_price": 200
    }
    result = check_volume_filter("MIDCAP", "NSE", 10000, test_data_3, None)  # 10% of volume
    print(f"Test 3 (Large Order): {result}")
    assert result[2] is not None  # Quantity should be adjusted
    
    print("\n✅ All volume filter tests passed!")
