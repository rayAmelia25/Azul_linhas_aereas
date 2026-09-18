import pandas as pd
import streamlit as st

caminho_arquivo = "data/tratados/cvm/itr/2021/azul_itr_cia_aberta_BPA_con_2021.csv"

df = pd.read_csv(
    caminho_arquivo,
    sep=";",
    encoding="utf-8-sig"
)

st.write("Quantidade de linhas:", len(df))
st.write("Tipos das colunas:")
st.write(df.dtypes)

st.dataframe(df)