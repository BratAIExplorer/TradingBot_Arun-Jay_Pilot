# python -m pip install requests pandas python-dotenv pytz

import requests
import hashlib
from strategies.nifty_sip import NiftySIPStrategy
print("✅ LOADED KICKSTART V3.0 (Fixes Applied)")

# Strategy Engines
sip_engine = None
notifier = None
STOP_REQUESTED = False
import pandas as pd
from datetime import datetime, timedelta, time as dtime, date
import json
import sys
from urllib.parse import urlencode
from urllib.parse import quote
import os
from dotenv import load_dotenv
import traceback
import pytz
import time
import socket
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from getRSI import calculate_intraday_rsi_tv
import logging
from requests.exceptions import Timeout, ConnectionError, RequestException
try:
    import pyotp
except ImportError:
    print("⚠️ pyotp not found, auto-login disabled")
    pyotp = None

try:
    from nifty50 import NIFTY_50
except ImportError:
    NIFTY_50 = set()

# ---------------- New Module Imports (Phase 0A) ----------------
try:
    from settings_manager import SettingsManager
    SETTINGS_AVAILABLE = True
except ImportError:
    print("⚠️ settings_manager not found, using legacy config")
    SETTINGS_AVAILABLE = False

try:
    from database.trades_db import TradesDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    print("⚠️ database module not found, trade logging disabled")
    DATABASE_AVAILABLE = False

try:
    from risk_manager import RiskManager
    RISK_MANAGER_AVAILABLE = True
except ImportError:
    print("⚠️ risk_manager not found, automated risk controls disabled")
    RISK_MANAGER_AVAILABLE = False

try:
    from state_manager import StateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    print("⚠️ state_manager not found, state persistence disabled")
    STATE_MANAGER_AVAILABLE = False

try:
    from notifications import NotificationManager
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    print("⚠️ notifications module not found, alerts disabled")
    NOTIFICATIONS_AVAILABLE = False

try:
    from utils import retry_on_failure, safe_divide, safe_get, setup_logging
    # Map retry_on_failure to retry_with_backoff if needed by other parts of the code
    retry_with_backoff = retry_on_failure
    UTILS_AVAILABLE = True
except ImportError:
    print("⚠️ utils not found, using basic fallback implementations")
    UTILS_AVAILABLE = False
    # Provide fallback functions
    def safe_divide(a, b, default=0):
        """Fallback safe divide"""
        return a / b if b != 0 else default
    def safe_get(d, key, default=None):
        """Fallback safe get"""
        if isinstance(d, dict) and '.' in key:
            keys = key.split('.')
            val = d
            for k in keys:
                if isinstance(val, dict) and k in val: val = val[k]
                else: return default
            return val
        return d.get(key, default) if isinstance(d, dict) else default
    def retry_with_backoff(max_retries=3):
        def decorator(func):
            return func # Simple no-op fallback
        return decorator

    def setup_logging(log_file="bot.log", level=20): pass # fallback


# ---------------- State & Utils ----------------

LOG_SUPPRESS = False

# Initialize Logging
try:
    setup_logging()
except Exception as e:
    print(f"Failed to setup logging: {e}")

def log_ok(msg: str = "", *args, force: bool = False, **kwargs):
    logging.info(msg)
    if LOG_SUPPRESS and not force:
        return
    # print(msg, *args, **kwargs) # Disable print, use logging

def log_fetch(symbol_ex: str):
    if not LOG_SUPPRESS and is_market_open_now_ist():
        log_ok(f"🔍 Fetching → {symbol_ex}")

@dataclass
class InflightState:
    fetching: bool
    result: Optional[dict]

OFFLINE = {"active": False, "since": None}
FETCH_INFLIGHT: Dict[str, bool] = {}
CYCLE_QUOTES: Dict[str, Optional[dict]] = {}
SYMBOL_LOCKS: Dict[str, bool] = {}  # Simplified to boolean for sync
FETCH_STATE: Dict[str, InflightState] = {}
MISSING_TOKEN_LOGGED: Dict[str, bool] = {}

def reset_cycle_state():
    MISSING_TOKEN_LOGGED.clear()
    CYCLE_QUOTES.clear()

def log_missing_token_once(exchange: str, symbol: str, err: Exception):
    key = f"{exchange}:{symbol.upper()}"
    if not MISSING_TOKEN_LOGGED.get(key):
        log_ok(f"❌ Missing token for {exchange}:{symbol} — {err}")
        MISSING_TOKEN_LOGGED[key] = True

def ensure_inflight(key: str) -> InflightState:
    st = FETCH_STATE.get(key)
    if st is None:
        st = InflightState(fetching=False, result=None)
        FETCH_STATE[key] = st
    return st

def fetch_market_data_once(symbol: str, exchange: str) -> Tuple[Optional[dict], Optional[str]]:
    if is_offline():
        return None, None

    key = f"{exchange}:{symbol.upper()}"
    cached = CYCLE_QUOTES.get(key)
    if cached is not None:
        return cached, exchange

    st = ensure_inflight(key)
    if st.fetching:
        for _ in range(20):  # Spin-wait for sync compatibility
            time.sleep(0.01)
            cached = CYCLE_QUOTES.get(key)
            if cached is not None:
                return cached, exchange
        return None, None

    st.fetching = True
    try:
        url = "https://api.mstock.trade/openapi/typea/instruments/quote/ohlc"
        headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
        params = {"i": key}
        resp = safe_request("GET", url, headers=headers, params=params)
        if resp is None or resp.status_code != 200:
            if resp is not None:
                log_ok(f"❌ API error {resp.status_code}: {resp.text}")
            st.result = None
        else:
            data = resp.json() or {}
            st.result = (data.get("data") or {}).get(params["i"])
        CYCLE_QUOTES[key] = st.result
        return st.result, exchange
    finally:
        st.fetching = False

INSUFFICIENT_HISTORY_TS: Dict[str, pd.Timestamp] = {}

def should_log_insufficient_history(symbol: str, bar_ts: pd.Timestamp) -> bool:
    last = INSUFFICIENT_HISTORY_TS.get(symbol)
    if last is None or last != bar_ts:
        INSUFFICIENT_HISTORY_TS[symbol] = bar_ts
        return True
    return False

def get_symbol_lock(symbol: str) -> bool:
    return SYMBOL_LOCKS.setdefault(symbol, False)

def reset_cycle_quotes():
    CYCLE_QUOTES.clear()

def is_offline() -> bool:
    return bool(OFFLINE.get("active"))

def mark_offline_once():
    if not OFFLINE["active"]:
        OFFLINE["active"] = True
        OFFLINE["since"] = datetime.now(pytz.timezone("Asia/Kolkata"))
        log_ok("🔴 Offline detected — pausing trading loop and monitoring connectivity")

def mark_online_if_needed():
    if OFFLINE["active"]:
        OFFLINE["active"] = False
        OFFLINE["since"] = None

def safe_request(method, url, **kwargs):
    try:
        if "timeout" not in kwargs:
            kwargs["timeout"] = (5, 15)
        resp = requests.request(method=method, url=url, **kwargs)
        
        # 403 Forbidden / 401 Unauthorized Handling (Auto-Login Trigger)
        if resp.status_code in [401, 403]:
            # Avoid infinite recursion if verifytotp itself fails
            if "verifytotp" not in url:
                log_ok(f"⚠️ API Error {resp.status_code}. Attempting Auto-Login refresh...")
                if perform_auto_login():
                     # Update headers with new token
                    if "headers" in kwargs and "Authorization" in kwargs["headers"]:
                        kwargs["headers"]["Authorization"] = f"token {API_KEY}:{ACCESS_TOKEN}"
                    # Retry once
                    log_ok("🔄 Retrying request with new token...")
                    resp = requests.request(method=method, url=url, **kwargs)

        mark_online_if_needed()
        return resp
    except (ConnectionError, Timeout):
        mark_offline_once()
        return None
    except RequestException as e:
        if not is_offline():
            log_ok(f"⚠️ Request error: {str(e)}")
        return None

def now_ist():
    return datetime.now(pytz.timezone("Asia/Kolkata"))

# ---------------- Config & Auth ----------------

# ---------------- Initialize Settings Manager Early (Phase 0A) ----------------
settings = None
if SETTINGS_AVAILABLE:
    try:
        settings = SettingsManager()
        settings.load()
    except Exception as e:
        print(f"⚠️ Settings Manager early init failed: {e}")

# ---------------- Config & Auth ----------------

load_dotenv()

# Prioritize settings.json, fallback to .env
API_KEY = settings.get_decrypted("broker.api_key") if settings else os.getenv('API_KEY')
API_SECRET = settings.get_decrypted("broker.api_secret") if settings else os.getenv('API_SECRET')
CLIENT_CODE = settings.get("broker.client_code") if settings else os.getenv('CLIENT_CODE')
PASSWORD = settings.get_decrypted("broker.password") if settings else os.getenv('PASSWORD')

if not all([API_KEY, API_SECRET, CLIENT_CODE]):
    log_ok("⚠️ Warning: Missing broker credentials. Please configure them in the Settings GUI.")
    if not any([API_KEY, API_SECRET, CLIENT_CODE]):
        log_ok("❌ Essential credentials missing. Bot will not be able to trade.")

EXCHANGES = ["NSE", "BSE"]

def reload_config():
    """Hot-reload settings and credentials without restart"""
    global settings, API_KEY, API_SECRET, CLIENT_CODE, ACCESS_TOKEN, PASSWORD
    
    log_ok("🔄 Reloading Configuration...")
    try:
        if SETTINGS_AVAILABLE:
            settings = SettingsManager() # Re-init
            settings.load()
            
            # Re-fetch credentials
            API_KEY = settings.get_decrypted("broker.api_key")
            API_SECRET = settings.get_decrypted("broker.api_secret")
            CLIENT_CODE = settings.get("broker.client_code")
            PASSWORD = settings.get_decrypted("broker.password")
            ACCESS_TOKEN = settings.get_decrypted("broker.access_token")
            
            log_ok("✅ Configuration Reloaded Successfully")
            log_ok("✅ Configuration Reloaded Successfully")
            return True
    except Exception as e:
        log_ok(f"❌ Failed to reload config: {e}")
        return False

# --- CAPITAL & RISK GLOBALS ---
portfolio_state = {}
RSI_PERIOD = 14
ALLOCATED_CAPITAL = 50000.0 # Default Safety Limit (₹50k)

if settings:
    try:
        # Load User's "Safety Box" Limit
        ALLOCATED_CAPITAL = float(settings.get("capital.allocated_limit", 50000.0))
        log_ok(f"💰 Bot Capital Limit Set to: ₹{ALLOCATED_CAPITAL:,.2f}")
    except: pass

def check_capital_safety(required_amount):
    """
    Returns True if we have enough ALLOCATED funds for this trade.
    This separates 'Bot Funds' from 'Life Savings'.
    """
    try:
        # Calculate currently used capital by BOT (sum of active positions cost)
        used_capital = 0.0
        conn = get_db_connection()
        cursor = conn.cursor()
        # Only count OPEN trades initiated by BOT
        cursor.execute("SELECT entry_price, quantity FROM trades WHERE status='OPEN' AND source='BOT'")
        rows = cursor.fetchall()
        for p, q in rows:
            used_capital += (p * q)
        conn.close()
        
        remaining = ALLOCATED_CAPITAL - used_capital
        
        if remaining >= required_amount:
            return True, remaining
        else:
            log_ok(f"🚫 Capital Limit Reached! Allocated: ₹{ALLOCATED_CAPITAL}, Used: ₹{used_capital}. Needed: ₹{required_amount}")
            return False, remaining
    except Exception as e:
        log_ok(f"⚠️ Capital Check Error: {e}. Defaulting to Safe Mode (Block).")
        return False, 0.0

# Consolidate Access Token
ACCESS_TOKEN = settings.get_decrypted("broker.access_token") if settings else None

# Migration Logic: If token is in credentials.json but not in settings, migrate it (Phase 0A Cleanup)
if not ACCESS_TOKEN and os.path.exists("credentials.json"):
    try:
        with open("credentials.json", "r") as f:
            legacy_creds = json.load(f)
            ACCESS_TOKEN = legacy_creds.get("mstock", {}).get("access_token")
            if ACCESS_TOKEN and settings:
                settings.set("broker.access_token", ACCESS_TOKEN)
                log_ok("🔐 Migrated access token from credentials.json to encrypted settings.json")
    except Exception as e:
        log_ok(f"⚠️ Migration from credentials.json failed: {e}")

def fetch_market_data(symbol, exchange):
    # 1. 24/7 SIMULATION FALLBACK (Fabricated Data)
    # Check if we should simulate data (Paper Mode + API Failure/Market Closed)
    should_simulate = False
    if SETTINGS_AVAILABLE:
        try:
            sm = SettingsManager()
            sm.load()
            if sm.get("app_settings", {}).get("paper_trading_mode", False):
                should_simulate = True
        except: pass

    # Try Real API First
    if not is_offline():
        try:
            url = "https://api.mstock.trade/openapi/typea/instruments/quote/ohlc"
            headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
            params = {"i": f"{exchange}:{symbol.upper()}"}
            response = safe_request("GET", url, headers=headers, params=params)
            
            if response and response.status_code == 200:
                data = response.json() or {}
                result = (data.get("data") or {}).get(params["i"])
                if result:
                    return result, exchange
        except Exception as e:
            # If simulaton is allowed, suppress the error to avoid log spam
            if not should_simulate:
                log_ok(f"❌ API Error for {symbol}: {e}")
            pass # Fallthrough to simulation if allowed

    # 2. Generate Fabricated Data if Allowed
    if should_simulate:
        # Generate a "Realistic" random walk price based on persistent state
        import random
        
        # Initialize Mock State if needed
        if 'MOCK_PRICES' not in globals():
            global MOCK_PRICES
            MOCK_PRICES = {}
            
        # Get last known mock price or seed
        if symbol not in MOCK_PRICES:
            base_seed = 1000.0
            if symbol == "NIFTY 50": base_seed = 24500.0
            elif symbol == "NIFTY BANK": base_seed = 52000.0
            elif symbol == "RELIANCE": base_seed = 2600.0
            elif symbol == "HDFCBANK": base_seed = 1650.0
            elif symbol == "TCS": base_seed = 3900.0
            MOCK_PRICES[symbol] = base_seed
            
        current_price = MOCK_PRICES[symbol]
        
        # Random Walk: drift 0, vol 0.02% per tick
        import random
        change = current_price * random.gauss(0, 0.0002) 
        new_price = current_price + change
        MOCK_PRICES[symbol] = new_price
        
        # Calculate daily change mock
        open_price = MOCK_PRICES[symbol] * 0.995 # Mock open
        change_pct = ((new_price - open_price) / open_price) * 100
        
        # Mock Response Structure matching mStock
        return {
            "last_price": new_price,
            "ohlc": {
                "open": open_price,
                "high": max(open_price, new_price * 1.001),
                "low": min(open_price, new_price * 0.999),
                "close": open_price # Prev close
            },
            "change_percent": change_pct,
            "instrument_token": "999999" # Mock Token
        }, exchange

    if not is_offline():
         # Only log if we really expected data and failed/didn't simulate
         pass
    return None, None

def fetch_funds():
    """Fetch available funds from broker"""
    if is_offline() or not ACCESS_TOKEN:
        return 0.0
    
    # Generic endpoint for mStock/Mirae (Limits/Cash)
    # Note: Exact endpoint path might vary, using standard Type A path pattern
    url = "https://api.mstock.trade/openapi/typea/limits/getCashLimits" 
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    
    try:
        response = safe_request("GET", url, headers=headers)
        if response and response.status_code == 200:
            data = response.json()
            # Parse response - usually 'data' -> 'availableCash' or similar
            # Placeholder parsing logic based on standard response structure
            return float(safe_get(data, "data.availableCash", 0.0))
    except Exception as e:
        log_ok(f"⚠️ Failed to fetch funds: {e}")
    
    return 0.0

    return 0.0

def check_connectivity_latency() -> Tuple[bool, int]:
    """Check API connection and measure latency in ms"""
    if is_offline() or not ACCESS_TOKEN:
        return False, 0
        
    start = time.time()
    try:
        # Use a lightweight endpoint - Limits is good
        url = "https://api.mstock.trade/openapi/typea/limits/getCashLimits"
        headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
        resp = safe_request("GET", url, headers=headers, timeout=(3, 5))
        
        latency = int((time.time() - start) * 1000)
        
        if resp and resp.status_code == 200:
            return True, latency
        return False, latency
    except Exception:
        return False, 0

def get_market_status_display() -> str:
    """Return display string for market status (IST)"""
    now = now_ist()
    t = now.time()
    
    # Weekends
    if now.weekday() >= 5: # Sat or Sun
        return "CLOSED (Weekend)"
        
    # Trading Hours (approx)
    pre_open_start = dtime(9, 0)
    market_start = dtime(9, 15)
    market_end = dtime(15, 30)
    
    if pre_open_start <= t < market_start:
        return "PRE-OPEN"
    elif market_start <= t < market_end:
        return "OPEN"
    elif t >= market_end:
        return "CLOSED"
    else:
        return "CLOSED"

def fetch_orders():
    """Fetch all orders for the day from broker"""
    if is_offline() or not ACCESS_TOKEN:
        return []
    
    # Generic endpoint for mStock/Mirae (Orders)
    url = "https://api.mstock.trade/openapi/typea/orders"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    
    try:
        response = safe_request("GET", url, headers=headers)
        if response and response.status_code == 200:
            data = response.json()
            # Expecting list of orders in data['data']
            return data.get("data", [])
    except Exception as e:
        log_ok(f"⚠️ Failed to fetch orders: {e}")
    
    return []

    return []

def cancel_all_orders() -> int:
    """
    Cancel all open/pending orders
    Returns: Count of cancelled orders
    """
    if is_offline() or not ACCESS_TOKEN:
        return 0
        
    count = 0
    orders = fetch_orders()
    for order in orders:
        status = order.get("orderStatus")
        if status not in ["COMPLETE", "REJECTED", "CANCELLED", "TRADED"]:
            # Need order ID
            oid = order.get("orderID") or order.get("orderId")
            if oid:
                # API Call to cancel
                url = "https://api.mstock.trade/openapi/typea/orders/cancel"
                headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
                payload = {"orderId": oid} # Adjust payload based on exact API spec
                try:
                    # Note: Type A cancel might differ slightly, using simplified payload for now
                    # requests.delete usually not used, usually POST for cancel endpoint in mStock
                    # Research suggests POST to /cancel with body
                    requests.post(url, json=payload, headers=headers, timeout=5)
                    count += 1
                except Exception:
                    pass
    log_ok(f"🚨 Panic Mode: Cancelled {count} pending orders.")
    return count

def square_off_all_positions() -> int:
    """
    Close all open positions at Market Price
    Returns: Count of positions closed
    """
    if is_offline() or not ACCESS_TOKEN:
        return 0

    count = 0
    positions = safe_get_live_positions_merged() 
    # This returns dict {symbol: details}
    
    for symbol_key, pos in positions.items():
        qty = int(pos.get("qty", 0))
        if qty == 0: continue
        
        # Determine symbol and exchange
        if isinstance(symbol_key, tuple):
            symbol, exchange = symbol_key
        else:
            symbol = str(symbol_key)
            exchange = "NSE" # Default assumption
            
        side = "SELL" if qty > 0 else "BUY"
        abs_qty = abs(qty)
        
        # Place Market Exit Order
        # We use instrument token if available, logic similar to place_order
        # For panic mode, we force MKT order
        
        # We need instrument token. 
        # Ideally we refactor place_order to handle this, but for now we try best effort
        try:
           # Assuming place_order handles instrument token lookup internally if not passed? 
           # No, it needs it. We must fetch.
           md, _ = fetch_market_data_once(symbol, exchange)
           it = md.get("instrument_token") if md else None
           
           if it:
               place_order(symbol, exchange, abs_qty, side, it, price=0)
               count += 1
        except Exception:
            pass
            
    log_ok(f"🚨 Panic Mode: Squared off {count} positions.")
    return count

def perform_auto_login() -> bool:
    """
    Attempt to auto-login using stored TOTP secret
    Returns: True if successful, False otherwise
    """
    global ACCESS_TOKEN
    
    if not pyotp:
        log_ok("⚠️ Auto-login skipped: pyotp not installed.")
        return False
        
    try:
        # Get TOTP Secret from settings
        # Note: We duplicate logic here for robustness if settings_mgr isn't fully init
        config_path = "settings.json"
        
        # Helper to find settings file
        if not os.path.exists(config_path):
            # Try looking relative to script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "settings.json")
            
        if not os.path.exists(config_path):
            log_ok("⚠️ Auto-login skipped: settings.json not found.")
            return False
            
        with open(config_path, "r") as f:
            settings = json.load(f)
            
        totp_secret = safe_get(settings, "api.totp_secret")
        api_key = safe_get(settings, "api.access_token") # We use 'access_token' field for API Key in this app
        
        if not totp_secret or not api_key:
            log_ok("⚠️ Auto-login skipped: TOTP secret or API Key missing.")
            return False
            
        # Generate TOTP
        try:
            totp = pyotp.TOTP(totp_secret)
            otp_code = totp.now()
            log_ok(f"🔐 Generating TOTP for auto-login...")
        except Exception as e:
            log_ok(f"❌ TOTP Generation failed: {e}")
            return False
            
        # Call Verify TOTP API
        url = "https://api.mstock.trade/openapi/typea/session/verifytotp"
        payload = {"api_key": api_key, "totp": otp_code}
        headers = {
            "X-Mirae-Version": "1", 
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Direct request to avoid recursion with safe_request if it checks token
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                new_token = safe_get(data, "data.access_token")
                if new_token:
                    ACCESS_TOKEN = new_token
                    log_ok("✅ Auto-Login SUCCESS! Access Token refreshed.")
                    return True
            else:
                log_ok(f"❌ Auto-Login API Error: {data.get('message')}")
        else:
            log_ok(f"❌ Auto-Login HTTP {resp.status_code}: {resp.text}")
            
    except Exception as e:
        log_ok(f"❌ Auto-Login Failed: {e}")
        
    return False

def handle_token_exception_and_refresh_token():
    global ACCESS_TOKEN
    log_ok("⚠️ Token refresh required (mStock session expired).")
    
    # 🔔 Notify user via Telegram/Email (MVP1 Feature)
    if notifier:
        try:
            notifier.send_auth_alert()
            log_ok("📲 Authentication alert sent via configured channels.")
        except Exception as e:
            log_ok(f"⚠️ Failed to send auth alert: {e}")

    try:
        login_url = "https://api.mstock.trade/openapi/typea/connect/login"
        login_payload = {"username": CLIENT_CODE, "password": PASSWORD}
        headers = {"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"}
        login_resp = requests.post(login_url, data=login_payload, headers=headers, timeout=(5, 15))
        if login_resp.status_code != 200:
            log_ok(f"❌ Login failed during token refresh: {login_resp.status_code}")
            return False
        login_data = login_resp.json()
        if login_data.get("status") != "success":
            log_ok(f"❌ Login error during token refresh: {login_data}")
            return False

        request_token = input("📩 Enter OTP sent to your registered device for token refresh: ")
        checksum_str = API_KEY + request_token + API_SECRET
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest()

        session_url = "https://api.mstock.trade/openapi/typea/session/token"
        session_payload = {"api_key": API_KEY, "request_token": request_token, "checksum": checksum}
        session_headers = {"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"}
        session_resp = requests.post(session_url, data=session_payload, headers=session_headers, timeout=(5, 15))
        if session_resp.status_code != 200:
            log_ok(f"❌ Session generation failed during token refresh: {session_resp.status_code}")
            return False
        session_data = session_resp.json()
        if session_data.get("status") != "success":
            log_ok(f"❌ Session error during token refresh: {session_data}")
            return False

        ACCESS_TOKEN = session_data["data"]["access_token"]
        if settings:
            settings.set("broker.access_token", ACCESS_TOKEN)
        
        # Legacy cleanup: Keep credentials.json empty or delete if preferred
        # For now, we just stop writing sensitive data to it.
        log_ok("✅ Access token refreshed and saved to encrypted settings.")
        return True
    except Exception as e:
        log_ok(f"❌ Exception in token refresh: {e}")
        return False

if not ACCESS_TOKEN:
    if __name__ == "__main__":
        if not handle_token_exception_and_refresh_token():
            sys.exit(1)
    else:
        log_ok("⚠️ Global Access Token is missing. Bot will not function until tokens are set in Settings.")

config_df = pd.read_csv('config_table.csv')
config_df['Enabled'] = config_df['Enabled'].astype(bool)
mstock_config = config_df[(config_df['Enabled']) & (config_df['Broker'] == 'mstock')]

duplicates = mstock_config[mstock_config.duplicated(subset=['Symbol', 'Exchange'], keep=False)]
if not duplicates.empty:
    log_ok("⚠️ Duplicate Symbol-Exchange pairs found in config_table.csv:")
    log_ok(duplicates)
    log_ok("Keeping the first occurrence of each duplicate pair.")
    mstock_config = mstock_config.drop_duplicates(subset=['Symbol', 'Exchange'], keep='first')

SYMBOLS_TO_TRACK = list(zip(mstock_config['Symbol'].str.upper(), mstock_config['Exchange'].str.upper()))
config_dict = mstock_config.set_index(['Symbol', 'Exchange']).to_dict('index')

# ---------------- Initialize Other Modules (Phase 0A) ----------------
settings = None
db = None
risk_mgr = None
state_mgr = None
notifier = None

if SETTINGS_AVAILABLE:
    try:
        settings = SettingsManager()
        log_ok("✅ Settings Manager initialized", force=True)
    except Exception as e:
        log_ok(f"⚠️ Settings Manager init failed: {e}", force=True)
        settings = None

if DATABASE_AVAILABLE:
    try:
        db = TradesDatabase()
        log_ok("✅ Trade Database initialized", force=True)
    except Exception as e:
        log_ok(f"⚠️ Database init failed: {e}", force=True)
        db = None

if RISK_MANAGER_AVAILABLE and db:
    try:
        # RiskManager(settings, database, market_data_fetcher)
        risk_mgr = RiskManager(settings, db, fetch_market_data)
        log_ok("✅ Risk Manager initialized", force=True)
    except Exception as e:
        log_ok(f"⚠️ Risk Manager init failed: {e}", force=True)
        risk_mgr = None
elif RISK_MANAGER_AVAILABLE and not db:
    log_ok("⚠️ Risk Manager skipped (database not available)", force=True)

if STATE_MANAGER_AVAILABLE:
    try:
        state_mgr = StateManager()
        log_ok("✅ State Manager initialized", force=True)
    except Exception as e:
        log_ok(f"⚠️ State Manager init failed: {e}", force=True)
        state_mgr = None

# Initialize Strategy Engines
sip_engine = NiftySIPStrategy(settings)

# Initialize Notification Manager
if NOTIFICATIONS_AVAILABLE and settings:
    try:
        notifier = NotificationManager(settings)
        log_ok("✅ Notification Manager initialized", force=True)
    except Exception as e:
        log_ok(f"⚠️ Notification Manager failed: {e}", force=True)


def get_exchange_for_symbol(symbol: str) -> list[str]:
    sym = symbol.upper()
    exchanges = [ex for (s, ex) in config_dict.keys() if s == sym]
    if not exchanges and sym in live_positions:
        exchanges = [live_positions[sym].get("exchange", "NSE")]
    if not exchanges:
        raise KeyError(f"No exchange found for symbol: {sym}")
    return exchanges

# ---------------- Positions ----------------

def get_positions():
    # Paper Trading Override
    if settings and settings.get("app_settings.paper_trading_mode"):
        if not db:
            return {}
        try:
            # Fetch simulated positions from DB
            db_positions = db.get_open_positions(is_paper=True)
            pos_dict = {}

            for pos in db_positions:
                sym = pos['symbol']
                qty = pos['net_quantity']
                avg_price = pos['avg_entry_price']
                exchange = pos['exchange']

                # Fetch live price for P&L calculation
                market_data, _ = fetch_market_data_once(sym, exchange)
                ltp = float(market_data.get("last_price", avg_price)) if market_data else avg_price

                pnl = (ltp - avg_price) * qty

                pos_dict[sym] = {
                    "qty": qty,
                    "price": avg_price,
                    "ltp": ltp,
                    "pnl": pnl,
                    "used_quantity": 0,
                    "exchange": exchange,
                    "is_paper": True
                }
            return pos_dict
        except Exception as e:
            log_ok(f"⚠️ Error fetching paper positions: {e}")
            return {}

    if is_offline():
        return {}
    url = "https://api.mstock.trade/openapi/typea/portfolio/holdings"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    resp = safe_request("GET", url, headers=headers)
    if resp is None:
        return {}
    if resp.status_code != 200:
        if not is_offline():
            log_ok(f"❌ Positions fetch error: {resp.text}")
            if "TokenException" or "invalid session" in resp.text:
                raise Exception("TokenException")
        return {}
    data_json = resp.json() or {}
    positions = data_json.get("data", []) or []
    
    # Mark token as validated for today (Smart Session Persistence)
    if state_mgr:
        state_mgr.mark_token_validated()
    pos_dict = {}
    for pos in positions:
        sym = pos.get("tradingsymbol")
        qty = pos.get("quantity", 0)
        price = pos.get("price", 0.0)
        ltp = pos.get("last_price", 0)
        pnl = pos.get("pnl", 0)
        used_quantity = pos.get("used_quantity", 0)
        if qty > 0 and qty - used_quantity != 0:
            pos_dict[sym] = {
                "qty": qty,
                "price": price,
                "ltp": ltp,
                "pnl": pnl,
                "used_quantity": used_quantity,
                "exchange": pos.get("exchange") or pos.get("exchangeSegment") or "NSE"
            }
    return pos_dict

def safe_get_positions():
    try:
        return get_positions()
    except Exception as e:
        error_str = str(e)
        if "TokenException" or "invalid session" in error_str:
            if handle_token_exception_and_refresh_token():
                return get_positions()
            else:
                if not is_offline():
                    log_ok("Failed to refresh token, cannot fetch positions.")
                return {}
        else:
            raise

def get_orders_today():
    # Paper Trading Override
    if settings and settings.get("app_settings.paper_trading_mode"):
        if not db:
            return []
        try:
            # Fetch simulated orders from DB for today
            df = db.get_today_trades(is_paper=True)
            if df is None: df = pd.DataFrame() # Fix NoneType error
            
            executed = []
            for _, row in df.iterrows():
                executed.append({
                    "tradingsymbol": row['symbol'],
                    "exchange": row['exchange'],
                    "transaction_type": row['action'],
                    "quantity": row['quantity'],
                    "filled_quantity": row['quantity'],
                    "price": row['price'],
                    "average_price": row['price'],
                    "status": "COMPLETE",
                    "order_timestamp": row['timestamp']
                })
            return executed
        except Exception as e:
            log_ok(f"⚠️ Error fetching paper orders: {e}")
            return []

    if is_offline():
        return []
    url = "https://api.mstock.trade/openapi/typea/orders"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    resp = safe_request("GET", url, headers=headers)
    if resp is None or resp.status_code != 200:
        return []
    data = resp.json() or {}
    orders = data.get("data", []) or []
    today = now_ist().date()
    executed = []
    for o in orders:
        status = (o.get("status") or "").upper()
        ts = o.get("order_timestamp") or o.get("updated_at") or o.get("created_at")
        ts_dt = None
        try:
            if ts:
                ts_dt = pd.to_datetime(ts).tz_localize(None).date()
        except Exception:
            ts_dt = None
        is_today = (ts_dt == today) if ts_dt else True
        if status in ("COMPLETE", "EXECUTED", "FILLED") and is_today:
            executed.append(o)
    return executed

def merge_positions_and_orders():
    holdings = get_positions()
    executed = get_orders_today()
    
    # Fetch BOT-initiated positions from DB to tag them
    bot_keys = set()
    if db:
        try:
            # Check paper/real mode from settings or logic
            is_paper = False 
            if settings and settings.get("app_settings.paper_trading_mode") == "1":
                is_paper = True
            
            # Fetch DB positions
            db_positions = db.get_open_positions(is_paper=is_paper)
            for p in db_positions:
                bot_keys.add((p['symbol'], p['exchange']))
        except: pass
    
    merged = {}
    for sym, pos in holdings.items():
        key = (sym, pos.get("exchange", "NSE"))
        source = "BOT" if key in bot_keys else "MANUAL"
        
        merged[key] = {
            "qty": int(pos.get("qty", 0)),
            "used_quantity": int(pos.get("used_quantity", 0)),
            "price": float(pos.get("price", 0.0)),
            "ltp": float(pos.get("ltp", 0.0)),
            "pnl": float(pos.get("pnl", 0.0)),
            "source": source
        }
    net = {}
    for o in executed:
        sym = o.get("tradingsymbol")
        ex = o.get("exchange") or o.get("exchangeSegment") or "NSE"
        side = (o.get("transaction_type") or "").upper()
        qty = int(o.get("quantity") or o.get("filled_quantity") or 0)
        avg = float(o.get("average_price") or o.get("price") or 0.0)
        if not sym or qty <= 0:
            continue
        key = (sym, ex)
        n = net.setdefault(key, {"net_qty": 0, "gross_buy_qty": 0, "wap_buy_num": 0.0})
        if side == "BUY":
            n["net_qty"] += qty
            n["gross_buy_qty"] += qty
            n["wap_buy_num"] += qty * avg
        elif side == "SELL":
            n["net_qty"] -= qty
    for key, n in net.items():
        sym, ex = key
        source = "BOT" if key in bot_keys else "MANUAL"
        
        if key not in merged and n["net_qty"] != 0:
            wap_buy = (n["wap_buy_num"] / n["gross_buy_qty"]) if n["gross_buy_qty"] > 0 else 0.0
            merged[key] = {
                "qty": n["net_qty"],
                "used_quantity": 0,
                "price": wap_buy,
                "ltp": 0.0,
                "pnl": 0.0,
                "source": source
            }
        elif key in merged:
            merged[key]["qty"] += n["net_qty"]
            if merged[key]["qty"] < 0:
                merged[key]["qty"] = 0
            # If it became merged, we keep source as BOT if it was ever BOT, usually safe assumption
            if source == "BOT": merged[key]["source"] = "BOT"
            
    return merged

def safe_get_live_positions_merged():
    try:
        return merge_positions_and_orders()
    except Exception as e:
        if "TokenException" in str(e) or "invalid session" in str(e):
            if handle_token_exception_and_refresh_token():
                return merge_positions_and_orders()
            return {}
        raise

live_positions = safe_get_positions()

# ---------------- RSI Helpers ----------------

def tv_rma(series: pd.Series, length: int) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    alpha = 1.0 / float(length)
    sma = x.rolling(length, min_periods=length).mean()
    rma = pd.Series(np.nan, index=x.index)
    first = sma.first_valid_index()
    if first is None:
        return rma
    rma.loc[first] = sma.loc[first]
    for i in range(x.index.get_loc(first) + 1, len(x)):
        rma.iloc[i] = alpha * x.iloc[i] + (1 - alpha) * rma.iloc[i - 1]
    return rma

def tv_rsi(close: pd.Series, length: int = 14) -> pd.Series:
    c = pd.to_numeric(close, errors="coerce")
    ch = c.diff()
    gain = ch.clip(lower=0)
    loss = (-ch).clip(lower=0)
    avg_gain = tv_rma(gain, length)
    avg_loss = tv_rma(loss, length)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where(avg_gain != 0, 0.0)
    return rsi

def tv_rsi_with_last_price(hist_close: pd.Series, last_price: float, length: int = 14) -> float:
    adj = hist_close.copy()
    if last_price is not None and np.isfinite(last_price):
        adj.iloc[-1] = float(last_price)
    return float(tv_rsi(adj, length).dropna().iloc[-1])

def compute_rsi(close_series, period=RSI_PERIOD):
    delta = close_series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def rsi_tradingview(close: pd.Series, length: int = 14) -> pd.Series:
    close = pd.to_numeric(close, errors="coerce").copy()
    change = close.diff()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    close = pd.to_numeric(close, errors="coerce")
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_rsi_cutler(close, period=14):
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.rolling(window=period, min_periods=1).mean()
    avg_loss = down.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_rsi_progressive(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = -delta.clip(upper=0).fillna(0)
    exp_gain = gain.expanding(min_periods=1).mean()
    exp_loss = loss.expanding(min_periods=1).mean()
    avg_gain = exp_gain.copy()
    avg_loss = exp_loss.copy()
    if len(gain) >= period:
        avg_gain.iloc[period-1] = gain.iloc[:period].mean()
        avg_loss.iloc[period-1] = loss.iloc[:period].mean()
    for i in range(period, len(gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def floor_to_frame(dt, minutes):
    discard = (dt.minute % minutes) * 60 + dt.second
    return dt - timedelta(seconds=discard, microseconds=dt.microsecond)

def build_last_nd_window_ist(days: int, frame_minutes: int):
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)
    from_base = now_ist - timedelta(days=days)
    from_dt = from_base.replace(hour=9, minute=15, second=0, microsecond=0)
    to_dt = floor_to_frame(now_ist, frame_minutes)
    from_encoded = quote(from_dt.strftime("%Y-%m-%d %H:%M:%S"))
    to_encoded = quote(to_dt.strftime("%Y-%m-%d %H:%M:%S"))
    return from_encoded, to_encoded

ist = pytz.timezone("Asia/Kolkata")

def is_market_open_now_ist() -> bool:
    # 1. 24/7 Paper Trading Override
    if SETTINGS_AVAILABLE:
        try:
            sm = SettingsManager()
            sm.load()
            if sm.get("app_settings", {}).get("paper_trading_mode", False):
                return True
        except: pass

    now = datetime.now(ist)
    if now.weekday() >= 5:
        return False
    start = dtime(9, 15)
    end = dtime(15, 30)
    return start <= now.time() <= end

def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    return True

def next_market_open_dt_ist(from_dt: Optional[datetime] = None) -> datetime:
    now = from_dt.astimezone(ist) if from_dt else datetime.now(ist)
    target_day = now.date()
    if is_trading_day(target_day) and now.time() < OPEN_T:
        target = datetime.combine(target_day, OPEN_T, ist)
        return target
    d = target_day
    while True:
        d += timedelta(days=1)
        if is_trading_day(d):
            return datetime.combine(d, OPEN_T, ist)

OPEN_T = dtime(9, 15)
CLOSE_T = dtime(15, 30)

def wait_for_market_open():
    global LOG_SUPPRESS
    LOG_SUPPRESS = True
    try:
        while not is_market_open_now_ist():
            if STOP_REQUESTED:
                log_ok("⏹ Cycle stopped by user during market wait.", force=True)
                return
            target = next_market_open_dt_ist()
            now = now_ist()
            remaining = int((target - now).total_seconds())
            if remaining <= 0 or is_market_open_now_ist():
                break
            hh, rem = divmod(remaining, 3600)
            mm, ss = divmod(rem, 60)
            log_ok(
                f"\n⏸️ Market closed — next open {target.strftime('%d-%b %H:%M IST')} | waiting {hh:02d}:{mm:02d}:{ss:02d}",
                end="",
                flush=True,
                force=True,
            )
            time.sleep(1)
        log_ok("\n🟢 Market open — resuming", flush=True, force=True)
    finally:
        LOG_SUPPRESS = False

def safe_place_order_when_open(symbol, exchange, qty, side, instrument_token, price=0, use_amo=False):
    if not is_market_open_now_ist():
        log_ok(f"⏸️ Market closed: skip {side} {symbol}")
        return False
        
    # print(f"{symbol}, {exchange}, {qty}, {side}")
    # print(check_existing_orders(symbol, exchange, qty, side))
    
    if check_existing_orders(symbol, exchange, qty, side):
        log_ok(f"⏸️ Skipping {side} order for {symbol}:{exchange} (Qty: {qty}) due to existing order")
        return False
    log_ok(f"Placing order : Symbol : {symbol}, Exchange : {exchange}, Quantity : {qty}, Side : {side}.")
    
    # Execute order placement
    order_success = place_order(symbol, exchange, qty, side, instrument_token, price=0, use_amo=use_amo)
    
    # ---------------- Trade Logging (Phase 0A) ----------------
    if order_success and db:
        try:
            # Get current price from market data
            market_data, _ = fetch_market_data_once(symbol, exchange)
            current_price = float(market_data.get("last_price", price)) if market_data else price
            
            # Calculate gross amount
            gross_amount = current_price * qty
            
            # Calculate fees (mStock fee structure for CNC delivery)
            brokerage = max(20, gross_amount * 0.0003)  # 0.03% or ₹20, whichever is higher
            stt = gross_amount * 0.001 if side.upper() == "SELL" else 0  # 0.1% on sell only
            exchange_fee = gross_amount * 0.0000345  # ~0.00345%
            gst = brokerage * 0.18  # 18% on brokerage
            sebi = gross_amount * 0.000001  # ₹10 per crore
            stamp = gross_amount * 0.00015 if side.upper() == "BUY" else 0  # 0.015% on buy only
            
            total_fees = brokerage + stt + exchange_fee + gst + sebi + stamp
            
            # Calculate net amount
            if side.upper() == "BUY":
                net_amount = gross_amount + total_fees  # Cost = price + fees
            else:  # SELL
                net_amount = gross_amount - total_fees  # Proceeds = price - fees
            
            fee_breakdown = {
                "brokerage": round(brokerage, 2),
                "stt": round(stt, 2),
                "exchange_charges": round(exchange_fee, 2),
                "gst": round(gst, 2),
                "sebi_charges": round(sebi, 2),
                "stamp_duty": round(stamp, 2)
            }
            
            # Log trade to database
            trade_id = db.insert_trade(
                symbol=symbol,
                exchange=exchange,
                action=side.upper(),
                quantity=qty,
                price=round(current_price, 2),
                gross_amount=round(gross_amount, 2),
                total_fees=round(total_fees, 2),
                net_amount=round(net_amount, 2),
                strategy="RSI",
                reason=f"RSI-based {side.upper()}",
                broker="mstock",
                fee_breakdown=fee_breakdown
            )
            log_ok(f"📝 Trade logged to database (ID: {trade_id})")
            
            # Send notification
            if notifier:
                try:
                    trade_info = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "action": side.upper(),
                        "quantity": qty,
                        "price": round(current_price, 2),
                        "gross_amount": round(gross_amount, 2),
                        "total_fees": round(total_fees, 2),
                        "net_amount": round(net_amount, 2),
                        "strategy": "RSI",
                        "reason": f"RSI-based {side.upper()}",
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    notifier.send_trade_alert(trade_info)
                except Exception as ne:
                    log_ok(f"⚠️ Notification failed: {ne}")
        except Exception as e:
            log_ok(f"⚠️ Trade logging failed: {e}", force=True)
            # Don't fail the order if logging fails
    
    return order_success

    # return False

# ---------------- Market Data ----------------

def fetch_historical_data(symbol, exchange, tf, instrument_token):
    if is_offline():
        return None

    def attempt_fetch():
        try:
            timeframe_map = {
                "1T": "1minute",
                "3T": "3minute",
                "5T": "5minute",
                "10T": "10minute",
                "15T": "15minute",
                "30T": "30minute",
                "1H": "60minute",
                "1D": "day"
            }
            api_timeframe = timeframe_map.get(tf, tf)
            frame_minutes = (
                1 if api_timeframe == "1minute" else
                3 if api_timeframe == "3minute" else
                5 if api_timeframe == "5minute" else
                10 if api_timeframe == "10minute" else
                15 if api_timeframe == "15minute" else
                30 if api_timeframe == "30minute" else
                60 if api_timeframe == "60minute" else
                None
            )
            if api_timeframe == "day":
                from_encoded, to_encoded = build_last_nd_window_ist(days=10, frame_minutes=60)
            else:
                from_encoded, to_encoded = build_last_nd_window_ist(days=10, frame_minutes=frame_minutes or 60)

            url = (
                f"https://api.mstock.trade/openapi/typea/instruments/historical/"
                f"{exchange.upper()}/{instrument_token}/{api_timeframe}"
                f"?from={from_encoded}&to={to_encoded}"
            )
            headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
            resp = safe_request("GET", url, headers=headers)
            if resp is None:
                return None
            if resp.status_code != 200:
                log_ok(f"❌ Historical data error for {symbol}: {resp.status_code} - {resp.text}")
                if "TokenException" in resp.text:
                    if handle_token_exception_and_refresh_token():
                        return attempt_fetch()
                    else:
                        if not is_offline():
                            log_ok("Failed to refresh mstock token, cannot fetch historical data.")
                        return None
                return None

            response_data = resp.json() or {}
            candles = (response_data.get("data") or {}).get("candles", [])
            if response_data.get("status") != "success" or not candles:
                log_ok(f"⚠️ No data returned for {symbol}: {response_data.get('message', 'No candles')}")
                return None

            cols = ["timestamp", "open", "high", "low", "close", "volume"]
            df = pd.DataFrame(candles, columns=cols)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Asia/Kolkata")
            df.set_index("timestamp", inplace=True)
            if api_timeframe != "day":
                df = df.between_time("09:15", "15:30")
            return df[["open", "high", "low", "close"]]
        except Exception as e:
            if not is_offline():
                log_ok(f"❌ Error fetching data for {symbol}: {e}")
            return None

    try:
        return attempt_fetch()
    except Exception as e:
        if "TokenException" in str(e):
            if handle_token_exception_and_refresh_token():
                return attempt_fetch()
            else:
                if not is_offline():
                    log_ok("Failed to refresh mstock token, cannot fetch historical data.")
                return None
        else:
            raise


# ---------------- Strategy ----------------

def check_existing_orders(symbol: str, exchange: str, qty: int, side: str) -> bool:
    if is_offline():
        return False
    url = "https://api.mstock.trade/openapi/typea/orders"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    response = safe_request("GET", url, headers=headers)
    if response is None or response.status_code != 200:
        return False
    orders = (response.json() or {}).get("data", []) or []
    
    # Define blocking statuses
    blocking = {"OPEN", "PENDING", "TRIGGERED", "TRADED"}
    
    # Track existence and quantities of buy and sell orders
    has_buy = False
    has_sell = False
    total_buy_qty = 0
    total_sell_qty = 0
    for o in orders:
        if (
            o.get("tradingsymbol") == symbol and
            (o.get("exchange") or o.get("exchangeSegment") or "NSE") == exchange
        ):
            transaction_type = (o.get("transaction_type") or "").upper()
            status = (o.get("status") or "").upper()
            order_qty = o.get("quantity", 0) if isinstance(o.get("quantity"), (int, float)) else 0
            if transaction_type == "BUY" and status in blocking:
                has_buy = True
                total_buy_qty += order_qty
            elif transaction_type == "SELL" and status in blocking:
                has_sell = True
                total_sell_qty += order_qty
    
    # If both buy and sell orders exist, allow buy orders only if total quantities match
    if side.upper() == "BUY" and has_buy and has_sell:
        return total_buy_qty != total_sell_qty
    
    # Check for blocking orders of the same side
    for o in orders:
        if (
            o.get("tradingsymbol") == symbol and
            (o.get("exchange") or o.get("exchangeSegment") or "NSE") == exchange and
            (o.get("transaction_type") or "").upper() == side.upper() and
            (o.get("status") or "").upper() in blocking
        ):
            return True
    return False
    
def process_market_data(symbol, exchange, market_data, tf, instrument_token):
    if SYMBOL_LOCKS.get(symbol, False):
        return
    SYMBOL_LOCKS[symbol] = True
    try:
        config_key = (symbol, exchange)
        if config_key not in config_dict:
            log_ok(f"⚠️ Skipped {symbol}:{exchange}: Not in config or disabled")
            return

        sym_config = config_dict[config_key]
        buy_rsi = sym_config["Buy RSI"]
        sell_rsi = sym_config["Sell RSI"]
        profit_pct = sym_config["Profit Target %"]
        config_qty = int(sym_config.get("Quantity", 0))
        strategy_type = str(sym_config.get("Strategy", "TRADE")).upper() # TRADE or INVEST
        
        # Get current price first (needed for quantity calculation)
        current_close = float(market_data.get("last_price", np.nan)) if market_data else np.nan
        if not np.isfinite(current_close):
            log_ok(f"⚠️ {symbol}:{exchange}: no valid LTP ({current_close})")
            return
        
        # Advanced Position Sizing (MVP1 Feature)
        if config_qty > 0:
            # METHOD A: Fixed quantity mode (from CSV)
            qty = config_qty
        else:
            # DYNAMIC SIZING (Methods B or C)
            if settings:
                total_capital = settings.get("capital.total_capital", 50000)
                sizing_type = settings.get("capital.max_per_stock_type", "percentage") # "percentage" or "fixed"
                
                if sizing_type == "percentage":
                    # METHOD C: Portfolio Percentage
                    per_trade_pct = settings.get("capital.max_per_stock_value", 10.0)
                    per_trade_amount = total_capital * (per_trade_pct / 100)
                else:
                    # METHOD B: Fixed Capital Amount
                    per_trade_amount = settings.get("capital.max_per_stock_fixed_amount", 5000)
                
                # Calculate quantity based on current price
                qty = int(per_trade_amount / current_close)
                
                # Ensure minimum quantity of 1 for Penny stocks
                qty = max(1, qty)
                
                # Risk Check: Max positions (handled in run_cycle but good to note)
            else:
                # Fallback if settings not available
                qty = 1
                log_ok(f"⚠️ Settings unavailable for {symbol}, using qty=1")

        timeframe_map = {
            "1T": "1m",
            "3T": "3m",
            "5T": "5m",
            "10T": "10m",
            "15T": "15m",
            "30T": "30m",
            "1H": "1h",
            "1D": "1d",
        }
        api_timeframe = timeframe_map.get(tf, tf)

        try:
            ts_str, tv_rsi_last_val, _ = calculate_intraday_rsi_tv(
                ticker=symbol,
                period=14,
                interval=api_timeframe,
                live_price=current_close,
                exchange=exchange
            )
        except Exception as e:
            log_ok(f"Error calculating RSI for {config_key}: {str(e)}")
            return

        last_rsi = float(tv_rsi_last_val)

        pos = portfolio_state.setdefault(symbol, {
            "active": False, "price": 0.0, "last_ts": None, "last_action_ts": None
        })

        live_positions_merged = safe_get_live_positions_merged()

        # Check for existing position for the specific symbol and exchange
        key_ex = (symbol, exchange)
        pos_rec = live_positions_merged.get(key_ex, {})
        available_qty = int(pos_rec.get("qty", 0)) - int(pos_rec.get("used_quantity", 0))
        has_existing_position = available_qty > 0

        # Update position for the specific symbol and exchange
        key_ex = (symbol, exchange)
        pos_rec = live_positions_merged.get(key_ex, {})
        available_qty = int(pos_rec.get("qty", 0)) - int(pos_rec.get("used_quantity", 0))
        entry_price = float(pos_rec.get("price", 0.0)) if pos_rec else 0.0
        pos["active"] = available_qty > 0
        if entry_price > 0:
            pos["price"] = entry_price
        target_price = pos["price"] * (1 + profit_pct / 100) if pos["price"] else None

        # --- SIP STRATEGY LOGIC (MVP1 Feature) ---
        if strategy_type == "SIP":
            if sip_engine:
                last_buy_price = pos.get("price", 0)
                should_buy, reason = sip_engine.should_buy(current_close, last_buy_price)
                
                if should_buy and is_market_open_now_ist():
                    # Check if we already bought today to avoid duplicates
                    if not check_existing_orders(symbol, exchange, qty, "BUY"):
                        log_ok(f"🎯 SIP TRIGGER: {reason} for {symbol}", force=True)
                        safe_place_order_when_open(symbol, exchange, qty, "BUY", instrument_token, 0)
                        
                        # Notify user
                        if notifier:
                            notifier.send_trade_alert({
                                'symbol': symbol, 'exchange': exchange, 'action': 'BUY',
                                'quantity': qty, 'price': current_close, 'strategy': 'SIP',
                                'reason': reason
                            })
            return # Exit SIP processing (SIP never sells via RSI)

        if pos["active"] and pos["price"] > 0:
            can_consider_sell = current_close > pos["price"]

            # --- SELL LOGIC ---
            should_sell = False
            sell_reason = ""

            # Check Profit Target (Available in both TRADE and INVEST)
            if target_price and current_close >= target_price:
                should_sell = True
                sell_reason = f"Profit Target Hit ({profit_pct}%)"

            # Check RSI Sell (Only for TRADE strategy)
            elif strategy_type == "TRADE":
                if last_rsi >= sell_rsi and can_consider_sell:
                    should_sell = True
                    sell_reason = f"RSI Sell Signal ({last_rsi:.1f} >= {sell_rsi})"

            # Accumulation Mode (INVEST): We SKIP RSI-based selling
            elif strategy_type == "INVEST":
                if last_rsi >= sell_rsi:
                     log_ok(f"💎 INVEST MODE: Ignoring Sell Signal for {symbol} (RSI {last_rsi:.1f}). HODLing.")

            if should_sell and is_market_open_now_ist():
                sell_qty = max(0, min(qty, available_qty))
                if sell_qty > 0:
                    pos["last_action_ts"] = current_close
                    log_ok(f"⏳ Attempting sell for {symbol}: {sell_reason}")
                    safe_place_order_when_open(symbol, exchange, sell_qty, "SELL", instrument_token, 0)
                return

        if has_existing_position:
            log_ok(f"⚠️ Skipped {symbol}:{exchange}: Existing position detected")
            return

        if last_rsi <= buy_rsi and is_market_open_now_ist() and not check_existing_orders(symbol, exchange, qty, "BUY"):
            need_qty = qty - max(0, available_qty)
            if need_qty > 0:
                log_ok(f"⏳ Attempting buy entry/top-up for {symbol}: RSI={last_rsi:.2f}")
                safe_place_order_when_open(symbol, exchange, need_qty, "BUY", instrument_token, 0)
    finally:
        SYMBOL_LOCKS[symbol] = False

# ---------------- Connectivity Monitor ----------------

ONLINE_CHECK_URL = "https://www.google.com/"  # lightweight

def is_system_online() -> bool:
    try:
        resp = requests.head(ONLINE_CHECK_URL, timeout=5)
        return 200 <= resp.status_code < 500
    except RequestException:
        try:
            resp = requests.get(ONLINE_CHECK_URL, timeout=5)
            return 200 <= resp.status_code < 500
        except RequestException:
            return False

def connectivity_monitor():
    offline = False
    offline_start = None
    while True:
        ok = is_system_online()
        if ok:
            if offline:
                downtime = now_ist() - offline_start
                secs = int(downtime.total_seconds())
                mins, rem = divmod(secs, 60)
                log_ok(f"🟢 Online again after {mins}m {rem}s downtime")
            offline = False
            OFFLINE["active"] = False
            OFFLINE["since"] = None
            run_cycle()
        else:
            if not offline:
                offline = True
                offline_start = now_ist()
                OFFLINE["active"] = True
                OFFLINE["since"] = offline_start
                log_ok("🔴 Offline detected — pausing trading loop and monitoring connectivity")
            time.sleep(5)

# ---------------- Orders ----------------

def place_order(symbol, exchange, qty, side, instrument_token, price=0, use_amo=False):
    if is_offline():
        return False

    # Check Paper Trading Mode
    if settings and settings.get("app_settings.paper_trading_mode"):
        log_ok(f"🧪 PAPER TRADE: {side} {symbol} Qty: {qty} @ {price or 'MKT'}")

        # Log to database as a paper trade
        if db:
            try:
                # Estimate price if MKT (use last close if available, else 0)
                estimated_price = price
                if estimated_price == 0:
                    market_data, _ = fetch_market_data_once(symbol, exchange)
                    estimated_price = float(market_data.get("last_price", 0)) if market_data else 0

                gross_amount = estimated_price * qty

                # Zero fees for paper trading simulation (or could simulate them)
                total_fees = 0
                net_amount = gross_amount if side.upper() == "BUY" else gross_amount

                db.insert_trade(
                    symbol=symbol,
                    exchange=exchange,
                    action=side.upper(),
                    quantity=qty,
                    price=estimated_price,
                    gross_amount=gross_amount,
                    total_fees=total_fees,
                    net_amount=net_amount,
                    strategy="RSI (Paper)",
                    reason=f"Paper Trade {side.upper()}",
                    broker="PAPER"
                )
                log_ok("✅ Paper trade logged to DB")
                return True
            except Exception as e:
                log_ok(f"❌ Failed to log paper trade: {e}")
                return False
        return True

    def attempt_place_order():
        variety = "regular"
        url = f"https://api.mstock.trade/openapi/typea/orders/{variety}"
        data = {
            'tradingsymbol': symbol,
            'exchange': exchange,
            'transaction_type': side.upper(),
            'order_type': 'MARKET' if price == 0 else 'LIMIT',
            'quantity': str(qty),
            'product': 'CNC',
            'validity': 'DAY',
            'price': str(price),
            'symboltoken': instrument_token
        }
        headers = {
            'X-Mirae-Version': '1',
            'Authorization': f'token {API_KEY}:{ACCESS_TOKEN}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        encoded_payload = urlencode(data)
        response = safe_request("POST", url, headers=headers, data=encoded_payload)
        if response is None:
            return False

        try:
            resp_json = response.json() or []
            if isinstance(resp_json, list) and len(resp_json) > 0:
                resp_dict = resp_json[0]
            else:
                resp_dict = resp_json

            status = resp_dict.get("status")
            message = resp_dict.get("message")
            if response.status_code == 200 and status == "success":
                log_ok(f"✅ {side} order placed for {symbol} (Qty: {qty})")
                return True
            else:
                log_ok(f"❌ Order failed for {symbol}: {message or response.text}")
                if message and "TokenException" in message:
                    raise Exception("TokenException")
                return False
        except Exception as e:
            log_ok(f"❌ Response parsing error: {e} - Raw: {response.text}")
            return False

    try:
        return attempt_place_order()
    except Exception as e:
        error_str = str(e)
        if "TokenException" in error_str or "invalid session" in error_str:
            if handle_token_exception_and_refresh_token():
                return attempt_place_order()
            else:
                log_ok("Failed to refresh token, order placement aborted.")
                return False
        else:
            raise

# ---------------- Runner ----------------

def run_cycle():
    if is_offline():
        return
    if not is_market_open_now_ist():
        wait_for_market_open()
    
    # ---------------- Risk Manager Checks (Phase 0A) ----------------
    if risk_mgr and db:
        try:
            # Check all positions for risk triggers before trading
            actions = risk_mgr.check_all_positions()
            
            # Execute risk-triggered actions
            for action in actions:
                symbol = action['symbol']
                exchange = action['exchange']
                qty = action['quantity']
                reason = action['reason']
                
                log_ok(f"🚨 RISK TRIGGER: {reason}", force=True)
                
                # Get instrument token for sell order
                market_data, _ = fetch_market_data_once(symbol, exchange)
                instrument_token = market_data.get("instrument_token") if market_data else None
                
                if instrument_token:
                    # Trigger sell order
                    safe_place_order_when_open(
                        symbol, exchange, qty, "SELL", 
                        instrument_token, price=0, use_amo=False
                    )

                    # 🔔 Notify user (MVP1 Feature)
                    if notifier:
                        try:
                            # Create a display-friendly position dict for the notifier
                            notif_data = {
                                'symbol': symbol,
                                'exchange': exchange,
                                'action': 'SELL',
                                'quantity': qty,
                                'reason': reason,
                                # Passing extra info if available from RiskManager action
                                'profit_amount': action.get('pnl_amount', 0),
                                'profit_pct': action.get('pnl_pct', 0),
                                'current_price': action.get('current_price', 0)
                            }
                            
                            if "Stop Loss" in reason:
                                notifier.send_stop_loss_alert(notif_data)
                            elif "Profit Target" in reason:
                                notifier.send_profit_target_alert(notif_data)
                            else:
                                # Fallback or circuit breaker
                                notifier.send_circuit_breaker_alert(notif_data)
                                
                            log_ok(f"📲 Risk alert sent for {symbol}: {reason}")
                        except Exception as e:
                            log_ok(f"⚠️ Failed to send risk alert: {e}")
                else:
                    log_ok(f"⚠️ Cannot execute risk-triggered sell: no instrument token for {symbol}", force=True)
        except Exception as e:
            log_ok(f"⚠️ Risk check failed: {e}", force=True)
    
    reset_cycle_quotes()
    log_ok(f"---------------------------------------------------------------------------------------------------------------{datetime.now()}")
    processed = set()
    nifty_only = settings.get("app_settings.nifty_50_only", False) if settings else False

    for symbol, ex in SYMBOLS_TO_TRACK:
        key = (symbol, ex)
        if key in processed:
            continue
        processed.add(key)

        # Nifty 50 Filter Check
        if nifty_only and symbol not in NIFTY_50:
            # We log this once per cycle to avoid spam, or check if we should even track it
            # For now, just skip silently or with verbose log
            # log_ok(f"🚫 Skipping {symbol}: Not in Nifty 50")
            continue

        try:
            tf = config_dict.get((symbol, ex), {}).get("Timeframe", "15T")
            market_data, _ = fetch_market_data_once(symbol, ex)
            instrument_token = market_data["instrument_token"] if market_data else None
            if not instrument_token:
                log_ok(f"⚠️ No instrument token for {symbol}:{ex}")
                continue
            if is_offline():
                return
            process_market_data(symbol, ex, market_data, tf, instrument_token)
        except Exception as e:
            if not is_offline():
                log_ok(f"❌ Cycle error for {symbol}:{ex}: {e}")
    
    # ---------------- Save State (Phase 0A) ----------------
    save_state_snapshot()

def save_state_snapshot():
    """Save current bot state for crash recovery"""
    if state_mgr and db:
        try:
            positions = safe_get_live_positions_merged()
            perf = db.get_performance_summary()
            
            # Update state components
            state_mgr.state['positions'] = positions
            state_mgr.update_portfolio_value(perf.get('total_net_pnl', 0))
            # circuit breaker is auto-saved in setter, so we might just sync it if needed, or rely on existing state
            state_mgr.state['total_trades_today'] = perf.get('total_trades', 0)
            state_mgr.save()
        except Exception as e:
            log_ok(f"⚠️ State save failed: {e}")

def main_loop():
    # ---------------- Auto-Login (Phase 3) ----------------
    if perform_auto_login():
        pass
    
    # ---------------- Load State (Phase 0A) ----------------
    if state_mgr:
        try:
            state = state_mgr.load()
            if state and state.get('circuit_breaker_active'):
                log_ok("🛑 Circuit breaker is ACTIVE. Bot will not trade.", force=True)
                log_ok(f"ℹ️ Previous state: {state.get('total_trades', 0)} trades, Portfolio Value: ₹{state.get('portfolio_value', 0):.2f}", force=True)
                return
        except Exception as e:
            log_ok(f"⚠️ State load failed: {e}", force=True)
    
    log_ok("🕒 Scheduler started (continuous)", force=True)
    if is_system_online():
        log_ok("🟢 Status: Online", force=True)
    # while True:
        # run_cycle()  # Run cycles back-to-back
        
    run_cycle()


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log_ok("🛑 Program terminated by user")
        sys.exit(0)