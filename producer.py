from kafka import KafkaProducer # type: ignore
import yfinance as yf # type: ignore
import json
import time

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Function to fetch stock price
def fetch_stock_price(ticker="AAPL"):
    stock = yf.Ticker(ticker)
    try:
        # Use "1d" for the last day's data and "1m" interval for minute-by-minute updates
        history = stock.history(period="1d", interval="1m")  
        if not history.empty:
            latest_price = history["Close"].iloc[-1]  # Get the most recent closing price
            return latest_price
        else:
            print(f"⚠️ No data found for {ticker}. Check the ticker symbol.")
            return None
    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")
        return None

# Send real-time stock prices to Kafka
ticker = "AAPL"  # Change to any stock

while True:
    price = fetch_stock_price(ticker)
    
    if price is not None:
        message = {"ticker": ticker, "price": price, "timestamp": time.time()}
        producer.send("stock_prices", message)
        print(f"✅ Sent: {message}")
    else:
        print("⚠️ Skipping sending due to missing price data.")

    time.sleep(5)  # Fetch price every 5 seconds
