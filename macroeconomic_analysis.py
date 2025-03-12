import pandas_datareader.data as web  # type: ignore
import sqlite3
import datetime
import pandas as pd  # type: ignore
import time

# Define Date Range
start = datetime.datetime(2020, 1, 1)
end = datetime.datetime.today()

# Define Economic Indicators (Each will be a column in the table)
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
    conn.execute("PRAGMA foreign_keys = ON;")  # Ensure foreign keys are enabled
    return conn

def initialize_database():
    """Ensure the macroeconomic_data table exists with separate columns for each indicator."""
    conn = create_connection()
    cursor = conn.cursor()

    # Generate SQL column definitions dynamically for each indicator
    columns = ", ".join([f"{code} REAL" for code in indicators.keys()])

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS macroeconomic_data (
            date DATE PRIMARY KEY,
            {columns}
        );
    """)

    conn.commit()
    conn.close()

def fetch_economic_data():
    """Fetch macroeconomic data from FRED and store it in SQLite."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check the last available date in the database
    cursor.execute("SELECT MAX(date) FROM macroeconomic_data;")
    last_date = cursor.fetchone()[0]
    
    if last_date:
        last_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")  # Convert string to datetime
        start_date = last_date + datetime.timedelta(days=1)  # Fetch data from the next day
    else:
        start_date = start  # Fetch all data if the database is empty

    all_data = None  # Initialize to None

    for code, name in indicators.items():
        try:
            df = web.DataReader(code, 'fred', start_date, end)

            if df is None or df.empty:
                print(f"No new data available for {name} ({code}). Skipping...")
                continue  # Skip if there's no new data

            df.rename(columns={df.columns[0]: code}, inplace=True)  # Rename dynamically
            df.index.name = 'date'

            if all_data is not None:
                all_data = all_data.join(df, how="outer")
            else:
                all_data = df  # First dataset initializes `all_data`

            print(f"Retrieved {name} ({code})")

            time.sleep(1)  # Prevent API rate limits

        except Exception as e:
            print(f"Could not retrieve {name} ({code}): {e}")

    if all_data is not None and not all_data.empty:
        all_data.reset_index(inplace=True)
        all_data['date'] = all_data['date'].astype(str)  # Convert date to string format
        
        # Batch Insert for Efficiency
        placeholders = ", ".join(["?"] * (len(all_data.columns)))  # Create placeholders for SQL query
        columns = ", ".join(all_data.columns)
        insert_query = f"INSERT OR IGNORE INTO macroeconomic_data ({columns}) VALUES ({placeholders});"

        cursor.executemany(insert_query, all_data.values.tolist())
        conn.commit()

        print("\nNew economic data saved successfully.")
    else:
        print("No new economic data was retrieved.")

    conn.close()

# Ensure table exists before fetching data
initialize_database()

