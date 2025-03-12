import alpaca_trade_api as tradeapi # type: ignore
import os

# Load Alpaca API credentials
api_key = "PKAC0YX4NUEZD73KJUSM"
api_secret = "Tm6QZkLgrwvsaV1vpov39We2Fb7T12yPJlr5yJJn"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Use this for paper trading

# Initialize Alpaca API connection
api = tradeapi.REST(api_key, api_secret, ALPACA_BASE_URL, api_version="v2")

def is_market_open():
    """Check if the Alpaca market is currently open."""
    try:
        clock = api.get_clock()
        return clock.is_open
    except Exception as e:
        print(f"Error checking market status: {e}")
        return False  # Assume market is closed if API check fails

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
        # 🔹 Check if market is open before placing trades
        if not is_market_open():
            print(f"Market is closed. Cannot place order for {ticker}.")
            return

        # 🔹 Get current positions
        positions = api.list_positions()
        current_position = next((p for p in positions if p.symbol == ticker), None)

        if signal == "BUY":
            if current_position:
                print(f"⚠ Already holding {ticker}. No additional buy needed.")
                return
            
            print(f"Placing a **BUY** order for {ticker} at ${buy_price}...")

            order = api.submit_order(
                symbol=ticker,
                qty=10,  # Modify quantity as needed
                side="buy",
                type="limit",
                limit_price=buy_price,
                time_in_force="gtc"
            )

            print(f"**BUY Order Placed:** {ticker} at ${buy_price} (Order ID: {order.id})")

        elif signal == "SELL":
            if current_position:
                sell_qty = int(float(current_position.qty))
                print(f"Placing a **SELL** order for {ticker} at ${sell_price}...")

                order = api.submit_order(
                    symbol=ticker,
                    qty=sell_qty,
                    side="sell",
                    type="limit",
                    limit_price=sell_price,
                    time_in_force="gtc"
                )

                print(f"**SELL Order Placed:** {ticker} at ${sell_price} (Order ID: {order.id})")

            else:
                print(f"No existing position in {ticker} to sell. Skipping SELL order.")

        else:
            print(f"No trade action taken for {ticker}. AI signal: {signal}")

    except tradeapi.rest.APIError as e:
        print(f"**Alpaca API Error for {ticker}**: {e}")

    except Exception as e:
        print(f"**Trade Execution Failed for {ticker}**: {e}")