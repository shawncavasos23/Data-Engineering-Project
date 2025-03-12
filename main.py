import argparse
import subprocess
import time
import psutil  # type: ignore
from database import initialize_database
from data_pipeline import update_stock_data, run_analysis_and_execute_trade

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
            print(f"Terminating process: {process.info['pid']} ({process.info['name']})")
            process.terminate()
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            print("Process not found.")
        except psutil.TimeoutExpired:
            print(f"Process {process.info['pid']} did not terminate in time, forcing kill.")
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

def main():
    parser = argparse.ArgumentParser(description="Trading Dashboard Controller")

    parser.add_argument(
        "command",
        choices=["init", "update", "analyze", "produce", "consume", "stop", "restart", "show"],
        help="""Available commands:
        init     → Initialize the SQLite database
        update   → Fetch latest stock, macroeconomic data, news, and sentiment
        analyze  → Run AI-powered analysis and execute a trade
        produce  → Start Kafka Producer for real-time price streaming
        consume  → Start Kafka Consumer for real-time visualization
        stop     → Stop both Producer and Consumer
        restart  → Restart both Producer and Consumer
        show     → Launch stock dashboard (via Streamlit)"""
    )
    
    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker for analysis, streaming, or dashboard (e.g., AAPL)"
    )

    args = parser.parse_args()

    # Initialize Database
    if args.command == "init":
        print("Initializing database...")
        initialize_database()
        print("Database initialized successfully.")

    # Update Data
    elif args.command == "update":
        ticker = args.ticker or DEFAULT_TICKER
        print(f"Fetching latest data for {ticker}...")
        update_stock_data(ticker)
        print(f"Data updated for {ticker}.")

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
        print(f"Launching stock dashboard for {ticker}...")

        try:
            subprocess.run(["streamlit", "run", "stock_dashboard.py", "--", ticker])
        except FileNotFoundError:
            print("Error: Streamlit is not installed or stock_dashboard.py is missing.")

if __name__ == "__main__":
    main()
