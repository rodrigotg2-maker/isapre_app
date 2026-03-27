import pandas as pd
import streamlit as st

from config import PLANES_FILE, REQUIRED_COLUMNS


@st.cache_data
def load_data():
    df = pd.read_csv(PLANES_FILE)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas requeridas: {missing_cols}")

    df = df.copy()

    numeric_cols = [
        "precio_pesos",
        "valor_plan_uf",
        "ges_uf",
        "costo_total_uf",
        "ambulatorio_num",
        "hospitalario_num",
        "tope_anual_uf",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Limpieza texto
    df["isapre"] = df["isapre"].astype(str).str.strip()
    df["codigo"] = df["codigo"].astype(str).str.strip()
    df["nombre_plan"] = df["nombre_plan"].astype(str).str.strip()
    df["clinica_preferente"] = df["clinica_preferente"].fillna("Sin clínica informada")
    df["clinica_preferente"] = df["clinica_preferente"].astype(str).str.strip()
    df["estado"] = df["estado"].astype(str).str.strip()

    # Filtrar solo registros válidos
    df = df[df["estado"] == "OK"].copy()

    # Eliminar filas críticas incompletas
    df = df.dropna(subset=[
        "isapre",
        "codigo",
        "nombre_plan",
        "precio_pesos",
        "ambulatorio_num",
        "hospitalario_num",
        "tope_anual_uf",
    ])

    return df