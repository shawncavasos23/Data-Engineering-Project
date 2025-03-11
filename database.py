import sqlite3

def create_connection():
    """Create or connect to the SQLite database."""
    return sqlite3.connect("trading_data.db")

def initialize_database():
    """Creates tables and ensures existing schema matches new schema."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check if fundamentals table already exists
    cursor.execute("PRAGMA table_info(fundamentals);")
    existing_columns = {row[1] for row in cursor.fetchall()}  # Get existing column names

    required_columns = {"id", "ticker", "sector", "pe_ratio", "market_cap", "revenue", "beta", "roa", "roe", "cluster"}

    if not required_columns.issubset(existing_columns):
        print("⚠ Table schema mismatch detected. Rebuilding database...")
        cursor.executescript("""
        DROP TABLE IF EXISTS fundamentals;
        DROP TABLE IF EXISTS technicals;
        DROP TABLE IF EXISTS macroeconomic_data;
        DROP TABLE IF EXISTS news;
        """)

    # Create updated tables
    cursor.executescript("""
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
        title TEXT,
        description TEXT,
        url TEXT,
        published_at DATETIME,
        UNIQUE(title, published_at)
    );
    """)

    # Preload some tickers if not already present
    tickers = ["AAPL"]
    cursor.executemany("INSERT OR IGNORE INTO fundamentals (ticker) VALUES (?);", [(t,) for t in tickers])

    conn.commit()
    conn.close()

# Initialize database
initialize_database()
