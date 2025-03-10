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

def run_analysis(ticker):
    """Runs fundamental & technical analysis, incorporating macroeconomic trends and Reddit sentiment."""
    print(f"Running Technical Analysis for {ticker}...")
    technical_result = run_technical_analysis(ticker)

    print(f"Running Fundamental Analysis for {ticker}...")
    fundamental_result = run_fundamental_analysis(ticker)

    return {
        "technical": technical_result,
        "fundamental": fundamental_result
    }
