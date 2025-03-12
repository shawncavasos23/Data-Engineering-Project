import pandas_datareader.data as web  # type: ignore
import sqlite3
import datetime
import pandas as pd  # type: ignore
import time
from database import create_connection

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

def fetch_economic_data():
    """Fetch macroeconomic data from FRED and store it in SQLite correctly."""
    conn = create_connection()
    cursor = conn.cursor()

    # Get the last stored date
    cursor.execute("SELECT MAX(date) FROM macroeconomic_data;")
    last_date = cursor.fetchone()[0]

    # Ensure last_date is valid and formatted correctly
    if last_date:
        try:
            last_date = datetime.datetime.strptime(str(last_date), "%Y-%m-%d")
            start_date = last_date + datetime.timedelta(days=1)  # Start from next day
        except ValueError:
            print(f"Warning: Invalid date format found in DB ({last_date}), resetting to default start date.")
            start_date = start
    else:
        start_date = start

    # Prevent fetching data beyond today
    start_date = min(start_date, end)

    for code, name in indicators.items():
        retry_attempts = 3
        while retry_attempts > 0:
            try:
                df = web.DataReader(code, 'fred', start_date, end)

                if df.empty:
                    print(f"Warning: No data available for {name} ({code}) in the given range.")
                    break  # No need to retry if data is empty

                df.reset_index(inplace=True)
                df.columns = ["date", "value"]
                df["indicator"] = code  # Store indicator name
                
                # Ensure the `date` column is correctly formatted as a string
                df["date"] = df["date"].astype(str)

                # Insert into database
                cursor.executemany(
                    "INSERT OR IGNORE INTO macroeconomic_data (indicator, date, value) VALUES (?, ?, ?);",
                    df[["indicator", "date", "value"]].values.tolist()
                )

                time.sleep(1)  # Prevent API rate limits
                break  # Success, move to next indicator

            except Exception as e:
                retry_attempts -= 1
                print(f"Error retrieving {name} ({code}): {e} - Retries left: {retry_attempts}")
                time.sleep(2 ** (3 - retry_attempts))  # Exponential backoff (2, 4, 8 seconds)

    conn.commit()
    conn.close()
