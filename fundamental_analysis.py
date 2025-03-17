import requests
import sqlite3
import itertools
from db_utils import create_connection

API_KEYS = [
    "rEwY9uKTA66xG5uK8CAifKsu9tSAzuHd", "6hY6I1N27gM7IE4suNpVNaUHxBeZw6yc",
    "oFLf4RZvkY3ksOBQ71PM39Cv84WOqqyV", "ug8ggu6nmS3NV6CAjIHD0k1YDeaTIk3w",
    "QaJCrea0m0Jw3X5xNID0b1KKOg3dPUrX", "fMFlUxLxqKwq6qHuYJ9YBIBxwy8drfZM",
    "ujyGSVIOvjWkHMygBvlLziESGhxiUoaG", "CCzHGrEB1dVVVkw11xxwZb6o0UeUu3Yh",
    "pgGOVJAlfchwFlvfcuuAqMukqbPIPK2a", "c8DQ6I283ArGIPx2fxxzG5NOECdB0AzM",
    "h3WqRv1L1aDOlqjTJSOSyTuQOgav3lFZ", "iUwc8g8lNedeWfEg1NwUnvXGM4iIL3ps",
    "cDWmTbAqq82eINliWSFxn4yVv1GbseJH", "IMgmBYeGkVlNgAwdP5xWXqbMNNEewnHl",
    "oDjz2EDlkZhIbdN18m1yOfDxSZkC7i31", "v1s0mDIr0tBLQJi9tf5aHYv6Iqn9EphC",
    "3f08L5h73zYFlEEtw1pg5JKC8qdR7nAR", "rXR0PrHyt4Vcdn1yqWhklKNSZfdGV9qU",
    "EtzquuX82cOSuWHSTqLfS2aP1D3uhLaT", "VrIWXD4KjvZ07IdwmyD81SDJzAjydQtr",
    "WhuS8fEd9aOh7edtwjUBHhznNdc0fdwx", "hPCjYsWS9RDgqCjJCH2mXa3CCk5LR1lu"
]

api_key_cycle = itertools.cycle(API_KEYS)  # Rotate through API keys

def get_fundamental_data(ticker):
    """Fetch fundamental financial data for a stock and store it in SQLite."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check if fundamentals exist
    cursor.execute("""
        SELECT COUNT(*) FROM fundamentals 
        WHERE ticker = ? AND market_cap IS NOT NULL
    """, (ticker,))
    data_exists = cursor.fetchone()[0]

    if data_exists:
        conn.close()
        return  # Prevent API call if data already exists

    conn.close()

    base_url = "https://financialmodelingprep.com/api/v3/"
    endpoints = {
        "profile": f"profile/{ticker}",
        "metrics": f"key-metrics/{ticker}",
        "ratios": f"ratios/{ticker}",
        "dividends": f"historical-price-full/stock_dividend/{ticker}",
        "balance_sheet": f"balance-sheet-statement/{ticker}",
        "cash_flow": f"cash-flow-statement/{ticker}"
    }

    try:
        data = {}
        for key, endpoint in endpoints.items():
            success = False
            while not success:
                api_key = next(api_key_cycle)  # Get next API key
                url = f"{base_url}{endpoint}?apikey={api_key}"
                
                response = requests.get(url)
                
                if response.status_code == 429:  # Too many requests
                    print(f"Rate limit exceeded for {api_key}, switching API key...")
                    continue  # Try the next API key
                
                response.raise_for_status()
                json_data = response.json()
                data[key] = json_data[0] if isinstance(json_data, list) and json_data else {}
                success = True  # Exit loop once successful response is received

        # Extract relevant metrics
        metrics = {
            "ticker": ticker,
            "sector": data["profile"].get("sector", "Unknown"),
            "pe_ratio": data["profile"].get("peRatio") or data["ratios"].get("priceEarningsRatio"),
            "market_cap": data["profile"].get("mktCap"),
            "revenue": data["profile"].get("revenue") or data["metrics"].get("revenuePerShare"),
            "beta": data["profile"].get("beta"),
            "roa": data["ratios"].get("returnOnAssets"),
            "roe": data["ratios"].get("returnOnEquity"),
            "dividend_yield": data["dividends"].get("dividendYield"),
            "dividend_per_share": data["dividends"].get("dividend"),
            "total_debt": data["balance_sheet"].get("totalDebt"),
            "total_cash": data["balance_sheet"].get("cashAndShortTermInvestments"),
            "free_cash_flow": data["cash_flow"].get("freeCashFlow"),
            "operating_cash_flow": data["cash_flow"].get("operatingCashFlow"),
            "net_income": data["cash_flow"].get("netIncome")
        }

        store_fundamentals(metrics)
    
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
                ticker, sector, pe_ratio, market_cap, revenue, beta, roa, roe, 
                dividend_yield, dividend_per_share, total_debt, total_cash, 
                free_cash_flow, operating_cash_flow, net_income, cluster
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET 
                sector=excluded.sector,
                pe_ratio=excluded.pe_ratio,
                market_cap=excluded.market_cap,
                revenue=excluded.revenue,
                beta=excluded.beta,
                roa=excluded.roa,
                roe=excluded.roe,
                dividend_yield=excluded.dividend_yield,
                dividend_per_share=excluded.dividend_per_share,
                total_debt=excluded.total_debt,
                total_cash=excluded.total_cash,
                free_cash_flow=excluded.free_cash_flow,
                operating_cash_flow=excluded.operating_cash_flow,
                net_income=excluded.net_income
        """, (
            data["ticker"], data["sector"], data["pe_ratio"], data["market_cap"], 
            data["revenue"], data["beta"], data["roa"], data["roe"], 
            data["dividend_yield"], data["dividend_per_share"], data["total_debt"], 
            data["total_cash"], data["free_cash_flow"], data["operating_cash_flow"], 
            data["net_income"], cluster_value
        ))
        conn.commit()

    except sqlite3.Error as e:
        print(f"SQLite Database Error: {e}")
    finally:
        conn.close()
