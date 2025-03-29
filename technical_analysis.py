import pandas as pd
import requests
import numpy as np
from sqlalchemy import text # type: ignore
from sqlalchemy.engine import Engine # type: ignore
import logging
import datetime

API_KEY = "67d7d8e193a3a4.14897669"

def get_stock_data(symbol, exchange="US", interval="daily", output_size="full"):
    """Fetch up to 1 year of historical stock data from the API (due to EODHD limits)."""
    base_url = "https://eodhistoricaldata.com/api/eod/"
    url = f"{base_url}{symbol}.{exchange}"

    # Automatically calculate 1 year back from today
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)

    params = {
        "api_token": API_KEY,
        "period": interval,
        "fmt": "json",
        "order": "desc" if output_size == "full" else "asc",
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "limit": 5000
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
    df["MA50"] = df["close"].rolling(window=50).mean()
    df["MA200"] = df["close"].rolling(window=200).mean()

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["L14"] = df["low"].rolling(window=14).min()
    df["H14"] = df["high"].rolling(window=14).max()
    df["%K"] = 100 * (df["close"] - df["L14"]) / (df["H14"] - df["L14"])
    df["%D"] = df["%K"].rolling(window=3).mean()

    df["SMA20"] = df["close"].rolling(window=20).mean()
    df["20-day_std"] = df["close"].rolling(window=20).std()
    df["Upper_Band"] = df["SMA20"] + (df["20-day_std"] * 2)
    df["Lower_Band"] = df["SMA20"] - (df["20-day_std"] * 2)

    df["EMA12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

    df["TR"] = np.maximum(df["high"] - df["low"], 
                          np.maximum(abs(df["high"] - df["close"].shift(1)), abs(df["low"] - df["close"].shift(1))))
    df["ATR"] = df["TR"].rolling(window=14).mean()
    df["DX"] = (abs(df["high"] - df["low"]) / df["ATR"]) * 100
    df["ADX"] = df["DX"].rolling(window=14).mean()

    df["OBV"] = (np.where(df["close"] > df["close"].shift(1), df["volume"], 
                 np.where(df["close"] < df["close"].shift(1), -df["volume"], 0))).cumsum()

    df["Pivot"] = (df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3
    df["R1"] = (2 * df["Pivot"]) - df["low"].shift(1)
    df["S1"] = (2 * df["Pivot"]) - df["high"].shift(1)

    return df.dropna()


def store_technical_data(df, engine: Engine):
    """Store OHLC and technical indicators in the database."""
    if df.empty:
        logging.warning("No valid technical data to store.")
        return

    records = [
        {
            "ticker": row["ticker"],
            "date": index.strftime("%Y-%m-%d"),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "adj_close": row["adj_close"],
            "volume": row["volume"],
            "ma50": row["MA50"],
            "ma200": row["MA200"],
            "macd": row["MACD"],
            "signal_line": row["Signal_Line"],
            "rsi": row["RSI"],
            "upper_band": row["Upper_Band"],
            "lower_band": row["Lower_Band"],
            "adx": row["ADX"],
            "obv": row["OBV"],
            "pivot": row["Pivot"],
            "r1": row["R1"],
            "s1": row["S1"],
        }
        for index, row in df.iterrows()
    ]

    insert_sql = text("""
        INSERT OR REPLACE INTO technicals 
        (ticker, date, open, high, low, close, adj_close, volume, ma50, ma200, 
         macd, signal_line, rsi, upper_band, lower_band, adx, obv, pivot, r1, s1)
        VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume, 
                :ma50, :ma200, :macd, :signal_line, :rsi, :upper_band, :lower_band, 
                :adx, :obv, :pivot, :r1, :s1)
    """)

    try:
        with engine.begin() as conn:
            conn.execute(insert_sql, records)
    except Exception as e:
        logging.error(f"Error storing technical data: {e}")


def run_technical_analysis(ticker, engine: Engine):
    """Fetch stock data, calculate indicators, and store in the database."""
    stock_data = get_stock_data(ticker)

    if isinstance(stock_data, str):
        logging.warning(stock_data)
        return

    stock_data = stock_data.sort_index()
    stock_data = calculate_technical_indicators(stock_data)
    store_technical_data(stock_data, engine)

    return stock_data.tail(1).to_dict(orient="records")[0] if not stock_data.empty else None
