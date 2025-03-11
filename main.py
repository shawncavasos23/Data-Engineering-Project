import argparse
from database import initialize_database
from data_pipeline import update_database, run_analysis_and_send_email

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")
    parser.add_argument("command", choices=["init", "update", "analyze"], help="Command to execute")
    parser.add_argument("--ticker", type=str, help="Stock ticker for analysis (e.g., AAPL)")

    args = parser.parse_args()

    if args.command == "init":
        print("Initializing database...")
        initialize_database()
        print("Database initialized successfully!")

    elif args.command == "update":
        print("Fetching latest stock, macroeconomic data, news, and Reddit sentiment...")
        update_database()
        print("All data updated!")

    elif args.command == "analyze":
        if not args.ticker:
            print("Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"Running analysis for {args.ticker} and sending email...")
        run_analysis_and_send_email(args.ticker)
        print("Analysis complete. Email sent.")

if __name__ == "__main__":
    main()
