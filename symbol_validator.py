import yfinance as yf
import pandas as pd
import logging
import numpy as np
import requests

from utils import get_yfinance_session, yf_rate_limit

def validate_symbol(symbol: str, exchange: str) -> bool:
    """
    Validate if a symbol exists on NSE/BSE using yfinance
    NSE symbols should end with .NS
    BSE symbols should end with .BO
    """
    # If it's an index (starts with ^), don't add suffix
    if symbol.startswith("^"):
        yf_symbol = symbol
    else:
        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        yf_symbol = f"{symbol}{suffix}"
    
    try:
        yf_rate_limit(0.3)
        session = get_yfinance_session()
        ticker = yf.Ticker(yf_symbol, session=session)
        # info = ticker.fast_info
        
        # Method 2: History (More robust than fast_info for validation)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return True
            
        # If history empty, try fast info
        info = ticker.fast_info
        if info and 'last_price' in info and np.isfinite(info['last_price']):
             return True
             
    except Exception as e:
        logging.error(f"yfinance validation failed for {yf_symbol}: {e}")

    # Method 3: Direct API Fallback
    try:
        price = _fetch_yahoo_direct(yf_symbol)
        if price is not None and price > 0:
            return True
    except Exception as e:
        logging.error(f"Direct validation fallback failed: {e}")
        
    return False

def get_symbol_price(symbol: str, exchange: str) -> float:
    """
    Get live price for validaton using yfinance (Fallback)
    Returns None if failed
    """
    # If it's an index (starts with ^), don't add suffix
    if symbol.startswith("^"):
        yf_symbol = symbol
    else:
        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        yf_symbol = f"{symbol}{suffix}"
    
    try:
        yf_rate_limit(0.3)
        session = get_yfinance_session()
        ticker = yf.Ticker(yf_symbol, session=session)
        
        # Method 1: Fast Info
        info = ticker.fast_info
        if info and 'last_price' in info and np.isfinite(info['last_price']):
             return float(info['last_price'])
             
        # Method 2: History
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
            
    except Exception as e:
        logging.error(f"yfinance failed for {yf_symbol}: {e}. Trying direct fallback...")
    
    # Method 3: Direct API Fallback
    try:
        return _fetch_yahoo_direct(yf_symbol)
    except Exception as e:
        logging.error(f"Direct fallback failed for {yf_symbol}: {e}")
        return None

def _fetch_yahoo_direct(yf_symbol):
    """
    Manual fallback using requests to bypass yfinance library issues.
    """
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yf_symbol}?range=1d&interval=1d"
    
    # Use reliable headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://finance.yahoo.com/",
        "Connection": "keep-alive"
    }
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        return None
        
    data = resp.json()
    
    # Parse generic yahoo chart response
    try:
        result = data['chart']['result'][0]
        meta = result['meta']
        price = meta.get('regularMarketPrice')
        if price and np.isfinite(price):
            return float(price)
            
        # fallback to close price
        quote = result['indicators']['quote'][0]
        closes = quote.get('close', [])
        if closes:
            # Get last non-none value
            valid_closes = [c for c in closes if c is not None]
            if valid_closes:
                return float(valid_closes[-1])
    except:
        pass
        
    return None

def validate_csv_symbols(csv_path: str) -> dict:
    """
    Validate all symbols in the config CSV
    Returns a dict mapping (symbol, exchange) to validation status
    """
    results = {}
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            sym = row['Symbol']
            ex = row['Exchange']
            is_valid = validate_symbol(sym, ex)
            results[(sym, ex)] = is_valid
    except Exception as e:
        logging.error(f"Error reading CSV for validation: {e}")
    
    return results
