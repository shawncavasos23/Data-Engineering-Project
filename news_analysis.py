import feedparser  # type: ignore
import datetime
import logging
from urllib.parse import quote
from sqlalchemy import text  # type: ignore
from sqlalchemy.engine import Engine  # type: ignore

# Further Improvement: Improve relevance for short/ambiguous tickers
company_alias = {
    "A": "Agilent Technologies",
    "T": "AT&T",
    "F": "Ford Motor Company",
    "C": "Citigroup",
    "B": "Barnes Group",
    "H": "Hyatt Hotels Corporation",
    "K": "Kellogg Company"
}


def fetch_news(ticker: str, engine: Engine, limit: int = 10):
    """Fetches the latest news articles from Google News RSS for a given stock ticker 
    and inserts only new, relevant records into the database."""

    try:
        # Get the latest timestamp from the database
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT MAX(published_at) FROM news WHERE ticker = :ticker"),
                {"ticker": ticker}
            )
            last_published_at = result.scalar()

        if last_published_at:
            try:
                last_published_at = datetime.datetime.strptime(last_published_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                last_published_at = None

        # Build RSS query with company context
        company_name = company_alias.get(ticker.upper(), ticker)
        search_query = f'"{company_name}" stock OR {ticker} stock'
        encoded_query = quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        feed = feedparser.parse(rss_url)

        if getattr(feed, "status", 200) != 200:
            logging.warning(f"Google News RSS returned status {feed.status} for {ticker}")
            return

        articles = feed.entries[:limit]
        if not articles:
            logging.info(f"No new news articles found for {ticker}.")
            return

        new_articles = []
        for article in articles:
            source = article.get("source", {}).get("title", "Unknown")
            title = article.get("title", "").strip()
            description = article.get("summary", "").strip()
            url = article.get("link", "").strip()
            published_at = article.get("published", "")

            if not title or not url or not published_at:
                continue

            try:
                published_at_dt = datetime.datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                continue

            if last_published_at and published_at_dt <= last_published_at:
                continue

            new_articles.append({
                "ticker": ticker,
                "source": source,
                "title": title,
                "description": description,
                "url": url,
                "published_at": published_at_dt.strftime("%Y-%m-%d %H:%M:%S")
            })

        if new_articles:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT OR IGNORE INTO news (ticker, source, title, description, url, published_at)
                    VALUES (:ticker, :source, :title, :description, :url, :published_at)
                """), new_articles)

            logging.info(f"Inserted {len(new_articles)} new articles for {ticker}.")

    except Exception as e:
        logging.error(f"Error fetching news for {ticker}: {e}")


def run_news_analysis(ticker: str, engine: Engine) -> dict:
    """Fetch latest news articles and return mention count for the given ticker."""
    fetch_news(ticker, engine)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM news WHERE ticker = :ticker"),
                {"ticker": ticker}
            )
            count = result.scalar() or 0
            return {"ticker": ticker, "news_mentions": count}
    except Exception as e:
        logging.error(f"Error counting news mentions for {ticker}: {e}")
        return {"ticker": ticker, "news_mentions": 0}
