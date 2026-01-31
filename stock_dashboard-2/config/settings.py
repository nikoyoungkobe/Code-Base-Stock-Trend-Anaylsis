# config/settings.py
"""
Konfigurationsdatei für das Stock Dashboard.
Hier werden alle zentralen Einstellungen verwaltet.
"""

from datetime import datetime, timedelta

# =============================================================================
# API KEYS
# =============================================================================
# FRED API Key für makroökonomische Daten (US Treasury Yields etc.)
# Kostenlos erhältlich unter: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = "DEIN_FRED_API_KEY_HIER"  # TODO: Eigenen API Key eintragen

# =============================================================================
# INITIAL TICKERS
# =============================================================================
# Standard-Aktien, die beim Start des Dashboards geladen werden
INITIAL_TICKERS = [
    'AAPL',   # Apple
    'MSFT',   # Microsoft
    'GOOGL',  # Alphabet
    'AMZN',   # Amazon
    'NVDA',   # NVIDIA
]

# =============================================================================
# ZEITRAUM EINSTELLUNGEN
# =============================================================================
# Standard-Zeitraum für historische Daten (3 Jahre)
DEFAULT_YEARS_BACK = 3

# Berechnete Datumswerte
END_DATE = datetime.now().strftime('%Y-%m-%d')
START_DATE = (datetime.now() - timedelta(days=365 * DEFAULT_YEARS_BACK)).strftime('%Y-%m-%d')

# =============================================================================
# DCF BEWERTUNG - STANDARDWERTE
# =============================================================================
DCF_CONFIG = {
    'forecast_years': 5,           # Prognosezeitraum in Jahren
    'discount_rate': 0.10,         # Diskontierungssatz (WACC) - 10%
    'growth_rate': 0.05,           # Erwartete FCF-Wachstumsrate - 5%
    'perpetual_growth_rate': 0.02, # Ewige Wachstumsrate (Terminal Value) - 2%
}

# =============================================================================
# DASHBOARD EINSTELLUNGEN
# =============================================================================
DASHBOARD_CONFIG = {
    'debug_mode': True,            # Debug-Modus für Entwicklung
    'host': '127.0.0.1',           # Server-Host
    'port': 8050,                  # Server-Port
}

# =============================================================================
# CHART EINSTELLUNGEN
# =============================================================================
CHART_CONFIG = {
    'template': 'plotly_white',    # Plotly Template
    'default_height': 400,         # Standard Chart-Höhe in Pixel
}
