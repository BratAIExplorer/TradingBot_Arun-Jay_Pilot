import yfinance as yf
import pandas as pd
import logging
import time
from typing import Tuple

def validate_symbol(symbol: str, exchange: str, retries: int = 2) -> Tuple[bool, str]:
    """
    Validate if a symbol exists on NSE/BSE using yfinance with retry logic
    and smart exchange auto-detection
    
    Args:
        symbol: Stock symbol (e.g., 'TATASTEEL')
        exchange: Exchange name ('NSE' or 'BSE')
        retries: Number of retry attempts (default: 2)
    
    Returns:
        Tuple of (is_valid: bool, message: str)
        - is_valid: True if symbol exists and has data
        - message: Status message with exchange suggestions
    """
    # Determine both exchanges to try
    primary_exchange = exchange.upper()
    primary_suffix = ".NS" if primary_exchange == "NSE" else ".BO"
    
    # Alternate exchange for fallback
    alternate_exchange = "BSE" if primary_exchange == "NSE" else "NSE"
    alternate_suffix = ".BO" if alternate_exchange == "BSE" else ".NS"
    
    # Try primary exchange first
    result, message = _try_validate_symbol(symbol, primary_suffix, primary_exchange, retries)
    
    if result:
        return (True, "Valid")
    
    # If primary failed, try alternate exchange (smart auto-detection!)
    alt_result, alt_message = _try_validate_symbol(symbol, alternate_suffix, alternate_exchange, retries)
    
    if alt_result:
        # Found on alternate exchange - suggest correction
        return (True, f"✓ Found on {alternate_exchange} (not {primary_exchange}). Update exchange?")
    
    # Not found on either exchange - return original error
    return (False, message)


def _try_validate_symbol(symbol: str, suffix: str, exchange_name: str, retries: int) -> Tuple[bool, str]:
    """
    Internal helper to try validating a symbol with specific suffix
    
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    yf_symbol = f"{symbol}{suffix}"
    
    # Try validation with retries
    for attempt in range(retries + 1):
        try:
            ticker = yf.Ticker(yf_symbol)
            
            # Set timeout for history call (10 seconds)
            hist = ticker.history(period="1d", timeout=10)
            
            if not hist.empty:
                return (True, "Valid")
            else:
                # Symbol found but no data (might be delisted or weekend)
                return (False, f"No data available (possibly delisted or market closed)")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check specific error types
            if "expecting value" in error_msg or "json" in error_msg:
                # Yahoo Finance API error - retry
                if attempt < retries:
                    time.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    return (False, f"Yahoo Finance API unavailable")
            
            elif "timeout" in error_msg:
                return (False, f"Timeout - check internet")
            
            elif "404" in error_msg or "not found" in error_msg:
                return (False, f"Symbol not found on {exchange_name}")
            
            else:
                # Unknown error
                return (False, f"Error: {str(e)[:40]}")
    
    # Should not reach here, but just in case
    return (False, "Validation failed after retries")


def validate_csv_symbols(csv_path: str) -> dict:
    """
    Validate all symbols in the config CSV
    Returns a dict mapping (symbol, exchange) to (is_valid, message) tuple
    """
    results = {}
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            sym = row['Symbol']
            ex = row['Exchange']
            is_valid, message = validate_symbol(sym, ex)
            results[(sym, ex)] = (is_valid, message)
    except Exception as e:
        logging.error(f"Error reading CSV for validation: {e}")
    
    return results
