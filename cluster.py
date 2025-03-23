import numpy as np
import pandas as pd
import logging
from sklearn.cluster import KMeans # type: ignore
from sklearn.preprocessing import StandardScaler # type: ignore
from kneed import KneeLocator # type: ignore
from sqlalchemy import text # type: ignore
from sqlalchemy.engine import Engine # type: ignore

def find_peers(ticker: str, engine: Engine) -> list[str]:
    """Find similar stocks in the same sector using K-Means clustering."""
    try:
        with engine.connect() as conn:
            # 1. Get sector of the target ticker
            result = conn.execute(text("SELECT sector FROM fundamentals WHERE ticker = :ticker"), {"ticker": ticker})
            row = result.fetchone()
            if not row:
                logging.warning(f"Ticker {ticker} not found in fundamentals.")
                return []

            sector = row[0]

            # 2. Fetch fundamental data for stocks in the same sector
            query = text("""
                SELECT ticker, pe_ratio, market_cap, revenue, beta, roa, roe, dividend_yield, 
                       dividend_per_share, total_debt, total_cash, free_cash_flow, 
                       operating_cash_flow, net_income
                FROM fundamentals
                WHERE sector = :sector
            """)
            result = conn.execute(query, {"sector": sector})
            data = result.fetchall()
            columns = result.keys()

        if len(data) < 20:
            logging.warning(f"Not enough data in sector {sector} for clustering.")
            return []

        # 3. Prepare DataFrame
        df = pd.DataFrame(data, columns=columns)
        df.set_index("ticker", inplace=True)

        # 4. Impute missing values with sector medians
        df.fillna(df.median(), inplace=True)

        # 5. Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(df.values)

        # 6. Find optimal number of clusters
        distortions = []
        K = range(1, min(11, len(df)))
        for k in K:
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            model.fit(features_scaled)
            distortions.append(model.inertia_)

        kneedle = KneeLocator(K, distortions, curve="convex", direction="decreasing")
        optimal_k = kneedle.elbow

        if optimal_k is None:
            logging.warning("Could not determine optimal number of clusters.")
            return []

        # 7. Perform clustering
        model = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        df["cluster"] = model.fit_predict(features_scaled)

        # 8. Return peer group (excluding self)
        ticker_cluster = df.loc[ticker, "cluster"]
        peers = df[df["cluster"] == ticker_cluster].index.tolist()
        return [t for t in peers if t != ticker]

    except Exception as e:
        logging.error(f"Error during peer clustering for {ticker}: {e}")
        return []


# Optional: CLI Interface
if __name__ == "__main__":
    import argparse
    from db_utils import get_sqlalchemy_engine

    parser = argparse.ArgumentParser(description="Find similar stocks using clustering.")
    parser.add_argument("ticker", type=str, help="Stock ticker to find peers for")
    args = parser.parse_args()

    engine = get_sqlalchemy_engine()
    peers = find_peers(args.ticker.upper(), engine)

    if peers:
        print(f"Peers for {args.ticker.upper()}: {', '.join(peers)}")
    else:
        print("No peers found.")
