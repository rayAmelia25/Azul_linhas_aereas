import pandas as pd
import re
from pathlib import Path


# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

caminho_arquivo = "data/original/Azul Fundamentos e Planilha 2T26.xlsx"

# Nome da aba analisada
nome_aba = "DRE | Income Statement"

# Nome utilizado nos arquivos gerados
nome_base = "balanco"

# Períodos desejados
anos_desejados = ["2021", "2022", "2023", "2024", "2025"]

# Colunas dos nomes dos indicadores na planilha original
COLUNA_INDICADOR_EN = 1
COLUNA_INDICADOR_PT = 2


# ==========================================
# 2. LEITURA DA PLANILHA
# ==========================================

df = pd.read_excel(
    caminho_arquivo,
    sheet_name=nome_aba,
    header=None
)

print(f"Aba lida com sucesso: {nome_aba}")
print(f"Dimensões da planilha: {df.shape}")


# ==========================================
# 3. IDENTIFICAR A LINHA DOS PERÍODOS
# ==========================================

linha_periodos = None

padrao_ano = r"(2021|2022|2023|2024|2025)"
padrao_trimestre = r"[1-4]T(?:21|22|23|24|25)"

for indice, linha in df.iterrows():

    valores = linha.fillna("").astype(str).tolist()

    quantidade_anos = 0
    quantidade_trimestres = 0

    for valor in valores:

        valor = valor.strip()

        if re.search(padrao_ano, valor):
            quantidade_anos += 1

        if re.search(padrao_trimestre, valor):
            quantidade_trimestres += 1

    # A linha de períodos deve conter vários anos
    # ou vários trimestres
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

    # Identificar trimestres
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
# 5. DEFINIR A ORDEM DOS TRIMESTRES
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


# ==========================================
# 6. FUNÇÕES AUXILIARES
# ==========================================

def obter_texto_indicador(linha):

    indicador_en = linha.iloc[COLUNA_INDICADOR_EN]
    indicador_pt = linha.iloc[COLUNA_INDICADOR_PT]

    if pd.isna(indicador_pt):
        indicador_pt = ""

    if pd.isna(indicador_en):
        indicador_en = ""

    return (
        str(indicador_en).strip(),
        str(indicador_pt).strip()
    )


def possui_valor_numerico(linha, colunas_periodos):

    valores = pd.to_numeric(
        linha[colunas_periodos],
        errors="coerce"
    )

    return valores.notna().any()


def texto_valido_para_categoria(texto):

    if not texto or texto.lower() == "nan":
        return False

    # Evitar textos muito longos, que geralmente são observações
    if len(texto) > 80:
        return False

    # Evitar frases com características de observação
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

    texto_minusculo = texto.lower()

    for sinal in sinais_de_observacao:
        if sinal in texto_minusculo:
            return False

    return True


def eh_grupo_principal(texto):

    texto_minusculo = texto.lower()

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
        palavra in texto_minusculo
        for palavra in palavras_de_grupo
    )


def identificar_categorias(base, colunas_periodos):

    grupo_atual = ""
    subgrupo_atual = ""

    grupos = []
    subgrupos = []
    indicadores_validos = []

    for _, linha in base.iterrows():

        indicador_en, indicador_pt = obter_texto_indicador(linha)

        # Preferir o nome em português
        texto_principal = indicador_pt

        if not texto_principal:
            texto_principal = indicador_en

        tem_valor = possui_valor_numerico(
            linha,
            colunas_periodos
        )

        # ------------------------------------------
        # Linhas que possuem valores financeiros
        # ------------------------------------------

        if tem_valor:

            grupos.append(grupo_atual)
            subgrupos.append(subgrupo_atual)
            indicadores_validos.append(True)

        # ------------------------------------------
        # Linhas sem valores: possíveis categorias
        # ------------------------------------------

        else:

            eh_categoria = texto_valido_para_categoria(
                texto_principal
            )

            if eh_categoria:

                if eh_grupo_principal(texto_principal):

                    grupo_atual = texto_principal
                    subgrupo_atual = ""

                else:

                    # Caso já exista um grupo, considerar
                    # o novo título como subgrupo
                    if grupo_atual:
                        subgrupo_atual = texto_principal

                    else:
                        grupo_atual = texto_principal

            grupos.append("")
            subgrupos.append("")
            indicadores_validos.append(False)

    base = base.copy()

    base["grupo"] = grupos
    base["subgrupo"] = subgrupos
    base["_indicador_valido"] = indicadores_validos

    # Manter somente as linhas que possuem valores financeiros
    base = base[
        base["_indicador_valido"]
    ].copy()

    base = base.drop(
        columns=["_indicador_valido"]
    )

    return base


def limpar_base(base, colunas_periodos):

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

    # Converter os valores dos períodos para números
    for coluna in colunas_periodos:

        base[coluna] = pd.to_numeric(
            base[coluna],
            errors="coerce"
        )

    # Remover linhas que não possuem nenhum valor numérico
    base = base[
        base[colunas_periodos]
        .notna()
        .any(axis=1)
    ].copy()

    # Organizar as colunas
    colunas_organizadas = [
        "grupo",
        "subgrupo",
        "indicador_en",
        "indicador_pt"
    ] + colunas_periodos

    base = base[colunas_organizadas]

    # Reiniciar os índices
    base = base.reset_index(drop=True)

    return base


# ==========================================
# 7. PREPARAR OS NOMES DOS INDICADORES
# ==========================================

df["indicador_en"] = df.iloc[:, COLUNA_INDICADOR_EN]
df["indicador_pt"] = df.iloc[:, COLUNA_INDICADOR_PT]


# ==========================================
# 8. CRIAR A PASTA DE DESTINO
# ==========================================

pasta_tratados = Path("data/tratados")

pasta_tratados.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# 9. CRIAR A BASE ANUAL
# ==========================================

base_anual = None

anos_encontrados = [
    ano
    for ano in anos_desejados
    if ano in colunas_anuais
]

if anos_encontrados:

    colunas_anuais_selecionadas = [
        colunas_anuais[ano]
        for ano in anos_encontrados
    ]

    base_anual = df[
        ["indicador_en", "indicador_pt"]
        + colunas_anuais_selecionadas
    ].copy()

    base_anual.columns = (
        ["indicador_en", "indicador_pt"]
        + anos_encontrados
    )

    # Identificar grupos e subgrupos
    base_anual = identificar_categorias(
        base_anual,
        anos_encontrados
    )

    # Limpar a base
    base_anual = limpar_base(
        base_anual,
        anos_encontrados
    )

    print("\nBase anual preparada com sucesso.")

else:

    print(
        "\nNenhum período anual encontrado. "
        "A base anual não será criada."
    )


# ==========================================
# 10. CRIAR A BASE TRIMESTRAL
# ==========================================

base_trimestral = None

if trimestres_encontrados:

    colunas_trimestrais_selecionadas = [
        colunas_trimestrais[trimestre]
        for trimestre in trimestres_encontrados
    ]

    base_trimestral = df[
        ["indicador_en", "indicador_pt"]
        + colunas_trimestrais_selecionadas
    ].copy()

    base_trimestral.columns = (
        ["indicador_en", "indicador_pt"]
        + trimestres_encontrados
    )

    # Identificar grupos e subgrupos
    base_trimestral = identificar_categorias(
        base_trimestral,
        trimestres_encontrados
    )

    # Limpar a base
    base_trimestral = limpar_base(
        base_trimestral,
        trimestres_encontrados
    )

    print("Base trimestral preparada com sucesso.")

else:

    print(
        "Nenhum período trimestral encontrado. "
        "A base trimestral não será criada."
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


# Salvar ou remover o arquivo anual
if base_anual is not None:

    base_anual.to_csv(
        arquivo_anual,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Arquivo anual salvo em: {arquivo_anual}")

else:

    if arquivo_anual.exists():
        arquivo_anual.unlink()
        print("Arquivo anual antigo removido.")


# Salvar ou remover o arquivo trimestral
if base_trimestral is not None:

    base_trimestral.to_csv(
        arquivo_trimestral,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Arquivo trimestral salvo em: "
        f"{arquivo_trimestral}"
    )

else:

    if arquivo_trimestral.exists():
        arquivo_trimestral.unlink()
        print("Arquivo trimestral antigo removido.")


# ==========================================
# 12. RESULTADO FINAL
# ==========================================

print("\nProcessamento concluído!")

if base_anual is not None:
    print(
        f"Linhas na base anual: "
        f"{len(base_anual)}"
    )

if base_trimestral is not None:
    print(
        f"Linhas na base trimestral: "
        f"{len(base_trimestral)}"
    )