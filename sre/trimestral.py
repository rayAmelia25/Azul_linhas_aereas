
from pathlib import Path
import re
import pandas as pd


# Pastas do projeto
RAIZ = Path(__file__).resolve().parent
ENTRADA = RAIZ / "data" / "tratados"
SAIDA = RAIZ / "data" / "padronizados" / "trimestrais"

SAIDA.mkdir(parents=True, exist_ok=True)


def identificar_trimestre(coluna):
    """
    Reconhece períodos como 1T21, 2T23 ou 4T25.
    """
    resultado = re.fullmatch(
        r"([1-4])T(\d{2}|\d{4})",
        str(coluna).strip().upper()
    )

    if not resultado:
        return None

    trimestre = int(resultado.group(1))
    ano = int(resultado.group(2))

    if ano < 100:
        ano += 2000

    return {
        "periodo": f"{trimestre}T{ano % 100:02d}",
        "ano": ano,
        "trimestre": trimestre,
        "semestre": 1 if trimestre <= 2 else 2,
        "frequencia": "trimestral"
    }


def transformar_base(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    periodos = {
        coluna: identificar_trimestre(coluna)
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

    # Transforma as colunas dos trimestres em linhas
    longo = df.melt(
        id_vars=colunas_id,
        value_vars=list(periodos),
        var_name="periodo_original",
        value_name="valor"
    )

    # Adiciona os metadados de cada período
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

    # Converte valores numéricos sem alterar os ausentes
    longo["valor"] = pd.to_numeric(
        longo["valor"],
        errors="coerce"
    )

    # Organiza cronologicamente
    longo = longo.sort_values(
        ["ano", "trimestre"]
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

            # Só processa bases que tenham períodos trimestrais
            df_novo = transformar_base(df)

            if df_novo is None:
                print(f"Ignorado: {arquivo.name}")
                continue

            destino = SAIDA / (
                arquivo.stem + "_trimestral.csv"
            )

            df_novo.to_csv(
                destino,
                index=False,
                encoding="utf-8-sig"
            )

            print(f"Salvo: {destino.name}")

        except Exception as erro:
            print(f"Erro em {arquivo.name}: {erro}")

    print("Processamento trimestral concluído!")


if __name__ == "__main__":
    processar_bases()
