import argparse
from database import initialize_database
from data_pipeline import update_database, run_analysis
from macroeconomic_analysis import get_macro_trends, compare_macro_indicators
from news_analysis import get_latest_news
from reddit_analysis import analyze_reddit_sentiment

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")
    parser.add_argument("command", choices=["init", "update", "analyze", "show_macro", "compare_macro", "macro_impact", "show_news", "show_reddit"], help="Command to execute")
    parser.add_argument("--ticker", type=str, help="Stock ticker for analysis (e.g., AAPL)")
    parser.add_argument("--indicator1", type=str, help="First macroeconomic indicator for comparison (e.g., UNRATE)")
    parser.add_argument("--indicator2", type=str, help="Second macroeconomic indicator for comparison (e.g., FEDFUNDS)")

    args = parser.parse_args()

    if args.command == "init":
        print("🔧 Initializing database...")
        initialize_database()
        print("✅ Database initialized successfully!")

    elif args.command == "update":
        print("📊 Fetching latest stock, macroeconomic data, news, and Reddit sentiment...")
        update_database()
        print("✅ All data updated!")

    elif args.command == "analyze":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"📈 Running analysis for {args.ticker}...")
        result = run_analysis(args.ticker)
        print(result)

    elif args.command == "show_macro":
        print("📊 Displaying latest macroeconomic trends...")
        get_macro_trends()

    elif args.command == "compare_macro":
        if not args.indicator1 or not args.indicator2:
            print("⚠ Please specify two indicators using --indicator1 <INDICATOR> --indicator2 <INDICATOR>")
            return
        
        print(f"📈 Comparing {args.indicator1} and {args.indicator2}...")
        compare_macro_indicators(args.indicator1, args.indicator2)

    elif args.command == "show_news":
        print("📰 Fetching latest news headlines...")
        get_latest_news()

    elif args.command == "show_reddit":
        if not args.ticker:
            print("⚠ Please specify a stock ticker using --ticker <TICKER>")
            return
        
        print(f"📢 Analyzing Reddit sentiment for {args.ticker}...")
        analyze_reddit_sentiment(args.ticker)

if __name__ == "__main__":
    main()
