# Dashboard: Cantonamento ferroviário da França (SNCF)
# Projeto Integrador 1
# Para rodar: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Cantonamento ferroviário - SNCF", layout="wide")


# ---------------------------------------------------------------
# 1. Carregar os dados (o cache evita reler o Excel a cada clique)
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados():
    caminho = Path(__file__).parent / "cantonamento_tratado.xlsx"
    return pd.read_excel(caminho)


df = carregar_dados()

# Cores de cada família tecnológica
cores = {
    "Sem cantonamento": "gray",
    "Cantonamento telefônico": "orangered",
    "Bloco manual": "gold",
    "Bonde / tram": "brown",
    "Bloco automático": "green",
    "Sinalização de cabine (TVM/ETCS)": "blue",
    "Outro / não especificado": "lightgray",
}

# ---------------------------------------------------------------
# 2. Título
# ---------------------------------------------------------------
st.title("Cantonamento ferroviário da França (SNCF)")
st.write(
    "Cantonamento é o sistema que divide a ferrovia em pedaços para que dois trens "
    "nunca ocupem o mesmo pedaço ao mesmo tempo. Cada linha da base é um **trecho** "
    "da ferrovia que usa uma tecnologia de controle."
)

# ---------------------------------------------------------------
# 3. Filtros (barra lateral)
# ---------------------------------------------------------------
st.sidebar.header("Filtros")

todas_familias = sorted(df["familia_tecnologica"].unique())
familias = st.sidebar.multiselect("Família tecnológica", todas_familias, default=todas_familias)

lgv = st.sidebar.radio("Linha de alta velocidade (LGV)", ["Todas", "Sim", "Não"])

# Aplica os filtros
df_f = df[df["familia_tecnologica"].isin(familias)]
if lgv != "Todas":
    df_f = df_f[df_f["linha_lgv"] == lgv]

# Se não sobrou nenhum trecho, avisa e para
if df_f.empty:
    st.warning("Nenhum trecho encontrado com esses filtros.")
    st.stop()

# ---------------------------------------------------------------
# 4. Números principais
# ---------------------------------------------------------------
total_km = df_f["extensao_km"].sum()
mediana_km = df_f["extensao_km"].median()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Trechos", f"{len(df_f):,}".replace(",", "."))
col2.metric("Linhas férreas", f"{df_f['codigo_linha'].nunique():,}".replace(",", "."))
col3.metric("Quilômetros", f"{round(total_km):,}".replace(",", "."))
col4.metric("Extensão mediana do trecho (km)", f"{mediana_km:.1f}".replace(".", ","))

st.divider()

# ---------------------------------------------------------------
# 5. Gráficos 1 e 2
# ---------------------------------------------------------------
graf1, graf2 = st.columns(2)

# Gráfico 1: qual tecnologia domina?
with graf1:
    st.subheader("Qual tecnologia domina a rede?")

    pct_trechos = df_f["familia_tecnologica"].value_counts() / len(df_f) * 100
    dados1 = pd.DataFrame({
        "Família": pct_trechos.index,
        "% dos trechos": pct_trechos.values,
    }).sort_values("% dos trechos")

    fig1 = px.bar(
        dados1, x="% dos trechos", y="Família", orientation="h",
        text="% dos trechos", color="Família", color_discrete_map=cores,
    )
    fig1.update_traces(texttemplate="%{text:.0f}%")
    fig1.update_layout(showlegend=False, yaxis_title="", xaxis_title="% dos trechos")
    st.plotly_chart(fig1, width="stretch")

# Gráfico 2: trechos x quilômetros
with graf2:
    st.subheader("Trechos x quilômetros")

    if total_km == 0:
        st.info("Os trechos selecionados não têm extensão registrada.")
    else:
        pct_t = df_f["grupo"].value_counts() / len(df_f) * 100
        pct_k = df_f.groupby("grupo")["extensao_km"].sum() / total_km * 100

        tabela = pd.DataFrame({"% dos trechos": pct_t, "% dos km": pct_k}).fillna(0)
        tabela.index.name = "Grupo"
        tabela = tabela.reset_index()
        dados2 = tabela.melt(id_vars="Grupo", var_name="Medida", value_name="Porcentagem")

        fig2 = px.bar(
            dados2, x="Grupo", y="Porcentagem", color="Medida", barmode="group",
            text="Porcentagem",
            color_discrete_map={"% dos trechos": "lightsteelblue", "% dos km": "darkorange"},
            category_orders={"Grupo": ["Bloco automático", "Manual e telefônico",
                                       "Sinalização de cabine", "Outros"]},
        )
        fig2.update_traces(texttemplate="%{text:.0f}%")
        fig2.update_layout(xaxis_title="", yaxis_title="% do total")
        st.plotly_chart(fig2, width="stretch")

# ---------------------------------------------------------------
# 6. Gráficos 3 e 4
# ---------------------------------------------------------------
graf3, graf4 = st.columns(2)

# Gráfico 3: sinalização de cabine e alta velocidade
with graf3:
    st.subheader("Sinalização de cabine e alta velocidade")

    cabine = df_f[df_f["familia_tecnologica"] == "Sinalização de cabine (TVM/ETCS)"]

    if cabine["extensao_km"].sum() == 0:
        st.info("Nenhum trecho de sinalização de cabine com os filtros atuais.")
    else:
        km_lgv = cabine[cabine["linha_lgv"] == "Sim"]["extensao_km"].sum()
        km_outras = cabine[cabine["linha_lgv"] == "Não"]["extensao_km"].sum()

        dados3 = pd.DataFrame({
            "Tipo de linha": ["Alta velocidade (LGV)", "Outras linhas"],
            "Quilômetros": [km_lgv, km_outras],
        })
        fig3 = px.bar(
            dados3, x="Tipo de linha", y="Quilômetros", text="Quilômetros",
            color="Tipo de linha",
            color_discrete_map={"Alta velocidade (LGV)": "royalblue", "Outras linhas": "lightgray"},
        )
        fig3.update_traces(texttemplate="%{text:.0f} km")
        fig3.update_layout(showlegend=False, xaxis_title="")
        st.plotly_chart(fig3, width="stretch")

# Gráfico 4: as linhas mudam de tecnologia?
with graf4:
    st.subheader("As linhas mudam de tecnologia?")

    # Conta as tecnologias de cada linha usando a base completa,
    # para o resultado não mudar quando filtramos por família
    modos_por_linha = df.groupby("codigo_linha")["modo_cantonamento"].nunique()
    modos_por_linha = modos_por_linha[df_f["codigo_linha"].unique()]

    uma = (modos_por_linha == 1).sum()
    varias = (modos_por_linha > 1).sum()

    dados4 = pd.DataFrame({
        "Tipo de linha": ["Uma tecnologia", "Mais de uma tecnologia"],
        "Número de linhas": [uma, varias],
    })
    fig4 = px.bar(
        dados4, x="Tipo de linha", y="Número de linhas", text="Número de linhas",
        color="Tipo de linha",
        color_discrete_map={"Uma tecnologia": "lightgray", "Mais de uma tecnologia": "darkorange"},
    )
    fig4.update_layout(showlegend=False, xaxis_title="")
    st.plotly_chart(fig4, width="stretch")

st.divider()

# ---------------------------------------------------------------
# 7. Mapa
# ---------------------------------------------------------------
st.subheader("Onde estão os trechos?")

fig_mapa = px.scatter_map(
    df_f, lat="lat_centro", lon="lon_centro",
    color="familia_tecnologica", color_discrete_map=cores,
    hover_name="nome_linha", hover_data=["modo_cantonamento", "extensao_km"],
    center={"lat": 46.6, "lon": 2.5}, zoom=4.5, height=600,
)
fig_mapa.update_layout(legend_title_text="Família", margin={"l": 0, "r": 0, "t": 0, "b": 0})
st.plotly_chart(fig_mapa, width="stretch")

# ---------------------------------------------------------------
# 8. Insights e tabela de dados
# ---------------------------------------------------------------
with st.expander("Principais insights da análise exploratória"):
    st.markdown("""
    1. O **bloco automático** domina a rede (cerca de 64% dos trechos).
    2. **Trechos e km contam histórias diferentes:** manual e telefônico são 13% dos trechos, mas 22% dos km.
    3. A **sinalização de cabine** é a tecnologia da alta velocidade (90% dos seus km estão em linhas LGV).
    4. Cerca de **29% das linhas** mudam de tecnologia ao longo do percurso.

    *Esses números valem para a base completa, sem filtros.*
    """)

with st.expander("Ver os dados"):
    st.dataframe(df_f, width="stretch")
