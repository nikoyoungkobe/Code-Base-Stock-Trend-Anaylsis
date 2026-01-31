# data/macro_data.py
"""
Modul zum Abrufen makroökonomischer Daten (VIX, Yield Curve etc.)
"""

import pandas as pd  # BUGFIX: Fehlender Import hinzugefügt
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta


def fetch_vix_data(start_date, end_date):
    """
    Ruft VIX (CBOE Volatility Index) Daten ab.
    
    Args:
        start_date: Startdatum (datetime oder string)
        end_date: Enddatum (datetime oder string)
        
    Returns:
        pandas Series mit VIX Schlusskursen
        
    Raises:
        ValueError: Wenn Daten nicht abgerufen werden können
    """
    try:
        vix_df = yf.download('^VIX', start=start_date, end=end_date, progress=False)
        
        if vix_df.empty:
            raise ValueError("Keine VIX Daten für den angegebenen Zeitraum verfügbar.")
        
        # Handle MultiIndex columns (neuere yfinance Versionen)
        if isinstance(vix_df.columns, pd.MultiIndex):
            if ('Close', '^VIX') in vix_df.columns:
                return vix_df[('Close', '^VIX')].dropna()
            # Fallback für andere MultiIndex-Strukturen
            close_cols = [col for col in vix_df.columns if 'Close' in str(col)]
            if close_cols:
                return vix_df[close_cols[0]].dropna()
        
        # Standard single-level columns
        if 'Close' in vix_df.columns:
            return vix_df['Close'].dropna()
        
        raise ValueError("Weder ('Close', '^VIX') noch 'Close' Spalte im VIX DataFrame gefunden.")
        
    except Exception as e:
        raise ValueError(f"Fehler beim Laden der VIX Daten: {e}")


def fetch_yield_curve_data(start_date, end_date, api_key):
    """
    Ruft US Treasury Yield Daten von FRED ab (2-jährige und 10-jährige Renditen).
    
    Args:
        start_date: Startdatum (datetime oder string)
        end_date: Enddatum (datetime oder string)
        api_key: FRED API Key
        
    Returns:
        DataFrame mit DGS10, DGS2 und Spread Spalten
        
    Raises:
        ValueError: Wenn Daten nicht abgerufen werden können
    """
    try:
        # Abrufen der Treasury Yields von FRED
        yield_data = web.DataReader(
            ['DGS10', 'DGS2'], 
            'fred', 
            start=start_date, 
            end=end_date,
            api_key=api_key
        )
        
        if yield_data.empty:
            raise ValueError("Keine Yield Curve Daten für den angegebenen Zeitraum verfügbar.")
        
        # Spread berechnen (10Y - 2Y)
        # Negativer Spread = invertierte Zinskurve = mögliches Rezessionssignal
        yield_data['Spread'] = yield_data['DGS10'] - yield_data['DGS2']
        
        return yield_data.dropna()
        
    except Exception as e:
        raise ValueError(f"Fehler beim Laden der Renditen Daten von FRED: {e}")


def fetch_fed_funds_rate(start_date, end_date, api_key):
    """
    Ruft den Federal Funds Rate von FRED ab.
    
    Args:
        start_date: Startdatum
        end_date: Enddatum
        api_key: FRED API Key
        
    Returns:
        pandas Series mit Fed Funds Rate
    """
    try:
        fed_data = web.DataReader('FEDFUNDS', 'fred', start=start_date, end=end_date, api_key=api_key)
        return fed_data['FEDFUNDS'].dropna()
    except Exception as e:
        raise ValueError(f"Fehler beim Laden des Fed Funds Rate: {e}")
