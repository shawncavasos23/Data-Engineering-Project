import argparse
import subprocess
import sys
from database import initialize_database
from data_pipeline import update_stock_data, run_analysis_and_execute_trade

# Default Stock Ticker
DEFAULT_TICKER = "AAPL"

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")

    parser.add_argument(
        "command",
        choices=["init", "update", "analyze", "produce", "consume", "show"],
        help="""Available commands:
        init     → Initialize the SQLite database
        update   → Fetch latest stock, macroeconomic data, news, and sentiment
        analyze  → Run AI-powered analysis and execute a trade
        produce  → Start Kafka Producer for real-time price streaming
        consume  → Start Kafka Consumer for real-time visualization
        show     → Launch stock dashboard (via Streamlit)"""
    )
    
    parser.add_argument(
        "--ticker",
        type=str,
        default=DEFAULT_TICKER,
        help=f"Stock ticker for analysis, streaming, or dashboard (Default: {DEFAULT_TICKER})"
    )

    args = parser.parse_args()

    # Initialize Database
    if args.command == "init":
        print("Initializing database...")
        initialize_database()
        print("Database initialized successfully.")

    # Update Data
    elif args.command == "update":
        print(f"Fetching latest data for {args.ticker}...")
        update_stock_data(args.ticker)
        print(f"Data updated for {args.ticker}.")

    # Run AI Analysis
    elif args.command == "analyze":
        print(f"Running AI-powered analysis for {args.ticker}...")
        result = run_analysis_and_execute_trade(args.ticker)
        print(result)

    # Start Kafka Producer (Streaming Data)
    elif args.command == "produce":
        print(f"Starting Kafka Producer for real-time stock price streaming: {args.ticker}...")
        try:
            subprocess.Popen(["python", "producer.py", args.ticker])
            print("Kafka Producer started successfully.")
        except FileNotFoundError:
            print("Error: producer.py not found. Make sure it is in the project directory.")

    # Start Kafka Consumer (Real-Time Visualization)
    elif args.command == "consume":
        print(f"Starting Kafka Consumer to plot real-time stock prices: {args.ticker}...")
        try:
            subprocess.Popen(["python", "consumer.py", args.ticker])
            print("Kafka Consumer started successfully.")
        except FileNotFoundError:
            print("Error: consumer.py not found. Make sure it is in the project directory.")

    # Launch Streamlit Dashboard
    elif args.command == "show":
        print(f"Launching stock dashboard for {args.ticker}...")
        try:
            subprocess.run(["streamlit", "run", "stock_dashboard.py", args.ticker])
        except FileNotFoundError:
            print("Error: Streamlit is not installed or stock_dashboard.py is missing.")

if __name__ == "__main__":
    main()
