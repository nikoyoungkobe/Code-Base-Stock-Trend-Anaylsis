# calculations/dcf_valuation.py
"""
Discounted Cash Flow (DCF) Bewertungsmodul.
Berechnet den intrinsischen Wert einer Aktie basierend auf prognostizierten Free Cash Flows.
"""


class DCFValuation:
    """
    Klasse für DCF-Bewertungen von Unternehmen.
    """
    
    @staticmethod
    def calculate_dcf(
        financial_data, 
        ticker_symbol, 
        forecast_years=5, 
        discount_rate=0.10, 
        growth_rate=0.05, 
        perpetual_growth_rate=0.02
    ):
        """
        Berechnet den DCF-basierten intrinsischen Wert pro Aktie.
        
        Args:
            financial_data: Dictionary mit Finanzdaten (cashflow, balance_sheet, etc.)
            ticker_symbol: Ticker-Symbol für Fehlermeldungen
            forecast_years: Anzahl Jahre für die FCF-Prognose (default: 5)
            discount_rate: Diskontierungssatz/WACC (default: 10%)
            growth_rate: Jährliche FCF-Wachstumsrate (default: 5%)
            perpetual_growth_rate: Ewige Wachstumsrate für Terminal Value (default: 2%)
            
        Returns:
            Dictionary mit:
                - enterprise_value: Unternehmenswert
                - equity_value: Eigenkapitalwert
                - intrinsic_value_per_share: Fairer Wert pro Aktie
                - cashflows: Liste der diskontierten Cashflows
                - discounted_terminal_value: Diskontierter Terminal Value
                - assumptions: Verwendete Annahmen
                
        Raises:
            ValueError: Wenn Berechnung fehlschlägt
        """
        try:
            # === Daten extrahieren ===
            cashflow_df = financial_data.get('cashflow')
            balance_sheet_df = financial_data.get('balance_sheet')
            
            # Free Cash Flow (letztes verfügbares Jahr)
            fcf = 0
            if cashflow_df is not None and 'Free Cash Flow' in cashflow_df.index:
                fcf = cashflow_df.loc['Free Cash Flow'].iloc[0]
            
            if fcf <= 0:
                raise ValueError(f"FCF für {ticker_symbol} ist nicht positiv ({fcf}). DCF nicht sinnvoll.")
            
            # Cash & Cash Equivalents
            cash = 0
            if balance_sheet_df is not None and 'Cash And Cash Equivalents' in balance_sheet_df.index:
                cash = balance_sheet_df.loc['Cash And Cash Equivalents'].iloc[0]
            
            # Total Debt
            total_debt = 0
            if balance_sheet_df is not None and 'Total Debt' in balance_sheet_df.index:
                total_debt = balance_sheet_df.loc['Total Debt'].iloc[0]
            
            # Shares Outstanding
            shares_outstanding = financial_data.get('Outstanding Shares', 0)
            if shares_outstanding <= 0:
                raise ValueError(f"Shares Outstanding für {ticker_symbol} ist ungültig.")
            
            # === DCF Berechnung ===
            
            # 1. Diskontierte Cashflows für Prognosezeitraum
            discounted_cashflows = []
            for year in range(1, forecast_years + 1):
                projected_fcf = fcf * (1 + growth_rate) ** year
                discounted_fcf = projected_fcf / (1 + discount_rate) ** year
                discounted_cashflows.append({
                    'year': year,
                    'projected_fcf': projected_fcf,
                    'discounted_fcf': discounted_fcf
                })
            
            # 2. Terminal Value (Gordon Growth Model)
            final_year_fcf = fcf * (1 + growth_rate) ** forecast_years
            terminal_value = (final_year_fcf * (1 + perpetual_growth_rate)) / (discount_rate - perpetual_growth_rate)
            discounted_terminal_value = terminal_value / (1 + discount_rate) ** forecast_years
            
            # 3. Enterprise Value = Sum of discounted FCFs + discounted Terminal Value
            sum_discounted_fcfs = sum(cf['discounted_fcf'] for cf in discounted_cashflows)
            enterprise_value = sum_discounted_fcfs + discounted_terminal_value
            
            # 4. Equity Value = Enterprise Value - Net Debt (Total Debt - Cash)
            net_debt = total_debt - cash
            equity_value = enterprise_value - net_debt
            
            # 5. Intrinsic Value per Share
            intrinsic_value_per_share = equity_value / shares_outstanding
            
            return {
                'ticker': ticker_symbol,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'intrinsic_value_per_share': intrinsic_value_per_share,
                'cashflows': discounted_cashflows,
                'discounted_terminal_value': discounted_terminal_value,
                'terminal_value': terminal_value,
                'assumptions': {
                    'base_fcf': fcf,
                    'forecast_years': forecast_years,
                    'discount_rate': discount_rate,
                    'growth_rate': growth_rate,
                    'perpetual_growth_rate': perpetual_growth_rate,
                    'cash': cash,
                    'total_debt': total_debt,
                    'shares_outstanding': shares_outstanding
                }
            }
            
        except Exception as e:
            raise ValueError(f"Fehler beim DCF für {ticker_symbol}: {e}")
    
    @staticmethod
    def format_dcf_result(dcf_result):
        """
        Formatiert das DCF-Ergebnis für die Anzeige.
        
        Args:
            dcf_result: Dictionary von calculate_dcf()
            
        Returns:
            Formatierter String mit DCF-Zusammenfassung
        """
        def fmt_money(value):
            """Formatiert Geldbeträge in Milliarden/Millionen."""
            if abs(value) >= 1e9:
                return f"${value/1e9:.2f}B"
            elif abs(value) >= 1e6:
                return f"${value/1e6:.2f}M"
            else:
                return f"${value:,.2f}"
        
        assumptions = dcf_result['assumptions']
        
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║  DCF Bewertung für {dcf_result['ticker']:^10}                           ║
╠══════════════════════════════════════════════════════════════╣
║  Enterprise Value:        {fmt_money(dcf_result['enterprise_value']):>20}      ║
║  Equity Value:            {fmt_money(dcf_result['equity_value']):>20}      ║
║  Fairer Wert pro Aktie:   {f"${dcf_result['intrinsic_value_per_share']:.2f}":>20}      ║
╠══════════════════════════════════════════════════════════════╣
║  Annahmen:                                                   ║
║    Basis FCF:             {fmt_money(assumptions['base_fcf']):>20}      ║
║    Prognosezeitraum:      {f"{assumptions['forecast_years']} Jahre":>20}      ║
║    Diskontierungsrate:    {f"{assumptions['discount_rate']*100:.1f}%":>20}      ║
║    Wachstumsrate:         {f"{assumptions['growth_rate']*100:.1f}%":>20}      ║
║    Ewige Wachstumsrate:   {f"{assumptions['perpetual_growth_rate']*100:.1f}%":>20}      ║
╚══════════════════════════════════════════════════════════════╝
"""
        return summary
