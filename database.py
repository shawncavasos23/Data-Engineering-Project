import sqlite3
from data_pipeline import update_stock_data
from db_utils import create_connection

def get_all_tickers():
    """Retrieve all tickers from the database."""
    conn = create_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM fundamentals")
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tickers

def initialize_database():
    """Creates tables and ensures schema is correct."""
    conn = create_connection()
    if conn is None:
        print("Error: Failed to create database connection.")
        return

    cursor = conn.cursor()
    print("Initializing database...")

    try:
             # Execute schema creation script
        cursor.executescript("""
        -- Fundamentals Table
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

        -- Technical Indicators Table
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

        -- Macroeconomic Data Table
        CREATE TABLE IF NOT EXISTS macroeconomic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL,
            date DATE NOT NULL,
            value REAL,
            UNIQUE(indicator, date)
        );

        -- News Articles Table
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

        -- Reddit Mentions Table
        CREATE TABLE IF NOT EXISTS reddit_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',  
            upvotes INTEGER DEFAULT 0,
            upvote_ratio REAL DEFAULT 0.0,
            date DATE NOT NULL DEFAULT (DATE('now')),
            link TEXT DEFAULT '',
            UNIQUE(ticker, title, date),
            FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
        );

        -- Trade Signals Table
        CREATE TABLE IF NOT EXISTS trade_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
            buy_price NUMERIC(10,2),  
            sell_price NUMERIC(10,2),
            stop_loss NUMERIC(10,2),
            date_generated DATE NOT NULL DEFAULT (DATE('now')),  
            FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
        );

        -- Indexes for Performance Optimization
        CREATE INDEX IF NOT EXISTS idx_technicals_ticker_date ON technicals (ticker, date);
        CREATE INDEX IF NOT EXISTS idx_news_ticker_date ON news (ticker, published_at);
        CREATE INDEX IF NOT EXISTS idx_reddit_ticker_date ON reddit_mentions (ticker, date);
        CREATE INDEX IF NOT EXISTS idx_signals_ticker ON trade_signals (ticker);
        CREATE INDEX IF NOT EXISTS idx_macro_indicator_date ON macroeconomic_data (indicator, date);
        """)

        # **Preload stock tickers with default values**
        tickers = [
            "AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "GOOGL", "META", "AMD", "NFLX", "BABA",
            "INTC", "PYPL", "CSCO", "QCOM", "ORCL", "IBM", "ADBE", "CRM", "TXN", "AVGO",
            "MU", "JD", "DIS", "PFE", "MRNA", "NIO", "BA", "XOM", "T",
            "V", "JPM", "WMT", "KO", "PEP", "MCD", "NKE", "GE", "HON", "CAT",
            "GS", "AXP", "LMT", "MMM", "CVX", "UNH", "ABBV", "ABT", "MDT", "DHR",
            "BMY", "LLY", "AMGN", "GILD", "TMO", "ISRG", "REGN", "VRTX", "SYK", "ZTS",
            "COST", "HD", "LOW", "TGT", "WBA", "CVS", "SBUX", "BKNG", "EBAY", "ROST",
            "TJX", "KHC", "CL", "PG", "MO", "PM", "DE", "F", "GM", "TSM",
            "SQ", "PLTR", "SNOW", "UBER", "LYFT", "ZM", "DOCU", "ROKU", "SPOT", "TWTR",
            "SHOP", "ETSY", "SE", "BIDU", "PDD", "NTES", "MELI", "FUTU", "NOK", "ERIC"
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO fundamentals (ticker, sector, pe_ratio, market_cap, revenue, beta, roa, roe, cluster) 
            VALUES (?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
        """, [(t,) for t in tickers])

        # 🔹 **Commit changes**
        conn.commit()
        print("Database initialized successfully.")

    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")

    finally:
        conn.close()
    
    # Prompt user to fetch stock data
    fetch_data = input("Initialize database and fetch stock data now? (y/n): ").strip().lower()
    if fetch_data == "y":
        tickers = get_all_tickers()
        for ticker in tickers:
            update_stock_data(ticker)

# 🔹 **Initialize the database**
if __name__ == "__main__":
    initialize_database()
