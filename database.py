import sqlite3

DB_NAME = "trading_data.db"

def create_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def initialize_database():
    """Create tables if they don’t exist."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER
    );

    CREATE TABLE IF NOT EXISTS indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        ma50 REAL,
        ma200 REAL,
        macd REAL,
        signal_line REAL,
        rsi REAL,
        upper_band REAL,
        lower_band REAL
    );

    CREATE TABLE IF NOT EXISTS fundamentals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        pe_ratio REAL,
        market_cap REAL,
        revenue REAL,
        beta REAL,
        roa REAL,
        roe REAL,
        cluster INTEGER DEFAULT NULL
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("✅ Database initialized successfully!")
