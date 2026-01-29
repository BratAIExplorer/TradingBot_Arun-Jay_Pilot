"""
🔍 MACD SCANNER ENGINE - Optimized Batch V2
═══════════════════════════════════════════════════════════════════════════════

High-Performance Batch Scanner using yf.download (Threaded)
Scans 100+ stocks per batch to avoid API rate limits.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
from typing import Dict, Optional, List, Tuple
import logging

class MACDScanner:
    """
    Optimized Batch Scanner for Dashboard
    """

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.stop_requested = False
        self.results = []

    def stop(self):
        self.stop_requested = True

    def get_stock_list(self, mode="FULL") -> List[str]:
        """
        Returns managed list of high-liquidity NSE stocks.
        """
        # --- TOP 200 HIGH LIQUIDITY STOCKS ---
        stocks = [
             # NIFTY 50
            "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS", "ITC.NS", "LT.NS", "AXISBANK.NS", 
            "BHARTIARTL.NS", "KOTAKBANK.NS", "SBIN.NS", "HINDUNILVR.NS", "BAJFINANCE.NS", "M&M.NS", "MARUTI.NS", 
            "TITAN.NS", "ULTRACEMCO.NS", "SUNPHARMA.NS", "TATASTEEL.NS", "NTPC.NS", "TATAMOTORS.NS", 
            "POWERGRID.NS", "ADANIENT.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "GRASIM.NS", "COALINDIA.NS", 
            "BAJAJFINSV.NS", "HCLTECH.NS", "ONGC.NS", "HINDALCO.NS", "TECHM.NS", "WIPRO.NS", "DIVISLAB.NS", 
            "CIPLA.NS", "EICHERMOT.NS", "BPCL.NS", "DRREDDY.NS", "HEROMOTOCO.NS", "UPL.NS", "ASIANPAINT.NS", 
            "BRITANNIA.NS", "NESTLEIND.NS", "APOLLOHOSP.NS", "INDUSINDBK.NS", "TATACONSUM.NS",
            
             # DEFENSE & RAILWAYS
            "HAL.NS", "BEL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "BDL.NS", "MIDHANI.NS", "PARAS.NS",
            "RVNL.NS", "IRFC.NS", "IRCON.NS", "RITES.NS", "RAILTEL.NS", "TITAGARH.NS", "TEXRAIL.NS",
            
            # PSU & POWER
            "PFC.NS", "RECLTD.NS", "SJVN.NS", "NHPC.NS", "NLCINDIA.NS", "BHEL.NS", "IOC.NS", "HPCL.NS", 
            "GAIL.NS", "OIL.NS", "MRPL.NS", "CHENNPETRO.NS", "TATAPOWER.NS", "ADANIPOWER.NS", "TORNTPOWER.NS",
            
            # IT & TECH
            "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "KPITTECH.NS", "TATAELXSI.NS", "MPHASIS.NS", "LTTS.NS",
            "CYIENT.NS", "ZENSARTECH.NS", "SONATSOFTW.NS", "INTELLECT.NS", "MASTEK.NS", "TANLA.NS", "ROUTE.NS",
            "NAUKRI.NS", "POLICYBZR.NS", "ZOMATO.NS", "PAYTM.NS", "DELHIVERY.NS", "MAPMYINDIA.NS",
            
            # PHARMA & CHEMICALS
            "LUPIN.NS", "AUROPHARMA.NS", "ALKEM.NS", "TORNTPHARM.NS", "SYNGENE.NS", "BIOCON.NS", "LAURUSLABS.NS",
            "GRANULES.NS", "FDC.NS", "NATCOPHARM.NS", "NAVINFLUOR.NS", "SRF.NS", "PIIND.NS", "AARTIIND.NS",
            "DEEPAKNTR.NS", "TATACHEM.NS", "UPL.NS", "CHAMBLFERT.NS", "COROMANDEL.NS",
            
            # AUTO & ANCILLARY
            "TVSMOTOR.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS", "BHARATFORG.NS", "MOTHERSON.NS", "BOSCHLTD.NS",
            "MRF.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "EXIDEIND.NS", "ENDURANCE.NS", "UNO_MINDA.NS",
            
            # BANKS & FINANCE
            "FEDERALBNK.NS", "IDFCFIRSTB.NS", "AUBANK.NS", "BANDHANBNK.NS", "RBLBANK.NS", "ABCAPITAL.NS",
            "CHOLAFIN.NS", "SHRIRAMFIN.NS", "M&MFIN.NS", "L&TFH.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS",
            "PEL.NS", "POONAWALLA.NS", "ISEC.NS", "CDSL.NS", "MCX.NS", "BSE.NS", "ANGELONE.NS",
            
            # REALTY & INFRA
            "DLF.NS", "GODREJPROP.NS", "LODHA.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "PHOENIXLTD.NS", "BRIGADE.NS",
            "NBCC.NS", "NCC.NS", "GMRINFRA.NS", "IRB.NS", "PNCINFRA.NS", "KNRCON.NS", "HGINFRA.NS",
            
            # FMCG & CONSUMER
            "VBL.NS", "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "COLPAL.NS", "BERGEPAINT.NS", "PIDILITIND.NS",
            "HAVELLS.NS", "VOLTAS.NS", "WHIRLPOOL.NS", "CROMPTON.NS", "POLYCAB.NS", "DIXON.NS", "AMBER.NS",
            "TITAN.NS", "KALYANKJIL.NS", "TRENT.NS", "ABFRL.NS", "PAGEIND.NS", "BATAINDIA.NS", "RELAXO.NS",
        ]
        
        # Add basic BSE check if needed, but primarily NSE
        return sorted(list(set(stocks)))

    def calculate_indicators_batch(self, df_dict):
        """
        Process the entire batch result from yf.download
        Returns list of results
        """
        batch_results = []
        
        # yf.download with group_by='ticker' returns a Dict-like or MultiIndex
        # If single ticker it's a DataFrame, if multiple it's a DataFrame with MultiIndex columns
        
        tickers = df_dict.columns.levels[0] if isinstance(df_dict.columns, pd.MultiIndex) else [df_dict.columns.name]
        
        # Handle the case where Ticker is the level 0
        is_multi = isinstance(df_dict.columns, pd.MultiIndex)
        
        # If it's not multi-index, it means only 1 stock was successful or requested
        if not is_multi:
            # Reframe it to look like multi-index for generic logic: dict[ticker] -> df
            # But wait, yf.download for 1 ticker returns simple DF.
            # We will handle iteration carefully.
            single_ticker_mode = True
            # Trying to infer ticker name is hard if single. We assume list loop handles this?
            # Actually yf.download(..., group_by='ticker') usually returns MultiIndex if >1.
            pass

        # We can iterate through the requested tickers provided they are in columns
        # If columns are (Price, Ticker), we swap. 
        # But group_by='ticker' makes it (Ticker, Price).
        
        for ticker in df_dict.columns.levels[0]: # Iterating 'Ticker' level
            try:
                # Extract Single DF
                df = df_dict[ticker].copy()
                
                # Check data sufficiency
                if df.empty or len(df) < 50: 
                    continue
                
                # Drop NAs
                df.dropna(inplace=True)
                close = df['Close']
                
                # 1. MACD (12, 26, 9)
                ema12 = close.ewm(span=12, adjust=False).mean()
                ema26 = close.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                
                # 2. Moving Averages
                ma20 = close.tail(25).rolling(window=20).mean() # optimize tail
                ma50 = close.tail(55).rolling(window=50).mean()
                
                # 3. Detect Crossover (Latest day)
                # Condition: MACD[-1] > Signal[-1] AND MACD[-2] <= Signal[-2]
                curr_macd = macd_line.iloc[-1]
                curr_sig = signal_line.iloc[-1]
                prev_macd = macd_line.iloc[-2]
                prev_sig = signal_line.iloc[-2]
                
                bullish_cross = (curr_macd > curr_sig) and (prev_macd <= prev_sig)
                
                # User asked for "CROSS DATE". 
                # If specifically TODAY/LATEST, we output date.
                # If they want historical scans, we'd loop back. 
                # Assuming "Latest Scan" means "Recent signal".
                
                # Let's verify standard Bullish Trend (MACD > Signal)
                # The user requirement: "MACD Line cross over the Signal line upwards... show the date it crossed"
                
                # We will search back up to 10 days for the crossover date
                crossover_date = None
                cross_found = False
                
                # Reverse loop last 15 candles
                for i in range(1, 15):
                    idx = -i
                    m_curr = macd_line.iloc[idx]
                    s_curr = signal_line.iloc[idx]
                    m_prev = macd_line.iloc[idx-1]
                    s_prev = signal_line.iloc[idx-1]
                    
                    if m_curr > s_curr and m_prev <= s_prev:
                        # Found the cross
                        crossover_date = df.index[idx].strftime('%d-%b-%Y')
                        cross_found = True
                        break
                
                # Filter: Only show if MACD is currently ABOVE signal (Trend is valid)
                if not (curr_macd > curr_sig):
                    continue # Downward trend currently, ignore old crosses?
                    
                if not cross_found:
                     # It might have maintained bullish for > 15 days
                     # We skip if no recent actionable cross
                     continue
                     
                # 4. Check Strong Buy Conditions
                curr_price = close.iloc[-1]
                val_ma20 = ma20.iloc[-1]
                val_ma50 = ma50.iloc[-1]
                
                above_20 = curr_price > val_ma20
                above_50 = curr_price > val_ma50
                
                # Logic: STRONG BUY if above 20 OR above 50
                if above_20 or above_50:
                    signal = "STRONG BUY"
                else:
                    signal = "BUY"
                    
                # Format Result
                res = {
                    "SYMBOL": ticker.replace(".NS", ""), # Clean name
                    "LTP": round(curr_price, 2),
                    "SIGNAL": signal,
                    "CROSS DATE": crossover_date,
                    "20 DMA": "Yes" if above_20 else "No",
                    "50 DMA": "Yes" if above_50 else "No",
                    "timestamp": datetime.now()
                }
                batch_results.append(res)
                
            except Exception as e:
                # logging.error(f"Error processing {ticker}: {e}")
                pass
                
        return batch_results

    def scan_market(self, max_stocks=None, mode="FULL") -> List[Dict]:
        """
        Batch Scan Execution
        """
        stock_list = self.get_stock_list(mode)
        if max_stocks:
            stock_list = stock_list[:max_stocks]
            
        total = len(stock_list)
        chunk_size = 20 # Safer batch size to avoid JSONDecodeError

        self.results = []
        
        if self.progress_callback:
            self.progress_callback(0, total, f"Starting Batch Scan ({total} symbols)...")
            
        # Chunk Looping
        for i in range(0, total, chunk_size):
            if self.stop_requested: break
            
            chunk = stock_list[i : i + chunk_size]
            
            try:
                batch_str = " ".join(chunk)
                
                # 1. BATCH DOWNLOAD (SAFE MODE)
                from utils import get_yfinance_session
                session = get_yfinance_session()
                
                # FORCE SAFE MODE: BYPASS YFINANCE LIBRARY ENTIRELY
                # User network/environment is blocking standard yf.download causing massive delays.
                # We switch to pure 'utils.fetch_yahoo_history_direct' immediately.
                
                # print(f"🔍 Scanning Batch: {batch_str[:30]}...") 
                
                try:
                    data = self.download_batch_direct(chunk)
                except Exception as fb_e:
                    print(f"❌ Direct Download failed: {fb_e}")
                    data = pd.DataFrame()

                # Legacy yf.download block (DISABLED)
                # try:
                #     data = yf.download(..., session=session)
                # except: ...
                
                if data.empty:
                    continue
                    
                # 2. PROCESS CHUNK
                processed = self.calculate_indicators_batch(data)
                self.results.extend(processed)
                
                # 3. UPDATE UI
                if self.progress_callback:
                    self.progress_callback(min(i + chunk_size, total), total, f"Scanned {min(i + chunk_size, total)}/{total}...")
                    
            except Exception as e:
                print(f"Batch Error: {e}")
                
            # Rate limit between batches
            time.sleep(1.0) # Moderate delay
            
        if self.progress_callback:
            self.progress_callback(total, total, f"✅ Done! Found {len(self.results)}")
            
        return self.results

    def download_batch_direct(self, tickers_list):
        """
        Fallback method to download data loop-wise using direct requests.
        Returns DataFrame compatible with yf.download structure (MultiIndex columns).
        """
        import pandas as pd
        from utils import fetch_yahoo_history_direct
        
        frames = {}
        successful = 0
        
        # print(f"  ↳ Switching to Sequential Direct Download for {len(tickers_list)} symbols...")
        
        for ticker in tickers_list:
            # We assume it takes ~0.5s per request. Slower but robust.
            df = fetch_yahoo_history_direct(ticker, period="3mo", interval="1d")
            
            if not df.empty and len(df) > 0:
                frames[ticker] = df
                successful += 1
            else:
                 # Try adding .NS if missing (fallback for badly formatted input)
                 if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
                     df = fetch_yahoo_history_direct(f"{ticker}.NS", period="3mo", interval="1d")
                     if not df.empty:
                         frames[f"{ticker}.NS"] = df # Store with suffix
                         successful += 1
        
        if not frames:
            return pd.DataFrame()
            
        # print(f"  ↳ Direct Download Success: {successful}/{len(tickers_list)}")
        
        # Combine into MultiIndex DataFrame (Ticker, PriceType)
        # keys=frames.keys() becomes level 0 (Ticker)
        # axis=1 columns
        try:
            result = pd.concat(frames, axis=1, names=['Ticker', 'PriceType'])
            return result
        except Exception as e:
             print(f"Error combining fallback frames: {e}")
             return pd.DataFrame()
            
if __name__ == "__main__":
    print("Testing Batch Scanner...")
    scanner = MACDScanner()
    res = scanner.scan_market(max_stocks=100)
    
    # Print Table
    if res:
        df = pd.DataFrame(res)
        print(df[["SYMBOL", "LTP", "SIGNAL", "CROSS DATE", "20 DMA", "50 DMA"]].to_string(index=False))
    else:
        print("No results found.")
