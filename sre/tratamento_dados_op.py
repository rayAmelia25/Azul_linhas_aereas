import pandas as pd
import re
import unicodedata
from pathlib import Path


# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

caminho_arquivo = "data/original/Azul Fundamentos e Planilha 2T26.xlsx"

# Nome exato da aba
nome_aba = "Dados Op. | Operating Data"

# Nome dos arquivos gerados
nome_base = "dados_op"

# Períodos desejados
anos_desejados = ["2021", "2022", "2023", "2024", "2025"]

# Colunas dos nomes dos indicadores na planilha original
COLUNA_INDICADOR_EN = 1
COLUNA_INDICADOR_PT = 2


# ==========================================
# 2. FUNÇÕES AUXILIARES
# ==========================================

def texto_vazio(valor):
    """Verifica se o valor está vazio."""

    if pd.isna(valor):
        return True

    texto = str(valor).strip().lower()

    return texto in ["", "nan", "none", "nat"]


def normalizar_texto(texto):
    """Normaliza o texto para facilitar comparações."""

    if texto_vazio(texto):
        return ""

    texto = str(texto).strip().lower()

    # Remove referências sobrescritas
    texto = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+", "", texto)

    # Remove acentos
    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    # Remove espaços duplicados
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def possui_valor_numerico(linha, colunas_periodos):
    """Verifica se a linha possui pelo menos um valor numérico."""

    valores = pd.to_numeric(
        linha[colunas_periodos],
        errors="coerce",
    )

    return valores.notna().any()


# ==========================================
# 3. IDENTIFICAR PERÍODOS
# ==========================================

def identificar_periodos(df):

    linha_periodos = None

    padrao_ano = r"(2021|2022|2023|2024|2025)"
    padrao_trimestre = r"[1-4]T(?:21|22|23|24|25)"

    # --------------------------------------
    # Procurar linha dos períodos
    # --------------------------------------

    for indice, linha in df.iterrows():

        valores = linha.fillna("").astype(str).tolist()

        quantidade_anos = sum(
            bool(
                re.search(
                    padrao_ano,
                    valor.strip()
                )
            )
            for valor in valores
        )

        quantidade_trimestres = sum(
            bool(
                re.search(
                    padrao_trimestre,
                    valor.strip()
                )
            )
            for valor in valores
        )

        if (
            quantidade_anos >= 3
            or quantidade_trimestres >= 3
        ):
            linha_periodos = indice
            break

    if linha_periodos is None:

        raise ValueError(
            "Não foi possível identificar a linha dos períodos."
        )

    colunas_anuais = {}
    colunas_trimestrais = {}

    # --------------------------------------
    # Identificar cada coluna
    # --------------------------------------

    for coluna, valor in df.iloc[linha_periodos].items():

        periodo = str(valor).strip()

        # Trimestre
        trimestre_encontrado = re.search(
            r"([1-4]T(?:21|22|23|24|25))",
            periodo,
        )

        if trimestre_encontrado:

            trimestre = trimestre_encontrado.group(1)

            colunas_trimestrais[trimestre] = coluna

            continue

        # Ano
        ano_encontrado = re.search(
            r"(2021|2022|2023|2024|2025)",
            periodo,
        )

        if ano_encontrado:

            ano = ano_encontrado.group(1)

            colunas_anuais[ano] = coluna

    return (
        linha_periodos,
        colunas_anuais,
        colunas_trimestrais,
    )


# ==========================================
# 4. IDENTIFICAR DOMÉSTICO / INTERNACIONAL
# ==========================================

def identificar_tipo_geografico(
    indicador_en,
    indicador_pt,
):
    """
    Identifica se a linha é:

    - Doméstico
    - Internacional
    - Nenhum dos dois
    """

    textos = [
        normalizar_texto(indicador_en),
        normalizar_texto(indicador_pt),
    ]

    for texto in textos:

        if texto in [
            "domestic",
            "domestico",
        ]:
            return "Doméstico"

        if texto in [
            "international",
            "internacional",
        ]:
            return "Internacional"

    return None


# ==========================================
# 5. IDENTIFICAR TÍTULOS
# ==========================================

def eh_titulo(indicador_en, indicador_pt):
    """
    Identifica títulos que não devem aparecer
    como indicadores na base final.
    """

    textos = [
        normalizar_texto(indicador_en),
        normalizar_texto(indicador_pt),
    ]

    textos = [
        texto
        for texto in textos
        if texto
    ]

    titulos = [
        "operational data",
        "dados operacionais",
        "operational indicators",
        "indicadores operacionais",
    ]

    return any(
        texto in titulos
        for texto in textos
    )


# ==========================================
# 6. PREPARAR A BASE
# ==========================================

def preparar_base(
    df,
    colunas_reais,
    nomes_periodos,
):
    """
    Organiza os Dados Operacionais.

    Estrutura:

    Indicador - Doméstico
    Indicador - Internacional
    Indicador

    Exemplo:

    Passageiros pagantes transportados por quilômetros
    voados (RPKs) - Doméstico

    Passageiros pagantes transportados por quilômetros
    voados (RPKs) - Internacional
    """

    # --------------------------------------
    # Selecionar colunas
    # --------------------------------------

    base = df[
        [
            "indicador_en",
            "indicador_pt",
        ]
        + colunas_reais
    ].copy()

    # Renomear períodos
    base.columns = (
        [
            "indicador_en",
            "indicador_pt",
        ]
        + nomes_periodos
    )

    # --------------------------------------
    # Guardar indicador principal
    # --------------------------------------

    indicador_principal_en = ""
    indicador_principal_pt = ""

    registros = []

    # --------------------------------------
    # Percorrer as linhas
    # --------------------------------------

    for _, linha in base.iterrows():

        indicador_en = (
            str(linha["indicador_en"]).strip()
            if not pd.isna(linha["indicador_en"])
            else ""
        )

        indicador_pt = (
            str(linha["indicador_pt"]).strip()
            if not pd.isna(linha["indicador_pt"])
            else ""
        )

        # ----------------------------------
        # Ignorar linhas vazias
        # ----------------------------------

        if (
            texto_vazio(indicador_en)
            and texto_vazio(indicador_pt)
        ):
            continue

        # ----------------------------------
        # Ignorar títulos gerais
        # ----------------------------------

        if eh_titulo(
            indicador_en,
            indicador_pt,
        ):
            continue

        # ----------------------------------
        # Verificar valores
        # ----------------------------------

        tem_valor = possui_valor_numerico(
            linha,
            nomes_periodos,
        )

        # ----------------------------------
        # Identificar localização
        # ----------------------------------

        tipo_geografico = identificar_tipo_geografico(
            indicador_en,
            indicador_pt,
        )

        # ==================================
        # DOMÉSTICO / INTERNACIONAL
        # ==================================

        if tipo_geografico is not None:

            # Se não existe indicador principal,
            # não há como associar a linha.
            if (
                texto_vazio(indicador_principal_en)
                and texto_vazio(indicador_principal_pt)
            ):
                continue

            if not tem_valor:
                continue

            # --------------------------------
            # Nome final do indicador
            # --------------------------------

            if not texto_vazio(indicador_principal_en):

                indicador_final_en = (
                    f"{indicador_principal_en}"
                    f" - {tipo_geografico}"
                )

            else:

                indicador_final_en = (
                    f"{indicador_principal_pt}"
                    f" - {tipo_geografico}"
                )

            if not texto_vazio(indicador_principal_pt):

                indicador_final_pt = (
                    f"{indicador_principal_pt}"
                    f" - {tipo_geografico}"
                )

            else:

                indicador_final_pt = (
                    f"{indicador_principal_en}"
                    f" - {tipo_geografico}"
                )

            registro = {
                "indicador_en": indicador_final_en,
                "indicador_pt": indicador_final_pt,
            }

            for periodo in nomes_periodos:

                registro[periodo] = linha[periodo]

            registros.append(registro)

            continue

        # ==================================
        # INDICADOR PRINCIPAL
        # ==================================

        # Se não possui valores, significa que
        # provavelmente é um título do próximo indicador.
        if not tem_valor:

            indicador_principal_en = indicador_en
            indicador_principal_pt = indicador_pt

            continue

        # ----------------------------------
        # Atualizar indicador principal
        # ----------------------------------

        indicador_principal_en = indicador_en
        indicador_principal_pt = indicador_pt

        # ----------------------------------
        # Criar registro TOTAL
        # ----------------------------------

        registro = {
            "indicador_en": indicador_principal_en,
            "indicador_pt": indicador_principal_pt,
        }

        for periodo in nomes_periodos:

            registro[periodo] = linha[periodo]

        registros.append(registro)

    # ======================================
    # CRIAR DATAFRAME
    # ======================================

    if not registros:

        return pd.DataFrame(
            columns=[
                "indicador_en",
                "indicador_pt",
            ]
            + nomes_periodos
        )

    resultado = pd.DataFrame(registros)

    # --------------------------------------
    # Converter períodos para números
    # --------------------------------------

    for periodo in nomes_periodos:

        resultado[periodo] = pd.to_numeric(
            resultado[periodo],
            errors="coerce",
        )

    # --------------------------------------
    # Remover linhas sem valores
    # --------------------------------------

    resultado = resultado[
        resultado[nomes_periodos]
        .notna()
        .any(axis=1)
    ].copy()

    # --------------------------------------
    # Organizar colunas
    # --------------------------------------

    resultado = resultado[
        [
            "indicador_en",
            "indicador_pt",
        ]
        + nomes_periodos
    ]

    return resultado.reset_index(drop=True)


# ==========================================
# 7. SALVAR ARQUIVO
# ==========================================

def salvar_ou_remover_arquivo(
    base,
    caminho,
):

    if base is not None:

        base.to_csv(
            caminho,
            index=False,
            encoding="utf-8-sig",
        )

        print(
            f"Arquivo salvo em: {caminho}"
        )

    elif caminho.exists():

        caminho.unlink()

        print(
            f"Arquivo antigo removido: {caminho}"
        )


# ==========================================
# 8. LER PLANILHA
# ==========================================

df = pd.read_excel(
    caminho_arquivo,
    sheet_name=nome_aba,
    header=None,
)

print(
    f"Aba lida com sucesso: {nome_aba}"
)

print(
    f"Dimensões da planilha: {df.shape}"
)


# ==========================================
# 9. IDENTIFICAR PERÍODOS
# ==========================================

(
    linha_periodos,
    colunas_anuais,
    colunas_trimestrais,
) = identificar_periodos(df)

print(
    f"Linha dos períodos identificada: "
    f"{linha_periodos}"
)

print(
    "\nColunas anuais identificadas:"
)

print(colunas_anuais)

print(
    "\nColunas trimestrais identificadas:"
)

print(colunas_trimestrais)


# ==========================================
# 10. PREPARAR INDICADORES
# ==========================================

df["indicador_en"] = (
    df.iloc[:, COLUNA_INDICADOR_EN]
)

df["indicador_pt"] = (
    df.iloc[:, COLUNA_INDICADOR_PT]
)


# ==========================================
# 11. ORDEM DOS TRIMESTRES
# ==========================================

ordem_trimestres = [
    f"{trimestre}T{ano}"
    for ano in [
        "21",
        "22",
        "23",
        "24",
        "25",
    ]
    for trimestre in [
        "1",
        "2",
        "3",
        "4",
    ]
]

trimestres_encontrados = [
    trimestre
    for trimestre in ordem_trimestres
    if trimestre in colunas_trimestrais
]


# ==========================================
# 12. PASTA DE DESTINO
# ==========================================

pasta_tratados = Path(
    "data/tratados"
)

pasta_tratados.mkdir(
    parents=True,
    exist_ok=True,
)


# ==========================================
# 13. BASE ANUAL
# ==========================================

base_anual = None

anos_encontrados = [
    ano
    for ano in anos_desejados
    if ano in colunas_anuais
]

if anos_encontrados:

    colunas_anuais_reais = [
        colunas_anuais[ano]
        for ano in anos_encontrados
    ]

    base_anual = preparar_base(
        df=df,
        colunas_reais=colunas_anuais_reais,
        nomes_periodos=anos_encontrados,
    )

    print(
        "\nBase anual preparada com sucesso."
    )

else:

    print(
        "\nNenhum período anual encontrado."
    )


# ==========================================
# 14. BASE TRIMESTRAL
# ==========================================

base_trimestral = None

if trimestres_encontrados:

    colunas_trimestrais_reais = [
        colunas_trimestrais[trimestre]
        for trimestre in trimestres_encontrados
    ]

    base_trimestral = preparar_base(
        df=df,
        colunas_reais=colunas_trimestrais_reais,
        nomes_periodos=trimestres_encontrados,
    )

    print(
        "Base trimestral preparada com sucesso."
    )

else:

    print(
        "Nenhum período trimestral encontrado."
    )


# ==========================================
# 15. SALVAR ARQUIVOS
# ==========================================

arquivo_anual = (
    pasta_tratados
    / "dados_operacionais_anual_2021_2025.csv"
)

arquivo_trimestral = (
    pasta_tratados
    / "dados_operacionais_trimestral_2021_2025.csv"
)


salvar_ou_remover_arquivo(
    base_anual,
    arquivo_anual,
)

salvar_ou_remover_arquivo(
    base_trimestral,
    arquivo_trimestral,
)


# ==========================================
# 16. RESULTADO FINAL
# ==========================================

print(
    "\n=========================================="
)

print(
    "PROCESSAMENTO CONCLUÍDO"
)

print(
    "=========================================="
)

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

print(
    "\nArquivos gerados em:"
)

print(
    pasta_tratados
)