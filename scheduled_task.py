from data_pipeline import update_stock_data, run_analysis_and_execute_trade
from db_utils import create_sqlalchemy_engine
import logging

logging.basicConfig(level=logging.INFO)

def run_all():
    engine = create_sqlalchemy_engine()

    # Add the tickers we want to monitor
    tickers = ["AAPL", "MSFT", "TSLA", "NVDA"]

    for ticker in tickers:
        try:
            update_stock_data(ticker)
            result = run_analysis_and_execute_trade(ticker)
            logging.info(f"{ticker} -> {result}")
        except Exception as e:
            logging.warning(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    run_all()
