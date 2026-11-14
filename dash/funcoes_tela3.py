from pathlib import Path
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CAMINHOS E CONFIGURAÇÕES
# ============================================================

RAIZ = Path(__file__).resolve().parents[2]
PASTA_TRATADOS = RAIZ / "Projeto_Azul" / "data" / "tratados"

def _buscar_arquivo(nome_base):
    if PASTA_TRATADOS.exists():
        for arq in PASTA_TRATADOS.rglob("*.csv"):
            if nome_base in arq.name:
                return arq
    candidatos = list(Path(__file__).resolve().parents[1].rglob(f"*{nome_base}*"))
    if candidatos:
        return candidatos[0]
    return Path(nome_base)

CAMINHO_DRE = _buscar_arquivo("dre_anual_2021_2025.csv")

ANOS = [2021, 2022, 2023, 2024, 2025]

# Cores da Paleta Oficial
MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
VERMELHO = "#C94C4C"
VERDE = "#23856D"


# ============================================================
# NORMALIZAÇÃO E FORMATAÇÃO
# ============================================================

def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())


def converter_numero(valor):
    if pd.isna(valor) or valor is None:
        return float("nan")
    valor = str(valor).strip()
    if valor in ["", "-", "nan", "None"]:
        return float("nan")
    valor = valor.replace("R$", "").replace(" ", "")
    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")
    return pd.to_numeric(valor, errors="coerce")


def formatar_valor(valor):
    if valor is None or pd.isna(valor):
        return "N/D"
    return f"{valor:,.2f}".translate(str.maketrans(".,", ",."))


def formatar_moeda(valor):
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"R$ {valor:,.2f} mi".translate(str.maketrans(".,", ",."))


# ============================================================
# CARREGAR E PREPARAR DADOS
# ============================================================

def carregar_dados():
    if not CAMINHO_DRE.exists():
        raise FileNotFoundError(f"Arquivo da DRE não encontrado: {CAMINHO_DRE}")

    df = pd.read_csv(CAMINHO_DRE, encoding="utf-8-sig")
    df.columns = [str(coluna).strip() for coluna in df.columns]
    return df


def preparar_dados(df):
    df = df.copy()

    coluna_indicador = next(
        (col for col in df.columns if normalizar_texto(col) in ["indicador_pt", "indicador", "descricao", "conta"]),
        None,
    )

    if coluna_indicador is None:
        raise ValueError(f"Não encontrei a coluna do indicador. Colunas disponíveis: {df.columns.tolist()}")

    df = df.rename(columns={coluna_indicador: "indicador_pt"})
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df = df.dropna(subset=["ano"]).copy()
    df["ano"] = df["ano"].astype(int)

    df["valor"] = df["valor"].apply(converter_numero)
    
    # Conversão de R$ mil para R$ mi
    df["valor_mi"] = df["valor"] / 1000.0

    df = df[df["ano"].isin(ANOS)].copy()
    df["indicador_normalizado"] = df["indicador_pt"].apply(normalizar_texto)

    return df


def obter_medias_periodo(df_longo):
    """Calcula as médias dos principais indicadores para todo o período (2021-2025)."""
    df_rec = df_longo[df_longo["indicador_normalizado"].str.contains("receita liquida", na=False)]
    df_ebitda = df_longo[df_longo["indicador_normalizado"].eq("ebitda")]
    df_lucro = df_longo[
        df_longo["indicador_normalizado"].str.contains("prejuizo liquido", na=False) |
        df_longo["indicador_normalizado"].str.contains("lucro liquido", na=False)
    ]

    media_rec = df_rec["valor_mi"].mean() if not df_rec.empty else None
    media_ebitda = df_ebitda["valor_mi"].mean() if not df_ebitda.empty else None
    media_lucro = df_lucro["valor_mi"].mean() if not df_lucro.empty else None
    
    media_margem = (media_ebitda / media_rec * 100) if media_rec and media_ebitda else None

    return {
        "media_receita": media_rec,
        "media_ebitda": media_ebitda,
        "media_margem": media_margem,
        "media_lucro": media_lucro,
    }


# ============================================================
# GRÁFICOS
# ============================================================

def grafico_receita_ebitda(df_longo):
    df_rec = df_longo[df_longo["indicador_normalizado"].str.contains("receita liquida", na=False)].copy()
    df_rec["indicador"] = "Receita Líquida"

    df_ebitda = df_longo[df_longo["indicador_normalizado"].eq("ebitda")].copy()
    df_ebitda["indicador"] = "EBITDA"

    dados = pd.concat([df_rec, df_ebitda], ignore_index=True)

    fig = px.line(
        dados,
        x="ano",
        y="valor_mi",
        color="indicador",
        markers=True,
        color_discrete_map={"Receita Líquida": AZUL, "EBITDA": TURQUESA},
        labels={
            "ano": "Ano",
            "valor_mi": "R$ milhões",
            "indicador": "",
        },
    )

    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
        hovermode="x unified",
    )

    return fig


def grafico_margem_ebitda(df_longo):
    df_ebitda = df_longo[df_longo["indicador_normalizado"].eq("ebitda")][["ano", "valor_mi"]].rename(columns={"valor_mi": "ebitda"})
    df_rec = df_longo[df_longo["indicador_normalizado"].str.contains("receita liquida", na=False)][["ano", "valor_mi"]].rename(columns={"valor_mi": "receita"})

    dados = pd.merge(df_ebitda, df_rec, on="ano")
    dados["margem"] = (dados["ebitda"] / dados["receita"]) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dados["ano"],
        y=dados["margem"],
        mode="lines+markers+text",
        name="Margem EBITDA",
        line=dict(color=TURQUESA, width=3),
        marker=dict(color=MARINHO, size=8),
        text=[f"{v:.2f}%" for v in dados["margem"]],
        textposition="top center",
        hovertemplate="Ano: %{x}<br>Margem EBITDA: %{y:.2f}%<extra></extra>",
    ))

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis_title="Ano", yaxis_title="Margem (%)",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
        hovermode="x unified",
    )

    return fig


def grafico_lucro_prejuizo(df_longo):
    dados = df_longo[
        df_longo["indicador_normalizado"].str.contains("prejuizo liquido", na=False) |
        df_longo["indicador_normalizado"].str.contains("lucro liquido", na=False)
    ].dropna(subset=["valor_mi"]).copy()

    cores = [VERDE if v >= 0 else VERMELHO for v in dados["valor_mi"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dados["ano"],
        y=dados["valor_mi"],
        marker_color=cores,
        text=[formatar_moeda(v) for v in dados["valor_mi"]],
        textposition="outside",
        name="Resultado Líquido",
        hovertemplate="Ano: %{x}<br>Resultado: %{y:,.2f} mi<extra></extra>",
    ))

    fig.add_hline(y=0, line_color="#75849A", line_width=1)

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis_title="Ano", yaxis_title="R$ milhões",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
        hovermode="x unified",
    )

    return fig


# ============================================================
# CUSTOS DOS SERVIÇOS PRESTADOS
# ============================================================

def preparar_custos_despesas(df, ano_selecionado):
    df_custos = df[df["grupo"].astype(str).str.strip() == "Custos dos serviços prestados"].copy()

    excluir = [
        normalizar_texto("Total custos dos serviços prestados"),
        normalizar_texto("Lucro / (prejuízo) operacional"),
        normalizar_texto("Margem EBIT"),
    ]

    df_custos = df_custos[~df_custos["indicador_pt"].apply(normalizar_texto).isin(excluir)].copy()
    df_custos = df_custos[df_custos["ano"] == int(ano_selecionado)].copy()

    df_custos["valor"] = pd.to_numeric(df_custos["valor"], errors="coerce")
    df_custos = df_custos.dropna(subset=["valor"])

    df_custos["valor_mi"] = (df_custos["valor"] / 1000.0).abs()

    df_custos = df_custos.rename(columns={"indicador_pt": "despesa"})
    return df_custos[["despesa", "valor_mi"]].sort_values("valor_mi", ascending=True)


def grafico_composicao_custos(df_custos):
    df_custos = df_custos.copy()
    total = df_custos["valor_mi"].sum()

    def montar_rotulo(val):
        if not total:
            return formatar_moeda(val)
        pct = (val / total) * 100
        return f"R$ {val:,.1f} mi ({pct:.1f}%)".translate(str.maketrans(".,", ",."))

    df_custos["rotulo"] = df_custos["valor_mi"].apply(montar_rotulo)

    fig = px.bar(
        df_custos,
        x="valor_mi",
        y="despesa",
        orientation="h",
        labels={"valor_mi": "R$ milhões", "despesa": ""},
        text="rotulo",
        color_discrete_sequence=[AZUL],
    )

    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=380, margin=dict(l=10, r=140, t=20, b=20),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis=dict(gridcolor="#E8EDF4", title_text="R$ milhões"),
    )

    return fig