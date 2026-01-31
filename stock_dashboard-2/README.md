# Stock Dashboard 📈

Ein interaktives Dashboard für Aktienanalyse und Trend-Visualisierung.

## Features

- **Kursdaten-Visualisierung**: Historische Schlusskurse mit Vergleichsmöglichkeit
- **Relative Performance**: Normalisierte Darstellung (Basis 100) zum Vergleich
- **Fundamentaldaten**: FCF, Verschuldung, Umsatz, Gewinn, Nettomarge
- **Makro-Indikatoren**: VIX (Volatilitätsindex), US Treasury Yield Curve
- **DCF-Bewertung**: Intrinsischer Wert basierend auf Free Cash Flow

## Installation

```bash
# Repository klonen
git clone <your-repo-url>
cd stock_dashboard

# Virtual Environment erstellen (empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt
```

## Konfiguration

1. **FRED API Key** (für Makrodaten):
   - Kostenlos erhältlich unter: https://fred.stlouisfed.org/docs/api/api_key.html
   - In `config/settings.py` eintragen:
   ```python
   FRED_API_KEY = "dein_api_key_hier"
   ```

2. **Initiale Ticker anpassen** (optional):
   ```python
   INITIAL_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
   ```

## Starten

```bash
python main.py
```

Dashboard öffnen: http://127.0.0.1:8050

## Projektstruktur

```
stock_dashboard/
├── main.py                 # Einstiegspunkt
├── requirements.txt        # Dependencies
├── README.md
│
├── config/
│   ├── __init__.py
│   └── settings.py         # Konfiguration (API Keys, Ticker, etc.)
│
├── data/
│   ├── __init__.py
│   ├── fetch_data.py       # Aktien- und Finanzdaten (yfinance)
│   └── macro_data.py       # Makrodaten (VIX, Yields)
│
├── calculations/
│   ├── __init__.py
│   └── dcf_valuation.py    # DCF-Bewertungsmodell
│
└── visualization/
    ├── __init__.py
    ├── dashboard.py        # Dash Layout
    └── callbacks.py        # Interaktive Callbacks
```

## Verwendung

1. **Ticker hinzufügen**: Ticker-Symbol(e) eingeben (kommagetrennt) und "Hinzufügen" klicken
2. **Ticker auswählen**: Im Dropdown einen oder mehrere Ticker für den Chart wählen
3. **Vergleichen**: "Relative Veränderung" aktivieren für normalisierten Vergleich
4. **Zeitraum**: Bei Makro-Indikatoren den gewünschten Zeitraum wählen

## Datenquellen

- **Kursdaten & Fundamentals**: Yahoo Finance (via yfinance)
- **Makrodaten**: FRED (Federal Reserve Economic Data)

## Lizenz

MIT License
