import requests # type: ignore
import sqlite3

NEWS_API_KEY =  "da4034cbcb214777a510dd89b5b9bb69"

def create_news_database():
    """Creates the news database if it does not exist."""
    conn = sqlite3.connect("trading_data.db")
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
    conn.close()

def fetch_news():
    """Fetch latest financial news headlines from NewsAPI and store in SQLite."""
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])[:10]

            conn = sqlite3.connect("trading_data.db")
            cursor = conn.cursor()

            for article in articles:
                cursor.execute("""
                    INSERT OR IGNORE INTO news (source, title, description, url, published_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article["source"]["name"],
                    article["title"],
                    article["description"],
                    article["url"],
                    article["publishedAt"]
                ))

            conn.commit()
            conn.close()
            print("Latest news stored in database.")

    except Exception as e:
        print(f"Error fetching news: {e}")
