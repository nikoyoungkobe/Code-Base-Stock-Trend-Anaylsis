# visualization/dashboard.py
"""
Dash Layout für das Stock Dashboard.
Definiert die UI-Struktur und alle visuellen Komponenten.
"""

from dash import Dash, dcc, html


def create_app():
    """
    Erstellt und konfiguriert die Dash-Applikation.
    
    Returns:
        Dash App Instanz mit vollständigem Layout
    """
    app = Dash(__name__)
    
    # Styling-Konstanten
    HEADER_STYLE = {'textAlign': 'center', 'color': '#333'}
    INPUT_SECTION_STYLE = {
        'textAlign': 'center', 
        'padding': '20px', 
        'backgroundColor': '#e0e0e0', 
        'borderRadius': '8px', 
        'marginBottom': '20px'
    }
    CHART_CONTAINER_STYLE = {
        'display': 'flex', 
        'justifyContent': 'space-between', 
        'marginBottom': '20px'
    }
    HALF_WIDTH_STYLE = {
        'width': '48%', 
        'display': 'inline-block', 
        'verticalAlign': 'top'
    }
    
    app.layout = html.Div([
        # =====================================================================
        # HEADER
        # =====================================================================
        html.H1(
            "Aktienanalyse Dashboard", 
            style={'textAlign': 'center', 'color': '#333', 'marginBottom': '5px'}
        ),
        html.P(
            "Stock Trend Analysis & Fundamental Data",
            style={'textAlign': 'center', 'color': '#666', 'marginTop': '0'}
        ),
        html.Hr(),
        
        # =====================================================================
        # TICKER INPUT SECTION
        # =====================================================================
        html.Div([
            html.Label(
                'Füge Ticker für Datenabfrage hinzu', 
                style={'fontSize': '1.2em', 'fontWeight': 'bold'}
            ),
            html.Div([
                dcc.Input(
                    id='new-ticker-input', 
                    type='text', 
                    placeholder="Ticker Symbol(e) eingeben (kommagetrennt, z.B. AAPL, TSLA)", 
                    style={
                        'width': '55%', 
                        'marginRight': '10px', 
                        'padding': '10px',
                        'borderRadius': '5px',
                        'border': '1px solid #ccc'
                    }
                ),
                html.Button(
                    'Ticker hinzufügen', 
                    id='add-ticker-button', 
                    n_clicks=0, 
                    style={
                        'padding': '10px 20px', 
                        'backgroundColor': '#4CAF50', 
                        'color': 'white', 
                        'border': 'none', 
                        'borderRadius': '5px', 
                        'cursor': 'pointer',
                        'fontWeight': 'bold'
                    }
                ),
            ], style={'marginTop': '10px'}),
            
            html.Div(id='add-ticker-status', style={'marginTop': '10px', 'color': 'blue'}),
            
            html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
            
            html.Label(
                "Wähle(n) Sie Ticker aus:", 
                style={'fontSize': '1.2em', 'fontWeight': 'bold'}
            ),
            dcc.Dropdown(
                id='ticker-dropdown', 
                options=[], 
                multi=True, 
                placeholder="Wählen Sie einen oder mehrere Ticker aus", 
                style={'width': '80%', 'margin': '10px auto'}
            ),
            
            html.Div([
                dcc.Checklist(
                    id='relative-change-checkbox', 
                    options=[{'label': ' Relative Veränderung anzeigen (Basis 100)', 'value': 'relative_change'}], 
                    value=[],
                    style={'fontSize': '1em'}
                ),
            ], style={
                'display': 'flex', 
                'alignItems': 'center', 
                'justifyContent': 'center', 
                'marginTop': '15px'
            }),
        ], style=INPUT_SECTION_STYLE),
        
        # =====================================================================
        # MAIN STOCK CHART
        # =====================================================================
        dcc.Graph(id='stock-price-plot', style={'height': '500px'}),
        html.Div(
            id='plot-info-status', 
            style={'textAlign': 'center', 'fontSize': '1em', 'marginTop': '10px', 'color': '#555'}
        ),
        
        html.Hr(),
        
        # =====================================================================
        # FINANCIAL METRICS SECTION
        # =====================================================================
        html.H2(
            "Unternehmens-Finanzkennzahlen", 
            style={'textAlign': 'center', 'color': '#333', 'marginTop': '30px'}
        ),
        html.P(
            "(Daten für den ersten ausgewählten Ticker)",
            style={'textAlign': 'center', 'color': '#888', 'fontSize': '0.9em'}
        ),
        
        # FCF und Debt nebeneinander
        html.Div([
            html.Div([
                html.H3("Free Cash Flow (FCF)", style={'textAlign': 'center', 'marginBottom': '10px'}),
                dcc.Graph(id='fcf-bar-chart', style={'height': '300px'})
            ], style={**HALF_WIDTH_STYLE, 'marginRight': '2%'}),
            
            html.Div([
                html.H3("Gesamtverschuldung", style={'textAlign': 'center', 'marginBottom': '10px'}),
                dcc.Graph(id='debt-bar-chart', style={'height': '300px'})
            ], style=HALF_WIDTH_STYLE),
        ], style=CHART_CONTAINER_STYLE),
        
        # Revenue/Profit Chart
        html.Div([
            html.H3("Umsatz, Gewinn & Nettomarge", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='revenue-profit-margin-chart', style={'height': '400px'}),
        ], style={'marginBottom': '20px'}),
        
        html.Hr(),
        
        # =====================================================================
        # MACRO ECONOMIC INDICATORS SECTION
        # =====================================================================
        html.H2(
            "Makroökonomische Indikatoren", 
            style={'textAlign': 'center', 'color': '#333', 'marginTop': '30px'}
        ),
        
        # Zeitraum-Dropdown
        html.Div([
            html.Label("Zeitraum auswählen:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='yearframe-dropdown',
                options=[
                    {"label": "1 Monat", "value": 1/12},
                    {"label": "3 Monate", "value": 0.25},
                    {"label": "1 Jahr", "value": 1},
                    {"label": "2 Jahre", "value": 2},
                    {"label": "5 Jahre", "value": 5},
                    {"label": "10 Jahre", "value": 10}
                ],
                clearable=False,
                value=5,
                style={'width': '200px', 'display': 'inline-block'}
            ),
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        # VIX und Yield Curve nebeneinander
        html.Div([
            html.Div([
                html.H3(
                    "VIX (Volatilitätsindex) - Marktstimmung", 
                    style={'textAlign': 'center', 'marginBottom': '10px'}
                ),
                dcc.Graph(id='vix-chart', style={'height': '350px'})
            ], style={**HALF_WIDTH_STYLE, 'marginRight': '2%'}),
            
            html.Div([
                html.H3(
                    "US Treasury Yields (2Y vs. 10Y)", 
                    style={'textAlign': 'center', 'marginBottom': '10px'}
                ),
                dcc.Graph(id='yield-curve-chart', style={'height': '350px'})
            ], style=HALF_WIDTH_STYLE),
        ], style=CHART_CONTAINER_STYLE),
        
        # =====================================================================
        # FOOTER
        # =====================================================================
        html.Hr(),
        html.Div([
            html.P(
                "Stock Dashboard | Datenquellen: Yahoo Finance, FRED",
                style={'textAlign': 'center', 'color': '#888', 'fontSize': '0.9em'}
            )
        ], style={'marginTop': '20px', 'paddingBottom': '20px'})
        
    ], style={
        'fontFamily': 'Arial, sans-serif', 
        'maxWidth': '1400px', 
        'margin': 'auto', 
        'padding': '20px', 
        'backgroundColor': '#f5f5f5', 
        'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
    })
    
    return app
