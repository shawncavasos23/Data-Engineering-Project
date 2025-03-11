import sqlite3

def create_connection():
    """Create or connect to the SQLite database."""
    return sqlite3.connect("trading_data.db")

def initialize_database():
    """Create tables for fundamentals, technical indicators, macroeconomic data, and news headlines."""
    conn = create_connection()
    cursor = conn.cursor()

    # Create or update database tables
    cursor.executescript("""
    -- Fundamentals Table: Stores financial ratios, sector data, and clustering info
    CREATE TABLE IF NOT EXISTS fundamentals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL UNIQUE,
        sector TEXT,
        pe_ratio REAL,
        market_cap REAL,
        revenue REAL,
        beta REAL,
        roa REAL,
        roe REAL,
        cluster INTEGER DEFAULT NULL
    );

    -- Technical Indicators Table: Stores stock trading indicators
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
        UNIQUE(ticker, date)
    );

    -- Macroeconomic Data Table: Stores key economic indicators over time
    CREATE TABLE IF NOT EXISTS macroeconomic_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        indicator TEXT NOT NULL,
        date DATE NOT NULL,
        value REAL,
        UNIQUE(indicator, date)
    );

    -- News Table: Stores the latest financial news headlines
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT,
        description TEXT,
        url TEXT,
        published_at DATETIME,
        UNIQUE(title, published_at)
    );
    """)

     # **Preload Some Tickers**
    tickers = ["AAPL"]
    cursor.executemany("INSERT OR IGNORE INTO fundamentals (ticker) VALUES (?);", [(t,) for t in tickers])

    conn.commit()
    conn.close()

# Initialize the database when the script is first run
initialize_database()
