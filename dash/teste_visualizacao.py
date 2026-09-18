import streamlit as st
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Visualização das Bases - Azul",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Visualização das Bases - Azul")

st.write(
    "Selecione uma pasta e um arquivo para visualizar "
    "as bases tratadas da Azul Linhas Aéreas."
)


# ============================================================
# LOCALIZAÇÃO DOS ARQUIVOS
# ============================================================

PASTA_TRATADOS = Path("data/tratados")


if not PASTA_TRATADOS.exists():
    st.error("A pasta 'data/tratados' não foi encontrada.")
    st.stop()


# Busca arquivos CSV dentro das subpastas
arquivos_csv = sorted(
    PASTA_TRATADOS.rglob("*.csv")
)


if not arquivos_csv:
    st.warning(
        "Nenhum arquivo CSV foi encontrado em "
        "'data/tratados'."
    )
    st.stop()


# ============================================================
# ORGANIZAÇÃO DAS PASTAS
# ============================================================

# Obtém as pastas relativas ao diretório tratados
pastas = sorted(
    set(
        arquivo.parent.relative_to(PASTA_TRATADOS)
        for arquivo in arquivos_csv
    )
)


# ============================================================
# SELEÇÃO DA PASTA
# ============================================================

opcoes_pastas = ["Todas as pastas"] + [
    str(pasta) for pasta in pastas
]


pasta_selecionada = st.selectbox(
    "📂 Selecione a pasta:",
    opcoes_pastas
)


# Filtra os arquivos conforme a pasta escolhida
if pasta_selecionada == "Todas as pastas":

    arquivos_filtrados = arquivos_csv

else:

    arquivos_filtrados = [
        arquivo
        for arquivo in arquivos_csv
        if str(
            arquivo.parent.relative_to(PASTA_TRATADOS)
        ) == pasta_selecionada
    ]


# ============================================================
# SELEÇÃO DO ARQUIVO
# ============================================================

arquivo_selecionado = st.selectbox(
    "📄 Selecione o arquivo:",
    arquivos_filtrados,
    format_func=lambda arquivo: arquivo.name
)


# Exibe o caminho do arquivo
st.caption(
    f"Caminho: {arquivo_selecionado.relative_to(PASTA_TRATADOS)}"
)


# ============================================================
# LEITURA DO ARQUIVO
# ============================================================

try:

    try:

        df = pd.read_csv(
            arquivo_selecionado,
            encoding="utf-8-sig",
            sep=None,
            engine="python"
        )

    except UnicodeDecodeError:

        df = pd.read_csv(
            arquivo_selecionado,
            encoding="latin1",
            sep=None,
            engine="python"
        )

except Exception as erro:

    st.error(f"Erro ao carregar o arquivo: {erro}")
    st.stop()


# ============================================================
# VISUALIZAÇÃO DA TABELA
# ============================================================

if df.empty:

    st.warning("O arquivo selecionado está vazio.")
    st.stop()


# Limpeza dos nomes das colunas
df.columns = df.columns.astype(str).str.strip()


st.subheader("📋 Tabela de dados")


# Informações básicas
coluna1, coluna2 = st.columns(2)

with coluna1:
    st.metric("Quantidade de linhas", df.shape[0])

with coluna2:
    st.metric("Quantidade de colunas", df.shape[1])


# ============================================================
# CONTROLE DE VISUALIZAÇÃO
# ============================================================

quantidade_linhas = st.selectbox(
    "Quantidade de linhas para visualizar:",
    [
        10,
        25,
        50,
        100,
        500,
        "Todas"
    ],
    index=2
)


if quantidade_linhas == "Todas":

    df_visualizacao = df

else:

    df_visualizacao = df.head(quantidade_linhas)


# Exibição da tabela
st.dataframe(
    df_visualizacao,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Projeto de análise de dados públicos da Azul Linhas Aéreas."
)