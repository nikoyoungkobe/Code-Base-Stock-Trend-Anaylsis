# main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from stock_dashboard import GetClosingPrices, create_app, register_callbacks
from stock_dashboard.config import INITIAL_TICKERS, START_DATE, END_DATE

if __name__ == '__main__':
    stock_manager = GetClosingPrices(INITIAL_TICKERS, START_DATE, END_DATE)
    app = create_app()
    register_callbacks(app, stock_manager)
    app.run(debug=True)

