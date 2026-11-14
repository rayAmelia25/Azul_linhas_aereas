from pathlib import Path
import unicodedata

import pandas as pd
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


CAMINHO_BALANCO = _buscar_arquivo("balanco_trimestral_2021_2025_estruturado.csv")
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
    return "".join(c for c in texto if not unicodedata.combining(c))


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


def formatar_moeda(valor):
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"R$ {valor:,.2f} mi".translate(str.maketrans(".,", ",."))


# ============================================================
# CARREGAR E PREPARAR DADOS
# ============================================================

def carregar_dados():
    if not CAMINHO_BALANCO.exists():
        raise FileNotFoundError(f"Arquivo do balanço não encontrado: {CAMINHO_BALANCO}")
    if not CAMINHO_DRE.exists():
        raise FileNotFoundError(f"Arquivo da DRE não encontrado: {CAMINHO_DRE}")

    df_balanco = pd.read_csv(CAMINHO_BALANCO)
    df_dre = pd.read_csv(CAMINHO_DRE)
    return df_balanco, df_dre


def preparar_dados_patrimoniais(df_balanco, df_dre):
    df_balanco["indicador_norm"] = df_balanco["indicador_pt_normalizado"].fillna("").map(normalizar_texto)
    df_dre["indicador_norm"] = df_dre["indicador_pt"].fillna("").map(normalizar_texto)

    resultados = []

    for ano in ANOS:
        # Fechamento 4T para o balanço patrimonial
        df_bal_ano = df_balanco[
            (df_balanco["ano"] == ano) &
            (df_balanco["periodo"].astype(str).str.contains("4T|4", na=False))
        ]
        if df_bal_ano.empty:
            df_bal_ano = df_balanco[df_balanco["ano"] == ano]

        ac = df_bal_ano[df_bal_ano["indicador_norm"].eq("circulante")]["valor"].sum() / 1000.0
        anc = df_bal_ano[df_bal_ano["indicador_norm"].eq("ativo nao circulante")]["valor"].sum() / 1000.0
        pc = df_bal_ano[df_bal_ano["indicador_norm"].eq("passivo circulante")]["valor"].sum() / 1000.0
        pnc = df_bal_ano[df_bal_ano["indicador_norm"].eq("nao circulante")]["valor"].sum() / 1000.0
        pl = df_bal_ano[df_bal_ano["indicador_norm"].eq("patrimonio liquido")]["valor"].sum() / 1000.0
        caixa = df_bal_ano[df_bal_ano["indicador_norm"].str.contains("caixa e equivalentes", na=False)]["valor"].sum() / 1000.0

        liquidez_corrente = ac / pc if pc > 0 else None

        # DRE Anual para Entradas e Saídas Operacionais
        df_dre_ano = df_dre[df_dre["ano"] == ano]
        receita = df_dre_ano[df_dre_ano["indicador_norm"].str.contains("receita liquida", na=False)]["valor"].sum() / 1000.0
        custos = df_dre_ano[df_dre_ano["indicador_norm"].str.contains("custos dos servicos prestados", na=False)]["valor"].sum() / 1000.0
        ebitda = df_dre_ano[df_dre_ano["indicador_norm"].eq("ebitda")]["valor"].sum() / 1000.0

        resultados.append({
            "Ano": ano,
            "Ativo Circulante": ac,
            "Ativo Não Circulante": anc,
            "Passivo Circulante": pc,
            "Passivo Não Circulante": pnc,
            "Patrimônio Líquido": pl,
            "Caixa": caixa,
            "Liquidez Corrente": liquidez_corrente,
            "Entradas Operacionais": receita,
            "Saídas Operacionais": -abs(custos),
            "EBITDA": ebitda,
        })

    return pd.DataFrame(resultados)


# ============================================================
# GRÁFICOS
# ============================================================

def grafico_entradas_saidas(df):
    """1. Colunas divergentes — Entradas e saídas de caixa operacionais"""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Ano"],
        y=df["Entradas Operacionais"],
        name="Entradas (Receita)",
        marker_color=VERDE,
        text=[f"R$ {v:,.0f} mi".translate(str.maketrans(".,", ",.")) for v in df["Entradas Operacionais"]],
        textposition="outside",
        hovertemplate="Ano: %{x}<br>Entradas: R$ %{y:,.2f} mi<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=df["Ano"],
        y=df["Saídas Operacionais"],
        name="Saídas (Custos)",
        marker_color=VERMELHO,
        text=[f"R$ {v:,.0f} mi".translate(str.maketrans(".,", ",.")) for v in df["Saídas Operacionais"]],
        textposition="outside",
        hovertemplate="Ano: %{x}<br>Saídas: R$ %{y:,.2f} mi<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["Ano"],
        y=df["EBITDA"],
        name="Resultado Operacional (EBITDA)",
        mode="lines+markers+text",
        line=dict(color=DOURADO, width=3),
        marker=dict(size=8, color=MARINHO),
        text=[f"R$ {v:,.0f} mi".translate(str.maketrans(".,", ",.")) for v in df["EBITDA"]],
        textposition="top center",
        hovertemplate="Ano: %{x}<br>Geração Operacional: R$ %{y:,.2f} mi<extra></extra>",
    ))

    fig.add_hline(y=0, line_color="#75849A", line_width=1)

    fig.update_layout(
        height=380, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        barmode="relative",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4", title_text="R$ milhões"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    return fig


def grafico_estrutura_patrimonial(df):
    """2. Barras empilhadas / agrupadas — Ativos, passivos e patrimônio líquido"""
    fig = go.Figure()

    fig.add_trace(go.Bar(x=df["Ano"], y=df["Ativo Circulante"], name="Ativo Circulante", marker_color=TURQUESA))
    fig.add_trace(go.Bar(x=df["Ano"], y=df["Ativo Não Circulante"], name="Ativo Não Circulante", marker_color=AZUL))
    fig.add_trace(go.Bar(x=df["Ano"], y=df["Passivo Circulante"], name="Passivo Circulante", marker_color=VERMELHO))
    fig.add_trace(go.Bar(x=df["Ano"], y=df["Passivo Não Circulante"], name="Passivo Não Circulante", marker_color=MARINHO))
    fig.add_trace(go.Bar(x=df["Ano"], y=df["Patrimônio Líquido"], name="Patrimônio Líquido", marker_color=DOURADO))

    fig.update_layout(
        height=380, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        barmode="group",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4", title_text="R$ milhões"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    return fig


def grafico_liquidez_corrente(df):
    """3. Linha — Liquidez corrente"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Ano"],
        y=df["Liquidez Corrente"],
        mode="lines+markers+text",
        name="Liquidez Corrente",
        line=dict(color=TURQUESA, width=3),
        marker=dict(color=MARINHO, size=8),
        text=[f"{v:.2f}x" if pd.notna(v) else "N/A" for v in df["Liquidez Corrente"]],
        textposition="top center",
        hovertemplate="Ano: %{x}<br>Liquidez Corrente: %{y:.2f}x<extra></extra>",
    ))

    fig.add_hline(
        y=1.0, line_dash="dash", line_color=DOURADO,
        annotation_text="Referência Ideal: 1,0x", annotation_position="top left",
    )

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis_title="Ano", yaxis_title="Múltiplo (x)",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4", rangemode="tozero"),
        hovermode="x unified",
    )

    return fig