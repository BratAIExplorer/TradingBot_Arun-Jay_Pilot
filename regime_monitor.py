"""
ARUN Stock Trading Bot - Market Regime Monitor

Monitors Nifty 50 index to detect current market regime and provide trading
recommendations based on market conditions.

Regime Types:
- BULLISH: Strong uptrend, full trading recommended
- BEARISH: Downtrend, trading halted to prevent losses
- SIDEWAYS: Range-bound, reduced position sizes
- VOLATILE: High volatility, extra caution
- CRISIS: Market crash/panic, emergency halt

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

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance not available - Regime Monitor will use fallback mode")

# Force Disable yfinance for now (Fixing VIX/Nifty Errors)
YFINANCE_AVAILABLE = False


class MarketRegime(Enum):
    """Market regime classifications"""
    BULLISH = "BULLISH"           # Trade normally, full positions
    BEARISH = "BEARISH"           # STOP all trading (avoid falling knives)
    SIDEWAYS = "SIDEWAYS"         # Reduce position sizes slightly
    VOLATILE = "VOLATILE"         # Extra caution, tighter stops
    CRISIS = "CRISIS"             # Emergency halt (crash scenario)


class RegimeMonitor:
    """
    Monitors Nifty 50 index to determine market regime
    and provide trading recommendations.
    
    Uses technical indicators:
    - 50-day and 200-day Simple Moving Averages (trend)
    - ADX (trend strength)
    - Volatility (20-day std deviation)
    - Drawdown from peak
    
    Caches results to avoid excessive API calls (default: 1 hour)
    """
    
    def __init__(self, index_symbol="^NSEI", cache_duration_minutes=60):
        """
        Initialize Regime Monitor
        
        Args:
            index_symbol: Yahoo Finance symbol for Nifty 50 (^NSEI)
            cache_duration_minutes: How long to cache results (default 60 mins)
        """
        self.index_symbol = index_symbol
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.last_check = None
        self.cached_regime = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def get_market_regime(self) -> Dict:
        """
        Main method: Returns current market regime with detailed indicators
        
        Returns:
            {
                'regime': MarketRegime.BULLISH,
                'confidence': 85,  # 0-100
                'should_trade': True,
                'position_size_multiplier': 1.0,  # 0.0 to 1.0
                'indicators': {
                    'price': 21500.0,
                    'sma_50': 21200.0,
                    'sma_200': 20800.0,
                    'price_vs_50dma': 'ABOVE',
                    'price_vs_200dma': 'ABOVE',
                    'sma_50_slope': 0.5,  # % slope
                    'sma_200_slope': 0.3,
                    'volatility_20d': 18.5,  # % annualized
                    'adx': 32.5,
                    'drawdown_from_peak': -2.3  # %
                },
                'recommendation': 'FULL_TRADING',
                'reason': 'Nifty above 200 DMA with positive slope',
                'timestamp': datetime.now()
            }
        """
        # Check cache first
        if self._is_cache_valid():
            self.logger.info("Returning cached regime data")
            return self.cached_regime
        
        # Fetch fresh data
        try:
            data = self._fetch_index_data()
            
            if data is None or len(data) < 200:
                # Fallback to neutral regime if data unavailable
                return self._get_fallback_regime()
            
            # Calculate indicators
            indicators = self._calculate_indicators(data)
            
            # Determine regime
            regime = self._determine_regime(indicators)
            
            # Cache and return
            self.cached_regime = regime
            self.last_check = datetime.now()
            
            self.logger.info(f"Regime detected: {regime['regime'].value} (confidence: {regime['confidence']}%)")
            
            return regime
            
        except Exception as e:
            self.logger.error(f"Error getting market regime: {e}")
            # Return fallback on error
            return self._get_fallback_regime()
    
    def _fetch_index_data(self) -> Optional[pd.DataFrame]:
        """Fetch 1 year of Nifty 50 daily data from Yahoo Finance"""
        if not YFINANCE_AVAILABLE:
            self.logger.warning("yfinance not available, cannot fetch index data")
            return None
        
        try:
            self.logger.info(f"Fetching Nifty 50 data from Yahoo Finance...")
            from utils import get_yfinance_session
            session = get_yfinance_session()
            nifty = yf.download(
                self.index_symbol, 
                period='1y', 
                interval='1d', 
                progress=False,
                session=session
            )
            
            if len(nifty) < 200:
                self.logger.warning(f"Insufficient data: only {len(nifty)} days available (need 200)")
                return None
            
            return nifty
            
        except Exception as e:
            self.logger.error(f"Failed to fetch index data: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all regime indicators from price data"""
        
        current_price = float(df['Close'].iloc[-1])
        
        # Moving Averages
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()
        sma_50 = float(df['SMA_50'].iloc[-1])
        sma_200 = float(df['SMA_200'].iloc[-1])
        
        # Trend Detection
        price_vs_50dma = "ABOVE" if current_price > sma_50 else "BELOW"
        price_vs_200dma = "ABOVE" if current_price > sma_200 else "BELOW"
        
        # Slope Analysis (trend strength)
        sma_50_slope = (df['SMA_50'].iloc[-1] - df['SMA_50'].iloc[-20]) / df['SMA_50'].iloc[-20] * 100
        sma_200_slope = (df['SMA_200'].iloc[-1] - df['SMA_200'].iloc[-50]) / df['SMA_200'].iloc[-50] * 100
        
        # Volatility (annualized)
        returns = df['Close'].pct_change()
        volatility_20d = float(returns.rolling(20).std() * np.sqrt(252) * 100)
        
        # ADX (Trend Strength) - simplified calculation
        adx = self._calculate_adx(df, period=14)
        
        # Drawdown from peak
        peak = float(df['Close'].rolling(252, min_periods=1).max().iloc[-1])
        current_drawdown = (current_price - peak) / peak * 100
        
        return {
            'price': current_price,
            'sma_50': sma_50,
            'sma_200': sma_200,
            'price_vs_50dma': price_vs_50dma,
            'price_vs_200dma': price_vs_200dma,
            'sma_50_slope': float(sma_50_slope),
            'sma_200_slope': float(sma_200_slope),
            'volatility_20d': volatility_20d,
            'adx': adx,
            'drawdown_from_peak': current_drawdown
        }
    
    def _determine_regime(self, indicators: Dict) -> Dict:
        """
        Determine market regime using decision tree logic
        
        Priority order:
        1. CRISIS: Drawdown > -15% OR Volatility > 35%
        2. BEARISH: Price < 200 DMA AND 200 DMA slope negative
        3. VOLATILE: ADX < 20 AND Volatility > 25%
        4. SIDEWAYS: ADX < 25 AND Price near 200 DMA
        5. BULLISH: Price > 200 DMA AND 200 DMA slope positive
        """
        
        price_vs_200 = indicators['price_vs_200dma']
        sma_200_slope = indicators['sma_200_slope']
        volatility = indicators['volatility_20d']
        adx = indicators['adx']
        drawdown = indicators['drawdown_from_peak']
        
        # CRISIS Detection (Highest Priority)
        if drawdown < -15 or volatility > 35:
            return {
                'regime': MarketRegime.CRISIS,
                'confidence': 95,
                'should_trade': False,
                'position_size_multiplier': 0.0,
                'indicators': indicators,
                'recommendation': 'HALT_ALL_TRADING',
                'reason': f"Market in crisis: {drawdown:.1f}% drawdown, {volatility:.1f}% volatility",
                'timestamp': datetime.now()
            }
        
        # BEARISH Detection
        if price_vs_200 == "BELOW" and sma_200_slope < 0:
            return {
                'regime': MarketRegime.BEARISH,
                'confidence': 80,
                'should_trade': False,
                'position_size_multiplier': 0.0,
                'indicators': indicators,
                'recommendation': 'STOP_NEW_POSITIONS',
                'reason': f"Nifty below 200 DMA with negative slope ({sma_200_slope:.2f}%)",
                'timestamp': datetime.now()
            }
        
        # VOLATILE Detection
        if adx < 20 and volatility > 25:
            return {
                'regime': MarketRegime.VOLATILE,
                'confidence': 70,
                'should_trade': True,
                'position_size_multiplier': 0.5,  # Half normal size
                'indicators': indicators,
                'recommendation': 'TRADE_WITH_CAUTION',
                'reason': f"High volatility ({volatility:.1f}%), weak trend (ADX {adx:.1f})",
                'timestamp': datetime.now()
            }
        
        # SIDEWAYS Detection
        if adx < 25 and abs(drawdown) < 5:
            return {
                'regime': MarketRegime.SIDEWAYS,
                'confidence': 75,
                'should_trade': True,
                'position_size_multiplier': 0.75,  # Slightly reduced
                'indicators': indicators,
                'recommendation': 'RANGE_TRADING_MODE',
                'reason': f"Weak trend (ADX {adx:.1f}), price near 200 DMA",
                'timestamp': datetime.now()
            }
        
        # BULLISH Detection (Default if price > 200 DMA)
        if price_vs_200 == "ABOVE" and sma_200_slope > 0:
            return {
                'regime': MarketRegime.BULLISH,
                'confidence': 85,
                'should_trade': True,
                'position_size_multiplier': 1.0,  # Full positions
                'indicators': indicators,
                'recommendation': 'FULL_TRADING',
                'reason': f"Nifty above 200 DMA with positive slope ({sma_200_slope:.2f}%)",
                'timestamp': datetime.now()
            }
        
        # Fallback (Neutral/Cautious)
        return {
            'regime': MarketRegime.SIDEWAYS,
            'confidence': 60,
            'should_trade': True,
            'position_size_multiplier': 0.75,
            'indicators': indicators,
            'recommendation': 'CAUTIOUS_TRADING',
            'reason': "Unclear signals, trade with caution",
            'timestamp': datetime.now()
        }
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average Directional Index (trend strength)
        
        ADX Values:
        - 0-20: Weak trend (choppy/sideways)
        - 20-40: Strong trend
        - 40+: Very strong trend
        """
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Directional Movement
            dm_plus = high.diff()
            dm_minus = -low.diff()
            dm_plus[dm_plus < 0] = 0
            dm_minus[dm_minus < 0] = 0
            
            # Smoothed values
            tr_smooth = tr.rolling(period).mean()
            dm_plus_smooth = dm_plus.rolling(period).mean()
            dm_minus_smooth = dm_minus.rolling(period).mean()
            
            # Directional Indicators
            di_plus = 100 * dm_plus_smooth / tr_smooth
            di_minus = 100 * dm_minus_smooth / tr_smooth
            
            # ADX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
            adx = dx.rolling(period).mean()
            
            return float(adx.iloc[-1])
            
        except Exception as e:
            self.logger.warning(f"ADX calculation failed: {e}, defaulting to 25")
            return 25.0  # Neutral value
    
    def _is_cache_valid(self) -> bool:
        """Check if cached regime is still valid"""
        if not self.last_check or not self.cached_regime:
            return False
        
        time_since_check = datetime.now() - self.last_check
        return time_since_check < self.cache_duration
    
    def _get_fallback_regime(self) -> Dict:
        """
        Return neutral/cautious regime when data is unavailable
        Used during market hours when API fails or yfinance unavailable
        """
        return {
            'regime': MarketRegime.SIDEWAYS,
            'confidence': 50,
            'should_trade': True,
            'position_size_multiplier': 0.5,  # Reduced for safety
            'indicators': {},
            'recommendation': 'CAUTIOUS_TRADING',
            'reason': "Market data unavailable - trading with reduced positions",
            'timestamp': datetime.now()
        }


# Example usage / Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    monitor = RegimeMonitor()
    regime = monitor.get_market_regime()
    
    print("=" * 70)
    print("NIFTY 50 MARKET REGIME MONITOR")
    print("=" * 70)
    print(f"Regime: {regime['regime'].value}")
    print(f"Confidence: {regime['confidence']}%")
    print(f"Should Trade: {regime['should_trade']}")
    print(f"Position Size Multiplier: {regime['position_size_multiplier']}")
    print(f"Recommendation: {regime['recommendation']}")
    print(f"Reason: {regime['reason']}")
    print()
    
    if regime['indicators']:
        print("Technical Indicators:")
        print(f"  Nifty Price: ₹{regime['indicators']['price']:.2f}")
        print(f"  50-day SMA: ₹{regime['indicators']['sma_50']:.2f} ({regime['indicators']['price_vs_50dma']})")
        print(f"  200-day SMA: ₹{regime['indicators']['sma_200']:.2f} ({regime['indicators']['price_vs_200dma']})")
        print(f"  200 DMA Slope: {regime['indicators']['sma_200_slope']:.2f}%")
        print(f"  Volatility (20d): {regime['indicators']['volatility_20d']:.1f}%")
        print(f"  ADX (Trend Strength): {regime['indicators']['adx']:.1f}")
        print(f"  Drawdown from Peak: {regime['indicators']['drawdown_from_peak']:.1f}%")
    
    print("=" * 70)
