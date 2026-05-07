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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🍅 TomateCarbon",
    page_icon="🍅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "page" not in st.session_state:
    st.session_state.page = 0
if "idioma" not in st.session_state:
    st.session_state.idioma = "Português"

PAGES = [
    "Início", "Dados do Produtor", "Condução & Plantas",
    "Calcário", "Fertilizantes", "Resíduos Orgânicos",
    "Operações Agrícolas", "Drone & Solar", "Irrigação",
    "Produtividade", "Resultados"
]

def go(p):
    st.session_state.page = p
    st.rerun()

def next_page():
    st.session_state.page += 1
    st.rerun()

def prev_page():
    st.session_state.page -= 1
    st.rerun()

# ══════════════════════════════════════════════════════════════
# TRADUÇÕES
# ══════════════════════════════════════════════════════════════
T = {
    "Português": {
        "nav_next":"Próximo →","nav_prev":"← Voltar","nav_calc":"⚡ Calcular Emissões",
        "plants_ha":"Número de Plantas por Hectare",
        "fert_a":"Fertilizante A","fert_b":"Fertilizante B",
        "fert_qty_a":"Quantidade – Fertilizante A","fert_qty_b":"Quantidade – Fertilizante B",
        "cattle":"Esterco Bovino","chicken":"Cama de Frango","compost":"Composto Orgânico",
        "limestone":"Calcário","lime_a":"Calcário A","lime_b":"Calcário B",
        "lime_type_a":"Tipo A","lime_type_b":"Tipo B",
        "lime_qty_a":"Quantidade A (kg ha⁻¹)","lime_qty_b":"Quantidade B (kg ha⁻¹)",
        "ops":"Operações Agrícolas","harvest":"Operação de Colheita",
        "harvest_type":"Tipo de Colheita","vehicle":"Veículo",
        "use_ref":"Usar valor de referência",
        "biodiesel":"Substituição Diesel → Biodiesel (%)",
        "drone":"Drone na Aplicação","batteries":"Baterias por hectare",
        "solar":"Energia Solar","solar_q":"A irrigação usa energia solar?",
        "irrigation":"Irrigação","irri_q":"Há irrigação na área?",
        "irri_type":"Tipo de irrigação","energy_type":"Tipo de energia",
        "hours_day":"Horas/dia","months_year":"Meses/ano","motor_cv":"Potência do motor (cv)",
        "productivity":"Produtividade","prod_label":"Caixas (25 kg) por hectare",
        "total_emission":"Emissão Total","per_box":"Por Caixa (25 kg)","per_kg":"Por kg Tomate",
        "chart_title":"Distribuição das Emissões",
        "download_excel":"📥 Baixar Excel","download_pdf":"📄 Baixar PDF",
        "unit":"Unidade","kg_ha":"kg ha⁻¹ ano⁻¹","g_plant":"g planta⁻¹ ano⁻¹",
        "n_conc":"Concentração de N (%)",
        "prod_name":"Nome do Produtor","farm_name":"Nome da Propriedade",
        "email":"E-mail","phone":"Telefone","car":"Número do CAR",
        "region":"Região","year":"Ano de Referência","city":"Cidade","state":"Estado (UF)",
        "area_tom":"Área de tomate (ha)","area_farm":"Área total (ha)",
        "yes":"Sim","no":"Não","production":"Produção","planting":"Plantio",
        "conduct":"Tipo de Condução","consumption":"Consumo (l ha⁻¹ ano⁻¹)",
        "ref_value":"Valor de referência",
    },
    "English": {
        "nav_next":"Next →","nav_prev":"← Back","nav_calc":"⚡ Calculate Emissions",
        "plants_ha":"Number of Plants per Hectare",
        "fert_a":"Fertilizer A","fert_b":"Fertilizer B",
        "fert_qty_a":"Amount – Fertilizer A","fert_qty_b":"Amount – Fertilizer B",
        "cattle":"Cattle Manure","chicken":"Chicken Bedding","compost":"Organic Compost",
        "limestone":"Limestone","lime_a":"Limestone A","lime_b":"Limestone B",
        "lime_type_a":"Type A","lime_type_b":"Type B",
        "lime_qty_a":"Amount A (kg ha⁻¹)","lime_qty_b":"Amount B (kg ha⁻¹)",
        "ops":"Agricultural Operations","harvest":"Harvest Operation",
        "harvest_type":"Harvest Type","vehicle":"Vehicle",
        "use_ref":"Use reference value",
        "biodiesel":"Diesel → Biodiesel substitution (%)",
        "drone":"Drone Application","batteries":"Batteries per hectare",
        "solar":"Solar Energy","solar_q":"Does irrigation use solar energy?",
        "irrigation":"Irrigation","irri_q":"Is there irrigation?",
        "irri_type":"Irrigation type","energy_type":"Energy type",
        "hours_day":"Hours/day","months_year":"Months/year","motor_cv":"Motor power (hp)",
        "productivity":"Productivity","prod_label":"Boxes (25 kg) per hectare",
        "total_emission":"Total Emission","per_box":"Per Box (25 kg)","per_kg":"Per kg Tomato",
        "chart_title":"Emission Distribution",
        "download_excel":"📥 Download Excel","download_pdf":"📄 Download PDF",
        "unit":"Unit","kg_ha":"kg ha⁻¹ year⁻¹","g_plant":"g plant⁻¹ year⁻¹",
        "n_conc":"N concentration (%)",
        "prod_name":"Producer Name","farm_name":"Property Name",
        "email":"E-mail","phone":"Phone","car":"CAR Number",
        "region":"Region","year":"Reference Year","city":"City","state":"State",
        "area_tom":"Tomato area (ha)","area_farm":"Total area (ha)",
        "yes":"Yes","no":"No","production":"Production","planting":"Planting",
        "conduct":"Cultivation Type","consumption":"Consumption (l ha⁻¹ year⁻¹)",
        "ref_value":"Reference value",
    }
}

idioma = st.session_state.idioma
t      = T[idioma]
KG     = t["kg_ha"]
GPL    = t["g_plant"]

# ══════════════════════════════════════════════════════════════
# DADOS ESTÁTICOS
# ══════════════════════════════════════════════════════════════
FERTILIZANTES = {
    "Sulfato de amônio" if idioma=="Português" else "Ammonium Sulfate": {"n":21.0,"tipo":"ammonium"},
    "Ureia"             if idioma=="Português" else "Urea":             {"n":46.0,"tipo":"urea"},
    "Nitrato de amônio" if idioma=="Português" else "Ammonium Nitrate": {"n":33.0,"tipo":"ammonium-nitrate"},
    "MAP":{"n":9.0,"tipo":"ammonium"},
    "NPK 20-20-20":{"n":20.0,"tipo":"ammonium-nitrate"},
    "NPK 10-10-10":{"n":10.0,"tipo":"ammonium-nitrate"},
}
FERT_KEYS = list(FERTILIZANTES.keys())

LIME_MAP = {"Português":["Calcítico","Dolomítico"],"English":["Calcitic","Dolomitic"]}
LIME_PT  = {"Calcítico":"Calcítico","Dolomítico":"Dolomítico","Calcitic":"Calcítico","Dolomitic":"Dolomítico"}

REF_DIESEL = {
    "Subsolagem":{"Trator":12.0},"Aração":{"Trator":10.0},"Gradagem":{"Trator":8.0},
    "Sulcação / Coveamento":{"Trator":8.0},"Calagem":{"Trator":7.0,"Triciclo":5.0},
    "Aplicação de Fertilizantes":{"Trator":9.0,"Triciclo":5.0,"Manual":0.0},
    "Transplantio":{"Trator":6.0,"Manual":0.0},
    "Aplicação de Defensivos":{"Trator":12.0,"Triciclo":6.0,"Manual":0.0},
    "Aplicação de Herbicidas":{"Trator":12.0,"Triciclo":6.0,"Manual":0.0},
    "Instalação de Tutores":{"Trator":5.0,"Manual":0.0},
    "Roçagem / Capina":{"Roçadeira Motorizada":3.0,"Trator":10.0,"Manual":0.0},
    "Aplicação de Adubo Foliar":{"Trator":9.0,"Triciclo":5.0,"Manual":0.0},
    "Amontoa":{"Trator":8.0,"Manual":0.0},
    "Tutoramento / Amarração":{"Manual":0.0},"Poda / Desbrota":{"Manual":0.0},
    "Colheita Manual":{"Manual":0.0},"Colheita Semimecanizada":{"Trator":10.0},
    "Colheita Mecanizada":{"Trator":14.0},"Transporte interno":{"Trator":6.0},
}

IRRI_OPTS = {
    "Português":["Gotejamento","Aspersor","Pivô Central","Microaspersor"],
    "English":  ["Drip","Sprinkler","Center Pivot","Micro-sprinkler"],
}
IRRI_REF = {
    "Gotejamento":{"Diesel":5.0,"Elétrica":7.0},"Drip":{"Diesel":5.0,"Elétrica":7.0},
    "Aspersor":{"Diesel":8.0,"Elétrica":10.0},"Sprinkler":{"Diesel":8.0,"Elétrica":10.0},
    "Pivô Central":{"Diesel":12.0,"Elétrica":14.0},"Center Pivot":{"Diesel":12.0,"Elétrica":14.0},
    "Microaspersor":{"Diesel":6.0,"Elétrica":8.0},"Micro-sprinkler":{"Diesel":6.0,"Elétrica":8.0},
}

# ══════════════════════════════════════════════════════════════
# CÁLCULOS
# ══════════════════════════════════════════════════════════════
def calc_fert(qtd_n, tipo):
    fv = {"urea":0.15,"ammonium":0.08,"nitrate":0.01,"ammonium-nitrate":0.05}.get(tipo,0.11)
    return (((qtd_n*0.016)+(qtd_n*fv*0.014)+(qtd_n*0.24*0.011))*44/28)*298

def calc_limestone(qtd, tipo_pt, fase):
    f = 0.12 if tipo_pt=="Calcítico" else (0.124 if fase=="Produção" else 0.13)
    return qtd*f*(44/12)

def calc_organic(qtd_n):
    return (((qtd_n*0.006)+(qtd_n*0.21*0.014)+(qtd_n*0.24*0.011))*44/28)*298

def calc_diesel(l):  return l*2.604
def calc_gas(l):     return l*2.2126
def calc_drone(b):   return b*0.006216*0.0003785
def calc_elec(kwh):  return kwh*0.0385

def fmt(v, d=2):
    return f"{v:,.{d}f}".replace(",","X").replace(".",",").replace("X",".")

def conv(val, unit):
    np_ = st.session_state.get("num_plantas",20000)
    return (val*np_/1000.0) if unit==GPL else val

# ══════════════════════════════════════════════════════════════
# CSS GLOBAL
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

html,body,[data-testid="stAppViewContainer"]{
    font-family:'Inter',sans-serif !important;
    background:#07070a !important;
    color:#e8e8f0 !important;
}
[data-testid="stAppViewContainer"]{
    background:
        radial-gradient(ellipse 80% 40% at 10% 0%,  rgba(198,40,40,0.12) 0%,transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 100%,rgba(30,100,30,0.07) 0%,transparent 60%),
        #07070a !important;
}
.block-container{
    max-width:860px !important;
    padding:0 1.8rem 8rem !important;
    margin:0 auto !important;
}
header[data-testid="stHeader"]{display:none !important;}
[data-testid="stSidebar"]{display:none !important;}
footer{display:none !important;}

/* ══ BARRA DE PROGRESSO TOPO ══ */
.prog-wrap{
    position:fixed;top:0;left:0;right:0;z-index:9999;
    height:4px;background:rgba(255,255,255,0.04);
}
.prog-fill{
    height:100%;
    background:linear-gradient(90deg,#7b0000,#c62828,#ff5252,#ff9800);
    background-size:200% 100%;
    animation:shimmer 2s linear infinite;
    transition:width .6s cubic-bezier(.4,0,.2,1);
    border-radius:0 3px 3px 0;
    box-shadow:0 0 16px rgba(220,53,69,.7);
}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* ══ TOP NAV ══ */
.topnav{
    display:flex;align-items:center;justify-content:space-between;
    padding:1.8rem 0 1.2rem;
    border-bottom:1px solid rgba(255,255,255,0.06);
    margin-bottom:2.5rem;
}
.topnav-logo{
    font-size:1.1rem;font-weight:900;letter-spacing:-.02em;
    background:linear-gradient(135deg,#ff5252,#ff9800);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.topnav-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px;}
.topnav-step{font-size:.68rem;font-weight:700;color:rgba(255,255,255,.25);
             letter-spacing:.12em;text-transform:uppercase;}
.topnav-pname{font-size:.8rem;font-weight:600;color:rgba(255,255,255,.4);}

/* ══ STEP DOTS ══ */
.step-dots{display:flex;gap:6px;align-items:center;justify-content:center;
           margin-bottom:2.8rem;flex-wrap:wrap;}
.dot{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.08);
     transition:all .4s cubic-bezier(.4,0,.2,1);cursor:default;}
.dot.active{width:28px;border-radius:99px;
            background:linear-gradient(90deg,#c62828,#ff5252);
            box-shadow:0 0 14px rgba(220,53,69,.55);}
.dot.done{background:rgba(220,53,69,.35);}

/* ══ PAGE HEADER ══ */
.page-eyebrow{
    font-size:.68rem;font-weight:800;letter-spacing:.18em;
    text-transform:uppercase;color:#ff5252;
    margin-bottom:.6rem;display:flex;align-items:center;gap:10px;
}
.page-eyebrow::before{content:'';width:24px;height:2px;
                      background:linear-gradient(90deg,#c62828,#ff5252);
                      border-radius:99px;}
.page-title{
    font-size:clamp(2rem,4vw,2.8rem);font-weight:900;
    line-height:1.08;color:#ffffff;margin-bottom:.6rem;letter-spacing:-.025em;
}
.page-desc{
    font-size:.88rem;color:rgba(255,255,255,.35);
    line-height:1.75;margin-bottom:2.4rem;max-width:580px;
}

/* ══ SECTION CARD — substitui glass-card ══ */
.section-header{
    display:flex;align-items:center;gap:10px;
    font-size:.7rem;font-weight:800;letter-spacing:.14em;
    text-transform:uppercase;color:rgba(255,255,255,.3);
    margin:1.8rem 0 .9rem;padding-bottom:.7rem;
    border-bottom:1px solid rgba(255,255,255,.07);
}
.section-header .sh-icon{font-size:1.1rem;}
.section-header::after{content:'';flex:1;height:1px;background:transparent;}

/* ══ WRAPPER de grupo de widgets ══ */
.widget-group{
    background:linear-gradient(150deg,rgba(255,255,255,.045) 0%,rgba(255,255,255,.018) 100%);
    border:1px solid rgba(255,255,255,.09);
    border-radius:18px;padding:1.5rem 1.7rem;margin-bottom:1.1rem;
    position:relative;overflow:hidden;
    transition:border-color .3s,box-shadow .3s;
}
.widget-group::before{
    content:'';position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.13),transparent);
}
.widget-group:hover{border-color:rgba(198,40,40,.25);box-shadow:0 10px 36px rgba(0,0,0,.3);}
.wg-title{
    font-size:.68rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;
    color:rgba(255,255,255,.28);margin-bottom:1.1rem;
    display:flex;align-items:center;gap:8px;
}
.wg-title-icon{font-size:1rem;}
.wg-divider{border:none;border-top:1px solid rgba(255,255,255,.05);margin:.9rem 0;}

/* ══ HERO ══ */
.hero-wrap{text-align:center;padding:5rem 0 3rem;}
.hero-badge{
    display:inline-flex;align-items:center;gap:8px;
    background:rgba(198,40,40,.1);border:1px solid rgba(198,40,40,.25);
    border-radius:999px;padding:6px 18px;
    font-size:.75rem;font-weight:700;color:#ff8a80;
    letter-spacing:.06em;margin-bottom:2rem;
}
.hero-icon{font-size:6rem;display:block;margin-bottom:1.5rem;
           filter:drop-shadow(0 0 60px rgba(220,53,69,.5));
           animation:float 3.5s ease-in-out infinite;}
@keyframes float{0%,100%{transform:translateY(0) rotate(-2deg);}
                 50%{transform:translateY(-12px) rotate(2deg);}}
.hero-title{
    font-size:clamp(3rem,7vw,4.5rem);font-weight:900;line-height:1.04;
    letter-spacing:-.035em;
    background:linear-gradient(135deg,#ffffff 0%,#ffccbc 40%,#ff5252 80%,#c62828 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    margin-bottom:.9rem;
}
.hero-sub{
    font-size:1.05rem;color:rgba(255,255,255,.38);
    max-width:460px;margin:0 auto 3rem;line-height:1.8;
}
.hero-chips{display:flex;flex-wrap:wrap;gap:.55rem;justify-content:center;margin-bottom:3.5rem;}
.hero-chip{
    padding:7px 18px;background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.08);border-radius:999px;
    font-size:.76rem;color:rgba(255,255,255,.45);font-weight:600;letter-spacing:.03em;
    transition:all .25s;
}
.hero-chip:hover{border-color:rgba(198,40,40,.35);color:rgba(255,255,255,.75);}

/* ══ METRIC CARDS ══ */
.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.8rem;}
@media(max-width:580px){.metric-grid{grid-template-columns:1fr;}}
.metric-card{
    background:linear-gradient(150deg,rgba(255,255,255,.055),rgba(255,255,255,.02));
    border:1px solid rgba(255,255,255,.09);border-radius:20px;
    padding:1.6rem 1.4rem;position:relative;overflow:hidden;
    transition:transform .3s,box-shadow .3s;
}
.metric-card:hover{transform:translateY(-5px);box-shadow:0 20px 50px rgba(0,0,0,.4);}
.metric-card::before{content:'';position:absolute;top:0;left:0;right:0;
                     height:3px;border-radius:20px 20px 0 0;}
.mc-red::before  {background:linear-gradient(90deg,#7b0000,#c62828,#ff5252);}
.mc-blue::before {background:linear-gradient(90deg,#0d47a1,#1976d2,#42a5f5);}
.mc-amber::before{background:linear-gradient(90deg,#bf360c,#e64a19,#ffd54f);}
.metric-icon {font-size:1.9rem;margin-bottom:.6rem;}
.metric-label{font-size:.63rem;font-weight:800;color:rgba(255,255,255,.28);
              text-transform:uppercase;letter-spacing:.12em;margin-bottom:.35rem;}
.metric-value{font-size:1.55rem;font-weight:900;color:#fff;line-height:1;letter-spacing:-.025em;}
.metric-unit {font-size:.63rem;color:rgba(255,255,255,.25);margin-top:.4rem;font-weight:500;}

/* ══ TABELA EMISSÕES ══ */
.em-wrap{
    background:linear-gradient(150deg,rgba(255,255,255,.04),rgba(255,255,255,.015));
    border:1px solid rgba(255,255,255,.08);border-radius:20px;
    padding:1.5rem 1.7rem;margin-top:1.2rem;position:relative;overflow:hidden;
}
.em-wrap::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
                 background:linear-gradient(90deg,transparent,rgba(255,255,255,.12),transparent);}
.em-title{font-size:.68rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
          color:rgba(255,255,255,.28);margin-bottom:1.1rem;
          display:flex;align-items:center;gap:10px;}
.em-title::after{content:'';flex:1;height:1px;background:rgba(255,255,255,.06);}
.em-table{width:100%;border-collapse:collapse;}
.em-table th{padding:8px 12px;font-size:.63rem;font-weight:800;
             color:rgba(255,255,255,.25);text-transform:uppercase;
             letter-spacing:.1em;border-bottom:1px solid rgba(255,255,255,.06);text-align:left;}
.em-table td{padding:10px 12px;font-size:.87rem;
             border-bottom:1px solid rgba(255,255,255,.04);
             color:rgba(255,255,255,.75);vertical-align:middle;}
.em-table tr:last-child td{border-bottom:none;}
.em-table tr:hover td{background:rgba(255,255,255,.025);}
.em-val{font-weight:800;color:#ff6b6b !important;text-align:right !important;
        font-variant-numeric:tabular-nums;}
.em-bar-bg{width:90px;height:5px;background:rgba(255,255,255,.07);
           border-radius:99px;overflow:hidden;}
.em-bar-fill{height:100%;border-radius:99px;
             background:linear-gradient(90deg,#c62828,#ff5252,#ff8a80);}
.em-pct{font-size:.7rem;color:rgba(255,255,255,.3);text-align:right !important;
        font-variant-numeric:tabular-nums;}
.em-total-row td{border-top:2px solid rgba(255,255,255,.1) !important;
                 font-weight:900 !important;color:#fff !important;padding-top:14px !important;}
.em-total-val{color:#ff5252 !important;font-size:1.1rem !important;}

/* ══ REF BOX ══ */
.ref-box{
    background:rgba(255,152,0,.08);border:1px solid rgba(255,152,0,.22);
    border-radius:10px;padding:9px 14px;font-size:.82rem;
    color:#ffcc80;font-weight:600;margin:5px 0 10px;
    display:flex;align-items:center;gap:8px;
}

/* ══ INFO TAG ══ */
.info-tag{
    display:inline-flex;align-items:center;gap:6px;
    background:rgba(66,165,245,.1);border:1px solid rgba(66,165,245,.2);
    border-radius:8px;padding:6px 14px;font-size:.8rem;
    color:#90caf9;font-weight:600;margin-top:.6rem;
}

/* ══ INPUTS BRANCOS COM TEXTO PRETO ══ */
input[type="text"],input[type="number"],input[type="email"],
input[type="tel"],textarea{
    color:#111111 !important;
    background:#f8f8f8 !important;
    border:2px solid #e0e0e0 !important;
    border-radius:10px !important;
    font-family:'Inter',sans-serif !important;
    font-size:.9rem !important;
    font-weight:500 !important;
    transition:border-color .2s,box-shadow .2s,background .2s !important;
    caret-color:#c62828 !important;
}
input:focus,textarea:focus{
    background:#ffffff !important;
    border-color:#c62828 !important;
    box-shadow:0 0 0 4px rgba(198,40,40,.12) !important;
    outline:none !important;
}
input::placeholder{color:#bbb !important;font-weight:400 !important;}

/* Select box branco */
[data-baseweb="select"]>div{
    background:#f8f8f8 !important;border:2px solid #e0e0e0 !important;
    border-radius:10px !important;color:#111 !important;
    font-family:'Inter',sans-serif !important;font-weight:500 !important;
    transition:border-color .2s,box-shadow .2s !important;
}
[data-baseweb="select"]>div:focus-within{
    background:#ffffff !important;border-color:#c62828 !important;
    box-shadow:0 0 0 4px rgba(198,40,40,.12) !important;
}
[data-baseweb="select"] *{color:#111 !important;}
[data-baseweb="select"] svg{color:#666 !important;fill:#666 !important;}
[data-baseweb="popover"],[data-baseweb="menu"]{
    background:#ffffff !important;border-radius:14px !important;
    box-shadow:0 12px 40px rgba(0,0,0,.3) !important;
    border:1px solid rgba(0,0,0,.08) !important;
}
[data-baseweb="option"]{background:#ffffff !important;color:#111 !important;
                        font-weight:500 !important;}
[data-baseweb="option"]:hover{background:#fff5f5 !important;color:#c62828 !important;}
[data-baseweb="option"][aria-selected="true"]{
    background:#fff5f5 !important;color:#c62828 !important;font-weight:700 !important;}
li[role="option"]{background:#ffffff !important;color:#111 !important;}
li[role="option"]:hover{background:#fff5f5 !important;}

/* Number input */
[data-testid="stNumberInput"] button{
    background:rgba(198,40,40,.1) !important;border-radius:8px !important;
    color:#ff5252 !important;border:none !important;transition:background .2s !important;
}
[data-testid="stNumberInput"] button:hover{background:rgba(198,40,40,.2) !important;}

/* Labels */
label,[data-testid="stWidgetLabel"] p{
    font-size:.82rem !important;font-weight:700 !important;
    color:rgba(255,255,255,.55) !important;letter-spacing:.025em !important;
}
/* Radio */
[data-testid="stRadio"] label{color:rgba(255,255,255,.7) !important;}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p{
    color:rgba(255,255,255,.7) !important;font-size:.88rem !important;}
/* Checkbox */
[data-testid="stCheckbox"] p{color:rgba(255,255,255,.6) !important;font-size:.85rem !important;}
[data-testid="stCheckbox"] span[aria-checked="true"]{
    background:#c62828 !important;border-color:#c62828 !important;}
/* Slider */
[data-testid="stSlider"]>div>div>div>div{
    background:linear-gradient(90deg,#c62828,#ff5252) !important;}
[data-testid="stSlider"] [role="slider"]{
    background:#ff5252 !important;border:3px solid #fff !important;
    box-shadow:0 0 12px rgba(220,53,69,.6) !important;}
/* st.info / success */
[data-testid="stInfo"]{
    background:rgba(66,165,245,.08) !important;
    border:1px solid rgba(66,165,245,.2) !important;
    border-radius:12px !important;color:#90caf9 !important;}
[data-testid="stSuccess"]{
    background:rgba(105,240,174,.07) !important;
    border:1px solid rgba(105,240,174,.18) !important;
    border-radius:12px !important;color:#69f0ae !important;}

/* ══ BOTÕES DE NAVEGAÇÃO ══ */
.nav-btn-wrap{
    display:flex;gap:1rem;margin-top:2.5rem;padding-top:1.5rem;
    border-top:1px solid rgba(255,255,255,.06);
}
.nav-btn-prev{
    flex:1;padding:16px 28px;
    background:rgba(255,255,255,.06);
    border:1.5px solid rgba(255,255,255,.12);
    border-radius:14px;color:rgba(255,255,255,.7);
    font-family:'Inter',sans-serif;font-size:.95rem;font-weight:700;
    cursor:pointer;transition:all .25s;letter-spacing:.02em;
    display:flex;align-items:center;justify-content:center;gap:8px;
}
.nav-btn-prev:hover{
    background:rgba(255,255,255,.1);color:#fff;
    border-color:rgba(255,255,255,.22);transform:translateX(-3px);
}
.nav-btn-next{
    flex:2;padding:16px 28px;
    background:linear-gradient(135deg,#c62828 0%,#b71c1c 100%);
    border:none;border-radius:14px;color:#fff;
    font-family:'Inter',sans-serif;font-size:.98rem;font-weight:800;
    cursor:pointer;transition:all .28s;letter-spacing:.02em;
    display:flex;align-items:center;justify-content:center;gap:10px;
    box-shadow:0 8px 28px rgba(198,40,40,.45),
               inset 0 1px 0 rgba(255,255,255,.15);
    position:relative;overflow:hidden;
}
.nav-btn-next::before{
    content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.1),transparent);
    transition:left .4s;
}
.nav-btn-next:hover::before{left:100%;}
.nav-btn-next:hover{
    background:linear-gradient(135deg,#d32f2f,#c62828);
    box-shadow:0 14px 38px rgba(198,40,40,.6),inset 0 1px 0 rgba(255,255,255,.2);
    transform:translateY(-2px);
}
.nav-btn-next:active{transform:translateY(0);}

/* Botões Streamlit padrão — override */
.stButton>button{
    font-family:'Inter',sans-serif !important;font-weight:800 !important;
    font-size:.95rem !important;border-radius:14px !important;
    padding:15px 24px !important;transition:all .28s !important;
    cursor:pointer !important;letter-spacing:.02em !important;
    width:100% !important;border:none !important;
}
/* Botão direito / único = primário vermelho */
div[data-testid="column"]:last-child .stButton>button,
div[data-testid="column"]:only-child .stButton>button{
    background:linear-gradient(135deg,#c62828,#b71c1c) !important;
    color:#fff !important;
    box-shadow:0 8px 28px rgba(198,40,40,.45),
               inset 0 1px 0 rgba(255,255,255,.15) !important;
}
div[data-testid="column"]:last-child .stButton>button:hover{
    transform:translateY(-3px) !important;
    box-shadow:0 14px 38px rgba(198,40,40,.6) !important;
    background:linear-gradient(135deg,#d32f2f,#c62828) !important;
}
/* Botão esquerdo = secundário */
div[data-testid="column"]:first-child .stButton>button{
    background:rgba(255,255,255,.06) !important;
    color:rgba(255,255,255,.7) !important;
    border:1.5px solid rgba(255,255,255,.12) !important;
}
div[data-testid="column"]:first-child .stButton>button:hover{
    background:rgba(255,255,255,.1) !important;
    color:#fff !important;border-color:rgba(255,255,255,.22) !important;
    transform:translateX(-3px) !important;
}
/* Download */
[data-testid="stDownloadButton"]>button{
    background:linear-gradient(135deg,rgba(255,255,255,.1),rgba(255,255,255,.05)) !important;
    border:1.5px solid rgba(255,255,255,.15) !important;
    border-radius:14px !important;color:#fff !important;
    font-weight:700 !important;padding:14px !important;
    transition:all .25s !important;
}
[data-testid="stDownloadButton"]>button:hover{
    background:rgba(255,255,255,.14) !important;
    border-color:rgba(255,255,255,.28) !important;
    transform:translateY(-2px) !important;
    box-shadow:0 8px 24px rgba(0,0,0,.3) !important;
}

/* Scrollbar */
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(220,53,69,.4);border-radius:99px;}

/* Caption */
[data-testid="stCaptionContainer"] p{
    color:rgba(255,255,255,.28) !important;font-size:.75rem !important;}
hr{border-color:rgba(255,255,255,.06) !important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HELPERS DE UI
# ══════════════════════════════════════════════════════════════
def progress_bar(current, total):
    pct = int((current/(total-1))*100)
    st.markdown(
        f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>',
        unsafe_allow_html=True)

def top_nav(step_name):
    p   = st.session_state.page
    tot = len(PAGES)
    pn  = st.session_state.get("prod_name","")
    fn  = st.session_state.get("farm_name","")
    sub = f"{pn} · {fn}" if (pn or fn) else ""
    st.markdown(f"""
    <div class="topnav">
        <div class="topnav-logo">🍅 TomateCarbon</div>
        <div class="topnav-right">
            <div class="topnav-step">Etapa {p} de {tot-1} · {step_name}</div>
            {"" if not sub else f'<div class="topnav-pname">{sub}</div>'}
        </div>
    </div>""", unsafe_allow_html=True)

def step_dots():
    p   = st.session_state.page
    tot = len(PAGES)
    dots = "".join(
        f'<div class="dot {"active" if i==p else ("done" if i<p else "")}"'
        f' title="{PAGES[i]}"></div>'
        for i in range(tot)
    )
    st.markdown(f'<div class="step-dots">{dots}</div>', unsafe_allow_html=True)

def page_header(eyebrow, title, desc=""):
    d = f'<div class="page-desc">{desc}</div>' if desc else ""
    st.markdown(
        f'<div class="page-eyebrow">{eyebrow}</div>'
        f'<div class="page-title">{title}</div>{d}',
        unsafe_allow_html=True)

def section_header(label, icon=""):
    ic = f'<span class="sh-icon">{icon}</span>' if icon else ""
    st.markdown(
        f'<div class="section-header">{ic}{label}</div>',
        unsafe_allow_html=True)

def wg_open(title="", icon=""):
    """Abre um widget-group: renderiza apenas o título acima dos widgets."""
    if title or icon:
        ic = f'<span class="wg-title-icon">{icon}</span>' if icon else ""
        st.markdown(
            f'<div class="wg-title">{ic}{title}</div>',
            unsafe_allow_html=True)

def wg_sep():
    st.markdown('<div class="wg-divider"></div>', unsafe_allow_html=True)

def ref_box(label, value):
    st.markdown(
        f'<div class="ref-box">📌 {label}: <strong>{value:.2f}</strong> l ha⁻¹</div>',
        unsafe_allow_html=True)

def info_tag(text):
    st.markdown(f'<div class="info-tag">{text}</div>', unsafe_allow_html=True)

def u_radio(key, horizontal=True):
    return st.radio(t["unit"], [KG, GPL], key=f"ur_{key}", horizontal=horizontal)

def nav_buttons(last=False):
    """Botões de navegação grandes e visíveis via colunas Streamlit."""
    p = st.session_state.page
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    if p == 0:
        if st.button(f"🚀  Começar Agora  →", use_container_width=True):
            next_page()
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button(f"{t['nav_prev']}", use_container_width=True):
            prev_page()
    with c2:
        lbl = t["nav_calc"] if last else f"{t['nav_next']}"
        if st.button(lbl, use_container_width=True):
            go(len(PAGES)-1) if last else next_page()

# ══════════════════════════════════════════════════════════════
# GERAÇÃO DE PDF
# ══════════════════════════════════════════════════════════════
def gerar_pdf(dados):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    RED    = colors.HexColor("#c62828")
    DARK   = colors.HexColor("#1a1a2e")
    GRAY   = colors.HexColor("#555555")
    LGRAY  = colors.HexColor("#f5f5f5")
    WHITE  = colors.white

    styles = getSampleStyleSheet()
    s_title = ParagraphStyle("title", fontSize=22, fontName="Helvetica-Bold",
                              textColor=RED, spaceAfter=4, alignment=TA_LEFT)
    s_sub   = ParagraphStyle("sub",   fontSize=11, fontName="Helvetica",
                              textColor=GRAY, spaceAfter=16, alignment=TA_LEFT)
    s_sec   = ParagraphStyle("sec",   fontSize=10, fontName="Helvetica-Bold",
                              textColor=RED, spaceBefore=16, spaceAfter=6,
                              borderPadding=(0,0,4,0))
    s_body  = ParagraphStyle("body",  fontSize=9,  fontName="Helvetica",
                              textColor=colors.HexColor("#333333"), spaceAfter=4)
    s_foot  = ParagraphStyle("foot",  fontSize=8,  fontName="Helvetica",
                              textColor=GRAY, alignment=TA_CENTER)

    story = []

    # Cabeçalho
    story.append(Paragraph("🍅 TomateCarbon", s_title))
    story.append(Paragraph("Relatório de Emissões de Carbono — Lavoura de Tomate", s_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=RED, spaceAfter=12))

    # Dados do produtor
    story.append(Paragraph("IDENTIFICAÇÃO", s_sec))
    info_data = [
        ["Produtor",    dados.get("prod_name","—"),  "Propriedade", dados.get("farm_name","—")],
        ["E-mail",      dados.get("email","—"),       "Telefone",    dados.get("phone","—")],
        ["CAR",         dados.get("car","—"),          "Região",      dados.get("region","—")],
        ["Cidade/UF",   f"{dados.get('city','—')}/{dados.get('state','—')}",
         "Ano",         str(dados.get("year_ref","—"))],
        ["Área Tomate", f"{dados.get('area_tom',0):.2f} ha",
         "Área Total",  f"{dados.get('area_farm',0):.2f} ha"],
    ]
    t_info = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 5*cm])
    t_info.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",  (2,0),(2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 8.5),
        ("TEXTCOLOR", (0,0),(0,-1),  GRAY),
        ("TEXTCOLOR", (2,0),(2,-1),  GRAY),
        ("BACKGROUND",(0,0),(-1,-1), LGRAY),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, LGRAY]),
        ("GRID",      (0,0),(-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING",(0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 14))

    # Indicadores
    story.append(Paragraph("INDICADORES DE EMISSÃO", s_sec))
    ind_data = [
        ["Indicador", "Valor", "Unidade"],
        ["Emissão Total",     f"{dados['em_total']:.2f}",  "kg CO₂eq ha⁻¹ ano⁻¹"],
        ["Por Caixa (25 kg)", f"{dados['em_cx']:.2f}",     "kg CO₂eq caixa⁻¹"],
        ["Por kg de Tomate",  f"{dados['em_kg']:.4f}",     "kg CO₂eq kg⁻¹"],
    ]
    t_ind = Table(ind_data, colWidths=[7*cm, 4*cm, 7*cm])
    t_ind.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,0),  RED),
        ("TEXTCOLOR",   (0,0),(-1,0),  WHITE),
        ("FONTNAME",    (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTNAME",    (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,0),(-1,-1), 9),
        ("ALIGN",       (1,0),(-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
        ("GRID",        (0,0),(-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",  (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING", (0,0),(-1,-1), 10),
    ]))
    story.append(t_ind)
    story.append(Spacer(1, 14))

    # Detalhamento
    story.append(Paragraph("DETALHAMENTO POR FONTE", s_sec))
    det_data = [["Fonte de Emissão", "kg CO₂eq ha⁻¹ ano⁻¹", "%"]]
    for lbl, val in dados["fontes"]:
        pct = (val/dados["em_total"]*100) if dados["em_total"] > 0 else 0
        det_data.append([lbl, f"{val:.2f}", f"{pct:.1f}%"])
    det_data.append(["TOTAL", f"{dados['em_total']:.2f}", "100%"])

    t_det = Table(det_data, colWidths=[9*cm, 5.5*cm, 3.5*cm])
    t_det.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0),  RED),
        ("TEXTCOLOR",    (0,0),(-1,0),  WHITE),
        ("FONTNAME",     (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTNAME",     (0,1),(-1,-2), "Helvetica"),
        ("FONTNAME",     (0,-1),(-1,-1),"Helvetica-Bold"),
        ("BACKGROUND",   (0,-1),(-1,-1),colors.HexColor("#ffebee")),
        ("TEXTCOLOR",    (0,-1),(-1,-1),RED),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
        ("ALIGN",        (1,0),(-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-2),[WHITE, LGRAY]),
        ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story.append(t_det)
    story.append(Spacer(1, 14))

    # Operações diesel
    if dados.get("diesel_op"):
        story.append(Paragraph("OPERAÇÕES AGRÍCOLAS — COMBUSTÍVEL", s_sec))
        op_data = [["Operação", "kg CO₂eq ha⁻¹ ano⁻¹"]]
        for op, val in dados["diesel_op"].items():
            if val > 0:
                op_data.append([op, f"{val:.2f}"])
        t_op = Table(op_data, colWidths=[12*cm, 6*cm])
        t_op.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,0),  colors.HexColor("#e65100")),
            ("TEXTCOLOR",    (0,0),(-1,0),  WHITE),
            ("FONTNAME",     (0,0),(-1,0),  "Helvetica-Bold"),
            ("FONTNAME",     (0,1),(-1,-1), "Helvetica"),
            ("FONTSIZE",     (0,0),(-1,-1), 9),
            ("ALIGN",        (1,0),(-1,-1), "RIGHT"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#dddddd")),
            ("TOPPADDING",   (0,0),(-1,-1), 7),
            ("BOTTOMPADDING",(0,0),(-1,-1), 7),
            ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ]))
        story.append(t_op)

    # Rodapé
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} · "
        f"TomateCarbon · Metodologia IPCC Tier 1 · GWP-100",
        s_foot))

    doc.build(story)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════
# GERAÇÃO DE EXCEL
# ══════════════════════════════════════════════════════════════
def gerar_excel(dados):
    buf = io.BytesIO()
    nomes_f = ["Fertilizante A","Fertilizante B","Calcário A","Calcário B",
               "Esterco Bovino","Cama de Frango","Composto Orgânico",
               "Diesel / Combustíveis","Irrigação","Drone","TOTAL"]
    vals_f  = [round(v,2) for v in [
        dados["em_f1"],dados["em_f2"],dados["em_c1"],dados["em_c2"],
        dados["em_est"],dados["em_cam"],dados["em_comp"],
        dados["em_diesel"],dados["em_irri"],dados["em_drone"],dados["em_total"]
    ]]
    df_r  = pd.DataFrame({"Fonte":nomes_f,"kg CO₂eq ha⁻¹ ano⁻¹":vals_f})
    df_d  = pd.DataFrame(list(dados["diesel_op"].items()),
                         columns=["Operação","kg CO₂eq ha⁻¹ ano⁻¹"])
    df_u  = pd.DataFrame({
        "Campo":  ["Produtor","Propriedade","E-mail","Telefone","CAR",
                   "Região","Ano","Cidade","Estado","Área Tomate","Área Total"],
        "Valor":  [dados.get(k,"") for k in
                   ["prod_name","farm_name","email","phone","car",
                    "region","year_ref","city","state","area_tom","area_farm"]]
    })
    df_i  = pd.DataFrame({
        "Indicador":["Emissão Total","Por Caixa (25 kg)","Por kg de Tomate"],
        "Valor":    [round(dados["em_total"],2),round(dados["em_cx"],2),round(dados["em_kg"],4)],
        "Unidade":  ["kg CO₂eq ha⁻¹ ano⁻¹","kg CO₂eq caixa⁻¹","kg CO₂eq kg⁻¹"]
    })
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_u.to_excel(writer, sheet_name="Produtor",    index=False)
        df_r.to_excel(writer, sheet_name="Resumo",      index=False)
        df_d.to_excel(writer, sheet_name="Operações",   index=False)
        df_i.to_excel(writer, sheet_name="Indicadores", index=False)
        wb = writer.book
        hdr_fmt = wb.add_format({"bold":True,"bg_color":"#c62828",
                                  "font_color":"#ffffff","align":"center","border":1})
        num_fmt = wb.add_format({"num_format":"#,##0.00","align":"right"})
        for sn in ["Produtor","Resumo","Operações","Indicadores"]:
            ws = writer.sheets[sn]
            ws.set_column("A:A",32); ws.set_column("B:B",28,num_fmt)
            ws.set_row(0, 18, hdr_fmt)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════
# PÁGINAS
# ══════════════════════════════════════════════════════════════
p = st.session_state.page
progress_bar(p, len(PAGES))

# ─────────────────────────────────────────────────────────────
# PÁG 0 · INÍCIO
# ─────────────────────────────────────────────────────────────
if p == 0:
    top_nav("Início")
    _, col_lang = st.columns([5, 1])
    with col_lang:
        lang = st.selectbox("", ["Português","English"],
                            index=0 if idioma=="Português" else 1,
                            label_visibility="collapsed", key="lang_sel")
        if lang != st.session_state.idioma:
            st.session_state.idioma = lang
            st.rerun()

    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">🌿 Metodologia IPCC Tier 1 · GWP-100</div>
        <span class="hero-icon">🍅</span>
        <div class="hero-title">TomateCarbon</div>
        <div class="hero-sub">
            Calcule, monitore e reduza as emissões de carbono<br>
            da sua lavoura de tomate com precisão científica.
        </div>
        <div class="hero-chips">
            <div class="hero-chip">📊 N₂O · CH₄ · CO₂</div>
            <div class="hero-chip">📥 Excel + PDF</div>
            <div class="hero-chip">🇧🇷 PT · EN</div>
            <div class="hero-chip">⚡ 9 etapas guiadas</div>
            <div class="hero-chip">🚁 Drone & Solar</div>
            <div class="hero-chip">💧 Irrigação</div>
        </div>
    </div>""", unsafe_allow_html=True)
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 1 · DADOS DO PRODUTOR
# ─────────────────────────────────────────────────────────────
elif p == 1:
    top_nav("Dados do Produtor")
    step_dots()
    page_header("Etapa 1 de 9", "Dados do Produtor",
                "Preencha as informações da propriedade. Aparecerão no relatório final.")

    section_header("Identificação", "👤")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input(t["prod_name"],  key="prod_name",  placeholder="Ex.: João Silva")
        st.text_input(t["email"],      key="email",       placeholder="email@exemplo.com")
        st.text_input(t["car"],        key="car",         placeholder="000-0000000/0000-00")
        st.text_input(t["city"],       key="city",        placeholder="Ex.: Poços de Caldas")
    with c2:
        st.text_input(t["farm_name"],  key="farm_name",   placeholder="Ex.: Fazenda Boa Vista")
        st.text_input(t["phone"],      key="phone",       placeholder="+55 (35) 99999-9999")
        st.text_input(t["region"],     key="region",      placeholder="Ex.: Sul de Minas")
        st.text_input(t["state"],      key="state",       placeholder="Ex.: MG")

    section_header("Propriedade & Período", "🌱")
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input(t["area_tom"],  key="area_tom",  min_value=0.0, format="%.2f")
    with c2: st.number_input(t["area_farm"], key="area_farm", min_value=0.0, format="%.2f")
    with c3: st.number_input(t["year"],      key="year_ref",  min_value=2000, max_value=2100,
                              value=2025, step=1)
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 2 · CONDUÇÃO & PLANTAS
# ─────────────────────────────────────────────────────────────
elif p == 2:
    top_nav("Condução & Plantas")
    step_dots()
    page_header("Etapa 2 de 9", "Condução & Plantas",
                "Defina o tipo de cultivo e a densidade de plantio.")

    section_header("Tipo de Condução", "🌿")
    st.radio(t["conduct"], [t["production"], t["planting"]],
             key="tipo_raw", horizontal=True, label_visibility="collapsed")

    section_header("Densidade de Plantio", "🌱")
    st.number_input(t["plants_ha"], key="num_plantas",
                    min_value=1, format="%d", value=20000,
                    label_visibility="collapsed")
    st.caption("💡 Usado para converter g/planta → kg/ha em todos os insumos.")
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 3 · CALCÁRIO
# ─────────────────────────────────────────────────────────────
elif p == 3:
    top_nav("Calcário")
    step_dots()
    page_header("Etapa 3 de 9", "Calcário",
                "Emissões calculadas pela dissolução do carbonato — IPCC Tier 1.")

    lime_opts = LIME_MAP[idioma]
    c1, c2 = st.columns(2)

    with c1:
        section_header("Calcário A", "🪨")
        st.selectbox(t["lime_type_a"], lime_opts, key="tc1")
        ur_c1 = u_radio("c1")
        st.number_input(t["lime_qty_a"], min_value=0.0, format="%.2f", key="qc1_raw")

    with c2:
        section_header("Calcário B", "🪨")
        st.selectbox(t["lime_type_b"], lime_opts, key="tc2")
        ur_c2 = u_radio("c2")
        st.number_input(t["lime_qty_b"], min_value=0.0, format="%.2f", key="qc2_raw")

    st.session_state["qc1_conv"] = conv(st.session_state.get("qc1_raw",0.0), ur_c1)
    st.session_state["qc2_conv"] = conv(st.session_state.get("qc2_raw",0.0), ur_c2)
    st.session_state["tc1_pt"]   = LIME_PT.get(st.session_state.get("tc1",lime_opts[0]),"Calcítico")
    st.session_state["tc2_pt"]   = LIME_PT.get(st.session_state.get("tc2",lime_opts[0]),"Calcítico")
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 4 · FERTILIZANTES
# ─────────────────────────────────────────────────────────────
elif p == 4:
    top_nav("Fertilizantes Sintéticos")
    step_dots()
    page_header("Etapa 4 de 9", "Fertilizantes Sintéticos",
                "N₂O direto + volatilização NH₃ + lixiviação NO₃⁻ (IPCC Tier 1).")

    c1, c2 = st.columns(2)
    with c1:
        section_header("Fertilizante A", "🧪")
        st.selectbox(t["fert_a"], FERT_KEYS, key="fert1", label_visibility="collapsed")
        ur_f1 = u_radio("f1")
        st.number_input(t["fert_qty_a"], min_value=0.0, format="%.2f", key="qf1_raw")
        n1 = FERTILIZANTES[st.session_state.get("fert1",FERT_KEYS[0])]["n"]
        info_tag(f"🔬 Teor de N: {n1}%")

    with c2:
        section_header("Fertilizante B", "🧪")
        st.selectbox(t["fert_b"], FERT_KEYS, key="fert2", label_visibility="collapsed")
        ur_f2 = u_radio("f2")
        st.number_input(t["fert_qty_b"], min_value=0.0, format="%.2f", key="qf2_raw")
        n2 = FERTILIZANTES[st.session_state.get("fert2",FERT_KEYS[0])]["n"]
        info_tag(f"🔬 Teor de N: {n2}%")

    st.session_state["qf1_conv"] = conv(st.session_state.get("qf1_raw",0.0), ur_f1)
    st.session_state["qf2_conv"] = conv(st.session_state.get("qf2_raw",0.0), ur_f2)
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 5 · RESÍDUOS ORGÂNICOS
# ─────────────────────────────────────────────────────────────
elif p == 5:
    top_nav("Resíduos Orgânicos")
    step_dots()
    page_header("Etapa 5 de 9", "Resíduos Orgânicos",
                "N₂O pela decomposição de fertilizantes orgânicos (IPCC Tier 1).")

    c1, c2 = st.columns(2)
    with c1:
        section_header("Esterco Bovino", "🐄")
        ur_est = u_radio("est")
        st.number_input(t["cattle"], min_value=0.0, format="%.2f",
                        key="qest_raw", label_visibility="collapsed")
        st.caption("Fator N padrão: 1,5% (IPCC)")

        section_header("Cama de Frango", "🐔")
        ur_cam = u_radio("cam")
        st.number_input(t["chicken"], min_value=0.0, format="%.2f",
                        key="qcam_raw", label_visibility="collapsed")
        st.caption("Fator N padrão: 3,1% (IPCC)")

    with c2:
        section_header("Composto Orgânico", "♻️")
        ur_comp = u_radio("comp")
        st.number_input(t["compost"], min_value=0.0, format="%.2f",
                        key="qcomp_raw", label_visibility="collapsed")
        st.number_input(t["n_conc"], min_value=0.0, max_value=100.0,
                        format="%.2f", key="n_comp_val")

    st.session_state["qest_conv"]  = conv(st.session_state.get("qest_raw",0.0),  ur_est)
    st.session_state["qcam_conv"]  = conv(st.session_state.get("qcam_raw",0.0),  ur_cam)
    st.session_state["qcomp_conv"] = conv(st.session_state.get("qcomp_raw",0.0), ur_comp)
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 6 · OPERAÇÕES AGRÍCOLAS
# ─────────────────────────────────────────────────────────────
elif p == 6:
    top_nav("Operações Agrícolas")
    step_dots()
    page_header("Etapa 6 de 9", "Operações Agrícolas",
                "Consumo de combustível por operação — use valores reais ou de referência.")

    tipo_raw     = st.session_state.get("tipo_raw", t["production"])
    tipo_cultivo = "Produção" if tipo_raw == t["production"] else "Plantio"

    ops_gerais = (
        {
            "Subsolagem":["Trator"],"Aração":["Trator"],"Gradagem":["Trator"],
            "Sulcação / Coveamento":["Trator"],"Calagem":["Trator","Triciclo"],
            "Aplicação de Fertilizantes":["Trator","Triciclo","Manual"],
            "Transplantio":["Trator","Manual"],
            "Aplicação de Defensivos":["Trator","Triciclo","Manual"],
            "Aplicação de Herbicidas":["Trator","Triciclo","Manual"],
            "Instalação de Tutores":["Trator","Manual"],
        } if tipo_cultivo=="Plantio" else {
            "Roçagem / Capina":["Roçadeira Motorizada","Trator","Manual"],
            "Aplicação de Defensivos":["Trator","Triciclo","Manual"],
            "Aplicação de Herbicidas":["Trator","Triciclo","Manual"],
            "Aplicação de Adubo Foliar":["Trator","Triciclo","Manual"],
            "Calagem":["Trator","Triciclo"],
            "Aplicação de Fertilizantes":["Trator","Triciclo","Manual"],
            "Amontoa":["Trator","Manual"],
            "Tutoramento / Amarração":["Manual"],
            "Poda / Desbrota":["Manual"],
        }
    )
    ops_colheita = {
        "Colheita Manual":["Manual"],
        "Colheita Semimecanizada":["Trator"],
        "Colheita Mecanizada":["Trator"],
        "Transporte interno":["Trator"],
    }
    diesel_inputs = {}

    section_header("Operações Gerais", "🚜")
    for i, (op, veics) in enumerate(ops_gerais.items()):
        ca, cb, cc = st.columns([2.2, 1.5, 1.5])
        with ca:
            st.markdown(
                f"<p style='color:rgba(255,255,255,.78);font-size:.88rem;"
                f"font-weight:600;padding:8px 0 0'>{op}</p>",
                unsafe_allow_html=True)
        with cb:
            veic = st.selectbox(t["vehicle"], veics, key=f"v_{op}",
                                label_visibility="collapsed")
        with cc:
            use_r = st.checkbox(t["use_ref"], key=f"r_{op}")
        rv = REF_DIESEL.get(op,{}).get(veic,0.0)
        if use_r:
            ref_box(f"{op} ({veic})", rv)
            diesel_inputs[op] = {veic: rv}
        else:
            val = st.number_input(t["consumption"], min_value=0.0, format="%.2f",
                                  key=f"i_{op}", label_visibility="collapsed")
            diesel_inputs[op] = {veic: val}
        if i < len(ops_gerais)-1:
            st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,.05);margin:.6rem 0">',
                        unsafe_allow_html=True)

    if tipo_cultivo == "Produção":
        section_header("Colheita", "🍅")
        ch1, ch2 = st.columns(2)
        with ch1: col_ch  = st.selectbox(t["harvest_type"], list(ops_colheita.keys()), key="sel_col")
        with ch2: veic_ch = st.selectbox(t["vehicle"], ops_colheita[col_ch], key="v_col")
        use_rc = st.checkbox(t["use_ref"], key="r_col")
        rvc = REF_DIESEL.get(col_ch,{}).get(veic_ch,0.0)
        if use_rc:
            ref_box(f"{col_ch} ({veic_ch})", rvc)
            diesel_inputs[col_ch] = {veic_ch: rvc}
        else:
            vc = st.number_input(t["consumption"], min_value=0.0, format="%.2f",
                                 key="i_col", label_visibility="collapsed")
            diesel_inputs[col_ch] = {veic_ch: vc}

    section_header("Substituição por Biodiesel", "♻️")
    st.slider(t["biodiesel"], 0, 100, key="perc_bio", label_visibility="collapsed")
    perc = st.session_state.get("perc_bio",0)
    info_tag(f"🌿 {perc}% biodiesel · {100-perc}% diesel fóssil")

    st.session_state["diesel_inputs"] = diesel_inputs
    st.session_state["tipo_cultivo"]  = tipo_cultivo
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 7 · DRONE & SOLAR
# ─────────────────────────────────────────────────────────────
elif p == 7:
    top_nav("Drone & Solar")
    step_dots()
    page_header("Etapa 7 de 9", "Drone & Energia Solar",
                "Aplicações com drone e uso de energia fotovoltaica na irrigação.")

    section_header("Drone na Aplicação", "🚁")
    st.number_input(t["batteries"], min_value=0.0, format="%.2f",
                    key="qtd_bat", label_visibility="collapsed")
    st.caption("⚡ 6,216 Wh/bateria · FE SIN Brasil 0,0385 kg CO₂eq/kWh")

    section_header("Energia Solar na Irrigação", "☀️")
    st.radio(t["solar_q"], [t["yes"], t["no"]], key="solar_raw", horizontal=True, index=1)
    usa_solar = st.session_state.get("solar_raw", t["no"]) == t["yes"]
    st.session_state["usa_solar"] = usa_solar
    if usa_solar:
        st.success("✅ Emissões da energia elétrica de irrigação serão zeradas.")
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 8 · IRRIGAÇÃO
# ─────────────────────────────────────────────────────────────
elif p == 8:
    top_nav("Irrigação")
    step_dots()
    page_header("Etapa 8 de 9", "Irrigação",
                "Emissões do bombeamento via diesel ou energia elétrica da rede nacional.")

    section_header("Configuração", "💧")
    st.radio(t["irri_q"], [t["yes"], t["no"]], key="irri_yn", horizontal=True, index=1)

    em_irri   = 0.0
    usa_solar = st.session_state.get("usa_solar", False)

    if st.session_state.get("irri_yn", t["no"]) == t["yes"]:
        section_header("Parâmetros", "⚙️")
        ci1, ci2 = st.columns(2)
        with ci1: tipo_irri = st.selectbox(t["irri_type"], IRRI_OPTS[idioma], key="tipo_irri")
        with ci2:
            ger_opts = ["Diesel","Elétrica"] if idioma=="Português" else ["Diesel","Electric"]
            tipo_ger = st.selectbox(t["energy_type"], ger_opts, key="tipo_ger")
        tg_pt = tipo_ger if idioma=="Português" else ("Elétrica" if tipo_ger=="Electric" else "Diesel")
        use_ri = st.checkbox(f"📌 {t['use_ref']} — {tipo_irri}", key="irri_useref")
        if use_ri:
            em_irri = IRRI_REF.get(tipo_irri,{}).get(tg_pt,0.0)
            st.info(f"{t['ref_value']}: **{em_irri:.2f}** l ou kWh ha⁻¹ ano⁻¹")
        else:
            if tg_pt == "Diesel":
                lit     = st.number_input("⛽ Consumo diesel (l ha⁻¹ ano⁻¹)",
                                          min_value=0.0, format="%.2f", key="irri_diesel")
                em_irri = calc_diesel(lit)
            else:
                ce1, ce2, ce3 = st.columns(3)
                with ce1: hd = st.number_input(t["hours_day"],   min_value=0.0, format="%.2f", key="irri_hd")
                with ce2: ma = st.number_input(t["months_year"], min_value=0, max_value=12, key="irri_ma")
                with ce3: cv = st.number_input(t["motor_cv"],    min_value=0.1, format="%.2f",
                                               key="irri_cv", value=1.0)
                kwh     = (cv*0.7355*hd*ma*30)/0.9
                em_irri = 0.0 if usa_solar else calc_elec(kwh)
                st.info(f"Consumo: **{kwh:.1f} kWh ha⁻¹ ano⁻¹** → **{em_irri:.2f} kg CO₂eq ha⁻¹ ano⁻¹**")

    st.session_state["em_irri"] = em_irri
    nav_buttons()

# ─────────────────────────────────────────────────────────────
# PÁG 9 · PRODUTIVIDADE
# ─────────────────────────────────────────────────────────────
elif p == 9:
    top_nav("Produtividade")
    step_dots()
    page_header("Etapa 9 de 9", "Produtividade",
                "Informe a produção para calcular a emissão por unidade de produto.")

    section_header("Produção por Hectare", "📦")
    st.number_input(t["prod_label"], min_value=0.0, format="%.2f",
                    key="qtd_caixas", label_visibility="collapsed")
    qtd_cx = st.session_state.get("qtd_caixas",0.0)
    if qtd_cx > 0:
        st.markdown(f"""
        <div style="display:flex;gap:.9rem;margin-top:1.2rem;flex-wrap:wrap">
            <div style="background:rgba(198,40,40,.1);border:1px solid rgba(198,40,40,.22);
                        border-radius:14px;padding:14px 20px;flex:1;min-width:130px">
                <div style="font-size:.62rem;color:rgba(255,255,255,.32);text-transform:uppercase;
                            letter-spacing:.1em;margin-bottom:5px;font-weight:700">Produção total</div>
                <div style="font-size:1.3rem;font-weight:900;color:#ff5252">{fmt(qtd_cx*25)} kg/ha</div>
            </div>
            <div style="background:rgba(66,165,245,.08);border:1px solid rgba(66,165,245,.2);
                        border-radius:14px;padding:14px 20px;flex:1;min-width:130px">
                <div style="font-size:.62rem;color:rgba(255,255,255,.32);text-transform:uppercase;
                            letter-spacing:.1em;margin-bottom:5px;font-weight:700">Em toneladas</div>
                <div style="font-size:1.3rem;font-weight:900;color:#42a5f5">{fmt(qtd_cx*25/1000)} t/ha</div>
            </div>
            <div style="background:rgba(105,240,174,.07);border:1px solid rgba(105,240,174,.18);
                        border-radius:14px;padding:14px 20px;flex:1;min-width:130px">
                <div style="font-size:.62rem;color:rgba(255,255,255,.32);text-transform:uppercase;
                            letter-spacing:.1em;margin-bottom:5px;font-weight:700">Caixas × 25 kg</div>
                <div style="font-size:1.3rem;font-weight:900;color:#69f0ae">{fmt(qtd_cx,0)} cx/ha</div>
            </div>
        </div>""", unsafe_allow_html=True)
    nav_buttons(last=True)

# ─────────────────────────────────────────────────────────────
# PÁG 10 · RESULTADOS
# ─────────────────────────────────────────────────────────────
elif p == 10:
    top_nav("Resultados")

    # ── Recuperar valores ──
    tipo_cultivo  = st.session_state.get("tipo_cultivo","Produção")
    num_plantas   = st.session_state.get("num_plantas",20000)
    fert1_key     = st.session_state.get("fert1",FERT_KEYS[0])
    fert2_key     = st.session_state.get("fert2",FERT_KEYS[0])
    qf1           = st.session_state.get("qf1_conv",0.0)
    qf2           = st.session_state.get("qf2_conv",0.0)
    qc1           = st.session_state.get("qc1_conv",0.0)
    qc2           = st.session_state.get("qc2_conv",0.0)
    tc1_pt        = st.session_state.get("tc1_pt","Calcítico")
    tc2_pt        = st.session_state.get("tc2_pt","Calcítico")
    qest          = st.session_state.get("qest_conv",0.0)
    qcam          = st.session_state.get("qcam_conv",0.0)
    qcomp         = st.session_state.get("qcomp_conv",0.0)
    n_comp        = st.session_state.get("n_comp_val",0.0)
    diesel_inputs = st.session_state.get("diesel_inputs",{})
    perc_bio      = st.session_state.get("perc_bio",0)
    qtd_bat       = st.session_state.get("qtd_bat",0.0)
    em_irri       = st.session_state.get("em_irri",0.0)
    qtd_caixas    = st.session_state.get("qtd_caixas",0.0)

    # ── Calcular ──
    pf = (100-perc_bio)/100; pb = perc_bio/100
    em_diesel_total = 0.0; em_diesel_op = {}
    for op, d in diesel_inputs.items():
        veic = list(d.keys())[0]; val = list(d.values())[0]
        if veic in ["Triciclo","Roçadeira Motorizada"]: em = calc_gas(val)
        elif veic == "Manual": em = 0.0
        else: em = val*pf*2.604 + val*pb*0.4
        em_diesel_total += em; em_diesel_op[op] = em

    em_f1   = calc_fert((FERTILIZANTES[fert1_key]["n"]/100)*qf1, FERTILIZANTES[fert1_key]["tipo"])
    em_f2   = calc_fert((FERTILIZANTES[fert2_key]["n"]/100)*qf2, FERTILIZANTES[fert2_key]["tipo"])
    em_est  = calc_organic(qest*0.015)
    em_cam  = calc_organic(qcam*0.031)
    em_comp = calc_organic(qcomp*(n_comp/100)) if n_comp > 0 else 0.0
    em_c1   = calc_limestone(qc1, tc1_pt, tipo_cultivo)
    em_c2   = calc_limestone(qc2, tc2_pt, tipo_cultivo)
    em_drone= calc_drone(qtd_bat)
    em_total= em_f1+em_f2+em_c1+em_c2+em_est+em_cam+em_comp+em_diesel_total+em_irri+em_drone
    em_cx   = em_total/qtd_caixas      if qtd_caixas > 0 else 0.0
    em_kg   = em_total/(qtd_caixas*25) if qtd_caixas > 0 else 0.0

    # ── Header ──
    pname = st.session_state.get("prod_name","—")
    fname = st.session_state.get("farm_name","—")
    year  = st.session_state.get("year_ref",2025)
    page_header("📊 Análise Completa", "Resultados",
                f"Produtor: **{pname}** · Propriedade: **{fname}** · Ano: **{year}**")

    # ── Métricas ──
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card mc-red">
            <div class="metric-icon">🍅</div>
            <div class="metric-label">{t['total_emission']}</div>
            <div class="metric-value">{fmt(em_total)}</div>
            <div class="metric-unit">kg CO₂eq ha⁻¹ ano⁻¹</div>
        </div>
        <div class="metric-card mc-blue">
            <div class="metric-icon">📦</div>
            <div class="metric-label">{t['per_box']}</div>
            <div class="metric-value">{fmt(em_cx)}</div>
            <div class="metric-unit">kg CO₂eq caixa⁻¹</div>
        </div>
        <div class="metric-card mc-amber">
            <div class="metric-icon">⚖️</div>
            <div class="metric-label">{t['per_kg']}</div>
            <div class="metric-value">{fmt(em_kg,4)}</div>
            <div class="metric-unit">kg CO₂eq kg⁻¹</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Tabela ──
    fontes = [
        ("🧪 Fertilizante A",    fert1_key, em_f1),
        ("🧪 Fertilizante B",    fert2_key, em_f2),
        ("🪨 Calcário A",        tc1_pt,    em_c1),
        ("🪨 Calcário B",        tc2_pt,    em_c2),
        ("🐄 Esterco Bovino",    "—",       em_est),
        ("🐔 Cama de Frango",    "—",       em_cam),
        ("♻️ Composto Orgânico", "—",       em_comp),
        ("🚜 Diesel / Combust.", "—",       em_diesel_total),
        ("💧 Irrigação",         "—",       em_irri),
        ("🚁 Drone",             "—",       em_drone),
    ]
    max_v = max((v for _,_,v in fontes), default=1) or 1
    rows  = ""
    for lbl, det, val in fontes:
        pct  = (val/max_v)*100
        pct2 = (val/em_total*100) if em_total > 0 else 0
        detalhe = (f" <small style='color:rgba(255,255,255,.28);font-size:.72rem'>({det})</small>"
                   if det != "—" else "")
        rows += (f"<tr><td>{lbl}{detalhe}</td>"
                 f"<td class='em-val'>{fmt(val)}</td>"
                 f"<td><div class='em-bar-bg'>"
                 f"<div class='em-bar-fill' style='width:{pct:.1f}%'></div></div></td>"
                 f"<td class='em-pct'>{pct2:.1f}%</td></tr>")
    rows += (f"<tr class='em-total-row'><td><strong>TOTAL</strong></td>"
             f"<td class='em-val em-total-val'>{fmt(em_total)}</td>"
             f"<td></td><td class='em-pct'>100%</td></tr>")

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

    # ── Detalhamento diesel ──
    if em_diesel_total > 0:
        op_rows = "".join(
            f"<tr><td>🚜 {op}</td>"
            f"<td class='em-val'>{fmt(val)}</td>"
            f"<td><div class='em-bar-bg'><div class='em-bar-fill' "
            f"style='width:{(val/em_diesel_total*100):.1f}%;"
            f"background:linear-gradient(90deg,#e65100,#ff9800)'></div></div></td>"
            f"<td class='em-pct'>{(val/em_diesel_total*100):.1f}%</td></tr>"
            for op, val in em_diesel_op.items() if val > 0
        )
        if op_rows:
            st.markdown(f"""
            <div class="em-wrap" style="margin-top:.9rem">
                <div class="em-title">Operações Agrícolas — Combustível</div>
                <table class="em-table">
                  <thead><tr>
                    <th>Operação</th>
                    <th style="text-align:right">kg CO₂eq ha⁻¹</th>
                    <th>Proporção</th>
                    <th style="text-align:right">%</th>
                  </tr></thead>
                  <tbody>{op_rows}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)

    # ── GRÁFICO PIZZA ──
    BG  = (0.027, 0.027, 0.039)
    PAL = [
        (0.937,0.325,0.314),(1.000,0.439,0.263),(1.000,0.835,0.310),
        (0.400,0.733,0.416),(0.259,0.647,0.961),(0.671,0.278,0.737),
        (0.149,0.651,0.604),(1.000,0.541,0.396),
    ]
    grupos = {
        "Fertilizante Sintético": em_f1+em_f2,
        "Calcário":               em_c1+em_c2,
        "Esterco Bovino":         em_est,
        "Cama de Frango":         em_cam,
        "Composto Orgânico":      em_comp,
        "Combustíveis Fósseis":   em_diesel_total,
        "Irrigação":              em_irri,
        "Drone":                  em_drone,
    }
    lbls = [k for k,v in grupos.items() if v > 0.01]
    vals = [v for v in grupos.values()  if v > 0.01]

    if vals:
        st.markdown("<br>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(11,7))
        fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
        wedges, _ = ax.pie(
            vals, labels=None, startangle=140,
            explode=[0.04]*len(vals),
            colors=PAL[:len(vals)],
            wedgeprops=dict(width=0.58, edgecolor=BG, linewidth=2.5)
        )
        for i,w in enumerate(wedges):
            ang = np.deg2rad((w.theta2+w.theta1)/2)
            r   = w.r - w.width/2
            pct = vals[i]/sum(vals)*100
            if pct > 4:
                ax.text(np.cos(ang)*r, np.sin(ang)*r, f"{pct:.1f}%",
                        ha="center",va="center",fontsize=11,fontweight="bold",color="white")
        handles = [
            mpatches.Patch(facecolor=PAL[i],
                           label=f"  {lbls[i]}   {vals[i]/sum(vals)*100:.1f}%")
            for i in range(len(lbls))
        ]
        leg = ax.legend(
            handles=handles, loc="center left", bbox_to_anchor=(1.0,0.5),
            fontsize=10, title="Fontes de Emissão", title_fontsize=11,
            labelcolor=(1,1,1,1),
            facecolor=(0.08,0.08,0.11),
            edgecolor=(0.18,0.18,0.18),
            labelspacing=1.1, framealpha=1
        )
        leg.get_title().set_color((0.65,0.65,0.65,1.0))
        ax.set_title(t["chart_title"], fontsize=14, fontweight="bold", color="white", pad=20)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # ── GRÁFICO BARRAS ──
    fontes_graf = [(lbl,val) for lbl,_,val in fontes if val > 0.01]
    if fontes_graf:
        nomes   = [f[0] for f in fontes_graf]
        valores = [f[1] for f in fontes_graf]
        norm_v  = [v/max(valores) for v in valores]
        bar_cols= [(0.78+0.20*(1-n), 0.16, 0.16) for n in norm_v]

        fig3, ax3 = plt.subplots(figsize=(11, max(3.5, len(nomes)*0.6)))
        fig3.patch.set_facecolor(BG); ax3.set_facecolor(BG)
        yp = np.arange(len(nomes))
        ax3.barh(yp, valores, color=bar_cols, height=0.6,
                 edgecolor=BG, linewidth=1.5)
        ax3.set_yticks(yp)
        ax3.set_yticklabels(nomes, fontsize=10, color="white")
        ax3.set_xlabel("kg CO₂eq ha⁻¹ ano⁻¹", fontsize=9, color=(0.5,0.5,0.5))
        ax3.set_title("Emissão por Fonte", fontsize=13, fontweight="bold",
                      color="white", pad=14)
        ax3.spines[["top","right","left","bottom"]].set_visible(False)
        ax3.tick_params(axis="x", colors=(0.4,0.4,0.4), labelsize=8)
        ax3.tick_params(axis="y", length=0)
        ax3.grid(axis="x", linestyle=":", alpha=0.1, color="white")
        ax3.invert_yaxis()
        for i, v in enumerate(valores):
            ax3.text(v+max(valores)*0.01, i, fmt(v),
                     ha="left", va="center", fontsize=8.5,
                     fontweight="bold", color="white")
        plt.tight_layout()
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)

    # ── DOWNLOADS ──
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Exportar Relatório", "📥")

    dados_export = {
        "prod_name":st.session_state.get("prod_name",""),
        "farm_name":st.session_state.get("farm_name",""),
        "email":st.session_state.get("email",""),
        "phone":st.session_state.get("phone",""),
        "car":st.session_state.get("car",""),
        "region":st.session_state.get("region",""),
        "year_ref":st.session_state.get("year_ref",2025),
        "city":st.session_state.get("city",""),
        "state":st.session_state.get("state",""),
        "area_tom":st.session_state.get("area_tom",0),
        "area_farm":st.session_state.get("area_farm",0),
        "em_total":em_total,"em_cx":em_cx,"em_kg":em_kg,
        "em_f1":em_f1,"em_f2":em_f2,"em_c1":em_c1,"em_c2":em_c2,
        "em_est":em_est,"em_cam":em_cam,"em_comp":em_comp,
        "em_diesel":em_diesel_total,"em_irri":em_irri,"em_drone":em_drone,
        "diesel_op":em_diesel_op,
        "fontes":[(lbl,val) for lbl,_,val in fontes],
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    d1, d2, d3 = st.columns([1,1,1])
    with d1:
        if st.button("← Editar dados", use_container_width=True):
            go(1)
    with d2:
        st.download_button(
            label=t["download_excel"],
            data=gerar_excel(dados_export),
            file_name=f"TomateCarbon_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with d3:
        st.download_button(
            label=t["download_pdf"],
            data=gerar_pdf(dados_export),
            file_name=f"TomateCarbon_{ts}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
