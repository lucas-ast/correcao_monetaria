# --- imports ---
import ipeadatapy as ipea
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime

# --- Premissas para correção monetária (simplificadas) ---
conversoes_monetarias = {
    datetime(1970, 1, 1): ('Cruzeiro (Cr$)', 1 / (1000**3 * 2750), 1000**3 * 2750),
    datetime(1986, 3, 1): ('Cruzado (Cz$)', 1 / (1000**2 * 2750), 1000**2 * 2750),
    datetime(1989, 2, 1): ('Cruzado Novo (NCz$)', 1 / (1000 * 2750), 1000 * 2750),
    datetime(1990, 4, 1): ('Cruzeiro (Cr$)', 1 / (1000 * 2750), 1000 * 2750),
    datetime(1993, 8, 1): ('Cruzeiro Real (CR$)', 1 / 2750, 2750),
    datetime(1994, 7, 1): ('Real (R$)', 1, 1),
}


def obter_conversoes(data):
    """Retorna o nome da moeda e os fatores de conversão para a data."""
    for data_corte, conversoes in sorted(conversoes_monetarias.items()):
        if data < data_corte:
            return conversoes
    return conversoes_monetarias[datetime(1994, 7, 1)]


# --- funções para correção monetária ---
def inflacao(periodo, st_write_func):
    """Calcula o fator de inflação acumulado."""
    fator = 1.0
    for data, variacao in periodo.items():
        fator *= (1 + variacao / 100)
        st_write_func(
            f"{data.strftime('%m-%Y')}: "
            f"variação = {variacao:.4f}%   |   fator acumulado = {fator:.6f}"
        )
    return fator


def deflacao(periodo, valor_data_inicial, st_write_func):
    """Calcula o fator de deflação acumulado."""
    fator = 1.0
    for data, variacao in periodo.items():
        fator /= (1 + variacao / 100)
        st_write_func(
            f"{data.strftime('%m-%Y')}: "
            f"variação = {variacao:.4f}%   |   fator deflacionado = {fator:.6f}"
        )
    return fator


def parse_data(user_input):
    """Converte a string de data para objeto datetime."""
    for fmt in ("%Y-%m", "%m-%Y"):
        try:
            return datetime.strptime(user_input, fmt)
        except ValueError:
            pass
    raise ValueError("Formato inválido. Use AAAA-MM ou MM-AAAA.")


# --- Layout do Streamlit ---
st.title("Calculadora de Correção Monetária")

# Widgets para entrada de dados do usuário
data_inicial_str = st.text_input("Data inicial (AAAA-MM ou MM-AAAA):", "1980-01")
data_final_str = st.text_input("Data final (AAAA-MM ou MM-AAAA):", "2025-08")
valor = st.number_input("Valor a ser corrigido:", value=100.0)

# Botão para executar o cálculo
if st.button("Calcular"):
    try:
        data_inicial = parse_data(data_inicial_str)
        data_final = parse_data(data_final_str)

        st.subheader("Buscando dados...")
        ipca = ipea.timeseries("PRECOS12_IPCAG12")

        st.subheader("Resultados:")

        # Filtro de período
        inicio = min(data_inicial, data_final)
        fim = max(data_inicial, data_final)
        periodo = ipca.loc[inicio.strftime("%Y-%m"):fim.strftime("%Y-%m"), "VALUE ((% a.m.))"]

        if data_inicial < data_final:  # Inflação
            nome_moeda, _, fator_conversao = obter_conversoes(data_inicial)

            st.write(f"Correção de {nome_moeda} para Real (Inflação)")
            st.write("Fator de correção acumulado (mensal):")
            fator = inflacao(periodo, st.write)
            valor_inflacao = (fator - 1) * 100
            valor_corrigido = valor * fator * fator_conversao

            st.write(f"Fator acumulado no período: {round(fator, 6)}")
            st.write(f"Inflação no período foi de: {round(valor_inflacao, 3)}%")
            st.write(f"Valor nominal: {nome_moeda} {valor}")
            st.metric("Valor corrigido", f"R$ {round(valor_corrigido, 2)}")

        else:  # Deflação
            nome_moeda, fator_conversao, _ = obter_conversoes(data_final)
            valor_data_final_ipca = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"]
            
            st.write(f"Correção de Real para {nome_moeda} (Deflação)")
            st.write("Fator de deflação acumulado (mensal):")
            fator = deflacao(periodo, valor_data_final_ipca, st.write)
            valor_deflacao = (1 - fator) * 100
            valor_corrigido = valor * fator * fator_conversao

            st.write(f"Fator deflacionado no periodo: {round(fator, 6)}")
            st.write(f"Deflação no período foi de: {round(valor_deflacao, 3)}%")
            st.write(f"Valor nominal: R$ {valor}")
            st.metric("Valor deflacionado", f"{nome_moeda} {round(valor_corrigido, 2)}")

        # Gráfico (sempre exibe no final do script)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(periodo.index, periodo.values)
        ax.set_title("Variação Mensal do IPCA (%)")
        ax.set_xlabel("Período")
        ax.set_ylabel("Variação (%)")
        ax.grid(True)
        st.pyplot(fig)

    except ValueError as e:
        st.error(str(e))
    except KeyError as e:
        st.error(f"Erro: Uma das datas está fora do período da série do IPCA. Por favor, ajuste as datas.")