import base64
from pathlib import Path
import pandas as pd
import streamlit as st

from funcoes_tela4 import (
    carregar_dados,
    preparar_dados_patrimoniais,
    formatar_moeda,
    grafico_entradas_saidas,
    grafico_estrutura_patrimonial,
    grafico_liquidez_corrente,
)

# ==========================================
# PALETA VISUAL
# ==========================================

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
FUNDO = "#F1F4F8"

# ==========================================
# ESTILOS CSS (Aplicados dentro da função)
# ==========================================

def aplicar_estilos():
    st.markdown(
        f"""
        <style>
            .stApp {{ background-color: {FUNDO}; }}
            [data-testid="stHeader"] {{ background-color: transparent; }}
            .block-container {{
                padding-top: 1.6rem;
                padding-bottom: 2rem;
                max-width: 1500px;
            }}
            
            /* Regras restritas à área principal igual à tela1 */
            .main h1, .main h2, .main h3 {{ color: {MARINHO} !important; letter-spacing: -0.4px; }}
            .main p, .main label {{ color: {MARINHO}; }}

            /* HERO CARD COM IMAGEM SOBREPOSTA */
            .hero {{
                position: relative;
                background: linear-gradient(120deg, {MARINHO} 0%, {AZUL} 100%);
                padding: 32px 36px;
                border-radius: 18px;
                margin-bottom: 28px;
                box-shadow: 0 5px 18px rgba(16,44,84,.12);
                display: flex;
                justify-content: space-between;
                align-items: center;
                overflow: visible !important;
            }}
            .hero-text {{ max-width: 60%; z-index: 2; }}
            .hero-label {{
                color: #BBD4F5; font-size: 12px; font-weight: 700;
                text-transform: uppercase; letter-spacing: 2px; margin-bottom: 7px;
            }}
            .hero h1 {{ color: white !important; font-size: 32px; margin: 0 0 8px 0; }}
            .hero p {{ color: #E4ECF7 !important; font-size: 14px; margin: 0; }}
            
            .hero-img-container {{
                position: absolute; right: -25px; top: 50%;
                transform: translateY(-50%); z-index: 3; pointer-events: none;
            }}
            .hero-img-container img {{
                width: 550px; height: auto;
                filter: drop-shadow(0px 12px 18px rgba(0, 0, 0, 0.45));
            }}

            .section-label {{
                color: {AZUL}; font-size: 11px; font-weight: 750;
                text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;
            }}
            .section-description {{ color: #68778B; font-size: 13px; margin-bottom: 13px; }}

            div[data-testid="stMetric"] {{
                background: white; border: 1px solid #E0E7F0; border-radius: 14px;
                padding: 17px 17px 12px 17px; min-height: 125px;
                box-shadow: 0 3px 12px rgba(16,44,84,.04);
            }}
            div[data-testid="stMetricLabel"] {{ color: #63748A !important; font-size: 12px; }}
            div[data-testid="stMetricValue"] {{ color: {MARINHO} !important; font-size: 23px; font-weight: 750; }}

            div[data-testid="stPlotlyChart"] {{
                background: white; border: 1px solid #E0E7F0; border-radius: 15px;
                padding: 8px; box-shadow: 0 3px 12px rgba(16,44,84,.035);
            }}

            .chart-legend-tag {{
                font-size: 12px; color: #68778B; background: #E8EDF4;
                padding: 4px 10px; border-radius: 6px; display: inline-block;
                margin-top: 6px; margin-bottom: 12px; font-weight: 600;
            }}

            .footer {{ text-align: center; color: #75849A; font-size: 12px; padding-top: 22px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# CONVERSÃO DE IMAGENS EM BASE64
# ==========================================

def obter_imagem_base64(termo_busca):
    diretorios = [
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parents[1],
        Path(__file__).resolve().parents[2],
    ]
    for d in diretorios:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and termo_busca.lower() in f.name.lower():
                    try:
                        with open(f, "rb") as arq:
                            return f"data:image/png;base64,{base64.b64encode(arq.read()).decode()}"
                    except Exception:
                        continue
    return ""

img_aviao_base64 = obter_imagem_base64("azul-air-asia")

# ==========================================
# CABEÇALHO
# ==========================================

def exibir_cabecalho():
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-text">
                <div class="hero-label">Análise financeira • Azul S.A.</div>
                <h1>Fluxo de Caixa e Saúde Patrimonial</h1>
                <p>Verifique a capacidade de sustentar as operações e administrar as obrigações patrimoniais da companhia.</p>
            </div>
            {"<div class='hero-img-container'><img src='" + img_aviao_base64 + "' alt='Avião Azul'></div>" if img_aviao_base64 else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# INDICADORES EXECUTIVOS (MÉDIA DO PERÍODO)
# ==========================================

def exibir_resumo(df):
    media_caixa = df["Caixa"].mean()
    media_ac = df["Ativo Circulante"].mean()
    media_pc = df["Passivo Circulante"].mean()
    media_lc = df["Liquidez Corrente"].mean()

    st.markdown(
        """
        <div class="section-label">Visão Geral</div>
        <h2 style="margin-top:0;">Saúde Patrimonial e Solvência (Média 2021-2025)</h2>
        <div class="section-description">
            Principais métricas de liquidez e capacidade de cobertura de compromissos no curto e longo prazo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.metric(
            "Caixa médio disponível",
            formatar_moeda(media_caixa),
            help="Saldo médio mantido em caixa e equivalentes.",
        )

    with c2:
        st.metric(
            "Ativo Circulante médio",
            formatar_moeda(media_ac),
            help="Bens e direitos conversíveis em dinheiro no curto prazo.",
        )

    with c3:
        st.metric(
            "Passivo Circulante médio",
            formatar_moeda(media_pc),
            help="Obrigações e dívidas com vencimento em até 12 meses.",
        )

    with c4:
        st.metric(
            "Liquidez Corrente média",
            f"{media_lc:.2f}x".replace(".", ","),
            help="Relação média entre Ativo Circulante e Passivo Circulante. Referência ideal >= 1,0x.",
        )

# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================

def render_tela4():
    # APLICAR ESTILOS NO INÍCIO DA RENDERIZAÇÃO
    aplicar_estilos()
    
    exibir_cabecalho()

    try:
        df_balanco, df_dre = carregar_dados()
        df = preparar_dados_patrimoniais(df_balanco, df_dre)
    except Exception as erro:
        st.error(f"Erro ao carregar os dados patrimoniais: {erro}")
        st.stop()

    # Cartões Indicadores
    exibir_resumo(df)

    st.divider()

    # Gráfico 1: Colunas divergentes - Entradas e saídas de caixa
    st.markdown(
        """
        <div class="section-label">01 • Operacional</div>
        <h2 style="margin-top:0;">Entradas e saídas operacionais de caixa</h2>
        <div class="section-description">
            Comparativo entre receitas (entradas) e custos operacionais (saídas) para verificar a evolução do faturamento operacional.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(grafico_entradas_saidas(df), use_container_width=True)
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # Gráfico 2: Estrutura Patrimonial
    st.markdown(
        """
        <div class="section-label">02 • Estrutura</div>
        <h2 style="margin-top:0;">Estrutura patrimonial (Ativos, Passivos e PL)</h2>
        <div class="section-description">
            Distribuição dos ativos e obrigações por prazo de vencimento (circulante e não circulante) e capital próprio.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(grafico_estrutura_patrimonial(df), use_container_width=True)
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Balanço Trimestral Consolidado 4T (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # Gráfico 3: Linha - Liquidez Corrente
    st.markdown(
        """
        <div class="section-label">03 • Liquidez</div>
        <h2 style="margin-top:0;">Evolução da liquidez corrente</h2>
        <div class="section-description">
            Acompanhamento da capacidade de pagamento das obrigações de curto prazo (Ativo Circulante / Passivo Circulante).
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(grafico_liquidez_corrente(df), use_container_width=True)
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Balanço Trimestral Consolidado 4T (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # Tabela Expansível
    with st.expander("Consultar dados patrimoniais utilizados na análise"):
        st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Fluxo de Caixa e Patrimônio | Azul",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    render_tela4()
