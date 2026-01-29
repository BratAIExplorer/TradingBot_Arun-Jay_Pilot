import yfinance as yf
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Initialize Sentiment Analyzer
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

# Google Sheets Setup
def connect_google_sheets(sheet_name="Legend Stocks Live"):
    """Connect to Google Sheets and return the worksheet"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    
    # Open the sheet
    sheet = client.open(sheet_name).sheet1
    return sheet

def get_sentiment(ticker_name):
    """Get sentiment score and order win detection from news"""
    try:
        stock = yf.Ticker(ticker_name)
        news = stock.news[:5]  # Top 5 headlines
        
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
        
        # Get top headline
        top_headline = headlines[0] if headlines else "No news"
        
        return round(avg_sentiment, 2), order_win, top_headline
        
    except Exception as e:
        return 0, "NO", f"Error: {str(e)}"

def analyze_stocks(stock_list):
    """Analyze all stocks and return DataFrame"""
    results = []
    
    print(f"\n{'='*80}")
    print(f"🔍 LEGEND STOCK ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    print(f"{'Ticker':<15} | {'Price':>8} | {'Sent.':>6} | {'Order?':>7} | {'Action':<15}")
    print("-" * 80)
    
    for ticker in stock_list:
        try:
            stock = yf.Ticker(ticker)
            price = stock.fast_info['last_price']
            sentiment, order_win, headline = get_sentiment(ticker)
            
            # Legend Logic
            action = "⏳ WATCH"
            if sentiment > 0.2 or order_win == "YES":
                action = "🔥 BUY/SWING"
            elif sentiment < -0.2:
                action = "⚠️ AVOID"
            
            print(f"{ticker:<15} | ₹{price:>7.2f} | {sentiment:>6} | {order_win:>7} | {action:<15}")
            
            results.append({
                "Ticker": ticker,
                "Price (₹)": round(price, 2),
                "Sentiment": sentiment,
                "Order Win?": order_win,
                "Action": action,
                "Top Headline": headline,
                "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            print(f"{ticker:<15} | ERROR: {str(e)}")
            results.append({
                "Ticker": ticker,
                "Price (₹)": "N/A",
                "Sentiment": 0,
                "Order Win?": "NO",
                "Action": "⚠️ ERROR",
                "Top Headline": f"Error: {str(e)}",
                "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return pd.DataFrame(results)

def update_google_sheet(df, sheet):
    """Push DataFrame to Google Sheets"""
    # Clear existing content
    sheet.clear()
    
    # Prepare data (headers + rows)
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Update sheet
    sheet.update('A1', data)
    
    # Format header row (bold)
    sheet.format('A1:G1', {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}
    })
    
    print(f"\n✅ Google Sheet updated successfully!")
    print(f"🔗 Check your sheet: Legend Stocks Live\n")

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Your stock list - ADD MORE STOCKS HERE
    my_stocks = [
        "HAL.NS", 
        "BEL.NS", 
        "LT.NS", 
        "RVNL.NS", 
        "JUPITERWAGONS.NS"
    ]
    
    try:
        # Step 1: Analyze stocks
        df = analyze_stocks(my_stocks)
        
        # Step 2: Connect to Google Sheets
        print("\n📊 Connecting to Google Sheets...")
        sheet = connect_google_sheets("Legend Stocks Live")
        
        # Step 3: Update the sheet
        update_google_sheet(df, sheet)
        
        # Step 4: Also save local CSV backup
        csv_filename = f"legend_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"💾 Local backup saved: {csv_filename}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check that 'credentials.json' is in the same folder as this script")
        print("2. Verify you shared the Google Sheet with the service account email")
        print("3. Make sure the sheet name is exactly 'Legend Stocks Live'")
