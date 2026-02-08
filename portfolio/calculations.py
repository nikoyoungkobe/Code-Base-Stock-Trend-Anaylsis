# portfolio/calculations.py
"""
Portfolio-Berechnungen: P/L, Performance, Allokation, Benchmark-Vergleich.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from .models import Holding, Portfolio
from .manager import PortfolioManager


class PortfolioCalculations:
    """
    Führt alle Portfolio-bezogenen Berechnungen durch.
    """

    def __init__(self, manager: PortfolioManager):
        self.manager = manager

    def calculate_holding_pnl(
        self,
        holding: Holding,
        current_price: Optional[float]
    ) -> dict:
        """Berechnet P/L für eine einzelne Position."""
        cost_basis = holding.cost_basis

        if current_price is None:
            return {
                'pnl': 0.0,
                'pnl_percent': 0.0,
                'current_value': cost_basis,
                'cost_basis': cost_basis,
                'price_available': False,
            }

        current_value = holding.quantity * current_price
        pnl = current_value - cost_basis
        pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0

        return {
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'current_value': current_value,
            'cost_basis': cost_basis,
            'price_available': True,
        }

    def calculate_portfolio_summary(
        self,
        portfolio: Portfolio,
        prices: Dict[str, Optional[float]]
    ) -> dict:
        """Berechnet eine Zusammenfassung des Portfolios."""
        total_value = 0.0
        total_cost_basis = 0.0
        holdings_data = []

        for holding in portfolio.holdings:
            price = prices.get(holding.ticker)
            pnl_data = self.calculate_holding_pnl(holding, price)

            total_value += pnl_data['current_value']
            total_cost_basis += pnl_data['cost_basis']

            holdings_data.append({
                'holding': holding,
                **pnl_data
            })

        total_pnl = total_value - total_cost_basis
        total_pnl_percent = (
            (total_pnl / total_cost_basis * 100)
            if total_cost_basis > 0 else 0.0
        )

        return {
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'total_cost_basis': total_cost_basis,
            'holdings_count': len(portfolio.holdings),
            'holdings_data': holdings_data,
        }

    def calculate_allocation(
        self,
        portfolio: Portfolio,
        prices: Dict[str, Optional[float]]
    ) -> List[dict]:
        """Berechnet die Allokation nach Ticker."""
        ticker_values: Dict[str, float] = {}

        for holding in portfolio.holdings:
            price = prices.get(holding.ticker)
            if price is not None:
                value = holding.quantity * price
            else:
                value = holding.cost_basis

            if holding.ticker in ticker_values:
                ticker_values[holding.ticker] += value
            else:
                ticker_values[holding.ticker] = value

        total_value = sum(ticker_values.values())

        allocations = []
        for ticker, value in sorted(
            ticker_values.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            percentage = (value / total_value * 100) if total_value > 0 else 0.0
            allocations.append({
                'ticker': ticker,
                'value': value,
                'percentage': percentage,
            })

        return allocations

    def calculate_portfolio_history(
        self,
        portfolio: Portfolio,
        period: str = '1y'
    ) -> Optional[pd.DataFrame]:
        """Berechnet den historischen Portfolio-Wert."""
        if not portfolio.holdings:
            return None

        ticker_data: Dict[str, pd.DataFrame] = {}
        for ticker in portfolio.unique_tickers:
            df = self.manager.get_historical_prices(ticker, period=period)
            if df is not None and not df.empty:
                ticker_data[ticker] = df

        if not ticker_data:
            return None

        all_dates = set()
        for df in ticker_data.values():
            all_dates.update(df.index)
        all_dates = sorted(all_dates)

        portfolio_values = []

        for date in all_dates:
            daily_value = 0.0

            for holding in portfolio.holdings:
                if holding.ticker not in ticker_data:
                    continue

                df = ticker_data[holding.ticker]
                if date in df.index:
                    price = df.loc[date, 'Close']
                else:
                    mask = df.index <= date
                    if mask.any():
                        price = df.loc[mask, 'Close'].iloc[-1]
                    else:
                        continue

                daily_value += holding.quantity * price

            if daily_value > 0:
                portfolio_values.append({
                    'Date': date,
                    'Value': daily_value
                })

        if not portfolio_values:
            return None

        return pd.DataFrame(portfolio_values).set_index('Date')

    def calculate_benchmark_comparison(
        self,
        portfolio: Portfolio,
        period: str = '1y'
    ) -> Optional[pd.DataFrame]:
        """Vergleicht Portfolio-Performance mit Benchmark."""
        portfolio_history = self.calculate_portfolio_history(portfolio, period)
        if portfolio_history is None or portfolio_history.empty:
            return None

        benchmark_df = self.manager.get_historical_prices(
            portfolio.benchmark_ticker,
            period=period
        )
        if benchmark_df is None or benchmark_df.empty:
            return None

        common_dates = portfolio_history.index.intersection(benchmark_df.index)
        if len(common_dates) < 2:
            return None

        portfolio_series = portfolio_history.loc[common_dates, 'Value']
        benchmark_series = benchmark_df.loc[common_dates, 'Close']

        portfolio_normalized = (portfolio_series / portfolio_series.iloc[0]) * 100
        benchmark_normalized = (benchmark_series / benchmark_series.iloc[0]) * 100

        result = pd.DataFrame({
            'Portfolio': portfolio_normalized,
            'Benchmark': benchmark_normalized,
        })

        return result

    def calculate_position_performance(
        self,
        portfolio: Portfolio,
        prices: Dict[str, Optional[float]]
    ) -> List[dict]:
        """Berechnet die Performance jeder Position."""
        performance = []

        for holding in portfolio.holdings:
            price = prices.get(holding.ticker)
            pnl_data = self.calculate_holding_pnl(holding, price)

            performance.append({
                'holding_id': holding.id,
                'ticker': holding.ticker,
                'quantity': holding.quantity,
                'buy_price': holding.buy_price,
                'buy_date': holding.buy_date,
                'current_price': price,
                'current_value': pnl_data['current_value'],
                'cost_basis': pnl_data['cost_basis'],
                'pnl': pnl_data['pnl'],
                'pnl_percent': pnl_data['pnl_percent'],
            })

        return performance

    def calculate_daily_change(
        self,
        portfolio: Portfolio
    ) -> Tuple[float, float]:
        """Berechnet die Tagesänderung des Portfolios."""
        total_change = 0.0
        total_prev_value = 0.0

        for ticker in portfolio.unique_tickers:
            try:
                df = self.manager.get_historical_prices(ticker, period='5d')
                if df is None or len(df) < 2:
                    continue

                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]

                ticker_quantity = sum(
                    h.quantity for h in portfolio.holdings
                    if h.ticker == ticker
                )

                daily_change = (current_price - prev_price) * ticker_quantity
                prev_value = prev_price * ticker_quantity

                total_change += daily_change
                total_prev_value += prev_value

            except Exception:
                continue

        percent_change = (
            (total_change / total_prev_value * 100)
            if total_prev_value > 0 else 0.0
        )

        return total_change, percent_change
