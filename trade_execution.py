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
        print(f"Error checking market status: {e}. Assuming market is closed.")
        return False  # Default to closed if API call fails

def get_position_size(ticker, max_dollars=5000):
    """
    Dynamically calculates position size based on max allocation.

    :param ticker: Stock symbol
    :param max_dollars: Max dollar amount to allocate per trade (default: $5000)
    :return: Quantity of shares to buy
    """
    try:
        # Fetch current market price
        quote = api.get_last_trade(ticker)
        price = quote.price
        qty = int(max_dollars / price)  # Ensure whole number of shares
        return max(qty, 1)  # Minimum 1 share
    except Exception as e:
        print(f"Error fetching market price for {ticker}: {e}. Defaulting to 1 share.")
        return 1  # Default to 1 share if price fetch fails

def place_trade(ticker, signal, buy_price, sell_price):
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
                print(f"Already holding {ticker}. No additional buy needed.")
                return
            
            qty = get_position_size(ticker)  # Determine position size dynamically
            print(f"Placing a **BUY** order for {ticker} at ${buy_price} (Qty: {qty})...")

            order = api.submit_order(
                symbol=ticker,
                qty=qty,
                side="buy",
                type="limit",
                limit_price=buy_price,
                time_in_force="gtc"
            )

            print(f"**BUY Order Placed:** {ticker} at ${buy_price} (Order ID: {order.id})")

        elif signal == "SELL":
            if current_position:
                sell_qty = int(float(current_position.qty))
                print(f"Placing a **SELL** order for {ticker} at ${sell_price} (Qty: {sell_qty})...")

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