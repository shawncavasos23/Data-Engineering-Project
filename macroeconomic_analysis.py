import pandas_datareader.data as web
import sqlite3
import datetime

# Define Date Range
start = datetime.datetime(2000, 1, 1)
end = datetime.datetime.today()

# Define Economic Indicators
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
    return sqlite3.connect('trading_data.db')

def initialize_database():
    """Ensure the macroeconomic_data table exists before inserting data."""
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
    """Fetch macroeconomic data from FRED and store it in SQLite."""
    conn = create_connection()
    cursor = conn.cursor()

    for code, name in indicators.items():
        try:
            df = web.DataReader(code, 'fred', start, end)

            if not df.empty:
                df.rename(columns={df.columns[0]: 'value'}, inplace=True)  # Rename dynamically
                df.index.name = 'date'

                # Insert each row into SQLite
                for index, row in df.iterrows():
                    cursor.execute("""
                        INSERT OR REPLACE INTO macroeconomic_data (indicator, date, value)
                        VALUES (?, ?, ?)
                    """, (code, index.strftime("%Y-%m-%d"), row['value']))

                conn.commit()
                print(f"Retrieved & stored {name} ({code})")

            else:
                print(f"No data available for {name} ({code}). Skipping...")

        except Exception as e:
            print(f"Could not retrieve {name} ({code}): {e}")

    conn.close()
    print("\nAll available economic data has been saved to SQLite successfully.")

# Ensure table exists before running
initialize_database()
