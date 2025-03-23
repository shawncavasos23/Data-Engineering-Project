# AI Trading System - User Manual

## 1. Overview

The AI Trading System is a comprehensive, modular solution for generating data-driven stock trading signals using artificial intelligence. It integrates structured and unstructured financial data and applies a large language model (LLM) to perform context-aware analysis. Built for swing trading of S&P 500 stocks, the system supports real-time streaming, automated email alerts, and peer clustering analysis.

The system incorporates:

- **Fundamental analysis** (e.g., P/E ratio, ROE, market cap)
- **Technical indicators** (e.g., RSI, MACD, moving averages)
- **Macroeconomic data** (e.g., inflation, interest rates, employment)
- **Sentiment analysis** from news headlines and Reddit
- **Peer clustering** using financial and sector-based attributes
- **Real-time stock price streaming** via Kafka
- **AI-generated trade decisions** and optional automated trade execution

This tool can be extended to any equity universe and scaled for more frequent trading strategies if needed.

---

## 2. System Requirements

- Python 3.9 or later  
- SQLite (included with Python)  
- Apache Kafka and Zookeeper  
- Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Environment Variables

Set the following environment variables in your shell or in a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key
EMAIL_USER=youremail@gmail.com
EMAIL_PASS=your_app_password
```

These are required for GPT-based signal generation and email functionality.

---

## 4. Initial Setup

Run this to initialize the database schema and preload a list of tickers:

```bash
python main.py init --auto
```

This creates the `trading_data.db` SQLite file with all necessary tables.

---

## 5. Command Reference

General format:

```bash
python main.py <command> [--ticker TICKER] [--auto] [--email]
```

### Command Descriptions

| Command        | Description                                                  |
|----------------|--------------------------------------------------------------|
| `init`         | Creates the database schema and inserts tickers              |
| `update`       | Fetches the latest fundamental, technical, macro, and sentiment data for a ticker |
| `analyze`      | Runs the AI signal pipeline and optionally sends an email    |
| `add`          | Adds a new ticker to the database                            |
| `produce`      | Starts Kafka producer to stream live prices                  |
| `consume`      | Starts Kafka consumer to receive and display live prices     |
| `stop`         | Stops all producer/consumer processes                        |
| `restart`      | Restarts producer/consumer for the specified ticker          |
| `show`         | Launches the Streamlit dashboard                             |
| `find_peers`   | Displays stocks clustered in the same group as the ticker    |

---

## 6. Typical Workflows

### Add, Update, and Analyze a Ticker

```bash
python main.py add --ticker MSFT
python main.py update --ticker MSFT
python main.py analyze --ticker MSFT --email
```

### Automate Daily Analysis at 1 PM (Windows Task Scheduler)

1. Create a `.bat` file like this:

```bat
@echo off
cd C:\Users\<YourUsername>\Documents\GitHub\Data-Engineering-Project
python main.py analyze --ticker AAPL --email
```

2. Open **Task Scheduler**:
   - **Trigger**: Daily at 1:00 PM  
   - **Action**: Start a program → point to the `.bat` file  
   - **Settings**: Run with highest privileges

This setup will run your AI analysis and email the trading signal each day at 1 PM.

---

## 7. Real-Time Streaming with Kafka

Kafka is used to stream 1-minute price data for selected tickers.

### Download and Setup

Download Kafka from: https://kafka.apache.org/downloads  
Unzip to a folder such as `C:\kafka` or `~/kafka`

### Start Zookeeper and Kafka Servers

#### On Windows:

```bash
cd C:\kafka
bin\windows\zookeeper-server-start.bat config\zookeeper.properties

cd C:\kafka
bin\windows\kafka-server-start.bat config\server.properties
```

#### On macOS/Linux:

```bash
cd ~/kafka
bin/zookeeper-server-start.sh config/zookeeper.properties

cd ~/kafka
bin/kafka-server-start.sh config/server.properties
```

### Start Producer and Consumer

Run in separate terminals:

```bash
python main.py produce --ticker AAPL
python main.py consume --ticker AAPL
```

### Stop All Kafka Processes

```bash
python main.py stop
```

### Restart Producer and Consumer

```bash
python main.py restart --ticker AAPL
```

---

## 8. Email Alerts

To send a trading signal via email:

```bash
python main.py analyze --ticker AAPL --email
```

This uses the configured `EMAIL_USER` and `EMAIL_PASS` credentials.

---

## 9. Data Sources

| Data Type        | Source                                |
|------------------|----------------------------------------|
| Technical Data   | `yfinance`                             |
| Fundamentals     | Alpha Vantage / FinancialModelingPrep  |
| Macroeconomics   | FRED (Federal Reserve Economic Data)   |
| News Headlines   | NewsAPI or custom scraper              |
| Reddit Sentiment | Reddit API or Pushshift                |

---

## 10. AI Customization

The system uses OpenAI’s `gpt-3.5-turbo` model by default to generate structured trading signals. You can customize or upgrade the model depending on your preferences or subscription level.

### Change the Model
In `data_pipeline.py`, locate the `get_ai_full_trading_signal()` function. To switch to GPT-4, modify this line:

```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # change to "gpt-4" if available
```

### Customize the Prompt
The GPT prompt is designed to balance fundamental, technical, macro, and sentiment inputs for medium-term trades. You can adjust the behavior by editing the `prompt` string to reflect your trading style, such as:

- **Risk tolerance**: conservative vs. aggressive
- **Investment horizon**: short-term, swing, or long-term
- **Market conditions**: bullish vs. bearish bias

### Control Temperature
Temperature determines randomness in GPT outputs:

```python
temperature=0.2  # lower = more deterministic
```

You can increase it to 0.6–0.8 for more creative signals or keep it low for consistency.

---

## 11. Notes

- All data is stored in a local `trading_data.db` file (SQLite)
- The system uses SQLAlchemy for easy migration to other databases (e.g., PostgreSQL)
- AI responses are formatted in structured JSON and parsed for execution
- A Streamlit dashboard (via `main.py show`) offers interactive visualization

---

## 12. Troubleshooting

| Problem                                     | Solution                                                   |
|--------------------------------------------|-------------------------------------------------------------|
| `'Engine' object has no attribute 'cursor'` | Upgrade `pandas` and `sqlalchemy` to the latest version     |
| `Invalid API key`                          | Check your `OPENAI_API_KEY` environment variable            |
| `Email not sending`                        | Use a Gmail App Password and verify credentials             |
| Kafka won't start                          | Ensure Zookeeper is running before Kafka                    |
| No streaming data received                 | Confirm both producer and consumer are running on same topic |

---

## 13. Risk Disclosure

> **Disclaimer**: This AI trading system is intended for educational and research purposes only. It is not a registered investment advisor or broker-dealer. The trading signals generated by this system are not financial advice, and past performance does not guarantee future results.

By using this system, you acknowledge that:

- The AI model may generate inaccurate or biased conclusions.
- No guarantees are made regarding signal profitability.
- Live trading with real capital based on this system is done at your own risk.

Always consult with a licensed financial advisor before making investment decisions, and thoroughly backtest any strategy in a simulated environment before deploying it in live markets.
