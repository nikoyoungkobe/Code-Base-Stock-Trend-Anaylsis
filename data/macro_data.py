# data/macro_data.py
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta

def fetch_vix_data(start_date, end_date):
    try:
        vix_df = yf.download('^VIX', start=start_date, end=end_date, progress=False)
        if isinstance(vix_df.columns, pd.MultiIndex) and ('Close', '^VIX') in vix_df.columns:
            return vix_df[('Close', '^VIX')].dropna()
        elif 'Close' in vix_df.columns:
            return vix_df['Close'].dropna()
        raise ValueError("Weder ('Close', '^VIX') noch 'Close' Spalte im VIX DataFrame gefunden.")
    except Exception as e:
        raise ValueError(f"Fehler beim Laden der VIX Daten: {e}")

def fetch_yield_curve_data(start_date, end_date, api_key):
    try:
        yield_data = web.DataReader(['DGS10', 'DGS2'], 'fred', start=start_date, end=end_date, api_key=api_key)
        yield_data['Spread'] = yield_data['DGS10'] - yield_data['DGS2']
        return yield_data.dropna()
    except Exception as e:
        raise ValueError(f"Fehler beim Laden der Renditen Daten von FRED: {e}")