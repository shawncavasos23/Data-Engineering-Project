import requests
import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from kneed import KneeLocator  # Automatically detects the elbow point
from database import create_connection

API_KEY = "rfxtGuPO4lt5yNQOIuS4r7P27L508Mvt"

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
    print(f"Found {len(same_sector_tickers)} tickers in the same sector.")

    return same_sector_tickers

def get_fundamental_data(ticker):
    """Fetches fundamental financial data and sector info for a given stock."""
    base_url = "https://financialmodelingprep.com/api/v3/"
    
    try:
        # Fetch Company Profile (Contains Sector Information)
        response_profile = requests.get(f"{base_url}profile/{ticker}?apikey={API_KEY}")
        response_profile.raise_for_status()
        profile_data = response_profile.json()

        if not profile_data:
            return None  # No data found
        
        sector = profile_data[0].get("sector", "Unknown")  # Extract sector information

        # Fetch Key Metrics (Financial Information)
        response_metrics = requests.get(f"{base_url}key-metrics/{ticker}?apikey={API_KEY}")
        response_metrics.raise_for_status()
        key_metrics = response_metrics.json()

        if not key_metrics:
            return None  # No data found

        data = key_metrics[0]  # Extract latest available data

        fundamentals = {
            "ticker": ticker,
            "sector": sector,  # Add sector information
            "pe_ratio": data.get("peRatio"),
            "market_cap": data.get("marketCap"),
            "revenue": data.get("revenue"),
            "beta": data.get("beta"),
            "roa": data.get("returnOnAssets"),
            "roe": data.get("returnOnEquity"),
        }
        return fundamentals

    except requests.exceptions.RequestException as e:
        print(f"Error fetching fundamental data for {ticker}: {e}")
        return None

def store_fundamentals(data):
    """Stores fetched fundamental data into the database."""
    if data is None:
        return

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO fundamentals (ticker, sector, pe_ratio, market_cap, revenue, beta, roa, roe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data["ticker"], data["sector"], data["pe_ratio"], data["market_cap"], data["revenue"],
          data["beta"], data["roa"], data["roe"]))

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

    features = df[['pe_ratio', 'market_cap', 'revenue', 'beta', 'roa', 'roe']].copy()
    features.fillna(features.mean(), inplace=True)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    k_range = range(1, 11)
    inertia = [KMeans(n_clusters=k, random_state=42, n_init=10).fit(scaled_features).inertia_ for k in k_range]
    kneedle = KneeLocator(k_range, inertia, curve="convex", direction="decreasing")
    optimal_k = kneedle.elbow or 3  # Default to 3 clusters if no elbow is found

    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(scaled_features)

    conn = create_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("UPDATE fundamentals SET cluster = ? WHERE ticker = ?", (row["cluster"], row["ticker"]))

    conn.commit()
    conn.close()
    return df

def get_cluster_peers(ticker):
    """Finds companies in the same cluster as the given ticker."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT cluster FROM fundamentals WHERE ticker = ?", (ticker,))
    cluster = cursor.fetchone()

    if cluster:
        cursor.execute("SELECT ticker FROM fundamentals WHERE cluster = ? AND ticker != ?", (cluster[0], ticker))
        peers = [row[0] for row in cursor.fetchall()]
        return peers

    return []

def run_fundamental_analysis(ticker):
    """Fetches fundamental data, finds same-sector companies, and clusters."""
    
    print(f"Fetching fundamental data for {ticker}...")
    sp500_df = get_sp500_symbols_and_sectors()  # Load S&P 500 data
    same_sector_tickers = get_sector_peers(ticker, sp500_df)  # Get same-sector firms

    if ticker not in same_sector_tickers:
        same_sector_tickers.append(ticker)  # Ensure main ticker is included

    selected_tickers = same_sector_tickers[:39]  # Limit to 40 total

    sector_data = []
    for tkr in selected_tickers:
        data = get_fundamental_data(tkr)
        if data:
            store_fundamentals(data)  # Save to DB
            sector_data.append(data)

    print(f"Stored data for {len(sector_data)} companies in the same sector.")

    print("Clustering companies...")
    cluster_companies()

    print(f"👥 Finding similar companies to {ticker}...")
    peers = get_cluster_peers(ticker)

    return {"ticker": ticker, "peers": peers, "fundamentals": get_fundamental_data(ticker)}
