# calculations/rsi_mean_reversion.py
"""
RSI Mean-Reversion Strategy Implementation

Strategie-Logik:
- Long Entry: RSI < oversold_threshold UND Preis < MA - n*StdDev
- Short Entry: RSI > overbought_threshold UND Preis > MA + n*StdDev
- Exit: Take Profit oder Stop Loss

Parameter für Optimierung:
- RSI Period
- RSI Thresholds (oversold/overbought)
- Moving Average Period
- Standard Deviation Multiplier
- Take Profit / Stop Loss
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Literal, Tuple
import pandas as pd
import numpy as np
from itertools import product
from datetime import datetime


@dataclass
class RSIMeanReversionParameters:
    """Konfigurationsparameter für RSI Mean-Reversion Strategie."""
    # RSI Parameter
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    # Moving Average & Bollinger
    ma_period: int = 20
    std_dev_multiplier: float = 1.0

    # Risk Management
    take_profit_pct: float = 5.0      # Take Profit in %
    stop_loss_pct: float = 2.0        # Stop Loss in %

    # Position Type
    position_type: Literal['long_only', 'short_only', 'long_short'] = 'long_short'

    # Sonstiges
    risk_free_rate: float = 0.02


@dataclass
class RSIMeanReversionMetrics:
    """Performance-Metriken für die Strategie."""
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    avg_trade_return: float
    profit_factor: float           # Gross Profit / Gross Loss
    avg_holding_days: float
    benchmark_return: float
    excess_return: float

    # Parameter für Referenz
    params: Optional[RSIMeanReversionParameters] = None


class RSIMeanReversion:
    """
    RSI Mean-Reversion Strategy Calculator.

    Generiert Signale basierend auf RSI und Bollinger-Band-ähnlicher Logik.
    """

    def __init__(self, params: Optional[RSIMeanReversionParameters] = None):
        self.params = params or RSIMeanReversionParameters()
        self._signals: Optional[pd.DataFrame] = None
        self._trades: Optional[pd.DataFrame] = None
        self._returns: Optional[pd.DataFrame] = None

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Berechnet den Relative Strength Index."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # Exponential smoothing nach erstem Wert
        for i in range(period, len(prices)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_signals(self, prices: pd.Series) -> pd.DataFrame:
        """
        Generiert Trading-Signale.

        Args:
            prices: pd.Series mit DatetimeIndex und Schlusskursen

        Returns:
            pd.DataFrame mit Signalen und Indikatoren
        """
        if prices.empty:
            raise ValueError("Price series cannot be empty")

        df = pd.DataFrame(index=prices.index)
        df['close'] = prices
        df['returns'] = df['close'].pct_change()

        # RSI berechnen
        df['rsi'] = self._calculate_rsi(df['close'], self.params.rsi_period)

        # Moving Average und Standard Deviation
        df['ma'] = df['close'].rolling(window=self.params.ma_period).mean()
        df['std'] = df['close'].rolling(window=self.params.ma_period).std()

        # Bollinger Bands
        df['upper_band'] = df['ma'] + (self.params.std_dev_multiplier * df['std'])
        df['lower_band'] = df['ma'] - (self.params.std_dev_multiplier * df['std'])

        # Preis-Deviation vom MA in Standardabweichungen
        df['price_deviation'] = (df['close'] - df['ma']) / df['std']

        # Entry Conditions
        df['long_condition'] = (
            (df['rsi'] < self.params.rsi_oversold) &
            (df['close'] < df['lower_band'])
        )
        df['short_condition'] = (
            (df['rsi'] > self.params.rsi_overbought) &
            (df['close'] > df['upper_band'])
        )

        # Signale generieren (ohne Position-Management - wird in Trades gemacht)
        df['raw_signal'] = 0
        if self.params.position_type in ['long_only', 'long_short']:
            df.loc[df['long_condition'], 'raw_signal'] = 1
        if self.params.position_type in ['short_only', 'long_short']:
            df.loc[df['short_condition'], 'raw_signal'] = -1

        self._signals = df
        return df

    def simulate_trades(self, signals_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Simuliert Trades mit Take Profit und Stop Loss.

        Returns:
            pd.DataFrame mit allen Trades
        """
        if signals_df is None:
            signals_df = self._signals

        if signals_df is None:
            raise ValueError("No signals available. Call calculate_signals() first.")

        trades = []
        position = 0  # 0 = flat, 1 = long, -1 = short
        entry_price = 0.0
        entry_date = None

        for i, (date, row) in enumerate(signals_df.iterrows()):
            if pd.isna(row['close']) or pd.isna(row['raw_signal']):
                continue

            current_price = row['close']

            # Check for exit if in position
            if position != 0:
                pnl_pct = ((current_price / entry_price) - 1) * position * 100

                # Take Profit
                if pnl_pct >= self.params.take_profit_pct:
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'direction': 'Long' if position > 0 else 'Short',
                        'return_pct': pnl_pct,
                        'exit_reason': 'Take Profit',
                        'holding_days': (date - entry_date).days
                    })
                    position = 0
                    entry_price = 0.0
                    entry_date = None
                    continue

                # Stop Loss
                if pnl_pct <= -self.params.stop_loss_pct:
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'direction': 'Long' if position > 0 else 'Short',
                        'return_pct': pnl_pct,
                        'exit_reason': 'Stop Loss',
                        'holding_days': (date - entry_date).days
                    })
                    position = 0
                    entry_price = 0.0
                    entry_date = None
                    continue

            # Check for entry if flat
            if position == 0 and row['raw_signal'] != 0:
                position = int(row['raw_signal'])
                entry_price = current_price
                entry_date = date

        # Close any open position at end
        if position != 0 and entry_date is not None:
            last_row = signals_df.iloc[-1]
            pnl_pct = ((last_row['close'] / entry_price) - 1) * position * 100
            trades.append({
                'entry_date': entry_date,
                'exit_date': signals_df.index[-1],
                'entry_price': entry_price,
                'exit_price': last_row['close'],
                'direction': 'Long' if position > 0 else 'Short',
                'return_pct': pnl_pct,
                'exit_reason': 'End of Period',
                'holding_days': (signals_df.index[-1] - entry_date).days
            })

        self._trades = pd.DataFrame(trades)
        return self._trades

    def calculate_returns(self, signals_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Berechnet tägliche und kumulative Renditen.
        """
        if signals_df is None:
            signals_df = self._signals

        if self._trades is None or self._trades.empty:
            self.simulate_trades(signals_df)

        df = pd.DataFrame(index=signals_df.index)
        df['close'] = signals_df['close']
        df['benchmark_return'] = signals_df['returns']
        df['strategy_return'] = 0.0

        # Renditen aus Trades zuordnen
        for _, trade in self._trades.iterrows():
            mask = (df.index >= trade['entry_date']) & (df.index <= trade['exit_date'])
            if mask.any():
                # Tägliche Rendite während Trade
                trade_days = mask.sum()
                if trade_days > 0:
                    daily_return = trade['return_pct'] / 100 / trade_days
                    direction = 1 if trade['direction'] == 'Long' else -1
                    df.loc[mask, 'strategy_return'] = signals_df.loc[mask, 'returns'] * direction

        df['cumulative_strategy'] = (1 + df['strategy_return'].fillna(0)).cumprod() * 100
        df['cumulative_benchmark'] = (1 + df['benchmark_return'].fillna(0)).cumprod() * 100

        df['peak'] = df['cumulative_strategy'].cummax()
        df['drawdown'] = (df['cumulative_strategy'] - df['peak']) / df['peak']

        self._returns = df
        return df

    def calculate_metrics(self) -> RSIMeanReversionMetrics:
        """
        Berechnet Performance-Metriken.
        """
        if self._returns is None:
            self.calculate_returns()

        if self._trades is None or self._trades.empty:
            return RSIMeanReversionMetrics(
                total_return=0.0,
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                num_trades=0,
                avg_trade_return=0.0,
                profit_factor=0.0,
                avg_holding_days=0.0,
                benchmark_return=0.0,
                excess_return=0.0,
                params=self.params
            )

        # Returns
        total_return = (self._returns['cumulative_strategy'].iloc[-1] / 100) - 1
        benchmark_return = (self._returns['cumulative_benchmark'].iloc[-1] / 100) - 1

        num_years = len(self._returns) / 252
        annualized_return = (1 + total_return) ** (1 / max(num_years, 0.01)) - 1

        # Volatility
        strategy_returns = self._returns['strategy_return'].dropna()
        annualized_vol = strategy_returns.std() * np.sqrt(252) if len(strategy_returns) > 0 else 0.0001

        # Sharpe
        sharpe = (annualized_return - self.params.risk_free_rate) / annualized_vol if annualized_vol > 0 else 0

        # Max Drawdown
        max_dd = self._returns['drawdown'].min()

        # Trade Statistics
        num_trades = len(self._trades)
        winning_trades = self._trades[self._trades['return_pct'] > 0]
        losing_trades = self._trades[self._trades['return_pct'] < 0]

        win_rate = len(winning_trades) / num_trades if num_trades > 0 else 0
        avg_trade_return = self._trades['return_pct'].mean() if num_trades > 0 else 0

        gross_profit = winning_trades['return_pct'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['return_pct'].sum()) if len(losing_trades) > 0 else 0.0001
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit

        avg_holding = self._trades['holding_days'].mean() if num_trades > 0 else 0

        return RSIMeanReversionMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            annualized_volatility=annualized_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            num_trades=num_trades,
            avg_trade_return=avg_trade_return,
            profit_factor=profit_factor,
            avg_holding_days=avg_holding,
            benchmark_return=benchmark_return,
            excess_return=total_return - benchmark_return,
            params=self.params
        )


class RSIParameterOptimizer:
    """
    Parameter-Optimierung für RSI Mean-Reversion Strategie.

    Iteriert durch verschiedene Parameterkombinationen und
    speichert Ergebnisse als Tabelle.
    """

    def __init__(self):
        self.results: List[Dict] = []
        self.results_df: Optional[pd.DataFrame] = None
        self.best_params: Optional[RSIMeanReversionParameters] = None
        self.best_metrics: Optional[RSIMeanReversionMetrics] = None

    def define_parameter_grid(
        self,
        rsi_periods: List[int] = None,
        rsi_oversold: List[float] = None,
        rsi_overbought: List[float] = None,
        ma_periods: List[int] = None,
        std_dev_multipliers: List[float] = None,
        take_profits: List[float] = None,
        stop_losses: List[float] = None,
    ) -> List[RSIMeanReversionParameters]:
        """
        Erstellt eine Liste aller Parameterkombinationen.
        """
        # Defaults
        rsi_periods = rsi_periods or [7, 14, 21]
        rsi_oversold = rsi_oversold or [20, 25, 30]
        rsi_overbought = rsi_overbought or [70, 75, 80]
        ma_periods = ma_periods or [10, 20, 50]
        std_dev_multipliers = std_dev_multipliers or [1.0, 1.5, 2.0]
        take_profits = take_profits or [3.0, 5.0, 10.0]
        stop_losses = stop_losses or [1.0, 2.0, 3.0]

        param_combinations = []

        for rsi_p, rsi_os, rsi_ob, ma_p, std_m, tp, sl in product(
            rsi_periods, rsi_oversold, rsi_overbought,
            ma_periods, std_dev_multipliers, take_profits, stop_losses
        ):
            # Skip invalid combinations
            if rsi_os >= rsi_ob:
                continue

            params = RSIMeanReversionParameters(
                rsi_period=rsi_p,
                rsi_oversold=rsi_os,
                rsi_overbought=rsi_ob,
                ma_period=ma_p,
                std_dev_multiplier=std_m,
                take_profit_pct=tp,
                stop_loss_pct=sl,
            )
            param_combinations.append(params)

        return param_combinations

    def run_optimization(
        self,
        prices: pd.Series,
        param_grid: Optional[List[RSIMeanReversionParameters]] = None,
        optimize_metric: str = 'sharpe_ratio',
        verbose: bool = True
    ) -> pd.DataFrame:
        """
        Führt Backtest für alle Parameterkombinationen durch.

        Args:
            prices: Preisdaten
            param_grid: Liste von Parametern (oder None für Default)
            optimize_metric: Metrik zur Optimierung
            verbose: Fortschrittsanzeige

        Returns:
            DataFrame mit allen Ergebnissen
        """
        if param_grid is None:
            param_grid = self.define_parameter_grid()

        total = len(param_grid)
        self.results = []

        if verbose:
            print(f"Starte Optimierung mit {total} Parameterkombinationen...")

        for i, params in enumerate(param_grid):
            try:
                strategy = RSIMeanReversion(params)
                signals = strategy.calculate_signals(prices)
                strategy.simulate_trades(signals)
                strategy.calculate_returns(signals)
                metrics = strategy.calculate_metrics()

                result = {
                    'rsi_period': params.rsi_period,
                    'rsi_oversold': params.rsi_oversold,
                    'rsi_overbought': params.rsi_overbought,
                    'ma_period': params.ma_period,
                    'std_dev_mult': params.std_dev_multiplier,
                    'take_profit': params.take_profit_pct,
                    'stop_loss': params.stop_loss_pct,
                    'total_return': metrics.total_return,
                    'annualized_return': metrics.annualized_return,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'win_rate': metrics.win_rate,
                    'num_trades': metrics.num_trades,
                    'profit_factor': metrics.profit_factor,
                    'avg_trade_return': metrics.avg_trade_return,
                    'excess_return': metrics.excess_return,
                }
                self.results.append(result)

                # Track best
                metric_value = getattr(metrics, optimize_metric, 0)
                if self.best_metrics is None or metric_value > getattr(self.best_metrics, optimize_metric, float('-inf')):
                    self.best_metrics = metrics
                    self.best_params = params

            except Exception as e:
                if verbose:
                    print(f"  Fehler bei Kombination {i+1}: {e}")
                continue

            if verbose and (i + 1) % 50 == 0:
                print(f"  Fortschritt: {i+1}/{total} ({(i+1)/total*100:.1f}%)")

        self.results_df = pd.DataFrame(self.results)

        # Sort by optimization metric
        if not self.results_df.empty:
            self.results_df = self.results_df.sort_values(optimize_metric, ascending=False)

        if verbose:
            print(f"\nOptimierung abgeschlossen!")
            if self.best_params:
                print(f"Beste Parameter nach {optimize_metric}:")
                print(f"  RSI: {self.best_params.rsi_period} (OS: {self.best_params.rsi_oversold}, OB: {self.best_params.rsi_overbought})")
                print(f"  MA: {self.best_params.ma_period}, StdDev: {self.best_params.std_dev_multiplier}")
                print(f"  TP: {self.best_params.take_profit_pct}%, SL: {self.best_params.stop_loss_pct}%")
                print(f"  Sharpe: {self.best_metrics.sharpe_ratio:.2f}, Return: {self.best_metrics.total_return:.1%}")

        return self.results_df

    def save_results(self, filepath: str) -> None:
        """Speichert Ergebnisse als CSV."""
        if self.results_df is not None:
            self.results_df.to_csv(filepath, index=False)
            print(f"Ergebnisse gespeichert: {filepath}")

    def get_top_n(self, n: int = 10, metric: str = 'sharpe_ratio') -> pd.DataFrame:
        """Gibt die Top-N Ergebnisse zurück."""
        if self.results_df is None or self.results_df.empty:
            return pd.DataFrame()
        return self.results_df.nlargest(n, metric)

    def get_heatmap_data(
        self,
        x_param: str = 'rsi_period',
        y_param: str = 'ma_period',
        value_metric: str = 'sharpe_ratio',
        aggregate: str = 'mean'
    ) -> pd.DataFrame:
        """
        Erstellt Pivot-Tabelle für Heatmap-Visualisierung.
        """
        if self.results_df is None or self.results_df.empty:
            return pd.DataFrame()

        pivot = self.results_df.pivot_table(
            values=value_metric,
            index=y_param,
            columns=x_param,
            aggfunc=aggregate
        )
        return pivot
