import requests
import pandas as pd

from pathlib import Path
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re


# ==========================================================
# 1. CONFIGURAÇÕES
# ==========================================================

ANOS = range(2021, 2026)

# Código CVM da Azul S.A.
CODIGO_CVM = "24112"

# Diretórios oficiais da CVM
URLS_CVM = {
    "itr": (
        "https://dados.cvm.gov.br/dados/"
        "cia_aberta/doc/itr/DADOS/"
    ),

    "dfp": (
        "https://dados.cvm.gov.br/dados/"
        "cia_aberta/doc/dfp/DADOS/"
    )
}

# Pastas do projeto
PASTA_RAW = Path("data/raw/cvm")

PASTA_TRATADOS = Path("data/tratados/cvm")

PASTA_RAW.mkdir(
    parents=True,
    exist_ok=True
)

PASTA_TRATADOS.mkdir(
    parents=True,
    exist_ok=True
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


# ==========================================================
# 2. OBTER LINKS DOS ARQUIVOS DA CVM
# ==========================================================

def obter_links_cvm(url_base):
    """
    Acessa o diretório da CVM e extrai os links
    dos arquivos ZIP disponíveis.
    """

    print(f"\nAcessando: {url_base}")

    resposta = requests.get(
        url_base,
        headers=HEADERS,
        timeout=60
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(
        resposta.text,
        "html.parser"
    )

    links = []

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if not href.lower().endswith(".zip"):
            continue

        url_completa = urljoin(
            url_base,
            href
        )

        links.append(url_completa)

    return links


# ==========================================================
# 3. LOCALIZAR O ARQUIVO DO ANO
# ==========================================================

def localizar_arquivo_ano(links, tipo, ano):
    """
    Localiza o ZIP correspondente ao tipo de documento
    e ao ano solicitado.
    """

    nome_procurado = (
        f"{tipo}_cia_aberta_{ano}.zip"
    ).lower()

    for link in links:

        nome_arquivo = Path(
            urlparse(link).path
        ).name.lower()

        if nome_arquivo == nome_procurado:

            return link

    return None


# ==========================================================
# 4. BAIXAR O ARQUIVO
# ==========================================================

def baixar_arquivo(url, caminho_zip):

    if caminho_zip.exists():

        print(
            f"Arquivo já baixado: "
            f"{caminho_zip.name}"
        )

        return

    print(f"Baixando: {url}")

    resposta = requests.get(
        url,
        headers=HEADERS,
        timeout=300
    )

    resposta.raise_for_status()

    caminho_zip.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho_zip.write_bytes(
        resposta.content
    )

    print("Download concluído!")


# ==========================================================
# 5. EXTRAIR O ARQUIVO ZIP
# ==========================================================

def extrair_zip(caminho_zip, pasta_destino):

    pasta_destino.mkdir(
        parents=True,
        exist_ok=True
    )

    arquivos_existentes = list(
        pasta_destino.rglob("*.csv")
    )

    if arquivos_existentes:

        print("Arquivos já extraídos. Pulando etapa.")

        return

    print(f"Extraindo: {caminho_zip.name}")

    try:

        with ZipFile(caminho_zip, "r") as arquivo_zip:

            arquivo_zip.extractall(
                pasta_destino
            )

        print("Extração concluída!")

    except BadZipFile:

        raise ValueError(
            f"O arquivo não é um ZIP válido: "
            f"{caminho_zip}"
        )


# ==========================================================
# 6. LER CSV DA CVM
# ==========================================================

def ler_csv_cvm(caminho_csv):

    configuracoes = [
        {"sep": ";", "encoding": "latin1"},
        {"sep": ";", "encoding": "utf-8"},
        {"sep": ";", "encoding": "utf-8-sig"}
    ]

    ultimo_erro = None

    for configuracao in configuracoes:

        try:

            df = pd.read_csv(
                caminho_csv,
                low_memory=False,
                **configuracao
            )

            if len(df.columns) > 1:

                return df

        except Exception as erro:

            ultimo_erro = erro

    raise ValueError(
        f"Não foi possível ler {caminho_csv}: "
        f"{ultimo_erro}"
    )


# ==========================================================
# 7. NORMALIZAR O CÓDIGO CVM
# ==========================================================

def normalizar_codigo(valor):

    if pd.isna(valor):

        return None

    texto = str(valor).strip()

    # Remove caracteres que não sejam números
    numeros = re.sub(r"\D", "", texto)

    # Remove zeros à esquerda
    numeros = numeros.lstrip("0")

    return numeros if numeros else None


# ==========================================================
# 8. FILTRAR DADOS DA AZUL
# ==========================================================

def filtrar_dados_azul(
    pasta_origem,
    pasta_destino
):
    """
    Filtra os CSVs e mantém apenas os registros
    correspondentes à Azul S.A.
    """

    pasta_destino.mkdir(
        parents=True,
        exist_ok=True
    )

    arquivos_csv = list(
        pasta_origem.rglob("*.csv")
    )

    total_arquivos = 0
    total_registros = 0

    if not arquivos_csv:

        print("Nenhum CSV encontrado.")

        return

    print(
        f"CSV encontrados: {len(arquivos_csv)}"
    )

    for caminho_csv in arquivos_csv:

        try:

            df = ler_csv_cvm(caminho_csv)

            # Localiza a coluna CD_CVM
            coluna_cvm = next(
                (
                    coluna
                    for coluna in df.columns
                    if str(coluna).strip().upper()
                    == "CD_CVM"
                ),
                None
            )

            if coluna_cvm is None:

                continue

            codigos = df[coluna_cvm].apply(
                normalizar_codigo
            )

            dados_azul = df[
                codigos == CODIGO_CVM
            ].copy()

            if dados_azul.empty:

                continue

            caminho_saida = (
                pasta_destino /
                f"azul_{caminho_csv.name}"
            )

            dados_azul.to_csv(
                caminho_saida,
                sep=";",
                index=False,
                encoding="utf-8-sig"
            )

            total_arquivos += 1
            total_registros += len(dados_azul)

            print(
                f"✓ {caminho_csv.name} | "
                f"{len(dados_azul)} registros"
            )

        except Exception as erro:

            print(
                f"Erro em {caminho_csv.name}: {erro}"
            )

    print("\nResultado da filtragem:")
    print(f"Arquivos salvos: {total_arquivos}")
    print(f"Registros encontrados: {total_registros}")


# ==========================================================
# 9. PROCESSAR ITR OU DFP
# ==========================================================

def processar_documentos(tipo):

    print("\n" + "=" * 60)
    print(f"PROCESSANDO: {tipo.upper()}")
    print("=" * 60)

    url_base = URLS_CVM[tipo]

    # Obtém os links disponíveis
    links = obter_links_cvm(url_base)

    print(
        f"Arquivos ZIP disponíveis: {len(links)}"
    )

    for ano in ANOS:

        print("\n" + "-" * 60)
        print(f"{tipo.upper()} — ANO {ano}")
        print("-" * 60)

        link_ano = localizar_arquivo_ano(
            links,
            tipo,
            ano
        )

        # Se o arquivo não existir, pula o ano
        if link_ano is None:

            print(
                f"⚠️ {tipo.upper()} de {ano} "
                f"não encontrado na CVM."
            )

            print("Ano ignorado. Continuando...")

            continue

        # Pastas de armazenamento
        pasta_raw_ano = (
            PASTA_RAW / tipo / str(ano)
        )

        pasta_tratada_ano = (
            PASTA_TRATADOS / tipo / str(ano)
        )

        caminho_zip = (
            pasta_raw_ano /
            f"{tipo}_cia_aberta_{ano}.zip"
        )

        pasta_extraida = (
            pasta_raw_ano / "extraido"
        )

        try:

            # Download
            baixar_arquivo(
                link_ano,
                caminho_zip
            )

            # Extração
            extrair_zip(
                caminho_zip,
                pasta_extraida
            )

            # Filtragem da Azul
            filtrar_dados_azul(
                pasta_extraida,
                pasta_tratada_ano
            )

        except Exception as erro:

            print(
                f"❌ Erro ao processar "
                f"{tipo.upper()} {ano}: {erro}"
            )

            print("Continuando para o próximo ano...")


# ==========================================================
# 10. EXECUÇÃO PRINCIPAL
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("COLETA DE DADOS DA CVM — AZUL S.A.")
    print("=" * 60)

    print(f"Código CVM: {CODIGO_CVM}")
    print("Período: 2021 a 2025")
    print("Documentos: ITR e DFP")

    # ======================================================
    # COLETA DOS ITRs
    # ======================================================

    processar_documentos("itr")

    # ======================================================
    # COLETA DOS DFPs
    # ======================================================

    processar_documentos("dfp")

    print("\n" + "=" * 60)
    print("COLETA FINALIZADA!")
    print("=" * 60)