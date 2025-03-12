import requests  # type: ignore
import sqlite3
import datetime

NEWS_API_KEY = "da4034cbcb214777a510dd89b5b9bb69"

def initialize_database():
    """Creates the news database if it does not exist."""
    with sqlite3.connect("trading_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL UNIQUE,
                published_at DATETIME NOT NULL,
                UNIQUE(title, published_at)
            )
        """)
        conn.commit()

def fetch_news(ticker):
    """Fetches the latest news articles for a given stock ticker from NewsAPI and stores them in SQLite."""
    
    conn = sqlite3.connect("trading_data.db")
    cursor = conn.cursor()

    # Get the latest `published_at` timestamp from the database
    cursor.execute("SELECT MAX(published_at) FROM news WHERE title LIKE ?", (f"%{ticker}%",))
    last_published_at = cursor.fetchone()[0]

    # If no news is found in the database, fetch all available articles
    if last_published_at:
        try:
            last_published_at = datetime.datetime.strptime(last_published_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            last_published_at = None  # Reset if the format is invalid

    url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()

        if data.get("status") != "ok":
            print(f"Error from NewsAPI: {data.get('message', 'Unknown error')}")
            return

        articles = data.get("articles", [])[:10]  # Limit to 10 latest articles

        if not articles:
            print(f"No new news articles found for {ticker}.")
            return

        new_articles = []
        for article in articles:
            source = article.get("source", {}).get("name", "Unknown")
            title = article.get("title", "").strip()
            description = article.get("description", "").strip()
            url = article.get("url", "").strip()
            published_at = article.get("publishedAt", "")

            if not title or not url or not published_at:
                continue  # Skip incomplete articles

            try:
                published_at_dt = datetime.datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue  # Skip article if date format is incorrect

            # Only insert new articles published after the last known date
            if last_published_at and published_at_dt <= last_published_at:
                continue

            new_articles.append((source, title, description, url, published_at_dt.strftime("%Y-%m-%d %H:%M:%S")))

        # Insert new articles into database
        if new_articles:
            cursor.executemany("""
                INSERT OR IGNORE INTO news (source, title, description, url, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, new_articles)
            conn.commit()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {ticker}: {e}")

    finally:
        conn.close()