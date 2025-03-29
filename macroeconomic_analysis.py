import pandas_datareader.data as web # type: ignore
import datetime
import pandas as pd
import time
import logging
from sqlalchemy import text # type: ignore
from sqlalchemy.engine import Engine # type: ignore

# Define Date Range
start = datetime.datetime(2020, 1, 1)
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

def fetch_economic_data(engine: Engine):
    """Fetch macroeconomic data from FRED and store it in the database using SQLAlchemy."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(date) FROM macroeconomic_data"))
            last_date = result.scalar()

        if last_date:
            try:
                last_date = datetime.datetime.strptime(str(last_date), "%Y-%m-%d")
                start_date = last_date + datetime.timedelta(days=1)
            except ValueError:
                start_date = start
        else:
            start_date = start

        start_date = min(start_date, end)

        for code, name in indicators.items():
            retry_attempts = 3
            while retry_attempts > 0:
                try:
                    df = web.DataReader(code, 'fred', start_date, end)

                    if df.empty:
                        break

                    df.reset_index(inplace=True)
                    df.columns = ["date", "value"]
                    df["indicator"] = code
                    df["date"] = df["date"].astype(str)

                    records = df[["indicator", "date", "value"]].to_dict(orient="records")

                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT OR IGNORE INTO macroeconomic_data (indicator, date, value)
                                VALUES (:indicator, :date, :value)
                            """),
                            records
                        )

                    time.sleep(1)
                    break  # Success, move on

                except Exception as e:
                    retry_attempts -= 1
                    logging.warning(f"Error retrieving {name} ({code}): {e} - Retries left: {retry_attempts}")
                    time.sleep(2 ** (3 - retry_attempts))

    except Exception as e:
        logging.error(f"Fatal error during macroeconomic fetch: {e}")