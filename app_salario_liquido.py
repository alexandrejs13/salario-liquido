# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.50.15)
# Tema azul plano, multilíngue, responsivo e com STI corrigido
# (Correção Definitiva Ordem Carregamento + Sidebar Simplificada)
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import altair as alt
import requests
import base64
from typing import Dict, Any, Tuple, List
import math
import json
import os

st.set_page_config(page_title="Simulador de Salário Líquido", layout="wide")

# ======================== HELPERS INICIAIS (Formatação) =========================
def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def fmt_percent(v: float) -> str:
    if v is None: return ""
    return f"{v:.2f}%"

# Precisa da variável global `country` OU passar como parâmetro
_COUNTRY_CODE_FOR_FMT = "Brasil" # Placeholder inicial
def fmt_cap(cap_value: Any, sym: str = None) -> str:
    global _COUNTRY_CODE_FOR_FMT # Usa a global definida mais tarde
    country_code = _COUNTRY_CODE_FOR_FMT
    if cap_value is None: return "—"
    if isinstance(cap_value, str): return cap_value
    if isinstance(cap_value, (int, float)):
        if country_code == "Chile" and cap_value < 200: return f"~{cap_value:.1f} UF"
        return fmt_money(cap_value, sym if sym else "")
    return str(cap_value)

# ======================== CONSTANTES e TETOS GLOBAIS =========================
ANNUAL_CAPS = { "US_FICA": 168600.0, "US_SUTA_BASE": 7000.0, "CA_CPP_YMPEx1": 68500.0, "CA_CPP_YMPEx2": 73200.0, "CA_CPP_EXEMPT": 3500.0, "CA_EI_MIE": 63200.0, "CL_TETO_UF": 84.3, "CL_TETO_CESANTIA_UF": 126.6, }
UMA_DIARIA_MX = 108.57
MX_IMSS_CAP_MONTHLY = 25 * UMA_DIARIA_MX * 30.4

# ======================== CARREGAMENTO DE CONFIGS JSON LOCAIS =========================
CONFIG_DIR = "."
I18N_FILE = os.path.join(CONFIG_DIR, "i18n.json")
COUNTRIES_FILE = os.path.join(CONFIG_DIR, "countries.json")
STI_CONFIG_FILE = os.path.join(CONFIG_DIR, "sti_config.json")
US_STATES_FILE = os.path.join(CONFIG_DIR, "us_state_tax_rates.json")
COUNTRY_TABLES_FILE = os.path.join(CONFIG_DIR, "country_tables.json")
BR_INSS_FILE = os.path.join(CONFIG_DIR, "br_inss.json")
BR_IRRF_FILE = os.path.join(CONFIG_DIR, "br_irrf.json")

def load_json(filepath, default_value={}):
    if not os.path.exists(filepath):
        print(f"Warning: Config file not found: {filepath}. Using default.")
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default_value

# --- Fallbacks Mínimos ---
I18N_FALLBACK = {"Português": {"app_title": "Simulador (Fallback)", "sidebar_title": "Simulador (Fallback)", "language_title": "Idioma", "country": "País", "menu_title": "Menu", "choose_country": "Escolha"}}
COUNTRIES_FALLBACK = {"countries": {"Brasil": {"symbol": "R$", "flag": "🇧🇷", "valid_from": "N/A", "benefits": {"ferias": True, "decimo": True}}}}
STI_CONFIG_FALLBACK = {"STI_RANGES": {}, "STI_LEVEL_OPTIONS": {}}
US_STATE_RATES_FALLBACK = {"No State Tax": 0.0}
BR_INSS_FALLBACK = {}
BR_IRRF_FALLBACK = {}
COUNTRY_TABLES_FALLBACK = {"TABLES": {}, "EMPLOYER_COST": {}, "REMUN_MONTHS": {}}

# --- Carrega Configurações Essenciais PRIMEIRO ---
I18N = load_json(I18N_FILE, I18N_FALLBACK)
COUNTRIES_DATA = load_json(COUNTRIES_FILE, COUNTRIES_FALLBACK)
COUNTRIES = COUNTRIES_DATA.get("countries", {})

# --- Carrega o Restante ---
STI_CONFIG = load_json(STI_CONFIG_FILE, STI_CONFIG_FALLBACK)
US_STATE_RATES = load_json(US_STATES_FILE, US_STATE_RATES_FALLBACK)
BR_INSS_TBL = load_json(BR_INSS_FILE, BR_INSS_FALLBACK)
BR_IRRF_TBL = load_json(BR_IRRF_FILE, BR_IRRF_FALLBACK)
COUNTRY_TABLES_DATA = load_json(COUNTRY_TABLES_FILE, COUNTRY_TABLES_FALLBACK)

# --- Extrai Dados Carregados ---
COUNTRY_BENEFITS = {k: v.get("benefits", {}) for k, v in COUNTRIES.items()}
STI_RANGES = STI_CONFIG.get("STI_RANGES", {})
STI_LEVEL_OPTIONS = STI_CONFIG.get("STI_LEVEL_OPTIONS", {})
TABLES_DEFAULT = COUNTRY_TABLES_DATA.get("TABLES", {})
EMPLOYER_COST_DEFAULT = COUNTRY_TABLES_DATA.get("EMPLOYER_COST", {})
REMUN_MONTHS_DEFAULT = COUNTRY_TABLES_DATA.get("REMUN_MONTHS", {})
CA_CPP_EI_DEFAULT = { "cpp_rate": 0.0595, "cpp_exempt_monthly": ANNUAL_CAPS["CA_CPP_EXEMPT"] / 12.0, "cpp_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx1"] / 12.0, "cpp2_rate": 0.04, "cpp2_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx2"] / 12.0, "ei_rate": 0.0163, "ei_cap_monthly": ANNUAL_CAPS["CA_EI_MIE"] / 12.0 }

# Função load_tables simplificada
def load_tables_data(): # Renomeado para evitar conflito com a função de load
    country_tables_dict = {
        "TABLES": COUNTRY_TABLES_DATA.get("TABLES", {}),
        "EMPLOYER_COST": COUNTRY_TABLES_DATA.get("EMPLOYER_COST", {}),
        "REMUN_MONTHS": COUNTRY_TABLES_DATA.get("REMUN_MONTHS", {})
    }
    return US_STATE_RATES, country_tables_dict, BR_INSS_TBL, BR_IRRF_TBL


# ============================== CSS ================================
# (CSS como na v2025.50.8)
st.markdown("""
<style>
/* ... (Todo o CSS da v2025.50.8 aqui) ... */
html, body { font-family:'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:2px; background:linear-gradient(to right, #0a3d62, #e2e6ea); margin:32px 0; border-radius:1px; }
section[data-testid="stSidebar"]{ background:#0a3d62 !important; padding-top:15px; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span { color:#ffffff !important; }
section[data-testid="stSidebar"] h2 { margin-bottom: 25px !important; }
section[data-testid="stSidebar"] h3 { margin-bottom: 0.5rem !important; margin-top: 1rem !important; }
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label { margin-bottom: 0.5rem !important; }
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div[data-baseweb="select"] { margin-top: 0 !important; }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox input,
section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{ color:#0b1f33 !important; background:#fff !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span { color: #ffffff !important; }
.metric-card{ background:#fff; border-radius:10px; box-shadow:0 1px 4px rgba(0,0,0,.06); padding: 8px 12px; text-align:center; transition: all 0.3s ease; min-height: 95px; display: flex; flex-direction: column; justify-content: center; border-left: 5px solid #ccc; }
.metric-card:hover{ box-shadow:0 6px 16px rgba(0,0,0,0.1); transform: translateY(-2px); }
.metric-card h4{ margin:0; font-size:17px; font-weight: 600; color:#0a3d62; }
.metric-card h3{ margin: 2px 0 0; color:#0a3d62; font-size:17px; font-weight: 700; }
.table-wrap{ background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }
.country-header{ display:flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 5px; }
.country-flag{ font-size:45px; }
.country-title{ font-size:36px; font-weight:700; color:#0a3d62; }
.vega-embed{ padding-bottom: 16px; }
.annual-card-base { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.06); padding: 8px 12px; margin-bottom: 1rem; border-left: 5px solid #0a3d62; min-height: 95px; display: flex; flex-direction: column; justify-content: center; box-sizing: border-box; }
.annual-card-label { align-items: flex-start; }
.annual-card-value { align-items: flex-end; }
.annual-card-label h4,
.annual-card-value h3 { margin: 0; font-size: 17px; color: #0a3d62; }
.annual-card-label h4 { font-weight: 600; }
.annual-card-value h3 { font-weight: 700; }
.annual-card-label .sti-note { display: block; font-size: 14px; font-weight: 400; line-height: 1.3; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ============================== (Restante dos HELPERS - Cálculo) ===============================
# (Funções: get_sti_range, calc_inss_progressivo, etc. como antes)
def get_sti_range(area: str, level: str) -> Tuple[float, float]:
    area_tbl = STI_RANGES.get(area, {})
    rng = area_tbl.get(level)
    return rng if rng else (0.0, None)

def calc_inss_progressivo(salario: float, inss_tbl: Dict[str, Any]) -> float:
    # Adiciona verificação se inss_tbl é dicionário
    if not isinstance(inss_tbl, dict): return 0.0
    contrib = 0.0; limite_anterior = 0.0
    for faixa in inss_tbl.get("faixas", []):
        teto_faixa = float(faixa["ate"]); aliquota = float(faixa["aliquota"])
        if salario > limite_anterior:
            base_faixa = min(salario, teto_faixa) - limite_anterior
            contrib += base_faixa * aliquota
            limite_anterior = teto_faixa
        else: break
    teto = inss_tbl.get("teto_contribuicao", None)
    if teto is not None: contrib = min(contrib, float(teto))
    return max(contrib, 0.0)

def calc_irrf(base: float, dep: int, irrf_tbl: Dict[str, Any]) -> float:
    if not isinstance(irrf_tbl, dict) or "deducao_dependente" not in irrf_tbl: return 0.0
    ded_dep = float(irrf_tbl.get("deducao_dependente", 0.0))
    base_calc = max(base - ded_dep * max(int(dep), 0), 0.0)
    for faixa in irrf_tbl.get("faixas", []):
        if base_calc <= float(faixa["ate"]):
            aliq = float(faixa["aliquota"]); ded = float(faixa.get("deducao", 0.0))
            return max(base_calc * aliq - ded, 0.0)
    return 0.0

def br_net(salary: float, dependentes: int, other_deductions: float, br_inss_tbl: Dict[str, Any], br_irrf_tbl: Dict[str, Any]):
    lines = []; total_earn = salary
    inss = calc_inss_progressivo(salary, br_inss_tbl)
    base_ir = max(salary - inss, 0.0)
    irrf = calc_irrf(base_ir, dependentes, br_irrf_tbl)
    lines.append(("Salário Base", salary, 0.0)); lines.append(("INSS", 0.0, inss)); lines.append(("IRRF", 0.0, irrf))
    if other_deductions > 0: lines.append(("Outras Deduções", 0.0, other_deductions))
    total_ded = inss + irrf + other_deductions
    fgts_value = salary * 0.08; net = total_earn - total_ded
    return lines, total_earn, total_ded, net, fgts_value

def generic_net(salary: float, other_deductions: float, rates: Dict[str, float], country_code: str):
    lines = [("Base", salary, 0.0)]; total_earn = salary; total_ded = 0.0
    for k, aliq in rates.items():
        if (k == "CPP2" and country_code == "Canadá") or \
           (country_code == "México" and k in ["ISR_Simplificado", "IMSS_Simplificado"]): continue
        v = salary * float(aliq); total_ded += v; lines.append((k, 0.0, v))
    if other_deductions > 0: lines.append(("Outras Deduções", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def us_net(salary: float, other_deductions: float, state_code: str, state_rate: float):
    FICA_WAGE_BASE_MONTHLY = ANNUAL_CAPS["US_FICA"] / 12.0
    lines = [("Base Pay", salary, 0.0)]; total_earn = salary
    salario_base_fica = min(salary, FICA_WAGE_BASE_MONTHLY); fica = salario_base_fica * 0.062
    medicare = salary * 0.0145; total_ded = fica + medicare
    lines += [("FICA (Social Security)", 0.0, fica), ("Medicare", 0.0, medicare)]
    if state_code:
        sr = state_rate if state_rate is not None else 0.0
        if sr > 0: sttax = salary * sr; total_ded += sttax; lines.append((f"State Tax ({state_code})", 0.0, sttax))
    if other_deductions > 0: lines.append(("Other Deductions", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def ca_net(salary: float, other_deductions: float, ca_tbl: Dict[str, Any]):
    lines = [("Base Pay", salary, 0.0)]; total_earn = salary
    cpp_base = max(0, min(salary, ca_tbl["cpp_cap_monthly"]) - ca_tbl["cpp_exempt_monthly"]); cpp = cpp_base * ca_tbl["cpp_rate"]
    cpp2_base = max(0, min(salary, ca_tbl["cpp2_cap_monthly"]) - ca_tbl["cpp_cap_monthly"]); cpp2 = cpp2_base * ca_tbl["cpp2_rate"]
    ei_base = min(salary, ca_tbl["ei_cap_monthly"]); ei = ei_base * ca_tbl["ei_rate"]
    income_tax = salary * 0.15 # Simplificado
    total_ded = cpp + cpp2 + ei + income_tax
    lines.append(("CPP", 0.0, cpp)); lines.append(("CPP2", 0.0, cpp2)); lines.append(("EI", 0.0, ei)); lines.append(("Income Tax (Est.)", 0.0, income_tax))
    if other_deductions > 0: lines.append(("Other Deductions", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def mx_net(salary: float, other_deductions: float, tables_ext: Dict[str, Any]):
    lines = [("Base", salary, 0.0)]; total_earn = salary; total_ded = 0.0
    if not tables_ext or "TABLES" not in tables_ext or "México" not in tables_ext["TABLES"]:
        rates = TABLES_DEFAULT.get("México", {}).get("rates", {})
    else:
        rates = tables_ext.get("TABLES", {}).get("México", {}).get("rates", {})
    imss_rate = rates.get("IMSS_Simplificado", 0.05)
    isr_rate = rates.get("ISR_Simplificado", 0.15)
    imss_base = min(salary, MX_IMSS_CAP_MONTHLY)
    imss = imss_base * imss_rate; total_ded += imss
    lines.append(("IMSS (Est.)", 0.0, imss))
    isr = (salary - imss) * isr_rate # Simplificado
    total_ded += isr
    lines.append(("ISR (Est.)", 0.0, isr))
    if other_deductions > 0: lines.append(("Otras Deducciones", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def calc_country_net(country_code: str, salary: float, other_deductions: float, state_code=None, state_rate=None, dependentes=0, tables_ext=None, br_inss_tbl=None, br_irrf_tbl=None):
    # Passa country_code para as funções internas se necessário
    if country_code == "Brasil":
        lines, te, td, net, fgts = br_net(salary, dependentes, other_deductions, br_inss_tbl, br_irrf_tbl)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": fgts}
    elif country_code == "Estados Unidos":
        lines, te, td, net = us_net(salary, other_deductions, state_code, state_rate)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    elif country_code == "Canadá":
        lines, te, td, net = ca_net(salary, other_deductions, CA_CPP_EI_DEFAULT)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    elif country_code == "México":
        lines, te, td, net = mx_net(salary, other_deductions, tables_ext)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    else:
        rates = (tables_ext or {}).get("TABLES", {}).get(country_code, {}).get("rates", {})
        if not rates: rates = TABLES_DEFAULT.get(country_code, {}).get("rates", {})
        lines, te, td, net = generic_net(salary, other_deductions, rates, country_code)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}

def calc_employer_cost(country_code: str, salary: float, bonus: float, T: Dict[str, str], tables_ext=None):
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(country_code, REMUN_MONTHS_DEFAULT.get(country_code, 12.0))
    if not tables_ext or "EMPLOYER_COST" not in tables_ext or country_code not in tables_ext["EMPLOYER_COST"]:
        enc_list = EMPLOYER_COST_DEFAULT.get(country_code, [])
    else:
        enc_list = tables_ext.get("EMPLOYER_COST", {}).get(country_code, [])

    benefits = COUNTRY_BENEFITS.get(country_code, {"ferias": False, "decimo": False})

    df = pd.DataFrame(enc_list)
    df_display = pd.DataFrame()
    if not df.empty:
        df_display = df.copy()
        df_display[T["cost_header_charge"]] = df_display["nome"]
        df_display[T["cost_header_percent"]] = df_display["percentual"].apply(lambda p: f"{p:.2f}%")
        df_display[T["cost_header_base"]] = df_display["base"]
        df_display[T["cost_header_obs"]] = df_display.apply(lambda row: fmt_cap(row.get('teto'), COUNTRIES[country_code]['symbol'], country_code) if row.get('teto') is not None else row['obs'], axis=1)
        df_display[T["cost_header_bonus"]] = ["✅" if b else "❌" for b in df_display["bonus"]]
        cols = [T["cost_header_charge"], T["cost_header_percent"], T["cost_header_base"], T["cost_header_bonus"], T["cost_header_obs"]]
        if benefits.get("ferias", False): df_display[T["cost_header_vacation"]] = ["✅" if b else "❌" for b in df_display["ferias"]]; cols.insert(3, T["cost_header_vacation"])
        if benefits.get("decimo", False): df_display[T["cost_header_13th"]] = ["✅" if b else "❌" for b in df_display["decimo"]]; insert_pos = 4 if benefits.get("ferias", False) else 3; cols.insert(insert_pos, T["cost_header_13th"])
        df_display = df_display[cols]

    salario_anual_base = salary * 12.0; salario_anual_beneficios = salary * months; total_cost_items = []
    for index, item in df.iterrows():
        perc = item.get("percentual", 0.0) / 100.0; teto = item.get("teto"); incide_bonus = item.get("bonus", False)
        base_calc_anual = salario_anual_base if country_code in ["Estados Unidos", "Canadá"] else salario_anual_beneficios
        if incide_bonus: base_calc_anual += bonus
        if teto is not None and isinstance(teto, (int, float)):
            if country_code == "Chile" and isinstance(teto, float) and teto < 200: pass
            elif item.get("nome") == "CPP2 (ER)": base_calc_anual = max(0, min(base_calc_anual, teto) - min(base_calc_anual, ANNUAL_CAPS["CA_CPP_YMPEx1"]))
            else: base_calc_anual = min(base_calc_anual, teto)
        custo_item = base_calc_anual * perc; total_cost_items.append(custo_item)
    total_encargos = sum(total_cost_items); custo_total_anual = (salary * months) + bonus + total_encargos
    mult = (custo_total_anual / salario_anual_base) if salario_anual_base > 0 else 0.0
    return custo_total_anual, mult, df_display, months

def get_sti_area_map(T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    display_list = [T["sti_area_non_sales"], T["sti_area_sales"]]; keys = ["Non Sales", "Sales"]
    return display_list, dict(zip(display_list, keys))

def get_sti_level_map(area: str, T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    keys = STI_LEVEL_OPTIONS.get(area, []); display_list = [T.get(STI_I18N_KEYS.get(key, ""), key) for key in keys]
    return display_list, dict(zip(display_list, keys))

# ============================== SIDEBAR ===============================
with st.sidebar:
    # Seleciona Idioma Primeiro
    st.markdown(f"<h3 style='margin-bottom: 0.5rem;'>{I18N['Português']['language_title']}</h3>", unsafe_allow_html=True)
    idioma = st.selectbox(label="Language Select", options=list(I18N.keys()), index=0, key="lang_select", label_visibility="collapsed")
    T = I18N[idioma] # Define T baseado na seleção

    # Renderiza Título da Sidebar Traduzido
    st.markdown(f"<h2 style='color:white; text-align:center; font-size:20px; margin-bottom: 25px;'>{T.get('sidebar_title', 'Simulador')}</h2>", unsafe_allow_html=True)

    st.markdown(f"<h3 style='margin-bottom: 0.5rem;'>{T.get('country', 'País')}</h3>", unsafe_allow_html=True)
    country_options = list(COUNTRIES.keys()) if COUNTRIES else ["Brasil"]
    default_country = "Brasil" if "Brasil" in country_options else (country_options[0] if country_options else None)
    # Tenta encontrar o índice do país atual no estado, senão usa o default
    try:
        current_country_index = country_options.index(st.session_state.get('country_select', default_country))
    except ValueError:
        current_country_index = country_options.index(default_country) if default_country in country_options else 0

    country = st.selectbox(T.get("choose_country", "Selecione"), country_options, index=current_country_index, key="country_select", label_visibility="collapsed")
    # Atualiza a variável global usada em fmt_cap
    _COUNTRY_CODE_FOR_FMT = country


    st.markdown(f"<h3 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>{T.get('menu_title', 'Menu')}</h3>", unsafe_allow_html=True)
    menu_options = [T.get("menu_calc", "Calc"), T.get("menu_rules", "Rules"), T.get("menu_rules_sti", "STI Rules"), T.get("menu_cost", "Cost")]

    # Garante que o menu ativo exista nas opções atuais (após mudança de idioma)
    if 'active_menu' not in st.session_state or st.session_state.active_menu not in menu_options:
         st.session_state.active_menu = menu_options[0]

    # Encontra o índice correto do menu ativo nas opções traduzidas
    try:
        active_menu_index = menu_options.index(st.session_state.active_menu)
    except ValueError:
        active_menu_index = 0 # Default para o primeiro item se não encontrar
        st.session_state.active_menu = menu_options[0]


    active_menu = st.radio(
        label="Menu Select",
        options=menu_options,
        key="menu_radio_select",
        label_visibility="collapsed",
        index=active_menu_index
    )
    if active_menu != st.session_state.active_menu:
        st.session_state.active_menu = active_menu
        st.rerun()

    # REQ 5: Mapa Removido

# Carrega tabelas restantes
US_STATE_RATES_LOADED, COUNTRY_TABLES_LOADED, BR_INSS_TBL_LOADED, BR_IRRF_TBL_LOADED = load_tables_data() # Usa a função renomeada

# Atualiza globais
COUNTRY_TABLES = COUNTRY_TABLES_LOADED

# --- Dados Globais do País Selecionado ---
# Verifica se `country` existe em `COUNTRIES` antes de acessar
if country not in COUNTRIES:
    st.error(f"Erro interno: País '{country}' não encontrado nos dados carregados.")
    st.stop()

symbol = COUNTRIES[country]["symbol"]
flag = COUNTRIES[country]["flag"]
valid_from = COUNTRIES[country]["valid_from"]
active_menu = st.session_state.active_menu

# ======================= TÍTULO DINÂMICO ==============================
if active_menu == T.get("menu_calc"): title = T.get("title_calc", "Calculator")
elif active_menu == T.get("menu_rules"): title = T.get("title_rules", "Rules")
elif active_menu == T.get("menu_rules_sti"): title = T.get("title_rules_sti", "STI Rules")
else: title = T.get("title_cost", "Cost")

st.markdown(f"<div class='country-header'><div class='country-title'>{title}</div><div class='country-flag'>{flag}</div></div>", unsafe_allow_html=True)
st.write("---")

# ========================= SIMULADOR DE REMUNERAÇÃO ==========================
if active_menu == T.get("menu_calc"):
    area_options_display, area_display_map = get_sti_area_map(T)
    st.subheader(T.get("calc_params_title", "Parameters"))

    if country == "Brasil":
        cols = st.columns([2, 1, 1.2, 1.6, 1.6, 2.4])
        salario = cols[0].number_input(f"{T.get('salary', 'Salary')} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"))
        dependentes = cols[1].number_input(f"{T.get('dependents', 'Dependents')}", min_value=0, value=0, step=1, key="dep_input", help=T.get("dependents_tooltip"))
        other_deductions = cols[2].number_input(f"{T.get('other_deductions', 'Other Ded.')} ({symbol})", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"))
        bonus_anual = cols[3].number_input(f"{T.get('bonus', 'Bonus')} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"))
        area_display = cols[4].selectbox(T.get("area", "Area"), area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"))
        area = area_display_map.get(area_display, "Non Sales") # Fallback
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = cols[5].selectbox(T.get("level", "Level"), level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"))
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others") # Fallback
        state_code, state_rate = None, None
    elif country == "Estados Unidos":
        c1, c2, c3, c4, c5 = st.columns([2, 1.4, 1.2, 1.2, 1.4])
        salario = c1.number_input(f"{T.get('salary', 'Salary')} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"))
        state_code = c2.selectbox(f"{T.get('state', 'State')}", list(US_STATE_RATES.keys()), index=0, key="state_select_main")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input(f"{T.get('state_rate', 'Rate')}", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input")
        other_deductions = c4.number_input(f"{T.get('other_deductions', 'Other Ded.')} ({symbol})", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"))
        bonus_anual = c5.number_input(f"{T.get('bonus', 'Bonus')} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"))
        r1, r2 = st.columns([1.2, 2.2])
        area_display = r1.selectbox(T.get("area", "Area"), area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"))
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox(T.get("level", "Level"), level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"))
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes = 0
    else: # Outros países
        c1, c2, c3 = st.columns([2, 1.2, 1.6])
        salario = c1.number_input(f"{T.get('salary', 'Salary')} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"))
        other_deductions = c2.number_input(f"{T.get('other_deductions', 'Other Ded.')} ({symbol})", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"))
        bonus_anual = c3.number_input(f"{T.get('bonus', 'Bonus')} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"))
        r1, r2 = st.columns([1.2, 2.2])
        area_display = r1.selectbox(T.get("area", "Area"), area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"))
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox(T.get("level", "Level"), level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"))
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes = 0
        state_code, state_rate = None, None

    st.subheader(T.get("monthly_comp_title", "Monthly Comp"))

    # Passa other_deductions para a função de cálculo
    calc = calc_country_net(country, salario, other_deductions, state_code=state_code, state_rate=state_rate, dependentes=dependentes, tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL)
    df_detalhe = pd.DataFrame(calc["lines"], columns=["Descrição", T.get("earnings","Earnings"), T.get("deductions","Deductions")])
    df_detalhe[T.get("earnings","Earnings")] = df_detalhe[T.get("earnings","Earnings")].apply(lambda v: money_or_blank(v, symbol))
    df_detalhe[T.get("deductions","Deductions")] = df_detalhe[T.get("deductions","Deductions")].apply(lambda v: money_or_blank(v, symbol))
    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True); st.table(df_detalhe); st.markdown("</div>", unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(f"<div class='metric-card' style='border-left-color: #28a745; background: #e6ffe6;'><h4>💰 {T.get('tot_earnings','Total Earnings')}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card' style='border-left-color: #dc3545; background: #ffe6e6;'><h4>📉 {T.get('tot_deductions','Total Deductions')}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card' style='border-left-color: #007bff; background: #e6f7ff;'><h4>💵 {T.get('net','Net Salary')}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)

    st.write("")
    if country == "Brasil": st.markdown(f"**💼 {T.get('fgts_deposit','FGTS')}:** {fmt_money(calc['fgts'], symbol)}")

    st.write("---")
    st.subheader(T.get("annual_comp_title", "Annual Comp"))
    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0
    pct_txt = f"{bonus_pct*100:.1f}%"
    faixa_txt = f"≤ {(max_pct or 0)*100:.0f}%" if level == "Others" else f"{min_pct*100:.0f}% – {max_pct*100:.0f}%"
    dentro = (bonus_pct <= (max_pct or 0)) if level == "Others" else (min_pct <= bonus_pct <= max_pct)
    cor = "#1976d2" if dentro else "#d32f2f"; status_txt = T.get("sti_in_range", "In") if dentro else T.get("sti_out_range", "Out"); bg_cor = "#e6f7ff" if dentro else "#ffe6e6"
    sti_line = f"STI ratio do bônus: <strong>{pct_txt}</strong> — <strong>{status_txt}</strong> ({faixa_txt}) — <em>{area_display} • {level_display}</em>"

    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='annual-card-base annual-card-label' style='border-left-color: #28a745; background: #e6ffe6;'><h4>{T.get('annual_salary','Annual Sal.')}</h4><span class='sti-note'>({T.get('months_factor','Months')}: {months})</span></div>", unsafe_allow_html=True)
    c1.markdown(f"<div class='annual-card-base annual-card-label' style='border-left-color: {cor}; background: {bg_cor};'><h4>{T.get('annual_bonus','Annual Bonus')}</h4><span class='sti-note' style='color:{cor}'>{sti_line}</span></div>", unsafe_allow_html=True)
    c1.markdown(f"<div class='annual-card-base annual-card-label' style='border-left-color: #0a3d62; background: #e6f0f8;'><h4>{T.get('annual_total','Annual Total')}</h4></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='annual-card-base annual-card-value' style='border-left-color: #28a745; background: #e6ffe6;'><h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='annual-card-base annual-card-value' style='border-left-color: {cor}; background: {bg_cor};'><h3>{fmt_money(bonus_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='annual-card-base annual-card-value' style='border-left-color: #0a3d62; background: #e6f0f8;'><h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True)

    st.write("---")
    st.subheader(T.get("pie_chart_title_dist", "Distribution"))
    chart_df = pd.DataFrame({"Componente": [T.get('annual_salary','Annual Sal.').split(" (")[0], T.get('annual_bonus','Annual Bonus')], "Valor": [salario_anual, bonus_anual]})
    base = alt.Chart(chart_df).transform_joinaggregate(Total="sum(Valor)").transform_calculate(Percent="datum.Valor / datum.Total")
    pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(theta=alt.Theta("Valor:Q", stack=True), color=alt.Color("Componente:N", legend=alt.Legend(orient="bottom", direction="horizontal", title=None, labelLimit=250, labelFontSize=15, symbolSize=90)), tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f"), alt.Tooltip("Percent:Q", format=".1%"),])
    labels = base.transform_filter(alt.datum.Percent >= 0.01).mark_text(radius=80, fontWeight="bold", color="white").encode(theta=alt.Theta("Valor:Q", stack=True), text=alt.Text("Percent:Q", format=".1%"))
    chart = alt.layer(pie, labels).properties(title="").configure_legend(orient="bottom", title=None, labelLimit=250).configure_view(strokeWidth=0).resolve_scale(color='independent')
    st.altair_chart(chart, use_container_width=True)

# =========================== REGRAS DE CONTRIBUIÇÕES ===================
elif active_menu == T.get("menu_rules"):
    st.subheader(T.get("rules_expanded", "Details"))
    # (Estrutura de dados das tabelas br_emp_contrib, etc. como na v2025.50.8)
    br_emp_contrib = [ {"desc": "INSS", "rate": "7.5% - 14% (Prog.)", "base": "Salário Bruto", "obs": f"Teto Base {fmt_money(BR_INSS_TBL.get('teto_base', 0), 'R$')}, Teto Contrib. {fmt_money(BR_INSS_TBL.get('teto_contribuicao', 0), 'R$')}"}, {"desc": "IRRF", "rate": "0% - 27.5% (Prog.)", "base": "Salário Bruto - INSS - Dep.", "obs": f"Ded. Dep. {fmt_money(BR_IRRF_TBL.get('deducao_dependente', 0), 'R$')}"} ]
    br_er_contrib = [ {"desc": "INSS Patronal", "rate": "20.00%", "base": "Folha", "obs": "Regra Geral"}, {"desc": "RAT/FAP", "rate": "~2.00%", "base": "Folha", "obs": "Varia (1% a 3%)"}, {"desc": "Sistema S", "rate": "~5.80%", "base": "Folha", "obs": "Terceiros"}, {"desc": "FGTS", "rate": "8.00%", "base": "Folha", "obs": "Depósito (Custo)"} ]
    us_emp_contrib = [ {"desc": "FICA (Social Sec.)", "rate": "6.20%", "base": "Sal. Bruto", "obs": f"Teto Anual {fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}"}, {"desc": "Medicare", "rate": "1.45%", "base": "Sal. Bruto", "obs": "Sem teto"}, {"desc": "State Tax", "rate": "Varia (0-8%+)","base": "Sal. Bruto", "obs": "Depende do Estado"} ]
    us_er_contrib = [ {"desc": "FICA Match", "rate": "6.20%", "base": "Sal. Bruto", "obs": f"Teto Anual {fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}"}, {"desc": "Medicare Match", "rate": "1.45%", "base": "Sal. Bruto", "obs": "Sem teto"}, {"desc": "SUTA/FUTA", "rate": "~2.00%", "base": "Sal. Bruto", "obs": f"Teto Base ~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}"} ]
    ca_emp_contrib = [ {"desc": "CPP", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp_rate']*100), "base": "Sal. Bruto (c/ Isenção)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}"}, {"desc": "CPP2", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp2_rate']*100), "base": "Sal. Bruto (pós Teto 1)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}"}, {"desc": "EI", "rate": fmt_percent(CA_CPP_EI_DEFAULT['ei_rate']*100), "base": "Sal. Bruto", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}"}, {"desc": "Income Tax", "rate": "Prog. Federal+Prov.", "base": "Renda Tributável", "obs": "Complexo"} ]
    ca_er_contrib = [ {"desc": "CPP Match", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp_rate']*100), "base": "Sal. Bruto (c/ Isenção)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}"}, {"desc": "CPP2 Match", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp2_rate']*100), "base": "Sal. Bruto (pós Teto 1)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}"}, {"desc": "EI Match", "rate": fmt_percent(CA_CPP_EI_DEFAULT['ei_rate']*100 * 1.4), "base": "Sal. Bruto", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}"} ]
    mx_emp_contrib = [{"desc": "ISR", "rate": "~15% (Simpl.)", "base": "Sal. Bruto", "obs": "Progressivo"}, {"desc": "IMSS", "rate": "~5% (Simpl.)", "base": "Sal. Bruto", "obs": f"Com Teto (~{fmt_money(MX_IMSS_CAP_MONTHLY, 'MX$')} /mês)"}]
    mx_er_contrib = [{"desc": "IMSS", "rate": "~7% (Simpl.)", "base": "SBC", "obs": "Complexo"}, {"desc": "INFONAVIT", "rate": "5.00%", "base": "SBC", "obs": "Habitação"}, {"desc": "SAR", "rate": "2.00%", "base": "SBC", "obs": "Aposentadoria"}, {"desc": "ISN", "rate": "~2.5%", "base": "Folha", "obs": "Imposto Estadual"}]
    cl_emp_contrib = [{"desc": "AFP", "rate": "~11.15%", "base": "Sal. Bruto", "obs": f"10% + Comissão (Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF)"}, {"desc": "Saúde", "rate": "7.00%", "base": "Sal. Bruto", "obs": f"Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF"}]
    cl_er_contrib = [{"desc": "Seg. Cesantía", "rate": "2.40%", "base": "Sal. Bruto", "obs": f"Teto {ANNUAL_CAPS['CL_TETO_CESANTIA_UF']:.1f} UF"}, {"desc": "SIS", "rate": "1.53%", "base": "Sal. Bruto", "obs": f"Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF"}]
    ar_emp_contrib = [{"desc": "Jubilación", "rate": "11.00%", "base": "Sal. Bruto", "obs": "Com Teto"}, {"desc": "Obra Social", "rate": "3.00%", "base": "Sal. Bruto", "obs": "Com Teto"}, {"desc": "PAMI", "rate": "3.00%", "base": "Sal. Bruto", "obs": "Com Teto"}]
    ar_er_contrib = [{"desc": "Cargas Sociales", "rate": "~23.50%", "base": "Sal. Bruto", "obs": "Com Teto (Média)"}]
    co_emp_contrib = [{"desc": "Salud", "rate": "4.00%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Pensión", "rate": "4.00%", "base": "Sal. Bruto", "obs": "-"}]
    co_er_contrib = [{"desc": "Salud", "rate": "8.50%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Pensión", "rate": "12.00%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Parafiscales", "rate": "9.00%", "base": "Sal. Bruto", "obs": "SENA, ICBF, Caja"}, {"desc": "Cesantías", "rate": "8.33%", "base": "Sal. Bruto", "obs": "1 Salário/Ano"}]
    country_contrib_map = { "Brasil": (br_emp_contrib, br_er_contrib), "Estados Unidos": (us_emp_contrib, us_er_contrib), "Canadá": (ca_emp_contrib, ca_er_contrib), "México": (mx_emp_contrib, mx_er_contrib), "Chile": (cl_emp_contrib, cl_er_contrib), "Argentina": (ar_emp_contrib, ar_er_contrib), "Colômbia": (co_emp_contrib, co_er_contrib), }
    official_links = { "Brasil": "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/tributos/contribuicoes-previdenciarias", "Estados Unidos": "https://www.irs.gov/businesses/small-businesses-self-employed/employment-tax-rates", "Canadá": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/payroll-deductions-contributions/canada-pension-plan-cpp/cpp-contribution-rates-maximums-exemptions.html", "México": "https://www.sat.gob.mx/consulta/29124/conoce-las-tablas-de-isr", "Chile": "https://www.previred.com/indicadores-previsionales/", "Argentina": "https://www.afip.gob.ar/aportesycontribuciones/", "Colômbia": "https://www.dian.gov.co/normatividad/Paginas/Normatividad.aspx", }

    emp_contrib_data, er_contrib_data = country_contrib_map.get(country, ([], []))
    link = official_links.get(country, "#")
    col_map = { "desc": T["rules_table_desc"], "rate": T["rules_table_rate"], "base": T["rules_table_base"], "obs": T["rules_table_obs"] }
    df_emp = pd.DataFrame(emp_contrib_data).rename(columns=col_map) if emp_contrib_data else pd.DataFrame()
    df_er = pd.DataFrame(er_contrib_data).rename(columns=col_map) if er_contrib_data else pd.DataFrame()

    if not df_emp.empty: st.markdown(f"#### {T['rules_emp']}"); st.dataframe(df_emp, use_container_width=True, hide_index=True)
    if not df_er.empty: st.markdown(f"#### {T['rules_er']}"); st.dataframe(df_er, use_container_width=True, hide_index=True)
    st.markdown("---")

    # --- Explicações Detalhadas ---
    # (Textos detalhados aqui, como na v2025.50.9)
    if country == "Brasil":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **INSS:** Calculado de forma progressiva sobre faixas salariais (7.5% a 14%). A contribuição total é a soma do valor calculado em cada faixa, limitada ao teto de contribuição.\n- **IRRF:** Calculado sobre o Salário Bruto após deduzir o INSS e um valor fixo por dependente. Aplica-se a alíquota da faixa (0% a 27.5%) e subtrai-se a parcela a deduzir.\n\n**{T["rules_er"]} - Explicação:**\n- **INSS Patronal, RAT, Sistema S:** Percentuais aplicados sobre o total da folha.\n- **FGTS:** Depósito mensal de 8% sobre o Salário Bruto.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Custo anual inclui 13º (1 salário) e Férias (1 salário + 1/3). Fator `13.33`. Encargos incidem sobre essa base ampliada.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **INSS:** Progressive rate (7.5% to 14%) on brackets, capped.\n- **IRRF:** Progressive rate (0% to 27.5%) on (Gross - INSS - Dep. Allowance) minus deduction.\n\n**{T["rules_er"]} - Explanation:**\n- **INSS Patronal, RAT, Sistema S:** Percentages on total payroll.\n- **FGTS:** 8% deposit.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Annual cost factor `13.33` includes 13th Salary and Vacation + 1/3 bonus. Charges apply to this base.""", unsafe_allow_html=True)
    elif country == "Estados Unidos":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **FICA (Social Security):** 6.2% sobre Sal. Bruto, até teto anual ({fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}).\n- **Medicare:** 1.45% sobre Sal. Bruto total.\n- **State Tax:** Varia por estado.\n\n**{T["rules_er"]} - Explicação:**\n- **FICA & Medicare Match:** Empregador paga o mesmo que o empregado.\n- **SUTA/FUTA:** Desemprego sobre base baixa (~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}).\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Não obrigatórios. Fator `12.00`.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **FICA (Social Security):** 6.2% on Gross Salary, up to cap ({fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}).\n- **Medicare:** 1.45% on total Gross Salary.\n- **State Tax:** Varies.\n\n**{T["rules_er"]} - Explanation:**\n- **FICA & Medicare Match:** Employer pays the same.\n- **SUTA/FUTA:** Unemployment on low base (~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Not mandatory. Factor `12.00`.""", unsafe_allow_html=True)
    elif country == "Canadá":
         if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **CPP:** 5.95% sobre Sal. Bruto (após isenção {fmt_money(ANNUAL_CAPS['CA_CPP_EXEMPT'], 'CAD$')}) até Teto 1 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}).\n- **CPP2:** 4.0% sobre Sal. Bruto entre Teto 1 e Teto 2 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}).\n- **EI:** 1.63% sobre Sal. Bruto até Teto ({fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}).\n- **Income Tax:** Progressivo Federal + Provincial.\n\n**{T["rules_er"]} - Explicação:**\n- **CPP/CPP2 Match:** Empregador paga o mesmo.\n- **EI Match:** Empregador paga 1.4x (2.28%).\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Não há 13º. Férias pagas são obrigatórias. Fator `12.00`.""", unsafe_allow_html=True)
         else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **CPP:** 5.95% on Gross (after exempt {fmt_money(ANNUAL_CAPS['CA_CPP_EXEMPT'], 'CAD$')}) up to Cap 1 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}).\n- **CPP2:** 4.0% on Gross between Cap 1 and Cap 2 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}).\n- **EI:** 1.63% on Gross up to Cap ({fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}).\n- **Income Tax:** Progressive Federal + Provincial.\n\n**{T["rules_er"]} - Explanation:**\n- **CPP/CPP2 Match:** Employer pays the same.\n- **EI Match:** Employer pays 1.4x (2.28%).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- No 13th. Paid vacation mandatory. Factor `12.00`.""", unsafe_allow_html=True)
    elif country == "México":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação (Simplificada):**\n- **ISR:** Imposto de renda progressivo. Cálculo exato usa tabelas complexas. O simulador usa uma taxa fixa como aproximação.\n- **IMSS:** Seguridade social (doenças, invalidez, etc.). Taxas variam e aplicam-se sobre o Salário Base de Contribuição (SBC), com teto (aprox. 25 UMAs). O simulador usa taxa e teto simplificados.\n\n**{T["rules_er"]} - Explicação:**\n- **IMSS, INFONAVIT, SAR, ISN:** Contribuições patronais sobre SBC (com tetos) e folha.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- **Aguinaldo (13º):** Mín. 15 dias. Fator `12.50`.\n- **Prima Vacacional:** 25% sobre dias de férias.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation (Simplified):**\n- **ISR:** Progressive income tax. Exact calculation uses complex tables. Simulator uses a flat rate approximation.\n- **IMSS:** Social security (illness, disability, etc.). Rates vary and apply to the Contribution Base Salary (SBC), capped (approx. 25 UMAs). Simulator uses simplified rate and cap.\n\n**{T["rules_er"]} - Explanation:**\n- **IMSS, INFONAVIT, SAR, ISN:** Contributions on SBC (capped) and payroll.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- **Aguinaldo (13th):** Min. 15 days. Factor `12.50`.\n- **Prima Vacacional:** 25% on vacation days.""", unsafe_allow_html=True)
    elif country == "Chile":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **AFP:** 10% + comissão (~1.15%) para pensão. Base com teto em UF.\n- **Saúde:** 7% para FONASA/ISAPRE. Base com teto em UF.\n\n**{T["rules_er"]} - Explicação:**\n- **Seguro de Cesantía:** 2.4%. Base com teto em UF.\n- **SIS:** ~1.53% para invalidez. Base com teto em UF.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Aguinaldo não obrigatório. Fator `12.00`.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **AFP:** 10% + fee (~1.15%) for pension. Base capped in UF.\n- **Health:** 7% for FONASA/ISAPRE. Base capped in UF.\n\n**{T["rules_er"]} - Explanation:**\n- **Seguro de Cesantía:** 2.4%. Base capped in UF.\n- **SIS:** ~1.53% for disability. Base capped in UF.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Aguinaldo not mandatory. Factor `12.00`.""", unsafe_allow_html=True)
    elif country == "Argentina":
         if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **Jubilación, Obra Social, PAMI:** Total 17% sobre Sal. Bruto (com teto).\n\n**{T["rules_er"]} - Explicação:**\n- **Cargas Sociales:** ~23.5% sobre Sal. Bruto (com teto).\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- **SAC (13º):** 1 salário/ano em 2 parcelas. Fator `13.00`. Encargos incidem.""", unsafe_allow_html=True)
         else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **Jubilación, Obra Social, PAMI:** Total 17% on Gross Salary (capped).\n\n**{T["rules_er"]} - Explanation:**\n- **Cargas Sociales:** ~23.5% on Gross Salary (capped).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- **SAC (13th):** 1 salary/year in 2 installments. Factor `13.00`. Charges apply.""", unsafe_allow_html=True)
    elif country == "Colômbia":
         if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **Salud & Pensión:** 4% cada sobre IBC.\n\n**{T["rules_er"]} - Explicação:**\n- **Salud & Pensión:** 8.5% e 12% sobre IBC.\n- **Parafiscales:** 9% sobre folha (salvo exceções).\n- **Cesantías:** 8.33% (1/12) sobre base anual, depositado em fundo.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- **Prima (13º):** 1 salário/ano.\n- **Cesantías:** Custo adicional de 1 salário/ano.\n- Fator `14.00` reflete base anual para encargos.""", unsafe_allow_html=True)
         else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **Salud & Pensión:** 4% each on IBC.\n\n**{T["rules_er"]} - Explanation:**\n- **Salud & Pensión:** 8.5% and 12% on IBC.\n- **Parafiscales:** 9% on payroll (exceptions apply).\n- **Cesantías:** 8.33% (1/12) on annual base, deposited into fund.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- **Prima (13th):** 1 salary/year.\n- **Cesantías:** Additional cost of 1 salary/year.\n- Factor `14.00` reflects annual base for charges.""", unsafe_allow_html=True)

    st.write(""); st.markdown(f"**{T['valid_from']}:** {valid_from}"); st.markdown(f"[{T['official_source']}]({link})", unsafe_allow_html=True)

# =========================== REGRAS DE CÁLCULO DO STI ==================
elif active_menu == T.get("menu_rules_sti"):
    header_level = T.get("sti_table_header_level", "Level"); header_pct = T.get("sti_table_header_pct", "STI %")
    st.markdown(f"#### {T.get('sti_area_non_sales', 'Non Sales')}")
    st.markdown(f"""
    | {header_level}                                       | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T.get(STI_I18N_KEYS.get("CEO", ""), "CEO")}                              |   100%   |
    | {T.get(STI_I18N_KEYS.get("Members of the GEB", ""), "GEB")}                |  50–80%  |
    | {T.get(STI_I18N_KEYS.get("Executive Manager", ""), "Exec Mgr")}                |  45–70%  |
    | {T.get(STI_I18N_KEYS.get("Senior Group Manager", ""), "Sr Grp Mgr")}             |  40–60%  |
    | {T.get(STI_I18N_KEYS.get("Group Manager", ""), "Grp Mgr")}                    |  30–50%  |
    | {T.get(STI_I18N_KEYS.get("Lead Expert / Program Manager", ""), "Lead Exp")}      |  25–40%  |
    | {T.get(STI_I18N_KEYS.get("Senior Manager", ""), "Sr Mgr")}                   |  20–40%  |
    | {T.get(STI_I18N_KEYS.get("Senior Expert / Senior Project Manager", ""), "Sr Exp")} |  15–35%  |
    | {T.get(STI_I18N_KEYS.get("Manager / Selected Expert / Project Manager", ""), "Mgr/Exp")} |  10–30%  |
    | {T.get(STI_I18N_KEYS.get("Others", ""), "Others")}                           |  ≤ 10%   |
    """, unsafe_allow_html=True)
    st.markdown(f"#### {T.get('sti_area_sales', 'Sales')}")
    st.markdown(f"""
    | {header_level}                                       | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T.get(STI_I18N_KEYS.get("Executive Manager / Senior Group Manager", ""), "Exec/Sr Grp Mgr")} |  45–70%  |
    | {T.get(STI_I18N_KEYS.get("Group Manager / Lead Sales Manager", ""), "Grp/Lead Sales Mgr")}    |  35–50%  |
    | {T.get(STI_I18N_KEYS.get("Senior Manager / Senior Sales Manager", ""), "Sr/Sr Sales Mgr")} |  25–45%  |
    | {T.get(STI_I18N_KEYS.get("Manager / Selected Sales Manager", ""), "Mgr/Sales Mgr")}      |  20–35%  |
    | {T.get(STI_I18N_KEYS.get("Others", ""), "Others")}                           |  ≤ 15%   |
    """, unsafe_allow_html=True)

# ========================= CUSTO DO EMPREGADOR ========================
elif active_menu == T.get("menu_cost"):
    c1, c2 = st.columns(2)
    salario = c1.number_input(f"{T.get('salary', 'Salary')} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    bonus_anual = c2.number_input(f"{T.get('bonus', 'Bonus')} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_cost_input")
    st.write("---")
    # Passa `country` explicitamente para fmt_cap dentro de calc_employer_cost
    anual, mult, df_cost, months = calc_employer_cost(country, salario, bonus_anual, T, tables_ext=COUNTRY_TABLES)
    st.markdown(f"**{T.get('employer_cost_total', 'Total Cost')} (Salário + Bônus + Encargos):** {fmt_money(anual, symbol)}  \n"
                f"**Multiplicador de Custo (vs Salário Base 12 meses):** {mult:.3f} × (12 meses)  \n"
                f"**{T.get('months_factor', 'Months')} (Base Salarial):** {months}")
    if not df_cost.empty: st.dataframe(df_cost, use_container_width=True, hide_index=True)
    else: st.info("Sem encargos configurados para este país.")
