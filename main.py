import argparse
import subprocess
import sys
import os
import signal
import time
import psutil # type: ignore
import atexit
from database import initialize_database
from data_pipeline import add_ticker, update_stock_data, run_analysis_and_execute_trade
from cluster import find_peers

# Default Stock Ticker
DEFAULT_TICKER = "AAPL"

def find_process(name):
    """Find a running process by name and return its PID."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and name in " ".join(proc.info["cmdline"]):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def kill_process(process):
    """Kill a process safely."""
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            process.kill()

def stop_all_processes():
    """Stop Kafka Producer and Consumer if they are running."""
    producer_proc = find_process("producer.py")
    consumer_proc = find_process("consumer.py")

    if producer_proc:
        print("Stopping Kafka Producer...")
        kill_process(producer_proc)
    else:
        print("No active Producer to stop.")

    if consumer_proc:
        print("Stopping Kafka Consumer...")
        kill_process(consumer_proc)
    else:
        print("No active Consumer to stop.")

def is_streamlit_running():
    """Check if Streamlit is already running to prevent duplicate processes."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and "streamlit" in " ".join(proc.info["cmdline"]):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")

    parser.add_argument(
        "command",
        choices=["init", "update", "analyze", "produce", "consume", "stop", "restart", "show", "find_peers", "add"],
        help="""Available commands:
        init     → Initialize the SQLite database
        update   → Fetch latest stock, macroeconomic data, news, and sentiment
        analyze  → Run AI-powered analysis and execute a trade
        produce  → Start Kafka Producer for real-time price streaming
        consume  → Start Kafka Consumer for real-time visualization
        stop     → Stop both Producer and Consumer
        restart  → Restart both Producer and Consumer
        show     → Launch stock dashboard (via Streamlit)
        find_peers → Find similar stocks using clustering
        add      → Add a new stock ticker to the database"""
    )
    
    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker for analysis, streaming, or dashboard (e.g., AAPL)"
    )

    args = parser.parse_args()

    # Initialize Database
    if args.command == "init":
        initialize_database()

    # Update Data
    elif args.command == "update":
        ticker = args.ticker or DEFAULT_TICKER
        update_stock_data(ticker)

    # Run AI Analysis
    elif args.command == "analyze":
        ticker = args.ticker or DEFAULT_TICKER
        print(f"Running AI-powered analysis for {ticker}...")
        result = run_analysis_and_execute_trade(ticker)
        print(result)

    # Start Kafka Producer (Streaming Data)
    elif args.command == "produce":
        ticker = args.ticker or DEFAULT_TICKER

        if find_process("producer.py"):
            print("Producer is already running.")
        else:
            print(f"Starting Kafka Producer for {ticker}...")
            subprocess.Popen(["python", "producer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Kafka Producer started successfully.")

    # Start Kafka Consumer (Real-Time Visualization)
    elif args.command == "consume":
        ticker = args.ticker or DEFAULT_TICKER

        if find_process("consumer.py"):
            print("Consumer is already running.")
        else:
            print(f"Starting Kafka Consumer for {ticker}...")
            subprocess.Popen(["python", "consumer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Kafka Consumer started successfully.")

    # Stop Kafka Producer & Consumer
    elif args.command == "stop":
        stop_all_processes()

    # Restart Kafka Producer & Consumer
    elif args.command == "restart":
        print("Restarting Kafka Producer and Consumer...")
        stop_all_processes()
        time.sleep(2)

        ticker = args.ticker or DEFAULT_TICKER
        print(f"Restarting Kafka Producer and Consumer for {ticker}...")
        subprocess.Popen(["python", "producer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["python", "consumer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Kafka Producer & Consumer restarted successfully.")

    # Launch Streamlit Dashboard
    elif args.command == "show":
        ticker = args.ticker or DEFAULT_TICKER

        if is_streamlit_running():
            print("Streamlit is already running.")
            return

        print(f"Launching stock dashboard for {ticker}...")

        try:
            process = subprocess.Popen(["streamlit", "run", "stock_dashboard.py", "--", ticker])

            # Gracefully handle Ctrl+C
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\nStock dashboard interrupted...")
                process.terminate()
                sys.exit(0)

        except FileNotFoundError:
            print("Error: Streamlit is not installed or stock_dashboard.py is missing.")

    elif args.command == "find_peers":
        ticker = args.ticker or DEFAULT_TICKER
        peers = find_peers(ticker)
        print(f"Peers for {ticker}: {', '.join(peers)}")

    # Add a new stock ticker to the database
    elif args.command == "add":
        if not args.ticker:
            print("Error: You must specify a ticker using --ticker.")
            sys.exit(1)

        ticker = args.ticker.upper()
        success = add_ticker(ticker)
        if success:
            print(f"Ticker {ticker} added successfully.")
       


if __name__ == "__main__":
    main()

