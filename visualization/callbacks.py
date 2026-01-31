# visualization/callbacks.py
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta
from stock_dashboard.data.fetch_data import GetClosingPrices
from stock_dashboard.data.macro_data import fetch_vix_data, fetch_yield_curve_data
from stock_dashboard.config.settings import FRED_API_KEY

def register_callbacks(app, stock_manager):
    @app.callback(
        Output('ticker-dropdown', 'options'),
        Output('ticker-dropdown', 'value'),
        Output('add-ticker-status', 'children'),
        Input('add-ticker-button', 'n_clicks'),
        State('new-ticker-input', 'value'),
        State('ticker-dropdown', 'options'),
        State('ticker-dropdown', 'value')
    )
    def add_new_tickers(n_clicks, new_tickers_input, current_options, current_selected_values):
        if n_clicks is None or n_clicks == 0:
            return current_options, current_selected_values, ""
        if not new_tickers_input:
            return current_options, current_selected_values, "Bitte geben Sie Ticker Symbole ein."
        new_tickers_list = [t.strip().upper() for t in new_tickers_input.split(',') if t.strip()]
        existing_tickers = [option['value'] for option in current_options]
        tickers_to_add = [t for t in new_tickers_list if t not in existing_tickers]
        if not tickers_to_add:
            return current_options, current_selected_values, "Alle eingegebenen Ticker sind bereits vorhanden."
        for ticker in tickers_to_add:
            if ticker not in stock_manager.ticker_list:
                stock_manager.ticker_list.append(ticker)
        original_start_date = stock_manager.start_date
        original_end_date = stock_manager.end_date
        stock_manager.start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
        stock_manager.end_date = datetime.now().strftime('%Y-%m-%d')
        stock_manager.fetch_historical_data()
        stock_manager.start_date = original_start_date
        stock_manager.end_date = original_end_date
        updated_available_tickers = [
            ticker for ticker in stock_manager.ticker_list
            if ticker in stock_manager.historical_data and not stock_manager.historical_data[ticker].empty
        ]
        new_options = [{'label': ticker, 'value': ticker} for ticker in updated_available_tickers]
        updated_selected_values = current_selected_values if current_selected_values else []
        for ticker in tickers_to_add:
            if ticker in updated_available_tickers and ticker not in updated_selected_values:
                updated_selected_values.append(ticker)
        status_message = f"Ticker {', '.join(tickers_to_add)} hinzugefügt."
        if any(t not in updated_available_tickers for t in tickers_to_add):
            failed_tickers = [t for t in tickers_to_add if t not in updated_available_tickers]
            status_message += f" (Hinweis: Daten konnten für {', '.join(failed_tickers)} nicht abgerufen werden.)"
        return new_options, updated_selected_values, status_message

    @app.callback(
        Output('stock-price-plot', 'figure'),
        Output('plot-info-status', 'children'),
        Input('ticker-dropdown', 'value'),
        Input('relative-change-checkbox', 'value')
    )
    def update_graph(selected_tickers, relative_change_values):
        relative_change_active = 'relative_change' in relative_change_values
        if not selected_tickers:
            return go.Figure(), "Bitte wählen Sie mindestens einen Ticker aus."
        if not isinstance(selected_tickers, list):
            selected_tickers = [selected_tickers]
        fig = go.Figure()
        plot_info_messages = []
        plot_title = 'Historische Schlusskurse'
        y_axis_label = 'Schlusskurs ($)'
        if relative_change_active:
            plot_title = 'Relative Veränderung der Schlusskurse (Basis = 100)'
            y_axis_label = 'Relative Veränderung (Index 100)'
        for ticker_symbol in selected_tickers:
            df = stock_manager.get_data_for_ticker(ticker_symbol)
            if df is None or df.empty:
                plot_info_messages.append(f"Keine Daten für {ticker_symbol} verfügbar.")
                continue
            if 'Close' in df.columns:
                data_to_plot = df['Close']
                if relative_change_active:
                    first_value = data_to_plot.iloc[0]
                    if first_value != 0:
                        data_to_plot = (data_to_plot / first_value) * 100
                    else:
                        plot_info_messages.append(f"Warnung: Erster Schlusskurs für {ticker_symbol} ist Null.")
                        continue
                fig.add_trace(go.Scatter(x=df.index, y=data_to_plot, mode='lines', name=ticker_symbol))
            else:
                plot_info_messages.append(f"Fehler: 'Close'-Spalte nicht gefunden für {ticker_symbol}.")
        if not fig.data:
            fig.update_layout(title='Keine Daten zum Plotten verfügbar', xaxis_title='Datum', yaxis_title=y_axis_label)
            return fig, html.Div(plot_info_messages)
        fig.update_layout(
            title=plot_title,
            xaxis_title='Datum',
            yaxis_title=y_axis_label,
            hovermode="x unified",
            template='plotly_white',
            xaxis_rangeslider_visible=True
        )
        status_text = html.Div([
            html.P(f"Plot zeigt Daten für: {', '.join([t for t in selected_tickers if t in stock_manager.historical_data and not stock_manager.historical_data[t].empty])}"),
            html.P("Hinweise: " + "; ".join(plot_info_messages), style={'color': 'orange', 'fontWeight': 'bold'}) if plot_info_messages else ""
        ])
        return fig, status_text

    @app.callback(
        Output('fcf-bar-chart', 'figure'),
        Output('debt-bar-chart', 'figure'),
        Output('revenue-profit-margin-chart', 'figure'),
        Input('ticker-dropdown', 'value')
    )
    def update_financial_charts(selected_tickers):
        if not selected_tickers:
            empty_fig = go.Figure()
            empty_fig.update_layout(title="Wählen Sie einen Ticker für Finanzdaten aus.")
            return empty_fig, empty_fig, empty_fig
        ticker_symbol = selected_tickers[0] if isinstance(selected_tickers, list) else selected_tickers
        financial_data = stock_manager.get_financial_data_for_ticker(ticker_symbol)
        fcf_fig = go.Figure()
        debt_fig = go.Figure()
        revenue_profit_margin_fig = go.Figure()
        if not financial_data:
            fcf_fig.update_layout(title=f"Keine Finanzdaten für {ticker_symbol} verfügbar")
            debt_fig.update_layout(title=f"Keine Finanzdaten für {ticker_symbol} verfügbar")
            revenue_profit_margin_fig.update_layout(title=f"Keine Finanzdaten für {ticker_symbol} verfügbar")
            return fcf_fig, debt_fig, revenue_profit_margin_fig
        cashflow_df = financial_data.get('cashflow')
        if cashflow_df is not None and 'Free Cash Flow' in cashflow_df.index:
            fcf_series = cashflow_df.loc['Free Cash Flow'].dropna().sort_index()
            fcf_fig = go.Figure(data=[go.Bar(x=fcf_series.index, y=fcf_series.values, name='Free Cash Flow', marker_color='skyblue')])
            fcf_fig.update_layout(
                title_text=f'Free Cash Flow für {ticker_symbol}',
                xaxis_title='Jahr',
                yaxis_title='FCF (in Mio. $)',
                template='plotly_white',
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis=dict(tickformat=".2s", hoverformat=".2s")
            )
        else:
            fcf_fig.update_layout(title=f"Free Cash Flow für {ticker_symbol} nicht verfügbar")
        balance_sheet_df = financial_data.get('balance_sheet')
        if balance_sheet_df is not None and 'Total Debt' in balance_sheet_df.index:
            debt_series = balance_sheet_df.loc['Total Debt'].dropna().sort_index()
            debt_fig = go.Figure(data=[go.Bar(x=debt_series.index, y=debt_series.values, name='Total Debt', marker_color='lightcoral')])
            debt_fig.update_layout(
                title_text=f'Gesamtverschuldung für {ticker_symbol}',
                xaxis_title='Jahr',
                yaxis_title='Schuld (in Mio. $)',
                template='plotly_white',
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis=dict(tickformat=".2s", hoverformat=".2s")
            )
        else:
            debt_fig.update_layout(title=f"Gesamtverschuldung für {ticker_symbol} nicht verfügbar")
        financials_df = financial_data.get('financials')
        if financials_df is not None and 'Total Revenue' in financials_df.index and 'Net Income' in financials_df.index:
            revenue_series = financials_df.loc['Total Revenue'].dropna().sort_index()
            net_income_series = financials_df.loc['Net Income'].dropna().sort_index()
            net_margin_series = (net_income_series / revenue_series * 100).fillna(0)
            revenue_profit_margin_fig = go.Figure()
            revenue_profit_margin_fig.add_trace(go.Bar(x=revenue_series.index, y=revenue_series.values, name='Umsatz', yaxis='y1', marker_color='mediumseagreen'))
            revenue_profit_margin_fig.add_trace(go.Bar(x=net_income_series.index, y=net_income_series.values, name='Gewinn', yaxis='y1', marker_color='darkorange'))
            revenue_profit_margin_fig.add_trace(go.Scatter(
                x=net_margin_series.index,
                y=net_margin_series.values,
                mode='lines+markers',
                name='Nettomarge (%)',
                yaxis='y2',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
            revenue_profit_margin_fig.update_layout(
                title_text=f'Umsatz, Gewinn & Nettomarge für {ticker_symbol}',
                xaxis_title='Jahr',
                yaxis=dict(title='Umsatz/Gewinn (in Mio. $)', tickformat=".2s", hoverformat=".2s", side='left'),
                yaxis2=dict(title='Nettomarge (%)', overlaying='y', side='right', tickformat=".1f", showgrid=False),
                barmode='group',
                template='plotly_white',
                legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)', bordercolor='rgba(0,0,0,0.2)', borderwidth=1),
                margin=dict(l=20, r=20, t=40, b=20)
            )
        else:
            revenue_profit_margin_fig.update_layout(title=f"Umsatz, Gewinn & Nettomarge für {ticker_symbol} nicht verfügbar")
        return fcf_fig, debt_fig, revenue_profit_margin_fig

    @app.callback(
        Output('vix-chart', 'figure'),
        Output('yield-curve-chart', 'figure'),
        Input('yearframe-dropdown', 'value')
    )
    def update_macro_charts(yearframe_duration):
        total_days = yearframe_duration * 365
        macro_end_date = datetime.now()
        macro_start_date = macro_end_date - timedelta(days=total_days)
        vix_fig = go.Figure()
        try:
            vix_data_to_plot = fetch_vix_data(macro_start_date, macro_end_date)
            if not vix_data_to_plot.empty:
                vix_fig = go.Figure(data=[go.Scatter(x=vix_data_to_plot.index, y=vix_data_to_plot.values, mode='lines', name='VIX')])
                vix_fig.update_layout(
                    title_text='VIX (CBOE Volatilitätsindex) - Marktstimmung',
                    xaxis_title='Datum',
                    yaxis_title='VIX Wert',
                    template='plotly_white',
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis=dict(tickformat='%Y-%m-%d', hoverformat='%Y-%m-%d %H:%M:%S')
                )
            else:
                vix_fig.update_layout(title="VIX Daten nicht verfügbar")
        except Exception as e:
            vix_fig.update_layout(title=f"Fehler beim Laden der VIX Daten: {e}")
        yield_curve_fig = go.Figure()
        try:
            yield_data = fetch_yield_curve_data(macro_start_date, macro_end_date, FRED_API_KEY)
            if not yield_data.empty:
                yield_curve_fig.add_trace(go.Scatter(x=yield_data.index, y=yield_data['DGS10'], mode='lines', name='10-jährig (FRED DGS10)'))
                yield_curve_fig.add_trace(go.Scatter(x=yield_data.index, y=yield_data['DGS2'], mode='lines', name='2-jährig (FRED DGS2)'))
                yield_curve_fig.add_trace(go.Scatter(x=yield_data.index, y=yield_data['Spread'], mode='lines', name='Spread (10Y - 2Y)', line=dict(dash='dot', color='grey')))
                yield_curve_fig.update_layout(
                    title_text='US Staatsanleihen-Renditen (2- vs. 10-jährig)',
                    xaxis_title='Datum',
                    yaxis_title='Rendite (%)',
                    template='plotly_white',
                    margin=dict(l=20, r=20, t=40, b=20)
                )
            else:
                yield_curve_fig.update_layout(title="US Staatsanleihen-Renditen Daten nicht verfügbar")
        except Exception as e:
            yield_curve_fig.update_layout(title=f"Fehler beim Laden der Renditen Daten: {e}")
        return vix_fig, yield_curve_fig