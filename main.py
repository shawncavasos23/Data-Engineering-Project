import argparse
import subprocess
import sys
import time
import psutil  # type: ignore
import logging

from db_utils import create_sqlalchemy_engine
from database import initialize_database
from data_pipeline import add_ticker, update_stock_data, run_analysis_and_execute_trade
from cluster import find_peers
from email_utils import send_email

DEFAULT_TICKER = "AAPL"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def find_process(name):
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and name in " ".join(proc.info["cmdline"]):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None


def kill_process(process):
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            process.kill()


def stop_all_processes():
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


def is_streamlit_running():
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
        help="Run a specific pipeline command"
    )
    parser.add_argument("--ticker", type=str, help="Stock ticker (e.g., AAPL)")
    parser.add_argument("--auto", action="store_true", help="Run in auto mode without prompts")
    parser.add_argument("--email", action="store_true", help="Send trading signal via email (analyze only)")
    args = parser.parse_args()

    ticker = args.ticker or DEFAULT_TICKER

    if args.command == "init":
        engine = create_sqlalchemy_engine()
        initialize_database(engine, fetch_data=args.auto)

    elif args.command == "update":
        update_stock_data(ticker)

    elif args.command == "analyze":
        result = run_analysis_and_execute_trade(ticker)
        logging.info(result)
        if args.email:
            send_email(subject=f"AI Trading Signal for {ticker}", body=result)

    elif args.command == "produce":
        if find_process(f"producer.py {ticker}"):
            logging.info(f"Producer already running for {ticker}.")
        else:
            logging.info(f"Starting Kafka Producer for {ticker}...")
            subprocess.Popen(["python", "producer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif args.command == "consume":
        if find_process(f"consumer.py {ticker}"):
            logging.info(f"Consumer already running for {ticker}.")
        else:
            logging.info(f"Starting Kafka Consumer for {ticker}...")
            subprocess.Popen(["python", "consumer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif args.command == "stop":
        stop_all_processes()

    elif args.command == "restart":
        logging.info(f"Restarting Kafka Producer and Consumer for {ticker}...")
        stop_all_processes()
        time.sleep(2)
        subprocess.Popen(["python", "producer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["python", "consumer.py", ticker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif args.command == "show":
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

    elif args.command == "find_peers":
        engine = create_sqlalchemy_engine()
        peers = find_peers(ticker, engine)
        
        print(f"Peers for {ticker}: {', '.join(peers)}")

    elif args.command == "add":
        if not ticker:
            logging.error("You must specify a ticker using --ticker.")
            sys.exit(1)
        success = add_ticker(ticker)
        if success:
            logging.info(f"Ticker {ticker} added successfully.")
        else:
            logging.error(f"Failed to add ticker {ticker}.")


if __name__ == "__main__":
    main()
