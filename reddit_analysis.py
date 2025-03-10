import praw
import datetime
import sqlite3
import pandas as pd
from pytrends.request import TrendReq
from database import create_connection

# 🔹 Reddit API credentials
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
REDDIT_USER_AGENT = "your_user_agent"

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def get_recent_ticker_mentions(ticker):
    """Fetch recent mentions of a stock ticker from Reddit's WallStreetBets."""
    subreddit = reddit.subreddit("wallstreetbets")
    mentions = []
    
    one_year_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
    
    for post in subreddit.search(f"${ticker}", limit=500):
        post_time = datetime.datetime.fromtimestamp(post.created_utc, datetime.timezone.utc)
        if post_time >= one_year_ago:
            mentions.append((ticker, post.title, post.score, post.upvote_ratio, post_time.strftime("%Y-%m-%d"), "https://www.reddit.com" + post.permalink))
    return mentions

def fetch_google_trends(ticker):
    """Fetch Google Trends data for a stock ticker."""
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload([ticker], cat=0, timeframe='today 12-m', geo='', gprop='')
    df = pytrends.interest_over_time()
    return [(ticker, date, int(value)) for date, value in df[ticker].items()]

def run_reddit_analysis(ticker):
    """Fetch & store Reddit mentions & Google Trends data."""
    mentions = get_recent_ticker_mentions(ticker)
    trends = fetch_google_trends(ticker)
    return {"ticker": ticker, "reddit_mentions": len(mentions), "google_trends": len(trends)}
