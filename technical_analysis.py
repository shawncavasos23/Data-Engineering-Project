import pandas as pd # type: ignore
import requests # type: ignore
import numpy as np # type: ignore
from database import create_connection

API_KEY = '67c1133a5815d0.62294566'

def get_stock_data(symbol, exchange='US', interval='daily', output_size='full'):
    """Fetch historical stock data from the API."""
    base_url = "https://eodhistoricaldata.com/api/eod/"
    url = f"{base_url}{symbol}.{exchange}"

    params = {
        'api_token': API_KEY,
        'period': interval,
        'fmt': 'json',
        'order': 'desc' if output_size == 'full' else 'asc'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return f"API error: {data.get('message', 'Unknown error')}"

        df = pd.DataFrame(data)
        required_cols = {'date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume'}
        if not required_cols.issubset(df.columns):
            return f"Error: Missing columns {required_cols - set(df.columns)} in API response."

        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.rename(columns={'adjusted_close': 'adj_close'}, inplace=True)
        df.insert(0, 'ticker', symbol)
        return df

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def calculate_indicators(df):
    """Calculate technical indicators and return the modified DataFrame."""
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['20-day_std'] = df['close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA20'] + (df['20-day_std'] * 2)
    df['Lower_Band'] = df['SMA20'] - (df['20-day_std'] * 2)

    return df.dropna()  # Drop NaN values before storing in database

def store_technical_indicators(df):
    """Store calculated technical indicators into the database."""
    if df.empty:
        print("No valid technical data to store.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        for index, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO technicals 
                (ticker, date, ma50, ma200, macd, signal_line, rsi, upper_band, lower_band, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['ticker'], index.strftime("%Y-%m-%d"), row['MA50'], row['MA200'],
                row['MACD'], row['Signal_Line'], row['RSI'], row['Upper_Band'], row['Lower_Band'], row['volume']
            ))

        conn.commit()
        print("Technical indicators updated in the database.")

    except Exception as e:
        print(f"⚠ Database error while storing technical indicators: {e}")

    finally:
        conn.close()

def run_technical_analysis(ticker):
    """Fetch stock data, calculate indicators, and store in the database."""

    stock_data = get_stock_data(ticker)

    if isinstance(stock_data, str):
        print(stock_data)  # Return error message if API fails
        return

    stock_data = stock_data.sort_index()
    stock_data = calculate_indicators(stock_data)

    store_technical_indicators(stock_data)
    
    latest_data = stock_data.tail(1).to_dict(orient='records')[0] if not stock_data.empty else "No valid data available."
    return latest_data
