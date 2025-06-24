import streamlit as st
import pandas as pd
import chardet

# Configuração do dashboard
st.set_page_config(page_title="Análise de Indexação", layout="wide")
st.title("📊 Dashboard de Produtividade por Indexador")

# Widget de upload de arquivo
uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type=["csv"])

@st.cache_data
def process_data(uploaded_file):
    if uploaded_file is not None:
        try:
            # Detecta o encoding do arquivo
            rawdata = uploaded_file.read(100000)
            uploaded_file.seek(0)
            result = chardet.detect(rawdata)
            encoding = result['encoding']
            
            # Lê o arquivo CSV com ponto-e-vírgula como separador
            df = pd.read_csv(
                uploaded_file,
                encoding=encoding,
                skiprows=1,
                sep=';',  # Usa ponto-e-vírgula como separador
                parse_dates=['Data Cadastro'],
                dayfirst=True
            )
            
            # Verifica se as colunas necessárias existem
            if not all(col in df.columns for col in ['Indexador', 'Data Cadastro']):
                st.error("Erro: O arquivo CSV deve conter as colunas:")
                st.error("- 'Indexador' (nome do colaborador)")
                st.error("- 'Data Cadastro' (data e hora)")
                st.write("Colunas encontradas no arquivo:", list(df.columns))
                return None
            
            # Renomeia colunas para padronização
            df = df.rename(columns={
                'Indexador': 'Indexador',
                'Data Cadastro': 'Data_cadastro'
            })
            
            # Limpeza básica dos dados
            df = df.dropna(subset=['Indexador', 'Data_cadastro'])
            df['Indexador'] = df['Indexador'].str.strip()
            
            return df

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
            return None
    return None

# Processa os dados
df = process_data(uploaded_file)

if df is not None:
    # ... (restante do código permanece igual ao anterior)
    # [Insira aqui o código de visualização que estava na versão anterior]
    # Sidebar com filtros
    st.sidebar.header("Filtros")
    
    # Seletor de indexador
    indexador_selecionado = st.sidebar.selectbox(
        "Selecione o indexador:",
        df['Indexador'].unique()
    )
    
    # Filtra os dados
    dados_filtrados = df[df['Indexador'] == indexador_selecionado].copy()
    dados_filtrados = dados_filtrados.sort_values('Data_cadastro')
    
    # Cálculos de produtividade
    total_indexacoes = len(dados_filtrados)
    
    # Calcula diferença entre indexações em minutos
    dados_filtrados['Diff'] = dados_filtrados['Data_cadastro'].diff().dt.total_seconds() / 60
    
    # Identifica pausas (intervalos > 60 minutos)
    dados_filtrados['Pausa'] = dados_filtrados['Diff'] > 60
    
    # Tempo ativo (descontando pausas longas)
    tempo_ativo = dados_filtrados[~dados_filtrados['Pausa']]['Diff'].sum()
    
    # Média por indexação
    media_por_indexacao = tempo_ativo / total_indexacoes if total_indexacoes > 0 else 0
    
    # Exibe métricas
    st.subheader(f"Métricas para {indexador_selecionado}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Indexações", total_indexacoes)
    col2.metric("Tempo Ativo (minutos)", f"{tempo_ativo:.1f}")
    col3.metric("Média por Indexação (min)", f"{media_por_indexacao:.1f}")
    
    # Gráfico de indexações por hora
    st.subheader("Indexações por Hora do Dia")
    indexacoes_por_hora = dados_filtrados['Data_cadastro'].dt.hour.value_counts().sort_index()
    st.bar_chart(indexacoes_por_hora)
    
    # Gráfico de tempo entre indexações
    st.subheader("Tempo entre Indexações (minutos)")
    st.line_chart(dados_filtrados.set_index('Data_cadastro')['Diff'].fillna(0))
    
    # Detalhes das pausas
    if dados_filtrados['Pausa'].any():
        st.subheader("Pausas Detectadas")
        pausas = dados_filtrados[dados_filtrados['Pausa']][['Data_cadastro', 'Diff']]
        pausas['Diff'] = pausas['Diff'].round(1)
        st.dataframe(pausas)
    
    # Dados completos (opcional)
    if st.checkbox("Mostrar dados completos"):
        st.subheader("Dados Completos")
        st.dataframe(dados_filtrados)
else:
    st.info("Por favor, faça upload de um arquivo CSV válido.")