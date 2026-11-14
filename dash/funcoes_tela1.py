from pathlib import Path
import unicodedata

import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CAMINHOS E CONFIGURAÇÕES
# ============================================================

RAIZ = Path(__file__).resolve().parents[2]
PASTA_TRATADOS = RAIZ / "Projeto_Azul" / "data" / "tratados"

# Busca flexível para garantir o arquivo mesmo se a estrutura de pastas mudar levemente
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
CAMINHO_ESG = _buscar_arquivo("esg_anual_2021_2025.csv")

ANOS = [2021, 2022, 2023, 2024, 2025]
META_ALAVANCAGEM = 1.5

# Cores do Design System
MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
VERMELHO = "#C94C4C"
VERDE = "#23856D"


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().casefold()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def formatar_numero(valor, casas=2):
    if pd.isna(valor) or valor is None:
        return "N/A"
    return f"{valor:,.{casas}f}".translate(str.maketrans(".,", ",."))


def formatar_moeda(valor):
    if pd.isna(valor) or valor is None:
        return "N/A"
    return ("R$ {:,.2f} mi".format(valor)).translate(str.maketrans(".,", ",."))


def carregar_dados():
    if not CAMINHO_BALANCO.exists():
        raise FileNotFoundError(f"Base do balanço não encontrada em: {CAMINHO_BALANCO}")
    if not CAMINHO_DRE.exists():
        raise FileNotFoundError(f"Base da DRE não encontrada em: {CAMINHO_DRE}")
    if not CAMINHO_ESG.exists():
        raise FileNotFoundError(f"Base de ESG não encontrada em: {CAMINHO_ESG}")

    df_balanco = pd.read_csv(CAMINHO_BALANCO)
    df_dre = pd.read_csv(CAMINHO_DRE)
    df_esg = pd.read_csv(CAMINHO_ESG)
    
    return df_balanco, df_dre, df_esg


def preparar_visao_geral(dados):
    df_balanco, df_dre, df_esg = dados

    # Normalizar nomes
    df_balanco["indicador_norm"] = df_balanco["indicador_pt"].fillna("").map(normalizar_texto)
    df_balanco["subgrupo_norm"] = df_balanco["subgrupo"].fillna("").map(normalizar_texto)
    df_dre["indicador_norm"] = df_dre["indicador_pt"].fillna("").map(normalizar_texto)

    resultados = []
    for ano in ANOS:
        # Pega 4T (trimestral) para o balanço patrimonial de fechamento do ano
        df_bal_ano = df_balanco[(df_balanco["ano"] == ano) & (df_balanco["periodo"].astype(str).str.contains("4T|4", na=False))]
        if df_bal_ano.empty:
            df_bal_ano = df_balanco[df_balanco["ano"] == ano]

        emp_cp = df_bal_ano[
            (df_bal_ano["indicador_norm"].str.contains("emprestimos e financiamentos")) &
            (df_bal_ano["subgrupo_norm"].str.contains("passivo circulante"))
        ]["valor"].sum()

        emp_lp = df_bal_ano[
            (df_bal_ano["indicador_norm"].str.contains("emprestimos e financiamentos")) &
            (~df_bal_ano["subgrupo_norm"].str.contains("passivo circulante"))
        ]["valor"].sum()

        divida_bruta = (emp_cp + emp_lp) / 1000.0  # Em milhões (base em R$ mil)

        caixa_val = df_bal_ano[
            df_bal_ano["indicador_norm"].str.contains("caixa e equivalentes de caixa")
        ]["valor"].sum() / 1000.0

        divida_liquida = divida_bruta - caixa_val

        # Patrimônio Líquido (convertido para R$ milhões)
        pl_row = df_bal_ano[df_bal_ano["indicador_norm"].eq("patrimonio liquido")]
        patrimonio_liquido = (pl_row["valor"].values[0] / 1000.0) if not pl_row.empty else None

        # DRE (dados anuais)
        df_dre_ano = df_dre[df_dre["ano"] == ano]
        
        ebitda_row = df_dre_ano[df_dre_ano["indicador_norm"].eq("ebitda")]
        ebitda_val = (ebitda_row["valor"].values[0] / 1000.0) if not ebitda_row.empty else None

        rec_row = df_dre_ano[df_dre_ano["indicador_norm"].str.contains("total receita liquida|receita liquida")]
        receita_val = (rec_row["valor"].values[0] / 1000.0) if not rec_row.empty else None

        lucro_row = df_dre_ano[df_dre_ano["indicador_norm"].str.contains("prejuizo liquido do exercicio|lucro/prejuizo")]
        lucro_val = (lucro_row["valor"].values[0] / 1000.0) if not lucro_row.empty else None

        alavancagem = (
            divida_liquida / ebitda_val
            if ebitda_val is not None and ebitda_val > 0
            else None
        )

        resultados.append({
            "Ano": ano,
            "Dívida Bruta": divida_bruta,
            "Caixa": caixa_val,
            "Dívida Líquida": divida_liquida,
            "EBITDA": ebitda_val,
            "Dívida Líquida / EBITDA": alavancagem,
            "Valor patrimonial contábil": patrimonio_liquido,
            "Receita Líquida": receita_val,
            "Lucro / Prejuízo": lucro_val,
        })

    df = pd.DataFrame(resultados)
    return df, df_esg


# ============================================================
# GRÁFICOS ESG
# ============================================================

def grafico_esg_eficiencia_combustivel(df_esg):
    """Gera o gráfico do pilar Ambiental (Consumo por ASK)."""
    df_filtered = df_esg[
        df_esg["indicador_pt"].str.contains("ASK", case=False, na=False)
    ].sort_values("ano")

    fig = go.Figure()

    if df_filtered.empty:
        fig.add_annotation(
            text="Dados de eficiência de combustível indisponíveis.",
            x=0.5, y=0.5, showarrow=False, font=dict(size=13, color="#68778B")
        )
    else:
        fig.add_trace(go.Scatter(
            x=df_filtered["ano"],
            y=df_filtered["valor"],
            mode="lines+markers+text",
            name="Kg / ASK (milhares)",
            line=dict(color=TURQUESA, width=3),
            marker=dict(color=MARINHO, size=8),
            text=[f"{v:,.1f}" for v in df_filtered["valor"]],
            textposition="top center",
            hovertemplate="Ano: %{x}<br>Consumo por ASK: %{y:,.2f} Kg/ASK<extra></extra>",
        ))

    fig.update_layout(
        height=330, margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis_title="Ano", yaxis_title="Kg / ASK (milhares)",
        hovermode="x unified",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
    )
    return fig


def grafico_esg_diversidade_governanca(df_esg):
    """Gera o gráfico dos pilares Social e Governança (% de Mulheres e Conselheiros Independentes)."""
    df_mulheres = df_esg[
        df_esg["indicador_pt"].str.contains("mulheres em cargo de gestão", case=False, na=False)
    ].sort_values("ano")

    df_indep = df_esg[
        df_esg["indicador_pt"].str.contains("Conselheiros Independentes", case=False, na=False)
    ].sort_values("ano")

    fig = go.Figure()

    if not df_mulheres.empty:
        fig.add_trace(go.Bar(
            x=df_mulheres["ano"],
            y=df_mulheres["valor"],
            name="% Mulheres na Gestão",
            marker_color=AZUL,
            text=[f"{v:.1f}%" for v in df_mulheres["valor"]],
            textposition="outside",
            hovertemplate="Ano: %{x}<br>Mulheres na Gestão: %{y:.1f}%<extra></extra>",
        ))

    if not df_indep.empty:
        fig.add_trace(go.Scatter(
            x=df_indep["ano"],
            y=df_indep["valor"],
            mode="lines+markers+text",
            name="% Conselheiros Independentes",
            line=dict(color=DOURADO, width=3),
            marker=dict(color=MARINHO, size=8),
            text=[f"{v:.1f}%" for v in df_indep["valor"]],
            textposition="top center",
            hovertemplate="Ano: %{x}<br>Conselheiros Independentes: %{y:.1f}%<extra></extra>",
        ))

    fig.update_layout(
        height=330, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Ano", yaxis_title="Percentual (%)",
        hovermode="x unified",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4", range=[0, 115]),
    )
    return fig