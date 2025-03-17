import feedparser  # type: ignore
import sqlite3
import datetime

def initialize_database():
    """Creates the news database if it does not exist."""
    with sqlite3.connect("trading_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,  -- Each article is linked to a specific stock
                source TEXT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL UNIQUE,
                published_at DATETIME NOT NULL,
                UNIQUE(ticker, title, published_at),
                FOREIGN KEY (ticker) REFERENCES fundamentals(ticker) ON DELETE CASCADE
            )
        """)
        conn.commit()

def fetch_news(ticker, limit=10):
    """Fetches the latest news articles for a given stock ticker from Google News RSS and stores them under the correct ticker."""

    conn = sqlite3.connect("trading_data.db")
    cursor = conn.cursor()

    # Get the latest `published_at` timestamp for this specific ticker
    cursor.execute("SELECT MAX(published_at) FROM news WHERE ticker = ?", (ticker,))
    last_published_at = cursor.fetchone()[0]

    # Convert timestamp to datetime object
    if last_published_at:
        try:
            last_published_at = datetime.datetime.strptime(last_published_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            last_published_at = None  # Reset if format is invalid

    # Google News RSS URL (fetches news specifically for the given ticker)
    google_news_rss_url = f"https://news.google.com/rss/search?q={ticker}&hl=en-US&gl=US&ceid=US:en"

    try:
        # Fetch RSS feed
        feed = feedparser.parse(google_news_rss_url)

        if feed.status != 200:
            print(f"Error fetching Google News RSS for {ticker}: {feed.status}")
            return

        articles = feed.entries[:limit]  # Limit number of articles

        if not articles:
            print(f"No new news articles found for {ticker}.")
            return

        new_articles = []
        for article in articles:
            source = article.get("source", {}).get("title", "Unknown")
            title = article.get("title", "").strip()
            description = article.get("summary", "").strip()
            url = article.get("link", "").strip()
            published_at = article.get("published", "")

            if not title or not url or not published_at:
                continue  # Skip incomplete articles

            try:
                published_at_dt = datetime.datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                continue  # Skip article if date format is incorrect

            # Only insert new articles published after the last known date
            if last_published_at and published_at_dt <= last_published_at:
                continue

            new_articles.append((ticker, source, title, description, url, published_at_dt.strftime("%Y-%m-%d %H:%M:%S")))

        # Insert new articles into the database
        if new_articles:
            cursor.executemany("""
                INSERT OR IGNORE INTO news (ticker, source, title, description, url, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, new_articles)
            conn.commit()

    except Exception as e:
        print(f"Error fetching news from Google RSS for {ticker}: {e}")

    finally:
        conn.close()

def run_news_analysis(ticker):
    """Fetch and store news from Google News RSS, then return the mention count from the database."""
    fetch_news(ticker)

    conn = sqlite3.connect("trading_data.db")
    cursor = conn.cursor()

    try:
        # Retrieve stored news count for the ticker
        cursor.execute("SELECT COUNT(*) FROM news WHERE ticker = ?", (ticker,))
        mention_count = cursor.fetchone()[0] or 0
        return {"ticker": ticker, "news_mentions": mention_count}

    except Exception as e:
        print(f"Database error retrieving news mentions count for {ticker}: {e}")
        return {"ticker": ticker, "news_mentions": 0}

    finally:
        conn.close()
