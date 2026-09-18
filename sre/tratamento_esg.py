import pandas as pd
import re
import unicodedata
from pathlib import Path


# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

caminho_arquivo = "data/original/Azul Fundamentos e Planilha 2T26.xlsx"
nome_aba = "Azul ESG"  # Altere para o nome exato da aba, se necessário
nome_base = "esg"
anos_desejados = ["2021", "2022", "2023", "2024", "2025"]

COLUNA_INDICADOR_EN = 1
COLUNA_INDICADOR_PT = 2


# ==========================================
# 2. ESTRUTURA DOS INDICADORES ESG
# ==========================================

estrutura_esg = {
    "Meio Ambiente": {
        "Combustível": [
            "Combustível consumido por ASK (Kg / ASK, milhares)",
            "Combustível consumido (GJ x 1000)",
        ],
        "Frota": [
            "Idade média da frota operacional¹",
        ],
    },
    "Social": {
        "Relações Trabalhistas": [
            "% de Rotatividade mensal de funcionários",
            "% de funcionários cobertos por acordos de negociação coletiva",
            "Voluntários",
        ],
        "Gênero e Diversidade": [
            "% Masculino",
            "% Feminino",
        ],
    },
    "Governança": {
        "Administração": [
            "% de Conselheiros Independentes",
            "% de Participação de mulheres no conselho de administração",
            "Idade média dos membros do Conselho de Administração",
            "% de Frequência da diretoria em reuniões",
            "Tamanho do Conselho de Administração",
            "% de Participação de mulheres em cargo de gestão",
        ],
    },
}


# ==========================================
# 3. FUNÇÕES AUXILIARES
# ==========================================

def normalizar_texto(texto):
    """Normaliza textos para facilitar a comparação dos indicadores."""

    if pd.isna(texto):
        return ""

    texto = str(texto).strip().lower()
    texto = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+", "", texto)

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def texto_vazio(texto):
    """Retorna True quando o conteúdo representa uma célula vazia."""

    if pd.isna(texto):
        return True

    return str(texto).strip().lower() in ["", "nan", "none", "nat"]


def possui_valor_numerico(linha, colunas_periodos):
    """Verifica se a linha possui pelo menos um valor numérico."""

    valores = pd.to_numeric(
        linha[colunas_periodos],
        errors="coerce",
    )

    return valores.notna().any()


def construir_mapa_indicadores(estrutura):
    """Cria um mapa de indicadores para grupo e subgrupo."""

    mapa = {}

    for grupo, subgrupos in estrutura.items():
        for subgrupo, indicadores in subgrupos.items():
            for indicador in indicadores:
                mapa[normalizar_texto(indicador)] = {
                    "grupo": grupo,
                    "subgrupo": subgrupo,
                }

    return mapa


def classificar_indicador(indicador_en, indicador_pt, mapa_indicadores):
    """Classifica o indicador usando o nome em português ou inglês."""

    candidatos = [
        normalizar_texto(indicador_pt),
        normalizar_texto(indicador_en),
    ]

    for candidato in candidatos:
        if candidato in mapa_indicadores:
            classificacao = mapa_indicadores[candidato]
            return (
                classificacao["grupo"],
                classificacao["subgrupo"],
            )

    return "Não classificado", "Não classificado"


def identificar_periodos(df):
    """Identifica a linha dos períodos e as colunas anuais e trimestrais."""

    linha_periodos = None
    padrao_ano = r"(2021|2022|2023|2024|2025)"
    padrao_trimestre = r"[1-4]T(?:21|22|23|24|25)"

    for indice, linha in df.iterrows():
        valores = linha.fillna("").astype(str).tolist()

        quantidade_anos = sum(
            bool(re.search(padrao_ano, valor.strip()))
            for valor in valores
        )

        quantidade_trimestres = sum(
            bool(re.search(padrao_trimestre, valor.strip()))
            for valor in valores
        )

        if quantidade_anos >= 3 or quantidade_trimestres >= 3:
            linha_periodos = indice
            break

    if linha_periodos is None:
        raise ValueError(
            "Não foi possível identificar a linha dos períodos."
        )

    colunas_anuais = {}
    colunas_trimestrais = {}

    for coluna, valor in df.iloc[linha_periodos].items():
        periodo = str(valor).strip()

        trimestre = re.search(
            r"([1-4]T(?:21|22|23|24|25))",
            periodo,
        )

        if trimestre:
            colunas_trimestrais[trimestre.group(1)] = coluna
            continue

        ano = re.search(
            r"(2021|2022|2023|2024|2025)",
            periodo,
        )

        if ano:
            colunas_anuais[ano.group(1)] = coluna

    return linha_periodos, colunas_anuais, colunas_trimestrais


def eh_linha_de_cabecalho(linha, colunas_periodos):
    """
    Identifica títulos, subtítulos e linhas de cabeçalho que não são
    indicadores reais.
    """

    indicador_en = linha["indicador_en"]
    indicador_pt = linha["indicador_pt"]

    # 1. Ignora linhas sem nome de indicador
    if texto_vazio(indicador_en) and texto_vazio(indicador_pt):
        return True

    texto_en = normalizar_texto(indicador_en)
    texto_pt = normalizar_texto(indicador_pt)

    # 2. Ignora títulos gerais da seção ESG
    termos_de_cabecalho = {
        "esg key indicators",
        "indicadores ambientais, sociais e de governanca",
        "environmental, social and governance indicators",
    }

    if texto_en in termos_de_cabecalho or texto_pt in termos_de_cabecalho:
        return True

    # 3. Ignora linhas em que os valores são exatamente os anos
    valores = pd.to_numeric(
        linha[colunas_periodos],
        errors="coerce",
    )

    if valores.notna().all():
        valores_texto = []

        for valor in valores:
            if float(valor).is_integer():
                valores_texto.append(str(int(valor)))
            else:
                valores_texto.append(str(valor))

        periodos_texto = [str(periodo) for periodo in colunas_periodos]

        if valores_texto == periodos_texto:
            return True

    return False


def preparar_base(df, colunas_reais, nomes_periodos, mapa_indicadores):
    """Prepara uma base anual ou trimestral de indicadores ESG."""

    base = df[
        ["indicador_en", "indicador_pt"] + colunas_reais
    ].copy()

    # Renomeia os índices das colunas para os períodos finais
    base.columns = [
        "indicador_en",
        "indicador_pt",
    ] + nomes_periodos

    grupos = []
    subgrupos = []
    indicadores_validos = []

    for _, linha in base.iterrows():

        # Remove títulos e subtítulos, como:
        # "ESG Key Indicators" e linhas com valores 2021, 2022 etc.
        if eh_linha_de_cabecalho(linha, nomes_periodos):
            grupos.append("")
            subgrupos.append("")
            indicadores_validos.append(False)
            continue

        indicador_en = linha["indicador_en"]
        indicador_pt = linha["indicador_pt"]

        if possui_valor_numerico(linha, nomes_periodos):
            grupo, subgrupo = classificar_indicador(
                indicador_en,
                indicador_pt,
                mapa_indicadores,
            )

            grupos.append(grupo)
            subgrupos.append(subgrupo)
            indicadores_validos.append(True)
        else:
            grupos.append("")
            subgrupos.append("")
            indicadores_validos.append(False)

    base["grupo"] = grupos
    base["subgrupo"] = subgrupos
    base["_indicador_valido"] = indicadores_validos

    # Mantém somente indicadores reais com pelo menos um valor numérico
    base = base[base["_indicador_valido"]].copy()
    base = base.drop(columns=["_indicador_valido"])

    # Converte os períodos para números
    for coluna in nomes_periodos:
        base[coluna] = pd.to_numeric(
            base[coluna],
            errors="coerce",
        )

    colunas_finais = [
        "grupo",
        "subgrupo",
        "indicador_en",
        "indicador_pt",
    ] + nomes_periodos

    return base[colunas_finais].reset_index(drop=True)


def salvar_ou_remover_arquivo(base, caminho):
    """Salva a base ou remove o arquivo antigo quando não há dados."""

    if base is not None:
        base.to_csv(
            caminho,
            index=False,
            encoding="utf-8-sig",
        )
        print(f"Arquivo salvo em: {caminho}")

    elif caminho.exists():
        caminho.unlink()
        print(f"Arquivo antigo removido: {caminho}")


def mostrar_nao_classificados(base, nome_base_processada):
    """Mostra os indicadores que ainda não foram classificados."""

    if base is None or base.empty:
        return

    nao_classificados = base[
        base["grupo"] == "Não classificado"
    ][["indicador_en", "indicador_pt"]].drop_duplicates()

    if not nao_classificados.empty:
        print(
            f"\nAtenção: indicadores {nome_base_processada} "
            "não classificados:"
        )
        print(nao_classificados.to_string(index=False))


# ==========================================
# 4. LEITURA DA PLANILHA
# ==========================================

df = pd.read_excel(
    caminho_arquivo,
    sheet_name=nome_aba,
    header=None,
)

print(f"Aba lida com sucesso: {nome_aba}")
print(f"Dimensões da planilha: {df.shape}")


# ==========================================
# 5. IDENTIFICAÇÃO DOS PERÍODOS
# ==========================================

(
    linha_periodos,
    colunas_anuais,
    colunas_trimestrais,
) = identificar_periodos(df)

print(f"Linha dos períodos identificada: {linha_periodos}")
print("\nColunas anuais identificadas:")
print(colunas_anuais)
print("\nColunas trimestrais identificadas:")
print(colunas_trimestrais)


# ==========================================
# 6. PREPARAÇÃO DOS INDICADORES
# ==========================================

df["indicador_en"] = df.iloc[:, COLUNA_INDICADOR_EN]
df["indicador_pt"] = df.iloc[:, COLUNA_INDICADOR_PT]

mapa_indicadores = construir_mapa_indicadores(estrutura_esg)


# ==========================================
# 7. ORDEM DOS TRIMESTRES
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
# 8. PASTA DE DESTINO
# ==========================================

pasta_tratados = Path("data/tratados")
pasta_tratados.mkdir(parents=True, exist_ok=True)


# ==========================================
# 9. BASE ANUAL
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
        mapa_indicadores=mapa_indicadores,
    )

    print("\nBase anual preparada com sucesso.")
else:
    print(
        "\nNenhum período anual encontrado. "
        "A base anual não será criada."
    )


# ==========================================
# 10. BASE TRIMESTRAL
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
        mapa_indicadores=mapa_indicadores,
    )

    print("Base trimestral preparada com sucesso.")
else:
    print(
        "Nenhum período trimestral encontrado. "
        "A base trimestral não será criada."
    )


# ==========================================
# 11. SALVAMENTO DOS ARQUIVOS
# ==========================================

arquivo_anual = pasta_tratados / "esg_anual_2021_2025.csv"
arquivo_trimestral = pasta_tratados / "esg_trimestral_2021_2025.csv"

salvar_ou_remover_arquivo(base_anual, arquivo_anual)
salvar_ou_remover_arquivo(base_trimestral, arquivo_trimestral)


# ==========================================
# 12. RESULTADO FINAL
# ==========================================

print("\nProcessamento concluído!")

if base_anual is not None:
    print(f"Linhas na base anual: {len(base_anual)}")

if base_trimestral is not None:
    print(f"Linhas na base trimestral: {len(base_trimestral)}")

mostrar_nao_classificados(base_anual, "anuais")
mostrar_nao_classificados(base_trimestral, "trimestrais")
