import praw # type: ignore
import datetime
import logging
import nltk # type: ignore
from nltk.sentiment import SentimentIntensityAnalyzer # type: ignore
from sqlalchemy import text # type: ignore
from sqlalchemy.engine import Engine # type: ignore
import math

# Download VADER if needed
nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

# Reddit API Credentials
REDDIT_CLIENT_ID = "iGbUVH-wZqqHRysT7wIEfg"
REDDIT_CLIENT_SECRET = "iHq4HqhFESF3WiyLV6mRvCdNdKR_6Q"
REDDIT_USER_AGENT = "RefrigeratorFew6940:WSB-Tracker:v1.0"

# Reddit API Client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_recent_ticker_mentions(ticker: str):
    """Scrape recent mentions of a ticker from WallStreetBets with sentiment scoring."""
    subreddit = reddit.subreddit("wallstreetbets")
    mentions = []
    one_year_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)

    for post in subreddit.search(f"${ticker}", limit=1000):
        post_time = datetime.datetime.fromtimestamp(post.created_utc, datetime.timezone.utc)
        if post_time < one_year_ago:
            continue

        upvotes = post.score
        upvote_ratio = post.upvote_ratio
        content = post.selftext[:500] if post.selftext else ""
        link = "https://www.reddit.com" + post.permalink
        sentiment = sia.polarity_scores(post.title + " " + content)["compound"]
        impact = sentiment * math.log(upvotes+1) * upvote_ratio / (1 + math.exp((datetime.datetime.now(datetime.timezone.utc) - post_time).days - 5))


        mentions.append({
            "ticker": ticker,
            "title": post.title.strip(),
            "content": content.strip(),
            "sentiment": sentiment,
            "upvotes": upvotes,
            "upvote_ratio": upvote_ratio,
            "date": post_time.strftime("%Y-%m-%d"),
            "link": link,
            'impact_score': impact
        })

    return mentions


def store_reddit_mentions(ticker: str, engine: Engine):
    """Store Reddit mentions for a given ticker using SQLAlchemy."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM fundamentals WHERE ticker = :ticker"),
                {"ticker": ticker}
            )
            if result.scalar() == 0:
                logging.warning(f"Ticker {ticker} not found in fundamentals. Skipping Reddit mentions.")
                return

        mentions = get_recent_ticker_mentions(ticker)
        if not mentions:
            logging.info(f"No new Reddit mentions found for {ticker}.")
            return

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO reddit_mentions
                (ticker, title, content, sentiment, upvotes, upvote_ratio, date, link, impact_score)
                VALUES (:ticker, :title, :content, :sentiment, :upvotes, :upvote_ratio, :date, :link, :impact_score)
            """), mentions)

        logging.info(f"Inserted {len(mentions)} Reddit mentions for {ticker}.")

    except Exception as e:
        logging.error(f"Error storing Reddit mentions for {ticker}: {e}")


def run_reddit_analysis(ticker: str, engine: Engine) -> dict:
    """Run Reddit scrape and return mention count for the ticker."""
    store_reddit_mentions(ticker, engine)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM reddit_mentions WHERE ticker = :ticker"),
                {"ticker": ticker}
            )
            count = result.scalar() or 0
            return {"ticker": ticker, "reddit_mentions": count}

    except Exception as e:
        logging.error(f"Error retrieving Reddit mention count for {ticker}: {e}")
        return {"ticker": ticker, "reddit_mentions": 0}
