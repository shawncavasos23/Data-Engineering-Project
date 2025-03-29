from data_pipeline import update_stock_data, run_analysis_and_execute_trade
from db_utils import create_sqlalchemy_engine
from email_utils import send_email

import logging
import os
from datetime import datetime

# === Logging Setup ===

# Configure logging to only log to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()  # Only console logging
    ]
)

# === Scheduled Task Logic ===

def run_all():
    engine = create_sqlalchemy_engine()

    # List of tickers to monitor and analyze
    tickers = ["AAPL"]

    for ticker in tickers:
        try:
            update_stock_data(ticker)
            result = run_analysis_and_execute_trade(ticker, engine)
    

        except Exception as e:
            logging.warning(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    run_all()

