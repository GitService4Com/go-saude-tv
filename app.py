import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import datetime
import time
import os

st.set_page_config(page_title="Go MED SAÚDE", page_icon=":bar_chart:", layout="wide")

# Configurações Globais
CAMINHO_ARQUIVO_IMAGENS = "go_med_saude.jpeg"
CAMINHO_ARQUIVO_VENDAS = "df_vendas.csv"
MESES_ABREVIADOS = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

def carregar_dados(caminho_arquivo):
    try:
        df = pd.read_csv(caminho_arquivo)
        if df.empty:
            st.warning("O arquivo CSV está vazio.")
            return None
        return df
    except FileNotFoundError:
        st.error("Arquivo não encontrado!")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
        return None

def formatar_moeda(valor, simbolo_moeda="R$"):
    if pd.isna(valor):
        return ''
    try:
        return f"{simbolo_moeda} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Valor inválido"
    

def calcular_metricas(df):
    """Calcula métricas de vendas, incluindo o Ticket Médio Geral."""
    total_nf = len(df['NF'].unique()) 
    total_qtd_produto = df['Qtd_Produto'].sum() 
    valor_total_item = df['Valor_Total_Item'].sum()  
    total_custo_compra = df['Total_Custo_Compra'].sum()  
    total_lucro_venda = df['Total_Lucro_Venda_Item'].sum() 


    ticket_medio_geral = valor_total_item / total_nf if total_nf > 0 else 0

    return total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda, ticket_medio_geral

def agrupar_e_somar(df, coluna_agrupamento):
    return df.groupby(coluna_agrupamento).agg(
        {'Valor_Total_Item': 'sum', 'Total_Custo_Compra': 'sum', 'Total_Lucro_Venda_Item': 'sum'}
    ).reset_index()


def ranking_clientes(df, top_n=20,max_len=25):
    """Retorna os top N clientes com maior faturamento total, incluindo o número do ranking."""
    df_clientes = df.groupby('Cliente').agg({'Valor_Total_Item': 'sum'}).reset_index()
    df_clientes = df_clientes.sort_values(by='Valor_Total_Item', ascending=False).head(top_n)
    df_clientes['Ranking'] = range(1, len(df_clientes) + 1)
    df_clientes['Valor_Total_Item'] = df_clientes['Valor_Total_Item'].apply(formatar_moeda)
    df_clientes = df_clientes[['Ranking', 'Cliente', 'Valor_Total_Item']]
    df_clientes['Cliente'] = df_clientes['Cliente'].str[:max_len]
    return df_clientes


def produtos_mais_vendidos(df, top_n=10, ordenar_por='Valor_Total_Item', max_len=30):
    df_agrupado = df.groupby('Descricao_produto')[ordenar_por].sum().reset_index()
    df_ordenado = df_agrupado.sort_values(by=ordenar_por, ascending=False)
    df_ordenado['Descricao_produto'] = df_ordenado['Descricao_produto'].str[:max_len]
    return df_ordenado.head(top_n)

def criar_grafico_barras(df, x, y, title, labels):
    df = df.sort_values(by=y, ascending=False) 
    df = df.iloc[::-1]
    df['Valor_Monetario'] = df['Valor_Total_Item'].apply(formatar_moeda)
    fig = px.bar(df, x=y, y=x,
                 title=title,
                 labels={labels.get(y, y): labels.get(x, x), labels.get(x, x): labels.get(y, y)},
                 color=y,
                 text=df['Valor_Monetario'],
                 template="ggplot2",
                 hover_data={y: False, x: False, 'Valor_Monetario': True},
                 orientation='h')
    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=22, font_family="Arial, sans-serif"),
        textfont=dict(size=28, color='white'),
        textangle=0,
        textposition='inside'
    )
    fig.update_layout(
        yaxis_title=labels.get(x, x),
        xaxis_title=labels.get(y, y),
        showlegend=False,
        height=1100,
        width=700,
        xaxis=dict(tickfont=dict(size=18)),
        yaxis=dict(
            title=dict(
                text=labels.get(x, x),
                font=dict(size=18)
            ),
            tickfont=dict(size=16),
        ),
        title_font=dict(size=40, family="Times New Roman"),
        margin=dict(l=10, r=10)
    )
    return fig

def criar_grafico_vendas_diarias(df, mes, ano):
    df_filtrado = df[(df['Mes'] == mes) & (df['Ano'] == ano)]
    vendas_diarias = df_filtrado.groupby('Dia')['Valor_Total_Item'].sum().reset_index()
    vendas_diarias["Valor_Monetario"] = vendas_diarias["Valor_Total_Item"].apply(formatar_moeda)
    fig = px.bar(
        vendas_diarias, x='Dia', y='Valor_Total_Item',
        title=f'Vendas Diárias em {mes}/{ano}',
        labels={'Dia': 'Dia', 'Valor_Total_Item': 'Valor Total de Venda'},
        color='Valor_Total_Item',
        text=vendas_diarias["Valor_Monetario"],
        template="plotly_white", hover_data={'Valor_Total_Item': False,'Valor_Monetario': True})
    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=22,
            font_family="Arial-bold, sans-serif"), 
            textfont=dict(size=55, color='#ffffff', family="Garamond"),
            textangle=0, textposition='outside', cliponaxis=False)
               
    fig.update_layout(yaxis_title='Valor Total de Venda',
        xaxis_title='Dia',
        showlegend=False, height=1100, 
        xaxis=dict(tickfont=dict(size=18)),
        yaxis=dict(
            title=dict(
                text='Valor Total de Venda',
                font=dict(size=14)
            ),
            tickfont=dict(size=12)
        ),
        title_font=dict(size=60, family="garamond")
    )
    return fig

def exibir_grafico_ticket_medio(df_ticket_medio):
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)

    fig = px.bar(
        df_ticket_medio,
        x="Vendedor",
        y="Ticket_Medio",
        title="Ticket Médio por Vendedor",
        labels={"Ticket_Medio": "Ticket Médio", "Vendedor": "Vendedor"},
        text=df_ticket_medio["Ticket Medio"],
        template="plotly_dark",
        hover_data={"Vendedor": False, "Ticket_Medio": False, 'Ticket Medio': True}
    )

    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=22, font_family="Arial, sans-serif"),
        textfont=dict(size=50, color='#ffffff', family="Arial, sans-serif"),
        textposition='outside',
        cliponaxis=False
    )

    fig.update_layout(
        yaxis_title="Ticket Médio",
        xaxis_title="Vendedor",
        showlegend=False,
        height=1100, width=900,
        xaxis=dict(tickfont=dict(size=28)),
        yaxis=dict(
            title=dict(
                text="Ticket Médio",
                font=dict(size=28)
            ),
            tickfont=dict(size=28),
        ),
        title_font=dict(size=60, family="Times New Roman"),
        bargap=0.1
    )

    return fig

def aplicar_filtros(df, vendedor='Todos', mes=None, ano=None, situacao='Faturada'):
    """Aplica filtros aos dados."""
    df_filtrado = df.copy()
    if ano is None:
        ano = datetime.datetime.now().year
    if mes is None:
        mes = datetime.datetime.now().month
    if vendedor != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['Ano'] == ano]
    if situacao != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['situacao'] == situacao]
    return df_filtrado


def processar_dados_ticket_medio(df):
    df['Data_Emissao'] = pd.to_datetime(df['Data_Emissao'], format='mixed', dayfirst=True)
    colunas_nf_unicas = ['NF', 'Data_Emissao', 'Vendedor', 'Valor_Total_Nota', 'Mes', 'Ano', 'situacao']
    df_nf_unicas = df.drop_duplicates(subset='NF')[colunas_nf_unicas].copy()
    df_nf_unicas = df_nf_unicas[df_nf_unicas['situacao'] == 'Faturada']

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    df_nf_unicas = aplicar_filtros(df_nf_unicas, mes=mes_atual, ano=ano_atual)

    df_ticket_medio = df_nf_unicas.groupby('Vendedor')['Valor_Total_Nota'].mean().reset_index(name='Ticket_Medio')
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda) 
    
    return df_ticket_medio

def criar_grafico_pizza_vendas_linha(df):
    """Cria um gráfico de pizza mostrando as vendas por linha de produto."""
    df_linha = df.groupby('Linha')['Valor_Total_Item'].sum().reset_index()
    fig = px.pie(df_linha, values='Valor_Total_Item', names='Linha', 
                 title='Vendas por Linha de Produto', 
                 hover_data=['Valor_Total_Item'])
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont=dict(size=38)  
    )
    fig.update_layout(
        height=1200, width=1200,
        showlegend=True,
        title_font=dict(size=40, family="Times New Roman")
    )
    return fig



def renderizar_pagina_vendas(df):
    df_filtrado = aplicar_filtros(df)

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda, ticket_medio_geral = calcular_metricas(df_filtrado)
    

    def card_style(metric_name, value, color="#FFFFFF", bg_color="#262730"):
        return f"""
        <div style="
            padding: 15px; 
            border-radius: 15px; 
            background-color: {bg_color}; 
            color: {color}; 
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        ">
            <h4 style="margin: 0; font-size: 22px;">{metric_name}</h4>
            <h2 style="margin: 10px 0; font-size: 36px;">{value}</h2>
        </div>
        """

    col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 1, 1, 1, 1, 1, 1])

    with col1:
        st.image(CAMINHO_ARQUIVO_IMAGENS, width=250)
    with col2:
        st.markdown(card_style("Total de Notas", f"{total_nf}"), unsafe_allow_html=True)
    with col3:
        st.markdown(card_style("Total de Produtos", f"{total_qtd_produto}"), unsafe_allow_html=True)
    with col4:
        st.markdown(card_style("Faturamento Total", formatar_moeda(valor_total_item)), unsafe_allow_html=True)
    with col5:
        st.markdown(card_style("Custo Total", formatar_moeda(total_custo_compra)), unsafe_allow_html=True)
    with col6:
        st.markdown(card_style("Margem Bruta", formatar_moeda(total_lucro_venda)), unsafe_allow_html=True)
    with col7:
        st.markdown(card_style("Ticket Médio Geral", formatar_moeda(ticket_medio_geral)), unsafe_allow_html=True)

    


    df_ticket_medio = processar_dados_ticket_medio(df_filtrado)

    df_ranking = ranking_clientes(df_filtrado)
    df_ranking = df_ranking.reset_index(drop=True)
    df_ranking = df_ranking.iloc[::-1]

    fig = px.bar(
        df_ranking,
        x="Valor_Total_Item",
        y="Cliente",
        orientation="h",
        title="Top Clientes por Faturamento (Personalizado)",
        labels={"Valor_Total_Item": "Faturamento (R$)", "Cliente": "Clientes"},
        text=df_ranking["Valor_Total_Item"],
        color="Valor_Total_Item", 
        color_continuous_scale="Viridis"
    )

    fig.update_traces(
        textposition="inside",
        textfont=dict(size=28, color="black") 
    )

    fig.update_layout(
        xaxis_showticklabels=True,
        height=1100,
        width=750,
        yaxis=dict(
            title=dict(font=dict(size=24)),
            tickfont=dict(size=16)
        ),
        xaxis=dict(
        tickfont=dict(size=16)
        ),
        title_font=dict(size=50, family="Times New Roman")
        
    )

            

    graphs = [
        criar_grafico_vendas_diarias(df_filtrado, mes_atual, ano_atual),
        criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Vendedor'), 'Vendedor', 'Valor_Total_Item', 'Vendas por Vendedor', {'Valor_Total_Item': 'Valor Total de Venda'}),
        criar_grafico_barras(produtos_mais_vendidos(df_filtrado), 'Descricao_produto', 'Valor_Total_Item', 'Top 10 Produtos Mais Vendidos', {'Descricao_produto': 'Produto', 'Valor_Total_Item': 'Valor Total de Venda'}),
        exibir_grafico_ticket_medio(df_ticket_medio),
        criar_grafico_pizza_vendas_linha(df_filtrado),
        fig
    ]

    if "graph_index" not in st.session_state:
        st.session_state.graph_index = 0

    st.plotly_chart(graphs[st.session_state.graph_index])

    time.sleep(20)  

    st.session_state.graph_index = (st.session_state.graph_index + 1) % len(graphs)
    st.rerun()  

    with open("no_sleep_component.html", "r") as f:
        html_string = f.read()
    components.html(html_string, height=100)


def main():
    caminho_arquivo = CAMINHO_ARQUIVO_VENDAS

    if caminho_arquivo and os.path.exists(caminho_arquivo):
        try:
            df = carregar_dados(caminho_arquivo)
            if df is not None:
                renderizar_pagina_vendas(df)

        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
    else:
        st.error("Arquivo não encontrado!")

if __name__ == "__main__":
    main()