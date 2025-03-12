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

    cursor.executescript("""
    -- Fundamentals Table
    CREATE TABLE IF NOT EXISTS fundamentals (
        ticker TEXT PRIMARY KEY,  -- Ensures uniqueness and enforces foreign keys
        sector TEXT,
        pe_ratio REAL,
        market_cap BIGINT,  -- Large values require BIGINT
        revenue REAL,
        beta REAL,
        roa REAL,
        roe REAL,
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
        volume BIGINT,  -- Large volumes require BIGINT
        ma50 REAL,
        ma200 REAL,
        macd REAL,
        signal_line REAL,
        rsi REAL,
        upper_band REAL,
        lower_band REAL,
        adx REAL,
        obv BIGINT,  -- Large values require BIGINT
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
        source TEXT,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT,
        published_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Use UTC timestamps
        UNIQUE(title, published_at)
    );

    -- Reddit Mentions Table
    CREATE TABLE IF NOT EXISTS reddit_mentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        title TEXT NOT NULL,
        upvotes INTEGER,
        upvote_ratio REAL,
        date DATE NOT NULL DEFAULT (DATE('now')),  -- Ensure ISO 8601 format
        link TEXT,
        UNIQUE(ticker, title, date),
        FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
    );

    -- Trade Signals Table
    CREATE TABLE IF NOT EXISTS trade_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
        buy_price NUMERIC(10,2),  -- Financial precision
        sell_price NUMERIC(10,2),
        stop_loss NUMERIC(10,2),
        date_generated DATE NOT NULL DEFAULT (DATE('now')),  -- Ensure correct date format
        FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
    );

    -- Indexes for Performance Optimization
    CREATE INDEX IF NOT EXISTS idx_technicals_ticker_date ON technicals (ticker, date);
    CREATE INDEX IF NOT EXISTS idx_reddit_ticker_date ON reddit_mentions (ticker, date);
    CREATE INDEX IF NOT EXISTS idx_signals_ticker ON trade_signals (ticker);
    CREATE INDEX IF NOT EXISTS idx_macro_indicator_date ON macroeconomic_data (indicator, date);
    CREATE INDEX IF NOT EXISTS idx_news_published ON news (published_at);
    """)
    
    # Preload 10 Stocks
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "JPM", "V"]
    cursor.executemany("INSERT OR IGNORE INTO fundamentals (ticker) VALUES (?);", [(t,) for t in tickers])

    conn.commit()
    conn.close()

# Initialize the updated database
initialize_database()
