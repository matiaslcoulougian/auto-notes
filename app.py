import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time


# --- Función para buscar datos en Yahoo Finance ---
def obtener_datos_yahoo(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1y")
        if hist.empty:
            return None, None, None, None

        precio_actual = hist['Close'].iloc[-1]
        hace_1_anio = hist['Close'].iloc[0]
        min_1y = hist['Close'].min()
        target_yhoo = data.info.get('targetMeanPrice', None)

        return precio_actual, target_yhoo, hace_1_anio, min_1y
    except Exception as e:
        print(f"Error en Yahoo para {ticker}: {e}")
        return None, None, None, None


# --- Scraping Target Price Morgan Stanley ---
def obtener_target_morgan(ticker):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }
    url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        top_analysts_section = soup.find("section", id="top-analyst")
        if top_analysts_section:
            table_container = top_analysts_section.find_next("div", class_="tableContainer yf-u5azpk")
            if table_container:
                rows = table_container.find_all("tr")
                for row in rows:
                    columns = row.find_all("td")
                    if columns:
                        analyst_name = columns[0].get_text(strip=True)
                        if "Morgan Stanley" in analyst_name:
                            price_target = columns[-2].get_text(strip=True)
                            try:
                                price_target = float(price_target.replace("$", "").replace(",", ""))
                            except:
                                pass
                            return price_target
            return None
        else:
            return None
    except Exception as e:
        print(f"Error scraping Morgan Stanley para {ticker}: {e}")
        return None


# Título de la app
st.title("Structured Investment Pro 📈")

# -- Session State para persistencia de datos temporales --
if "notas" not in st.session_state:
    st.session_state["notas"] = []
if "pesos" not in st.session_state:
    st.session_state["pesos"] = {
        "Tasa": 0.15,
        "Colchón": 0.34,
        "Memory": 0.24,
        "Target Yahoo": 0.09,
        "Target MS": 0.09,
        "1 Año": 0.09,
        "Mín 1 Año": 0.09,
    }
if "reset" not in st.session_state:
    st.session_state["reset"] = False

# -- Formulario de Inputs --
with st.form("input_form", clear_on_submit=True):
    st.subheader("Agregar nueva nota")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("Ticker", max_chars=8)
    with col2:  # format in 0.00
        tasa = st.number_input("Tasa (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f")
    with col3:
        colchon = st.number_input("Colchón (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f")
    with col4:
        memory = st.checkbox("Memory", value=False)
    submitted = st.form_submit_button("Agregar nota")

    # Al agregar, guardamos en session_state
    if submitted:
        if ticker and len(st.session_state["notas"]) < 20:
            st.session_state["notas"].append({
                "Ticker": ticker.upper(),
                "Tasa": tasa,
                "Colchón": colchon,
                "Memory": memory,
            })
        elif not ticker:
            st.warning("Ingrese un ticker válido.")
        elif len(st.session_state["notas"]) >= 20:
            st.warning("Máximo 20 notas.")

# -- Edición de Pesos Ponderados --
with st.expander("⚙️ Configurar pesos del motor"):
    st.write("Modifique los pesos de cada variable (suma no obligatoria = 1):")
    for key in st.session_state["pesos"]:
        valor = st.number_input(
            f"Peso para {key}",
            min_value=0.0, max_value=1.0, step=0.01,
            value=float(st.session_state["pesos"][key]),
            key=f"peso_{key}"
        )
        st.session_state["pesos"][key] = valor

# -- Visualización de la tabla de notas --
st.subheader("Notas cargadas")
if st.session_state["notas"]:
    df = pd.DataFrame(st.session_state["notas"])

    # Botón para completar datos automáticos
    if st.button("Completar datos automáticos"):
        with st.spinner("Buscando datos para cada ticker..."):
            nuevas_notas = []
            for nota in st.session_state["notas"]:
                ticker = nota["Ticker"]
                # --- Yahoo Finance ---
                precio_actual, target_yhoo, hace_1_anio, min_1y = obtener_datos_yahoo(ticker)
                # --- Morgan Stanley ---
                target_morgan = obtener_target_morgan(ticker)
                # Armar nueva nota con todos los datos
                nota_actualizada = nota.copy()
                nota_actualizada["Precio actual"] = precio_actual
                nota_actualizada["Target Yahoo"] = target_yhoo
                nota_actualizada["Hace 1 año"] = hace_1_anio
                nota_actualizada["Mín 1 año"] = min_1y
                nota_actualizada["Target Morgan"] = target_morgan
                nuevas_notas.append(nota_actualizada)
                time.sleep(1)  # Evita bloqueos por scraping agresivo
            st.session_state["notas"] = nuevas_notas
        st.success("Datos completados para todos los tickers.")

    # Mostrar tabla actualizada
    df = pd.DataFrame(st.session_state["notas"])
    st.dataframe(df, use_container_width=True)
    st.info(f"Total notas cargadas: {len(st.session_state['notas'])}/20")
else:
    st.info("No hay notas cargadas aún.")

# -- Botón para limpiar entradas --
if st.button("Limpiar todas las notas"):
    st.session_state["notas"] = []
    st.session_state["reset"] = True
    st.rerun()
