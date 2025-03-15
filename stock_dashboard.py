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
    .block-container { padding-top: 20px !important; }
    .title-text {
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }
    .info-card {
        border: 1px solid #444;
        padding: 15px;
        border-radius: 8px;
        background: linear-gradient(135deg, #2c3e50, #3a3f44);
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        margin-bottom: 15px;
        color: white;
    }
    .info-card a { text-decoration: none; color: #1abc9c; font-size: 18px; font-weight: bold; }
    .info-card p { margin: 5px 0; color: #ddd; font-size: 14px; }
    .chart-container {
        padding: 10px;
        background: #2c3e50;
        border-radius: 10px;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.3);
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
            return f"${value:,.2f}"
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
        "Cluster": safe_format(row.get("cluster")),
    }

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
        title="",
        xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False,
        template="plotly_dark", height=700
    )
    return fig

def plot_technical_chart(data, indicator, color, title):
    """通用技术指标绘图函数"""
    if data.empty or indicator not in data.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["date"], y=data[indicator], mode='lines', name=title, line=dict(color=color)))

    fig.update_layout(title="", xaxis_title="Date", yaxis_title=title, template="plotly_dark", height=400)
    return fig

def show_dashboard(ticker):
    """Display stock data in a structured layout."""
    
    # 重新加入 `title-text` CSS，确保标题样式生效
    st.markdown('<h1 class="title-text">Stock Analysis Dashboard</h1>', unsafe_allow_html=True)

    # Sidebar 选项
    ticker = st.sidebar.text_input("Enter Stock Ticker", value=ticker, key="stock_ticker_input").upper()
    st.sidebar.markdown("---")

    show_candlestick = st.sidebar.checkbox("Show Candlestick Chart", value=True)
    indicator_options = ["RSI", "OBV", "MACD", "ADX", "Volume"]
    selected_indicators = st.sidebar.multiselect("Select Two Indicators", indicator_options, default=["RSI", "OBV"])
    
    num_news_articles = st.sidebar.slider("Number of News Articles", 1, 10, 5)
    num_reddit_mentions = st.sidebar.slider("Number of Reddit Mentions", 1, 10, 5)

    data = fetch_stock_data(ticker, num_news_articles, num_reddit_mentions)

    # **⬇️ 新增 Fundamentals & Macro Data 展示**
    st.subheader("Company Fundamentals")
    st.markdown(format_fundamentals(data["fundamentals"]), unsafe_allow_html=True)

    st.subheader("Macroeconomic Indicators")
    format_macroeconomic_data(data["macro_data"])
    
    # **📊 主页面布局**
    col1, col2 = st.columns([7, 5])

    with col1:
        if show_candlestick:
            st.subheader("Candlestick Chart")
            st.plotly_chart(plot_candlestick_chart(data["technicals"]), use_container_width=True)

        # **📈 显示两个选定的技术指标**
        if len(selected_indicators) == 2:
            st.subheader("Technical Indicators")
            indicator1, indicator2 = selected_indicators
            col_a, col_b = st.columns(2)

            with col_a:
                st.plotly_chart(plot_technical_chart(data["technicals"], indicator1.lower(), "purple", indicator1), use_container_width=True)
            with col_b:
                st.plotly_chart(plot_technical_chart(data["technicals"], indicator2.lower(), "orange", indicator2), use_container_width=True)

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

if __name__ == "__main__":
    ticker = sys.argv[-1] if len(sys.argv) > 1 else "AAPL"
    show_dashboard(ticker)
