import streamlit as st
import pandas as pd
from pathlib import Path


st.title("Validação dos dados da CVM")

pasta = Path("data/tratados/cvm")

arquivos = list(pasta.rglob("*.csv"))

if not arquivos:

    st.warning("Nenhum arquivo CSV encontrado.")

else:

    nomes_arquivos = [
        arquivo.name for arquivo in arquivos
    ]

    arquivo_selecionado = st.selectbox(
        "Selecione um arquivo:",
        nomes_arquivos
    )

    caminho_arquivo = next(
        arquivo
        for arquivo in arquivos
        if arquivo.name == arquivo_selecionado
    )

    df = pd.read_csv(
        caminho_arquivo,
        sep=";",
        encoding="utf-8-sig"
    )

    st.write(f"**Arquivo:** {arquivo_selecionado}")

    st.write(f"Quantidade de linhas: {df.shape[0]}")

    st.write(f"Quantidade de colunas: {df.shape[1]}")

    st.dataframe(
        df,
        use_container_width=True
    )