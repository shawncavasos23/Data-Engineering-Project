import openai  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
from technical_analysis import run_technical_analysis
from fundamental_analysis import get_fundamental_data
from macroeconomic_analysis import fetch_economic_data
from news_analysis import fetch_news
from reddit_analysis import run_reddit_analysis
from db_utils import create_connection
from email_utils import send_email  # Import email function
from trade_execution import place_trade  # Import Alpaca trade function

# Securely load OpenAI API Key
api_key = "your_api_key"


def add_ticker(ticker):
    """Add a new ticker to all relevant tables if it doesn't already exist."""
    conn = create_connection()
    if conn is None:
        print("Error: Failed to create database connection.")
        return

    cursor = conn.cursor()

    try:
        # Check if the ticker already exists in the fundamentals table
        cursor.execute("SELECT 1 FROM fundamentals WHERE ticker = ?", (ticker,))
        exists = cursor.fetchone()

        if exists:
            print(f"Ticker {ticker} already exists in the database.")
        else:
            # Add ticker to fundamentals
            cursor.execute("""
                INSERT INTO fundamentals (ticker, sector, pe_ratio, market_cap, revenue, beta, roa, roe, cluster) 
                VALUES (?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
            """, (ticker,))

            # Add an entry to technicals
            cursor.execute("""
                INSERT INTO technicals (ticker, date, open, high, low, close, adj_close, volume, ma50, ma200, macd, signal_line, rsi, upper_band, lower_band, adx, obv, pivot, r1, s1)
                VALUES (?, DATE('now'), NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
            """, (ticker,))

            # Add placeholder trade signal
            cursor.execute("""
                INSERT INTO trade_signals (ticker, signal, buy_price, sell_price, stop_loss, date_generated)
                VALUES (?, 'HOLD', NULL, NULL, NULL, DATE('now'));
            """, (ticker,))

            # Commit changes
            conn.commit()
            print(f"Ticker {ticker} added successfully to all relevant tables.")

    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    
    finally:
        conn.close()

def update_stock_data(ticker):
    """
    Fetches the latest stock, macroeconomic indicators, news, and sentiment data for a specific ticker.
    """

    print(f"Updating data for {ticker}...")

    # Connect to SQLite database
    conn = create_connection()
    cursor = conn.cursor()

    # Ensure ticker exists in the database
    cursor.execute("SELECT COUNT(*) FROM fundamentals WHERE ticker = ?", (ticker,))
    if cursor.fetchone()[0] == 0:
        print(f"⚠ {ticker} not found in database. Please add it before updating.")
        conn.close()
        return
    
    run_technical_analysis(ticker)
    get_fundamental_data(ticker)
    run_reddit_analysis(ticker)
    fetch_news(ticker)
    fetch_economic_data()
    
    conn.commit()
    conn.close()
    
    print(f"Data updated for {ticker}.")

def extract_existing_data(ticker):
    """
    Extracts existing stock data, fundamental analysis, technical indicators, macroeconomic trends, news, and sentiment 
    from the database instead of making new API calls.
    """

    conn = create_connection()
    
    # Extract Fundamentals
    fundamentals_query = "SELECT * FROM fundamentals WHERE ticker = ?"
    fundamentals = pd.read_sql(fundamentals_query, conn, params=(ticker,))

    # Extract Peer Companies from Clustering
    peer_query = """
    SELECT f.ticker FROM fundamentals f
    WHERE f.cluster = (SELECT cluster FROM fundamentals WHERE ticker = ?) AND f.ticker != ?
    """
    peer_companies = pd.read_sql(peer_query, conn, params=(ticker, ticker))

    # Extract Technical Indicators (Most Recent)
    technicals_query = """
    SELECT * FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 1
    """
    technicals = pd.read_sql(technicals_query, conn, params=(ticker,))

    # Extract Macroeconomic Data (Latest Available)
    macroeconomic_query = """
    SELECT indicator, value FROM macroeconomic_data 
    WHERE date = (SELECT MAX(date) FROM macroeconomic_data)
    """
    macro_data = pd.read_sql(macroeconomic_query, conn)

    # Extract Latest News
    news_query = """
    SELECT title FROM news ORDER BY published_at DESC LIMIT 5
    """
    news_titles = pd.read_sql(news_query, conn)['title'].tolist()

    # Extract Sentiment Data (Reddit Mentions & Google Trends)
    sentiment_query = """
    SELECT * FROM reddit_mentions WHERE ticker = ? ORDER BY date DESC LIMIT 5
    """
    sentiment_data = pd.read_sql(sentiment_query, conn, params=(ticker,))

    conn.close()

    return {
        "fundamentals": fundamentals.to_dict(orient="records")[0] if not fundamentals.empty else {},
        "technical_data": technicals.to_dict(orient="records")[0] if not technicals.empty else {},
        "macro_data": macro_data.set_index("indicator")["value"].to_dict(),
        "news_titles": news_titles,
        "sentiment_data": sentiment_data.to_dict(orient="records")[0] if not sentiment_data.empty else {},
        "peer_companies": peer_companies["ticker"].tolist()
    }

def run_analysis_and_execute_trade(ticker):
    """
    Extracts existing financial data from the database, generates an AI-powered trading signal,
    sends the results via email, and executes trades if applicable.
    """
    
    print(f"Extracting existing data for {ticker}...")
    extracted_data = extract_existing_data(ticker)

    # 🔹 Generate AI Final Trading Signal
    ai_final_trading_signal = get_ai_full_trading_signal(
        ticker,
        extracted_data["macro_data"],
        extracted_data["fundamentals"],
        extracted_data["technical_data"],
        extracted_data["sentiment_data"],
        extracted_data["macro_data"],  # Latest macroeconomic indicators
        extracted_data["news_titles"],  # Top recent news headlines
        extracted_data["peer_companies"]  # Peer comparison data
    )

    print("\nAI-Generated Final Trading Signal & Price Targets:")
    print(ai_final_trading_signal)

    # Send AI-generated output via email
    send_email(
        subject=f"AI Trading Analysis for {ticker}",
        body=ai_final_trading_signal
    )

    # **Execute Trade Based on AI Signal**
    if "BUY" in ai_final_trading_signal:
        place_trade(ticker, "buy", 10)  # Example: Buy 10 shares
    elif "SELL" in ai_final_trading_signal:
        place_trade(ticker, "sell", 10)  # Example: Sell 10 shares

    return f"AI analysis complete. Trade executed if applicable."



# Securely load OpenAI API Key
def get_ai_full_trading_signal(ticker, db_path, macro_data, fundamental_data, technical_data, sentiment_data, latest_economic_data, news_titles, peer_companies):
    """
    AI summarizes all generated insights to produce a final trading signal, target prices, and justification.
    """

    # Fetch most recent closing price inline
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT close FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 1;", (ticker,))
    recent_close = cursor.fetchone()
    conn.close()
    recent_close = recent_close[0] if recent_close else "N/A"

    # Format economic indicators for readability
    economic_summary = "\n".join([
        f"- {key}: {value:,.2f}" if isinstance(value, (int, float)) else f"- {key}: {value}"
        for key, value in latest_economic_data.items()
    ])

    # Format news headlines
    news_bullets = "\n".join([f"- {title}" for title in news_titles])

    # Format peer comparison table
    peer_table = "\n".join([f"- {peer}" for peer in peer_companies]) if peer_companies else "No peer data available."

    # AI Prompt for Full Trading Analysis   
    prompt = f"""  
        You are a quantitative financial analyst specializing in macroeconomics, fundamental valuation, technical indicators, and behavioral finance.  
        Your task is to generate a **data-driven trading analysis** for {ticker} using the provided database metrics.  

        Stock: {ticker}  

        Macroeconomic Analysis  
        Evaluate the broader economic environment using the following indicators from the database:  
            - Federal Funds Rate: {macro_data.get('FEDFUNDS', 'N/A')}  
            - Inflation Rate (CPI): {macro_data.get('CPIAUCSL', 'N/A')}  
            - Producer Price Index (PPI): {macro_data.get('PPIACO', 'N/A')}  
            - Unemployment Rate: {macro_data.get('UNRATE', 'N/A')}  
            - Total Nonfarm Payrolls (Employment): {macro_data.get('PAYEMS', 'N/A')}    

        Recent macroeconomic news headlines that may impact {ticker}:  
        {news_bullets}  

        Fundamental Analysis  
        Assess {ticker}'s financial position using key metrics from the `fundamentals` table:  
            - Price-to-Earnings (P/E) Ratio: {fundamental_data.get('pe_ratio', 'N/A')}  
            - Market Capitalization: {fundamental_data.get('market_cap', 'N/A')}  
            - Revenue: {fundamental_data.get('revenue', 'N/A')}  
            - Beta (Volatility Measure): {fundamental_data.get('beta', 'N/A')}  
            - Return on Assets (ROA): {fundamental_data.get('roa', 'N/A')}  
            - Return on Equity (ROE): {fundamental_data.get('roe', 'N/A')}  
            - Dividend Yield: {fundamental_data.get('dividend_yield', 'N/A')}  
            - Dividend Per Share: {fundamental_data.get('dividend_per_share', 'N/A')}  
            - Total Debt: {fundamental_data.get('total_debt', 'N/A')}  
            - Total Cash: {fundamental_data.get('total_cash', 'N/A')}  
            - Free Cash Flow: {fundamental_data.get('free_cash_flow', 'N/A')}  
            - Operating Cash Flow: {fundamental_data.get('operating_cash_flow', 'N/A')}  
            - Net Income: {fundamental_data.get('net_income', 'N/A')}  

        Peer Comparison  
        Analyze {ticker} compared to similar companies in the same sector using the clustering model:  
        {peer_table}  

        Technical Analysis  
        Evaluate {ticker}'s price action and momentum using data from the `technicals` table:  
            - **Most Recent Closing Price:** {recent_close}  
            - 50-Day Moving Average: {technical_data.get('ma50', 'N/A')}  
            - 200-Day Moving Average: {technical_data.get('ma200', 'N/A')}  
            - MACD Value: {technical_data.get('macd', 'N/A')}  
            - RSI (Relative Strength Index): {technical_data.get('rsi', 'N/A')}  
            - Bollinger Bands (Upper, Lower): ({technical_data.get('upper_band', 'N/A')}, {technical_data.get('lower_band', 'N/A')})  
            - ADX (Trend Strength): {technical_data.get('adx', 'N/A')}  
            - On-Balance Volume (OBV): {technical_data.get('obv', 'N/A')}  
            - Pivot Point: {technical_data.get('pivot', 'N/A')}  
            - Resistance Level (R1): {technical_data.get('r1', 'N/A')}  
            - Support Level (S1): {technical_data.get('s1', 'N/A')}  

        Sentiment Analysis  
        Evaluate investor sentiment using data from the `news` and `reddit_mentions` tables:  
            - Recent news sentiment based on headlines and descriptions: {sentiment_data.get('news_sentiment', 'N/A')}  
            - Number of Reddit mentions for {ticker}: {sentiment_data.get('reddit_mentions', 'N/A')}  
            - Average Reddit post upvote ratio: {sentiment_data.get('upvote_ratio', 'N/A')}  

        AI-Generated Trading Strategy  
        Based on all available data, generate a final trading signal for {ticker}:  
            - **Trading Decision:** Should traders Buy, Sell, or Hold?  
            - **Entry Price:** Optimal price to enter a trade  
            - **Target Price:** Expected price level for taking profit  
            - **Stop-Loss Level:** Risk management level to exit the trade  
            - **Justification:** Explain the rationale using fundamental, technical, macroeconomic, and sentiment insights  
            - **Key Risks & Catalysts:** Highlight any major risks or events that could impact {ticker} in the next three to six months  
    """

    try:
        client = openai.OpenAI(api_key="YOUR_API_KEY")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating final trading signal: {e}"