import pandas as pd
import re
from pathlib import Path


# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

caminho_arquivo = "data/original/Azul Fundamentos e Planilha 2T26.xlsx"

nome_aba = "Balanço | Balance Sheet"

nome_base = "dre"

anos_desejados = ["2021", "2022", "2023", "2024", "2025"]

COLUNA_INDICADOR_EN = 1
COLUNA_INDICADOR_PT = 2


# ==========================================
# 2. ESTRUTURA DA DRE
# ==========================================

estrutura_dre = {
    "Receita líquida": [
        "Transporte de passageiros",
        "Outras receitas",
        "Total receita líquida"
    ],

    "Custos dos serviços prestados": [
        "Combustível de aviação",
        "Salários e benefícios",
        "Outros aluguéis & ACMI",
        "Tarifas aeroportuárias",
        "Prestação de serviços de tráfego",
        "Comerciais e marketing",
        "Material de manutenção e reparo",
        "Depreciação e amortização",
        "Incentivo baseado em ações",
        "Outras despesas operacionais, líquidas",
        "Total custos dos serviços prestados"
    ],

    "Lucro / (prejuízo) operacional": [
        "Margem EBIT"
    ],

    "Resultado Financeiro": [
        "Receita financeira",
        "Despesas financeiras",
        "Instrumentos financeiros derivativos",
        "Variações monetárias e cambiais, líquida"
    ],

    "Resultado de transações relacionadas, net": [],

    "Lucro (prejuízo) antes do IR e contribuição": [
        "Imposto de renda e contribuição social",
        "Imposto de renda e contribuição social diferidos"
    ],

    "Prejuízo líquido do exercício": [
        "Margem líquida"
    ],

    "EBITDA": [
        "Margem EBITDA"
    ]
}


# ==========================================
# 3. NORMALIZAR TEXTOS
# ==========================================

def normalizar_texto(texto):

    if pd.isna(texto):
        return ""

    texto = str(texto).strip().lower()

    texto = re.sub(r"\s+", " ", texto)

    return texto


estrutura_normalizada = {}

for grupo, indicadores in estrutura_dre.items():

    estrutura_normalizada[normalizar_texto(grupo)] = {
        "nome_original": grupo,
        "indicadores": {
            normalizar_texto(indicador): indicador
            for indicador in indicadores
        }
    }


# ==========================================
# 4. LEITURA DA PLANILHA
# ==========================================

df = pd.read_excel(
    caminho_arquivo,
    sheet_name=nome_aba,
    header=None
)

print(f"Aba lida com sucesso: {nome_aba}")
print(f"Dimensões da planilha: {df.shape}")


# ==========================================
# 5. IDENTIFICAR A LINHA DOS PERÍODOS
# ==========================================

linha_periodos = None

for indice, linha in df.iterrows():

    valores = linha.fillna("").astype(str).tolist()

    quantidade_periodos = sum(
        bool(
            re.search(
                r"(2021|2022|2023|2024|2025)|"
                r"[1-4]T(?:21|22|23|24|25)",
                valor
            )
        )
        for valor in valores
    )

    if quantidade_periodos >= 3:

        linha_periodos = indice
        break

if linha_periodos is None:

    raise ValueError(
        "Não foi possível identificar a linha dos períodos."
    )


print(f"Linha dos períodos identificada: {linha_periodos}")


# ==========================================
# 6. IDENTIFICAR AS COLUNAS DOS PERÍODOS
# ==========================================

colunas_anuais = {}
colunas_trimestrais = {}

for coluna, valor in df.iloc[linha_periodos].items():

    periodo = str(valor).strip()

    trimestre = re.search(
        r"([1-4]T(?:21|22|23|24|25))",
        periodo
    )

    if trimestre:

        nome_trimestre = trimestre.group(1)

        colunas_trimestrais[nome_trimestre] = coluna

        continue

    ano = re.search(
        r"(2021|2022|2023|2024|2025)",
        periodo
    )

    if ano:

        nome_ano = ano.group(1)

        colunas_anuais[nome_ano] = coluna


print("\nColunas anuais identificadas:")
print(colunas_anuais)

print("\nColunas trimestrais identificadas:")
print(colunas_trimestrais)


# ==========================================
# 7. IDENTIFICAR OS INDICADORES DA DRE
# ==========================================

def identificar_grupo_subgrupo(indicador_pt):

    texto = normalizar_texto(indicador_pt)

    # Verificar se o texto é um grupo
    if texto in estrutura_normalizada:

        return estrutura_normalizada[texto]["nome_original"], ""

    # Verificar se o texto é um indicador de algum grupo
    for grupo, dados in estrutura_normalizada.items():

        if texto in dados["indicadores"]:

            return (
                dados["nome_original"],
                ""
            )

    return None, None


# ==========================================
# 8. PREPARAR OS INDICADORES
# ==========================================

indicadores = df.iloc[:, [
    COLUNA_INDICADOR_EN,
    COLUNA_INDICADOR_PT
]].copy()

indicadores.columns = [
    "indicador_en",
    "indicador_pt"
]


# Criar as classificações
grupos = []
subgrupos = []
linhas_validas = []

for _, linha in indicadores.iterrows():

    indicador_pt = linha["indicador_pt"]

    grupo, subgrupo = identificar_grupo_subgrupo(
        indicador_pt
    )

    if grupo is not None:

        grupos.append(grupo)
        subgrupos.append(subgrupo)
        linhas_validas.append(True)

    else:

        grupos.append("")
        subgrupos.append("")
        linhas_validas.append(False)


# ==========================================
# 9. PREPARAR OS DADOS ANUAIS
# ==========================================

anos_encontrados = [
    ano
    for ano in anos_desejados
    if ano in colunas_anuais
]

base_anual = None

if anos_encontrados:

    colunas_anuais_selecionadas = [
        colunas_anuais[ano]
        for ano in anos_encontrados
    ]

    base_anual = df.iloc[
        :,
        [
            COLUNA_INDICADOR_EN,
            COLUNA_INDICADOR_PT
        ] + colunas_anuais_selecionadas
    ].copy()

    base_anual.columns = (
        ["indicador_en", "indicador_pt"]
        + anos_encontrados
    )

    base_anual.insert(0, "subgrupo", subgrupos)
    base_anual.insert(0, "grupo", grupos)

    base_anual["_linha_valida"] = linhas_validas

    base_anual = base_anual[
        base_anual["_linha_valida"]
    ].drop(columns="_linha_valida")

    print("\nBase anual preparada.")


# ==========================================
# 10. PREPARAR OS DADOS TRIMESTRAIS
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

base_trimestral = None

if trimestres_encontrados:

    colunas_trimestrais_selecionadas = [
        colunas_trimestrais[trimestre]
        for trimestre in trimestres_encontrados
    ]

    base_trimestral = df.iloc[
        :,
        [
            COLUNA_INDICADOR_EN,
            COLUNA_INDICADOR_PT
        ] + colunas_trimestrais_selecionadas
    ].copy()

    base_trimestral.columns = (
        ["indicador_en", "indicador_pt"]
        + trimestres_encontrados
    )

    base_trimestral.insert(0, "subgrupo", subgrupos)
    base_trimestral.insert(0, "grupo", grupos)

    base_trimestral["_linha_valida"] = linhas_validas

    base_trimestral = base_trimestral[
        base_trimestral["_linha_valida"]
    ].drop(columns="_linha_valida")

    print("Base trimestral preparada.")


# ==========================================
# 11. CRIAR A PASTA DE DESTINO
# ==========================================

pasta_tratados = Path("data/tratados")

pasta_tratados.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# 12. SALVAR OS ARQUIVOS
# ==========================================

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

    print(f"Arquivo anual salvo em: {arquivo_anual}")

else:

    if arquivo_anual.exists():

        arquivo_anual.unlink()

        print("Arquivo anual antigo removido.")


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
# 13. RESULTADO FINAL
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