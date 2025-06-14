import streamlit as st
import pandas as pd
import yfinance as yf
from io import BytesIO

st.title("📊 Cargar datos de Yahoo Finance")
st.write("Subí un archivo Excel con acciones y completaremos: precio actual, hace 1 año, mínimo y target.")

uploaded_file = st.file_uploader("📁 Soltá el archivo Excel acá", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=3)
    df.columns = [str(col).strip().lower() for col in df.columns]

    st.success("Archivo cargado correctamente.")

    # Agregá tickers manualmente (luego podés automatizar esta parte)
    tickers = {
        1: "COP",
        3: "BAC",
        # agregá más filas y tickers si querés
    }

    for col in ['precio actual', 'target yhoo', 'hace 1 año', 'min 1y']:
        if col not in df.columns:
            df[col] = None

    if st.button("🚀 Ejecutar búsqueda de datos"):
        for i, ticker in tickers.items():
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period="1y")

                if not hist.empty:
                    df.at[i, 'precio actual'] = hist['Close'].iloc[-1]
                    df.at[i, 'hace 1 año'] = hist['Close'].iloc[0]
                    df.at[i, 'min 1y'] = hist['Close'].min()
                    df.at[i, 'target yhoo'] = data.info.get('targetMeanPrice', None)

            except Exception as e:
                st.warning(f"Error con {ticker}: {e}")

        # Exportar como archivo descargable
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        st.success("✅ Archivo procesado. Podés descargarlo abajo.")
        st.download_button("📥 Descargar Excel", output, file_name="notas_actualizadas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")