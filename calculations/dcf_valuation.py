# calculations/dcf_valuation.py
class DCFValuation:
    @staticmethod
    def calculate_dcf(financial_data, ticker_symbol, forecast_years=5, discount_rate=0.0650, growth_rate=0.02, perpetual_growth_rate=0.02):
        try:
            fcf = financial_data['cashflow'].loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in financial_data['cashflow'].index else 0
            cash = financial_data['balance_sheet'].loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in financial_data['balance_sheet'].index else 0
            total_debt = financial_data['balance_sheet'].loc['Total Debt'].iloc[0] if 'Total Debt' in financial_data['balance_sheet'].index else 0
            shares_outstanding = financial_data['Outstanding Shares']

            cashflows = []
            for i in range(forecast_years):
                projected_fcf = fcf * (1 + growth_rate) ** (i + 1)
                discounted_fcf = projected_fcf / (1 + discount_rate) ** (i + 1)
                cashflows.append(discounted_fcf)

            final_fcf = fcf * (1 + growth_rate) ** forecast_years
            terminal_value = (final_fcf * (1 + perpetual_growth_rate)) / (discount_rate - perpetual_growth_rate)
            discounted_terminal_value = terminal_value / (1 + discount_rate) ** forecast_years

            enterprise_value = sum(cashflows) + discounted_terminal_value
            equity_value = enterprise_value - total_debt + cash
            intrinsic_value_per_share = equity_value / shares_outstanding

            return {
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'intrinsic_value_per_share': intrinsic_value_per_share,
                'cashflows': cashflows,
                'discounted_terminal_value': discounted_terminal_value
            }
        except Exception as e:
            raise ValueError(f"Fehler beim DCF für {ticker_symbol}: {e}")