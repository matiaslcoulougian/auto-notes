import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time
from openpyxl.styles import PatternFill
import io
import datetime


# --- Función para buscar datos en Yahoo Finance ---
def obtener_datos_yahoo(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1y")
        if hist.empty:
            return None, None, None, None

        precio_actual = hist['Close'].iloc[-1]
        hace_1_anio = hist['Close'].iloc[0]
        # TODO: get this data from scrapping yahoo finance.
        min_1y = 53.51
        target_yhoo = data.info.get('targetMeanPrice', None)

        return precio_actual, target_yhoo, hace_1_anio, min_1y
    except Exception as e:
        print(f"Error en Yahoo para {ticker}: {e}")
        return None, None, None, None


# --- Scraping Target Price Morgan Stanley ---
#TODO: Use https://www.tipranks.com/stocks/c/forecast instead.
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


# -- Cálculo de Score (según lógica del PRD) --
def calcular_score(nota, pesos):
    # Extraer valores, convertir None a 0
    tasa = nota.get("Tasa") or 0
    colchon = nota.get("Colchón") or 0
    memory = 1 if nota.get("Memory") else 0
    precio_actual = nota.get("Precio actual") or 0
    target_yahoo = nota.get("Target Yahoo") or 0
    target_morgan = nota.get("Target Morgan") or 0
    hace_1_anio = nota.get("Hace 1 año") or 0
    min_1_anio = nota.get("Mín 1 año") or 0

    # Pesos
    p_tasa = pesos["Tasa"]
    p_colchon = pesos["Colchón"]
    p_memory = pesos["Memory"]
    p_yahoo = pesos["Target Yahoo"]
    p_ms = pesos["Target MS"]
    p_1y = pesos["1 Año"]
    p_min1y = pesos["Mín 1 Año"]

    # Trigger
    try:
        trigger = precio_actual * (100 - colchon) / 100 if precio_actual and colchon is not None else 0
    except Exception:
        trigger = 0

    # Evitar divisiones por cero
    def safe_div(n, d):
        try:
            return n / d if d else 0
        except:
            return 0

    # Términos polinómicos
    t1 = tasa * p_tasa / 20
    t2 = colchon * p_colchon / 100
    t3 = memory * p_memory
    t4 = ((safe_div(target_yahoo, precio_actual) - 1) * p_yahoo if precio_actual else 0)
    t5 = ((safe_div(target_morgan, precio_actual) - 1) * p_ms if precio_actual else 0)
    t6 = (safe_div(hace_1_anio, trigger) * p_1y if trigger else 0)
    t7 = (safe_div(min_1_anio, trigger) * p_min1y if trigger else 0)

    score = t1 + t2 + t3 + t4 + t5 + t6 + t7
    return score

# -- Calcular Score para cada nota --
if st.session_state["notas"]:
    if st.button("Calcular Score"):
        nuevas_notas = []
        pesos = st.session_state["pesos"]
        for nota in st.session_state["notas"]:
            nota_actualizada = nota.copy()
            score = calcular_score(nota, pesos)
            nota_actualizada["Score"] = score
            nuevas_notas.append(nota_actualizada)
        st.session_state["notas"] = nuevas_notas
        st.success("Score calculado para todas las notas.")

    # -- Mostrar tabla con Score y semáforo --
    df = pd.DataFrame(st.session_state["notas"])

    def color_semaforo(val):
        # Colores tipo semáforo según score (ajustá los rangos si querés)
        if "Score" in df.columns:
            try:
                if val >= df["Score"].max() * 0.66:
                    return "background-color: #2ecc40; color: black;"  # Verde
                elif val >= df["Score"].max() * 0.33:
                    return "background-color: #ffe066; color: black;"  # Amarillo
                else:
                    return "background-color: #ff7f7f; color: black;"  # Rojo
            except:
                return ""
        return ""


    def exportar_excel_semaforo(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Notas")
            workbook = writer.book
            worksheet = writer.sheets["Notas"]
            # Determinar la columna "Score"
            score_col = None
            for idx, col in enumerate(df.columns, 1):
                if col == "Score":
                    score_col = idx
                    break
            # Solo si hay Score y más de 1 nota
            if score_col is not None and len(df) > 0:
                valores = df["Score"].values
                max_score = max(valores)
                min_score = min(valores)
                for row in range(2, len(df) + 2):  # Desde fila 2 (1 es header)
                    cell = worksheet.cell(row=row, column=score_col)
                    val = cell.value
                    # Definir color según score
                    if max_score - min_score > 0:
                        rel_val = (val - min_score) / (max_score - min_score)
                    else:
                        rel_val = 1  # Todos iguales, poner verde
                    if rel_val >= 0.66:
                        fill = PatternFill(start_color="99FF99", end_color="99FF99", fill_type="solid")  # Verde
                    elif rel_val >= 0.33:
                        fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")  # Amarillo
                    else:
                        fill = PatternFill(start_color="FF9999", end_color="FF9999", fill_type="solid")  # Rojo
                    cell.fill = fill
        output.seek(0)
        return output

    if "Score" in df.columns:
        st.dataframe(
            df.style.map(color_semaforo, subset=["Score"]),
            use_container_width=True
        )
    else:
        st.dataframe(df, use_container_width=True)

    # Botón para exportar a Excel
    if "Score" in df.columns and not df["Score"].isnull().all():
        excel_data = exportar_excel_semaforo(df)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        st.download_button(
            label="📥 Descargar Excel con Resultados",
            data=excel_data,
            file_name="notas_scoring_{}.xlsx".format(today),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
