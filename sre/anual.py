
from pathlib import Path
import re
import pandas as pd


# Pastas do projeto
RAIZ = Path(__file__).resolve().parent
ENTRADA = RAIZ / "data" / "tratados"
SAIDA = RAIZ / "data" / "padronizados" / "anuais"

SAIDA.mkdir(parents=True, exist_ok=True)


def identificar_ano(coluna):
    """
    Reconhece anos como 2021, 2022 ou 2025.
    """
    nome = str(coluna).strip()

    if re.fullmatch(r"(19|20)\d{2}", nome):
        ano = int(nome)

        return {
            "periodo": str(ano),
            "ano": ano,
            "frequencia": "anual"
        }

    return None


def transformar_base(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    periodos = {
        coluna: identificar_ano(coluna)
        for coluna in df.columns
    }

    periodos = {
        coluna: info
        for coluna, info in periodos.items()
        if info is not None
    }

    if not periodos:
        return None

    # Colunas que identificam o indicador
    colunas_id = [
        c for c in df.columns
        if c not in periodos
    ]

    # Transforma os anos em linhas
    longo = df.melt(
        id_vars=colunas_id,
        value_vars=list(periodos),
        var_name="periodo_original",
        value_name="valor"
    )

    # Adiciona os metadados anuais
    metadados = pd.DataFrame(
        [
            periodos[p]
            for p in longo["periodo_original"]
        ],
        index=longo.index
    )

    longo = longo.drop(columns="periodo_original")

    for coluna in metadados.columns:
        longo[coluna] = metadados[coluna]

    longo["valor"] = pd.to_numeric(
        longo["valor"],
        errors="coerce"
    )

    longo = longo.sort_values(
        "ano"
    ).reset_index(drop=True)

    return longo


def processar_bases():
    arquivos = list(ENTRADA.glob("*.csv"))

    if not arquivos:
        print(f"Nenhum CSV encontrado em {ENTRADA}")
        return

    for arquivo in arquivos:
        try:
            df = pd.read_csv(
                arquivo,
                sep=None,
                engine="python",
                encoding="utf-8-sig"
            )

            # Só processa bases que tenham colunas anuais
            df_novo = transformar_base(df)

            if df_novo is None:
                print(f"Ignorado: {arquivo.name}")
                continue

            destino = SAIDA / (
                arquivo.stem + "_anual.csv"
            )

            df_novo.to_csv(
                destino,
                index=False,
                encoding="utf-8-sig"
            )

            print(f"Salvo: {destino.name}")

        except Exception as erro:
            print(f"Erro em {arquivo.name}: {erro}")

    print("Processamento anual concluído!")


if __name__ == "__main__":
    processar_bases()