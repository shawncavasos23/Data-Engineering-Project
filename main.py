import argparse
import subprocess
from database import initialize_database
from data_pipeline import update_stock_data, run_analysis_and_execute_trade

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")
    parser.add_argument(
        "command",
        choices=["init", "update", "analyze", "produce", "consume", "show"],
        help="Command to execute"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker for analysis, streaming, or dashboard (e.g., AAPL)"
    )

    args = parser.parse_args()

    if args.command == "init":
        print("Initializing database...")
        initialize_database()
        print("Database initialized successfully!")

    elif args.command == "update":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"Fetching latest stock, macroeconomic data, news, and Reddit sentiment for {args.ticker}...")
        update_stock_data(args.ticker)
        print(f"Data updated successfully for {args.ticker}.")

    elif args.command == "analyze":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"Running AI-powered analysis for {args.ticker}...")
        result = run_analysis_and_execute_trade(args.ticker)
        print(result)

    elif args.command == "produce":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"Starting Kafka Producer for real-time stock price streaming: {args.ticker}...")
        subprocess.run(["python", "producer.py", args.ticker])

    elif args.command == "consume":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"Starting Kafka Consumer to plot real-time stock prices: {args.ticker}...")
        subprocess.run(["python", "consumer.py", args.ticker])

    elif args.command == "show":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return

        print(f"Launching stock dashboard for {args.ticker}...")
        subprocess.run(["streamlit", "run", "stock_dashboard.py", args.ticker])

if __name__ == "__main__":
    main()
