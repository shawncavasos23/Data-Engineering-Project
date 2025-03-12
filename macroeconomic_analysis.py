import pandas_datareader.data as web  # type: ignore
import sqlite3
import datetime
import pandas as pd  # type: ignore
import time

# Define Date Range
start = datetime.datetime(2020, 1, 1)
end = datetime.datetime.today()

# Define Economic Indicators (Stored as rows, not columns)
indicators = {
    'CPIAUCSL': 'CPI (Consumer Price Index)',
    'PPIACO': 'PPI (Producer Price Index)',
    'UNRATE': 'Unemployment Rate',
    'PAYEMS': 'Nonfarm Employment',
    'FEDFUNDS': 'Federal Funds Rate',
    'GS10': '10-Year Treasury Yield',
    'UMCSENT': 'Consumer Confidence Index',
    'GDPC1': 'Real GDP',
    'RRSFS': 'Retail Sales',
    'HOUST': 'Housing Starts',
    'M1SL': 'M1 Money Supply',
    'M2SL': 'M2 Money Supply'
}

def create_connection():
    """Create or connect to the SQLite database."""
    conn = sqlite3.connect('trading_data.db')
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database():
    """Ensure the macroeconomic_data table exists in row format."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macroeconomic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL,
            date DATE NOT NULL,
            value REAL,
            UNIQUE(indicator, date)
        );
    """)

    conn.commit()
    conn.close()

def fetch_economic_data():
    """Fetch macroeconomic data from FRED and store it in SQLite correctly."""
    conn = create_connection()
    cursor = conn.cursor()

    # Ensure we get the correct column data
    cursor.execute("SELECT MAX(date) FROM macroeconomic_data;")
    last_date = cursor.fetchone()[0]

    # **Fix: Check if last_date is an invalid number**
    if last_date and not isinstance(last_date, str):  # If not a string, it's wrong
        print(f"⚠ Warning: last_date is invalid ({last_date}), resetting to None.")
        last_date = None  # Reset to None to fetch all data correctly

    if last_date:
        last_date = str(last_date)  # Ensure last_date is a string
        last_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # Convert to datetime
        start_date = last_date + datetime.timedelta(days=1)  # Start from next day
    else:
        start_date = start  # Fetch all data if empty

    # Prevent fetching data beyond today's date
    start_date = min(start_date, end)

    for code, name in indicators.items():
        try:
            df = web.DataReader(code, 'fred', start_date, end)

            if df.empty:
                continue

            df.reset_index(inplace=True)
            df.columns = ["date", "value"]
            df["indicator"] = code  # Store indicator name
            
            # **Ensure the `date` column is correctly formatted as a string**
            df["date"] = df["date"].astype(str)

            # **Ensure correct column order before inserting**
            cursor.executemany(
                "INSERT OR IGNORE INTO macroeconomic_data (indicator, date, value) VALUES (?, ?, ?);",
                df[["indicator", "date", "value"]].values.tolist()
            )

            print(f"Saved {name} ({code}) to database.")
            time.sleep(1)  # Prevent API rate limits

        except Exception as e:
            print(f"Could not retrieve {name} ({code}): {e}")

    conn.commit()
    conn.close()


# Ensure table exists before fetching data
initialize_database()
fetch_economic_data()