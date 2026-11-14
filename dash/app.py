import base64
import os
import streamlit as st

import tela1, tela2, tela3, tela4, tela5, tela6

st.set_page_config(
    page_title="Dashboard Financeiro | Azul",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        /* Força a cor branca para a seta do menu lateral em todas as versões do Streamlit */
        [data-testid="stSidebarCollapseButton"] *,
        [data-testid="stSidebarCollapseButton"] button *,
        [data-testid="stSidebarHeader"] button * {
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
            stroke: #FFFFFF !important;
        }
        
        /* Ajusta o fundo e a opacidade do botão para não ofuscar o ícone */
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarHeader"] button {
            color: #FFFFFF !important;
            background-color: transparent !important;
        }

        /* Efeito visual ao passar o rato por cima */
        [data-testid="stSidebarCollapseButton"] button:hover,
        [data-testid="stSidebarHeader"] button:hover {
            background-color: rgba(255, 255, 255, 0.2) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Imagem de fundo da barra lateral
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def _find_sidebar_image():
    if not os.path.isdir(ASSETS_DIR):
        return None
    imgs = sorted(
        f for f in os.listdir(ASSETS_DIR)
        if f.lower().endswith((".svg", ".jpg", ".jpeg", ".png", ".webp"))
    )
    if not imgs:
        return None
    preferidas = [f for f in imgs if f.lower().startswith("sidebar")]
    return os.path.join(ASSETS_DIR, (preferidas or imgs)[0])

SIDEBAR_IMG = _find_sidebar_image()

@st.cache_data(show_spinner=False)
def img_to_base64(path: str, max_width: int = 700):
    from io import BytesIO
    from PIL import Image

    if path.lower().endswith(".svg"):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode(), "svg+xml"

    img = Image.open(path)
    if img.width > max_width:
        new_h = int(img.height * max_width / img.width)
        img = img.resize((max_width, new_h), Image.LANCZOS)

    buf = BytesIO()
    if path.lower().endswith(".png"):
        img.save(buf, format="PNG", optimize=True)
        mime = "png"
    else:
        img.convert("RGB").save(buf, format="JPEG", quality=85)
        mime = "jpeg"
    return base64.b64encode(buf.getvalue()).decode(), mime

SKY_GRADIENT = "linear-gradient(180deg, #0A3D91 0%, #1B64C4 40%, #5BAEF0 75%, #BEE3FA 100%)"
CLOUDS = """
    radial-gradient(ellipse 65% 7% at 22% 90%, rgba(255, 255, 255, 0.55), transparent 70%),
    radial-gradient(ellipse 75% 6% at 78% 82%, rgba(255, 255, 255, 0.40), transparent 70%),
    radial-gradient(ellipse 55% 5% at 30% 72%, rgba(255, 255, 255, 0.25), transparent 70%),
    radial-gradient(ellipse 60% 4% at 80% 60%, rgba(255, 255, 255, 0.15), transparent 70%)
"""

if SIDEBAR_IMG:
    bg_b64, mime = img_to_base64(SIDEBAR_IMG)
    sidebar_background = f"""
        background-color: #1B64C4;
        background-image:
            url("data:image/{mime};base64,{bg_b64}"),
            {CLOUDS},
            {SKY_GRADIENT};
        background-size: 100% auto, 100% 100%, 100% 100%, 100% 100%, 100% 100%, 100% 100%;
        background-position: bottom center, 0 0, 0 0, 0 0, 0 0, 0 0;
        background-repeat: no-repeat;
    """
else:
    sidebar_background = f"""
        background-color: #1B64C4;
        background-image: {CLOUDS}, {SKY_GRADIENT};
        background-size: 100% 100%;
        background-repeat: no-repeat;
    """

# ---------------------------------------------------------------------------
# ESTILOS GLOBAIS (Aplica para o App e para todas as telas importadas)
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    /* Fundo da aplicação */
    [data-testid="stApp"] {{
        background-color: #F1F4F8 !important;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Menu Lateral */
    [data-testid="stSidebar"] {{
        {sidebar_background}
        border-right: none;
    }}

    [data-testid="stSidebar"][aria-expanded="true"] {{
        min-width: 270px;
        max-width: 270px;
    }}

    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        background: transparent !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding: 1.4rem 0.8rem !important;
    }}

    .azul-logo {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 6px 24px 6px !important;
    }}

    .azul-icon {{ color: #FFFFFF; font-size: 34px; line-height: 1; flex-shrink: 0; }}
    .azul-name {{ color: #FFFFFF; font-size: 24px; font-weight: 750; letter-spacing: -0.5px; line-height: 1.1; }}
    .azul-subtitle {{ color: #A9C6F0; font-size: 9px; margin-top: 3px; letter-spacing: 0.8px; }}
    .menu-section {{ color: #A9C6F0; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; margin: 0 0 10px 9px !important; }}

    /* Botões do Menu Lateral */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{ width: 100% !important; }}
    [data-testid="stSidebar"] .stButton {{ width: 100% !important; }}
    [data-testid="stSidebar"] .stButton > button {{
        width: 100% !important;
        height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 0 12px !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        box-sizing: border-box !important;
    }}

    [data-testid="stSidebar"] .stButton > button > div {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        gap: 10px !important;
    }}

    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span {{
        text-align: left !important;
        margin: 0 !important;
        color: inherit !important;
        white-space: normal !important;
        word-break: normal !important;
        line-height: 1.2 !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {{ background: transparent !important; color: #FFFFFF !important; }}
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{ background: rgba(255, 255, 255, 0.15) !important; color: #FFFFFF !important; }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{ background: #FFFFFF !important; color: #0B3A8C !important; font-weight: 600 !important; }}

    /* ---------- ESPAÇAMENTO VERTICAL EQUILIBRADO ---------- */
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }}

    /* Ajuste suave do gap dos blocos de conteúdo */
    div[data-testid="stVerticalBlock"] {{
        gap: 1rem !important;
    }}

    /* Linhas divisórias com respiro moderado */
    hr {{
        margin-top: 1.4rem !important;
        margin-bottom: 1.4rem !important;
    }}

    /* ESTILOS DOS CARDS E HERO */
    .hero {{
        position: relative !important;
        background: linear-gradient(120deg, #102C54 0%, #2457A7 100%) !important;
        padding: 22px 30px !important;
        border-radius: 16px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 5px 18px rgba(16,44,84,.12) !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        overflow: visible !important;
        min-height: 115px !important;
    }}

    .hero-text {{ max-width: 55% !important; z-index: 2 !important; }}
    .hero-label {{
        color: #BBD4F5 !important; font-size: 11px !important; font-weight: 700 !important;
        text-transform: uppercase !important; letter-spacing: 2px !important; margin-bottom: 4px !important;
    }}
    .hero h1 {{ color: #FFFFFF !important; font-size: 26px !important; margin: 0 0 4px 0 !important; }}
    .hero p {{ color: #E4ECF7 !important; font-size: 13.5px !important; margin: 0 !important; }}

    .hero-img-container {{
        position: absolute !important; right: -20px !important; top: 50% !important;
        transform: translateY(-50%) !important; z-index: 3 !important; pointer-events: none !important;
    }}
    .hero-img-container img {{
        width: 450px !important; height: auto !important;
        filter: drop-shadow(0px 10px 15px rgba(0, 0, 0, 0.4)) !important;
    }}

    .section-label {{
        color: #2457A7 !important; font-size: 11px !important; font-weight: 750 !important;
        text-transform: uppercase !important; letter-spacing: 1.5px !important; margin-bottom: 3px !important;
    }}
    .section-description {{ color: #68778B !important; font-size: 13px !important; margin-bottom: 10px !important; }}

    /* Cards de Métricas */
    div[data-testid="stMetric"] {{
        background: #FFFFFF !important; border: 1px solid #E0E7F0 !important; border-radius: 14px !important;
        padding: 14px 16px 12px 16px !important; min-height: 112px !important;
        box-shadow: 0 3px 12px rgba(16,44,84,.04) !important;
    }}
    div[data-testid="stMetricLabel"] {{ color: #63748A !important; font-size: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #102C54 !important; font-size: 22px !important; font-weight: 750 !important; }}

    /* Gráficos Plotly */
    div[data-testid="stPlotlyChart"] {{
        background: #FFFFFF !important; border: 1px solid #E0E7F0 !important; border-radius: 15px !important;
        padding: 6px !important; box-shadow: 0 3px 12px rgba(16,44,84,.035) !important;
    }}

    /* FIX DE COR DO SLIDER PARA AZUL MARINHO */
    div[data-testid="stSlider"],
    div[data-testid="stSlider"] * {{
        --primary-color: #102C54 !important;
        --stSliderTrackColor: #102C54 !important;
    }}

    div[data-testid="stSlider"] [role="slider"] {{
        background-color: #102C54 !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(16, 44, 84, 0.4) !important;
    }}

    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div,
    div[data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"] {{
        background: #102C54 !important;
        background-color: #102C54 !important;
        filter: hue-rotate(190deg) brightness(0.4) saturate(2) !important;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Menu lateral
# ---------------------------------------------------------------------------
PAGINAS = [
    ("Visão executiva", ":material/home:"),
    ("Endividamento", ":material/account_balance:"),
    ("Rentabilidade", ":material/trending_up:"),
    ("Caixa e patrimônio", ":material/account_balance_wallet:"),
    ("Eficiência e criação de valor", ":material/bolt:"),
    ("Projeções e cenários", ":material/query_stats:"),
]

if "pagina" not in st.session_state:
    st.session_state["pagina"] = PAGINAS[0][0]

with st.sidebar:
    st.markdown("""
        <div class="azul-logo">
            <div class="azul-icon">✈</div>
            <div>
                <div class="azul-name">Azul</div>
                <div class="azul-subtitle">ANÁLISE FINANCEIRA</div>
            </div>
        </div>
        <div class="menu-section">NAVEGAÇÃO</div>
    """, unsafe_allow_html=True)

    for nome, icone in PAGINAS:
        ativo = st.session_state["pagina"] == nome
        if st.button(
            nome,
            icon=icone,
            key=f"nav_{nome}",
            type="primary" if ativo else "secondary",
            use_container_width=True,
        ):
            st.session_state["pagina"] = nome
            st.rerun()

selected = st.session_state["pagina"]

# Roteamento
if selected == "Visão executiva":
    tela1.render_tela1()

elif selected == "Endividamento":
    tela2.render_tela2()

elif selected == "Rentabilidade":
    tela3.render_tela3()

elif selected == "Caixa e patrimônio":
    tela4.render_tela4()

elif selected == "Eficiência e criação de valor":
    tela5.render_tela5()

elif selected == "Projeções e cenários":
    tela6.render_tela6()