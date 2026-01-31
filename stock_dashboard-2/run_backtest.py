#!/usr/bin/env python3
# run_backtest.py
"""
Standalone Script zum Ausführen der SMA 200 LETF Strategie.
Kann unabhängig vom Dashboard genutzt werden.

Verwendung:
    python run_backtest.py                    # Standard: S&P 500 + UPRO (3x)
    python run_backtest.py --preset nasdaq_3x # Nasdaq 100 + TQQQ (3x)
    python run_backtest.py --signal ^GSPC --trade SSO --sma 200  # Custom
"""

import argparse
import sys
import os

# Projektpfad hinzufügen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies.sma_letf_strategy import SMALETFStrategy, StrategyConfig, CONFIGS
from strategies.sma_letf_visualization import (
    create_signal_chart,
    create_performance_chart,
    create_drawdown_chart,
    create_annual_returns_chart
)


def main():
    parser = argparse.ArgumentParser(
        description='SMA 200 LETF Strategie Backtest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python run_backtest.py                          # S&P 500 + UPRO (3x)
  python run_backtest.py --preset nasdaq_3x       # Nasdaq + TQQQ (3x)
  python run_backtest.py --preset sp500_2x        # S&P 500 + SSO (2x)
  python run_backtest.py --signal ^GSPC --trade UPRO --start 2015-01-01
  
Verfügbare Presets: sp500_3x, sp500_2x, nasdaq_3x, nasdaq_2x
        """
    )
    
    parser.add_argument(
        '--preset', 
        choices=['sp500_3x', 'sp500_2x', 'nasdaq_3x', 'nasdaq_2x'],
        default='sp500_3x',
        help='Vordefinierte Konfiguration (default: sp500_3x)'
    )
    parser.add_argument('--signal', help='Signalgeber Ticker (z.B. ^GSPC)')
    parser.add_argument('--trade', help='Handelsobjekt Ticker (z.B. UPRO)')
    parser.add_argument('--sma', type=int, default=200, help='SMA Periode (default: 200)')
    parser.add_argument('--start', default='2010-01-01', help='Startdatum (default: 2010-01-01)')
    parser.add_argument('--end', default=None, help='Enddatum (default: heute)')
    parser.add_argument('--capital', type=float, default=10000, help='Startkapital (default: 10000)')
    parser.add_argument('--show-charts', action='store_true', help='Charts im Browser öffnen')
    parser.add_argument('--save-html', help='Charts als HTML speichern (Pfad angeben)')
    
    args = parser.parse_args()
    
    # Konfiguration erstellen
    if args.signal or args.trade:
        # Custom Konfiguration
        config = StrategyConfig(
            signal_ticker=args.signal or "^GSPC",
            trade_ticker=args.trade or "UPRO",
            sma_period=args.sma,
            initial_capital=args.capital,
            start_date=args.start,
            end_date=args.end
        )
    else:
        # Preset verwenden
        config = CONFIGS[args.preset]
        config.initial_capital = args.capital
        config.start_date = args.start
        if args.end:
            config.end_date = args.end
    
    print("\n" + "=" * 70)
    print("  SMA LETF STRATEGIE - BACKTEST")
    print("=" * 70)
    print(f"  Signalgeber:    {config.signal_ticker}")
    print(f"  Handelsobjekt:  {config.trade_ticker}")
    print(f"  SMA Periode:    {config.sma_period} Tage")
    print(f"  Startkapital:   ${config.initial_capital:,.2f}")
    print(f"  Zeitraum:       {config.start_date} bis {config.end_date or 'heute'}")
    print("=" * 70)
    
    # Strategie ausführen
    strategy = SMALETFStrategy(config)
    
    print("\n[1/3] Lade Kursdaten...")
    strategy.fetch_data()
    
    print("[2/3] Führe Backtest durch...")
    df = strategy.run_backtest()
    
    print("[3/3] Berechne Statistiken...")
    strategy.print_statistics()
    
    # Charts erstellen
    if args.show_charts or args.save_html:
        print("\nErstelle Visualisierungen...")
        
        signal_fig = create_signal_chart(df, config)
        perf_fig = create_performance_chart(df, config, config.initial_capital)
        dd_fig = create_drawdown_chart(df, config)
        annual_fig = create_annual_returns_chart(df, config)
        
        if args.save_html:
            # Als HTML speichern
            from plotly.subplots import make_subplots
            import plotly.io as pio
            
            # Kombiniertes HTML erstellen
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SMA {config.sma_period} LETF Strategie - Backtest</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                    .chart-container {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    h1 {{ color: #333; text-align: center; }}
                    .info {{ text-align: center; color: #666; margin-bottom: 30px; }}
                </style>
            </head>
            <body>
                <h1>SMA {config.sma_period} LETF Strategie - Backtest Ergebnisse</h1>
                <p class="info">
                    Signalgeber: {config.signal_ticker} | 
                    Handelsobjekt: {config.trade_ticker} | 
                    Zeitraum: {config.start_date} bis {df.index[-1].strftime('%Y-%m-%d')}
                </p>
                
                <div class="chart-container">
                    {signal_fig.to_html(full_html=False, include_plotlyjs=False)}
                </div>
                
                <div class="chart-container">
                    {perf_fig.to_html(full_html=False, include_plotlyjs=False)}
                </div>
                
                <div class="chart-container">
                    {dd_fig.to_html(full_html=False, include_plotlyjs=False)}
                </div>
                
                <div class="chart-container">
                    {annual_fig.to_html(full_html=False, include_plotlyjs=False)}
                </div>
            </body>
            </html>
            """
            
            with open(args.save_html, 'w') as f:
                f.write(html_content)
            print(f"✓ Charts gespeichert: {args.save_html}")
        
        if args.show_charts:
            # Im Browser öffnen
            signal_fig.show()
            perf_fig.show()
            dd_fig.show()
            annual_fig.show()
    
    print("\n✓ Backtest abgeschlossen!\n")
    
    return strategy, df


if __name__ == "__main__":
    main()
