import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile

from loaders import load_data
from scoring import calculate_score
from pdf_utils import download_plan_pdf, merge_pdfs

st.set_page_config(page_title="Ranking Planes Isapre", layout="wide")

st.title("Modelo interactivo de ranking de planes")
st.write("Ranking dinámico del universo de planes de Isapre")

SCENARIOS = {
    "Balanceado": {
        "hospitalario": 35,
        "ambulatorio": 20,
        "tope_anual": 25,
        "precio": 20,
    },
    "Priorizar precio": {
        "hospitalario": 20,
        "ambulatorio": 15,
        "tope_anual": 15,
        "precio": 50,
    },
    "Priorizar maternidad": {
        "hospitalario": 40,
        "ambulatorio": 15,
        "tope_anual": 30,
        "precio": 15,
    },
    "Máxima cobertura": {
        "hospitalario": 35,
        "ambulatorio": 30,
        "tope_anual": 25,
        "precio": 10,
    },
}


def to_csv_download(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_download(sheets_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df_sheet in sheets_dict.items():
            df_sheet.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    output.seek(0)
    return output.getvalue()


def build_zip_from_pdfs(pdf_items):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, pdf_bytes in pdf_items:
            zf.writestr(filename, pdf_bytes)
    output.seek(0)
    return output.getvalue()


def safe_filename(text):
    text = str(text)
    invalid = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for ch in invalid:
        text = text.replace(ch, "-")
    return text.strip()


def get_pdf_url(codigo):
    return f"https://pdfplan.cl/viewplan/{codigo}.pdf"


def get_semaforo(score):
    if score >= 0.75:
        return "🟢 Recomendado"
    elif score >= 0.55:
        return "🟡 Evaluar"
    return "🔴 Bajo atractivo"


def build_recommendation(top1, escenario, presupuesto_max, excluir_fuera_presupuesto, priorizar_maternidad):
    motivos = []

    motivos.append(f"obtiene el mayor score del escenario '{escenario}'")
    motivos.append(f"en la isapre {top1['isapre']}")
    motivos.append(f"con clínica preferente '{top1['clinica_preferente']}'")
    motivos.append(f"destaca con {top1['hospitalario_num']:.0f}% hospitalario")
    motivos.append(f"y {top1['ambulatorio_num']:.0f}% ambulatorio")
    motivos.append(f"con tope anual de {top1['tope_anual_uf']:.0f} UF")

    if presupuesto_max > 0:
        if top1["precio_pesos"] <= presupuesto_max:
            motivos.append(f"queda dentro del presupuesto definido (${top1['precio_pesos']:,.0f})")
        else:
            if excluir_fuera_presupuesto:
                motivos.append("cumple las restricciones activas")
            else:
                motivos.append(
                    f"supera el presupuesto definido (${top1['precio_pesos']:,.0f}), pero compensa por cobertura"
                )

    if priorizar_maternidad:
        motivos.append("se beneficia del criterio adicional de maternidad")

    return (
        f"**Recomendación principal:** {top1['nombre_plan']}  \n"
        f"Este plan se recomienda porque " + ", ".join(motivos) + "."
    )


def format_main_table(df):
    df_show = df.copy()

    rename_map = {
        "ranking": "Ranking",
        "isapre": "Isapre",
        "codigo": "Código",
        "nombre_plan": "Plan",
        "clinica_preferente": "Clínica preferente",
        "semaforo": "Semáforo",
        "precio_pesos": "Precio ($)",
        "hospitalario_num": "Hospitalario (%)",
        "ambulatorio_num": "Ambulatorio (%)",
        "tope_anual_uf": "Tope anual (UF)",
        "score": "Score",
        "pdf_url": "PDF",
    }

    df_show = df_show.rename(columns=rename_map)

    if "Precio ($)" in df_show.columns:
        df_show["Precio ($)"] = df_show["Precio ($)"].map(lambda x: f"${x:,.0f}")
    if "Hospitalario (%)" in df_show.columns:
        df_show["Hospitalario (%)"] = df_show["Hospitalario (%)"].map(lambda x: f"{x:.0f}%")
    if "Ambulatorio (%)" in df_show.columns:
        df_show["Ambulatorio (%)"] = df_show["Ambulatorio (%)"].map(lambda x: f"{x:.0f}%")
    if "Tope anual (UF)" in df_show.columns:
        df_show["Tope anual (UF)"] = df_show["Tope anual (UF)"].map(lambda x: f"{x:.0f}")
    if "Score" in df_show.columns:
        df_show["Score"] = df_show["Score"].map(lambda x: f"{x:.4f}")

    return df_show


def format_comparator_table(df):
    df_show = df.copy()

    rename_map = {
        "ranking": "Ranking",
        "isapre": "Isapre",
        "codigo": "Código",
        "nombre_plan": "Plan",
        "clinica_preferente": "Clínica preferente",
        "semaforo": "Semáforo",
        "precio_pesos": "Precio ($)",
        "hospitalario_num": "Hospitalario (%)",
        "ambulatorio_num": "Ambulatorio (%)",
        "tope_anual_uf": "Tope anual (UF)",
        "aporte_precio": "Aporte precio",
        "aporte_hospitalario": "Aporte hospitalario",
        "aporte_ambulatorio": "Aporte ambulatorio",
        "aporte_tope": "Aporte tope",
        "penalizacion_presupuesto": "Penalización presupuesto",
        "bonus_maternidad": "Bonus maternidad",
        "score": "Score",
    }

    df_show = df_show.rename(columns=rename_map)

    if "Precio ($)" in df_show.columns:
        df_show["Precio ($)"] = df_show["Precio ($)"].map(lambda x: f"${x:,.0f}")
    if "Hospitalario (%)" in df_show.columns:
        df_show["Hospitalario (%)"] = df_show["Hospitalario (%)"].map(lambda x: f"{x:.0f}%")
    if "Ambulatorio (%)" in df_show.columns:
        df_show["Ambulatorio (%)"] = df_show["Ambulatorio (%)"].map(lambda x: f"{x:.0f}%")
    if "Tope anual (UF)" in df_show.columns:
        df_show["Tope anual (UF)"] = df_show["Tope anual (UF)"].map(lambda x: f"{x:.0f}")

    for col in [
        "Aporte precio",
        "Aporte hospitalario",
        "Aporte ambulatorio",
        "Aporte tope",
        "Penalización presupuesto",
        "Bonus maternidad",
        "Score",
    ]:
        if col in df_show.columns:
            df_show[col] = df_show[col].map(lambda x: f"{x:.4f}")

    return df_show


try:
    df = load_data()

    st.sidebar.header("Filtros de universo")

    isapres = sorted(df["isapre"].dropna().unique().tolist())
    clinicas = sorted(df["clinica_preferente"].dropna().unique().tolist())

    isapre_sel = st.sidebar.selectbox(
        "Isapre",
        options=["Todas"] + isapres,
        index=0
    )

    clinica_sel = st.sidebar.selectbox(
        "Clínica preferente",
        options=["Todas"] + clinicas,
        index=0
    )

    st.sidebar.header("Parámetros del modelo")

    escenario = st.sidebar.selectbox(
        "Escenario",
        list(SCENARIOS.keys()),
        index=0
    )

    pesos_base = SCENARIOS[escenario]

    peso_hospitalario = st.sidebar.slider("Peso hospitalario", 0, 100, pesos_base["hospitalario"])
    peso_ambulatorio = st.sidebar.slider("Peso ambulatorio", 0, 100, pesos_base["ambulatorio"])
    peso_tope = st.sidebar.slider("Peso tope anual", 0, 100, pesos_base["tope_anual"])
    peso_precio = st.sidebar.slider("Peso precio", 0, 100, pesos_base["precio"])

    presupuesto_max = st.sidebar.number_input(
        "Presupuesto máximo ($)",
        min_value=0,
        value=0,
        step=10000
    )

    excluir_fuera_presupuesto = st.sidebar.toggle(
        "Excluir planes fuera de presupuesto",
        value=False
    )

    priorizar_maternidad = st.sidebar.toggle(
        "Priorizar maternidad",
        value=False
    )

    cobertura_hospitalaria_min = st.sidebar.slider(
        "Cobertura hospitalaria mínima (%)", 0, 100, 0
    )
    cobertura_ambulatoria_min = st.sidebar.slider(
        "Cobertura ambulatoria mínima (%)", 0, 100, 0
    )

    top_n = st.sidebar.selectbox("Mostrar top", [3, 5, 10], index=0)

    weights = {
        "hospitalario": peso_hospitalario,
        "ambulatorio": peso_ambulatorio,
        "tope_anual": peso_tope,
        "precio": peso_precio,
    }

    df_filtrado = df.copy()

    if isapre_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["isapre"] == isapre_sel]

    if clinica_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["clinica_preferente"] == clinica_sel]

    df_filtrado = df_filtrado[
        (df_filtrado["hospitalario_num"] >= cobertura_hospitalaria_min) &
        (df_filtrado["ambulatorio_num"] >= cobertura_ambulatoria_min)
    ].copy()

    if excluir_fuera_presupuesto and presupuesto_max > 0:
        df_filtrado = df_filtrado[df_filtrado["precio_pesos"] <= presupuesto_max]

    budget = presupuesto_max if presupuesto_max > 0 else None

    ranking = calculate_score(
        df=df_filtrado,
        weights=weights,
        budget=budget,
        maternity=priorizar_maternidad
    )

    st.success(f"Planes evaluados: {len(ranking)}")

    if len(ranking) == 0:
        st.warning("No hay planes que cumplan los filtros seleccionados.")
    else:
        ranking = ranking.copy()
        ranking["ranking"] = range(1, len(ranking) + 1)
        ranking["semaforo"] = ranking["score"].apply(get_semaforo)
        ranking["pdf_url"] = ranking["codigo"].apply(get_pdf_url)

        columnas_principales = [
            "ranking",
            "isapre",
            "codigo",
            "nombre_plan",
            "clinica_preferente",
            "semaforo",
            "precio_pesos",
            "hospitalario_num",
            "ambulatorio_num",
            "tope_anual_uf",
            "score",
        ]

        top1 = ranking.iloc[0]

        st.info(
            build_recommendation(
                top1=top1,
                escenario=escenario,
                presupuesto_max=presupuesto_max,
                excluir_fuera_presupuesto=excluir_fuera_presupuesto,
                priorizar_maternidad=priorizar_maternidad,
            )
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Mejor plan", top1["nombre_plan"])
            st.metric("Isapre / Clínica", f"{top1['isapre']} / {top1['clinica_preferente']}")

        with col2:
            st.metric("Precio mejor plan", f"${top1['precio_pesos']:,.0f}")
            st.metric("Semáforo", top1["semaforo"])

        with col3:
            st.metric("Hospitalario / Ambulatorio", f"{top1['hospitalario_num']:.0f}% / {top1['ambulatorio_num']:.0f}%")
            st.metric("Tope anual UF", f"{top1['tope_anual_uf']:.0f}")

        st.link_button(
            "📄 Descargar PDF mejor plan",
            get_pdf_url(top1["codigo"]),
            use_container_width=False
        )

        st.subheader(f"Top {top_n} planes")

        top_export = ranking[columnas_principales + ["pdf_url"]].head(top_n).copy()
        top_show = format_main_table(top_export)

        st.data_editor(
            top_show,
            column_config={
                "PDF": st.column_config.LinkColumn(
                    "PDF",
                    display_text="📄 Descargar"
                )
            },
            hide_index=True,
            disabled=True,
            use_container_width=True
        )

        col_top_csv, col_top_xlsx = st.columns(2)
        with col_top_csv:
            st.download_button(
                label=f"Descargar Top {top_n} en CSV",
                data=to_csv_download(top_export),
                file_name=f"top_{top_n}_planes.csv",
                mime="text/csv"
            )
        with col_top_xlsx:
            st.download_button(
                label=f"Descargar Top {top_n} en Excel",
                data=to_excel_download({"Top": top_export}),
                file_name=f"top_{top_n}_planes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.subheader("Ranking completo")

        ranking_export = ranking.copy()
        ranking_show = format_main_table(ranking[columnas_principales].copy())
        st.dataframe(ranking_show, use_container_width=True)

        col_rank_csv, col_rank_xlsx = st.columns(2)
        with col_rank_csv:
            st.download_button(
                label="Descargar ranking completo en CSV",
                data=to_csv_download(ranking_export),
                file_name="ranking_planes_completo.csv",
                mime="text/csv"
            )
        with col_rank_xlsx:
            st.download_button(
                label="Descargar ranking completo en Excel",
                data=to_excel_download({"Ranking": ranking_export}),
                file_name="ranking_planes_completo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.subheader("Desglose del score")

        plan_detalle = st.selectbox(
            "Selecciona un plan para ver su desglose",
            ranking["nombre_plan"].tolist()
        )

        detalle = ranking[ranking["nombre_plan"] == plan_detalle].iloc[0]

        detalle_export = pd.DataFrame({
            "Componente": [
                "Aporte precio",
                "Aporte hospitalario",
                "Aporte ambulatorio",
                "Aporte tope",
                "Penalización presupuesto",
                "Bonus maternidad",
                "Score final",
            ],
            "Valor": [
                detalle["aporte_precio"],
                detalle["aporte_hospitalario"],
                detalle["aporte_ambulatorio"],
                detalle["aporte_tope"],
                detalle["penalizacion_presupuesto"],
                detalle["bonus_maternidad"],
                detalle["score"],
            ]
        })

        detalle_show = detalle_export.copy()
        detalle_show["Valor"] = detalle_show["Valor"].map(lambda x: f"{x:.4f}")

        st.dataframe(detalle_show, use_container_width=True)

        col_det_csv, col_det_xlsx = st.columns(2)
        with col_det_csv:
            st.download_button(
                label="Descargar desglose en CSV",
                data=to_csv_download(detalle_export),
                file_name=f"desglose_{safe_filename(plan_detalle)}.csv",
                mime="text/csv"
            )
        with col_det_xlsx:
            st.download_button(
                label="Descargar desglose en Excel",
                data=to_excel_download({"Desglose": detalle_export}),
                file_name=f"desglose_{safe_filename(plan_detalle)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.subheader("Comparador de planes")

        opciones_default = ranking["nombre_plan"].head(min(3, len(ranking))).tolist()

        planes_comparar = st.multiselect(
            "Selecciona 2 o 3 planes para comparar",
            options=ranking["nombre_plan"].tolist(),
            default=opciones_default
        )

        comparador_export = pd.DataFrame()

        if len(planes_comparar) < 2:
            st.info("Selecciona al menos 2 planes para comparar.")
        else:
            comparador_export = ranking[ranking["nombre_plan"].isin(planes_comparar)].copy()

            comparador = comparador_export[[
                "ranking",
                "isapre",
                "codigo",
                "nombre_plan",
                "clinica_preferente",
                "semaforo",
                "precio_pesos",
                "hospitalario_num",
                "ambulatorio_num",
                "tope_anual_uf",
                "aporte_precio",
                "aporte_hospitalario",
                "aporte_ambulatorio",
                "aporte_tope",
                "penalizacion_presupuesto",
                "bonus_maternidad",
                "score",
            ]].copy()

            comparador = comparador.sort_values("ranking")
            comparador_show = format_comparator_table(comparador)

            st.dataframe(comparador_show, use_container_width=True)

            col_comp_csv, col_comp_xlsx = st.columns(2)
            with col_comp_csv:
                st.download_button(
                    label="Descargar comparador en CSV",
                    data=to_csv_download(comparador_export),
                    file_name="comparador_planes.csv",
                    mime="text/csv"
                )
            with col_comp_xlsx:
                st.download_button(
                    label="Descargar comparador en Excel",
                    data=to_excel_download({"Comparador": comparador_export}),
                    file_name="comparador_planes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        st.subheader("Descarga consolidada")

        excel_consolidado = to_excel_download({
            "Top": top_export,
            "Ranking": ranking_export,
            "Desglose": detalle_export,
            "Comparador": comparador_export,
        })

        st.download_button(
            label="Descargar Excel consolidado",
            data=excel_consolidado,
            file_name="analisis_planes_isapre_consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("Descarga de PDFs de planes")

        ranking_pdf = ranking[["ranking", "isapre", "codigo", "nombre_plan", "clinica_preferente"]].copy()
        ranking_pdf["label_pdf"] = ranking_pdf.apply(
            lambda x: f"{x['ranking']}. [{x['codigo']}] {x['nombre_plan']} | {x['isapre']} | {x['clinica_preferente']}",
            axis=1
        )

        pdf_map = dict(zip(ranking_pdf["label_pdf"], ranking_pdf["codigo"]))

        plan_pdf_sel = st.selectbox(
            "Selecciona un plan para descargar su PDF",
            options=ranking_pdf["label_pdf"].tolist()
        )

        codigo_pdf = pdf_map[plan_pdf_sel]
        plan_pdf_row = ranking[ranking["codigo"] == codigo_pdf].iloc[0]

        col_pdf_1, col_pdf_2 = st.columns(2)

        with col_pdf_1:
            if st.button("Preparar PDF individual"):
                try:
                    pdf_bytes = download_plan_pdf(str(codigo_pdf))
                    st.session_state["pdf_individual_bytes"] = pdf_bytes
                    st.session_state["pdf_individual_name"] = (
                        f"{safe_filename(plan_pdf_row['codigo'])}_{safe_filename(plan_pdf_row['nombre_plan'])}.pdf"
                    )
                    st.success("PDF individual listo para descargar.")
                except Exception as ex:
                    st.error(f"No fue posible descargar el PDF individual: {ex}")

        with col_pdf_2:
            if "pdf_individual_bytes" in st.session_state and "pdf_individual_name" in st.session_state:
                st.download_button(
                    label="Descargar PDF individual",
                    data=st.session_state["pdf_individual_bytes"],
                    file_name=st.session_state["pdf_individual_name"],
                    mime="application/pdf"
                )

        st.markdown("---")
        st.write("### Descarga múltiple de PDFs")

        opciones_pdf_default = ranking_pdf["label_pdf"].head(min(3, len(ranking_pdf))).tolist()

        planes_pdf_multi = st.multiselect(
            "Selecciona planes para descargar PDFs",
            options=ranking_pdf["label_pdf"].tolist(),
            default=opciones_pdf_default
        )

        col_multi_1, col_multi_2 = st.columns(2)

        with col_multi_1:
            if st.button("Preparar ZIP de PDFs"):
                if len(planes_pdf_multi) == 0:
                    st.warning("Selecciona al menos un plan.")
                else:
                    try:
                        pdf_items = []
                        for label in planes_pdf_multi:
                            codigo = pdf_map[label]
                            row = ranking[ranking["codigo"] == codigo].iloc[0]
                            pdf_bytes = download_plan_pdf(str(codigo))
                            filename = f"{safe_filename(row['codigo'])}_{safe_filename(row['nombre_plan'])}.pdf"
                            pdf_items.append((filename, pdf_bytes))

                        zip_bytes = build_zip_from_pdfs(pdf_items)
                        st.session_state["pdf_zip_bytes"] = zip_bytes
                        st.success("ZIP de PDFs listo para descargar.")
                    except Exception as ex:
                        st.error(f"No fue posible preparar el ZIP: {ex}")

        with col_multi_2:
            if "pdf_zip_bytes" in st.session_state:
                st.download_button(
                    label="Descargar ZIP de PDFs",
                    data=st.session_state["pdf_zip_bytes"],
                    file_name="planes_isapre_pdfs.zip",
                    mime="application/zip"
                )

        st.write("### Descargar PDF unido")

        col_merge_1, col_merge_2 = st.columns(2)

        with col_merge_1:
            if st.button("Preparar PDF unido"):
                if len(planes_pdf_multi) == 0:
                    st.warning("Selecciona al menos un plan.")
                else:
                    try:
                        pdf_bytes_list = []
                        for label in planes_pdf_multi:
                            codigo = pdf_map[label]
                            pdf_bytes = download_plan_pdf(str(codigo))
                            pdf_bytes_list.append(pdf_bytes)

                        merged_pdf = merge_pdfs(pdf_bytes_list)
                        st.session_state["pdf_merged_bytes"] = merged_pdf
                        st.success("PDF unido listo para descargar.")
                    except Exception as ex:
                        st.error(f"No fue posible unir los PDFs: {ex}")

        with col_merge_2:
            if "pdf_merged_bytes" in st.session_state:
                st.download_button(
                    label="Descargar PDF unido",
                    data=st.session_state["pdf_merged_bytes"],
                    file_name="planes_isapre_unidos.pdf",
                    mime="application/pdf"
                )

except Exception as e:
    st.error(f"Error en la aplicación: {e}")