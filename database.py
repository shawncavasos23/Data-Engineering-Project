import sqlite3

def create_connection():
    """Create or connect to the SQLite database with foreign keys enabled."""
    try:
        conn = sqlite3.connect("trading_data.db")
        conn.execute("PRAGMA foreign_keys = ON;")  # Enforce foreign key constraints
        return conn
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
        return None

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

        # 🔹 **Preload stock tickers with default values**
        tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "JPM", "V",
            "BA", "IBM", "DIS", "INTC", "WMT", "KO", "PEP", "ORCL", "MCD", "NKE",
            "CVX", "XOM", "PFE", "UNH", "ABT", "AXP", "CAT", "RTX", "GS", "HD",
            "PG", "SPG", "LMT", "MMM", "BMY", "MDT", "DHR", "GE", "LUV", "CSCO",
            "SCHW", "COST", "TMO", "VZ", "ADBE", "CVS", "SYK", "SBUX", "TRV",
            "AMT", "MO", "BAX", "T", "LRCX", "CTSH", "ISRG", "UAL", "AMGN", "REGN",
            "CSX", "GILD", "FISV", "EQIX", "F", "ZM", "MRK", "ZTS", "VLO", "AIG",
            "SCHW", "HCA", "MS", "KHC", "COP", "WM", "CCI", "DOW", "TGT", "STT",
            "BK", "CME", "WFC", "MCK", "HUM", "CTVA", "ALL", "ICE", "MA", "CHTR",
            "AMAT", "ADI", "WDC", "BKR", "NSC", "STZ", "APD", "DLR", "NOC", "CSGP",
            "NEM", "FIS", "CTXS", "LVS", "EXPE", "USB", "PGR", "TFX", "MAR", "RSG"
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

# 🔹 **Initialize the database**
if __name__ == "__main__":
    initialize_database()
