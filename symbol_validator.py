import yfinance as yf
import pandas as pd
import logging

def validate_symbol(symbol: str, exchange: str) -> bool:
    """
    Validate if a symbol exists on NSE/BSE using yfinance
    NSE symbols should end with .NS
    BSE symbols should end with .BO
    """
    suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
    yf_symbol = f"{symbol}{suffix}"
    
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # Try to get historical data (more reliable than fast_info)
        hist = ticker.history(period="5d")
        
        # Symbol is valid if we got some historical data
        if hist is not None and not hist.empty and len(hist) > 0:
            return True
            
        # Fallback: Try fast_info method
        try:
            info = ticker.fast_info
            # Check if we have a valid last price (not None, not 0)
            if hasattr(info, 'last_price'):
                last_price = getattr(info, 'last_price', None)
                if last_price and last_price > 0:
                    return True
        except Exception:
            pass  # fast_info failed, rely on history check
            
        # No valid data found
        logging.warning(f"Symbol {yf_symbol} exists but has no trading data")
        return False
        
    except Exception as e:
        logging.error(f"Error validating {yf_symbol}: {e}")
        return False

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
