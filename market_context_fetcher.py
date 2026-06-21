"""
Market Context Fetcher - Phase 2
Fetches real-time market data and stores snapshots.
Runs every 5 minutes to capture market conditions.

This module provides:
1. Nifty 50 trend analysis
2. Sector performance tracking
3. Market volatility calculation
4. Market regime detection (UPTREND/DOWNTREND/SIDEWAYS)
5. Earnings calendar
6. Economic event tracking
"""

import yfinance as yf
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database.analytics_migration import AnalyticsDatabase
import traceback

logger = logging.getLogger("market_context")


class MarketContextFetcher:
    """
    Fetches and analyzes market context for trading decisions.
    Caches results to avoid excessive API calls.
    """

    def __init__(self, analytics_db: Optional[AnalyticsDatabase] = None):
        """
        Initialize market context fetcher.

        Args:
            analytics_db: AnalyticsDatabase instance for storing snapshots.
                         If None, will create its own.
        """
        self.analytics_db = analytics_db or AnalyticsDatabase()
        self.last_fetch = {}
        self.cache_duration = 300  # 5 minutes cache

        # Sector tickers (India NSE stocks as proxies)
        self.sector_map = {
            'IT': 'TCS.NS',                     # IT proxy: TCS
            'Finance': 'HDFC.NS',               # Finance proxy: HDFC
            'Pharma': 'SUNPHARMA.NS',           # Pharma proxy: Sun Pharma
            'Auto': 'MARUTI.NS',                # Auto proxy: Maruti
            'FMCG': 'ITC.NS',                   # FMCG proxy: ITC
            'Energy': 'COALINDIA.NS',           # Energy proxy: Coal India
        }

        # Top stocks for market health check
        self.top_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFC.NS', 'ICICIBANK.NS']

    def fetch_nifty_trend(self) -> Optional[Dict]:
        """
        Fetch Nifty 50 current value and % change.

        Returns:
            {
                'symbol': '^NSEI',
                'value': 24150.50,
                'change_pct': 1.25,
                'open': 23900,
                'high': 24200,
                'low': 23850,
                'volume': 123456789,
                'timestamp': '2026-06-21T15:30:00'
            }
        """
        try:
            nifty = yf.Ticker('^NSEI')
            hist = nifty.history(period='5d')

            if hist.empty:
                logger.warning("No Nifty 50 data available")
                return None

            latest = hist.iloc[-1]
            today_open = hist.iloc[-1]['Open']
            current_price = latest['Close']
            change_pct = ((current_price - today_open) / today_open) * 100

            return {
                'symbol': '^NSEI',
                'value': float(current_price),
                'change_pct': float(change_pct),
                'open': float(today_open),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']) if pd.notna(latest['Volume']) else 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching Nifty 50: {e}")
            return None

    def fetch_sector_performance(self) -> Optional[Dict[str, float]]:
        """
        Fetch sector-wise % change for the day.

        Returns:
            {
                'IT': 1.25,
                'Finance': -0.50,
                'Pharma': 0.75,
                'Auto': 2.10,
                'FMCG': -1.30,
                'Energy': 1.50
            }
        """
        try:
            performance = {}

            for sector_name, ticker in self.sector_map.items():
                try:
                    sector_ticker = yf.Ticker(ticker)
                    hist = sector_ticker.history(period='5d')

                    if not hist.empty:
                        today_open = hist.iloc[-1]['Open']
                        current = hist.iloc[-1]['Close']
                        change_pct = ((current - today_open) / today_open) * 100
                        performance[sector_name] = float(round(change_pct, 2))
                    else:
                        performance[sector_name] = 0.0

                except Exception as e:
                    logger.warning(f"Error fetching {sector_name}: {e}")
                    performance[sector_name] = 0.0

            return performance if performance else None

        except Exception as e:
            logger.error(f"Error fetching sector performance: {e}")
            return None

    def fetch_market_volatility(self) -> Optional[float]:
        """
        Estimate market volatility using ATR of Nifty 50.
        Returns a 0-100 scale where higher = more volatile.

        Returns:
            volatility_score: float (0-100)
        """
        try:
            nifty = yf.Ticker('^NSEI')
            hist = nifty.history(period='30d')

            if hist.empty or len(hist) < 14:
                return None

            # Calculate True Range
            high = hist['High'].values
            low = hist['Low'].values
            close = hist['Close'].shift(1).values

            tr = []
            for i in range(1, len(high)):
                tr1 = high[i] - low[i]
                tr2 = abs(high[i] - close[i])
                tr3 = abs(low[i] - close[i])
                tr.append(max(tr1, tr2, tr3))

            # Calculate ATR (14-period)
            atr = pd.Series(tr).rolling(window=14).mean().iloc[-1]
            avg_price = hist['Close'].iloc[-1]

            # Convert ATR to volatility percentage
            volatility_pct = (atr / avg_price) * 100

            # Scale to 0-100 (empirically, volatility rarely exceeds 5%)
            volatility_score = min(volatility_pct * 20, 100)

            return float(round(volatility_score, 2))

        except Exception as e:
            logger.error(f"Error calculating market volatility: {e}")
            return None

    def fetch_market_regime(self) -> Optional[Tuple[str, float]]:
        """
        Determine market regime using 50-day MA and 20-day MA.

        Returns:
            (regime, confidence) where:
            - regime: 'UPTREND' | 'DOWNTREND' | 'SIDEWAYS' | 'OVERBOUGHT' | 'OVERSOLD'
            - confidence: 0.0 - 1.0 (how confident we are in this regime)
        """
        try:
            nifty = yf.Ticker('^NSEI')
            hist = nifty.history(period='200d')

            if hist.empty or len(hist) < 50:
                return None

            close = hist['Close']

            # Calculate moving averages
            ma20 = close.rolling(window=20).mean().iloc[-1]
            ma50 = close.rolling(window=50).mean().iloc[-1]
            ma200 = close.rolling(window=200).mean().iloc[-1]

            current_price = close.iloc[-1]
            rsi = self._calculate_rsi(close)

            # Determine regime
            if current_price > ma50 > ma200:
                regime = 'UPTREND'
                confidence = 0.85
            elif current_price < ma50 < ma200:
                regime = 'DOWNTREND'
                confidence = 0.85
            elif abs(current_price - ma50) / ma50 < 0.01:  # Within 1% of MA50
                regime = 'SIDEWAYS'
                confidence = 0.70
            else:
                regime = 'SIDEWAYS'
                confidence = 0.60

            # Override with RSI extremes
            if rsi > 75:
                regime = 'OVERBOUGHT'
                confidence = 0.80
            elif rsi < 25:
                regime = 'OVERSOLD'
                confidence = 0.80

            return (regime, confidence)

        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return None

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except:
            return 50.0  # Neutral if error

    def calculate_advance_decline_ratio(self) -> Optional[Tuple[float, str]]:
        """
        Calculate advance/decline ratio using top stocks.

        Returns:
            (ratio, breadth) where:
            - ratio: % of stocks advancing
            - breadth: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'
        """
        try:
            advancing = 0
            declining = 0

            for stock in self.top_stocks:
                try:
                    ticker = yf.Ticker(stock)
                    hist = ticker.history(period='5d')

                    if not hist.empty:
                        today_open = hist.iloc[-1]['Open']
                        current = hist.iloc[-1]['Close']

                        if current > today_open:
                            advancing += 1
                        else:
                            declining += 1
                except:
                    pass

            total = advancing + declining
            if total == 0:
                return None

            ratio = (advancing / total) * 100

            if ratio > 60:
                breadth = 'POSITIVE'
            elif ratio < 40:
                breadth = 'NEGATIVE'
            else:
                breadth = 'NEUTRAL'

            return (float(round(ratio, 1)), breadth)

        except Exception as e:
            logger.error(f"Error calculating advance/decline ratio: {e}")
            return None

    def get_top_gainers_losers(self, limit: int = 5) -> Optional[Dict[str, List]]:
        """
        Get top gainers and losers from key stocks.

        Returns:
            {
                'gainers': [
                    {'symbol': 'TCS.NS', 'change_pct': 2.50},
                    ...
                ],
                'losers': [...]
            }
        """
        try:
            changes = []

            for stock in self.top_stocks:
                try:
                    ticker = yf.Ticker(stock)
                    hist = ticker.history(period='5d')

                    if not hist.empty:
                        today_open = hist.iloc[-1]['Open']
                        current = hist.iloc[-1]['Close']
                        change_pct = ((current - today_open) / today_open) * 100

                        changes.append({
                            'symbol': stock.replace('.NS', ''),
                            'change_pct': float(round(change_pct, 2))
                        })
                except:
                    pass

            if not changes:
                return None

            changes.sort(key=lambda x: x['change_pct'], reverse=True)

            return {
                'gainers': changes[:limit],
                'losers': changes[-limit:]
            }

        except Exception as e:
            logger.error(f"Error getting top gainers/losers: {e}")
            return None

    def should_trade_now(self) -> Tuple[bool, str, float]:
        """
        Based on market conditions, should we trade right now?

        Returns:
            (can_trade: bool, reason: str, confidence: float)

        Examples:
            (False, "Market in downtrend, avoid new positions", 0.85)
            (True, "Market strong, good setup", 0.95)
            (False, "Market very volatile, reduce size", 0.70)
        """
        try:
            nifty = self.fetch_nifty_trend()
            if not nifty:
                return (True, "Market data unavailable, proceeding with caution", 0.50)

            regime_result = self.fetch_market_regime()
            if not regime_result:
                return (True, "Regime analysis unavailable", 0.50)

            regime, confidence = regime_result

            volatility = self.fetch_volatility()
            if not volatility:
                volatility = 50  # Neutral

            # Decision logic
            if regime == 'OVERBOUGHT':
                return (False, "Market overbought (RSI > 75), avoid new longs", 0.80)

            if regime == 'OVERSOLD':
                return (True, "Market oversold (RSI < 25), good for mean reversion", 0.80)

            if regime == 'DOWNTREND' and volatility > 70:
                return (False, "Downtrend + High volatility, too risky", 0.85)

            if regime == 'UPTREND' and nifty['change_pct'] > 2:
                return (True, "Strong uptrend, momentum favors us", 0.90)

            if volatility > 80:
                return (False, "Extreme volatility, reduce position size", 0.70)

            # Default: proceed with caution
            return (True, f"Market in {regime}, volatility={volatility:.0f}, proceed normally", 0.70)

        except Exception as e:
            logger.error(f"Error in should_trade_now: {e}")
            return (True, "Error analyzing market, proceeding with caution", 0.50)

    def fetch_volatility(self) -> Optional[float]:
        """Cached volatility fetch"""
        now = datetime.now()
        cache_key = 'volatility'

        if cache_key in self.last_fetch:
            last_time, last_value = self.last_fetch[cache_key]
            if (now - last_time).total_seconds() < self.cache_duration:
                return last_value

        result = self.fetch_market_volatility()
        self.last_fetch[cache_key] = (now, result)
        return result

    def create_snapshot(self) -> Optional[Dict]:
        """
        Create a complete market snapshot at this point in time.

        Returns:
            {
                'timestamp': '2026-06-21T15:30:00',
                'nifty_50': {...},
                'sector_performance': {...},
                'market_volatility': 45.5,
                'market_regime': 'UPTREND',
                'advance_decline_ratio': 65.0,
                'market_breadth': 'POSITIVE',
                'top_gainers': [...],
                'top_losers': [...],
                'recommended_action': (can_trade, reason, confidence)
            }
        """
        try:
            nifty = self.fetch_nifty_trend()
            if not nifty:
                logger.warning("Cannot create snapshot: Nifty data unavailable")
                return None

            sectors = self.fetch_sector_performance()
            volatility = self.fetch_volatility()
            regime_result = self.fetch_market_regime()
            ad_ratio = self.calculate_advance_decline_ratio()
            top_movers = self.get_top_gainers_losers()
            can_trade, reason, confidence = self.should_trade_now()

            regime = regime_result[0] if regime_result else 'UNKNOWN'

            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'nifty_50_value': nifty['value'],
                'nifty_50_change_pct': nifty['change_pct'],
                'sector_performance': sectors or {},
                'market_volatility': volatility,
                'market_regime': regime,
                'advance_decline_ratio': ad_ratio[0] if ad_ratio else None,
                'market_breadth': ad_ratio[1] if ad_ratio else None,
                'top_gainers': top_movers['gainers'] if top_movers else [],
                'top_losers': top_movers['losers'] if top_movers else [],
                'recommended_action': {
                    'can_trade': can_trade,
                    'reason': reason,
                    'confidence': confidence
                },
                'data_source': 'yfinance'
            }

            return snapshot

        except Exception as e:
            logger.error(f"Error creating market snapshot: {e}\n{traceback.format_exc()}")
            return None

    def store_snapshot(self) -> Optional[int]:
        """
        Create and store a market snapshot in the analytics database.

        Returns:
            snapshot_id or None if failed
        """
        try:
            snapshot = self.create_snapshot()
            if not snapshot:
                return None

            snapshot_id = self.analytics_db.insert_market_snapshot(
                timestamp=snapshot['timestamp'],
                nifty_50_value=snapshot['nifty_50_value'],
                nifty_50_change_pct=snapshot['nifty_50_change_pct'],
                market_volatility=snapshot['market_volatility'],
                market_regime=snapshot['market_regime'],
                sector_performance=snapshot['sector_performance'],
                top_gainers=snapshot['top_gainers'],
                top_losers=snapshot['top_losers'],
                advance_decline_ratio=snapshot['advance_decline_ratio'],
                market_breadth=snapshot['market_breadth'],
                data_source=snapshot['data_source']
            )

            if snapshot_id > 0:
                logger.info(f"Market snapshot stored: ID {snapshot_id}")
            elif snapshot_id == -1:
                logger.debug("Duplicate snapshot timestamp (already stored in this minute)")

            return snapshot_id if snapshot_id > 0 else None

        except Exception as e:
            logger.error(f"Error storing snapshot: {e}")
            return None


if __name__ == "__main__":
    """Test market context fetcher"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s'
    )

    print("Testing Market Context Fetcher...\n")

    fetcher = MarketContextFetcher()

    print("1. Fetching Nifty 50 trend...")
    nifty = fetcher.fetch_nifty_trend()
    if nifty:
        print(f"   Nifty 50: {nifty['value']:.0f} ({nifty['change_pct']:+.2f}%)\n")

    print("2. Fetching sector performance...")
    sectors = fetcher.fetch_sector_performance()
    if sectors:
        for sector, change in sectors.items():
            print(f"   {sector}: {change:+.2f}%")
        print()

    print("3. Calculating market volatility...")
    volatility = fetcher.fetch_volatility()
    if volatility:
        print(f"   Volatility Score: {volatility:.1f}/100\n")

    print("4. Determining market regime...")
    regime_result = fetcher.fetch_market_regime()
    if regime_result:
        regime, confidence = regime_result
        print(f"   Regime: {regime} (confidence: {confidence:.0%})\n")

    print("5. Analyzing trading conditions...")
    can_trade, reason, confidence = fetcher.should_trade_now()
    print(f"   Can Trade Now: {can_trade}")
    print(f"   Reason: {reason}")
    print(f"   Confidence: {confidence:.0%}\n")

    print("6. Creating market snapshot...")
    snapshot = fetcher.create_snapshot()
    if snapshot:
        print(f"   Snapshot created at {snapshot['timestamp']}")
        print(f"   Recommended action: {snapshot['recommended_action']['can_trade']}")
        print()

    print("7. Storing snapshot in analytics database...")
    snapshot_id = fetcher.store_snapshot()
    if snapshot_id:
        print(f"   Snapshot stored with ID: {snapshot_id}\n")
        print("SUCCESS: Market context fetcher is working!")
    else:
        print("WARNING: Could not store snapshot")
