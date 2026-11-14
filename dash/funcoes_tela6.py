from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# CONSTANTES & PALETA VISUAL
# ============================================================

ANOS_HISTORICOS = range(2021, 2026)
META_ALAVANCAGEM = 1.5

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
FUNDO = "#F1F4F8"
VERDE = "#23856D"
VERMELHO = "#C94C4C"

# ============================================================
# CÁLCULOS DE PROJEÇÃO E TAXAS
# ============================================================

def taxa_crescimento_historico(serie: pd.Series, limite_inferior=-0.30, limite_superior=0.50) -> float:
    """Calcula a taxa média anual de crescimento (CAGR) ou mediana das variações."""
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    serie = serie[np.isfinite(serie)]
    
    if len(serie) >= 2 and serie.iloc[0] > 0 and serie.iloc[-1] > 0:
        n = len(serie) - 1
        taxa = (serie.iloc[-1] / serie.iloc[0]) ** (1 / n) - 1
    elif len(serie) >= 2:
        variacoes = serie.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        taxa = float(variacoes.median()) if not variacoes.empty else 0.08
    else:
        taxa = 0.08
        
    return float(np.clip(taxa, limite_inferior, limite_superior))


def projetar_cenarios(dados: pd.DataFrame, anos_futuros=range(2026, 2030),
                      crescimento_receita=0.08, crescimento_ebitda=0.10,
                      crescimento_divida=0.00, amplitude=0.05) -> pd.DataFrame:
    """Projeta os cenários Otimista, Base e Pessimista para os anos futuros."""
    anos_validos = dados.dropna(how="all")
    if anos_validos.empty:
        raise ValueError("Não há dados históricos suficientes para projetar.")

    ultimo_ano = int(anos_validos.index.max())
    ultimo = dados.loc[ultimo_ano]
    
    col_receita = "Receita líquida (R$ mi)"
    col_ebitda = "EBITDA (R$ mi)"
    col_divida = "Dívida líquida aproximada (R$ mi)"

    cenarios = {
        "Otimista": (crescimento_receita + amplitude, crescimento_ebitda + amplitude, crescimento_divida - amplitude),
        "Base": (crescimento_receita, crescimento_ebitda, crescimento_divida),
        "Pessimista": (crescimento_receita - amplitude, crescimento_ebitda - amplitude, crescimento_divida + amplitude),
    }

    linhas = []
    for nome, (taxa_rec, taxa_ebi, taxa_div) in cenarios.items():
        for ano in anos_futuros:
            n = ano - ultimo_ano
            receita_proj = float(ultimo[col_receita]) * ((1 + taxa_rec) ** n)
            ebitda_proj = float(ultimo[col_ebitda]) * ((1 + taxa_ebi) ** n)
            
            divida_base = ultimo.get(col_divida, np.nan)
            divida_proj = float(divida_base) * ((1 + taxa_div) ** n) if pd.notna(divida_base) else np.nan
            
            alavancagem = divida_proj / ebitda_proj if pd.notna(divida_proj) and ebitda_proj > 0 else np.nan
            
            linhas.append({
                "Ano": ano,
                "Cenário": nome,
                col_receita: receita_proj,
                col_ebitda: ebitda_proj,
                col_divida: divida_proj,
                "Dívida Líquida / EBITDA (x)": alavancagem,
                "Crescimento da receita": taxa_rec,
                "Crescimento do EBITDA": taxa_ebi,
                "Crescimento da dívida": taxa_div,
            })

    return pd.DataFrame(linhas)

# ============================================================
# VISUALIZAÇÕES PLOTLY
# ============================================================

def grafico_alavancagem(dados: pd.DataFrame, projecoes: pd.DataFrame) -> go.Figure:
    """Gera o gráfico de linhas de evolução e projeção da Alavancagem."""
    fig = go.Figure()
    
    historico = dados.dropna(subset=["Dívida líquida aproximada (R$ mi)", "EBITDA (R$ mi)"]).copy()
    historico["Alavancagem"] = historico["Dívida líquida aproximada (R$ mi)"] / historico["EBITDA (R$ mi)"].replace(0, np.nan)
    
    if not historico.empty:
        fig.add_trace(go.Scatter(
            x=historico.index, y=historico["Alavancagem"], mode="lines+markers",
            name="Histórico", line=dict(color=MARINHO, width=3), marker=dict(size=8)
        ))

    cores = {"Otimista": VERDE, "Base": TURQUESA, "Pessimista": VERMELHO}
    
    for nome in ("Otimista", "Base", "Pessimista"):
        parte = projecoes[projecoes["Cenário"] == nome]
        if parte["Dívida Líquida / EBITDA (x)"].notna().any():
            fig.add_trace(go.Scatter(
                x=parte["Ano"], y=parte["Dívida Líquida / EBITDA (x)"],
                mode="lines+markers", name=f"Projeção {nome.lower()}",
                line=dict(color=cores[nome], width=2.5, dash="dash")
            ))

    fig.add_hline(
        y=META_ALAVANCAGEM, line_dash="dot", line_color=DOURADO, line_width=2,
        annotation_text="Meta: 1,5x", annotation_position="top left",
        annotation_font=dict(color=MARINHO, size=11, family="sans-serif")
    )

    fig.update_layout(
        template="plotly_white",
        height=410,
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(title="Ano", dtick=1),
        yaxis=dict(title="Dívida líquida / EBITDA (x)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def grafico_receita_ebitda(dados: pd.DataFrame, projecoes: pd.DataFrame) -> go.Figure:
    """Gera o gráfico comparativo de trajetória de Receita Líquida e EBITDA."""
    fig = go.Figure()

    for coluna, nome, cor in [
        ("Receita líquida (R$ mi)", "Receita líquida — histórico", MARINHO),
        ("EBITDA (R$ mi)", "EBITDA — histórico", AZUL),
    ]:
        parte = dados[coluna].dropna()
        if not parte.empty:
            fig.add_trace(go.Scatter(
                x=parte.index, y=parte.values, mode="lines+markers", name=nome,
                line=dict(color=cor, width=3)
            ))

    cores = {"Otimista": VERDE, "Base": TURQUESA, "Pessimista": VERMELHO}
    
    for nome in ("Otimista", "Base", "Pessimista"):
        parte = projecoes[projecoes["Cenário"] == nome]
        fig.add_trace(go.Scatter(
            x=parte["Ano"], y=parte["Receita líquida (R$ mi)"],
            mode="lines", name=f"Receita — {nome.lower()}",
            line=dict(color=cores[nome], dash="dash", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=parte["Ano"], y=parte["EBITDA (R$ mi)"],
            mode="lines", name=f"EBITDA — {nome.lower()}",
            line=dict(color=cores[nome], dash="dot", width=2), visible="legendonly"
        ))

    fig.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(title="Ano", dtick=1),
        yaxis=dict(title="R$ milhões"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

# ============================================================
# FORMATADORES AUXILIARES
# ============================================================

def formatar_moeda_milhoes(valor) -> str:
    """Formata valores numéricos para R$ milhões no padrão brasileiro."""
    if pd.isna(valor) or not np.isfinite(valor):
        return "Indisponível"
    return f"R$ {valor:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor, casas=1) -> str:
    """Formata valores em percentual (ex: 15,2%)."""
    if pd.isna(valor) or not np.isfinite(valor):
        return "N/A"
    return f"{valor:.{casas}f}%".replace(".", ",")