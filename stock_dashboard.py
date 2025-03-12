import streamlit as st  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
import argparse
import plotly.graph_objects as go  # type: ignore
import plotly.express as px  # type: ignore

# Database Connection
DB_PATH = "trading_data.db"

def fetch_stock_data(ticker):
    """Fetch stock data from the database."""
    conn = sqlite3.connect(DB_PATH)

    # Fetch Fundamentals
    fundamentals_query = "SELECT * FROM fundamentals WHERE ticker = ?"
    fundamentals = pd.read_sql(fundamentals_query, conn, params=(ticker,))

    # Fetch Technical Indicators (latest 50 data points for better visualization)
    technicals_query = "SELECT * FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 50"
    technicals = pd.read_sql(technicals_query, conn, params=(ticker,))

    # Fetch Macroeconomic Data (latest 10 rows)
    macro_query = "SELECT * FROM macroeconomic_data ORDER BY date DESC LIMIT 10"
    macro_data = pd.read_sql(macro_query, conn)

    # Fetch Latest 5 News Articles
    news_query = "SELECT * FROM news ORDER BY published_at DESC LIMIT 5"
    news = pd.read_sql(news_query, conn)

    # Fetch Latest 5 Reddit Mentions
    sentiment_query = "SELECT * FROM reddit_mentions WHERE ticker = ? ORDER BY date DESC LIMIT 5"
    sentiment = pd.read_sql(sentiment_query, conn, params=(ticker,))

    conn.close()

    return {
        "fundamentals": fundamentals,
        "technicals": technicals,
        "macro_data": macro_data,
        "news": news,
        "sentiment": sentiment
    }

def plot_candlestick_chart(data):
    """Generate an interactive candlestick chart with moving averages."""
    if data.empty or not all(col in data.columns for col in ["date", "open", "high", "low", "close"]):
        return None

    data["date"] = pd.to_datetime(data["date"])

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data["date"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="Candlestick",
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    if "ma50" in data.columns:
        fig.add_trace(go.Scatter(x=data["date"], y=data["ma50"], mode='lines', name='50-Day MA', line=dict(color='blue')))
    if "ma200" in data.columns:
        fig.add_trace(go.Scatter(x=data["date"], y=data["ma200"], mode='lines', name='200-Day MA', line=dict(color='red')))

    fig.update_layout(
        title="Candlestick Chart with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    
    return fig

def plot_technical_indicators(data):
    """Generate RSI and MACD Charts."""
    if data.empty:
        return None, None

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data["date"], y=data["rsi"], mode='lines', name='RSI', line=dict(color='purple')))
    fig_rsi.update_layout(title="Relative Strength Index (RSI)", xaxis_title="Date", yaxis_title="RSI", template="plotly_dark")

    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data["date"], y=data["macd"], mode='lines', name='MACD', line=dict(color='orange')))
    fig_macd.add_trace(go.Scatter(x=data["date"], y=data["signal_line"], mode='lines', name='Signal Line', line=dict(color='blue')))
    fig_macd.update_layout(title="MACD vs Signal Line", xaxis_title="Date", yaxis_title="MACD", template="plotly_dark")

    return fig_rsi, fig_macd

def bordered_section(title, content):
    """Wrap content inside a bordered container for better UI separation."""
    st.markdown(
        f"""
        <div style="
            border: 2px solid #444; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 10px 0px; 
            background-color: #1e1e1e;">
            <h3 style="color: white;">{title}</h3>
            {content}
        </div>
        """, 
        unsafe_allow_html=True
    )

def show_dashboard(ticker):
    """Display stock data in a full-screen, single-page layout."""
    st.set_page_config(layout="wide")

    # Hide sidebar for full-screen experience
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] {display: none;}
            div.block-container {padding-top: 1rem; padding-bottom: 1rem;}
        </style>
    """, unsafe_allow_html=True)

    st.title(f"{ticker} Stock Analysis Dashboard")

    # Fetch stock data
    data = fetch_stock_data(ticker)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Candlestick Chart")
        fig_candlestick = plot_candlestick_chart(data["technicals"])
        if fig_candlestick:
            st.plotly_chart(fig_candlestick, use_container_width=True, config={'scrollZoom': False})
        else:
            st.warning("No technical data available.")

        st.subheader("Technical Indicators")
        fig_rsi, fig_macd = plot_technical_indicators(data["technicals"])
        if fig_rsi:
            st.plotly_chart(fig_rsi, use_container_width=True, config={'scrollZoom': False})
            st.plotly_chart(fig_macd, use_container_width=True, config={'scrollZoom': False})
        else:
            st.warning("No technical indicator data available.")

    with col2:
        bordered_section("Company Fundamentals", data["fundamentals"].to_html(index=False) if not data["fundamentals"].empty else "No fundamental data available.")

        bordered_section("Latest News", 
            "".join([f"<p><a href='{row['url']}' target='_blank'>{row['title']}</a> - {row['source']}</p>" for _, row in data["news"].iterrows()])
            if not data["news"].empty else "No news data available."
        )

        bordered_section("Latest Reddit Mentions", 
            "".join([f"<p><a href='{row['link']}' target='_blank'>{row['title']}</a> ({row['date']}) - Upvotes: {row['upvotes']}</p>" for _, row in data["sentiment"].iterrows()])
            if not data["sentiment"].empty else "No Reddit mentions available."
        )

        if not data["macro_data"].empty:
            macro_pivot = data["macro_data"].pivot(index="date", columns="indicator", values="value")
            macro_pivot.index = pd.to_datetime(macro_pivot.index).strftime("%Y-%m-%d")
            bordered_section("Macroeconomic Indicators", macro_pivot.to_html(index=True))
        else:
            bordered_section("Macroeconomic Indicators", "No macroeconomic data available.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stock Dashboard")
    parser.add_argument("ticker", type=str, help="Stock ticker to display (e.g., AAPL)")
    args = parser.parse_args()
    
    show_dashboard(args.ticker)
