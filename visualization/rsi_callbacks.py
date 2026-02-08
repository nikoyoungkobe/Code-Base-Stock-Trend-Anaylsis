# visualization/rsi_callbacks.py
"""
Dash Callbacks für RSI Mean-Reversion Backtest.
"""

import os
from datetime import datetime
from dash import html, no_update, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd

from calculations.rsi_mean_reversion import (
    RSIMeanReversion,
    RSIMeanReversionParameters,
    RSIParameterOptimizer
)
from visualization.components.rsi_components import create_rsi_metric_card


def parse_comma_list(text: str, dtype=float) -> list:
    """
    Parst kommagetrennte Werte und Ranges.

    Unterstützte Formate:
    - Einzelwerte: "10, 20, 30"
    - Ranges: "10-30" (alle Werte von 10 bis 30)
    - Ranges mit Step: "10-30:5" (10, 15, 20, 25, 30)
    - Kombiniert: "5, 10-20, 25, 30-40:2"

    Args:
        text: Input-String
        dtype: Zieltyp (int oder float)

    Returns:
        Liste von Werten
    """
    if not text or not text.strip():
        return []

    result = []
    parts = [p.strip() for p in text.split(',') if p.strip()]

    for part in parts:
        try:
            # Check for range notation: "start-end" or "start-end:step"
            if '-' in part and not part.startswith('-'):
                # Handle negative numbers at start
                range_parts = part.split('-')
                if len(range_parts) == 2:
                    start_str, end_str = range_parts

                    # Check for step notation in end part
                    step = 1
                    if ':' in end_str:
                        end_str, step_str = end_str.split(':')
                        step = float(step_str) if dtype == float else int(step_str)

                    start = float(start_str) if dtype == float else int(start_str)
                    end = float(end_str) if dtype == float else int(end_str)

                    # Generate range
                    if dtype == int:
                        result.extend(range(int(start), int(end) + 1, int(step)))
                    else:
                        # Float range
                        current = start
                        while current <= end + 0.0001:  # Small epsilon for float comparison
                            result.append(round(current, 2))
                            current += step
                elif len(range_parts) == 3 and range_parts[0] == '':
                    # Negative start: "-10-20" means -10 to 20
                    start = -float(range_parts[1]) if dtype == float else -int(range_parts[1])
                    end_str = range_parts[2]

                    step = 1
                    if ':' in end_str:
                        end_str, step_str = end_str.split(':')
                        step = float(step_str) if dtype == float else int(step_str)

                    end = float(end_str) if dtype == float else int(end_str)

                    if dtype == int:
                        result.extend(range(int(start), int(end) + 1, int(step)))
                    else:
                        current = start
                        while current <= end + 0.0001:
                            result.append(round(current, 2))
                            current += step
                else:
                    # Invalid format, try as single value
                    result.append(dtype(part))
            else:
                # Single value
                result.append(dtype(part))
        except (ValueError, TypeError):
            continue

    # Remove duplicates and sort
    result = sorted(list(set(result)))
    return result


def register_rsi_callbacks(app, stock_manager):
    """Registriert alle RSI-Backtest Callbacks."""

    # =========================================================================
    # Callback: Einzelner Backtest
    # =========================================================================
    @app.callback(
        Output('rsi-signal-chart', 'figure'),
        Output('rsi-returns-chart', 'figure'),
        Output('rsi-metrics-container', 'children'),
        Input('rsi-run-backtest-btn', 'n_clicks'),
        State('ticker-dropdown', 'value'),
        State('rsi-period-input', 'value'),
        State('rsi-oversold-input', 'value'),
        State('rsi-overbought-input', 'value'),
        State('rsi-ma-period-input', 'value'),
        State('rsi-stddev-input', 'value'),
        State('rsi-tp-input', 'value'),
        State('rsi-sl-input', 'value'),
        State('rsi-position-type', 'value'),
    )
    def run_single_backtest(
        n_clicks, selected_tickers,
        rsi_period, rsi_os, rsi_ob,
        ma_period, stddev_mult,
        take_profit, stop_loss,
        position_type
    ):
        """Führt einzelnen Backtest durch und zeigt Ergebnisse."""
        signal_fig = go.Figure()
        returns_fig = go.Figure()
        metrics_html = html.P(
            "Wählen Sie einen Ticker aus und klicken Sie 'Backtest starten'.",
            style={'textAlign': 'center', 'color': '#666'}
        )

        if not n_clicks or not selected_tickers:
            signal_fig.update_layout(title="Wählen Sie einen Ticker aus")
            returns_fig.update_layout(title="Wählen Sie einen Ticker aus")
            return signal_fig, returns_fig, metrics_html

        ticker = selected_tickers[0] if isinstance(selected_tickers, list) else selected_tickers

        # Preisdaten holen
        prices = stock_manager.get_price_series(ticker, 'Close')
        if prices is None or prices.empty:
            signal_fig.update_layout(title=f"Keine Daten für {ticker}")
            returns_fig.update_layout(title=f"Keine Daten für {ticker}")
            return signal_fig, returns_fig, metrics_html

        # Parameter erstellen
        params = RSIMeanReversionParameters(
            rsi_period=int(rsi_period or 14),
            rsi_oversold=float(rsi_os or 30),
            rsi_overbought=float(rsi_ob or 70),
            ma_period=int(ma_period or 20),
            std_dev_multiplier=float(stddev_mult or 1.0),
            take_profit_pct=float(take_profit or 5.0),
            stop_loss_pct=float(stop_loss or 2.0),
            position_type=position_type or 'long_short'
        )

        try:
            # Strategie ausführen
            strategy = RSIMeanReversion(params)
            signals = strategy.calculate_signals(prices)
            trades = strategy.simulate_trades(signals)
            returns = strategy.calculate_returns(signals)
            metrics = strategy.calculate_metrics()

        except Exception as e:
            signal_fig.update_layout(title=f"Fehler: {str(e)}")
            returns_fig.update_layout(title=f"Fehler: {str(e)}")
            return signal_fig, returns_fig, html.P(f"Fehler: {str(e)}", style={'color': 'red'})

        # =====================================================================
        # Signal Chart mit Subplots
        # =====================================================================
        signal_fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=['Preis & Bollinger Bands', 'RSI']
        )

        # Preis
        signal_fig.add_trace(
            go.Scatter(
                x=signals.index, y=signals['close'],
                mode='lines', name='Preis',
                line=dict(color='#333', width=1.5)
            ),
            row=1, col=1
        )

        # Moving Average
        signal_fig.add_trace(
            go.Scatter(
                x=signals.index, y=signals['ma'],
                mode='lines', name=f'MA({params.ma_period})',
                line=dict(color='#2196F3', width=1, dash='dash')
            ),
            row=1, col=1
        )

        # Bollinger Bands
        signal_fig.add_trace(
            go.Scatter(
                x=signals.index, y=signals['upper_band'],
                mode='lines', name='Upper Band',
                line=dict(color='#FF9800', width=1),
                showlegend=False
            ),
            row=1, col=1
        )
        signal_fig.add_trace(
            go.Scatter(
                x=signals.index, y=signals['lower_band'],
                mode='lines', name='Lower Band',
                line=dict(color='#FF9800', width=1),
                fill='tonexty',
                fillcolor='rgba(255, 152, 0, 0.1)'
            ),
            row=1, col=1
        )

        # Trade Markers
        if not trades.empty:
            # Entry Points
            long_entries = trades[trades['direction'] == 'Long']
            short_entries = trades[trades['direction'] == 'Short']

            if not long_entries.empty:
                signal_fig.add_trace(
                    go.Scatter(
                        x=long_entries['entry_date'],
                        y=long_entries['entry_price'],
                        mode='markers',
                        name='Long Entry',
                        marker=dict(symbol='triangle-up', size=12, color='#4CAF50')
                    ),
                    row=1, col=1
                )

            if not short_entries.empty:
                signal_fig.add_trace(
                    go.Scatter(
                        x=short_entries['entry_date'],
                        y=short_entries['entry_price'],
                        mode='markers',
                        name='Short Entry',
                        marker=dict(symbol='triangle-down', size=12, color='#f44336')
                    ),
                    row=1, col=1
                )

            # Exit Points (TP/SL)
            tp_exits = trades[trades['exit_reason'] == 'Take Profit']
            sl_exits = trades[trades['exit_reason'] == 'Stop Loss']

            if not tp_exits.empty:
                signal_fig.add_trace(
                    go.Scatter(
                        x=tp_exits['exit_date'],
                        y=tp_exits['exit_price'],
                        mode='markers',
                        name='Take Profit',
                        marker=dict(symbol='star', size=10, color='#4CAF50')
                    ),
                    row=1, col=1
                )

            if not sl_exits.empty:
                signal_fig.add_trace(
                    go.Scatter(
                        x=sl_exits['exit_date'],
                        y=sl_exits['exit_price'],
                        mode='markers',
                        name='Stop Loss',
                        marker=dict(symbol='x', size=10, color='#f44336')
                    ),
                    row=1, col=1
                )

        # RSI
        signal_fig.add_trace(
            go.Scatter(
                x=signals.index, y=signals['rsi'],
                mode='lines', name='RSI',
                line=dict(color='#9C27B0', width=1.5)
            ),
            row=2, col=1
        )

        # RSI Thresholds
        signal_fig.add_hline(y=params.rsi_overbought, line_dash='dash',
                            line_color='#f44336', row=2, col=1)
        signal_fig.add_hline(y=params.rsi_oversold, line_dash='dash',
                            line_color='#4CAF50', row=2, col=1)

        signal_fig.update_layout(
            title=f'RSI Mean-Reversion: {ticker}',
            template='plotly_white',
            hovermode='x unified',
            showlegend=True,
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
            margin=dict(l=50, r=20, t=60, b=20)
        )
        signal_fig.update_yaxes(title_text='Preis ($)', row=1, col=1)
        signal_fig.update_yaxes(title_text='RSI', row=2, col=1, range=[0, 100])

        # =====================================================================
        # Returns Chart
        # =====================================================================
        returns_fig = go.Figure()

        returns_fig.add_trace(go.Scatter(
            x=returns.index, y=returns['cumulative_strategy'],
            mode='lines', name='Strategie',
            line=dict(color='#2196F3', width=2)
        ))

        returns_fig.add_trace(go.Scatter(
            x=returns.index, y=returns['cumulative_benchmark'],
            mode='lines', name='Buy & Hold',
            line=dict(color='#9E9E9E', width=2, dash='dash')
        ))

        returns_fig.add_trace(go.Scatter(
            x=returns.index, y=returns['drawdown'] * 100,
            mode='lines', name='Drawdown (%)',
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.2)',
            line=dict(color='rgba(255, 0, 0, 0.5)', width=1),
            yaxis='y2'
        ))

        returns_fig.update_layout(
            title='Kumulative Rendite vs. Buy & Hold',
            template='plotly_white',
            hovermode='x unified',
            yaxis=dict(title='Wert (Basis 100)', side='left'),
            yaxis2=dict(title='Drawdown (%)', overlaying='y', side='right', range=[-50, 5]),
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
            margin=dict(l=50, r=50, t=40, b=20),
            xaxis_rangeslider_visible=True
        )

        # =====================================================================
        # Metriken
        # =====================================================================
        metrics_html = html.Div([
            create_rsi_metric_card(
                'Total Return',
                f'{metrics.total_return:.1%}',
                '#4CAF50' if metrics.total_return > 0 else '#f44336'
            ),
            create_rsi_metric_card(
                'Sharpe Ratio',
                f'{metrics.sharpe_ratio:.2f}',
                '#4CAF50' if metrics.sharpe_ratio > 0.5 else '#FF9800' if metrics.sharpe_ratio > 0 else '#f44336'
            ),
            create_rsi_metric_card(
                'Max Drawdown',
                f'{metrics.max_drawdown:.1%}',
                '#f44336'
            ),
            create_rsi_metric_card(
                'Win Rate',
                f'{metrics.win_rate:.1%}',
                '#4CAF50' if metrics.win_rate > 0.5 else '#FF9800'
            ),
            create_rsi_metric_card(
                'Trades',
                f'{metrics.num_trades}',
                '#333'
            ),
            create_rsi_metric_card(
                'Profit Factor',
                f'{metrics.profit_factor:.2f}',
                '#4CAF50' if metrics.profit_factor > 1 else '#f44336'
            ),
            create_rsi_metric_card(
                'Avg Trade',
                f'{metrics.avg_trade_return:.2f}%',
                '#4CAF50' if metrics.avg_trade_return > 0 else '#f44336'
            ),
            create_rsi_metric_card(
                'vs. B&H',
                f'{metrics.excess_return:.1%}',
                '#4CAF50' if metrics.excess_return > 0 else '#f44336'
            ),
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'gap': '15px',
            'justifyContent': 'center',
            'marginBottom': '20px'
        })

        return signal_fig, returns_fig, metrics_html

    # =========================================================================
    # Callback: Parameter-Optimierung
    # =========================================================================
    @app.callback(
        Output('optimization-results-store', 'data'),
        Output('optimization-status', 'children'),
        Output('optimization-results-container', 'style'),
        Input('rsi-run-optimization-btn', 'n_clicks'),
        State('ticker-dropdown', 'value'),
        State('opt-rsi-periods', 'value'),
        State('opt-take-profits', 'value'),
        State('opt-stop-losses', 'value'),
        State('opt-ma-periods', 'value'),
        State('opt-stddev-mults', 'value'),
        State('opt-metric-select', 'value'),
        prevent_initial_call=True,
    )
    def run_optimization(
        n_clicks, selected_tickers,
        rsi_periods_str, tps_str, sls_str,
        ma_periods_str, stddev_str,
        optimize_metric
    ):
        if not n_clicks or not selected_tickers:
            return no_update, "Bitte wählen Sie einen Ticker aus.", {'display': 'none'}

        ticker = selected_tickers[0] if isinstance(selected_tickers, list) else selected_tickers

        # Preisdaten holen
        prices = stock_manager.get_price_series(ticker, 'Close')
        if prices is None or prices.empty:
            return no_update, f"Keine Daten für {ticker}.", {'display': 'none'}

        # Parameter parsen
        rsi_periods = parse_comma_list(rsi_periods_str, int) or [14]
        take_profits = parse_comma_list(tps_str, float) or [5.0]
        stop_losses = parse_comma_list(sls_str, float) or [2.0]
        ma_periods = parse_comma_list(ma_periods_str, int) or [20]
        stddev_mults = parse_comma_list(stddev_str, float) or [1.0]

        # Optimierung durchführen
        optimizer = RSIParameterOptimizer()
        param_grid = optimizer.define_parameter_grid(
            rsi_periods=rsi_periods,
            rsi_oversold=[30],  # Fixed für Einfachheit
            rsi_overbought=[70],
            ma_periods=ma_periods,
            std_dev_multipliers=stddev_mults,
            take_profits=take_profits,
            stop_losses=stop_losses,
        )

        try:
            results_df = optimizer.run_optimization(
                prices,
                param_grid,
                optimize_metric=optimize_metric,
                verbose=False
            )

            if results_df.empty:
                return no_update, "Keine Ergebnisse generiert.", {'display': 'none'}

            # Speichere als JSON-kompatibles Format
            results_data = results_df.to_dict('records')

            status = f"Optimierung abgeschlossen: {len(results_data)} Kombinationen getestet."
            if optimizer.best_params:
                status += f" Beste Sharpe Ratio: {optimizer.best_metrics.sharpe_ratio:.2f}"

            return results_data, status, {'display': 'block'}

        except Exception as e:
            return no_update, f"Fehler: {str(e)}", {'display': 'none'}

    # =========================================================================
    # Callback: Heatmap
    # =========================================================================
    @app.callback(
        Output('rsi-heatmap-chart', 'figure'),
        Input('optimization-results-store', 'data'),
        Input('heatmap-x-param', 'value'),
        Input('heatmap-y-param', 'value'),
        State('opt-metric-select', 'value'),
    )
    def update_heatmap(results_data, x_param, y_param, metric):
        fig = go.Figure()

        if not results_data:
            fig.update_layout(title="Keine Daten verfügbar")
            return fig

        df = pd.DataFrame(results_data)

        if x_param not in df.columns or y_param not in df.columns:
            fig.update_layout(title="Parameter nicht gefunden")
            return fig

        # Pivot für Heatmap
        try:
            pivot = df.pivot_table(
                values=metric,
                index=y_param,
                columns=x_param,
                aggfunc='mean'
            )

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='RdYlGn',
                text=[[f'{v:.2f}' for v in row] for row in pivot.values],
                texttemplate='%{text}',
                textfont={"size": 10},
                hovertemplate=f'{x_param}: %{{x}}<br>{y_param}: %{{y}}<br>{metric}: %{{z:.3f}}<extra></extra>'
            ))

            fig.update_layout(
                title=f'{metric} nach {x_param} und {y_param}',
                xaxis_title=x_param,
                yaxis_title=y_param,
                template='plotly_white',
            )

        except Exception as e:
            fig.update_layout(title=f"Fehler: {str(e)}")

        return fig

    # =========================================================================
    # Callback: Top-N Tabelle
    # =========================================================================
    @app.callback(
        Output('optimization-results-table', 'children'),
        Input('optimization-results-store', 'data'),
        State('opt-metric-select', 'value'),
    )
    def update_results_table(results_data, metric):
        if not results_data:
            return html.P("Keine Daten verfügbar.", style={'textAlign': 'center', 'color': '#666'})

        df = pd.DataFrame(results_data)

        # Top 10 nach Metrik
        top_df = df.nlargest(10, metric) if metric in df.columns else df.head(10)

        # Tabelle erstellen
        header = html.Tr([
            html.Th('RSI', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('MA', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('TP', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('SL', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('Return', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('Sharpe', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('Win Rate', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
            html.Th('Trades', style={'padding': '8px', 'borderBottom': '2px solid #ddd'}),
        ])

        rows = []
        for _, row in top_df.iterrows():
            rows.append(html.Tr([
                html.Td(f"{int(row.get('rsi_period', 0))}", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
                html.Td(f"{int(row.get('ma_period', 0))}", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
                html.Td(f"{row.get('take_profit', 0):.1f}%", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
                html.Td(f"{row.get('stop_loss', 0):.1f}%", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
                html.Td(
                    f"{row.get('total_return', 0):.1%}",
                    style={
                        'padding': '8px',
                        'borderBottom': '1px solid #eee',
                        'color': '#4CAF50' if row.get('total_return', 0) > 0 else '#f44336'
                    }
                ),
                html.Td(f"{row.get('sharpe_ratio', 0):.2f}", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
                html.Td(f"{row.get('win_rate', 0):.1%}", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
                html.Td(f"{int(row.get('num_trades', 0))}", style={'padding': '8px', 'borderBottom': '1px solid #eee'}),
            ]))

        return html.Table(
            [html.Thead(header), html.Tbody(rows)],
            style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'textAlign': 'center',
                'backgroundColor': 'white',
                'borderRadius': '5px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            }
        )

    # =========================================================================
    # Callback: CSV Download
    # =========================================================================
    @app.callback(
        Output('download-csv', 'data'),
        Output('download-status', 'children'),
        Input('download-results-btn', 'n_clicks'),
        State('optimization-results-store', 'data'),
        prevent_initial_call=True,
    )
    def download_results(n_clicks, results_data):
        if not n_clicks or not results_data:
            return no_update, ""

        df = pd.DataFrame(results_data)

        # Speichere auch lokal
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'rsi_optimization_{timestamp}.csv'
        filepath = os.path.join(os.path.dirname(__file__), '..', 'backtest_results', filename)

        # Erstelle Verzeichnis falls nicht vorhanden
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)

        return (
            dict(content=df.to_csv(index=False), filename=filename),
            f"Gespeichert: {filepath}"
        )
