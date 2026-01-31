# data/fetch_data.py
"""
Modul zum Abrufen von Aktien- und Finanzdaten via yfinance.
"""

import yfinance as yf


class GetClosingPrices:
    """
    Eine Klasse zum Verwalten und Abrufen historischer Finanzdaten für eine Liste von Aktien.
    """
    
    def __init__(self, ticker_list, start_date, end_date):
        """
        Initialisiert den GetClosingPrices Manager.
        
        Args:
            ticker_list: Liste von Ticker-Symbolen (z.B. ['AAPL', 'MSFT'])
            start_date: Startdatum für historische Daten (Format: 'YYYY-MM-DD')
            end_date: Enddatum für historische Daten (Format: 'YYYY-MM-DD')
        """
        self.ticker_list = ticker_list
        self.start_date = start_date
        self.end_date = end_date
        self.historical_data = {}
        self.financial_data = {}

    def fetch_historical_data(self):
        """
        Ruft historische Kursdaten und Finanzdaten für alle Ticker ab.
        """
        # === Teil 1: Kursdaten abrufen ===
        print(f"Starte Datenabruf für: {', '.join(self.ticker_list)} von {self.start_date} bis {self.end_date}")
        
        for ticker_symbol in self.ticker_list:
            print(f"Abrufen von Kursdaten für {ticker_symbol}...")
            try:
                ticker_data = yf.Ticker(ticker_symbol)
                ticker_df = ticker_data.history(start=self.start_date, end=self.end_date)

                if not ticker_df.empty:
                    self.historical_data[ticker_symbol] = ticker_df
                    print(f"  ✓ Kursdaten für {ticker_symbol} erfolgreich abgerufen.")
                else:
                    print(f"  ⚠ Warnung: Keine Kursdaten für {ticker_symbol} im angegebenen Zeitraum gefunden.")
            except Exception as e:
                print(f"  ✗ Fehler beim Abrufen von Kursdaten für {ticker_symbol}: {e}")
        
        print("Kursdatenabruf abgeschlossen.\n")

        # === Teil 2: Finanzdaten abrufen ===
        print(f"Starte Finanzdatenabruf für: {', '.join(self.ticker_list)}")
        
        for ticker_symbol in self.ticker_list:
            print(f"Abrufen von Finanzdaten für {ticker_symbol}...")
            try:
                # BUGFIX: Korrigierte Zeile (war: yf.Tickerticker_data = yf.Ticker)
                ticker_data = yf.Ticker(ticker_symbol)
                
                # Finanzdaten abrufen
                financials = ticker_data.financials        # Jährliche Gewinn- und Verlustrechnung
                cashflow = ticker_data.cashflow            # Jährliche Cashflow-Rechnung
                balance_sheet = ticker_data.balance_sheet  # Jährliche Bilanz
                
                # Zusätzliche Kennzahlen extrahieren
                shares_outstanding = ticker_data.info.get('sharesOutstanding', 0)
                
                # Free Cash Flow ermitteln (mit Fallback auf Operating Cash Flow)
                fcf = 0
                if cashflow is not None and not cashflow.empty:
                    if 'Free Cash Flow' in cashflow.index:
                        fcf = cashflow.loc['Free Cash Flow'].iloc[0]
                    elif 'Operating Cash Flow' in cashflow.index:
                        fcf = cashflow.loc['Operating Cash Flow'].iloc[0]
                
                # Finanzdaten als Dictionary speichern
                self.financial_data[ticker_symbol] = {
                    'financials': financials,
                    'cashflow': cashflow,
                    'balance_sheet': balance_sheet,
                    'Outstanding Shares': shares_outstanding,
                    'Free Cashflow': fcf
                }
                
                print(f"  ✓ Finanzdaten für {ticker_symbol} erfolgreich abgerufen.")
                
            except Exception as e:
                print(f"  ✗ Fehler beim Abrufen von Finanzdaten für {ticker_symbol}: {e}")
        
        print("Finanzdatenabruf abgeschlossen.\n")

    def get_data_for_ticker(self, ticker_symbol):
        """
        Gibt die historischen Kursdaten für einen bestimmten Ticker zurück.
        
        Args:
            ticker_symbol: Das Ticker-Symbol (z.B. 'AAPL')
            
        Returns:
            DataFrame mit Kursdaten oder None wenn nicht vorhanden
        """
        return self.historical_data.get(ticker_symbol)
    
    def get_financial_data_for_ticker(self, ticker_symbol):
        """
        Gibt die Finanzdaten für einen bestimmten Ticker zurück.
        
        Args:
            ticker_symbol: Das Ticker-Symbol (z.B. 'AAPL')
            
        Returns:
            Dictionary mit Finanzdaten oder None wenn nicht vorhanden
        """
        return self.financial_data.get(ticker_symbol)
    
    def get_available_tickers(self):
        """
        Gibt eine Liste aller Ticker zurück, für die Daten verfügbar sind.
        
        Returns:
            Liste von Ticker-Symbolen
        """
        return [
            ticker for ticker in self.ticker_list
            if ticker in self.historical_data and not self.historical_data[ticker].empty
        ]
