"""
Nifty 50 ETF SIP Strategy
Steady accumulation of Nifty 50 ETFs (e.g., NIFTYBEES)
"""

from datetime import datetime
import pandas as pd

class NiftySIPStrategy:
    def __init__(self, settings):
        self.settings = settings
        self.symbol = "NIFTYBEES"
        self.exchange = "NSE"
        self.sip_day = "Monday" # Can be 0 (Monday) to 4 (Friday)
        self.dip_threshold = 2.0 # % drop to trigger buy
        
    def should_buy(self, current_price, last_buy_price=None):
        """
        Determine if we should buy today
        1. Is it the SIP day?
        2. Is the price significantly lower than last buy? (Buy the dip)
        """
        if current_price <= 0:
            return False, "Invalid Price"

        now = datetime.now()
        
        # 1. SIP Day Check (e.g., Buy every Monday)
        is_sip_day = now.strftime('%A') == self.sip_day
        
        # 2. Buy the Dip Check
        is_dip = False
        if last_buy_price and current_price > 0:
            drop_pct = ((last_buy_price - current_price) / last_buy_price) * 100
            if drop_pct >= self.dip_threshold:
                is_dip = True
                
        if is_sip_day:
            return True, f"Weekly SIP Day ({self.sip_day})"
        if is_dip:
            return True, f"Buy the Dip ({self.dip_threshold}% drop detected)"
            
        return False, None

    def calculate_quantity(self, capital_amount, current_price):
        """Calculate shares based on allocated capital"""
        if current_price <= 0: return 0
        return int(capital_amount / current_price)
