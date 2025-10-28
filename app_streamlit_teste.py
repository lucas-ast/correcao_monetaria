# -*- coding: utf-8 -*-
# Dashboard de índices econômicos brasileiros
# Autor: Lucas Magalhães

import streamlit as st
import pandas as pd
import altair as alt
import ipeadatapy as ipea

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Índices Econômicos",
    page_icon=":bar_chart:",
    layout="wide",
)

"""
# :bar_chart: Dashboard de Índices Econômicos Brasileiros

Compare a evolução de diferentes índices de inflação, juros e preços ao longo do tempo.
"""

# --- Dicionário de índices disponíveis ---
indices = {
    "IPCA": "PRECOS12_IPCAG12",
    "IGP-M": "IGP12_IGPMG12",
    "INPC": "PRECOS12_INPCBR12",
    "SELIC (Over)": "BM12_TJOVER12",
    "IPC-FIPE": "FIPE12_FIPE0001",
    "IGP-DI": "IGP12_IGPDIG12",
}

DEFAULT_INDICES = ["IPCA", "IGP-M", "INPC"]

# --- Função para carregar séries ---
@st.cache_data(show_spinner=True)
def carregar_series(indices):
    dados = {}
    for nome, codigo in indices.items():
        try:
            serie = ipea.timeseries(codigo)
            serie = serie.rename(columns={"VALUE ((% a.m.))": "valor"})
            serie = serie[["valor"]].dropna()
            dados[nome] = serie
        except Exception as e:
            st.warning(f"Erro ao carregar {nome}: {e}")
    return dados

dados_indices = carregar_series(indices)

# --- Seletor de índices ---
indices_escolhidos = st.multiselect(
    "Escolha os índices para comparar:",
    options=list(indices.keys()),
    default=DEFAULT_INDICES,
)

if not indices_escolhidos:
    st.info("Selecione ao menos um índice para continuar.")
    st.stop()

# --- Filtro de datas ---
todas_datas = pd.concat([dados_indices[i] for i in indices_escolhidos]).index
data_min = todas_datas.min().to_pydatetime()
data_max = todas_datas.max().to_pydatetime()

periodo = st.slider(
    "Selecione o período de análise:",
    min_value=data_min,
    max_value=data_max,
    value=(data_min, data_max),
    format="MM/YYYY"
)

# --- Preparar dados para gráfico ---
df_comb = pd.DataFrame()
for nome in indices_escolhidos:
    serie = dados_indices[nome].loc[periodo[0]:periodo[1]]
    serie["Índice"] = nome
    df_comb = pd.concat([df_comb, serie])

# --- Normalizar as séries para comparação ---
df_comb["valor_norm"] = df_comb.groupby("Índice")["valor"].apply(
    lambda x: x / x.iloc[0]
)

# --- Gráfico de comparação ---
st.subheader("📈 Evolução comparativa (valores normalizados)")
chart = (
    alt.Chart(df_comb.reset_index())
    .mark_line()
    .encode(
        x=alt.X("DATE:T", title="Data"),
        y=alt.Y("valor_norm:Q", title="Valor Normalizado"),
        color="Índice:N",
        tooltip=["DATE:T", "Índice:N", "valor:Q"]
    )
    .properties(height=400)
)
st.altair_chart(chart, use_container_width=True)

# --- Estatísticas simples ---
st.subheader("📊 Estatísticas do período selecionado")
for nome in indices_escolhidos:
    serie = dados_indices[nome].loc[periodo[0]:periodo[1]]
    variacao = ((serie.iloc[-1]["valor"] / serie.iloc[0]["valor"]) - 1) * 100
    st.metric(nome, f"{variacao:.2f}%", delta_color="inverse")

# --- Mostrar dados brutos ---
st.subheader("📑 Dados brutos")
st.dataframe(df_comb.reset_index().rename(columns={"DATE": "Data"}))

# ============================================================
# 💰 CORREÇÃO MONETÁRIA (NOVA SEÇÃO)
# ============================================================

import ipeadatapy as ipea
from datetime import datetime

st.divider()
st.header(":money_with_wings: Correção Monetária")

# --- dicionário com os códigos do IPEA ---
indices = {
    "IPCA": "PRECOS12_IPCAG12",
    "IGP-M": "IGP12_IGPMG12",
    "IGP-DI": "IGP12_IGPDIG12",
    "INPC": "PRECOS12_INPCBR12",
    "IPC-FIPE": "FIPE12_FIPE0001",
    "SELIC (Over)": "BM12_TJOVER12",
}

# --- cache dos dados para não recarregar sempre ---
@st.cache_resource(show_spinner=False)
def carregar_indices():
    dados = {}
    for nome, codigo in indices.items():
        try:
            dados[nome] = ipea.timeseries(codigo)
        except Exception as e:
            st.warning(f"Erro ao carregar {nome}: {e}")
    return dados

dados_indices = carregar_indices()

# --- seleção de índice ---
indice_escolhido = st.selectbox(
    "Selecione o índice de correção:",
    list(dados_indices.keys())
)

# --- entrada de dados ---
col1, col2, col3 = st.columns(3)
with col1:
    data_inicial = st.text_input("Data inicial (AAAA-MM ou MM-AAAA):")
with col2:
    data_final = st.text_input("Data final (AAAA-MM ou MM-AAAA):")
with col3:
    valor = st.number_input("Valor a corrigir (R$):", min_value=0.0, format="%.2f")

# --- função auxiliar para interpretar data ---
def parse_data(data_str):
    data_str = data_str.strip()
    try:
        if "-" in data_str:
            partes = data_str.split("-")
            if len(partes[0]) == 4:  # formato AAAA-MM
                return datetime.strptime(data_str, "%Y-%m")
            else:  # formato MM-AAAA
                return datetime.strptime(data_str, "%m-%Y")
    except Exception:
        st.error("⚠️ Formato inválido. Use AAAA-MM ou MM-AAAA.")
        return None

# --- botão para calcular ---
if st.button("Calcular correção"):
    if not (data_inicial and data_final and valor > 0):
        st.warning("Por favor, preencha todas as informações.")
        st.stop()

    inicio = parse_data(data_inicial)
    fim = parse_data(data_final)

    if not (inicio and fim):
        st.stop()

    if indice_escolhido not in dados_indices:
        st.error("Índice inválido.")
        st.stop()

    serie = dados_indices[indice_escolhido].copy()
    serie = serie.rename(columns={"VALUE ((% a.m.))": "valor"})
    serie.index = pd.to_datetime(serie.index)

    inicio, fim = sorted([inicio, fim])

    serie_filtrada = serie.loc[inicio.strftime("%Y-%m"):fim.strftime("%Y-%m")]

    if serie_filtrada.empty:
        st.error("Nenhum dado encontrado nesse intervalo.")
        st.stop()

    # cálculo do fator acumulado
    fator = (1 + serie_filtrada["valor"] / 100).prod()
    valor_corrigido = valor * fator

    # resultado
    st.success(f"Valor corrigido de **R$ {valor:,.2f}** para **R$ {valor_corrigido:,.2f}**")
    st.write(f"Variação acumulada: **{(fator - 1) * 100:.2f}%** no período.")

    # gráfico com Altair
    graf = (
        alt.Chart(serie_filtrada.reset_index())
        .mark_line()
        .encode(
            x=alt.X("DATE:T", title="Período"),
            y=alt.Y("valor:Q", title=f"Variação mensal (%) - {indice_escolhido}"),
            tooltip=["DATE", "valor"]
        )
        .properties(title=f"Variação mensal do {indice_escolhido}", height=400)
    )
    st.altair_chart(graf, use_container_width=True)
