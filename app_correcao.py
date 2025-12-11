# --- imports ---
import ipeadatapy as ipea
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import faicons as fa
import io

from datetime import datetime
from shinywidgets import output_widget, render_plotly
from shiny import App, reactive, render, ui

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

# --- Funções globais ---
# função para definir o fator histórico da moeda antiga para real
def fator_historico(data):
    if data < data_corte_cruzeiro:
        return fator_cruzeiro_real
    elif data < data_corte_cruzado:
        return fator_cruzado_real
    elif data < data_corte_cruzadonovo:
        return fator_cruzadonovo_real
    elif data < data_corte_cruzeiro2:
        return fator_cruzeiro2_real
    elif data < data_corte_cruzeiroreal:
        return fator_cruzeiroreal_real
    else:
        return 1.0  # já em real

# função para definir o fator histórico do real para  moeda antiga
def fator_historico_real_moedaantiga(data):
    if data < data_corte_cruzeiro:
        return fator_real_cruzeiro
    elif data < data_corte_cruzado:
        return fator_real_cruzado
    elif data < data_corte_cruzadonovo:
        return fator_real_cruzadonovo
    elif data < data_corte_cruzeiro2:
        return fator_real_cruzeiro2
    elif data < data_corte_cruzeiroreal:
        return fator_real_cruzeiroreal
    else:
        return 1.0  # já em real

# função para fazer a correção monetária considerando a inflação
fator_acumulado = {}

def inflacao(periodo):
    fator = 1.0
    for data, variacao in periodo.items():
        fator = fator * (1 + variacao/100)
    return fator

# função para fazer a correção monetária considerando uma deflação
def deflacao(periodo, valor_data_inicial):
    denominador = 1.0
    fator_inicial = (1 + valor_data_inicial/100 ) 
    for data, variacao in periodo.items():
        denominador = (1 + variacao/100) * denominador
        fator = fator_inicial / denominador
    return fator


# --- lógica para ler e guardar os dados dos índices de correção monetária do ipeadata ---
# dicionário de índices de correção monetária
indices = {
    "IPCA": "PRECOS12_IPCAG12",
    "IGP_M": "IGP12_IGPMG12",
    "IGP_DI": "IGP12_IGPDIG12",
    "SELIC_OVER": "BM12_TJOVER12",
    "INPC": "PRECOS12_INPCBR12",
    "IPC_BR": "IGP12_IPCG12",
    "IPC_FIPE": "FIPE12_FIPE0001"
}

# criando um dicionário para amarzenar os dataframe de cada índice inflacionário
dados_indices = {}

# carregando os índices inflacionários
for nome, codigo in indices.items():
    dados_indices[nome] = ipea.timeseries(codigo)


# --- 1. UI (User Interface) ---
app_ui = ui.page_sidebar( #sidebar = construção da página do User Interface
    ui.sidebar(
        ui.h3("Painel de Controle"),
        ui.input_select(
            id="indice_codigo",
            label="selecione o índice inflacionário:",
            choices=list(indices.keys()),
        ),

        ui.input_date(id="data_inicial_str", label="data inicial:", value="2025-01-01", format="mm-yyyy"),
        ui.input_date(id="data_final_str", label="data final:", value="2025-02-01", format="mm-yyyy"),
        ui.input_numeric(id="valor_nominal", label="valor a ser corrigido", value=100, min=0),
        ui.input_action_button(id="button_calcular", label="Calcular"),
        

        ui.h5("Dados Brutos:"),
        # IPCA
        ui.download_button(
            id="download_ipca",
            label=ui.span(fa.icon_svg("download", "solid"), "IPCA"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),
        
        # IGP-M
        ui.download_button(
            id="download_igpm",
            label=ui.span(fa.icon_svg("download", "solid"), "IGP-M"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),

        # IGP-DI
        ui.download_button(
            id="download_igpdi",
            label=ui.span(fa.icon_svg("download", "solid"), "IGP-DI"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),
    
        # SELIC-OVER
        ui.download_button(
            id="download_selicover",
            label=ui.span(fa.icon_svg("download", "solid"), "SELIC-OVER"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),

        # INPC
        ui.download_button(
            id="download_inpc",
            label=ui.span(fa.icon_svg("download", "solid"), "INPC"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),

        # IPC-BR
        ui.download_button(
            id="download_ipcbr",
            label=ui.span(fa.icon_svg("download", "solid"), "IPC-BR"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),

        # IPC-FIPE
        ui.download_button(
            id="download_ipcfipe",
            label=ui.span(fa.icon_svg("download", "solid"), "IPC-FIPE"),
            class_="btn-sm",
            style="margin-bottom: 5px; margin-right: 5px;"
        ),

         # Fonte dos dados: Ipeadata https://www.ipeadata.gov.br/Default.aspx
        ui.a(
            ui.p(
                "Fonte: ",
                ui.a("Ipeadata", href="https://www.ipeadata.gov.br/Default.aspx", target="_blank")
            )
        )      
    ),

    # ui.layout_columns = refe-se a parte do conteúdo princiapl, onde os outputs que você quer por
    # elaboração dos KPIs (Key Perfomance Indicator)
    ui.layout_columns(
        ui.value_box("Valor Nominal", ui.output_ui("kpi_valor_nominal"), showcase=""),
        ui.value_box("Inflação no Período", ui.output_ui("kpi_inflacao_periodo"), showcase=""),
        ui.value_box("Fator Acumulado", ui.output_ui("kpi_fator_acumulado"), showcase=""),
        ui.value_box("Valor Corrigido", ui.output_ui("kpi_valor_corrigido"), showcase=""),
        fill=False, # altura normal (natural) do conteúdo, se fosse True: força os itens a "esticar" para ocupar o máximo de altura
    ),

    # Conteúdo principal: tabela à esquerda e gráfico à direita (col widths)
    ui.layout_columns(
        ui.card(
            ui.card_header(
                ui.span("Resultados da Correção"),
                    # Botão de download com ícone e classe "btn-sm"
                    ui.download_button(
                        "download_excel",
                        label=ui.span(fa.icon_svg("file-excel", "regular")), # Ícone de Excel
                        class_="btn-sm float-end", # btn-sm: pequeno; float-end: alinha à direita
                        style="margin-left: 10px;"
                    ),
                    class_="d-flex justify-content-between align-items-center"
                ), 
            ui.output_data_frame("df_result"), 
            full_screen=True
        ),
        ui.card(ui.card_header("Gráfico da Variação Mensal"), output_widget("variacao_plot"), full_screen=True),
        col_widths=[6, 6],
    ),

    ui.card( #Este trecho cria um card independente, ou seja, uma seção (caixa) isolada na página
        ui.card_header("Comparação entre Índices"),
        output_widget("comparacao_plot"),
        full_screen=True
    ),

     # --- LINKS SOCIAIS NA PARTE INFERIOR ---
    ui.div(
        ui.span("Desenvolvido por Lucas Magalhães Ast | ", style="margin-right: 8px;"),

        ui.a(
            fa.icon_svg("github", "brands"), # Ícone do GitHub
            href="https://github.com/lucas-ast",
            target="_blank",
            style="text-decoration: none; color: #333333;"
        ),
        ui.a(
            fa.icon_svg("linkedin", "brands"), # ìcone do Linkedin
            href="https://www.linkedin.com/in/lucas-magalhaes-ast",
            target="_blank",
            style="text-decoration: none; color: #0077b5;"
        ),
        ui.a(
            fa.icon_svg("folder-open"),
            href="https://lucas-magalhaes.quarto.pub/portfolio/",
            target="_blank",
            style="text-decoration: none; color: #007bc2;"
        ),
        
        # Estilos do Container Interno: Centraliza e usa pouco padding
        class_="d-flex justify-content-center align-items-center", 
        style="padding: 0; line-height: 0.8",

    ),

    open="desktop",

    # definição geral da página
    title="Calculadora - Correção Monetária",
    fillable=True, # isso ativa o comportamento responsivo/fluido, ou seja: Os elementos internos se ajustam ao tamanho da tela; O espaço sobrando pode ser utilizado pelo conteúdo; Em telas menores, o layout reorganiza.
)

# --- 2. Server ---
def server(input, output, session):

    # função para trabalhar com os inputs do tipo data
    @reactive.Calc
    def datas_convertidas():
        data_inicial = input.data_inicial_str()
        data_final = input.data_final_str()

        if data_inicial is None or data_final is None:
            return None

        # Formatar date para datetime
        data_inicial_fmt = datetime.combine(data_inicial, datetime.min.time())
        data_final_fmt = datetime.combine(data_final, datetime.min.time())

        # Padroniza sempre para o "dd" seja "01"
        data_inicial_fmt = data_inicial_fmt.replace(day=1)
        data_final_fmt = data_final_fmt.replace(day=1)

        # garantir a ordem(menor, maior)
        inicio = min(data_inicial_fmt, data_final_fmt) # garantir qual é a menor data
        fim = max(data_inicial_fmt, data_final_fmt) # garantirr qual é a maior data
        return data_inicial_fmt, data_final_fmt, inicio, fim

    # aplicação do período no índice escolhido no input.
    @reactive.Calc
    def dados_periodo():
        indice_escolhido = input.indice_codigo()
        indice_df = dados_indices[indice_escolhido]
        data_inicial, data_final, inicio, fim = datas_convertidas()
        periodo = indice_df.loc[inicio:fim, "VALUE ((% a.m.))"]
        # valida se as datas existem na série
        if data_inicial not in indice_df.index or data_final not in indice_df.index:
            data_inicial_valida = min(indice_df.index)
            data_final_valida = max(indice_df.index)
            raise ValueError(
                f"As datas digitadas não estão no período do {indice_escolhido}. "
                f"Use entre {data_inicial_valida} até {data_final_valida}."
            )
        return periodo, indice_df

    # --- MOTOR DE CÁLCULO ---
    # o data frame gerado aqui é oq será usado para os outputs
    @reactive.Calc
    @reactive.event(input.button_calcular)
    def resultados():
        valor = input.valor_nominal()
        if valor is None:
            return None

        dados_periodo_result = dados_periodo()
        if dados_periodo_result is None:
            return None
        dados_filtrados, indice_df = dados_periodo_result
        data_inicial_fmt, data_final_fmt, inicio, fim = datas_convertidas()

        # DataFrame operacional (numérico)
        df_result = pd.DataFrame(dados_filtrados).copy()
        # insere coluna date (string formatada) como primeira coluna
        df_result.insert(0, "date", df_result.index.strftime("%m-%Y"))

        # inflação (data_inicial <= data_final)
        if data_inicial_fmt <= data_final_fmt:
            fator = 1.0
            fatores_acumulados = []

            for mes, variacao in df_result["VALUE ((% a.m.))"].items(): # mes nesse caso é o index, o items() retorna o valor da variação de cada index.
                fator = fator * (1 + variacao / 100)
                fatores_acumulados.append(fator)

            df_result["fator_acumulado"] = fatores_acumulados # criando a coluna "fator_acumulado"

            # data frame final
            df_result["valor_corrigido"] = valor * df_result["fator_acumulado"] * fator_historico(data_inicial_fmt)# criando a coluna "valor_corrigido"


        # deflação (data_inicial > data_final)
        else:
            fator = 1.0
            fatores_acumulados = []

            for mes, variacao in df_result["VALUE ((% a.m.))"].items():
                fator = fator * (1 + variacao / 100)
                fator_deflacionado = 1 / fator
                fatores_acumulados.append(fator_deflacionado)


            df_result["fator_acumulado"] = fatores_acumulados
            df_result["valor_corrigido"] = valor * df_result["fator_acumulado"] * fator_historico_real_moedaantiga(data_final_fmt)

        # renomeia coluna (mantendo colunas numéricas)
        df_result.rename(columns={"VALUE ((% a.m.))": "variacao_mensal"}, inplace=True)

        # garante tipos numéricos (float)
        df_result["variacao_mensal"] = df_result["variacao_mensal"].astype(float)
        df_result["fator_acumulado"] = df_result["fator_acumulado"].astype(float)
        df_result["valor_corrigido"] = df_result["valor_corrigido"].astype(float)

        return df_result
    

    # --- DOWNLOAD DAS SÉRIES DO IPEADATA E DO DF_RESULT ---
    # Função para baixar o df_result
    @session.download(filename=lambda: "serie_indice.xlsx")
    def download_excel():
        df = resultados() # df_result original
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer

    # Função para baixar as séries brutas do ipeadata
    #IPCA
    @session.download(filename=lambda: "ipca_ipeadata.xlsx")
    def download_ipca():
        df_ipca = dados_indices["IPCA"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_ipca.to_excel(buffer)
        buffer.seek(0)
        return buffer
    
    # IGP-M
    @session.download(filename=lambda: "igpm_ipeadata.xlsx")
    def download_igpm():
        df_igpm= dados_indices["IGP_M"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_igpm.to_excel(buffer)
        buffer.seek(0)
        return buffer
    
    # IGP-DI
    @session.download(filename=lambda: "igpdi_ipeadata.xlsx")
    def download_igpdi():
        df_igpdi = dados_indices["IGP_DI"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_igpdi.to_excel(buffer)
        buffer.seek(0)
        return buffer

    # SELIC-OVER
    @session.download(filename=lambda: "selicover_ipeadata.xlsx")
    def download_selicover():
        df_selicover = dados_indices["SELIC_OVER"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_selicover.to_excel(buffer)
        buffer.seek(0)
        return buffer
    
    # INPC
    @session.download(filename=lambda: "inpc_ipeadata.xlsx")
    def download_inpc():
        df_inpc = dados_indices["INPC"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_inpc.to_excel(buffer)
        buffer.seek(0)
        return buffer
    
    # IPC-BR
    @session.download(filename=lambda: "ipcbr_ipeadata.xlsx")
    def download_ipcbr():
        df_ipcbr = dados_indices["IPC_BR"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_ipcbr.to_excel(buffer)
        buffer.seek(0)
        return buffer
    
    # IPC-FIPE
    @session.download(filename=lambda: "ipcfipe_ipeadata.xlsx")
    def download_ipcfipe():
        df_ipcfipe = dados_indices["IPC_FIPE"]
        buffer = io.BytesIO()  # O buffer é uma memória temporária onde exportamos o arquivo antes de enviá-lo para download.
        df_ipcfipe.to_excel(buffer)
        buffer.seek(0)
        return buffer


    # --- DATA FRAME COM TODOS OS ÍNDICES PARA FAZER O GRÁFICO COMPARATIVO ---
    @reactive.Calc
    @reactive.event(input.button_calcular)
    # função para criar um data frame com todos os índices 
    def todos_indices_periodo():
        data_inicial, data_final, inicio, fim = datas_convertidas() # puxo a função das datas convertidas

        dfs = []
        for nome, df in dados_indices.items(): # localizo o nome do índice e o data frame do índice no dicionário dados_índices
            p = df.loc[inicio:fim, "VALUE ((% a.m.))"].copy() # pego o intervalo do período e pego somente a coluna de variação mensal, o loop faz para todos os índices.
            p = pd.DataFrame(p) # transformo em um data frame
            p = p.rename(columns={"VALUE ((% a.m.))": "variacao_mensal"})  # renomeio a coluna de variação mensal.
            p["indice"] = nome #crio uma coluna com o nome de "indice"
            p["date"] = p.index.strftime("%Y-%m") # crio uma coluna com a data formatada.
            dfs.append(p) # guarda esse pedaço do DataFrame dentro da lista dfs.

        return pd.concat(dfs, axis=0) # o "concat" concatena todos os dataframe verticalmente



    # --- KPIs (render.ui usado dentro de value_box) ---
    @output
    @render.ui
    @reactive.event(input.button_calcular)
    def kpi_valor_nominal():
        v = input.valor_nominal()
        data_inicial = input.data_inicial_str()
        data_final = input.data_final_str()
        data_inicial_fmt = datetime.combine(data_inicial, datetime.min.time())
        data_final_fmt = datetime.combine(data_final, datetime.min.time())
        # Padroniza sempre para o "dd" seja "01"
        data_inicial_fmt = data_inicial_fmt.replace(day=1)
        data_final_fmt = data_final_fmt.replace(day=1)

        # teste lógico para pegar o símbolo monetário do valor nominal.
        if v is None:
            return "—"
        elif data_inicial_fmt < data_corte_cruzeiro:
            return f"Cr$ {v:,.2f}"
        elif data_inicial_fmt < data_corte_cruzado:
            return f"Cz$ {v:,.2f}"
        elif data_inicial_fmt < data_corte_cruzadonovo:
            return f"NCz$ {v:,.2f}"
        elif data_inicial_fmt < data_corte_cruzeiro2:
            return f"Cr$ {v:,.2f}"
        elif data_inicial_fmt < data_corte_cruzeiroreal:
            return f"CR$ {v:,.2f}"
        else:
            return f"R$ {v:,.2f}"


    @output
    @render.ui
    @reactive.event(input.button_calcular)
    def kpi_fator_acumulado():
        df = resultados()
        if df is None or df.empty:
            return "—"
        # pega o último fator acumulado
        last = df["fator_acumulado"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
        return f"{last:,.6f}"

    @output
    @render.ui
    @reactive.event(input.button_calcular)
    def kpi_inflacao_periodo():
        df = resultados()
        if df is None or df.empty:
            return "—"
        last = df["fator_acumulado"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
        # se inflação (início <= fim), inflação% = (fator - 1) * 100
        # se deflação (início > fim), usamos (1 - fator)*100 para indicar deflação
        data_inicial_fmt, data_final_fmt, inicio, fim = datas_convertidas()
        if data_inicial_fmt <= data_final_fmt:
            inf = (last - 1) * 100
            return f"{inf:,.2f} %"
        else:
            inf = (1 - last) * 100
            return f"-{inf:,.2f} %"

    @output
    @render.ui
    @reactive.event(input.button_calcular)
    def kpi_valor_corrigido():
        df = resultados()
        data_inicial = input.data_inicial_str()
        data_final = input.data_final_str()
        data_inicial_fmt = datetime.combine(data_inicial, datetime.min.time())
        data_final_fmt = datetime.combine(data_final, datetime.min.time())
        # Padroniza sempre para o "dd" seja "01"
        data_inicial_fmt = data_inicial_fmt.replace(day=1)
        data_final_fmt = data_final_fmt.replace(day=1)

        if df is None or df.empty:
            return "—"
        elif data_final_fmt < data_corte_cruzeiro:
            last = df["valor_corrigido"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
            return f"Cr$ {last:,.2f}"
        elif data_final_fmt < data_corte_cruzado:
            last = df["valor_corrigido"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
            return f"Cz$ {last:,.2f}"
        elif data_final_fmt < data_corte_cruzadonovo:
            last = df["valor_corrigido"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
            return f"NCz$ {last:,.2f}"
        elif data_final_fmt < data_corte_cruzeiro2:
            last = df["valor_corrigido"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
            return f"Cr$ {last:,.2f}"
        elif data_final_fmt < data_corte_cruzeiroreal:
            last = df["valor_corrigido"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
            return f"CR$ {last:,.2f}"
        else:
            last = df["valor_corrigido"].iloc[-1] # .iloc[-1] é para acessar a última linha do DataFrame, ou seja, posição negativa significa contar a partir do final.
            return f"R$ {last:,.2f}"

    # --- Tabela: exibimos uma versão formatada para display (strings) ---
    @output
    @render.data_frame
    @reactive.event(input.button_calcular)
    def df_result():
        df = resultados()
        data_inicial = input.data_inicial_str()
        data_final = input.data_final_str()
        data_inicial_fmt = datetime.combine(data_inicial, datetime.min.time())
        data_final_fmt = datetime.combine(data_final, datetime.min.time())
        # Padroniza sempre para o "dd" seja "01"
        data_inicial_fmt = data_inicial_fmt.replace(day=1)
        data_final_fmt = data_final_fmt.replace(day=1)

        if df is None:
            return pd.DataFrame({"Aviso": ["Verifique inputs e datas"]})
        # cria cópia para exibição (formatada)
        display_df = df.copy()
        # formata colunas numéricas para visual (mantendo df original em resultados())
        display_df["variacao_mensal"] = display_df["variacao_mensal"].map(lambda x: f"{x:,.2f}")
        display_df["fator_acumulado"] = display_df["fator_acumulado"].map(lambda x: f"{x:,.6f}")

        # teste lógico quando for deflação para colocar o símbolo da moeda de forma correta.
        if data_final_fmt < data_corte_cruzeiro:
            display_df["valor_corrigido"] = display_df["valor_corrigido"].map(lambda x: f"Cr$ {x:,.2f}")
        elif data_final_fmt < data_corte_cruzado:
            display_df["valor_corrigido"] = display_df["valor_corrigido"].map(lambda x: f"Cz$ {x:,.2f}")
        elif data_final_fmt < data_corte_cruzadonovo:
            display_df["valor_corrigido"] = display_df["valor_corrigido"].map(lambda x: f"NCz$ {x:,.2f}")
        elif data_final_fmt < data_corte_cruzeiro2:
            display_df["valor_corrigido"] = display_df["valor_corrigido"].map(lambda x: f"Cr$ {x:,.2f}")
        elif data_final_fmt < data_corte_cruzeiroreal:
            display_df["valor_corrigido"] = display_df["valor_corrigido"].map(lambda x: f"CR$ {x:,.2f}")
        else:
            display_df["valor_corrigido"] = display_df["valor_corrigido"].map(lambda x: f"R$ {x:,.2f}")

        
        # organiza as ordens das colunas
        display_df = display_df[["date", "variacao_mensal", "fator_acumulado", "valor_corrigido"]]
        
        return render.DataGrid(display_df)

    # --- Gráfico: usa os valores numéricos de resultados() ---
    @output
    @render_plotly
    def variacao_plot():
        df = resultados()
        if df is None or df.empty:
            return None
    
        fig = px.line(
            df,
            x=df["date"],
            y=df["variacao_mensal"],
            markers=True,
            title=""
        )
        fig.update_layout(
            xaxis_title="Mês/Ano",
            yaxis_title="Variação (%)",
            hovermode="x unified"
        )
        return fig

    
    @output
    @render_plotly
    def comparacao_plot():
        df = todos_indices_periodo()
        if df is None or df.empty:
            return None

        fig = px.line(
            df,
            x="date",
            y="variacao_mensal",
            color="indice",
            markers=True,
            title=""
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified",
            xaxis_title="Mês/Ano",
            yaxis_title="Variação Mensal (%)"
        )
        return fig


# fim do server
app  = App(app_ui, server)