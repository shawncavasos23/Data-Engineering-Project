import praw # type: ignore
import datetime
import sqlite3
import pandas as pd # type: ignore
from pytrends.request import TrendReq # type: ignore
from database import create_connection

# Reddit API credentials
REDDIT_CLIENT_ID = "iGbUVH-wZqqHRysT7wIEfg"
REDDIT_CLIENT_SECRET = "iHq4HqhFESF3WiyLV6mRvCdNdKR_6Q"
REDDIT_USER_AGENT = "RefrigeratorFew6940:WSB-Tracker:v1.0"

# 🔹 Connect to Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_recent_ticker_mentions(ticker):
    """Fetch recent mentions of a stock ticker from Reddit's WallStreetBets."""
    print(f"Fetching Reddit mentions for {ticker}...")
    subreddit = reddit.subreddit("wallstreetbets")
    mentions = []
    
    one_year_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
    
    try:
        for post in subreddit.search(f"${ticker}", limit=500):
            post_time = datetime.datetime.fromtimestamp(post.created_utc, datetime.timezone.utc)
            if post_time >= one_year_ago:
                mentions.append(
                    (ticker, post.title, post.score, post.upvote_ratio, post_time.strftime("%Y-%m-%d"), "https://www.reddit.com" + post.permalink)
                )
    except Exception as e:
        print(f"⚠ Error fetching Reddit mentions for {ticker}: {e}")
        return []

    return mentions

def store_reddit_mentions(ticker):
    """Fetch and store Reddit mentions in the database."""
    mentions = get_recent_ticker_mentions(ticker)
    if not mentions:
        print(f"⚠ No new Reddit mentions found for {ticker}.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.executemany("""
            INSERT OR REPLACE INTO reddit_mentions (ticker, title, upvotes, upvote_ratio, date, link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, mentions)
        conn.commit()
        print(f"Stored {len(mentions)} Reddit mentions for {ticker}.")
    except Exception as e:
        print(f"Database error storing Reddit mentions: {e}")
    finally:
        conn.close()

def fetch_google_trends(ticker):
    """Fetch Google Trends data for a stock ticker."""
    print(f"Fetching Google Trends data for {ticker}...")
    pytrends = TrendReq(hl='en-US', tz=360)

    try:
        pytrends.build_payload([ticker], cat=0, timeframe='today 12-m', geo='', gprop='')
        df = pytrends.interest_over_time()
        if df.empty:
            print(f"⚠ No Google Trends data available for {ticker}.")
            return []

        return [(ticker, date.strftime("%Y-%m-%d"), int(value)) for date, value in df[ticker].items()]
    except Exception as e:
        print(f"Error fetching Google Trends data for {ticker}: {e}")
        return []

def store_google_trends(ticker):
    """Fetch and store Google Trends data in the database."""
    trends = fetch_google_trends(ticker)
    if not trends:
        print(f"No Google Trends data to store for {ticker}.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.executemany("""
            INSERT OR REPLACE INTO google_trends (ticker, date, search_interest)
            VALUES (?, ?, ?)
        """, trends)
        conn.commit()
        print(f"Stored {len(trends)} Google Trends records for {ticker}.")
    except Exception as e:
        print(f"⚠ Database error storing Google Trends data: {e}")
    finally:
        conn.close()

def run_reddit_analysis(ticker):
    """Fetch and store Reddit mentions & Google Trends data for a ticker."""
    store_reddit_mentions(ticker)
    store_google_trends(ticker)

    return {"ticker": ticker, "reddit_mentions": len(get_recent_ticker_mentions(ticker)), "google_trends": len(fetch_google_trends(ticker))}
