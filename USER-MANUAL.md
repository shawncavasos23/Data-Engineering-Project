# AI Trading System - User Manual

## 1. Overview

This AI-powered trading system is a comprehensive solution that integrates multiple dimensions of financial data to support informed decision-making in the equity markets. It leverages large language models (LLMs) for analysis and integrates with modern data engineering tools for data ingestion, processing, and visualization.

The system incorporates:

- Fundamental analysis
- Technical indicators
- Macroeconomic context
- Sentiment analysis from news and Reddit
- Clustering-based peer comparisons
- Real-time price streaming
- Automated AI signal generation and trade execution

Designed primarily for swing trading of S&P 500 stocks, it is easily extensible to other equities.

---

## 2. System Requirements

- Python 3.9 or later  
- SQLite (included with Python)  
- Apache Kafka and Zookeeper  
- Required Python packages:

```bash
pip install -r requirements.txt
```

---

## 3. Environment Variables

Set these either in your shell or via a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
EMAIL_USER=youremail@gmail.com
EMAIL_PASS=your_app_password
```

These are required for GPT-powered trading signals and for email notifications.

---

## 4. Initial Setup

Run this command to set up the database and preload tickers:

```bash
python main.py init --auto
```

This creates a local `trading_data.db` SQLite database with all required tables and inserts a default list of S&P 500 tickers.

---

## 5. Command Reference

The general command format is:

```bash
python main.py <command> [--ticker TICKER] [--auto] [--email]
```

### Command Descriptions

| Command        | Description                                              |
|----------------|----------------------------------------------------------|
| `init`         | Initializes the database schema and preloads tickers     |
| `update`       | Fetches latest data for a ticker                         |
| `analyze`      | Runs AI-powered trading signal analysis                  |
| `add`          | Adds a new ticker to the database                        |
| `produce`      | Starts Kafka producer for real-time price streaming      |
| `consume`      | Starts Kafka consumer to display live price data         |
| `stop`         | Stops active producer and consumer processes             |
| `restart`      | Restarts streaming for a specific ticker                 |
| `show`         | Launches the Streamlit dashboard                         |
| `find_peers`   | Lists peer stocks based on clustering                    |

---

## 6. Typical Workflows

### Add, Update, and Analyze a New Ticker

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

2. Open **Task Scheduler**, create a new task:
   - Trigger: **Daily at 1:00 PM**
   - Action: Run your `.bat` file
   - Settings: Run with highest privileges

This schedules the system to generate and email a trading signal daily at 1 PM.

---

## 7. Real-Time Streaming with Kafka

Kafka is used to stream and consume real-time stock prices.

### Download and Setup

Download Kafka: https://kafka.apache.org/downloads  
Unzip to a folder such as `C:\kafka` or `~/kafka`

### Starting Zookeeper and Kafka

#### Windows

Start Zookeeper:

```bash
cd C:\kafka
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
```

Start Kafka:

```bash
cd C:\kafka
bin\windows\kafka-server-start.bat config\server.properties
```

#### macOS/Linux

Start Zookeeper:

```bash
cd ~/kafka
bin/zookeeper-server-start.sh config/zookeeper.properties
```

Start Kafka:

```bash
cd ~/kafka
bin/kafka-server-start.sh config/server.properties
```

### Starting the Producer and Consumer

```bash
python main.py produce --ticker AAPL
python main.py consume --ticker AAPL
```

These should be run in separate terminals.

### Stopping Streaming

```bash
python main.py stop
```

### Restarting Streaming

```bash
python main.py restart --ticker AAPL
```

---

## 8. Email Alerts

To receive trading signals via email:

```bash
python main.py analyze --ticker AAPL --email
```

This uses the SMTP credentials configured in your environment.

---

## 9. Data Sources

| Type             | Source                                |
|------------------|----------------------------------------|
| Technical Data   | yfinance                               |
| Fundamentals     | Alpha Vantage / FinancialModelingPrep |
| Macro Indicators | FRED (Federal Reserve)                |
| News             | NewsAPI / scraping                     |
| Sentiment        | Reddit API / scraping                  |

---

## 10. Notes

- All data is stored in a local SQLite file: `trading_data.db`
- Modular design makes it easy to replace components (e.g., use PostgreSQL instead of SQLite)
- GPT-generated signals are returned as structured JSON for consistency
- The system supports visualization using Streamlit and Plotly

---

## 11. Troubleshooting

| Problem                                 | Solution                                                   |
|----------------------------------------|-------------------------------------------------------------|
| `'Engine' object has no attribute 'cursor'` | Upgrade `pandas` and `sqlalchemy`                          |
| `Invalid API key`                      | Check `OPENAI_API_KEY` in your `.env` or shell config       |
| `Email not sending`                   | Use a Gmail App Password; check `EMAIL_USER`, `EMAIL_PASS`  |
| Kafka not running                      | Make sure Zookeeper and Kafka are started correctly         |
| Producer/Consumer not responding       | Check Kafka logs; confirm topic is created and port 9092 open|

---

For more details, refer to the full codebase or contact the maintainers for guidance on extension or deployment.
