import pandas as pd
import yfinance as yf

# Cargar Excel
df = pd.read_excel("notas sem 22-4-24.xlsx", header=3)
df.columns = [str(col).strip().lower() for col in df.columns]

# Definir tickers manualmente para cada fila (ajustalo con tus propios tickers)
tickers = {
    1: "COP",   # ConocoPhillips
    3: "BAC",   # Bank of America
    # agregar más: índice de fila -> ticker
}

# Asegurar columnas necesarias
for col in ['precio actual', 'target yhoo', 'hace 1 año', 'min 1y']:
    if col not in df.columns:
        df[col] = None

# Completar datos para cada fila con ticker
for i, ticker in tickers.items():
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1y")

        if hist.empty:
            print(f"{ticker}: sin datos")
            continue

        df.at[i, 'precio actual'] = hist['Close'].iloc[-1]
        df.at[i, 'hace 1 año'] = hist['Close'].iloc[0]
        df.at[i, 'min 1y'] = hist['Close'].min()
        df.at[i, 'target yhoo'] = data.info.get('targetMeanPrice', None)

        print(f"{ticker}: OK")

    except Exception as e:
        print(f"{ticker}: error - {e}")

# Guardar nuevo Excel
df.to_excel("notas_completadas.xlsx", index=False)