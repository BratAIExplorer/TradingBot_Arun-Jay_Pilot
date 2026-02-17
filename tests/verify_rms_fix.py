import sys
import os
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.getcwd())

import kickstart

class TestRMSCooldown(unittest.TestCase):
    def setUp(self):
        # Reset globals
        kickstart.RMS_FAILURES = {}
        kickstart.API_KEY = "test_key"
        kickstart.ACCESS_TOKEN = "test_token"

    def test_rms_failure_detection(self):
        """Test that place_order adds symbol to RMS_FAILURES on quantity error"""
        symbol = "TESTSTOCK"
        exchange = "NSE"
        
        # Mock safe_request to return an INSUFFICIENT response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "RMS: RULE: LIMIT CHECK FAILED FOR ENTITY ARUN-1 IN NSE-EQ SCRIP TESTSTOCK-EQ INSUFFICIENT BY-10 AND AVAILABLE QTY IS - 0"
        }
        
        with patch('kickstart.safe_request', return_value=mock_response):
            with patch('kickstart.log_ok'): # Suppress logging
                result = kickstart.place_order(symbol, exchange, 10, "SELL", "1234")
                
        self.assertFalse(result)
        self.assertIn((symbol, exchange), kickstart.RMS_FAILURES)
        self.assertIsInstance(kickstart.RMS_FAILURES[(symbol, exchange)], datetime)

    def test_check_existing_orders_cooldown(self):
        """Test that check_existing_orders returns True during cooldown"""
        symbol = "COOLSTOCK"
        exchange = "NSE"
        
        # Manually add to failures
        kickstart.RMS_FAILURES[(symbol, exchange)] = datetime.now()
        
        with patch('kickstart.log_ok'):
            # Should return True (blocked) due to cooldown even without API call
            result = kickstart.check_existing_orders(symbol, exchange, 1, "SELL")
            
        self.assertTrue(result)

    def test_cooldown_expiry(self):
        """Test that cooling down expires after 1 hour"""
        symbol = "OLDSTOCK"
        exchange = "NSE"
        
        # Add a failure from 2 hours ago
        kickstart.RMS_FAILURES[(symbol, exchange)] = datetime.now() - timedelta(hours=2)
        
        # Mock API to return no orders
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": []}
        
        with patch('kickstart.safe_request', return_value=mock_response):
            with patch('kickstart.log_ok'):
                result = kickstart.check_existing_orders(symbol, exchange, 1, "SELL")
        
        # Should be False now because cooldown expired and no actual orders exist
        self.assertFalse(result)
        self.assertNotIn((symbol, exchange), kickstart.RMS_FAILURES)

if __name__ == '__main__':
    unittest.main()
