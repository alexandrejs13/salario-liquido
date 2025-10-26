# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.50.21 - NameError FIX)
# Correção do NameError 'active_menu' e escopo da variável T.
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
# (Definidos antes para serem usados nos Defaults)
def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def fmt_percent(v: float) -> str:
    if v is None: return ""
    return f"{v:.2f}%"

# Variável global temporária para o código do país, será definida na sidebar
_COUNTRY_CODE_FOR_FMT = "Brasil" 

def fmt_cap(cap_value: Any, sym: str = None) -> str:
    global _COUNTRY_CODE_FOR_FMT 
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
try:
    CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
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
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return default_value

# --- Fallbacks Mínimos (Mantidos) ---
I18N_FALLBACK = { "Português": { "sidebar_title": "Simulador de Remuneração<br>(Região das Americas)", "app_title": "Simulador de Salário Líquido e Custo do Empregador", "menu_calc": "Simulador de Remuneração", "menu_rules": "Regras de Contribuições", "menu_rules_sti": "Regras de Cálculo do STI", "menu_cost": "Custo do Empregador", "title_calc": "Simulador de Remuneração", "title_rules": "Regras de Contribuições", "title_rules_sti": "Regras de Cálculo do STI", "title_cost": "Custo do Empregador", "country": "País", "salary": "Salário Bruto", "state": "Estado (EUA)", "state_rate": "State Tax (%)", "dependents": "Dependentes (IR)", "bonus": "Bônus Anual", "other_deductions": "Outras Deduções Mensais", "earnings": "Proventos", "deductions": "Descontos", "net": "Salário Líquido", "fgts_deposit": "Depósito FGTS", "tot_earnings": "Total de Proventos", "tot_deductions": "Total de Descontos", "valid_from": "Vigência", "rules_emp": "Contribuições do Empregado", "rules_er": "Contribuições do Empregador", "rules_table_desc": "Descrição", "rules_table_rate": "Alíquota (%)", "rules_table_base": "Base de Cálculo", "rules_table_obs": "Observações / Teto", "official_source": "Fonte Oficial", "employer_cost_total": "Custo Total do Empregador", "annual_comp_title": "Composição da Remuneração Total Anual Bruta", "calc_params_title": "Parâmetros de Cálculo da Remuneração", "monthly_comp_title": "Remuneração Mensal Bruta e Líquida", "annual_salary": "📅 Salário Anual", "annual_bonus": "🎯 Bônus Anual", "annual_total": "💼 Remuneração Total Anual", "months_factor": "Meses considerados", "pie_title": "Distribuição Anual: Salário vs Bônus", "pie_chart_title_dist": "Distribuição da Remuneração Total", "reload": "Recarregar tabelas", "source_remote": "Tabelas remotas", "source_local": "Fallback local", "choose_country": "Selecione o país", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalhes das Contribuições Obrigatórias", "salary_tooltip": "Seu salário mensal antes de impostos e deduções.", "dependents_tooltip": "Número de dependentes para dedução no Imposto de Renda (aplicável apenas no Brasil).", "bonus_tooltip": "Valor total do bônus esperado no ano (pago de uma vez ou parcelado).", "other_deductions_tooltip": "Soma de outras deduções mensais recorrentes (ex: plano de saúde, vale-refeição, contribuição sindical).", "sti_area_tooltip": "Selecione sua área de atuação (Vendas ou Não Vendas) para verificar a faixa de bônus (STI).", "sti_level_tooltip": "Selecione seu nível de carreira para verificar a faixa de bônus (STI). 'Others' inclui níveis não listados.", "sti_area_non_sales": "Não Vendas", "sti_area_sales": "Vendas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Membros do GEB", "sti_level_executive_manager": "Gerente Executivo", "sti_level_senior_group_manager": "Gerente de Grupo Sênior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Especialista Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sênior", "sti_level_senior_expert_senior_project_manager": "Especialista Sênior / Gerente de Projeto Sênior", "sti_level_manager_selected_expert_project_manager": "Gerente / Especialista Selecionado / Gerente de Projeto", "sti_level_others": "Outros", "sti_level_executive_manager_senior_group_manager": "Gerente Executivo / Gerente de Grupo Sênior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Vendas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sênior / Gerente de Vendas Sênior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Vendas Selecionado", "sti_in_range": "Dentro do range", "sti_out_range": "Fora do range", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observação", "cost_header_bonus": "Incide Bônus", "cost_header_vacation": "Incide Férias", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nível de Carreira", "sti_table_header_pct": "STI %" }, "English": { "sidebar_title": "Compensation Simulator<br>(Americas Region)", "other_deductions": "Other Monthly Deductions", "salary_tooltip": "Your monthly salary before taxes and deductions.", "dependents_tooltip": "Number of dependents for Income Tax deduction (applicable only in Brazil).", "bonus_tooltip": "Total expected bonus amount for the year (paid lump sum or installments).", "other_deductions_tooltip": "Sum of other recurring monthly deductions (e.g., health plan, meal voucher, union dues).", "sti_area_tooltip": "Select your area (Sales or Non Sales) to check the bonus (STI) range.", "sti_level_tooltip": "Select your career level to check the bonus (STI) range. 'Others' includes unlisted levels.", "app_title": "Net Salary & Employer Cost Simulator", "menu_calc": "Compensation Simulator", "menu_rules": "Contribution Rules", "menu_rules_sti": "STI Calculation Rules", "menu_cost": "Employer Cost", "title_calc": "Compensation Simulator", "title_rules": "Contribution Rules", "title_rules_sti": "STI Calculation Rules", "title_cost": "Employer Cost", "country": "Country", "salary": "Gross Salary", "state": "State (USA)", "state_rate": "State Tax (%)", "dependents": "Dependents (Tax)", "bonus": "Annual Bonus", "earnings": "Earnings", "deductions": "Deductions", "net": "Net Salary", "fgts_deposit": "FGTS Deposit", "tot_earnings": "Total Earnings", "tot_deductions": "Total Deductions", "valid_from": "Effective Date", "rules_emp": "Employee Contributions", "rules_er": "Employer Contributions", "rules_table_desc": "Description", "rules_table_rate": "Rate (%)", "rules_table_base": "Calculation Base", "rules_table_obs": "Notes / Cap", "official_source": "Official Source", "employer_cost_total": "Total Employer Cost", "annual_comp_title": "Total Annual Gross Compensation", "calc_params_title": "Compensation Calculation Parameters", "monthly_comp_title": "Monthly Gross and Net Compensation", "annual_salary": "📅 Annual Salary", "annual_bonus": "🎯 Annual Bonus", "annual_total": "💼 Total Annual Compensation", "months_factor": "Months considered", "pie_title": "Annual Split: Salary vs Bonus", "pie_chart_title_dist": "Total Compensation Distribution", "reload": "Reload tables", "source_remote": "Remote tables", "source_local": "Local fallback", "choose_country": "Select a country", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Area (STI)", "level": "Career Level (STI)", "rules_expanded": "Details of Mandatory Contributions", "sti_area_non_sales": "Non Sales", "sti_area_sales": "Sales", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Members of the GEB", "sti_level_executive_manager": "Executive Manager", "sti_level_senior_group_manager": "Senior Group Manager", "sti_level_group_manager": "Group Manager", "sti_level_lead_expert_program_manager": "Lead Expert / Program Manager", "sti_level_senior_manager": "Senior Manager", "sti_level_senior_expert_senior_project_manager": "Senior Expert / Senior Project Manager", "sti_level_manager_selected_expert_project_manager": "Manager / Selected Expert / Project Manager", "sti_level_others": "Others", "sti_level_executive_manager_senior_group_manager": "Executive Manager / Senior Group Manager", "sti_level_group_manager_lead_sales_manager": "Group Manager / Lead Sales Manager", "sti_level_senior_manager_senior_sales_manager": "Senior Manager / Senior Sales Manager", "sti_level_manager_selected_sales_manager": "Manager / Selected Sales Manager", "sti_in_range": "Within range", "sti_out_range": "Outside range", "cost_header_charge": "Charge", "cost_header_percent": "Percent (%)", "cost_header_base": "Base", "cost_header_obs": "Observation", "cost_header_bonus": "Applies to Bonus", "cost_header_vacation": "Applies to Vacation", "cost_header_13th": "Applies to 13th", "sti_table_header_level": "Career Level", "sti_table_header_pct": "STI %" }, "Español": { "sidebar_title": "Simulador de Remuneración<br>(Región Américas)", "other_deductions": "Otras Deducciones Mensuales", "salary_tooltip": "Su salario mensual antes de impuestos y deducciones.", "dependents_tooltip": "Número de dependientes para deducción en el Impuesto de Renta (solo aplicable en Brasil).", "bonus_tooltip": "Monto total del bono esperado en el año (pago único o en cuotas).", "other_deductions_tooltip": "Suma de otras deducciones mensuales recurrentes (ej: plan de salud, ticket de comida, cuota sindical).", "sti_area_tooltip": "Seleccione su área (Ventas o No Ventas) para verificar el rango del bono (STI).", "sti_level_tooltip": "Seleccione su nivel de carrera para verificar el rango del bono (STI). 'Otros' incluye niveles no listados.", "app_title": "Simulador de Salario Neto y Costo del Empleador", "menu_calc": "Simulador de Remuneración", "menu_rules": "Regras de Contribuições", "menu_rules_sti": "Regras de Cálculo del STI", "menu_cost": "Costo del Empleador", "title_calc": "Simulador de Remuneración", "title_rules": "Regras de Contribuições", "title_rules_sti": "Reglas de Cálculo del STI", "title_cost": "Costo del Empleador", "country": "País", "salary": "Salario Bruto", "state": "Estado (EE. UU.)", "state_rate": "Impuesto Estatal (%)", "dependents": "Dependientes (Impuesto)", "bonus": "Bono Anual", "earnings": "Ingresos", "deductions": "Descuentos", "net": "Salario Neto", "fgts_deposit": "Depósito de FGTS", "tot_earnings": "Total Ingresos", "tot_deductions": "Total Descuentos", "valid_from": "Vigencia", "rules_emp": "Contribuições del Empleado", "rules_er": "Contribuições del Empleador", "rules_table_desc": "Descripción", "rules_table_rate": "Tasa (%)", "rules_table_base": "Base de Cálculo", "rules_table_obs": "Notas / Tope", "official_source": "Fuente Oficial", "employer_cost_total": "Costo Total del Empleador", "annual_comp_title": "Composição de la Remuneração Anual Bruta", "calc_params_title": "Parâmetros de Cálculo de Remuneración", "monthly_comp_title": "Remuneração Mensual Bruta y Neta", "annual_salary": "📅 Salario Anual", "annual_bonus": "🎯 Bono Anual", "annual_total": "💼 Remuneração Anual Total", "months_factor": "Meses considerados", "pie_title": "Distribuição Anual: Salario vs Bono", "pie_chart_title_dist": "Distribución de la Remuneración Total", "reload": "Recarregar tablas", "source_remote": "Tablas remotas", "source_local": "Copia local", "choose_country": "Seleccione un país", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalles de las Contribuições Obligatorias", "sti_area_non_sales": "No Ventas", "sti_area_sales": "Ventas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Miembros del GEB", "sti_level_executive_manager": "Gerente Ejecutivo", "sti_level_senior_group_manager": "Gerente de Grupo Sénior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Experto Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sénior", "sti_level_senior_expert_senior_project_manager": "Experto Sénior / Gerente de Proyecto Sénior", "sti_level_manager_selected_expert_project_manager": "Gerente / Experto Seleccionado / Gerente de Proyecto", "sti_level_others": "Otros", "sti_level_executive_manager_senior_group_manager": "Gerente Ejecutivo / Gerente de Grupo Sénior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Ventas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sénior / Gerente de Ventas Sénior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Ventas Seleccionado", "sti_in_range": "Dentro del rango", "sti_out_range": "Fuera del rango", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observação", "cost_header_bonus": "Incide Bono", "cost_header_vacation": "Incide Vacaciones", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nivel de Carrera", "sti_table_header_pct": "STI %" } }
COUNTRIES_FALLBACK = {"Brasil": {"symbol": "R$", "flag": "🇧🇷", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "México": {"symbol": "MX$", "flag": "🇲🇽", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Chile": {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": False}}, "Argentina": {"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01", "benefits": {"ferias": False, "decimo": False}}, "Canadá": {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01", "benefits": {"ferias": False, "decimo": False}}}
STI_CONFIG_FALLBACK = {"STI_RANGES": { "Non Sales": { "CEO": [1.00, 1.00], "Members of the GEB": [0.50, 0.80], "Executive Manager": [0.45, 0.70], "Senior Group Manager": [0.40, 0.60], "Group Manager": [0.30, 0.50], "Lead Expert / Program Manager": [0.25, 0.40], "Senior Manager": [0.20, 0.40], "Senior Expert / Senior Project Manager": [0.15, 0.35], "Manager / Selected Expert / Project Manager": [0.10, 0.30], "Others": [0.0, 0.10] }, "Sales": { "Executive Manager / Senior Group Manager": [0.45, 0.70], "Group Manager / Lead Sales Manager": [0.35, 0.50], "Senior Manager / Senior Sales Manager": [0.25, 0.45], "Manager / Selected Sales Manager": [0.20, 0.35], "Others": [0.0, 0.15] } }, "STI_LEVEL_OPTIONS": { "Non Sales": [ "CEO", "Members of the GEB", "Executive Manager", "Senior Group Manager", "Group Manager", "Lead Expert / Program Manager", "Senior Manager", "Senior Expert / Senior Project Manager", "Manager / Selected Expert / Project Manager", "Others" ], "Sales": [ "Executive Manager / Senior Group Manager", "Group Manager / Lead Sales Manager", "Senior Manager / Senior Sales Manager", "Manager / Selected Sales Manager", "Others" ]}}
BR_INSS_FALLBACK = { "vigencia": "2025-01-01", "teto_contribuicao": 1146.68, "teto_base": 8157.41, "faixas": [ {"ate": 1412.00, "aliquota": 0.075}, {"ate": 2666.68, "aliquota": 0.09}, {"ate": 4000.03, "aliquota": 0.12}, {"ate": 8157.41, "aliquota": 0.14} ] }
BR_IRRF_FALLBACK = { "vigencia": "2025-01-01", "deducao_dependente": 189.59, "faixas": [ {"ate": 2259.20, "aliquota": 0.00,  "deducao": 0.00}, {"ate": 2826.65, "aliquota": 0.075, "deducao": 169.44}, {"ate": 3751.05, "aliquota": 0.15,  "deducao": 381.44}, {"ate": 4664.68, "aliquota": 0.225, "deducao": 662.77}, {"ate": 999999999.0, "aliquota": 0.275, "deducao": 896.00} ] }


# --- Carrega Configurações ---
I18N = load_json(I18N_FILE, I18N_FALLBACK)
COUNTRIES_DATA = load_json(COUNTRIES_FILE, COUNTRIES_FALLBACK)
STI_CONFIG_DATA = load_json(STI_CONFIG_FILE, STI_CONFIG_FALLBACK)
US_STATE_RATES = load_json(US_STATES_FILE, {}) 
BR_INSS_TBL = load_json(BR_INSS_FILE, BR_INSS_FALLBACK)
BR_IRRF_TBL = load_json(BR_IRRF_FILE, BR_IRRF_FALLBACK)
COUNTRY_TABLES_DATA = load_json(COUNTRY_TABLES_FILE, {})

# --- Extrai Dados Carregados ---
COUNTRIES = COUNTRIES_DATA if COUNTRIES_DATA else COUNTRIES_FALLBACK 
if not COUNTRIES: COUNTRIES = COUNTRIES_FALLBACK 

if not STI_CONFIG_DATA or "STI_RANGES" not in STI_CONFIG_DATA:
    STI_RANGES = STI_CONFIG_FALLBACK.get("STI_RANGES", {})
    STI_LEVEL_OPTIONS = STI_CONFIG_FALLBACK.get("STI_LEVEL_OPTIONS", {})
else:
    STI_RANGES = STI_CONFIG_DATA.get("STI_RANGES", {})
    STI_LEVEL_OPTIONS = STI_CONFIG_DATA.get("STI_LEVEL_OPTIONS", {})


COUNTRY_BENEFITS = {k: v.get("benefits", {}) for k, v in COUNTRIES.items()}
TABLES_DEFAULT = COUNTRY_TABLES_DATA.get("TABLES", {})
EMPLOYER_COST_DEFAULT = COUNTRY_TABLES_DATA.get("EMPLOYER_COST", {})
REMUN_MONTHS_DEFAULT = COUNTRY_TABLES_DATA.get("REMUN_MONTHS", {})
CA_CPP_EI_DEFAULT = { "cpp_rate": 0.0595, "cpp_exempt_monthly": ANNUAL_CAPS["CA_CPP_EXEMPT"] / 12.0, "cpp_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx1"] / 12.0, "cpp2_rate": 0.04, "cpp2_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx2"] / 12.0, "ei_rate": 0.0163, "ei_cap_monthly": ANNUAL_CAPS["CA_EI_MIE"] / 12.0 }

STI_I18N_KEYS = {
    "CEO": "sti_level_ceo",
    "Members of the GEB": "sti_level_members_of_the_geb",
    "Executive Manager": "sti_level_executive_manager",
    "Senior Group Manager": "sti_level_senior_group_manager",
    "Group Manager": "sti_level_group_manager",
    "Lead Expert / Program Manager": "sti_level_lead_expert_program_manager",
    "Senior Manager": "sti_level_senior_manager",
    "Senior Expert / Senior Project Manager": "sti_level_senior_expert_senior_project_manager",
    "Manager / Selected Expert / Project Manager": "sti_level_manager_selected_expert_project_manager",
    "Others": "sti_level_others",
    "Executive Manager / Senior Group Manager": "sti_level_executive_manager_senior_group_manager",
    "Group Manager / Lead Sales Manager": "sti_level_group_manager_lead_sales_manager",
    "Senior Manager / Senior Sales Manager": "sti_level_senior_manager_senior_sales_manager",
    "Manager / Selected Sales Manager": "sti_level_manager_selected_sales_manager"
}

def load_tables_data(): 
    country_tables_dict = {
        "TABLES": COUNTRY_TABLES_DATA.get("TABLES", TABLES_DEFAULT),
        "EMPLOYER_COST": COUNTRY_TABLES_DATA.get("EMPLOYER_COST", EMPLOYER_COST_DEFAULT),
        "REMUN_MONTHS": COUNTRY_TABLES_DATA.get("REMUN_MONTHS", REMUN_MONTHS_DEFAULT)
    }
    return US_STATE_RATES, country_tables_dict, BR_INSS_TBL, BR_IRRF_TBL

# [CSS bloco mantido]
st.markdown("""
<style>
/* ... (Seu CSS) ... */
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
# [Fim CSS bloco mantido]

# [Funções de cálculo mantidas]

# ============================== SIDEBAR ===============================
with st.sidebar:
    # 1. TÍTULO PRINCIPAL (Ordem Corrigida)
    # T_temp é usado aqui, pois T só é definido após o selectbox de idioma
    T_temp = I18N.get(st.session_state.get('idioma', 'Português'), I18N_FALLBACK["Português"])
    st.markdown(f"<h2 style='color:white; text-align:center; font-size:20px; margin-bottom: 25px;'>{T_temp.get('sidebar_title', 'Simulador')}</h2>", unsafe_allow_html=True)
    
    # 2. SELETOR DE IDIOMA
    st.markdown(f"<h3 style='margin-bottom: 0.5rem;'>{T_temp.get('language_title', '🌐 Idioma / Language / Idioma')}</h3>", unsafe_allow_html=True)
    
    if 'idioma' not in st.session_state:
        st.session_state.idioma = 'Português'
        
    idioma = st.selectbox(
        label="Language Select", 
        options=list(I18N.keys()), 
        index=list(I18N.keys()).index(st.session_state.idioma), 
        key="lang_select", 
        label_visibility="collapsed"
    )
    
    # T AGORA ESTÁ DEFINIDO PARA USO POSTERIOR
    T = I18N.get(idioma, I18N_FALLBACK["Português"])
    
    # Atualiza o estado se o idioma mudou
    if idioma != st.session_state.idioma:
        st.session_state.idioma = idioma
        if 'active_menu' in st.session_state:
            del st.session_state['active_menu']
        if 'country_select' in st.session_state:
             del st.session_state['country_select']
        st.rerun()

    # 3. SELETOR DE PAÍS
    st.markdown(f"<h3 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>{T.get('country', 'País')}</h3>", unsafe_allow_html=True)
    country_options = list(COUNTRIES.keys()) 
    
    if not country_options:
        st.error("Erro fatal: Arquivo 'countries.json' não carregou países.")
        st.stop()
    
    default_country = "Brasil" if "Brasil" in country_options else country_options[0]
    
    if 'country_select' not in st.session_state: st.session_state.country_select = default_country
    if st.session_state.country_select not in country_options: st.session_state.country_select = default_country
    
    try: country_index = country_options.index(st.session_state.country_select)
    except ValueError: country_index = 0
    
    country_selected = st.selectbox(T.get("choose_country", "Selecione"), country_options, index=country_index, key="country_select", label_visibility="collapsed")
    
    _COUNTRY_CODE_FOR_FMT = country_selected
    if country_selected != st.session_state.country_select:
        st.session_state.country_select = country_selected
        st.experimental_rerun() 

    # 4. MENU DE NAVEGAÇÃO
    st.markdown(f"<h3 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>{T.get('menu_title', 'Menu')}</h3>", unsafe_allow_html=True)
    menu_options = [T.get("menu_calc", "Calc"), T.get("menu_rules", "Rules"), T.get("menu_rules_sti", "STI Rules"), T.get("menu_cost", "Cost")]

    if 'active_menu' not in st.session_state or st.session_state.active_menu not in menu_options:
        st.session_state.active_menu = menu_options[0]
    
    try: active_menu_index = menu_options.index(st.session_state.active_menu)
    except ValueError: active_menu_index = 0; st.session_state.active_menu = menu_options[0]

    # Atribuímos o valor retornado à chave do session_state
    st.radio(
        label="Menu Select", options=menu_options, key="menu_radio_select",
        label_visibility="collapsed", index=active_menu_index
    )
    # A verificação de mudança de menu é feita implicitamente pelo key="menu_radio_select"
    # st.session_state.active_menu é atualizado automaticamente.

# ======================= INICIALIZAÇÃO PÓS-SIDEBAR =======================
# --- CORREÇÃO DE ESCOPO/NAMEERROR ---
# T e active_menu devem ser recuperados do session_state/sidebar
# T já foi definido no sidebar, mas precisamos defini-lo no escopo principal se houver rerun.
if 'idioma' in st.session_state:
    T = I18N.get(st.session_state.idioma, I18N_FALLBACK["Português"])
else:
    T = I18N_FALLBACK["Português"]

country = st.session_state.get('country_select', 'Brasil') # Padrão seguro
active_menu = st.session_state.get('active_menu', T.get("menu_calc", "Calc"))
# --- FIM CORREÇÃO DE ESCOPO/NAMEERROR ---

US_STATE_RATES_LOADED, COUNTRY_TABLES_LOADED, BR_INSS_TBL_LOADED, BR_IRRF_TBL_LOADED = load_tables_data()
COUNTRY_TABLES = COUNTRY_TABLES_LOADED

if country not in COUNTRIES:
    st.error(f"Erro: País '{country}' não encontrado. Verifique 'countries.json'.")
    st.stop()
    
try:
    symbol = COUNTRIES[country]["symbol"]
    flag = COUNTRIES[country]["flag"]
    valid_from = COUNTRIES[country]["valid_from"]
except KeyError as e:
    st.error(f"Erro de Configuração: O país '{country}' está na lista, mas falta a chave de configuração essencial '{e}' em 'countries.json'. Por favor, verifique o arquivo.")
    st.stop()
    
# ======================= TÍTULO DINÂMICO (MANTIDO) ==============================
if active_menu == T.get("menu_calc"): title = T.get("title_calc", "Calculator")
elif active_menu == T.get("menu_rules"): title = T.get("title_rules", "Rules")
elif active_menu == T.get("menu_rules_sti"): title = T.get("title_rules_sti", "STI Rules")
else: title = T.get("title_cost", "Cost")

st.markdown(f"<div class='country-header'><div class='country-title'>{title}</div><div class='country-flag'>{flag}</div></div>", unsafe_allow_html=True)
st.write("---")

# ========================= SIMULADOR DE REMUNERAÇÃO (RESPONSIVIDADE APLICADA) ==========================
if active_menu == T.get("menu_calc"):
    area_options_display, area_display_map = get_sti_area_map(T)
    st.subheader(T.get("calc_params_title", "Parameters"))

    # CORREÇÃO: Uso de HTML/Markdown e colunas para alinhar input boxes e garantir quebra de linha em rótulos longos.
    
    if country == "Brasil":
        # 6 campos: Salário, Dependentes, Outras Ded, Bônus, Área STI, Nível STI
        
        # RÓTULOS EM HTML ACIMA DAS COLUNAS
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 16.66%;"><h5>{T.get('salary', 'Salário Bruto')}<br>({symbol})</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('dependents', 'Dependentes')}<br>(IR)</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('other_deductions', 'Outras Deduções')}<br>({symbol})</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('bonus', 'Bônus Anual')}<br>({symbol})</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('area', 'Área')}<br>(STI)</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('level', 'Career Level')}<br>(STI)</h5></div>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(6) 
        salario = cols[0].number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed")
        dependentes = cols[1].number_input("Dependentes", min_value=0, value=0, step=1, key="dep_input", help=T.get("dependentes_tooltip"), label_visibility="collapsed")
        other_deductions = cols[2].number_input("Outras Deduções", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed")
        bonus_anual = cols[3].number_input("Bônus Anual", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed")
        area_display = cols[4].selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = cols[5].selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        state_code, state_rate = None, None
        
    elif country == "Estados Unidos":
        # 5 campos + 2 STI
        
        # RÓTULOS PRINCIPAIS EM HTML ACIMA DAS COLUNAS (5 campos)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 20%;"><h5>{T.get('salary', 'Gross Salary')}<br>({symbol})</h5></div>
            <div style="width: 20%;"><h5>{T.get('state', 'State')}<br>(USA)</h5></div>
            <div style="width: 20%;"><h5>{T.get('state_rate', 'State Tax')}<br>(%)</h5></div>
            <div style="width: 20%;"><h5>{T.get('other_deductions', 'Other Deductions')}<br>({symbol})</h5></div>
            <div style="width: 20%;"><h5>{T.get('bonus', 'Annual Bonus')}<br>({symbol})</h5></div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5 = st.columns(5)
        salario = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed")
        state_code = c2.selectbox("Estado", list(US_STATE_RATES.keys()), index=0, key="state_select_main", label_visibility="collapsed")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input("Taxa Estadual", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input", label_visibility="collapsed")
        other_deductions = c4.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed")
        bonus_anual = c5.number_input("Bônus Anual", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed")
        
        # RÓTULOS STI em uma nova linha de 4 colunas (usando 2 colunas vazias)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div style="width: 20%;"><h5>{T.get('area', 'Área')}<br>(STI)</h5></div>
            <div style="width: 20%;"><h5>{T.get('level', 'Career Level')}<br>(STI)</h5></div>
            <div style="width: 60%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, _ = st.columns([1, 1, 3]) 
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes = 0
        
    else: # Outros países (3 campos + 2 STI)
        
        # RÓTULOS PRINCIPAIS EM HTML ACIMA DAS COLUNAS (3 campos + 1 vazio)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 25%;"><h5>{T.get('salary', 'Salário Bruto')}<br>({symbol})</h5></div>
            <div style="width: 25%;"><h5>{T.get('other_deductions', 'Outras Deduções')}<br>({symbol})</h5></div>
            <div style="width: 25%;"><h5>{T.get('bonus', 'Bônus Anual')}<br>({symbol})</h5></div>
            <div style="width: 25%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, _ = st.columns(4)
        salario = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed")
        other_deductions = c2.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed")
        bonus_anual = c3.number_input("Bônus Anual", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed")
        
        # RÓTULOS STI em uma nova linha de 4 colunas (usando 2 colunas vazias)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div style="width: 25%;"><h5>{T.get('area', 'Área')}<br>(STI)</h5></div>
            <div style="width: 25%;"><h5>{T.get('level', 'Career Level')}<br>(STI)</h5></div>
            <div style="width: 50%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, _ = st.columns([1, 1, 2])
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes = 0
        state_code, state_rate = None, None

    st.subheader(T.get("monthly_comp_title", "Monthly Comp"))
    
    # ... (Restante do código mantido) ...
