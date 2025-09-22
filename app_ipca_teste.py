# --- imports ---
import ipeadatapy as ipea
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime

# --- Premissas para correção monetária considerando as datas ---
# 1970 até fev/1986 -> cruzeiro (Cr$) | cruzeiro para real fator de conversão = 1 / (1000^3 * 2750);
data_corte_cruzeiro = datetime(1986, 3, 1)
fator_cruzeiro_real = 1 / (1000**3 * 2750)
fator_real_cruzeiro = 1000**3 * 2750
# mar/1986 até jan/1989 -> cruzado (Cz$) | cruzado para real fator de conversão = 1 / (1000^2 * 2750);
data_corte_cruzado = datetime(1989, 2, 1)
fator_cruzado_real = 1 / (1000**2 * 2750)
fator_real_cruzado = 1000**2 * 2750
# fev/1989 até mar/1990 -> cruzado novo (NCz$) | cruzado novo para real fator de conversão = 1 / (1000 * 2750);
data_corte_cruzadonovo = datetime(1990, 4, 1)
fator_cruzadonovo_real = 1 / (1000 * 2750)
fator_real_cruzadonovo = 1000 * 2750
# abr/1990 até jul/1993 ->  cruzeiro (Cr$) | cruzeiro para real fator de conversão = 1 / (1000 * 2750);
data_corte_cruzeiro2 = datetime(1993, 8, 1)
fator_cruzeiro2_real = 1 / (1000 * 2750)
fator_real_cruzeiro2 = 1000 * 2750
# ago/1993 até jun/1994 -> cruzeiro real (CR$) | cruzeiro real para real fator de conversão = 1 / 2750;
data_corte_cruzeiroreal = datetime(1994, 7, 1)
fator_cruzeiroreal_real = 1 / 2750
fator_real_cruzeiroreal = 2750
# jul/1994 em diante -> real (R$)


# --- função para converter a data digitada ---
def parse_data(user_input):
    for fmt in ("%Y-%m", "%m-%Y"):
        try:
            return datetime.strptime(user_input, fmt)
        except ValueError:
            pass
    raise ValueError("Formato inválido. Use AAAA-MM ou MM-AAAA.")

# --- função para fazer a correção monetária considerando a inflação ---
def inflacao(periodo):
    fator = 1.0
    for data, variacao in periodo.items():
        fator = fator * (1 + variacao/100)
        print(
            f"{data.strftime('%m-%Y')}: "
            f"variação = {variacao:.4f}%   |   fator acumulado = {fator:.6f}"
        )
    return fator

# --- função para fazer a correção monetária considerando uma deflação ---
def deflacao(periodo, valor_data_inicial):
    denominador = 1.0
    fator_inicial = (1 + valor_data_inicial/100 ) 
    for data, variacao in periodo.items():
        denominador = (1 + variacao/100) * denominador
        fator = fator_inicial / denominador
        print(
            f"{data.strftime('%m-%Y')}: "
            f"variação = {variacao:.4f}%   |   fator deflacionado = {fator:.6f}" 
        )
    return fator

# --- código principal ---
st.title("Calculadora do Lucas") # título streamlit

ipca = ipea.timeseries("PRECOS12_IPCAG12")

# datas válidas na série do IPCA
data_inicial_valida = min(ipca.index).strftime("%m-%Y")
data_final_valida = max(ipca.index).strftime("%m-%Y")

# pedir datas ao usuário
data_inicial = parse_data(input("Digite a data inicial (AAAA-MM ou MM-AAAA): ")) # widget streamlit
data_final   = parse_data(input("Digite a data final (AAAA-MM ou MM-AAAA): ")) # widget streamlit

# pedir o valor a ser corrigido
valor = float(input("Digite o valor a ser corrigido: "))

# garantir que no filtro, a função .loc consiga sempre pegar da menor data até a maior data
inicio = min(data_inicial, data_final)
fim = max(data_inicial, data_final)

# filtrar período (convertendo datetime para string ano-mês)
periodo = ipca.loc[inicio.strftime("%Y-%m"):fim.strftime("%Y-%m"), "VALUE ((% a.m.))"]

# condições para as correções monetárias
if not (data_inicial in ipca.index and data_final in ipca.index):
    print(
        f"As datas digitadas não estão no período do índice IPCA."
        f"\nUtilize as datas entre {data_inicial_valida} até {data_final_valida}."
        f"\nObrigado. Vai corinthians!"
    )
elif data_inicial < data_final and data_inicial < data_corte_cruzeiro: # cruzeiro para real
    print(f"Fator inicial = 1.000000")
    fator = inflacao(periodo)
    valor_inflacao = (fator - 1) * 100
    valor_corrigido = valor * fator * fator_cruzeiro_real
    print(
        f"\nFator acumulado no período: {round(fator, 6)}"
        f"\nInflação no período foi de: {round(valor_inflacao,3)}%"
        f"\nValor nominal: Cr$ {valor}"
        f"\nValor corrigido: R$ {round(valor_corrigido, 2)}"
    )
elif data_inicial < data_final and data_inicial < data_corte_cruzado: # cruzado para real
    print(f"Fator inicial = 1.000000")
    fator = inflacao(periodo)
    valor_inflacao = (fator - 1) * 100
    valor_corrigido = valor * fator * fator_cruzado_real
    print(
        f"\nFator acumulado no período: {round(fator, 6)}"
        f"\nInflação no período foi de: {round(valor_inflacao,3)}%"
        f"\nValor nominal: Cz$ {valor}"
        f"\nValor corrigido: R$ {round(valor_corrigido, 2)}"
    )
elif data_inicial < data_final and data_inicial < data_corte_cruzadonovo: # cruzado novo para real
    print(f"Fator inicial = 1.000000")
    fator = inflacao(periodo)
    valor_inflacao = (fator - 1) * 100
    valor_corrigido = valor * fator * fator_cruzadonovo_real
    print(
        f"\nFator acumulado no período: {round(fator, 6)}"
        f"\nInflação no período foi de: {round(valor_inflacao,3)}%"
        f"\nValor nominal: NCz$ {valor}"
        f"\nValor corrigido: R$ {round(valor_corrigido, 2)}"
    )
elif data_inicial < data_final and data_inicial < data_corte_cruzeiro2: # volta do cruzeiro para real
    print(f"Fator inicial = 1.000000")
    fator = inflacao(periodo)
    valor_inflacao = (fator - 1) * 100
    valor_corrigido = valor * fator * fator_cruzeiro2_real
    print(
        f"\nFator acumulado no período: {round(fator, 6)}"
        f"\nInflação no período foi de: {round(valor_inflacao,3)}%"
        f"\nValor nominal: Cr$ {valor}"
        f"\nValor corrigido: R$ {round(valor_corrigido, 2)}"
    )
elif data_inicial < data_final and data_inicial < data_corte_cruzeiroreal: # cruzeiro real para real
    print(f"Fator inicial = 1.000000")
    fator = inflacao(periodo)
    valor_inflacao = (fator - 1) * 100
    valor_corrigido = valor * fator * fator_cruzeiroreal_real
    print(
        f"\nFator acumulado no período: {round(fator, 6)}"
        f"\nInflação no período foi de: {round(valor_inflacao,3)}%"
        f"\nValor nominal: CR$ {valor}"
        f"\nValor corrigido: R$ {round(valor_corrigido, 2)}"
    )
elif data_inicial < data_final and data_inicial >= data_corte_cruzeiroreal: # apenas correção monetária em real considerando a inflação
    print(f"Fator inicial = 1.000000")
    fator = inflacao(periodo)
    valor_inflacao = (fator - 1) * 100
    valor_corrigido = valor * fator
    print(
        f"\nFator acumulado no período: {round(fator, 6)}"
        f"\nInflação no período foi de: {round(valor_inflacao,3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor corrigido: R$ {round(valor_corrigido, 2)}"
    )
elif data_inicial > data_final and data_final < data_corte_cruzeiro: # real para cruzeiro
    valor_data_inicial = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"].values[0] # como a data final é menor que a data inicial, para fazer o cálculo do fator acumulado na função deflação é necessário utilizar a data final como valor da data inicial
    fator_inicial_deflacao = (1 + valor_data_inicial/100)
    print(f"Fator deflator inicial = {fator_inicial_deflacao:.6f}")
    fator = deflacao(periodo, valor_data_inicial)
    valor_deflacao = (1 - fator)*100
    valor_corrigido = valor * fator * fator_real_cruzeiro
    print(
        f"\nFator deflacionado no periodo: {round(fator, 6)}"
        f"\nDeflação no período foi de: {round(valor_deflacao, 3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor deflacionado: Cr$ {round(valor_corrigido, 2)}"
    )
elif data_inicial > data_final and data_final < data_corte_cruzado: # real para cruzado
    valor_data_inicial = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"].values[0] # como a data final é menor que a data inicial, para fazer o cálculo do fator acumulado na função deflação é necessário utilizar a data final como valor da data inicial
    fator_inicial_deflacao = (1 + valor_data_inicial/100)
    print(f"Fator deflator inicial = {fator_inicial_deflacao:.6f}")
    fator = deflacao(periodo, valor_data_inicial)
    valor_deflacao = (1 - fator)*100
    valor_corrigido = valor * fator * fator_real_cruzado
    print(
        f"\nFator deflacionado no periodo: {round(fator, 6)}"
        f"\nDeflação no período foi de: {round(valor_deflacao, 3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor deflacionado: Cz$ {round(valor_corrigido, 2)}"
    )
elif data_inicial > data_final and data_final < data_corte_cruzadonovo: # real para cruzado novo
    valor_data_inicial = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"].values[0] # como a data final é menor que a data inicial, para fazer o cálculo do fator acumulado na função deflação é necessário utilizar a data final como valor da data inicial
    fator_inicial_deflacao = (1 + valor_data_inicial/100)
    print(f"Fator deflator inicial = {fator_inicial_deflacao:.6f}")
    fator = deflacao(periodo, valor_data_inicial)
    valor_deflacao = (1 - fator)*100
    valor_corrigido = valor * fator * fator_real_cruzadonovo
    print(
        f"\nFator deflacionado no periodo: {round(fator, 6)}"
        f"\nDeflação no período foi de: {round(valor_deflacao, 3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor deflacionado: NCz$ {round(valor_corrigido, 2)}"
    )
elif data_inicial > data_final and data_final < data_corte_cruzeiro2: # real para volta do cruzeiro
    valor_data_inicial = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"].values[0] # como a data final é menor que a data inicial, para fazer o cálculo do fator acumulado na função deflação é necessário utilizar a data final como valor da data inicial
    fator_inicial_deflacao = (1 + valor_data_inicial/100)
    print(f"Fator deflator inicial = {fator_inicial_deflacao:.6f}")
    fator = deflacao(periodo, valor_data_inicial)
    valor_deflacao = (1 - fator)*100
    valor_corrigido = valor * fator * fator_real_cruzeiro2
    print(
        f"\nFator deflacionado no periodo: {round(fator, 6)}"
        f"\nDeflação no período foi de: {round(valor_deflacao, 3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor deflacionado: Cr$ {round(valor_corrigido, 2)}"
    )
elif data_inicial > data_final and data_final < data_corte_cruzeiroreal: # real para cruzeiro real
    valor_data_inicial = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"].values[0] # como a data final é menor que a data inicial, para fazer o cálculo do fator acumulado na função deflação é necessário utilizar a data final como valor da data inicial
    fator_inicial_deflacao = (1 + valor_data_inicial/100)
    print(f"Fator deflator inicial = {fator_inicial_deflacao:.6f}")
    fator = deflacao(periodo, valor_data_inicial)
    valor_deflacao = (1 - fator)*100
    valor_corrigido = valor * fator * fator_real_cruzeiroreal
    print(
        f"\nFator deflacionado no periodo: {round(fator, 6)}"
        f"\nDeflação no período foi de: {round(valor_deflacao, 3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor deflacionado: Cr$ {round(valor_corrigido, 2)}"
    )
elif data_inicial > data_final and data_final >= data_corte_cruzeiroreal: # apenas correção monetária em real considerando a deflação
    valor_data_inicial = ipca.loc[data_final.strftime("%Y-%m"), "VALUE ((% a.m.))"].values[0] # como a data final é menor que a data inicial, para fazer o cálculo do fator acumulado na função deflação é necessário utilizar a data final como valor da data inicial
    fator_inicial_deflacao = (1 + valor_data_inicial/100)
    print(f"Fator deflator inicial = {fator_inicial_deflacao:.6f}")
    fator = deflacao(periodo, valor_data_inicial)
    valor_deflacao = (1 - fator)*100
    valor_corrigido = valor * fator
    print(
        f"\nFator deflacionado no período: {round(fator, 6)}"
        f"\nDeflação no período foi de: {round(valor_deflacao, 3)}%"
        f"\nValor nominal: R$ {valor}"
        f"\nValor deflacionado: R$ {round(valor_corrigido, 2)}"
    )
else:
    print(
        "As datas informadas não se enquadram em nenhum cenário de "
        "conversão ou correção monetária previsto.\n"
        f"Período disponível no IPCA: {data_inicial_valida} a {data_final_valida}.\n"
        "Verifique se:\n"
        " • As datas estão no formato AAAA-MM ou MM-AAAA.\n"
        " • A data inicial e a final estão corretas"
    )
    # ou, se preferir encerrar a execução:
    # raise ValueError("Datas fora do intervalo ou cenário não previsto.")



# --- Gráfico ---
plt.figure(figsize=(10,5))
plt.plot(periodo.index, periodo.values)
plt.title("Variação Mensal do IPCA (%)")
plt.xlabel("Período")
plt.ylabel("Variação (%)")
plt.grid(True)
plt.show()
