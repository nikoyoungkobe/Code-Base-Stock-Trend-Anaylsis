# visualization/components/rsi_components.py
"""
Dash UI-Komponenten für RSI Mean-Reversion Backtest.
"""

from dash import dcc, html


def create_rsi_backtest_section():
    """Erstellt den kompletten RSI-Backtest-Bereich."""
    return html.Div([
        html.Hr(),
        html.H2(
            "RSI Mean-Reversion Strategie Backtest",
            style={'textAlign': 'center', 'color': '#333', 'marginTop': '30px'}
        ),
        html.P(
            "Long Entry: RSI < Oversold UND Preis < MA - n*StdDev | "
            "Short Entry: RSI > Overbought UND Preis > MA + n*StdDev",
            style={'textAlign': 'center', 'color': '#666', 'fontSize': '0.9em'}
        ),

        # Parameter-Eingabe
        html.Div([
            html.H3("Strategie-Parameter", style={'marginBottom': '15px'}),

            # Zeile 1: RSI Parameter
            html.Div([
                html.Div([
                    html.Label("RSI Periode", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-period-input',
                        type='number',
                        value=14,
                        min=2,
                        max=50,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("RSI Oversold", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-oversold-input',
                        type='number',
                        value=30,
                        min=10,
                        max=50,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("RSI Overbought", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-overbought-input',
                        type='number',
                        value=70,
                        min=50,
                        max=90,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'marginBottom': '15px'}),

            # Zeile 2: MA und StdDev
            html.Div([
                html.Div([
                    html.Label("MA Periode", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-ma-period-input',
                        type='number',
                        value=20,
                        min=5,
                        max=200,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("StdDev Multiplier", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-stddev-input',
                        type='number',
                        value=1.0,
                        min=0.5,
                        max=3.0,
                        step=0.1,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("Position Typ", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='rsi-position-type',
                        options=[
                            {'label': 'Long & Short', 'value': 'long_short'},
                            {'label': 'Nur Long', 'value': 'long_only'},
                            {'label': 'Nur Short', 'value': 'short_only'},
                        ],
                        value='long_short',
                        clearable=False,
                        style={'width': '100%'}
                    ),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'marginBottom': '15px'}),

            # Zeile 3: TP/SL
            html.Div([
                html.Div([
                    html.Label("Take Profit (%)", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-tp-input',
                        type='number',
                        value=5.0,
                        min=1,
                        max=50,
                        step=0.5,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("Stop Loss (%)", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='rsi-sl-input',
                        type='number',
                        value=2.0,
                        min=0.5,
                        max=20,
                        step=0.5,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Button(
                        'Backtest starten',
                        id='rsi-run-backtest-btn',
                        n_clicks=0,
                        style={
                            'padding': '10px 25px',
                            'backgroundColor': '#4CAF50',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontWeight': 'bold',
                            'marginTop': '20px',
                            'width': '100%'
                        }
                    ),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'marginBottom': '15px'}),

        ], style={
            'backgroundColor': '#e8e8e8',
            'padding': '20px',
            'borderRadius': '8px',
            'marginBottom': '20px'
        }),

        # Ergebnis-Metriken
        html.Div(id='rsi-metrics-container', style={'marginBottom': '20px'}),

        # Charts
        html.Div([
            # Preis + Signale Chart
            html.Div([
                html.H3("Preis, RSI & Signale", style={'textAlign': 'center'}),
                dcc.Graph(id='rsi-signal-chart', style={'height': '400px'})
            ], style={'marginBottom': '20px'}),

            # Cumulative Returns
            html.Div([
                html.H3("Kumulative Rendite", style={'textAlign': 'center'}),
                dcc.Graph(id='rsi-returns-chart', style={'height': '350px'})
            ], style={'marginBottom': '20px'}),
        ]),

        html.Hr(),

        # Parameter-Optimierung
        html.Div([
            html.H3("Parameter-Optimierung", style={'marginBottom': '15px'}),
            html.P(
                "Iteriert durch verschiedene Parameterkombinationen und zeigt die Auswirkungen.",
                style={'color': '#666', 'fontSize': '0.9em'}
            ),

            # Hinweis zu Eingabeformaten
            html.Div([
                html.P(
                    "Eingabeformate: Einzelwerte (10, 20, 30) | Ranges (10-30) | "
                    "Ranges mit Step (10-30:5) | Kombiniert (5, 10-20, 30-50:5)",
                    style={'color': '#888', 'fontSize': '0.85em', 'marginBottom': '10px', 'fontStyle': 'italic'}
                ),
            ]),

            # Optimierungs-Parameter
            html.Div([
                html.Div([
                    html.Label("RSI Perioden", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='opt-rsi-periods',
                        type='text',
                        value='7-21:7',
                        placeholder='z.B. 7-21 oder 7, 14, 21',
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("Take Profits (%)", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='opt-take-profits',
                        type='text',
                        value='2-10:2',
                        placeholder='z.B. 2-10:2 oder 3, 5, 10',
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("Stop Losses (%)", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='opt-stop-losses',
                        type='text',
                        value='1-5',
                        placeholder='z.B. 1-5 oder 1, 2, 3',
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'marginBottom': '15px'}),

            html.Div([
                html.Div([
                    html.Label("MA Perioden", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='opt-ma-periods',
                        type='text',
                        value='10-50:10',
                        placeholder='z.B. 10-50:10 oder 10, 20, 50',
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("StdDev Multiplier", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='opt-stddev-mults',
                        type='text',
                        value='0.5-2.0:0.5',
                        placeholder='z.B. 0.5-2.0:0.5 oder 1.0, 1.5, 2.0',
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'flex': '1', 'marginRight': '15px'}),

                html.Div([
                    html.Label("Optimierungs-Metrik", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='opt-metric-select',
                        options=[
                            {'label': 'Sharpe Ratio', 'value': 'sharpe_ratio'},
                            {'label': 'Total Return', 'value': 'total_return'},
                            {'label': 'Win Rate', 'value': 'win_rate'},
                            {'label': 'Profit Factor', 'value': 'profit_factor'},
                        ],
                        value='sharpe_ratio',
                        clearable=False,
                        style={'width': '100%'}
                    ),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'marginBottom': '15px'}),

            html.Button(
                'Optimierung starten',
                id='rsi-run-optimization-btn',
                n_clicks=0,
                style={
                    'padding': '10px 25px',
                    'backgroundColor': '#2196F3',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '5px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                }
            ),

            html.Div(id='optimization-status', style={'marginTop': '10px', 'color': '#666'}),

        ], style={
            'backgroundColor': '#e8e8e8',
            'padding': '20px',
            'borderRadius': '8px',
            'marginBottom': '20px'
        }),

        # Optimierungs-Ergebnisse
        html.Div([
            # Heatmap
            html.Div([
                html.H3("Performance Heatmap", style={'textAlign': 'center'}),
                html.Div([
                    html.Label("X-Achse:", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='heatmap-x-param',
                        options=[
                            {'label': 'RSI Periode', 'value': 'rsi_period'},
                            {'label': 'MA Periode', 'value': 'ma_period'},
                            {'label': 'Take Profit', 'value': 'take_profit'},
                            {'label': 'Stop Loss', 'value': 'stop_loss'},
                            {'label': 'StdDev Mult', 'value': 'std_dev_mult'},
                        ],
                        value='take_profit',
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block'}
                    ),
                    html.Label("Y-Achse:", style={'marginLeft': '20px', 'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='heatmap-y-param',
                        options=[
                            {'label': 'RSI Periode', 'value': 'rsi_period'},
                            {'label': 'MA Periode', 'value': 'ma_period'},
                            {'label': 'Take Profit', 'value': 'take_profit'},
                            {'label': 'Stop Loss', 'value': 'stop_loss'},
                            {'label': 'StdDev Mult', 'value': 'std_dev_mult'},
                        ],
                        value='stop_loss',
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block'}
                    ),
                ], style={'textAlign': 'center', 'marginBottom': '10px'}),
                dcc.Graph(id='rsi-heatmap-chart', style={'height': '400px'})
            ], style={'marginBottom': '20px'}),

            # Top-N Ergebnisse Tabelle
            html.Div([
                html.H3("Top 10 Parameterkombinationen", style={'textAlign': 'center'}),
                html.Div(id='optimization-results-table'),
            ], style={'marginBottom': '20px'}),

            # Download Button
            html.Div([
                html.Button(
                    'Ergebnisse als CSV speichern',
                    id='download-results-btn',
                    n_clicks=0,
                    style={
                        'padding': '10px 25px',
                        'backgroundColor': '#9C27B0',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'fontWeight': 'bold',
                    }
                ),
                dcc.Download(id='download-csv'),
                html.Div(id='download-status', style={'marginTop': '10px', 'color': '#666'}),
            ], style={'textAlign': 'center'}),

        ], id='optimization-results-container', style={'display': 'none'}),

        # Store für Optimierungsergebnisse
        dcc.Store(id='optimization-results-store'),

    ], style={'marginTop': '20px'})


def create_rsi_metric_card(title: str, value: str, color: str = '#333'):
    """Erstellt eine Metrik-Karte."""
    return html.Div([
        html.Div(title, style={
            'fontSize': '0.85em',
            'color': '#666',
            'marginBottom': '5px'
        }),
        html.Div(value, style={
            'fontSize': '1.3em',
            'fontWeight': 'bold',
            'color': color
        }),
    ], style={
        'backgroundColor': 'white',
        'padding': '15px',
        'borderRadius': '8px',
        'textAlign': 'center',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'minWidth': '120px',
    })
