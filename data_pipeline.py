# Securely load OpenAI API Key
api_key = 

import os
import logging
import pandas as pd
import openai
import json
from sqlalchemy import text  # type: ignore
from sqlalchemy.exc import SQLAlchemyError  # type: ignore
import re

from technical_analysis import run_technical_analysis
from fundamental_analysis import get_fundamental_data
from macroeconomic_analysis import fetch_economic_data
from news_analysis import fetch_news
from reddit_analysis import run_reddit_analysis
from db_utils import create_sqlalchemy_engine
from email_utils import send_email
from trade_execution import place_trade

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

engine = create_sqlalchemy_engine()

def add_ticker(ticker: str) -> bool:
    """Add a new ticker to all relevant tables if it doesn't already exist."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT 1 FROM fundamentals WHERE ticker = :ticker"),
                {"ticker": ticker}
            )
            if result.scalar():
                return True 

            conn.execute(text("INSERT INTO fundamentals (ticker) VALUES (:ticker)"), {"ticker": ticker})
            conn.execute(text("INSERT INTO technicals (ticker, date) VALUES (:ticker, DATE('now'))"), {"ticker": ticker})
            conn.execute(text(
                "INSERT INTO trade_signals (ticker, signal, date_generated) "
                "VALUES (:ticker, 'HOLD', DATE('now'))"
            ), {"ticker": ticker})

        return True

    except SQLAlchemyError as e:
        logging.error(f"Database error when adding ticker {ticker}: {e}", exc_info=True)
        return False

def update_stock_data(ticker: str):
    """Update data for a given ticker using all analysis modules."""
    logging.info(f"Updating data for {ticker}...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM fundamentals WHERE ticker = :ticker"), {"ticker": ticker})
            if not result.scalar():
                logging.warning(f"{ticker} not found in database.")
                return

        run_technical_analysis(ticker, engine)
        get_fundamental_data(ticker, engine)
        run_reddit_analysis(ticker, engine)
        fetch_news(ticker, engine)
        fetch_economic_data(engine)

        logging.info(f"Data updated for {ticker}.")

    except Exception as e:
        logging.error(f"Error updating data for {ticker}: {e}")

def extract_existing_data(ticker: str) -> dict:
    """Extract stock, technical, macro, sentiment, and peer data for AI analysis."""
    try:
        fundamentals = pd.read_sql(
            "SELECT * FROM fundamentals WHERE ticker = :ticker",
            con=engine,
            params={"ticker": ticker}
        )

        peer_companies = pd.read_sql(
            """
            SELECT f.ticker FROM fundamentals f
            WHERE f.cluster = (SELECT cluster FROM fundamentals WHERE ticker = :ticker)
            AND f.ticker != :ticker
            """,
            con=engine,
            params={"ticker": ticker}
        )

        technicals = pd.read_sql(
            "SELECT * FROM technicals WHERE ticker = :ticker ORDER BY date DESC LIMIT 1",
            con=engine,
            params={"ticker": ticker}
        )

        macro = pd.read_sql(
            """
            SELECT indicator, value 
            FROM macroeconomic_data 
            WHERE date = (SELECT MAX(date) FROM macroeconomic_data)
            """,
            con=engine
        )

        news = pd.read_sql(
            "SELECT title FROM news WHERE ticker = :ticker ORDER BY published_at DESC LIMIT 5",
            con=engine,
            params={"ticker": ticker}
        )["title"].tolist()

        sentiment = pd.read_sql(
            "SELECT * FROM reddit_mentions WHERE ticker = :ticker ORDER BY date DESC LIMIT 5",
            con=engine,
            params={"ticker": ticker}
        )

        return {
            "fundamentals": fundamentals.to_dict("records")[0] if not fundamentals.empty else {},
            "technical_data": technicals.to_dict("records")[0] if not technicals.empty else {},
            "macro_data": macro.set_index("indicator")["value"].to_dict() if not macro.empty else {},
            "news_titles": news,
            "sentiment_data": sentiment.to_dict("records")[0] if not sentiment.empty else {},
            "peer_companies": peer_companies["ticker"].tolist()
        }

    except Exception as e:
        logging.error(f"Error extracting data for {ticker}: {e}")
        return {
            "fundamentals": {},
            "technical_data": {},
            "macro_data": {},
            "news_titles": [],
            "sentiment_data": {},
            "peer_companies": []
        }

from sqlalchemy import text  # type: ignore

from sqlalchemy import create_engine, text  # type: ignore
from sqlalchemy.exc import SQLAlchemyError  # type: ignore
import logging
import json

def run_analysis_and_execute_trade(ticker: str, engine) -> str:
    """Run full analysis pipeline and execute trade if signal is generated."""
    logging.info(f"Running AI-powered analysis for {ticker}...")

    data = extract_existing_data(ticker)

    signal = get_ai_full_trading_signal(
        ticker=ticker,
        macro_data=data["macro_data"],
        fundamental_data=data["fundamentals"],
        technical_data=data["technical_data"],
        sentiment_data=data["sentiment_data"],
        news_titles=data["news_titles"],
        peer_companies=data["peer_companies"]
    )

    logging.info(f"\nAI Trading Signal for {ticker}:\n{json.dumps(signal, indent=2)}")

    send_email(subject=f"AI Trading Analysis for {ticker}", body=json.dumps(signal, indent=2))

    if "trading_decision" in signal:
        decision = signal["trading_decision"].upper()
        buy_price = float(signal.get("entry_price", 10.0))
        sell_price = float(signal.get("target_price", 12.0))
        stop_loss = float(signal.get("stop_loss", 9.0))

        with engine.begin() as conn:
            query = text("""
                INSERT INTO trade_signals (ticker, signal, buy_price, sell_price, stop_loss, date_generated)
                VALUES (:ticker, :signal, :buy_price, :sell_price, :stop_loss, DATE('now'))
                ON CONFLICT(ticker, date_generated) DO UPDATE SET
                    signal=excluded.signal,
                    buy_price=excluded.buy_price,
                    sell_price=excluded.sell_price,
                    stop_loss=excluded.stop_loss
            """)
            try:
                conn.execute(query, {
                    "ticker": ticker,
                    "signal": decision,
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "stop_loss": stop_loss
                })
            except SQLAlchemyError as e:
                logging.error(f"Error storing trade signal for {ticker}: {e}")

        if decision == "BUY":
            place_trade(ticker, "buy", buy_price, sell_price, stop_loss, engine)
        elif decision == "SELL":
            place_trade(ticker, "sell", buy_price, sell_price, stop_loss, engine)

    return "AI analysis complete. Trade executed if applicable."


def get_ai_full_trading_signal(ticker, macro_data, fundamental_data, technical_data, sentiment_data, news_titles, peer_companies):
    """Generate a structured AI trading signal (JSON format)."""
    try:
        news_bullets = "\n".join([f"- {title}" for title in news_titles])
    
        prompt = f"""  
        You are a financial analyst specializing in macroeconomic, fundamental, technical, and sentiment analysis.  
        Your task is to analyze {ticker} using the following metrics and return your conclusion strictly in JSON format.  

        Stock: {ticker}  

        Macroeconomic Indicators:
        - Federal Funds Rate: {macro_data.get('FEDFUNDS', 'N/A')}  
        - CPI: {macro_data.get('CPIAUCSL', 'N/A')}  
        - PPI: {macro_data.get('PPIACO', 'N/A')}  
        - Unemployment Rate: {macro_data.get('UNRATE', 'N/A')}  
        - Nonfarm Payrolls: {macro_data.get('PAYEMS', 'N/A')}  

        Relevant News Headlines:
        {news_bullets}

        Fundamental Data:
        {json.dumps(fundamental_data, indent=2)}

        Technical Data:
        {json.dumps(technical_data, indent=2)}

        Sentiment Data:
        {json.dumps(sentiment_data, indent=2)}

        Return your analysis in the following JSON format **only**:

        {{
          "trading_decision": "BUY / SELL / HOLD",
          "entry_price": float,
          "target_price": float,
          "stop_loss": float,
          "justification": "Short paragraph with reasoning",
          "risks_and_catalysts": "Short summary of major risks and catalysts"
        }}

        Respond with only valid JSON. Do not add commentary or explanation.
        """

        client = openai.OpenAI(api_key=api_key)
        logging.debug(f"Sending prompt to OpenAI for {ticker}")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )

        raw = response.choices[0].message.content.strip()
        logging.debug(f"Received raw GPT response: {raw[:300]}...")

        try:
            signal = json.loads(raw)
            return signal
        except json.JSONDecodeError:
            logging.warning("GPT response not valid JSON. Returning raw text.")
            raw_clean = re.sub(r"```json|```", "", raw).strip()
            return {"raw_output": raw_clean}

    except Exception as e:
        logging.error(f"Error generating AI trading signal: {e}")
        return {"error": str(e)}