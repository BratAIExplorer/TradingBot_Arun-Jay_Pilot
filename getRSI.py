# pip install yfinance pandas numpy pytz

import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import time as dtime
from typing import Optional

IST = pytz.timezone("Asia/Kolkata")

def _tv_rma(src: pd.Series, length: int) -> pd.Series:
    x = pd.to_numeric(src, errors="coerce")
    alpha = 1.0 / float(length)
    sma = x.rolling(length, min_periods=length).mean()
    rma = pd.Series(np.nan, index=x.index)
    first = sma.first_valid_index()
    if first is None:
        return rma
    rma.loc[first] = sma.loc[first]
    for i in range(x.index.get_loc(first) + 1, len(x)):
        rma.iloc[i] = alpha * x.iloc[i] + (1.0 - alpha) * rma.iloc[i - 1]
    return rma

def tv_rsi_series(close: pd.Series, length: int = 14) -> pd.Series:
    c = pd.to_numeric(close, errors="coerce")
    ch = c.diff()
    gain = ch.clip(lower=0)
    loss = (-ch).clip(lower=0)
    up = _tv_rma(gain, length)
    down = _tv_rma(loss, length)
    rs = up / down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(down != 0, 100.0)
    rsi = rsi.where(up != 0, 0.0)
    return rsi

def _filter_session(df: pd.DataFrame) -> pd.DataFrame:
    # Keep only 09:15–15:30 IST like TradingView’s NSE session
    df = df.copy()
    df = df.tz_convert(IST)
    start = dtime(9, 15)
    end = dtime(15, 30)
    return df.between_time(start_time=start, end_time=end)
    
def _filter_session_intraday(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.tz_convert(IST)
    start = dtime(9, 15)
    end = dtime(15, 30)
    return df.between_time(start_time=start, end_time=end)
    
def _is_daily_interval(interval: str) -> bool:
    return interval in {"1d", "5d"}

def calculate_intraday_rsi_tv(
    ticker: str,
    period: int = 14,
    interval: str = "15m",
    lookback: str = None,
    live_price: Optional[float] = None,
    exchange: str = "NSE"
):
    """
    Compute TradingView-exact RSI for both minute ('Xm') and daily ('Xd') intervals.
    - For intraday, filters to NSE 09:15–15:30 IST and can overwrite last bar with live_price.
    - For daily, no session filtering/overwrite, longer default lookback for correct seeding.
    - Supports different exchanges (e.g., NSE, BSE) for Yahoo Finance symbol suffix.
    Returns: (timestamp_str, last_rsi_float, df[['Close','RSI']])
    """
    # Robust check: Ensure ticker is a string; if tuple, extract the symbol
    if isinstance(ticker, tuple):
        # print(f"WARNING: ticker is a tuple {ticker}; extracting first element as symbol")
        symbol = str(ticker[0]).upper()
        # If second element is exchange, override the provided exchange
        if len(ticker) > 1 and isinstance(ticker[1], str):
            exchange = str(ticker[1]).upper()
    elif not isinstance(ticker, str):
        raise ValueError(f"Expected ticker to be a string or tuple, got {type(ticker)}: {ticker}")
    else:
        symbol = str(ticker).upper()

    # Map exchange to Yahoo Finance suffix
    exchange_suffix_map = {
        "NSE": ".NS",
        "BSE": ".BO"
    }
    suffix = exchange_suffix_map.get(exchange.upper(), ".NS")  # Default to .NS if exchange not found
    yf_symbol = f"{symbol}{suffix}" if "." not in symbol else symbol

    # Debug: Log the constructed symbol
    # print(f"DEBUG: Constructed yf_symbol={yf_symbol} from symbol={symbol}, exchange={exchange}")

    # Choose sensible defaults if lookback not provided
    if lookback is None:
        lookback = "6mo" if _is_daily_interval(interval) else "60d"  # Yahoo intraday limit ~60 days

    df = yf.Ticker(yf_symbol).history(period=lookback, interval=interval, auto_adjust=False)
    if df.empty:
        raise ValueError(f"No {interval} data for {yf_symbol}. Try a longer lookback or check hours.")

    # Ensure timezone-aware index in IST
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(IST)
    else:
        df.index = df.index.tz_convert(IST)

    if not _is_daily_interval(interval):
        # Intraday: keep regular session only (assuming NSE/BSE have same hours)
        df = _filter_session_intraday(df)
        # Optional live price overwrite on the current forming bar
        if live_price is not None and np.isfinite(live_price) and not df.empty:
            df.iloc[-1, df.columns.get_loc("Close")] = float(live_price)

    rsi = tv_rsi_series(df["Close"], length=period)
    df = df.assign(RSI=rsi)

    last_idx = df["RSI"].last_valid_index()
    if last_idx is None:
        raise ValueError("Insufficient history to seed RSI.")

    ts = last_idx.strftime("%Y-%m-%d %H:%M:%S %Z")
    return ts, float(df.loc[last_idx, "RSI"]), df[["Close", "RSI"]]

# if __name__ == "__main__":
    # # Example: Ideaforge 15m like the screenshot
    # # Optionally pass a live LTP from broker feed to match an open candle exactly
    # date, rsi, data = calculate_intraday_rsi_tv("Ideaforge", period=14, interval="1d", live_price=None)
    # print(f"1d RSI (TV‑exact) for Ideaforge on {date}: {rsi:.2f}")
    # print("\nLast 10 rows:")
    # print(data.tail(10))
