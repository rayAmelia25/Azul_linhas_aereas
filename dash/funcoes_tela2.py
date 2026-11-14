from pathlib import Path
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# CAMINHOS E CONFIGURAÇÕES
# ============================================================

RAIZ = Path(__file__).resolve().parents[2]
PASTA_TRATADOS = RAIZ / "Projeto_Azul" / "data" / "tratados"

@st.cache_data
def _buscar_arquivo(nome_base):
    if PASTA_TRATADOS.exists():
        for arq in PASTA_TRATADOS.rglob("*.csv"):
            if nome_base in arq.name:
                return arq
    candidatos = list(Path(__file__).resolve().parents[1].rglob(f"*{nome_base}*"))
    if candidatos:
        return candidatos[0]
    return Path(nome_base)

ANOS = [2021, 2022, 2023, 2024, 2025]
META_ALAVANCAGEM = 1.5

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
VERMELHO = "#C94C4C"

# ============================================================
# NORMALIZAÇÃO E TRATAMENTO DE COLUNAS
# ============================================================

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

def _encontrar_coluna(df, nomes_possiveis):
    """Encontra o nome exato de uma coluna ignorando maiúsculas/minúsculas."""
    colunas_map = {c.lower().strip(): c for c in df.columns}
    for nome in nomes_possiveis:
        if nome.lower() in colunas_map:
            return colunas_map[nome.lower()]
    return None

def _encontrar_coluna_valor(df):
    col = _encontrar_coluna(df, ["valor", "valor_mi", "valor_mil", "valor_rs", "val"])
    if col:
        return col
    num_cols = df.select_dtypes(include=["number"]).columns
    return num_cols[0] if len(num_cols) > 0 else df.columns[-1]

def _garantir_colunas_temporais(df):
    """Garante que as colunas 'ano' e 'trimestre' existam, extraindo de 'periodo' se necessário."""
    df = df.copy()
    col_ano = _encontrar_coluna(df, ["ano", "year"])
    col_per = _encontrar_coluna(df, ["periodo", "period", "quarter"])
    col_tri = _encontrar_coluna(df, ["trimestre", "tri", "q"])

    if col_ano:
        df["ano_num"] = pd.to_numeric(df[col_ano], errors="coerce")
    elif col_per:
        df["ano_num"] = pd.to_numeric("20" + df[col_per].astype(str).str.extract(r"(\d{2})$")[0], errors="coerce")
    else:
        df["ano_num"] = None

    if col_tri:
        df["tri_num"] = pd.to_numeric(df[col_tri], errors="coerce")
    elif col_per:
        df["tri_num"] = pd.to_numeric(df[col_per].astype(str).str.extract(r"^(\d)")[0], errors="coerce")
    else:
        df["tri_num"] = None

    df["periodo_str"] = df[col_per].astype(str) if col_per else ""
    return df

@st.cache_data
def carregar_dados_por_periodo(frequencia="Anual"):
    caminho_balanco = _buscar_arquivo("balanco_trimestral")
    if frequencia in ["Trimestral", "Semestral"]:
        caminho_dre = _buscar_arquivo("dre_trimestral")
    else:
        caminho_dre = _buscar_arquivo("dre_anual")

    df_balanco = pd.read_csv(caminho_balanco)
    df_dre = pd.read_csv(caminho_dre)
    return df_balanco, df_dre

@st.cache_data
def preparar_dados_anual():
    """Resumo Anual Consolidado para os Cartões Executivos."""
    df_balanco, df_dre = carregar_dados_por_periodo(frequencia="Anual")
    df_balanco = _garantir_colunas_temporais(df_balanco)
    df_dre = _garantir_colunas_temporais(df_dre)

    col_val_bal = _encontrar_coluna_valor(df_balanco)
    col_val_dre = _encontrar_coluna_valor(df_dre)

    col_ind_bal = _encontrar_coluna(df_balanco, ["indicador_pt", "indicador", "conta"]) or df_balanco.columns[0]
    col_ind_dre = _encontrar_coluna(df_dre, ["indicador_pt", "indicador", "conta"]) or df_dre.columns[0]

    df_balanco["indicador_norm"] = df_balanco[col_ind_bal].fillna("").map(normalizar_texto)
    df_balanco["subgrupo_norm"] = df_balanco["subgrupo"].fillna("").map(normalizar_texto) if "subgrupo" in df_balanco.columns else ""
    df_dre["indicador_norm"] = df_dre[col_ind_dre].fillna("").map(normalizar_texto)

    resultados = []
    for ano in ANOS:
        df_bal_ano = df_balanco[(df_balanco["ano_num"] == ano) & (df_balanco["periodo_str"].str.contains("4T|4", na=False))]
        if df_bal_ano.empty:
            df_bal_ano = df_balanco[df_balanco["ano_num"] == ano]

        emp_cp = pd.to_numeric(df_bal_ano[
            (df_bal_ano["indicador_norm"].str.contains("emprestimos")) &
            (df_bal_ano["subgrupo_norm"].str.contains("circulante"))
        ][col_val_bal], errors="coerce").sum()

        emp_lp = pd.to_numeric(df_bal_ano[
            (df_bal_ano["indicador_norm"].str.contains("emprestimos")) &
            (~df_bal_ano["subgrupo_norm"].str.contains("circulante"))
        ][col_val_bal], errors="coerce").sum()

        valor_caixa = pd.to_numeric(df_bal_ano[df_bal_ano["indicador_norm"].str.contains("caixa")][col_val_bal], errors="coerce").sum()
        valor_arrendamento = pd.to_numeric(df_bal_ano[df_bal_ano["indicador_norm"].eq("arrendamento")][col_val_bal], errors="coerce").sum()

        df_dre_ano = df_dre[df_dre["ano_num"] == ano]
        ebitda_rows = df_dre_ano[df_dre_ano["indicador_norm"].str.contains("ebitda", na=False)]
        valor_ebitda = pd.to_numeric(ebitda_rows[col_val_dre], errors="coerce").sum()

        divida_bruta = emp_cp + emp_lp
        divida_liquida = divida_bruta - valor_caixa
        alavancagem = (divida_liquida / valor_ebitda) if (valor_ebitda is not None and valor_ebitda != 0) else None

        resultados.append({
            "Ano": ano,
            "Ordem": ano,
            "Dívida CP": emp_cp / 1000.0,
            "Dívida LP": emp_lp / 1000.0,
            "Caixa": valor_caixa / 1000.0,
            "Arrendamento": valor_arrendamento / 1000.0,
            "Dívida Bruta": divida_bruta / 1000.0,
            "Dívida Líquida": divida_liquida / 1000.0,
            "EBITDA": valor_ebitda / 1000.0,
            "Dívida Líquida / EBITDA": alavancagem,
        })
    df_res = pd.DataFrame(resultados)
    return df_res.sort_values("Ordem").drop(columns=["Ordem"])

@st.cache_data
def preparar_dados_dinamico(df_balanco, df_dre, frequencia="Anual"):
    """Prepara os dados organizados em ordem cronológica contínua por período."""
    df_bal = _garantir_colunas_temporais(df_balanco)
    df_d = _garantir_colunas_temporais(df_dre)

    col_val_bal = _encontrar_coluna_valor(df_bal)
    col_val_dre = _encontrar_coluna_valor(df_d)

    col_ind_bal = _encontrar_coluna(df_bal, ["indicador_pt", "indicador", "conta"]) or df_bal.columns[0]
    col_ind_dre = _encontrar_coluna(df_d, ["indicador_pt", "indicador", "conta"]) or df_d.columns[0]

    df_bal["indicador_norm"] = df_bal[col_ind_bal].fillna("").map(normalizar_texto)
    df_bal["subgrupo_norm"] = df_bal["subgrupo"].fillna("").map(normalizar_texto) if "subgrupo" in df_bal.columns else ""
    df_d["indicador_norm"] = df_d[col_ind_dre].fillna("").map(normalizar_texto)

    resultados = []
    anos_unicos = sorted(df_bal["ano_num"].dropna().unique().astype(int)) if df_bal["ano_num"].notna().any() else ANOS

    if frequencia == "Anual":
        for ano in anos_unicos:
            df_bal_p = df_bal[(df_bal["ano_num"] == ano) & (df_bal["periodo_str"].str.contains("4T|4", na=False))]
            if df_bal_p.empty:
                df_bal_p = df_bal[df_bal["ano_num"] == ano]

            df_dre_p = df_d[df_d["ano_num"] == ano]

            emp_cp = pd.to_numeric(df_bal_p[(df_bal_p["indicador_norm"].str.contains("emprestimos")) & (df_bal_p["subgrupo_norm"].str.contains("circulante"))][col_val_bal], errors="coerce").sum()
            emp_lp = pd.to_numeric(df_bal_p[(df_bal_p["indicador_norm"].str.contains("emprestimos")) & (~df_bal_p["subgrupo_norm"].str.contains("circulante"))][col_val_bal], errors="coerce").sum()
            valor_caixa = pd.to_numeric(df_bal_p[df_bal_p["indicador_norm"].str.contains("caixa")][col_val_bal], errors="coerce").sum()
            valor_arrendamento = pd.to_numeric(df_bal_p[df_bal_p["indicador_norm"].eq("arrendamento")][col_val_bal], errors="coerce").sum()

            ebitda_rows = df_dre_p[df_dre_p["indicador_norm"].str.contains("ebitda", na=False)]
            valor_ebitda = pd.to_numeric(ebitda_rows[col_val_dre], errors="coerce").sum()

            divida_bruta = emp_cp + emp_lp
            divida_liquida = divida_bruta - valor_caixa
            alavancagem = (divida_liquida / valor_ebitda) if (valor_ebitda is not None and valor_ebitda != 0) else None

            resultados.append({
                "Periodo": str(ano),
                "Ordem": int(ano),
                "Dívida CP": emp_cp / 1000.0,
                "Dívida LP": emp_lp / 1000.0,
                "Caixa": valor_caixa / 1000.0,
                "Arrendamento": valor_arrendamento / 1000.0,
                "Dívida Bruta": divida_bruta / 1000.0,
                "Dívida Líquida": divida_liquida / 1000.0,
                "EBITDA": valor_ebitda / 1000.0,
                "Dívida Líquida / EBITDA": alavancagem,
            })

    elif frequencia == "Semestral":
        for ano in anos_unicos:
            for sem in [1, 2]:
                rotulo = f"{ano}-S{sem}"
                ordem = ano * 10 + sem
                tris_dre = [1, 2] if sem == 1 else [3, 4]
                tri_fecho_balanco = 2 if sem == 1 else 4

                df_bal_p = df_bal[(df_bal["ano_num"] == ano) & (df_bal["tri_num"] == tri_fecho_balanco)]
                if df_bal_p.empty:
                    df_bal_p = df_bal[(df_bal["ano_num"] == ano) & (df_bal["periodo_str"].str.contains(f"{tri_fecho_balanco}T|{tri_fecho_balanco}", na=False))]

                df_dre_p = df_d[(df_d["ano_num"] == ano) & (df_d["tri_num"].isin(tris_dre))]

                emp_cp = pd.to_numeric(df_bal_p[(df_bal_p["indicador_norm"].str.contains("emprestimos")) & (df_bal_p["subgrupo_norm"].str.contains("circulante"))][col_val_bal], errors="coerce").sum()
                emp_lp = pd.to_numeric(df_bal_p[(df_bal_p["indicador_norm"].str.contains("emprestimos")) & (~df_bal_p["subgrupo_norm"].str.contains("circulante"))][col_val_bal], errors="coerce").sum()
                valor_caixa = pd.to_numeric(df_bal_p[df_bal_p["indicador_norm"].str.contains("caixa")][col_val_bal], errors="coerce").sum()
                valor_arrendamento = pd.to_numeric(df_bal_p[df_bal_p["indicador_norm"].eq("arrendamento")][col_val_bal], errors="coerce").sum()

                ebitda_rows = df_dre_p[df_dre_p["indicador_norm"].str.contains("ebitda", na=False)]
                valor_ebitda = pd.to_numeric(ebitda_rows[col_val_dre], errors="coerce").sum()

                divida_bruta = emp_cp + emp_lp
                divida_liquida = divida_bruta - valor_caixa
                alavancagem = (divida_liquida / valor_ebitda) if (valor_ebitda is not None and valor_ebitda != 0) else None

                resultados.append({
                    "Periodo": rotulo,
                    "Ordem": ordem,
                    "Dívida CP": emp_cp / 1000.0,
                    "Dívida LP": emp_lp / 1000.0,
                    "Caixa": valor_caixa / 1000.0,
                    "Arrendamento": valor_arrendamento / 1000.0,
                    "Dívida Bruta": divida_bruta / 1000.0,
                    "Dívida Líquida": divida_liquida / 1000.0,
                    "EBITDA": valor_ebitda / 1000.0,
                    "Dívida Líquida / EBITDA": alavancagem,
                })

    else:  # Trimestral
        for ano in anos_unicos:
            for tri in [1, 2, 3, 4]:
                rotulo = f"{tri}T{str(ano)[2:]}"
                ordem = ano * 10 + tri

                df_bal_p = df_bal[(df_bal["ano_num"] == ano) & (df_bal["tri_num"] == tri)]
                if df_bal_p.empty:
                    df_bal_p = df_bal[(df_bal["ano_num"] == ano) & (df_bal["periodo_str"] == rotulo)]

                df_dre_p = df_d[(df_d["ano_num"] == ano) & (df_d["tri_num"] == tri)]
                if df_dre_p.empty:
                    df_dre_p = df_d[(df_d["ano_num"] == ano) & (df_d["periodo_str"] == rotulo)]

                if df_bal_p.empty and df_dre_p.empty:
                    continue

                emp_cp = pd.to_numeric(df_bal_p[(df_bal_p["indicador_norm"].str.contains("emprestimos")) & (df_bal_p["subgrupo_norm"].str.contains("circulante"))][col_val_bal], errors="coerce").sum()
                emp_lp = pd.to_numeric(df_bal_p[(df_bal_p["indicador_norm"].str.contains("emprestimos")) & (~df_bal_p["subgrupo_norm"].str.contains("circulante"))][col_val_bal], errors="coerce").sum()
                valor_caixa = pd.to_numeric(df_bal_p[df_bal_p["indicador_norm"].str.contains("caixa")][col_val_bal], errors="coerce").sum()
                valor_arrendamento = pd.to_numeric(df_bal_p[df_bal_p["indicador_norm"].eq("arrendamento")][col_val_bal], errors="coerce").sum()

                ebitda_rows = df_dre_p[df_dre_p["indicador_norm"].str.contains("ebitda", na=False)]
                valor_ebitda = pd.to_numeric(ebitda_rows[col_val_dre], errors="coerce").sum()

                divida_bruta = emp_cp + emp_lp
                divida_liquida = divida_bruta - valor_caixa
                alavancagem = (divida_liquida / valor_ebitda) if (valor_ebitda is not None and valor_ebitda != 0) else None

                resultados.append({
                    "Periodo": rotulo,
                    "Ordem": ordem,
                    "Dívida CP": emp_cp / 1000.0,
                    "Dívida LP": emp_lp / 1000.0,
                    "Caixa": valor_caixa / 1000.0,
                    "Arrendamento": valor_arrendamento / 1000.0,
                    "Dívida Bruta": divida_bruta / 1000.0,
                    "Dívida Líquida": divida_liquida / 1000.0,
                    "EBITDA": valor_ebitda / 1000.0,
                    "Dívida Líquida / EBITDA": alavancagem,
                })

    df_final = pd.DataFrame(resultados)
    if not df_final.empty:
        df_final = df_final.sort_values("Ordem").drop(columns=["Ordem"])
    return df_final

# ============================================================
# GRÁFICOS
# ============================================================

def grafico_alavancagem(df):
    col_x = "Periodo" if "Periodo" in df.columns else df.columns[0]
    fig = go.Figure()
    dados = df.copy()
    cores = [
        VERMELHO if pd.notna(v) and v > META_ALAVANCAGEM else TURQUESA
        for v in dados["Dívida Líquida / EBITDA"]
    ]
    fig.add_trace(go.Bar(
        x=dados[col_x],
        y=dados["Dívida Líquida / EBITDA"],
        marker_color=cores,
        text=[f"{v:.2f}x" if pd.notna(v) else "N/A" for v in dados["Dívida Líquida / EBITDA"]],
        textposition="outside",
        name="Dívida Líquida / EBITDA",
        hovertemplate="Período: %{x}<br>Alavancagem: %{y:.2f}x<extra></extra>",
    ))
    fig.add_hline(
        y=META_ALAVANCAGEM, line_dash="dash", line_color=DOURADO,
        annotation_text="Meta: 1,5x", annotation_position="top left",
    )
    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis_title="Período", yaxis_title="Multiplicador (x)",
        xaxis=dict(type="category"),
        yaxis=dict(rangemode="tozero", gridcolor="#E8EDF4"),
        hovermode="x unified",
    )
    return fig

def grafico_divida_ebitda(df):
    col_x = "Periodo" if "Periodo" in df.columns else df.columns[0]
    dados = df.melt(
        id_vars=[col_x],
        value_vars=["Dívida Líquida", "EBITDA"],
        var_name="Indicador",
        value_name="Valor",
    )

    fig = px.bar(
        dados,
        x=col_x,
        y="Valor",
        color="Indicador",
        barmode="group",
        color_discrete_map={"Dívida Líquida": AZUL, "EBITDA": TURQUESA},
        labels={col_x: "Período", "Valor": "R$ milhões", "Indicador": "Indicador"},
        text_auto=".2f",
    )

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        xaxis=dict(type="category"),
        yaxis=dict(gridcolor="#E8EDF4"),
        hovermode="x unified",
    )
    return fig

def grafico_composicao_divida(df):
    col_x = "Periodo" if "Periodo" in df.columns else df.columns[0]
    fig = go.Figure()

    fig.add_trace(go.Bar(x=df[col_x], y=df["Dívida CP"], name="Empréstimos — circulante", marker_color=AZUL))
    fig.add_trace(go.Bar(x=df[col_x], y=df["Dívida LP"], name="Empréstimos — não circulante", marker_color=MARINHO))
    fig.add_trace(go.Bar(x=df[col_x], y=df["Arrendamento"], name="Arrendamento", marker_color=TURQUESA))

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        xaxis_title="Período", yaxis_title="R$ milhões",
        xaxis=dict(type="category"),
        yaxis=dict(gridcolor="#E8EDF4"),
        barmode="stack",
        hovermode="x unified",
    )
    return fig
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

CAMINHO_BALANCO = _buscar_arquivo("balanco_trimestral_2021_2025_estruturado.csv")
CAMINHO_DRE = _buscar_arquivo("dre_anual_2021_2025.csv")

ANOS = [2021, 2022, 2023, 2024, 2025]
META_ALAVANCAGEM = 1.5

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
VERMELHO = "#C94C4C"


# ============================================================
# CARREGAMENTO E FORMATAÇÃO
# ============================================================

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().casefold()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def converter_numero(valor):
    if pd.isna(valor) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if texto in ("", "-", "—", "nan", "None"):
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


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
        raise FileNotFoundError(f"Base do balanço não encontrada:\n{CAMINHO_BALANCO}")
    if not CAMINHO_DRE.exists():
        raise FileNotFoundError(f"Base da DRE não encontrada:\n{CAMINHO_DRE}")

    df_balanco = pd.read_csv(CAMINHO_BALANCO)
    df_dre = pd.read_csv(CAMINHO_DRE)

    return df_balanco, df_dre


def preparar_dados(df_balanco, df_dre):
    df_balanco["indicador_norm"] = df_balanco["indicador_pt"].fillna("").map(normalizar_texto)
    df_balanco["subgrupo_norm"] = df_balanco["subgrupo"].fillna("").map(normalizar_texto)
    df_dre["indicador_norm"] = df_dre["indicador_pt"].fillna("").map(normalizar_texto)

    resultados = []

    for ano in ANOS:
        # Consolida fechamento trimestral (4T) para o balanço
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

        valor_caixa = df_bal_ano[
            df_bal_ano["indicador_norm"].str.contains("caixa e equivalentes de caixa")
        ]["valor"].sum()

        valor_arrendamento = df_bal_ano[
            df_bal_ano["indicador_norm"].eq("arrendamento")
        ]["valor"].sum()

        # DRE Anual
        df_dre_ano = df_dre[df_dre["ano"] == ano]
        ebitda_row = df_dre_ano[df_dre_ano["indicador_norm"].eq("ebitda")]
        valor_ebitda = ebitda_row["valor"].values[0] if not ebitda_row.empty else 0.0

        divida_bruta = emp_cp + emp_lp
        divida_liquida = divida_bruta - valor_caixa

        alavancagem = (
            divida_liquida / valor_ebitda
            if valor_ebitda is not None and valor_ebitda > 0
            else None
        )

        resultados.append({
            "Ano": ano,
            "Dívida CP": emp_cp / 1000.0,
            "Dívida LP": emp_lp / 1000.0,
            "Caixa": valor_caixa / 1000.0,
            "Arrendamento": valor_arrendamento / 1000.0,
            "Dívida Bruta": divida_bruta / 1000.0,
            "Dívida Líquida": divida_liquida / 1000.0,
            "EBITDA": valor_ebitda / 1000.0,
            "Dívida Líquida / EBITDA": alavancagem,
        })

    return pd.DataFrame(resultados)


# ============================================================
# GRÁFICOS
# ============================================================

def grafico_alavancagem(df):
    fig = go.Figure()
    dados = df.sort_values("Ano")
    cores = [
        VERMELHO if pd.notna(v) and v > META_ALAVANCAGEM else TURQUESA
        for v in dados["Dívida Líquida / EBITDA"]
    ]
    fig.add_trace(go.Bar(
        x=dados["Ano"],
        y=dados["Dívida Líquida / EBITDA"],
        marker_color=cores,
        text=[
            f"{v:.2f}x" if pd.notna(v) else "N/A"
            for v in dados["Dívida Líquida / EBITDA"]
        ],
        textposition="outside",
        name="Dívida Líquida / EBITDA",
        hovertemplate="Ano: %{x}<br>Alavancagem: %{y:.2f}x<extra></extra>",
    ))
    fig.add_hline(
        y=META_ALAVANCAGEM, line_dash="dash", line_color=DOURADO,
        annotation_text="Meta: 1,5x", annotation_position="top left",
    )
    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO), showlegend=False,
        xaxis_title="Ano", yaxis_title="Multiplicador (x)",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(rangemode="tozero", gridcolor="#E8EDF4"),
        hovermode="x unified",
    )
    return fig


def grafico_divida_ebitda(df):
    dados = df.melt(
        id_vars=["Ano"],
        value_vars=["Dívida Líquida", "EBITDA"],
        var_name="Indicador",
        value_name="Valor",
    )

    fig = px.bar(
        dados,
        x="Ano",
        y="Valor",
        color="Indicador",
        barmode="group",
        color_discrete_map={"Dívida Líquida": AZUL, "EBITDA": TURQUESA},
        labels={
            "Ano": "Ano",
            "Valor": "R$ milhões",
            "Indicador": "Indicador",
        },
        text_auto=".2f",
    )

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
        hovermode="x unified",
    )

    return fig


def grafico_composicao_divida(df):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["Ano"],
            y=df["Dívida CP"],
            name="Empréstimos — circulante",
            marker_color=AZUL,
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["Ano"],
            y=df["Dívida LP"],
            name="Empréstimos — não circulante",
            marker_color=MARINHO,
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["Ano"],
            y=df["Arrendamento"],
            name="Arrendamento",
            marker_color=TURQUESA,
        )
    )

    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=25, b=15),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=MARINHO),
        xaxis_title="Ano",
        yaxis_title="R$ milhões",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#E8EDF4"),
        barmode="stack",
        hovermode="x unified",
    )

    return fig