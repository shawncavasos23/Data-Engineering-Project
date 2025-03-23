import sqlite3
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans  # type: ignore
from sklearn.preprocessing import StandardScaler # type: ignore
from kneed import KneeLocator  # type: ignore
from db_utils import create_connection

def find_peers(ticker):
    """Find similar stocks using K-Means clustering within the same sector."""
    conn = create_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    
    # Get the sector of the given ticker
    cursor.execute("SELECT sector FROM fundamentals WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if row is None:
        print("Ticker not found in database.")
        return []
    sector = row[0]
    
    # Get all stocks in the same sector with available data
    cursor.execute("""
        SELECT ticker, pe_ratio, market_cap, revenue, beta, roa, roe, dividend_yield, dividend_per_share,
               total_debt, total_cash, free_cash_flow, operating_cash_flow, net_income
        FROM fundamentals WHERE sector = ?
    """, (sector,))
    data = cursor.fetchall()
    conn.close()
    
    if len(data) < 20:
        print("Not enough available stocks in the sector for clustering.")
        return []
    
    # Convert to DataFrame for better handling
    columns = ["ticker", "pe_ratio", "market_cap", "revenue", "beta", "roa", "roe", "dividend_yield", 
               "dividend_per_share", "total_debt", "total_cash", "free_cash_flow", "operating_cash_flow", "net_income"]
    df = pd.DataFrame(data, columns=columns)
    df.set_index("ticker", inplace=True)
    
    # Handle missing values by filling with sector median
    df.fillna(df.median(), inplace=True)
    features = df.values
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Determine optimal number of clusters using the Kneedle algorithm
    distortions = []
    K = range(1, min(11, len(df)))  # Limit to avoid excessive clusters
    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(features_scaled)
        distortions.append(kmeans.inertia_)
    
    kneedle = KneeLocator(K, distortions, curve="convex", direction="decreasing")
    optimal_k = kneedle.elbow
    
    if optimal_k is None:
        print("Could not determine optimal number of clusters.")
        return []
    
    # Perform clustering
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)
    
    # Assign peer groups based on clustering
    df["cluster"] = labels
    
    # Find the cluster for the given ticker
    ticker_cluster = df.loc[ticker, "cluster"]
    peers = df[df["cluster"] == ticker_cluster].index.tolist()
    
    return [t for t in peers if t != ticker]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Find stock peers using clustering.")
    parser.add_argument("ticker", type=str, help="Stock ticker to find peers for")
    args = parser.parse_args()
    
    peers = find_peers(args.ticker)
    if peers:
        print(f"Peers for {args.ticker}: {', '.join(peers)}")
    else:
        print("No peers found.")