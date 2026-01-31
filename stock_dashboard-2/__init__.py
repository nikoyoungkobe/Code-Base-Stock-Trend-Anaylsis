# stock_dashboard/__init__.py
"""
Stock Dashboard - Aktienanalyse und Visualisierung

Ein interaktives Dashboard für:
- Historische Kursdaten und Vergleiche
- Fundamentale Finanzkennzahlen (FCF, Debt, Revenue, Profit)
- Makroökonomische Indikatoren (VIX, Yield Curve)
- DCF-Bewertungen
"""

from .data.fetch_data import GetClosingPrices
from .visualization.dashboard import create_app
from .visualization.callbacks import register_callbacks

__version__ = '0.1.0'
__all__ = ['GetClosingPrices', 'create_app', 'register_callbacks']
