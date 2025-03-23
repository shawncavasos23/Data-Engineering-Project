from sqlalchemy import create_engine, text  # type: ignore
from sqlalchemy.exc import SQLAlchemyError  # type: ignore
import logging
import os

from data_pipeline import update_stock_data
from db_utils import create_sqlalchemy_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("database_init.log"),
        logging.StreamHandler()
    ]
)

def get_all_tickers(engine) -> list[str]:
    """Retrieve all tickers from the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT ticker FROM fundamentals"))
            return [row[0] for row in result.fetchall()]
    except SQLAlchemyError as e:
        logging.error(f"Error fetching tickers: {e}")
        return []

def initialize_database(engine, fetch_data=False):
    """Creates tables and initializes the schema."""
    logging.info("Initializing database schema...")

    schema_statements = [
        # Fundamentals Table
        """
        CREATE TABLE IF NOT EXISTS fundamentals (
            ticker TEXT PRIMARY KEY,
            sector TEXT DEFAULT NULL,
            pe_ratio REAL DEFAULT NULL,
            market_cap BIGINT DEFAULT NULL,
            revenue REAL DEFAULT NULL,
            beta REAL DEFAULT NULL,
            roa REAL DEFAULT NULL,
            roe REAL DEFAULT NULL,
            dividend_yield REAL DEFAULT NULL,
            dividend_per_share REAL DEFAULT NULL,
            total_debt BIGINT DEFAULT NULL,
            total_cash BIGINT DEFAULT NULL,
            free_cash_flow REAL DEFAULT NULL,
            operating_cash_flow REAL DEFAULT NULL,
            net_income REAL DEFAULT NULL,
            cluster INTEGER DEFAULT NULL
        );
        """,
        # Technicals Table
        """
        CREATE TABLE IF NOT EXISTS technicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume BIGINT,
            ma50 REAL,
            ma200 REAL,
            macd REAL,
            signal_line REAL,
            rsi REAL,
            upper_band REAL,
            lower_band REAL,
            adx REAL,
            obv BIGINT,
            pivot REAL,
            r1 REAL,
            s1 REAL,
            UNIQUE(ticker, date),
            FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
        );
        """,
        # Macroeconomic Table
        """
        CREATE TABLE IF NOT EXISTS macroeconomic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL,
            date DATE NOT NULL,
            value REAL,
            UNIQUE(indicator, date)
        );
        """,
        # News Table
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            source TEXT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT NOT NULL UNIQUE,
            published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, title, published_at),
            FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
        );
        """,
        # Reddit Mentions Table
        """
        CREATE TABLE IF NOT EXISTS reddit_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            sentiment REAL DEFAULT 0.0,
            upvotes INTEGER DEFAULT 0,
            upvote_ratio REAL DEFAULT 0.0,
            date DATE NOT NULL DEFAULT (DATE('now')),
            link TEXT DEFAULT '',
            UNIQUE(ticker, title, date),
            FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
        );
        """,
        # Trade Signals Table with tracking
        """
        CREATE TABLE IF NOT EXISTS trade_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
            buy_price NUMERIC(10,2),
            sell_price NUMERIC(10,2),
            stop_loss NUMERIC(10,2),
            date_generated DATE NOT NULL DEFAULT (DATE('now')),
            executed_at DATETIME DEFAULT NULL,
            status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'EXECUTED', 'FAILED')),
            order_id TEXT DEFAULT NULL,
            error_message TEXT DEFAULT NULL,
            FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
        );
        """,
        # Indexes
        "CREATE INDEX IF NOT EXISTS idx_technicals_ticker_date ON technicals (ticker, date);",
        "CREATE INDEX IF NOT EXISTS idx_news_ticker_date ON news (ticker, published_at);",
        "CREATE INDEX IF NOT EXISTS idx_reddit_ticker_date ON reddit_mentions (ticker, date);",
        "CREATE INDEX IF NOT EXISTS idx_signals_ticker ON trade_signals (ticker);",
        "CREATE INDEX IF NOT EXISTS idx_macro_indicator_date ON macroeconomic_data (indicator, date);"
    ]

    try:
        with engine.begin() as conn:
            for stmt in schema_statements:
                conn.execute(text(stmt))

            # Preload tickers
            tickers = [
                "AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "GOOGL", "META", "AMD", "NFLX", "BABA",
                "INTC", "PYPL", "CSCO", "QCOM", "ORCL", "IBM", "ADBE", "CRM", "TXN", "AVGO",
                "MU", "JD", "DIS", "PFE", "MRNA", "NIO", "BA", "XOM", "T", "V", "JPM", "WMT", "KO",
                "PEP", "MCD", "NKE", "GE", "HON", "CAT", "GS", "AXP", "LMT", "MMM", "CVX", "UNH",
                "ABBV", "ABT", "MDT", "DHR", "BMY", "LLY", "AMGN", "GILD", "TMO", "ISRG", "REGN",
                "VRTX", "SYK", "ZTS", "COST", "HD", "LOW", "TGT", "WBA", "CVS", "SBUX", "BKNG",
                "EBAY", "ROST", "TJX", "KHC", "CL", "PG", "MO", "PM", "DE", "F", "GM", "TSM",
                "SQ", "PLTR", "SNOW", "UBER", "LYFT", "ZM", "DOCU", "ROKU", "SPOT", "TWTR", "SHOP",
                "ETSY", "SE", "BIDU", "PDD", "NTES", "MELI", "FUTU", "NOK", "ERIC"
            ]

            conn.execute(
                text("INSERT OR IGNORE INTO fundamentals (ticker) VALUES (:ticker)"),
                [{"ticker": t} for t in tickers]
            )

        logging.info("Database schema and tickers initialized successfully.")

    except SQLAlchemyError as e:
        logging.error(f"SQLAlchemy error during schema creation: {e}")

    # Optional data fetch
    if fetch_data:
        logging.info("Fetching stock data for all tickers...")
        tickers = get_all_tickers(engine)
        for ticker in tickers:
            try:
                update_stock_data(ticker)
                logging.info(f"Fetched data for {ticker}")
            except Exception as e:
                logging.warning(f"Failed to fetch data for {ticker}: {e}")

if __name__ == "__main__":
    engine = create_sqlalchemy_engine()
    fetch = os.getenv("FETCH_DATA", "n").lower() == "y"
    initialize_database(engine, fetch_data=fetch)
