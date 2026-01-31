import os
from datetime import datetime, timedelta

# FRED API Key for macroeconomic data (Treasury yields)
# Get your free API key at: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Initial stock tickers to load on startup
INITIAL_TICKERS = ["AAPL", "MSFT", "GOOGL"]

# Date range for historical data
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DATE = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")

# Dashboard settings
DEBUG_MODE = True
HOST = "127.0.0.1"
PORT = 8050
