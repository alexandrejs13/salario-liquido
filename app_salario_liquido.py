# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.50.18)
# Tema azul plano, multilíngue, responsivo e com STI corrigido
# (Correção Crítica: NameError na definição de Fallbacks)
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import altair as alt
import requests
import base64
from typing import Dict, Any, Tuple, List
import math
import json
import os # Essencial para caminhos de arquivo

st.set_page_config(page_title="Simulador de Salário Líquido", layout="wide")

# ======================== HELPERS INICIAIS (Formatação) =========================
def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def fmt_percent(v: float) -> str:
    if v is None: return ""
    return f"{v:.2f}%"

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
        print(f"Warning: Config file not found: {filepath}. Using default.")
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default_value

# --- Fallbacks Mínimos (Definidos PRIMEIRO, caso o JSON falhe) ---
I18N_FALLBACK = { "Português": { "sidebar_title": "Simulador de Remuneração<br>(Região das Americas)", "app_title": "Simulador de Salário Líquido e Custo do Empregador", "menu_calc": "Simulador de Remuneração", "menu_rules": "Regras de Contribuições", "menu_rules_sti": "Regras de Cálculo do STI", "menu_cost": "Custo do Empregador", "title_calc": "Simulador de Remuneração", "title_rules": "Regras de Contribuições", "title_rules_sti": "Regras de Cálculo do STI", "title_cost": "Custo do Empregador", "country": "País", "salary": "Salário Bruto", "state": "Estado (EUA)", "state_rate": "State Tax (%)", "dependents": "Dependentes (IR)", "bonus": "Bônus Anual", "other_deductions": "Outras Deduções Mensais", "earnings": "Proventos", "deductions": "Descontos", "net": "Salário Líquido", "fgts_deposit": "Depósito FGTS", "tot_earnings": "Total de Proventos", "tot_deductions": "Total de Descontos", "valid_from": "Vigência", "rules_emp": "Contribuições do Empregado", "rules_er": "Contribuições do Empregador", "rules_table_desc": "Descrição", "rules_table_rate": "Alíquota (%)", "rules_table_base": "Base de Cálculo", "rules_table_obs": "Observações / Teto", "official_source": "Fonte Oficial", "employer_cost_total": "Custo Total do Empregador", "annual_comp_title": "Composição da Remuneração Total Anual Bruta", "calc_params_title": "Parâmetros de Cálculo da Remuneração", "monthly_comp_title": "Remuneração Mensal Bruta e Líquida", "annual_salary": "📅 Salário Anual", "annual_bonus": "🎯 Bônus Anual", "annual_total": "💼 Remuneração Total Anual", "months_factor": "Meses considerados", "pie_title": "Distribuição Anual: Salário vs Bônus", "pie_chart_title_dist": "Distribuição da Remuneração Total", "reload": "Recarregar tabelas", "source_remote": "Tabelas remotas", "source_local": "Fallback local", "choose_country": "Selecione o país", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalhes das Contribuições Obrigatórias", "salary_tooltip": "Seu salário mensal antes de impostos e deduções.", "dependents_tooltip": "Número de dependentes para dedução no Imposto de Renda (aplicável apenas no Brasil).", "bonus_tooltip": "Valor total do bônus esperado no ano (pago de uma vez ou parcelado).", "other_deductions_tooltip": "Soma de outras deduções mensais recorrentes (ex: plano de saúde, vale-refeição, contribuição sindical).", "sti_area_tooltip": "Selecione sua área de atuação (Vendas ou Não Vendas) para verificar a faixa de bônus (STI).", "sti_level_tooltip": "Selecione seu nível de carreira para verificar a faixa de bônus (STI). 'Others' inclui níveis não listados.", "sti_area_non_sales": "Não Vendas", "sti_area_sales": "Vendas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Membros do GEB", "sti_level_executive_manager": "Gerente Executivo", "sti_level_senior_group_manager": "Gerente de Grupo Sênior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Especialista Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sênior", "sti_level_senior_expert_senior_project_manager": "Especialista Sênior / Gerente de Projeto Sênior", "sti_level_manager_selected_expert_project_manager": "Gerente / Especialista Selecionado / Gerente de Projeto", "sti_level_others": "Outros", "sti_level_executive_manager_senior_group_manager": "Gerente Executivo / Gerente de Grupo Sênior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Vendas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sênior / Gerente de Vendas Sênior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Vendas Selecionado", "sti_in_range": "Dentro do range", "sti_out_range": "Fora do range", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observação", "cost_header_bonus": "Incide Bônus", "cost_header_vacation": "Incide Férias", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nível de Carreira", "sti_table_header_pct": "STI %" }, "English": { "sidebar_title": "Compensation Simulator<br>(Americas Region)", "other_deductions": "Other Monthly Deductions", "salary_tooltip": "Your monthly salary before taxes and deductions.", "dependents_tooltip": "Number of dependents for Income Tax deduction (applicable only in Brazil).", "bonus_tooltip": "Total expected bonus amount for the year (paid lump sum or installments).", "other_deductions_tooltip": "Sum of other recurring monthly deductions (e.g., health plan, meal voucher, union dues).", "sti_area_tooltip": "Select your area (Sales or Non Sales) to check the bonus (STI) range.", "sti_level_tooltip": "Select your career level to check the bonus (STI) range. 'Others' includes unlisted levels.", "app_title": "Net Salary & Employer Cost Simulator", "menu_calc": "Compensation Simulator", "menu_rules": "Contribution Rules", "menu_rules_sti": "STI Calculation Rules", "menu_cost": "Employer Cost", "title_calc": "Compensation Simulator", "title_rules": "Contribution Rules", "title_rules_sti": "STI Calculation Rules", "title_cost": "Employer Cost", "country": "Country", "salary": "Gross Salary", "state": "State (USA)", "state_rate": "State Tax (%)", "dependents": "Dependents (Tax)", "bonus": "Annual Bonus", "earnings": "Earnings", "deductions": "Deductions", "net": "Net Salary", "fgts_deposit": "FGTS Deposit", "tot_earnings": "Total Earnings", "tot_deductions": "Total Deductions", "valid_from": "Effective Date", "rules_emp": "Employee Contributions", "rules_er": "Employer Contributions", "rules_table_desc": "Description", "rules_table_rate": "Rate (%)", "rules_table_base": "Calculation Base", "rules_table_obs": "Notes / Cap", "official_source": "Official Source", "employer_cost_total": "Total Employer Cost", "annual_comp_title": "Total Annual Gross Compensation", "calc_params_title": "Compensation Calculation Parameters", "monthly_comp_title": "Monthly Gross and Net Compensation", "annual_salary": "📅 Annual Salary", "annual_bonus": "🎯 Annual Bonus", "annual_total": "💼 Total Annual Compensation", "months_factor": "Months considered", "pie_title": "Annual Split: Salary vs Bonus", "pie_chart_title_dist": "Total Compensation Distribution", "reload": "Reload tables", "source_remote": "Remote tables", "source_local": "Local fallback", "choose_country": "Select a country", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Area (STI)", "level": "Career Level (STI)", "rules_expanded": "Details of Mandatory Contributions", "sti_area_non_sales": "Non Sales", "sti_area_sales": "Sales", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Members of the GEB", "sti_level_executive_manager": "Executive Manager", "sti_level_senior_group_manager": "Senior Group Manager", "sti_level_group_manager": "Group Manager", "sti_level_lead_expert_program_manager": "Lead Expert / Program Manager", "sti_level_senior_manager": "Senior Manager", "sti_level_senior_expert_senior_project_manager": "Senior Expert / Senior Project Manager", "sti_level_manager_selected_expert_project_manager": "Manager / Selected Expert / Project Manager", "sti_level_others": "Others", "sti_level_executive_manager_senior_group_manager": "Executive Manager / Senior Group Manager", "sti_level_group_manager_lead_sales_manager": "Group Manager / Lead Sales Manager", "sti_level_senior_manager_senior_sales_manager": "Senior Manager / Senior Sales Manager", "sti_level_manager_selected_sales_manager": "Manager / Selected Sales Manager", "sti_in_range": "Within range", "sti_out_range": "Outside range", "cost_header_charge": "Charge", "cost_header_percent": "Percent (%)", "cost_header_base": "Base", "cost_header_obs": "Observation", "cost_header_bonus": "Applies to Bonus", "cost_header_vacation": "Applies to Vacation", "cost_header_13th": "Applies to 13th", "sti_table_header_level": "Career Level", "sti_table_header_pct": "STI %" }, "Español": { "sidebar_title": "Simulador de Remuneración<br>(Región Américas)", "other_deductions": "Otras Deducciones Mensuales", "salary_tooltip": "Su salario mensual antes de impuestos y deducciones.", "dependents_tooltip": "Número de dependientes para deducción en el Impuesto de Renta (solo aplicable en Brasil).", "bonus_tooltip": "Monto total del bono esperado en el año (pago único o en cuotas).", "other_deductions_tooltip": "Suma de otras deducciones mensuales recurrentes (ej: plan de salud, ticket de comida, cuota sindical).", "sti_area_tooltip": "Seleccione su área (Ventas o No Ventas) para verificar el rango del bono (STI).", "sti_level_tooltip": "Seleccione su nivel de carrera para verificar el rango del bono (STI). 'Otros' incluye niveles no listados.", "app_title": "Simulador de Salario Neto y Costo del Empleador", "menu_calc": "Simulador de Remuneración", "menu_rules": "Reglas de Contribuciones", "menu_rules_sti": "Reglas de Cálculo del STI", "menu_cost": "Costo del Empleador", "title_calc": "Simulador de Remuneración", "title_rules": "Reglas de Contribuciones", "title_rules_sti": "Reglas de Cálculo del STI", "title_cost": "Costo del Empleador", "country": "País", "salary": "Salario Bruto", "state": "Estado (EE. UU.)", "state_rate": "Impuesto Estatal (%)", "dependents": "Dependientes (Impuesto)", "bonus": "Bono Anual", "earnings": "Ingresos", "deductions": "Descuentos", "net": "Salario Neto", "fgts_deposit": "Depósito de FGTS", "tot_earnings": "Total Ingresos", "tot_deductions": "Total Descuentos", "valid_from": "Vigencia", "rules_emp": "Contribuciones del Empleado", "rules_er": "Contribuciones del Empleador", "rules_table_desc": "Descripción", "rules_table_rate": "Tasa (%)", "rules_table_base": "Base de Cálculo", "rules_table_obs": "Notas / Tope", "official_source": "Fuente Oficial", "employer_cost_total": "Costo Total del Empleador", "annual_comp_title": "Composición de la Remuneración Anual Bruta", "calc_params_title": "Parámetros de Cálculo de Remuneración", "monthly_comp_title": "Remuneración Mensual Bruta y Neta", "annual_salary": "📅 Salario Anual", "annual_bonus": "🎯 Bono Anual", "annual_total": "💼 Remuneração Anual Total", "months_factor": "Meses considerados", "pie_title": "Distribución Anual: Salario vs Bono", "pie_chart_title_dist": "Distribución de la Remuneración Total", "reload": "Recarregar tablas", "source_remote": "Tablas remotas", "source_local": "Copia local", "choose_country": "Seleccione un país", "menu_title": "Menú", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalles de las Contribuciones Obligatorias", "sti_area_non_sales": "No Ventas", "sti_area_sales": "Ventas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Miembros del GEB", "sti_level_executive_manager": "Gerente Ejecutivo", "sti_level_senior_group_manager": "Gerente de Grupo Sénior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Experto Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sénior", "sti_level_senior_expert_senior_project_manager": "Experto Sénior / Gerente de Proyecto Sénior", "sti_level_manager_selected_expert_project_manager": "Gerente / Experto Seleccionado / Gerente de Proyecto", "sti_level_others": "Otros", "sti_level_executive_manager_senior_group_manager": "Gerente Ejecutivo / Gerente de Grupo Sénior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Ventas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sénior / Gerente de Ventas Sénior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Ventas Seleccionado", "sti_in_range": "Dentro del rango", "sti_out_range": "Fuera del rango", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observación", "cost_header_bonus": "Incide Bono", "cost_header_vacation": "Incide Vacaciones", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nivel de Carrera", "sti_table_header_pct": "STI %" } }
COUNTRIES_FALLBACK = {"countries": {"Brasil": {"symbol": "R$", "flag": "🇧🇷", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "México": {"symbol": "MX$", "flag": "🇲🇽", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Chile": {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": False}}, "Argentina": {"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01", "benefits": {"ferias": True, "decimo": True}}, "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01", "benefits": {"ferias": False, "decimo": False}}, "Canadá": {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01", "benefits": {"ferias": False, "decimo": False}}}}
STI_CONFIG_FALLBACK = {"STI_RANGES": { "Non Sales": { "CEO": [1.00, 1.00], "Members of the GEB": [0.50, 0.80], "Executive Manager": [0.45, 0.70], "Senior Group Manager": [0.40, 0.60], "Group Manager": [0.30, 0.50], "Lead Expert / Program Manager": [0.25, 0.40], "Senior Manager": [0.20, 0.40], "Senior Expert / Senior Project Manager": [0.15, 0.35], "Manager / Selected Expert / Project Manager": [0.10, 0.30], "Others": [0.0, 0.10] }, "Sales": { "Executive Manager / Senior Group Manager": [0.45, 0.70], "Group Manager / Lead Sales Manager": [0.35, 0.50], "Senior Manager / Senior Sales Manager": [0.25, 0.45], "Manager / Selected Sales Manager": [0.20, 0.35], "Others": [0.0, 0.15] } }, "STI_LEVEL_OPTIONS": { "Non Sales": [ "CEO", "Members of the GEB", "Executive Manager", "Senior Group Manager", "Group Manager", "Lead Expert / Program Manager", "Senior Manager", "Senior Expert / Senior Project Manager", "Manager / Selected Expert / Project Manager", "Others" ], "Sales": [ "Executive Manager / Senior Group Manager", "Group Manager / Lead Sales Manager", "Senior Manager / Senior Sales Manager", "Manager / Selected Sales Manager", "Others" ] }}
US_STATE_RATES_FALLBACK = { "No State Tax": 0.00, "AK": 0.00, "FL": 0.00, "NV": 0.00, "SD": 0.00, "TN": 0.00, "TX": 0.00, "WA": 0.00, "WY": 0.00, "NH": 0.00, "AL": 0.05, "AR": 0.049, "AZ": 0.025, "CA": 0.06,  "CO": 0.044, "CT": 0.05, "DC": 0.06,  "DE": 0.055, "GA": 0.054, "HI": 0.08, "IA": 0.06,  "ID": 0.06,  "IL": 0.0495, "IN": 0.0323, "KS": 0.046, "KY": 0.05,  "LA": 0.0425, "MA": 0.05,  "MD": 0.0575, "ME": 0.058, "MI": 0.0425, "MN": 0.058, "MO": 0.045, "MS": 0.05, "MT": 0.054, "NC": 0.045, "ND": 0.02,  "NE": 0.05,  "NJ": 0.055, "NM": 0.049, "NY": 0.064, "OH": 0.030, "OK": 0.0475, "OR": 0.08,  "PA": 0.0307, "RI": 0.0475, "SC": 0.052, "UT": 0.0485, "VA": 0.05,  "VT": 0.06, "WI": 0.053, "WV": 0.05 }
TABLES_DEFAULT_FALLBACK = { "México": {"rates": {"ISR_Simplificado": 0.15, "IMSS_Simplificado": 0.05}}, "Chile": {"rates": {"AFP": 0.1115, "Saúde": 0.07}}, "Argentina": {"rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}}, "Colômbia": {"rates": {"Saúde": 0.04, "Pensão": 0.04}}, "Canadá": {"rates": {"Income Tax_Simplificado": 0.15}} }
EMPLOYER_COST_DEFAULT_FALLBACK = {
    "Brasil": [ {"nome": "INSS Patronal", "percentual": 20.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Previdência", "teto": None}, {"nome": "RAT", "percentual": 2.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Risco", "teto": None}, {"nome": "Sistema S", "percentual": 5.8, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Terceiros", "teto": None}, {"nome": "FGTS", "percentual": 8.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Crédito empregado", "teto": None} ],
    "México": [ {"nome": "IMSS Patronal", "percentual": 7.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Seguro social (aprox.)", "teto": "Teto IMSS"}, {"nome": "INFONAVIT Empregador", "percentual": 5.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Habitação", "teto": "Teto IMSS"}, {"nome": "SAR (Aposentadoria)", "percentual": 2.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Adicionado", "teto": "Teto IMSS"}, {"nome": "ISN (Imposto Estadual)", "percentual": 2.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Média (aprox.)", "teto": None} ],
    "Chile": [ {"nome": "Seguro Desemprego", "percentual": 2.4, "base": "Salário", "ferias": True, "decimo": False, "bonus": True, "obs": f"Empregador (Teto {ANNUAL_CAPS['CL_TETO_CESANTIA_UF']:.1f} UF)", "teto": ANNUAL_CAPS["CL_TETO_CESANTIA_UF"]}, {"nome": "SIS (Invalidez)", "percentual": 1.53, "base": "Salário", "ferias": True, "decimo": False, "bonus": True, "obs": f"Adicionado (Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF)", "teto": ANNUAL_CAPS["CL_TETO_UF"]} ],
    "Argentina": [ {"nome": "Contribuições Patronais", "percentual": 23.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Média ajustada", "teto": "Teto SIPA"} ],
    "Colômbia": [ {"nome": "Saúde Empregador", "percentual": 8.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "—", "teto": None}, {"nome": "Pensão Empregador", "percentual": 12.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "—", "teto": None}, {"nome": "Parafiscales (SENA, ICBF...)", "percentual": 9.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Adicionado", "teto": None}, {"nome": "Cesantías (Fundo)", "percentual": 8.33, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "(1/12)", "teto": None} ],
    "Estados Unidos": [ {"nome": "Social Security (ER)", "percentual": 6.2, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"Teto {fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}", "teto": ANNUAL_CAPS["US_FICA"]}, {"nome": "Medicare (ER)", "percentual": 1.45, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "Sem teto", "teto": None}, {"nome": "SUTA (avg)", "percentual": 2.0, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"Teto base {fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}", "teto": ANNUAL_CAPS["US_SUTA_BASE"]} ],
    "Canadá": [ {"nome": "CPP (ER)", "percentual": 5.95, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}", "teto": ANNUAL_CAPS["CA_CPP_YMPEx1"]}, {"nome": "CPP2 (ER)", "percentual": 4.0, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}", "teto": ANNUAL_CAPS["CA_CPP_YMPEx2"]}, {"nome": "EI (ER)", "percentual": 2.28, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}", "teto": ANNUAL_CAPS["CA_EI_MIE"]} ]
}
BR_INSS_FALLBACK = { "vigencia": "2025-01-01", "teto_contribuicao": 1146.68, "teto_base": 8157.41, "faixas": [ {"ate": 1412.00, "aliquota": 0.075}, {"ate": 2666.68, "aliquota": 0.09}, {"ate": 4000.03, "aliquota": 0.12}, {"ate": 8157.41, "aliquota": 0.14} ] }
BR_IRRF_FALLBACK = { "vigencia": "2025-01-01", "deducao_dependente": 189.59, "faixas": [ {"ate": 2259.20, "aliquota": 0.00,  "deducao": 0.00}, {"ate": 2826.65, "aliquota": 0.075, "deducao": 169.44}, {"ate": 3751.05, "aliquota": 0.15,  "deducao": 381.44}, {"ate": 4664.68, "aliquota": 0.225, "deducao": 662.77}, {"ate": 999999999.0, "aliquota": 0.275, "deducao": 896.00} ] }
# **CORREÇÃO: Definir dicionários de componentes antes de usá-los**
TABLES_DEFAULT = TABLES_FALLBACK
EMPLOYER_COST_DEFAULT = EMPLOYER_COST_FALLBACK
REMUN_MONTHS_DEFAULT = REMUN_MONTHS_DEFAULT_FALLBACK
COUNTRY_TABLES_FALLBACK = {"TABLES": TABLES_DEFAULT, "EMPLOYER_COST": EMPLOYER_COST_DEFAULT, "REMUN_MONTHS": REMUN_MONTHS_DEFAULT}


# --- Carrega Configurações ---
I18N = load_json(I18N_FILE, I18N_FALLBACK)
COUNTRIES_DATA = load_json(COUNTRIES_FILE, COUNTRIES_FALLBACK)
STI_CONFIG = load_json(STI_CONFIG_FILE, STI_CONFIG_FALLBACK)
US_STATE_RATES = load_json(US_STATES_FILE, US_STATE_RATES_FALLBACK)
BR_INSS_TBL = load_json(BR_INSS_FILE, BR_INSS_FALLBACK)
BR_IRRF_TBL = load_json(BR_IRRF_FILE, BR_IRRF_FALLBACK)
COUNTRY_TABLES_DATA = load_json(COUNTRY_TABLES_FILE, COUNTRY_TABLES_FALLBACK)

# --- Extrai Dados Carregados ---
if "countries" in COUNTRIES_DATA:
    COUNTRIES = COUNTRIES_DATA.get("countries", {})
else:
    COUNTRIES = COUNTRIES_DATA # Assume que a raiz é o dicionário de países
COUNTRY_BENEFITS = {k: v.get("benefits", {}) for k, v in COUNTRIES.items()}
STI_RANGES = STI_CONFIG.get("STI_RANGES", {})
STI_LEVEL_OPTIONS = STI_CONFIG.get("STI_LEVEL_OPTIONS", {})
TABLES_DEFAULT = COUNTRY_TABLES_DATA.get("TABLES", {})
EMPLOYER_COST_DEFAULT = COUNTRY_TABLES_DATA.get("EMPLOYER_COST", {})
REMUN_MONTHS_DEFAULT = COUNTRY_TABLES_DATA.get("REMUN_MONTHS", {})

def load_tables_data(): 
    country_tables_dict = {
        "TABLES": COUNTRY_TABLES_DATA.get("TABLES", {}),
        "EMPLOYER_COST": COUNTRY_TABLES_DATA.get("EMPLOYER_COST", {}),
        "REMUN_MONTHS": COUNTRY_TABLES_DATA.get("REMUN_MONTHS", {})
    }
    return US_STATE_RATES, country_tables_dict, BR_INSS_TBL, BR_IRRF_TBL


# ============================== (Restante dos HELPERS - Cálculo) ===============================
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
    df = pd.DataFrame(enc_list); df_display = pd.DataFrame()
    if not df.empty:
        df_display = df.copy()
        df_display[T["cost_header_charge"]] = df_display["nome"]
        df_display[T["cost_header_percent"]] = df_display["percentual"].apply(lambda p: f"{p:.2f}%")
        df_display[T["cost_header_base"]] = df_display["base"]
        df_display[T["cost_header_obs"]] = df_display.apply(lambda row: fmt_cap(row.get('teto'), COUNTRIES[country_code]['symbol']) if row.get('teto') is not None else row['obs'], axis=1) # Removido country_code
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
    display_list = [T.get("sti_area_non_sales", "Non Sales"), T.get("sti_area_sales", "Sales")]; keys = ["Non Sales", "Sales"]
    return display_list, dict(zip(display_list, keys))

def get_sti_level_map(area: str, T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    keys = STI_LEVEL_OPTIONS.get(area, []); display_list = [T.get(STI_I18N_KEYS.get(key, key), key) for key in keys]
    return display_list, dict(zip(display_list, keys))

# ============================== SIDEBAR ===============================
with st.sidebar:
    # REQ 1: Ordem corrigida - Título H3 para Idioma
    st.markdown(f"<h3 style='margin-bottom: 0.5rem;'>{I18N.get('Português', {}).get('language_title', '🌐 Idioma / Language / Idioma')}</h3>", unsafe_allow_html=True)
    idioma = st.selectbox(label="Language Select", options=list(I18N.keys()), index=0, key="lang_select", label_visibility="collapsed")
    T = I18N.get(idioma, I18N_FALLBACK["Português"])

    # REQ 1: Renderiza Título da Sidebar DEPOIS de T ser definido
    st.markdown(f"<h2 style='color:white; text-align:center; font-size:20px; margin-bottom: 25px;'>{T.get('sidebar_title', 'Simulador')}</h2>", unsafe_allow_html=True)

    st.markdown(f"<h3 style='margin-bottom: 0.5rem;'>{T.get('country', 'País')}</h3>", unsafe_allow_html=True)
    country_options = list(COUNTRIES.keys())
    if not country_options:
        # Erro fatal se COUNTRIES não for carregado
        st.error("Erro: Arquivo 'countries.json' não encontrado ou vazio.")
        st.stop()
    
    default_country = "Brasil" if "Brasil" in country_options else country_options[0]
    
    if 'country_select' not in st.session_state: st.session_state.country_select = default_country
    if st.session_state.country_select not in country_options: st.session_state.country_select = default_country
    
    try: country_index = country_options.index(st.session_state.country_select)
    except ValueError: country_index = 0
    
    country = st.selectbox(T.get("choose_country", "Selecione"), country_options, index=country_index, key="country_select", label_visibility="collapsed")
    _COUNTRY_CODE_FOR_FMT = country

    st.markdown(f"<h3 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>{T.get('menu_title', 'Menu')}</h3>", unsafe_allow_html=True)
    menu_options = [T.get("menu_calc", "Calc"), T.get("menu_rules", "Rules"), T.get("menu_rules_sti", "STI Rules"), T.get("menu_cost", "Cost")]

    if 'active_menu' not in st.session_state or st.session_state.active_menu not in menu_options:
         st.session_state.active_menu = menu_options[0]
    
    try: active_menu_index = menu_options.index(st.session_state.active_menu)
    except ValueError: active_menu_index = 0; st.session_state.active_menu = menu_options[0]

    active_menu = st.radio(
        label="Menu Select", options=menu_options, key="menu_radio_select",
        label_visibility="collapsed", index=active_menu_index
    )
    if active_menu != st.session_state.active_menu:
        st.session_state.active_menu = active_menu
        st.rerun()

    # REQ 5: Mapa Removido

# ======================= INICIALIZAÇÃO PÓS-SIDEBAR =======================
US_STATE_RATES_LOADED, COUNTRY_TABLES_LOADED, BR_INSS_TBL_LOADED, BR_IRRF_TBL_LOADED = load_tables_data()
COUNTRY_TABLES = COUNTRY_TABLES_LOADED

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
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = cols[5].selectbox(T.get("level", "Level"), level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"))
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
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
        state_code, state
