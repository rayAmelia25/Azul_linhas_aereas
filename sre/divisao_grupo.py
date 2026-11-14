
from pathlib import Path
import re
import unicodedata
import pandas as pd


# ============================================================
# CAMINHOS
# ============================================================

RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO_ENTRADA = (
    RAIZ
    / "data"
    / "tratados"
    / "balanco_trimestral_2021_2025.csv"
)

ARQUIVO_SAIDA = (
    RAIZ
    / "data"
    / "tratados"
    / "balanco_trimestral_2021_2025_estruturado.csv"
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(texto):
    """Padroniza textos para facilitar a identificação das contas."""
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().casefold()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def identificar_grupo(indicador):
    """Identifica os grupos principais do balanço."""

    indicador = normalizar_texto(indicador)

    if indicador == "ativo":
        return "Ativo"

    if indicador == "passivo":
        return "Passivo"

    if indicador.startswith("patrimonio liquido"):
        return "Patrimônio Líquido"

    return None


def identificar_subgrupo(indicador, grupo_atual):
    """Identifica os subgrupos do balanço."""

    indicador = normalizar_texto(indicador)

    # Ativo
    if indicador == "ativo circulante":
        return "Ativo circulante"

    if indicador == "ativo nao circulante":
        return "Ativo não circulante"

    # Passivo
    if indicador == "passivo circulante":
        return "Passivo circulante"

    if indicador in (
        "passivo nao circulante",
        "passivo não circulante",
    ):
        return "Passivo não circulante"

    if indicador == "nao circulante" and grupo_atual == "Passivo":
        return "Passivo não circulante"

    # Patrimônio líquido
    if grupo_atual == "Patrimônio Líquido":
        return "Patrimônio Líquido"

    return None


# ============================================================
# ESTRUTURAÇÃO DO BALANÇO
# ============================================================

def estruturar_balanco(df):
    """Adiciona grupo e subgrupo sem alterar os valores originais."""

    if "indicador_pt" not in df.columns:
        raise ValueError(
            "A coluna 'indicador_pt' não existe no arquivo."
        )

    df = df.copy()

    # Preserva o nome original e cria uma versão normalizada.
    df["indicador_pt_normalizado"] = (
        df["indicador_pt"].apply(normalizar_texto)
    )

    grupos = []
    subgrupos = []

    grupo_atual = ""
    subgrupo_atual = ""

    for _, linha in df.iterrows():

        indicador = linha["indicador_pt"]

        # Atualiza o grupo principal quando encontrar um cabeçalho.
        novo_grupo = identificar_grupo(indicador)

        if novo_grupo is not None:
            grupo_atual = novo_grupo
            subgrupo_atual = ""

        # Atualiza o subgrupo.
        novo_subgrupo = identificar_subgrupo(
            indicador,
            grupo_atual
        )

        if novo_subgrupo is not None:
            subgrupo_atual = novo_subgrupo

        grupos.append(grupo_atual)
        subgrupos.append(subgrupo_atual)

    df["grupo"] = grupos
    df["subgrupo"] = subgrupos

    return df


# ============================================================
# VALIDAÇÃO
# ============================================================

def validar_balanco(df):
    """Exibe verificações básicas da classificação."""

    print("\n" + "=" * 60)
    print("RESUMO DA BASE ESTRUTURADA")
    print("=" * 60)

    print(f"Quantidade de linhas: {len(df)}")
    print(f"Quantidade de colunas: {len(df.columns)}")

    print("\nQuantidade de linhas por grupo:")

    print(
        df["grupo"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nQuantidade de linhas por subgrupo:")

    print(
        df["subgrupo"]
        .value_counts(dropna=False)
        .to_string()
    )

    # Conferência dos empréstimos.
    emprestimos = df[
        df["indicador_pt_normalizado"].str.contains(
            r"emprestimos e financiamentos",
            regex=True,
            na=False
        )
    ]

    print("\n" + "=" * 60)
    print("EMPRÉSTIMOS E FINANCIAMENTOS")
    print("=" * 60)

    if emprestimos.empty:
        print("Nenhuma linha de empréstimos foi encontrada.")
    else:
        print(
            emprestimos[
                ["grupo", "subgrupo", "indicador_pt"]
            ].to_string(index=False)
        )

    # Mostra as contas que não receberam grupo.
    sem_grupo = df[df["grupo"].eq("")]

    print("\n" + "=" * 60)
    print("LINHAS SEM GRUPO IDENTIFICADO")
    print("=" * 60)

    if sem_grupo.empty:
        print("Todas as linhas receberam um grupo.")
    else:
        print(
            sem_grupo[["indicador_pt"]]
            .to_string(index=False)
        )


# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    if not ARQUIVO_ENTRADA.exists():
        raise FileNotFoundError(
            "Arquivo de entrada não encontrado:\n"
            f"{ARQUIVO_ENTRADA}"
        )

    # Lê a base original.
    df = pd.read_csv(ARQUIVO_ENTRADA)

    # Estrutura a base.
    df_estruturado = estruturar_balanco(df)

    # Cria a pasta de saída, se necessário.
    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Salva sem excluir ou alterar as linhas originais.
    df_estruturado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nBase estruturada com sucesso!")
    print(f"Arquivo salvo em:\n{ARQUIVO_SAIDA}")

    # Exibe as verificações.
    validar_balanco(df_estruturado)


if __name__ == "__main__":
    main()
