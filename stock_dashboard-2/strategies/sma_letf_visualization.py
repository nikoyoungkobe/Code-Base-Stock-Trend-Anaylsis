# strategies/sma_letf_visualization.py
"""
Visualisierungen für die SMA 200 LETF Strategie.
Erstellt interaktive Plotly-Charts für das Dashboard.
"""

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_signal_chart(df: pd.DataFrame, config) -> go.Figure:
    """
    Erstellt Chart mit Signalgeber, SMA 200 und Buy/Sell-Signalen.
    
    Args:
        df: DataFrame mit Backtest-Ergebnissen
        config: StrategyConfig Objekt
        
    Returns:
        Plotly Figure
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(
            f'{config.signal_ticker} mit SMA {config.sma_period}',
            'Investitionsstatus'
        )
    )
    
    # Signalgeber Kurs
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['signal_close'],
            mode='lines',
            name=f'{config.signal_ticker} Kurs',
            line=dict(color='#2196F3', width=1.5)
        ),
        row=1, col=1
    )
    
    # SMA 200
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['sma_200'],
            mode='lines',
            name=f'SMA {config.sma_period}',
            line=dict(color='#FF9800', width=2, dash='dash')
        ),
        row=1, col=1
    )
    
    # Buy-Signale (Einstieg)
    buy_signals = df[df['signal_change'] == 1]
    fig.add_trace(
        go.Scatter(
            x=buy_signals.index,
            y=buy_signals['signal_close'],
            mode='markers',
            name='Einstieg (Buy)',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='#4CAF50',
                line=dict(width=1, color='darkgreen')
            )
        ),
        row=1, col=1
    )
    
    # Sell-Signale (Ausstieg)
    sell_signals = df[df['signal_change'] == -1]
    fig.add_trace(
        go.Scatter(
            x=sell_signals.index,
            y=sell_signals['signal_close'],
            mode='markers',
            name='Ausstieg (Sell)',
            marker=dict(
                symbol='triangle-down',
                size=12,
                color='#F44336',
                line=dict(width=1, color='darkred')
            )
        ),
        row=1, col=1
    )
    
    # Investitionsstatus (unterer Chart)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['signal'],
            mode='lines',
            name='Status',
            fill='tozeroy',
            line=dict(color='#4CAF50', width=0),
            fillcolor='rgba(76, 175, 80, 0.3)'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f'SMA {config.sma_period} Trendfolge-Signale',
        template='plotly_white',
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Kurs", row=1, col=1)
    fig.update_yaxes(
        title_text="Investiert", 
        tickvals=[0, 1], 
        ticktext=['Cash', 'LETF'],
        row=2, col=1
    )
    fig.update_xaxes(title_text="Datum", row=2, col=1)
    
    return fig


def create_performance_chart(df: pd.DataFrame, config, initial_capital: float) -> go.Figure:
    """
    Erstellt Performance-Vergleichschart.
    
    Args:
        df: DataFrame mit Backtest-Ergebnissen
        config: StrategyConfig Objekt
        initial_capital: Startkapital
        
    Returns:
        Plotly Figure
    """
    fig = go.Figure()
    
    # Strategie
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['strategy_value'],
            mode='lines',
            name=f'SMA {config.sma_period} Strategie',
            line=dict(color='#4CAF50', width=2.5)
        )
    )
    
    # Buy & Hold LETF
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['bh_letf_value'],
            mode='lines',
            name=f'Buy & Hold {config.trade_ticker}',
            line=dict(color='#F44336', width=2)
        )
    )
    
    # Buy & Hold Index
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['bh_index_value'],
            mode='lines',
            name=f'Buy & Hold {config.signal_ticker}',
            line=dict(color='#2196F3', width=2, dash='dash')
        )
    )
    
    # Startkapital-Linie
    fig.add_hline(
        y=initial_capital,
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Startkapital: ${initial_capital:,.0f}"
    )
    
    fig.update_layout(
        title=f'Portfolio-Entwicklung: ${initial_capital:,.0f} Startkapital',
        xaxis_title='Datum',
        yaxis_title='Portfolio-Wert ($)',
        template='plotly_white',
        height=500,
        hovermode='x unified',
        yaxis=dict(tickformat="$,.0f"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_drawdown_chart(df: pd.DataFrame, config) -> go.Figure:
    """
    Erstellt Drawdown-Vergleichschart.
    
    Args:
        df: DataFrame mit Backtest-Ergebnissen
        config: StrategyConfig Objekt
        
    Returns:
        Plotly Figure
    """
    fig = go.Figure()
    
    # Strategie Drawdown
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['strategy_drawdown'],
            mode='lines',
            name=f'SMA {config.sma_period} Strategie',
            fill='tozeroy',
            line=dict(color='#4CAF50', width=1),
            fillcolor='rgba(76, 175, 80, 0.3)'
        )
    )
    
    # Buy & Hold LETF Drawdown
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['bh_letf_drawdown'],
            mode='lines',
            name=f'Buy & Hold {config.trade_ticker}',
            fill='tozeroy',
            line=dict(color='#F44336', width=1),
            fillcolor='rgba(244, 67, 54, 0.3)'
        )
    )
    
    # Markante Drawdown-Level
    fig.add_hline(y=-20, line_dash="dash", line_color="orange", 
                  annotation_text="-20% (Korrektur)")
    fig.add_hline(y=-50, line_dash="dash", line_color="red", 
                  annotation_text="-50% (Crash)")
    
    fig.update_layout(
        title='Drawdown-Vergleich (Verlust vom Höchststand)',
        xaxis_title='Datum',
        yaxis_title='Drawdown (%)',
        template='plotly_white',
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_annual_returns_chart(df: pd.DataFrame, config) -> go.Figure:
    """
    Erstellt Chart mit jährlichen Renditen.
    
    Args:
        df: DataFrame mit Backtest-Ergebnissen
        config: StrategyConfig Objekt
        
    Returns:
        Plotly Figure
    """
    # Jährliche Renditen berechnen
    df_yearly = df.copy()
    df_yearly['year'] = df_yearly.index.year
    
    yearly_returns = []
    for year in df_yearly['year'].unique():
        year_data = df_yearly[df_yearly['year'] == year]
        if len(year_data) > 0:
            strategy_return = (year_data['strategy_value'].iloc[-1] / year_data['strategy_value'].iloc[0] - 1) * 100
            bh_letf_return = (year_data['bh_letf_value'].iloc[-1] / year_data['bh_letf_value'].iloc[0] - 1) * 100
            bh_index_return = (year_data['bh_index_value'].iloc[-1] / year_data['bh_index_value'].iloc[0] - 1) * 100
            yearly_returns.append({
                'Jahr': year,
                'Strategie': strategy_return,
                'LETF B&H': bh_letf_return,
                'Index B&H': bh_index_return
            })
    
    yearly_df = pd.DataFrame(yearly_returns)
    
    fig = go.Figure()
    
    # Strategie
    fig.add_trace(
        go.Bar(
            x=yearly_df['Jahr'],
            y=yearly_df['Strategie'],
            name=f'SMA {config.sma_period} Strategie',
            marker_color='#4CAF50'
        )
    )
    
    # Buy & Hold LETF
    fig.add_trace(
        go.Bar(
            x=yearly_df['Jahr'],
            y=yearly_df['LETF B&H'],
            name=f'Buy & Hold {config.trade_ticker}',
            marker_color='#F44336'
        )
    )
    
    # Buy & Hold Index
    fig.add_trace(
        go.Bar(
            x=yearly_df['Jahr'],
            y=yearly_df['Index B&H'],
            name=f'Buy & Hold {config.signal_ticker}',
            marker_color='#2196F3'
        )
    )
    
    fig.update_layout(
        title='Jährliche Renditen im Vergleich',
        xaxis_title='Jahr',
        yaxis_title='Rendite (%)',
        template='plotly_white',
        height=400,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Null-Linie hervorheben
    fig.add_hline(y=0, line_color="gray", line_width=1)
    
    return fig


def create_statistics_table(stats: dict) -> go.Figure:
    """
    Erstellt eine Tabelle mit den Statistiken.
    
    Args:
        stats: Dictionary mit Statistiken
        
    Returns:
        Plotly Figure mit Tabelle
    """
    headers = ['Kennzahl', 'Strategie', 'B&H LETF', 'B&H Index']
    
    rows = [
        ['Endwert', stats['Strategie']['Endwert'], stats['Buy & Hold LETF']['Endwert'], stats['Buy & Hold Index']['Endwert']],
        ['Gesamtrendite', stats['Strategie']['Gesamtrendite'], stats['Buy & Hold LETF']['Gesamtrendite'], stats['Buy & Hold Index']['Gesamtrendite']],
        ['CAGR', stats['Strategie']['CAGR'], stats['Buy & Hold LETF']['CAGR'], stats['Buy & Hold Index']['CAGR']],
        ['Volatilität', stats['Strategie']['Volatilität'], stats['Buy & Hold LETF']['Volatilität'], stats['Buy & Hold Index']['Volatilität']],
        ['Sharpe Ratio', stats['Strategie']['Sharpe Ratio'], stats['Buy & Hold LETF']['Sharpe Ratio'], '-'],
        ['Max Drawdown', stats['Strategie']['Max Drawdown'], stats['Buy & Hold LETF']['Max Drawdown'], '-'],
    ]
    
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=headers,
                fill_color='#4CAF50',
                font=dict(color='white', size=14),
                align='center',
                height=35
            ),
            cells=dict(
                values=list(zip(*rows)),
                fill_color=[['#f9f9f9', 'white'] * 3],
                font=dict(size=13),
                align='center',
                height=30
            )
        )
    ])
    
    fig.update_layout(
        title=f"Performance-Übersicht ({stats['Zeitraum']})",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig
