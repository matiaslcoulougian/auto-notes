import streamlit as st
import pandas as pd

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

# -- Formulario de Inputs --
with st.form("input_form", clear_on_submit=True):
    st.subheader("Agregar nueva nota")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("Ticker", max_chars=8)
    with col2:
        tasa = st.number_input("Tasa (%)", min_value=0.0, max_value=100.0, step=0.01)
    with col3:
        colchon = st.number_input("Colchón (%)", min_value=0.0, max_value=100.0, step=0.01)
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
    st.dataframe(df, use_container_width=True)
    st.info(f"Total notas cargadas: {len(st.session_state['notas'])}/20")
else:
    st.info("No hay notas cargadas aún.")

# -- Botón para limpiar entradas (opcional) --
if st.button("Limpiar todas las notas"):
    st.session_state["notas"] = []
    st.success("Notas eliminadas.")