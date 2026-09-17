import pandas as pd
import re
from pathlib import Path


# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

caminho_arquivo = "data/original/Azul Fundamentos e Planilha 2T26.xlsx"

# Altere apenas o nome da aba para reutilizar o código
nome_aba = "Balanço | Balance Sheet"

# Nome-base dos arquivos de saída
nome_base = "balanco"

# Anos que serão analisados
anos_desejados = ["2021", "2022", "2023", "2024", "2025"]


# ==========================================
# 2. LEITURA DA PLANILHA
# ==========================================

df = pd.read_excel(
    caminho_arquivo,
    sheet_name=nome_aba,
    header=None
)

print(f"Aba '{nome_aba}' lida com sucesso!")
print(f"Dimensões da planilha: {df.shape}")


# ==========================================
# 3. IDENTIFICAR A LINHA DOS PERÍODOS
# ==========================================

linha_periodos = None

for indice, linha in df.iterrows():

    valores = linha.fillna("").astype(str).tolist()

    quantidade_anos = 0
    quantidade_trimestres = 0

    for valor in valores:

        valor = valor.strip()

        # Identificar anos de 2021 a 2025,
        # mesmo que tenham números sobrescritos
        if re.search(r"20(21|22|23|24|25)", valor):
            quantidade_anos += 1

        # Identificar trimestres de 2021 a 2025
        if re.search(r"[1-4]T(21|22|23|24|25)", valor):
            quantidade_trimestres += 1

    # Identificar a linha que contém vários períodos
    if quantidade_anos >= 3 or quantidade_trimestres >= 3:
        linha_periodos = indice
        break

if linha_periodos is None:
    raise ValueError(
        "Não foi possível identificar a linha dos períodos."
    )

print(f"Linha dos períodos identificada: {linha_periodos}")


# ==========================================
# 4. IDENTIFICAR AS COLUNAS DOS PERÍODOS
# ==========================================

colunas_anuais = {}
colunas_trimestrais = {}

for coluna, valor in df.iloc[linha_periodos].items():

    periodo = str(valor).strip()

    # Identificar trimestres, como 1T21, 2T22 e 4T25
    trimestre_encontrado = re.search(
        r"([1-4]T(?:21|22|23|24|25))",
        periodo
    )

    if trimestre_encontrado:

        trimestre = trimestre_encontrado.group(1)
        colunas_trimestrais[trimestre] = coluna

        continue

    # Identificar anos, mesmo com números sobrescritos
    ano_encontrado = re.search(
        r"(2021|2022|2023|2024|2025)",
        periodo
    )

    if ano_encontrado:

        ano = ano_encontrado.group(1)
        colunas_anuais[ano] = coluna


print("\nColunas anuais identificadas:")
print(colunas_anuais)

print("\nColunas trimestrais identificadas:")
print(colunas_trimestrais)


# ==========================================
# 5. VALIDAR OS PERÍODOS ENCONTRADOS
# ==========================================

anos_faltantes = [
    ano
    for ano in anos_desejados
    if ano not in colunas_anuais
]

if anos_faltantes:

    print("\nAtenção! Anos não identificados:")
    print(anos_faltantes)


# ==========================================
# 6. DEFINIR AS COLUNAS DOS INDICADORES
# ==========================================

# Coluna 1: indicador em inglês
# Coluna 2: indicador em português
colunas_indicadores = [1, 2]


# ==========================================
# 7. CRIAR A BASE ANUAL
# ==========================================

anos_encontrados = [
    ano
    for ano in anos_desejados
    if ano in colunas_anuais
]

colunas_anuais_selecionadas = [
    colunas_anuais[ano]
    for ano in anos_encontrados
]

base_anual = df.iloc[
    :,
    colunas_indicadores + colunas_anuais_selecionadas
].copy()

base_anual.columns = (
    ["indicador_en", "indicador_pt"]
    + anos_encontrados
)


# ==========================================
# 8. CRIAR A BASE TRIMESTRAL
# ==========================================

ordem_trimestres = [
    f"{trimestre}T{ano}"
    for ano in ["21", "22", "23", "24", "25"]
    for trimestre in ["1", "2", "3", "4"]
]

trimestres_encontrados = [
    trimestre
    for trimestre in ordem_trimestres
    if trimestre in colunas_trimestrais
]

colunas_trimestrais_selecionadas = [
    colunas_trimestrais[trimestre]
    for trimestre in trimestres_encontrados
]

base_trimestral = df.iloc[
    :,
    colunas_indicadores + colunas_trimestrais_selecionadas
].copy()

base_trimestral.columns = (
    ["indicador_en", "indicador_pt"]
    + trimestres_encontrados
)


# ==========================================
# 9. LIMPAR AS BASES
# ==========================================

def limpar_base(base, colunas_periodos):

    # Identificar as células que possuem valores numéricos
    valores_numericos = base[colunas_periodos].apply(
        pd.to_numeric,
        errors="coerce"
    )

    # Manter somente as linhas que possuem pelo menos
    # um valor numérico em algum período
    base = base[
        valores_numericos.notna().any(axis=1)
    ].copy()

    # Remover linhas sem nome de indicador
    base = base[
        base["indicador_pt"].notna()
        & (
            base["indicador_pt"]
            .astype(str)
            .str.strip()
            != ""
        )
    ].copy()

    # Reiniciar os índices
    base = base.reset_index(drop=True)

    return base


# Aplicar a limpeza na base anual
base_anual = limpar_base(
    base_anual,
    anos_encontrados
)

# Aplicar a limpeza na base trimestral
base_trimestral = limpar_base(
    base_trimestral,
    trimestres_encontrados
)

# ==========================================
# 10. CRIAR A PASTA DE DESTINO
# ==========================================

pasta_tratados = Path("data/tratados")

pasta_tratados.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# 11. SALVAR OS ARQUIVOS
# ==========================================

arquivo_anual = (
    pasta_tratados
    / f"{nome_base}_anual_2021_2025.csv"
)

arquivo_trimestral = (
    pasta_tratados
    / f"{nome_base}_trimestral_2021_2025.csv"
)

base_anual.to_csv(
    arquivo_anual,
    index=False,
    encoding="utf-8-sig"
)

base_trimestral.to_csv(
    arquivo_trimestral,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================
# 12. RESULTADO FINAL
# ==========================================

print("\nProcessamento concluído com sucesso!")

print(f"Arquivo anual salvo em: {arquivo_anual}")
print(f"Arquivo trimestral salvo em: {arquivo_trimestral}")

print(
    f"\nQuantidade de linhas na base anual: "
    f"{len(base_anual)}"
)

print(
    f"Quantidade de linhas na base trimestral: "
    f"{len(base_trimestral)}"
)