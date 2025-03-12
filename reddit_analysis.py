import praw  # type: ignore
import datetime
import sqlite3
import time
from database import create_connection

# 🔹 Reddit API Credentials
REDDIT_CLIENT_ID = "iGbUVH-wZqqHRysT7wIEfg"
REDDIT_CLIENT_SECRET = "iHq4HqhFESF3WiyLV6mRvCdNdKR_6Q"
REDDIT_USER_AGENT = "RefrigeratorFew6940:WSB-Tracker:v1.0"

# 🔹 Connect to Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_recent_ticker_mentions(ticker, limit=200):
    """Fetch recent mentions of a stock ticker from r/wallstreetbets."""
    mentions = []
    one_year_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)

    try:
        for post in reddit.subreddit("wallstreetbets").new(limit=limit):  
            post_time = datetime.datetime.fromtimestamp(post.created_utc, datetime.timezone.utc)
            
            if post_time >= one_year_ago and f"${ticker}" in post.title:
                mentions.append((
                    ticker,
                    post.title,
                    post.score,
                    post.upvote_ratio if post.upvote_ratio is not None else 0.0,  # Handle `NoneType`
                    post_time.strftime("%Y-%m-%d"),
                    f"https://www.reddit.com{post.permalink}"
                ))
        
        time.sleep(1)  # Prevent API rate limits

    except praw.exceptions.APIException as e:
        print(f"⚠ Reddit API Error: {e}")
    except Exception as e:
        print(f"⚠ Error fetching Reddit mentions for {ticker}: {e}")

    return mentions

def store_reddit_mentions(ticker):
    """Fetch and store Reddit mentions in the database."""
    mentions = get_recent_ticker_mentions(ticker)
    
    if not mentions:
        return  # No mentions, no need to store anything

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO reddit_mentions (ticker, title, upvotes, upvote_ratio, date, link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, mentions)
        conn.commit()
    except Exception as e:
        print(f"⚠ Database error storing Reddit mentions: {e}")
    finally:
        conn.close()


def run_reddit_analysis(ticker):
    """Fetch and store Reddit mentions."""
    store_reddit_mentions(ticker)
    return {"ticker": ticker, "reddit_mentions": len(get_recent_ticker_mentions(ticker))}
