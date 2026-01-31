"""
Unit tests for Time Series Momentum strategy implementation.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from stock_dashboard.calculations.momentum_strategy import (
    TimeSeriesMomentum,
    TSMParameters,
    TSMPerformanceMetrics,
    ScenarioComparison
)


@pytest.fixture
def sample_prices():
    """Generate sample price series for testing."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    # Simulate trending market with some volatility
    returns = np.random.normal(0.0005, 0.02, 500)
    prices = 100 * (1 + pd.Series(returns)).cumprod()
    return pd.Series(prices.values, index=dates, name='Close')


@pytest.fixture
def trending_up_prices():
    """Generate consistently upward trending prices."""
    dates = pd.date_range('2020-01-01', periods=300, freq='B')
    prices = 100 * (1.001 ** np.arange(300))  # 0.1% daily growth
    return pd.Series(prices, index=dates, name='Close')


@pytest.fixture
def trending_down_prices():
    """Generate consistently downward trending prices."""
    dates = pd.date_range('2020-01-01', periods=300, freq='B')
    prices = 100 * (0.999 ** np.arange(300))  # 0.1% daily decline
    return pd.Series(prices, index=dates, name='Close')


class TestTSMParameters:
    """Test TSMParameters dataclass."""

    def test_default_values(self):
        params = TSMParameters()
        assert params.lookback_months == 12
        assert params.holding_period_days == 21
        assert params.volatility_target == 0.10
        assert params.enable_volatility_scaling is True
        assert params.position_type == 'long_cash'

    def test_custom_values(self):
        params = TSMParameters(
            lookback_months=6,
            holding_period_days=5,
            volatility_target=0.15,
            position_type='long_short'
        )
        assert params.lookback_months == 6
        assert params.holding_period_days == 5
        assert params.volatility_target == 0.15
        assert params.position_type == 'long_short'


class TestTimeSeriesMomentum:
    """Test TimeSeriesMomentum class."""

    def test_initialization_default_params(self):
        tsm = TimeSeriesMomentum()
        assert tsm.params.lookback_months == 12

    def test_initialization_custom_params(self):
        params = TSMParameters(lookback_months=6)
        tsm = TimeSeriesMomentum(params)
        assert tsm.params.lookback_months == 6

    def test_empty_prices_raises_error(self):
        tsm = TimeSeriesMomentum()
        with pytest.raises(ValueError, match="Price series cannot be empty"):
            tsm.calculate_signals(pd.Series(dtype=float))

    def test_signal_generation_returns_dataframe(self, sample_prices):
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)

        assert isinstance(signals, pd.DataFrame)
        assert 'close' in signals.columns
        assert 'returns' in signals.columns
        assert 'momentum' in signals.columns
        assert 'volatility' in signals.columns
        assert 'signal' in signals.columns
        assert 'position_size' in signals.columns

    def test_signal_values_long_cash(self, sample_prices):
        """Test that Long/Cash mode never generates short signals."""
        params = TSMParameters(position_type='long_cash')
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(sample_prices)

        # Signals should be 0 or 1 only (after shift, may have NaN at start)
        valid_signals = signals['signal'].dropna()
        assert (valid_signals >= 0).all()
        assert (valid_signals <= 1).all()

    def test_signal_values_long_short(self, sample_prices):
        """Test that Long/Short mode can generate -1, 0, or 1 signals."""
        params = TSMParameters(position_type='long_short')
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(sample_prices)

        valid_signals = signals['signal'].dropna()
        assert valid_signals.isin([-1, 0, 1]).all()

    def test_volatility_scaling_caps_position(self, sample_prices):
        """Test that position size is capped at 2.0."""
        params = TSMParameters(enable_volatility_scaling=True, volatility_target=0.10)
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(sample_prices)

        valid_positions = signals['position_size'].dropna()
        assert (valid_positions <= 2.0).all()
        assert (valid_positions >= 0.0).all()

    def test_volatility_scaling_disabled(self, sample_prices):
        """Test that position size equals signal when vol scaling disabled."""
        params = TSMParameters(enable_volatility_scaling=False)
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(sample_prices)

        # Position size should be 0 or 1 (absolute value of signal)
        valid_positions = signals['position_size'].dropna()
        assert valid_positions.isin([0.0, 1.0]).all()

    def test_strategy_returns_calculation(self, sample_prices):
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)
        returns = tsm.calculate_strategy_returns(signals)

        assert isinstance(returns, pd.DataFrame)
        assert 'strategy_return' in returns.columns
        assert 'cumulative_strategy' in returns.columns
        assert 'benchmark_return' in returns.columns
        assert 'cumulative_benchmark' in returns.columns
        assert 'drawdown' in returns.columns

    def test_cumulative_returns_start_at_100(self, sample_prices):
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)
        returns = tsm.calculate_strategy_returns(signals)

        # First non-NaN value should be close to 100
        first_valid_idx = returns['cumulative_strategy'].first_valid_index()
        assert abs(returns.loc[first_valid_idx, 'cumulative_strategy'] - 100) < 1

    def test_performance_metrics_calculation(self, sample_prices):
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)
        returns = tsm.calculate_strategy_returns(signals)
        metrics = tsm.calculate_performance_metrics(returns)

        assert isinstance(metrics, TSMPerformanceMetrics)
        assert metrics.total_return is not None
        assert metrics.annualized_return is not None
        assert metrics.sharpe_ratio is not None
        assert metrics.max_drawdown is not None
        assert metrics.win_rate is not None
        assert metrics.num_trades >= 0

    def test_max_drawdown_never_positive(self, sample_prices):
        """Test max drawdown is always <= 0."""
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)
        returns = tsm.calculate_strategy_returns(signals)
        metrics = tsm.calculate_performance_metrics(returns)

        assert metrics.max_drawdown <= 0

    def test_win_rate_between_0_and_1(self, sample_prices):
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)
        returns = tsm.calculate_strategy_returns(signals)
        metrics = tsm.calculate_performance_metrics(returns)

        assert 0 <= metrics.win_rate <= 1

    def test_uptrend_generates_long_signals(self, trending_up_prices):
        """Test that uptrending market generates mostly long signals."""
        params = TSMParameters(lookback_months=3)  # Shorter lookback
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(trending_up_prices)

        valid_signals = signals['signal'].dropna()
        long_ratio = (valid_signals == 1).sum() / len(valid_signals)

        # Should be mostly long in uptrend
        assert long_ratio > 0.7

    def test_downtrend_generates_cash_signals_long_cash(self, trending_down_prices):
        """Test that downtrending market generates cash signals in long_cash mode."""
        params = TSMParameters(lookback_months=3, position_type='long_cash')
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(trending_down_prices)

        valid_signals = signals['signal'].dropna()
        cash_ratio = (valid_signals == 0).sum() / len(valid_signals)

        # Should be mostly cash in downtrend
        assert cash_ratio > 0.7

    def test_trade_log_generation(self, sample_prices):
        tsm = TimeSeriesMomentum()
        signals = tsm.calculate_signals(sample_prices)
        trade_log = tsm.generate_trade_log(signals)

        assert isinstance(trade_log, pd.DataFrame)
        if len(trade_log) > 0:
            assert 'entry_date' in trade_log.columns
            assert 'exit_date' in trade_log.columns
            assert 'direction' in trade_log.columns
            assert 'return' in trade_log.columns


class TestScenarioComparison:
    """Test ScenarioComparison class."""

    def test_add_scenario(self):
        comparison = ScenarioComparison()
        params = TSMParameters(lookback_months=6)
        comparison.add_scenario('Test Scenario', params)

        assert 'Test Scenario' in comparison.scenarios
        assert comparison.scenarios['Test Scenario'].lookback_months == 6

    def test_run_all_scenarios(self, sample_prices):
        comparison = ScenarioComparison()
        comparison.add_scenario('Short Lookback', TSMParameters(lookback_months=3))
        comparison.add_scenario('Long Lookback', TSMParameters(lookback_months=12))

        results_df = comparison.run_all(sample_prices)

        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) == 2
        assert 'Szenario' in results_df.columns
        assert 'Total Return' in results_df.columns

    def test_get_best_scenario(self, sample_prices):
        comparison = ScenarioComparison()
        comparison.add_scenario('Scenario A', TSMParameters(lookback_months=3))
        comparison.add_scenario('Scenario B', TSMParameters(lookback_months=12))
        comparison.run_all(sample_prices)

        best_name, best_params = comparison.get_best_scenario('sharpe_ratio')

        assert best_name in ['Scenario A', 'Scenario B']
        assert isinstance(best_params, TSMParameters)


class TestHoldingPeriod:
    """Test holding period logic."""

    def test_daily_rebalancing(self, sample_prices):
        """Test that daily rebalancing allows signal changes every day."""
        params = TSMParameters(holding_period_days=1)
        tsm = TimeSeriesMomentum(params)
        signals = tsm.calculate_signals(sample_prices)

        # Count signal changes
        signal_changes = signals['signal'].diff().fillna(0) != 0
        # Should have some signal changes
        assert signal_changes.sum() > 0

    def test_monthly_rebalancing_reduces_trades(self, sample_prices):
        """Test that monthly rebalancing reduces number of signal changes."""
        params_daily = TSMParameters(holding_period_days=1)
        params_monthly = TSMParameters(holding_period_days=21)

        tsm_daily = TimeSeriesMomentum(params_daily)
        tsm_monthly = TimeSeriesMomentum(params_monthly)

        signals_daily = tsm_daily.calculate_signals(sample_prices)
        signals_monthly = tsm_monthly.calculate_signals(sample_prices)

        changes_daily = (signals_daily['signal'].diff().fillna(0) != 0).sum()
        changes_monthly = (signals_monthly['signal'].diff().fillna(0) != 0).sum()

        # Monthly should have fewer or equal signal changes
        assert changes_monthly <= changes_daily


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
