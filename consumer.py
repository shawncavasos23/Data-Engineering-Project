from kafka import KafkaConsumer  # type: ignore
import json
import datetime
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.animation as animation  # type: ignore
import pandas as pd  # type: ignore
import argparse
from collections import deque

# Enable dark mode in Matplotlib
plt.style.use("dark_background")

# Command-line argument for ticker
parser = argparse.ArgumentParser(description="Kafka Stock Price Consumer")
parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g., AAPL, TSLA, MSFT)")
args = parser.parse_args()

ticker = args.ticker.upper()  # Convert to uppercase

# Kafka Consumer Setup
consumer = KafkaConsumer(
    "stock_prices",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

# Store Last 30 Data Points for Real-Time Plot (30 minutes of data)
data = deque(maxlen=30)

# Initialize Matplotlib Figure
fig, ax = plt.subplots(figsize=(10, 5))
line, = ax.plot([], [], "cyan", linewidth=2, label=f"{ticker} Price")

# Apply dark theme customizations
ax.set_facecolor("#121212")  # Dark background for the chart
fig.patch.set_facecolor("#1e1e1e")  # Dark background for the figure
ax.grid(color="gray", linestyle="dotted", linewidth=0.5)  # Grid lines

def update_plot(frame):
    """Fetch data from Kafka and update the plot."""
    try:
        message = next(consumer)
        stock_data = message.value

        # Only update the plot if the stock data matches the selected ticker
        if stock_data["ticker"] == ticker:
            timestamp = datetime.datetime.fromtimestamp(stock_data["timestamp"]).strftime("%H:%M")

            # Store new data point
            data.append((timestamp, stock_data["price"]))

            # Convert to DataFrame for plotting
            df = pd.DataFrame(data, columns=["Time", "Price"])

            # Update plot
            ax.clear()
            ax.set_facecolor("#121212")  # Ensure background remains dark
            ax.plot(df["Time"], df["Price"], color="cyan", linewidth=2, marker="o", markersize=6, markerfacecolor="red", label=f"{ticker} Price")
            
            ax.set_xlabel("Time (HH:MM)", color="white")
            ax.set_ylabel("Price", color="white")
            ax.set_title(f"Real-Time Price of {ticker}", color="white")
            ax.legend(facecolor="black", edgecolor="white", labelcolor="white")
            ax.grid(color="gray", linestyle="dotted", linewidth=0.5)
            
            ax.tick_params(axis="x", colors="white", rotation=45)
            ax.tick_params(axis="y", colors="white")

    except StopIteration:
        pass  # No new data yet

# Animate Plot with Updates Every 60 Seconds (Matching Producer)
ani = animation.FuncAnimation(fig, update_plot, interval=60000)

print(f"Listening for stock price updates for {ticker} every 60 seconds...\n")
plt.show()