"""
Utilities for ARUN Trading Bot
Retry logic, decorators, and helpers
"""

import time
import logging
from functools import wraps
from typing import Callable, Any

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying failed operations with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    
    Usage:
        @retry_on_failure(max_retries=3, delay=2)
        def fetch_data():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        logging.error(f"❌ {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    logging.warning(
                        f"⚠️ {func.__name__} attempt {attempt+1}/{max_retries} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
            
            # Should never reach here
            raise last_exception
        
        return wrapper
    return decorator


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division that returns default instead of raising ZeroDivisionError
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except:
        return default


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values
    
    Usage:
        safe_get(data, 'response.data.price', default=0)
    """
    keys = key.split('.')
    value = dictionary
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def format_inr(amount: float) -> str:
    """
    Format amount as Indian Rupees
    """
    return f"₹{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format as percentage with sign
    """
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


if __name__ == "__main__":
    # Test retry logic
    attempt_count = 0
    
    @retry_on_failure(max_retries=3, delay=0.5)
    def flaky_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")
        return "Success!"
    
    result = flaky_function()
    print(f"Result: {result}")
    print(f"Took {attempt_count} attempts")


def setup_logging(log_file="bot.log", level=logging.INFO):
    """
    Configure standardized logging for the entire application.
    - Console Handler: Easy-to-read format
    - File Handler: Detailed format with rotation
    """
    import os
    from logging.handlers import RotatingFileHandler
    
    # ensure log dir exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    full_path = os.path.join(log_dir, log_file)
    
    # Create Logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
        
    # Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File Handler (10MB per file, max 5 backups)
    file_handler = RotatingFileHandler(full_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Add Handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info(f"✅ Logging initialized. Writing to {full_path}")


def get_yfinance_session():
    """
    Returns a requests.Session with headers to mimic a real browser.
    This helps avoid 403 Forbidden / 'Expecting value' errors from Yahoo Finance.
    """
    import requests
    session = requests.Session()
    # Comprehensive browser headers to avoid blocking
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://finance.yahoo.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    })
    return session

def yf_rate_limit(seconds=0.5):
    """Simple global rate limit helper for yfinance calls"""
    time.sleep(seconds)

def fetch_yahoo_history_direct(symbol, period="1d", interval="1d"):
    """
    Direct fallback for fetching Yahoo Finance history when yfinance library fails.
    Returns a pandas DataFrame compatible with yfinance.history() output.
    """
    import requests
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    # Map period/interval to range
    # range=1d, interval=1m etc.
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval={interval}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://finance.yahoo.com/",
        "Connection": "keep-alive"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return pd.DataFrame()
            
        data = resp.json()
        result = data['chart']['result'][0]
        timestamp = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        df = pd.DataFrame({
            'Open': quote.get('open', []),
            'High': quote.get('high', []),
            'Low': quote.get('low', []),
            'Close': quote.get('close', []),
            'Volume': quote.get('volume', [])
        })
        df.index = pd.to_datetime(timestamp, unit='s')
        
        return df
    except Exception as e:
        print(f"Direct History Fallback Error for {symbol}: {e}")
        return pd.DataFrame()
