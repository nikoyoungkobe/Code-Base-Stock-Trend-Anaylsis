# main.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from data.fetch_data import GetClosingPrices
from visualization.dashboard import create_app
from visualization.callbacks import register_callbacks
from config.settings import INITIAL_TICKERS, START_DATE, END_DATE

if __name__ == '__main__':
    stock_manager = GetClosingPrices(INITIAL_TICKERS, START_DATE, END_DATE)
    app = create_app()
    register_callbacks(app, stock_manager)
    app.run(debug=True)

