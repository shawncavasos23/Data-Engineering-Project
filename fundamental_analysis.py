import requests  # type: ignore
import time
import sqlite3
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore
from sklearn.cluster import KMeans  # type: ignore
from kneed import KneeLocator  # type: ignore
from database import create_connection


def get_sp500_symbols_and_sectors():
    """Fetch S&P 500 tickers and their sector information from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    sp500_df = tables[0]  # First table contains stock symbols and sectors
    return sp500_df[['Symbol', 'GICS Sector']].rename(columns={'Symbol': 'ticker', 'GICS Sector': 'sector'})

def get_sector_peers(ticker, sp500_df):
    """Find all companies in the same sector as the given ticker."""
    sector = sp500_df.loc[sp500_df['ticker'] == ticker, 'sector'].values
    if len(sector) == 0:
        print(f"⚠ {ticker} not found in S&P 500 list.")
        return []
    
    sector = sector[0]  # Get sector name
    same_sector_tickers = sp500_df[sp500_df['sector'] == sector]['ticker'].tolist()
    
    print(f"Sector for {ticker}: {sector}")

    return same_sector_tickers

API_KEY = "your_api_key_here"

def get_fundamental_data(ticker):
    """Fetch fundamental financial data and sector info for a given stock, with retries on failure."""
    base_url = "https://financialmodelingprep.com/api/v3/"
    attempts = 0
    wait_time = 2  # Start with 2-second wait, increase on failure

    while attempts < 3:
        try:
            response_profile = requests.get(f"{base_url}profile/{ticker}?apikey={API_KEY}")
            response_profile.raise_for_status()
            profile_data = response_profile.json()

            if not profile_data:
                raise ValueError("No profile data returned from API.")

            company_data = profile_data[0]
            sector = company_data.get("sector", "Unknown")

            response_metrics = requests.get(f"{base_url}key-metrics/{ticker}?apikey={API_KEY}")
            response_metrics.raise_for_status()
            key_metrics = response_metrics.json()[0] if response_metrics.json() else {}

            response_ratios = requests.get(f"{base_url}ratios/{ticker}?apikey={API_KEY}")
            response_ratios.raise_for_status()
            ratios_data = response_ratios.json()[0] if response_ratios.json() else {}

            fundamentals = {
                "ticker": ticker,
                "sector": sector,
                "pe_ratio": key_metrics.get("peRatio") or ratios_data.get("priceEarningsRatio"),
                "market_cap": company_data.get("mktCap"),
                "revenue": company_data.get("revenue") or key_metrics.get("revenue"),
                "beta": company_data.get("beta"),
                "roa": company_data.get("returnOnAssets") or ratios_data.get("returnOnAssets"),
                "roe": company_data.get("returnOnEquity") or ratios_data.get("returnOnEquity")
            }
            return fundamentals

        except requests.exceptions.RequestException as e:
            print(f"Error fetching fundamental data for {ticker}: {e}")
            attempts += 1
            time.sleep(wait_time)
            wait_time *= 2

    print(f"Skipping {ticker} after 3 failed attempts.")
    return None

def store_fundamentals(data):
    """Stores fetched fundamental data into the database."""
    if data is None:
        return

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO fundamentals (
            ticker, sector, pe_ratio, 
            market_cap, revenue, beta, roa, roe
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["ticker"], data["sector"], data["pe_ratio"],
        data["market_cap"], data["revenue"], data["beta"], data["roa"], data["roe"]
    ))

    conn.commit()
    conn.close()

def cluster_companies():
    """Uses K-Means clustering to group companies based on financial metrics."""
    conn = create_connection()
    df = pd.read_sql("SELECT * FROM fundamentals", conn)
    conn.close()

    if df.empty:
        print("No data available for clustering.")
        return df

    print("\n[DEBUG] Missing values in raw fundamentals dataset:")
    print(df.isna().sum())

    features = df[['pe_ratio', 'market_cap', 'revenue', 'beta', 'roa', 'roe']].copy()

    features.fillna(features.mean(), inplace=True)  # Handle missing values
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    k_range = range(1, 11)
    inertia = [KMeans(n_clusters=k, random_state=42, n_init=10).fit(scaled_features).inertia_ for k in k_range]
    kneedle = KneeLocator(k_range, inertia, curve="convex", direction="decreasing")
    optimal_k = kneedle.elbow or 3

    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(scaled_features)

    conn = create_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("UPDATE fundamentals SET cluster = ? WHERE ticker = ?", (row["cluster"], row["ticker"]))

    conn.commit()
    conn.close()
    
    print("\n[INFO] Clustering complete. Clusters assigned to database.")
    return df
