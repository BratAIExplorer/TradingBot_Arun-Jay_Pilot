# python -m pip install requests pandas python-dotenv pytz

import requests
import hashlib
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
from requests.exceptions import Timeout, ConnectionError, RequestException

# ---------------- State & Utils ----------------

LOG_SUPPRESS = False

def log_ok(msg: str = "", *args, force: bool = False, **kwargs):
    if LOG_SUPPRESS and not force:
        return
    print(msg, *args, **kwargs)

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

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
CLIENT_CODE = os.getenv('CLIENT_CODE')
PASSWORD = os.getenv('PASSWORD')

if not all([API_KEY, API_SECRET, CLIENT_CODE, PASSWORD]):
    log_ok("❌ Missing required environment variables from .env file.")
    sys.exit(1)

EXCHANGES = ["NSE", "BSE"]
portfolio_state = {}
RSI_PERIOD = 14

try:
    with open("credentials.json", "r") as f:
        creds = json.load(f)
except FileNotFoundError:
    creds = {}

ACCESS_TOKEN = creds.get("mstock", {}).get("access_token")

def handle_token_exception_and_refresh_token():
    global ACCESS_TOKEN
    log_ok("⚠️ TokenException detected, refreshing token...")
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
        creds["mstock"] = {"access_token": ACCESS_TOKEN}
        with open("credentials.json", "w") as f:
            json.dump(creds, f, indent=2)
        log_ok("✅ Access token refreshed and saved.")
        return True
    except Exception as e:
        log_ok(f"❌ Exception in token refresh: {e}")
        return False

if not ACCESS_TOKEN:
    if not handle_token_exception_and_refresh_token():
        sys.exit(1)

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
    
    merged = {}
    for sym, pos in holdings.items():
        merged[(sym, pos.get("exchange", "NSE"))] = {
            "qty": int(pos.get("qty", 0)),
            "used_quantity": int(pos.get("used_quantity", 0)),
            "price": float(pos.get("price", 0.0)),
            "ltp": float(pos.get("ltp", 0.0)),
            "pnl": float(pos.get("pnl", 0.0)),
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
        if key not in merged and n["net_qty"] != 0:
            wap_buy = (n["wap_buy_num"] / n["gross_buy_qty"]) if n["gross_buy_qty"] > 0 else 0.0
            merged[key] = {
                "qty": n["net_qty"],
                "used_quantity": 0,
                "price": wap_buy,
                "ltp": 0.0,
                "pnl": 0.0
            }
        elif key in merged:
            merged[key]["qty"] += n["net_qty"]
            if merged[key]["qty"] < 0:
                merged[key]["qty"] = 0
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

def next_market_open_dt_ist(from_dt: datetime | None = None) -> datetime:
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
    return place_order(symbol, exchange, qty, side, instrument_token, price=0, use_amo=use_amo)
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

def fetch_market_data(symbol, exchange):
    if is_offline():
        return None, None
    url = "https://api.mstock.trade/openapi/typea/instruments/quote/ohlc"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    params = {"i": f"{exchange}:{symbol.upper()}"}
    # log_fetch(f"{exchange}:{symbol}")
    try:
        response = safe_request("GET", url, headers=headers, params=params)
        if response is None:
            return None, None
        if response.status_code != 200:
            log_ok(f"❌ API error {response.status_code}: {response.text}")
            return None, None
        data = response.json() or {}
        result = (data.get("data") or {}).get(params["i"])
        if result:
            return result, exchange
        return None, None
    except Exception as e:
        if not is_offline():
            log_ok(f"❌ Exception during market data fetch: {e}")
        return None, None

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
        qty = sym_config["Quantity"]

        current_close = float(market_data.get("last_price", np.nan)) if market_data else np.nan
        if not np.isfinite(current_close):
            log_ok(f"⚠️ {symbol}:{exchange}: no valid LTP ({current_close})")
            return

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

        if pos["active"] and pos["price"] > 0:
            can_consider_sell = current_close > pos["price"]
            should_sell = (last_rsi >= sell_rsi and can_consider_sell) or (target_price and current_close > pos["price"] and current_close >= target_price)
            if should_sell and is_market_open_now_ist():
                sell_qty = max(0, min(qty, available_qty))
                if sell_qty > 0:
                    pos["last_action_ts"] = current_close
                    log_ok(f"⏳ Attempting sell for {symbol}: RSI={last_rsi:.2f}")
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
    reset_cycle_quotes()
    log_ok(f"---------------------------------------------------------------------------------------------------------------{datetime.now()}")
    processed = set()
    for symbol, ex in SYMBOLS_TO_TRACK:
        key = (symbol, ex)
        if key in processed:
            continue
        processed.add(key)
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

def main_loop():
    log_ok("🕒 Scheduler started (continuous)")
    if is_system_online():
        log_ok("🟢 Status: Online")
    # while True:
        # run_cycle()  # Run cycles back-to-back
        
    run_cycle()

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log_ok("🛑 Program terminated by user")
        sys.exit(0)