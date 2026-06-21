"""
Parameter Capture Helper Functions
Captures all trade parameters for comprehensive AI analysis.

Principles: Plan → Test → Deploy → Verify → Document
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any
import json

logger = logging.getLogger("parameter_capture")


class ParameterCapture:
    """Captures all parameters for entry and exit trades"""

    def __init__(self, market_fetcher=None):
        """
        Initialize parameter capture.

        Args:
            market_fetcher: MarketContextFetcher instance for market data
        """
        self.market_fetcher = market_fetcher
        self.position_size_mode = "DYNAMIC"  # Can be set externally
        self.base_position_size = 1
        self.volatility_adjustment_pct = 100.0
        self.current_timeframe = "15T"  # Default: 15-minute candles

    def set_position_sizing(self, mode: str, base_size: int, adjustment: float):
        """Set position sizing parameters"""
        self.position_size_mode = mode
        self.base_position_size = base_size
        self.volatility_adjustment_pct = adjustment
        logger.info(f"Position sizing: {mode} (base={base_size}, adj={adjustment}%)")

    def set_timeframe(self, tf: str):
        """Set trading timeframe"""
        self.current_timeframe = tf
        logger.debug(f"Timeframe set to: {tf}")

    def get_market_regime(self) -> Optional[str]:
        """Get current market regime"""
        if self.market_fetcher:
            regime_result = self.market_fetcher.fetch_market_regime()
            return regime_result[0] if regime_result else None
        return None

    def get_market_volatility(self) -> Optional[float]:
        """Get current market volatility (0-100)"""
        if self.market_fetcher:
            return self.market_fetcher.fetch_market_volatility()
        return None

    def get_nifty_change_pct(self) -> Optional[float]:
        """Get Nifty 50 % change"""
        if self.market_fetcher:
            nifty = self.market_fetcher.fetch_nifty_trend()
            return nifty['change_pct'] if nifty else None
        return None

    def get_sector_performance(self) -> Optional[Dict]:
        """Get sector-wise performance"""
        if self.market_fetcher:
            return self.market_fetcher.fetch_sector_performance()
        return None

    def capture_entry_parameters(
        self,
        symbol: str,
        exchange: str,
        qty: int,
        entry_price: float,
        rsi_value: float,
        atr: float,
        adx: float,
        macd_val: float,
        macd_signal: float,
        macd_hist: float,
        strategy: str = "RSI"
    ) -> Dict[str, Any]:
        """
        Capture all parameters at trade entry.

        Returns comprehensive parameter dictionary for database storage.
        """
        now = datetime.now()

        entry_params = {
            # Position Sizing
            'quantity': qty,
            'position_size_mode': self.position_size_mode,
            'base_position_size': self.base_position_size,
            'volatility_adjustment_pct': self.volatility_adjustment_pct,

            # Technical Parameters
            'timeframe': self.current_timeframe,
            'rsi_value': rsi_value,
            'rsi_threshold_buy': 35,  # Should be read from settings
            'rsi_threshold_sell': 65,
            'atr': atr,
            'adx': adx,
            'macd_value': macd_val,
            'macd_signal': macd_signal,
            'macd_histogram': macd_hist,

            # Market Context at Entry
            'entry_market_regime': self.get_market_regime(),
            'entry_nifty_50_change_pct': self.get_nifty_change_pct(),
            'entry_volatility': self.get_market_volatility(),
            'entry_sector_performance': self.get_sector_performance(),

            # Time Analysis
            'entry_hour': now.hour,
            'entry_day_of_week': now.strftime('%A'),

            # Prices & Strategy
            'entry_price': entry_price,
            'strategy': strategy,
        }

        vol_str = f"{entry_params['entry_volatility']:.1f}" if entry_params['entry_volatility'] else "N/A"
        logger.info(
            f"Captured entry parameters for {symbol}: "
            f"Qty={qty}, Regime={entry_params['entry_market_regime']}, "
            f"Vol={vol_str}, Hour={now.hour}"
        )

        return entry_params

    def capture_exit_parameters(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str,
        entry_time: datetime,
        pnl: float,
        pnl_pct: float
    ) -> Dict[str, Any]:
        """
        Capture all parameters at trade exit.

        Args:
            symbol: Stock symbol
            exit_price: Exit price
            exit_reason: Why exited ('Profit Target', 'Stop-Loss', 'Manual', etc.)
            entry_time: When trade was entered (datetime object)
            pnl: Profit/loss amount
            pnl_pct: Profit/loss percentage

        Returns comprehensive exit parameter dictionary.
        """
        now = datetime.now()
        hold_duration_seconds = (now - entry_time).total_seconds()
        hold_duration_minutes = int(hold_duration_seconds / 60)

        exit_params = {
            # Exit Context
            'exit_reason': exit_reason,
            'exit_price': exit_price,

            # Market Context at Exit
            'exit_market_regime': self.get_market_regime(),
            'exit_nifty_50_change_pct': self.get_nifty_change_pct(),
            'exit_volatility': self.get_market_volatility(),
            'exit_sector_performance': self.get_sector_performance(),

            # Compare entry vs exit
            'market_regime_changed': 'YES' if self.market_regime_changed(
                None,  # Would need to pass entry regime
                self.get_market_regime()
            ) else 'NO',

            # Hold Duration
            'hold_duration_minutes': hold_duration_minutes,
            'hold_duration_bars': self.calculate_hold_bars(hold_duration_minutes),

            # Time of Exit
            'exit_hour': now.hour,
            'exit_day_of_week': now.strftime('%A'),

            # Outcome
            'pnl': pnl,
            'pnl_pct': pnl_pct,
        }

        logger.info(
            f"Captured exit parameters for {symbol}: "
            f"Reason={exit_reason}, Duration={hold_duration_minutes}min, "
            f"P&L={pnl_pct:.2f}%, Regime={exit_params['exit_market_regime']}"
        )

        return exit_params

    @staticmethod
    def market_regime_changed(entry_regime: Optional[str], exit_regime: Optional[str]) -> bool:
        """Check if market regime changed from entry to exit"""
        if entry_regime is None or exit_regime is None:
            return False
        return entry_regime != exit_regime

    @staticmethod
    def calculate_hold_bars(hold_minutes: int) -> int:
        """
        Calculate how many candles were held based on timeframe.
        Assumes 15-minute candles by default.
        """
        # For now, assume 15-minute timeframe
        # TODO: Make this respect self.current_timeframe
        return max(1, hold_minutes // 15)

    def get_all_parameters_for_buy(
        self,
        symbol: str,
        exchange: str,
        qty: int,
        entry_price: float,
        rsi_value: float,
        atr: float,
        adx: float,
        macd_val: float,
        macd_signal: float,
        macd_hist: float
    ) -> Dict[str, Any]:
        """
        Get all parameters needed for a BUY trade.
        Ready to pass directly to database.
        """
        return self.capture_entry_parameters(
            symbol=symbol,
            exchange=exchange,
            qty=qty,
            entry_price=entry_price,
            rsi_value=rsi_value,
            atr=atr,
            adx=adx,
            macd_val=macd_val,
            macd_signal=macd_signal,
            macd_hist=macd_hist
        )

    def get_all_parameters_for_sell(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str,
        entry_time: datetime,
        pnl: float,
        pnl_pct: float
    ) -> Dict[str, Any]:
        """
        Get all parameters needed for a SELL trade.
        Ready to pass directly to database.
        """
        return self.capture_exit_parameters(
            symbol=symbol,
            exit_price=exit_price,
            exit_reason=exit_reason,
            entry_time=entry_time,
            pnl=pnl,
            pnl_pct=pnl_pct
        )


# ============================================================================
# UNIT TESTS (Run with: python -m pytest parameter_capture.py -v)
# ============================================================================

def test_parameter_capture_initialization():
    """Test that ParameterCapture initializes correctly"""
    capture = ParameterCapture()
    assert capture.position_size_mode == "DYNAMIC"
    assert capture.base_position_size == 1
    assert capture.current_timeframe == "15T"
    print("[PASS] Initialization test passed")


def test_set_position_sizing():
    """Test setting position sizing parameters"""
    capture = ParameterCapture()
    capture.set_position_sizing("FIXED", 5, 80.0)
    assert capture.position_size_mode == "FIXED"
    assert capture.base_position_size == 5
    assert capture.volatility_adjustment_pct == 80.0
    print("[PASS] Position sizing test passed")


def test_set_timeframe():
    """Test setting timeframe"""
    capture = ParameterCapture()
    capture.set_timeframe("5T")
    assert capture.current_timeframe == "5T"
    print("[PASS] Timeframe test passed")


def test_capture_entry_parameters():
    """Test capturing entry parameters"""
    capture = ParameterCapture()
    capture.set_position_sizing("DYNAMIC", 1, 100.0)

    params = capture.capture_entry_parameters(
        symbol="INFY",
        exchange="NSE",
        qty=1,
        entry_price=1850.50,
        rsi_value=34.2,
        atr=42.5,
        adx=32.1,
        macd_val=0.45,
        macd_signal=0.38,
        macd_hist=0.07
    )

    # Verify all required fields are present
    required_fields = [
        'quantity', 'position_size_mode', 'timeframe',
        'rsi_value', 'atr', 'adx', 'macd_value',
        'entry_hour', 'entry_day_of_week', 'entry_price'
    ]

    for field in required_fields:
        assert field in params, f"Missing field: {field}"
        assert params[field] is not None, f"Field is None: {field}"

    assert params['quantity'] == 1
    assert params['entry_price'] == 1850.50
    assert params['rsi_value'] == 34.2
    assert isinstance(params['entry_hour'], int)
    assert params['entry_day_of_week'] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    print("[PASS] Capture entry parameters test passed")


def test_capture_exit_parameters():
    """Test capturing exit parameters"""
    from datetime import datetime, timedelta

    capture = ParameterCapture()
    entry_time = datetime.now() - timedelta(minutes=90)

    params = capture.capture_exit_parameters(
        symbol="INFY",
        exit_price=1925.50,
        exit_reason="Profit Target Hit",
        entry_time=entry_time,
        pnl=75.00,
        pnl_pct=4.05
    )

    # Verify all required fields
    required_fields = [
        'exit_reason', 'exit_price', 'hold_duration_minutes',
        'hold_duration_bars', 'exit_hour', 'exit_day_of_week',
        'pnl', 'pnl_pct'
    ]

    for field in required_fields:
        assert field in params, f"Missing field: {field}"

    assert params['exit_reason'] == "Profit Target Hit"
    assert params['exit_price'] == 1925.50
    assert params['hold_duration_minutes'] == 90
    assert params['hold_duration_bars'] == 6  # 90 / 15 = 6 bars
    assert params['pnl'] == 75.00

    print("[PASS] Capture exit parameters test passed")


def test_calculate_hold_bars():
    """Test hold bar calculation"""
    assert ParameterCapture.calculate_hold_bars(15) == 1   # 1 bar
    assert ParameterCapture.calculate_hold_bars(30) == 2   # 2 bars
    assert ParameterCapture.calculate_hold_bars(90) == 6   # 6 bars
    assert ParameterCapture.calculate_hold_bars(5) == 1    # Min 1 bar
    print("[PASS] Hold bars calculation test passed")


def test_market_regime_changed():
    """Test market regime change detection"""
    assert ParameterCapture.market_regime_changed("UPTREND", "DOWNTREND") == True
    assert ParameterCapture.market_regime_changed("SIDEWAYS", "SIDEWAYS") == False
    assert ParameterCapture.market_regime_changed(None, "UPTREND") == False
    assert ParameterCapture.market_regime_changed("UPTREND", None) == False
    print("[PASS] Market regime change test passed")


def run_all_tests():
    """Run all unit tests"""
    print("\n" + "="*70)
    print("PARAMETER CAPTURE UNIT TESTS")
    print("="*70 + "\n")

    tests = [
        test_parameter_capture_initialization,
        test_set_position_sizing,
        test_set_timeframe,
        test_capture_entry_parameters,
        test_capture_exit_parameters,
        test_calculate_hold_bars,
        test_market_regime_changed,
    ]

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"[FAIL] {test.__name__} FAILED: {e}")
            return False

    print("\n" + "="*70)
    print("ALL TESTS PASSED!")
    print("="*70 + "\n")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_all_tests()
    exit(0 if success else 1)
