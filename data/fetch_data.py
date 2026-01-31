import yfinance as yf
import pandas as pd


class GetClosingPrices:
    """
    Eine Klasse zum Verwalten und Abrufen historischer Finanzdaten für eine Liste von Aktien.
    """
    def __init__(self, ticker_list, start_date, end_date):
        self.ticker_list = ticker_list
        self.start_date = start_date
        self.end_date = end_date
        self.historical_data = {}
        self.financial_data = {}

    def fetch_historical_data(self):
        """Datenabruf für Kursdaten gestartet"""
        print(f"Starte Datenabruf für: {', '.join(self.ticker_list)} von {self.start_date} bis {self.end_date}")
        for ticker_symbol in self.ticker_list:
            print(f"Abrufen von Daten für {ticker_symbol}...")
            try:
                ticker_data = yf.Ticker(ticker_symbol)
                ticker_df = ticker_data.history(start=self.start_date, end=self.end_date)

                if not ticker_df.empty:
                    self.historical_data[ticker_symbol] = ticker_df
                    print(f"Daten für {ticker_symbol} erfolgreich abgerufen.")
                else:
                    print(f"Warnung: Keine Daten für {ticker_symbol} im angegebenen Zeitraum gefunden.")
            except Exception as e:
                print(f"Fehler beim Abrufen von Daten für {ticker_symbol}: {e}")
        print("Datenabruf für Kursdaten abgeschlossen.")

        """Datenabruf für Finanzdaten"""
        print(f"Starte Datenabruf für: {', '.join(self.ticker_list)}")
        for ticker_symbol in self.ticker_list:
                    print(f'Rufe Finanzdaten für Ticker {ticker_symbol} ab.')

                    try:
                        ticker_data = yf.Ticker(ticker_symbol)
                        financials = ticker_data.financials      # Jährliche Gewinn- und Verlustrechnung
                        cashflow = ticker_data.cashflow          # Jährliche Cashflow-Rechnung
                        balance_sheet = ticker_data.balance_sheet # Jährliche Bilanz
                        cash = balance_sheet.loc['Cash And Cash Equivalents'] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
                        shares_outstanding = ticker_data.info['sharesOutstanding']
                        fcf = cashflow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cashflow.index else cashflow.loc['Operating Cash Flow'].iloc[-1]
                        total_debt = balance_sheet.loc['Total Debt']
                        
                        
                        print(f"Finanzdaten für {ticker_symbol} erfolgreich abgerufen.")     

                    #Dataframes aus Finanzdaten für einen Stockticker zusammenführen als Dictionary
                        self.financial_data[ticker_symbol] = {'financials': financials,
                                                              'cashflow': cashflow,
                                                              'balance_sheet': balance_sheet,
                                                              #'Total Cash': cash,
                                                              'Outstanding Shares': shares_outstanding,
                                                              'Free Cashflow': fcf
                                                              #'Total Debt': total_debt
                                                              }
                                                                    
                        print(f"Finanzdataframe für {ticker_symbol} erfolgreich erstellt.")
                        print('This is cash:', cash, shares_outstanding)
                        
                    except Exception as e:
                        print(f"Fehler beim Abrufen von Finanzdaten für {ticker_symbol}: {e}")            
        print('Finanzdatenabruf abgeschlossen.')   

    def get_data_for_ticker(self, ticker_symbol):
        """Ruft Chartdata für den gewählten Stockticker über den gewählten Zeitraum und Periode ab."""
        return self.historical_data.get(ticker_symbol)
    
    def get_financial_data_for_ticker(self, ticker_symbol):
        "Ruft Finanzdaten wie Umsatz, Gewinn, Schulden etc. ab"
        return self.financial_data.get(ticker_symbol)

    def get_price_series(self, ticker_symbol: str, column: str = 'Close') -> pd.Series:
        """
        Get a specific price column as a Series.

        Args:
            ticker_symbol: Stock ticker
            column: Price column name ('Close', 'Open', 'High', 'Low')

        Returns:
            pd.Series with DatetimeIndex, or None if not found
        """
        df = self.historical_data.get(ticker_symbol)
        if df is not None and column in df.columns:
            return df[column]
        return None

    def get_returns_for_ticker(
        self,
        ticker_symbol: str,
        return_type: str = 'simple'
    ) -> pd.Series:
        """
        Calculate returns for a ticker.

        Args:
            ticker_symbol: Stock ticker
            return_type: 'simple' for arithmetic, 'log' for logarithmic

        Returns:
            pd.Series of returns with DatetimeIndex, or None if not found
        """
        prices = self.get_price_series(ticker_symbol, 'Close')
        if prices is None:
            return None

        if return_type == 'log':
            import numpy as np
            return np.log(prices / prices.shift(1))
        else:
            return prices.pct_change()