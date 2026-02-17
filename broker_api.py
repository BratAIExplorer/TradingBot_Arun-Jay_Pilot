import requests
import logging
import time
from urllib.parse import urlencode

class BrokerAPI:
    """
    Handles direct communication with mStock (Mirae Asset) API.
    Responsible for: Authentication, Requests, Retry Logic, and Response Parsing.
    """
    BASE_URL = "https://api.mstock.trade/openapi/typea"

    def __init__(self, api_key, access_token, client_code=None, logger=None, login_callback=None):
        self.api_key = api_key
        self.access_token = access_token
        self.client_code = client_code
        self.logger = logger or logging.getLogger(__name__)
        self.login_callback = login_callback
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        self.session.headers.update({
            'Authorization': f'token {self.api_key}:{self.access_token}',
            'X-Mirae-Version': '1',
            'Content-Type': 'application/json',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def set_tokens(self, api_key, access_token):
        """Update tokens dynamically (e.g. after refresh)"""
        self.api_key = api_key
        self.access_token = access_token
        self._update_headers()

    def _request(self, method, endpoint, params=None, data=None, headers=None, attempt=1):
        """Internal safe request wrapper"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            # Merge custom headers if any (e.g. for urlencoded forms)
            req_headers = self.session.headers.copy()
            if headers:
                req_headers.update(headers)

            response = self.session.request(method, url, params=params, data=data, headers=req_headers, timeout=5)
            
            # Auto-Login / Token Refresh Logic
            if response.status_code in [401, 403] and attempt < 2:
                self.logger.warning(f"⚠️ Broker API Auth Error: {response.status_code}. Attempting refresh...")
                if self.login_callback:
                    new_key, new_token = self.login_callback()
                    if new_token:
                        self.logger.info("🔄 Token refreshed via callback. Retrying request...")
                        self.set_tokens(new_key, new_token)
                        return self._request(method, endpoint, params, data, headers, attempt=attempt+1)
            
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Broker API Request Failed: {e}")
            return None

    def get_funds(self):
        """Fetch available funds"""
        # Endpoint confirmed from kickstart.py line 630
        resp = self._request("GET", "/user/fundsummary")
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                inner = data.get("data", [])
                if isinstance(inner, list) and inner:
                    return float(inner[0].get("AVAILABLE_BALANCE", 0.0))
        return 0.0

    def get_holdings(self):
        """Fetch long-term holdings (CNC)"""
        # Endpoint confirmed from kickstart.py line 1148
        resp = self._request("GET", "/portfolio/holdings")
        if resp and resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    def get_positions(self):
        """Fetch active Intraday/MIS positions"""
        # Endpoint confirmed from kickstart.py line 1272
        resp = self._request("GET", "/portfolio/positions")
        if resp and resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    def get_orders(self):
        """Fetch order book for today"""
        resp = self._request("GET", "/orders")
        if resp and resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    def get_quote(self, symbol, exchange):
        """Fetch OHLC Quote"""
        # Endpoint confirmed from kickstart.py line 523
        # https://api.mstock.trade/openapi/typea/instruments/quote/ohlc
        symbol_encoded = f"{exchange}:{symbol}"
        resp = self._request("GET", "/instruments/quote/ohlc", params={"i": symbol_encoded})
        
        if resp and resp.status_code == 200:
            data = resp.json() or {}
            # Response format: { "status": "success", "data": { "NSE:RELIANCE": { ... } } }
            inner = data.get("data", {})
            return inner.get(symbol_encoded)
        return None

    def place_order(self, symbol, exchange, side, quantity, price=0, trigger_price=0, product="CNC", validity="DAY", variety="regular", instrument_token=None):
        """Place an order"""
        endpoint = f"/orders/{variety}"
        
        payload = {
            'tradingsymbol': symbol,
            'exchange': exchange,
            'transaction_type': side.upper(),
            'order_type': 'MARKET' if price == 0 else 'LIMIT',
            'quantity': str(quantity),
            'product': product,
            'validity': validity,
            'price': str(price),
            'symboltoken': instrument_token
        }
        
        # mStock API expects Form Data (urlencoded)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        encoded_data = urlencode(payload)
        
        resp = self._request("POST", endpoint, data=encoded_data, headers=headers)
        return resp

    def get_historical_data(self, exchange, instrument_token, interval, from_date, to_date):
        """Fetch historical candles"""
        # Endpoint confirmed from kickstart.py line 1900
        # /instruments/historical/{exchange}/{token}/{interval}
        endpoint = f"/instruments/historical/{exchange}/{instrument_token}/{interval}"
        
        # Kickstart handles 'from' and 'to' as query params
        params = {'from': from_date, 'to': to_date}
        
        resp = self._request("GET", endpoint, params=params)
        if resp and resp.status_code == 200:
             return resp.json()
        return None
