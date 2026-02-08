# visualization/dashboard.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dash import Dash, dcc, html
from visualization.components.tsm_components import create_tsm_dashboard_section
from visualization.components.rsi_components import create_rsi_backtest_section
from portfolio.components import create_portfolio_layout


def create_stock_analysis_layout():
    """Erstellt das Layout für den Aktienanalyse-Tab."""
    return html.Div([
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
        html.Div(id='plot-info-status', style={'textAlign': 'center', 'fontSize': '1.1em', 'marginTop': '10px', 'color': '#555'}),

        # TSM Section
        create_tsm_dashboard_section(),

        # RSI Mean-Reversion Backtest Section
        create_rsi_backtest_section(),
    ])


def create_app():
    app = Dash(__name__, suppress_callback_exceptions=True)

    # Tab-Styling
    TAB_STYLE = {
        'padding': '12px 24px',
        'fontWeight': 'bold',
        'backgroundColor': '#f0f0f0',
        'border': '1px solid #ddd',
        'borderBottom': 'none',
        'borderRadius': '8px 8px 0 0',
    }
    TAB_SELECTED_STYLE = {
        **TAB_STYLE,
        'backgroundColor': 'white',
        'borderTop': '3px solid #2962ff',
    }

    app.layout = html.Div([
        html.H1("Aktienanalyse Dashboard", style={'textAlign': 'center', 'color': '#333'}),
        html.P("Stock Trend Analysis & Portfolio Tracking", style={'textAlign': 'center', 'color': '#666', 'marginTop': '0'}),
        html.Hr(),

        # Tabs
        dcc.Tabs(
            id='main-tabs',
            value='stock-analysis-tab',
            children=[
                dcc.Tab(
                    label='Aktienanalyse',
                    value='stock-analysis-tab',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        html.Div([
                            create_stock_analysis_layout(),
                        ], style={'padding': '20px'})
                    ]
                ),
                dcc.Tab(
                    label='Portfolio Tracker',
                    value='portfolio-tab',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=[
                        create_portfolio_layout(),
                    ]
                ),
            ],
            style={'marginBottom': '0'}
        ),

        # Footer
        html.Hr(),
        html.Div([
            html.P("Stock Dashboard | Datenquellen: Yahoo Finance, FRED",
                   style={'textAlign': 'center', 'color': '#888', 'fontSize': '0.9em'})
        ], style={'marginTop': '20px', 'paddingBottom': '20px'})

    ], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1400px', 'margin': 'auto', 'padding': '20px', 'backgroundColor': '#f0f0f0', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})

    return app
