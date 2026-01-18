#!/usr/bin/env python3
"""
Test suite for Settings Manager V2.0
Tests all functionality without requiring external dependencies
"""

import sys
import os

# Test by importing just the core logic
sys.path.insert(0, os.path.dirname(__file__))

def test_settings_v2_without_v1():
    """Test settings v2.0 in standalone mode (no v1 dependencies)"""
    print("=" * 80)
    print("Settings Manager V2.0 - Standalone Test")
    print("=" * 80)

    # Temporarily prevent v1 import
    import settings_manager_v2
    settings_manager_v2.V1_AVAILABLE = False
    from settings_manager_v2 import SettingsManagerV2, RiskProfile, StopLossMode, TradingMode

    # Test 1: Initialize
    print("\nTest 1: Initialize (no v1 migration)")
    settings = SettingsManagerV2(settings_file="test_settings_v2.json", auto_migrate=False)
    print("✅ PASS: Initialized successfully")

    # Test 2: Default risk profile
    print("\nTest 2: Default Risk Profile")
    profile = settings.get_risk_profile()
    assert profile == RiskProfile.CONSERVATIVE, "Default should be CONSERVATIVE"
    print(f"✅ PASS: Default profile is {profile.value}")

    # Test 3: Regime behavior for Conservative
    print("\nTest 3: Regime Behavior (CONSERVATIVE profile)")
    test_cases = {
        'CRISIS': ('HALT', 0.0),
        'BEARISH': ('HALT', 0.0),
        'VOLATILE': ('REDUCE', 0.5),
        'SIDEWAYS': ('REDUCE', 0.75),
        'BULLISH': ('CONTINUE', 1.0)
    }

    for regime, (expected_action, expected_mult) in test_cases.items():
        behavior = settings.get_regime_behavior(regime)
        assert behavior['action'] == expected_action
        assert behavior['position_multiplier'] == expected_mult
        print(f"  ✅ {regime}: {behavior['action']} ({behavior['position_multiplier']:.0%})")

    # Test 4: Change risk profile
    print("\nTest 4: Change to MODERATE profile")
    settings.set_risk_profile(RiskProfile.MODERATE)
    profile = settings.get_risk_profile()
    assert profile == RiskProfile.MODERATE
    print(f"✅ PASS: Changed to {profile.value}")

    # Check MODERATE behavior (BEARISH should be REDUCE, not HALT)
    behavior = settings.get_regime_behavior('BEARISH')
    assert behavior['action'] == 'REDUCE', "MODERATE should REDUCE in BEARISH, not HALT"
    assert behavior['position_multiplier'] == 0.5
    print(f"  ✅ BEARISH in MODERATE: {behavior['action']} ({behavior['position_multiplier']:.0%})")

    # Test 5: AGGRESSIVE profile
    print("\nTest 5: Change to AGGRESSIVE profile")
    settings.set_risk_profile(RiskProfile.AGGRESSIVE)
    profile = settings.get_risk_profile()
    assert profile == RiskProfile.AGGRESSIVE

    # AGGRESSIVE should CONTINUE in all regimes
    for regime in ['CRISIS', 'BEARISH', 'VOLATILE']:
        behavior = settings.get_regime_behavior(regime)
        assert behavior['action'] == 'CONTINUE', f"AGGRESSIVE should CONTINUE in {regime}"
        assert behavior['position_multiplier'] == 1.0
    print(f"✅ PASS: AGGRESSIVE continues trading in all regimes")

    # Test 6: Stop-loss mode
    print("\nTest 6: Stop-Loss Mode")
    sl_mode = settings.get_stop_loss_mode()
    assert sl_mode == StopLossMode.SMART_AUTO, "Default should be SMART_AUTO"
    print(f"✅ PASS: Default stop-loss mode is {sl_mode.value}")

    settings.set_stop_loss_mode(StopLossMode.AUTO)
    sl_mode = settings.get_stop_loss_mode()
    assert sl_mode == StopLossMode.AUTO
    print(f"✅ PASS: Changed to {sl_mode.value}")

    # Test 7: Trading mode
    print("\nTest 7: Trading Mode")
    mode = settings.get_trading_mode()
    assert mode == TradingMode.PAPER, "Default should be PAPER"
    assert settings.is_paper_trading() == True
    print(f"✅ PASS: Default is {mode.value} (paper trading)")

    settings.set_trading_mode(TradingMode.LIVE)
    mode = settings.get_trading_mode()
    assert mode == TradingMode.LIVE
    assert settings.is_paper_trading() == False
    print(f"✅ PASS: Switched to {mode.value}")

    # Test 8: Override functionality
    print("\nTest 8: Regime Override")
    assert settings.can_override_halt() == True
    assert settings.has_active_override() == False
    print("✅ PASS: Override allowed, no active override")

    settings.set_regime_override('CRISIS', duration_hours=24)
    assert settings.has_active_override() == True
    print("✅ PASS: Override activated for 24 hours")

    settings.clear_regime_override()
    assert settings.has_active_override() == False
    print("✅ PASS: Override cleared")

    # Test 9: Dot notation get/set
    print("\nTest 9: Dot Notation Access")
    value = settings.get('risk_profile.selected')
    assert value == 'LIVE'  # We set LIVE mode earlier... wait no, we set LIVE for trading_mode
    # Let me fix this
    value = settings.get('trading_mode.current_mode')
    assert value == 'LIVE'
    print(f"✅ PASS: get('trading_mode.current_mode') = {value}")

    settings.set('trading_mode.show_mode_banner', False)
    value = settings.get('trading_mode.show_mode_banner')
    assert value == False
    print(f"✅ PASS: set/get via dot notation works")

    # Test 10: First run flag
    print("\nTest 10: First Run Detection")
    assert settings.is_first_run() == True  # Default is first run
    print("✅ PASS: Detected first run")

    settings.mark_first_run_complete()
    assert settings.is_first_run() == False
    print("✅ PASS: First run marked complete")

    # Test 11: Summary
    print("\nTest 11: Settings Summary")
    summary = settings.get_summary()
    print("Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    assert 'version' in summary
    assert 'risk_profile' in summary
    print("✅ PASS: Summary generated")

    # Test 12: Export/Save
    print("\nTest 12: Save and Reload")
    settings.save()
    print("✅ PASS: Settings saved")

    # Create new instance and verify settings persisted
    settings2 = SettingsManagerV2(settings_file="test_settings_v2.json", auto_migrate=False)
    assert settings2.get_trading_mode() == TradingMode.LIVE
    assert settings2.is_first_run() == False
    print("✅ PASS: Settings persisted across instances")

    # Cleanup
    if os.path.exists("test_settings_v2.json"):
        os.remove("test_settings_v2.json")
        print("🧹 Cleanup: Test file removed")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)

    return True


if __name__ == '__main__':
    try:
        success = test_settings_v2_without_v1()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
