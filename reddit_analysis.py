import praw # type: ignore
import datetime
import sqlite3
import pandas as pd # type: ignore
import matplotlib.pyplot as plt # type: ignore
import nltk # type: ignore
from textblob import TextBlob # type: ignore
from nltk.sentiment import SentimentIntensityAnalyzer # type: ignore
from pytrends.request import TrendReq # type: ignore

# 🔹 Reddit API Credentials
REDDIT_CLIENT_ID = "iGbUVH-wZqqHRysT7wIEfg"
REDDIT_CLIENT_SECRET = "iHq4HqhFESF3WiyLV6mRvCdNdKR_6Q"
REDDIT_USER_AGENT = "RefrigeratorFew6940:WSB-Tracker:v1.0"

# 🔹 Download NLTK VADER for sentiment analysis
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()

# 🔹 Connect to Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# 🔹 Fetch Reddit Data for a Specific Stock
def fetch_reddit_data(ticker):
    subreddit = reddit.subreddit("wallstreetbets")
    five_years_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=5*365)

    data = []
    for post in subreddit.search(f"{ticker}", limit=500):  # Fetch 500 posts max
        post_time = datetime.datetime.fromtimestamp(post.created_utc, datetime.timezone.utc)
        if post_time >= five_years_ago:
            sentiment = sia.polarity_scores(post.title)["compound"]
            upvotes = post.score
            upvote_ratio = post.upvote_ratio
            link = "https://www.reddit.com" + post.permalink

            # 🔹 Fetch `content` (limit to 500 chars, fallback to "No content available")
            content = post.selftext[:500] if post.selftext else "No content available"

            data.append((ticker, post.title, content, sentiment, post_time, upvotes, upvote_ratio, link))

    return data

# 🔹 Save Data to Database
def save_to_database(data):
    if not data:
        return

    conn = sqlite3.connect("trading_data.db")
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT OR IGNORE INTO reddit_mentions (ticker, title, content, sentiment, time, upvotes, upvote_ratio, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()

# 🔹 Fetch and Store Data for the Imported `tickers`
def fetch_selected_tickers():
    for i, ticker in enumerate(ticker):
        print(f"Fetching Reddit data for {ticker} ({i+1}/{len(ticker)})...")
        data = fetch_reddit_data(ticker)
        save_to_database(data)
    print("Fetch Done!")

fetch_selected_tickers()  # Run the function to fetch data