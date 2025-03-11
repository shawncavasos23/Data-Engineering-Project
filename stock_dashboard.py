import streamlit as st  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
import argparse
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore

# Database Connection
DB_PATH = "trading_data.db"

def fetch_stock_data(ticker):
    """Fetch all stock-related data from the database."""
    conn = sqlite3.connect(DB_PATH)

    # Fetch Fundamentals
    fundamentals_query = "SELECT * FROM fundamentals WHERE ticker = ?"
    fundamentals = pd.read_sql(fundamentals_query, conn, params=(ticker,))

    # Fetch Technical Indicators (latest 100 data points)
    technicals_query = "SELECT * FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 100"
    technicals = pd.read_sql(technicals_query, conn, params=(ticker,))

    # Fetch Macroeconomic Data (latest 20 rows)
    macro_query = "SELECT * FROM macroeconomic_data ORDER BY date DESC LIMIT 20"
    macro_data = pd.read_sql(macro_query, conn)

    # Fetch News (latest 5 articles)
    news_query = "SELECT * FROM news ORDER BY published_at DESC LIMIT 5"
    news = pd.read_sql(news_query, conn)

    # Fetch Sentiment Data (latest 5 mentions)
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

def show_dashboard(ticker):
    """Display the stock data in a professional, interactive Streamlit UI."""
    st.set_page_config(layout="wide")

    st.title(f"{ticker} Stock Analysis Dashboard")

    # Fetch stock data
    data = fetch_stock_data(ticker)

    # Tabs for Navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Fundamentals", "Technical Analysis", "Macroeconomic Data", "News", "Market Sentiment"]
    )

    # Fundamentals Tab
    with tab1:
        st.subheader("Company Fundamentals")
        if not data["fundamentals"].empty:
            # Identify numeric columns for formatting
            num_cols = data["fundamentals"].select_dtypes(include=["float64", "int64"]).columns
            st.dataframe(data["fundamentals"].style.format({col: "{:,.2f}" for col in num_cols}))
        else:
            st.warning("No fundamental data available.")

    # Technical Analysis Tab
    with tab2:
        st.subheader("Technical Indicators & Price Trends")
        if not data["technicals"].empty:
            # Moving Averages
            fig_ma = px.line(
                data["technicals"],
                x="date",
                y=["ma50", "ma200"],
                labels={"value": "Price", "date": "Date"},
                title="50-Day vs 200-Day Moving Averages",
            )
            st.plotly_chart(fig_ma, use_container_width=True)

            # RSI Trend
            fig_rsi = px.line(
                data["technicals"],
                x="date",
                y="rsi",
                labels={"rsi": "RSI", "date": "Date"},
                title="Relative Strength Index (RSI)",
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

            # Bollinger Bands Visualization
            fig_bb = go.Figure()
            fig_bb.add_trace(go.Scatter(x=data["technicals"]["date"], y=data["technicals"]["upper_band"], mode='lines', name='Upper Band', line=dict(color='red')))
            fig_bb.add_trace(go.Scatter(x=data["technicals"]["date"], y=data["technicals"]["lower_band"], mode='lines', name='Lower Band', line=dict(color='blue')))
            fig_bb.add_trace(go.Scatter(x=data["technicals"]["date"], y=data["technicals"]["ma50"], mode='lines', name='50-Day MA', line=dict(color='green')))
            fig_bb.update_layout(title="Bollinger Bands", xaxis_title="Date", yaxis_title="Price", legend_title="Legend")
            st.plotly_chart(fig_bb, use_container_width=True)

            # Trading Volume
            fig_vol = px.bar(
                data["technicals"],
                x="date",
                y="volume",
                labels={"volume": "Trading Volume", "date": "Date"},
                title="Trading Volume Over Time",
            )
            st.plotly_chart(fig_vol, use_container_width=True)

        else:
            st.warning("No technical data available.")

    # Macroeconomic Data Tab
    with tab3:
        st.subheader("Macroeconomic Indicators")
        if not data["macro_data"].empty:
            num_cols_macro = data["macro_data"].select_dtypes(include=["float64", "int64"]).columns
            st.dataframe(data["macro_data"].style.format({col: "{:,.2f}" for col in num_cols_macro}))

            # Inflation vs Interest Rates
            fig_macro = px.line(
                data["macro_data"],
                x="date",
                y=["CPIAUCSL", "FEDFUNDS"],
                labels={"value": "Value", "date": "Date"},
                title="Inflation (CPI) vs Federal Funds Rate",
            )
            st.plotly_chart(fig_macro, use_container_width=True)

        else:
            st.warning("No macroeconomic data available.")

    # News Tab
    with tab4:
        st.subheader("Latest Market News")
        if not data["news"].empty:
            for _, row in data["news"].iterrows():
                st.markdown(f"**[{row['title']}]({row['url']})** - {row['source']}")
                st.write(row["description"])
        else:
            st.warning("No news data available.")

    # Market Sentiment Tab
    with tab5:
        st.subheader("Market Sentiment Analysis")
        if not data["sentiment"].empty:
            fig_sentiment = px.bar(
                data["sentiment"],
                x="date",
                y="upvotes",
                color="upvote_ratio",
                labels={"upvotes": "Upvotes", "date": "Date", "upvote_ratio": "Upvote Ratio"},
                title="Reddit Sentiment Analysis",
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)

            st.dataframe(data["sentiment"])

        else:
            st.warning("No sentiment data available.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stock Dashboard")
    parser.add_argument("ticker", type=str, help="Stock ticker to display (e.g., AAPL)")
    args = parser.parse_args()
    
    show_dashboard(args.ticker)
