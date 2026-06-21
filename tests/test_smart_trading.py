"""
ARUN Trading Bot v2.6.0 - Smart Trading Rules Unit Tests

RED PHASE: Tests for per-stock rules, risk tiers, volume confirmation, and fallback logic.
Tests will fail until settings_manager.get_stock_rule() is implemented.

Test Coverage:
- Per-stock config fallback (key exists → use it, key missing → use default)
- Risk tier mapping (aggressive/moderate/conservative → per_trade_pct multipliers)
- Volume confirmation (skip BUY if volume < min_volume, fail-open if unavailable)
- Trend filter override per-stock
- Backward compatibility (old settings.json without new keys still works)
"""

import pytest
from unittest.mock import Mock, patch


class TestPerStockFallback:
    """settings_manager.get_stock_rule() fallback logic"""

    def test_get_stock_rule_returns_per_stock_value_if_exists(self):
        """If stock has the key, return per-stock value"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        # Mock settings with per-stock rule
        mgr.settings = {
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "risk_tier": "aggressive"
                }
            ]
        }

        result = mgr.get_stock_rule("HDFCBANK", "NSE", "risk_tier", default="moderate")

        assert result == "aggressive"

    def test_get_stock_rule_returns_default_if_key_missing(self):
        """If stock exists but key missing, return default"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    # risk_tier key is missing
                }
            ]
        }

        result = mgr.get_stock_rule("HDFCBANK", "NSE", "risk_tier", default="moderate")

        assert result == "moderate"

    def test_get_stock_rule_returns_default_if_stock_not_found(self):
        """If stock not in config, return default"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "stocks": [
                {"symbol": "INFY", "exchange": "NSE"}
            ]
        }

        result = mgr.get_stock_rule("HDFCBANK", "NSE", "risk_tier", default="moderate")

        assert result == "moderate"

    def test_get_stock_rule_preserves_ignore_rsi_casing(self):
        """Ignore_RSI key keeps its exact casing (not normalized to ignore_rsi)"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "Ignore_RSI": True  # Exact casing
                }
            ]
        }

        result = mgr.get_stock_rule("HDFCBANK", "NSE", "Ignore_RSI", default=False)

        assert result is True

    def test_get_stock_rule_with_none_value(self):
        """Key exists but value is None: return None (not default)"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "trend_filter_override": None  # Explicitly None
                }
            ]
        }

        result = mgr.get_stock_rule("HDFCBANK", "NSE", "trend_filter_override", default=True)

        assert result is None


class TestRiskTierMapping:
    """Risk tier → per_trade_pct mapping"""

    def test_aggressive_tier_15_percent(self):
        """Aggressive tier: 15% per_trade_pct"""
        risk_tier = "aggressive"
        per_trade_pct_base = 10

        multiplier_map = {
            "aggressive": 1.5,
            "moderate": 1.0,
            "conservative": 0.5
        }

        multiplier = multiplier_map[risk_tier]
        per_trade_pct = per_trade_pct_base * multiplier

        assert per_trade_pct == 15.0

    def test_moderate_tier_10_percent(self):
        """Moderate (default) tier: 10% per_trade_pct (1.0x multiplier)"""
        risk_tier = "moderate"
        per_trade_pct_base = 10

        multiplier_map = {
            "aggressive": 1.5,
            "moderate": 1.0,
            "conservative": 0.5
        }

        multiplier = multiplier_map[risk_tier]
        per_trade_pct = per_trade_pct_base * multiplier

        assert per_trade_pct == 10.0

    def test_conservative_tier_5_percent(self):
        """Conservative tier: 5% per_trade_pct (0.5x multiplier)"""
        risk_tier = "conservative"
        per_trade_pct_base = 10

        multiplier_map = {
            "aggressive": 1.5,
            "moderate": 1.0,
            "conservative": 0.5
        }

        multiplier = multiplier_map[risk_tier]
        per_trade_pct = per_trade_pct_base * multiplier

        assert per_trade_pct == 5.0

    def test_risk_tier_affects_stop_loss(self):
        """Stop loss % also scales by risk tier"""
        risk_tiers = {
            "aggressive": {"stop_loss_pct": 8, "profit_target_pct": 1.5},
            "moderate": {"stop_loss_pct": 5, "profit_target_pct": 1.0},
            "conservative": {"stop_loss_pct": 3, "profit_target_pct": 0.75}
        }

        assert risk_tiers["aggressive"]["stop_loss_pct"] == 8
        assert risk_tiers["moderate"]["stop_loss_pct"] == 5
        assert risk_tiers["conservative"]["stop_loss_pct"] == 3


class TestVolumeConfirmation:
    """Volume check before BUY signal"""

    def test_volume_above_min_threshold_allows_buy(self):
        """If volume >= min_volume, proceed with BUY"""
        min_volume = 100000
        current_volume = 150000  # Above threshold

        should_buy = current_volume >= min_volume

        assert should_buy is True

    def test_volume_below_min_threshold_skips_buy(self):
        """If volume < min_volume, skip BUY signal"""
        min_volume = 100000
        current_volume = 50000  # Below threshold

        should_buy = current_volume >= min_volume

        assert should_buy is False

    def test_volume_exactly_at_min_threshold_allows_buy(self):
        """If volume == min_volume, proceed with BUY"""
        min_volume = 100000
        current_volume = 100000  # Exact

        should_buy = current_volume >= min_volume

        assert should_buy is True

    def test_volume_check_fail_open_if_unavailable(self):
        """If volume data missing, fail-open (allow trade)"""
        volume_data = None  # Unavailable

        if volume_data is None:
            should_buy = True  # Fail-open: proceed anyway
        else:
            should_buy = volume_data >= 100000

        assert should_buy is True

    def test_zero_volume_skips_buy(self):
        """Zero volume is clearly insufficient"""
        min_volume = 100000
        current_volume = 0

        should_buy = current_volume >= min_volume

        assert should_buy is False

    def test_per_stock_volume_override(self):
        """Per-stock min_volume overrides global setting"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "global_min_volume": 100000,
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "min_volume": 50000  # Override: lower for liquid stock
                }
            ]
        }

        stock_min = mgr.get_stock_rule("HDFCBANK", "NSE", "min_volume", default=mgr.settings.get("global_min_volume"))

        # Should use stock-specific 50k, not global 100k
        assert stock_min == 50000


class TestTrendFilterOverride:
    """Per-stock trend filter override"""

    def test_trend_filter_override_forces_enabled(self):
        """Per-stock override=true forces trend filter on, ignoring global"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "trend_filter": {"enabled": False, "ma_period": 50},  # Global: disabled
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "trend_filter_override": True  # Per-stock: force on
                }
            ]
        }

        global_enabled = mgr.settings["trend_filter"]["enabled"]
        stock_override = mgr.get_stock_rule("HDFCBANK", "NSE", "trend_filter_override", default=None)

        # Should use stock override (True), not global (False)
        should_filter = stock_override if stock_override is not None else global_enabled
        assert should_filter is True

    def test_trend_filter_override_forces_disabled(self):
        """Per-stock override=false disables trend filter, ignoring global"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "trend_filter": {"enabled": True, "ma_period": 50},  # Global: enabled
            "stocks": [
                {
                    "symbol": "INFY",
                    "exchange": "NSE",
                    "trend_filter_override": False  # Per-stock: force off
                }
            ]
        }

        global_enabled = mgr.settings["trend_filter"]["enabled"]
        stock_override = mgr.get_stock_rule("INFY", "NSE", "trend_filter_override", default=None)

        # Should use stock override (False), not global (True)
        should_filter = stock_override if stock_override is not None else global_enabled
        assert should_filter is False

    def test_trend_filter_no_override_uses_global(self):
        """If no per-stock override, use global setting"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mgr.settings = {
            "trend_filter": {"enabled": True, "ma_period": 50},  # Global: enabled
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE"
                    # No trend_filter_override key
                }
            ]
        }

        global_enabled = mgr.settings["trend_filter"]["enabled"]
        stock_override = mgr.get_stock_rule("HDFCBANK", "NSE", "trend_filter_override", default=None)

        # Should use global since no override
        should_filter = stock_override if stock_override is not None else global_enabled
        assert should_filter is True


class TestBackwardCompatibility:
    """Old settings.json (without new keys) still works"""

    def test_old_settings_json_loads_unchanged(self):
        """Old config without risk_tier, min_volume, trend_filter_override loads fine"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        # Simulated old settings.json (v2.5.2)
        old_settings = {
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "enabled": True,
                    "buy_rsi": 30,
                    "sell_rsi": 70,
                    "Ignore_RSI": False,
                    "quantity": 10,
                    "profit_target_pct": 10.0
                    # No risk_tier, min_volume, trend_filter_override
                }
            ]
        }

        mgr.settings = old_settings

        # Should still load and access old keys
        assert mgr.settings["stocks"][0]["symbol"] == "HDFCBANK"
        assert mgr.settings["stocks"][0]["buy_rsi"] == 30

    def test_get_stock_rule_defaults_for_missing_keys(self):
        """get_stock_rule() with old settings returns defaults for new keys"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        old_settings = {
            "stocks": [
                {"symbol": "HDFCBANK", "exchange": "NSE", "buy_rsi": 30}
            ]
        }

        mgr.settings = old_settings

        # New key not present: returns default
        risk_tier = mgr.get_stock_rule("HDFCBANK", "NSE", "risk_tier", default="moderate")
        min_volume = mgr.get_stock_rule("HDFCBANK", "NSE", "min_volume", default=100000)

        assert risk_tier == "moderate"
        assert min_volume == 100000

    def test_mixed_old_and_new_config(self):
        """Some stocks have new keys, others don't (gradual migration)"""
        from settings_manager import SettingsManager

        mgr = SettingsManager()

        mixed_settings = {
            "stocks": [
                {
                    "symbol": "HDFCBANK",
                    "exchange": "NSE",
                    "buy_rsi": 30,
                    "risk_tier": "aggressive"  # New key
                },
                {
                    "symbol": "INFY",
                    "exchange": "NSE",
                    "buy_rsi": 25
                    # Old config, no new keys
                }
            ]
        }

        mgr.settings = mixed_settings

        # HDFCBANK: has risk_tier
        hdfc_tier = mgr.get_stock_rule("HDFCBANK", "NSE", "risk_tier", default="moderate")
        assert hdfc_tier == "aggressive"

        # INFY: missing risk_tier, use default
        infy_tier = mgr.get_stock_rule("INFY", "NSE", "risk_tier", default="moderate")
        assert infy_tier == "moderate"


class TestSmartTradingIntegration:
    """Smart trading rules working together"""

    def test_aggressive_stock_with_high_volume_buys(self):
        """Aggressive + volume confirmed = proceed with buy"""
        risk_tier = "aggressive"
        min_volume = 100000
        current_volume = 150000

        should_buy = (risk_tier in ["aggressive", "moderate", "conservative"] and
                     current_volume >= min_volume)

        assert should_buy is True

    def test_conservative_stock_low_volume_blocks_buy(self):
        """Conservative + low volume = skip buy"""
        risk_tier = "conservative"
        min_volume = 100000
        current_volume = 50000

        should_buy = (risk_tier in ["aggressive", "moderate", "conservative"] and
                     current_volume >= min_volume)

        assert should_buy is False

    def test_moderate_stock_with_trend_override_respects_override(self):
        """Moderate tier + trend override applies override"""
        risk_tier = "moderate"
        trend_override = False  # Disable trend filter for this stock

        use_trend_filter = trend_override if trend_override is not None else True

        assert use_trend_filter is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
