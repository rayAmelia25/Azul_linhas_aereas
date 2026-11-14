import base64
from pathlib import Path
import pandas as pd
import streamlit as st

from funcoes_tela3 import (
    carregar_dados,
    preparar_dados,
    obter_medias_periodo,
    formatar_moeda,
    grafico_receita_ebitda,
    grafico_margem_ebitda,
    grafico_lucro_prejuizo,
    preparar_custos_despesas,
    grafico_composicao_custos,
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
            
            /* Regras restritas à área principal para sobrescrever os seletores do Streamlit */
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
# CONVERSÃO DA IMAGEM DO AVIÃO EM BASE64
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
                <h1>Resultados Financeiros</h1>
                <p>Acompanhe o desempenho da receita, a rentabilidade operacional (EBITDA) e a estrutura de custos da companhia.</p>
            </div>
            {"<div class='hero-img-container'><img src='" + img_aviao_base64 + "' alt='Avião Azul'></div>" if img_aviao_base64 else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# RESUMO FINANCEIRO — MÉDIA DO PERÍODO
# ==========================================

def exibir_resumo_medio(df_longo):
    medias = obter_medias_periodo(df_longo)

    st.markdown(
        """
        <div class="section-label">Visão Geral</div>
        <h2 style="margin-top:0;">Resumo Financeiro (Média do Período 2021-2025)</h2>
        <div class="section-description">
            Média anual acumulada dos principais indicadores do demonstrativo de resultados.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.metric(
            "Receita líquida média",
            formatar_moeda(medias["media_receita"]),
            help="Média do faturamento anual da companhia no período de 2021 a 2025.",
        )

    with col2:
        st.metric(
            "EBITDA médio",
            formatar_moeda(medias["media_ebitda"]),
            help="Média da geração de caixa operacional anual entre 2021 e 2025.",
        )

    with col3:
        st.metric(
            "Margem EBITDA média",
            f"{medias['media_margem']:.2f}%".replace(".", ",") if medias["media_margem"] is not None else "N/A",
            help="Média percentual da receita convertida em EBITDA no período.",
        )

    with col4:
        st.metric(
            "Resultado líquido médio",
            formatar_moeda(medias["media_lucro"]),
            delta_color="normal" if medias["media_lucro"] and medias["media_lucro"] >= 0 else "inverse",
            help="Média do lucro ou prejuízo líquido anual entre 2021 e 2025.",
        )

# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================

def main():
    # APLICAR ESTILOS NO INÍCIO DA RENDERIZAÇÃO
    aplicar_estilos()

    exibir_cabecalho()

    try:
        df = carregar_dados()
        df_longo = preparar_dados(df)
    except Exception as erro:
        st.error(f"Erro ao carregar ou preparar os dados: {erro}")
        st.stop()

    anos_disponiveis = sorted(df_longo["ano"].dropna().unique().astype(int).tolist())

    if not anos_disponiveis:
        st.warning("Nenhum ano disponível na DRE.")
        st.stop()

    # Resumo Executivo em Média do Período
    exibir_resumo_medio(df_longo)

    st.divider()

    # Gráfico 1: Receita vs EBITDA
    st.markdown(
        """
        <div class="section-label">01 • faturamento & caixa</div>
        <h2 style="margin-top:0;">Receita líquida versus EBITDA</h2>
        <div class="section-description">
            Evolução comparativa entre o faturamento líquido total e a geração operacional de caixa.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(grafico_receita_ebitda(df_longo), use_container_width=True)
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # Gráficos 2 e 3: Margem EBITDA e Lucro/Prejuízo Lado a Lado
    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown(
            """
            <div class="section-label">02 • Eficiência</div>
            <h2 style="margin-top:0;">Margem EBITDA (%)</h2>
            <div class="section-description">
                Percentual da receita que é transformado em caixa operacional.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(grafico_margem_ebitda(df_longo), use_container_width=True)
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual (2021-2025)</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown(
            """
            <div class="section-label">03 • Resultado Final</div>
            <h2 style="margin-top:0;">Lucro / prejuízo líquido</h2>
            <div class="section-description">
                Resultado contábil do exercício após despesas financeiras e impostos.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(grafico_lucro_prejuizo(df_longo), use_container_width=True)
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # Gráfico 4: Composição de Custos
    st.markdown(
        """
        <div class="section-label">04 • Detalhamento de Custos</div>
        <h2 style="margin-top:0;">Composição dos custos dos serviços prestados</h2>
        <div class="section-description">
            Distribuição dos custos operacionais diretos da Azul por categoria.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_filtro, _ = st.columns([1, 3])
    with col_filtro:
        ano_custos = st.selectbox(
            "Selecione o ano dos custos:",
            options=anos_disponiveis,
            index=len(anos_disponiveis) - 1,
            key="ano_custos_tela3",
        )

    try:
        df_custos = preparar_custos_despesas(df, ano_custos)

        if df_custos.empty:
            st.warning("Nenhuma conta de custos encontrada para esse ano.")
        else:
            st.plotly_chart(grafico_composicao_custos(df_custos), use_container_width=True)
            st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual detalhada</div>', unsafe_allow_html=True)

    except Exception as erro:
        st.error(f"Erro ao gerar o gráfico de custos: {erro}")

    st.divider()

    # Tabela Expansível de Dados
    with st.expander("Consultar dados utilizados na análise"):
        st.caption("Valores extraídos diretamente das demonstrações do resultado do exercício (DRE).")
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_tela3():
    main()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Resultados Financeiros | Azul",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    main()