import streamlit as st  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
import argparse
import plotly.graph_objects as go  # type: ignore
import plotly.express as px  # type: ignore

# Database Connection
DB_PATH = "trading_data.db"

def fetch_stock_data(ticker):
    """Fetch all stock-related data from the database."""
    conn = sqlite3.connect(DB_PATH)

    # Fetch Fundamentals
    fundamentals_query = "SELECT * FROM fundamentals WHERE ticker = ?"
    fundamentals = pd.read_sql(fundamentals_query, conn, params=(ticker,))

    # Fetch Technical Indicators (latest 30 data points for compact view)
    technicals_query = "SELECT * FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 30"
    technicals = pd.read_sql(technicals_query, conn, params=(ticker,))

    # Fetch Macroeconomic Data (latest 10 rows)
    macro_query = "SELECT * FROM macroeconomic_data ORDER BY date DESC LIMIT 10"
    macro_data = pd.read_sql(macro_query, conn)

    # Fetch News (latest 3 articles)
    news_query = "SELECT * FROM news ORDER BY published_at DESC LIMIT 3"
    news = pd.read_sql(news_query, conn)

    # Fetch Sentiment Data (latest 3 mentions)
    sentiment_query = "SELECT * FROM reddit_mentions WHERE ticker = ? ORDER BY date DESC LIMIT 3"
    sentiment = pd.read_sql(sentiment_query, conn, params=(ticker,))

    conn.close()

    return {
        "fundamentals": fundamentals,
        "technicals": technicals,
        "macro_data": macro_data,
        "news": news,
        "sentiment": sentiment
    }

def show_dashboard(ticker):
    """Display the stock data in a full-screen, single-page layout without scrolling."""
    st.set_page_config(layout="wide")

    # Hide sidebar for full-screen experience
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] {display: none;}
            div.block-container {padding-top: 1rem; padding-bottom: 1rem;}
            .stPlotlyChart {overflow: hidden !important;}
        </style>
    """, unsafe_allow_html=True)

    st.title(f"{ticker} Stock Analysis Dashboard")

    # Fetch stock data
    data = fetch_stock_data(ticker)

    # Create a **Grid Layout** for the full-screen dashboard
    col1, col2 = st.columns([2, 3])

    # **Left Column (Fundamentals, News, Sentiment)**
    with col1:
        st.subheader("Company Fundamentals")
        if not data["fundamentals"].empty:
            num_cols = data["fundamentals"].select_dtypes(include=["float64", "int64"]).columns
            st.dataframe(data["fundamentals"].style.format({col: "{:,.2f}" for col in num_cols}), height=180)
        else:
            st.warning("No fundamental data available.")

        st.subheader("Latest News")
        if not data["news"].empty:
            for _, row in data["news"].iterrows():
                st.markdown(f"**[{row['title']}]({row['url']})** - {row['source']}")
                st.write(row["description"])
        else:
            st.warning("No news data available.")

        st.subheader("Market Sentiment")
        if not data["sentiment"].empty:
            fig_sentiment = px.bar(
                data["sentiment"],
                x="date",
                y="upvotes",
                color="upvote_ratio",
                labels={"upvotes": "Upvotes", "date": "Date", "upvote_ratio": "Upvote Ratio"},
                title="Reddit Sentiment Analysis",
            )
            st.plotly_chart(fig_sentiment, use_container_width=True, config={'scrollZoom': False})
        else:
            st.warning("No sentiment data available.")

    # **Right Column (Technical Analysis & Macroeconomic Data)**
    with col2:
        st.subheader("Technical Indicators & Market Trends")

        if not data["technicals"].empty:
            fig_ma = go.Figure()
            fig_ma.add_trace(go.Scatter(x=data["technicals"]["date"], y=data["technicals"]["ma50"], mode='lines', name='50-Day MA', line=dict(color='blue')))
            fig_ma.add_trace(go.Scatter(x=data["technicals"]["date"], y=data["technicals"]["ma200"], mode='lines', name='200-Day MA', line=dict(color='red')))
            fig_ma.update_layout(title="50-Day vs 200-Day Moving Averages", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig_ma, use_container_width=True, config={'scrollZoom': False})

            fig_vol = px.bar(
                data["technicals"],
                x="date",
                y="volume",
                labels={"volume": "Trading Volume", "date": "Date"},
                title="Trading Volume Over Time",
            )
            st.plotly_chart(fig_vol, use_container_width=True, config={'scrollZoom': False})
        else:
            st.warning("No technical data available.")

        st.subheader("Macroeconomic Indicators")
        if not data["macro_data"].empty:
            num_cols_macro = data["macro_data"].select_dtypes(include=["float64", "int64"]).columns
            st.dataframe(data["macro_data"].style.format({col: "{:,.2f}" for col in num_cols_macro}), height=180)
        else:
            st.warning("No macroeconomic data available.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stock Dashboard")
    parser.add_argument("ticker", type=str, help="Stock ticker to display (e.g., AAPL)")
    args = parser.parse_args()
    
    show_dashboard(args.ticker)
