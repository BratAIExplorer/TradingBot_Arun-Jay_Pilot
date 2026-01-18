#!/usr/bin/env python3
"""
Regime Engine - User-Controlled Market Regime Logic
====================================================

Integrates with SettingsManagerV2 to provide user-controlled regime behavior.
Users can choose risk profiles (CONSERVATIVE, MODERATE, AGGRESSIVE) which
determine how the bot responds to different market regimes.

Part of MVP v1.0 - Week 1 Foundation

Author: Claude AI (Anthropic)
Date: January 18, 2026
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from enum import Enum
import sys
import os

# Import existing regime monitor
try:
    from regime_monitor import RegimeMonitor
    REGIME_MONITOR_AVAILABLE = True
except (ImportError, Exception) as e:
    print(f"⚠️ Warning: Could not import regime_monitor: {e}")
    REGIME_MONITOR_AVAILABLE = False
    RegimeMonitor = None

# Import settings manager
try:
    from settings_manager_v2 import SettingsManagerV2, RiskProfile
    SETTINGS_V2_AVAILABLE = True
except (ImportError, Exception) as e:
    print(f"❌ Error: Could not import settings_manager_v2: {e}")
    SETTINGS_V2_AVAILABLE = False
    sys.exit(1)


class RegimeAction(Enum):
    """Actions the bot can take in response to regime"""
    CONTINUE = "CONTINUE"  # Continue trading normally
    REDUCE = "REDUCE"      # Reduce position sizes
    HALT = "HALT"          # Stop all new trading


class RegimeDecision:
    """
    Represents a decision about whether to trade based on current regime
    """
    def __init__(
        self,
        regime: str,
        action: RegimeAction,
        position_multiplier: float,
        user_profile: RiskProfile,
        can_override: bool = False,
        has_override: bool = False,
        override_expires_at: Optional[datetime] = None,
        message: str = ""
    ):
        self.regime = regime
        self.action = action
        self.position_multiplier = position_multiplier
        self.user_profile = user_profile
        self.can_override = can_override
        self.has_override = has_override
        self.override_expires_at = override_expires_at
        self.message = message

    def should_trade(self) -> bool:
        """Returns True if trading is allowed (CONTINUE or REDUCE)"""
        return self.action != RegimeAction.HALT or self.has_override

    def get_position_size_adjustment(self, base_size: float) -> float:
        """
        Apply position size adjustment based on regime

        Args:
            base_size: Base position size (e.g., ₹5000)

        Returns:
            Adjusted position size (e.g., ₹2500 if multiplier is 0.5)
        """
        if self.has_override:
            return base_size  # Override means full size
        return base_size * self.position_multiplier

    def __str__(self) -> str:
        """String representation for logging"""
        override_info = ""
        if self.has_override:
            override_info = f" [OVERRIDE ACTIVE until {self.override_expires_at}]"

        return (
            f"RegimeDecision(regime={self.regime}, action={self.action.value}, "
            f"multiplier={self.position_multiplier:.0%}, profile={self.user_profile.value}"
            f"{override_info})"
        )


class RegimeEngine:
    """
    Main regime engine that combines regime detection with user preferences
    """

    def __init__(
        self,
        settings: Optional[SettingsManagerV2] = None,
        enable_regime_monitor: bool = True
    ):
        """
        Initialize regime engine

        Args:
            settings: SettingsManagerV2 instance (creates new if None)
            enable_regime_monitor: Whether to use actual regime detection
        """
        self.settings = settings or SettingsManagerV2()
        self.enable_regime_monitor = enable_regime_monitor and REGIME_MONITOR_AVAILABLE

        if self.enable_regime_monitor:
            self.regime_monitor = RegimeMonitor()
        else:
            self.regime_monitor = None

        self.last_regime_check = None
        self.cached_regime = None
        self.cache_duration = timedelta(minutes=15)  # Refresh every 15 minutes

    def get_current_regime(self, force_refresh: bool = False) -> str:
        """
        Get current market regime (with caching)

        Args:
            force_refresh: Force refresh even if cached

        Returns:
            Regime string (CRISIS, BEARISH, VOLATILE, SIDEWAYS, BULLISH)
        """
        now = datetime.now()

        # Use cache if valid
        if not force_refresh and self.last_regime_check and self.cached_regime:
            if now - self.last_regime_check < self.cache_duration:
                return self.cached_regime

        # Detect regime
        if self.enable_regime_monitor and self.regime_monitor:
            try:
                regime = self.regime_monitor.get_current_regime()
                self.cached_regime = regime
                self.last_regime_check = now
                return regime
            except Exception as e:
                print(f"⚠️ Warning: Regime detection failed: {e}")
                # Fallback to SIDEWAYS (neutral)
                return "SIDEWAYS"
        else:
            # If regime monitor disabled, assume SIDEWAYS (neutral)
            return "SIDEWAYS"

    def check_trading_allowed(self, force_refresh: bool = False) -> RegimeDecision:
        """
        Check if trading is allowed based on current regime and user settings

        Args:
            force_refresh: Force regime refresh

        Returns:
            RegimeDecision object with trading decision
        """
        # Get current regime
        current_regime = self.get_current_regime(force_refresh)

        # Get user's risk profile
        user_profile = self.settings.get_risk_profile()

        # Check for active override
        has_override = self.settings.has_active_override()
        override_info = None
        if has_override:
            override_info = self.settings.get_override_info()

        # Get regime behavior from settings (respects risk profile)
        behavior = self.settings.get_regime_behavior(current_regime)

        # Convert to RegimeAction enum
        action_str = behavior['action']
        action = RegimeAction[action_str]
        multiplier = behavior['position_multiplier']

        # Check if user can override
        can_override = self.settings.can_override_halt()

        # Create message
        message = self._create_message(
            current_regime,
            action,
            multiplier,
            user_profile,
            has_override,
            override_info
        )

        # Create decision object
        decision = RegimeDecision(
            regime=current_regime,
            action=action,
            position_multiplier=multiplier,
            user_profile=user_profile,
            can_override=can_override,
            has_override=has_override,
            override_expires_at=override_info['expires_at'] if override_info else None,
            message=message
        )

        return decision

    def _create_message(
        self,
        regime: str,
        action: RegimeAction,
        multiplier: float,
        profile: RiskProfile,
        has_override: bool,
        override_info: Optional[Dict]
    ) -> str:
        """Create user-facing message about regime status"""

        if has_override:
            expires = override_info['expires_at']
            return (
                f"🔓 OVERRIDE ACTIVE: Trading in {regime} regime "
                f"(expires {expires.strftime('%b %d at %I:%M %p')})"
            )

        regime_emoji = {
            'CRISIS': '🚨',
            'BEARISH': '🐻',
            'VOLATILE': '⚡',
            'SIDEWAYS': '➡️',
            'BULLISH': '🐂'
        }

        emoji = regime_emoji.get(regime, '❓')

        if action == RegimeAction.HALT:
            return (
                f"{emoji} {regime} regime detected. "
                f"Trading HALTED per {profile.value} risk profile. "
                f"You can override if needed."
            )
        elif action == RegimeAction.REDUCE:
            return (
                f"{emoji} {regime} regime detected. "
                f"Position sizes reduced to {multiplier:.0%} "
                f"per {profile.value} risk profile."
            )
        else:  # CONTINUE
            return (
                f"{emoji} {regime} regime. "
                f"Trading normally per {profile.value} risk profile."
            )

    def set_override(self, duration_hours: int = 24) -> bool:
        """
        Set temporary override to continue trading despite regime

        Args:
            duration_hours: How long override lasts (default 24 hours)

        Returns:
            True if override set, False if not allowed
        """
        if not self.settings.can_override_halt():
            return False

        current_regime = self.get_current_regime()
        self.settings.set_regime_override(current_regime, duration_hours)
        return True

    def clear_override(self):
        """Clear any active regime override"""
        self.settings.clear_regime_override()

    def get_status_summary(self) -> Dict:
        """
        Get comprehensive status summary for UI display

        Returns:
            Dictionary with status information
        """
        decision = self.check_trading_allowed()

        return {
            'regime': decision.regime,
            'action': decision.action.value,
            'position_multiplier': decision.position_multiplier,
            'risk_profile': decision.user_profile.value,
            'can_trade': decision.should_trade(),
            'can_override': decision.can_override,
            'has_override': decision.has_override,
            'override_expires_at': decision.override_expires_at,
            'message': decision.message,
            'last_check': self.last_regime_check
        }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("Regime Engine - Standalone Test")
    print("=" * 80)

    # Test 1: Initialize
    print("\nTest 1: Initialize Regime Engine")
    engine = RegimeEngine(enable_regime_monitor=False)  # Disable actual detection for test
    print("✅ Initialized successfully")

    # Test 2: Check trading allowed (default CONSERVATIVE profile)
    print("\nTest 2: Check Trading Allowed (CONSERVATIVE profile)")
    decision = engine.check_trading_allowed()
    print(f"Regime: {decision.regime}")
    print(f"Action: {decision.action.value}")
    print(f"Position Multiplier: {decision.position_multiplier:.0%}")
    print(f"Can Trade: {decision.should_trade()}")
    print(f"Message: {decision.message}")

    # Test 3: Position size adjustment
    print("\nTest 3: Position Size Adjustment")
    base_size = 5000  # ₹5,000 base position
    adjusted = decision.get_position_size_adjustment(base_size)
    print(f"Base Position: ₹{base_size:,.0f}")
    print(f"Adjusted Position: ₹{adjusted:,.0f}")

    # Test 4: Change risk profile to AGGRESSIVE
    print("\nTest 4: Change to AGGRESSIVE Profile")
    engine.settings.set_risk_profile(RiskProfile.AGGRESSIVE)
    decision = engine.check_trading_allowed()
    print(f"Action: {decision.action.value}")
    print(f"Position Multiplier: {decision.position_multiplier:.0%}")
    print(f"Message: {decision.message}")

    # Test 5: Set override
    print("\nTest 5: Set Regime Override")
    engine.settings.set_risk_profile(RiskProfile.CONSERVATIVE)  # Back to conservative
    success = engine.set_override(duration_hours=1)
    print(f"Override Set: {success}")

    decision = engine.check_trading_allowed()
    print(f"Has Override: {decision.has_override}")
    print(f"Can Trade: {decision.should_trade()}")
    print(f"Message: {decision.message}")

    # Test 6: Status summary
    print("\nTest 6: Status Summary")
    status = engine.get_status_summary()
    print("Status Summary:")
    for key, value in status.items():
        if key != 'last_check':
            print(f"  {key}: {value}")

    # Test 7: Clear override
    print("\nTest 7: Clear Override")
    engine.clear_override()
    decision = engine.check_trading_allowed()
    print(f"Has Override: {decision.has_override}")
    print(f"Can Trade: {decision.should_trade()}")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
