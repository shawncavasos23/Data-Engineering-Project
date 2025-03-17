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