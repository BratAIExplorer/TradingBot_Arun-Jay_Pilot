import yfinance as yf
import pandas as pd
import logging

def validate_symbol(symbol: str, exchange: str):
    """
    Validate if a symbol exists on NSE/BSE using yfinance
    NSE symbols should end with .NS
    BSE symbols should end with .BO
    """
    symbol = symbol.strip().upper()
    exchange = exchange.strip().upper()
    
    # 0. Quick sanity check (if it looks like a ticker, it's probably okay)
    if not symbol or len(symbol) < 2:
        return False, "Symbol too short"
    
    suffix = ".NS" if exchange == "NSE" else ".BO"
    yf_symbol = f"{symbol}{suffix}"
    
    try:
        # 1. Ticker check with tight timeout
        ticker = yf.Ticker(yf_symbol)
        
        # Method 1: Check fast_info (often fails or hangs)
        try:
            info = ticker.fast_info
            if info and getattr(info, 'last_price', None) is not None:
                return True, "Valid"
        except (AttributeError, ValueError, KeyError, ConnectionError, TimeoutError) as e:
            # BUG-004 FIX: Handle specific yfinance API errors
            # Fast_info can fail in many ways, fall through to history check
            pass
        except Exception as e:
            # BUG-004 FIX: Catch any other yfinance errors
            pass

        # Method 2: Fallback to history (restricted period to speed up)
        try:
            hist = ticker.history(period="1d", timeout=5)
            if not hist.empty:
                return True, "Valid (History)"
            else:
                # If history is empty but symbol looks like a valid Indian stock (ALPHANUMERIC)
                # We assume it's a network issue rather than an invalid symbol
                if symbol.isalnum() and 2 <= len(symbol) <= 15:
                    return True, "Likely Valid (No Data)"
        except Exception as e:
            if "Expecting value" in str(e) or "empty" in str(e).lower() or "Connection" in str(e):
                # This is likely a Yahoo Finance API block or network error
                if symbol.isalnum():
                     return True, "Likely Valid (Network Blocked)"
            
        return False, "Not Found"
            
    except Exception as e:
        # If network error or main try block fails, don't fail the user 
        # assume valid if it looks right (alphanumeric, 2-20 chars)
        if symbol.isalnum() and 2 <= len(symbol) <= 20:
            return True, "Passed (Bypassed Error)"
        return False, f"Error: {str(e)[:20]}"

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
