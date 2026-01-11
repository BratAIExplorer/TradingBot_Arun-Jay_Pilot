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
        info = ticker.fast_info
        # If we can get a price, it's valid
        if info and 'last_price' in info:
             return True
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
