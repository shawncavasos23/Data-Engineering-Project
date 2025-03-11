import openai  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
from technical_analysis import run_technical_analysis
from fundamental_analysis import run_fundamental_analysis
from macroeconomic_analysis import fetch_economic_data
from news_analysis import fetch_news
from reddit_analysis import run_reddit_analysis
from database import create_connection
from email_utils import send_email  # Import email function
from trade_execution import place_trade  # Import Alpaca trade function

# Securely load OpenAI API Key
api_key = "your_api_key"

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

    # 🔹 **Step 1: Update Technical & Fundamental Data**
    print(f"Running Technical Analysis for {ticker}...")
    run_technical_analysis(ticker)

    print(f"Running Fundamental Analysis for {ticker}...")
    run_fundamental_analysis(ticker)

    print(f"Running Reddit Sentiment & Google Trends Analysis for {ticker}...")
    run_reddit_analysis(ticker)

    # 🔹 **Step 2: Update Macroeconomic & News Data**
    print("Fetching latest macroeconomic data...")
    fetch_economic_data()

    print("Fetching latest news headlines...")
    fetch_news()

    conn.commit()
    conn.close()
    print(f"✅ Data updated for {ticker}.")

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
    SELECT * FROM reddit_mentions WHERE ticker = ? ORDER BY date DESC LIMIT 1
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

    # **🔹 Execute Trade Based on AI Signal**
    if "BUY" in ai_final_trading_signal:
        place_trade(ticker, "buy", 10)  # Example: Buy 10 shares
    elif "SELL" in ai_final_trading_signal:
        place_trade(ticker, "sell", 10)  # Example: Sell 10 shares

    return f"✅ AI analysis complete. Trade executed if applicable."

def get_ai_full_trading_signal(ticker, macro_data, fundamental_data, technical_data, sentiment_data, latest_economic_data, news_titles, peer_companies):
    """
    AI summarizes all generated insights to produce a final trading signal, target prices, and justification.
    """

    # Format economic indicators for readability
    economic_summary = "\n".join([
        f"- {key}: {value:,.2f}" if isinstance(value, (int, float)) else f"- {key}: {value}"
        for key, value in latest_economic_data.items()
    ])

    # Format news headlines
    news_bullets = "\n".join([f"- {title}" for title in news_titles])

    # Format peer comparison table
    peer_table = "\n".join([f"- {peer}" for peer in peer_companies]) if peer_companies else "No peer data available."

    # --- AI Prompt for Full Trading Analysis ---
    prompt = f"""
    You are a **quantitative financial analyst** with expertise in **macroeconomics, fundamental research, technical analysis, and behavioral finance**.
    Your role is to generate a **professional, data-driven trading signal** based on multi-factor analysis.

    --- 
    
    ## **Stock: {ticker}**
    
    --- 
    
    ## **Macroeconomic Analysis**
    {economic_summary}

    **Recent Macroeconomic News:**
    {news_bullets}

    **AI Macro Insights:**
    {macro_data}

    --- 
    
    ## **Fundamental Analysis**
    {fundamental_data}

    **Peer Company Comparison:**
    {peer_table}

    --- 
    
    ## **Technical Analysis**
    {technical_data}

    --- 
    
    ## **Sentiment & Market Psychology**
    {sentiment_data}

    --- 
    
    ## **Final AI-Generated Trading Strategy**
    **Final Trading Signal:**  
       - Should traders **BUY, SELL, or HOLD** {ticker}?  

    **Price Targets:**  
       - **BUY Target Price:** Where should traders enter?  
       - **SELL Target Price:** Where should traders take profit?  
       - **STOP-LOSS:** Where should traders exit if {ticker} moves against them?  

    **Justification:**  
       - Combine macroeconomic, fundamental, technical, and sentiment insights.
       - Identify **key risks and catalysts** for {ticker} in the next 3-6 months.
    """

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating final trading signal: {e}"
