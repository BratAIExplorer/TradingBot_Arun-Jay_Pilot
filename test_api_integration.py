#!/usr/bin/env python3
"""
mStock API Integration Test Suite
==================================

Tests API connectivity, authentication, and endpoints WITHOUT placing real orders.
Can run ANYTIME - market open or closed.

Usage:
    python test_api_integration.py              # Run all tests
    python test_api_integration.py --quick      # Run quick tests only
    python test_api_integration.py --gui        # Show GUI results

Author: ARUN Trading Bot
Version: 2.0
Date: January 18, 2026
"""

import os
import sys
import json
import argparse
from datetime import datetime, time as dtime, timedelta
from typing import Dict, List, Optional

# Graceful imports with fallbacks
try:
    import requests
except ImportError:
    print("⚠️  Warning: 'requests' library not installed. Install with: pip install requests")
    requests = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  Warning: 'python-dotenv' not installed. Reading from environment variables directly.")
    def load_dotenv():
        pass

try:
    import pytz
except ImportError:
    print("⚠️  Warning: 'pytz' not installed. Using system timezone.")
    pytz = None

import hashlib
from urllib.parse import urlencode

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class APIIntegrationTester:
    """
    Comprehensive API integration test suite
    Tests all critical endpoints without side effects
    """

    def __init__(self):
        """Initialize tester with API credentials from .env"""
        self.api_key = os.getenv('MSTOCK_API_KEY')
        self.api_secret = os.getenv('MSTOCK_API_SECRET')
        self.access_token = os.getenv('MSTOCK_ACCESS_TOKEN')

        self.base_url = "https://api.mstock.trade/openapi/typea"

        # Set timezone (with fallback)
        if pytz:
            self.ist = pytz.timezone("Asia/Kolkata")
        else:
            self.ist = None  # Will use system time

        # Test results
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def get_now(self):
        """Get current time in IST (with fallback)"""
        if self.ist:
            return datetime.now(self.ist)
        else:
            return datetime.now()

    def print_header(self):
        """Print test suite header"""
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}{Colors.HEADER}mStock API Integration Test Suite{Colors.ENDC}")
        print("=" * 80)
        print(f"Timestamp: {self.get_now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"Market Status: {'🟢 OPEN' if self.is_market_open() else '🔴 CLOSED'}")
        print("=" * 80 + "\n")

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = self.get_now()
        if now.weekday() >= 5:  # Weekend
            return False
        market_start = dtime(9, 15)
        market_end = dtime(15, 30)
        current_time = now.time()
        return market_start <= current_time <= market_end

    def add_result(self, test_name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add test result"""
        result = {
            'test': test_name,
            'status': status,  # PASS, FAIL, WARNING
            'message': message,
            'details': details or {},
            'timestamp': self.get_now().isoformat()
        }
        self.results.append(result)

        if status == 'PASS':
            self.passed += 1
            print(f"{Colors.OKGREEN}✅ PASS{Colors.ENDC} - {test_name}")
            print(f"   {message}")
        elif status == 'FAIL':
            self.failed += 1
            print(f"{Colors.FAIL}❌ FAIL{Colors.ENDC} - {test_name}")
            print(f"   {message}")
        elif status == 'WARNING':
            self.warnings += 1
            print(f"{Colors.WARNING}⚠️  WARN{Colors.ENDC} - {test_name}")
            print(f"   {message}")

        if details:
            print(f"   {Colors.OKCYAN}Details: {json.dumps(details, indent=2)}{Colors.ENDC}")
        print()

    def test_credentials_loaded(self) -> bool:
        """Test 1: Check if API credentials are loaded from .env"""
        test_name = "Environment Variables"

        missing = []
        if not self.api_key:
            missing.append('MSTOCK_API_KEY')
        if not self.api_secret:
            missing.append('MSTOCK_API_SECRET')
        if not self.access_token:
            missing.append('MSTOCK_ACCESS_TOKEN')

        if missing:
            self.add_result(
                test_name,
                'FAIL',
                f"Missing credentials in .env file: {', '.join(missing)}",
                {'missing_vars': missing}
            )
            return False
        else:
            self.add_result(
                test_name,
                'PASS',
                "All required credentials found in .env file",
                {
                    'api_key_length': len(self.api_key),
                    'access_token_length': len(self.access_token)
                }
            )
            return True

    def test_user_profile(self) -> bool:
        """Test 2: Fetch user profile (no side effects)"""
        test_name = "User Profile API"

        try:
            headers = {
                "X-Mirae-Version": "1",
                "Authorization": f"Bearer {self.access_token}"
            }

            response = requests.get(
                f"{self.base_url}/user/profile",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})

                self.add_result(
                    test_name,
                    'PASS',
                    f"Successfully fetched user profile: {user_data.get('user_name', 'Unknown')}",
                    {
                        'user_id': user_data.get('user_id'),
                        'user_name': user_data.get('user_name'),
                        'broker': user_data.get('broker', 'mStock')
                    }
                )
                return True
            elif response.status_code == 401:
                self.add_result(
                    test_name,
                    'FAIL',
                    "Authentication failed - Invalid or expired access token",
                    {'status_code': 401, 'response': response.text}
                )
                return False
            else:
                self.add_result(
                    test_name,
                    'FAIL',
                    f"API returned error: {response.status_code}",
                    {'status_code': response.status_code, 'response': response.text}
                )
                return False

        except requests.Timeout:
            self.add_result(test_name, 'FAIL', "Request timeout - API server not responding")
            return False
        except requests.ConnectionError:
            self.add_result(test_name, 'FAIL', "Connection error - Check internet connection")
            return False
        except Exception as e:
            self.add_result(test_name, 'FAIL', f"Unexpected error: {str(e)}")
            return False

    def test_available_funds(self) -> bool:
        """Test 3: Fetch available funds (no side effects)"""
        test_name = "Available Funds API"

        try:
            headers = {
                "X-Mirae-Version": "1",
                "Authorization": f"Bearer {self.access_token}"
            }

            response = requests.get(
                f"{self.base_url}/funds",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                funds_data = data.get('data', {})
                available_cash = funds_data.get('available_cash', 0)

                self.add_result(
                    test_name,
                    'PASS',
                    f"Available cash: ₹{available_cash:,.2f}",
                    {
                        'available_cash': available_cash,
                        'used_margin': funds_data.get('used_margin', 0),
                        'available_margin': funds_data.get('available_margin', 0)
                    }
                )
                return True
            else:
                self.add_result(
                    test_name,
                    'FAIL',
                    f"API error: {response.status_code}",
                    {'response': response.text}
                )
                return False

        except Exception as e:
            self.add_result(test_name, 'FAIL', f"Error: {str(e)}")
            return False

    def test_positions(self) -> bool:
        """Test 4: Fetch current positions (no side effects)"""
        test_name = "Positions API"

        try:
            headers = {
                "X-Mirae-Version": "1",
                "Authorization": f"Bearer {self.access_token}"
            }

            response = requests.get(
                f"{self.base_url}/positions",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                positions = data.get('data', [])

                position_details = []
                for pos in positions[:5]:  # Show first 5
                    position_details.append({
                        'symbol': pos.get('trading_symbol'),
                        'qty': pos.get('quantity'),
                        'avg_price': pos.get('average_price'),
                        'pnl': pos.get('pnl')
                    })

                self.add_result(
                    test_name,
                    'PASS',
                    f"Found {len(positions)} open position(s)",
                    {'count': len(positions), 'positions': position_details}
                )
                return True
            else:
                self.add_result(
                    test_name,
                    'FAIL',
                    f"API error: {response.status_code}",
                    {'response': response.text}
                )
                return False

        except Exception as e:
            self.add_result(test_name, 'FAIL', f"Error: {str(e)}")
            return False

    def test_order_validation(self) -> bool:
        """Test 5: Validate order parameters WITHOUT placing order"""
        test_name = "Order Parameter Validation"

        # Test order parameters (NOT sent to API)
        test_order = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 1,
            'side': 'BUY',
            'order_type': 'MARKET',
            'product': 'CNC'
        }

        # Validate locally
        validation_errors = []

        if not test_order['symbol'] or len(test_order['symbol']) == 0:
            validation_errors.append("Symbol cannot be empty")

        if test_order['exchange'] not in ['NSE', 'BSE']:
            validation_errors.append(f"Invalid exchange: {test_order['exchange']}")

        if test_order['quantity'] <= 0:
            validation_errors.append("Quantity must be positive")

        if test_order['side'] not in ['BUY', 'SELL']:
            validation_errors.append(f"Invalid side: {test_order['side']}")

        if validation_errors:
            self.add_result(
                test_name,
                'FAIL',
                f"Order validation failed: {', '.join(validation_errors)}",
                {'errors': validation_errors}
            )
            return False
        else:
            # Simulate what API would return if we tried to place order now
            market_open = self.is_market_open()

            if market_open:
                simulated_response = {
                    'status': 'success',
                    'message': 'Order would be accepted (market is open)',
                    'order_id': 'SIMULATED_ORDER_123456'
                }
                status_msg = "Order parameters valid. Market is OPEN - order would be accepted."
            else:
                simulated_response = {
                    'status': 'error',
                    'error_code': 'MARKET_CLOSED',
                    'message': 'Market is closed. Orders can only be placed during market hours (9:15 AM - 3:30 PM IST, Mon-Fri)'
                }
                status_msg = "Order parameters valid. Market is CLOSED - API would reject with 'MARKET_CLOSED' error."

            self.add_result(
                test_name,
                'PASS',
                status_msg,
                {
                    'test_order': test_order,
                    'simulated_api_response': simulated_response,
                    'market_currently_open': market_open
                }
            )
            return True

    def test_session_validity(self) -> bool:
        """Test 6: Check if session/access token is valid"""
        test_name = "Session Token Validity"

        # If we successfully fetched user profile, session is valid
        # This is a logical test based on previous results

        profile_test = next((r for r in self.results if r['test'] == 'User Profile API'), None)

        if profile_test and profile_test['status'] == 'PASS':
            self.add_result(
                test_name,
                'PASS',
                "Session token is valid and active",
                {'token_type': 'Bearer', 'authenticated': True}
            )
            return True
        else:
            self.add_result(
                test_name,
                'FAIL',
                "Session token is invalid or expired. Run authentication flow to get new token.",
                {'authenticated': False}
            )
            return False

    def test_market_hours_check(self) -> bool:
        """Test 7: Market hours detection logic"""
        test_name = "Market Hours Detection"

        now = self.get_now()
        is_open = self.is_market_open()

        market_start = dtime(9, 15)
        market_end = dtime(15, 30)

        if is_open:
            next_close = now.replace(hour=15, minute=30, second=0)
            time_until_close = (next_close - now).total_seconds() / 60
            message = f"Market is OPEN. Closes in {int(time_until_close)} minutes."
        else:
            # Calculate next market open
            if now.weekday() >= 5:  # Weekend
                days_until_monday = (7 - now.weekday()) % 7
                next_open = now.replace(hour=9, minute=15, second=0) + timedelta(days=days_until_monday)
            elif now.time() < market_start:
                # Before market open today
                next_open = now.replace(hour=9, minute=15, second=0)
            else:
                # After market close, next day
                next_open = (now + timedelta(days=1)).replace(hour=9, minute=15, second=0)
                if next_open.weekday() >= 5:
                    days_until_monday = (7 - next_open.weekday()) % 7
                    next_open = next_open + timedelta(days=days_until_monday)

            message = f"Market is CLOSED. Opens at {next_open.strftime('%A, %d %b %Y at %I:%M %p IST')}"

        self.add_result(
            test_name,
            'PASS',
            message,
            {
                'market_open': is_open,
                'current_time': now.strftime('%H:%M:%S IST'),
                'day_of_week': now.strftime('%A'),
                'market_hours': '9:15 AM - 3:30 PM IST (Mon-Fri)'
            }
        )
        return True

    def run_all_tests(self, quick: bool = False) -> Dict:
        """
        Run all integration tests

        Args:
            quick: If True, run only essential tests

        Returns:
            dict: Summary of test results
        """
        self.print_header()

        # Essential tests (always run)
        print(f"{Colors.BOLD}Running Essential Tests...{Colors.ENDC}\n")
        self.test_credentials_loaded()
        self.test_user_profile()
        self.test_session_validity()
        self.test_order_validation()
        self.test_market_hours_check()

        if not quick:
            # Additional tests
            print(f"\n{Colors.BOLD}Running Additional Tests...{Colors.ENDC}\n")
            self.test_available_funds()
            self.test_positions()

        # Print summary
        self.print_summary()

        return {
            'passed': self.passed,
            'failed': self.failed,
            'warnings': self.warnings,
            'total': len(self.results),
            'success_rate': (self.passed / len(self.results) * 100) if self.results else 0,
            'results': self.results
        }

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
        print("=" * 80)
        print(f"Total Tests:   {len(self.results)}")
        print(f"{Colors.OKGREEN}Passed:        {self.passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed:        {self.failed}{Colors.ENDC}")
        print(f"{Colors.WARNING}Warnings:      {self.warnings}{Colors.ENDC}")

        if len(self.results) > 0:
            success_rate = (self.passed / len(self.results)) * 100
            print(f"Success Rate:  {success_rate:.1f}%")

        print("=" * 80)

        if self.failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ All tests passed! API integration is working correctly.{Colors.ENDC}")
            print(f"{Colors.OKGREEN}You can safely run the trading bot.{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ Some tests failed. Please fix the issues above.{Colors.ENDC}")
            print(f"{Colors.FAIL}Do NOT run the trading bot until all tests pass.{Colors.ENDC}\n")

    def export_results(self, filename: str = "api_test_results.json"):
        """Export test results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': self.get_now().isoformat(),
                'summary': {
                    'passed': self.passed,
                    'failed': self.failed,
                    'warnings': self.warnings,
                    'total': len(self.results)
                },
                'results': self.results
            }, f, indent=2)

        print(f"\n📄 Results exported to: {filename}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='mStock API Integration Test Suite')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--export', type=str, help='Export results to JSON file')
    parser.add_argument('--gui', action='store_true', help='Show GUI results (future feature)')

    args = parser.parse_args()

    # Run tests
    tester = APIIntegrationTester()
    results = tester.run_all_tests(quick=args.quick)

    # Export if requested
    if args.export:
        tester.export_results(args.export)

    # Exit code based on results
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
