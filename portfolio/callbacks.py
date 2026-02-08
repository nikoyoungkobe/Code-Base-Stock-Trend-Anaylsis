# portfolio/callbacks.py
"""
Dash Callbacks für den Portfolio Tracker.
"""

from dash import html, callback_context, no_update
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objs as go
import plotly.express as px

from .manager import PortfolioManager
from .calculations import PortfolioCalculations


POSITIVE_COLOR = '#26a69a'
NEGATIVE_COLOR = '#ef5350'
NEUTRAL_COLOR = '#787b86'
CHART_BG_COLOR = '#1e222d'
CHART_PAPER_COLOR = '#1e222d'
CHART_FONT_COLOR = '#d1d4dc'
CHART_GRID_COLOR = '#363a45'


def get_chart_layout(title: str = ''):
    """Erstellt ein einheitliches Chart-Layout."""
    return {
        'plot_bgcolor': CHART_BG_COLOR,
        'paper_bgcolor': CHART_PAPER_COLOR,
        'font': {'color': CHART_FONT_COLOR},
        'title': {'text': title, 'font': {'size': 14}},
        'margin': {'l': 40, 'r': 20, 't': 30, 'b': 40},
        'xaxis': {'gridcolor': CHART_GRID_COLOR, 'zerolinecolor': CHART_GRID_COLOR},
        'yaxis': {'gridcolor': CHART_GRID_COLOR, 'zerolinecolor': CHART_GRID_COLOR},
        'showlegend': True,
        'legend': {'bgcolor': 'rgba(0,0,0,0)', 'font': {'size': 10}},
    }


def format_currency(value: float) -> str:
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${abs(value):,.2f}"


def format_percent(value: float) -> str:
    sign = '+' if value >= 0 else ''
    return f"{sign}{value:.2f}%"


def get_color_for_value(value: float) -> str:
    if value > 0:
        return POSITIVE_COLOR
    elif value < 0:
        return NEGATIVE_COLOR
    return NEUTRAL_COLOR


def register_portfolio_callbacks(app, portfolio_manager: PortfolioManager):
    """Registriert alle Portfolio-Callbacks."""
    calculations = PortfolioCalculations(portfolio_manager)

    # Callback 1: Portfolio-Dropdown aktualisieren
    @app.callback(
        Output('portfolio-dropdown', 'options'),
        Output('portfolio-dropdown', 'value'),
        Input('portfolio-refresh-interval', 'n_intervals'),
        Input('portfolio-data-store', 'data'),
        State('portfolio-dropdown', 'value'),
    )
    def update_portfolio_dropdown(n_intervals, store_data, current_value):
        portfolios = portfolio_manager.get_all_portfolios()
        options = [
            {'label': f"{p.name} ({len(p.holdings)} Positionen)", 'value': p.id}
            for p in portfolios
        ]

        if not current_value and portfolios:
            return options, portfolios[0].id

        if current_value and not any(p.id == current_value for p in portfolios):
            return options, portfolios[0].id if portfolios else None

        return options, current_value

    # Callback 2: Neues Portfolio Modal
    @app.callback(
        Output('create-portfolio-modal', 'style'),
        Output('portfolio-data-store', 'data', allow_duplicate=True),
        Output('portfolio-status-message', 'children'),
        Output('new-portfolio-name', 'value'),
        Input('create-portfolio-btn', 'n_clicks'),
        Input('confirm-create-portfolio-btn', 'n_clicks'),
        Input('cancel-create-portfolio-btn', 'n_clicks'),
        Input('delete-portfolio-btn', 'n_clicks'),
        State('new-portfolio-name', 'value'),
        State('new-portfolio-benchmark', 'value'),
        State('portfolio-dropdown', 'value'),
        State('create-portfolio-modal', 'style'),
        prevent_initial_call=True,
    )
    def handle_portfolio_modal(
        create_clicks, confirm_clicks, cancel_clicks, delete_clicks,
        name, benchmark, selected_portfolio, current_style
    ):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        modal_hidden = {'display': 'none'}
        modal_visible = {
            'display': 'flex',
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.7)',
            'zIndex': '1000',
            'justifyContent': 'center',
            'alignItems': 'center',
        }

        if trigger_id == 'create-portfolio-btn':
            return modal_visible, no_update, '', ''

        if trigger_id == 'cancel-create-portfolio-btn':
            return modal_hidden, no_update, '', ''

        if trigger_id == 'confirm-create-portfolio-btn':
            if not name or not name.strip():
                return modal_visible, no_update, html.Span(
                    'Bitte geben Sie einen Namen ein.',
                    style={'color': NEGATIVE_COLOR}
                ), name

            portfolio = portfolio_manager.create_portfolio(
                name=name.strip(),
                benchmark_ticker=benchmark or '^GSPC'
            )
            return modal_hidden, {'action': 'created', 'id': portfolio.id}, html.Span(
                f'Portfolio "{portfolio.name}" erstellt.',
                style={'color': POSITIVE_COLOR}
            ), ''

        if trigger_id == 'delete-portfolio-btn':
            if not selected_portfolio:
                return modal_hidden, no_update, html.Span(
                    'Kein Portfolio ausgewählt.',
                    style={'color': NEGATIVE_COLOR}
                ), ''

            portfolio = portfolio_manager.get_portfolio(selected_portfolio)
            if portfolio:
                portfolio_manager.delete_portfolio(selected_portfolio)
                return modal_hidden, {'action': 'deleted', 'id': selected_portfolio}, html.Span(
                    f'Portfolio "{portfolio.name}" gelöscht.',
                    style={'color': POSITIVE_COLOR}
                ), ''

        return modal_hidden, no_update, '', ''

    # Callback 3: Position hinzufügen
    @app.callback(
        Output('portfolio-data-store', 'data', allow_duplicate=True),
        Output('add-holding-status', 'children'),
        Output('add-holding-ticker', 'value'),
        Output('add-holding-quantity', 'value'),
        Output('add-holding-price', 'value'),
        Output('add-holding-date', 'date'),
        Input('add-holding-btn', 'n_clicks'),
        State('portfolio-dropdown', 'value'),
        State('add-holding-ticker', 'value'),
        State('add-holding-quantity', 'value'),
        State('add-holding-price', 'value'),
        State('add-holding-date', 'date'),
        prevent_initial_call=True,
    )
    def add_holding(n_clicks, portfolio_id, ticker, quantity, price, date):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update

        if not portfolio_id:
            return no_update, html.Span(
                'Bitte wählen Sie zuerst ein Portfolio.',
                style={'color': NEGATIVE_COLOR}
            ), no_update, no_update, no_update, no_update

        if not ticker or not ticker.strip():
            return no_update, html.Span(
                'Bitte geben Sie einen Ticker ein.',
                style={'color': NEGATIVE_COLOR}
            ), no_update, no_update, no_update, no_update

        if not quantity or quantity <= 0:
            return no_update, html.Span(
                'Bitte geben Sie eine gültige Anzahl ein.',
                style={'color': NEGATIVE_COLOR}
            ), no_update, no_update, no_update, no_update

        if not price or price <= 0:
            return no_update, html.Span(
                'Bitte geben Sie einen gültigen Preis ein.',
                style={'color': NEGATIVE_COLOR}
            ), no_update, no_update, no_update, no_update

        if not date:
            return no_update, html.Span(
                'Bitte wählen Sie ein Datum.',
                style={'color': NEGATIVE_COLOR}
            ), no_update, no_update, no_update, no_update

        holding = portfolio_manager.add_holding(
            portfolio_id=portfolio_id,
            ticker=ticker.strip().upper(),
            quantity=float(quantity),
            buy_price=float(price),
            buy_date=date,
        )

        if holding:
            return (
                {'action': 'holding_added', 'id': holding.id},
                html.Span(
                    f'{holding.ticker} hinzugefügt ({holding.quantity} @ ${holding.buy_price:.2f})',
                    style={'color': POSITIVE_COLOR}
                ),
                '', None, None, None,
            )

        return no_update, html.Span(
            'Fehler beim Hinzufügen der Position.',
            style={'color': NEGATIVE_COLOR}
        ), no_update, no_update, no_update, no_update

    # Callback 4: Summary Cards aktualisieren
    @app.callback(
        Output('summary-total-value', 'children'),
        Output('summary-total-value', 'style'),
        Output('summary-total-pnl', 'children'),
        Output('summary-total-pnl', 'style'),
        Output('summary-total-pnl-percent', 'children'),
        Output('summary-total-pnl-percent', 'style'),
        Output('summary-daily-change', 'children'),
        Output('summary-daily-change', 'style'),
        Output('summary-daily-change-percent', 'children'),
        Output('summary-daily-change-percent', 'style'),
        Output('summary-positions-count', 'children'),
        Input('portfolio-dropdown', 'value'),
        Input('portfolio-data-store', 'data'),
    )
    def update_summary_cards(portfolio_id, store_data):
        default_style = {'fontSize': '1.5em', 'fontWeight': 'bold', 'color': '#d1d4dc'}
        small_style = {'fontSize': '0.9em'}

        if not portfolio_id:
            return (
                '$0.00', default_style,
                '$0.00', default_style,
                '0.00%', small_style,
                '$0.00', default_style,
                '0.00%', small_style,
                '0',
            )

        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio:
            return (
                '$0.00', default_style,
                '$0.00', default_style,
                '0.00%', small_style,
                '$0.00', default_style,
                '0.00%', small_style,
                '0',
            )

        prices = portfolio_manager.get_portfolio_prices(portfolio_id)
        summary = calculations.calculate_portfolio_summary(portfolio, prices)
        daily_change, daily_change_percent = calculations.calculate_daily_change(portfolio)

        pnl_color = get_color_for_value(summary['total_pnl'])
        daily_color = get_color_for_value(daily_change)

        return (
            format_currency(summary['total_value']),
            default_style,
            format_currency(summary['total_pnl']),
            {**default_style, 'color': pnl_color},
            format_percent(summary['total_pnl_percent']),
            {**small_style, 'color': pnl_color},
            format_currency(daily_change),
            {**default_style, 'color': daily_color},
            format_percent(daily_change_percent),
            {**small_style, 'color': daily_color},
            str(summary['holdings_count']),
        )

    # Callback 5: Holdings-Tabelle aktualisieren
    @app.callback(
        Output('holdings-table-container', 'children'),
        Input('portfolio-dropdown', 'value'),
        Input('portfolio-data-store', 'data'),
    )
    def update_holdings_table(portfolio_id, store_data):
        if not portfolio_id:
            return html.P(
                'Bitte wählen Sie ein Portfolio.',
                style={'color': NEUTRAL_COLOR, 'textAlign': 'center', 'padding': '20px'}
            )

        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.holdings:
            return html.P(
                'Keine Positionen vorhanden. Fügen Sie eine Position hinzu.',
                style={'color': NEUTRAL_COLOR, 'textAlign': 'center', 'padding': '20px'}
            )

        prices = portfolio_manager.get_portfolio_prices(portfolio_id)
        performance = calculations.calculate_position_performance(portfolio, prices)

        header_style = {
            'backgroundColor': '#131722',
            'color': NEUTRAL_COLOR,
            'padding': '10px',
            'textAlign': 'left',
            'fontWeight': 'bold',
            'fontSize': '0.85em',
        }
        cell_style = {
            'padding': '10px',
            'borderBottom': f'1px solid {CHART_GRID_COLOR}',
        }

        rows = [
            html.Tr([
                html.Th('Ticker', style=header_style),
                html.Th('Anzahl', style=header_style),
                html.Th('Kaufpreis', style=header_style),
                html.Th('Akt. Preis', style=header_style),
                html.Th('Kaufwert', style=header_style),
                html.Th('Akt. Wert', style=header_style),
                html.Th('G/V', style=header_style),
                html.Th('G/V %', style=header_style),
                html.Th('', style=header_style),
            ])
        ]

        for perf in performance:
            pnl_color = get_color_for_value(perf['pnl'])
            current_price = f"${perf['current_price']:.2f}" if perf['current_price'] else 'N/A'

            rows.append(html.Tr([
                html.Td(perf['ticker'], style={**cell_style, 'fontWeight': 'bold'}),
                html.Td(f"{perf['quantity']:.2f}", style=cell_style),
                html.Td(f"${perf['buy_price']:.2f}", style=cell_style),
                html.Td(current_price, style=cell_style),
                html.Td(format_currency(perf['cost_basis']), style=cell_style),
                html.Td(format_currency(perf['current_value']), style=cell_style),
                html.Td(format_currency(perf['pnl']), style={**cell_style, 'color': pnl_color}),
                html.Td(format_percent(perf['pnl_percent']), style={**cell_style, 'color': pnl_color}),
                html.Td(
                    html.Button(
                        'X',
                        id={'type': 'delete-holding-btn', 'index': perf['holding_id']},
                        n_clicks=0,
                        style={
                            'backgroundColor': NEGATIVE_COLOR,
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '4px',
                            'padding': '4px 8px',
                            'cursor': 'pointer',
                            'fontSize': '0.8em',
                        }
                    ),
                    style=cell_style
                ),
            ]))

        return html.Table(rows, style={'width': '100%', 'borderCollapse': 'collapse'})

    # Callback 5b: Position löschen
    @app.callback(
        Output('portfolio-data-store', 'data', allow_duplicate=True),
        Input({'type': 'delete-holding-btn', 'index': ALL}, 'n_clicks'),
        State({'type': 'delete-holding-btn', 'index': ALL}, 'id'),
        State('portfolio-dropdown', 'value'),
        prevent_initial_call=True,
    )
    def delete_holding(n_clicks_list, ids, portfolio_id):
        if not any(n_clicks_list) or not portfolio_id:
            return no_update

        ctx = callback_context
        if not ctx.triggered:
            return no_update

        for i, n_clicks in enumerate(n_clicks_list):
            if n_clicks and n_clicks > 0:
                holding_id = ids[i]['index']
                if portfolio_manager.remove_holding(portfolio_id, holding_id):
                    return {'action': 'holding_deleted', 'id': holding_id}

        return no_update

    # Callback 6: Allokations-Pie-Chart
    @app.callback(
        Output('allocation-pie-chart', 'figure'),
        Input('portfolio-dropdown', 'value'),
        Input('portfolio-data-store', 'data'),
    )
    def update_allocation_chart(portfolio_id, store_data):
        fig = go.Figure()

        if not portfolio_id:
            fig.update_layout(**get_chart_layout())
            fig.add_annotation(
                text='Kein Portfolio ausgewählt',
                xref='paper', yref='paper',
                x=0.5, y=0.5, showarrow=False,
                font={'color': NEUTRAL_COLOR}
            )
            return fig

        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.holdings:
            fig.update_layout(**get_chart_layout())
            fig.add_annotation(
                text='Keine Positionen',
                xref='paper', yref='paper',
                x=0.5, y=0.5, showarrow=False,
                font={'color': NEUTRAL_COLOR}
            )
            return fig

        prices = portfolio_manager.get_portfolio_prices(portfolio_id)
        allocations = calculations.calculate_allocation(portfolio, prices)

        fig = go.Figure(data=[go.Pie(
            labels=[a['ticker'] for a in allocations],
            values=[a['value'] for a in allocations],
            hole=0.5,
            textinfo='label+percent',
            textposition='outside',
            marker={'colors': px.colors.qualitative.Set2},
        )])

        layout = get_chart_layout()
        layout['showlegend'] = False
        fig.update_layout(**layout)

        return fig

    # Callback 7: Portfolio-Wert-Chart
    @app.callback(
        Output('portfolio-value-chart', 'figure'),
        Input('portfolio-dropdown', 'value'),
        Input('portfolio-value-period', 'value'),
        Input('portfolio-data-store', 'data'),
    )
    def update_portfolio_value_chart(portfolio_id, period, store_data):
        fig = go.Figure()

        if not portfolio_id:
            fig.update_layout(**get_chart_layout())
            return fig

        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.holdings:
            fig.update_layout(**get_chart_layout())
            return fig

        history = calculations.calculate_portfolio_history(portfolio, period)
        if history is None or history.empty:
            fig.update_layout(**get_chart_layout())
            fig.add_annotation(
                text='Keine historischen Daten verfügbar',
                xref='paper', yref='paper',
                x=0.5, y=0.5, showarrow=False,
                font={'color': NEUTRAL_COLOR}
            )
            return fig

        fig.add_trace(go.Scatter(
            x=history.index,
            y=history['Value'],
            mode='lines',
            fill='tozeroy',
            name='Portfolio-Wert',
            line={'color': '#2962ff'},
            fillcolor='rgba(41, 98, 255, 0.2)',
        ))

        layout = get_chart_layout()
        layout['yaxis']['tickformat'] = '$,.0f'
        layout['showlegend'] = False
        fig.update_layout(**layout)

        return fig

    # Callback 8: Benchmark-Vergleich-Chart
    @app.callback(
        Output('benchmark-comparison-chart', 'figure'),
        Input('portfolio-dropdown', 'value'),
        Input('portfolio-value-period', 'value'),
        Input('portfolio-data-store', 'data'),
    )
    def update_benchmark_chart(portfolio_id, period, store_data):
        fig = go.Figure()

        if not portfolio_id:
            fig.update_layout(**get_chart_layout())
            return fig

        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.holdings:
            fig.update_layout(**get_chart_layout())
            return fig

        comparison = calculations.calculate_benchmark_comparison(portfolio, period)
        if comparison is None or comparison.empty:
            fig.update_layout(**get_chart_layout())
            fig.add_annotation(
                text='Keine Vergleichsdaten verfügbar',
                xref='paper', yref='paper',
                x=0.5, y=0.5, showarrow=False,
                font={'color': NEUTRAL_COLOR}
            )
            return fig

        fig.add_trace(go.Scatter(
            x=comparison.index,
            y=comparison['Portfolio'],
            mode='lines',
            name='Portfolio',
            line={'color': '#2962ff', 'width': 2},
        ))

        fig.add_trace(go.Scatter(
            x=comparison.index,
            y=comparison['Benchmark'],
            mode='lines',
            name=portfolio.benchmark_ticker,
            line={'color': '#ff6d00', 'width': 2},
        ))

        fig.add_hline(
            y=100,
            line_dash='dash',
            line_color=NEUTRAL_COLOR,
            annotation_text='Basis 100',
        )

        layout = get_chart_layout()
        layout['yaxis']['title'] = 'Normiert (Basis 100)'
        fig.update_layout(**layout)

        return fig

    # Callback 9: Position-Performance-Bar-Chart
    @app.callback(
        Output('position-performance-chart', 'figure'),
        Input('portfolio-dropdown', 'value'),
        Input('portfolio-data-store', 'data'),
    )
    def update_position_performance_chart(portfolio_id, store_data):
        fig = go.Figure()

        if not portfolio_id:
            fig.update_layout(**get_chart_layout())
            return fig

        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.holdings:
            fig.update_layout(**get_chart_layout())
            return fig

        prices = portfolio_manager.get_portfolio_prices(portfolio_id)
        performance = calculations.calculate_position_performance(portfolio, prices)

        performance.sort(key=lambda x: x['pnl_percent'], reverse=True)

        colors = [POSITIVE_COLOR if p['pnl_percent'] >= 0 else NEGATIVE_COLOR for p in performance]

        fig.add_trace(go.Bar(
            x=[p['ticker'] for p in performance],
            y=[p['pnl_percent'] for p in performance],
            marker_color=colors,
            text=[format_percent(p['pnl_percent']) for p in performance],
            textposition='outside',
        ))

        layout = get_chart_layout()
        layout['yaxis']['title'] = 'Performance (%)'
        layout['showlegend'] = False
        fig.update_layout(**layout)

        return fig
