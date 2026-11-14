import base64
from pathlib import Path
import pandas as pd
import streamlit as st

from funcoes_tela2 import (
    carregar_dados,
    preparar_dados,
    grafico_alavancagem,
    grafico_divida_ebitda,
    grafico_composicao_divida,
    formatar_moeda,
    formatar_numero,
)

# ==========================================
# PALETA VISUAL
# ==========================================

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
TURQUESA2 = "#2ad2c3"
DOURADO = "#E5A544"
FUNDO = "#F1F4F8"

# ==========================================
# FUNÇÃO PARA CONVERTER IMAGEM PARA BASE64
# ==========================================

def obter_imagem_base64(nome_arquivo):
    caminhos = list(Path(__file__).resolve().parents[2].rglob(nome_arquivo)) + \
               list(Path(__file__).resolve().parents[1].rglob(nome_arquivo)) + \
               [Path(nome_arquivo)]
    
    for c in caminhos:
        if c.exists() and c.is_file():
            with open(c, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

img_aviao_base64 = obter_imagem_base64("azul-air-asia-a330-neo-capa-removebg-preview.png")
img_cartao_base64 = obter_imagem_base64("CARD-12-removebg-preview.png")


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
            
            /* Regras restritas à área principal (.main) para NÃO alterar o menu lateral */
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

            .card-img-container {{
                text-align: center;
                margin-top: 14px;
                margin-bottom: 4px;
            }}
            .card-img-container img {{
                max-width: 80%;
                max-height: 175px;
                height: auto;
                object-fit: contain;
                filter: drop-shadow(0px 8px 16px rgba(16, 44, 84, 0.25));
            }}

            .footer {{ text-align: center; color: #75849A; font-size: 12px; padding-top: 22px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# CARTÕES DE INDICADORES
# ==========================================

def exibir_cartoes(df):
    df = df.sort_values("Ano").reset_index(drop=True)
    atual = df.iloc[-1]

    divida_bruta = atual.get("Dívida Bruta")
    divida_liquida = atual.get("Dívida Líquida")
    ebitda = atual.get("EBITDA")

    variacao = None

    if len(df) >= 2:
        anterior = df.iloc[-2]
        divida_liquida_anterior = anterior.get("Dívida Líquida")

        if pd.notna(divida_liquida) and pd.notna(divida_liquida_anterior) and divida_liquida_anterior != 0:
            variacao = ((divida_liquida - divida_liquida_anterior) / abs(divida_liquida_anterior)) * 100

    alavancagem = (
        divida_liquida / ebitda
        if pd.notna(divida_liquida) and pd.notna(ebitda) and ebitda > 0
        else None
    )

    st.markdown(
        f"""
        <div class="section-label">Visão geral</div>
        <h2 style="margin-top:0;">Indicadores de Endividamento</h2>
        <div class="section-description">
            Principais métricas de endividamento e alavancagem em {int(atual['Ano'])}.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.metric(
            "Dívida bruta",
            formatar_moeda(divida_bruta),
            help="Total das obrigações financeiras consideradas no cálculo.",
        )

    with col2:
        st.metric(
            "Dívida líquida",
            formatar_moeda(divida_liquida),
            help="Dívida bruta menos caixa e equivalentes, conforme os dados utilizados.",
        )

    with col3:
        st.metric(
            "Dívida líquida / EBITDA",
            f"{formatar_numero(alavancagem)}x" if alavancagem is not None else "N/A",
            delta=f"Meta: até 1,5x | {formatar_numero(alavancagem - 1.5)}x da meta" if alavancagem is not None else None,
            delta_color="inverse" if alavancagem is not None and alavancagem > 1.5 else "normal",
            help="Indicador de alavancagem. A referência utilizada neste painel é 1,5x.",
        )

    with col4:
        st.metric(
            "Variação anual da dívida",
            f"{formatar_numero(variacao)}%" if variacao is not None else "N/A",
            delta="Em relação ao ano anterior" if variacao is not None else None,
            delta_color="off",
            help="Variação percentual da dívida líquida em relação ao ano anterior.",
        )


# ==========================================
# CABEÇALHO
# ==========================================

def exibir_cabecalho():
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-text">
                <div class="hero-label">Análise financeira • Azul S.A.</div>
                <h1>Endividamento e Alavancagem</h1>
                <p>Acompanhe a evolução da dívida, a capacidade de pagamento e a estrutura financeira da companhia.</p>
            </div>
            {"<div class='hero-img-container'><img src='" + img_aviao_base64 + "' alt='Avião Azul'></div>" if img_aviao_base64 else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# APLICAÇÃO PRINCIPAL DA TELA 2
# ==========================================

def render_tela2():
    aplicar_estilos()
    exibir_cabecalho()

    try:
        df_balanco, df_dre = carregar_dados()
        df = preparar_dados(df_balanco, df_dre)

        if df is None or df.empty:
            st.warning("Não há dados disponíveis para exibir.")
            st.stop()

    except Exception as erro:
        st.error(f"Erro ao carregar ou preparar os dados: {erro}")
        st.stop()

    # Indicadores Executivos
    exibir_cartoes(df)

    st.divider()

    # Gráfico 1: Evolução da Alavancagem
    st.markdown(
        """
        <div class="section-label">01 • Evolução</div>
        <h2 style="margin-top:0;">Alavancagem financeira</h2>
        <div class="section-description">
            A relação entre a dívida líquida e a geração operacional de caixa (EBITDA), com referência de 1,5x.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        grafico_alavancagem(df),
        use_container_width=True,
    )
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual e Balanço 4T (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # Gráfico 2: Comparação Dívida Líquida vs EBITDA + Quadro Interpretativo + Cartão
    st.markdown(
        """
        <div class="section-label">02 • Comparação</div>
        <h2 style="margin-top:0;">Dívida versus geração operacional</h2>
        <div class="section-description">
            Trajetória comparativa entre a dívida líquida total e a geração operacional de caixa.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_grafico, col_info = st.columns([2, 1], gap="large")

    with col_grafico:
        st.plotly_chart(
            grafico_divida_ebitda(df),
            use_container_width=True,
        )
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: DRE Anual e Balanço 4T (2021-2025)</div>', unsafe_allow_html=True)

    with col_info:
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E7F0;
                border-radius: 15px;
                padding: 20px 22px;
                box-shadow: 0 3px 12px rgba(16,44,84,.035);
            ">
                <div style="
                    color: {TURQUESA};
                    font-size: 12px;
                    font-weight: 750;
                    letter-spacing: 1px;
                ">
                    COMO INTERPRETAR
                </div>
                <h3 style="font-size:18px; margin-top:6px; margin-bottom:12px;">O que observar?</h3>
                <p style="color:#63748A; font-size:12.5px; line-height:1.5; margin-bottom:10px;">
                    <b style="color:{MARINHO};">Dívida em alta:</b>
                    Investigue se o aumento está associado a novos leasings de aeronaves, refinanciamentos ou pressões operacionais.
                </p>
                <p style="color:#63748A; font-size:12.5px; line-height:1.5; margin:0;">
                    <b style="color:{MARINHO};">EBITDA em alta:</b>
                    Avalie se a geração operacional acompanha o ritmo do endividamento para garantir sustentabilidade.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        if img_cartao_base64:
            st.markdown(
                f"""
                <div class="card-img-container">
                    <img src="{img_cartao_base64}" alt="Cartão Azul Visa">
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # Gráfico 3: Composição da dívida
    st.markdown(
        """
        <div class="section-label">03 • Estrutura</div>
        <h2 style="margin-top:0;">Composição da dívida</h2>
        <div class="section-description">
            Distribuição das obrigações entre prazos de vencimento (curto e longo prazo) e arrendamentos.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        grafico_composicao_divida(df),
        use_container_width=True,
    )
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Balanço Trimestral Consolidado 4T (2021-2025)</div>', unsafe_allow_html=True)

    # Tabela detalhada
    st.divider()

    with st.expander("Consultar dados utilizados na análise"):
        st.caption("Valores estruturados e consolidados por ano (em R$ milhões).")
        st.dataframe(
            df.sort_values("Ano", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            label="Baixar dados em CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="endividamento_azul.csv",
            mime="text/csv",
        )

    st.markdown(
        """
        <div class="footer">
            Azul S.A. • Dashboard de análise financeira
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    render_tela2()