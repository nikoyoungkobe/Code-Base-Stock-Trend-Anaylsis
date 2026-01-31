# strategies/sma_letf_strategy.py
"""
SMA 200 LETF Trendfolgestrategie (nach ZahlGraf)

Prinzip:
- Signalgeber: Basis-Index (z.B. S&P 500)
- Handelsobjekt: Gehebelter ETF (LETF)
- Risk-On: Kurs > SMA 200 → Halte LETF
- Risk-Off: Kurs < SMA 200 → Verkaufe LETF, halte Cash
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class StrategyConfig:
    """Konfiguration für die SMA LETF Strategie."""
    signal_ticker: str = "^GSPC"      # Signalgeber (S&P 500)
    trade_ticker: str = "UPRO"         # Handelsobjekt (3x S&P 500 LETF)
    sma_period: int = 200              # SMA Periode in Tagen
    initial_capital: float = 10000.0   # Startkapital
    risk_free_rate: float = 0.02       # Risikofreier Zins für Cash (2% p.a.)
    start_date: str = "2010-01-01"     # Backtest Start
    end_date: str = None               # Backtest Ende (None = heute)


class SMALETFStrategy:
    """
    Implementierung der SMA 200 LETF Trendfolgestrategie.
    """
    
    def __init__(self, config: StrategyConfig = None):
        """
        Initialisiert die Strategie.
        
        Args:
            config: StrategyConfig Objekt mit Einstellungen
        """
        self.config = config or StrategyConfig()
        if self.config.end_date is None:
            self.config.end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.signal_data = None
        self.trade_data = None
        self.backtest_results = None
        
    def fetch_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Lädt die Kursdaten für Signalgeber und Handelsobjekt.
        
        Returns:
            Tuple aus (signal_data, trade_data) DataFrames
        """
        print(f"Lade Daten für Signalgeber: {self.config.signal_ticker}")
        print(f"Lade Daten für Handelsobjekt: {self.config.trade_ticker}")
        
        # Etwas früher starten für SMA-Berechnung
        buffer_start = (
            datetime.strptime(self.config.start_date, '%Y-%m-%d') 
            - timedelta(days=self.config.sma_period + 50)
        ).strftime('%Y-%m-%d')
        
        # Signalgeber (Basis-Index)
        signal = yf.download(
            self.config.signal_ticker,
            start=buffer_start,
            end=self.config.end_date,
            progress=False
        )
        
        # Handelsobjekt (LETF)
        trade = yf.download(
            self.config.trade_ticker,
            start=buffer_start,
            end=self.config.end_date,
            progress=False
        )
        
        # Handle MultiIndex columns (neuere yfinance Versionen)
        if isinstance(signal.columns, pd.MultiIndex):
            signal = signal.droplevel(1, axis=1)
        if isinstance(trade.columns, pd.MultiIndex):
            trade = trade.droplevel(1, axis=1)
        
        self.signal_data = signal
        self.trade_data = trade
        
        print(f"✓ Signalgeber: {len(signal)} Datenpunkte")
        print(f"✓ Handelsobjekt: {len(trade)} Datenpunkte")
        
        return signal, trade
    
    def calculate_signals(self) -> pd.DataFrame:
        """
        Berechnet SMA und Handelssignale.
        
        Returns:
            DataFrame mit Signalen und Indikatoren
        """
        if self.signal_data is None:
            self.fetch_data()
        
        df = pd.DataFrame(index=self.signal_data.index)
        
        # Kursdaten
        df['signal_close'] = self.signal_data['Close']
        df['trade_close'] = self.trade_data['Close'].reindex(df.index)
        
        # SMA 200 auf Signalgeber berechnen
        df['sma_200'] = df['signal_close'].rolling(window=self.config.sma_period).mean()
        
        # Handelssignal: 1 = Risk-On (investiert), 0 = Risk-Off (Cash)
        df['signal'] = (df['signal_close'] > df['sma_200']).astype(int)
        
        # Signal-Wechsel erkennen
        df['signal_change'] = df['signal'].diff().fillna(0)
        
        # Auf Backtest-Zeitraum beschränken
        df = df[df.index >= self.config.start_date].copy()
        
        # NaN-Werte entfernen
        df = df.dropna()
        
        return df
    
    def run_backtest(self) -> pd.DataFrame:
        """
        Führt den Backtest der Strategie durch.
        
        Returns:
            DataFrame mit Backtest-Ergebnissen
        """
        df = self.calculate_signals()
        
        # Tägliche Renditen
        df['trade_return'] = df['trade_close'].pct_change()
        df['signal_return'] = df['signal_close'].pct_change()
        
        # Täglicher risikofreier Zins
        daily_rf = (1 + self.config.risk_free_rate) ** (1/252) - 1
        
        # Strategie-Rendite:
        # - Wenn investiert (signal=1): LETF-Rendite
        # - Wenn Cash (signal=0): risikofreier Zins
        # Signal vom Vortag verwenden (wir handeln am nächsten Tag)
        df['strategy_return'] = np.where(
            df['signal'].shift(1) == 1,
            df['trade_return'],
            daily_rf
        )
        
        # Buy & Hold LETF zum Vergleich
        df['bh_letf_return'] = df['trade_return']
        
        # Buy & Hold Basis-Index zum Vergleich
        df['bh_index_return'] = df['signal_return']
        
        # Kumulative Renditen (Portfolio-Wert)
        df['strategy_value'] = self.config.initial_capital * (1 + df['strategy_return']).cumprod()
        df['bh_letf_value'] = self.config.initial_capital * (1 + df['bh_letf_return']).cumprod()
        df['bh_index_value'] = self.config.initial_capital * (1 + df['bh_index_return']).cumprod()
        
        # Drawdown berechnen
        df['strategy_peak'] = df['strategy_value'].cummax()
        df['strategy_drawdown'] = (df['strategy_value'] - df['strategy_peak']) / df['strategy_peak'] * 100
        
        df['bh_letf_peak'] = df['bh_letf_value'].cummax()
        df['bh_letf_drawdown'] = (df['bh_letf_value'] - df['bh_letf_peak']) / df['bh_letf_peak'] * 100
        
        self.backtest_results = df
        return df
    
    def get_statistics(self) -> dict:
        """
        Berechnet Performance-Statistiken.
        
        Returns:
            Dictionary mit Kennzahlen
        """
        if self.backtest_results is None:
            self.run_backtest()
        
        df = self.backtest_results
        
        # Anzahl Handelstage
        trading_days = len(df)
        years = trading_days / 252
        
        # Endwerte
        strategy_final = df['strategy_value'].iloc[-1]
        bh_letf_final = df['bh_letf_value'].iloc[-1]
        bh_index_final = df['bh_index_value'].iloc[-1]
        
        # Gesamtrendite
        strategy_total_return = (strategy_final / self.config.initial_capital - 1) * 100
        bh_letf_total_return = (bh_letf_final / self.config.initial_capital - 1) * 100
        bh_index_total_return = (bh_index_final / self.config.initial_capital - 1) * 100
        
        # Annualisierte Rendite (CAGR)
        strategy_cagr = ((strategy_final / self.config.initial_capital) ** (1/years) - 1) * 100
        bh_letf_cagr = ((bh_letf_final / self.config.initial_capital) ** (1/years) - 1) * 100
        bh_index_cagr = ((bh_index_final / self.config.initial_capital) ** (1/years) - 1) * 100
        
        # Volatilität (annualisiert)
        strategy_vol = df['strategy_return'].std() * np.sqrt(252) * 100
        bh_letf_vol = df['bh_letf_return'].std() * np.sqrt(252) * 100
        bh_index_vol = df['bh_index_return'].std() * np.sqrt(252) * 100
        
        # Sharpe Ratio
        excess_return = df['strategy_return'].mean() - (self.config.risk_free_rate / 252)
        strategy_sharpe = (excess_return / df['strategy_return'].std()) * np.sqrt(252) if df['strategy_return'].std() > 0 else 0
        
        excess_return_bh = df['bh_letf_return'].mean() - (self.config.risk_free_rate / 252)
        bh_letf_sharpe = (excess_return_bh / df['bh_letf_return'].std()) * np.sqrt(252) if df['bh_letf_return'].std() > 0 else 0
        
        # Max Drawdown
        strategy_max_dd = df['strategy_drawdown'].min()
        bh_letf_max_dd = df['bh_letf_drawdown'].min()
        
        # Anzahl Trades
        trades = (df['signal_change'] != 0).sum()
        
        # Zeit investiert
        time_invested = df['signal'].mean() * 100
        
        return {
            'Zeitraum': f"{df.index[0].strftime('%Y-%m-%d')} bis {df.index[-1].strftime('%Y-%m-%d')}",
            'Handelstage': trading_days,
            'Jahre': round(years, 2),
            
            'Strategie': {
                'Endwert': f"${strategy_final:,.2f}",
                'Gesamtrendite': f"{strategy_total_return:.1f}%",
                'CAGR': f"{strategy_cagr:.1f}%",
                'Volatilität': f"{strategy_vol:.1f}%",
                'Sharpe Ratio': f"{strategy_sharpe:.2f}",
                'Max Drawdown': f"{strategy_max_dd:.1f}%",
            },
            
            'Buy & Hold LETF': {
                'Endwert': f"${bh_letf_final:,.2f}",
                'Gesamtrendite': f"{bh_letf_total_return:.1f}%",
                'CAGR': f"{bh_letf_cagr:.1f}%",
                'Volatilität': f"{bh_letf_vol:.1f}%",
                'Sharpe Ratio': f"{bh_letf_sharpe:.2f}",
                'Max Drawdown': f"{bh_letf_max_dd:.1f}%",
            },
            
            'Buy & Hold Index': {
                'Endwert': f"${bh_index_final:,.2f}",
                'Gesamtrendite': f"{bh_index_total_return:.1f}%",
                'CAGR': f"{bh_index_cagr:.1f}%",
                'Volatilität': f"{bh_index_vol:.1f}%",
            },
            
            'Strategie-Details': {
                'Anzahl Trades': trades,
                'Zeit investiert': f"{time_invested:.1f}%",
                'Signalgeber': self.config.signal_ticker,
                'Handelsobjekt': self.config.trade_ticker,
                'SMA Periode': self.config.sma_period,
            }
        }
    
    def print_statistics(self):
        """Gibt die Statistiken formatiert aus."""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print(f"  SMA {self.config.sma_period} LETF STRATEGIE - BACKTEST ERGEBNISSE")
        print("=" * 70)
        print(f"  Zeitraum: {stats['Zeitraum']}")
        print(f"  Handelstage: {stats['Handelstage']} ({stats['Jahre']} Jahre)")
        print(f"  Startkapital: ${self.config.initial_capital:,.2f}")
        print("-" * 70)
        
        print(f"\n  {'Kennzahl':<20} {'Strategie':>15} {'B&H LETF':>15} {'B&H Index':>15}")
        print("  " + "-" * 65)
        
        print(f"  {'Endwert':<20} {stats['Strategie']['Endwert']:>15} {stats['Buy & Hold LETF']['Endwert']:>15} {stats['Buy & Hold Index']['Endwert']:>15}")
        print(f"  {'Gesamtrendite':<20} {stats['Strategie']['Gesamtrendite']:>15} {stats['Buy & Hold LETF']['Gesamtrendite']:>15} {stats['Buy & Hold Index']['Gesamtrendite']:>15}")
        print(f"  {'CAGR':<20} {stats['Strategie']['CAGR']:>15} {stats['Buy & Hold LETF']['CAGR']:>15} {stats['Buy & Hold Index']['CAGR']:>15}")
        print(f"  {'Volatilität':<20} {stats['Strategie']['Volatilität']:>15} {stats['Buy & Hold LETF']['Volatilität']:>15} {stats['Buy & Hold Index']['Volatilität']:>15}")
        print(f"  {'Sharpe Ratio':<20} {stats['Strategie']['Sharpe Ratio']:>15} {stats['Buy & Hold LETF']['Sharpe Ratio']:>15} {'-':>15}")
        print(f"  {'Max Drawdown':<20} {stats['Strategie']['Max Drawdown']:>15} {stats['Buy & Hold LETF']['Max Drawdown']:>15} {'-':>15}")
        
        print("\n  Strategie-Details:")
        print(f"    Signalgeber: {stats['Strategie-Details']['Signalgeber']}")
        print(f"    Handelsobjekt: {stats['Strategie-Details']['Handelsobjekt']}")
        print(f"    Anzahl Trades: {stats['Strategie-Details']['Anzahl Trades']}")
        print(f"    Zeit investiert: {stats['Strategie-Details']['Zeit investiert']}")
        print("=" * 70 + "\n")


# Vordefinierte Konfigurationen
CONFIGS = {
    'sp500_3x': StrategyConfig(
        signal_ticker="^GSPC",
        trade_ticker="UPRO",
        sma_period=200,
        start_date="2010-01-01"
    ),
    'sp500_2x': StrategyConfig(
        signal_ticker="^GSPC",
        trade_ticker="SSO",
        sma_period=200,
        start_date="2010-01-01"
    ),
    'nasdaq_3x': StrategyConfig(
        signal_ticker="^NDX",
        trade_ticker="TQQQ",
        sma_period=200,
        start_date="2010-01-01"
    ),
    'nasdaq_2x': StrategyConfig(
        signal_ticker="^NDX",
        trade_ticker="QLD",
        sma_period=200,
        start_date="2010-01-01"
    ),
}


if __name__ == "__main__":
    # Beispiel: S&P 500 mit 3x LETF
    print("Starte Backtest für S&P 500 + UPRO (3x)...")
    
    strategy = SMALETFStrategy(CONFIGS['sp500_3x'])
    strategy.run_backtest()
    strategy.print_statistics()
