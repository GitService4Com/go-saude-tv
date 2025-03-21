# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import streamlit.components.v1 as components
# import os
# import datetime
# import warnings

# warnings.simplefilter(action='ignore', category=FutureWarning)

# st.set_page_config(page_title="Go MED SAÚDE", page_icon=":bar_chart:", layout="wide")

# # Configurações Globais
# CAMINHO_ARQUIVO_VENDAS = "df_vendas.csv"
# MESES_ABREVIADOS = {
#     1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
#     7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
# }

# def carregar_dados(caminho_arquivo):
#     """Carrega os dados de vendas de um arquivo CSV."""
#     try:
#         df = pd.read_csv(caminho_arquivo)
#         if df.empty:
#             st.warning("O arquivo CSV está vazio.")
#             return None
#         return df
#     except FileNotFoundError:
#         st.error("Arquivo não encontrado!")
#         return None
#     except Exception as e:
#         st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
#         return None

# def formatar_moeda(valor, simbolo_moeda="R$"):
#     """Formata um valor numérico como moeda."""
#     if pd.isna(valor):
#         return ''
#     try:
#         return f"{simbolo_moeda} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
#     except (TypeError, ValueError):
#         return "Valor inválido" #Tratamento de erro, para caso o valor não possa ser convertido para float.

# def calcular_metricas(df):
#     """Calcula métricas de vendas."""
#     total_nf = len(df['NF'].unique())
#     total_qtd_produto = df['Qtd_Produto'].sum()
#     valor_total_item = df['Valor_Total_Item'].sum()
#     total_custo_compra = df['Total_Custo_Compra'].sum()
#     total_lucro_venda = df['Total_Lucro_Venda_Item'].sum()
#     return total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda

# def agrupar_e_somar(df, coluna_agrupamento):
#     """Agrupa e soma valores por uma coluna."""
#     return df.groupby(coluna_agrupamento).agg(
#         {'Valor_Total_Item': 'sum', 'Total_Custo_Compra': 'sum', 'Total_Lucro_Venda_Item': 'sum'}
#     ).reset_index()

# def ranking_clientes(df, top_n=10,max_len=25):
#     """Retorna os top N clientes com maior faturamento total, incluindo o número do ranking."""
#     df_clientes = df.groupby('Cliente').agg({'Valor_Total_Item': 'sum'}).reset_index()
#     df_clientes = df_clientes.sort_values(by='Valor_Total_Item', ascending=False).head(top_n)
#     df_clientes['Ranking'] = range(1, len(df_clientes) + 1)
#     df_clientes['Valor_Total_Item'] = df_clientes['Valor_Total_Item'].apply(formatar_moeda)
#     df_clientes = df_clientes[['Ranking', 'Cliente', 'Valor_Total_Item']]
#     df_clientes['Cliente'] = df_clientes['Cliente'].str[:max_len]
#     return df_clientes

# def produtos_mais_vendidos(df, top_n=10, ordenar_por='Valor_Total_Item', max_len=20):
#     df_agrupado = df.groupby('Descricao_produto')[ordenar_por].sum().reset_index()
#     df_ordenado = df_agrupado.sort_values(by=ordenar_por, ascending=False)
#     df_ordenado['Descricao_produto'] = df_ordenado['Descricao_produto'].str[:max_len]
#     return df_ordenado.head(top_n)

# def criar_grafico_barras(df, x, y, title, labels):
#     """Cria um gráfico de barras."""
#     df['Valor_Monetario'] = df[y].apply(formatar_moeda)
#     fig = px.bar(df, x=x, y=y, title=title, labels=labels, 
#                  color=y, text=df['Valor_Monetario'], template="plotly_white", 
#                  hover_data={x: False, y: False, 'Valor_Monetario': True})
#     fig.update_traces(marker=dict(line=dict(color='black', width=1)), 
#                       hoverlabel=dict(bgcolor="black", font_size=22, 
#                                       font_family="Arial, sans-serif"))
#     fig.update_layout(yaxis_title=labels.get(y, y), 
#                       xaxis_title=labels.get(x, x),
#                       showlegend=False, height=400)
    
#     return fig

# def criar_grafico_vendas_diarias(df, mes, ano):
#     """Cria um gráfico de vendas diárias."""
#     df_filtrado = df[(df['Mes'] == mes) & (df['Ano'] == ano)]
#     vendas_diarias = df_filtrado.groupby('Dia')['Valor_Total_Item'].sum().reset_index()
#     vendas_diarias["Valor_Monetario"] = vendas_diarias["Valor_Total_Item"].apply(formatar_moeda)
#     fig = px.bar(vendas_diarias, x='Dia', y='Valor_Total_Item',
#                  title=f'Vendas Diárias em {mes}/{ano}',
#                  labels={'Dia': 'Dia', 'Valor_Total_Item': 'Valor Total de Venda'},
#                  color='Valor_Total_Item', text=vendas_diarias["Valor_Monetario"],
#                  template="plotly_white", hover_data={'Valor_Total_Item': False,'Valor_Monetario': True})
#     fig.update_traces(marker=dict(line=dict(color='black', width=1)),
#                       hoverlabel=dict(bgcolor="black", font_size=22,
#                                       font_family="Arial-bold, sans-serif"))
#     fig.update_layout(yaxis_title='Valor Total de Venda',
#                       xaxis_title='Dia',
#                       showlegend=False, height=400)
#     return fig

# def aplicar_filtros(df, vendedor='Todos', mes=None, ano=None, situacao='Faturada'):
#     """Aplica filtros aos dados."""
#     df_filtrado = df.copy()

#     # Define o ano atual como padrão se 'ano' não for especificado
#     if ano is None:
#         ano = datetime.datetime.now().year

#     # Define o mês atual como padrão se 'mes' não for especificado
#     if mes is None:
#         mes = datetime.datetime.now().month

#     if vendedor != 'Todos':
#         df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor]
#     if mes is not None:
#         df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
#     if ano is not None:
#         df_filtrado = df_filtrado[df_filtrado['Ano'] == ano]
#     if situacao != 'Todos':
#         df_filtrado = df_filtrado[df_filtrado['situacao'] == situacao]

#     return df_filtrado

# def renderizar_pagina_vendas(df):
#     print(f"Número de valores NaN na coluna 'Mes': {df['Mes'].isnull().sum()}")

#     ano_atual = datetime.datetime.now().year
#     mes_atual = datetime.datetime.now().month
 

#     df_filtrado = aplicar_filtros(df, 'Todos', mes_atual, ano_atual, 'Faturada')

#     total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda = calcular_metricas(df_filtrado)

#     col1, col2, col3, col4, col5 = st.columns(5)
#     col1.metric("Total de Notas", f"{total_nf}")
#     col2.metric("Total de Produtos", f"{total_qtd_produto}")
#     col3.metric("Faturamento Total", formatar_moeda(valor_total_item))
#     col4.metric("Custo Total", formatar_moeda(total_custo_compra))
#     col5.metric("Margem Bruta", formatar_moeda(total_lucro_venda))

#     col_graf1, col_graf2, col_graf3 = st.columns(3)

#     with col_graf1:
#         if 'Dia' in df.columns:
#             fig_vendas_diarias = criar_grafico_vendas_diarias(df_filtrado, mes_atual, ano_atual)
#             st.plotly_chart(fig_vendas_diarias)

#         fig_linha = criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Linha'), 'Linha', 'Valor_Total_Item',
#                                         'Vendas por Linha de Produto', {'Valor_Total_Item': 'Valor Total de Venda'})
#         st.plotly_chart(fig_linha)

#     with col_graf2:
#         fig_vendedor = criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Vendedor'), 'Vendedor', 'Valor_Total_Item',
#                                             'Vendas por Vendedor', {'Valor_Total_Item': 'Valor Total de Venda'})
#         st.plotly_chart(fig_vendedor)

#         fig_produtos = criar_grafico_barras(produtos_mais_vendidos(df_filtrado), 'Descricao_produto', 'Valor_Total_Item',
#                                             'Top 10 Produtos Mais Vendidos',
#                                             {'Descricao_produto': 'Produto', 'Valor_Total_Item': 'Valor Total de Venda'})
#         st.plotly_chart(fig_produtos)


#     def processar_dados(df):
#         df['Data_Emissao'] = pd.to_datetime(df['Data_Emissao'], format='mixed', dayfirst=True)
#         df['Semana'] = df['Data_Emissao'].dt.isocalendar().week
#         colunas_nf_unicas = ['NF', 'Data_Emissao', 'Vendedor', 'Valor_Total_Nota', 'Mes', 'Ano', 'Semana', 'situacao']
#         df_nf_unicas = df.drop_duplicates(subset='NF')[colunas_nf_unicas].copy()
#         df_nf_unicas = df_nf_unicas[df_nf_unicas['situacao'] == 'Faturada']

#         meses_abreviados = {
#             1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
#             7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
#         }

#         meses_numericos = sorted(df_nf_unicas['Mes'].unique().tolist(), key=int)
#         mes = [meses_abreviados[mes] for mes in meses_numericos]

#         ano = sorted(df_nf_unicas['Ano'].unique().tolist(), key=int)

#         ano_atual = datetime.datetime.now().year
#         mes_atual = datetime.datetime.now().month
#         mes_atual_abreviado = meses_abreviados[mes_atual]

#         # Adicionar o ano e mês atuais se eles não estiverem na lista
#         if ano_atual not in ano:
#             ano.append(ano_atual)
#             ano.sort()

#         if mes_atual_abreviado not in mes:
#             mes.append(mes_atual_abreviado)
#             mes.sort(key=lambda x: list(meses_abreviados.values()).index(x))

#         ano_selecionado = ano_atual
#         mes_selecionado = mes_atual_abreviado

#         def aplicar_filtros(df, mes_selecionado, ano_selecionado):
#             if mes_selecionado != 'Todos':
#                 meses_invertidos = {v: k for k, v in meses_abreviados.items()}
#                 mes_numero = meses_invertidos[mes_selecionado]
#                 df = df[df['Mes'] == mes_numero]
#             if ano_selecionado != 'Todos':
#                 df = df[df['Ano'] == ano_selecionado]
#             return df

#         df_nf_unicas = aplicar_filtros(df_nf_unicas, mes_selecionado, ano_selecionado)

#         df_resumo = df_nf_unicas.groupby(['Ano', 'Mes', 'Semana', 'Vendedor'])['NF'].count().reset_index(name='Quantidade_Notas_Semana')
#         df_nf_unicas = pd.merge(df_nf_unicas, df_resumo, on=['Ano', 'Mes', 'Semana', 'Vendedor'], how='left')
#         df_nf_unicas['Quantidade_Notas_Semana'] = df_nf_unicas['Quantidade_Notas_Semana'].fillna(0).astype(int)

#         df_resumo_vendas = df_nf_unicas.groupby(['Ano', 'Mes', 'Semana', 'Vendedor'])['Valor_Total_Nota'].sum().reset_index(name='Soma_Venda_Semana')
#         df_nf_unicas = pd.merge(df_nf_unicas, df_resumo_vendas, on=['Ano', 'Mes', 'Semana', 'Vendedor'], how='left')


#         df_ticket_medio = df_nf_unicas.groupby(['Vendedor', 'Semana'])['Valor_Total_Nota'].mean().reset_index(name='Ticket_Medio')
#         df_pivot = df_ticket_medio.pivot(index='Vendedor', columns='Semana', values='Ticket_Medio')

#         df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)

#         st.subheader("Ticket Médio por Vendedor e Semana (Tabela)")

#         df_pivot = df_pivot.applymap(formatar_moeda)
#         html_table = df_pivot.to_html(classes='data', index=True)

#         css = """
#         <style type="text/css">
#         table.data {
#             border-collapse: collapse;
#             width: 100%;
#             background-color: #8FBC8F; /* Verde Médio para o fundo geral */
#             color: #000; /* Cor do texto para contraste no fundo verde */
#         }

#         table.data th, table.data td {
#             border: 2px solid black;
#             padding: 8px;
#             text-align: center;
#             background-color: inherit; /* Herda o fundo verde da tabela */
#         }

#         table.data th {
#             background-color: #2E8B57; /* Verde Marinho para o cabeçalho */
#             color: #000000; /* Cor do texto branca para contraste no cabeçalho */
#         }

#         table.data tr:nth-child(even) {
#             background-color: inherit; /* Herda o fundo verde da tabela */
#         }

#         table.data tr {color: #000; /* Cor do texto preta para contraste nas linhas */
#         }
#         </style>
#         """
#         components.html(css + html_table, height=300)
        
#     df = processar_dados(df)

#     with col_graf3:

#         # Obtém o ranking dos clientes a partir do seu DataFrame real
#         df_ranking = ranking_clientes(df_filtrado)
#         df_ranking = df_ranking.reset_index(drop=True)

#         # Criação do gráfico de barras horizontal
#         fig = px.bar(
#             df_ranking,
#             x="Valor_Total_Item",
#             y="Cliente",
#             orientation="h",
#             title="Top Clientes por Faturamento",
#             labels={"Valor_Total_Item": "Faturamento", "Cliente": "Clientes"},
#             text=df_ranking["Valor_Total_Item"]
#         )

#         fig.update_traces(textposition="inside", marker_color="royalblue")

#         # Ocultar o eixo X
#         fig.update_layout(xaxis_showticklabels=False, height=850, width=100)

#         # Exibir no Streamlit
#         st.plotly_chart(fig)

# # def renderizar_pagina_vendedor(df):
    

# def main():
#     caminho_arquivo = CAMINHO_ARQUIVO_VENDAS

#     if caminho_arquivo and os.path.exists(caminho_arquivo):
#         try:
#             df = carregar_dados(caminho_arquivo)
#             if df is not None:
#                 renderizar_pagina_vendas(df)

#         except Exception as e:
#             st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
#     else:
#         st.error("Arquivo não encontrado!")

# if __name__ == "__main__":
#     main()