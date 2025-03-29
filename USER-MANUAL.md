# AI Trading System - User Manual

## Version: 1.0 – March 2025  
**Maintainer**: Shawn Cavasos  
**GitHub**: [github.com/shawncavasos23/Data-Engineering-Project](https://github.com/shawncavasos23/Data-Engineering-Project)

---

## 1. Overview

The AI Trading System is a comprehensive, modular solution for generating data-driven stock trading signals using artificial intelligence. It integrates structured and unstructured financial data and applies a large language model (LLM) to perform context-aware analysis.

### Key Features:
- Fundamental, technical, macroeconomic, and sentiment analysis
- Peer clustering using sector and financial attributes
- Real-time price streaming via Kafka
- AI-generated trade signals (Buy/Sell/Hold)
- Automated email alerts and optional trade execution

---

## 2. TL;DR – Quick Start Commands

```bash
# Initialize system and preload tickers
python main.py init --auto

# Add and update a stock
python main.py add --ticker AAPL
python main.py update --ticker AAPL

# Generate trade signal and send email
python main.py analyze --ticker AAPL --email

# Stream live prices
python main.py produce --ticker AAPL
python main.py consume --ticker AAPL

# Launch the dashboard
python main.py show
```

---

## 3. System Requirements

- Python 3.9+
- SQLite
- Apache Kafka + Zookeeper
- Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 4. Environment Variables

Set in your shell or `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
EMAIL_USER=youremail@gmail.com
EMAIL_PASS=your_app_password
```

---

## 5. Initial Setup

```bash
python main.py init --auto
```

Creates `trading_data.db` and preloads tickers.

---

## 6. Command Reference

| Command        | Description                                                  |
|----------------|--------------------------------------------------------------|
| `init`         | Create database and insert tickers                           |
| `update`       | Fetch latest data for a ticker                               |
| `analyze`      | Generate AI signal (optional `--email`)                      |
| `add`          | Add new ticker to system                                     |
| `produce`      | Start Kafka producer for live prices                         |
| `consume`      | Start Kafka consumer (display live prices)                   |
| `stop`         | Stop all Kafka processes                                     |
| `restart`      | Restart Kafka for a specific ticker                          |
| `show`         | Launch Streamlit dashboard                                   |
| `find_peers`   | Show tickers in same cluster group                           |

---

## 7. Real-Time Streaming with Kafka

```bash
# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka
bin/kafka-server-start.sh config/server.properties

# Stream prices
python main.py produce --ticker AAPL
python main.py consume --ticker AAPL
```

---

## 8. Email Alerts

```bash
python main.py analyze --ticker AAPL --email
```

Requires Gmail App Password if using Gmail.

---

## 9. AI Customization

In `data_pipeline.py`, update:

```python
model="gpt-3.5-turbo"  # Change to "gpt-4" if needed
temperature=0.2        # Lower = more consistent
```

### Example GPT Output

```json
{
  "decision": "BUY",
  "entry_price": 172.4,
  "target_price": 180.0,
  "stop_loss": 168.0,
  "rationale": "Strong fundamentals, bullish RSI crossover, and macro support."
}
```

Edit the prompt to adjust for:
- Risk appetite
- Time horizon
- Market sentiment bias

---

## 10. Data Sources

| Type             | Source                          |
|------------------|---------------------------------|
| Technical Data   | EOD Historical Data (eodhd)     |
| Fundamentals     | Financial Modeling Prep         |
| Macroeconomics   | FRED                            |
| News Headlines   | NewsAPI or custom scraper       |
| Reddit Sentiment | Reddit API / Pushshift          |
| Real-Time Prices | yfinance                        |

---

## 11. Troubleshooting

| Issue                                | Fix                                                  |
|-------------------------------------|-------------------------------------------------------|
| `Engine has no attribute 'cursor'`  | Upgrade `pandas` and `sqlalchemy`                    |
| API key errors                      | Re-check `OPENAI_API_KEY` in `.env`                  |
| Kafka not running                   | Ensure Zookeeper is started first                    |
| No price stream                     | Check if both producer and consumer are on same topic |
| Email not sent                      | Use Gmail App Password; verify `EMAIL_USER/PASS`     |

---

## 12. Risk Disclosure

> This system is for educational purposes only and not financial advice.  
Backtest thoroughly and consult a licensed financial advisor before trading with real money.