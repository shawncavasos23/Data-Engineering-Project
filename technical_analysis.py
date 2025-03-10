def run():
    import requests
    import pandas as pd
    import mplfinance as mpf
    import numpy as np
    import matplotlib.pyplot as plt

    API_KEY = '67c1133a5815d0.62294566'

    def get_stock_data(symbol, exchange='US', interval='daily', output_size='full'):
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

    # Fetch stock data
    ticker = "AAPL"
    stock_data = get_stock_data(ticker, interval='daily')

    if isinstance(stock_data, str):
        return stock_data  # Return error message if API fails

    stock_data = stock_data.sort_index()

    # 📌 **Technical Indicator Calculations**
    def calculate_indicators(df):
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

        return df

    stock_data = calculate_indicators(stock_data)

    # 📌 **Candlestick Chart**
    if len(stock_data) >= 200:
        mpf.plot(
            stock_data.tail(200),
            type='candle',
            volume=True,
            style='yahoo',
            figsize=(14, 7),
            title=f"{ticker} Stock Price (Last 200 Days)",
        )

    # 📌 **Generate Trading Signals**
    def generate_signals(df):
        df['Buy_MACD_RSI'] = ((df['MACD'] > df['Signal_Line']) & (df['MACD'].shift(1) <= df['Signal_Line']) & (df['RSI'] > 30)).astype(int)
        df['Sell_MACD_RSI'] = ((df['MACD'] < df['Signal_Line']) & (df['MACD'].shift(1) >= df['Signal_Line']) & (df['RSI'] < 70)).astype(int) * -1

        df['Buy_BB_RSI'] = ((df['close'] < df['Lower_Band']) & (df['RSI'] < 30)).astype(int)
        df['Sell_BB_RSI'] = ((df['close'] > df['Upper_Band']) & (df['RSI'] > 70)).astype(int) * -1

        df['Buy_MA_MACD'] = ((df['close'] > df['MA50']) & (df['MACD'] > df['Signal_Line']) & (df['MACD'].shift(1) <= df['Signal_Line'])).astype(int)
        df['Sell_MA_MACD'] = ((df['close'] < df['MA50']) & (df['MACD'] < df['Signal_Line']) & (df['MACD'].shift(1) >= df['Signal_Line'])).astype(int) * -1

        return df

    stock_data = generate_signals(stock_data)

    # 📌 **Extract Latest Technicals**
    def extract_latest_technicals(df):
        return {
            "ticker": df['ticker'].iloc[-1],
            "latest_price": df['close'].iloc[-1],
            "50-day MA": df['MA50'].iloc[-1],
            "200-day MA": df['MA200'].iloc[-1],
            "MACD": df['MACD'].iloc[-1],
            "Signal Line": df['Signal_Line'].iloc[-1],
            "RSI": df['RSI'].iloc[-1],
            "Upper Bollinger Band": df['Upper_Band'].iloc[-1],
            "Lower Bollinger Band": df['Lower_Band'].iloc[-1],
            "Volume": df['volume'].iloc[-1]
        }

    latest_technicals = extract_latest_technicals(stock_data)

    # 📌 **Return Data for Dashboard**
    result_str = (
        f"Ticker: {latest_technicals['ticker']}\n"
        f"Latest Price: ${latest_technicals['latest_price']:.2f}\n"
        f"50-Day MA: ${latest_technicals['50-day MA']:.2f}\n"
        f"200-Day MA: ${latest_technicals['200-day MA']:.2f}\n"
        f"MACD: {latest_technicals['MACD']:.2f}\n"
        f"Signal Line: {latest_technicals['Signal Line']:.2f}\n"
        f"RSI: {latest_technicals['RSI']:.2f}\n"
        f"Upper Bollinger Band: ${latest_technicals['Upper Bollinger Band']:.2f}\n"
        f"Lower Bollinger Band: ${latest_technicals['Lower Bollinger Band']:.2f}\n"
        f"Volume: {latest_technicals['Volume']:,}\n"
    )

    return result_str
