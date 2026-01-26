"""
Regime Monitor Module
Classifies market conditions (Bullish, Bearish, Sideways, Volatile, Crisis) 
based on NIFTY 50 trend and INDIA VIX volatility.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from enum import Enum
from datetime import datetime, timedelta
import threading
import time

class MarketRegime(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"
    CRISIS = "CRISIS"
    UNKNOWN = "UNKNOWN"

class RegimeMonitor:
    def __init__(self):
        self.nifty_ticker = "^NSEI"
        self.vix_ticker = "^INDIAVIX"
        self.cache_duration = 3600  # 1 hour cache
        self.last_update = 0
        self.cached_result = None
        self._lock = threading.Lock()
        
    def get_market_regime(self):
        """
        Main public method to get current regime.
        Returns cached result if valid, else fetches new data.
        """
        with self._lock:
            now = time.time()
            if self.cached_result and (now - self.last_update < self.cache_duration):
                return self.cached_result
            
            # Fetch fresh data
            result = self._analyze_market()
            self.cached_result = result
            self.last_update = now
            return result
    
    def _analyze_market(self):
        """
        Internal method to fetch data and determine regime.
        """
        try:
            # 1. Fetch Data (History for trend analysis)
            # We need enough data for 200 SMA, but let's stick to 50 SMA for speed if user runs frequently
            # Let's fetch 3 months
            period = "3mo" 
            tickers = yf.Tickers(f"{self.nifty_ticker} {self.vix_ticker}")
            
            nifty_df = tickers.tickers[self.nifty_ticker].history(period=period)
            vix_df = tickers.tickers[self.vix_ticker].history(period="5d") # VIX we just need recent
            
            if nifty_df.empty or vix_df.empty:
                raise Exception("Empty data received from yfinance")
                
            # 2. Calculate Metrics
            current_price = nifty_df['Close'].iloc[-1]
            sma_50 = nifty_df['Close'].rolling(window=50).mean().iloc[-1]
            
            # Intraday Change
            if len(nifty_df) >= 2:
                prev_close = nifty_df['Close'].iloc[-2]
                pct_change = ((current_price - prev_close) / prev_close) * 100
            else:
                pct_change = 0.0
                
            # VIX Level
            vix_current = vix_df['Close'].iloc[-1]
            
            # 3. Determine Regime Logic
            regime = MarketRegime.UNKNOWN
            reason = "Analyzing..."
            confidence = 0
            should_trade = False
            size_mult = 0.0
            
            # --- LOGIC TREE ---
            
            # CRISIS: VIX > 30 OR Huge Drop (-3% or more)
            if vix_current > 30 or pct_change < -3.0:
                regime = MarketRegime.CRISIS
                reason = f"EXTREME RISK! VIX: {vix_current:.1f}, Change: {pct_change:.1f}%"
                confidence = 90
                should_trade = False
                size_mult = 0.0
                
            # VOLATILE: VIX > 20
            elif vix_current > 20:
                regime = MarketRegime.VOLATILE
                reason = f"High Volatility (VIX {vix_current:.1f}). Reduce position size."
                confidence = 80
                should_trade = True
                size_mult = 0.5  # Half size
                
            # BULLISH: Price > SMA50 AND VIX < 20
            # Also consider short term momentum (positive change)
            elif current_price > sma_50 and vix_current < 20:
                regime = MarketRegime.BULLISH
                reason = "Healthy Uptrend. Price > 50 SMA & VIX Stable."
                confidence = 85
                should_trade = True
                size_mult = 1.0
                
            # BEARISH: Price < SMA50
            elif current_price < sma_50:
                regime = MarketRegime.BEARISH
                reason = "Downtrend Detected. Price < 50 SMA."
                confidence = 75
                # Conservative: Don't trade long-only strategies in Bear market
                # But allow if user wants (handled by strategy logic usually)
                # For safety feature: default to NO trade or Reduced
                should_trade = False 
                size_mult = 0.0
                
            # SIDEWAYS: Default if nothing else matches (e.g. Price ~ SMA50, Low VIX but negative change)
            else:
                regime = MarketRegime.SIDEWAYS
                reason = "Market is choppy/flat. No clear trend."
                confidence = 60
                should_trade = True
                size_mult = 0.75
                
            return {
                "regime": regime,
                "should_trade": should_trade,
                "confidence": confidence,
                "reason": reason,
                "position_size_multiplier": size_mult,
                "vix": vix_current,
                "nifty_change": pct_change
            }

        except Exception as e:
            # Fallback for offline/error
            return {
                "regime": MarketRegime.UNKNOWN,
                "should_trade": False,
                "confidence": 0,
                "reason": f"Data Fetch Error: {str(e)[:50]}...",
                "position_size_multiplier": 0.0,
                "vix": 0,
                "nifty_change": 0
            }

if __name__ == "__main__":
    # Test
    monitor = RegimeMonitor()
    print("Testing Regime Monitor...")
    res = monitor.get_market_regime()
    print(res)
