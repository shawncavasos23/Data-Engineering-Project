from kafka import KafkaProducer  # type: ignore
import yfinance as yf  # type: ignore
import json
import time
import argparse

# Kafka Producer Setup
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# Function to Fetch Stock Price
def fetch_stock_price(ticker):
    stock = yf.Ticker(ticker)
    try:
        history = stock.history(period="1d", interval="1m")  # 1-min interval
        if not history.empty:
            latest_price = history["Close"].iloc[-1]
            return latest_price
        else:
            print(f"No data found for {ticker}. Check the ticker symbol.")
            return None
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Command-line argument for ticker
parser = argparse.ArgumentParser(description="Kafka Stock Price Producer")
parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g., AAPL, TSLA, MSFT)")
args = parser.parse_args()

ticker = args.ticker.upper()  # Convert to uppercase

while True:
    price = fetch_stock_price(ticker)

    if price is not None:
        message = {"ticker": ticker, "price": price, "timestamp": time.time()}
        producer.send("stock_prices", message)
        print(f"Sent: {message}")
    else:
        print("Skipping sending due to missing price data.")

    time.sleep(60)
