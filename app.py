import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import os
import datetime
import warnings
import time

warnings.simplefilter(action='ignore', category=FutureWarning)

st.set_page_config(page_title="Go MED SAÚDE", page_icon=":bar_chart:", layout="wide")

# Configurações Globais
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
    return f"{simbolo_moeda} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def ranking_clientes(df, top_n=10,max_len=25):
    """Retorna os top N clientes com maior faturamento total, incluindo o número do ranking."""
    df_clientes = df.groupby('Cliente').agg({'Valor_Total_Item': 'sum'}).reset_index()
    df_clientes = df_clientes.sort_values(by='Valor_Total_Item', ascending=False).head(top_n)
    df_clientes['Ranking'] = range(1, len(df_clientes) + 1)
    df_clientes['Valor_Total_Item'] = df_clientes['Valor_Total_Item'].apply(formatar_moeda)
    df_clientes = df_clientes[['Ranking', 'Cliente', 'Valor_Total_Item']]
    df_clientes['Cliente'] = df_clientes['Cliente'].str[:max_len]
    return df_clientes

def calcular_metricas(df):
    total_nf = len(df['NF'].unique())
    total_qtd_produto = df['Qtd_Produto'].sum()
    valor_total_item = df['Valor_Total_Item'].sum()
    total_custo_compra = df['Total_Custo_Compra'].sum()
    total_lucro_venda = df['Total_Lucro_Venda_Item'].sum()
    return total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda

def agrupar_e_somar(df, coluna_agrupamento):
    return df.groupby(coluna_agrupamento).agg(
        {'Valor_Total_Item': 'sum', 'Total_Custo_Compra': 'sum', 'Total_Lucro_Venda_Item': 'sum'}
    ).reset_index()

def produtos_mais_vendidos(df, top_n=10, ordenar_por='Valor_Total_Item', max_len=25):
    df_agrupado = df.groupby('Descricao_produto')[ordenar_por].sum().reset_index()
    df_ordenado = df_agrupado.sort_values(by=ordenar_por, ascending=False)
    df_ordenado['Descricao_produto'] = df_ordenado['Descricao_produto'].str[:max_len]
    return df_ordenado.head(top_n)

def criar_grafico_barras(df, x, y, title, labels):
    df['Valor_Monetario'] = df[y].apply(formatar_moeda)
    fig = px.bar(df, x=x, y=y, title=title, labels=labels, 
                 color=y, text=df['Valor_Monetario'], template="plotly_white", 
                 hover_data={x: False, y: False, 'Valor_Monetario': True})
    fig.update_traces(marker=dict(line=dict(color='black', width=1)), 
                      hoverlabel=dict(bgcolor="black", font_size=22, 
                                      font_family="Arial, sans-serif"),
                      textfont=dict(size=28, color='black'))

    fig.update_layout(
        yaxis_title=labels.get(y, y), 
        xaxis_title=labels.get(x, x), 
        showlegend=False, 
        height=800,
        xaxis=dict(tickfont=dict(size=18)),
        yaxis=dict(
            title=dict(
                text=labels.get(y, y),
                font=dict(size=18)      
            ),
            tickfont=dict(size=16),    
        ),
        title_font=dict(size=40, family="Times New Roman")
    )
    return fig

def criar_grafico_vendas_diarias(df, mes, ano):
    df_filtrado = df[(df['Mes'] == mes) & (df['Ano'] == ano)]
    vendas_diarias = df_filtrado.groupby('Dia')['Valor_Total_Item'].sum().reset_index()
    vendas_diarias["Valor_Monetario"] = vendas_diarias["Valor_Total_Item"].apply(formatar_moeda)
    fig = px.bar(vendas_diarias, x='Dia', y='Valor_Total_Item',
                title=f'Vendas Diárias em {mes}/{ano}',
                labels={'Dia': 'Dia', 'Valor_Total_Item': 'Valor Total de Venda'},
                color='Valor_Total_Item',
                text=vendas_diarias["Valor_Monetario"],
                template="plotly_white", hover_data={'Valor_Total_Item': False,'Valor_Monetario': True})
    fig.update_traces(marker=dict(line=dict(color='black', width=1)),
                      hoverlabel=dict(bgcolor="black", font_size=14,
                                      font_family="Arial-bold, sans-serif"), textfont=dict(size=16, color='black'))
    fig.update_layout(yaxis_title='Valor Total de Venda',
                      xaxis_title='Dia',
                      showlegend=False, height=800, 
                      xaxis=dict(tickfont=dict(size=18)),
                      yaxis=dict(
                          title=dict(
                              text='Valor Total de Venda',
                              font=dict(size=14)      
                          ),
                          tickfont=dict(size=12)
                      ),
                      title_font=dict(size=40, family="Times New Roman")
                      )
    return fig

def aplicar_filtros(df, vendedor='Todos', mes=None, ano=None, situacao='Faturada'):
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
    df['Semana'] = df['Data_Emissao'].dt.isocalendar().week
    colunas_nf_unicas = ['NF', 'Data_Emissao', 'Vendedor', 'Valor_Total_Nota', 'Mes', 'Ano', 'Semana', 'situacao']
    df_nf_unicas = df.drop_duplicates(subset='NF')[colunas_nf_unicas].copy()
    df_nf_unicas = df_nf_unicas[df_nf_unicas['situacao'] == 'Faturada']

    meses_abreviados = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    meses_numericos = sorted(df_nf_unicas['Mes'].unique().tolist(), key=int)
    mes = [meses_abreviados[mes] for mes in meses_numericos]

    ano = sorted(df_nf_unicas['Ano'].unique().tolist(), key=int)

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month
    mes_atual_abreviado = meses_abreviados[mes_atual]

    if ano_atual not in ano:
        ano.append(ano_atual)
        ano.sort()

    if mes_atual_abreviado not in mes:
        mes.append(mes_atual_abreviado)
        mes.sort(key=lambda x: list(meses_abreviados.values()).index(x))

    ano_selecionado = ano_atual
    mes_selecionado = mes_atual_abreviado

    def aplicar_filtros(df, mes_selecionado, ano_selecionado):
        if mes_selecionado != 'Todos':
            meses_invertidos = {v: k for k, v in meses_abreviados.items()}
            mes_numero = meses_invertidos[mes_selecionado]
            df = df[df['Mes'] == mes_numero]
        if ano_selecionado != 'Todos':
            df = df[df['Ano'] == ano_selecionado]
        return df

    df_nf_unicas = aplicar_filtros(df_nf_unicas, mes_selecionado, ano_selecionado)

    df_resumo = df_nf_unicas.groupby(['Ano', 'Mes', 'Semana', 'Vendedor'])['NF'].count().reset_index(name='Quantidade_Notas_Semana')
    df_nf_unicas = pd.merge(df_nf_unicas, df_resumo, on=['Ano', 'Mes', 'Semana', 'Vendedor'], how='left')
    df_nf_unicas['Quantidade_Notas_Semana'] = df_nf_unicas['Quantidade_Notas_Semana'].fillna(0).astype(int)

    df_resumo_vendas = df_nf_unicas.groupby(['Ano', 'Mes', 'Semana', 'Vendedor'])['Valor_Total_Nota'].sum().reset_index(name='Soma_Venda_Semana')
    df_nf_unicas = pd.merge(df_nf_unicas, df_resumo_vendas, on=['Ano', 'Mes', 'Semana', 'Vendedor'], how='left')


    df_ticket_medio = df_nf_unicas.groupby(['Vendedor', 'Semana'])['Valor_Total_Nota'].mean().reset_index(name='Ticket_Medio')
    df_pivot = df_ticket_medio.pivot(index='Vendedor', columns='Semana', values='Ticket_Medio')

    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)

    st.subheader("Ticket Médio por Vendedor e Semana (Tabela)")

    df_pivot = df_pivot.applymap(formatar_moeda)
    html_table = df_pivot.to_html(classes='data', index=True)

    css = """
    <style type="text/css">
    table.data {
        border-collapse: collapse;
        width: 100%;
        background-color: #8FBC8F;
        color: #000;
    }

    table.data th, table.data td {
        border: 2px solid black;
        padding: 8px;
        text-align: center;
        background-color: inherit;
    }

    table.data th {
        background-color: #2E8B57;
        color: #000000;
    }

    table.data tr:nth-child(even) {
        background-color: inherit;
    }

    table.data tr {color: #000;
    }
    </style>
    """
    components.html(css + html_table, height=400)

def renderizar_pagina_vendas(df):
    print(f"Número de valores NaN na coluna 'Mes': {df['Mes'].isnull().sum()}")

    
    df_filtrado = aplicar_filtros(df)

    total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda = calcular_metricas(df_filtrado)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total de Notas", f"{total_nf}")
    col2.metric("Total de Produtos", f"{total_qtd_produto}")
    col3.metric("Faturamento Total", formatar_moeda(valor_total_item))
    col4.metric("Custo Total", formatar_moeda(total_custo_compra))
    col5.metric("Lucro Total", formatar_moeda(total_lucro_venda))

    # # Exibição do Ticket Médio
    # processar_dados_ticket_medio(df)

    # Obtém o ranking dos clientes a partir do seu DataFrame real
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
        textfont=dict(size=40, color="black") 
    )

    fig.update_layout(
        xaxis_showticklabels=True,
        height=800,
        width=300,
        yaxis=dict(
            title=dict(font=dict(size=24)),
            tickfont=dict(size=16)
        ),
        xaxis=dict(
        tickfont=dict(size=16)
        ),
        title_font=dict(size=40, color="black") 
    )
    


    # Carrossel de gráficos (e tabela de ranking)
    if 'graph_index' not in st.session_state:
        st.session_state.graph_index = 0

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    graphs = [
        criar_grafico_vendas_diarias(df_filtrado, mes_atual, ano_atual),
        criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Linha'), 'Linha', 'Valor_Total_Item',
                            'Vendas por Linha de Produto', {'Valor_Total_Item': 'Valor Total de Venda'}),
        criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Vendedor'), 'Vendedor', 'Valor_Total_Item',
                            'Vendas por Vendedor', {'Valor_Total_Item': 'Valor Total de Venda'}),
        criar_grafico_barras(produtos_mais_vendidos(df_filtrado), 'Descricao_produto', 'Valor_Total_Item',
                            'Top 10 Produtos Mais Vendidos',
                            {'Descricao_produto': 'Produto', 'Valor_Total_Item': 'Valor Total de Venda'}),
        fig 
    ]


    if isinstance(graphs[st.session_state.graph_index], pd.DataFrame):
        st.subheader("Top 20 Clientes por Faturamento Total")
        st.dataframe(graphs[st.session_state.graph_index], use_container_width=True)
    else:
        st.plotly_chart(graphs[st.session_state.graph_index], key=f"graph_{st.session_state.graph_index}")

    time.sleep(10)
    st.session_state.graph_index = (st.session_state.graph_index + 1) % len(graphs)
    st.rerun()

    # Adição do componente no-sleep
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