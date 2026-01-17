"""
Market Sentiment Engine
Fetches NIFTY 50 and INDIA VIX data to determine the market's "Mood" (Fear vs Greed).
"""

import yfinance as yf
import traceback

class MarketSentiment:
    def __init__(self):
        self.nifty_ticker = "^NSEI"
        self.vix_ticker = "^INDIAVIX"
        self.status = "NEUTRAL"
        self.score = 50  # 0 (Extreme Fear) to 100 (Extreme Greed)
        self.details = "Initializing..."

    def fetch_sentiment(self):
        """
        Fetches live data and calculates sentiment score.
        Logic:
        - VIX High (> 15) + Rising = Fear
        - NIFTY Dropping (> 1%) = Fear
        - NIFTY Rising + VIX Stable = Greed
        """
        try:
            # Fetch Data (1 day period to get today's change)
            tickers = yf.Tickers(f"{self.nifty_ticker} {self.vix_ticker}")
            
            # Get previous close and current price
            # Note: yfinance might be slow, so we wrap in try/except
            nifty_info = tickers.tickers[self.nifty_ticker].history(period="2d")
            vix_info = tickers.tickers[self.vix_ticker].history(period="2d")

            if nifty_info.empty or vix_info.empty:
                raise Exception("Data fetch failed or market closed/no data")

            # Calculate Changes
            nifty_change = ((nifty_info['Close'].iloc[-1] - nifty_info['Close'].iloc[0]) / nifty_info['Close'].iloc[0]) * 100
            vix_current = vix_info['Close'].iloc[-1]
            vix_change = ((vix_info['Close'].iloc[-1] - vix_info['Close'].iloc[0]) / vix_info['Close'].iloc[0]) * 100

            # --- LOGIC ENGINE ---
            
            # Base Score: 50 (Neutral)
            score = 50
            reason = []

            # 1. VIX Impact (Fear Gauge)
            if vix_current > 20: 
                score -= 20
                reason.append(f"High VIX ({vix_current:.1f})")
            elif vix_current < 12:
                score += 10
                reason.append("Low Volatility")

            if vix_change > 5:
                score -= 15
                reason.append(f"VIX Spiking (+{vix_change:.1f}%)")
            
            # 2. Market Trend (Nifty)
            if nifty_change > 1.0:
                score += 20
                reason.append(f"Nifty Rally (+{nifty_change:.1f}%)")
            elif nifty_change < -1.0:
                score -= 20
                reason.append(f"Nifty Drop ({nifty_change:.1f}%)")
            
            # Clamp Score 0-100
            self.score = max(0, min(100, score))

            # Determine Text Status
            if self.score <= 30: self.status = "EXTREME FEAR 😱"
            elif self.score <= 45: self.status = "FEAR 😨"
            elif self.score <= 55: self.status = "NEUTRAL 😐"
            elif self.score <= 70: self.status = "GREED 🤑"
            else: self.status = "EXTREME GREED 🚀"

            self.details = f"{', '.join(reason)}" if reason else "Market is stable."
            
            return {
                "score": self.score,
                "status": self.status,
                "details": self.details,
                "nifty_change": nifty_change,
                "vix_change": vix_change
            }

        except Exception as e:
            print(f"Sentiment Fetch Error: {e}")
            # Fallback
            self.status = "OFFLINE"
            self.score = 50
            self.details = "Data Unavailable"
            return {"score": 50, "status": "OFFLINE", "details": "Could not fetch data"}

# Usage
if __name__ == "__main__":
    ms = MarketSentiment()
    print(ms.fetch_sentiment())
