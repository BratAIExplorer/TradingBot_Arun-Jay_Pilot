"""
Arun Backtester Module
Uses backtesting.py to simulate RSI and SIP strategies on historical data.
"""

from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
import numpy as np

class RsiStrategy(Strategy):
    buy_rsi = 35
    sell_rsi = 65
    
    def init(self):
        # We assume the data already has RSI, or calculate it here
        # For simplicity in this wrapper, we expect an 'RSI' column
        pass

    def next(self):
        if self.data.RSI[-1] <= self.buy_rsi:
            self.buy()
        elif self.data.RSI[-1] >= self.sell_rsi:
            self.position.close()

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_backtest(symbol, period="1y", interval="1d", buy_rsi=35, sell_rsi=65):
    """Run a simple RSI backtest and return stats"""
    try:
        # Patch for Yahoo Finance 403/Blocking
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

        # 1. Fetch data
        df = yf.download(symbol, period=period, interval=interval, progress=False, session=session)
        
        # Retry with .NS if empty and looks like an Indian stock (no suffix)
        if df.empty and "." not in symbol:
             symbol_ns = f"{symbol}.NS"
             df = yf.download(symbol_ns, period=period, interval=interval, progress=False, session=session)

        if df.empty:
            msg = f"No data found for {symbol}"
            if "." not in symbol:
                msg += f" (tried {symbol}.NS too)"
            return {"error": msg}
        
        # 2. Add RSI
        df['RSI'] = calculate_rsi(df)
        df = df.dropna()
        
        # 3. Setup Strategy
        class DynamicRsi(RsiStrategy):
            pass
        DynamicRsi.buy_rsi = buy_rsi
        DynamicRsi.sell_rsi = sell_rsi
        
        # 4. Run Backtest
        bt = Backtest(df, DynamicRsi, cash=50000, commission=.002)
        stats = bt.run()
        
        # 5. Format results
        return {
            "Total Return": f"{stats['Return [%]']:.2f}%",
            "Win Rate": f"{stats['Win Rate [%]']:.2f}%",
            "Max Drawdown": f"{stats['Max. Drawdown [%]']:.2f}%",
            "Total Trades": int(stats['# Trades']),
            "Sharpe Ratio": f"{stats['Sharpe Ratio']:.2f}"
        }
    except Exception as e:
        return {"error": str(e)}
