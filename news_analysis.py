import requests  # type: ignore
import sqlite3
import datetime

NEWS_API_KEY = "da4034cbcb214777a510dd89b5b9bb69"

def create_news_database():
    """Creates the news database if it does not exist."""
    with sqlite3.connect("trading_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                title TEXT,
                description TEXT,
                url TEXT,
                published_at DATETIME,
                UNIQUE(title, published_at)
            )
        """)
        conn.commit()

def fetch_news(ticker):
    """Fetch news articles related to a specific stock ticker from NewsAPI."""
    url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])[:10]  # Limit to latest 10 articles

            if not articles:
                return  # No articles found, exit early

            with sqlite3.connect("trading_data.db") as conn:
                cursor = conn.cursor()

                for article in articles:
                    # Ensure all necessary fields exist
                    source = article.get("source", {}).get("name", "Unknown")
                    title = article.get("title", "").strip()
                    description = article.get("description", "").strip()
                    url = article.get("url", "").strip()
                    published_at = article.get("publishedAt", "")

                    # Convert ISO 8601 date format to SQLite-compatible format
                    if published_at:
                        try:
                            published_at = datetime.datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                        except ValueError:
                            continue  # Skip article if date format is incorrect

                    cursor.execute("""
                        INSERT OR IGNORE INTO news (source, title, description, url, published_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (source, title, description, url, published_at))

                conn.commit()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {ticker}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
