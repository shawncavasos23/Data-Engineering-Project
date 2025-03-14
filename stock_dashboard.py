import sys
import streamlit as st
import sqlite3
import pandas as pd  # type: ignore
import plotly.graph_objects as go  # type: ignore

# Set Streamlit page config
st.set_page_config(layout="wide")

# Custom CSS to move everything up
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Database Connection
DB_PATH = "trading_data.db"

@st.cache_data
def fetch_stock_data(ticker):
    """Fetch available stock data from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        fundamentals = pd.read_sql("SELECT * FROM fundamentals WHERE ticker = ?", conn, params=(ticker,))
        technicals = pd.read_sql("SELECT * FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 100", conn, params=(ticker,))
        macro_data = pd.read_sql("SELECT * FROM macroeconomic_data ORDER BY date DESC LIMIT 10", conn)
        news = pd.read_sql("SELECT * FROM news WHERE title LIKE ? ORDER BY published_at DESC LIMIT 5", conn, params=(f"%{ticker}%",))
        sentiment = pd.read_sql("SELECT * FROM reddit_mentions WHERE ticker = ? ORDER BY date DESC LIMIT 5", conn, params=(ticker,))
    
    return {
        "fundamentals": fundamentals,
        "technicals": technicals,
        "macro_data": macro_data,
        "news": news,
        "sentiment": sentiment
    }

def plot_candlestick_chart(data):
    """Generate an interactive candlestick chart with moving averages and Bollinger Bands."""
    if data.empty or not all(col in data.columns for col in ["date", "open", "high", "low", "close"]):
        return go.Figure()

    data["date"] = pd.to_datetime(data["date"])
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data["date"], open=data["open"], high=data["high"],
        low=data["low"], close=data["close"], name="Candlestick",
        increasing_line_color='green', decreasing_line_color='red'
    ))

    if "ma50" in data.columns:
        fig.add_trace(go.Scatter(x=data["date"], y=data["ma50"], mode='lines', name='50-Day MA', line=dict(color='blue')))
    if "ma200" in data.columns:
        fig.add_trace(go.Scatter(x=data["date"], y=data["ma200"], mode='lines', name='200-Day MA', line=dict(color='red')))
    
    fig.update_layout(
        title="Candlestick Chart",
        xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=700
    )
    return fig

def plot_rsi_chart(data):
    """Generate RSI Chart."""
    if data.empty or "rsi" not in data.columns:
        return go.Figure()
    
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data["date"], y=data["rsi"], mode='lines', name='RSI', line=dict(color='purple')))
    fig_rsi.update_layout(title="Relative Strength Index (RSI)", xaxis_title="Date", yaxis_title="RSI", template="plotly_white", height=400)
    return fig_rsi

def plot_volume_chart(data):
    """Generate an interactive volume chart."""
    if data.empty or "volume" not in data.columns:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data["date"], y=data["volume"], name="Volume", marker=dict(color='rgba(0, 0, 255, 0.3)')))
    fig.update_layout(title="Trading Volume", xaxis_title="Date", yaxis_title="Volume", template="plotly_white", height=400)
    return fig

def show_dashboard(ticker):
    """Display stock data in a structured layout."""
    st.title(f"{ticker} Stock Analysis Dashboard")
    
    ticker = st.sidebar.text_input("Enter Stock Ticker", value=ticker).upper()
    show_candlestick = st.sidebar.checkbox("Show Candlestick Chart", value=True)
    show_rsi = st.sidebar.checkbox("Show RSI Chart", value=True)
    show_volume = st.sidebar.checkbox("Show Volume Chart", value=True)
    num_news_articles = st.sidebar.slider("Number of News Articles", 1, 20, 5)
    num_reddit_mentions = st.sidebar.slider("Number of Reddit Mentions", 1, 20, 5)
    
    data = fetch_stock_data(ticker)
    
    col1, col2 = st.columns([7, 5])
    
    with col1:
        if show_candlestick:
            st.subheader("Candlestick Chart")
            st.plotly_chart(plot_candlestick_chart(data["technicals"]), use_container_width=True)
        
        rsi_col, volume_col = st.columns(2)
        if show_rsi:
            with rsi_col:
                st.subheader("RSI Indicator")
                st.plotly_chart(plot_rsi_chart(data["technicals"]), use_container_width=True)
        
        if show_volume:
            with volume_col:
                st.subheader("Volume Chart")
                st.plotly_chart(plot_volume_chart(data["technicals"]), use_container_width=True)
    
    with col2:
        st.subheader("Latest News")
        for _, row in data["news"].head(num_news_articles).iterrows():
            with st.container():
                st.markdown(
                    f"""
                    <div style="border:1px solid #ddd; padding:10px; border-radius:8px; background-color:#f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); margin-bottom:10px;">
                        <a href="{row['url']}" target="_blank" style="text-decoration:none; color:#0077cc; font-size:16px; font-weight:bold;">{row['title']}</a>
                        <p style="margin:5px 0; color:gray; font-size:12px;">{row['source']} | {row['published_at']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
        st.subheader("Reddit Sentiment")
        for _, row in data["sentiment"].head(num_reddit_mentions).iterrows():
            with st.container():
                st.markdown(
                    f"""
                    <div style="border:1px solid #ddd; padding:10px; border-radius:8px; background-color:#f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); margin-bottom:10px;">
                        <p style="font-size:16px; font-weight:bold;">{row['title']}</p>
                        <p style="margin:5px 0; color:gray; font-size:12px;">{row['content']}</p>
                        <p style="margin:5px 0; color:gray; font-size:12px;">Date: {row['date']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    ticker = sys.argv[-1] if len(sys.argv) > 1 else "AAPL"
    show_dashboard(ticker)