"""
Settings Manager v2.0 for ARUN Trading Bot
===========================================

Enhanced settings manager with user-centric features:
- Risk Profile support (Conservative, Moderate, Aggressive, Custom)
- Regime Monitor settings
- Stop-Loss execution modes
- Paper/Live trading management
- Backward compatible with v1.0 settings

Author: ARUN Trading Bot Team
Version: 2.0
Date: January 18, 2026
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
import copy

# Import existing SettingsManager for backward compatibility
try:
    from settings_manager import SettingsManager as SettingsManagerV1
    V1_AVAILABLE = True
except (ImportError, Exception) as e:
    # Handle both ImportError and dependency errors (like cryptography issues)
    # print(f"⚠️ Warning: Could not import settings_manager v1: {e}")
    # print("⚠️ V2 will work standalone without v1 backward compatibility.")
    V1_AVAILABLE = False
    SettingsManagerV1 = object


class RiskProfile(Enum):
    """Risk profile options for user customization"""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    CUSTOM = "CUSTOM"


class StopLossMode(Enum):
    """Stop-loss execution modes"""
    AUTO = "AUTO"  # Always auto-execute immediately
    SMART_AUTO = "SMART_AUTO"  # Auto for small positions, confirm for large
    ALERT_ONLY = "ALERT_ONLY"  # Only alert, manual execution required


class TradingMode(Enum):
    """Trading mode - Paper or Live"""
    PAPER = "PAPER"
    LIVE = "LIVE"


class SettingsManagerV2:
    """
    Enhanced Settings Manager with user-centric features

    Key Features:
    - Risk profiles (Conservative/Moderate/Aggressive/Custom)
    - Regime monitor configuration
    - Stop-loss execution modes
    - Paper/Live trading management
    - Backward compatible with v1.0 settings
    - Schema validation
    - Migration support

    Usage:
        settings = SettingsManagerV2()
        risk_profile = settings.get_risk_profile()
        regime_behavior = settings.get_regime_behavior('CRISIS')
    """

    VERSION = "2.0"
    SETTINGS_FILE = "settings_v2.json"
    V1_SETTINGS_FILE = "settings.json"

    # Default settings schema for v2.0
    DEFAULT_V2_SETTINGS = {
        'version': '2.0',
        'last_updated': None,
        'migration_from_v1': False,

        # Risk Profile Settings (NEW in v2.0)
        'risk_profile': {
            'selected': RiskProfile.CONSERVATIVE.value,  # Default to safest
            'allow_user_override': True,  # User can temporarily override halts
            'override_duration_hours': 24,
            'show_risk_warnings': True
        },

        # Regime Monitor Settings (NEW in v2.0)
        'regime_monitor': {
            'enabled': True,
            'alert_on_regime_change': True,
            'custom_rules': {
                # These are used when risk_profile = CUSTOM
                'CRISIS': {
                    'action': 'HALT',  # HALT, REDUCE, CONTINUE
                    'position_multiplier': 0.0,  # 0.0 = no trading
                    'alert': True
                },
                'BEARISH': {
                    'action': 'HALT',
                    'position_multiplier': 0.0,
                    'alert': True
                },
                'VOLATILE': {
                    'action': 'REDUCE',
                    'position_multiplier': 0.5,  # 50% position sizes
                    'alert': True
                },
                'SIDEWAYS': {
                    'action': 'REDUCE',
                    'position_multiplier': 0.75,  # 75% position sizes
                    'alert': False
                },
                'BULLISH': {
                    'action': 'CONTINUE',
                    'position_multiplier': 1.0,  # Full position sizes
                    'alert': False
                }
            }
        },

        # Stop-Loss Settings (ENHANCED in v2.0)
        'stop_loss': {
            'execution_mode': StopLossMode.SMART_AUTO.value,  # AUTO, SMART_AUTO, ALERT_ONLY
            'confirmation_threshold': 50000,  # Ask for confirmation if position > ₹50k
            'timeout_seconds': 60,  # Auto-execute after 60s if no user response
            'enable_trailing': False,
            'trailing_percent': 5.0,
            'partial_exit_enabled': True,  # Allow selling 50% instead of all
            'partial_exit_percent': 50,
            'notifications': {
                'telegram': True,
                'desktop': True,
                'sound': True
            }
        },

        # Paper/Live Trading Mode (ENHANCED in v2.0)
        'trading_mode': {
            'current_mode': TradingMode.PAPER.value,  # PAPER or LIVE
            'paper_initial_capital': 100000,  # ₹1,00,000 virtual money
            'paper_current_capital': 100000,
            'paper_started_at': None,
            'show_mode_banner': True,  # Always visible banner
            'require_confirmation_to_switch': True,
            'safe_transition_wizard': True  # Show wizard when switching to LIVE
        },

        # Backtest Settings (NEW in v2.0)
        'backtest': {
            'auto_run_on_first_launch': True,
            'require_passing_backtest': False,  # User choice
            'min_sharpe_ratio': 1.0,
            'max_drawdown_pct': 15.0,
            'min_win_rate_pct': 55.0,
            'test_period_years': 5,
            'include_realistic_costs': True,
            'cost_per_trade_pct': 0.98  # Indian market: 0.98% round-trip
        },

        # UI/UX Settings (NEW in v2.0)
        'ui': {
            'theme': 'dark',  # dark, light, auto
            'show_tooltips': True,
            'show_educational_tips': True,
            'confirm_risky_actions': True,
            'first_run_completed': False,
            'onboarding_wizard_shown': False,
            'last_risk_profile_reminder': None
        },

        # Active Overrides (Runtime state)
        'active_overrides': {
            'regime_halt_override': {
                'active': False,
                'regime': None,
                'started_at': None,
                'expires_at': None
            }
        }
    }

    def __init__(self, settings_file: Optional[str] = None, auto_migrate: bool = True):
        """
        Initialize Settings Manager V2

        Args:
            settings_file: Path to settings file (default: settings_v2.json)
            auto_migrate: Automatically migrate from v1.0 if v2.0 doesn't exist
        """
        self.settings_file = settings_file or self.SETTINGS_FILE
        self.settings: Dict[str, Any] = {}
        self.v1_settings: Optional[Dict[str, Any]] = None

        # Try to load v2.0 settings
        if os.path.exists(self.settings_file):
            self.load()
        elif auto_migrate and os.path.exists(self.V1_SETTINGS_FILE):
            # Migrate from v1.0
            print(f"🔄 Migrating from v1.0 settings ({self.V1_SETTINGS_FILE})...")
            self.migrate_from_v1()
        else:
            # Create new v2.0 settings with defaults
            print(f"📝 Creating new v2.0 settings...")
            self.settings = copy.deepcopy(self.DEFAULT_V2_SETTINGS)
            self.settings['last_updated'] = datetime.now().isoformat()
            self.save()

    def load(self) -> Dict[str, Any]:
        """Load settings from JSON file"""
        try:
            with open(self.settings_file, 'r') as f:
                loaded_settings = json.load(f)

            # Validate version
            if loaded_settings.get('version') != self.VERSION:
                print(f"⚠️ Settings version mismatch. Expected {self.VERSION}, got {loaded_settings.get('version')}")
                print("🔄 Attempting to upgrade...")
                self.settings = self._upgrade_settings(loaded_settings)
            else:
                self.settings = loaded_settings

            # Merge with defaults (add any new keys from updates)
            self.settings = self._merge_with_defaults(self.settings)

            print(f"✅ Settings v{self.VERSION} loaded from {self.settings_file}")
            return self.settings

        except json.JSONDecodeError as e:
            print(f"❌ Error reading settings: {e}")
            print("⚠️ Using default settings")
            self.settings = copy.deepcopy(self.DEFAULT_V2_SETTINGS)
            return self.settings
        except Exception as e:
            print(f"❌ Unexpected error loading settings: {e}")
            self.settings = copy.deepcopy(self.DEFAULT_V2_SETTINGS)
            return self.settings

    def save(self) -> bool:
        """Save current settings to JSON file"""
        try:
            self.settings['last_updated'] = datetime.now().isoformat()

            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            print(f"✅ Settings v{self.VERSION} saved to {self.settings_file}")
            return True

        except Exception as e:
            print(f"❌ Error saving settings: {e}")
            return False

    def migrate_from_v1(self) -> bool:
        """
        Migrate settings from v1.0 to v2.0
        Preserves all v1.0 settings and adds v2.0 enhancements
        """
        try:
            # Load v1.0 settings
            with open(self.V1_SETTINGS_FILE, 'r') as f:
                v1_settings = json.load(f)

            self.v1_settings = v1_settings

            # Start with v2.0 defaults
            self.settings = copy.deepcopy(self.DEFAULT_V2_SETTINGS)

            # Migrate v1.0 settings (preserve user customizations)
            # These will be stored in a 'v1_legacy' section for backward compatibility
            self.settings['v1_legacy'] = v1_settings

            # Migrate specific settings
            if 'app_settings' in v1_settings:
                # Migrate paper trading mode
                old_paper_mode = v1_settings['app_settings'].get('paper_trading_mode', True)
                self.settings['trading_mode']['current_mode'] = (
                    TradingMode.PAPER.value if old_paper_mode else TradingMode.LIVE.value
                )

            if 'capital' in v1_settings:
                # Migrate capital settings
                total_capital = v1_settings['capital'].get('total_capital', 100000)
                self.settings['trading_mode']['paper_initial_capital'] = total_capital
                self.settings['trading_mode']['paper_current_capital'] = total_capital

            if 'risk_controls' in v1_settings:
                # Migrate stop-loss settings
                default_sl = v1_settings['risk_controls'].get('default_stop_loss_pct', 5)
                # Keep v1.0 stop-loss % in legacy section, but use v2.0 execution modes

            self.settings['migration_from_v1'] = True
            self.settings['last_updated'] = datetime.now().isoformat()

            # Save migrated settings
            self.save()

            print(f"✅ Successfully migrated from v1.0 to v2.0")
            print(f"📝 V1.0 settings preserved in 'v1_legacy' section")
            return True

        except Exception as e:
            print(f"❌ Error migrating from v1.0: {e}")
            return False

    def _merge_with_defaults(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults (add missing keys)"""
        def merge_dicts(base: dict, updates: dict) -> dict:
            """Recursively merge dicts, adding missing keys from base"""
            result = copy.deepcopy(updates)
            for key, value in base.items():
                if key not in result:
                    result[key] = copy.deepcopy(value)
                elif isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = merge_dicts(value, result[key])
            return result

        return merge_dicts(self.DEFAULT_V2_SETTINGS, settings)

    def _upgrade_settings(self, old_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade settings from older v2.x versions"""
        # For now, just merge with defaults
        # In future, handle specific version upgrades here
        return self._merge_with_defaults(old_settings)

    # ========================================================================
    # Risk Profile Methods
    # ========================================================================

    def get_risk_profile(self) -> RiskProfile:
        """Get current risk profile"""
        profile_str = self.settings['risk_profile']['selected']
        return RiskProfile(profile_str)

    def set_risk_profile(self, profile: RiskProfile) -> bool:
        """Set risk profile"""
        self.settings['risk_profile']['selected'] = profile.value
        return self.save()

    def get_regime_behavior(self, regime_type: str) -> Dict[str, Any]:
        """
        Get behavior for specific market regime based on user's risk profile

        Args:
            regime_type: CRISIS, BEARISH, VOLATILE, SIDEWAYS, or BULLISH

        Returns:
            dict: {'action': str, 'position_multiplier': float, 'alert': bool}
        """
        profile = self.get_risk_profile()

        if profile == RiskProfile.CUSTOM:
            # Use custom rules defined by user
            return self.settings['regime_monitor']['custom_rules'].get(regime_type, {
                'action': 'HALT',
                'position_multiplier': 0.0,
                'alert': True
            })

        # Use predefined profile rules
        PROFILE_RULES = {
            RiskProfile.CONSERVATIVE: {
                'CRISIS': {'action': 'HALT', 'position_multiplier': 0.0, 'alert': True},
                'BEARISH': {'action': 'HALT', 'position_multiplier': 0.0, 'alert': True},
                'VOLATILE': {'action': 'REDUCE', 'position_multiplier': 0.5, 'alert': True},
                'SIDEWAYS': {'action': 'REDUCE', 'position_multiplier': 0.75, 'alert': False},
                'BULLISH': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': False}
            },
            RiskProfile.MODERATE: {
                'CRISIS': {'action': 'HALT', 'position_multiplier': 0.0, 'alert': True},
                'BEARISH': {'action': 'REDUCE', 'position_multiplier': 0.5, 'alert': True},
                'VOLATILE': {'action': 'REDUCE', 'position_multiplier': 0.75, 'alert': True},
                'SIDEWAYS': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': False},
                'BULLISH': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': False}
            },
            RiskProfile.AGGRESSIVE: {
                'CRISIS': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': True},
                'BEARISH': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': True},
                'VOLATILE': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': True},
                'SIDEWAYS': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': False},
                'BULLISH': {'action': 'CONTINUE', 'position_multiplier': 1.0, 'alert': False}
            }
        }

        return PROFILE_RULES.get(profile, {}).get(regime_type, {
            'action': 'HALT',
            'position_multiplier': 0.0,
            'alert': True
        })

    def can_override_halt(self) -> bool:
        """Check if user has enabled halt override capability"""
        return self.settings['risk_profile']['allow_user_override']

    def set_regime_override(self, regime_type: str, duration_hours: int = 24) -> bool:
        """
        Set temporary override for regime halt

        Args:
            regime_type: CRISIS, BEARISH, etc.
            duration_hours: How long override is active (default: 24)
        """
        now = datetime.now()
        expires = now + timedelta(hours=duration_hours)

        self.settings['active_overrides']['regime_halt_override'] = {
            'active': True,
            'regime': regime_type,
            'started_at': now.isoformat(),
            'expires_at': expires.isoformat()
        }

        return self.save()

    def has_active_override(self) -> bool:
        """Check if there's an active regime override"""
        override = self.settings['active_overrides']['regime_halt_override']

        if not override['active']:
            return False

        # Check if expired
        if override['expires_at']:
            expires = datetime.fromisoformat(override['expires_at'])
            if datetime.now() > expires:
                # Override expired, clear it
                override['active'] = False
                self.save()
                return False

        return True

    def clear_regime_override(self) -> bool:
        """Clear active regime override"""
        self.settings['active_overrides']['regime_halt_override']['active'] = False
        return self.save()

    # ========================================================================
    # Stop-Loss Methods
    # ========================================================================

    def get_stop_loss_mode(self) -> StopLossMode:
        """Get stop-loss execution mode"""
        mode_str = self.settings['stop_loss']['execution_mode']
        return StopLossMode(mode_str)

    def set_stop_loss_mode(self, mode: StopLossMode) -> bool:
        """Set stop-loss execution mode"""
        self.settings['stop_loss']['execution_mode'] = mode.value
        return self.save()

    def get_stop_loss_confirmation_threshold(self) -> float:
        """Get threshold for stop-loss confirmation (in ₹)"""
        return self.settings['stop_loss']['confirmation_threshold']

    # ========================================================================
    # Trading Mode Methods
    # ========================================================================

    def get_trading_mode(self) -> TradingMode:
        """Get current trading mode (PAPER or LIVE)"""
        mode_str = self.settings['trading_mode']['current_mode']
        return TradingMode(mode_str)

    def set_trading_mode(self, mode: TradingMode) -> bool:
        """Set trading mode (PAPER or LIVE)"""
        old_mode = self.get_trading_mode()

        if old_mode == TradingMode.PAPER and mode == TradingMode.LIVE:
            # Switching to LIVE - important event
            print("⚠️  SWITCHING TO LIVE TRADING MODE - REAL MONEY AT RISK")

        self.settings['trading_mode']['current_mode'] = mode.value
        return self.save()

    def is_paper_trading(self) -> bool:
        """Check if currently in paper trading mode"""
        return self.get_trading_mode() == TradingMode.PAPER

    def is_first_run(self) -> bool:
        """Check if this is first run (onboarding not completed)"""
        return not self.settings['ui']['first_run_completed']

    def mark_first_run_complete(self) -> bool:
        """Mark first run as completed"""
        self.settings['ui']['first_run_completed'] = True
        self.settings['ui']['onboarding_wizard_shown'] = True
        return self.save()

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get(self, key_path: str, default=None):
        """
        Get setting value using dot notation (backward compatible with v1.0)

        Example:
            settings.get('risk_profile.selected')
            settings.get('stop_loss.execution_mode')
        """
        keys = key_path.split('.')
        value = self.settings

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> bool:
        """
        Set setting value using dot notation

        Example:
            settings.set('risk_profile.selected', 'MODERATE')
        """
        keys = key_path.split('.')
        current = self.settings

        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value
        current[keys[-1]] = value
        return self.save()

    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        self.settings = copy.deepcopy(self.DEFAULT_V2_SETTINGS)
        self.settings['last_updated'] = datetime.now().isoformat()
        return self.save()

    def export_settings(self, filename: str) -> bool:
        """Export settings to a file (for backup)"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"✅ Settings exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting settings: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get human-readable summary of current settings"""
        return {
            'version': self.VERSION,
            'risk_profile': self.get_risk_profile().value,
            'trading_mode': self.get_trading_mode().value,
            'stop_loss_mode': self.get_stop_loss_mode().value,
            'regime_monitor_enabled': self.settings['regime_monitor']['enabled'],
            'paper_trading': self.is_paper_trading(),
            'first_run': self.is_first_run(),
            'active_override': self.has_active_override()
        }


# Example usage and testing
if __name__ == '__main__':
    print("=" * 80)
    print("Settings Manager V2.0 - Test Suite")
    print("=" * 80)

    # Test 1: Initialize with defaults
    print("\nTest 1: Initialize Settings Manager V2.0")
    settings = SettingsManagerV2(auto_migrate=False)
    print(f"✅ Initialized successfully")

    # Test 2: Get risk profile
    print("\nTest 2: Risk Profile")
    profile = settings.get_risk_profile()
    print(f"Current Risk Profile: {profile.value}")

    # Test 3: Get regime behavior
    print("\nTest 3: Regime Behavior (Conservative Profile)")
    for regime in ['CRISIS', 'BEARISH', 'VOLATILE', 'SIDEWAYS', 'BULLISH']:
        behavior = settings.get_regime_behavior(regime)
        print(f"  {regime}: {behavior['action']} (multiplier: {behavior['position_multiplier']:.0%})")

    # Test 4: Change to Moderate
    print("\nTest 4: Change to Moderate Risk Profile")
    settings.set_risk_profile(RiskProfile.MODERATE)
    print(f"New profile: {settings.get_risk_profile().value}")

    # Test 5: Get stop-loss mode
    print("\nTest 5: Stop-Loss Settings")
    sl_mode = settings.get_stop_loss_mode()
    threshold = settings.get_stop_loss_confirmation_threshold()
    print(f"Execution Mode: {sl_mode.value}")
    print(f"Confirmation Threshold: ₹{threshold:,.0f}")

    # Test 6: Trading mode
    print("\nTest 6: Trading Mode")
    trading_mode = settings.get_trading_mode()
    is_paper = settings.is_paper_trading()
    print(f"Current Mode: {trading_mode.value}")
    print(f"Is Paper Trading: {is_paper}")

    # Test 7: Summary
    print("\nTest 7: Settings Summary")
    summary = settings.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("All tests completed successfully! ✅")
    print("=" * 80)
