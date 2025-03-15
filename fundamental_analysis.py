import requests  # type: ignore
import time
import sqlite3
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore
from sklearn.cluster import KMeans  # type: ignore
from sklearn.impute import SimpleImputer  # type: ignore
from kneed import KneeLocator  # type: ignore
from database import create_connection
import os

API_KEY = "ryvHpF6OKhRpZ4c7YJ4zBv8JD4PwcDbl"

def get_fundamental_data(ticker):
    """Fetch fundamental financial data for a stock and store it in SQLite."""
    
    conn = create_connection()
    cursor = conn.cursor()

    # Check if fundamentals are missing
    cursor.execute("""
        SELECT COUNT(*) FROM fundamentals 
        WHERE ticker = ? AND (pe_ratio IS NOT NULL OR revenue IS NOT NULL OR market_cap IS NOT NULL)
    """, (ticker,))
    data_exists = cursor.fetchone()[0]

    if data_exists:
        conn.close()
        return  # Prevents API call if data is already there

    conn.close()

    # Fetch data from API (unchanged)
    base_url = "https://financialmodelingprep.com/api/v3/"
    try:
        response_profile = requests.get(f"{base_url}profile/{ticker}?apikey={API_KEY}")
        response_metrics = requests.get(f"{base_url}key-metrics/{ticker}?apikey={API_KEY}")
        response_ratios = requests.get(f"{base_url}ratios/{ticker}?apikey={API_KEY}")

        response_profile.raise_for_status()
        response_metrics.raise_for_status()
        response_ratios.raise_for_status()

        profile_data = response_profile.json()[0] if response_profile.json() else {}
        key_metrics = response_metrics.json()[0] if response_metrics.json() else {}
        ratios_data = response_ratios.json()[0] if response_ratios.json() else {}

        # Store fetched data
        store_fundamentals({
            "ticker": ticker,
            "sector": profile_data.get("sector", "Unknown"),
            "pe_ratio": key_metrics.get("peRatio") or ratios_data.get("priceEarningsRatio"),
            "market_cap": profile_data.get("mktCap"),
            "revenue": profile_data.get("revenue") or key_metrics.get("revenue"),
            "beta": profile_data.get("beta"),
            "roa": key_metrics.get("returnOnAssets") or ratios_data.get("returnOnAssets"),
            "roe": key_metrics.get("returnOnEquity") or ratios_data.get("returnOnEquity")
        })

    except requests.exceptions.RequestException as e:
        print(f"Error fetching fundamental data for {ticker}: {e}")


def store_fundamentals(data):
    """Stores fetched fundamental data into the database while preserving cluster assignments."""
    if data is None:
        return

    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Preserve existing cluster assignments
        cursor.execute("SELECT cluster FROM fundamentals WHERE ticker = ?", (data["ticker"],))
        existing_cluster = cursor.fetchone()
        cluster_value = existing_cluster[0] if existing_cluster else None

        cursor.execute("""
            INSERT INTO fundamentals (
                ticker, sector, pe_ratio, market_cap, revenue, beta, roa, roe, cluster
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET 
                sector=excluded.sector,
                pe_ratio=excluded.pe_ratio,
                market_cap=excluded.market_cap,
                revenue=excluded.revenue,
                beta=excluded.beta,
                roa=excluded.roa,
                roe=excluded.roe
        """, (
            data["ticker"], data["sector"], data["pe_ratio"],
            data["market_cap"], data["revenue"], data["beta"], data["roa"], data["roe"],
            cluster_value  # Preserve existing cluster
        ))

        conn.commit()
       
    except sqlite3.Error as e:
        print(f"SQLite Database Error: {e}")
    finally:
        conn.close()