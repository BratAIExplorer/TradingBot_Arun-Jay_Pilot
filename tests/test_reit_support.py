
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from constants import REIT_TOKEN_MAP
import symbol_validator
import kickstart

class TestREITSupport(unittest.TestCase):

    def test_reit_mappings_exist(self):
        """Ensure constants are defined"""
        self.assertIn("EMBASSY", REIT_TOKEN_MAP)
        self.assertIn("BIRET", REIT_TOKEN_MAP)
        self.assertIn("MINDSPACE", REIT_TOKEN_MAP)
        print("\n✅ REIT Mappings Confirmed")

    def test_validation_logic(self):
        """Test that validate_symbol returns True for REITs without calling Yahoo"""
        
        # We mock get_yfinance_session to ensure it's NOT called for REITs if optimization works
        with patch('symbol_validator.get_yfinance_session') as mock_yf:
            # Test EMBASSY
            is_valid = symbol_validator.validate_symbol("EMBASSY", "NSE")
            self.assertTrue(is_valid, "EMBASSY should be valid")
            mock_yf.assert_not_called() 
            print("✅ EMBASSY validated without Yahoo call")
            
            # Test Normal Symbol (should call YF)
            # We mock the return of ticker.history to be non-empty
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = MagicMock(empty=False)
            
            with patch('yfinance.Ticker', return_value=mock_ticker):
                symbol_validator.validate_symbol("RELIANCE", "NSE")
                self.assertTrue(mock_yf.called, "Normal symbol should trigger Yahoo call")
                print("✅ Normal symbol triggered Yahoo call as expected")

    def test_startup_token_resolution(self):
        """Test that kickstart resolves tokens for REITs from the map"""
        
        # Mock safe_request to fail (so we prove it uses the MAP, not the API)
        with patch('kickstart.safe_request', return_value=None):
            token = kickstart.resolve_instrument_token("EMBASSY", "NSE")
            self.assertEqual(token, REIT_TOKEN_MAP["EMBASSY"])
            print(f"✅ Resolved EMBASSY to {token} using local map")
            
            token2 = kickstart.resolve_instrument_token("BIRET", "NSE")
            self.assertEqual(token2, REIT_TOKEN_MAP["BIRET"])
            print(f"✅ Resolved BIRET to {token2} using local map")

    def test_initialize_stock_configs_reit_injection(self):
        """Test full config initialization with REITs"""
        
        # Setup mock settings
        mock_settings = MagicMock()
        mock_settings.get_stock_configs.return_value = [
            {"symbol": "EMBASSY", "exchange": "NSE", "enabled": True, "quantity": 10},
            {"symbol": "TATASTEEL", "exchange": "NSE", "enabled": True, "quantity": 5}
        ]
        
        # Patch kickstart's settings instance
        with patch('kickstart.settings', mock_settings):
            kickstart.initialize_stock_configs()
            
            # Verify SYMBOLS_TO_TRACK
            tracked = [s[0] for s in kickstart.SYMBOLS_TO_TRACK]
            self.assertIn("EMBASSY", tracked)
            self.assertIn("TATASTEEL", tracked)
            print("✅ kickstart initialized with REITs successfully")
            
            # Verify Dict
            self.assertIn(("EMBASSY", "NSE"), kickstart.config_dict)
            print("✅ Config dict populated")

if __name__ == '__main__':
    unittest.main()
