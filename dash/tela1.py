import base64
from pathlib import Path
import pandas as pd
import streamlit as st

from funcoes_tela1 import (
    carregar_dados,
    preparar_visao_geral,
    grafico_esg_eficiencia_combustivel,
    grafico_esg_diversidade_governanca,
    formatar_moeda,
    formatar_numero,
)

# ============================================================
# PALETA VISUAL
# ============================================================

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
FUNDO = "#F1F4F8"
VERMELHO = "#C94C4C"
VERDE = "#23856D"

# ============================================================
# FUNÇÃO PARA CONVERTER IMAGEM LOCAL PARA BASE64
# ============================================================

def obter_imagem_base64(nome_arquivo):
    """Procura a imagem no projeto e converte para base64 para uso direto no HTML."""
    caminhos_possiveis = list(Path(__file__).resolve().parents[2].rglob(nome_arquivo)) + \
                        list(Path(__file__).resolve().parents[1].rglob(nome_arquivo)) + \
                        [Path(nome_arquivo)]
    
    for caminho in caminhos_possiveis:
        if caminho.exists() and caminho.is_file():
            with open(caminho, "rb") as f:
                dados = f.read()
            return f"data:image/png;base64,{base64.b64encode(dados).decode()}"
    return ""

img_aviao_base64 = obter_imagem_base64("azul-air-asia-a330-neo-capa-removebg-preview.png")

# ============================================================
# ESTILOS CSS (Restritos à área principal .main)
# ============================================================

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
            
            /* Regras restritas à área principal para NÃO pintar o menu de preto */
            .main h1, .main h2, .main h3 {{ color: {MARINHO} !important; }}
            .main p, .main label {{ color: {MARINHO}; }}
            
            /* HERO CARD COM ANIMAÇÃO/SOBREPOSIÇÃO DO AVIÃO */
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
            .hero-text {{
                max-width: 65%;
                z-index: 2;
            }}
            .hero-label {{
                color: #BBD4F5; font-size: 12px; font-weight: 700;
                text-transform: uppercase; letter-spacing: 2px; margin-bottom: 7px;
            }}
            .hero h1 {{ color: white !important; font-size: 32px; margin: 0 0 8px 0; }}
            .hero p {{ color: #E4ECF7 !important; font-size: 14px; margin: 0; }}
            
            .hero-img-container {{
                position: absolute;
                right: -15px;
                top: 50%;
                transform: translateY(-50%);
                z-index: 3;
                pointer-events: none;
            }}
            .hero-img-container img {{
                width: 550px;
                height: auto;
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
            .context {{
                background: white; border: 1px solid #E0E7F0; border-radius: 12px;
                padding: 13px 15px; color: #63748A; font-size: 12px;
            }}
            .chart-legend-tag {{
                font-size: 12px;
                color: #68778B;
                background: #E8EDF4;
                padding: 4px 10px;
                border-radius: 6px;
                display: inline-block;
                margin-top: 6px;
                margin-bottom: 12px;
                font-weight: 600;
            }}
            .footer {{ text-align: center; color: #75849A; font-size: 12px; padding-top: 22px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# FUNÇÃO DE NAVEGAÇÃO
# ============================================================

def ir_para_pagina(nome_pagina):
    st.session_state["pagina"] = nome_pagina
    st.rerun()

# ============================================================
# RENDERIZAÇÃO DA PÁGINA
# ============================================================

def render_tela1():
    aplicar_estilos()

    # CABEÇALHO
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-text">
                <div class="hero-label">Análise Corporativa & ESG • Azul S.A.</div>
                <h1>Visão geral da empresa</h1>
                <p>Um resumo rápido do desempenho financeiro, estrutura patrimonial e compromissos com Meio Ambiente, Social e Governança (ESG).</p>
            </div>
            {"<div class='hero-img-container'><img src='" + img_aviao_base64 + "' alt='Avião Azul'></div>" if img_aviao_base64 else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CARREGAMENTO DOS DADOS
    try:
        dados = carregar_dados()
        resultado_preparacao = preparar_visao_geral(dados)
        
        if isinstance(resultado_preparacao, tuple):
            df, df_esg = resultado_preparacao
        else:
            df = resultado_preparacao
            df_esg = dados[2]

        # Garantia de padronização da coluna de ano em df_esg
        if df_esg is not None and not df_esg.empty:
            df_esg = df_esg.rename(columns={c: "ano" for c in df_esg.columns if c.lower() == "ano"})

    except Exception as erro:
        st.error(f"Não foi possível montar a visão geral: {erro}")
        st.info(
            "Confira se as bases tratadas de Balanço, DRE e ESG estão na pasta 'Projeto_Azul/data/tratados'."
        )
        st.stop()

    if df.empty:
        st.warning("Não há dados suficientes para exibir a visão geral.")
        st.stop()

    atual = df.sort_values("Ano").iloc[-1]

    # INDICADORES EXECUTIVOS
    st.markdown('<div class="section-label">Resumo executivo</div>', unsafe_allow_html=True)
    st.markdown("## A saúde financeira em poucos segundos")
    st.markdown(
        '<div class="section-description">Os cartões mostram o dado mais recente disponível. '
        'Use os links para investigar cada resultado nas telas analíticas.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        alav = atual.get("Dívida Líquida / EBITDA")
        diff_meta = alav - 1.5 if pd.notna(alav) else None
        st.metric(
            "Dívida Líquida / EBITDA",
            f"{formatar_numero(alav)}x" if pd.notna(alav) else "N/A",
            delta=f"Meta: até 1,5x | {formatar_numero(diff_meta)}x da meta" if pd.notna(alav) else "Meta: até 1,5x",
            delta_color="inverse" if pd.notna(alav) and alav > 1.5 else "normal",
            help="Quanto maior o múltiplo, maior a dívida líquida em relação ao EBITDA. A referência usada neste painel é 1,5x.",
        )
        st.button(
            "Investigar alavancagem →", 
            key="ir_tela2", 
            use_container_width=True,
            on_click=ir_para_pagina,
            args=("Endividamento",)
        )

    with c2:
        patrimonio = atual.get("Valor patrimonial contábil", atual.get("Patrimônio Líquido", None))
        st.metric(
            "Valor patrimonial contábil",
            formatar_moeda(patrimonio) if pd.notna(patrimonio) else "N/A",
            delta="PL Positivo" if pd.notna(patrimonio) and patrimonio > 0 else ("Passivo a descoberto" if pd.notna(patrimonio) and patrimonio < 0 else "N/A"),
            delta_color="normal" if pd.notna(patrimonio) and patrimonio > 0 else "inverse",
            help="Patrimônio Líquido contábil extraído do Balanço Patrimonial (Ativo total menos Passivo total).",
        )
        st.button(
            "Investigar balanço →", 
            key="ir_tela4_pl", 
            use_container_width=True,
            on_click=ir_para_pagina,
            args=("Caixa e patrimônio",)
        )

    with c3:
        receita = atual.get("Receita Líquida")
        st.metric(
            "Receita líquida",
            formatar_moeda(receita) if pd.notna(receita) else "N/A",
            help="Receita líquida do último ano disponível na DRE, em R$ milhões.",
        )
        st.button(
            "Investigar receita →", 
            key="ir_receita", 
            use_container_width=True,
            on_click=ir_para_pagina,
            args=("Rentabilidade",)
        )

    with c4:
        lucro = atual.get("Lucro / Prejuízo")
        st.metric(
            "Lucro / prejuízo",
            formatar_moeda(lucro) if pd.notna(lucro) else "N/A",
            delta="Lucro" if pd.notna(lucro) and lucro > 0 else ("Prejuízo" if pd.notna(lucro) and lucro < 0 else "Resultado zero / indisponível"),
            delta_color="normal" if pd.notna(lucro) and lucro > 0 else "inverse",
            help="Resultado líquido do período. Valor negativo indica prejuízo.",
        )
        st.button(
            "Investigar resultado →", 
            key="ir_lucro", 
            use_container_width=True,
            on_click=ir_para_pagina,
            args=("Rentabilidade",)
        )

    st.divider()

    # ============================================================
    # GRÁFICOS ESG
    # ============================================================
    st.markdown('<div class="section-label">Panorama ESG & Sustentabilidade</div>', unsafe_allow_html=True)
    st.markdown("## Compromisso com o Meio Ambiente, Social e Governança")
    st.markdown(
        '<div class="section-description">Acompanhe a eficiência no consumo de combustível (E) '
        'e a evolução da diversidade na liderança e governança (S & G).</div>',
        unsafe_allow_html=True,
    )

    # 1. Linha de Títulos e Subtítulos (Alinhamento do cabeçalho)
    c_title1, c_title2 = st.columns(2, gap="large")
    
    with c_title1:
        st.markdown("### Eficiência de Combustível (Ambiental)")
        st.caption("Consumo de combustível por ASK (Assento-Quilômetro Oferecido)")
        
    with c_title2:
        st.markdown("### Diversidade & Governança (Social e Governança)")
        st.caption("Participação de mulheres na gestão e independência do conselho")

    # 2. Linha dos Gráficos (Alinhados perfeitamente no topo)
    g1, g2 = st.columns(2, gap="large")

    with g1:
        st.plotly_chart(
            grafico_esg_eficiencia_combustivel(df_esg), 
            use_container_width=True, 
            key="grafico_esg_combustivel"
        )
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Consolidação Anual (2021-2025)</div>', unsafe_allow_html=True)

    with g2:
        st.plotly_chart(
            grafico_esg_diversidade_governanca(df_esg), 
            use_container_width=True, 
            key="grafico_esg_diversidade"
        )
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Consolidação Anual (2021-2025)</div>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div class="context">
            <b>Como ler o painel:</b>
            Os cartões executivos acompanham a alavancagem financeira (calculada com dados trimestrais consolidando o 4T), o Valor patrimonial contábil (PL), a DRE e a rentabilidade.
            Nos gráficos ESG, o pilar ambiental destaca a intensidade do consumo de combustível por ASK (quanto menor, mais eficiente).
            Os pilares de Social e Governança acompanham as metas de inclusão feminina em cargos de liderança e a independência do Conselho de Administração.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ano_esg = "ano" if "ano" in df_esg.columns else df_esg.columns[0]

    with st.expander("Consultar os dados usados nesta tela"):
        tab1, tab2 = st.tabs(["Indicadores Financeiros", "Indicadores ESG"])
        with tab1:
            st.dataframe(df.sort_values("Ano", ascending=False), use_container_width=True, hide_index=True)
        with tab2:
            st.dataframe(df_esg.sort_values(col_ano_esg, ascending=False), use_container_width=True, hide_index=True)

        st.download_button(
            "Baixar dados da visão geral (CSV)",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="visao_geral_azul.csv",
            mime="text/csv",
        )

    st.markdown(
        '<div class="footer">Azul S.A. • Dashboard de análise financeira & ESG</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    render_tela1()