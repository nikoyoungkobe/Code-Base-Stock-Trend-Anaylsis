# visualization/dashboard.py
from dash import Dash, dcc, html

def create_app():
    app = Dash(__name__)
    app.layout = html.Div([
        html.H1("Aktienanalyse Dashboard", style={'textAlign': 'center', 'color': '#333'}),
        html.Hr(),
        html.Div([
            html.Label('Füge Ticker für Datenabfrage hinzu', style={'fontSize': '1.2em', 'fontWeight': 'bold'}),
            dcc.Input(id='new-ticker-input', type='text', placeholder="Ticker Symbol(e) eingeben (kommagetrennt)", style={'width': '60%', 'marginRight': '10px', 'padding': '8px'}),
            html.Button('Ticker hinzufügen', id='add-ticker-button', n_clicks=0, style={'padding': '8px 15px', 'backgroundColor': '#4CAF50', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
            html.Div(id='add-ticker-status', style={'marginTop': '10px', 'color': 'blue'}),
            html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
            html.Label("Wähle(n) Sie Ticker aus:", style={'fontSize': '1.2em', 'fontWeight': 'bold'}),
            dcc.Dropdown(id='ticker-dropdown', options=[], multi=True, placeholder="Wählen Sie einen oder mehrere Ticker aus", style={'width': '80%', 'margin': '10px auto'}),
            html.Div([
                dcc.Checklist(id='relative-change-checkbox', options=[{'label': 'Relative Veränderung anzeigen', 'value': 'relative_change'}], value=[]),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginTop': '15px'}),
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e0e0e0', 'borderRadius': '8px', 'marginBottom': '20px'}),
        html.Hr(),
        html.H2("Unternehmens-Finanzkennzahlen", style={'textAlign': 'center', 'color': '#333', 'marginTop': '30px'}),
        html.Div([
            html.Div([html.H3("Free Cash Flow (FCF)", style={'textAlign': 'center', 'marginBottom': '10px'}), dcc.Graph(id='fcf-bar-chart', style={'height': '300px'})], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%'}),
            html.Div([html.H3("Gesamtverschuldung", style={'textAlign': 'center', 'marginBottom': '10px'}), dcc.Graph(id='debt-bar-chart', style={'height': '300px'})], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
        html.Div([
            html.H3("Umsatz, Gewinn & Nettomarge", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='revenue-profit-margin-chart', style={'height': '350px'}),
        ], style={'marginBottom': '20px'}),
        html.Hr(),
        html.H2("Makroökonomische Indikatoren", style={'textAlign': 'center', 'color': '#333', 'marginTop': '30px'}),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='yearframe-dropdown',
                    options=[
                        {"label": "1 Month", "value": 1/12},
                        {"label": "1 Year", "value": 1},
                        {"label": "2 Years", "value": 2},
                        {"label": "5 Years", "value": 5},
                        {"label": "10 Years", "value": 10}],
                    clearable=False,
                    value=5,
                    style={'width': '80%', 'margin': '10px auto'}
                ),
                html.H3("VIX (CBOE Volatilitätsindex) - Marktstimmung", style={'textAlign': 'center', 'marginBottom': '10px'}),
                dcc.Graph(id='vix-chart', style={'height': '350px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%'}),
            html.Div([
                html.H3("US Staatsanleihen-Renditen (2- vs. 10-jährig)", style={'textAlign': 'center', 'marginBottom': '10px'}),
                dcc.Graph(id='yield-curve-chart', style={'height': '350px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
        dcc.Graph(id='stock-price-plot'),
        html.Hr(),
        html.Div(id='plot-info-status', style={'textAlign': 'center', 'fontSize': '1.1em', 'marginTop': '10px', 'color': '#555'})
    ], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1200px', 'margin': 'auto', 'padding': '20px', 'backgroundColor': '#f0f0f0', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
    return app