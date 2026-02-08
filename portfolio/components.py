# portfolio/components.py
"""
Dash UI-Komponenten für den Portfolio Tracker im TradingView-Stil.
"""

from dash import dcc, html


# =============================================================================
# Styling Konstanten
# =============================================================================

CARD_STYLE = {
    'backgroundColor': '#1e222d',
    'borderRadius': '8px',
    'padding': '15px',
    'color': '#d1d4dc',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.3)',
}

CARD_HEADER_STYLE = {
    'fontSize': '0.85em',
    'color': '#787b86',
    'marginBottom': '5px',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px',
}

CARD_VALUE_STYLE = {
    'fontSize': '1.5em',
    'fontWeight': 'bold',
    'color': '#d1d4dc',
}

POSITIVE_COLOR = '#26a69a'
NEGATIVE_COLOR = '#ef5350'
NEUTRAL_COLOR = '#787b86'

BUTTON_STYLE = {
    'backgroundColor': '#2962ff',
    'color': 'white',
    'border': 'none',
    'borderRadius': '4px',
    'padding': '8px 16px',
    'cursor': 'pointer',
    'fontWeight': 'bold',
    'marginRight': '8px',
}

BUTTON_DANGER_STYLE = {
    **BUTTON_STYLE,
    'backgroundColor': '#ef5350',
}

INPUT_STYLE = {
    'backgroundColor': '#2a2e39',
    'border': '1px solid #363a45',
    'borderRadius': '4px',
    'color': '#d1d4dc',
    'padding': '8px 12px',
    'width': '100%',
}


def create_portfolio_header():
    """Erstellt den Header mit Portfolio-Auswahl und Buttons."""
    return html.Div([
        html.Div([
            html.Div([
                html.Label(
                    'Portfolio auswählen',
                    style={'color': '#787b86', 'fontSize': '0.9em', 'marginBottom': '5px'}
                ),
                dcc.Dropdown(
                    id='portfolio-dropdown',
                    options=[],
                    value=None,
                    placeholder='Portfolio wählen...',
                    style={'width': '300px'},
                ),
            ], style={'flex': '1'}),

            html.Div([
                html.Button(
                    'Neues Portfolio',
                    id='create-portfolio-btn',
                    n_clicks=0,
                    style=BUTTON_STYLE
                ),
                html.Button(
                    'Löschen',
                    id='delete-portfolio-btn',
                    n_clicks=0,
                    style=BUTTON_DANGER_STYLE
                ),
            ], style={'display': 'flex', 'alignItems': 'flex-end', 'gap': '8px'}),
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'flex-end',
            'padding': '20px',
            'backgroundColor': '#131722',
            'borderRadius': '8px',
            'marginBottom': '20px',
        }),

        # Modal für neues Portfolio
        html.Div([
            html.Div([
                html.H3('Neues Portfolio erstellen', style={'color': '#d1d4dc', 'marginBottom': '20px'}),
                html.Div([
                    html.Label('Portfolio Name', style={'color': '#787b86', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='new-portfolio-name',
                        type='text',
                        placeholder='z.B. Mein Hauptportfolio',
                        style={**INPUT_STYLE, 'marginBottom': '15px'}
                    ),
                ]),
                html.Div([
                    html.Label('Benchmark', style={'color': '#787b86', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id='new-portfolio-benchmark',
                        options=[
                            {'label': 'S&P 500 (^GSPC)', 'value': '^GSPC'},
                            {'label': 'NASDAQ 100 (^NDX)', 'value': '^NDX'},
                            {'label': 'DAX (^GDAXI)', 'value': '^GDAXI'},
                            {'label': 'Dow Jones (^DJI)', 'value': '^DJI'},
                        ],
                        value='^GSPC',
                        style={'marginBottom': '20px'},
                    ),
                ]),
                html.Div([
                    html.Button(
                        'Erstellen',
                        id='confirm-create-portfolio-btn',
                        n_clicks=0,
                        style=BUTTON_STYLE
                    ),
                    html.Button(
                        'Abbrechen',
                        id='cancel-create-portfolio-btn',
                        n_clicks=0,
                        style={**BUTTON_STYLE, 'backgroundColor': '#363a45'}
                    ),
                ], style={'display': 'flex', 'gap': '10px'}),
            ], style={
                **CARD_STYLE,
                'width': '400px',
                'position': 'relative',
            }),
        ], id='create-portfolio-modal', style={
            'display': 'none',
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.7)',
            'zIndex': '1000',
            'justifyContent': 'center',
            'alignItems': 'center',
        }),

        html.Div(id='portfolio-status-message', style={'marginBottom': '10px'}),
    ])


def create_summary_cards():
    """Erstellt die Summary Cards."""
    return html.Div([
        html.Div([
            html.Div('Gesamtwert', style=CARD_HEADER_STYLE),
            html.Div(id='summary-total-value', children='$0.00', style=CARD_VALUE_STYLE),
        ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Div('Gewinn/Verlust', style=CARD_HEADER_STYLE),
            html.Div(id='summary-total-pnl', children='$0.00', style=CARD_VALUE_STYLE),
            html.Div(id='summary-total-pnl-percent', children='0.00%', style={'fontSize': '0.9em'}),
        ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Div('Tagesänderung', style=CARD_HEADER_STYLE),
            html.Div(id='summary-daily-change', children='$0.00', style=CARD_VALUE_STYLE),
            html.Div(id='summary-daily-change-percent', children='0.00%', style={'fontSize': '0.9em'}),
        ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '200px'}),

        html.Div([
            html.Div('Positionen', style=CARD_HEADER_STYLE),
            html.Div(id='summary-positions-count', children='0', style=CARD_VALUE_STYLE),
        ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '150px'}),

    ], style={
        'display': 'flex',
        'gap': '15px',
        'marginBottom': '20px',
        'flexWrap': 'wrap',
    })


def create_add_holding_form():
    """Erstellt das Formular zum Hinzufügen von Positionen."""
    return html.Div([
        html.H3('Position hinzufügen', style={'color': '#d1d4dc', 'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.Label('Ticker', style={'color': '#787b86', 'fontSize': '0.9em'}),
                dcc.Input(
                    id='add-holding-ticker',
                    type='text',
                    placeholder='z.B. AAPL',
                    style=INPUT_STYLE
                ),
            ], style={'flex': '1', 'minWidth': '100px'}),

            html.Div([
                html.Label('Anzahl', style={'color': '#787b86', 'fontSize': '0.9em'}),
                dcc.Input(
                    id='add-holding-quantity',
                    type='number',
                    placeholder='10',
                    min=0,
                    step=0.01,
                    style=INPUT_STYLE
                ),
            ], style={'flex': '1', 'minWidth': '100px'}),

            html.Div([
                html.Label('Kaufpreis ($)', style={'color': '#787b86', 'fontSize': '0.9em'}),
                dcc.Input(
                    id='add-holding-price',
                    type='number',
                    placeholder='150.00',
                    min=0,
                    step=0.01,
                    style=INPUT_STYLE
                ),
            ], style={'flex': '1', 'minWidth': '120px'}),

            html.Div([
                html.Label('Kaufdatum', style={'color': '#787b86', 'fontSize': '0.9em'}),
                dcc.DatePickerSingle(
                    id='add-holding-date',
                    placeholder='Datum wählen',
                    display_format='YYYY-MM-DD',
                    style={'width': '100%'},
                ),
            ], style={'flex': '1', 'minWidth': '150px'}),

            html.Div([
                html.Button(
                    'Hinzufügen',
                    id='add-holding-btn',
                    n_clicks=0,
                    style={**BUTTON_STYLE, 'marginTop': '20px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'flex-end'}),

        ], style={
            'display': 'flex',
            'gap': '15px',
            'flexWrap': 'wrap',
            'alignItems': 'flex-end',
        }),

        html.Div(id='add-holding-status', style={'marginTop': '10px', 'color': '#787b86'}),

    ], style={
        **CARD_STYLE,
        'marginBottom': '20px',
    })


def create_holdings_table():
    """Erstellt die Holdings-Tabelle."""
    return html.Div([
        html.H3('Positionen', style={'color': '#d1d4dc', 'marginBottom': '15px'}),
        html.Div(
            id='holdings-table-container',
            children=[
                html.P(
                    'Keine Positionen vorhanden. Fügen Sie eine Position hinzu.',
                    style={'color': '#787b86', 'textAlign': 'center', 'padding': '20px'}
                )
            ],
        ),
    ], style={
        **CARD_STYLE,
        'marginBottom': '20px',
    })


def create_charts_section():
    """Erstellt den Bereich mit allen Charts."""
    return html.Div([
        html.Div([
            html.Div([
                html.H3('Allokation', style={'color': '#d1d4dc', 'marginBottom': '10px'}),
                dcc.Graph(
                    id='allocation-pie-chart',
                    config={'displayModeBar': False},
                    style={'height': '300px'}
                ),
            ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '300px'}),

            html.Div([
                html.H3('Portfolio-Wert', style={'color': '#d1d4dc', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='portfolio-value-period',
                    options=[
                        {'label': '1 Monat', 'value': '1mo'},
                        {'label': '3 Monate', 'value': '3mo'},
                        {'label': '6 Monate', 'value': '6mo'},
                        {'label': '1 Jahr', 'value': '1y'},
                        {'label': '2 Jahre', 'value': '2y'},
                    ],
                    value='1y',
                    style={'width': '150px', 'marginBottom': '10px'},
                    clearable=False,
                ),
                dcc.Graph(
                    id='portfolio-value-chart',
                    config={'displayModeBar': False},
                    style={'height': '280px'}
                ),
            ], style={**CARD_STYLE, 'flex': '2', 'minWidth': '400px'}),
        ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px', 'flexWrap': 'wrap'}),

        html.Div([
            html.Div([
                html.H3('Benchmark-Vergleich', style={'color': '#d1d4dc', 'marginBottom': '10px'}),
                dcc.Graph(
                    id='benchmark-comparison-chart',
                    config={'displayModeBar': False},
                    style={'height': '300px'}
                ),
            ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '400px'}),

            html.Div([
                html.H3('Performance nach Position', style={'color': '#d1d4dc', 'marginBottom': '10px'}),
                dcc.Graph(
                    id='position-performance-chart',
                    config={'displayModeBar': False},
                    style={'height': '300px'}
                ),
            ], style={**CARD_STYLE, 'flex': '1', 'minWidth': '400px'}),
        ], style={'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap'}),
    ])


def create_portfolio_layout():
    """Erstellt das komplette Portfolio-Layout."""
    return html.Div([
        dcc.Interval(
            id='portfolio-refresh-interval',
            interval=60000,
            n_intervals=0,
        ),

        dcc.Store(id='portfolio-data-store'),

        create_portfolio_header(),
        create_summary_cards(),
        create_add_holding_form(),
        create_holdings_table(),
        create_charts_section(),

    ], style={
        'backgroundColor': '#0f1117',
        'padding': '20px',
        'minHeight': '100vh',
    })
