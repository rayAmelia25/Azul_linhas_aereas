import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from funcoes_tela5 import (
    ANO_META,
    carregar_operacionais,
    preparar_eficiencia,
    formatar_numero,
    formatar_percentual,
    grafico_load_factor,
    grafico_rask_cask,
    grafico_rpk_ask,
    grafico_criacao_valor,
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
            
            /* Regras restritas à área principal para garantir sobrescrita dos seletores */
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
                <h1>Eficiência operacional e criação de valor</h1>
                <p>Relaciona a operação aérea com a criação de valor e o caminho até as metas de {ANO_META}.</p>
            </div>
            {"<div class='hero-img-container'><img src='" + img_aviao_base64 + "' alt='Avião Azul'></div>" if img_aviao_base64 else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# RESUMO DA EFICIÊNCIA — ÚLTIMO ANO
# ==========================================

def exibir_resumo(tabela):
    atual = tabela.sort_values("Ano").iloc[-1]
    inicial = tabela.sort_values("Ano").iloc[0]
    ano_atual, ano_inicial = int(atual["Ano"]), int(inicial["Ano"])

    st.markdown(
        f"""
        <div class="section-label">Visão Geral</div>
        <h2 style="margin-top:0;">Resumo operacional ({ano_atual})</h2>
        <div class="section-description">
            Principais indicadores de eficiência do último ano disponível, comparados com {ano_inicial}.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        delta_lf = atual["Load Factor (%)"] - inicial["Load Factor (%)"]
        st.metric(
            "Load Factor",
            formatar_percentual(atual["Load Factor (%)"], 1),
            delta=f"{formatar_numero(delta_lf, 1)} p.p. vs {ano_inicial}",
            help="Percentual da capacidade oferecida (ASK) que foi efetivamente ocupada (RPK ÷ ASK).",
        )

    with c2:
        st.metric(
            "RASK",
            formatar_percentual(atual["RASK Var (%)"], 1, sinal=True),
            delta=f"{formatar_numero(atual['RASK (centavos)'], 2)}¢ por ASK",
            help="Variação percentual da receita operacional por ASK em relação ao ano base de 2021.",
        )

    with c3:
        st.metric(
            "CASK",
            formatar_percentual(atual["CASK Var (%)"], 1, sinal=True),
            delta=f"{formatar_numero(atual['CASK (centavos)'], 2)}¢ por ASK",
            delta_color="inverse",
            help="Variação percentual do custo operacional por ASK em relação ao ano base de 2021.",
        )

    with c4:
        margem_atual = (atual["Spread RASK − CASK (centavos)"] / atual["RASK (centavos)"]) * 100
        margem_inicial = (inicial["Spread RASK − CASK (centavos)"] / inicial["RASK (centavos)"]) * 100
        delta_margem = margem_atual - margem_inicial

        st.metric(
            "Margem Spread (RASK − CASK)",
            formatar_percentual(margem_atual, 1),
            delta=f"{formatar_numero(delta_margem, 1)} p.p. vs {ano_inicial}",
            delta_color="normal" if delta_margem >= 0 else "inverse",
            help="Percentual da receita unitária (RASK) retido como margem sobre o custo unitário (CASK).",
        )

# ==========================================
# ÁREA B — CRIAÇÃO DE VALOR
# ==========================================

def exibir_area_b(tabela):
    st.markdown(
        f"""
        <div class="section-label">Área B • Criação de valor</div>
        <h2 style="margin-top:0;">Evolução da criação de valor</h2>
        <div class="section-description">
            Evolução histórica da Receita de Passageiros e trajetória necessária para alcançar a meta de Faturamento.
        </div>
        """,
        unsafe_allow_html=True,
    )

    val_ref = tabela.loc[tabela["Ano"] == 2025, "Receita Passageiros (R$ mi)"].values[0]
    val_meta = 25000.0  # Meta de R$ 25 bilhões em receitas de transporte para 2029

    var_acumulada_meta = ((val_meta - val_ref) / val_ref) * 100
    val_2021 = tabela.loc[tabela["Ano"] == 2021, "Receita Passageiros (R$ mi)"].values[0]
    var_historica_ref = ((val_ref - val_2021) / val_2021) * 100

    col_graf, col_ind = st.columns([2.2, 1], gap="large")

    with col_graf:
        st.plotly_chart(
            grafico_criacao_valor(tabela, val_ref, val_meta),
            use_container_width=True,
        )
        st.markdown(
            '<div class="chart-legend-tag">📅 Fonte dos dados: Dados Operacionais Anuais (2021-2025)</div>',
            unsafe_allow_html=True,
        )

    with col_ind:
        st.markdown("<h3 style='font-size:18px; margin-top:0;'>Indicador de Valorização</h3>", unsafe_allow_html=True)

        st.metric(
            "Receita de Passageiros (Ref. 2025)",
            f"R$ {val_ref:,.0f} Mi".replace(",", "."),
            delta=f"{var_historica_ref:.1f}% vs 2021".replace(".", ","),
            delta_color="normal" if var_historica_ref >= 0 else "inverse",
            help="Valor do faturamento de transporte de passageiros adotado como referência de partida.",
        )

        st.metric(
            "Variação Acumulada para a Meta",
            f"+{var_acumulada_meta:.1f}%".replace(".", ","),
            delta=f"Meta: R$ {val_meta:,.0f} Mi até {ANO_META}".replace(",", "."),
            delta_color="normal",
            help="Mudança percentual necessária em relação ao valor de referência adotado para a meta.",
        )

# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================

def render_tela5():
    # APLICAR ESTILOS NO INÍCIO DA RENDERIZAÇÃO
    aplicar_estilos()

    exibir_cabecalho()

    try:
        df = carregar_operacionais()
        tabela = preparar_eficiencia(df)
    except Exception as erro:
        st.error(f"Erro ao carregar os dados operacionais anuais: {erro}")
        st.stop()

    if tabela.empty:
        st.warning("Não há dados operacionais suficientes para esta tela.")
        st.stop()

    exibir_resumo(tabela)

    st.divider()

    # ---------------- ÁREA A ----------------
    st.markdown(
        """
        <div class="section-label">Área A • Eficiência operacional</div>
        <h2 style="margin-top:0;">A operação está usando bem seus recursos?</h2>
        <div class="section-description">
            Aproveitamento da capacidade, relação entre receita e custo por assento e equilíbrio entre demanda e oferta.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown(
            """
            <div class="section-label">01 • Ocupação</div>
            <h2 style="margin-top:0;">Load Factor (%)</h2>
            <div class="section-description">
                Percentual da capacidade oferecida que foi efetivamente ocupada.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(grafico_load_factor(tabela), use_container_width=True)
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Dados operacionais anuais (2021-2025)</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown(
            """
            <div class="section-label">02 • Receita × custo unitário</div>
            <h2 style="margin-top:0;">RASK versus CASK</h2>
            <div class="section-description">
                A área sombreada mostra o quanto a receita por ASK supera o custo por ASK.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(grafico_rask_cask(tabela), use_container_width=True)
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Dados operacionais anuais (2021-2025)</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-label">03 • Demanda × capacidade</div>
        <h2 style="margin-top:0;">RPK versus ASK</h2>
        <div class="section-description">
            Compara a demanda transportada (RPK) com a capacidade oferecida (ASK), em milhões.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(grafico_rpk_ask(tabela), use_container_width=True)
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Dados operacionais anuais (2021-2025)</div>', unsafe_allow_html=True)

    st.divider()

    # ---------------- ÁREA B ----------------
    exibir_area_b(tabela)

    st.divider()

    with st.expander("Consultar dados operacionais anuais utilizados na análise"):
        st.dataframe(tabela, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Eficiência e Valor | Azul",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    render_tela5()