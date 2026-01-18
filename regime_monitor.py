"""
Market Regime Monitor for Nifty 50 Index

This module detects the current market regime (BULLISH, BEARISH, SIDEWAYS, VOLATILE, or CRISIS)
and provides trading recommendations based on market conditions.

Author: ARUN Stock Trading Bot
Version: 1.0
Date: January 18, 2026
"""

import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import numpy as np
import yfinance as yf


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    CRISIS = "CRISIS"
    BEARISH = "BEARISH"
    VOLATILE = "VOLATILE"
    SIDEWAYS = "SIDEWAYS"
    BULLISH = "BULLISH"


class RegimeMonitor:
    """
    Market regime detection for Nifty 50 index

    Detects market conditions and provides position sizing recommendations:
    - CRISIS: Major crash or panic (HALT trading)
    - BEARISH: Bear market (HALT trading)
    - VOLATILE: High volatility, no clear trend (50% position sizes)
    - SIDEWAYS: Range-bound market (75% position sizes)
    - BULLISH: Bull market (100% position sizes)
    """

    def __init__(self, symbol: str = '^NSEI', cache_duration: int = 3600):
        """
        Initialize Regime Monitor

        Args:
            symbol: Yahoo Finance symbol (default: ^NSEI for Nifty 50)
            cache_duration: Cache duration in seconds (default: 3600 = 1 hour)
        """
        self.symbol = symbol
        self.cache_duration = cache_duration

        # Cache variables
        self._cached_regime: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None

        logger.info(f"✅ RegimeMonitor initialized for {symbol} (cache: {cache_duration}s)")

    def get_market_regime(self) -> Dict:
        """
        Get current market regime with comprehensive analysis

        Returns:
            dict: {
                'regime': MarketRegime enum,
                'should_trade': bool (False for CRISIS/BEARISH),
                'position_size_multiplier': float (0.0-1.0),
                'confidence': int (0-100),
                'reason': str (human-readable explanation),
                'indicators': dict (all calculated values),
                'timestamp': datetime
            }
        """
        # Check cache first
        if self._is_cache_valid():
            logger.info(f"📊 Using cached regime: {self._cached_regime['regime'].value}")
            return self._cached_regime

        logger.info(f"🔄 Fetching fresh market data for {self.symbol}...")

        try:
            # Fetch 1 year of daily data (250 trading days)
            df = self._fetch_market_data()

            # Calculate all indicators
            indicators = self._calculate_indicators(df)

            # Determine regime based on indicators
            regime_result = self._determine_regime(indicators)

            # Add indicators and timestamp to result
            regime_result['indicators'] = indicators
            regime_result['timestamp'] = datetime.now()

            # Cache the result
            self._cached_regime = regime_result
            self._cache_timestamp = datetime.now()

            logger.info(f"✅ Market Regime: {regime_result['regime'].value} | "
                       f"Trade: {regime_result['should_trade']} | "
                       f"Multiplier: {regime_result['position_size_multiplier']:.1%}")
            logger.info(f"📝 Reason: {regime_result['reason']}")

            return regime_result

        except Exception as e:
            logger.error(f"❌ Error detecting market regime: {e}")
            # Return conservative default on error
            return {
                'regime': MarketRegime.CRISIS,
                'should_trade': False,
                'position_size_multiplier': 0.0,
                'confidence': 0,
                'reason': f'Error fetching data: {str(e)}',
                'indicators': {},
                'timestamp': datetime.now()
            }

    def _fetch_market_data(self) -> pd.DataFrame:
        """
        Fetch market data from Yahoo Finance

        Returns:
            pd.DataFrame: OHLCV data with 1 year of daily candles
        """
        try:
            ticker = yf.Ticker(self.symbol)

            # Fetch 1 year + buffer for moving averages
            end_date = datetime.now()
            start_date = end_date - timedelta(days=400)  # 400 days to ensure 250 trading days

            df = ticker.history(start=start_date, end=end_date, interval='1d')

            if df.empty:
                raise ValueError(f"No data returned for {self.symbol}")

            logger.info(f"📥 Fetched {len(df)} days of data for {self.symbol}")
            return df

        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            raise

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calculate all regime detection indicators

        Args:
            df: OHLCV DataFrame

        Returns:
            dict: All calculated indicators
        """
        try:
            # Current price
            current_price = df['Close'].iloc[-1]

            # Moving Averages
            sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
            sma_200 = df['Close'].rolling(window=200).mean().iloc[-1]

            # 200 DMA slope (% change over 50 days)
            sma_200_series = df['Close'].rolling(window=200).mean()
            sma_200_50_days_ago = sma_200_series.iloc[-50] if len(sma_200_series) >= 50 else sma_200
            sma_200_slope = ((sma_200 - sma_200_50_days_ago) / sma_200_50_days_ago) * 100

            # Volatility (20-day, annualized)
            returns = df['Close'].pct_change()
            volatility_20d = returns.rolling(window=20).std().iloc[-1]
            volatility_annualized = volatility_20d * np.sqrt(252) * 100  # Convert to %

            # ADX (Average Directional Index)
            adx = self._calculate_adx(df, period=14)

            # Maximum Drawdown from peak
            rolling_max = df['Close'].rolling(window=250, min_periods=1).max()
            drawdown = ((df['Close'] - rolling_max) / rolling_max * 100).iloc[-1]

            indicators = {
                'current_price': current_price,
                'sma_50': sma_50,
                'sma_200': sma_200,
                'sma_200_slope': sma_200_slope,
                'volatility_20d_annualized': volatility_annualized,
                'adx': adx,
                'drawdown_pct': drawdown
            }

            logger.info(f"📊 Indicators: Price={current_price:.2f}, "
                       f"200DMA={sma_200:.2f}, Slope={sma_200_slope:.2f}%, "
                       f"Vol={volatility_annualized:.1f}%, ADX={adx:.1f}, DD={drawdown:.1f}%")

            return indicators

        except Exception as e:
            logger.error(f"❌ Error calculating indicators: {e}")
            raise

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average Directional Index (ADX)

        ADX measures trend strength (0-100):
        - ADX < 20: Weak/no trend (ranging market)
        - ADX 20-25: Emerging trend
        - ADX > 25: Strong trend
        - ADX > 50: Very strong trend

        Args:
            df: OHLCV DataFrame
            period: ADX period (default: 14)

        Returns:
            float: ADX value
        """
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']

            # Calculate True Range (TR)
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Calculate Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low

            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

            # Smooth TR and DM using Wilder's smoothing (EMA with alpha = 1/period)
            alpha = 1.0 / period
            atr = pd.Series(tr).ewm(alpha=alpha, adjust=False).mean()
            plus_di = 100 * pd.Series(plus_dm).ewm(alpha=alpha, adjust=False).mean() / atr
            minus_di = 100 * pd.Series(minus_dm).ewm(alpha=alpha, adjust=False).mean() / atr

            # Calculate DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.ewm(alpha=alpha, adjust=False).mean()

            return adx.iloc[-1]

        except Exception as e:
            logger.warning(f"⚠️ Error calculating ADX, using default 25: {e}")
            return 25.0  # Default neutral value

    def _determine_regime(self, indicators: Dict) -> Dict:
        """
        Determine market regime using decision tree logic

        Decision flow:
        1. CRISIS: Drawdown > -15% OR Volatility > 35%
        2. BEARISH: Price < 200 DMA AND 200 DMA slope < 0
        3. VOLATILE: ADX < 20 AND Volatility > 25%
        4. SIDEWAYS: ADX < 25 AND |Drawdown| < 5%
        5. BULLISH: Price > 200 DMA AND 200 DMA slope > 0

        Args:
            indicators: Dictionary of calculated indicators

        Returns:
            dict: Regime analysis with trading recommendations
        """
        price = indicators['current_price']
        sma_200 = indicators['sma_200']
        sma_200_slope = indicators['sma_200_slope']
        volatility = indicators['volatility_20d_annualized']
        adx = indicators['adx']
        drawdown = indicators['drawdown_pct']

        # Priority 1: CRISIS Detection
        if drawdown < -15 or volatility > 35:
            return {
                'regime': MarketRegime.CRISIS,
                'should_trade': False,
                'position_size_multiplier': 0.0,
                'confidence': 95,
                'reason': f'Market CRISIS detected: Drawdown={drawdown:.1f}% (threshold: -15%), '
                         f'Volatility={volatility:.1f}% (threshold: 35%). HALT ALL TRADING for safety.'
            }

        # Priority 2: BEARISH Detection
        if price < sma_200 and sma_200_slope < 0:
            return {
                'regime': MarketRegime.BEARISH,
                'should_trade': False,
                'position_size_multiplier': 0.0,
                'confidence': 85,
                'reason': f'BEARISH market: Price ({price:.2f}) below 200 DMA ({sma_200:.2f}) '
                         f'with negative slope ({sma_200_slope:.2f}%). HALT trading in downtrend.'
            }

        # Priority 3: VOLATILE Detection
        if adx < 20 and volatility > 25:
            return {
                'regime': MarketRegime.VOLATILE,
                'should_trade': True,
                'position_size_multiplier': 0.5,
                'confidence': 75,
                'reason': f'VOLATILE market: ADX={adx:.1f} (weak trend), '
                         f'Volatility={volatility:.1f}% (high). Trade with 50% position sizes.'
            }

        # Priority 4: SIDEWAYS Detection
        if adx < 25 and abs(drawdown) < 5:
            return {
                'regime': MarketRegime.SIDEWAYS,
                'should_trade': True,
                'position_size_multiplier': 0.75,
                'confidence': 70,
                'reason': f'SIDEWAYS market: ADX={adx:.1f} (range-bound), '
                         f'Drawdown={drawdown:.1f}% (stable). Trade with 75% position sizes.'
            }

        # Default: BULLISH Detection
        return {
            'regime': MarketRegime.BULLISH,
            'should_trade': True,
            'position_size_multiplier': 1.0,
            'confidence': 80,
            'reason': f'BULLISH market: Price ({price:.2f}) above 200 DMA ({sma_200:.2f}), '
                     f'Slope={sma_200_slope:.2f}%, ADX={adx:.1f}. Trade with full position sizes.'
        }

    def _is_cache_valid(self) -> bool:
        """
        Check if cached regime is still valid

        Returns:
            bool: True if cache is valid, False otherwise
        """
        if self._cached_regime is None or self._cache_timestamp is None:
            return False

        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self.cache_duration


# Example usage and testing
if __name__ == '__main__':
    print("=" * 80)
    print("REGIME MONITOR - Testing Module")
    print("=" * 80)

    # Initialize monitor
    monitor = RegimeMonitor(symbol='^NSEI', cache_duration=3600)

    # Get current regime
    regime = monitor.get_market_regime()

    # Display results
    print(f"\n📊 MARKET REGIME ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    print(f"Regime:           {regime['regime'].value}")
    print(f"Should Trade:     {'✅ YES' if regime['should_trade'] else '❌ NO (HALTED)'}")
    print(f"Position Sizing:  {regime['position_size_multiplier']:.0%} of normal size")
    print(f"Confidence:       {regime['confidence']}%")
    print(f"\n💡 Reason:")
    print(f"   {regime['reason']}")

    # Display indicators
    print(f"\n📈 TECHNICAL INDICATORS:")
    print("-" * 80)
    indicators = regime['indicators']
    print(f"Current Price:    ₹{indicators['current_price']:.2f}")
    print(f"50 DMA:           ₹{indicators['sma_50']:.2f}")
    print(f"200 DMA:          ₹{indicators['sma_200']:.2f}")
    print(f"200 DMA Slope:    {indicators['sma_200_slope']:.2f}%")
    print(f"Volatility (20d): {indicators['volatility_20d_annualized']:.1f}%")
    print(f"ADX (14):         {indicators['adx']:.1f}")
    print(f"Max Drawdown:     {indicators['drawdown_pct']:.1f}%")

    # Trading recommendation
    print(f"\n🎯 TRADING RECOMMENDATION:")
    print("-" * 80)
    if regime['should_trade']:
        base_amount = 5000
        adjusted_amount = base_amount * regime['position_size_multiplier']
        print(f"✅ Trading ALLOWED")
        print(f"   Base position size: ₹{base_amount:,.0f}")
        print(f"   Adjusted size:      ₹{adjusted_amount:,.0f}")
        print(f"   Multiplier:         {regime['position_size_multiplier']:.0%}")
    else:
        print(f"❌ Trading HALTED")
        print(f"   Market conditions are unfavorable")
        print(f"   Wait for regime to improve before trading")

    print("=" * 80)
