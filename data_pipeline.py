import openai  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
from technical_analysis import run_technical_analysis
from fundamental_analysis import run_fundamental_analysis
from macroeconomic_analysis import fetch_economic_data
from news_analysis import fetch_news
from reddit_analysis import run_reddit_analysis
from database import create_connection

# Securely load OpenAI API Key
api_key = "your_openai_api_key"

def update_database():
    """
    Fetches the latest stock, macroeconomic indicators, news, and sentiment data, and updates the database.
    """
    print("Fetching latest stock, macroeconomic data, news, and Reddit sentiment...")

    # Connect to SQLite database
    conn = create_connection()
    cursor = conn.cursor()

    # 🔹 **Step 1: Get List of Tracked Tickers**
    cursor.execute("SELECT DISTINCT ticker FROM fundamentals")
    tracked_tickers = [row[0] for row in cursor.fetchall()]

    if not tracked_tickers:
        print("No tickers found in the database. Please initialize with stock data first.")
        return

    # 🔹 **Step 2: Update Technical & Fundamental Data for Each Ticker**
    for ticker in tracked_tickers:
        print(f"Running Technical Analysis for {ticker}...")
        run_technical_analysis(ticker)

        print(f"Running Fundamental Analysis for {ticker}...")
        run_fundamental_analysis(ticker)

        print(f"Running Reddit Sentiment & Google Trends Analysis for {ticker}...")
        run_reddit_analysis(ticker)

    # 🔹 **Step 3: Update Macroeconomic Data**
    print("Fetching latest macroeconomic data...")
    macro_data = fetch_economic_data()

    # 🔹 **Step 4: Update Latest News Data**
    print("Fetching latest news headlines...")
    news_data = fetch_news()

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("All data updated in the database.")

def run_analysis(ticker):
    """
    Performs AI-powered trading analysis using all available financial data sources.
    """
    print(f"**Running AI-powered analysis for {ticker}...**")

    # 🔹 Fetch Latest Data from Each Analysis
    technicals = run_technical_analysis(ticker)
    fundamentals = run_fundamental_analysis(ticker)
    macro_trends = fetch_economic_data()
    latest_news = fetch_news()
    sentiment_analysis = run_reddit_analysis(ticker)

    # 🔹 Generate AI Final Trading Signal
    ai_final_trading_signal = get_ai_full_trading_signal(
        ticker,
        macro_trends,
        fundamentals,
        technicals,
        sentiment_analysis,
        latest_news.get("economic_data", {}),  # Latest macroeconomic indicators
        latest_news.get("news_titles", []),  # Top recent news headlines
        fundamentals.get("peer_companies", [])  # Peer comparison data
    )

    print("\n**AI-Generated Final Trading Signal & Price Targets:**")
    print(ai_final_trading_signal)

    return "\n**AI Analysis Complete!**"

def get_ai_full_trading_signal(ticker, macro_data, fundamental_data, technical_data, sentiment_data, latest_economic_data, news_titles, peer_companies):
    """
    AI summarizes all generated insights to produce a final trading signal, target prices, and justification.
    """

    # Convert Pandas Series to Dictionary (if applicable)
    if isinstance(latest_economic_data, pd.Series):
        latest_economic_data = latest_economic_data.to_dict()

    # Format economic indicators for readability
    economic_summary = "\n".join([
        f"- {key}: {value:,.2f}" if isinstance(value, (int, float)) else f"- {key}: {value}"
        for key, value in latest_economic_data.items()
    ])

    # Format news headlines
    news_bullets = "\n".join([f"- {title}" for title in news_titles])

    # Format peer comparison table
    peer_table = peer_companies.to_markdown(index=False) if isinstance(peer_companies, pd.DataFrame) and not peer_companies.empty else "No peer data available."

    # --- AI Prompt for Full Trading Analysis ---
    prompt = f"""
    You are a **quantitative financial analyst** with expertise in **macroeconomics, fundamental research, technical analysis, and behavioral finance**.
    Your role is to generate a **professional, data-driven trading signal** based on multi-factor analysis.

    --- 
    
    ## **Stock: {ticker}**
    
    --- 
    
    ## **Macroeconomic Analysis**
    - **Economic Overview**: How do current macroeconomic conditions affect {ticker}?
    - **Interest rates & inflation**: What impact do central bank policies have?
    - **Sector-Specific Trends**: How does the {ticker} sector perform under these conditions?
    - **GDP Growth & Consumer Trends**: What are the broader economic implications?
    
    **Macroeconomic Data:**
    {economic_summary}

    **Recent Macroeconomic News:**
    {news_bullets}

    **AI Macro Insights:**
    {macro_data}

    --- 
    
    ## **Fundamental Analysis**
    - **Valuation Metrics**: P/E ratio, P/B ratio, P/S ratio, EV/EBITDA
    - **Growth Metrics**: Revenue trends, earnings growth, future projections
    - **Profitability Metrics**: Gross margin, return on equity (ROE), return on assets (ROA)
    - **Financial Stability**: Debt-to-equity, free cash flow, institutional ownership
    - **Competitive Moat**: Does {ticker} have an advantage over competitors?

    **Company Fundamentals:**
    {fundamental_data}

    **Peer Company Comparison:**
    {peer_table}

    --- 
    
    ## **Technical Analysis**
    - **Trend Strength**: Is {ticker} in an uptrend, downtrend, or range-bound?
    - **Momentum Indicators**: RSI (Relative Strength Index), MACD (Moving Average Convergence Divergence)
    - **Volatility & Bollinger Bands**: Key resistance and support levels
    - **Moving Averages**: 50-day and 200-day MA
    - **Trading Volume & Institutional Activity**: Any major unusual buying or selling?

    **Technical Indicators:**
    {technical_data}

    --- 
    
    ## **Sentiment & Market Psychology**
    - **Retail Investor Sentiment**: How is {ticker} being discussed on social media?
    - **Options Market Trends**: Are traders positioning for bullish or bearish moves?
    - **Financial News Sentiment**: Are analysts upgrading or downgrading?
    - **Insider Transactions**: Are executives buying or selling shares?

    **Reddit & Market Sentiment:**
    {sentiment_data}

    --- 
    
    ## **Final AI-Generated Trading Strategy**
    **Final Trading Signal:**  
       - Should traders **BUY, SELL, or HOLD** {ticker}?  
       - Confidence level: **High, Medium, or Low**?  

    **Price Targets:**  
       - **BUY Target Price:** Where should traders enter?  
       - **SELL Target Price:** Where should traders take profit?  
       - **STOP-LOSS:** Where should traders exit if {ticker} moves against them?  

    **Justification:**  
       - Combine macroeconomic, fundamental, technical, and sentiment insights.
       - Identify **key risks and catalysts** for {ticker} in the next 3-6 months.
    
    **Provide a structured, professional response suitable for institutional investors.**
    """

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional financial strategist providing detailed, multi-factor trading analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating final trading signal: {e}"
