import argparse
from database import initialize_database
from data_pipeline import update_database, run_analysis

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")
    parser.add_argument("command", choices=["init", "update", "analyze"], help="Command to execute")
    parser.add_argument("--ticker", type=str, help="Stock ticker for analysis (e.g., AAPL)")
    parser.add_argument("--all", action="store_true", help="Analyze all tickers in the database")

    args = parser.parse_args()

    if args.command == "init":
        print("Initializing database...")
        initialize_database()
        print("Database initialized successfully.")

    elif args.command == "update":
        print("Fetching latest stock, macroeconomic data, news, and Reddit sentiment...")
        try:
            update_database()
            print("All data updated successfully.")
        except Exception as e:
            print(f"Error updating database: {e}")

    elif args.command == "analyze":
        if args.all:
            print("Running AI analysis for all tickers in the database...")
            try:
                from database import get_all_tickers  # Import function to get all tickers
                tickers = get_all_tickers()
                if not tickers:
                    print("No tickers found in the database.")
                    return
                for ticker in tickers:
                    print(f"\nRunning AI-powered analysis for {ticker}...")
                    result = run_analysis(ticker)
                    print(result)
            except Exception as e:
                print(f"Error during analysis: {e}")

        elif args.ticker:
            print(f"Running AI-powered analysis for {args.ticker}...")
            try:
                result = run_analysis(args.ticker)
                print(result)
            except Exception as e:
                print(f"Error during analysis: {e}")

        else:
            print("Please specify a stock ticker using --ticker <TICKER> or use --all to analyze all tickers.")

if __name__ == "__main__":
    main()
