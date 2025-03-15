import praw  # type: ignore
import datetime
import sqlite3
import time
from database import create_connection

# Reddit API Credentials
REDDIT_CLIENT_ID = "iGbUVH-wZqqHRysT7wIEfg"
REDDIT_CLIENT_SECRET = "iHq4HqhFESF3WiyLV6mRvCdNdKR_6Q"
REDDIT_USER_AGENT = "RefrigeratorFew6940:WSB-Tracker:v1.0"

# Connect to Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_recent_ticker_mentions(ticker):
    """Fetch recent mentions of a stock ticker from WallStreetBets."""
    subreddit = reddit.subreddit("wallstreetbets")
    mentions = []
    
    one_year_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)

    for post in subreddit.search(f"${ticker}", limit=1000):  # Fetch up to 1000 mentions
        post_time = datetime.datetime.fromtimestamp(post.created_utc, datetime.timezone.utc)

        if post_time >= one_year_ago:
            upvotes = post.score
            upvote_ratio = post.upvote_ratio
            downvotes = int(upvotes * (1 - upvote_ratio))  
            link = "https://www.reddit.com" + post.permalink
            content = post.selftext[:500] if post.selftext else "No content available"  # Limit content length

            mentions.append((ticker, post.title, content, upvotes, upvote_ratio, post_time, link))

    return mentions

def store_reddit_mentions(ticker):
    """Fetch and store Reddit mentions in the database while preventing duplicates."""
    
    conn = create_connection()
    cursor = conn.cursor()

    # Ensure the ticker exists in `fundamentals`
    cursor.execute("SELECT COUNT(*) FROM fundamentals WHERE ticker = ?", (ticker,))
    ticker_exists = cursor.fetchone()[0]
    
    if not ticker_exists:
        print(f"{ticker} not found in fundamentals table. Skipping Reddit mentions.")
        conn.close()
        return  

    mentions = get_recent_ticker_mentions(ticker)

    if not mentions:
        print(f"No new mentions found for {ticker}. Skipping database update.")
        conn.close()
        return  

    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO reddit_mentions (ticker, title, content, upvotes, upvote_ratio, date, link)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, mentions)

        conn.commit()

    except sqlite3.IntegrityError as e:
        print(f"Integrity error storing Reddit mentions for {ticker}: {e}")

    except Exception as e:
        print(f"Database error storing Reddit mentions: {e}")

    finally:
        conn.close()

def run_reddit_analysis(ticker):
    """Fetch and store Reddit mentions, then return the mention count."""
    store_reddit_mentions(ticker)

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM reddit_mentions WHERE ticker = ?", (ticker,))
        mention_count = cursor.fetchone()[0] or 0
        return {"ticker": ticker, "reddit_mentions": mention_count}

    except Exception as e:
        print(f"Database error retrieving Reddit mentions count: {e}")
        return {"ticker": ticker, "reddit_mentions": 0}

    finally:
        conn.close()
