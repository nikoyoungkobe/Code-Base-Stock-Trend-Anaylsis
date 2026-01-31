"""
Time Series Momentum Strategy Implementation

Implements TSM following academic literature (Moskowitz, Ooi, Pedersen 2012):
- Long when past returns positive, Short/Cash when negative
- Volatility-scaled position sizing
- Configurable lookback and holding periods
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Literal
import pandas as pd
import numpy as np


@dataclass
class TSMParameters:
    """Configuration parameters for Time Series Momentum strategy."""
    lookback_months: int = 12          # Signal calculation window (1-24)
    holding_period_days: int = 21      # Rebalancing frequency in trading days
    volatility_window: int = 21        # Rolling volatility window (trading days)
    volatility_target: float = 0.10    # Annualized volatility target (10%)
    enable_volatility_scaling: bool = True
    position_type: Literal['long_short', 'long_cash'] = 'long_cash'
    risk_free_rate: float = 0.02       # For Sharpe calculation


@dataclass
class TSMPerformanceMetrics:
    """Performance metrics for the TSM strategy."""
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration_days: int
    win_rate: float                    # % of profitable trades
    num_trades: int
    avg_holding_period: float
    calmar_ratio: float                # Return / Max Drawdown
    sortino_ratio: float               # Return / Downside volatility
    benchmark_total_return: float
    benchmark_sharpe_ratio: float
    excess_return: float


class TimeSeriesMomentum:
    """
    Time Series Momentum Strategy Calculator.

    Generates momentum signals and calculates strategy performance
    based on configurable parameters.
    """

    def __init__(self, params: Optional[TSMParameters] = None):
        """
        Initialize TSM calculator with strategy parameters.

        Args:
            params: TSMParameters instance. Uses defaults if None.
        """
        self.params = params or TSMParameters()
        self._signals: Optional[pd.DataFrame] = None
        self._returns: Optional[pd.DataFrame] = None

    def calculate_signals(
        self,
        prices: pd.Series,
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None
    ) -> pd.DataFrame:
        """
        Generate TSM signals from price data.

        Args:
            prices: pd.Series with DatetimeIndex containing closing prices
            start_date: Optional start date for signal generation
            end_date: Optional end date for signal generation

        Returns:
            pd.DataFrame with columns:
                - 'close': Original prices
                - 'returns': Daily returns
                - 'momentum': Lookback period returns
                - 'volatility': Rolling realized volatility
                - 'signal': -1, 0, or 1
                - 'position_size': Volatility-adjusted position
        """
        if prices.empty:
            raise ValueError("Price series cannot be empty")

        # Filter by date range if specified
        if start_date is not None:
            prices = prices[prices.index >= start_date]
        if end_date is not None:
            prices = prices[prices.index <= end_date]

        df = pd.DataFrame(index=prices.index)
        df['close'] = prices

        # Calculate daily returns
        df['returns'] = df['close'].pct_change()

        # Calculate momentum (lookback period returns)
        lookback_days = self.params.lookback_months * 21  # ~21 trading days per month
        df['momentum'] = df['close'].pct_change(periods=lookback_days)

        # Calculate rolling volatility (annualized)
        df['volatility'] = df['returns'].rolling(
            window=self.params.volatility_window
        ).std() * np.sqrt(252)

        # Set minimum volatility floor to avoid extreme position sizes
        df['volatility'] = df['volatility'].clip(lower=0.05)

        # Generate raw signals based on momentum sign
        if self.params.position_type == 'long_cash':
            # Long when momentum positive, cash otherwise
            df['signal'] = np.where(df['momentum'] > 0, 1, 0)
        else:
            # Long when positive, short when negative
            df['signal'] = np.sign(df['momentum'])

        # Apply holding period (don't change signal within holding period)
        df['signal'] = self._apply_holding_period(df['signal'])

        # Calculate position size with volatility scaling
        if self.params.enable_volatility_scaling:
            # Position size = target vol / realized vol
            df['position_size'] = (self.params.volatility_target / df['volatility']).clip(upper=2.0)
            df['position_size'] = df['position_size'] * df['signal'].abs()
        else:
            df['position_size'] = df['signal'].abs().astype(float)

        # Shift signals by 1 day to avoid look-ahead bias
        # (signal generated today, position entered tomorrow)
        df['signal'] = df['signal'].shift(1)
        df['position_size'] = df['position_size'].shift(1)

        self._signals = df
        return df

    def _apply_holding_period(self, signals: pd.Series) -> pd.Series:
        """
        Apply holding period constraint to signals.
        Only allow signal changes every N days.
        """
        if self.params.holding_period_days <= 1:
            return signals

        result = signals.copy()
        last_change_idx = 0
        last_signal = 0

        for i, (idx, signal) in enumerate(signals.items()):
            if pd.isna(signal):
                continue

            if i == 0 or (i - last_change_idx) >= self.params.holding_period_days:
                if signal != last_signal:
                    last_change_idx = i
                    last_signal = signal

            result.iloc[i] = last_signal

        return result

    def calculate_strategy_returns(
        self,
        signals_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Calculate strategy returns based on signals.

        Args:
            signals_df: DataFrame from calculate_signals(). Uses cached if None.

        Returns:
            pd.DataFrame with columns:
                - 'strategy_return': Daily strategy returns
                - 'cumulative_strategy': Cumulative strategy returns
                - 'benchmark_return': Daily buy-and-hold returns
                - 'cumulative_benchmark': Cumulative benchmark returns
                - 'drawdown': Strategy drawdown from peak
        """
        if signals_df is None:
            signals_df = self._signals

        if signals_df is None:
            raise ValueError("No signals available. Call calculate_signals() first.")

        df = pd.DataFrame(index=signals_df.index)

        # Daily returns from underlying
        df['benchmark_return'] = signals_df['returns']

        # Strategy returns = signal * position_size * underlying return
        if self.params.enable_volatility_scaling:
            df['strategy_return'] = (
                signals_df['signal'] *
                signals_df['position_size'] *
                signals_df['returns']
            )
        else:
            df['strategy_return'] = signals_df['signal'] * signals_df['returns']

        # Cumulative returns (indexed to 100)
        df['cumulative_strategy'] = (1 + df['strategy_return'].fillna(0)).cumprod() * 100
        df['cumulative_benchmark'] = (1 + df['benchmark_return'].fillna(0)).cumprod() * 100

        # Calculate drawdown
        df['peak'] = df['cumulative_strategy'].cummax()
        df['drawdown'] = (df['cumulative_strategy'] - df['peak']) / df['peak']

        self._returns = df
        return df

    def calculate_performance_metrics(
        self,
        returns_df: Optional[pd.DataFrame] = None
    ) -> TSMPerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Args:
            returns_df: DataFrame from calculate_strategy_returns(). Uses cached if None.

        Returns:
            TSMPerformanceMetrics dataclass with all metrics
        """
        if returns_df is None:
            returns_df = self._returns

        if returns_df is None:
            raise ValueError("No returns available. Call calculate_strategy_returns() first.")

        strategy_returns = returns_df['strategy_return'].dropna()
        benchmark_returns = returns_df['benchmark_return'].dropna()

        # Total and annualized returns
        total_return = (returns_df['cumulative_strategy'].iloc[-1] / 100) - 1
        num_years = len(strategy_returns) / 252
        annualized_return = (1 + total_return) ** (1 / num_years) - 1 if num_years > 0 else 0

        # Benchmark metrics
        benchmark_total = (returns_df['cumulative_benchmark'].iloc[-1] / 100) - 1

        # Volatility
        annualized_vol = strategy_returns.std() * np.sqrt(252)
        benchmark_vol = benchmark_returns.std() * np.sqrt(252)

        # Sharpe ratios
        sharpe = (annualized_return - self.params.risk_free_rate) / annualized_vol if annualized_vol > 0 else 0
        benchmark_ann_return = (1 + benchmark_total) ** (1 / num_years) - 1 if num_years > 0 else 0
        benchmark_sharpe = (benchmark_ann_return - self.params.risk_free_rate) / benchmark_vol if benchmark_vol > 0 else 0

        # Max drawdown
        max_dd = returns_df['drawdown'].min()

        # Max drawdown duration
        dd_duration = self._calculate_max_dd_duration(returns_df['drawdown'])

        # Sortino ratio (downside volatility)
        downside_returns = strategy_returns[strategy_returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
        sortino = (annualized_return - self.params.risk_free_rate) / downside_vol

        # Calmar ratio
        calmar = annualized_return / abs(max_dd) if max_dd != 0 else 0

        # Trade statistics
        trades = self._calculate_trade_stats(self._signals)

        return TSMPerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            annualized_volatility=annualized_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            max_drawdown_duration_days=dd_duration,
            win_rate=trades['win_rate'],
            num_trades=trades['num_trades'],
            avg_holding_period=trades['avg_holding'],
            calmar_ratio=calmar,
            sortino_ratio=sortino,
            benchmark_total_return=benchmark_total,
            benchmark_sharpe_ratio=benchmark_sharpe,
            excess_return=total_return - benchmark_total
        )

    def _calculate_max_dd_duration(self, drawdown: pd.Series) -> int:
        """Calculate the longest drawdown duration in days."""
        in_drawdown = drawdown < 0

        if not in_drawdown.any():
            return 0

        # Find consecutive drawdown periods
        dd_groups = (~in_drawdown).cumsum()
        dd_lengths = in_drawdown.groupby(dd_groups).sum()

        return int(dd_lengths.max()) if len(dd_lengths) > 0 else 0

    def _calculate_trade_stats(self, signals_df: pd.DataFrame) -> dict:
        """Calculate trade-level statistics."""
        if signals_df is None:
            return {'win_rate': 0, 'num_trades': 0, 'avg_holding': 0}

        # Detect signal changes (trades)
        signal_changes = signals_df['signal'].diff().fillna(0) != 0
        num_trades = signal_changes.sum()

        if num_trades == 0:
            return {'win_rate': 0, 'num_trades': 0, 'avg_holding': 0}

        # Calculate win rate based on returns during positions
        position_returns = signals_df['returns'] * signals_df['signal']
        winning_days = (position_returns > 0).sum()
        total_position_days = (signals_df['signal'] != 0).sum()

        win_rate = winning_days / total_position_days if total_position_days > 0 else 0
        avg_holding = total_position_days / num_trades if num_trades > 0 else 0

        return {
            'win_rate': win_rate,
            'num_trades': int(num_trades),
            'avg_holding': avg_holding
        }

    def generate_trade_log(
        self,
        signals_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Generate a log of all trades (signal changes).

        Returns:
            pd.DataFrame with trade details
        """
        if signals_df is None:
            signals_df = self._signals

        if signals_df is None:
            return pd.DataFrame()

        trades = []
        current_position = 0
        entry_date = None
        entry_price = None

        for date, row in signals_df.iterrows():
            signal = row['signal']

            if pd.isna(signal):
                continue

            # Position change detected
            if signal != current_position:
                # Close existing position
                if current_position != 0 and entry_date is not None:
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': row['close'],
                        'direction': 'Long' if current_position > 0 else 'Short',
                        'return': (row['close'] / entry_price - 1) * current_position,
                        'holding_days': (date - entry_date).days
                    })

                # Open new position
                if signal != 0:
                    entry_date = date
                    entry_price = row['close']

                current_position = signal

        return pd.DataFrame(trades)


@dataclass
class ScenarioComparison:
    """Container for comparing multiple parameter scenarios."""
    scenarios: Dict[str, TSMParameters] = field(default_factory=dict)
    results: Dict[str, TSMPerformanceMetrics] = field(default_factory=dict)

    def add_scenario(self, name: str, params: TSMParameters) -> None:
        """Add a named parameter scenario."""
        self.scenarios[name] = params

    def run_all(
        self,
        prices: pd.Series
    ) -> pd.DataFrame:
        """
        Run all scenarios and return comparison DataFrame.

        Returns:
            pd.DataFrame with scenario names as index and metrics as columns
        """
        results_data = []

        for name, params in self.scenarios.items():
            tsm = TimeSeriesMomentum(params)
            signals = tsm.calculate_signals(prices)
            returns = tsm.calculate_strategy_returns(signals)
            metrics = tsm.calculate_performance_metrics(returns)

            self.results[name] = metrics

            results_data.append({
                'Szenario': name,
                'Lookback': params.lookback_months,
                'Holding': params.holding_period_days,
                'Vol Scaling': params.enable_volatility_scaling,
                'Total Return': f"{metrics.total_return:.1%}",
                'Sharpe': f"{metrics.sharpe_ratio:.2f}",
                'Max DD': f"{metrics.max_drawdown:.1%}",
                'Win Rate': f"{metrics.win_rate:.1%}",
                'Trades': metrics.num_trades
            })

        return pd.DataFrame(results_data)

    def get_best_scenario(
        self,
        metric: str = 'sharpe_ratio'
    ) -> tuple:
        """Return the scenario with best performance for given metric."""
        if not self.results:
            return None, None

        best_name = max(
            self.results.keys(),
            key=lambda x: getattr(self.results[x], metric)
        )
        return best_name, self.scenarios[best_name]
