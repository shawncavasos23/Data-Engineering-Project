import argparse
import subprocess
import sys
import time
import psutil  # type: ignore
import logging

from db_utils import create_sqlalchemy_engine
from database import initialize_database, get_all_tickers
from data_pipeline import add_ticker, update_stock_data, run_analysis_and_execute_trade
from cluster import find_peers
from email_utils import send_email

DEFAULT_TICKER = "AAPL"

# Setup logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("controller.log"),
        logging.StreamHandler()
    ]
)

def find_process(name):
    """
    Find a process by matching a name or keyword in its command line.
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and name in " ".join(proc.info["cmdline"]):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def kill_process(process):
    """
    Attempt to terminate a process gracefully, then forcefully if needed.
    """
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            process.kill()

def stop_all_processes():
    """
    Stop Kafka producer, consumer, and Streamlit dashboard if running.
    """
    producer_proc = find_process("producer.py")
    consumer_proc = find_process("consumer.py")

    if producer_proc:
        logging.info("Stopping Kafka Producer...")
        kill_process(producer_proc)
    else:
        logging.info("No active Producer to stop.")

    if consumer_proc:
        logging.info("Stopping Kafka Consumer...")
        kill_process(consumer_proc)
    else:
        logging.info("No active Consumer to stop.")

    stop_streamlit()

def stop_streamlit():
    """
    Stop the Streamlit dashboard if it is currently running.
    """
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            if proc.info["cmdline"] and "streamlit" in " ".join(proc.info["cmdline"]):
                logging.info("Stopping Streamlit dashboard...")
                kill_process(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def is_streamlit_running():
    """
    Check if Streamlit is currently running.
    """
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            if proc.info["cmdline"] and "streamlit" in " ".join(proc.info["cmdline"]):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def run_command(command, ticker, args, engine):
    """
    Execute a specific command for a given ticker.
    """
    if command == "init":
        initialize_database(engine, fetch_data=args.auto)

    elif command == "update":
        update_stock_data(ticker)

    elif command == "analyze":
        result = run_analysis_and_execute_trade(ticker, engine)
        logging.info(result)
        if args.email:
            send_email(subject=f"AI Trading Signal for {ticker}", body=result)

    elif command == "produce":
        if find_process(f"producer.py {ticker}"):
            logging.info(f"Producer already running for {ticker}.")
        else:
            logging.info(f"Starting Kafka Producer for {ticker}...")
            subprocess.Popen(["python", "producer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif command == "consume":
        if find_process(f"consumer.py {ticker}"):
            logging.info(f"Consumer already running for {ticker}.")
        else:
            logging.info(f"Starting Kafka Consumer for {ticker}...")
            subprocess.Popen(["python", "consumer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif command == "restart":
        logging.info(f"Restarting Kafka Producer and Consumer for {ticker}...")
        stop_all_processes()
        time.sleep(2)
        subprocess.Popen(["python", "producer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["python", "consumer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif command == "show":
        if is_streamlit_running():
            logging.info("Streamlit is already running.")
            return
        logging.info(f"Launching Streamlit dashboard for {ticker}...")
        try:
            process = subprocess.Popen(["streamlit", "run", "stock_dashboard.py", "--", ticker])
            process.wait()
        except KeyboardInterrupt:
            logging.info("Streamlit interrupted by user.")
            process.terminate()
            sys.exit(0)

    elif command == "find_peers":
        peers = find_peers(ticker, engine)
        print(f"Peers for {ticker}: {', '.join(peers)}")

    elif command == "add":
        success = add_ticker(ticker)
        if success:
            logging.info(f"Ticker {ticker} added successfully.")
        else:
            logging.error(f"Failed to add ticker {ticker}.")

    elif command == "status":
        logging.info("Checking running processes...")
        for name in ["producer.py", "consumer.py", "streamlit"]:
            proc = find_process(name)
            if proc:
                logging.info(f"{name} is running (PID: {proc.pid})")
            else:
                logging.info(f"{name} is not running.")

    elif command == "stop":
        stop_all_processes()

    elif command == "list_tickers":
        tickers = sorted(get_all_tickers(engine))
        if tickers:
            print("\nAvailable tickers:")
            for i in range(0, len(tickers), 10):
                print(", ".join(tickers[i:i+10]))
            print(f"\nTotal: {len(tickers)} tickers\n")
        else:
            logging.warning("No tickers found in the database.")

def main():
    engine = create_sqlalchemy_engine()

    parser = argparse.ArgumentParser(description="Alpha Fusion: Trading Dashboard Controller")
    parser.add_argument(
        "command",
        choices=[
            "init", "update", "analyze", "produce", "consume",
            "stop", "restart", "show", "find_peers", "add", "status", "list_tickers"
        ],
        help="Run a specific pipeline command"
    )
    parser.add_argument("--ticker", type=str, help="Stock ticker(s), comma-separated (e.g., AAPL,MSFT)")
    parser.add_argument("--auto", action="store_true", help="Run in auto mode without prompts")
    parser.add_argument("--email", action="store_true", help="Send trading signal via email (analyze only)")
    parser.add_argument("--debug", action="store_true", help="Enable debug-level logging")
    parser.add_argument("--version", action="version", version="Alpha Fusion CLI v1.0")
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    # Adjust logging level if debug flag is set
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse tickers safely
    tickers = [t.strip().upper() for t in (args.ticker or DEFAULT_TICKER).split(",")]

    # Commands safe to apply across multiple tickers
    multi_ticker_cmds = {"update", "analyze", "add", "find_peers"}

    # Single-ticker or general commands
    single_ticker_cmds = {
        "produce", "consume", "restart", "show", "stop", "status", "init", "list_tickers"
    }

    if args.command in multi_ticker_cmds:
        for ticker in tickers:
            run_command(args.command, ticker, args, engine)
    elif args.command in single_ticker_cmds:
        run_command(args.command, tickers[0], args, engine)
    else:
        logging.error("Unknown command.")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
