"""
Reusable UI components for TSM dashboard section.
Follows Dash component patterns from existing dashboard.py
"""
from dash import dcc, html


def create_tsm_parameter_controls() -> html.Div:
    """
    Create the parameter control panel for TSM settings.

    Returns:
        html.Div containing parameter controls
    """
    return html.Div([
        html.H3("TSM Parameter", style={'textAlign': 'center', 'marginBottom': '15px'}),

        # Lookback Period
        html.Div([
            html.Label("Lookback-Periode (Monate):", style={'fontWeight': 'bold'}),
            dcc.Slider(
                id='tsm-lookback-slider',
                min=1, max=24, step=1, value=12,
                marks={i: str(i) for i in [1, 3, 6, 12, 18, 24]},
                tooltip={'placement': 'bottom', 'always_visible': True}
            )
        ], style={'marginBottom': '20px'}),

        # Holding Period
        html.Div([
            html.Label("Halteperiode:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='tsm-holding-dropdown',
                options=[
                    {'label': 'Täglich (1 Tag)', 'value': 1},
                    {'label': 'Wöchentlich (5 Tage)', 'value': 5},
                    {'label': 'Monatlich (21 Tage)', 'value': 21},
                    {'label': 'Quartal (63 Tage)', 'value': 63}
                ],
                value=21,
                clearable=False
            )
        ], style={'marginBottom': '20px'}),

        # Volatility Scaling
        html.Div([
            html.Label("Volatilitätsskalierung:", style={'fontWeight': 'bold'}),
            dcc.Checklist(
                id='tsm-vol-scaling-check',
                options=[{'label': ' Aktivieren', 'value': 'enabled'}],
                value=['enabled']
            ),
            html.Div([
                html.Label("Ziel-Volatilität (%):", style={'marginLeft': '20px'}),
                dcc.Input(
                    id='tsm-vol-target-input',
                    type='number',
                    value=10, min=1, max=50, step=1,
                    style={'width': '80px', 'marginLeft': '10px'}
                )
            ], id='tsm-vol-target-container', style={'marginTop': '5px'})
        ], style={'marginBottom': '20px'}),

        # Position Type
        html.Div([
            html.Label("Positionstyp:", style={'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='tsm-position-type',
                options=[
                    {'label': ' Long/Cash (nur Long)', 'value': 'long_cash'},
                    {'label': ' Long/Short (beidseitig)', 'value': 'long_short'}
                ],
                value='long_cash',
                inline=False,
                style={'marginTop': '5px'}
            )
        ])
    ], style={
        'backgroundColor': '#f9f9f9',
        'padding': '20px',
        'borderRadius': '8px',
        'border': '1px solid #ddd',
        'height': '100%'
    })


def create_tsm_signal_chart_container() -> html.Div:
    """
    Create container for the momentum signal visualization chart.
    """
    return html.Div([
        html.H3("Momentum-Signal Zeitreihe", style={'textAlign': 'center'}),
        dcc.Graph(id='tsm-signal-chart', style={'height': '400px'})
    ])


def create_tsm_returns_chart_container() -> html.Div:
    """
    Create container for cumulative returns comparison chart.
    """
    return html.Div([
        html.H3("Kumulative Renditen: Strategie vs. Buy-and-Hold", style={'textAlign': 'center'}),
        dcc.Graph(id='tsm-returns-chart', style={'height': '400px'})
    ])


def create_metric_card(label: str, value: str, color: str = '#333') -> html.Div:
    """
    Create a single metric display card.
    """
    return html.Div([
        html.P(label, style={'margin': '0', 'fontSize': '0.85em', 'color': '#666'}),
        html.P(value, style={'margin': '0', 'fontSize': '1.3em', 'fontWeight': 'bold', 'color': color})
    ], style={
        'display': 'inline-block',
        'width': '120px',
        'textAlign': 'center',
        'padding': '10px',
        'margin': '5px',
        'backgroundColor': 'white',
        'borderRadius': '5px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    })


def create_tsm_metrics_panel() -> html.Div:
    """
    Create the performance metrics display panel.
    """
    return html.Div([
        html.H3("Performance-Kennzahlen", style={'textAlign': 'center'}),
        html.Div(id='tsm-metrics-container', children=[
            # Will be populated by callback with metric cards
            html.P("Wählen Sie einen Ticker aus, um die Analyse zu starten.",
                   style={'textAlign': 'center', 'color': '#666'})
        ], style={'textAlign': 'center'})
    ], style={
        'backgroundColor': '#f5f5f5',
        'padding': '15px',
        'borderRadius': '8px'
    })


def create_scenario_comparison_section() -> html.Div:
    """
    Create the scenario comparison section for parameter optimization.
    """
    return html.Div([
        html.H3("Szenario-Vergleich", style={'textAlign': 'center'}),

        # Scenario save controls
        html.Div([
            dcc.Input(
                id='tsm-scenario-name-input',
                type='text',
                placeholder='Szenario-Name eingeben',
                style={'width': '200px', 'marginRight': '10px', 'padding': '8px'}
            ),
            html.Button(
                'Szenario speichern',
                id='tsm-save-scenario-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 15px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                }
            ),
            html.Button(
                'Alle löschen',
                id='tsm-clear-scenarios-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#f44336',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 15px',
                    'borderRadius': '5px',
                    'cursor': 'pointer',
                    'marginLeft': '10px'
                }
            )
        ], style={'textAlign': 'center', 'marginBottom': '15px'}),

        # Comparison table container
        html.Div(id='tsm-scenario-table-container', children=[
            html.P("Noch keine Szenarien gespeichert.",
                   style={'textAlign': 'center', 'color': '#666', 'fontStyle': 'italic'})
        ]),

        # Store for scenario data (client-side)
        dcc.Store(id='tsm-scenarios-store', data={})
    ])


def create_tsm_dashboard_section() -> html.Div:
    """
    Create the complete TSM dashboard section.
    Assembles all TSM components into a cohesive layout.
    """
    return html.Div([
        html.Hr(style={'marginTop': '30px', 'marginBottom': '20px'}),
        html.H2(
            "Time Series Momentum (TSM) Strategie",
            style={'textAlign': 'center', 'color': '#333', 'marginBottom': '20px'}
        ),

        # Row 1: Parameters (left) and Signal Chart (right)
        html.Div([
            html.Div([
                create_tsm_parameter_controls()
            ], style={'width': '28%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px'}),

            html.Div([
                create_tsm_signal_chart_container()
            ], style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'display': 'flex', 'marginBottom': '20px'}),

        # Row 2: Cumulative Returns Chart
        html.Div([
            create_tsm_returns_chart_container()
        ], style={'marginBottom': '20px'}),

        # Row 3: Metrics Panel
        html.Div([
            create_tsm_metrics_panel()
        ], style={'marginBottom': '20px'}),

        # Row 4: Scenario Comparison
        html.Div([
            create_scenario_comparison_section()
        ])
    ], id='tsm-section', style={'padding': '0 20px'})
