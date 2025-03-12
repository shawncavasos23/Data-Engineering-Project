import sqlite3

def create_connection():
    """Create or connect to the SQLite database with foreign keys enabled."""
    conn = sqlite3.connect("trading_data.db")
    conn.execute("PRAGMA foreign_keys = ON;")  # Enforce foreign key constraints
    return conn

def initialize_database():
    """Creates tables and ensures schema is correct."""
    conn = create_connection()
    cursor = conn.cursor()

    # Drop and recreate tables if schema needs updates
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS fundamentals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL UNIQUE,
        sector TEXT,  -- Allows multiple sectors as comma-separated values
        pe_ratio REAL,
        market_cap REAL,
        revenue REAL,
        beta REAL,
        roa REAL,
        roe REAL,
        cluster INTEGER DEFAULT NULL
    );

    CREATE TABLE IF NOT EXISTS technicals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        date DATE NOT NULL,
        ma50 REAL,
        ma200 REAL,
        macd REAL,
        signal_line REAL,
        rsi REAL,
        upper_band REAL,
        lower_band REAL,
        volume INTEGER,
        UNIQUE(ticker, date),
        FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS macroeconomic_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        indicator TEXT NOT NULL,
        date DATE NOT NULL,
        value REAL,
        UNIQUE(indicator, date)
    );

    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT,
        published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(title, published_at)
    );

    CREATE TABLE IF NOT EXISTS reddit_mentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        title TEXT NOT NULL,
        upvotes INTEGER,
        upvote_ratio REAL,
        date DATE NOT NULL,
        link TEXT,
        UNIQUE(ticker, title, date),
        FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS trade_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),  -- Ensure only valid signals
        buy_price REAL,
        sell_price REAL,
        stop_loss REAL,
        date_generated DATE NOT NULL DEFAULT (DATE('now')),
        FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
    );

    -- **Indexes for performance optimization**
    CREATE INDEX IF NOT EXISTS idx_technicals_ticker_date ON technicals (ticker, date);
    CREATE INDEX IF NOT EXISTS idx_reddit_ticker_date ON reddit_mentions (ticker, date);
    CREATE INDEX IF NOT EXISTS idx_signals_ticker ON trade_signals (ticker);
    """)

    # **Preload 10 Stocks**
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "JPM", "V"]
    cursor.executemany("INSERT OR IGNORE INTO fundamentals (ticker) VALUES (?);", [(t,) for t in tickers])

    conn.commit()
    conn.close()

# Initialize database
initialize_database()
