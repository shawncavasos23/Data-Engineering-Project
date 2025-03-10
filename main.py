import argparse
import subprocess
from database import initialize_database
from data_pipeline import update_database
from technical_analysis import run as run_technical
from fundamental_analysis import run as run_fundamental

def run_dashboard():
    """Start the Dash web app."""
    subprocess.run(["python", "app.py"])

def main():
    """Main entry point for the trading system."""
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")
    parser.add_argument("command", choices=["init", "update", "run", "tech", "fund"], help="Command to execute")
    parser.add_argument("--ticker", type=str, help="Ticker symbol (for 'tech' and 'fund' commands)")

    args = parser.parse_args()

    if args.command == "init":
        print("🔧 Initializing database...")
        initialize_database()
        print("✅ Database initialized successfully!")

    elif args.command == "update":
        print("📊 Fetching latest stock data and indicators...")
        update_database()
        print("✅ Database updated with latest financial data!")

    elif args.command == "tech":
        if args.ticker:
            print(f"📉 Running Technical Analysis for {args.ticker}...")
            result = run_technical(args.ticker)
            print("✅ Technical Indicators Updated!")
            print(result)
        else:
            print("⚠ Please specify a ticker using --ticker (e.g., python main.py tech --ticker AAPL)")

    elif args.command == "fund":
        if args.ticker:
            print(f"🏦 Running Fundamental Analysis for {args.ticker}...")
            result = run_fundamental(args.ticker)
            print("✅ Fundamental Data Updated!")
            print(result)
        else:
            print("⚠ Please specify a ticker using --ticker (e.g., python main.py fund --ticker AAPL)")

    elif args.command == "run":
        print("🚀 Launching Trading Dashboard...")
        run_dashboard()

if __name__ == "__main__":
    main()
