# portfolio/storage.py
"""
JSON-Persistenz für Portfolios.
Speichert und lädt Portfolios aus dem Dateisystem.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from .models import Portfolio


class PortfolioStorage:
    """
    Verwaltet die Persistenz von Portfolios als JSON-Dateien.
    """

    def __init__(self, storage_dir: str = None):
        """
        Initialisiert den Storage.

        Args:
            storage_dir: Pfad zum Speicherverzeichnis.
                        Default: 'portfolios' im Projektverzeichnis
        """
        if storage_dir is None:
            base_dir = Path(__file__).parent.parent
            storage_dir = base_dir / 'portfolios'

        self.storage_dir = Path(storage_dir)
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Stellt sicher, dass das Speicherverzeichnis existiert."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, portfolio_id: str) -> Path:
        """Gibt den Dateipfad für ein Portfolio zurück."""
        return self.storage_dir / f"{portfolio_id}.json"

    def save(self, portfolio: Portfolio) -> bool:
        """Speichert ein Portfolio als JSON-Datei."""
        try:
            file_path = self._get_file_path(portfolio.id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(portfolio.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern des Portfolios: {e}")
            return False

    def load(self, portfolio_id: str) -> Optional[Portfolio]:
        """Lädt ein Portfolio aus einer JSON-Datei."""
        try:
            file_path = self._get_file_path(portfolio_id)
            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Portfolio.from_dict(data)
        except Exception as e:
            print(f"Fehler beim Laden des Portfolios {portfolio_id}: {e}")
            return None

    def delete(self, portfolio_id: str) -> bool:
        """Löscht ein Portfolio."""
        try:
            file_path = self._get_file_path(portfolio_id)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Fehler beim Löschen des Portfolios {portfolio_id}: {e}")
            return False

    def list_all(self) -> List[Portfolio]:
        """Lädt alle gespeicherten Portfolios."""
        portfolios = []
        try:
            for file_path in self.storage_dir.glob('*.json'):
                portfolio_id = file_path.stem
                portfolio = self.load(portfolio_id)
                if portfolio:
                    portfolios.append(portfolio)
        except Exception as e:
            print(f"Fehler beim Auflisten der Portfolios: {e}")

        portfolios.sort(key=lambda p: p.created_at, reverse=True)
        return portfolios

    def list_summaries(self) -> List[dict]:
        """Gibt eine Liste von Portfolio-Zusammenfassungen zurück."""
        summaries = []
        for portfolio in self.list_all():
            summaries.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'holdings_count': len(portfolio.holdings),
                'created_at': portfolio.created_at,
            })
        return summaries

    def exists(self, portfolio_id: str) -> bool:
        """Prüft, ob ein Portfolio existiert."""
        return self._get_file_path(portfolio_id).exists()
