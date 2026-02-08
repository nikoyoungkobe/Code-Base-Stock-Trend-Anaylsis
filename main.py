# main.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from data.fetch_data import GetClosingPrices
from visualization.dashboard import create_app
from visualization.callbacks import register_callbacks
from visualization.rsi_callbacks import register_rsi_callbacks
from config.settings import INITIAL_TICKERS, START_DATE, END_DATE, DEBUG_MODE, HOST, PORT, PORTFOLIO_CONFIG
from portfolio import PortfolioManager, register_portfolio_callbacks


def main():
    """Hauptfunktion zum Starten des Dashboards."""
    print("=" * 60)
    print("  STOCK DASHBOARD - Aktienanalyse & Portfolio Tracker")
    print("=" * 60)
    print(f"\nInitiale Ticker: {', '.join(INITIAL_TICKERS)}")
    print(f"Zeitraum: {START_DATE} bis {END_DATE}")
    print("-" * 60)

    # Stock Manager initialisieren
    print("\n[1/4] Initialisiere Stock Manager...")
    stock_manager = GetClosingPrices(INITIAL_TICKERS, START_DATE, END_DATE)

    print("[2/4] Lade historische Daten...")
    stock_manager.fetch_historical_data()

    # Portfolio Manager initialisieren
    print("[3/4] Initialisiere Portfolio Manager...")
    portfolio_manager = PortfolioManager(
        storage_dir=PORTFOLIO_CONFIG.get('storage_dir'),
        cache_ttl=PORTFOLIO_CONFIG.get('cache_ttl', 300)
    )
    portfolios = portfolio_manager.get_all_portfolios()
    print(f"  -> {len(portfolios)} Portfolio(s) geladen")

    # Dash App erstellen und Callbacks registrieren
    print("[4/4] Starte Dashboard...")
    app = create_app()
    register_callbacks(app, stock_manager)
    register_rsi_callbacks(app, stock_manager)
    register_portfolio_callbacks(app, portfolio_manager)

    print("-" * 60)
    print(f"\n Dashboard bereit!")
    print(f"  Portfolios: {len(portfolios)}")
    print(f"\n  Öffne im Browser: http://{HOST}:{PORT}")
    print("  Zum Beenden: Ctrl+C")
    print("=" * 60 + "\n")

    app.run(debug=DEBUG_MODE, host=HOST, port=PORT)


if __name__ == '__main__':
    main()
