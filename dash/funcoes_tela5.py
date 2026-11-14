from pathlib import Path
import unicodedata

import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONSTANTES E CONFIGURAÇÕES DE DADOS
# ============================================================

ANOS = [2021, 2022, 2023, 2024, 2025]
ANO_META = 2029

# Paleta de cores oficial do projeto
MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
VERMELHO = "#C94C4C"
VERDE = "#23856D"


def _pasta_pai(nivel):
    try:
        return Path(__file__).resolve().parents[nivel]
    except IndexError:
        return Path(__file__).resolve().parent


RAIZ = _pasta_pai(2)
PASTA_TRATADOS = RAIZ / "Projeto_Azul" / "data" / "tratados"


def _buscar_arquivo(nome_base):
    if PASTA_TRATADOS.exists():
        for arq in PASTA_TRATADOS.rglob("*.csv"):
            if nome_base in arq.name:
                return arq
    candidatos = list(_pasta_pai(1).rglob(f"*{nome_base}*"))
    if candidatos:
        return candidatos[0]
    return Path(nome_base)


CAMINHO_OPERACIONAL = _buscar_arquivo("dados_operacionais_anual_2021_2025")


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
    if valor is None or pd.isna(valor):
        return float("nan")
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if texto in ["", "-", "nan", "None"]:
        return float("nan")
    sufixos = {"K": 1e3, "M": 1e6, "B": 1e9}
    multiplicador = 1.0
    if texto[-1:].upper() in sufixos and len(texto) > 1:
        multiplicador = sufixos[texto[-1].upper()]
        texto = texto[:-1]
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1:
        texto = texto.replace(".", "")
    return pd.to_numeric(texto, errors="coerce") * multiplicador


def formatar_numero(valor, casas=2):
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"{valor:,.{casas}f}".translate(str.maketrans(".,", ",."))


def formatar_percentual(valor, casas=1, sinal=False):
    if valor is None or pd.isna(valor):
        return "N/A"
    prefixo = "+" if sinal and valor > 0 else ""
    return f"{prefixo}{formatar_numero(valor, casas)}%"


# ============================================================
# DADOS OPERACIONAIS (ÁREA A E ÁREA B)
# ============================================================

def carregar_operacionais():
    if not CAMINHO_OPERACIONAL.exists():
        raise FileNotFoundError(f"Arquivo de dados operacionais não encontrado: {CAMINHO_OPERACIONAL}")
    df = pd.read_csv(CAMINHO_OPERACIONAL, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _serie(df, nome_normalizado):
    filtro = df[df["indicador_pt"].apply(normalizar_texto).eq(nome_normalizado)]
    if filtro.empty:
        return pd.Series(dtype=float)
    filtro = filtro.copy()
    filtro["valor"] = filtro["valor"].apply(converter_numero)
    filtro["ano"] = pd.to_numeric(filtro["ano"], errors="coerce")
    filtro = filtro.dropna(subset=["ano"])
    filtro = filtro[filtro["ano"].astype(int).isin(ANOS)]
    return filtro.groupby(filtro["ano"].astype(int))["valor"].first()


def preparar_eficiencia(df):
    """Monta a tabela anual com dados reais de RASK, CASK, Spread e Margens."""
    ask = _serie(df, normalizar_texto("Assento-quilômetro oferecido (ASKs) (milhões)"))
    rpk = _serie(df, normalizar_texto(
        "Passageiros pagantes transportados por quilômetros voados (RPK) (milhões)"))
    ocupacao = _serie(df, normalizar_texto("Taxa de ocupação (%)"))
    rask = _serie(df, normalizar_texto("Receita operacional por ASK (centavos) (RASK)"))
    cask = _serie(df, normalizar_texto("CASK (centavos)"))
    receita_pass = _serie(df, normalizar_texto("Receitas de transporte de passageiros (em milhões de reais)"))

    tabela = pd.DataFrame({"Ano": ANOS}).set_index("Ano")
    tabela["ASK (milhões)"] = ask
    tabela["RPK (milhões)"] = rpk
    tabela["Load Factor (%)"] = ocupacao
    tabela["RASK (centavos)"] = rask
    tabela["CASK (centavos)"] = cask
    tabela["Receita Passageiros (R$ mi)"] = receita_pass

    if tabela["Load Factor (%)"].dropna().le(1.5).all():
        tabela["Load Factor (%)"] = tabela["Load Factor (%)"] * 100

    faltando = tabela["Load Factor (%)"].isna()
    tabela.loc[faltando, "Load Factor (%)"] = (
        tabela.loc[faltando, "RPK (milhões)"] / tabela.loc[faltando, "ASK (milhões)"] * 100
    )

    tabela["Spread RASK − CASK (centavos)"] = tabela["RASK (centavos)"] - tabela["CASK (centavos)"]

    # Variações e Margens reais
    rask_2021 = tabela.loc[2021, "RASK (centavos)"]
    cask_2021 = tabela.loc[2021, "CASK (centavos)"]

    tabela["RASK Var (%)"] = ((tabela["RASK (centavos)"] - rask_2021) / rask_2021) * 100
    tabela["CASK Var (%)"] = ((tabela["CASK (centavos)"] - cask_2021) / cask_2021) * 100
    
    # Margem Unitária Real (%) = (Spread / RASK) * 100
    tabela["Margem Spread (%)"] = (tabela["Spread RASK − CASK (centavos)"] / tabela["RASK (centavos)"]) * 100

    return tabela.reset_index().dropna(how="all", subset=tabela.columns[1:])


def _layout_base(fig, altura=350, legenda=True):
    fig.update_layout(
        height=altura, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
        hovermode="x unified",
    )
    return fig


def grafico_load_factor(tabela):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tabela["Ano"], y=tabela["Load Factor (%)"],
        mode="lines+markers+text", name="Load Factor",
        line=dict(color=AZUL, width=3), marker=dict(color=MARINHO, size=8),
        text=[formatar_percentual(v, 1) for v in tabela["Load Factor (%)"]],
        textposition="top center",
        hovertemplate="Ano: %{x}<br>Load Factor: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Ano", yaxis_title="Aproveitamento (%)")
    _layout_base(fig, legenda=False)
    minimo = tabela["Load Factor (%)"].min()
    maximo = tabela["Load Factor (%)"].max()
    if pd.notna(minimo) and pd.notna(maximo):
        fig.update_yaxes(range=[minimo - 3, maximo + 3])
    return fig


def grafico_rask_cask(tabela):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tabela["Ano"], y=tabela["CASK (centavos)"],
        mode="lines+markers", name="CASK (custo por ASK)",
        line=dict(color=DOURADO, width=3), marker=dict(size=8),
        hovertemplate="CASK: %{y:.2f} centavos<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=tabela["Ano"], y=tabela["RASK (centavos)"],
        mode="lines+markers", name="RASK (receita por ASK)",
        line=dict(color=AZUL, width=3), marker=dict(size=8),
        fill="tonexty", fillcolor="rgba(36,87,167,0.10)",
        hovertemplate="RASK: %{y:.2f} centavos<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Ano", yaxis_title="Centavos por ASK")
    _layout_base(fig)
    return fig


def grafico_rpk_ask(tabela):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tabela["Ano"], y=tabela["ASK (milhões)"],
        name="ASK (capacidade oferecida)", marker_color="#BBD4F5",
        hovertemplate="ASK: %{y:,.0f} mi<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=tabela["Ano"], y=tabela["RPK (milhões)"],
        name="RPK (demanda transportada)", marker_color=AZUL,
        hovertemplate="RPK: %{y:,.0f} mi<extra></extra>",
    ))
    fig.update_layout(barmode="group", xaxis_title="Ano", yaxis_title="Milhões de km")
    _layout_base(fig)
    return fig


def grafico_criacao_valor(tabela, val_ref, val_meta):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tabela["Ano"],
        y=tabela["Receita Passageiros (R$ mi)"],
        mode="lines+markers+text",
        name="Receita de Passageiros (Histórico)",
        line=dict(color=AZUL, width=3.5),
        marker=dict(size=8, color=MARINHO),
        text=[f"R$ {v:,.0f}M".replace(",", ".") for v in tabela["Receita Passageiros (R$ mi)"]],
        textposition="top center",
        textfont=dict(color=MARINHO, size=11, weight="bold"),
        hovertemplate="Ano: %{x}<br>Receita: R$ %{y:,.2f} mi<extra></extra>",
    ))

    ultimo_ano = tabela["Ano"].iloc[-1]
    ultimo_val = tabela["Receita Passageiros (R$ mi)"].iloc[-1]

    fig.add_trace(go.Scatter(
        x=[ultimo_ano, ANO_META],
        y=[ultimo_val, val_meta],
        mode="lines+markers+text",
        name=f"Trajetória para a Meta ({ANO_META})",
        line=dict(color=TURQUESA, width=3, dash="dash"),
        marker=dict(size=[0, 12], symbol="star", color=DOURADO, line=dict(color=MARINHO, width=1)),
        text=["", f"Meta: R$ {val_meta:,.0f}M".replace(",", ".")],
        textposition="top center",
        textfont=dict(color=MARINHO, size=11, weight="bold"),
        hovertemplate="Ano: %{x}<br>Objetivo: R$ %{y:,.2f} mi<extra></extra>",
    ))

    fig.add_hline(
        y=val_ref, line_dash="dot", line_color="#75849A", line_width=1.5,
        annotation_text="Valor de Referência (2025)", annotation_position="bottom left",
    )

    fig.update_layout(
        height=380, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(title="R$ Milhões", gridcolor="#E8EDF4"),
        hovermode="x unified",
    )

    return fig