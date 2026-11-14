
import base64
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

# Importamos a função de carga e consolidação da Tela 1 que já funciona no projeto
from funcoes_tela1 import carregar_dados as carregar_dados_tela1, preparar_visao_geral

from funcoes_tela6 import (
    META_ALAVANCAGEM,
    taxa_crescimento_historico,
    projetar_cenarios,
    grafico_alavancagem,
    grafico_receita_ebitda,
    formatar_moeda_milhoes,
    formatar_percentual,
)

# ==========================================
# PALETA VISUAL & CONSTANTES
# ==========================================

MARINHO = "#102C54"
AZUL = "#2457A7"
TURQUESA = "#29A6A1"
DOURADO = "#E5A544"
FUNDO = "#F1F4F8"
VERDE = "#23856D"
VERMELHO = "#C94C4C"

# ==========================================
# ESTILOS CSS (Scoped à área principal)
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
            
            .main h1, .main h2, .main h3 {{ color: {MARINHO} !important; letter-spacing: -0.4px; }}
            .main p, .main label {{ color: {MARINHO}; }}

            /* 2. Cabeçalho/Hero com altura (largura vertical) reduzida */
            .hero {{
                position: relative;
                background: linear-gradient(120deg, {MARINHO} 0%, {AZUL} 100%);
                padding: 20px 32px !important;
                min-height: 120px !important;
                border-radius: 16px;
                margin-bottom: 24px;
                box-shadow: 0 5px 18px rgba(16,44,84,.12);
                display: flex;
                justify-content: space-between;
                align-items: center;
                overflow: visible !important;
            }}
            .hero-text {{ max-width: 60%; z-index: 2; }}
            .hero-label {{
                color: #BBD4F5; font-size: 11px; font-weight: 700;
                text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px;
            }}
            .hero h1 {{ color: white !important; font-size: 26px !important; margin: 0 0 4px 0 !important; }}
            .hero p {{ color: #E4ECF7 !important; font-size: 13px !important; margin: 0 !important; }}
            
            .hero-img-container {{
                position: absolute; right: -25px; top: 50%;
                transform: translateY(-50%); z-index: 3; pointer-events: none;
            }}
            .hero-img-container img {{
                width: 460px !important; height: auto;
                filter: drop-shadow(0px 10px 15px rgba(0, 0, 0, 0.4));
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

            /* 1. Customização estrita para os Sliders (Forçando Marinho) */
            div[data-testid="stSlider"] div[role="slider"] {{
                background-color: {MARINHO} !important;
                border: 2px solid #FFFFFF !important;
                box-shadow: 0 2px 6px rgba(16,44,84,0.4) !important;
            }}
            div[data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"] {{
                background: {MARINHO} !important;
            }}
            div[data-testid="stSlider"] label,
            div[data-testid="stSlider"] p,
            div[data-testid="stSlider"] span {{
                color: {MARINHO} !important;
                font-weight: 600 !important;
            }}

            .chart-legend-tag {{
                font-size: 12px; color: #68778B; background: #E8EDF4;
                padding: 4px 10px; border-radius: 6px; display: inline-block;
                margin-top: 6px; margin-bottom: 12px; font-weight: 600;
            }}

            .caixa-insight {{
                background: white; border-left: 4px solid {AZUL}; border-radius: 10px;
                padding: 14px 16px; color: #485668; font-size: 13px; margin-bottom: 10px;
                box-shadow: 0 2px 8px rgba(16,44,84,.03);
            }}

            .footer {{ text-align: center; color: #75849A; font-size: 12px; padding-top: 22px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# CONVERSÃO DE IMAGEM EM BASE64
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
                <div class="hero-label">Projeções & Modelagem • Azul S.A.</div>
                <h1>Cenários de Desalavancagem e Longo Prazo</h1>
                <p>Simulação e análise exploratória de cenários financeiros (2026–2029) com foco na meta de desalavancagem corporativa.</p>
            </div>
            {"<div class='hero-img-container'><img src='" + img_aviao_base64 + "' alt='Avião Azul'></div>" if img_aviao_base64 else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================

def render_tela6():
    aplicar_estilos()
    exibir_cabecalho()

    # Carregamento dos dados usando a mesma estrutura garantida na Tela 1
    try:
        dados_raw = carregar_dados_tela1()
        resultado = preparar_visao_geral(dados_raw)
        
        df = resultado[0] if isinstance(resultado, tuple) else resultado

        col_ano = [c for c in df.columns if c.lower() == "ano"][0]
        col_rec = [c for c in df.columns if "receita" in c.lower()][0]
        col_ebi = [c for c in df.columns if "ebitda" in c.lower()][0]
        col_luc = [c for c in df.columns if any(p in c.lower() for p in ["lucro", "prejuizo"])][0]

        df_sorted = df.sort_values(col_ano).copy()
        
        dados = pd.DataFrame(index=df_sorted[col_ano].astype(int))
        dados.index.name = "Ano"

        dados["Receita líquida (R$ mi)"] = df_sorted[col_rec].values
        dados["EBITDA (R$ mi)"] = df_sorted[col_ebi].values
        dados["Lucro/prejuízo (R$ mi)"] = df_sorted[col_luc].values
        
        col_div = [c for c in df.columns if "dívida líquida" in c.lower() or "divida liquida" in c.lower()]
        col_alav = [c for c in df.columns if "alavancagem" in c.lower() or "/" in c.lower()]

        if col_div:
            dados["Dívida líquida aproximada (R$ mi)"] = df_sorted[col_div[0]].values
        elif col_alav:
            dados["Dívida líquida aproximada (R$ mi)"] = dados["EBITDA (R$ mi)"] * df_sorted[col_alav[0]].values
        else:
            dados["Dívida líquida aproximada (R$ mi)"] = dados["EBITDA (R$ mi)"] * 2.5

        if dados["Receita líquida (R$ mi)"].abs().max() > 100000:
            dados = dados / 1000.0

    except Exception as erro:
        st.error(f"Erro ao carregar os dados financeiros para a Tela 6: {erro}")
        st.stop()

    if dados.empty or dados[["Receita líquida (R$ mi)", "EBITDA (R$ mi)"]].dropna(how="all").empty:
        st.warning("Não há dados históricos suficientes para gerar as projeções de cenários.")
        st.stop()

    tx_rec_hist = taxa_crescimento_historico(dados["Receita líquida (R$ mi)"])
    tx_ebi_hist = taxa_crescimento_historico(dados["EBITDA (R$ mi)"])

    # Painel de Premissas e Controles de Simulação
    st.markdown('<div class="section-label">Configuração de Premissas</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Parâmetros de Simulação de Cenários (2026–2029)</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Ajuste as taxas anuais de crescimento projetado para simular o comportamento do resultado e da alavancagem.</div>',
        unsafe_allow_html=True,
    )

    col_p1, col_p2, col_p3, col_p4 = st.columns(4, gap="medium")

    with col_p1:
        crescimento_receita_pct = st.slider(
            "Crescimento anual da receita",
            min_value=-10,
            max_value=35,
            value=8,
            step=1,
            format="%d%%",
            help="Taxa anual de crescimento da Receita Líquida no Cenário-Base.",
        )
        crescimento_receita = crescimento_receita_pct / 100.0

    with col_p2:
        crescimento_ebitda_pct = st.slider(
            "Crescimento anual do EBITDA",
            min_value=-10,
            max_value=35,
            value=10,
            step=1,
            format="%d%%",
            help="Taxa anual de crescimento do EBITDA no Cenário-Base.",
        )
        crescimento_ebitda = crescimento_ebitda_pct / 100.0

    with col_p3:
        crescimento_divida_pct = st.slider(
            "Crescimento anual da dívida",
            min_value=-10,
            max_value=35,
            value=0,
            step=1,
            format="%d%%",
            help="Taxa anual de variação da Dívida Líquida no Cenário-Base.",
        )
        crescimento_divida = crescimento_divida_pct / 100.0

    with col_p4:
        amplitude_pct = st.slider(
            "Sensibilidade dos cenários (±)",
            min_value=1,
            max_value=15,
            value=5,
            step=1,
            format="%d%%",
            help="Otimista: soma a taxa na receita/EBITDA e subtrai na dívida; Pessimista faz o inverso.",
        )
        amplitude = amplitude_pct / 100.0

    # Cálculo dos Cenários Projetados
    try:
        projecoes = projetar_cenarios(
            dados,
            anos_futuros=range(2026, 2030),
            crescimento_receita=crescimento_receita,
            crescimento_ebitda=crescimento_ebitda,
            crescimento_divida=crescimento_divida,
            amplitude=amplitude,
        )
    except Exception as erro:
        st.error(f"Não foi possível calcular os cenários: {erro}")
        st.stop()

    ultimo_ano = int(dados.dropna(how="all").index.max())
    ultimo = dados.loc[ultimo_ano]
    base_2029 = projecoes[(projecoes["Ano"] == 2029) & (projecoes["Cenário"] == "Base")].iloc[0]
    otimista_2029 = projecoes[(projecoes["Ano"] == 2029) & (projecoes["Cenário"] == "Otimista")].iloc[0]
    pessimista_2029 = projecoes[(projecoes["Ano"] == 2029) & (projecoes["Cenário"] == "Pessimista")].iloc[0]

    st.divider()

    # Resumo Executivo das Projeções para 2029
    st.markdown('<div class="section-label">Visão Geral</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Resumo Projetado (Cenário-Base 2029)</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Estimativa dos principais indicadores corporativos no encerramento do ciclo de projeção.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        val_alav = base_2029["Dívida Líquida / EBITDA (x)"]
        st.metric(
            "Alavancagem (2029)",
            "Indisponível" if pd.isna(val_alav) else f"{val_alav:.2f}x".replace(".", ","),
            delta="Dentro da Meta (≤1,5x)" if pd.notna(val_alav) and val_alav <= 1.5 else "Acima da Meta",
            delta_color="normal" if pd.notna(val_alav) and val_alav <= 1.5 else "inverse",
            help="Alavancagem projetada no cenário-base para 2029.",
        )

    with c2:
        st.metric(
            "EBITDA Projetado",
            formatar_moeda_milhoes(base_2029["EBITDA (R$ mi)"]),
            help="Geração de caixa operacional estimada no cenário-base para 2029.",
        )

    with c3:
        st.metric(
            "Receita Líquida Projetada",
            formatar_moeda_milhoes(base_2029["Receita líquida (R$ mi)"]),
            help="Faturamento líquido estimado no cenário-base para 2029.",
        )

    with c4:
        st.metric(
            "Dívida Líquida Projetada",
            formatar_moeda_milhoes(base_2029["Dívida líquida aproximada (R$ mi)"]),
            help="Dívida líquida estimada no cenário-base para 2029.",
        )

    st.divider()

    # Seção 01: Trajetória da Alavancagem
    st.markdown('<div class="section-label">01 • Desalavancagem</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Trajetória da Alavancagem Financeira (Dívida Líquida / EBITDA)</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Acompanhamento do indicador de solvência em relação à meta corporativa de 1,5x.</div>',
        unsafe_allow_html=True,
    )

    col_graf, col_info = st.columns([2, 1], gap="large")

    with col_graf:
        st.plotly_chart(grafico_alavancagem(dados, projecoes), use_container_width=True)
        st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Projeções baseadas no Balanço e DRE (2021–2025)</div>', unsafe_allow_html=True)

    with col_info:
        st.markdown("<h3 style='font-size:16px; margin-top:0;'>Cenários para 2029</h3>", unsafe_allow_html=True)
        for nome, linha, cor in [
            ("Otimista", otimista_2029, VERDE),
            ("Base", base_2029, TURQUESA),
            ("Pessimista", pessimista_2029, VERMELHO),
        ]:
            valor = linha["Dívida Líquida / EBITDA (x)"]
            st.markdown(
                f"<div style='background:#fff; border-left:4px solid {cor}; padding:12px 16px; border-radius:10px; margin-bottom:10px; box-shadow: 0 2px 8px rgba(16,44,84,.04);'>"
                f"<span style='font-size:12px; color:#68778B; font-weight:600;'>Cenário {nome}</span><br>"
                f"<span style='font-size:22px; color:{cor}; font-weight:750;'>"
                f"{'Indisponível' if pd.isna(valor) else f'{valor:.2f}x'.replace('.', ',')}</span></div>",
                unsafe_allow_html=True,
            )

        if pd.notna(base_2029["Dívida Líquida / EBITDA (x)"]):
            if base_2029["Dívida Líquida / EBITDA (x)"] <= 1.5:
                st.success("No Cenário-Base, a alavancagem atinge a meta (≤1,5x) até 2029.")
            else:
                st.warning("No Cenário-Base, a projeção ultrapassa o limite de 1,5x. Avalie premissas mais conservadoras de dívida ou maior crescimento do EBITDA.")

    st.divider()

    # Seção 02: Evolução de Receita e EBITDA
    st.markdown('<div class="section-label">02 • Resultado Operacional</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Evolução Projetada da Receita e EBITDA</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Comparativo entre a expansão do faturamento e a geração de caixa operacional nos 3 cenários.</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(grafico_receita_ebitda(dados, projecoes), use_container_width=True)
    st.markdown('<div class="chart-legend-tag">📅 Fonte dos dados: Projeções baseadas na DRE Anual</div>', unsafe_allow_html=True)

    st.divider()

    # Seção 03: Insights Diagnósticos e Metodologia
    st.markdown('<div class="section-label">03 • Diagnóstico Executivo</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Insights e Considerações Metodológicas</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Síntese dos principais pontos de atenção para análise de decisões estratégicas.</div>',
        unsafe_allow_html=True,
    )

    insights = []
    if pd.notna(base_2029["Dívida Líquida / EBITDA (x)"]):
        valor = base_2029["Dívida Líquida / EBITDA (x)"]
        if valor > 1.5:
            insights.append(
                "<b>Meta de desalavancagem:</b> O Cenário-Base permanece acima da meta de 1,5x em 2029. "
                "Investigue quais premissas de expansão operacional do EBITDA ou amortização extraordinária de dívida são necessárias para atingir a meta."
            )
        else:
            insights.append(
                "<b>Meta de desalavancagem:</b> O Cenário-Base alcança a meta projetada (≤1,5x em 2029). "
                "Recomenda-se monitorar a sustentabilidade da margem EBITDA a cada trimestre."
            )

    if pd.notna(ultimo.get("EBITDA (R$ mi)")) and pd.notna(ultimo.get("Receita líquida (R$ mi)")) and ultimo["Receita líquida (R$ mi)"] != 0:
        margem_atual = (ultimo["EBITDA (R$ mi)"] / ultimo["Receita líquida (R$ mi)"]) * 100
        margem_proj = (base_2029["EBITDA (R$ mi)"] / base_2029["Receita líquida (R$ mi)"]) * 100 if base_2029["Receita líquida (R$ mi)"] else float("nan")
        if pd.notna(margem_proj):
            direcao = "aumenta" if margem_proj > margem_atual else ("diminui" if margem_proj < margem_atual else "permanece estável")
            insights.append(
                f"<b>Margem EBITDA:</b> Com base nas taxas selecionadas, a margem EBITDA {direcao} de "
                f"{formatar_percentual(margem_atual, 1)} para {formatar_percentual(margem_proj, 1)}. "
                f"Confira a coerência das premissas de custos operacionais com o cenário do setor aéreo."
            )

    for insight in insights:
        st.markdown(f"<div class='caixa-insight'>{insight}</div>", unsafe_allow_html=True)

    st.markdown("<h4 style='margin-top:15px;'>Nota Metodológica & Limitações</h4>", unsafe_allow_html=True)
    st.info(
        "Os cenários são projeções compostas a partir das taxas definidas nos controles interativos. "
        "O Cenário Otimista eleva o crescimento da Receita e do EBITDA e reduz a taxa de expansão da dívida; o Pessimista aplica o efeito inverso. "
        "A Dívida Líquida foi aproximada por (Empréstimos + Financiamentos + Arrendamentos − Caixa e Equivalentes). "
        "Este modelo é um instrumento exploratório e não incorpora variações cambiais, juros, refinanciamentos ou eventos extraordinários."
    )

    # 3. Tabela Expansível reposicionada para o final, sem linha divisória abaixo
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    with st.expander("Consultar tabela completa de dados históricos e projeções"):
        historico_tabela = dados.reset_index().copy()
        historico_tabela["Tipo"] = "Histórico"
        proj_tabela = projecoes.copy()
        proj_tabela["Tipo"] = "Projeção"
        
        colunas_tabela = [
            "Ano", "Tipo", "Receita líquida (R$ mi)", "EBITDA (R$ mi)",
            "Dívida líquida aproximada (R$ mi)", "Dívida Líquida / EBITDA (x)"
        ]
        
        historico_tabela["Dívida Líquida / EBITDA (x)"] = (
            historico_tabela["Dívida líquida aproximada (R$ mi)"] /
            historico_tabela["EBITDA (R$ mi)"].replace(0, np.nan)
        )
        
        tabela_consolidada = pd.concat(
            [historico_tabela.reindex(columns=colunas_tabela), proj_tabela.reindex(columns=colunas_tabela)], 
            ignore_index=True
        )
        
        st.dataframe(tabela_consolidada, use_container_width=True, hide_index=True)
        
        st.download_button(
            "Baixar dados projetados (CSV)",
            data=tabela_consolidada.to_csv(index=False).encode("utf-8-sig"),
            file_name="projecoes_azul_2026_2029.csv",
            mime="text/csv",
        )

    st.markdown(
        '<div class="footer">Azul S.A. • Dashboard de análise financeira & projeções de longo prazo</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    st.set_page_config(
        page_title="Projeções & Cenários | Azul",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    render_tela6()