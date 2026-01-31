# main.py
"""
Einstiegspunkt für das Stock Dashboard.
Startet die Dash-Applikation.
"""

import sys
import os

# Projektverzeichnis zum Path hinzufügen
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from stock_dashboard import GetClosingPrices, create_app, register_callbacks
from stock_dashboard.config import INITIAL_TICKERS, START_DATE, END_DATE, DASHBOARD_CONFIG


def main():
    """Hauptfunktion zum Starten des Dashboards."""
    
    print("=" * 60)
    print("  STOCK DASHBOARD - Aktienanalyse Tool")
    print("=" * 60)
    print(f"\nInitiale Ticker: {', '.join(INITIAL_TICKERS)}")
    print(f"Zeitraum: {START_DATE} bis {END_DATE}")
    print("-" * 60)
    
    # Stock Manager initialisieren und Daten laden
    print("\n[1/3] Initialisiere Stock Manager...")
    stock_manager = GetClosingPrices(INITIAL_TICKERS, START_DATE, END_DATE)
    
    print("[2/3] Lade historische Daten...")
    stock_manager.fetch_historical_data()
    
    # Dash App erstellen
    print("[3/3] Starte Dashboard...")
    app = create_app()
    register_callbacks(app, stock_manager)
    
    # Initiale Dropdown-Optionen setzen
    available_tickers = stock_manager.get_available_tickers()
    
    print("-" * 60)
    print(f"\n✓ Dashboard bereit!")
    print(f"  Verfügbare Ticker: {', '.join(available_tickers)}")
    print(f"\n  Öffne im Browser: http://{DASHBOARD_CONFIG['host']}:{DASHBOARD_CONFIG['port']}")
    print("  Zum Beenden: Ctrl+C")
    print("=" * 60 + "\n")
    
    # Server starten
    app.run(
        debug=DASHBOARD_CONFIG['debug_mode'],
        host=DASHBOARD_CONFIG['host'],
        port=DASHBOARD_CONFIG['port']
    )


if __name__ == '__main__':
    main()
