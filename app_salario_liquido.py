# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.50.53 - REDESIGN COMPLETO E CORREÇÕES FINAIS)
# DESIGN: Aplicada nova paleta de cores profissional (Azul Sutil, Cinza) em todo o app.
# DESIGN/CSS: Barra lateral agora tem largura fixa (350px) e não pode ser redimensionada.
# DESIGN/CSS: Fonte dos valores nos cards de resumo foi reduzida para melhor equilíbrio visual.
# CORREÇÃO: Lógica de menu refatorada para garantir a tradução correta dos títulos da página e do menu.
# CORREÇÃO: Reestruturada a ordem dos elementos na página "Comparador de Remuneração".
# FEATURE: Adicionada coluna de variação nos cards de comparação anual.
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
_COUNTRY_CODE_FOR_FMT = "Brasil"
INPUT_FORMAT = "%.2f"

def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def fmt_percent(v: float) -> str:
    if v is None: return ""
    return f"{v:.2f}%"

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

# --- Fallbacks Mínimos ---
I18N_FALLBACK = {
    "Português": {
        "sidebar_title": "Simulador de Remuneração<br><span style='font-size: 14px; font-weight: 400;'>Região das Américas</span>", "app_title": "Simulador de Salário Líquido e Custo do Empregador", "menu_calc": "Simulador de Remuneração", "menu_comp": "Comparador de Remuneração", "menu_rules": "Regras de Contribuições", "menu_sti_rules": "Regras de Cálculo do STI", "menu_cost": "Custo do Empregador", "title_calc": "Simulador de Remuneração", "title_comp": "Comparador de Remuneração", "title_rules": "Regras de Contribuições", "title_sti_rules": "Regras de Cálculo do STI", "title_cost": "Custo do Empregador", "prop_title": "Remuneração Proposta", "cand_title": "Remuneração do Candidato", "comp_analysis_title": "Análise Comparativa", "comp_net_salary": "Salário Líquido Mensal", "comp_total_comp": "Remuneração Total Anual", "comp_employer_cost": "Custo Total Anual (Empregador)", "cost_total_label": "Custo Total do Empregador (Salário + Bônus + Encargos)", "cost_multiplier_label": "Multiplicador de Custo (vs Salário Base 12 meses)", "cost_months_label": "Meses considerados (Base Salarial)", "variation": "Variação", "country": "País", "salary": "Salário Bruto", "state": "Estado (EUA)", "state_rate": "State Tax (%)", "dependents": "Dependentes (IR)", "bonus": "Bônus", "other_deductions": "Outras Deduções Mensais", "earnings": "Proventos", "deductions": "Descontos", "net": "Salário Líquido", "fgts_deposit": "Depósito FGTS", "tot_earnings": "Total de Proventos", "tot_deductions": "Total de Descontos", "valid_from": "Vigência", "rules_emp": "Contribuições do Empregado", "rules_er": "Contribuições do Empregador", "rules_table_desc": "Descrição", "rules_table_rate": "Alíquota (%)", "rules_table_base": "Base de Cálculo", "rules_table_obs": "Observações / Teto", "official_source": "Fonte Oficial", "employer_cost_total": "Custo Total do Empregador", "annual_comp_title": "Composição da Remuneração Total Anual Bruta", "calc_params_title": "Parâmetros de Cálculo da Remuneração", "monthly_comp_title": "Remuneração Mensal Bruta e Líquida", "annual_salary": "Salário Anual", "annual_bonus": "Bônus", "annual_total": "Remuneração Total", "months_factor": "Meses considerados", "pie_chart_title_dist": "Distribuição da Remuneração Total", "choose_country": "Selecione o país", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalhes das Contribuições Obrigatórias", "salary_tooltip": "Seu salário mensal antes de impostos e deduções.", "dependents_tooltip": "Número de dependentes para dedução no Imposto de Renda (aplicável apenas no Brasil).", "bonus_tooltip": "Valor total do bônus esperado no ano (pago de uma vez ou parcelado).", "other_deductions_tooltip": "Soma de outras deduções mensais recorrentes (ex: plano de saúde, vale-refeição, contribuição sindical).", "sti_area_tooltip": "Selecione sua área de atuação (Vendas ou Não Vendas) para verificar a faixa de bônus (STI).", "sti_level_tooltip": "Selecione seu nível de carreira para verificar a faixa de bônus (STI). 'Others' inclui níveis não listados.", "sti_area_non_sales": "Não Vendas", "sti_area_sales": "Vendas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Membros do GEB", "sti_level_executive_manager": "Gerente Executivo", "sti_level_senior_group_manager": "Gerente de Grupo Sênior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Especialista Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sênior", "sti_level_senior_expert_senior_project_manager": "Especialista Sênior / Gerente de Projeto Sênior", "sti_level_manager_selected_expert_project_manager": "Gerente / Especialista Selecionado / Gerente de Projeto", "sti_level_others": "Outros", "sti_level_executive_manager_senior_group_manager": "Gerente Executivo / Gerente de Grupo Sênior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Vendas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sênior / Gerente de Vendas Sênior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Vendas Selecionado", "sti_in_range": "Dentro do range", "sti_out_range": "Fora do range", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observação", "cost_header_bonus": "Incide Bônus", "cost_header_vacation": "Incide Férias", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nível de Carreira", "sti_table_header_pct": "STI %"
    },
    "English": { "sidebar_title": "Compensation Simulator<br><span style='font-size: 14px; font-weight: 400;'>Americas Region</span>", "menu_comp": "Compensation Comparator", "title_comp": "Compensation Comparator", "prop_title": "Proposed Compensation", "cand_title": "Candidate's Compensation", "comp_analysis_title": "Comparative Analysis", "comp_net_salary": "Monthly Net Salary", "comp_total_comp": "Total Annual Compensation", "comp_employer_cost": "Total Annual Employer Cost", "cost_total_label": "Total Employer Cost (Salary + Bonus + Charges)", "cost_multiplier_label": "Cost Multiplier (vs 12-month Base Salary)", "cost_months_label": "Months considered (Salary Base)", "variation": "Variation", "other_deductions": "Other Monthly Deductions", "salary_tooltip": "Your monthly salary before taxes and deductions.", "dependents_tooltip": "Number of dependents for Income Tax deduction (applicable only in Brazil).", "bonus_tooltip": "Total expected bonus amount for the year (paid lump sum or installments).", "other_deductions_tooltip": "Sum of other recurring monthly deductions (e.g., health plan, meal voucher, union dues).", "sti_area_tooltip": "Select your area (Sales or Non Sales) to check the bonus (STI) range.", "sti_level_tooltip": "Select your career level to check the bonus (STI) range. 'Others' includes unlisted levels.", "app_title": "Net Salary & Employer Cost Simulator", "menu_calc": "Compensation Simulator", "menu_rules": "Contribution Rules", "menu_sti_rules": "STI Calculation Rules", "menu_cost": "Employer Cost", "title_calc": "Compensation Simulator", "title_rules": "Contribution Rules", "title_sti_rules": "STI Calculation Rules", "title_cost": "Employer Cost", "country": "Country", "salary": "Gross Salary", "state": "State (USA)", "state_rate": "State Tax (%)", "dependents": "Dependents (Tax)", "bonus": "Bonus", "earnings": "Earnings", "deductions": "Deductions", "net": "Net Salary", "fgts_deposit": "FGTS Deposit", "tot_earnings": "Total Earnings", "tot_deductions": "Total Deductions", "valid_from": "Effective Date", "rules_emp": "Employee Contributions", "rules_er": "Employer Contributions", "rules_table_desc": "Description", "rules_table_rate": "Rate (%)", "rules_table_base": "Calculation Base", "rules_table_obs": "Notes / Cap", "official_source": "Official Source", "employer_cost_total": "Total Employer Cost", "annual_comp_title": "Total Gross Compensation", "annual_salary": "Annual Salary", "annual_bonus": "Bonus", "annual_total": "Total Compensation", "months_factor": "Months considered", "pie_chart_title_dist": "Total Compensation Distribution", "choose_country": "Select a country", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Area (STI)", "level": "Career Level (STI)", "rules_expanded": "Details of Mandatory Contributions", "sti_area_non_sales": "Non Sales", "sti_area_sales": "Sales", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Members of the GEB", "sti_level_executive_manager": "Executive Manager", "sti_level_senior_group_manager": "Senior Group Manager", "sti_level_group_manager": "Group Manager", "sti_level_lead_expert_program_manager": "Lead Expert / Program Manager", "sti_level_senior_manager": "Senior Manager", "sti_level_senior_expert_senior_project_manager": "Senior Expert / Senior Project Manager", "sti_level_manager_selected_expert_project_manager": "Manager / Selected Expert / Project Manager", "sti_level_others": "Others", "sti_level_executive_manager_senior_group_manager": "Executive Manager / Senior Group Manager", "sti_level_group_manager_lead_sales_manager": "Group Manager / Lead Sales Manager", "sti_level_senior_manager_senior_sales_manager": "Senior Manager / Senior Sales Manager", "sti_level_manager_selected_sales_manager": "Manager / Selected Sales Manager", "sti_in_range": "Within range", "sti_out_range": "Outside range", "cost_header_charge": "Charge", "cost_header_percent": "Percent (%)", "cost_header_base": "Base", "cost_header_obs": "Observation", "cost_header_bonus": "Applies to Bonus", "cost_header_vacation": "Applies to Vacation", "cost_header_13th": "Applies to 13th", "sti_table_header_level": "Career Level", "sti_table_header_pct": "STI %" },
    "Español": { "sidebar_title": "Simulador de Remuneración<br><span style='font-size: 14px; font-weight: 400;'>Región Américas</span>", "menu_comp": "Comparador de Remuneración", "title_comp": "Comparador de Remuneración", "prop_title": "Remuneración Propuesta", "cand_title": "Remuneración del Candidato", "comp_analysis_title": "Análisis Comparativo", "comp_net_salary": "Salario Neto Mensual", "comp_total_comp": "Remuneración Total Anual", "comp_employer_cost": "Costo Total Anual (Empleador)", "cost_total_label": "Costo Total del Empleador (Salario + Bono + Encargos)", "cost_multiplier_label": "Multiplicador de Costo (vs Salario Base 12 meses)", "cost_months_label": "Meses considerados (Base Salarial)", "variation": "Variación", "other_deductions": "Otras Deducciones Mensuales", "salary_tooltip": "Su salario mensual antes de impuestos y deducciones.", "dependents_tooltip": "Número de dependientes para deducción en el Impuesto de Renta (solo aplicable en Brasil).", "bonus_tooltip": "Monto total del bono esperado en el año (pago único o en cuotas).", "other_deductions_tooltip": "Suma de otras deducciones mensuales recurrentes (ej: plan de salud, ticket de comida, cuota sindical).", "sti_area_tooltip": "Seleccione su área (Ventas o No Ventas) para verificar el rango del bono (STI).", "sti_level_tooltip": "Seleccione su nivel de carrera para verificar el rango del bono (STI). 'Otros' incluye niveles no listados.", "app_title": "Simulador de Salario Neto y Costo del Empleador", "menu_calc": "Simulador de Remuneración", "menu_rules": "Reglas de Contribuciones", "menu_sti_rules": "Reglas de Cálculo del STI", "menu_cost": "Costo del Empleador", "title_calc": "Simulador de Remuneración", "title_rules": "Reglas de Contribuciones", "title_sti_rules": "Reglas de Cálculo del STI", "title_cost": "Costo del Empleador", "country": "País", "salary": "Salario Bruto", "state": "Estado (EE. UU.)", "state_rate": "Impuesto Estatal (%)", "dependents": "Dependientes (Impuesto)", "bonus": "Bono", "earnings": "Ingresos", "deductions": "Descuentos", "net": "Salario Neto", "fgts_deposit": "Depósito de FGTS", "tot_earnings": "Total Ingresos", "tot_deductions": "Total Descuentos", "valid_from": "Vigencia", "rules_emp": "Contribuciones del Empleado", "rules_er": "Contribuciones del Empleador", "rules_table_desc": "Descripción", "rules_table_rate": "Tasa (%)", "rules_table_base": "Base de Cálculo", "rules_table_obs": "Notas / Tope", "official_source": "Fuente Oficial", "employer_cost_total": "Costo Total del Empleador", "annual_comp_title": "Composición de la Remuneración Total Bruta", "annual_salary": "Salario Anual", "annual_bonus": "Bono", "annual_total": "Remuneración Total", "months_factor": "Meses considerados", "pie_chart_title_dist": "Distribución de la Remuneración Total", "choose_country": "Seleccione un país", "menu_title": "Menú", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalles de las Contribuciones Obligatorias", "sti_area_non_sales": "No Ventas", "sti_area_sales": "Ventas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Miembros del GEB", "sti_level_executive_manager": "Gerente Ejecutivo", "sti_level_senior_group_manager": "Gerente de Grupo Sénior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Experto Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sénior", "sti_level_senior_expert_senior_project_manager": "Experto Sénior / Gerente de Proyecto Sénior", "sti_level_manager_selected_expert_project_manager": "Gerente / Experto Seleccionado / Gerente de Proyecto", "sti_level_others": "Otros", "sti_level_executive_manager_senior_group_manager": "Gerente Ejecutivo / Gerente de Grupo Sénior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Ventas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sénior / Gerente de Ventas Sénior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Ventas Seleccionado", "sti_in_range": "Dentro del rango", "sti_out_range": "Fuera del rango", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observación", "cost_header_bonus": "Incide Bono", "cost_header_vacation": "Incide Vacaciones", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nivel de Carrera", "sti_table_header_pct": "STI %" }
}
COUNTRIES_FALLBACK = {"Brasil": {"symbol": "R$", "flag": "🇧🇷", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "México": {"symbol": "MX$", "flag": "🇲🇽", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Chile": {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": False}}, "Argentina": {"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01", "benefits": {"ferias": False, "decimo": False}}, "Canadá": {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01", "benefits": {"ferias": False, "decimo": False}}}
STI_CONFIG_FALLBACK = {"STI_RANGES": { "Non Sales": { "CEO": [1.00, 1.00], "Members of the GEB": [0.50, 0.80], "Executive Manager": [0.45, 0.70], "Senior Group Manager": [0.40, 0.60], "Group Manager": [0.30, 0.50], "Lead Expert / Program Manager": [0.25, 0.40], "Senior Manager": [0.20, 0.40], "Senior Expert / Senior Project Manager": [0.15, 0.35], "Manager / Selected Expert / Project Manager": [0.10, 0.30], "Others": [0.0, 0.10] }, "Sales": { "Executive Manager / Senior Group Manager": [0.45, 0.70], "Group Manager / Lead Sales Manager": [0.35, 0.50], "Senior Manager / Senior Sales Manager": [0.25, 0.45], "Manager / Selected Sales Manager": [0.20, 0.35], "Others": [0.0, 0.15] } }, "STI_LEVEL_OPTIONS": { "Non Sales": [ "CEO", "Members of the GEB", "Executive Manager", "Senior Group Manager", "Group Manager", "Lead Expert / Program Manager", "Senior Manager", "Senior Expert / Senior Project Manager", "Manager / Selected Expert / Project Manager", "Others" ], "Sales": [ "Executive Manager / Senior Group Manager", "Group Manager / Lead Sales Manager", "Senior Manager / Senior Sales Manager", "Manager / Selected Sales Manager", "Others" ]}}
BR_INSS_FALLBACK = { "vigencia": "2025-01-01", "teto_contribuicao": 1146.68, "teto_base": 8157.41, "faixas": [ {"ate": 1412.00, "aliquota": 0.075}, {"ate": 2666.68, "aliquota": 0.09}, {"ate": 4000.03, "aliquota": 0.12}, {"ate": 8157.41, "aliquota": 0.14} ] }
BR_IRRF_FALLBACK = { "vigencia": "2025-01-01", "deducao_dependente": 189.59, "faixas": [ {"ate": 2259.20, "aliquota": 0.00, "deducao": 0.00}, {"ate": 2826.65, "aliquota": 0.075, "deducao": 169.44}, {"ate": 3751.05, "aliquota": 0.15, "deducao": 381.44}, {"ate": 4664.68, "aliquota": 0.225, "deducao": 662.77}, {"ate": 999999999.0, "aliquota": 0.275, "deducao": 896.00} ] }

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
    "CEO": "sti_level_ceo", "Members of the GEB": "sti_level_members_of_the_geb", "Executive Manager": "sti_level_executive_manager", "Senior Group Manager": "sti_level_senior_group_manager", "Group Manager": "sti_level_group_manager", "Lead Expert / Program Manager": "sti_level_lead_expert_program_manager", "Senior Manager": "sti_level_senior_manager", "Senior Expert / Senior Project Manager": "sti_level_senior_expert_senior_project_manager", "Manager / Selected Expert / Project Manager": "sti_level_manager_selected_expert_project_manager", "Others": "sti_level_others", "Executive Manager / Senior Group Manager": "sti_level_executive_manager_senior_group_manager", "Group Manager / Lead Sales Manager": "sti_level_group_manager_lead_sales_manager", "Senior Manager / Senior Sales Manager": "sti_level_senior_manager_senior_sales_manager", "Manager / Selected Sales Manager": "sti_level_manager_selected_sales_manager"
}

def load_tables_data():
    country_tables_dict = {
        "TABLES": COUNTRY_TABLES_DATA.get("TABLES", TABLES_DEFAULT),
        "EMPLOYER_COST": COUNTRY_TABLES_DATA.get("EMPLOYER_COST", EMPLOYER_COST_DEFAULT),
        "REMUN_MONTHS": COUNTRY_TABLES_DATA.get("REMUN_MONTHS", REMUN_MONTHS_DEFAULT)
    }
    return US_STATE_RATES, country_tables_dict, BR_INSS_TBL, BR_IRRF_TBL

# ======================== FUNÇÕES DE CÁLCULO E AUXÍLIO =========================
def get_sti_range(area: str, level: str) -> Tuple[float, float]:
    area_tbl = STI_RANGES.get(area, {})
    rng = area_tbl.get(level)
    return rng if rng else (0.0, None)

def calc_inss_progressivo(salario: float, inss_tbl: Dict[str, Any]) -> float:
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
    if not isinstance(irrf_tbl, dict): return 0.0
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
        v = salary * float(aliq); total_ded += v; lines.append((k, 0.0, v))
    if other_deductions > 0: lines.append(("Outras Deduções", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def us_net(salary: float, other_deductions: float, state_code: str, state_rate: float):
    FICA_WAGE_BASE_MONTHLY = ANNUAL_CAPS["US_FICA"] / 12.0
    lines = [("Base Pay", salary, 0.0)]; total_earn = salary
    salario_base_fica = min(salary, FICA_WAGE_BASE_MONTHLY); fica = salario_base_fica * 0.062
    medic = salary * 0.0145; total_ded = fica + medic
    lines += [("FICA (Social Security)", 0.0, fica), ("Medicare", 0.0, medic)]
    if state_code and state_rate is not None and state_rate > 0:
        sttax = salary * state_rate; total_ded += sttax; lines.append((f"State Tax ({state_code})", 0.0, sttax))
    if other_deductions > 0: lines.append(("Other Deductions", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def ca_net(salary: float, other_deductions: float, ca_tbl: Dict[str, Any]):
    lines = [("Base Pay", salary, 0.0)]; total_earn = salary
    cpp_base = max(0, min(salary, ca_tbl["cpp_cap_monthly"]) - ca_tbl["cpp_exempt_monthly"]); cpp = cpp_base * ca_tbl["cpp_rate"]
    cpp2_base = max(0, min(salary, ca_tbl["cpp2_cap_monthly"]) - ca_tbl["cpp_cap_monthly"]); cpp2 = cpp2_base * ca_tbl["cpp2_rate"]
    ei_base = min(salary, ca_tbl["ei_cap_monthly"]); ei = ei_base * ca_tbl["ei_rate"]
    income_tax = salary * 0.15
    total_ded = cpp + cpp2 + ei + income_tax
    lines.append(("CPP", 0.0, cpp)); lines.append(("CPP2", 0.0, cpp2)); lines.append(("EI", 0.0, ei)); lines.append(("Income Tax (Est.)", 0.0, income_tax))
    if other_deductions > 0: lines.append(("Other Deductions", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def mx_net(salary: float, other_deductions: float, tables_ext: Dict[str, Any]):
    lines = [("Base", salary, 0.0)]; total_earn = salary; total_ded = 0.0
    rates = tables_ext.get("TABLES", {}).get("México", {}).get("rates", {}) or TABLES_DEFAULT.get("México", {}).get("rates", {})
    imss_rate = rates.get("IMSS_Simplificado", 0.05) or rates.get("IMSS", 0.05)
    isr_rate = rates.get("ISR_Simplificado", 0.15) or rates.get("ISR", 0.15)
    imss_base = min(salary, MX_IMSS_CAP_MONTHLY)
    imss = imss_base * imss_rate; total_ded += imss
    lines.append(("IMSS (Est.)", 0.0, imss))
    isr = (salary - imss) * isr_rate
    total_ded += isr
    lines.append(("ISR (Est.)", 0.0, isr))
    if other_deductions > 0: lines.append(("Otras Deducciones", 0.0, other_deductions))
    total_ded += other_deductions
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def calc_country_net(country_code: str, salary: float, other_deductions: float, dependentes: int, state_code: str = None, state_rate: float = None, tables_ext=None, br_inss_tbl=None, br_irrf_tbl=None):
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
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(country_code, 12.0)
    enc_list = tables_ext.get("EMPLOYER_COST", {}).get(country_code, [])
    country_info = COUNTRIES.get(country_code, {})
    symbol_local = country_info.get("symbol", "")
    benefits = country_info.get("benefits", {"ferias": False, "decimo": False})
    df = pd.DataFrame(enc_list); df_display = pd.DataFrame()
    if not df.empty:
        df_display = df.copy()
        df_display[T.get("cost_header_charge", "Encargo")] = df_display["nome"]
        df_display["percentual"] = df_display["percentual"].astype(float)
        df_display[T.get("cost_header_percent", "%")] = df_display["percentual"].apply(lambda p: f"{p:.2f}%")
        df_display[T.get("cost_header_base", "Base")] = df_display["base"]
        df_display[T.get("cost_header_obs", "Obs")] = df_display.apply(lambda row: fmt_cap(row.get('teto'), symbol_local) if row.get('teto') is not None else row.get('obs', '—'), axis=1)
        df_display[T.get("cost_header_bonus", "Incide Bônus")] = ["✅" if b else "❌" for b in df_display["bonus"]]
        cols = [T.get("cost_header_charge"), T.get("cost_header_percent"), T.get("cost_header_base"), T.get("cost_header_bonus"), T.get("cost_header_obs")]
        if benefits.get("ferias", False): df_display[T.get("cost_header_vacation", "Incide Férias")] = ["✅" if b else "❌" for b in df_display["ferias"]]; cols.insert(3, T.get("cost_header_vacation"))
        if benefits.get("decimo", False): df_display[T.get("cost_header_13th", "Incide 13º")] = ["✅" if b else "❌" for b in df_display["decimo"]]; insert_pos = 4 if benefits.get("ferias", False) else 3; cols.insert(insert_pos, T.get("cost_header_13th"))
        df_display = df_display[cols]
    salario_anual_base = salary * 12.0; salario_anual_beneficios = salary * months; total_cost_items = []
    for index, item in df.iterrows():
        perc = item.get("percentual", 0.0) / 100.0; teto = item.get("teto"); incide_bonus = item.get("bonus", False)
        base_calc_anual = salario_anual_base if country_code in ["Estados Unidos", "Canadá"] else salario_anual_beneficios
        if incide_bonus: base_calc_anual += bonus
        if teto is not None and isinstance(teto, (int, float)):
            if country_code == "Canadá" and item.get("nome") == "CPP2 (ER)":
                base_calc_anual = max(0, min(base_calc_anual, ANNUAL_CAPS["CA_CPP_YMPEx2"]) - ANNUAL_CAPS["CA_CPP_YMPEx1"])
            else:
                base_calc_anual = min(base_calc_anual, teto)
        custo_item = base_calc_anual * perc; total_cost_items.append(custo_item)
    total_encargos = sum(total_cost_items); custo_total_anual = (salary * months) + bonus + total_encargos
    mult = (custo_total_anual / salario_anual_base) if salario_anual_base > 0 else 0.0
    return custo_total_anual, mult, df_display, months

def get_sti_area_map(T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    display_list = [T.get("sti_area_non_sales", "Non Sales"), T.get("sti_area_sales", "Sales")]; keys = ["Non Sales", "Sales"]
    return display_list, dict(zip(display_list, keys))

def get_sti_level_map(area: str, T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    keys = STI_LEVEL_OPTIONS.get(area, []);
    display_list = [T.get(STI_I18N_KEYS.get(key, key), key) for key in keys]
    return display_list, dict(zip(display_list, keys))

def display_input_fields_comparator(prefix: str, defaults: dict, T: dict, country: str, symbol: str, us_state_rates: dict):
    params = {}
    salario_default = defaults.get("salario", 10000.0)
    bonus_default = defaults.get("bonus", 0.0)

    if country == "Brasil":
        st.markdown(f"<h5>{T.get('salary', 'Salário Bruto')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["salary"] = st.number_input("Salário", min_value=0.0, value=salario_default, step=100.0, key=f"salary_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"<h5>{T.get('dependents', 'Dependentes')} (IR)</h5>", unsafe_allow_html=True)
        params["dependentes"] = st.number_input("Dependentes", min_value=0, value=0, step=1, key=f"dep_{prefix}", label_visibility="collapsed")
        st.markdown(f"<h5>{T.get('other_deductions', 'Outras Deduções')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["other_deductions"] = st.number_input("Outras Deduções", min_value=0.0, value=0.0, step=10.0, key=f"other_ded_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"<h5>{T.get('bonus', 'Bônus')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["bonus_anual"] = st.number_input("Bônus", min_value=0.0, value=bonus_default, step=100.0, key=f"bonus_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        params["state_code"], params["state_rate"] = None, None
    elif country == "Estados Unidos":
        st.markdown(f"<h5>{T.get('salary', 'Gross Salary')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["salary"] = st.number_input("Salário", min_value=0.0, value=salario_default, step=100.0, key=f"salary_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"<h5>{T.get('state', 'State')}</h5>", unsafe_allow_html=True)
        params["state_code"] = st.selectbox("Estado", list(us_state_rates.keys()), index=0, key=f"state_{prefix}", label_visibility="collapsed")
        default_rate = float(us_state_rates.get(params["state_code"], 0.0))
        st.markdown(f"<h5>{T.get('state_rate', 'State Tax')} (%)</h5>", unsafe_allow_html=True)
        params["state_rate"] = st.number_input("Taxa Estadual", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key=f"state_rate_{prefix}", label_visibility="collapsed")
        st.markdown(f"<h5>{T.get('other_deductions', 'Other Deductions')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["other_deductions"] = st.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key=f"other_ded_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"<h5>{T.get('bonus', 'Bonus')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["bonus_anual"] = st.number_input("Bônus", min_value=0.0, value=bonus_default, step=100.0, key=f"bonus_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        params["dependentes"] = 0
    else:
        st.markdown(f"<h5>{T.get('salary', 'Salário Bruto')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["salary"] = st.number_input("Salário", min_value=0.0, value=salario_default, step=100.0, key=f"salary_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"<h5>{T.get('other_deductions', 'Outras Deduções')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["other_deductions"] = st.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key=f"other_ded_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"<h5>{T.get('bonus', 'Bônus')} <span>({symbol})</span></h5>", unsafe_allow_html=True)
        params["bonus_anual"] = st.number_input("Bônus", min_value=0.0, value=bonus_default, step=100.0, key=f"bonus_{prefix}", label_visibility="collapsed", format=INPUT_FORMAT)
        params["dependentes"], params["state_code"], params["state_rate"] = 0, None, None
    return params

# ============================== CSS ================================
st.markdown("""<style>
:root {
    --sidebar-bg: #0a2540;
    --primary-color: #2667FF;
    --background-color: #F8F9FA;
    --text-color: #334155;
    --light-text-color: #64748B;
    --card-bg: #D1E5F9;
    --white: #ffffff;
}
div.block-container { max-width: 1100px; padding-left: 1rem; padding-right: 1rem; }
html, body { background-color: var(--background-color); color: var(--text-color); font-family:'Segoe UI', Helvetica, Arial, sans-serif; }
h1, h2, h3, h4, .country-title { color: var(--primary-color); }
.stMarkdown h5 { font-size: 15px; font-weight: 500; line-height: 1.2; color: var(--primary-color); margin-bottom: 0.2rem !important; }
.stMarkdown h5 span { font-weight: 400; color: var(--text-color); font-size: 14px; }
.metric-card, .annual-card-base { min-height: 95px !important; padding: 10px 15px !important; display: flex; flex-direction: column; justify-content: center; text-align: center; box-sizing: border-box; background: var(--card-bg); border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 10px; border-left: none !important; transition: all 0.3s ease; }
.metric-card:hover{ box-shadow: 0 6px 16px rgba(0,0,0,0.12); transform: translateY(-2px); }
.metric-card h4, .annual-card-base h4 { margin:0; font-size:15px; font-weight: 500; color:var(--text-color); }
.metric-card h3, .annual-card-base h3 { margin: 4px 0 0; color:var(--primary-color); font-size:18px; font-weight: 700; }
.metric-card p { font-size: 14px; color: var(--light-text-color); margin: 0; }
.table-wrap { background:var(--white); border:1px solid #d0d7de; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
.monthly-table { width: 100%; border-collapse: collapse; margin: 0; border: none; font-size: 15px; }
.monthly-table thead th { background-color: var(--primary-color); color: var(--white); padding: 12px 15px; text-align: left; font-weight: 600; }
.monthly-table tbody td { padding: 10px 15px; border-bottom: 1px solid #eee; }
.monthly-table tbody tr:nth-child(even) { background-color: #fcfcfc; }
.monthly-table tbody tr:last-child td { border-bottom: none; }
hr { border:0; height:1px; background:#e2e6ea; margin:24px 0; border-radius:1px; }
section[data-testid="stSidebar"]{ background-color: var(--sidebar-bg) !important; width: 350px !important; min-width: 350px !important; max-width: 350px !important; }
div[data-testid="stSidebar-resizer"] { display: none; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span { color: var(--white) !important; }
section[data-testid="stSidebar"] h2 { margin-bottom: 25px !important; }
section[data-testid="stSidebar"] h3 { margin-bottom: 0.5rem !important; margin-top: 1rem !important; }
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label { margin-bottom: 0.5rem !important; }
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div[data-baseweb="select"] { margin-top: 0 !important; }
section[data-testid="stSidebar"] .stTextInput input, section[data-testid="stSidebar"] .stNumberInput input, section[data-testid="stSidebar"] .stSelectbox input, section[data-testid="stSidebar"] .stNumberInput input:focus, section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *, section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{ color: var(--text-color) !important; background: var(--white) !important; }
.country-header{ display:flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 5px; }
.country-flag{ font-size:45px; }
.country-title{ font-size:36px; font-weight:700; color: var(--primary-color); }
.card-row-spacing { margin-top: 20px; }
</style>""", unsafe_allow_html=True)


# ============================== SIDEBAR ===============================
with st.sidebar:
    T_temp = I18N.get(st.session_state.get('idioma', 'Português'), I18N_FALLBACK["Português"])
    st.markdown(f"<h2 style='color:white; text-align:center; font-size:20px; line-height: 1.3; margin-bottom: 25px;'>{T_temp.get('sidebar_title')}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-bottom: 0.5rem;'>{T_temp.get('language_title')}</h3>", unsafe_allow_html=True)
    if 'idioma' not in st.session_state: st.session_state.idioma = 'Português'
    idioma = st.selectbox("Language Select", options=list(I18N.keys()), index=list(I18N.keys()).index(st.session_state.idioma), key="lang_select", label_visibility="collapsed")
    T = I18N.get(idioma, I18N_FALLBACK["Português"])
    if idioma != st.session_state.idioma:
        st.session_state.idioma = idioma
        st.session_state.active_menu_key = "calc" 
        if 'country_select' in st.session_state: del st.session_state['country_select']
        st.rerun()

    st.markdown(f"<h3 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>{T.get('country')}</h3>", unsafe_allow_html=True)
    country_options = list(COUNTRIES.keys())
    if not country_options: st.error("Erro fatal: Arquivo 'countries.json' não carregou países."); st.stop()
    default_country = "Brasil" if "Brasil" in country_options else country_options[0]
    if 'country_select' not in st.session_state: st.session_state.country_select = default_country
    if st.session_state.country_select not in country_options: st.session_state.country_select = default_country
    try: country_index = country_options.index(st.session_state.country_select)
    except ValueError: country_index = 0
    country_selected = st.selectbox(T.get("choose_country"), country_options, index=country_index, key="country_select", label_visibility="collapsed")
    _COUNTRY_CODE_FOR_FMT = country_selected
    if country_selected != st.session_state.country_select:
        st.session_state.country_select = country_selected
        st.rerun()

    st.markdown(f"<h3 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>{T.get('menu_title', 'Menu')}</h3>", unsafe_allow_html=True)
    
    MENU_KEYS = ["calc", "comp", "rules", "sti_rules", "cost"]
    menu_labels = {key: T.get(f"menu_{key}", key.replace('_', ' ').title()) for key in MENU_KEYS}
    
    if 'active_menu_key' not in st.session_state or st.session_state.active_menu_key not in MENU_KEYS:
        st.session_state.active_menu_key = "calc"
    
    selected_key = st.radio(
        "Menu Select", 
        options=MENU_KEYS, 
        index=MENU_KEYS.index(st.session_state.active_menu_key),
        format_func=lambda key: menu_labels.get(key),
        label_visibility="collapsed", 
        key="menu_radio_widget"
    )

    if selected_key != st.session_state.active_menu_key:
        st.session_state.active_menu_key = selected_key
        st.rerun()

# ======================= INICIALIZAÇÃO PÓS-SIDEBAR =======================
if 'idioma' in st.session_state: T = I18N.get(st.session_state.idioma, I18N_FALLBACK["Português"])
else: T = I18N_FALLBACK["Português"]
country = st.session_state.get('country_select', 'Brasil')
active_menu_key = st.session_state.get('active_menu_key', 'calc')
US_STATE_RATES_LOADED, COUNTRY_TABLES_LOADED, BR_INSS_TBL_LOADED, BR_IRRF_TBL_LOADED = load_tables_data()
COUNTRY_TABLES = COUNTRY_TABLES_LOADED
if country not in COUNTRIES: st.error(f"Erro: País '{country}' não encontrado."); st.stop()
try:
    symbol = COUNTRIES[country]["symbol"]; flag = COUNTRIES[country]["flag"]; valid_from = COUNTRIES[country]["valid_from"]
except KeyError as e: st.error(f"Erro de Configuração: Falta a chave '{e}' para o país '{country}'."); st.stop()

# ======================= TÍTULO DINÂMICO ==============================
title_key = f"title_{active_menu_key}"
title = T.get(title_key, active_menu_key.replace("_", " ").title())
st.markdown(f"<div class='country-header'><div class='country-title'>{title}</div><div class='country-flag'>{flag}</div></div>", unsafe_allow_html=True)
st.write("---")

# ========================= SIMULADOR DE REMUNERAÇÃO (Página Principal) ==========================
if active_menu_key == "calc":
    area_options_display, area_display_map = get_sti_area_map(T)
    st.subheader(T.get("calc_params_title", "Parameters"))

    def get_simple_label(T_key, default_text, symbol=None):
        label = T.get(T_key, default_text)
        if label.endswith('(STI)'): label = label.replace('(STI)', '').strip()
        if symbol: label = f"{label} <span>({symbol})</span>"
        return label

    def get_sti_label(T_key, default_text):
        label = T.get(T_key, default_text)
        if not label.endswith('(STI)'): label = f"{label} (STI)"
        return label

    if country == "Brasil":
        st.markdown(f"""<div style="display: flex; justify-content: space-between;"><div style="width: 25%;"><h5>{get_simple_label('salary', 'Salário Bruto', symbol)}</h5></div><div style="width: 25%;"><h5>{get_simple_label('dependents', 'Dependentes')} (IR)</h5></div><div style="width: 25%;"><h5>{get_simple_label('other_deductions', 'Outras Deduções', symbol)}</h5></div><div style="width: 25%;"><h5>{get_simple_label('bonus', 'Bônus', symbol)}</h5></div></div>""", unsafe_allow_html=True)
        cols = st.columns(4)
        salary = cols[0].number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        dependentes = cols[1].number_input("Dependentes", min_value=0, value=0, step=1, key="dep_input", help=T.get("dependents_tooltip"), label_visibility="collapsed")
        other_deductions = cols[2].number_input("Outras Deduções", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        bonus_anual = cols[3].number_input("Bônus", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"""<div style="display: flex; justify-content: space-between; margin-top: 1rem;"><div style="width: 25%;"><h5>{get_sti_label('area', 'Área')}</h5></div><div style="width: 25%;"><h5>{get_sti_label('level', 'Career Level')}</h5></div><div style="width: 50%;"></div></div>""", unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        state_code, state_rate = None, None
        dependentes_fixed = dependentes
    elif country == "Estados Unidos":
        st.markdown(f"""<div style="display: flex; justify-content: space-between;"><div style="width: 20%;"><h5>{get_simple_label('salary', 'Gross Salary', symbol)}</h5></div><div style="width: 20%;"><h5>{get_simple_label('state', 'State')}</h5></div><div style="width: 20%;"><h5>{get_simple_label('state_rate', 'State Tax')} (%)</h5></div><div style="width: 20%;"><h5>{get_simple_label('other_deductions', 'Other Deductions', symbol)}</h5></div><div style="width: 20%;"><h5>{get_simple_label('bonus', 'Bonus', symbol)}</h5></div></div>""", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        salary = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        state_code = c2.selectbox("Estado", list(US_STATE_RATES.keys()), index=0, key="state_select_main", help=T.get("state"), label_visibility="collapsed")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input("Taxa Estadual", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input", help=T.get("state_rate"), label_visibility="collapsed")
        other_deductions = c4.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        bonus_anual = c5.number_input("Bônus", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"""<div style="display: flex; justify-content: space-between; margin-top: 1rem;"><div style="width: 20%;"><h5>{get_sti_label('area', 'Area')}</h5></div><div style="width: 20%;"><h5>{get_sti_label('level', 'Career Level')}</h5></div><div style="width: 60%;"></div></div>""", unsafe_allow_html=True)
        r1, r2, r3, r4, r5 = st.columns(5)
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes_fixed = 0
    else:
        st.markdown(f"""<div style="display: flex; justify-content: space-between;"><div style="width: 25%;"><h5>{get_simple_label('salary', 'Salário Bruto', symbol)}</h5></div><div style="width: 25%;"><h5>{get_simple_label('other_deductions', 'Outras Deduções', symbol)}</h5></div><div style="width: 25%;"><h5>{get_simple_label('bonus', 'Bônus', symbol)}</h5></div><div style="width: 25%;"></div></div>""", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        salary = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        other_deductions = c2.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        bonus_anual = c3.number_input("Bônus", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        st.markdown(f"""<div style="display: flex; justify-content: space-between; margin-top: 1rem;"><div style="width: 25%;"><h5>{get_sti_label('area', 'Área')}</h5></div><div style="width: 25%;"><h5>{get_sti_label('level', 'Career Level')}</h5></div><div style="width: 50%;"></div></div>""", unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes_fixed, state_code, state_rate = 0, None, None
    st.write("---")
    st.subheader(T.get("monthly_comp_title", "Remuneração Mensal"))
    calc = calc_country_net(country, salary=salary, other_deductions=other_deductions, dependentes=dependentes_fixed, state_code=state_code, state_rate=state_rate, tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL)
    df_detalhe = pd.DataFrame(calc["lines"], columns=["Descrição", T.get("earnings"), T.get("deductions")])
    df_detalhe[T.get("earnings")] = df_detalhe[T.get("earnings")].apply(lambda v: money_or_blank(v, symbol))
    df_detalhe[T.get("deductions")] = df_detalhe[T.get("deductions")].apply(lambda v: money_or_blank(v, symbol))
    st.markdown(f"<div class='table-wrap'>{df_detalhe.to_html(index=False, classes='monthly-table')}</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-row-spacing'>", unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(f"<div class='metric-card'><h4>💰 {T.get('tot_earnings')}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card'><h4>📉 {T.get('tot_deductions')}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card'><h4>💵 {T.get('net')}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if country == "Brasil": st.markdown(f"<div style='margin-top: 10px; padding: 5px 0;'><p style='font-size: 17px; font-weight: 600; color: #2667FF;'>💼 {T.get('fgts_deposit')}: {fmt_money(calc['fgts'], symbol)}</p></div>", unsafe_allow_html=True)
    st.write("---")
    st.subheader(T.get("annual_comp_title"))
    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, 12.0)
    salario_anual = salary * months
    total_anual = salario_anual + bonus_anual
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0
    pct_txt = f"{bonus_pct*100:.1f}%"
    faixa_txt = f"≤ {(max_pct or 0)*100:.0f}%" if level == "Others" else f"{min_pct*100:.0f}% – {max_pct*100:.0f}%"
    dentro = (bonus_pct <= (max_pct or 0)) if level == "Others" else (min_pct <= bonus_pct <= max_pct)
    cor = "#2667FF" if dentro else "#d32f2f"; status_txt = T.get("sti_in_range") if dentro else T.get("sti_out_range")
    sti_note_text = f"<span style='color:{cor};'><strong>{pct_txt}</strong> — <strong>{status_txt}</strong></span> ({faixa_txt}) — <em>{area_display} • {level_display}</em>"
    col_salario, col_bonus, col_total = st.columns(3)
    col_salario.markdown(f"<div class='metric-card'><h4> {T.get('annual_salary')} </h4><h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    col_bonus.markdown(f"<div class='metric-card'><h4 style='color:{cor};'> {T.get('annual_bonus')} </h4><h3 style='color:{cor};'>{fmt_money(bonus_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    col_total.markdown(f"<div class='metric-card'><h4> {T.get('annual_total')} </h4><h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top: 10px; padding: 5px 0;'><p style='font-size: 17px; font-weight: 600; color: #2667FF; margin: 0;'>📅 {T.get('months_factor')}: {months}</p><p style='font-size: 17px; font-weight: 600; color: #2667FF; margin: 5px 0 0 0;'>🎯 STI Ratio: {sti_note_text}</p></div>", unsafe_allow_html=True)
    st.write("---")
    chart_df = pd.DataFrame({"Componente": [T.get('annual_salary'), T.get('annual_bonus')], "Valor": [salario_anual, bonus_anual]})
    base = alt.Chart(chart_df).transform_joinaggregate(Total='sum(Valor)').transform_calculate(Percent='datum.Valor / datum.Total', Label=alt.expr.if_(alt.datum.Valor > alt.datum.Total * 0.05, alt.datum.Componente + " (" + alt.expr.format(alt.datum.Percent, ".1%") + ")", ""))
    pie = base.mark_arc(outerRadius=120, innerRadius=80, cornerRadius=2).encode(theta=alt.Theta("Valor:Q", stack=True), color=alt.Color("Componente:N", legend=None, scale=alt.Scale(range=['#2667FF', '#D3D3D3'])), order=alt.Order("Percent:Q", sort="descending"), tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f")])
    text = base.mark_text(radius=140).encode(text=alt.Text("Label:N"), theta=alt.Theta("Valor:Q", stack=True), order=alt.Order("Percent:Q", sort="descending"), color=alt.value("#334155"))
    final_chart = alt.layer(pie, text).properties(title=T.get("pie_chart_title_dist")).configure_view(strokeWidth=0).configure_title(fontSize=17, anchor='middle', color='#2667FF')
    st.altair_chart(final_chart, use_container_width=True)

# ========================= COMPARADOR DE REMUNERAÇÃO ==========================
elif active_menu_key == "comp":
    st.subheader(T.get("calc_params_title", "Parâmetros de Cálculo"))
    col_prop, col_cand = st.columns(2)

    with col_prop:
        st.markdown(f"<h4>{T.get('prop_title', 'Remuneração Proposta')}</h4>", unsafe_allow_html=True)
        params_prop = display_input_fields_comparator(prefix="prop", defaults={"salario": 12000.0, "bonus": 10000.0}, T=T, country=country, symbol=symbol, us_state_rates=US_STATE_RATES_LOADED)

    with col_cand:
        st.markdown(f"<h4>{T.get('cand_title', 'Remuneração do Candidato')}</h4>", unsafe_allow_html=True)
        params_cand = display_input_fields_comparator(prefix="cand", defaults={"salario": 10000.0, "bonus": 8000.0}, T=T, country=country, symbol=symbol, us_state_rates=US_STATE_RATES_LOADED)

    st.write("---")
    
    # --- Cálculos para ambos os cenários ---
    calc_prop = calc_country_net(country, salary=params_prop["salary"], other_deductions=params_prop["other_deductions"], dependentes=params_prop["dependentes"], state_code=params_prop["state_code"], state_rate=params_prop["state_rate"], tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL)
    calc_cand = calc_country_net(country, salary=params_cand["salary"], other_deductions=params_cand["other_deductions"], dependentes=params_cand["dependentes"], state_code=params_cand["state_code"], state_rate=params_cand["state_rate"], tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL)
    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, 12.0)
    
    # Valores Anuais Proposta
    salario_anual_prop = params_prop['salary'] * months
    bonus_anual_prop = params_prop['bonus_anual']
    total_anual_prop = salario_anual_prop + bonus_anual_prop
    
    # Valores Anuais Candidato
    salario_anual_cand = params_cand['salary'] * months
    bonus_anual_cand = params_cand['bonus_anual']
    total_anual_cand = salario_anual_cand + bonus_anual_cand

    # Variações Anuais
    salario_anual_diff = salario_anual_prop - salario_anual_cand
    salario_anual_pct = (salario_anual_diff / salario_anual_cand * 100) if salario_anual_cand > 0 else 0
    bonus_anual_diff = bonus_anual_prop - bonus_anual_cand
    bonus_anual_pct = (bonus_anual_diff / bonus_anual_cand * 100) if bonus_anual_cand > 0 else 0
    total_anual_diff = total_anual_prop - total_anual_cand
    total_anual_pct = (total_anual_diff / total_anual_cand * 100) if total_anual_cand > 0 else 0

    # --- Seção: Composição Anual (com Variação) ---
    st.subheader(T.get("annual_comp_title", "Composição da Remuneração Total Anual Bruta"))
    comp_prop, comp_cand, comp_var = st.columns(3)
    
    with comp_prop:
        st.markdown(f"<h6>{T.get('prop_title', 'Proposta')}</h6>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_salary')}</h4><h3>{fmt_money(salario_anual_prop, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_bonus')}</h4><h3>{fmt_money(bonus_anual_prop, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_total')}</h4><h3>{fmt_money(total_anual_prop, symbol)}</h3></div>", unsafe_allow_html=True)
    with comp_cand:
        st.markdown(f"<h6>{T.get('cand_title', 'Candidato')}</h6>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_salary')}</h4><h3>{fmt_money(salario_anual_cand, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_bonus')}</h4><h3>{fmt_money(bonus_anual_cand, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_total')}</h4><h3>{fmt_money(total_anual_cand, symbol)}</h3></div>", unsafe_allow_html=True)
    with comp_var:
        st.markdown(f"<h6>{T.get('variation', 'Variação')}</h6>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_salary')}</h4><h3>{fmt_money(salario_anual_diff, symbol)}</h3><p>({salario_anual_pct:+.2f}%)</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_bonus')}</h4><h3>{fmt_money(bonus_anual_diff, symbol)}</h3><p>({bonus_anual_pct:+.2f}%)</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><h4>{T.get('annual_total')}</h4><h3>{fmt_money(total_anual_diff, symbol)}</h3><p>({total_anual_pct:+.2f}%)</p></div>", unsafe_allow_html=True)

    st.write("---")

    # --- Seção: Remuneração Mensal ---
    st.subheader(T.get("monthly_comp_title", "Remuneração Mensal Bruta e Líquida"))
    res_prop, res_cand = st.columns(2)
    with res_prop:
        st.markdown(f"<h4>{T.get('prop_title', 'Remuneração Proposta')}</h4>", unsafe_allow_html=True)
        df_detalhe_prop = pd.DataFrame(calc_prop["lines"], columns=["Descrição", T.get("earnings"), T.get("deductions")])
        df_detalhe_prop[T.get("earnings")] = df_detalhe_prop[T.get("earnings")].apply(lambda v: money_or_blank(v, symbol))
        df_detalhe_prop[T.get("deductions")] = df_detalhe_prop[T.get("deductions")].apply(lambda v: money_or_blank(v, symbol))
        st.markdown(f"<div class='table-wrap'>{df_detalhe_prop.to_html(index=False, classes='monthly-table')}</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-row-spacing'>", unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        p1.markdown(f"<div class='metric-card'><h4>💰 {T.get('tot_earnings', 'Proventos')}</h4><h3>{fmt_money(calc_prop['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
        p2.markdown(f"<div class='metric-card'><h4>📉 {T.get('tot_deductions', 'Descontos')}</h4><h3>{fmt_money(calc_prop['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
        p3.markdown(f"<div class='metric-card'><h4>💵 {T.get('net', 'Líquido')}</h4><h3>{fmt_money(calc_prop['net'], symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if country == "Brasil": st.markdown(f"<p style='font-size: 15px; text-align: center; font-weight: 600; color: #2667FF;'>💼 {T.get('fgts_deposit')}: {fmt_money(calc_prop['fgts'], symbol)}</p>", unsafe_allow_html=True)

    with res_cand:
        st.markdown(f"<h4>{T.get('cand_title', 'Remuneração do Candidato')}</h4>", unsafe_allow_html=True)
        df_detalhe_cand = pd.DataFrame(calc_cand["lines"], columns=["Descrição", T.get("earnings"), T.get("deductions")])
        df_detalhe_cand[T.get("earnings")] = df_detalhe_cand[T.get("earnings")].apply(lambda v: money_or_blank(v, symbol))
        df_detalhe_cand[T.get("deductions")] = df_detalhe_cand[T.get("deductions")].apply(lambda v: money_or_blank(v, symbol))
        st.markdown(f"<div class='table-wrap'>{df_detalhe_cand.to_html(index=False, classes='monthly-table')}</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-row-spacing'>", unsafe_allow_html=True)
        c1_cand, c2_cand, c3_cand = st.columns(3)
        c1_cand.markdown(f"<div class='metric-card'><h4>💰 {T.get('tot_earnings', 'Proventos')}</h4><h3>{fmt_money(calc_cand['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
        c2_cand.markdown(f"<div class='metric-card'><h4>📉 {T.get('tot_deductions', 'Descontos')}</h4><h3>{fmt_money(calc_cand['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
        c3_cand.markdown(f"<div class='metric-card'><h4>💵 {T.get('net', 'Líquido')}</h4><h3>{fmt_money(calc_cand['net'], symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if country == "Brasil": st.markdown(f"<p style='font-size: 15px; text-align: center; font-weight: 600; color: #2667FF;'>💼 {T.get('fgts_deposit')}: {fmt_money(calc_cand['fgts'], symbol)}</p>", unsafe_allow_html=True)

    st.write("---")

    # --- Seção Final: Análise Comparativa ---
    st.subheader(T.get("comp_analysis_title", "Análise Comparativa"))
    net_diff = calc_prop['net'] - calc_cand['net']
    net_diff_pct = (net_diff / calc_cand['net'] * 100) if calc_cand.get('net') and calc_cand['net'] > 0 else 0
    total_comp_diff = total_anual_prop - total_anual_cand
    total_comp_diff_pct = (total_comp_diff / total_anual_cand * 100) if total_anual_cand > 0 else 0
    custo_total_anual_prop, _, _, _ = calc_employer_cost(country, params_prop['salary'], params_prop['bonus_anual'], T, tables_ext=COUNTRY_TABLES)
    custo_total_anual_cand, _, _, _ = calc_employer_cost(country, params_cand['salary'], params_cand['bonus_anual'], T, tables_ext=COUNTRY_TABLES)
    employer_cost_diff = custo_total_anual_prop - custo_total_anual_cand
    employer_cost_diff_pct = (employer_cost_diff / custo_total_anual_cand * 100) if custo_total_anual_cand > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric(label=f"📊 {T.get('comp_net_salary', 'Salário Líquido Mensal')}", value=fmt_money(calc_prop['net'], symbol), delta=f"{fmt_money(net_diff, symbol)} ({net_diff_pct:+.2f}%)")
    c2.metric(label=f"📈 {T.get('comp_total_comp', 'Remuneração Total Anual')}", value=fmt_money(total_anual_prop, symbol), delta=f"{fmt_money(total_comp_diff, symbol)} ({total_comp_diff_pct:+.2f}%)")
    c3.metric(label=f"🏢 {T.get('comp_employer_cost', 'Custo Total Anual (Empregador)')}", value=fmt_money(custo_total_anual_prop, symbol), delta=f"{fmt_money(employer_cost_diff, symbol)} ({employer_cost_diff_pct:+.2f}%)")

# =========================== REGRAS DE CONTRIBUIÇÕES ===================
elif active_menu_key == "rules":
    st.subheader(T.get("rules_expanded", "Details"))
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
    co_emp_contrib = [{"desc": "Salud", "rate": "4.00%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Pensão", "rate": "4.00%", "base": "Sal. Bruto", "obs": "-"}]
    co_er_contrib = [{"desc": "Salud Empregador", "rate": "8.50%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Pensão Empregador", "rate": "12.00%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Parafiscales", "rate": "9.00%", "base": "Salário", "obs": "SENA, ICBF, Caja"}, {"desc": "Cesantías", "rate": "8.33%", "base": "Salário", "obs": "1 Salário/Ano"}]
    country_contrib_map = { "Brasil": (br_emp_contrib, br_er_contrib), "Estados Unidos": (us_emp_contrib, us_er_contrib), "Canadá": (ca_emp_contrib, ca_er_contrib), "México": (mx_emp_contrib, mx_er_contrib), "Chile": (cl_emp_contrib, cl_er_contrib), "Argentina": (ar_emp_contrib, ar_er_contrib), "Colômbia": (co_emp_contrib, co_er_contrib), }
    official_links = { "Brasil": "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/tributos/contribuicoes-previdenciarias", "Estados Unidos": "https://www.irs.gov/businesses/small-businesses-self-employed/employment-tax-rates", "Canadá": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/payroll/payroll-deductions-contributions/canada-pension-plan-cpp/cpp-contribution-rates-maximums-exemptions.html", "México": "https://www.sat.gob.mx/consulta/29124/conoce-las-tablas-de-isr", "Chile": "https://www.previred.com/indicadores-previsionales/", "Argentina": "https://www.afip.gob.ar/aportesycontribuciones/", "Colômbia": "https://www.dian.gov.co/normatividad/Paginas/Normatividad.aspx", }
    emp_contrib_data, er_contrib_data = country_contrib_map.get(country, ([], []))
    link = official_links.get(country, "#")
    col_map = { "desc": T.get("rules_table_desc", "Desc"), "rate": T.get("rules_table_rate", "Rate"), "base": T.get("rules_table_base", "Base"), "obs": T.get("rules_table_obs", "Obs") }
    df_emp = pd.DataFrame(emp_contrib_data).rename(columns=col_map) if emp_contrib_data else pd.DataFrame()
    df_er = pd.DataFrame(er_contrib_data).rename(columns=col_map) if er_contrib_data else pd.DataFrame()
    if not df_emp.empty: st.markdown(f"#### {T.get('rules_emp', 'Employee')}"); st.dataframe(df_emp, use_container_width=True, hide_index=True)
    if not df_er.empty: st.markdown(f"#### {T.get('rules_er', 'Employer')}"); st.dataframe(df_er, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.write(""); st.markdown(f"**{T.get('valid_from', 'Vigência')}:** {valid_from}"); st.markdown(f"[{T.get('official_source', 'Fonte Oficial')}]({link})", unsafe_allow_html=True)


# =========================== REGRAS DE CÁLCULO DO STI ==================
elif active_menu_key == "sti_rules":
    header_level = T.get("sti_table_header_level", "Level"); header_pct = T.get("sti_table_header_pct", "STI %")
    st.markdown(f"#### {T.get('sti_area_non_sales', 'Non Sales')}")
    st.markdown(f"""
    | {header_level}                                               | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T.get(STI_I18N_KEYS.get("CEO", ""), "CEO")}                                |   100%   |
    | {T.get(STI_I18N_KEYS.get("Members of the GEB", ""), "GEB")}  |  50–80%  |
    | {T.get(STI_I18N_KEYS.get("Executive Manager", ""), "Exec Mgr")}   |  45–70%  |
    | {T.get(STI_I18N_KEYS.get("Senior Group Manager", ""), "Sr Grp Mgr")}  |  40–60%  |
    | {T.get(STI_I18N_KEYS.get("Group Manager", ""), "Grp Mgr")}     |  30–50%  |
    | {T.get(STI_I18N_KEYS.get("Lead Expert / Program Manager", ""), "Lead Exp")}   |  25–40%  |
    | {T.get(STI_I18N_KEYS.get("Senior Manager", ""), "Sr Mgr")}     |  20–40%  |
    | {T.get(STI_I18N_KEYS.get("Senior Expert / Senior Project Manager", ""), "Sr Exp")} |  15–35%  |
    | {T.get(STI_I18N_KEYS.get("Manager / Selected Expert / Project Manager", ""), "Mgr/Exp")} |  10–30%  |
    | {T.get(STI_I18N_KEYS.get("Others", ""), "Others")}                                   |  ≤ 10%   |
    """, unsafe_allow_html=True)
    st.markdown(f"#### {T.get('sti_area_sales', 'Sales')}")
    st.markdown(f"""
    | {header_level}                                               | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T.get(STI_I18N_KEYS.get("Executive Manager / Senior Group Manager", ""), "Exec/Sr Grp Mgr")} |  45–70%  |
    | {T.get(STI_I18N_KEYS.get("Group Manager / Lead Sales Manager", ""), "Grp/Lead Sales Mgr")}     |  35–50%  |
    | {T.get(STI_I18N_KEYS.get("Senior Manager / Senior Sales Manager", ""), "Sr/Sr Sales Mgr")} |  25–45%  |
    | {T.get(STI_I18N_KEYS.get("Manager / Selected Sales Manager", ""), "Mgr/Sales Mgr")}     |  20–35%  |
    | {T.get(STI_I18N_KEYS.get("Others", ""), "Others")}                                   |  ≤ 15%   |
    """, unsafe_allow_html=True)

# ========================= CUSTO DO EMPREGADOR ========================
elif active_menu_key == "cost":
    c1, c2 = st.columns(2)
    salary_cost = c1.number_input(f"{T.get('salary', 'Salário Bruto')} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost", format=INPUT_FORMAT)
    bonus_anual_cost = c2.number_input(f"{T.get('bonus', 'Bônus')} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_cost_input", format=INPUT_FORMAT)
    st.write("---")
    anual, mult, df_cost, months = calc_employer_cost(country, salary_cost, bonus_anual_cost, T, tables_ext=COUNTRY_TABLES)
    st.markdown(f"**{T.get('cost_total_label', 'Custo Total')}:** {fmt_money(anual, symbol)}  \n"
                  f"**{T.get('cost_multiplier_label', 'Multiplicador')}:** {mult:.3f} × (12 meses)  \n"
                  f"**{T.get('cost_months_label', 'Meses')}:** {months}")
    if not df_cost.empty: st.dataframe(df_cost, use_container_width=True, hide_index=True)
    else: st.info("Sem encargos configurados para este país.")
