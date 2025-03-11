import alpaca_trade_api as tradeapi # type: ignore
import os

# Load Alpaca API credentials
ALPACA_API_KEY = "your_alpaca_api_key"
ALPACA_SECRET_KEY = "your_alpaca_secret_key"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Use this for paper trading

# Initialize Alpaca API connection
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version="v2")

def place_trade(ticker, signal, buy_price, sell_price, stop_loss):
    """
    Places a trade order based on the AI-generated trading signal.

    :param ticker: Stock symbol (e.g., "AAPL")
    :param signal: AI trading decision ("BUY", "SELL", or "HOLD")
    :param buy_price: Recommended entry price
    :param sell_price: Target profit-taking price
    :param stop_loss: Stop-loss price to manage risk
    """
    try:
        # Get current position to check if we already hold the stock
        positions = api.list_positions()
        current_position = next((p for p in positions if p.symbol == ticker), None)
        
        if signal == "BUY":
            if current_position:
                print(f"Already holding {ticker}. No need to buy more.")
                return
            print(f"Placing a BUY order for {ticker} at {buy_price}...")

            api.submit_order(
                symbol=ticker,
                qty=10,  # Modify quantity as needed
                side="buy",
                type="limit",
                limit_price=buy_price,
                time_in_force="gtc"
            )
            print(f"BUY order placed for {ticker} at {buy_price}")

        elif signal == "SELL":
            if current_position:
                print(f"Selling {ticker} at {sell_price}...")
                api.submit_order(
                    symbol=ticker,
                    qty=current_position.qty,
                    side="sell",
                    type="limit",
                    limit_price=sell_price,
                    time_in_force="gtc"
                )
                print(f"SELL order placed for {ticker} at {sell_price}")
            else:
                print(f"No position in {ticker} to sell.")

        else:
            print(f"No trade action taken for {ticker} ({signal}).")

    except Exception as e:
        print(f"⚠ Error placing trade: {e}")
