# portfolio/models.py
"""
Datenmodelle für das Portfolio-Tracking.
Definiert Holding und Portfolio Klassen mit Serialisierung.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class Holding:
    """
    Repräsentiert eine einzelne Position im Portfolio.

    Attributes:
        ticker: Ticker-Symbol (z.B. 'AAPL')
        quantity: Anzahl der Aktien
        buy_price: Kaufpreis pro Aktie
        buy_date: Kaufdatum im Format 'YYYY-MM-DD'
        id: Eindeutige ID der Position
    """
    ticker: str
    quantity: float
    buy_price: float
    buy_date: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Konvertiert das Holding in ein Dictionary für JSON-Serialisierung."""
        return {
            'ticker': self.ticker,
            'quantity': self.quantity,
            'buy_price': self.buy_price,
            'buy_date': self.buy_date,
            'id': self.id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Holding':
        """Erstellt ein Holding aus einem Dictionary."""
        return cls(
            ticker=data['ticker'],
            quantity=data['quantity'],
            buy_price=data['buy_price'],
            buy_date=data['buy_date'],
            id=data.get('id', str(uuid.uuid4())),
        )

    @property
    def cost_basis(self) -> float:
        """Berechnet die Gesamtkosten der Position."""
        return self.quantity * self.buy_price


@dataclass
class Portfolio:
    """
    Repräsentiert ein Portfolio mit mehreren Holdings.

    Attributes:
        name: Name des Portfolios
        holdings: Liste der Positionen
        benchmark_ticker: Benchmark-Index für Vergleiche (Default: S&P 500)
        id: Eindeutige ID des Portfolios
        created_at: Erstellungszeitpunkt im ISO-Format
    """
    name: str
    holdings: List[Holding] = field(default_factory=list)
    benchmark_ticker: str = '^GSPC'  # S&P 500
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Konvertiert das Portfolio in ein Dictionary für JSON-Serialisierung."""
        return {
            'name': self.name,
            'holdings': [h.to_dict() for h in self.holdings],
            'benchmark_ticker': self.benchmark_ticker,
            'id': self.id,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """Erstellt ein Portfolio aus einem Dictionary."""
        holdings = [Holding.from_dict(h) for h in data.get('holdings', [])]
        return cls(
            name=data['name'],
            holdings=holdings,
            benchmark_ticker=data.get('benchmark_ticker', '^GSPC'),
            id=data.get('id', str(uuid.uuid4())),
            created_at=data.get('created_at', datetime.now().isoformat()),
        )

    def add_holding(self, holding: Holding) -> None:
        """Fügt eine Position zum Portfolio hinzu."""
        self.holdings.append(holding)

    def remove_holding(self, holding_id: str) -> bool:
        """Entfernt eine Position aus dem Portfolio."""
        for i, holding in enumerate(self.holdings):
            if holding.id == holding_id:
                self.holdings.pop(i)
                return True
        return False

    def get_holding(self, holding_id: str) -> Optional[Holding]:
        """Gibt eine Position anhand der ID zurück."""
        for holding in self.holdings:
            if holding.id == holding_id:
                return holding
        return None

    @property
    def total_cost_basis(self) -> float:
        """Berechnet die Gesamtkosten aller Positionen."""
        return sum(h.cost_basis for h in self.holdings)

    @property
    def unique_tickers(self) -> List[str]:
        """Gibt eine Liste aller eindeutigen Ticker im Portfolio zurück."""
        return list(set(h.ticker for h in self.holdings))
