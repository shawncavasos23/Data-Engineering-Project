from data_pipeline import update_stock_data, run_analysis_and_execute_trade
from db_utils import create_sqlalchemy_engine
from email_utils import send_email

import logging
import os
from datetime import datetime

# === Logging Setup ===

# Create a logs folder if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate a timestamped log file name
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"logs/alpha_fusion_{timestamp}.log"

# Configure logging to file + console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# === Scheduled Task Logic ===

def run_all():
    engine = create_sqlalchemy_engine()

    # List of tickers to monitor and analyze
    tickers = ["AAPL", "MSFT", "TSLA", "NVDA"]

    for ticker in tickers:
        try:
            logging.info(f"Updating data for {ticker}...")
            update_stock_data(ticker)

            result = run_analysis_and_execute_trade(ticker)
            logging.info(f"{ticker} -> {result}")

        except Exception as e:
            logging.warning(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    run_all()

    # === Email the log file after completion ===
    send_email(
        subject="Alpha Fusion Daily Log",
        body=f"Attached is the log file for the Alpha Fusion run on {timestamp}.",
        attachment_path=log_file
    )