import pandas_datareader.data as web  # type: ignore
import sqlite3
import datetime
import pandas as pd  # type: ignore

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
    return sqlite3.connect('trading_data.db')

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

    all_data = None  # Initialize to None

    for code, name in indicators.items():
        try:
            df = web.DataReader(code, 'fred', start, end)

            # Explicitly check if DataFrame is empty
            if df is None or df.empty:
                print(f"No data available for {name} ({code}). Skipping...")
                continue  # Skip this iteration if data is empty

            df.rename(columns={df.columns[0]: code}, inplace=True)  # Rename dynamically
            df.index.name = 'date'

            if all_data is not None:
                all_data = all_data.join(df, how="outer")
            else:
                all_data = df  # First dataset initializes `all_data`

            print(f"Retrieved {name} ({code})")

        except Exception as e:
            print(f"Could not retrieve {name} ({code}): {e}")

    # Ensure there's data before storing it in SQLite
    if all_data is not None and not all_data.empty:
        all_data.reset_index(inplace=True)
        
        # Ensure data types are correctly formatted
        all_data['date'] = all_data['date'].astype(str)  # Convert date to string format
        
        all_data.to_sql("macroeconomic_data", conn, if_exists="replace", index=False)
        print("\nAll available economic data has been saved to SQLite successfully.")
    else:
        print("No economic data was retrieved, skipping database insertion.")

    conn.close()

# Ensure table exists before running
initialize_database()