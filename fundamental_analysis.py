import requests
import itertools
import logging
from sqlalchemy import text # type: ignore
from sqlalchemy.engine import Engine # type: ignore

# API Key Pool (rotating for rate limits)
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

api_key_cycle = itertools.cycle(API_KEYS)
BASE_URL = "https://financialmodelingprep.com/api/v3/"

def get_fundamental_data(ticker: str, engine: Engine) -> bool:
    """Fetch and store fundamental financial data for a stock using multiple endpoints."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM fundamentals WHERE ticker = :ticker AND market_cap IS NOT NULL"),
                {"ticker": ticker}
            )
            if result.scalar():
                logging.info(f"Skipping {ticker}: fundamentals already exist.")
                return True

        endpoints = {
            "profile": f"profile/{ticker}",
            "metrics": f"key-metrics/{ticker}",
            "ratios": f"ratios/{ticker}",
            "dividends": f"historical-price-full/stock_dividend/{ticker}",
            "balance_sheet": f"balance-sheet-statement/{ticker}",
            "cash_flow": f"cash-flow-statement/{ticker}"
        }

        data = {}
        for key, endpoint in endpoints.items():
            success = False
            while not success:
                api_key = next(api_key_cycle)
                url = f"{BASE_URL}{endpoint}?apikey={api_key}"
                response = requests.get(url)

                if response.status_code == 429:
                    logging.warning(f"Rate limit hit for {api_key}, rotating...")
                    continue

                response.raise_for_status()
                json_data = response.json()
                data[key] = json_data[0] if isinstance(json_data, list) and json_data else {}
                success = True

        metrics = {
            "ticker": ticker,
            "sector": data["profile"].get("sector", "Unknown"),
            "pe_ratio": data["profile"].get("peRatio") or data["ratios"].get("priceEarningsRatio"),
            "market_cap": data["profile"].get("mktCap"),
            "revenue": data["profile"].get("revenue") or data["metrics"].get("revenuePerShare"),
            "beta": data["profile"].get("beta"),
            "roa": data["ratios"].get("returnOnAssets"),
            "roe": data["ratios"].get("returnOnEquity"),
            "dividend_yield": data["ratios"].get("dividendYield"),
            "dividend_per_share": data["dividends"].get("dividend"),
            "total_debt": data["balance_sheet"].get("totalDebt"),
            "total_cash": data["balance_sheet"].get("cashAndShortTermInvestments"),
            "free_cash_flow": data["cash_flow"].get("freeCashFlow"),
            "operating_cash_flow": data["cash_flow"].get("operatingCashFlow"),
            "net_income": data["cash_flow"].get("netIncome")
        }

        store_fundamentals(metrics, engine)
        return True

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching fundamental data for {ticker}: {e}")
        return False


def store_fundamentals(data: dict, engine: Engine):
    """Insert or update fundamental data in the database while preserving cluster info."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT cluster FROM fundamentals WHERE ticker = :ticker"),
                {"ticker": data["ticker"]}
            )
            row = result.fetchone()
            cluster_value = row[0] if row else None

            conn.execute(text("""
                INSERT INTO fundamentals (
                    ticker, sector, pe_ratio, market_cap, revenue, beta, roa, roe,
                    dividend_yield, dividend_per_share, total_debt, total_cash,
                    free_cash_flow, operating_cash_flow, net_income, cluster
                ) VALUES (
                    :ticker, :sector, :pe_ratio, :market_cap, :revenue, :beta, :roa, :roe,
                    :dividend_yield, :dividend_per_share, :total_debt, :total_cash,
                    :free_cash_flow, :operating_cash_flow, :net_income, :cluster
                )
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
            """), {**data, "cluster": cluster_value})

        logging.info(f"Stored fundamentals for {data['ticker']}.")

    except Exception as e:
        logging.error(f"Error storing fundamentals for {data['ticker']}: {e}")
