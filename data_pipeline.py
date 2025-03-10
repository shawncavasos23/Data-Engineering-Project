import sys
import os

# Ensure Python can find local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fundamental_analysis import run as run_fundamental
from technical_analysis import run as run_technical
from database import create_connection

def update_database():
    """Fetches and updates the database with technical and fundamental data."""
    tickers = ["CVX"]

    for ticker in tickers:
        print(f"📉 Running Technical Analysis for {ticker}...")
        run_technical(ticker)

        print(f"🏦 Running Fundamental Analysis for {ticker}...")
        result = run_fundamental(ticker)
        print(result)

    print("✅ Database updated with latest financial data!")
