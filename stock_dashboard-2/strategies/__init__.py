# stock_dashboard/strategies/__init__.py
"""
Trading-Strategien für das Stock Dashboard.
"""

from .sma_letf_strategy import SMALETFStrategy, StrategyConfig, CONFIGS
from .sma_letf_visualization import (
    create_signal_chart,
    create_performance_chart,
    create_drawdown_chart,
    create_annual_returns_chart,
    create_statistics_table
)

__all__ = [
    'SMALETFStrategy',
    'StrategyConfig', 
    'CONFIGS',
    'create_signal_chart',
    'create_performance_chart',
    'create_drawdown_chart',
    'create_annual_returns_chart',
    'create_statistics_table'
]
