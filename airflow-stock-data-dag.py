from airflow import DAG # type: ignore
from airflow.operators.python import PythonOperator # type: ignore
from datetime import datetime, timedelta
import sqlite3

# Import  existing functions
from technical_analysis import run_technical_analysis
from fundamental_analysis import get_fundamental_data
from macroeconomic_analysis import fetch_economic_data
from news_analysis import fetch_news
from reddit_analysis import run_reddit_analysis

# Database connection helper
def create_connection():
    return sqlite3.connect("your_database.db")

# Function to check if the ticker exists in the database
def check_ticker(ticker):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fundamentals WHERE ticker = ?", (ticker,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    if not exists:
        raise ValueError(f"{ticker} not found in database. Please add it before updating.")

# Function to wrap each task
def run_task(func, ticker):
    func(ticker)

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 14),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
with DAG(
    dag_id="update_stock_data_dag",
    default_args=default_args,
    schedule_interval="@daily",  # Runs daily, modify as needed
    catchup=False
) as dag:

    ticker = "AAPL"  # You can make this dynamic later

    # Task 1: Check if ticker exists
    check_ticker_task = PythonOperator(
        task_id='check_ticker',
        python_callable=check_ticker,
        op_kwargs={'ticker': ticker}
    )

    # Task 2: Run technical analysis
    technical_analysis_task = PythonOperator(
        task_id='run_technical_analysis',
        python_callable=run_task,
        op_kwargs={'func': run_technical_analysis, 'ticker': ticker}
    )

    # Task 3: Fetch fundamental data
    fundamental_data_task = PythonOperator(
        task_id='get_fundamental_data',
        python_callable=run_task,
        op_kwargs={'func': get_fundamental_data, 'ticker': ticker}
    )

    # Task 4: Run Reddit sentiment analysis
    reddit_analysis_task = PythonOperator(
        task_id='run_reddit_analysis',
        python_callable=run_task,
        op_kwargs={'func': run_reddit_analysis, 'ticker': ticker}
    )

    # Task 5: Fetch news data
    news_task = PythonOperator(
        task_id='fetch_news',
        python_callable=run_task,
        op_kwargs={'func': fetch_news, 'ticker': ticker}
    )

    # Task 6: Fetch macroeconomic data
    macroeconomic_task = PythonOperator(
        task_id='fetch_economic_data',
        python_callable=fetch_economic_data  # No ticker needed
    )

    # Define Task Dependencies
    check_ticker_task >> [technical_analysis_task, fundamental_data_task]
    fundamental_data_task >> [reddit_analysis_task, news_task]
    [reddit_analysis_task, news_task] >> macroeconomic_task
