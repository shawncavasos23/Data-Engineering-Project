import logging
import sqlite3
import pandas as pd
import datetime
from fredapi import Fred

# Set up logging
logging.basicConfig(level=logging.INFO)

#FRED API Key
FRED_API_KEY = "834419259ee085e93f6ab31eeb4fa5e8"  #My account
fred = Fred(api_key=FRED_API_KEY)

# data series
series_dict = {
    "CPIAUCSL": "CPIAUCSL",  # # Consumer Price Index
    "PPIACO": "PPIACO",  # # Producer Price Index
    "UNRATE": "UNRATE",  # Unemployment Rate
    "PAYEMS": "PAYEMS",  # Non-farm Payrolls
    "FEDFUNDS": "FEDFUNDS",  # Federal Reserve Interest Rate
    "GS10": "GS10",  # 10-Year Treasury Yield
    "UMCSENT": "UMCSENT",  # Consumer Confidence Index
    "GDPC1": "GDPC1",  # GDP
    "RRSFS": "RRSFS",  # Retail Sales
    "HOUST": "HOUST",  # Housing Starts
    "M1SL": "M1SL",  # M1 Money Supply
    "M2SL": "M2SL",  # M2 Money Supply
}

# Set the data time range
start_date = "2020-01-01"
end_date = datetime.date.today().strftime("%Y-%m-%d")  # Today

# Fetch data
df = pd.DataFrame()
for name, series in series_dict.items():
    
    data = fred.get_series(series, start_date, end_date)
    df[name] = data




# Process the time index
df.index.name = "date"
df.reset_index(inplace=True)

#  Convert `date` to string format to avoid SQLite errors
df["date"] = df["date"].astype(str)

# Handle missing values
df.fillna(method="ffill", inplace=True)  # Forward fill
df.fillna(method="bfill", inplace=True)  # Backward fill

# avoid `.ffill(inplace=True)` error
df["GDPC1"] = df["GDPC1"].ffill()

# Calculate derived features
df["CPI_diff"] = df["CPIAUCSL"].diff()
df["UNRATE_diff"] = df["UNRATE"].diff()
df["PPI_diff"] = df["PPIACO"].diff()
df["GDP_growth"] = df["GDPC1"].pct_change()

# Connect to the database
conn = sqlite3.connect("macroeconomic_data.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS macroeconomic_data (
        date TEXT PRIMARY KEY,
        CPIAUCSL REAL,
        PPIACO REAL,
        UNRATE REAL,
        PAYEMS REAL,
        FEDFUNDS REAL,
        GS10 REAL,
        UMCSENT REAL,
        GDPC1 REAL,
        RRSFS REAL,
        HOUST REAL,
        M1SL REAL,
        M2SL REAL
    )
""")
conn.commit()
logging.info("Table 'macroeconomic_data' created successfully.")

# Insert data
try:
    df.to_sql("macroeconomic_data", conn, if_exists="replace", index=False)
    logging.info("Data stored successfully in SQLite database.")
except Exception as e:
    logging.error(f"Error storing macroeconomic data: {e}")

# Close database connection
conn.close()

# Print data preview
logging.info("Data fetched and processed successfully.")
logging.info("Features prepared for machine learning.")
logging.info(f"Data preview:\n{df.head()}")
