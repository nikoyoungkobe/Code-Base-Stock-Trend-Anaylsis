# portfolio/manager.py
"""
Portfolio Manager - CRUD-Operationen und Preisdaten-Integration.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd

from .models import Holding, Portfolio
from .storage import PortfolioStorage


class PortfolioManager:
    """
    Verwaltet Portfolios mit CRUD-Operationen und Live-Preisdaten.
    """

    def __init__(self, storage_dir: str = None, cache_ttl: int = 300):
        """
        Initialisiert den Portfolio Manager.

        Args:
            storage_dir: Verzeichnis für Portfolio-Dateien
            cache_ttl: Cache-Gültigkeit in Sekunden (Default: 5 Minuten)
        """
        self.storage = PortfolioStorage(storage_dir)
        self.price_cache: Dict[str, dict] = {}
        self.cache_ttl = cache_ttl
        self._portfolios: Dict[str, Portfolio] = {}
        self._load_all_portfolios()

    def _load_all_portfolios(self) -> None:
        """Lädt alle Portfolios in den Speicher."""
        for portfolio in self.storage.list_all():
            self._portfolios[portfolio.id] = portfolio

    # =========================================================================
    # Portfolio CRUD
    # =========================================================================

    def create_portfolio(self, name: str, benchmark_ticker: str = '^GSPC') -> Portfolio:
        """Erstellt ein neues Portfolio."""
        portfolio = Portfolio(name=name, benchmark_ticker=benchmark_ticker)
        self._portfolios[portfolio.id] = portfolio
        self.storage.save(portfolio)
        return portfolio

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Gibt ein Portfolio anhand der ID zurück."""
        return self._portfolios.get(portfolio_id)

    def get_all_portfolios(self) -> List[Portfolio]:
        """Gibt alle Portfolios zurück."""
        return list(self._portfolios.values())

    def update_portfolio(self, portfolio: Portfolio) -> bool:
        """Aktualisiert ein Portfolio."""
        if portfolio.id in self._portfolios:
            self._portfolios[portfolio.id] = portfolio
            return self.storage.save(portfolio)
        return False

    def delete_portfolio(self, portfolio_id: str) -> bool:
        """Löscht ein Portfolio."""
        if portfolio_id in self._portfolios:
            del self._portfolios[portfolio_id]
            return self.storage.delete(portfolio_id)
        return False

    # =========================================================================
    # Holding CRUD
    # =========================================================================

    def add_holding(
        self,
        portfolio_id: str,
        ticker: str,
        quantity: float,
        buy_price: float,
        buy_date: str
    ) -> Optional[Holding]:
        """Fügt eine Position zu einem Portfolio hinzu."""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None

        holding = Holding(
            ticker=ticker.upper(),
            quantity=quantity,
            buy_price=buy_price,
            buy_date=buy_date
        )
        portfolio.add_holding(holding)
        self.storage.save(portfolio)
        return holding

    def remove_holding(self, portfolio_id: str, holding_id: str) -> bool:
        """Entfernt eine Position aus einem Portfolio."""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return False

        if portfolio.remove_holding(holding_id):
            self.storage.save(portfolio)
            return True
        return False

    # =========================================================================
    # Preisdaten
    # =========================================================================

    def _is_cache_valid(self, ticker: str) -> bool:
        """Prüft, ob der Cache für einen Ticker noch gültig ist."""
        if ticker not in self.price_cache:
            return False
        cache_entry = self.price_cache[ticker]
        age = (datetime.now() - cache_entry['timestamp']).total_seconds()
        return age < self.cache_ttl

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Holt den aktuellen Preis für einen Ticker."""
        if self._is_cache_valid(ticker):
            return self.price_cache[ticker]['price']

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')

            if price is None:
                hist = stock.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]

            if price is not None:
                self.price_cache[ticker] = {
                    'price': float(price),
                    'timestamp': datetime.now()
                }
                return float(price)

        except Exception as e:
            print(f"Fehler beim Abrufen des Preises für {ticker}: {e}")

        return None

    def get_historical_prices(
        self,
        ticker: str,
        start_date: str = None,
        end_date: str = None,
        period: str = '1y'
    ) -> Optional[pd.DataFrame]:
        """Holt historische Preisdaten für einen Ticker."""
        try:
            stock = yf.Ticker(ticker)
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)
            return df if not df.empty else None
        except Exception as e:
            print(f"Fehler beim Abrufen historischer Daten für {ticker}: {e}")
            return None

    def get_portfolio_prices(self, portfolio_id: str) -> Dict[str, Optional[float]]:
        """Holt aktuelle Preise für alle Ticker in einem Portfolio."""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return {}

        prices = {}
        for ticker in portfolio.unique_tickers:
            prices[ticker] = self.get_current_price(ticker)

        prices[portfolio.benchmark_ticker] = self.get_current_price(
            portfolio.benchmark_ticker
        )

        return prices

    def refresh_prices(self, portfolio_id: str) -> None:
        """Aktualisiert alle Preise für ein Portfolio."""
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio:
            for ticker in portfolio.unique_tickers:
                if ticker in self.price_cache:
                    del self.price_cache[ticker]
            self.get_portfolio_prices(portfolio_id)
