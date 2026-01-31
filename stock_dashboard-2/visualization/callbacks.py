# visualization/callbacks.py
"""
Dash Callbacks für das Stock Dashboard.
Verarbeitet User-Interaktionen und aktualisiert die Visualisierungen.
"""

from dash import html  # BUGFIX: Fehlender Import hinzugefügt
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta

from stock_dashboard.data.fetch_data import GetClosingPrices
from stock_dashboard.data.macro_data import fetch_vix_data, fetch_yield_curve_data
from stock_dashboard.config.settings import FRED_API_KEY


def register_callbacks(app, stock_manager):
    """
    Registriert alle Dash Callbacks für die App.
    
    Args:
        app: Die Dash App Instanz
        stock_manager: GetClosingPrices Instanz für Datenzugriff
    """
    
    # =========================================================================
    # CALLBACK 1: Ticker hinzufügen
    # =========================================================================
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
        """Fügt neue Ticker zur Auswahl hinzu und lädt deren Daten."""
        
        # Initial load oder kein Klick
        if n_clicks is None or n_clicks == 0:
            return current_options, current_selected_values, ""
        
        # Keine Eingabe
        if not new_tickers_input:
            return current_options, current_selected_values, "Bitte geben Sie Ticker Symbole ein."
        
        # Ticker parsen und normalisieren
        new_tickers_list = [t.strip().upper() for t in new_tickers_input.split(',') if t.strip()]
        existing_tickers = [option['value'] for option in current_options] if current_options else []
        tickers_to_add = [t for t in new_tickers_list if t not in existing_tickers]
        
        if not tickers_to_add:
            return current_options, current_selected_values, "Alle eingegebenen Ticker sind bereits vorhanden."
        
        # Neue Ticker zur Liste hinzufügen
        for ticker in tickers_to_add:
            if ticker not in stock_manager.ticker_list:
                stock_manager.ticker_list.append(ticker)
        
        # Daten für neue Ticker abrufen (3 Jahre historisch)
        original_start_date = stock_manager.start_date
        original_end_date = stock_manager.end_date
        stock_manager.start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
        stock_manager.end_date = datetime.now().strftime('%Y-%m-%d')
        stock_manager.fetch_historical_data()
        stock_manager.start_date = original_start_date
        stock_manager.end_date = original_end_date
        
        # Verfügbare Ticker aktualisieren
        updated_available_tickers = stock_manager.get_available_tickers()
        new_options = [{'label': ticker, 'value': ticker} for ticker in updated_available_tickers]
        
        # Neue Ticker automatisch auswählen
        updated_selected_values = current_selected_values if current_selected_values else []
        for ticker in tickers_to_add:
            if ticker in updated_available_tickers and ticker not in updated_selected_values:
                updated_selected_values.append(ticker)
        
        # Status-Nachricht erstellen
        status_message = f"Ticker {', '.join(tickers_to_add)} hinzugefügt."
        failed_tickers = [t for t in tickers_to_add if t not in updated_available_tickers]
        if failed_tickers:
            status_message += f" (Hinweis: Daten konnten für {', '.join(failed_tickers)} nicht abgerufen werden.)"
        
        return new_options, updated_selected_values, status_message

    # =========================================================================
    # CALLBACK 2: Aktienkurs-Chart aktualisieren
    # =========================================================================
    @app.callback(
        Output('stock-price-plot', 'figure'),
        Output('plot-info-status', 'children'),
        Input('ticker-dropdown', 'value'),
        Input('relative-change-checkbox', 'value')
    )
    def update_graph(selected_tickers, relative_change_values):
        """Aktualisiert den Hauptchart mit Aktienkursen."""
        
        relative_change_active = relative_change_values and 'relative_change' in relative_change_values
        
        if not selected_tickers:
            return go.Figure(), "Bitte wählen Sie mindestens einen Ticker aus."
        
        if not isinstance(selected_tickers, list):
            selected_tickers = [selected_tickers]
        
        fig = go.Figure()
        plot_info_messages = []
        
        # Chart-Titel basierend auf Modus
        if relative_change_active:
            plot_title = 'Relative Veränderung der Schlusskurse (Basis = 100)'
            y_axis_label = 'Relative Veränderung (Index 100)'
        else:
            plot_title = 'Historische Schlusskurse'
            y_axis_label = 'Schlusskurs ($)'
        
        # Daten für jeden Ticker plotten
        for ticker_symbol in selected_tickers:
            df = stock_manager.get_data_for_ticker(ticker_symbol)
            
            if df is None or df.empty:
                plot_info_messages.append(f"Keine Daten für {ticker_symbol} verfügbar.")
                continue
            
            if 'Close' not in df.columns:
                plot_info_messages.append(f"Fehler: 'Close'-Spalte nicht gefunden für {ticker_symbol}.")
                continue
            
            data_to_plot = df['Close']
            
            # Relative Veränderung berechnen
            if relative_change_active:
                first_value = data_to_plot.iloc[0]
                if first_value != 0:
                    data_to_plot = (data_to_plot / first_value) * 100
                else:
                    plot_info_messages.append(f"Warnung: Erster Schlusskurs für {ticker_symbol} ist Null.")
                    continue
            
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=data_to_plot, 
                mode='lines', 
                name=ticker_symbol
            ))
        
        # Leerer Chart wenn keine Daten
        if not fig.data:
            fig.update_layout(
                title='Keine Daten zum Plotten verfügbar',
                xaxis_title='Datum',
                yaxis_title=y_axis_label
            )
            return fig, html.Div(plot_info_messages)
        
        # Chart formatieren
        fig.update_layout(
            title=plot_title,
            xaxis_title='Datum',
            yaxis_title=y_axis_label,
            hovermode="x unified",
            template='plotly_white',
            xaxis_rangeslider_visible=True
        )
        
        # Status-Text erstellen
        plotted_tickers = [t for t in selected_tickers 
                          if t in stock_manager.historical_data 
                          and not stock_manager.historical_data[t].empty]
        
        status_text = html.Div([
            html.P(f"Plot zeigt Daten für: {', '.join(plotted_tickers)}"),
            html.P(
                "Hinweise: " + "; ".join(plot_info_messages), 
                style={'color': 'orange', 'fontWeight': 'bold'}
            ) if plot_info_messages else ""
        ])
        
        return fig, status_text

    # =========================================================================
    # CALLBACK 3: Finanzkennzahlen-Charts aktualisieren
    # =========================================================================
    @app.callback(
        Output('fcf-bar-chart', 'figure'),
        Output('debt-bar-chart', 'figure'),
        Output('revenue-profit-margin-chart', 'figure'),
        Input('ticker-dropdown', 'value')
    )
    def update_financial_charts(selected_tickers):
        """Aktualisiert die Finanzkennzahlen-Charts (FCF, Debt, Revenue/Profit)."""
        
        empty_fig = go.Figure()
        
        if not selected_tickers:
            empty_fig.update_layout(title="Wählen Sie einen Ticker für Finanzdaten aus.")
            return empty_fig, empty_fig, empty_fig
        
        # Nur ersten Ticker für Finanzdaten verwenden
        ticker_symbol = selected_tickers[0] if isinstance(selected_tickers, list) else selected_tickers
        financial_data = stock_manager.get_financial_data_for_ticker(ticker_symbol)
        
        fcf_fig = go.Figure()
        debt_fig = go.Figure()
        revenue_profit_margin_fig = go.Figure()
        
        if not financial_data:
            no_data_msg = f"Keine Finanzdaten für {ticker_symbol} verfügbar"
            fcf_fig.update_layout(title=no_data_msg)
            debt_fig.update_layout(title=no_data_msg)
            revenue_profit_margin_fig.update_layout(title=no_data_msg)
            return fcf_fig, debt_fig, revenue_profit_margin_fig
        
        # --- FCF Chart ---
        cashflow_df = financial_data.get('cashflow')
        if cashflow_df is not None and 'Free Cash Flow' in cashflow_df.index:
            fcf_series = cashflow_df.loc['Free Cash Flow'].dropna().sort_index()
            fcf_fig = go.Figure(data=[
                go.Bar(
                    x=fcf_series.index, 
                    y=fcf_series.values, 
                    name='Free Cash Flow', 
                    marker_color='skyblue'
                )
            ])
            fcf_fig.update_layout(
                title_text=f'Free Cash Flow für {ticker_symbol}',
                xaxis_title='Jahr',
                yaxis_title='FCF (in $)',
                template='plotly_white',
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis=dict(tickformat=".2s", hoverformat=".2s")
            )
        else:
            fcf_fig.update_layout(title=f"Free Cash Flow für {ticker_symbol} nicht verfügbar")
        
        # --- Debt Chart ---
        balance_sheet_df = financial_data.get('balance_sheet')
        if balance_sheet_df is not None and 'Total Debt' in balance_sheet_df.index:
            debt_series = balance_sheet_df.loc['Total Debt'].dropna().sort_index()
            debt_fig = go.Figure(data=[
                go.Bar(
                    x=debt_series.index, 
                    y=debt_series.values, 
                    name='Total Debt', 
                    marker_color='lightcoral'
                )
            ])
            debt_fig.update_layout(
                title_text=f'Gesamtverschuldung für {ticker_symbol}',
                xaxis_title='Jahr',
                yaxis_title='Schuld (in $)',
                template='plotly_white',
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis=dict(tickformat=".2s", hoverformat=".2s")
            )
        else:
            debt_fig.update_layout(title=f"Gesamtverschuldung für {ticker_symbol} nicht verfügbar")
        
        # --- Revenue/Profit/Margin Chart ---
        financials_df = financial_data.get('financials')
        if (financials_df is not None 
            and 'Total Revenue' in financials_df.index 
            and 'Net Income' in financials_df.index):
            
            revenue_series = financials_df.loc['Total Revenue'].dropna().sort_index()
            net_income_series = financials_df.loc['Net Income'].dropna().sort_index()
            net_margin_series = (net_income_series / revenue_series * 100).fillna(0)
            
            revenue_profit_margin_fig = go.Figure()
            
            # Umsatz Balken
            revenue_profit_margin_fig.add_trace(go.Bar(
                x=revenue_series.index, 
                y=revenue_series.values, 
                name='Umsatz', 
                yaxis='y1', 
                marker_color='mediumseagreen'
            ))
            
            # Gewinn Balken
            revenue_profit_margin_fig.add_trace(go.Bar(
                x=net_income_series.index, 
                y=net_income_series.values, 
                name='Gewinn', 
                yaxis='y1', 
                marker_color='darkorange'
            ))
            
            # Nettomarge Linie
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
                yaxis=dict(
                    title='Umsatz/Gewinn (in $)', 
                    tickformat=".2s", 
                    hoverformat=".2s", 
                    side='left'
                ),
                yaxis2=dict(
                    title='Nettomarge (%)', 
                    overlaying='y', 
                    side='right', 
                    tickformat=".1f", 
                    showgrid=False
                ),
                barmode='group',
                template='plotly_white',
                legend=dict(
                    x=0.01, y=0.99, 
                    bgcolor='rgba(255,255,255,0.8)', 
                    bordercolor='rgba(0,0,0,0.2)', 
                    borderwidth=1
                ),
                margin=dict(l=20, r=20, t=40, b=20)
            )
        else:
            revenue_profit_margin_fig.update_layout(
                title=f"Umsatz, Gewinn & Nettomarge für {ticker_symbol} nicht verfügbar"
            )
        
        return fcf_fig, debt_fig, revenue_profit_margin_fig

    # =========================================================================
    # CALLBACK 4: Makroökonomische Charts aktualisieren
    # =========================================================================
    @app.callback(
        Output('vix-chart', 'figure'),
        Output('yield-curve-chart', 'figure'),
        Input('yearframe-dropdown', 'value')
    )
    def update_macro_charts(yearframe_duration):
        """Aktualisiert die makroökonomischen Charts (VIX, Yield Curve)."""
        
        # Zeitraum berechnen
        total_days = int(yearframe_duration * 365)
        macro_end_date = datetime.now()
        macro_start_date = macro_end_date - timedelta(days=total_days)
        
        # --- VIX Chart ---
        vix_fig = go.Figure()
        try:
            vix_data = fetch_vix_data(macro_start_date, macro_end_date)
            if not vix_data.empty:
                vix_fig = go.Figure(data=[
                    go.Scatter(
                        x=vix_data.index, 
                        y=vix_data.values, 
                        mode='lines', 
                        name='VIX',
                        line=dict(color='purple')
                    )
                ])
                vix_fig.update_layout(
                    title_text='VIX (CBOE Volatilitätsindex) - Marktstimmung',
                    xaxis_title='Datum',
                    yaxis_title='VIX Wert',
                    template='plotly_white',
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis=dict(tickformat='%Y-%m-%d')
                )
                
                # Referenzlinien für VIX-Levels
                vix_fig.add_hline(y=20, line_dash="dash", line_color="green", 
                                  annotation_text="Niedrige Volatilität")
                vix_fig.add_hline(y=30, line_dash="dash", line_color="orange", 
                                  annotation_text="Erhöhte Volatilität")
            else:
                vix_fig.update_layout(title="VIX Daten nicht verfügbar")
        except Exception as e:
            vix_fig.update_layout(title=f"Fehler beim Laden der VIX Daten: {e}")
        
        # --- Yield Curve Chart ---
        yield_curve_fig = go.Figure()
        try:
            yield_data = fetch_yield_curve_data(macro_start_date, macro_end_date, FRED_API_KEY)
            if not yield_data.empty:
                # 10-jährige Rendite
                yield_curve_fig.add_trace(go.Scatter(
                    x=yield_data.index, 
                    y=yield_data['DGS10'], 
                    mode='lines', 
                    name='10-jährig (DGS10)',
                    line=dict(color='blue')
                ))
                
                # 2-jährige Rendite
                yield_curve_fig.add_trace(go.Scatter(
                    x=yield_data.index, 
                    y=yield_data['DGS2'], 
                    mode='lines', 
                    name='2-jährig (DGS2)',
                    line=dict(color='red')
                ))
                
                # Spread (10Y - 2Y)
                yield_curve_fig.add_trace(go.Scatter(
                    x=yield_data.index, 
                    y=yield_data['Spread'], 
                    mode='lines', 
                    name='Spread (10Y - 2Y)', 
                    line=dict(dash='dot', color='grey')
                ))
                
                # Nulllinie für Spread (invertierte Zinskurve)
                yield_curve_fig.add_hline(y=0, line_dash="dash", line_color="black", 
                                          annotation_text="Inversions-Schwelle")
                
                yield_curve_fig.update_layout(
                    title_text='US Staatsanleihen-Renditen (2- vs. 10-jährig)',
                    xaxis_title='Datum',
                    yaxis_title='Rendite (%)',
                    template='plotly_white',
                    margin=dict(l=20, r=20, t=40, b=20)
                )
            else:
                yield_curve_fig.update_layout(title="US Staatsanleihen-Renditen nicht verfügbar")
        except Exception as e:
            yield_curve_fig.update_layout(title=f"Fehler beim Laden der Renditen: {e}")
        
        return vix_fig, yield_curve_fig
