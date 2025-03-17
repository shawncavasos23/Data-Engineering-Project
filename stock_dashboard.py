import sys
import streamlit as st  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
import plotly.graph_objects as go  # type: ignore

# Set Streamlit page config
st.set_page_config(layout="wide", page_title="Stock Analysis Dashboard")

# Custom CSS for improved styling
st.markdown(
    """
    <style>
    .block-container { padding-top: 5px !important; }
    .css-1d391kg { background-color: #f8f9fa !important; padding: 20px; border-radius: 10px; }
    h1 { color: #2c3e50; text-align: center; }
    .info-card {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 8px;
        background: linear-gradient(135deg, #f9f9f9, #ffffff);
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .info-card a { text-decoration: none; color: #0077cc; font-size: 18px; font-weight: bold; }
    .info-card p { margin: 5px 0; color: #666; font-size: 14px; }
    .chart-container {
        padding: 10px;
        background: white;
        border-radius: 10px;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Database Connection
DB_PATH = "trading_data.db"

@st.cache_data
def fetch_stock_data(ticker, num_news, num_reddit):
    """Fetch available stock data from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        fundamentals = pd.read_sql("SELECT * FROM fundamentals WHERE ticker = ?", conn, params=(ticker,))
        technicals = pd.read_sql("SELECT * FROM technicals WHERE ticker = ? ORDER BY date DESC LIMIT 100", conn, params=(ticker,))
        macro_data = pd.read_sql("SELECT * FROM macroeconomic_data ORDER BY date DESC LIMIT 10", conn)
        news = pd.read_sql("SELECT * FROM news WHERE title LIKE ? ORDER BY published_at DESC LIMIT ?", conn, params=(f"%{ticker}%", num_news))
        sentiment = pd.read_sql("SELECT * FROM reddit_mentions WHERE ticker = ? ORDER BY date DESC LIMIT ?", conn, params=(ticker, num_reddit))

    return {
        "fundamentals": fundamentals,
        "technicals": technicals,
        "macro_data": macro_data,
        "news": news,
        "sentiment": sentiment
    }

def format_fundamentals(fundamentals):
    """Format and display company fundamentals in separate columns across the screen."""
    if fundamentals.empty:
        return "No fundamentals available."

    row = fundamentals.iloc[0]

    def safe_format(value, is_currency=False):
        """Safely format numbers, handling None values."""
        if value is None:
            return "N/A"
        if is_currency:
            return f"${value:,.0f}"
        return f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)

    # Define fundamentals to display
    fundamentals_data = {
        "Sector": safe_format(row.get("sector")),
        "P/E Ratio": safe_format(row.get("pe_ratio")),
        "Market Cap": safe_format(row.get("market_cap"), is_currency=True),
        "Revenue": safe_format(row.get("revenue"), is_currency=True),
        "Return on Assets (ROA)": safe_format(row.get("roa")),
        "Return on Equity (ROE)": safe_format(row.get("roe")),
        "Beta": safe_format(row.get("beta")),
        "Dividend Per Share": safe_format(row.get("dividend_per_share"), is_currency=True),
        "Total Debt": safe_format(row.get("total_debt"), is_currency=True),
        "Total Cash": safe_format(row.get("total_cash"), is_currency=True),
        "Free Cash Flow": safe_format(row.get("free_cash_flow"), is_currency=True),
        "Operating Cash Flow": safe_format(row.get("operating_cash_flow"), is_currency=True),
        "Net Income": safe_format(row.get("net_income"), is_currency=True),}


    # Create one column per metric dynamically
    columns = st.columns(len(fundamentals_data))

    for col, (label, value) in zip(columns, fundamentals_data.items()):
        with col:
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                font-size: 14px;
            ">
                <b>{label}</b><br>
                <span style="font-size: 18px; font-weight: bold; color: #333;">{value}</span>
            </div>
            """, unsafe_allow_html=True)

def format_macroeconomic_data(macro_data):
    """Format and display macroeconomic indicators at the bottom of the screen."""
    if macro_data.empty:
        return "No macroeconomic data available."

    # Pivot the macroeconomic data for easier access
    latest_data = macro_data.set_index("indicator")["value"].to_dict()

    def safe_format(value, scale=1, unit=""):
        """Safely format macroeconomic numbers while handling None values and scaling appropriately."""
        if value is None:
            return "N/A"
    
        formatted_value = f"{(value / scale):,.2f}" if scale != 1 else f"{value:,.2f}"
        return f"{formatted_value} {unit}".strip()


    # Define macroeconomic indicators with scaling and units
    macro_indicators = {
        "CPI (Inflation)": safe_format(latest_data.get("CPIAUCSL")),
        "PPI (Producer Prices)": safe_format(latest_data.get("PPIACO")),
        "Unemployment Rate": safe_format(latest_data.get("UNRATE"), unit="%"),
        "Total Employment": safe_format(latest_data.get("PAYEMS"), scale=1000, unit="Million"),  # PAYEMS is in thousands
        "Fed Funds Rate": safe_format(latest_data.get("FEDFUNDS"), unit="%"),
        "10-Year Treasury Yield": safe_format(latest_data.get("GS10"), unit="%"),
    }

    # Create one column per macroeconomic indicator
    columns = st.columns(len(macro_indicators))

    for col, (label, value) in zip(columns, macro_indicators.items()):
        with col:
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                font-size: 14px;
            ">
                <b>{label}</b><br>
                <span style="font-size: 18px; font-weight: bold; color: #333;">{value}</span>
            </div>
            """, unsafe_allow_html=True)


def plot_candlestick_chart(data):
    """Generate an interactive candlestick chart with moving averages."""
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
        xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False,
        template="plotly_white", height=700
    )
    return fig

def plot_rsi_chart(data):
    """Generate a compact RSI Chart with overbought/oversold zones."""
    if data.empty or "rsi" not in data.columns:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["date"], y=data["rsi"], mode='lines', name='RSI', line=dict(color='purple')))

    # Overbought & Oversold lines
    fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Overbought", annotation_position="top right")
    fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Oversold", annotation_position="bottom right")

    fig.update_layout(xaxis_title="Date", yaxis_title="RSI", template="plotly_white", height=600)
    return fig

def plot_obv_and_volume_chart(data):
    """Generate OBV and Volume on the same plot."""
    if data.empty or not all(col in data.columns for col in ["date", "obv", "volume"]):
        return go.Figure()

    fig = go.Figure()

    # Plot Volume as Bars
    fig.add_trace(go.Bar(
        x=data["date"], y=data["volume"],
        name="Volume", marker=dict(color="blue", opacity=0.3),
        yaxis="y1"
    ))

    # Plot OBV as a Line
    fig.add_trace(go.Scatter(
        x=data["date"], y=data["obv"],
        mode="lines", name="On-Balance Volume (OBV)",
        line=dict(color="green"),
        yaxis="y2"
    ))

    # Configure Dual Y-Axis
    fig.update_layout(
        xaxis=dict(title="Date"),
        yaxis=dict(title="Volume", side="left", showgrid=False),
        yaxis2=dict(title="OBV", overlaying="y", side="right", showgrid=False),
        template="plotly_white",
        height=600
    )

    return fig

def show_dashboard(ticker):
    """Display stock data in a structured layout."""

    # Sidebar UI Enhancements
    ticker = st.sidebar.text_input("Enter Stock Ticker", value=ticker).upper()
    st.sidebar.markdown("---")

    # Apply custom CSS to fix title cut-off issue
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 20px !important;
        }}
        .title-text {{
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # Dynamically update the title after sidebar input
    st.title(f"{ticker} Stock Analysis Dashboard")

    num_news_articles = st.sidebar.slider("Number of News Articles", 1, 10, 5)
    num_reddit_mentions = st.sidebar.slider("Number of Reddit Mentions", 1, 10, 6)

    data = fetch_stock_data(ticker, num_news_articles, num_reddit_mentions)

    # Company Fundamentals Section
    st.subheader("Company Fundamentals")
    st.markdown(format_fundamentals(data["fundamentals"]), unsafe_allow_html=True)

    col1, col2 = st.columns([7, 5])

    with col1:
        st.subheader("Candlestick Chart")
        st.plotly_chart(plot_candlestick_chart(data["technicals"]), use_container_width=True, key="candlestick_chart")

        rsi_col, volume_col = st.columns(2)

        with rsi_col:
            st.subheader("RSI Indicator")
            st.plotly_chart(plot_rsi_chart(data["technicals"]), use_container_width=True, key="rsi_chart")

        with volume_col:
            st.subheader("OBV & Volume Chart")
            st.plotly_chart(plot_obv_and_volume_chart(data["technicals"]), use_container_width=True, key="obv_chart")
    
    with col2:
        st.subheader("Latest News")
        for _, row in data["news"].iterrows():
            st.markdown(
                f"""
                <div class="info-card">
                    <a href="{row['url']}" target="_blank">{row['title']}</a>
                    <p>{row['source']} | {row['published_at']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.subheader("Reddit Sentiment")
        for _, row in data["sentiment"].iterrows():
            st.markdown(
                f"""
                <div class="info-card">
                    <a href="{row['link']}" target="_blank">{row['title']}</a>
                    <p>Upvotes: {row['upvotes']} | Score: {row['upvote_ratio']}</p>
                    <p>{row['date']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("Macroeconomic Indicators")
    format_macroeconomic_data(data["macro_data"])


if __name__ == "__main__":
    ticker = sys.argv[-1] if len(sys.argv) > 1 else "AAPL"
    show_dashboard(ticker)