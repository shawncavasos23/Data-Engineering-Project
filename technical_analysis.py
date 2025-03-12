import pandas as pd  # type: ignore
import requests  # type: ignore
import numpy as np  # type: ignore
import sqlite3
from database import create_connection

API_KEY = " 67c1133a5815d0.62294566"

def get_stock_data(symbol, exchange="US", interval="daily", output_size="full"):
    """Fetch historical stock data from the API."""
    base_url = "https://eodhistoricaldata.com/api/eod/"
    url = f"{base_url}{symbol}.{exchange}"

    params = {
        "api_token": API_KEY,
        "period": interval,
        "fmt": "json",
        "order": "desc" if output_size == "full" else "asc",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return f"API error: {data.get('message', 'Unknown error')}"

        df = pd.DataFrame(data)
        required_cols = {"date", "open", "high", "low", "close", "adjusted_close", "volume"}
        if not required_cols.issubset(df.columns):
            return f"Error: Missing columns {required_cols - set(df.columns)} in API response."

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.rename(columns={"adjusted_close": "adj_close"}, inplace=True)
        df.insert(0, "ticker", symbol)

        return df

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def calculate_technical_indicators(df):
    """Calculate a variety of technical indicators."""
    
    # Moving Averages
    df["MA50"] = df["close"].rolling(window=50).mean()
    df["MA200"] = df["close"].rolling(window=200).mean()

    # RSI Calculation
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Stochastic Oscillator
    df["L14"] = df["low"].rolling(window=14).min()
    df["H14"] = df["high"].rolling(window=14).max()
    df["%K"] = 100 * (df["close"] - df["L14"]) / (df["H14"] - df["L14"])
    df["%D"] = df["%K"].rolling(window=3).mean()  # Signal line

    # Bollinger Bands
    df["SMA20"] = df["close"].rolling(window=20).mean()
    df["20-day_std"] = df["close"].rolling(window=20).std()
    df["Upper_Band"] = df["SMA20"] + (df["20-day_std"] * 2)
    df["Lower_Band"] = df["SMA20"] - (df["20-day_std"] * 2)

    # MACD
    df["EMA12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # ADX (Average Directional Index)
    df["TR"] = np.maximum(df["high"] - df["low"], 
                          np.maximum(abs(df["high"] - df["close"].shift(1)), abs(df["low"] - df["close"].shift(1))))
    df["ATR"] = df["TR"].rolling(window=14).mean()
    df["DX"] = (abs(df["high"] - df["low"]) / df["ATR"]) * 100
    df["ADX"] = df["DX"].rolling(window=14).mean()

    # On-Balance Volume (OBV)
    df["OBV"] = (np.where(df["close"] > df["close"].shift(1), df["volume"], 
                 np.where(df["close"] < df["close"].shift(1), -df["volume"], 0))).cumsum()

    # Pivot Points (Support & Resistance Levels)
    df["Pivot"] = (df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3
    df["R1"] = (2 * df["Pivot"]) - df["low"].shift(1)  # First resistance
    df["S1"] = (2 * df["Pivot"]) - df["high"].shift(1)  # First support

    return df.dropna()

def store_technical_data(df):
    """Store OHLC and technical indicators in the SQLite database."""
    if df.empty:
        print("No valid technical data to store.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technicals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume INTEGER,
                ma50 REAL,
                ma200 REAL,
                macd REAL,
                signal_line REAL,
                rsi REAL,
                upper_band REAL,
                lower_band REAL,
                adx REAL,
                obv INTEGER,
                pivot REAL,
                r1 REAL,
                s1 REAL,
                UNIQUE(ticker, date)
            );
        """)

        records = [
            (
                row["ticker"], index.strftime("%Y-%m-%d"), row["open"], row["high"], row["low"],
                row["close"], row["adj_close"], row["volume"], row["MA50"], row["MA200"],
                row["MACD"], row["Signal_Line"], row["RSI"], row["Upper_Band"], row["Lower_Band"],
                row["ADX"], row["OBV"], row["Pivot"], row["R1"], row["S1"]
            )
            for index, row in df.iterrows()
        ]

        cursor.executemany("""
            INSERT OR REPLACE INTO technicals 
            (ticker, date, open, high, low, close, adj_close, volume, ma50, ma200, 
             macd, signal_line, rsi, upper_band, lower_band, adx, obv, pivot, r1, s1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, records)

        conn.commit()

    except Exception as e:
        print(f"Database error while storing technical indicators: {e}")

    finally:
        conn.close()

def run_technical_analysis(ticker):
    """Fetch stock data, calculate indicators, and store in the database."""
    stock_data = get_stock_data(ticker)

    if isinstance(stock_data, str):
        print(stock_data)
        return

    stock_data = stock_data.sort_index()
    stock_data = calculate_technical_indicators(stock_data)

    store_technical_data(stock_data)
    
    latest_data = stock_data.tail(1).to_dict(orient="records")[0] if not stock_data.empty else "No valid data available."
    return latest_data