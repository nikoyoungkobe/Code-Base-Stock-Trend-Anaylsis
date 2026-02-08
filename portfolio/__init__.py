# portfolio/__init__.py
"""
Portfolio Tracker Module - TradingView-ähnlicher Portfolio Tracker.

Ermöglicht das Erstellen, Verwalten und Analysieren von Aktienportfolios
mit JSON-Persistenz und interaktiven Visualisierungen.
"""

from .models import Holding, Portfolio
from .storage import PortfolioStorage
from .manager import PortfolioManager
from .calculations import PortfolioCalculations
from .components import create_portfolio_layout
from .callbacks import register_portfolio_callbacks

__all__ = [
    'Holding',
    'Portfolio',
    'PortfolioStorage',
    'PortfolioManager',
    'PortfolioCalculations',
    'create_portfolio_layout',
    'register_portfolio_callbacks',
]
