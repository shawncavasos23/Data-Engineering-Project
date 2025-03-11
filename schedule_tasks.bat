@echo off
echo Running update for AAPL...
python main.py update --ticker AAPL

echo Running analysis for AAPL...
python main.py analyze --ticker AAPL

echo Process complete.
