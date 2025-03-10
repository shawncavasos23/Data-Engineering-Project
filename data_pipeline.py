from macroeconomic_analysis import fetch_economic_data
from news_analysis import fetch_news
from reddit_analysis import run_reddit_analysis
from technical_analysis import run_technical_analysis
from fundamental_analysis import run_fundamental_analysis

def update_database():
    """Updates stock, macroeconomic, news, and Reddit/Google Trends data."""
    print("Fetching latest macroeconomic data...")
    fetch_economic_data()
    
    print("Fetching latest news headlines...")
    fetch_news()
    
    print("Fetching Reddit mentions and Google Trends...")
    run_reddit_analysis("AAPL")  # Example with AAPL

    print("All data updated in the database.")

import openai
import sqlite3
import pandas as pd
from technical_analysis import run as run_technical
from fundamental_analysis import run as run_fundamental
from macroeconomic_analysis import get_macro_trends
from news_analysis import get_latest_news
from reddit_analysis import analyze_reddit_sentiment

# OpenAI API Key (Replace with your actual API key)
api_key = "your_openai_api_key"

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

def run_analysis(ticker):
    """Performs AI-powered trading analysis using all available financial data sources."""

    print(f"Analyzing {ticker}...")

    # 🔹 Technical Analysis
    technicals = run_technical(ticker)

    # 🔹 Fundamental Analysis
    fundamentals = run_fundamental(ticker)

    # 🔹 Macroeconomic Trends
    macro_trends = get_macro_trends()

    # 🔹 News Analysis
    latest_news = get_latest_news()

    # 🔹 Reddit Sentiment Analysis
    sentiment_analysis = analyze_reddit_sentiment(ticker)

    # 🔹 AI Trading Signal
    ai_final_trading_signal = get_ai_full_trading_signal(
        ticker,
        macro_trends,
        fundamentals,
        technicals,
        sentiment_analysis,
        latest_news["economic_data"],  # Latest macroeconomic indicators
        latest_news["news_titles"],  # Top recent news headlines
        fundamentals["peer_companies"]  # Peer comparison data
    )

    print("\n**AI-Generated Final Trading Signal & Price Targets:**")
    print(ai_final_trading_signal)

    return "\nAI Analysis Complete!"

