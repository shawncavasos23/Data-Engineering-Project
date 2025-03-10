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
    'FEDFUNDS': 'Federal Funds Rate',
    'GS10': '10-Year Treasury Yield',
    'GDPC1': 'Real GDP'
}

def create_connection():
    """Create or connect to the SQLite database."""
    return sqlite3.connect('trading_data.db')

def fetch_economic_data():
    """Fetches macroeconomic data from FRED and stores it in SQLite."""
    conn = create_connection()
    cursor = conn.cursor()

    for code, name in indicators.items():
        try:
            df = web.DataReader(code, 'fred', start, end)
            if not df.empty:
                for index, row in df.iterrows():
                    cursor.execute("""
                        INSERT OR IGNORE INTO macroeconomic_data (indicator, date, value)
                        VALUES (?, ?, ?)
                    """, (code, index.strftime("%Y-%m-%d"), row['value']))
                
                conn.commit()
                print(f"Retrieved & stored {name} ({code})")

        except Exception as e:
            print(f"Could not retrieve {name} ({code}): {e}")

    conn.close()
