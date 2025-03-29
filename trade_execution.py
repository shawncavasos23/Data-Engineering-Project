import alpaca_trade_api as tradeapi  # type: ignore
import logging
from sqlalchemy import text  # type: ignore
from sqlalchemy.engine import Engine  # type: ignore

# Load Alpaca API credentials
api_key = "PKAC0YX4NUEZD73KJUSM"
api_secret = "Tm6QZkLgrwvsaV1vpov39We2Fb7T12yPJlr5yJJn"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Initialize Alpaca API connection
api = tradeapi.REST(api_key, api_secret, ALPACA_BASE_URL, api_version="v2")

def is_market_open():
    """Check if the Alpaca market is currently open."""
    try:
        clock = api.get_clock()
        return clock.is_open
    except Exception as e:
        logging.warning(f"Error checking market status: {e}. Assuming market is closed.")
        return False

def get_position_size(ticker, max_dollars=5000):
    """
    Dynamically calculates position size based on max allocation.
    """
    try:
        quote = api.get_last_trade(ticker)
        price = quote.price
        qty = int(max_dollars / price)
        return max(qty, 1)
    except Exception as e:
        logging.warning(f"Error fetching market price for {ticker}: {e}. Defaulting to 1 share.")
        return 1

def place_trade(ticker: str, signal: str, buy_price: float, sell_price: float, stop_loss: float, engine: Engine):
    """
    Logs AI signal and executes trade if market is open.
    """
    signal = signal.upper()
    try:
        market_open = is_market_open()
        trade_status = "EXECUTED" if market_open else "PENDING"

        # Log signal to database (ignore duplicate same-day entries)
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO trade_signals (
                    ticker, signal, buy_price, sell_price, stop_loss,
                    date_generated, status
                )
                VALUES (
                    :ticker, :signal, :buy_price, :sell_price, :stop_loss,
                    DATE('now'), :status
                )
            """), {
                "ticker": ticker,
                "signal": signal,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "stop_loss": stop_loss,
                "status": trade_status
            })

        if not market_open:
            logging.info(f"Market closed. Trade logged for {ticker} but not executed.")
            return

        positions = api.list_positions()
        current_position = next((p for p in positions if p.symbol == ticker), None)

        if signal == "BUY":
            if current_position:
                logging.info(f"Already holding {ticker}. No additional buy executed.")
                return

            qty = get_position_size(ticker)
            logging.info(f"Placing BUY order for {ticker} at ${buy_price} (Qty: {qty})")

            order = api.submit_order(
                symbol=ticker,
                qty=qty,
                side="buy",
                type="limit",
                limit_price=buy_price,
                time_in_force="gtc"
            )

            logging.info(f"BUY Order Placed: {ticker} at ${buy_price} (Order ID: {order.id})")

            # Update database with order ID and execution timestamp
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE trade_signals
                    SET executed_at = CURRENT_TIMESTAMP,
                        order_id = :order_id,
                        status = 'EXECUTED'
                    WHERE ticker = :ticker AND date_generated = DATE('now')
                """), {
                    "order_id": order.id,
                    "ticker": ticker
                })

        elif signal == "SELL":
            if current_position:
                qty = int(float(current_position.qty))
                logging.info(f"Placing SELL order for {ticker} at ${sell_price} (Qty: {qty})")

                order = api.submit_order(
                    symbol=ticker,
                    qty=qty,
                    side="sell",
                    type="limit",
                    limit_price=sell_price,
                    time_in_force="gtc"
                )

                logging.info(f"SELL Order Placed: {ticker} at ${sell_price} (Order ID: {order.id})")

                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE trade_signals
                        SET executed_at = CURRENT_TIMESTAMP,
                            order_id = :order_id,
                            status = 'EXECUTED'
                        WHERE ticker = :ticker AND date_generated = DATE('now')
                    """), {
                        "order_id": order.id,
                        "ticker": ticker
                    })
            else:
                logging.info(f"No existing position in {ticker} to sell.")
        else:
            logging.info(f"No trade executed. Signal for {ticker}: {signal}")

    except tradeapi.rest.APIError as e:
        logging.error(f"Alpaca API Error for {ticker}: {e}")
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE trade_signals
                SET status = 'FAILED',
                    error_message = :error
                WHERE ticker = :ticker AND date_generated = DATE('now')
            """), {
                "error": str(e),
                "ticker": ticker
            })

    except Exception as e:
        logging.error(f"Trade Execution Error for {ticker}: {e}")
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE trade_signals
                SET status = 'FAILED',
                    error_message = :error
                WHERE ticker = :ticker AND date_generated = DATE('now')
            """), {
                "error": str(e),
                "ticker": ticker
            })
