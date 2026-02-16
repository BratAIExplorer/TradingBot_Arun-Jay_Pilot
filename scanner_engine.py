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
        Matches Legacy Logic: Tries to load Nifty 500 from CSV, falls back to hardcoded list.
        """
        import os
        import pandas as pd
        
        # 1. Try Loading Nifty 500 / All Stocks CSV (Legacy Parity)
        csv_files = ["nifty500.csv", "all_nse_stocks.csv"]
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                try:
                    df = pd.read_csv(csv_file)
                    if 'Symbol' in df.columns:
                        # Ensure .NS suffix
                        stocks = [f"{sym}.NS" if not str(sym).endswith('.NS') else sym for sym in df['Symbol'].tolist()]
                        # print(f"✅ Loaded {len(stocks)} stocks from {csv_file}")
                        return sorted(list(set(stocks)))
                except Exception as e:
                    print(f"⚠️ Error loading {csv_file}: {e}")

        # 2. Fallback: Hardcoded Top 200 (If CSVs missing)
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
        Match Legacy Logic: 60d Lookback, SMA Filters, Long Term Bull
        """
        batch_results = []
        
        # yf.download with group_by='ticker' returns a Dict-like or MultiIndex
        # If single ticker it's a DataFrame, if multiple it's a DataFrame with MultiIndex columns
        
        # Handle the case where Ticker is the level 0
        is_multi = isinstance(df_dict.columns, pd.MultiIndex)
        
        # If it's not multi-index, it means only 1 stock was successful or requested
        # We will iterate through the requested tickers provided they are in columns
        
        # Prepare iteration list
        tickers_to_process = []
        if is_multi:
            tickers_to_process = df_dict.columns.levels[0]
        else:
            # Single ticker result - how to know which ticker?
            # Usually yf.download returns columns like 'Open', 'Close' directly for single ticker
            # We assume the caller knows, but here we might need to deduce or handle robustly.
            # For simplicity in batch mode (which is always >1 ideally), we assume multi.
            # If single, we might skip or handle if we knew the ticker name.
            # Given we pump 50 stocks, it should be multi.
            pass

        for ticker in tickers_to_process:
            try:
                # Extract Single DF
                df = df_dict[ticker].copy()
                
                # Check data sufficiency (200 SMA needs ~200 pts, legacy checks 200)
                if df.empty or len(df) < 200: 
                    continue
                
                # Drop NAs
                df.dropna(inplace=True)
                close = df['Close']
                
                # --- CALCULATE INDICATORS (Legacy 'ta' style logic) ---
                
                # 1. MACD (12, 26, 9)
                ema12 = close.ewm(span=12, adjust=False).mean()
                ema26 = close.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                
                # 2. Moving Averages
                # Legacy uses full rolling. We can do the same.
                ma20 = close.rolling(window=20).mean()
                ma50 = close.rolling(window=50).mean()
                ma100 = close.rolling(window=100).mean()
                ma200 = close.rolling(window=200).mean()
                
                # Get Latest Values
                curr_price = close.iloc[-1]
                curr_macd = macd_line.iloc[-1]
                curr_sig = signal_line.iloc[-1]
                val_ma20 = ma20.iloc[-1]
                val_ma50 = ma50.iloc[-1]
                val_ma100 = ma100.iloc[-1]
                val_ma200 = ma200.iloc[-1]
                
                # --- FILTER 1: TREND DIRECTION (MACD must be Bullish) ---
                if curr_macd <= curr_sig:
                    # print(f"DEBUG: {ticker} Rejected - Bearish MACD")
                    continue # MACD is Bearish, skip immediately
                    
                # --- FILTER 2: SMA SUPPORT (Legacy: Must be above 20 OR 50) ---
                above_20 = curr_price > val_ma20
                above_50 = curr_price > val_ma50
                
                if not (above_20 or above_50):
                     # print(f"DEBUG: {ticker} Rejected - Below SMA 20/50")
                     continue # REJECT: Below both short-term averages (Bottom fishing risky)
                
                # --- FILTER 3: CROSSOVER DATE (Lookback 60 Days) ---
                crossover_date = "Long Term Bull" # Default if no recent cross but trend is up
                cross_found = False
                
                # Look back 60 days (Legacy Logic)
                lookback = min(60, len(df))
                
                for i in range(1, lookback):
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
                
                # print(f"DEBUG: {ticker} MATCHED! Signal={crossover_date}")
                
                # --- SUPPORT / RESISTANCE LOGIC (Smart Buy) ---
                mas = [
                    (val_ma20, '20 DMA'), 
                    (val_ma50, '50 DMA'), 
                    (val_ma100, '100 DMA'), 
                    (val_ma200, '200 DMA')
                ]
                # Filter out NaNs if history is short
                mas = [m for m in mas if not pd.isna(m[0])]
                
                supports = [m for m in mas if curr_price > m[0]]
                resistances = [m for m in mas if curr_price < m[0]]
                
                # Nearest Support
                support_val = max(supports, key=lambda x: x[0])[0] if supports else 0
                support_desc = max(supports, key=lambda x: x[0])[1] if supports else "None"
                
                # Nearest Resistance
                resistance_val = min(resistances, key=lambda x: x[0])[0] if resistances else curr_price * 1.05
                resistance_desc = min(resistances, key=lambda x: x[0])[1] if resistances else "Blue Sky"

                # Prepare Signal String
                signal = "BUY"
                if above_20 or above_50:
                    signal = "STRONG BUY"
                    
                # Format Result
                res = {
                    "SYMBOL": ticker.replace(".NS", ""), # Clean name
                    "LTP": round(curr_price, 2),
                    "SIGNAL": signal,
                    "CROSS DATE": crossover_date,
                    "20 DMA": "Yes" if above_20 else "No",
                    "50 DMA": "Yes" if above_50 else "No",
                    "SUPPORT": support_val, # Float for logic
                    "RESISTANCE": resistance_val, # Float for logic
                    "SUPPORT_DESC": support_desc,
                    "RESISTANCE_DESC": resistance_desc,
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
                    print("DEBUG: Data batch is empty.")
                    continue
                
                print(f"DEBUG: Data Shape: {data.shape}")
                print(f"DEBUG: Data Columns Level 0: {data.columns.levels[0].tolist() if isinstance(data.columns, pd.MultiIndex) else data.columns.tolist()}")
                    
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
            df = fetch_yahoo_history_direct(ticker, period="1y", interval="1d")
            
            if not df.empty and len(df) > 0:
                frames[ticker] = df
                successful += 1
            else:
                 # Try adding .NS if missing (fallback for badly formatted input)
                 if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
                     df = fetch_yahoo_history_direct(f"{ticker}.NS", period="1y", interval="1d")
                     if not df.empty:
                         frames[f"{ticker}.NS"] = df # Store with suffix
                         successful += 1
            
            # Small delay between direct requests to be extra safe
            time.sleep(0.2)
        
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
    
    # Check if stock list loads correctly
    stocks = scanner.get_stock_list()
    print(f"DEBUG: Loaded {len(stocks)} stocks for scanning.")
    
    # Progress callback
    def debug_callback(current, total, msg):
        print(f"[{current}/{total}] {msg}")
        
    scanner.progress_callback = debug_callback
    res = scanner.scan_market(max_stocks=100) # Still limit to 100 for verification speed, user can change later
    
    # Print Table
    if res:
        df = pd.DataFrame(res)
        print(df[["SYMBOL", "LTP", "SIGNAL", "CROSS DATE", "SUPPORT", "RESISTANCE"]].to_string(index=False))
    else:
        print("No results found.")
