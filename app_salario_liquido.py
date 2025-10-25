# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.50.2)
# Tema azul plano, multilíngue, responsivo e com STI corrigido
# (Correção NameError + Ajustes Layout/Menu/Regras)
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import altair as alt
import requests
import base64
from typing import Dict, Any, Tuple, List

st.set_page_config(page_title="Simulador de Salário Líquido", layout="wide")

# ======================== ENDPOINTS REMOTOS =========================
RAW_BASE = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main"
URL_US_STATES = f"{RAW_BASE}/us_state_tax_rates.json"
URL_COUNTRY_TABLES = f"{RAW_BASE}/country_tables.json"
URL_BR_INSS = f"{RAW_BASE}/br_inss.json"
URL_BR_IRRF = f"{RAW_BASE}/br_irrf.json"

# ============================== CSS ================================
st.markdown("""
<style>
html, body { font-family:'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:2px; background:linear-gradient(to right, #0a3d62, #e2e6ea); margin:32px 0; border-radius:1px; }

/* Sidebar */
section[data-testid="stSidebar"]{ background:#0a3d62 !important; padding-top:15px; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label{ color:#ffffff !important; }
section[data-testid="stSidebar"] h2 { margin-bottom: 25px !important; }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox input,
section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{ color:#0b1f33 !important; background:#fff !important; }

/* Botões Menu Sidebar */
section[data-testid="stSidebar"] .stButton > button{ background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.3) !important; border-radius: 8px !important; font-weight: 600 !important; box-shadow: none !important; color: #ffffff !important; width: 100%; margin-bottom: 8px; transition: background 0.2s ease; }
section[data-testid="stSidebar"] .stButton > button:hover{ background: rgba(255, 255, 255, 0.2) !important; border-color: rgba(255, 255, 255, 0.5) !important; }
section[data-testid="stSidebar"] .stButton > button.active-menu-button { background: #ffffff !important; color: #0a3d62 !important; border-color: #ffffff !important; }
section[data-testid="stSidebar"] .stButton > button:focus:not(:active) { border-color: rgba(255, 255, 255, 0.3) !important; box-shadow: none !important; }
section[data-testid="stSidebar"] .stButton > button.active-menu-button:focus:not(:active) { border-color: #ffffff !important; }

/* Cards Mensais */
.metric-card{ background:#fff; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); padding:16px; text-align:center; transition: all 0.3s ease; }
.metric-card:hover{ box-shadow:0 6px 16px rgba(0,0,0,0.15); transform: translateY(-2px); }
.metric-card h4{ margin:0; font-size:17px; font-weight: 600; color:#0a3d62; }
.metric-card h3{ margin:2px 0 0; color:#0a3d62; font-size:17px; font-weight: 700; }

/* Tabela */
.table-wrap{ background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }

/* Título com bandeira */
.country-header{ display:flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 5px; }
.country-flag{ font-size:45px; }
.country-title{ font-size:36px; font-weight:700; color:#0a3d62; }

/* Gráfico */
.vega-embed{ padding-bottom: 16px; }

/* Cards Anuais */
.annual-card-base { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.06); padding: 10px 15px; margin-bottom: 8px; border-left: 5px solid #0a3d62; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-sizing: border-box; }
.annual-card-label { align-items: flex-start; }
.annual-card-value { align-items: flex-end; }
.annual-card-label h4,
.annual-card-value h3 { margin: 0; font-size: 17px; color: #0a3d62; }
.annual-card-label h4 { font-weight: 600; }
.annual-card-value h3 { font-weight: 700; }
.annual-card-label .sti-note { display: block; font-size: 15px; font-weight: 400; line-height: 1.3; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================== I18N ================================
# (Dicionário I18N completo como na versão anterior)
I18N = {
    "Português": {
        "app_title": "Simulador de Salário Líquido e Custo do Empregador",
        "menu_calc": "Simulador de Remuneração", # REQ 2
        "menu_rules": "Regras de Contribuições",
        "menu_rules_sti": "Regras de Cálculo do STI",
        "menu_cost": "Custo do Empregador",
        "title_calc": "Simulador de Remuneração", # REQ 3
        "title_rules": "Regras de Contribuições",
        "title_rules_sti": "Regras de Cálculo do STI",
        "title_cost": "Custo do Empregador",
        "country": "País",
        "salary": "Salário Bruto",
        "state": "Estado (EUA)",
        "state_rate": "State Tax (%)",
        "dependents": "Dependentes (IR)",
        "bonus": "Bônus Anual",
        "earnings": "Proventos",
        "deductions": "Descontos",
        "net": "Salário Líquido",
        "fgts_deposit": "Depósito FGTS",
        "tot_earnings": "Total de Proventos",
        "tot_deductions": "Total de Descontos",
        "valid_from": "Vigência",
        "rules_emp": "Contribuições do Empregado", # Título Tabela Regras
        "rules_er": "Contribuições do Empregador", # Título Tabela Regras
        "rules_table_desc": "Descrição", # Header Tabela Regras
        "rules_table_rate": "Alíquota (%)", # Header Tabela Regras
        "rules_table_base": "Base de Cálculo", # Header Tabela Regras
        "rules_table_obs": "Observações / Teto", # Header Tabela Regras
        "official_source": "Fonte Oficial (Exemplo)", # Link Regras
        "employer_cost_total": "Custo Total do Empregador",
        "annual_comp_title": "Composição da Remuneração Total Anual Bruta",
        "calc_params_title": "Parâmetros de Cálculo da Remuneração",
        "monthly_comp_title": "Remuneração Mensal Bruta e Líquida",
        "annual_salary": "📅 Salário Anual", # Simplificado
        "annual_bonus": "🎯 Bônus Anual",
        "annual_total": "💼 Remuneração Total Anual",
        "months_factor": "Meses considerados",
        "pie_title": "Distribuição Anual: Salário vs Bônus",
        "reload": "Recarregar tabelas",
        "source_remote": "Tabelas remotas",
        "source_local": "Fallback local",
        "choose_country": "Selecione o país",
        "area": "Área (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Detalhes das Contribuições Obrigatórias", # Título Regras
        "sti_area_non_sales": "Não Vendas",
        "sti_area_sales": "Vendas",
        "sti_level_ceo": "CEO",
        "sti_level_members_of_the_geb": "Membros do GEB",
        "sti_level_executive_manager": "Gerente Executivo",
        "sti_level_senior_group_manager": "Gerente de Grupo Sênior",
        "sti_level_group_manager": "Gerente de Grupo",
        "sti_level_lead_expert_program_manager": "Especialista Líder / Gerente de Programa",
        "sti_level_senior_manager": "Gerente Sênior",
        "sti_level_senior_expert_senior_project_manager": "Especialista Sênior / Gerente de Projeto Sênior",
        "sti_level_manager_selected_expert_project_manager": "Gerente / Especialista Selecionado / Gerente de Projeto",
        "sti_level_others": "Outros",
        "sti_level_executive_manager_senior_group_manager": "Gerente Executivo / Gerente de Grupo Sênior",
        "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Vendas Líder",
        "sti_level_senior_manager_senior_sales_manager": "Gerente Sênior / Gerente de Vendas Sênior",
        "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Vendas Selecionado",
        "sti_in_range": "Dentro do range",
        "sti_out_range": "Fora do range",
        "cost_header_charge": "Encargo",
        "cost_header_percent": "Percentual (%)",
        "cost_header_base": "Base",
        "cost_header_obs": "Observação",
        "cost_header_bonus": "Incide Bônus",
        "cost_header_vacation": "Incide Férias",
        "cost_header_13th": "Incide 13º",
        "sti_table_header_level": "Nível de Carreira",
        "sti_table_header_pct": "STI %"
    },
    "English": {
        "app_title": "Net Salary & Employer Cost Simulator",
        "menu_calc": "Compensation Simulator",
        "menu_rules": "Contribution Rules",
        "menu_rules_sti": "STI Calculation Rules",
        "menu_cost": "Employer Cost",
        "title_calc": "Compensation Simulator",
        "title_rules": "Contribution Rules",
        "title_rules_sti": "STI Calculation Rules",
        "title_cost": "Employer Cost",
        "country": "Country",
        "salary": "Gross Salary",
        "state": "State (USA)",
        "state_rate": "State Tax (%)",
        "dependents": "Dependents (Tax)",
        "bonus": "Annual Bonus",
        "earnings": "Earnings",
        "deductions": "Deductions",
        "net": "Net Salary",
        "fgts_deposit": "FGTS Deposit",
        "tot_earnings": "Total Earnings",
        "tot_deductions": "Total Deductions",
        "valid_from": "Effective Date",
        "rules_emp": "Employee Contributions",
        "rules_er": "Employer Contributions",
        "rules_table_desc": "Description",
        "rules_table_rate": "Rate (%)",
        "rules_table_base": "Calculation Base",
        "rules_table_obs": "Notes / Cap",
        "official_source": "Official Source (Example)",
        "employer_cost_total": "Total Employer Cost",
        "annual_comp_title": "Total Annual Gross Compensation",
        "calc_params_title": "Compensation Calculation Parameters",
        "monthly_comp_title": "Monthly Gross and Net Compensation",
        "annual_salary": "📅 Annual Salary",
        "annual_bonus": "🎯 Annual Bonus",
        "annual_total": "💼 Total Annual Compensation",
        "months_factor": "Months considered",
        "pie_title": "Annual Split: Salary vs Bonus",
        "reload": "Reload tables",
        "source_remote": "Remote tables",
        "source_local": "Local fallback",
        "choose_country": "Select a country",
        "area": "Area (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Details of Mandatory Contributions",
        "sti_area_non_sales": "Non Sales",
        "sti_area_sales": "Sales",
        "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Members of the GEB", "sti_level_executive_manager": "Executive Manager", "sti_level_senior_group_manager": "Senior Group Manager", "sti_level_group_manager": "Group Manager", "sti_level_lead_expert_program_manager": "Lead Expert / Program Manager", "sti_level_senior_manager": "Senior Manager", "sti_level_senior_expert_senior_project_manager": "Senior Expert / Senior Project Manager", "sti_level_manager_selected_expert_project_manager": "Manager / Selected Expert / Project Manager", "sti_level_others": "Others", "sti_level_executive_manager_senior_group_manager": "Executive Manager / Senior Group Manager", "sti_level_group_manager_lead_sales_manager": "Group Manager / Lead Sales Manager", "sti_level_senior_manager_senior_sales_manager": "Senior Manager / Senior Sales Manager", "sti_level_manager_selected_sales_manager": "Manager / Selected Sales Manager",
        "sti_in_range": "Within range",
        "sti_out_range": "Outside range",
        "cost_header_charge": "Charge", "cost_header_percent": "Percent (%)", "cost_header_base": "Base", "cost_header_obs": "Observation", "cost_header_bonus": "Applies to Bonus", "cost_header_vacation": "Applies to Vacation", "cost_header_13th": "Applies to 13th",
        "sti_table_header_level": "Career Level", "sti_table_header_pct": "STI %"
    },
    "Español": {
        "app_title": "Simulador de Salario Neto y Costo del Empleador",
        "menu_calc": "Simulador de Remuneración",
        "menu_rules": "Reglas de Contribuciones",
        "menu_rules_sti": "Reglas de Cálculo del STI",
        "menu_cost": "Costo del Empleador",
        "title_calc": "Simulador de Remuneración",
        "title_rules": "Reglas de Contribuciones",
        "title_rules_sti": "Reglas de Cálculo del STI",
        "title_cost": "Costo del Empleador",
        "country": "País",
        "salary": "Salario Bruto",
        "state": "Estado (EE. UU.)",
        "state_rate": "Impuesto Estatal (%)",
        "dependents": "Dependientes (Impuesto)",
        "bonus": "Bono Anual",
        "earnings": "Ingresos",
        "deductions": "Descuentos",
        "net": "Salario Neto",
        "fgts_deposit": "Depósito de FGTS",
        "tot_earnings": "Total Ingresos",
        "tot_deductions": "Total Descuentos",
        "valid_from": "Vigencia",
        "rules_emp": "Contribuciones del Empleado",
        "rules_er": "Contribuciones del Empleador",
        "rules_table_desc": "Descripción",
        "rules_table_rate": "Tasa (%)",
        "rules_table_base": "Base de Cálculo",
        "rules_table_obs": "Notas / Tope",
        "official_source": "Fuente Oficial (Ejemplo)",
        "employer_cost_total": "Costo Total del Empleador",
        "annual_comp_title": "Composición de la Remuneración Anual Bruta",
        "calc_params_title": "Parámetros de Cálculo de Remuneración",
        "monthly_comp_title": "Remuneración Mensual Bruta y Neta",
        "annual_salary": "📅 Salario Anual",
        "annual_bonus": "🎯 Bono Anual",
        "annual_total": "💼 Remuneración Anual Total",
        "months_factor": "Meses considerados",
        "pie_title": "Distribución Anual: Salario vs Bono",
        "reload": "Recargar tablas",
        "source_remote": "Tablas remotas",
        "source_local": "Copia local",
        "choose_country": "Seleccione un país",
        "area": "Área (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Detalles de las Contribuciones Obligatorias",
        "sti_area_non_sales": "No Ventas",
        "sti_area_sales": "Ventas",
        "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Miembros del GEB", "sti_level_executive_manager": "Gerente Ejecutivo", "sti_level_senior_group_manager": "Gerente de Grupo Sénior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Experto Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sénior", "sti_level_senior_expert_senior_project_manager": "Experto Sénior / Gerente de Proyecto Sénior", "sti_level_manager_selected_expert_project_manager": "Gerente / Experto Seleccionado / Gerente de Proyecto", "sti_level_others": "Otros", "sti_level_executive_manager_senior_group_manager": "Gerente Ejecutivo / Gerente de Grupo Sénior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Ventas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sénior / Gerente de Ventas Sénior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Ventas Seleccionado",
        "sti_in_range": "Dentro del rango",
        "sti_out_range": "Fuera del rango",
        "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observación", "cost_header_bonus": "Incide Bono", "cost_header_vacation": "Incide Vacaciones", "cost_header_13th": "Incide 13º",
        "sti_table_header_level": "Nivel de Carrera", "sti_table_header_pct": "STI %"
    }
}


# ====================== PAÍSES / MOEDAS / BANDEIRAS =====================
COUNTRIES = {
    "Brasil":   {"symbol": "R$",    "flag": "🇧🇷", "valid_from": "2025-01-01"},
    "México":   {"symbol": "MX$",   "flag": "🇲🇽", "valid_from": "2025-01-01"},
    "Chile":    {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01"},
    "Argentina": {"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01"},
    "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01"},
    "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01"},
    "Canadá":   {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01"},
}

COUNTRY_BENEFITS = {
    "Brasil": {"ferias": True, "decimo": True},
    "México": {"ferias": True, "decimo": True},
    "Chile": {"ferias": True, "decimo": False},
    "Argentina": {"ferias": True, "decimo": True},
    "Colômbia": {"ferias": True, "decimo": True},
    "Estados Unidos": {"ferias": False, "decimo": False},
    "Canadá": {"ferias": False, "decimo": False},
}

REMUN_MONTHS_DEFAULT = {
    "Brasil": 13.33, "México": 12.50, "Chile": 12.00, "Argentina": 13.00,
    "Colômbia": 14.00, # 12 sal + 1 Prima + 1 Cesantías
    "Estados Unidos": 12.00, "Canadá": 12.00
}

ANNUAL_CAPS = {
    "US_FICA": 168600.0,
    "US_SUTA_BASE": 7000.0,
    "CA_CPP_YMPEx1": 68500.0,
    "CA_CPP_YMPEx2": 73200.0,
    "CA_CPP_EXEMPT": 3500.0,
    "CA_EI_MIE": 63200.0,
    "CL_TETO_UF": 84.3,
    "CL_TETO_CESANTIA_UF": 126.6,
}

# <<< CORREÇÃO NameError: Mover funções helpers para ANTES de onde são usadas >>>
# ============================== HELPERS ===============================

def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def fmt_percent(v: float) -> str:
    if v is None: return ""
    return f"{v:.2f}%"

def fmt_cap(cap_value: Any, sym: str = None, country_code: str = None) -> str: # Adicionado country_code
    if cap_value is None: return "—"
    if isinstance(cap_value, str): return cap_value
    if isinstance(cap_value, (int, float)):
        # Check context for UF (Chile)
        if country_code == "Chile" and cap_value < 200:
             return f"~{cap_value:.1f} UF"
        return fmt_money(cap_value, sym if sym else "")
    return str(cap_value)

# <<< Fim das funções movidas >>>


# ========================== FALLBACKS LOCAIS ============================
US_STATE_RATES_DEFAULT = { "No State Tax": 0.00, "AK": 0.00, "FL": 0.00, "NV": 0.00, "SD": 0.00, "TN": 0.00, "TX": 0.00, "WA": 0.00, "WY": 0.00, "NH": 0.00, "AL": 0.05, "AR": 0.049, "AZ": 0.025, "CA": 0.06,  "CO": 0.044, "CT": 0.05, "DC": 0.06,  "DE": 0.055, "GA": 0.054, "HI": 0.08, "IA": 0.06,  "ID": 0.06,  "IL": 0.0495, "IN": 0.0323, "KS": 0.046, "KY": 0.05,  "LA": 0.0425, "MA": 0.05,  "MD": 0.0575, "ME": 0.058, "MI": 0.0425, "MN": 0.058, "MO": 0.045, "MS": 0.05, "MT": 0.054, "NC": 0.045, "ND": 0.02,  "NE": 0.05,  "NJ": 0.055, "NM": 0.049, "NY": 0.064, "OH": 0.030, "OK": 0.0475, "OR": 0.08,  "PA": 0.0307, "RI": 0.0475, "SC": 0.052, "UT": 0.0485, "VA": 0.05,  "VT": 0.06, "WI": 0.053, "WV": 0.05 }
TABLES_DEFAULT = { "México": {"rates": {"ISR": 0.15, "IMSS": 0.05, "INFONAVIT": 0.05}}, "Chile": {"rates": {"AFP": 0.1115, "Saúde": 0.07}}, "Argentina": {"rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}}, "Colômbia": {"rates": {"Saúde": 0.04, "Pensão": 0.04}}, "Canadá": {"rates": {"CPP": 0.0595, "CPP2": 0.04, "EI": 0.0163, "Income Tax": 0.15}} }
# <<< CORREÇÃO NameError: Usar fmt_money diretamente aqui >>>
EMPLOYER_COST_DEFAULT = {
    "Brasil": [ {"nome": "INSS Patronal", "percentual": 20.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Previdência", "teto": None}, {"nome": "RAT", "percentual": 2.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Risco", "teto": None}, {"nome": "Sistema S", "percentual": 5.8, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Terceiros", "teto": None}, {"nome": "FGTS", "percentual": 8.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Crédito empregado", "teto": None} ],
    "México": [ {"nome": "IMSS Patronal", "percentual": 7.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Seguro social (aprox.)", "teto": "Teto IMSS"}, {"nome": "INFONAVIT Empregador", "percentual": 5.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Habitação", "teto": "Teto IMSS"}, {"nome": "SAR (Aposentadoria)", "percentual": 2.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Adicionado", "teto": "Teto IMSS"}, {"nome": "ISN (Imposto Estadual)", "percentual": 2.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Média (aprox.)", "teto": None} ],
    "Chile": [ {"nome": "Seguro Desemprego", "percentual": 2.4, "base": "Salário", "ferias": True, "decimo": False, "bonus": True, "obs": f"Empregador (Teto {ANNUAL_CAPS['CL_TETO_CESANTIA_UF']:.1f} UF)", "teto": ANNUAL_CAPS["CL_TETO_CESANTIA_UF"]}, {"nome": "SIS (Invalidez)", "percentual": 1.53, "base": "Salário", "ferias": True, "decimo": False, "bonus": True, "obs": f"REQ 1: Adicionado (Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF)", "teto": ANNUAL_CAPS["CL_TETO_UF"]} ],
    "Argentina": [ {"nome": "Contribuições Patronais", "percentual": 23.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Média ajustada", "teto": "Teto SIPA"} ],
    "Colômbia": [ {"nome": "Saúde Empregador", "percentual": 8.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "—", "teto": None}, {"nome": "Pensão Empregador", "percentual": 12.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "—", "teto": None}, {"nome": "Parafiscales (SENA, ICBF...)", "percentual": 9.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Adicionado", "teto": None}, {"nome": "Cesantías (Fundo)", "percentual": 8.33, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: (1/12)", "teto": None} ],
    "Estados Unidos": [ {"nome": "Social Security (ER)", "percentual": 6.2, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"REQ 1: Teto {fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}", "teto": ANNUAL_CAPS["US_FICA"]}, {"nome": "Medicare (ER)", "percentual": 1.45, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "Sem teto", "teto": None}, {"nome": "SUTA (avg)", "percentual": 2.0, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"REQ 1: Teto base {fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}", "teto": ANNUAL_CAPS["US_SUTA_BASE"]} ],
    "Canadá": [ {"nome": "CPP (ER)", "percentual": 5.95, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"REQ 1: Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}", "teto": ANNUAL_CAPS["CA_CPP_YMPEx1"]}, {"nome": "CPP2 (ER)", "percentual": 4.0, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"REQ 1: Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}", "teto": ANNUAL_CAPS["CA_CPP_YMPEx2"]}, {"nome": "EI (ER)", "percentual": 2.28, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": f"REQ 1: Teto {fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}", "teto": ANNUAL_CAPS["CA_EI_MIE"]} ]
}
BR_INSS_DEFAULT = { "vigencia": "2025-01-01", "teto_contribuicao": 1146.68, "teto_base": 8157.41, "faixas": [ {"ate": 1412.00, "aliquota": 0.075}, {"ate": 2666.68, "aliquota": 0.09}, {"ate": 4000.03, "aliquota": 0.12}, {"ate": 8157.41, "aliquota": 0.14} ] }
BR_IRRF_DEFAULT = { "vigencia": "2025-01-01", "deducao_dependente": 189.59, "faixas": [ {"ate": 2259.20, "aliquota": 0.00,  "deducao": 0.00}, {"ate": 2826.65, "aliquota": 0.075, "deducao": 169.44}, {"ate": 3751.05, "aliquota": 0.15,  "deducao": 381.44}, {"ate": 4664.68, "aliquota": 0.225, "deducao": 662.77}, {"ate": 999999999.0, "aliquota": 0.275, "deducao": 896.00} ] }
CA_CPP_EI_DEFAULT = { "cpp_rate": 0.0595, "cpp_exempt_monthly": ANNUAL_CAPS["CA_CPP_EXEMPT"] / 12.0, "cpp_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx1"] / 12.0, "cpp2_rate": 0.04, "cpp2_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx2"] / 12.0, "ei_rate": 0.0163, "ei_cap_monthly": ANNUAL_CAPS["CA_EI_MIE"] / 12.0 }

STI_RANGES = { "Non Sales": { "CEO": (1.00, 1.00), "Members of the GEB": (0.50, 0.80), "Executive Manager": (0.45, 0.70), "Senior Group Manager": (0.40, 0.60), "Group Manager": (0.30, 0.50), "Lead Expert / Program Manager": (0.25, 0.40), "Senior Manager": (0.20, 0.40), "Senior Expert / Senior Project Manager": (0.15, 0.35), "Manager / Selected Expert / Project Manager": (0.10, 0.30), "Others": (0.0, 0.10) }, "Sales": { "Executive Manager / Senior Group Manager": (0.45, 0.70), "Group Manager / Lead Sales Manager": (0.35, 0.50), "Senior Manager / Senior Sales Manager": (0.25, 0.45), "Manager / Selected Sales Manager": (0.20, 0.35), "Others": (0.0, 0.15) } }
STI_LEVEL_OPTIONS = { "Non Sales": [ "CEO", "Members of the GEB", "Executive Manager", "Senior Group Manager", "Group Manager", "Lead Expert / Program Manager", "Senior Manager", "Senior Expert / Senior Project Manager", "Manager / Selected Expert / Project Manager", "Others" ], "Sales": [ "Executive Manager / Senior Group Manager", "Group Manager / Lead Sales Manager", "Senior Manager / Senior Sales Manager", "Manager / Selected Sales Manager", "Others" ] }
STI_I18N_KEYS = { "CEO": "sti_level_ceo", "Members of the GEB": "sti_level_members_of_the_geb", "Executive Manager": "sti_level_executive_manager", "Senior Group Manager": "sti_level_senior_group_manager", "Group Manager": "sti_level_group_manager", "Lead Expert / Program Manager": "sti_level_lead_expert_program_manager", "Senior Manager": "sti_level_senior_manager", "Senior Expert / Senior Project Manager": "sti_level_senior_expert_senior_project_manager", "Manager / Selected Expert / Project Manager": "sti_level_manager_selected_expert_project_manager", "Others": "sti_level_others", "Executive Manager / Senior Group Manager": "sti_level_executive_manager_senior_group_manager", "Group Manager / Lead Sales Manager": "sti_level_group_manager_lead_sales_manager", "Senior Manager / Senior Sales Manager": "sti_level_senior_manager_senior_sales_manager", "Manager / Selected Sales Manager": "sti_level_manager_selected_sales_manager" }
MAPA_AMERICAS_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTgwIiBzdHlsZT0iYmFja2dyb3VuZDp0cmFuc3BhcmVudDsiPgogIDxwYXRoIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMC44IiBmaWxsPSJub25lIiBkPSJNNDIgMjRMMzggMjEgMzIgMjAgMzEgMjIgMzQgMjggMzggMzEgNDEgMzQgNDQgNDAgNDkgNDIgNTUgNDkgNjAgNTQgNjcgNTggNzUgNTggODIgNTYgODggNTIgOTUgNTAgMTAzIDQ4IDExMCA0OCAxMTcgNTAgMTI1IDUyIDEzMiA1MyAxNDAgNTUgMTQ4IDU4IDE1NSA2MiAxNjIgNjcgMTY4IDcxIDE3MyA3MyAxNzcgNzUgMTc5IDc5IDE4MCA4MyAxNzkgODYgMTc2IDg4IDE3MiA4OSAxNjggOTAgMTYzIDg5IDE1OCA4NyAxNTIgODQgMTQ2IDgwIDEzOSA3NSAxMzIgNzAgMTIzIDY1IDExNSA2MiAxMDcgNjAgOTkgNTkgOTEgNjAgODQgNjMgNzggNjcgNzIgNzAgNjcgNzIgNjIgNzUgNTggNzcgNTMgNzggNDggNzcgNDMgNzQgMzggNjkgMzMgNjMgMjggNTggMjYgNTIgMjUgNDYgMjR6Ii8+Cjwvc3ZnPgo="

# ============================== (Restante dos HELPERS) ===============================

def get_sti_range(area: str, level: str) -> Tuple[float, float]:
    area_tbl = STI_RANGES.get(area, {})
    rng = area_tbl.get(level)
    return rng if rng else (0.0, None)

def calc_inss_progressivo(salario: float, inss_tbl: Dict[str, Any]) -> float:
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
    ded_dep = float(irrf_tbl.get("deducao_dependente", 0.0))
    base_calc = max(base - ded_dep * max(int(dep), 0), 0.0)
    for faixa in irrf_tbl.get("faixas", []):
        if base_calc <= float(faixa["ate"]):
            aliq = float(faixa["aliquota"]); ded = float(faixa.get("deducao", 0.0))
            return max(base_calc * aliq - ded, 0.0)
    return 0.0

def br_net(salary: float, dependentes: int, br_inss_tbl: Dict[str, Any], br_irrf_tbl: Dict[str, Any]):
    lines = []; total_earn = salary
    inss = calc_inss_progressivo(salary, br_inss_tbl)
    base_ir = max(salary - inss, 0.0)
    irrf = calc_irrf(base_ir, dependentes, br_irrf_tbl)
    lines.append(("Salário Base", salary, 0.0)); lines.append(("INSS", 0.0, inss)); lines.append(("IRRF", 0.0, irrf))
    fgts_value = salary * 0.08; net = total_earn - (inss + irrf)
    return lines, total_earn, inss + irrf, net, fgts_value

def generic_net(salary: float, rates: Dict[str, float], country_code: str):
    lines = [("Base", salary, 0.0)]; total_earn = salary; total_ded = 0.0
    for k, aliq in rates.items():
        if k == "CPP2" and country_code == "Canadá": continue # Ignora CPP2 aqui
        v = salary * float(aliq); total_ded += v; lines.append((k, 0.0, v))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def us_net(salary: float, state_code: str, state_rate: float):
    FICA_WAGE_BASE_MONTHLY = ANNUAL_CAPS["US_FICA"] / 12.0
    lines = [("Base Pay", salary, 0.0)]; total_earn = salary
    salario_base_fica = min(salary, FICA_WAGE_BASE_MONTHLY); fica = salario_base_fica * 0.062
    medicare = salary * 0.0145; total_ded = fica + medicare
    lines += [("FICA (Social Security)", 0.0, fica), ("Medicare", 0.0, medicare)]
    if state_code:
        sr = state_rate if state_rate is not None else 0.0
        if sr > 0: sttax = salary * sr; total_ded += sttax; lines.append((f"State Tax ({state_code})", 0.0, sttax))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def ca_net(salary: float, ca_tbl: Dict[str, Any]):
    lines = [("Base Pay", salary, 0.0)]; total_earn = salary
    cpp_base = max(0, min(salary, ca_tbl["cpp_cap_monthly"]) - ca_tbl["cpp_exempt_monthly"]); cpp = cpp_base * ca_tbl["cpp_rate"]
    cpp2_base = max(0, min(salary, ca_tbl["cpp2_cap_monthly"]) - ca_tbl["cpp_cap_monthly"]); cpp2 = cpp2_base * ca_tbl["cpp2_rate"]
    ei_base = min(salary, ca_tbl["ei_cap_monthly"]); ei = ei_base * ca_tbl["ei_rate"]
    income_tax = salary * 0.15 # Simplificado
    total_ded = cpp + cpp2 + ei + income_tax
    lines.append(("CPP", 0.0, cpp)); lines.append(("CPP2", 0.0, cpp2)); lines.append(("EI", 0.0, ei)); lines.append(("Income Tax (Est.)", 0.0, income_tax))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def calc_country_net(country: str, salary: float, state_code=None, state_rate=None, dependentes=0, tables_ext=None, br_inss_tbl=None, br_irrf_tbl=None):
    if country == "Brasil":
        lines, te, td, net, fgts = br_net(salary, dependentes, br_inss_tbl, br_irrf_tbl)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": fgts}
    elif country == "Estados Unidos":
        lines, te, td, net = us_net(salary, state_code, state_rate)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    elif country == "Canadá":
        lines, te, td, net = ca_net(salary, CA_CPP_EI_DEFAULT)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    else:
        rates = (tables_ext or {}).get("TABLES", {}).get(country, {}).get("rates", {})
        if not rates: rates = TABLES_DEFAULT.get(country, {}).get("rates", {})
        lines, te, td, net = generic_net(salary, rates, country)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}

def calc_employer_cost(country: str, salary: float, bonus: float, T: Dict[str, str], tables_ext=None):
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    enc_list = (tables_ext or {}).get("EMPLOYER_COST", {}).get(country, EMPLOYER_COST_DEFAULT.get(country, []))
    benefits = COUNTRY_BENEFITS.get(country, {"ferias": False, "decimo": False})

    df = pd.DataFrame(enc_list)
    if not df.empty:
        df[T["cost_header_charge"]] = df["nome"]
        df[T["cost_header_percent"]] = df["percentual"].apply(lambda p: f"{p:.2f}%")
        df[T["cost_header_base"]] = df["base"]
        # Usa fmt_cap para formatar tetos na coluna de Observações
        df[T["cost_header_obs"]] = df.apply(lambda row: fmt_cap(row['teto'], COUNTRIES[country]['symbol'], country) if 'teto' in row and row['teto'] is not None else row['obs'], axis=1)
        # ^^^ Modificado para usar fmt_cap se teto existir
        df[T["cost_header_bonus"]] = ["✅" if b else "❌" for b in df["bonus"]]
        cols = [T["cost_header_charge"], T["cost_header_percent"], T["cost_header_base"], T["cost_header_bonus"], T["cost_header_obs"]]
        if benefits.get("ferias", False):
            df[T["cost_header_vacation"]] = ["✅" if b else "❌" for b in df["ferias"]]
            cols.insert(3, T["cost_header_vacation"])
        if benefits.get("decimo", False):
            df[T["cost_header_13th"]] = ["✅" if b else "❌" for b in df["decimo"]]
            insert_pos = 4 if benefits.get("ferias", False) else 3
            cols.insert(insert_pos, T["cost_header_13th"])
        df = df[cols]

    salario_anual_base = salary * 12.0
    salario_anual_beneficios = salary * months
    total_cost_items = []
    for item in enc_list:
        perc = item.get("percentual", 0.0) / 100.0; teto = item.get("teto", None); incide_bonus = item.get("bonus", False)
        base_calc_anual = salario_anual_base if country in ["Estados Unidos", "Canadá"] else salario_anual_beneficios
        if incide_bonus: base_calc_anual += bonus
        if teto is not None and isinstance(teto, (int, float)):
            if country == "Chile" and "UF" in item.get("obs", ""): pass # Ignora teto UF por simplicidade
            elif item.get("nome") == "CPP2 (ER)": base_calc_anual = max(0, min(base_calc_anual, teto) - min(base_calc_anual, ANNUAL_CAPS["CA_CPP_YMPEx1"]))
            else: base_calc_anual = min(base_calc_anual, teto)
        custo_item = base_calc_anual * perc
        total_cost_items.append(custo_item)
    total_encargos = sum(total_cost_items)
    custo_total_anual = (salary * months) + bonus + total_encargos
    mult = (custo_total_anual / salario_anual_base) if salario_anual_base > 0 else 0.0
    return custo_total_anual, mult, df, months

def get_sti_area_map(T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    display_list = [T["sti_area_non_sales"], T["sti_area_sales"]]
    keys = ["Non Sales", "Sales"]
    return display_list, dict(zip(display_list, keys))

def get_sti_level_map(area: str, T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    keys = STI_LEVEL_OPTIONS.get(area, [])
    display_list = [T.get(STI_I18N_KEYS.get(key, ""), key) for key in keys]
    return display_list, dict(zip(display_list, keys))

def fetch_json_no_cache(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=8); r.raise_for_status(); return r.json()

def load_tables():
    try: us_states = fetch_json_no_cache(URL_US_STATES)
    except Exception: us_states = US_STATE_RATES_DEFAULT
    try: country_tables = fetch_json_no_cache(URL_COUNTRY_TABLES)
    except Exception: country_tables = {"TABLES": TABLES_DEFAULT, "EMPLOYER_COST": EMPLOYER_COST_DEFAULT, "REMUN_MONTHS": REMUN_MONTHS_DEFAULT}
    try: br_inss = fetch_json_no_cache(URL_BR_INSS)
    except Exception: br_inss = BR_INSS_DEFAULT
    try: br_irrf = fetch_json_no_cache(URL_BR_IRRF)
    except Exception: br_irrf = BR_IRRF_DEFAULT
    return us_states, country_tables, br_inss, br_irrf

# ============================== SIDEBAR ===============================
with st.sidebar:
    st.markdown("<h2 style='color:white; text-align:center; font-size:20px; margin-bottom: 25px;'>Simulador de Remuneração<br>(Região das Americas)</h2>", unsafe_allow_html=True)
    idioma = st.selectbox("🌐 Idioma / Language / Idioma", list(I18N.keys()), index=0, key="lang_select")
    T = I18N[idioma]
    st.markdown(f"### {T['country']}")
    country = st.selectbox(T["choose_country"], list(COUNTRIES.keys()), index=0, key="country_select")
    st.markdown("---", unsafe_allow_html=True)

    menu_options = [T["menu_calc"], T["menu_rules"], T["menu_rules_sti"], T["menu_cost"]]
    if 'active_menu' not in st.session_state or st.session_state.active_menu not in menu_options:
        st.session_state.active_menu = menu_options[0]

    button_container = st.container()
    cols = button_container.columns(1) # Cria uma única coluna para empilhar os botões
    # Loop para criar os botões estilizados
    for i, option in enumerate(menu_options):
        is_active = (st.session_state.active_menu == option)
        button_key = f"menu_btn_{option.replace(' ', '_')}" # Chave única para cada botão
        
        # Usar st.markdown para aplicar a classe CSS
        button_html = f"""
        <style>
            #{button_key} {{
                background: {'#ffffff' if is_active else 'rgba(255, 255, 255, 0.1)'} !important;
                color: {'#0a3d62' if is_active else '#ffffff'} !important;
                border: 1px solid {'#ffffff' if is_active else 'rgba(255, 255, 255, 0.3)'} !important;
                border-radius: 8px !important;
                width: 100% !important;
                margin-bottom: 8px !important;
                font-weight: 600 !important;
                box-shadow: none !important;
                transition: background 0.2s ease;
            }}
             #{button_key}:hover {{
                 background: {'#f0f0f0' if is_active else 'rgba(255, 255, 255, 0.2)'} !important;
                 border-color: {'#d0d0d0' if is_active else 'rgba(255, 255, 255, 0.5)'} !important;
            }}
             #{button_key}:focus:not(:active) {{
                 border-color: {'#ffffff' if is_active else 'rgba(255, 255, 255, 0.3)'} !important;
                 box-shadow: none !important;
            }}
        </style>
        """
        st.markdown(button_html, unsafe_allow_html=True)

        if cols[0].button(option, key=button_key, use_container_width=True):
             if not is_active: # Apenas atualiza e reroda se clicar num botão diferente
                 st.session_state.active_menu = option
                 st.rerun()

    st.markdown("---", unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center;"><img src="data:image/svg+xml;base64,{MAPA_AMERICAS_B64}" style="width:80%; max-width: 150px; height:auto; padding-top: 20px; opacity: 0.8;"></div>', unsafe_allow_html=True)

US_STATE_RATES, COUNTRY_TABLES, BR_INSS_TBL, BR_IRRF_TBL = load_tables()

symbol = COUNTRIES[country]["symbol"]
flag = COUNTRIES[country]["flag"]
valid_from = COUNTRIES[country]["valid_from"]
active_menu = st.session_state.active_menu

# ======================= TÍTULO DINÂMICO ==============================
if active_menu == T["menu_calc"]: title = T["title_calc"]
elif active_menu == T["menu_rules"]: title = T["title_rules"]
elif active_menu == T["menu_rules_sti"]: title = T["title_rules_sti"]
else: title = T["title_cost"]

st.markdown(f"<div class='country-header'><div class='country-title'>{title}</div><div class='country-flag'>{flag}</div></div>", unsafe_allow_html=True)
st.write("---")

# ========================= SIMULADOR DE REMUNERAÇÃO ==========================
if active_menu == T["menu_calc"]:
    area_options_display, area_display_map = get_sti_area_map(T)
    if country == "Brasil":
        st.subheader(T["calc_params_title"])
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1.6, 1.6, 2.4])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        dependentes = c2.number_input(f"{T['dependents']}", min_value=0, value=0, step=1, key="dep_input")
        bonus_anual = c3.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        area_display = c4.selectbox(T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = c5.selectbox(T["level"], level_options_display, index=len(level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]
        st.subheader(T["monthly_comp_title"])
        state_code, state_rate = None, None
    elif country == "Estados Unidos":
        st.subheader(T["calc_params_title"])
        c1, c2, c3, c4 = st.columns([2, 1.4, 1.2, 1.4])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        state_code = c2.selectbox(f"{T['state']}", list(US_STATE_RATES.keys()), index=0, key="state_select_main")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input(f"{T['state_rate']}", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input")
        bonus_anual = c4.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        area_display = r1.selectbox(T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = r2.selectbox(T["level"], level_options_display, index=len(level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]
        dependentes = 0
        st.subheader(T["monthly_comp_title"])
    else: # Outros países
        st.subheader(T["calc_params_title"])
        c1, c2 = st.columns([2, 1.6])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        bonus_anual = c2.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        area_display = r1.selectbox(T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = r2.selectbox(T["level"], level_options_display, index=len(level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]
        dependentes = 0
        state_code, state_rate = None, None
        st.subheader(T["monthly_comp_title"])

    calc = calc_country_net(country, salario, state_code=state_code, state_rate=state_rate, dependentes=dependentes, tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL)
    df_detalhe = pd.DataFrame(calc["lines"], columns=["Descrição", T["earnings"], T["deductions"]])
    df_detalhe[T["earnings"]] = df_detalhe[T["earnings"]].apply(lambda v: money_or_blank(v, symbol))
    df_detalhe[T["deductions"]] = df_detalhe[T["deductions"]].apply(lambda v: money_or_blank(v, symbol))
    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True); st.table(df_detalhe); st.markdown("</div>", unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(f"<div class='metric-card' style='border-left: 5px solid #28a745; background: #e6ffe6;'><h4>💰 {T['tot_earnings']}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card' style='border-left: 5px solid #dc3545; background: #ffe6e6;'><h4>📉 {T['tot_deductions']}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card' style='border-left: 5px solid #007bff; background: #e6f7ff;'><h4>💵 {T['net']}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)
    if country == "Brasil": st.markdown(f"**💼 {T['fgts_deposit']}:** {fmt_money(calc['fgts'], symbol)}")

    st.write("---")
    st.subheader(T["annual_comp_title"])
    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0
    pct_txt = f"{bonus_pct*100:.1f}%"
    faixa_txt = f"≤ {(max_pct or 0)*100:.0f}%" if level == "Others" else f"{min_pct*100:.0f}% – {max_pct*100:.0f}%"
    dentro = (bonus_pct <= (max_pct or 0)) if level == "Others" else (min_pct <= bonus_pct <= max_pct)
    cor = "#1976d2" if dentro else "#d32f2f"; status_txt = T["sti_in_range"] if dentro else T["sti_out_range"]; bg_cor = "#e6f7ff" if dentro else "#ffe6e6"
    sti_line = f"STI ratio do bônus: <strong>{pct_txt}</strong> — <strong>{status_txt}</strong> ({faixa_txt}) — <em>{area_display} • {level_display}</em>"

    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='annual-card-base annual-card-label' style='border-left-color: #28a745; background: #e6ffe6;'><h4>{T['annual_salary']}</h4><span class='sti-note'>({T['months_factor']}: {months})</span></div>", unsafe_allow_html=True)
    c1.markdown(f"<div class='annual-card-base annual-card-label' style='border-left-color: {cor}; background: {bg_cor};'><h4>{T['annual_bonus']}</h4><span class='sti-note' style='color:{cor}'>{sti_line}</span></div>", unsafe_allow_html=True)
    c1.markdown(f"<div class='annual-card-base annual-card-label' style='border-left-color: #0a3d62; background: #e6f0f8;'><h4>{T['annual_total']}</h4></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='annual-card-base annual-card-value' style='border-left-color: #28a745; background: #e6ffe6;'><h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='annual-card-base annual-card-value' style='border-left-color: {cor}; background: {bg_cor};'><h3>{fmt_money(bonus_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='annual-card-base annual-card-value' style='border-left-color: #0a3d62; background: #e6f0f8;'><h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True)

    st.write("---")
    chart_df = pd.DataFrame({"Componente": [T["annual_salary"].split(" (")[0], T["annual_bonus"]], "Valor": [salario_anual, bonus_anual]})
    base = alt.Chart(chart_df).transform_joinaggregate(Total="sum(Valor)").transform_calculate(Percent="datum.Valor / datum.Total")
    pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(theta=alt.Theta("Valor:Q", stack=True), color=alt.Color("Componente:N", legend=alt.Legend(orient="bottom", direction="horizontal", title=None, labelLimit=250, labelFontSize=15, symbolSize=90)), tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f"), alt.Tooltip("Percent:Q", format=".1%"),])
    labels = base.transform_filter(alt.datum.Percent >= 0.01).mark_text(radius=80, fontWeight="bold", color="white").encode(theta=alt.Theta("Valor:Q", stack=True), text=alt.Text("Percent:Q", format=".1%"))
    chart = alt.layer(pie, labels).properties(title="").configure_legend(orient="bottom", title=None, labelLimit=250).configure_view(strokeWidth=0).resolve_scale(color='independent')
    st.altair_chart(chart, use_container_width=True)

# =========================== REGRAS DE CONTRIBUIÇÕES ===================
elif active_menu == T["menu_rules"]:
    st.subheader(T["rules_expanded"])
    br_emp_contrib = [ {"desc": "INSS", "rate": "7.5% - 14% (Prog.)", "base": "Salário Bruto", "obs": f"Teto Base {fmt_money(BR_INSS_DEFAULT['teto_base'], 'R$')}, Teto Contrib. {fmt_money(BR_INSS_DEFAULT['teto_contribuicao'], 'R$')}"}, {"desc": "IRRF", "rate": "0% - 27.5% (Prog.)", "base": "Salário Bruto - INSS - Dep.", "obs": f"Ded. Dep. {fmt_money(BR_IRRF_DEFAULT['deducao_dependente'], 'R$')}"} ]
    br_er_contrib = [ {"desc": "INSS Patronal", "rate": "20.00%", "base": "Folha", "obs": "Regra Geral"}, {"desc": "RAT/FAP", "rate": "~2.00%", "base": "Folha", "obs": "Varia (1% a 3%)"}, {"desc": "Sistema S", "rate": "~5.80%", "base": "Folha", "obs": "Terceiros"}, {"desc": "FGTS", "rate": "8.00%", "base": "Folha", "obs": "Depósito (Custo)"} ]
    us_emp_contrib = [ {"desc": "FICA (Social Sec.)", "rate": "6.20%", "base": "Sal. Bruto", "obs": f"Teto Anual {fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}"}, {"desc": "Medicare", "rate": "1.45%", "base": "Sal. Bruto", "obs": "Sem teto"}, {"desc": "State Tax", "rate": "Varia (0-8%+)","base": "Sal. Bruto", "obs": "Depende do Estado"} ]
    us_er_contrib = [ {"desc": "FICA Match", "rate": "6.20%", "base": "Sal. Bruto", "obs": f"Teto Anual {fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}"}, {"desc": "Medicare Match", "rate": "1.45%", "base": "Sal. Bruto", "obs": "Sem teto"}, {"desc": "SUTA/FUTA", "rate": "~2.00%", "base": "Sal. Bruto", "obs": f"Teto Base ~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}"} ]
    ca_emp_contrib = [ {"desc": "CPP", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp_rate']*100), "base": "Sal. Bruto (c/ Isenção)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}"}, {"desc": "CPP2", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp2_rate']*100), "base": "Sal. Bruto (pós Teto 1)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}"}, {"desc": "EI", "rate": fmt_percent(CA_CPP_EI_DEFAULT['ei_rate']*100), "base": "Sal. Bruto", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}"}, {"desc": "Income Tax", "rate": "Prog. Federal+Prov.", "base": "Renda Tributável", "obs": "Complexo"} ]
    ca_er_contrib = [ {"desc": "CPP Match", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp_rate']*100), "base": "Sal. Bruto (c/ Isenção)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}"}, {"desc": "CPP2 Match", "rate": fmt_percent(CA_CPP_EI_DEFAULT['cpp2_rate']*100), "base": "Sal. Bruto (pós Teto 1)", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}"}, {"desc": "EI Match", "rate": fmt_percent(CA_CPP_EI_DEFAULT['ei_rate']*100 * 1.4), "base": "Sal. Bruto", "obs": f"Teto {fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}"} ]
    mx_emp_contrib = [{"desc": "ISR", "rate": "~15% (Simpl.)", "base": "Sal. Bruto", "obs": "Progressivo"}, {"desc": "IMSS", "rate": "~5% (Simpl.)", "base": "Sal. Bruto", "obs": "Com Teto"}]
    mx_er_contrib = [{"desc": "IMSS", "rate": "~7% (Simpl.)", "base": "SBC", "obs": "Complexo"}, {"desc": "INFONAVIT", "rate": "5.00%", "base": "SBC", "obs": "Habitação"}, {"desc": "SAR", "rate": "2.00%", "base": "SBC", "obs": "Aposentadoria"}, {"desc": "ISN", "rate": "~2.5%", "base": "Folha", "obs": "Imposto Estadual"}]
    cl_emp_contrib = [{"desc": "AFP", "rate": "~11.15%", "base": "Sal. Bruto", "obs": f"10% + Comissão (Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF)"}, {"desc": "Saúde", "rate": "7.00%", "base": "Sal. Bruto", "obs": f"Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF"}]
    cl_er_contrib = [{"desc": "Seg. Cesantía", "rate": "2.40%", "base": "Sal. Bruto", "obs": f"Teto {ANNUAL_CAPS['CL_TETO_CESANTIA_UF']:.1f} UF"}, {"desc": "SIS", "rate": "1.53%", "base": "Sal. Bruto", "obs": f"Teto {ANNUAL_CAPS['CL_TETO_UF']:.1f} UF"}]
    ar_emp_contrib = [{"desc": "Jubilación", "rate": "11.00%", "base": "Sal. Bruto", "obs": "Com Teto"}, {"desc": "Obra Social", "rate": "3.00%", "base": "Sal. Bruto", "obs": "Com Teto"}, {"desc": "PAMI", "rate": "3.00%", "base": "Sal. Bruto", "obs": "Com Teto"}]
    ar_er_contrib = [{"desc": "Cargas Sociales", "rate": "~23.50%", "base": "Sal. Bruto", "obs": "Com Teto (Média)"}]
    co_emp_contrib = [{"desc": "Salud", "rate": "4.00%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Pensión", "rate": "4.00%", "base": "Sal. Bruto", "obs": "-"}]
    co_er_contrib = [{"desc": "Salud", "rate": "8.50%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Pensión", "rate": "12.00%", "base": "Sal. Bruto", "obs": "-"}, {"desc": "Parafiscales", "rate": "9.00%", "base": "Sal. Bruto", "obs": "SENA, ICBF, Caja"}, {"desc": "Cesantías", "rate": "8.33%", "base": "Sal. Bruto", "obs": "1 Salário/Ano"}]
    country_contrib_map = { "Brasil": (br_emp_contrib, br_er_contrib), "Estados Unidos": (us_emp_contrib, us_er_contrib), "Canadá": (ca_emp_contrib, ca_er_contrib), "México": (mx_emp_contrib, mx_er_contrib), "Chile": (cl_emp_contrib, cl_er_contrib), "Argentina": (ar_emp_contrib, ar_er_contrib), "Colômbia": (co_emp_contrib, co_er_contrib), }
    official_links = { "Brasil": "https://www.gov.br/receitafederal/pt-br", "Estados Unidos": "https://www.irs.gov/", "Canadá": "https://www.canada.ca/en/revenue-agency.html", "México": "https://www.sat.gob.mx/", "Chile": "https://www.sii.cl/", "Argentina": "https://www.afip.gob.ar/", "Colômbia": "https://www.dian.gov.co/", }

    emp_contrib_data, er_contrib_data = country_contrib_map.get(country, ([], []))
    link = official_links.get(country, "#")
    col_map = { "desc": T["rules_table_desc"], "rate": T["rules_table_rate"], "base": T["rules_table_base"], "obs": T["rules_table_obs"] }
    df_emp = pd.DataFrame(emp_contrib_data).rename(columns=col_map) if emp_contrib_data else pd.DataFrame()
    df_er = pd.DataFrame(er_contrib_data).rename(columns=col_map) if er_contrib_data else pd.DataFrame()

    st.markdown(f"Abaixo estão os principais componentes de contribuição para **{country}**.")
    if not df_emp.empty:
        st.markdown(f"#### {T['rules_emp']}")
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
    if not df_er.empty:
        st.markdown(f"#### {T['rules_er']}")
        st.dataframe(df_er, use_container_width=True, hide_index=True)
    st.write("")
    st.markdown(f"**{T['valid_from']}:** {valid_from}")
    st.markdown(f"[{T['official_source']}]({link})")

# =========================== REGRAS DE CÁLCULO DO STI ==================
elif active_menu == T["menu_rules_sti"]:
    header_level = T["sti_table_header_level"]; header_pct = T["sti_table_header_pct"]
    st.markdown(f"#### {T['sti_area_non_sales']}")
    st.markdown(f"""
    | {header_level}                                       | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T[STI_I18N_KEYS["CEO"]]}                              |   100%   |
    | {T[STI_I18N_KEYS["Members of the GEB"]]}                |  50–80%  |
    | {T[STI_I18N_KEYS["Executive Manager"]]}                |  45–70%  |
    | {T[STI_I18N_KEYS["Senior Group Manager"]]}             |  40–60%  |
    | {T[STI_I18N_KEYS["Group Manager"]]}                    |  30–50%  |
    | {T[STI_I18N_KEYS["Lead Expert / Program Manager"]]}      |  25–40%  |
    | {T[STI_I18N_KEYS["Senior Manager"]]}                   |  20–40%  |
    | {T[STI_I18N_KEYS["Senior Expert / Senior Project Manager"]]} |  15–35%  |
    | {T[STI_I18N_KEYS["Manager / Selected Expert / Project Manager"]]} |  10–30%  |
    | {T[STI_I18N_KEYS["Others"]]}                           |  ≤ 10%   |
    """, unsafe_allow_html=True)
    st.markdown(f"#### {T['sti_area_sales']}")
    st.markdown(f"""
    | {header_level}                                       | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T[STI_I18N_KEYS["Executive Manager / Senior Group Manager"]]} |  45–70%  |
    | {T[STI_I18N_KEYS["Group Manager / Lead Sales Manager"]]}    |  35–50%  |
    | {T[STI_I18N_KEYS["Senior Manager / Senior Sales Manager"]]} |  25–45%  |
    | {T[STI_I18N_KEYS["Manager / Selected Sales Manager"]]}      |  20–35%  |
    | {T[STI_I18N_KEYS["Others"]]}                           |  ≤ 15%   |
    """, unsafe_allow_html=True)

# ========================= CUSTO DO EMPREGADOR ========================
elif active_menu == T["menu_cost"]:
    c1, c2 = st.columns(2)
    salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    bonus_anual = c2.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_cost_input")
    st.write("---")
    anual, mult, df_cost, months = calc_employer_cost(country, salario, bonus_anual, T, tables_ext=COUNTRY_TABLES)
    st.markdown(f"**{T['employer_cost_total']} (Salário + Bônus + Encargos):** {fmt_money(anual, symbol)}  \n"
                f"**Multiplicador de Custo (vs Salário Base 12 meses):** {mult:.3f} × (12 meses)  \n"
                f"**{T['months_factor']} (Base Salarial):** {months}")
    if not df_cost.empty: st.dataframe(df_cost, use_container_width=True, hide_index=True)
    else: st.info("Sem encargos configurados para este país (no JSON).")
