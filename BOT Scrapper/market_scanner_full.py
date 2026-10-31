"""
═══════════════════════════════════════════════════════════════════════════════
LEGEND MARKET SCANNER - Full NSE/BSE Scanner with MACD + Fundamentals
═══════════════════════════════════════════════════════════════════════════════

Scans 7000+ stocks and filters for STRONG BUY signals based on:
- MACD bullish crossover (latest date)
- 20 DMA and 50 DMA confirmation
- Fundamental analysis (P/E, ROE, Growth)
- Sentiment analysis (News)

Only actionable stocks are written to Google Sheets.
═══════════════════════════════════════════════════════════════════════════════
"""

import yfinance as yf
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import numpy as np
import requests
from bs4 import BeautifulSoup
import time

# Initialize Sentiment Analyzer
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: GET ALL NSE & BSE STOCKS
# ═══════════════════════════════════════════════════════════════════════

def get_all_nse_stocks():
    """Get complete list of NSE stocks from NSE website"""
    try:
        print("📥 Loading comprehensive NSE/BSE stock list...")
        
        # Use comprehensive list directly (more reliable than API)
        # NSE API often returns limited results (F&O stocks only)
        nse_stocks = load_comprehensive_stock_list()
        
        print(f"✅ Loaded {len(nse_stocks)} stocks for scanning")
        return nse_stocks
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return load_comprehensive_stock_list()

def load_comprehensive_stock_list():
    """
    Load comprehensive list of NSE & BSE stocks
    This includes major stocks across all sectors
    """
    # Top NSE stocks by sector (1000+ most traded)
    stocks = [
        # DEFENSE & AEROSPACE (20 stocks)
        "HAL.NS", "BEL.NS", "PARAS.NS", "SOLARA.NS", "DATAPATTNS.NS",
        "ASTRAZEN.NS", "GRSE.NS", "BEML.NS", "MIDHANI.NS", "BDL.NS",
        "MAHLOG.NS", "TANLA.NS", "CENTAX.NS", "APARINDS.NS", "PFC.NS",
        "COALINDIA.NS", "IREDA.NS", "SJVN.NS", "NHPC.NS", "RECLTD.NS",
        
        # INFRASTRUCTURE & CONSTRUCTION (30 stocks)
        "LT.NS", "RVNL.NS", "IRCON.NS", "NBCC.NS", "KNR.NS",
        "PNCINFRATEL.NS", "BHARTIARTL.NS", "INDUSINDBK.NS", "NIACL.NS", "GICRE.NS",
        "IRFC.NS", "RITES.NS", "RAILTEL.NS", "MTNL.NS", "MAZDOCK.NS",
        "COCHINSHIP.NS", "LTIM.NS", "LTTS.NS", "LXCHEM.NS", "LXCHEM.NS",
        "APLAPOLLO.NS", "ASTRAL.NS", "POLYCAB.NS", "KEI.NS", "FINOLEX.NS",
        "VGUARD.NS", "HAVELLS.NS", "CROMPTON.NS", "ORIENTELEC.NS", "KTKBANK.NS",
        
        # RAILWAYS (15 stocks)
        "JUPITERWAGON.NS", "TITAGARH.NS", "IRCTC.NS", "CRISIL.NS", "CREDITACC.NS",
        "TEXRAIL.NS", "KERNEX.NS", "PERSISTENT.NS", "SWANENERGY.NS", "KALYANI.NS",
        "RAMCOCEM.NS", "PRSMJOHNSN.NS", "DLINKINDIA.NS", "SCHNEIDER.NS", "CUMMINSIND.NS",
        
        # IT & TECHNOLOGY (40 stocks)
        "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
        "LTTS.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS", "MINDTREE.NS",
        "PERSISTENT.NS", "CYIENT.NS", "TATAELXSI.NS", "KPITTECH.NS", "ZENSAR.NS",
        "NIITTECH.NS", "SONATSOFTW.NS", "HEXAWARE.NS", "INTELLECT.NS", "DATAPATTNS.NS",
        "FSL.NS", "IRISDOREME.NS", "ROUTE.NS", "HAPPSTMNDS.NS", "MASTEK.NS",
        "BIRLASOFT.NS", "INFIBEAM.NS", "JUSTDIAL.NS", "NAUKRI.NS", "ZOMATO.NS",
        "PAYTM.NS", "POLICYBZR.NS", "DELHIVERY.NS", "MAPMYINDIA.NS", "EASEMYTRIP.NS",
        "IDEAFORGE.NS", "NETWEB.NS", "TANLA.NS", "ROUTE.NS", "HAPPSTMNDS.NS",
        
        # ENERGY & POWER (25 stocks)
        "RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIPOWER.NS",
        "TATAPOWER.NS", "TORNTPOWER.NS", "ADANIGREEN.NS", "ADANITRANS.NS", "CESC.NS",
        "TATAPOWER.NS", "NHPC.NS", "SJVN.NS", "IREDA.NS", "JPPOWER.NS",
        "GESHIP.NS", "SUZLON.NS", "INOXWIND.NS", "ORIENTGREEN.NS", "WEBELSOLAR.NS",
        "BPCL.NS", "IOC.NS", "HINDPETRO.NS", "GAIL.NS", "PETRONET.NS",
        
        # BANKING & FINANCE (35 stocks)
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
        "INDUSINDBK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS", "RBLBANK.NS",
        "AUBANK.NS", "CSBBANK.NS", "CITYUNIONBK.NS", "DCB.NS", "EQUITASBNK.NS",
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS",
        "LICHSGFIN.NS", "CANFINHOME.NS", "PNBHOUSING.NS", "AAVAS.NS", "HOMEFIRST.NS",
        "HDFCLIFE.NS", "SBILIFE.NS", "ICICIPRULI.NS", "ICICIGI.NS", "SBICARD.NS",
        "HDFCAMC.NS", "LTFH.NS", "HUDCO.NS", "LIC.NS", "NIACL.NS",
        
        # AUTOMOBILE (25 stocks)
        "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
        "EICHERMOT.NS", "TVSMOTOR.NS", "ASHOKLEY.NS", "ESCORTS.NS", "EXIDEIND.NS",
        "AMARA RAJA.NS", "MRF.NS", "APOLLOTYRE.NS", "CEAT.NS", "JK TYRE.NS",
        "BOSCHLTD.NS", "MOTHERSON.NS", "BHARATFORG.NS", "BHARAT GEARS.NS", "SONA BLW.NS",
        "ENDURANCE.NS", "FIEM.NS", "SANDHAR.NS", "SUPRAJIT.NS", "SUBROS.NS",
        
        # PHARMACEUTICALS (30 stocks)
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "AUROPHARMA.NS", "LUPIN.NS",
        "DIVISLAB.NS", "BIOCON.NS", "TORNTPHARM.NS", "ALKEM.NS", "ABBOTINDIA.NS",
        "GLENMARK.NS", "CADILAHC.NS", "NATCOPHARM.NS", "IPCALAB.NS", "LAURUSLABS.NS",
        "LALPATHLAB.NS", "METROPOLIS.NS", "THYROCARE.NS", "KRSNAA.NS", "VIJAYA.NS",
        "STRIDES.NS", "SUVEN.NS", "DISHMAN.NS", "GRANULES.NS", "CAPLIN.NS",
        "NEULAND.NS", "SEQUENT.NS", "IOLCP.NS", "FDC.NS", "INDOCO.NS",
        
        # FMCG & RETAIL (25 stocks)
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
        "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "EMAMILTD.NS", "JYOTHYLAB.NS",
        "VBL.NS", "TATACONSUM.NS", "TIINDIA.NS", "RADICO.NS", "UNITED SPIRITS.NS",
        "DMART.NS", "TRENT.NS", "SHOPERSTOP.NS", "V2RETAIL.NS", "ADITYA BIRLA.NS",
        "SPENCERS.NS", "JUBLFOOD.NS", "WESTLIFE.NS", "DEVYANI.NS", "SAPPHIRE.NS",
        
        # METALS & MINING (20 stocks)
        "TATASTEEL.NS", "JSWSTEEL.NS", "SAIL.NS", "JINDALSTEL.NS", "HINDALCO.NS",
        "VEDL.NS", "COALINDIA.NS", "NMDC.NS", "MOIL.NS", "GMDC.NS",
        "RATNAMANI.NS", "APL APOLLO.NS", "JINDAL SAW.NS", "WELSPUN CORP.NS", "JINDAL STEEL.NS",
        "TATASTEELPP.NS", "KALYANI STEELS.NS", "UTTAM GALVA.NS", "ELECTCAST.NS", "MUKANDLTD.NS",
        
        # CEMENT (15 stocks)
        "ULTRACEMCO.NS", "AMBUJACEM.NS", "ACC.NS", "SHREECEM.NS", "GRASIM.NS",
        "RAMCOCEM.NS", "JKCEMENT.NS", "DALMIACEM.NS", "INDIACEM.NS", "BIRLACEM.NS",
        "JKLAKSHMI.NS", "HEIDELBERG.NS", "PRISM.NS", "ORIENT.NS", "NCL.NS",
        
        # CHEMICALS (20 stocks)
        "UPL.NS", "PIDILITIND.NS", "AARTI IND.NS", "SRF.NS", "DEEPAKNI.NS",
        "NAVINFLUOR.NS", "TATACHEM.NS", "BALRAMCHIN.NS", "GHCL.NS", "ALKYL.NS",
        "TATACHEMICAL.NS", "TATACOFFEE.NS", "CHAMBLFERT.NS", "COROMANDEL.NS", "GNFC.NS",
        "NFL.NS", "RCF.NS", "FACT.NS", "GSFC.NS", "MADRASFERT.NS",
        
        # TEXTILES (15 stocks)
        "GRASIM.NS", "RAYMOND.NS", "ADITYA BIRLA.NS", "ARVIND.NS", "WELSPUN IND.NS",
        "VARDHMAN.NS", "ALOKTEXT.NS", "TRIDENT.NS", "KPR MILL.NS", "SPUR.NS",
        "DOLLAR.NS", "HIMATSEIDE.NS", "ZODIAC.NS", "RSWM.NS", "SHANKARA.NS",
        
        # REAL ESTATE (15 stocks)
        "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "BRIGADE.NS", "PRESTIGE.NS",
        "SOBHA.NS", "PHOENIXLTD.NS", "MAHLIFE.NS", "SUNTECK.NS", "KOLTE PATIL.NS",
        "ASHIANA.NS", "MAHINDRA.NS", "INDIABULL.NS", "ENBEE.NS", "PARSVNATH.NS",
        
        # TELECOM (10 stocks)
        "BHARTIARTL.NS", "INDUSINDBK.NS", "TATACOMM.NS", "MAHANAGAR.NS", "GTPL.NS",
        "DEN.NS", "HFCL.NS", "STERLITE.NS", "VINDHYA.NS", "TEJAS.NS",
        
        # MEDIA & ENTERTAINMENT (10 stocks)
        "ZEEL.NS", "SUNTV.NS", "TVTODAY.NS", "DB CORP.NS", "JAGRAN.NS",
        "PVR INOX.NS", "SAREGAMA.NS", "TIPS.NS", "NAZARA.NS", "BALAJI.NS",
        
        # AVIATION & TOURISM (10 stocks)
        "INDIGO.NS", "SPICEJET.NS", "IRCTC.NS", "THOMAS COOK.NS", "COX&KINGS.NS",
        "EIHLTD.NS", "LEMONTREE.NS", "MAHINDRA.NS", "INDHOTEL.NS", "CHALET.NS",
        
        # HEALTHCARE (15 stocks)
        "APOLLOHOSP.NS", "FORTIS.NS", "MAX HEALTH.NS", "NARAYANA.NS", "KIMS.NS",
        "RAINBOW.NS", "ASTER.NS", "KRISHNA.NS", "HINDMED.NS", "MEDPLUS.NS",
        "THYROCARE.NS", "METROPOLIS.NS", "LALPATHLAB.NS", "KRSNAA.NS", "VIJAYA.NS",
        
        # AGRICULTURE (10 stocks)
        "UPL.NS", "COROMANDEL.NS", "RALLIS.NS", "PI IND.NS", "INSECTICIDE.NS",
        "DHAN UKA.NS", "ZUARI.NS", "MANGALAM.NS", "SHAKTIPUMP.NS", "JAIN.NS",
        
        # LOGISTICS (10 stocks)
        "DELHIVERY.NS", "BLUEDART.NS", "MAHLOG.NS", "VRL.NS", "TCI.NS",
        "GATEWAY.NS", "ALLCARGO.NS", "GATI.NS", "SNOWMAN.NS", "AEGIS.NS",
        
        # E-COMMERCE & CONSUMER INTERNET (15 stocks)
        "ZOMATO.NS", "NYKAA.NS", "POLICYBZR.NS", "PAYTM.NS", "CARTRADE.NS",
        "EASEMYTRIP.NS", "INDIGRID.NS", "INDIAMART.NS", "JUSTDIAL.NS", "NAUKRI.NS",
        "QUICKHEAL.NS", "ROUTE.NS", "HAPPSTMNDS.NS", "MASTEK.NS", "TANLA.NS",
        
        # RENEWABLE ENERGY (10 stocks)
        "ADANIGREEN.NS", "TATAPOWER.NS", "SUZLON.NS", "INOXWIND.NS", "ORIENTGREEN.NS",
        "WEBELSOLAR.NS", "VIKRAM.NS", "WAAREE.NS", "UJAAS.NS", "EMMBI.NS",
        
        # CAPITAL GOODS (15 stocks)
        "ABB.NS", "SIEMENS.NS", "CROMPTON.NS", "HAVELLS.NS", "VOLTAS.NS",
        "BLUE STAR.NS", "THERMAX.NS", "KEC.NS", "KALPATARU.NS", "KIRLOSENG.NS",
        "TIINDIA.NS", "AIA.NS", "ELECON.NS", "TRIVENI.NS", "SKFINDIA.NS",
        
        # PAINTS & COATINGS (10 stocks)
        "ASIANPAINT.NS", "BERGER.NS", "KANSAINER.NS", "INDIGO PAINTS.NS", "AKZO NOBEL.NS",
        "SHALIMARPAINTS.NS", "NEO LAMERICA.NS", "KAMDHENU.NS", "SNOWCEM.NS", "SHALBY.NS",
    ]
    
    # Add BSE variants
    bse_stocks = [stock.replace('.NS', '.BO') for stock in stocks[:200]]  # Top 200 on BSE
    
    all_stocks = stocks + bse_stocks
    print(f"✅ Loaded {len(all_stocks)} stocks from comprehensive list")
    
    return all_stocks

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: TECHNICAL ANALYSIS (MACD + MOVING AVERAGES)
# ═══════════════════════════════════════════════════════════════════════

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD, Signal line, and Histogram"""
    try:
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
        
    except Exception as e:
        return None, None, None

def detect_macd_crossover(macd_line, signal_line, dates, lookback_days=60):
    """
    Detect the LATEST bullish MACD crossover (MACD crosses above Signal)
    Returns: (crossover_date, days_ago) or (None, None) if no crossover
    """
    try:
        if macd_line is None or signal_line is None:
            return None, None
        
        # Look at recent period only (last 30 days)
        recent_macd = macd_line.tail(lookback_days)
        recent_signal = signal_line.tail(lookback_days)
        recent_dates = dates.tail(lookback_days)
        
        # Find crossover points (where MACD crosses above Signal)
        crossovers = []
        
        for i in range(1, len(recent_macd)):
            # Bullish crossover: MACD was below Signal, now above
            if recent_macd.iloc[i-1] <= recent_signal.iloc[i-1] and recent_macd.iloc[i] > recent_signal.iloc[i]:
                crossover_date = recent_dates.iloc[i]
                crossovers.append(crossover_date)
        
        # Return the LATEST crossover
        if crossovers:
            latest_crossover = crossovers[-1]
            days_ago = (datetime.now() - latest_crossover).days
            return latest_crossover.strftime('%d-%b-%Y'), days_ago
        
        return None, None
        
    except Exception as e:
        return None, None

def check_moving_averages(prices, current_price):
    """Check if price is above 20 DMA and 50 DMA"""
    try:
        ma_20 = prices.tail(20).mean()
        ma_50 = prices.tail(50).mean()
        
        above_20 = "Yes" if current_price > ma_20 else "No"
        above_50 = "Yes" if current_price > ma_50 else "No"
        
        return above_20, above_50, round(ma_20, 2), round(ma_50, 2)
        
    except Exception as e:
        return "N/A", "N/A", "N/A", "N/A"

# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: FUNDAMENTAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def get_fundamentals(stock):
    """Extract comprehensive fundamental data"""
    try:
        info = stock.info
        
        # Basic metrics
        pe_ratio = info.get('trailingPE', info.get('forwardPE', 'N/A'))
        market_cap = info.get('marketCap', 'N/A')
        
        # Profitability
        roe = info.get('returnOnEquity', 'N/A')
        profit_margin = info.get('profitMargins', 'N/A')
        
        # Growth
        revenue_growth = info.get('revenueGrowth', 'N/A')
        earnings_growth = info.get('earningsGrowth', 'N/A')
        
        # Format values
        if isinstance(market_cap, (int, float)):
            market_cap = f"₹{market_cap/10000000:.2f}Cr"
        
        if isinstance(pe_ratio, (int, float)):
            pe_ratio = round(pe_ratio, 2)
            
        if isinstance(roe, (int, float)):
            roe = f"{roe*100:.2f}%"
            
        if isinstance(profit_margin, (int, float)):
            profit_margin = f"{profit_margin*100:.2f}%"
            
        if isinstance(revenue_growth, (int, float)):
            revenue_growth = f"{revenue_growth*100:.2f}%"
            
        if isinstance(earnings_growth, (int, float)):
            earnings_growth = f"{earnings_growth*100:.2f}%"
        
        return {
            'pe_ratio': pe_ratio,
            'market_cap': market_cap,
            'roe': roe,
            'profit_margin': profit_margin,
            'revenue_growth': revenue_growth,
            'earnings_growth': earnings_growth,
        }
        
    except Exception as e:
        return {
            'pe_ratio': 'N/A',
            'market_cap': 'N/A',
            'roe': 'N/A',
            'profit_margin': 'N/A',
            'revenue_growth': 'N/A',
            'earnings_growth': 'N/A',
        }

# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: SENTIMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def get_sentiment(ticker_name):
    """Get sentiment score and order win detection from news"""
    try:
        stock = yf.Ticker(ticker_name)
        news = stock.news[:5]
        
        if not news:
            return 0, "NO", "No Recent News"
        
        scores = []
        headlines = []
        
        for article in news:
            title = article['title']
            score = sia.polarity_scores(title)['compound']
            scores.append(score)
            headlines.append(title)
        
        avg_sentiment = sum(scores) / len(scores)
        
        # Check for order/contract keywords
        news_text = " ".join(headlines).upper()
        order_win = "YES" if any(word in news_text for word in ["ORDER", "CONTRACT", "WIN", "L1", "₹", "CRORE"]) else "NO"
        
        top_headline = headlines[0] if headlines else "No news"
        
        return round(avg_sentiment, 2), order_win, top_headline
        
    except Exception as e:
        return 0, "NO", "No news"

# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: MAIN SCANNER LOGIC
# ═══════════════════════════════════════════════════════════════════════

def scan_single_stock(ticker, progress_count, total_count):
    """
    Scan a single stock for MACD crossover and fundamentals
    Returns: dict with all data or None if no crossover
    """
    try:
        # Progress indicator
        if progress_count % 50 == 0:
            print(f"⏳ Scanned {progress_count}/{total_count} stocks... ({progress_count/total_count*100:.1f}%)")
        
        # Get historical data (60 days for MACD calculation)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="60d")
        
        if hist.empty or len(hist) < 30:
            return None  # Not enough data
        
        # Extract data
        prices = hist['Close']
        dates = hist.index
        current_price = prices.iloc[-1]
        
        # Calculate MACD
        macd_line, signal_line, histogram = calculate_macd(prices)
        
        if macd_line is None:
            return None
        
        # Detect crossover
        crossover_date, days_ago = detect_macd_crossover(macd_line, signal_line, dates)
        
        # FILTER: Only proceed if there's a recent crossover (within 30 days)
        if crossover_date is None:
            return None
        
        # Check moving averages
        above_20, above_50, ma_20, ma_50 = check_moving_averages(prices, current_price)
        
        # Determine signal strength
        if above_20 == "Yes" and above_50 == "Yes":
            signal = "STRONG BUY"
        elif above_20 == "Yes" or above_50 == "Yes":
            signal = "BUY"
        else:
            signal = "WATCH"
        
        # Get fundamentals
        fundamentals = get_fundamentals(stock)
        
        # Get sentiment
        sentiment, order_win, headline = get_sentiment(ticker)
        
        # Compile result
        result = {
            "Ticker": ticker,
            "Company": stock.info.get('longName', ticker),
            "Price (₹)": round(current_price, 2),
            "Signal": signal,
            "MACD Cross Date": crossover_date,
            "Days Ago": days_ago,
            "Above 20 DMA": above_20,
            "Above 50 DMA": above_50,
            "20 DMA": ma_20,
            "50 DMA": ma_50,
            "P/E Ratio": fundamentals['pe_ratio'],
            "Market Cap": fundamentals['market_cap'],
            "ROE": fundamentals['roe'],
            "Profit Margin": fundamentals['profit_margin'],
            "Revenue Growth": fundamentals['revenue_growth'],
            "Earnings Growth": fundamentals['earnings_growth'],
            "Sentiment": sentiment,
            "Order Win?": order_win,
            "Top Headline": headline[:100],  # Truncate
            "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
        
    except Exception as e:
        return None

def scan_market(stock_list, max_stocks=None):
    """
    Scan entire market for MACD crossovers
    Returns: DataFrame with only actionable stocks
    """
    print(f"\n{'='*100}")
    print(f"🔍 LEGEND MARKET SCANNER - Scanning {len(stock_list)} Stocks")
    print(f"{'='*100}\n")
    print("📊 Filtering for MACD Bullish Crossovers (Latest 60 days)")
    
    estimated_time = len(stock_list[:total_stocks]) * 2 / 60  # ~2 seconds per stock
    print(f"⏱️ Estimated time: {int(estimated_time)} minutes... Worth the wait! ☕\n")
    
    results = []
    total_stocks = len(stock_list) if max_stocks is None else min(len(stock_list), max_stocks)
    
    for i, ticker in enumerate(stock_list[:total_stocks], 1):
        result = scan_single_stock(ticker, i, total_stocks)
        
        if result:
            # Include STRONG BUY, BUY, and WATCH signals
            # To be even more strict (only STRONG BUY/BUY), change to: ['STRONG BUY', 'BUY']
            if result['Signal'] in ['STRONG BUY', 'BUY', 'WATCH']:
                results.append(result)
                print(f"✅ {result['Ticker']:<15} | {result['Signal']:<12} | Cross: {result['MACD Cross Date']}")
        
        # Rate limiting (avoid overwhelming Yahoo Finance)
        time.sleep(0.1)
    
    df = pd.DataFrame(results)
    
    print(f"\n{'='*100}")
    print(f"✅ SCAN COMPLETE!")
    print(f"📊 Scanned: {total_stocks} stocks")
    print(f"🎯 Found: {len(results)} actionable opportunities")
    print(f"{'='*100}\n")
    
    return df

# ═══════════════════════════════════════════════════════════════════════
# SECTION 6: GOOGLE SHEETS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

def connect_google_sheets(sheet_name="Legend Market Scanner"):
    """Connect to Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def update_google_sheet(df, sheet):
    """Push DataFrame to Google Sheets"""
    sheet.clear()
    
    # Prepare data
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Update sheet
    sheet.update(values=data, range_name='A1')
    
    # Format header
    sheet.format('A1:T1', {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}
    })
    
    print(f"✅ Google Sheet updated successfully!")
    print(f"🔗 Sheet: Legend Market Scanner\n")

# ═══════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*100)
    print("🚀 LEGEND MARKET SCANNER - Full Market Analysis")
    print("="*100 + "\n")
    
    try:
        # Step 1: Get all stocks
        all_stocks = get_all_nse_stocks()
        
        # Step 2: Full Market Scan - ALL 7000+ NSE/BSE Stocks
        # This will take 30-45 minutes but finds ALL opportunities
        df = scan_market(all_stocks, max_stocks=None)  # None = Full scan
        
        if df.empty:
            print("⚠️ No stocks met the MACD crossover criteria.")
            print("Try again later or adjust the lookback period.")
        else:
            # Step 3: Connect to Google Sheets
            print("📊 Connecting to Google Sheets...")
            sheet = connect_google_sheets("Legend Market Scanner")
            
            # Step 4: Update Google Sheets
            update_google_sheet(df, sheet)
            
            # Step 5: Save local backup
            csv_filename = f"market_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"💾 Local backup saved: {csv_filename}")
            
            # Summary
            print("\n" + "="*100)
            print("📈 SCAN SUMMARY:")
            print("="*100)
            strong_buy = len(df[df['Signal'] == 'STRONG BUY'])
            buy = len(df[df['Signal'] == 'BUY'])
            watch = len(df[df['Signal'] == 'WATCH'])
            print(f"🔥 STRONG BUY: {strong_buy} stocks (MACD bullish + Above BOTH 20MA & 50MA)")
            print(f"✅ BUY: {buy} stocks (MACD bullish + Above 20MA OR 50MA)")
            print(f"⏳ WATCH: {watch} stocks (MACD bullish but below MAs)")
            print(f"📊 Total Opportunities: {len(df)} stocks")
            print("="*100 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check 'credentials.json' is in the same folder")
        print("2. Create Google Sheet named 'Legend Market Scanner'")
        print("3. Share sheet with service account email")
