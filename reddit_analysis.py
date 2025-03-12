import praw  # type: ignore
import datetime
import sqlite3
import time
from database import create_connection

# Reddit API Credentials (Ensure these are set securely in environment variables)
REDDIT_CLIENT_ID = "iGbUVH-wZqqHRysT7wIEfg"
REDDIT_CLIENT_SECRET = "iHq4HqhFESF3WiyLV6mRvCdNdKR_6Q"
REDDIT_USER_AGENT = "RefrigeratorFew6940:WSB-Tracker:v1.0"

# Connect to Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_recent_ticker_mentions(ticker, limit=20):
    """Fetch recent mentions of a stock ticker from r/wallstreetbets."""
    mentions = []
    retry_attempts = 3

    print(f"Searching r/wallstreetbets for {ticker} mentions...")

    for attempt in range(retry_attempts):
        try:
            for post in reddit.subreddit("wallstreetbets").new(limit=limit):
                title_lower = post.title.lower()

                # Match both "$AAPL" and "AAPL"
                if f"${ticker.lower()}" in title_lower or f"{ticker.lower()}" in title_lower:
                    mentions.append((
                        ticker,
                        post.title,
                        post.score,
                        post.upvote_ratio if post.upvote_ratio is not None else 0.0,
                        datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d"),
                        f"https://www.reddit.com{post.permalink}"
                    ))

            time.sleep(3)  # Prevent API rate limits
            break  # Exit loop on success

        except praw.exceptions.APIException as e:
            print(f"Reddit API Error ({attempt+1}/{retry_attempts}): {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            print(f"Error fetching Reddit mentions for {ticker}: {e}")
            break  # Exit loop on unknown error

    print(f"Total mentions found: {len(mentions)}")
    return mentions

def store_reddit_mentions(ticker):
    """Fetch and store Reddit mentions in the database while preventing duplicate calls."""
    
    # Check if the ticker exists in fundamentals table
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fundamentals WHERE ticker = ?", (ticker,))
    ticker_exists = cursor.fetchone()[0]
    
    if not ticker_exists:
        print(f"⚠ {ticker} not found in fundamentals table. Skipping Reddit mentions.")
        conn.close()
        return  # If ticker is not found in fundamentals, do not insert into reddit_mentions

    mentions = get_recent_ticker_mentions(ticker)

    if not mentions:
        print(f"No new mentions found for {ticker}. Skipping database update.")
        conn.close()
        return  # No mentions, no need to store anything

    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO reddit_mentions (ticker, title, upvotes, upvote_ratio, date, link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, mentions)

        # Optionally store the mention count in trade_signals
        cursor.execute("""
            INSERT OR REPLACE INTO trade_signals (ticker, signal, date_generated)
            VALUES (?, 'REDDIT', DATE('now'))
        """, (ticker,))

        conn.commit()
        print(f"Stored {len(mentions)} Reddit mentions for {ticker}.")

    except sqlite3.IntegrityError as e:
        print(f"Integrity error while storing Reddit mentions for {ticker}: {e}")

    except Exception as e:
        print(f"Database error storing Reddit mentions: {e}")

    finally:
        conn.close()


def run_reddit_analysis(ticker):
    """Fetch and store Reddit mentions, then return the mention count from the database."""
    store_reddit_mentions(ticker)

    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Retrieve stored mention count
        cursor.execute("SELECT COUNT(*) FROM reddit_mentions WHERE ticker = ?", (ticker,))
        mention_count = cursor.fetchone()[0] or 0
        return {"ticker": ticker, "reddit_mentions": mention_count}

    except Exception as e:
        print(f"Database error retrieving Reddit mentions count: {e}")
        return {"ticker": ticker, "reddit_mentions": 0}

    finally:
        conn.close()
