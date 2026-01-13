"""
Market Regime Monitor
Checks the broader market trend (Nifty 50) to act as a circuit breaker.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class RegimeMonitor:
    def __init__(self, index_symbol="^NSEI"):
        self.index_symbol = index_symbol
        self.last_status = "UNKNOWN"
        self.last_price = 0.0
        self.dma_200 = 0.0
        self.last_check = None

    def get_market_status(self) -> dict:
        """
        Fetches Nifty 50 data and calculates trend.
        Returns: {'status': 'BULLISH'|'BEARISH', 'price': float, 'dma': float}
        """
        # Cache check (avoid spamming yfinance, check every 1 hour)
        if self.last_check and datetime.now() - self.last_check < timedelta(hours=1):
            return {
                "status": self.last_status,
                "price": self.last_price,
                "dma": self.dma_200
            }

        try:
            # Fetch 1 year of history to calculate 200 DMA
            ticker = yf.Ticker(self.index_symbol)
            hist = ticker.history(period="1y")

            if hist.empty:
                return {"status": "UNKNOWN", "error": "No data"}

            # Calculate 200 DMA
            self.dma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
            self.last_price = hist['Close'].iloc[-1]

            # Determine Trend
            # If current price > 200 DMA = BULLISH
            # If current price < 200 DMA = BEARISH
            if self.last_price > self.dma_200:
                self.last_status = "BULLISH"
            else:
                self.last_status = "BEARISH"

            self.last_check = datetime.now()

            return {
                "status": self.last_status,
                "price": self.last_price,
                "dma": self.dma_200
            }

        except Exception as e:
            print(f"⚠️ Regime Monitor Error: {e}")
            return {"status": "UNKNOWN", "error": str(e)}

if __name__ == "__main__":
    monitor = RegimeMonitor()
    print(monitor.get_market_status())
