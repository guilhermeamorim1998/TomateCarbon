import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import io
from datetime import datetime
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🍅 TomateCarbon",
    page_icon="🍅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
# NOVA ESTRUTURA DE PÁGINAS (sugestão 7)
# 0=Intro | 1=Identificação | 2=Ciclo | 3=Correção Solo
# 4=Adub.Plantio | 5=Adub.Cobertura | 6=Defensivos
# 7=Operações | 8=Irrigação | 9=Produtividade | 10=Resultados
# ══════════════════════════════════════════════════════════════
PAGES = [
    "Apresentação",         # 0
    "Identificação",        # 1
    "Ciclo de Cultivo",     # 2
    "Correção de Solo",     # 3
    "Adubação de Plantio",  # 4
    "Adubação de Cobertura",# 5
    "Defensivos Agrícolas", # 6
    "Operações Mecanizadas",# 7
    "Irrigação & Energia",  # 8
    "Produtividade",        # 9
    "Resultados",           # 10
]
TOTAL_STEPS = len(PAGES) - 1  # 10 etapas (0 é intro)

# ══════════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO SESSION STATE (sugestão 6)
# ══════════════════════════════════════════════════════════════
def init_session_state():
    defaults = {
        "page": 0,
        # Identificação
        "prod_name": "", "farm_name": "", "email": "", "phone": "",
        "car": "", "region": "", "city": "", "state": "",
        "area_tom": 0.0, "area_farm": 0.0, "year_ref": 2025,
        # Ciclo de cultivo
        "tipo_cultivo": "Campo aberto",
        "data_plantio": "", "espacamento_linha": 1.0,
        "espacamento_planta": 0.5, "num_plantas": 20000,
        # Correção de solo
        "calc_calcitico": 0.0, "calc_dolomitico": 0.0,
        "gesso": 0.0,
        "fosfato_rocha": 0.0, "sfs_corr": 0.0, "sft_corr": 0.0,
        "kcl_corr": 0.0, "po_rocha_k": 0.0,
        # Adubação de plantio — sintéticos
        "ureia_p": 0.0, "map_p": 0.0, "npk4148_p": 0.0,
        "npk43016_p": 0.0, "nitcalc_p": 0.0, "nitpot_p": 0.0,
        "sfs_p": 0.0, "sft_p": 0.0, "kcl_p": 0.0,
        "sufmg_p": 0.0, "sufzn_p": 0.0, "borax_p": 0.0,
        # Adubação de plantio — orgânicos
        "est_bov_p": 0.0, "est_fra_p": 0.0, "est_sui_p": 0.0,
        "bokashi_p": 0.0, "composto_p": 0.0,
        # Adubação de cobertura
        "ureia_c": 0.0, "map_c": 0.0, "nitcalc_c": 0.0,
        "nitpot_c": 0.0, "npk2020_c": 0.0, "kcl_c": 0.0,
        "sufmg_c": 0.0, "sufzn_c": 0.0, "borax_c": 0.0,
        # Defensivos
        "herb_trator": 0.0, "herb_triciclo": 0.0, "herb_manual": 0.0,
        "inset_trator": 0.0, "inset_triciclo": 0.0, "inset_manual": 0.0,
        # Operações mecanizadas
        "op_preparo": 0.0, "op_adub_plantio": 0.0,
        "op_adub_cobertura": 0.0, "op_plantio_mudas": 0.0,
        "op_herbicida": 0.0, "op_inset_fungi": 0.0,
        "op_irrigacao": 0.0, "op_colheita": 0.0, "op_outras": 0.0,
        "perc_bio": 0,
        # Irrigação
        "irri_yn": "Não", "tipo_irri": "Gotejamento",
        "tipo_ger": "Elétrica", "irri_useref": False,
        "irri_diesel": 0.0, "irri_hd": 0.0,
        "irri_ma": 0, "irri_cv": 1.0,
        "usa_solar": False, "qtd_bat": 0.0,
        "em_irri": 0.0,
        # Produtividade
        "produtividade": 0.0, "ciclos_ano": 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()


def go(p: int):
    st.session_state.page = p
    st.rerun()

def next_page():
    st.session_state.page += 1
    st.rerun()

def prev_page():
    st.session_state.page -= 1
    st.rerun()

# ══════════════════════════════════════════════════════════════
# FATORES DE EMISSÃO (kg CO₂eq / kg produto)
# ══════════════════════════════════════════════════════════════
EF = {
    # Correção de solo
    "calc_calcitico":  0.12,   # IPCC Tier 1
    "calc_dolomitico": 0.13,   # IPCC Tier 1
    "gesso":           0.023,  # CaSO₄ — baixa emissão
    "fosfato_rocha":   0.10,   # literatura
    "sfs_corr":        0.51,   # IPCC
    "sft_corr":        0.58,   # IPCC
    "kcl_corr":        0.39,   # IPCC
    "po_rocha_k":      0.06,   # literatura
    # Adubação plantio — sintéticos
    "ureia_p":         1.57,   # IPCC/Brentrup
    "map_p":           1.09,   # IFA/LCA
    "npk4148_p":       0.48,   # CBAM EU
    "npk43016_p":      0.52,   # estimado
    "nitcalc_p":       1.30,   # literatura
    "nitpot_p":        1.35,   # literatura
    "sfs_p":           0.51,   # IPCC
    "sft_p":           0.58,   # IPCC
    "kcl_p":           0.39,   # IPCC
    "sufmg_p":         0.14,   # ecoinvent
    "sufzn_p":         0.18,   # ecoinvent
    "borax_p":         0.10,   # estimado
    # Adubação plantio — orgânicos
    "est_bov_p":       0.23,   # IPCC
    "est_fra_p":       0.31,   # IPCC
    "est_sui_p":       0.28,   # literatura
    "bokashi_p":       0.15,   # estimado
    "composto_p":      0.10,   # IPCC
    # Adubação cobertura
    "ureia_c":         1.57,
    "map_c":           1.09,
    "nitcalc_c":       1.30,
    "nitpot_c":        1.35,
    "npk2020_c":       0.48,
    "kcl_c":           0.39,
    "sufmg_c":         0.14,
    "sufzn_c":         0.18,
    "borax_c":         0.10,
    # Defensivos — estimativa por litro/kg de produto comercial
    "herb_trator":     2.604,
    "herb_triciclo":   2.213,
    "herb_manual":     0.0,
    "inset_trator":    2.604,
    "inset_triciclo":  2.213,
    "inset_manual":    0.0,
}

# Fator de emissão operações: kg CO₂eq por h/ha (trator 75cv, diesel)
EF_OP_HHA = 16.0  # ~16 kg CO₂eq / h·ha (média literatura)

def calc_emissao(key: str) -> float:
    """Emissão simples: quantidade × fator."""
    qtd = float(st.session_state.get(key, 0.0) or 0.0)
    return qtd * EF.get(key, 0.0)

def calc_operacoes() -> float:
    """Emissão total das operações mecanizadas (h/ha × EF)."""
    keys_op = [
        "op_preparo", "op_adub_plantio", "op_adub_cobertura",
        "op_plantio_mudas", "op_herbicida", "op_inset_fungi",
        "op_irrigacao", "op_colheita", "op_outras",
    ]
    total_h = sum(float(st.session_state.get(k, 0.0) or 0.0) for k in keys_op)
    perc_bio = int(st.session_state.get("perc_bio", 0) or 0)
    fator    = EF_OP_HHA * (1 - perc_bio / 100.0 * 0.85)  # biodiesel reduz 85%
    return total_h * fator

def calc_drone() -> float:
    b = float(st.session_state.get("qtd_bat", 0.0) or 0.0)
    return b * 6.216 * 0.001 * 0.0385

def calc_elec(kwh: float) -> float:
    return kwh * 0.0385

def calc_diesel_l(l: float) -> float:
    return l * 2.604

def fmt(v: float, d: int = 2) -> str:
    if v < 0:
        return f"-{fmt(-v, d)}"
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# ══════════════════════════════════════════════════════════════
# CSS GLOBAL — compacto + visual premium (sugestões 1, 2, 4, 14)
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── SUGESTÃO 2: esconder elementos do Streamlit ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]   { display: none !important; }

/* ── SUGESTÃO 1: layout compacto sem scroll ── */
*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background: #07070a !important;
    color: #e8e8f0 !important;
    font-size: 13px !important;
}

/* SUGESTÃO 14: fundo com gradientes sutis de tomate */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 8%  12%, rgba(220,53,69,0.06) 0%, transparent 40%),
        radial-gradient(circle at 92% 88%, rgba(220,53,69,0.05) 0%, transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(46,125,50,0.03) 0%, transparent 60%),
        radial-gradient(ellipse 80% 40% at 10% 0%,  rgba(198,40,40,0.10) 0%, transparent 55%),
        radial-gradient(ellipse 60% 50% at 90% 100%,rgba(30,100,30,0.06) 0%, transparent 55%),
        #07070a !important;
}

/* Bloco principal compacto */
.block-container {
    max-width: 1100px !important;
    padding: 0.4rem 1.4rem 2rem !important;
    margin: 0 auto !important;
}

/* Reduzir espaços verticais entre widgets */
[data-testid="stVerticalBlock"] { gap: 0.25rem !important; }
[data-testid="stHorizontalBlock"] { gap: 0.6rem !important; align-items: flex-end !important; }

/* Inputs compactos */
input[type="text"], input[type="number"],
input[type="email"], input[type="tel"], textarea {
    color: #111111 !important;
    background: #f8f8f8 !important;
    border: 1.5px solid #e0e0e0 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 4px 8px !important;
    height: 32px !important;
    transition: border-color .2s, box-shadow .2s !important;
    caret-color: #c62828 !important;
}
input:focus, textarea:focus {
    background: #ffffff !important;
    border-color: #c62828 !important;
    box-shadow: 0 0 0 3px rgba(198,40,40,.10) !important;
    outline: none !important;
}
input::placeholder { color: #bbb !important; font-weight: 400 !important; }

/* Labels compactos */
label, [data-testid="stWidgetLabel"] p {
    font-size: 11px !important;
    font-weight: 700 !important;
    color: rgba(255,255,255,.55) !important;
    letter-spacing: .02em !important;
    margin-bottom: 1px !important;
}

/* Number input botões */
[data-testid="stNumberInput"] button {
    background: rgba(198,40,40,.1) !important;
    border-radius: 6px !important;
    color: #ff5252 !important;
    border: none !important;
    height: 28px !important;
    width: 28px !important;
}
[data-testid="stNumberInput"] button:hover {
    background: rgba(198,40,40,.2) !important;
}

/* Select box */
[data-baseweb="select"] > div {
    background: #f8f8f8 !important;
    border: 1.5px solid #e0e0e0 !important;
    border-radius: 8px !important;
    color: #111 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    min-height: 32px !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: #c62828 !important;
    box-shadow: 0 0 0 3px rgba(198,40,40,.10) !important;
}
[data-baseweb="select"] * { color: #111 !important; font-size: 12px !important; }
[data-baseweb="select"] svg { color: #666 !important; fill: #666 !important; }
[data-baseweb="popover"], [data-baseweb="menu"] {
    background: #fff !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 40px rgba(0,0,0,.25) !important;
}
[data-baseweb="option"] { background: #fff !important; color: #111 !important; font-size: 12px !important; }
[data-baseweb="option"]:hover { background: #fff5f5 !important; color: #c62828 !important; }
[data-baseweb="option"][aria-selected="true"] {
    background: #fff5f5 !important; color: #c62828 !important; font-weight: 700 !important;
}

/* Radio / Checkbox */
[data-testid="stRadio"] label { color: rgba(255,255,255,.7) !important; font-size: 12px !important; }
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color: rgba(255,255,255,.7) !important; font-size: 12px !important;
}
[data-testid="stCheckbox"] p { color: rgba(255,255,255,.6) !important; font-size: 12px !important; }
[data-testid="stCheckbox"] span[aria-checked="true"] {
    background: #c62828 !important; border-color: #c62828 !important;
}

/* Slider */
[data-testid="stSlider"] > div > div > div > div {
    background: linear-gradient(90deg, #c62828, #ff5252) !important;
}
[data-testid="stSlider"] [role="slider"] {
    background: #ff5252 !important;
    border: 2px solid #fff !important;
    box-shadow: 0 0 8px rgba(220,53,69,.6) !important;
}

/* st.info / st.success / st.warning */
[data-testid="stInfo"] {
    background: rgba(66,165,245,.08) !important;
    border: 1px solid rgba(66,165,245,.2) !important;
    border-radius: 10px !important;
    color: #90caf9 !important;
    padding: 0.5rem 0.8rem !important;
}
[data-testid="stSuccess"] {
    background: rgba(105,240,174,.07) !important;
    border: 1px solid rgba(105,240,174,.18) !important;
    border-radius: 10px !important;
    color: #69f0ae !important;
    padding: 0.5rem 0.8rem !important;
}
[data-testid="stWarning"] {
    background: rgba(255,152,0,.08) !important;
    border: 1px solid rgba(255,152,0,.22) !important;
    border-radius: 10px !important;
    color: #ffcc80 !important;
    padding: 0.5rem 0.8rem !important;
}

/* Expander compacto */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,.08) !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,.03) !important;
    margin-bottom: 0.4rem !important;
}
[data-testid="stExpander"] summary {
    font-size: 12px !important;
    font-weight: 700 !important;
    color: rgba(255,255,255,.7) !important;
    padding: 0.5rem 0.8rem !important;
}

/* Caption */
[data-testid="stCaptionContainer"] p {
    color: rgba(255,255,255,.28) !important;
    font-size: 11px !important;
    margin-top: 1px !important;
}

/* HR */
hr { border-color: rgba(255,255,255,.06) !important; margin: 0.5rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(220,53,69,.4); border-radius: 99px; }

/* ── SUGESTÃO 4: botões de navegação — SUGESTÃO 4 ── */
/* Botão único / último da linha = vermelho (Próximo / Calcular) */
div[data-testid="column"]:last-child .stButton > button,
div[data-testid="column"]:only-child .stButton > button {
    background: linear-gradient(135deg, #c62828, #b71c1c) !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 20px !important;
    box-shadow: 0 6px 20px rgba(198,40,40,.40),
                inset 0 1px 0 rgba(255,255,255,.15) !important;
    letter-spacing: .03em !important;
    transition: all .25s !important;
    width: 100% !important;
    cursor: pointer !important;
    white-space: nowrap !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(198,40,40,.55) !important;
    background: linear-gradient(135deg, #d32f2f, #c62828) !important;
}

/* Botão esquerdo = cinza (Voltar) */
div[data-testid="column"]:first-child .stButton > button {
    background: rgba(255,255,255,.07) !important;
    color: rgba(255,255,255,.75) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    border: 1.5px solid rgba(255,255,255,.14) !important;
    border-radius: 12px !important;
    padding: 12px 20px !important;
    transition: all .25s !important;
    width: 100% !important;
    cursor: pointer !important;
    white-space: nowrap !important;
}
div[data-testid="column"]:first-child .stButton > button:hover {
    background: rgba(255,255,255,.12) !important;
    color: #fff !important;
    border-color: rgba(255,255,255,.24) !important;
    transform: translateX(-2px) !important;
}

/* Download buttons */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.06)) !important;
    border: 1.5px solid rgba(255,255,255,.16) !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 12px !important;
    transition: all .25s !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(255,255,255,.16) !important;
    border-color: rgba(255,255,255,.28) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,.28) !important;
}

/* ── BARRA DE PROGRESSO TOPO ── */
.prog-wrap {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    height: 3px; background: rgba(255,255,255,.04);
}
.prog-fill {
    height: 100%;
    background: linear-gradient(90deg, #7b0000, #c62828, #ff5252, #ff9800);
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
    transition: width .5s cubic-bezier(.4,0,.2,1);
    border-radius: 0 3px 3px 0;
    box-shadow: 0 0 12px rgba(220,53,69,.65);
}
@keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* ── TOP NAV ── */
.topnav {
    display: flex; align-items: center; justify-content: space-between;
    padding: .9rem 0 .7rem;
    border-bottom: 1px solid rgba(255,255,255,.06);
    margin-bottom: 1rem;
}
.topnav-logo {
    font-size: 1rem; font-weight: 900; letter-spacing: -.02em;
    background: linear-gradient(135deg, #ff5252, #ff9800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.topnav-right  { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.topnav-step   { font-size: .62rem; font-weight: 700; color: rgba(255,255,255,.25);
                 letter-spacing: .12em; text-transform: uppercase; }
.topnav-pname  { font-size: .72rem; font-weight: 600; color: rgba(255,255,255,.38); }

/* ── STEP DOTS ── */
.step-dots {
    display: flex; gap: 5px; align-items: center; justify-content: center;
    margin-bottom: .9rem; flex-wrap: wrap;
}
.dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: rgba(255,255,255,.08);
    transition: all .35s cubic-bezier(.4,0,.2,1);
}
.dot.active {
    width: 24px; border-radius: 99px;
    background: linear-gradient(90deg, #c62828, #ff5252);
    box-shadow: 0 0 10px rgba(220,53,69,.5);
}
.dot.done { background: rgba(220,53,69,.32); }

/* ── PAGE HEADER ── */
.page-eyebrow {
    font-size: .62rem; font-weight: 800; letter-spacing: .16em;
    text-transform: uppercase; color: #ff5252;
    margin-bottom: .3rem; display: flex; align-items: center; gap: 8px;
}
.page-eyebrow::before {
    content: ''; width: 20px; height: 2px;
    background: linear-gradient(90deg, #c62828, #ff5252); border-radius: 99px;
}
.page-title {
    font-size: clamp(1.4rem, 3vw, 2rem); font-weight: 900;
    line-height: 1.08; color: #ffffff;
    margin-bottom: .25rem; letter-spacing: -.025em;
}
.page-desc {
    font-size: .78rem; color: rgba(255,255,255,.32);
    line-height: 1.6; margin-bottom: .8rem; max-width: 620px;
}

/* ── SECTION HEADER ── */
.section-header {
    display: flex; align-items: center; gap: 8px;
    font-size: .62rem; font-weight: 800; letter-spacing: .13em;
    text-transform: uppercase; color: rgba(255,255,255,.28);
    margin: .9rem 0 .5rem; padding-bottom: .4rem;
    border-bottom: 1px solid rgba(255,255,255,.06);
}
.section-header .sh-icon { font-size: 1rem; }

/* ── REF BOX ── */
.ref-box {
    background: rgba(255,152,0,.07); border: 1px solid rgba(255,152,0,.20);
    border-radius: 8px; padding: 6px 12px; font-size: .76rem;
    color: #ffcc80; font-weight: 600; margin: 3px 0 6px;
    display: flex; align-items: center; gap: 6px;
}

/* ── INFO TAG ── */
.info-tag {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(66,165,245,.1); border: 1px solid rgba(66,165,245,.2);
    border-radius: 7px; padding: 4px 12px; font-size: .74rem;
    color: #90caf9; font-weight: 600; margin-top: 4px;
}

/* ── METRIC CARDS ── */
.metric-grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: .7rem; margin-bottom: 1.2rem;
}
@media(max-width:580px) { .metric-grid { grid-template-columns: 1fr; } }
.metric-card {
    background: linear-gradient(150deg, rgba(255,255,255,.055), rgba(255,255,255,.02));
    border: 1px solid rgba(255,255,255,.09); border-radius: 16px;
    padding: 1.1rem 1.1rem; position: relative; overflow: hidden;
    transition: transform .3s, box-shadow .3s;
}
.metric-card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(0,0,0,.38); }
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 16px 16px 0 0;
}
.mc-red::before   { background: linear-gradient(90deg, #7b0000, #c62828, #ff5252); }
.mc-blue::before  { background: linear-gradient(90deg, #0d47a1, #1976d2, #42a5f5); }
.mc-amber::before { background: linear-gradient(90deg, #bf360c, #e64a19, #ffd54f); }
.metric-icon  { font-size: 1.5rem; margin-bottom: .3rem; }
.metric-label {
    font-size: .58rem; font-weight: 800; color: rgba(255,255,255,.28);
    text-transform: uppercase; letter-spacing: .11em; margin-bottom: .2rem;
}
.metric-value {
    font-size: 1.3rem; font-weight: 900; color: #fff;
    line-height: 1; letter-spacing: -.02em;
}
.metric-unit { font-size: .58rem; color: rgba(255,255,255,.22); margin-top: .3rem; font-weight: 500; }

/* ── TABELA EMISSÕES ── */
.em-wrap {
    background: linear-gradient(150deg, rgba(255,255,255,.04), rgba(255,255,255,.015));
    border: 1px solid rgba(255,255,255,.08); border-radius: 16px;
    padding: 1.1rem 1.3rem; margin-top: .8rem; position: relative; overflow: hidden;
}
.em-wrap::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,.10), transparent);
}
.em-title {
    font-size: .62rem; font-weight: 800; letter-spacing: .13em; text-transform: uppercase;
    color: rgba(255,255,255,.26); margin-bottom: .8rem;
    display: flex; align-items: center; gap: 8px;
}
.em-title::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,.05); }
.em-table { width: 100%; border-collapse: collapse; }
.em-table th {
    padding: 6px 10px; font-size: .58rem; font-weight: 800;
    color: rgba(255,255,255,.22); text-transform: uppercase;
    letter-spacing: .09em; border-bottom: 1px solid rgba(255,255,255,.05); text-align: left;
}
.em-table td {
    padding: 8px 10px; font-size: .82rem;
    border-bottom: 1px solid rgba(255,255,255,.03);
    color: rgba(255,255,255,.72); vertical-align: middle;
}
.em-table tr:last-child td { border-bottom: none; }
.em-table tr:hover td { background: rgba(255,255,255,.02); }
.em-val {
    font-weight: 800; color: #ff6b6b !important; text-align: right !important;
    font-variant-numeric: tabular-nums;
}
.em-bar-bg { width: 80px; height: 4px; background: rgba(255,255,255,.06); border-radius: 99px; overflow: hidden; }
.em-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #c62828, #ff5252, #ff8a80); }
.em-pct { font-size: .66rem; color: rgba(255,255,255,.28); text-align: right !important; font-variant-numeric: tabular-nums; }
.em-total-row td {
    border-top: 2px solid rgba(255,255,255,.09) !important;
    font-weight: 900 !important; color: #fff !important; padding-top: 12px !important;
}
.em-total-val { color: #ff5252 !important; font-size: 1rem !important; }

/* ── HERO (página intro) ── */
.hero-wrap  { text-align: center; padding: 2.5rem 0 1.5rem; }
.hero-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: rgba(198,40,40,.1); border: 1px solid rgba(198,40,40,.22);
    border-radius: 999px; padding: 5px 16px;
    font-size: .7rem; font-weight: 700; color: #ff8a80;
    letter-spacing: .05em; margin-bottom: 1.2rem;
}
.hero-icon {
    font-size: 4.5rem; display: block; margin-bottom: .9rem;
    filter: drop-shadow(0 0 40px rgba(220,53,69,.5));
    animation: float 3.5s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform: translateY(0) rotate(-2deg); }
    50%      { transform: translateY(-10px) rotate(2deg); }
}
.hero-title {
    font-size: clamp(2.2rem, 5vw, 3.5rem); font-weight: 900; line-height: 1.05;
    letter-spacing: -.03em;
    background: linear-gradient(135deg, #ffffff 0%, #ffccbc 40%, #ff5252 80%, #c62828 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin-bottom: .6rem;
}
.hero-sub {
    font-size: .95rem; color: rgba(255,255,255,.36);
    max-width: 440px; margin: 0 auto 1.8rem; line-height: 1.75;
}
.hero-chips { display: flex; flex-wrap: wrap; gap: .45rem; justify-content: center; margin-bottom: 2rem; }
.hero-chip {
    padding: 5px 14px; background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08); border-radius: 999px;
    font-size: .7rem; color: rgba(255,255,255,.42); font-weight: 600; letter-spacing: .02em;
}

/* ── INTRO CARDS (limites/premissas) ── */
.intro-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin: .8rem 0 1.2rem;
}
@media(max-width:640px) { .intro-grid { grid-template-columns: 1fr; } }
.intro-card {
    border-radius: 14px; padding: 1rem 1.2rem;
    border: 1px solid; position: relative; overflow: hidden;
}
.intro-card-blue  { background: rgba(66,165,245,.07);  border-color: rgba(66,165,245,.2); }
.intro-card-amber { background: rgba(255,152,0,.07);   border-color: rgba(255,152,0,.2); }
.intro-card h4 { font-size: .72rem; font-weight: 800; letter-spacing: .1em;
                 text-transform: uppercase; margin-bottom: .5rem; }
.intro-card-blue  h4 { color: #90caf9; }
.intro-card-amber h4 { color: #ffcc80; }
.intro-card ul { list-style: none; padding: 0; margin: 0; }
.intro-card li {
    font-size: .78rem; line-height: 1.6; color: rgba(255,255,255,.55);
    padding: .15rem 0; border-bottom: 1px solid rgba(255,255,255,.04);
    display: flex; align-items: flex-start; gap: 6px;
}
.intro-card li:last-child { border-bottom: none; }
.intro-card li::before { content: '▸'; font-size: .65rem; margin-top: .18rem; flex-shrink: 0; }
.intro-card-blue  li::before { color: #42a5f5; }
.intro-card-amber li::before { color: #ffa726; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# GERAÇÃO DE PDF
# ══════════════════════════════════════════════════════════════
def gerar_pdf(dados: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    RED   = colors.HexColor("#c62828")
    GRAY  = colors.HexColor("#555555")
    LGRAY = colors.HexColor("#f5f5f5")
    WHITE = colors.white

    s_title = ParagraphStyle("title", fontSize=20, fontName="Helvetica-Bold",
                              textColor=RED, spaceAfter=4, alignment=TA_LEFT)
    s_sub   = ParagraphStyle("sub",   fontSize=10, fontName="Helvetica",
                              textColor=GRAY, spaceAfter=14, alignment=TA_LEFT)
    s_sec   = ParagraphStyle("sec",   fontSize=9,  fontName="Helvetica-Bold",
                              textColor=RED, spaceBefore=14, spaceAfter=5)
    s_foot  = ParagraphStyle("foot",  fontSize=7,  fontName="Helvetica",
                              textColor=GRAY, alignment=TA_CENTER)

    story = []
    story.append(Paragraph("TomateCarbon", s_title))
    story.append(Paragraph("Relatório de Emissões de Carbono — Lavoura de Tomate", s_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=RED, spaceAfter=10))

    # Identificação
    story.append(Paragraph("IDENTIFICAÇÃO", s_sec))
    info_data = [
        ["Produtor",    dados.get("prod_name","—"),  "Propriedade", dados.get("farm_name","—")],
        ["E-mail",      dados.get("email","—"),       "Telefone",    dados.get("phone","—")],
        ["CAR",         dados.get("car","—"),          "Região",      dados.get("region","—")],
        ["Cidade/UF",
         f"{dados.get('city','—')}/{dados.get('state','—')}",
         "Ano", str(dados.get("year_ref","—"))],
        ["Área Tomate", f"{dados.get('area_tom',0):.2f} ha",
         "Área Total",  f"{dados.get('area_farm',0):.2f} ha"],
    ]
    t_info = Table(info_data, colWidths=[3.2*cm, 6*cm, 3.2*cm, 5.5*cm])
    t_info.setStyle(TableStyle([
        ("FONTNAME",       (0,0),(-1,-1), "Helvetica"),
        ("FONTNAME",       (0,0),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",       (2,0),(2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,-1), 8),
        ("TEXTCOLOR",      (0,0),(0,-1),  GRAY),
        ("TEXTCOLOR",      (2,0),(2,-1),  GRAY),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [WHITE, LGRAY]),
        ("GRID",           (0,0),(-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("LEFTPADDING",    (0,0),(-1,-1), 7),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))

    # Indicadores principais
    story.append(Paragraph("INDICADORES DE EMISSÃO", s_sec))
    ind_data = [
        ["Indicador", "Valor", "Unidade"],
        ["Emissão Total",
         f"{dados.get('em_total',0):.2f}",   "kg CO₂eq ha⁻¹ ano⁻¹"],
        ["Por kg de Tomate",
         f"{dados.get('em_kg',0):.4f}",       "kg CO₂eq kg⁻¹"],
        ["Produtividade",
         f"{dados.get('produtividade',0):.0f}", "kg ha⁻¹"],
        ["Ciclos/ano",
         str(dados.get("ciclos_ano",1)),        "ciclos"],
    ]
    t_ind = Table(ind_data, colWidths=[7*cm, 4*cm, 7*cm])
    t_ind.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  RED),
        ("TEXTCOLOR",      (0,0),(-1,0),  WHITE),
        ("FONTNAME",       (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTNAME",       (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0),(-1,-1), 8.5),
        ("ALIGN",          (1,0),(-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, LGRAY]),
        ("GRID",           (0,0),(-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",     (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 6),
        ("LEFTPADDING",    (0,0),(-1,-1), 9),
    ]))
    story.append(t_ind)
    story.append(Spacer(1, 12))

    # Detalhamento por fonte
    story.append(Paragraph("DETALHAMENTO POR FONTE", s_sec))
    det_data = [["Fonte de Emissão", "kg CO₂eq ha⁻¹ ano⁻¹", "%"]]
    em_total = dados.get("em_total", 0)
    for lbl, val in dados.get("fontes", []):
        pct = (val / em_total * 100) if em_total > 0 else 0
        det_data.append([lbl, f"{val:.2f}", f"{pct:.1f}%"])
    det_data.append(["TOTAL", f"{em_total:.2f}", "100%"])

    t_det = Table(det_data, colWidths=[9*cm, 5.5*cm, 3.5*cm])
    t_det.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),  (-1,0),  RED),
        ("TEXTCOLOR",      (0,0),  (-1,0),  WHITE),
        ("FONTNAME",       (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",       (0,1),  (-1,-2), "Helvetica"),
        ("FONTNAME",       (0,-1), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND",     (0,-1), (-1,-1), colors.HexColor("#ffebee")),
        ("TEXTCOLOR",      (0,-1), (-1,-1), RED),
        ("FONTSIZE",       (0,0),  (-1,-1), 8.5),
        ("ALIGN",          (1,0),  (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1),  (-1,-2), [WHITE, LGRAY]),
        ("GRID",           (0,0),  (-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",     (0,0),  (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0),  (-1,-1), 6),
        ("LEFTPADDING",    (0,0),  (-1,-1), 9),
    ]))
    story.append(t_det)

    # Rodapé
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} · "
        "TomateCarbon · Metodologia IPCC Tier 1 · GWP-100", s_foot))
    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# GERAÇÃO DE EXCEL
# ══════════════════════════════════════════════════════════════
def gerar_excel(dados: dict) -> bytes:
    buf = io.BytesIO()
    fontes = dados.get("fontes", [])
    df_r = pd.DataFrame(
        [(l, round(v, 2)) for l, v in fontes] + [("TOTAL", round(dados.get("em_total",0),2))],
        columns=["Fonte", "kg CO₂eq ha⁻¹ ano⁻¹"],
    )
    df_u = pd.DataFrame({
        "Campo": ["Produtor","Propriedade","E-mail","Telefone","CAR",
                  "Região","Ano","Cidade","Estado","Área Tomate","Área Total",
                  "Produtividade (kg/ha)","Ciclos/ano"],
        "Valor": [dados.get(k,"") for k in
                  ["prod_name","farm_name","email","phone","car","region",
                   "year_ref","city","state","area_tom","area_farm",
                   "produtividade","ciclos_ano"]],
    })
    df_i = pd.DataFrame({
        "Indicador": ["Emissão Total","Por kg de Tomate","Produtividade"],
        "Valor":     [round(dados.get("em_total",0),2),
                      round(dados.get("em_kg",0),4),
                      round(dados.get("produtividade",0),0)],
        "Unidade":   ["kg CO₂eq ha⁻¹ ano⁻¹","kg CO₂eq kg⁻¹","kg ha⁻¹"],
    })
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_u.to_excel(writer, sheet_name="Produtor",    index=False)
        df_r.to_excel(writer, sheet_name="Resumo",      index=False)
        df_i.to_excel(writer, sheet_name="Indicadores", index=False)
        wb      = writer.book
        hdr_fmt = wb.add_format({"bold":True,"bg_color":"#c62828",
                                  "font_color":"#ffffff","align":"center","border":1})
        num_fmt = wb.add_format({"num_format":"#,##0.00","align":"right"})
        for sn in ["Produtor","Resumo","Indicadores"]:
            ws = writer.sheets[sn]
            ws.set_column("A:A", 32)
            ws.set_column("B:B", 28, num_fmt)
            ws.set_row(0, 18, hdr_fmt)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# HELPERS DE UI
# ══════════════════════════════════════════════════════════════
def progress_bar(current: int, total: int):
    pct = int((current / (total - 1)) * 100) if total > 1 else 0
    st.markdown(
        f'<div class="prog-wrap">'
        f'<div class="prog-fill" style="width:{pct}%"></div></div>',
        unsafe_allow_html=True)

def top_nav(step_name: str):
    p   = st.session_state.page
    tot = TOTAL_STEPS
    pn  = st.session_state.get("prod_name", "")
    fn  = st.session_state.get("farm_name", "")
    sub = f"{pn} · {fn}" if (pn or fn) else ""
    sub_html = f'<div class="topnav-pname">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="topnav">'
        f'<div class="topnav-logo">🍅 TomateCarbon</div>'
        f'<div class="topnav-right">'
        f'<div class="topnav-step">Etapa {p} de {tot} · {step_name}</div>'
        f'{sub_html}</div></div>',
        unsafe_allow_html=True)

def step_dots():
    p   = st.session_state.page
    tot = len(PAGES)
    dots = "".join(
        f'<div class="dot {"active" if i==p else ("done" if i<p else "")}"'
        f' title="{PAGES[i]}"></div>'
        for i in range(tot)
    )
    st.markdown(f'<div class="step-dots">{dots}</div>', unsafe_allow_html=True)

def page_header(eyebrow: str, title: str, desc: str = ""):
    d = f'<div class="page-desc">{desc}</div>' if desc else ""
    st.markdown(
        f'<div class="page-eyebrow">{eyebrow}</div>'
        f'<div class="page-title">{title}</div>{d}',
        unsafe_allow_html=True)

def section_header(label: str, icon: str = ""):
    ic = f'<span class="sh-icon">{icon}</span>' if icon else ""
    st.markdown(f'<div class="section-header">{ic}{label}</div>',
                unsafe_allow_html=True)

def info_tag(text: str):
    st.markdown(f'<div class="info-tag">{text}</div>', unsafe_allow_html=True)

def nav_buttons(current: int, last: bool = False):
    """Sugestão 4: botões grandes, fixos, com texto claro e barra de progresso central."""
    st.markdown("<div style='margin-top:.6rem'></div>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c_mid, c2 = st.columns([1, 3, 1])
    with c1:
        if current > 0:
            if st.button("← Voltar", key=f"btn_v_{current}",
                         use_container_width=True):
                prev_page()
    with c_mid:
        progresso = current / TOTAL_STEPS
        st.progress(progresso,
                    text=f"Etapa {current} de {TOTAL_STEPS} — {PAGES[current]}")
    with c2:
        lbl = "Ver Resultados ✅" if last else "Próxima →"
        if st.button(lbl, key=f"btn_p_{current}", use_container_width=True):
            if last:
                go(10)
            else:
                next_page()


# ══════════════════════════════════════════════════════════════
# PÁGINAS
# ══════════════════════════════════════════════════════════════
p = st.session_state.page
progress_bar(p, len(PAGES))

# ─────────────────────────────────────────────────────────────
# PÁG 0 · APRESENTAÇÃO (sugestão 3)
# ─────────────────────────────────────────────────────────────
if p == 0:
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">🌿 Metodologia IPCC Tier 1 · GWP-100</div>
        <span class="hero-icon">🍅</span>
        <div class="hero-title">TomateCarbon</div>
        <div class="hero-sub">
            Calculadora de Pegada de Carbono<br>para Lavouras de Tomate
        </div>
        <div class="hero-chips">
            <div class="hero-chip">📊 N₂O · CO₂</div>
            <div class="hero-chip">📥 Excel + PDF</div>
            <div class="hero-chip">⚡ 10 etapas guiadas</div>
            <div class="hero-chip">🚁 Drone &amp; Solar</div>
            <div class="hero-chip">💧 Irrigação</div>
            <div class="hero-chip">🌱 Correção de solo</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:.8rem;font-weight:800;letter-spacing:.14em;"
        "text-transform:uppercase;color:rgba(255,255,255,.3);margin-bottom:.5rem'>"
        "📌 Sobre o aplicativo</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:.84rem;color:rgba(255,255,255,.5);line-height:1.7;"
        "margin-bottom:.8rem'>"
        "Este aplicativo estima as <strong style='color:rgba(255,255,255,.75)'>"
        "emissões de gases de efeito estufa (GEE)</strong> associadas ao cultivo "
        "de tomate, expressas em <strong style='color:#ff5252'>kg CO₂eq ha⁻¹</strong>. "
        "Os cálculos seguem o método IPCC Tier 1 e usam fatores de emissão da "
        "literatura científica internacional.</p>",
        unsafe_allow_html=True)

    st.markdown("""
    <div class="intro-grid">
        <div class="intro-card intro-card-blue">
            <h4>✅ Entradas Consideradas</h4>
            <ul>
                <li>Correção de solo — calagem, gessagem, fosfatagem, potassagem</li>
                <li>Adubação de plantio (sintéticos + orgânicos)</li>
                <li>Adubação de cobertura</li>
                <li>Defensivos agrícolas (herbicidas / inseticidas e fungicidas)</li>
                <li>Operações mecanizadas (h/ha × fator de emissão)</li>
                <li>Irrigação — diesel ou energia elétrica</li>
                <li>Drone agrícola (baterias recarregáveis)</li>
                <li>Produtividade em kg/ha</li>
            </ul>
        </div>
        <div class="intro-card intro-card-amber">
            <h4>⚠️ Limites do Sistema</h4>
            <ul>
                <li>Unidade funcional: <strong>1 hectare por ciclo</strong></li>
                <li>Emissões de N₂O pelo método IPCC Tier 1</li>
                <li>Fatores de emissão baseados em literatura científica</li>
                <li>Não inclui transporte pós-colheita</li>
                <li>Não inclui embalagens nem cadeia fria</li>
                <li>Produtividade em <strong>kg ha⁻¹</strong></li>
                <li>Energia elétrica: FE SIN Brasil 0,0385 kg CO₂eq/kWh</li>
                <li>Diesel: 2,604 kg CO₂eq/L | Gasolina: 2,213 kg CO₂eq/L</li>
            </ul>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    _, cb, _ = st.columns([1, 2, 1])
    with cb:
        if st.button("🚀  Começar Agora  →", use_container_width=True):
            next_page()

# ─────────────────────────────────────────────────────────────
# PÁG 1 · IDENTIFICAÇÃO
# ─────────────────────────────────────────────────────────────
elif p == 1:
    top_nav("Identificação")
    step_dots()
    page_header("Etapa 1 de 10", "Identificação",
                "Dados do produtor e da propriedade — aparecerão no relatório final.")

    section_header("Produtor & Propriedade", "👤")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("Nome do Produtor",    key="prod_name",  placeholder="João Silva")
    with c2: st.text_input("Nome da Propriedade", key="farm_name",  placeholder="Fazenda Boa Vista")
    with c3: st.text_input("Município",           key="city",       placeholder="Poços de Caldas")
    with c4: st.text_input("Estado (UF)",         key="state",      placeholder="MG")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("E-mail",        key="email",   placeholder="email@exemplo.com")
    with c2: st.text_input("Telefone",      key="phone",   placeholder="+55 (35) 99999-9999")
    with c3: st.text_input("Nº do CAR",     key="car",     placeholder="000-0000000/0000-00")
    with c4: st.text_input("Região",        key="region",  placeholder="Sul de Minas")

    section_header("Área & Período", "🌱")
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input("Área de tomate (ha)",  key="area_tom",  min_value=0.0, format="%.2f")
    with c2: st.number_input("Área total (ha)",      key="area_farm", min_value=0.0, format="%.2f")
    with c3: st.number_input("Ano de referência",    key="year_ref",
                              min_value=2000, max_value=2100, step=1)
    nav_buttons(1)

# ─────────────────────────────────────────────────────────────
# PÁG 2 · CICLO DE CULTIVO (sugestão 7)
# ─────────────────────────────────────────────────────────────
elif p == 2:
    top_nav("Ciclo de Cultivo")
    step_dots()
    page_header("Etapa 2 de 10", "Ciclo de Cultivo",
                "Defina o sistema de produção, espaçamento e densidade de plantio.")

    section_header("Sistema de Produção", "🌿")
    c1, c2 = st.columns(2)
    with c1:
        st.radio("Tipo de cultivo",
                 ["Campo aberto", "Estufa / Ambiente protegido"],
                 key="tipo_cultivo", horizontal=True)
    with c2:
        st.number_input("Número de plantas por hectare",
                        key="num_plantas", min_value=1,
                        format="%d")
        st.caption("💡 Valor típico: 20.000 a 30.000 plantas/ha")

    section_header("Espaçamento", "📐")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Entre linhas (m)", key="espacamento_linha",
                        min_value=0.1, format="%.2f")
    with c2:
        st.number_input("Entre plantas (m)", key="espacamento_planta",
                        min_value=0.1, format="%.2f")
    with c3:
        el = float(st.session_state.get("espacamento_linha",   1.0) or 1.0)
        ep = float(st.session_state.get("espacamento_planta",  0.5) or 0.5)
        pl_calc = int(10000 / (el * ep)) if (el > 0 and ep > 0) else 0
        st.metric("Plantas/ha calculadas", f"{pl_calc:,}".replace(",","."))
    nav_buttons(2)

# ─────────────────────────────────────────────────────────────
# PÁG 3 · CORREÇÃO DE SOLO (sugestão 8)
# ─────────────────────────────────────────────────────────────
elif p == 3:
    top_nav("Correção de Solo")
    step_dots()
    page_header("Etapa 3 de 10", "Correção de Solo",
                "Insumos aplicados para correção de pH e nutrição base do solo. Unidade: kg/ha.")

    section_header("Calagem", "🟤")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Calcário calcítico (kg/ha)", 0.0, 20000.0,
                        key="calc_calcitico",
                        help="CaCO₃ > 85% | EF: 0,12 kg CO₂eq/kg (IPCC Tier 1)")
    with c2:
        st.number_input("Calcário dolomítico (kg/ha)", 0.0, 20000.0,
                        key="calc_dolomitico",
                        help="CaMg(CO₃)₂ | EF: 0,13 kg CO₂eq/kg (IPCC Tier 1)")

    section_header("Gessagem", "⬜")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.number_input("Gesso agrícola (kg/ha)", 0.0, 15000.0,
                        key="gesso",
                        help="CaSO₄·2H₂O — EF: 0,023 kg CO₂eq/kg")
    with c2:
        st.markdown(
            "<p style='font-size:.74rem;color:rgba(255,255,255,.28);"
            "padding-top:1.6rem;line-height:1.5'>"
            "O gesso agrícola melhora a estrutura do subsolo. "
            "Emissão predominantemente pela produção industrial (CaSO₄).</p>",
            unsafe_allow_html=True)

    section_header("Fosfatagem", "🟡")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Fosfato de rocha (kg/ha)", 0.0, 5000.0,
                        key="fosfato_rocha",
                        help="EF: 0,10 kg CO₂eq/kg")
    with c2:
        st.number_input("Superfosfato simples (kg/ha)", 0.0, 5000.0,
                        key="sfs_corr",
                        help="EF: 0,51 kg CO₂eq/kg (IPCC)")
    with c3:
        st.number_input("Superfosfato triplo (kg/ha)", 0.0, 5000.0,
                        key="sft_corr",
                        help="EF: 0,58 kg CO₂eq/kg (IPCC)")

    section_header("Potassagem", "🟠")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Cloreto de potássio (kg/ha)", 0.0, 5000.0,
                        key="kcl_corr",
                        help="EF: 0,39 kg CO₂eq/kg (IPCC)")
    with c2:
        st.number_input("Pó de rocha potássica (kg/ha)", 0.0, 5000.0,
                        key="po_rocha_k",
                        help="EF: 0,06 kg CO₂eq/kg (literatura)")
    nav_buttons(3)

# ─────────────────────────────────────────────────────────────
# PÁG 4 · ADUBAÇÃO DE PLANTIO (sugestão 9)
# ─────────────────────────────────────────────────────────────
elif p == 4:
    top_nav("Adubação de Plantio")
    step_dots()
    page_header("Etapa 4 de 10", "Adubação de Plantio",
                "Fertilizantes aplicados no sulco ou na área antes/durante o plantio. Unidade: kg/ha.")

    with st.expander("⚗️ Fertilizantes Sintéticos", expanded=True):
        campos_sint = [
            ("Ureia",                 "ureia_p",    0.0, 1000.0, "46% N | EF 1,57 kg CO₂eq/kg"),
            ("MAP",                   "map_p",      0.0, 1000.0, "9% N, 48% P₂O₅ | EF 1,09"),
            ("NPK 4-14-8",            "npk4148_p",  0.0, 2000.0, "EF 0,48 kg CO₂eq/kg (CBAM EU)"),
            ("NPK 4-30-16",           "npk43016_p", 0.0, 2000.0, "EF 0,52 kg CO₂eq/kg"),
            ("Nitrato de cálcio",     "nitcalc_p",  0.0, 1000.0, "15,5% N | EF 1,30"),
            ("Nitrato de potássio",   "nitpot_p",   0.0, 1000.0, "13% N | EF 1,35"),
            ("Superfosfato simples",  "sfs_p",      0.0, 1000.0, "EF 0,51 kg CO₂eq/kg"),
            ("Superfosfato triplo",   "sft_p",      0.0, 1000.0, "EF 0,58 kg CO₂eq/kg"),
            ("Cloreto de potássio",   "kcl_p",      0.0, 1000.0, "EF 0,39 kg CO₂eq/kg"),
            ("Sulfato de magnésio",   "sufmg_p",    0.0,  500.0, "EF 0,14 kg CO₂eq/kg"),
            ("Sulfato de zinco",      "sufzn_p",    0.0,  100.0, "EF 0,18 kg CO₂eq/kg"),
            ("Bórax",                 "borax_p",    0.0,  100.0, "EF 0,10 kg CO₂eq/kg"),
        ]
        c1, c2, c3, c4 = st.columns(4)
        cols = [c1, c2, c3, c4]
        for i, (label, key, mn, mx, tip) in enumerate(campos_sint):
            with cols[i % 4]:
                st.number_input(f"{label} (kg/ha)", mn, mx, key=key, help=tip)

    with st.expander("🌿 Fertilizantes Orgânicos", expanded=True):
        campos_org = [
            ("Esterco bovino",   "est_bov_p",  0.0, 50000.0, "EF 0,23 kg CO₂eq/kg (IPCC)"),
            ("Esterco de frango","est_fra_p",  0.0, 20000.0, "EF 0,31 kg CO₂eq/kg (IPCC)"),
            ("Esterco suíno",    "est_sui_p",  0.0, 20000.0, "EF 0,28 kg CO₂eq/kg"),
            ("Bokashi",          "bokashi_p",  0.0, 10000.0, "EF 0,15 kg CO₂eq/kg"),
            ("Composto orgânico","composto_p", 0.0, 30000.0, "EF 0,10 kg CO₂eq/kg (IPCC)"),
        ]
        c1, c2, c3, c4, c5 = st.columns(5)
        cols_org = [c1, c2, c3, c4, c5]
        for i, (label, key, mn, mx, tip) in enumerate(campos_org):
            with cols_org[i]:
                st.number_input(f"{label} (kg/ha)", mn, mx, key=key, help=tip)
    nav_buttons(4)

# ─────────────────────────────────────────────────────────────
# PÁG 5 · ADUBAÇÃO DE COBERTURA (sugestão 10)
# ─────────────────────────────────────────────────────────────
elif p == 5:
    top_nav("Adubação de Cobertura")
    step_dots()
    page_header("Etapa 5 de 10", "Adubação de Cobertura",
                "Fertilizantes aplicados após o estabelecimento da cultura. Unidade: kg/ha.")

    section_header("Fertilizantes de Cobertura", "🌿")
    campos_cob = [
        ("Ureia",                 "ureia_c",    0.0, 1000.0, "EF 1,57 kg CO₂eq/kg"),
        ("MAP",                   "map_c",      0.0, 1000.0, "EF 1,09 kg CO₂eq/kg"),
        ("Nitrato de cálcio",     "nitcalc_c",  0.0, 1000.0, "EF 1,30 kg CO₂eq/kg"),
        ("Nitrato de potássio",   "nitpot_c",   0.0, 1000.0, "EF 1,35 kg CO₂eq/kg"),
        ("NPK 20-0-20",           "npk2020_c",  0.0, 1000.0, "EF 0,48 kg CO₂eq/kg"),
        ("Cloreto de potássio",   "kcl_c",      0.0, 1000.0, "EF 0,39 kg CO₂eq/kg"),
        ("Sulfato de magnésio",   "sufmg_c",    0.0,  500.0, "EF 0,14 kg CO₂eq/kg"),
        ("Sulfato de zinco",      "sufzn_c",    0.0,  100.0, "EF 0,18 kg CO₂eq/kg"),
        ("Bórax",                 "borax_c",    0.0,  100.0, "EF 0,10 kg CO₂eq/kg"),
    ]
    c1, c2, c3, c4 = st.columns(4)
    cols = [c1, c2, c3, c4]
    for i, (label, key, mn, mx, tip) in enumerate(campos_cob):
        with cols[i % 4]:
            st.number_input(f"{label} (kg/ha)", mn, mx, key=key, help=tip)
    nav_buttons(5)

# ─────────────────────────────────────────────────────────────
# PÁG 6 · DEFENSIVOS AGRÍCOLAS (sugestão 11)
# ─────────────────────────────────────────────────────────────
elif p == 6:
    top_nav("Defensivos Agrícolas")
    step_dots()
    page_header("Etapa 6 de 10", "Defensivos Agrícolas",
                "Consumo de combustível nas aplicações. Informe litros de diesel ou gasolina por ha.")

    section_header("Herbicidas", "🌾")
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input("Trator — diesel (l/ha)",   0.0, 100.0, key="herb_trator",   help="EF 2,604 kg CO₂eq/l")
    with c2: st.number_input("Triciclo — gasolina (l/ha)",0.0, 100.0, key="herb_triciclo", help="EF 2,213 kg CO₂eq/l")
    with c3: st.number_input("Aplicação manual (l/ha)",  0.0, 100.0, key="herb_manual",   help="Costal motorizado")

    section_header("Inseticidas & Fungicidas", "🐛")
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input("Trator — diesel (l/ha)",   0.0, 100.0, key="inset_trator",   help="EF 2,604 kg CO₂eq/l")
    with c2: st.number_input("Triciclo — gasolina (l/ha)",0.0, 100.0, key="inset_triciclo", help="EF 2,213 kg CO₂eq/l")
    with c3: st.number_input("Aplicação manual (l/ha)",  0.0, 100.0, key="inset_manual",   help="Costal motorizado")

    section_header("Drone na Aplicação", "🚁")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.number_input("Baterias por hectare", 0.0, 50.0, key="qtd_bat",
                        help="6,216 Wh/bateria · FE SIN 0,0385 kg CO₂eq/kWh")
    with c2:
        bat = float(st.session_state.get("qtd_bat", 0.0) or 0.0)
        em_drone_prev = calc_drone()
        if bat > 0:
            info_tag(f"🚁 Estimativa: {fmt(em_drone_prev)} kg CO₂eq ha⁻¹")
    nav_buttons(6)

# ─────────────────────────────────────────────────────────────
# PÁG 7 · OPERAÇÕES MECANIZADAS (sugestão 11)
# ─────────────────────────────────────────────────────────────
elif p == 7:
    top_nav("Operações Mecanizadas")
    step_dots()
    page_header("Etapa 7 de 10", "Operações Mecanizadas",
                "Informe as horas de máquina por hectare (h/ha). "
                "Referência: trator 75cv a diesel ≈ 16 kg CO₂eq/h·ha.")

    section_header("Horas de máquina por operação (h/ha)", "🚜")
    operacoes = [
        ("Preparo e correção do solo",          "op_preparo",        "Aração, gradagem, calagem, gessagem etc."),
        ("Adubação de plantio",                 "op_adub_plantio",   "Distribuição de fertilizantes no sulco"),
        ("Plantio de mudas",                    "op_plantio_mudas",  "Transplantio mecanizado ou semi-mecanizado"),
        ("Adubação de cobertura",               "op_adub_cobertura", "Fertirrigação ou aplicação em cobertura"),
        ("Aplicação de herbicidas",             "op_herbicida",      "Pulverização de herbicidas"),
        ("Aplicação de inseticidas/fungicidas", "op_inset_fungi",    "Pulverização fitossanitária"),
        ("Irrigação (operação mecanizada)",     "op_irrigacao",      "Manejo do sistema de irrigação"),
        ("Colheita",                            "op_colheita",       "Colheita manual assistida ou mecanizada"),
        ("Outras operações",                    "op_outras",         "Roçagem, capina, tutoramento etc."),
    ]
    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    for i, (label, key, tip) in enumerate(operacoes):
        with cols[i % 3]:
            st.number_input(f"{label} (h/ha)", 0.0, 200.0, key=key, help=tip)

    section_header("Substituição por Biodiesel", "♻️")
    c1, c2 = st.columns([2, 3])
    with c1:
        st.slider("Biodiesel (%)", 0, 100, key="perc_bio")
    with c2:
        perc = int(st.session_state.get("perc_bio", 0) or 0)
        st.markdown(
            f"<p style='font-size:.8rem;color:rgba(255,255,255,.45);"
            f"padding-top:1.8rem'>"
            f"🌿 <strong style='color:#69f0ae'>{perc}%</strong> biodiesel · "
            f"<strong style='color:rgba(255,255,255,.7)'>{100-perc}%</strong> diesel fóssil"
            f"</p>",
            unsafe_allow_html=True)
    nav_buttons(7)

# ─────────────────────────────────────────────────────────────
# PÁG 8 · IRRIGAÇÃO & ENERGIA
# ─────────────────────────────────────────────────────────────
elif p == 8:
    top_nav("Irrigação & Energia")
    step_dots()
    page_header("Etapa 8 de 10", "Irrigação & Energia",
                "Emissões do bombeamento via diesel ou energia elétrica da rede (SIN).")

    section_header("Energia Solar", "☀️")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.radio("A irrigação usa energia solar?", ["Não", "Sim"],
                 key="usa_solar_raw", horizontal=True, index=0)
    with c2:
        usa_solar = st.session_state.get("usa_solar_raw", "Não") == "Sim"
        st.session_state["usa_solar"] = usa_solar
        if usa_solar:
            st.success("☀️ Energia solar: emissões de eletricidade da irrigação = 0 kg CO₂eq.")

    section_header("Sistema de Irrigação", "💧")
    c1, c2 = st.columns(2)
    with c1:
        st.radio("Há irrigação na área?", ["Não", "Sim"],
                 key="irri_yn", horizontal=True, index=0)

    em_irri = 0.0
    IRRI_OPTS = ["Gotejamento", "Aspersor", "Pivô Central", "Microaspersor"]
    IRRI_REF  = {
        "Gotejamento":  {"Diesel": 5.0,  "Elétrica": 7.0},
        "Aspersor":     {"Diesel": 8.0,  "Elétrica": 10.0},
        "Pivô Central": {"Diesel": 12.0, "Elétrica": 14.0},
        "Microaspersor":{"Diesel": 6.0,  "Elétrica": 8.0},
    }

    if st.session_state.get("irri_yn", "Não") == "Sim":
        section_header("Parâmetros", "⚙️")
        ci1, ci2 = st.columns(2)
        with ci1:
            st.selectbox("Tipo de irrigação", IRRI_OPTS, key="tipo_irri")
        with ci2:
            st.selectbox("Tipo de energia", ["Diesel", "Elétrica"], key="tipo_ger")

        tipo_irri = st.session_state.get("tipo_irri", "Gotejamento")
        tg_pt     = st.session_state.get("tipo_ger",  "Elétrica")

        c1, c2 = st.columns(2)
        with c1:
            use_ri = st.checkbox("📌 Usar valor de referência", key="irri_useref")
        with c2:
            if use_ri:
                ref_l = IRRI_REF.get(tipo_irri, {}).get(tg_pt, 0.0)
                em_irri = (calc_diesel_l(ref_l) if tg_pt == "Diesel"
                           else (0.0 if usa_solar else calc_elec(ref_l)))
                st.markdown(
                    f'<div class="ref-box">📌 Referência ({tipo_irri} · {tg_pt}): '
                    f'<strong>{ref_l:.1f}</strong> l ou kWh/ha → '
                    f'<strong>{em_irri:.2f}</strong> kg CO₂eq/ha</div>',
                    unsafe_allow_html=True)

        if not use_ri:
            if tg_pt == "Diesel":
                c1, _ = st.columns([1, 3])
                with c1:
                    lit = st.number_input("Consumo diesel (l/ha)", 0.0, 5000.0,
                                         key="irri_diesel")
                em_irri = calc_diesel_l(lit)
            else:
                c1, c2, c3 = st.columns(3)
                with c1: hd = st.number_input("Horas/dia",    0.0, 24.0,  key="irri_hd")
                with c2: ma = st.number_input("Meses/ano",    0,   12,    key="irri_ma")
                with c3: cv = st.number_input("Potência (cv)",0.1, 500.0, key="irri_cv",
                                              value=1.0)
                kwh     = (cv * 0.7355 * hd * ma * 30) / 0.9
                em_irri = 0.0 if usa_solar else calc_elec(kwh)
                if kwh > 0:
                    st.info(f"Consumo: **{kwh:.1f} kWh/ha** → **{em_irri:.2f} kg CO₂eq/ha**")

    st.session_state["em_irri"] = em_irri
    nav_buttons(8)

# ─────────────────────────────────────────────────────────────
# PÁG 9 · PRODUTIVIDADE (sugestão 12)
# ─────────────────────────────────────────────────────────────
elif p == 9:
    top_nav("Produtividade")
    step_dots()
    page_header("Etapa 9 de 10", "Produtividade",
                "Informe a produtividade obtida ou esperada para calcular a emissão por kg.")

    section_header("Produção por Hectare", "📦")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input(
            "Produtividade (kg/ha)",
            min_value=0.0, max_value=500_000.0, format="%.0f",
            key="produtividade",
            help="Produção total de tomate por hectare no ciclo avaliado")
    with c2:
        st.number_input(
            "Ciclos por ano", min_value=1, max_value=4,
            key="ciclos_ano",
            help="Quantos ciclos de cultivo por ano nesta área?")
    with c3:
        prod = float(st.session_state.get("produtividade", 0.0) or 0.0)
        cic  = int(st.session_state.get("ciclos_ano",  1)   or 1)
        if prod > 0:
            st.metric("Produção anual (kg/ha)", f"{fmt(prod * cic, 0)}")
    nav_buttons(9, last=True)

# ─────────────────────────────────────────────────────────────
# PÁG 10 · RESULTADOS
# ─────────────────────────────────────────────────────────────
elif p == 10:
    top_nav("Resultados")

    # ── Cálculo consolidado de todas as fontes ─────────────────
    fontes_calc = {
        # Correção de solo
        "🪨 Calcário calcítico":    calc_emissao("calc_calcitico"),
        "🪨 Calcário dolomítico":   calc_emissao("calc_dolomitico"),
        "⬜ Gesso agrícola":        calc_emissao("gesso"),
        "🟡 Fosfato de rocha":      calc_emissao("fosfato_rocha"),
        "🟡 Superfosfato simples (CS)": calc_emissao("sfs_corr"),
        "🟡 Superfosfato triplo (CS)":  calc_emissao("sft_corr"),
        "🟠 Cloreto de potássio (CS)":  calc_emissao("kcl_corr"),
        "🟠 Pó de rocha potássica":     calc_emissao("po_rocha_k"),
        # Adubação plantio — sintéticos
        "🧪 Ureia (plantio)":          calc_emissao("ureia_p"),
        "🧪 MAP (plantio)":            calc_emissao("map_p"),
        "🧪 NPK 4-14-8":               calc_emissao("npk4148_p"),
        "🧪 NPK 4-30-16":              calc_emissao("npk43016_p"),
        "🧪 Nitrato de cálcio (P)":    calc_emissao("nitcalc_p"),
        "🧪 Nitrato de potássio (P)":  calc_emissao("nitpot_p"),
        "🧪 Superfosfato simples (P)": calc_emissao("sfs_p"),
        "🧪 Superfosfato triplo (P)":  calc_emissao("sft_p"),
        "🧪 Cloreto de potássio (P)":  calc_emissao("kcl_p"),
        "🧪 Sulfato de Mg (P)":        calc_emissao("sufmg_p"),
        "🧪 Sulfato de Zn (P)":        calc_emissao("sufzn_p"),
        "🧪 Bórax (plantio)":          calc_emissao("borax_p"),
        # Adubação plantio — orgânicos
        "🌿 Esterco bovino":           calc_emissao("est_bov_p"),
        "🌿 Esterco de frango":        calc_emissao("est_fra_p"),
        "🌿 Esterco suíno":            calc_emissao("est_sui_p"),
        "🌿 Bokashi":                  calc_emissao("bokashi_p"),
        "🌿 Composto orgânico":        calc_emissao("composto_p"),
        # Adubação cobertura
        "🌱 Ureia (cobertura)":        calc_emissao("ureia_c"),
        "🌱 MAP (cobertura)":          calc_emissao("map_c"),
        "🌱 Nitrato de cálcio (C)":    calc_emissao("nitcalc_c"),
        "🌱 Nitrato de potássio (C)":  calc_emissao("nitpot_c"),
        "🌱 NPK 20-0-20":              calc_emissao("npk2020_c"),
        "🌱 Cloreto de potássio (C)":  calc_emissao("kcl_c"),
        "🌱 Sulfato de Mg (C)":        calc_emissao("sufmg_c"),
        "🌱 Sulfato de Zn (C)":        calc_emissao("sufzn_c"),
        "🌱 Bórax (cobertura)":        calc_emissao("borax_c"),
        # Defensivos
        "🌾 Herbicida — trator":       calc_emissao("herb_trator"),
        "🌾 Herbicida — triciclo":     calc_emissao("herb_triciclo"),
        "🌾 Herbicida — manual":       calc_emissao("herb_manual"),
        "🐛 Inset./Fungic. — trator":  calc_emissao("inset_trator"),
        "🐛 Inset./Fungic. — triciclo":calc_emissao("inset_triciclo"),
        "🐛 Inset./Fungic. — manual":  calc_emissao("inset_manual"),
        # Operações, irrigação, drone
        "🚜 Operações mecanizadas":    calc_operacoes(),
        "💧 Irrigação":                float(st.session_state.get("em_irri", 0.0) or 0.0),
        "🚁 Drone":                    calc_drone(),
    }

    # Remover fontes zeradas para a exibição
    fontes_nz = {k: v for k, v in fontes_calc.items() if v > 0.001}
    em_total  = sum(fontes_calc.values())
    prod      = float(st.session_state.get("produtividade", 0.0) or 0.0)
    em_kg     = em_total / prod if prod > 0 else 0.0

    # ── Header ──
    pname = st.session_state.get("prod_name", "—")
    fname = st.session_state.get("farm_name", "—")
    year  = st.session_state.get("year_ref",  2025)
    page_header(
        "📊 Análise Completa", "Resultados",
        f"Produtor: <strong>{pname}</strong> · "
        f"Propriedade: <strong>{fname}</strong> · "
        f"Ano: <strong>{year}</strong>")

    # ── Métricas ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card mc-red">
            <div class="metric-icon">🍅</div>
            <div class="metric-label">Emissão Total</div>
            <div class="metric-value">{fmt(em_total)}</div>
            <div class="metric-unit">kg CO₂eq ha⁻¹ ano⁻¹</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card mc-blue">
            <div class="metric-icon">⚖️</div>
            <div class="metric-label">Por kg de Tomate</div>
            <div class="metric-value">{fmt(em_kg, 4)}</div>
            <div class="metric-unit">kg CO₂eq kg⁻¹</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card mc-amber">
            <div class="metric-icon">📦</div>
            <div class="metric-label">Produtividade</div>
            <div class="metric-value">{fmt(prod, 0)}</div>
            <div class="metric-unit">kg ha⁻¹</div>
        </div>""", unsafe_allow_html=True)

    # ── Tabela de emissões (só fontes > 0) ──
    if fontes_nz:
        max_v = max(fontes_nz.values()) or 1
        rows  = ""
        for lbl, val in fontes_nz.items():
            pct  = (val / max_v) * 100
            pct2 = (val / em_total * 100) if em_total > 0 else 0
            rows += (
                f"<tr><td>{lbl}</td>"
                f"<td class='em-val'>{fmt(val)}</td>"
                f"<td><div class='em-bar-bg'>"
                f"<div class='em-bar-fill' style='width:{pct:.1f}%'></div></div></td>"
                f"<td class='em-pct'>{pct2:.1f}%</td></tr>"
            )
        rows += (
            f"<tr class='em-total-row'><td><strong>TOTAL</strong></td>"
            f"<td class='em-val em-total-val'>{fmt(em_total)}</td>"
            f"<td></td><td class='em-pct'>100%</td></tr>"
        )
        st.markdown(f"""
        <div class="em-wrap">
            <div class="em-title">Detalhamento por Fonte de Emissão</div>
            <table class="em-table">
              <thead><tr>
                <th>Fonte</th>
                <th style="text-align:right">kg CO₂eq ha⁻¹ ano⁻¹</th>
                <th>Proporção</th>
                <th style="text-align:right">%</th>
              </tr></thead>
              <tbody>{rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)

    # ── Gráfico pizza ──
    BG  = (0.027, 0.027, 0.039)
    PAL = [
        (0.937,0.325,0.314),(1.000,0.439,0.263),(1.000,0.835,0.310),
        (0.400,0.733,0.416),(0.259,0.647,0.961),(0.671,0.278,0.737),
        (0.149,0.651,0.604),(1.000,0.541,0.396),(0.5,0.8,0.3),
        (0.9,0.6,0.1),(0.3,0.7,0.9),(0.8,0.3,0.5),
    ]

    # Agrupar para pizza (categorias principais)
    grupos_pizza = {
        "Correção de Solo": sum(fontes_calc.get(k, 0) for k in [
            "🪨 Calcário calcítico","🪨 Calcário dolomítico","⬜ Gesso agrícola",
            "🟡 Fosfato de rocha","🟡 Superfosfato simples (CS)","🟡 Superfosfato triplo (CS)",
            "🟠 Cloreto de potássio (CS)","🟠 Pó de rocha potássica"]),
        "Adubação de Plantio (Sint.)": sum(fontes_calc.get(k, 0) for k in [
            "🧪 Ureia (plantio)","🧪 MAP (plantio)","🧪 NPK 4-14-8","🧪 NPK 4-30-16",
            "🧪 Nitrato de cálcio (P)","🧪 Nitrato de potássio (P)",
            "🧪 Superfosfato simples (P)","🧪 Superfosfato triplo (P)",
            "🧪 Cloreto de potássio (P)","🧪 Sulfato de Mg (P)",
            "🧪 Sulfato de Zn (P)","🧪 Bórax (plantio)"]),
        "Adubação de Plantio (Org.)": sum(fontes_calc.get(k, 0) for k in [
            "🌿 Esterco bovino","🌿 Esterco de frango","🌿 Esterco suíno",
            "🌿 Bokashi","🌿 Composto orgânico"]),
        "Adubação de Cobertura": sum(fontes_calc.get(k, 0) for k in [
            "🌱 Ureia (cobertura)","🌱 MAP (cobertura)","🌱 Nitrato de cálcio (C)",
            "🌱 Nitrato de potássio (C)","🌱 NPK 20-0-20","🌱 Cloreto de potássio (C)",
            "🌱 Sulfato de Mg (C)","🌱 Sulfato de Zn (C)","🌱 Bórax (cobertura)"]),
        "Defensivos Agrícolas": sum(fontes_calc.get(k, 0) for k in [
            "🌾 Herbicida — trator","🌾 Herbicida — triciclo","🌾 Herbicida — manual",
            "🐛 Inset./Fungic. — trator","🐛 Inset./Fungic. — triciclo","🐛 Inset./Fungic. — manual"]),
        "Operações Mecanizadas": fontes_calc.get("🚜 Operações mecanizadas", 0),
        "Irrigação":             fontes_calc.get("💧 Irrigação", 0),
        "Drone":                 fontes_calc.get("🚁 Drone", 0),
    }
    lbls_p = [k for k, v in grupos_pizza.items() if v > 0.01]
    vals_p = [v for k, v in grupos_pizza.items() if v > 0.01]

    if vals_p:
        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            fig, ax = plt.subplots(figsize=(7, 5))
            fig.patch.set_facecolor(BG)
            ax.set_facecolor(BG)
            wedges, _ = ax.pie(
                vals_p, labels=None, startangle=140,
                explode=[0.04] * len(vals_p),
                colors=PAL[:len(vals_p)],
                wedgeprops=dict(width=0.58, edgecolor=BG, linewidth=2),
            )
            for i, w in enumerate(wedges):
                ang   = np.deg2rad((w.theta2 + w.theta1) / 2.0)
                r_mid = 1.0 - w.width / 2.0
                pct   = vals_p[i] / sum(vals_p) * 100
                if pct > 5:
                    ax.text(np.cos(ang) * r_mid, np.sin(ang) * r_mid,
                            f"{pct:.0f}%", ha="center", va="center",
                            fontsize=9, fontweight="bold", color="white")
            ax.set_title("Distribuição por Categoria",
                         fontsize=11, fontweight="bold", color="white", pad=14)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        with col_g2:
            # Gráfico de barras horizontais
            items_bar = sorted(fontes_nz.items(), key=lambda x: x[1], reverse=True)
            nomes_b   = [i[0] for i in items_bar]
            vals_b    = [i[1] for i in items_bar]
            max_vb    = max(vals_b) or 1
            bar_cols  = [(0.78 + 0.20*(1 - v/max_vb), 0.16, 0.16) for v in vals_b]

            fig3, ax3 = plt.subplots(figsize=(7, max(3.5, len(nomes_b)*0.45)))
            fig3.patch.set_facecolor(BG)
            ax3.set_facecolor(BG)
            yp = np.arange(len(nomes_b))
            ax3.barh(yp, vals_b, color=bar_cols, height=0.6,
                     edgecolor=BG, linewidth=1)
            ax3.set_yticks(yp)
            ax3.set_yticklabels(nomes_b, fontsize=8, color="white")
            ax3.set_xlabel("kg CO₂eq ha⁻¹", fontsize=8, color=(0.5,0.5,0.5))
            ax3.set_title("Emissão por Fonte (detalhado)",
                          fontsize=11, fontweight="bold", color="white", pad=12)
            ax3.spines[["top","right","left","bottom"]].set_visible(False)
            ax3.tick_params(axis="x", colors=(0.4,0.4,0.4), labelsize=7)
            ax3.tick_params(axis="y", length=0)
            ax3.grid(axis="x", linestyle=":", alpha=0.08, color="white")
            ax3.invert_yaxis()
            for i, v in enumerate(vals_b):
                ax3.text(v + max_vb*0.01, i, fmt(v),
                         ha="left", va="center",
                         fontsize=7, fontweight="bold", color="white")
            plt.tight_layout(pad=0.5)
            st.pyplot(fig3, use_container_width=True)
            plt.close(fig3)

        # Legenda da pizza
        leg_html = "".join(
            f"<span style='display:inline-flex;align-items:center;gap:4px;"
            f"margin:.2rem .4rem;font-size:.72rem;color:rgba(255,255,255,.55)'>"
            f"<span style='width:10px;height:10px;border-radius:3px;flex-shrink:0;"
            f"background:rgb({int(PAL[i%len(PAL)][0]*255)},"
            f"{int(PAL[i%len(PAL)][1]*255)},"
            f"{int(PAL[i%len(PAL)][2]*255)})'></span>"
            f"{lbls_p[i]} — {fmt(vals_p[i])} kg</span>"
            for i in range(len(lbls_p))
        )
        st.markdown(
            f"<div style='display:flex;flex-wrap:wrap;margin-top:.4rem'>{leg_html}</div>",
            unsafe_allow_html=True)

    # ── Downloads ──
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Exportar Relatório", "📥")

    dados_export = {
        **{k: st.session_state.get(k, "") for k in
           ["prod_name","farm_name","email","phone","car","region",
            "city","state","area_tom","area_farm","year_ref",
            "produtividade","ciclos_ano"]},
        "em_total":       em_total,
        "em_kg":          em_kg,
        "fontes":         list(fontes_nz.items()),
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        if st.button("← Editar dados", use_container_width=True):
            go(1)
    with d2:
        if st.button("🔄 Nova análise", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k != "page":
                    del st.session_state[k]
            go(0)
    with d3:
        st.download_button(
            label="📥 Baixar Excel",
            data=gerar_excel(dados_export),
            file_name=f"TomateCarbon_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with d4:
        st.download_button(
            label="📄 Baixar PDF",
            data=gerar_pdf(dados_export),
            file_name=f"TomateCarbon_{ts}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
