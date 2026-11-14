
import re
from pathlib import Path

import pandas as pd


# ==================================================
# 1. CONFIGURAÇÕES
# ==================================================

caminho_arquivo = Path(
    "data/original/Azul Fundamentos e Planilha 2T26.xlsx"
)

nome_aba = "DRE | Income Statement"

# IMPORTANTE: este arquivo é da DRE, não do balanço.
nome_base = "dre"

anos_desejados = ["2021", "2022", "2023", "2024", "2025"]

COLUNA_INDICADOR_EN = 1
COLUNA_INDICADOR_PT = 2

pasta_tratados = Path("data/tratados")


# ==================================================
# 2. LER A PLANILHA ORIGINAL
# ==================================================

if not caminho_arquivo.exists():
    raise FileNotFoundError(
        f"Arquivo original não encontrado: {caminho_arquivo}"
    )

df = pd.read_excel(
    caminho_arquivo,
    sheet_name=nome_aba,
    header=None
)

print(f"Aba lida: {nome_aba}")
print(f"Dimensões da planilha: {df.shape}")


# ==================================================
# 3. IDENTIFICAR A LINHA DOS PERÍODOS
# ==================================================

padrao_trimestre = re.compile(
    r"([1-4]T(?:21|22|23|24|25))"
)

padrao_ano = re.compile(
    r"(2021|2022|2023|2024|2025)"
)

linha_periodos = None

for indice, linha in df.iterrows():

    valores = linha.fillna("").astype(str).tolist()

    qtd_trimestres = sum(
        bool(padrao_trimestre.search(valor.strip()))
        for valor in valores
    )

    qtd_anos = sum(
        bool(padrao_ano.search(valor.strip()))
        for valor in valores
    )

    if qtd_trimestres >= 3 or qtd_anos >= 3:
        linha_periodos = indice
        break

if linha_periodos is None:
    raise ValueError(
        "Não foi possível identificar a linha dos períodos."
    )

print(f"Linha dos períodos: {linha_periodos}")


# ==================================================
# 4. IDENTIFICAR AS COLUNAS ANUAIS E TRIMESTRAIS
# ==================================================

colunas_anuais = {}
colunas_trimestrais = {}

for coluna, valor in df.iloc[linha_periodos].items():

    periodo = str(valor).strip()

    trimestre_encontrado = padrao_trimestre.search(periodo)

    if trimestre_encontrado:
        trimestre = trimestre_encontrado.group(1)
        colunas_trimestrais[trimestre] = coluna
        continue

    ano_encontrado = padrao_ano.search(periodo)

    if ano_encontrado:
        ano = ano_encontrado.group(1)
        colunas_anuais[ano] = coluna

ordem_trimestres = [
    f"{trimestre}T{ano}"
    for ano in ["21", "22", "23", "24", "25"]
    for trimestre in ["1", "2", "3", "4"]
]

trimestres_encontrados = [
    periodo
    for periodo in ordem_trimestres
    if periodo in colunas_trimestrais
]

anos_encontrados = [
    ano
    for ano in anos_desejados
    if ano in colunas_anuais
]

print("\nTrimestres identificados:")
print(trimestres_encontrados)

print("\nAnos identificados:")
print(anos_encontrados)


# ==================================================
# 5. PREPARAR OS NOMES DOS INDICADORES
# ==================================================

df["indicador_en"] = df.iloc[:, COLUNA_INDICADOR_EN]
df["indicador_pt"] = df.iloc[:, COLUNA_INDICADOR_PT]


# ==================================================
# 6. FUNÇÕES AUXILIARES
# ==================================================

def texto_indicador(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def texto_valido_para_categoria(texto):

    if not texto or texto.lower() == "nan":
        return False

    if len(texto) > 80:
        return False

    sinais_de_observacao = [
        ". ",
        " conforme ",
        " relacionados ",
        " referente ",
        " durante ",
        " devido ",
        " parcialmente ",
        " foram ajustados "
    ]

    texto_lower = texto.lower()

    return not any(
        sinal in texto_lower
        for sinal in sinais_de_observacao
    )


def eh_grupo_principal(texto):

    texto_lower = texto.lower()

    palavras_de_grupo = [
        "operating revenue",
        "operating expenses",
        "receita líquida",
        "receitas operacionais",
        "despesas operacionais",
        "custos dos serviços",
        "resultado operacional",
        "resultado financeiro",
        "lucro líquido",
        "prejuízo líquido",
        "income",
        "expenses",
        "revenue",
        "despesas",
        "receitas",
        "custos"
    ]

    return any(
        palavra in texto_lower
        for palavra in palavras_de_grupo
    )


def converter_numero(valor):
    """
    Converte números sem aplicar escalas ou multiplicadores.
    Valores numéricos do Excel são mantidos em sua escala original.
    """

    if pd.isna(valor):
        return float("nan")

    if isinstance(valor, str):
        valor = valor.strip()

        if not valor:
            return float("nan")

        # Formatos contábeis com parênteses: (1234) = -1234
        if valor.startswith("(") and valor.endswith(")"):
            valor = "-" + valor[1:-1]

    return pd.to_numeric(valor, errors="coerce")


def identificar_categorias(base, colunas_periodos):

    base = base.copy()

    grupo_atual = ""
    subgrupo_atual = ""

    grupos = []
    subgrupos = []
    indicadores_validos = []

    for _, linha in base.iterrows():

        indicador_en = texto_indicador(linha["indicador_en"])
        indicador_pt = texto_indicador(linha["indicador_pt"])

        texto_principal = indicador_pt or indicador_en

        valores = pd.to_numeric(
            linha[colunas_periodos],
            errors="coerce"
        )

        tem_valor = valores.notna().any()

        if tem_valor:

            grupos.append(grupo_atual)
            subgrupos.append(subgrupo_atual)
            indicadores_validos.append(True)

        else:

            if texto_valido_para_categoria(texto_principal):

                if eh_grupo_principal(texto_principal):
                    grupo_atual = texto_principal
                    subgrupo_atual = ""

                elif grupo_atual:
                    subgrupo_atual = texto_principal

                else:
                    grupo_atual = texto_principal

            grupos.append("")
            subgrupos.append("")
            indicadores_validos.append(False)

    base["grupo"] = grupos
    base["subgrupo"] = subgrupos
    base["_indicador_valido"] = indicadores_validos

    base = base[
        base["_indicador_valido"]
    ].copy()

    return base.drop(columns=["_indicador_valido"])


def limpar_base(base, colunas_periodos):

    base = base.copy()

    # Remover indicadores sem nome em português.
    base = base[
        base["indicador_pt"].notna()
        & (
            base["indicador_pt"]
            .astype(str)
            .str.strip()
            .ne("")
        )
    ].copy()

    # Converter os períodos para números.
    for coluna in colunas_periodos:
        base[coluna] = base[coluna].map(converter_numero)

    # Remover linhas sem valores financeiros.
    base = base[
        base[colunas_periodos].notna().any(axis=1)
    ].copy()

    colunas_finais = [
        "grupo",
        "subgrupo",
        "indicador_en",
        "indicador_pt"
    ] + colunas_periodos

    base = base[colunas_finais]

    return base.reset_index(drop=True)


# ==================================================
# 7. VERIFICAR O EBITDA NA PLANILHA ORIGINAL
# ==================================================

print("\n" + "=" * 55)
print("VERIFICAÇÃO DO EBITDA NA PLANILHA ORIGINAL")
print("=" * 55)

indicadores_en = (
    df["indicador_en"].fillna("").astype(str).str.strip().str.lower()
)

indicadores_pt = (
    df["indicador_pt"].fillna("").astype(str).str.strip().str.lower()
)

mascara_ebitda = (
    indicadores_en.eq("ebitda")
    | indicadores_pt.eq("ebitda")
)

linhas_ebitda = df.loc[mascara_ebitda]

if linhas_ebitda.empty:

    print("ATENÇÃO: EBITDA não encontrado na planilha original.")

else:

    for indice, linha in linhas_ebitda.iterrows():

        print(f"\nLinha original do Excel (índice {indice}):")

        for periodo in trimestres_encontrados:

            coluna_excel = colunas_trimestrais[periodo]
            valor_original = linha.iloc[coluna_excel]

            print(f"{periodo}: {valor_original!r}")


# ==================================================
# 8. CRIAR A PASTA DE DESTINO
# ==================================================

pasta_tratados.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# 9. CRIAR A BASE ANUAL
# ==================================================

base_anual = None

if anos_encontrados:

    colunas_selecionadas = [
        colunas_anuais[ano]
        for ano in anos_encontrados
    ]

    base_anual = df[
        ["indicador_en", "indicador_pt"]
        + colunas_selecionadas
    ].copy()

    base_anual.columns = (
        ["indicador_en", "indicador_pt"]
        + anos_encontrados
    )

    base_anual = identificar_categorias(
        base_anual,
        anos_encontrados
    )

    base_anual = limpar_base(
        base_anual,
        anos_encontrados
    )

    print("\nBase anual preparada.")

else:
    print("\nNenhuma coluna anual encontrada.")


# ==================================================
# 10. CRIAR A BASE TRIMESTRAL
# ==================================================

base_trimestral = None

if trimestres_encontrados:

    colunas_selecionadas = [
        colunas_trimestrais[periodo]
        for periodo in trimestres_encontrados
    ]

    base_trimestral = df[
        ["indicador_en", "indicador_pt"]
        + colunas_selecionadas
    ].copy()

    base_trimestral.columns = (
        ["indicador_en", "indicador_pt"]
        + trimestres_encontrados
    )

    base_trimestral = identificar_categorias(
        base_trimestral,
        trimestres_encontrados
    )

    base_trimestral = limpar_base(
        base_trimestral,
        trimestres_encontrados
    )

    print("Base trimestral preparada.")

else:
    print("Nenhuma coluna trimestral encontrada.")


# ==================================================
# 11. VALIDAR O EBITDA NA BASE TRATADA
# ==================================================

if base_trimestral is not None:

    mascara_ebitda = (
        base_trimestral["indicador_pt"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("ebitda")
    )

    ebitda_tratado = base_trimestral.loc[mascara_ebitda]

    print("\n" + "=" * 55)
    print("EBITDA NA BASE TRATADA")
    print("=" * 55)

    if ebitda_tratado.empty:

        print("ATENÇÃO: EBITDA não encontrado na base tratada.")

    else:

        for _, linha in ebitda_tratado.iterrows():

            for periodo in trimestres_encontrados:
                print(f"{periodo}: {linha[periodo]!r}")

        # Comparar o valor original com o tratado em 3T25.
        periodo = "3T25"

        if periodo in colunas_trimestrais:

            coluna_excel = colunas_trimestrais[periodo]

            for _, linha_original in linhas_ebitda.iterrows():

                valor_original = converter_numero(
                    linha_original.iloc[coluna_excel]
                )

                valor_tratado = ebitda_tratado.iloc[0][periodo]

                print(f"\nComparação de {periodo}:")
                print(f"Valor original lido: {valor_original!r}")
                print(f"Valor tratado:       {valor_tratado!r}")

                if pd.notna(valor_original) and pd.notna(valor_tratado):

                    if abs(valor_original - valor_tratado) > 0.01:
                        print(
                            "ATENÇÃO: os valores são diferentes. "
                            "Investigue antes de usar os dados."
                        )
                    else:
                        print("Os valores conferem.")


# ==================================================
# 12. SALVAR OS ARQUIVOS CSV
# ==================================================

arquivo_anual = (
    pasta_tratados
    / f"{nome_base}_anual_2021_2025.csv"
)

arquivo_trimestral = (
    pasta_tratados
    / f"{nome_base}_trimestral_2021_2025.csv"
)

if base_anual is not None:

    base_anual.to_csv(
        arquivo_anual,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nArquivo anual salvo: {arquivo_anual}")

elif arquivo_anual.exists():

    arquivo_anual.unlink()
    print("Arquivo anual antigo removido.")

if base_trimestral is not None:

    base_trimestral.to_csv(
        arquivo_trimestral,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Arquivo trimestral salvo: {arquivo_trimestral}")

elif arquivo_trimestral.exists():

    arquivo_trimestral.unlink()
    print("Arquivo trimestral antigo removido.")


# ==================================================
# 13. RESUMO FINAL
# ==================================================

print("\n" + "=" * 55)
print("PROCESSAMENTO CONCLUÍDO")
print("=" * 55)

if base_anual is not None:
    print(f"Linhas na base anual: {len(base_anual)}")

if base_trimestral is not None:
    print(f"Linhas na base trimestral: {len(base_trimestral)}")

print(f"Pasta de saída: {pasta_tratados.resolve()}")
