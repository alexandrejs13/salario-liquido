# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.49)
# Tema azul plano, multilíngue, responsivo e com STI corrigido
# (REQ 1: Cálculos de Custo e Líquido com Tetos implementados)
# (REQ 3: Correção de erro 'ValidationError' no gráfico Altair)
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
/* REQ 9: Aumentar espaço do divisor */
hr { border:0; height:2px; background:linear-gradient(to right, #0a3d62, #e2e6ea); margin:32px 0; border-radius:1px; }

/* Sidebar */
section[data-testid="stSidebar"]{ background:#0a3d62 !important; padding-top:8px; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label{ color:#ffffff !important; }

section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox input,
section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{
  color:#0b1f33 !important; background:#fff !important;
}
section[data-testid="stSidebar"] .stButton > button{
  background:#ffffff !important; border:1px solid #c9d6e2 !important; border-radius:10px !important;
  font-weight:600 !important; box-shadow:0 1px 3px rgba(0,0,0,.06); color:#0b1f33 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover{ background:#f5f8ff !important; border-color:#9bb4d1 !important; }

/* Cards Mensais (Proventos, Descontos, Líquido) */
.metric-card{ background:#fff; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); padding:16px; text-align:center; transition: all 0.3s ease; }
.metric-card:hover{ box-shadow:0 6px 16px rgba(0,0,0,0.15); transform: translateY(-2px); }

/* REQ 2: Ajuste de fontes dos cards mensais para 17px */
.metric-card h4{
    margin:0;
    font-size:17px; /* REQ 2: Aumentado de 13px p/ 17px */
    font-weight: 600; /* REQ 2: Alinhado com card anual */
    color:#0a3d62;
}
.metric-card h3{
    margin:2px 0 0;
    color:#0a3d62;
    font-size:17px; /* REQ 6: Garantido 17px */
    font-weight: 700; /* REQ 2: Alinhado com card anual */
}

/* Tabela */
.table-wrap{ background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }

/* Título com bandeira (REQ 3: Flag maior) */
.country-header{ display:flex; align-items:center; gap:12px; }
.country-flag{ font-size:40px; } /* REQ 3: Aumentado de 28px */
.country-title{ font-size:36px; font-weight:700; color:#0a3d62; } /* REQ 3: Aumentado de 32px */

/* Espaço extra abaixo do gráfico para legenda */
.vega-embed{ padding-bottom: 16px; }

/* CSS dos Cards Anuais (REQ 5: Fontes maiores) */
.annual-card-base {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 10px 15px;
    margin-bottom: 8px;
    border-left: 5px solid #0a3d62;
    min-height: 110px; /* REQ 5: Aumentado para 110px p/ caber fontes */
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
}
.annual-card-label { align-items: flex-start; }
.annual-card-value { align-items: flex-end; }

.annual-card-label h4,
.annual-card-value h3 {
    margin: 0;
    font-size: 17px; /* REQ 6: Tamanho da fonte 17px */
    color: #0a3d62;
}
.annual-card-label h4 { font-weight: 600; }
.annual-card-value h3 { font-weight: 700; }

.annual-card-label .sti-note {
    display: block;
    font-size: 15px; /* REQ 5: Aumentado de 12px para 15px */
    font-weight: 400; /* REQ 5: Não negrito */
    line-height: 1.3;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ============================== I18N (REQ 2 e 3) ================================
I18N = {
    "Português": {
        "app_title": "Simulador de Salário Líquido e Custo do Empregador",
        "menu_calc": "Simulador de Remuneração", # REQ 2
        "menu_rules": "Regras de Contribuições",
        "menu_rules_sti": "Regras de Cálculo do STI",
        "menu_cost": "Custo do Empregador",
        "title_calc": "Simulador de Remuneração – {pais}", # REQ 3
        "title_rules": "Regras de Contribuições – {pais}",
        "title_rules_sti": "Regras de Cálculo do STI",
        "title_cost": "Custo do Empregador – {pais}",
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
        "rules_emp": "Parte do Empregado",
        "rules_er": "Parte do Empregador",
        "employer_cost_total": "Custo Total do Empregador",
        "annual_comp_title": "Composição da Remuneração Total Anual Bruta",
        "calc_params_title": "Parâmetros de Cálculo da Remuneração",
        "monthly_comp_title": "Remuneração Mensal Bruta e Líquida",
        "annual_salary": "📅 Salário Anual (Salário × Meses do País)",
        "annual_bonus": "🎯 Bônus Anual",
        "annual_total": "💼 Remuneração Total Anual",
        "months_factor": "Meses considerados",
        "pie_title": "Distribuição Anual: Salário vs Bônus",
        "reload": "Recarregar tabelas",
        "source_remote": "Tabelas remotas",
        "source_local": "Fallback local",
        "menu": "Menu",
        "choose_country": "Selecione o país",
        "choose_menu": "Escolha uma opção",
        "area": "Área (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Regras detalhadas, fórmulas e exemplos práticos",
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
        "menu_calc": "Compensation Simulator", # REQ 2
        "menu_rules": "Contribution Rules",
        "menu_rules_sti": "STI Calculation Rules",
        "menu_cost": "Employer Cost",
        "title_calc": "Compensation Simulator – {pais}", # REQ 3
        "title_rules": "Contribution Rules – {pais}",
        "title_rules_sti": "STI Calculation Rules",
        "title_cost": "Employer Cost – {pais}",
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
        "valid_from": "Valid from",
        "rules_emp": "Employee Portion",
        "rules_er": "Employer Portion",
        "employer_cost_total": "Total Employer Cost",
        "annual_comp_title": "Total Annual Gross Compensation",
        "calc_params_title": "Compensation Calculation Parameters",
        "monthly_comp_title": "Monthly Gross and Net Compensation",
        "annual_salary": "📅 Annual Salary (Salary × Country Months)",
        "annual_bonus": "🎯 Annual Bonus",
        "annual_total": "💼 Total Annual Compensation",
        "months_factor": "Months considered",
        "pie_title": "Annual Split: Salary vs Bonus",
        "reload": "Reload tables",
        "source_remote": "Remote tables",
        "source_local": "Local fallback",
        "menu": "Menu",
        "choose_country": "Select a country",
        "choose_menu": "Choose an option",
        "area": "Area (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Detailed rules, formulas and worked examples",
        "sti_area_non_sales": "Non Sales",
        "sti_area_sales": "Sales",
        "sti_level_ceo": "CEO",
        "sti_level_members_of_the_geb": "Members of the GEB",
        "sti_level_executive_manager": "Executive Manager",
        "sti_level_senior_group_manager": "Senior Group Manager",
        "sti_level_group_manager": "Group Manager",
        "sti_level_lead_expert_program_manager": "Lead Expert / Program Manager",
        "sti_level_senior_manager": "Senior Manager",
        "sti_level_senior_expert_senior_project_manager": "Senior Expert / Senior Project Manager",
        "sti_level_manager_selected_expert_project_manager": "Manager / Selected Expert / Project Manager",
        "sti_level_others": "Others",
        "sti_level_executive_manager_senior_group_manager": "Executive Manager / Senior Group Manager",
        "sti_level_group_manager_lead_sales_manager": "Group Manager / Lead Sales Manager",
        "sti_level_senior_manager_senior_sales_manager": "Senior Manager / Senior Sales Manager",
        "sti_level_manager_selected_sales_manager": "Manager / Selected Sales Manager",
        "sti_in_range": "Within range",
        "sti_out_range": "Outside range",
        "cost_header_charge": "Charge",
        "cost_header_percent": "Percent (%)",
        "cost_header_base": "Base",
        "cost_header_obs": "Observation",
        "cost_header_bonus": "Applies to Bonus",
        "cost_header_vacation": "Applies to Vacation",
        "cost_header_13th": "Applies to 13th",
        "sti_table_header_level": "Career Level",
        "sti_table_header_pct": "STI %"
    },
    "Español": {
        "app_title": "Simulador de Salario Neto y Costo del Empleador",
        "menu_calc": "Simulador de Remuneración", # REQ 2
        "menu_rules": "Reglas de Contribuciones",
        "menu_rules_sti": "Reglas de Cálculo del STI",
        "menu_cost": "Costo del Empleador",
        "title_calc": "Simulador de Remuneración – {pais}", # REQ 3
        "title_rules": "Reglas de Contribuciones – {pais}",
        "title_rules_sti": "Reglas de Cálculo del STI",
        "title_cost": "Costo del Empleador – {pais}",
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
        "rules_emp": "Parte del Trabajador",
        "rules_er": "Parte del Empleador",
        "employer_cost_total": "Costo Total del Empleador",
        "annual_comp_title": "Composición de la Remuneración Anual Bruta",
        "calc_params_title": "Parámetros de Cálculo de Remuneración",
        "monthly_comp_title": "Remuneración Mensual Bruta y Neta",
        "annual_salary": "📅 Salario Anual (Salario × Meses del País)",
        "annual_bonus": "🎯 Bono Anual",
        "annual_total": "💼 Remuneración Anual Total",
        "months_factor": "Meses considerados",
        "pie_title": "Distribución Anual: Salario vs Bono",
        "reload": "Recargar tablas",
        "source_remote": "Tablas remotas",
        "source_local": "Copia local",
        "menu": "Menú",
        "choose_country": "Seleccione un país",
        "choose_menu": "Elija uma opción",
        "area": "Área (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Reglas detalladas, fórmulas y ejemplos prácticos",
        "sti_area_non_sales": "No Ventas",
        "sti_area_sales": "Ventas",
        "sti_level_ceo": "CEO",
        "sti_level_members_of_the_geb": "Miembros del GEB",
        "sti_level_executive_manager": "Gerente Ejecutivo",
        "sti_level_senior_group_manager": "Gerente de Grupo Sénior",
        "sti_level_group_manager": "Gerente de Grupo",
        "sti_level_lead_expert_program_manager": "Experto Líder / Gerente de Programa",
        "sti_level_senior_manager": "Gerente Sénior",
        "sti_level_senior_expert_senior_project_manager": "Experto Sénior / Gerente de Proyecto Sénior",
        "sti_level_manager_selected_expert_project_manager": "Gerente / Experto Seleccionado / Gerente de Proyecto",
        "sti_level_others": "Otros",
        "sti_level_executive_manager_senior_group_manager": "Gerente Ejecutivo / Gerente de Grupo Sénior",
        "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Ventas Líder",
        "sti_level_senior_manager_senior_sales_manager": "Gerente Sénior / Gerente de Ventas Sénior",
        "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Ventas Seleccionado",
        "sti_in_range": "Dentro del rango",
        "sti_out_range": "Fuera del rango",
        "cost_header_charge": "Encargo",
        "cost_header_percent": "Percentual (%)",
        "cost_header_base": "Base",
        "cost_header_obs": "Observación",
        "cost_header_bonus": "Incide Bono",
        "cost_header_vacation": "Incide Vacaciones",
        "cost_header_13th": "Incide 13º",
        "sti_table_header_level": "Nivel de Carrera",
        "sti_table_header_pct": "STI %"
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
    "Colômbia": 14.00, # REQ 1 CORREÇÃO: 12 sal + 1 Prima + 1 Cesantías = 14
    "Estados Unidos": 12.00, "Canadá": 12.00
}

# REQ 1: Tetos de Contribuição (Valores 2024/2025 como fallback)
ANNUAL_CAPS = {
    "US_FICA": 168600.0,
    "US_SUTA_BASE": 7000.0, # Varia por estado, 7k é o federal/mínimo
    "CA_CPP_YMPEx1": 68500.0, # Teto base
    "CA_CPP_YMPEx2": 73200.0, # Teto 2 (CPP2)
    "CA_CPP_EXEMPT": 3500.0,
    "CA_EI_MIE": 63200.0,
    "CL_TETO_UF": 84.3,
    "CL_TETO_CESANTIA_UF": 126.6,
    # Faltam tetos da Argentina, México, etc. - Cálculos ainda simplificados.
}


# ========================== FALLBACKS LOCAIS (REQ 1: Atualizados) ============================
US_STATE_RATES_DEFAULT = {
    "No State Tax": 0.00, "AK": 0.00, "FL": 0.00, "NV": 0.00, "SD": 0.00, "TN": 0.00, "TX": 0.00, "WA": 0.00, "WY": 0.00, "NH": 0.00,
    "AL": 0.05, "AR": 0.049, "AZ": 0.025, "CA": 0.06,  "CO": 0.044, "CT": 0.05, "DC": 0.06,  "DE": 0.055, "GA": 0.054, "HI": 0.08,
    "IA": 0.06,  "ID": 0.06,  "IL": 0.0495, "IN": 0.0323, "KS": 0.046, "KY": 0.05,  "LA": 0.0425, "MA": 0.05,  "MD": 0.0575, "ME": 0.058,
    "MI": 0.0425, "MN": 0.058, "MO": 0.045, "MS": 0.05, "MT": 0.054, "NC": 0.045, "ND": 0.02,  "NE": 0.05,  "NJ": 0.055, "NM": 0.049,
    "NY": 0.064, "OH": 0.030, "OK": 0.0475, "OR": 0.08,  "PA": 0.0307, "RI": 0.0475, "SC": 0.052, "UT": 0.0485, "VA": 0.05,  "VT": 0.06,
    "WI": 0.053, "WV": 0.05
}
TABLES_DEFAULT = {
    "México": {"rates": {"ISR": 0.15, "IMSS": 0.05, "INFONAVIT": 0.05}},
    "Chile": {"rates": {"AFP": 0.1115, "Saúde": 0.07}}, # AFP 10% + comissão média
    "Argentina": {"rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}},
    "Colômbia": {"rates": {"Saúde": 0.04, "Pensão": 0.04}},
    "Canadá": {"rates": {"CPP": 0.0595, "CPP2": 0.04, "EI": 0.0163, "Income Tax": 0.15}} # Simplificado
}
EMPLOYER_COST_DEFAULT = {
    # REQ 1: Encargos atualizados (mais precisos)
    "Brasil": [
        {"nome": "INSS Patronal", "percentual": 20.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Previdência", "teto": None},
        {"nome": "RAT", "percentual": 2.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Risco", "teto": None},
        {"nome": "Sistema S", "percentual": 5.8, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Terceiros", "teto": None},
        {"nome": "FGTS", "percentual": 8.0, "base": "Salário Bruto", "ferias": True, "decimo": True, "bonus": True, "obs": "Crédito empregado", "teto": None}
    ],
    "México": [
        {"nome": "IMSS Patronal", "percentual": 7.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Seguro social (aprox.)", "teto": "Teto IMSS"},
        {"nome": "INFONAVIT Empregador", "percentual": 5.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "Habitação", "teto": "Teto IMSS"},
        {"nome": "SAR (Aposentadoria)", "percentual": 2.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Adicionado", "teto": "Teto IMSS"},
        {"nome": "ISN (Imposto Estadual)", "percentual": 2.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Média (aprox.)", "teto": None}
    ],
    "Chile": [
        {"nome": "Seguro Desemprego", "percentual": 2.4, "base": "Salário", "ferias": True, "decimo": False, "bonus": True, "obs": "Empregador", "teto": ANNUAL_CAPS["CL_TETO_CESANTIA_UF"]},
        {"nome": "SIS (Invalidez)", "percentual": 1.53, "base": "Salário", "ferias": True, "decimo": False, "bonus": True, "obs": "REQ 1: Adicionado", "teto": ANNUAL_CAPS["CL_TETO_UF"]}
    ],
    "Argentina": [
        {"nome": "Contribuições Patronais", "percentual": 23.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Média ajustada", "teto": "Teto SIPA"}
    ],
    "Colômbia": [
        {"nome": "Saúde Empregador", "percentual": 8.5, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "—", "teto": None},
        {"nome": "Pensão Empregador", "percentual": 12.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "—", "teto": None},
        {"nome": "Parafiscales (SENA, ICBF...)", "percentual": 9.0, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: Adicionado", "teto": None},
        {"nome": "Cesantías (Fundo)", "percentual": 8.33, "base": "Salário", "ferias": True, "decimo": True, "bonus": True, "obs": "REQ 1: (1/12)", "teto": None}
    ],
    "Estados Unidos": [
        {"nome": "Social Security (ER)", "percentual": 6.2, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "REQ 1: Teto aplicado", "teto": ANNUAL_CAPS["US_FICA"]},
        {"nome": "Medicare (ER)", "percentual": 1.45, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "Sem teto", "teto": None},
        {"nome": "SUTA (avg)", "percentual": 2.0, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "REQ 1: Teto base aplicado", "teto": ANNUAL_CAPS["US_SUTA_BASE"]}
    ],
    "Canadá": [
        {"nome": "CPP (ER)", "percentual": 5.95, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "REQ 1: Teto aplicado", "teto": ANNUAL_CAPS["CA_CPP_YMPEx1"]},
        {"nome": "CPP2 (ER)", "percentual": 4.0, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "REQ 1: Teto 2 aplicado", "teto": ANNUAL_CAPS["CA_CPP_YMPEx2"]},
        {"nome": "EI (ER)", "percentual": 2.28, "base": "Salário", "ferias": False, "decimo": False, "bonus": True, "obs": "REQ 1: Teto aplicado", "teto": ANNUAL_CAPS["CA_EI_MIE"]}
    ]
}
BR_INSS_DEFAULT = {
    "vigencia": "2025-01-01",
    "teto_contribuicao": 1146.68,
    "teto_base": 8157.41,
    "faixas": [
        {"ate": 1412.00, "aliquota": 0.075},
        {"ate": 2666.68, "aliquota": 0.09},
        {"ate": 4000.03, "aliquota": 0.12},
        {"ate": 8157.41, "aliquota": 0.14}
    ]
}
BR_IRRF_DEFAULT = {
    "vigencia": "2025-01-01",
    "deducao_dependente": 189.59,
    "faixas": [
        {"ate": 2259.20, "aliquota": 0.00,  "deducao": 0.00},
        {"ate": 2826.65, "aliquota": 0.075, "deducao": 169.44},
        {"ate": 3751.05, "aliquota": 0.15,  "deducao": 381.44},
        {"ate": 4664.68, "aliquota": 0.225, "deducao": 662.77},
        {"ate": 999999999.0, "aliquota": 0.275, "deducao": 896.00}
    ]
}

# REQ 1: Fallback para cálculo líquido do Canadá
CA_CPP_EI_DEFAULT = {
    "cpp_rate": 0.0595,
    "cpp_exempt_monthly": ANNUAL_CAPS["CA_CPP_EXEMPT"] / 12.0,
    "cpp_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx1"] / 12.0,
    "cpp2_rate": 0.04,
    "cpp2_cap_monthly": ANNUAL_CAPS["CA_CPP_YMPEx2"] / 12.0,
    "ei_rate": 0.0163,
    "ei_cap_monthly": ANNUAL_CAPS["CA_EI_MIE"] / 12.0
}

# ============== STI RANGES (Sales / Non Sales) ==============
STI_RANGES = {
    "Non Sales": {
        "CEO": (1.00, 1.00),
        "Members of the GEB": (0.50, 0.80),
        "Executive Manager": (0.45, 0.70),
        "Senior Group Manager": (0.40, 0.60),
        "Group Manager": (0.30, 0.50),
        "Lead Expert / Program Manager": (0.25, 0.40),
        "Senior Manager": (0.20, 0.40),
        "Senior Expert / Senior Project Manager": (0.15, 0.35),
        "Manager / Selected Expert / Project Manager": (0.10, 0.30),
        "Others": (0.0, 0.10)
    },
    "Sales": {
        "Executive Manager / Senior Group Manager": (0.45, 0.70),
        "Group Manager / Lead Sales Manager": (0.35, 0.50),
        "Senior Manager / Senior Sales Manager": (0.25, 0.45),
        "Manager / Selected Sales Manager": (0.20, 0.35),
        "Others": (0.0, 0.15)
    }
}
STI_LEVEL_OPTIONS = {
    "Non Sales": [
        "CEO", "Members of the GEB", "Executive Manager", "Senior Group Manager", "Group Manager",
        "Lead Expert / Program Manager", "Senior Manager", "Senior Expert / Senior Project Manager",
        "Manager / Selected Expert / Project Manager", "Others"
    ],
    "Sales": [
        "Executive Manager / Senior Group Manager", "Group Manager / Lead Sales Manager",
        "Senior Manager / Senior Sales Manager", "Manager / Selected Sales Manager", "Others"
    ]
}
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

# REQ 1/8: Mapa Sidebar (SVG Minimalista Base64)
MAPA_AMERICAS_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjIgMjE1IiBzdHlsZT0iYmFja2dyb3VuZDp0cmFuc3BhcmVudDsiPgogIDxwYXRoIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIxLjIiIGZpbGw9Im5vbmUiIGQ9Ik0zOS4xMSA3My40NkwzMy42OSA3MC4xM0MzMS4wMyA2OC4wMiAyOS45MSA2NC45OCAzMC40MSA2Mi4xOEwzMi43MyA0OS4yM0MzMy4zOCA0NS42MiAzNS4zMSA0Mi41NiAzOC4wNyA0MC44MUw0MS4zMiAzOC4zOEM0My4zNyAzNi44OCA0NS44MyAzNi4zNyA0OC4yMSAzNi45OEw1OC4yMyAzOS4zN0M2MC4yMyA0MC4wMiA2MS44OSA0MS4zOSA2Mi44NSA0My4yMUw2NS43MiA0Ny45M0M2Ny4xNSA1MC41NyA2Ny4zMiA1My44MiA2Ni4xOCA1Ni44Mkw2Mi4xMyA2Ny45M0M2MS4xNiA3MC4zMyA1OS4zMyA3Mi4yNSA1Ny4wMyA3My4yMUw0OC42MyA3Ni4zNUM0NS41MyA3Ny42NyA0MS45MyA3Ni40NyAzOS4xMSA3My40NlpNOTQuNTcgNDEuNjdMODkuMDggMzcuNTJDODcuNDEgMzYuMTggODUuMjkgMzUuNDQgODMuMDcgMzUuNDhMODAuNTMgMzUuNTdDNzguNDMgMzUuNjMgNzYuNDEgMzYuMzggNzQuODUgMzcuNjFMNDguMSA1MS4xOEM0Ni43MSA1Mi4yNyA0NS42NiA1My43MiA0NS4wOSA1NS4zNUw0Mi45MiA2MC45OUM0Mi4wMSA2My41MiA0Mi4zNyA2Ni4zMiA0My45NSA2OC41M0w0OC44MiA3NS4zMUM1MC4wMyA3Ny4wMiA1MS43MyA3OC4zNSA1My43NyA3OC45OEw2MC42MyA4MS4wNEM2My4zMyA4MS45MiA2Ni4yNiA4MS42NiA2OC43MiA4MC4zMUw3NS4xOSA3Ni45OUM3Ny40NSA3NS43NyA3OS4yOCA3My44OSA4MC4zMyA3MS41MUw4MS42MiA2OC44OEM4Mi4yOCA2Ny40MyA4My4yOSA2Ni4yMSA4NC41OCA2NS4zOEw5MS41MiA2MC4yOEM5My4yMyA1OS4xNSA5NC41NSA1Ny41MiA5NS4yMSA1NS42NUw5Ny42MSA0OC45NEM5OC4xMyA0Ny4zNSA5Ny45OSA0NS42MiA5Ny4yNSA0NC4wM0w5NC41NyA0MS42N1pNMTAzLjMyIDU2LjYyTDEwMC4wNyA1NS4xM0M5OC4yMyA1NC4zMiA5Ni43OSA1Mi43NiA5Ni4yMSA1MC44N0w5NS40NSA0OC4yOEM5NS4xOSA0Ny40MyA5NS4xNyA0Ni41MyA5NS4zOCA0NS43M0w5Ni40MSA0Mi4yOEM5Ny4wNyA0MC4xMyA5OC42NyAzOC41MyAxMDA4LjcyIDM3Ljg4TDEwNC43OCAzNy4xM0MxMDYuNzMgMzYuNzggMTA4LjU5IDM3LjQxIDEwOS45MiAzOC44M0wxMTIuMDMgNDAuOTVDMTEzLjE3IDQyLjE3IDExMy44MyA0My44MSAxMTMuODMgNDUuNTNMMTEzLjU3IDQ5LjQ4QzExMy41MiA1MS4yNiAxMTIuODEgNTIuOTMgMTExLjYyIDU0LjExTDEwNy42MyA1OC40M0MxMDUuOTcgNjAuMDkgMTAzLjMyIDU5LjUxIDEwMi4yMyA1Ny43N0MxMDIuMDcgNTcuNDMgMTAxLjk1IDU2Ljc1IDEwMi4yMyA1Ni4xOEwxMDMuMzIgNTYuNjJaTTYwLjkyIDEyMS4xOEw1Ni4wMyAxMjAuNDNDNTMuNDMgMTIxLjA3IDUxLjE4IDEyMi45MiA1MC4xMiAxMjUuNDJMMzkuMzcgMTUxLjYyQzM4LjU2IDE1My44MiAzOC41NiAxNTYuMzcgMzkuMzcgMTU4LjU3TDUwLjEyIDE4NC43OEM1MS4xOCAxODcuMjggNTMuNDMgMTg5LjEzIDU2LjAzIDE4OS43OEw2MC45MiAxOTAuNTNDNjIuNTIgMTkxLjAxIDY0LjIyIDE5MS4wMSA2NS44MiAxOTAuNTNMNzAuNzIgMTg5Ljc4QzcyLjczIDE4OS4zNSA3NC41OCAxODguMTggNzUuOTEgMTg2LjQzTDc5LjQyIDE4Mi4yM0M4Mi4wNyAxNzkuMDMgODMuMDEgMTc0Ljc4IDgyLjE3IDE3MC44NEw3OS45MSAxNjIuNTRDNzguNDMgMTU2Ljc4IDc0LjM4IDE1MS44OCA2OC41MyAxNDkuNzdMNjIuMzMgMTQ3LjU3QzYxLjQ4IDE0Ny4yNiA2MC42MyAxNDcuMjYgNTkuNzggMTQ3LjU3TDUzLjU4IDE0OS43N0M0Ny43MyAxNTEuODggNDMuNjMgMTU2Ljc4IDQyLjE4IDE2Mi41NEwzOS45MiAxNzAuODRDMzkuMDcgMTc0Ljc4IDQwLjAxIDE3OS4wMyA0Mi42NSAxODIuMjNMNDYuMTcgMTg2LjQzQzQ3LjQ5IDE4OC4xOCA0OS4zNCAxODkuMzUgNTEuMzggMTg5Ljc4TDU0LjQ4IDE5MC4zOEM1NC43OCAxOTAuNDMgNTUuMDMgMTkwLjQzIDU1LjI4IDE5MC4zOEw1NS41MyAxOTAuMzhMNTEuMzggMTg5Ljc4TDQ5LjM0IDE4OS4zNUw0Ny40OSAxODguMThMNDYuMTcgMTg2LjQzTDQyLjY1IDE4Mi4yM0wzOS45MiAxNzAuODRMNDIuMTggMTYyLjVMMC40MiAxMjUuNDJMNTEuMTMgMTIyLjkyQzUxLjUxIDEyMi43NiA1MS44MyAxMjIuNTUgNTIuMTMgMTIyLjMyTDUyLjM4IDEyMi4yM0M1Mi43MyAxMjIuMDcgNTMuMDkgMTIxLjk1IDUzLjUgMTIxLjg4QzU0LjM1IDEyMS43IDU1LjIxIDEyMS43IDU2LjAzIDEyMS44OEw1OC4wMyAxMjIuMjNDNTguMzggMTIyLjMyIDU4LjY4IDEyMi40NSA1OC45MyAxMjIuNjdMNTkuMTggMTIyLjkzTDY4LjUzIDE0OS43N0w2Mi4zMyAxNDcuNTdMNTMuNTggMTQ5Ljc3TDQyLjE4IDE2Mi41NEwzOS45MiAxNzAuODRMNDIuNjUgMTgyLjIzTDQ2LjE3IDE4Ni40M0w0Ny40OSAxODguMThMODUuMDMgMTg4LjE4Qzg1LjY4IDE4Ny45NyA4Ni4yOCAxODcuNjcgODYuODMgMTg3LjI4TDg5Ljc4IDE4NS4wOEM5MS41MyAxODMuODIgOTIuNzMgMTgxLjk3IDkzLjEzIDE3OS44N0w5OC4xMyAxNjUuNTRDOTkuMDQgMTYzLjAxIDk4LjY4IDE2MC4xMyA5Ny4yIDE1Ry45OEw5Mi44NyAxNTAuOTNDOTEuNzMgMTQ5LjQ4IDkwLjAyIDE0OC41MyA4OC4xOCAxNDguMjJMODMuMjMgMTQ3LjI2QzgxLjM4IDE0Ny4wMSA3OS41MyAxNDcuNTIgNzggMTQ4LjY3TDczLjY4IDE1MS4zOEM3Mi4wNyAxNTIuNDIgNzAuOTMgMTU0LjA3IDcwLjQzIDE1NS45Mkw2OC42MyAxNjIuNTRDNjguMDcgMTY0LjcyIDY4LjU4IDE2Ny4wMiA3MC4wMyAxNjguNzNMNzMuODggMTczLjYyQzc0LjQ4IDE3NC40MyA3NS40MyAxNzQuOSA3Ni40MyAxNzQuOUw3OC42OCAxNzQuNjVDNzkuNTMgMTc0LjU1IDgwLjMyIDE3NC4yIDgwLjkzIDE3My42N0w4NS41OCAxNzAuMzhDODYuODQgMTY5LjQ4IDg3Ljc5IDE2OC4xMyA4OC4xMyAxNjYuNjJMODkuOTMgMTYwLjE4QzkwLjI4IDE1viii4ODIgOTAuMTggMTU3LjM3IDg5LjYzIDE1Ni4wOEw4OC40OCAxNTMuMThDODguMDMgMTUyLjEzIDg3LjE4IDE1MS4zOCA4Ni4xMyAxNTEuMTNM affinitiesAxNTAuNjNDODIuNTMgMTUwLjM4IDgxLjA4IDE1MC43MyA4MC4wMyAxNTEuNjJMNDguMSA1MS4xOEw0Ni4wMyA1NC4zMUM0NS44MyA1NC42MiA0NS42MSA1NC45MyA0NS40MyA1NS4yNUw0My4yNyA1OS45QzQyLjc5IDYxLjE1IDQyLjkgNjIuNTMgNDMuNjggNjMuNjlMNDguNTUgNzAuNDhDNDkuMDcgNzEuNDMgNDkuOTcgNzIuMSA1MC45OCA3Mi40M0w1Ny44NCA3NC41QzU5LjE5IDc0Ljk4IDYwLjY0IDc0LjQ4IDYxLjU0IDczLjQzTDY4LjA0IDY2LjVDNzAuMDQgNjQuMyA3MC4zMyA2MS4xIDY4LjUzIDU4Ljc1TDY0Ljc4IDUzLjQzQzYyLjAyIDUwLjM4IDU3LjQzIDQ5LjU3IDUzLjc3IDUyLjE4TDQ3LjE4IDU2Ljc1QzQ1Ljk4IDU3LjU4IDQ0LjkzIDU4Ljc4IDQ0LjIyIDYwLjE4TDQyLjA1IDY1Ljg0QzQxLjI1IDY4LjM3IDQyLjMxIDcxLjE3IDQ0LjUzIDczLjA3TDU1LjI4IDE5MC4zOEw1NS4wMyAxOTAuNDNMNzYuNDMgMTc0LjkiLz4KPC9zdmc+Cg=="

# ============================== HELPERS (REQ 1: Atualizados) ===============================


def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)


def get_sti_range(area: str, level: str) -> Tuple[float, float]:
    area_tbl = STI_RANGES.get(area, {})
    rng = area_tbl.get(level)
    if not rng:
        return (0.0, None)
    return rng

# -------- Funções de Cálculo (Brasil) ----------


def calc_inss_progressivo(salario: float, inss_tbl: Dict[str, Any]) -> float:
    contrib = 0.0
    limite_anterior = 0.0
    for faixa in inss_tbl.get("faixas", []):
        teto_faixa = float(faixa["ate"])
        aliquota = float(faixa["aliquota"])
        if salario > limite_anterior:
            base_faixa = min(salario, teto_faixa) - limite_anterior
            contrib += base_faixa * aliquota
            limite_anterior = teto_faixa
        else:
            break
    teto = inss_tbl.get("teto_contribuicao", None)
    if teto is not None:
        contrib = min(contrib, float(teto))
    return max(contrib, 0.0)


def calc_irrf(base: float, dep: int, irrf_tbl: Dict[str, Any]) -> float:
    ded_dep = float(irrf_tbl.get("deducao_dependente", 0.0))
    base_calc = max(base - ded_dep * max(int(dep), 0), 0.0)
    for faixa in irrf_tbl.get("faixas", []):
        if base_calc <= float(faixa["ate"]):
            aliq = float(faixa["aliquota"])
            ded = float(faixa.get("deducao", 0.0))
            return max(base_calc * aliq - ded, 0.0)
    return 0.0


def br_net(salary: float, dependentes: int, br_inss_tbl: Dict[str, Any], br_irrf_tbl: Dict[str, Any]):
    lines = []
    total_earn = salary
    inss = calc_inss_progressivo(salary, br_inss_tbl)
    base_ir = max(salary - inss, 0.0)
    irrf = calc_irrf(base_ir, dependentes, br_irrf_tbl)
    lines.append(("Salário Base", salary, 0.0))
    lines.append(("INSS", 0.0, inss))
    lines.append(("IRRF", 0.0, irrf))
    fgts_value = salary * 0.08
    net = total_earn - (inss + irrf)
    return lines, total_earn, inss + irrf, net, fgts_value


def generic_net(salary: float, rates: Dict[str, float]):
    lines = [("Base", salary, 0.0)]
    total_earn = salary
    total_ded = 0.0
    for k, aliq in rates.items():
        v = salary * float(aliq)
        total_ded += v
        lines.append((k, 0.0, v))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net


def us_net(salary: float, state_code: str, state_rate: float):
    FICA_WAGE_BASE_MONTHLY = ANNUAL_CAPS["US_FICA"] / 12.0
    
    lines = [("Base Pay", salary, 0.0)]
    total_earn = salary
    
    salario_base_fica = min(salary, FICA_WAGE_BASE_MONTHLY)
    fica = salario_base_fica * 0.062
    
    medicare = salary * 0.0145 # Sem teto
    total_ded = fica + medicare
    
    lines += [("FICA (Social Security)", 0.0, fica),
              ("Medicare", 0.0, medicare)]
    if state_code:
        sr = state_rate if state_rate is not None else 0.0
        if sr > 0:
            sttax = salary * sr
            total_ded += sttax
            lines.append((f"State Tax ({state_code})", 0.0, sttax))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

# REQ 1: Cálculo líquido do Canadá (com tetos)
def ca_net(salary: float, ca_tbl: Dict[str, Any]):
    lines = [("Base Pay", salary, 0.0)]
    total_earn = salary
    
    # CPP
    cpp_base = max(0, min(salary, ca_tbl["cpp_cap_monthly"]) - ca_tbl["cpp_exempt_monthly"])
    cpp = cpp_base * ca_tbl["cpp_rate"]
    
    # CPP2
    cpp2_base = max(0, min(salary, ca_tbl["cpp2_cap_monthly"]) - ca_tbl["cpp_cap_monthly"])
    cpp2 = cpp2_base * ca_tbl["cpp2_rate"]

    # EI
    ei_base = min(salary, ca_tbl["ei_cap_monthly"])
    ei = ei_base * ca_tbl["ei_rate"]
    
    # Income Tax (simplificado)
    income_tax = salary * 0.15 
    
    total_ded = cpp + cpp2 + ei + income_tax
    lines.append(("CPP", 0.0, cpp))
    lines.append(("CPP2", 0.0, cpp2))
    lines.append(("EI", 0.0, ei))
    lines.append(("Income Tax (Est.)", 0.0, income_tax))
    
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net


def calc_country_net(country: str, salary: float, state_code=None, state_rate=None,
                     dependentes=0, tables_ext=None, br_inss_tbl=None, br_irrf_tbl=None):
    if country == "Brasil":
        lines, te, td, net, fgts = br_net(
            salary, dependentes, br_inss_tbl, br_irrf_tbl)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": fgts}
    elif country == "Estados Unidos":
        lines, te, td, net = us_net(salary, state_code, state_rate)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    elif country == "Canadá": # REQ 1: Cálculo dedicado
        lines, te, td, net = ca_net(salary, CA_CPP_EI_DEFAULT)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    else:
        rates = (tables_ext or {}).get("TABLES", {}).get(
            country, {}).get("rates", {})
        if not rates:
            rates = TABLES_DEFAULT.get(country, {}).get("rates", {})
        lines, te, td, net = generic_net(salary, rates)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}

# REQ 1: Função de Custo do Empregador reescrita para aplicar tetos
def calc_employer_cost(country: str, salary: float, bonus: float, T: Dict[str, str], tables_ext=None):
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(
        country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    enc_list = (tables_ext or {}).get("EMPLOYER_COST", {}).get(
        country, EMPLOYER_COST_DEFAULT.get(country, []))
    benefits = COUNTRY_BENEFITS.get(
        country, {"ferias": False, "decimo": False})
    
    # ----------------- Tabela de Encargos (DataFrame) -----------------
    df = pd.DataFrame(enc_list)
    if not df.empty:
        df[T["cost_header_charge"]] = df["nome"]
        df[T["cost_header_percent"]] = df["percentual"].apply(lambda p: f"{p:.2f}%")
        df[T["cost_header_base"]] = df["base"]
        df[T["cost_header_obs"]] = df["obs"]
        df[T["cost_header_bonus"]] = ["✅" if b else "❌" for b in df["bonus"]]
        cols = [T["cost_header_charge"], T["cost_header_percent"],
                T["cost_header_base"], T["cost_header_bonus"], T["cost_header_obs"]]
        
        if benefits.get("ferias", False):
            df[T["cost_header_vacation"]] = ["✅"if b else "❌" for b in df["ferias"]]
            cols.insert(3, T["cost_header_vacation"])
        if benefits.get("decimo", False):
            df[T["cost_header_13th"]] = ["✅" if b else "❌" for b in df["decimo"]]
            insert_pos = 4 if benefits.get("ferias", False) else 3
            cols.insert(insert_pos, T["cost_header_13th"])
        df = df[cols]
    
    # ----------------- Cálculo do Custo Total Anual (com Tetos) -----------------
    salario_anual_base = salary * 12.0
    salario_anual_beneficios = salary * months # Ex: 13.33 no BR, 14.00 na CO
    
    total_cost_items = []
    
    for item in enc_list:
        perc = item.get("percentual", 0.0) / 100.0
        teto = item.get("teto", None)
        incide_bonus = item.get("bonus", False)
        
        # Define a base de cálculo
        if country in ["Estados Unidos", "Canadá"]:
            base_calc_anual = salario_anual_base
            if incide_bonus:
                base_calc_anual += bonus
        else:
            base_calc_anual = salario_anual_beneficios
            if incide_bonus:
                base_calc_anual += bonus
                
        # Aplica o teto ANUAL (se houver)
        if teto is not None and isinstance(teto, (int, float)):
            # Caso especial CPP2
            if item.get("nome") == "CPP2 (ER)":
                base_cpp1 = min(base_calc_anual, ANNUAL_CAPS["CA_CPP_YMPEx1"])
                base_calc_anual = max(0, min(base_calc_anual, teto) - base_cpp1)
            else:
                base_calc_anual = min(base_calc_anual, teto)
        
        custo_item = base_calc_anual * perc
        total_cost_items.append(custo_item)

    total_encargos = sum(total_cost_items)
    
    custo_total_anual = (salary * months) + bonus + total_encargos
    
    mult = (custo_total_anual / salario_anual_base) if salario_anual_base > 0 else 0.0
    
    return custo_total_anual, mult, df, months

# -------- Helpers de Tradução (Req 2) ----------

def get_sti_area_map(T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    display_list = [T["sti_area_non_sales"], T["sti_area_sales"]]
    keys = ["Non Sales", "Sales"]
    key_map = dict(zip(display_list, keys))
    return display_list, key_map


def get_sti_level_map(area: str, T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    keys = STI_LEVEL_OPTIONS.get(area, [])
    display_list = [T.get(STI_I18N_KEYS.get(key, ""), key) for key in keys]
    key_map = dict(zip(display_list, keys))
    return display_list, key_map


# ======================== FETCH REMOTO (sem cache) =====================


def fetch_json_no_cache(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    return r.json()


def load_tables():
    try:
        us_states = fetch_json_no_cache(URL_US_STATES)
    except Exception:
        us_states = US_STATE_RATES_DEFAULT
    try:
        country_tables = fetch_json_no_cache(URL_COUNTRY_TABLES)
    except Exception:
        country_tables = {
            "TABLES": TABLES_DEFAULT,
            "EMPLOYER_COST": EMPLOYER_COST_DEFAULT,
            "REMUN_MONTHS": REMUN_MONTHS_DEFAULT,
        }
    try:
        br_inss = fetch_json_no_cache(URL_BR_INSS)
    except Exception:
        br_inss = BR_INSS_DEFAULT
    try:
        br_irrf = fetch_json_no_cache(URL_BR_IRRF)
    except Exception:
        br_irrf = BR_IRRF_DEFAULT
    return us_states, country_tables, br_inss, br_irrf


# ============================== SIDEBAR (REQ 2, 7 e 8) ===============================
with st.sidebar:
    # REQ 7: Título Sidebar + REQ 2: Espaçamento
    st.markdown("<h2 style='color:white; text-align:center; font-size:20px; margin-bottom: 25px;'>Simulador de Salários<br>(Região das Americas)</h2>", unsafe_allow_html=True)
    
    idioma = st.selectbox("🌐 Idioma / Language / Idioma",
                          list(I18N.keys()), index=0, key="lang_select")
    T = I18N[idioma]
    st.markdown(f"### {T['country']}")
    country = st.selectbox(T["choose_country"] if "choose_country" in T else T["country"],
                             list(COUNTRIES.keys()), index=0, key="country_select")
    st.markdown(f"### {T['menu']}")
    menu = st.radio(
        T["choose_menu"] if "choose_menu" in T else "Menu",
        [T["menu_calc"], T["menu_rules"], T["menu_rules_sti"], T["menu_cost"]],
        index=0, key="menu_radio"
    )
    
    # REQ 1/8: Mapa Sidebar
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{MAPA_AMERICAS_B64}" style="width:100%; height:auto; padding-top: 30px; opacity: 0.7;">', 
        unsafe_allow_html=True
    )


US_STATE_RATES, COUNTRY_TABLES, BR_INSS_TBL, BR_IRRF_TBL = load_tables()

# === dados do país ===
symbol = COUNTRIES[country]["symbol"]
flag = COUNTRIES[country]["flag"]
valid_from = COUNTRIES[country]["valid_from"]

# ======================= TÍTULO DINÂMICO (REQ 3) ==============================
if menu == T["menu_calc"]:
    title = T["title_calc"].format(pais=country) # REQ 3
elif menu == T["menu_rules"]:
    title = T["title_rules"].format(pais=country)
elif menu == T["menu_rules_sti"]:
    title = T["title_rules_sti"]
else:
    title = T["title_cost"].format(pais=country)

st.markdown(
    f"<div class='country-header'><div class='country-flag'>{flag}</div>"
    f"<div class='country-title'>{title}</div></div>",
    unsafe_allow_html=True
)
st.write(
    f"**{T['valid_from'] if 'valid_from' in T else 'Vigência'}:** {valid_from}")
st.write("---") # REQ 9 (espaçamento)

# ========================= SIMULADOR DE REMUNERAÇÃO (REQ 2) ==========================
if menu == T["menu_calc"]:

    area_options_display, area_display_map = get_sti_area_map(T)

    if country == "Brasil":
        st.subheader(T["calc_params_title"])
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1.6, 1.6, 2.4])
        salario = c1.number_input(
            f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        dependentes = c2.number_input(
            f"{T['dependents']}", min_value=0, value=0, step=1, key="dep_input")
        bonus_anual = c3.number_input(
            f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        area_display = c4.selectbox(
            T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = c5.selectbox(T["level"], level_options_display, index=len(
            level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]

        st.write("---")
        st.subheader(T["monthly_comp_title"])
        state_code, state_rate = None, None

    elif country == "Estados Unidos":
        st.subheader(T["calc_params_title"]) 
        c1, c2, c3, c4 = st.columns([2, 1.4, 1.2, 1.4])
        salario = c1.number_input(
            f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        state_code = c2.selectbox(f"{T['state']}", list(
            US_STATE_RATES.keys()), index=0, key="state_select_main")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input(f"{T['state_rate']}", min_value=0.0, max_value=0.20,
                                      value=default_rate, step=0.001, format="%.3f", key="state_rate_input")
        bonus_anual = c4.number_input(
            f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        area_display = r1.selectbox(
            T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = r2.selectbox(T["level"], level_options_display, index=len(
            level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]
        dependentes = 0
        st.write("---")
        st.subheader(T["monthly_comp_title"])

    else:
        st.subheader(T["calc_params_title"])
        c1, c2 = st.columns([2, 1.6])
        salario = c1.number_input(
            f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        bonus_anual = c2.number_input(
            f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        area_display = r1.selectbox(
            T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = r2.selectbox(T["level"], level_options_display, index=len(
            level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]
        dependentes = 0
        state_code, state_rate = None, None
        st.write("---")
        st.subheader(T["monthly_comp_title"]) 

    # ---- Cálculo do país selecionado (REQ 1: Atualizado)
    calc = calc_country_net(
        country, salario,
        state_code=state_code, state_rate=state_rate, dependentes=dependentes,
        tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL
    )

    # ---- Tabela de proventos/descontos
    df = pd.DataFrame(calc["lines"], columns=[
                      "Descrição", T["earnings"], T["deductions"]])
    df[T["earnings"]] = df[T["earnings"]].apply(
        lambda v: money_or_blank(v, symbol))
    df[T["deductions"]] = df[T["deductions"]].apply(
        lambda v: money_or_blank(v, symbol))
    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True)
    st.table(df)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Cards totais (linha única) (REQ 2: Fonte)
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(
        f"<div class='metric-card' style='border-left: 5px solid #28a745; background: #e6ffe6;'><h4>💰 {T['tot_earnings']}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(
        f"<div class='metric-card' style='border-left: 5px solid #dc3545; background: #ffe6e6;'><h4>📉 {T['tot_deductions']}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(
        f"<div class='metric-card' style='border-left: 5px solid #007bff; background: #e6f7ff;'><h4>💵 {T['net']}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)

    if country == "Brasil":
        st.write("")
        st.markdown(
            f"**💼 {T['fgts_deposit']}:** {fmt_money(calc['fgts'], symbol)}")

    # ---------- Composição da Remuneração Total Anual ----------
    st.write("---") 

    st.subheader(T["annual_comp_title"])

    # ==== Cálculos base ====
    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(
        country, REMUN_MONTHS_DEFAULT.get(country, 12.0)
    )
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual

    # ==== Validação do bônus (STI) ====
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0
    pct_txt = f"{bonus_pct*100:.1f}%"
    faixa_txt = f"≤ {(max_pct or 0)*100:.0f}%" if level == "Others" else f"{min_pct*100:.0f}% – {max_pct*100:.0f}%"
    dentro = (bonus_pct <= (max_pct or 0)) if level == "Others" else (
        min_pct <= bonus_pct <= max_pct)
    cor = "#1976d2" if dentro else "#d32f2f"
    status_txt = T["sti_in_range"] if dentro else T["sti_out_range"]
    bg_cor = "#e6f7ff" if dentro else "#ffe6e6"
    
    # REQ 5 (Texto STI)
    sti_line = (
        f"STI ratio do bônus: <strong>{pct_txt}</strong> — "
        f"<strong>{status_txt}</strong> ({faixa_txt}) — "
        f"<em>{area_display} • {level_display}</em>"
    )

    # ==== Layout (REQ 5: Fontes) ====
    c1, c2 = st.columns(2)

    # --- Coluna 1: Labels ---
    c1.markdown(
        f"""
        <div class='annual-card-base annual-card-label' style='border-left-color: #28a745; background: #e6ffe6;'>
            <h4>{T['annual_salary']}</h4>
            <span class='sti-note'>({T['months_factor']}: {months})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1.markdown(
        f"""
        <div class='annual-card-base annual-card-label' style='border-left-color: {cor}; background: {bg_cor};'>
            <h4>{T['annual_bonus']}</h4>
            <span class='sti-note' style='color:{cor}'>{sti_line}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1.markdown(
        f"""
        <div class='annual-card-base annual-card-label' style='border-left-color: #0a3d62; background: #e6f0f8;'>
            <h4>{T['annual_total']}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Coluna 2: Valores ---
    c2.markdown(
        f"""
        <div class='annual-card-base annual-card-value' style='border-left-color: #28a745; background: #e6ffe6;'>
            <h3>{fmt_money(salario_anual, symbol)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"""
        <div class='annual-card-base annual-card-value' style='border-left-color: {cor}; background: {bg_cor};'>
            <h3>{fmt_money(bonus_anual, symbol)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"""
        <div class='annual-card-base annual-card-value' style='border-left-color: #0a3d62; background: #e6f0f8;'>
            <h3>{fmt_money(total_anual, symbol)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Gráfico de Pizza (REQ 3: Correção de Erro) ---
    st.write("---")
    
    chart_df = pd.DataFrame(
        {"Componente": [T["annual_salary"].split(" (")[0], T["annual_bonus"]], 
         "Valor": [salario_anual, bonus_anual]}
    )

    base = (
        alt.Chart(chart_df)
        .transform_joinaggregate(Total="sum(Valor)")
        .transform_calculate(Percent="datum.Valor / datum.Total")
    )

    pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(
        theta=alt.Theta("Valor:Q", stack=True),
        color=alt.Color(
            "Componente:N",
            legend=alt.Legend(
                orient="bottom", direction="horizontal",
                title=None, labelLimit=250, 
                labelFontSize=15, # REQ 5: Aumentado para 15px
                symbolSize=90
            ),
        ),
        tooltip=[
            alt.Tooltip("Componente:N"),
            alt.Tooltip("Valor:Q", format=",.2f"),
            alt.Tooltip("Percent:Q", format=".1%"),
        ],
    )

    labels = (
        base.transform_filter(alt.datum.Percent >= 0.01)
        .mark_text(radius=80, fontWeight="bold", color="white")
        .encode(theta=alt.Theta("Valor:Q", stack=True),
                text=alt.Text("Percent:Q", format=".1%"))
    )

    chart = (
        alt.layer(pie, labels)
        .properties(title="") # REQ 3: Corrigido de None para ""
        .configure_legend(orient="bottom", title=None, labelLimit=250)
        .configure_view(strokeWidth=0)
        .resolve_scale(color='independent')
    )

    st.altair_chart(chart, use_container_width=True)


# =========================== REGRAS DE CONTRIBUIÇÕES (REQ 1: Atualizadas) ===================
elif menu == T["menu_rules"]:
    st.subheader(T["rules_expanded"])

    if country == "Brasil":
        if idioma == "Português":
            st.markdown(f"""
### 🇧🇷 {T["rules_emp"]}
- **INSS (Previdência Social):** Alíquota progressiva (7.5% a 14%) aplicada por faixas de salário.
  - **Base:** Salário Bruto.
  - **Teto da Base (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_base', 8157.41), 'R$')}. Salários acima disso contribuem sobre o teto.
  - **Teto da Contribuição (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_contribuicao', 1146.68), 'R$')}.
- **IRRF (Imposto de Renda):** Alíquota progressiva (0% a 27.5%) com parcelas a deduzir.
  - **Base:** Salário Bruto - INSS - ( {fmt_money(BR_IRRF_DEFAULT.get('deducao_dependente', 189.59), 'R$')} × Nº de Dependentes).

### 🇧🇷 {T["rules_er"]}
- **INSS Patronal (CPP):** 20% (Regra Geral). **Base:** Total da folha (Salário Bruto).
- **RAT/FAP (Risco Acidente):** 1% a 3% (usamos 2% no simulador). **Base:** Total da folha.
- **Sistema S (Terceiros):** ~5.8%. **Base:** Total da folha.
- **FGTS (Fundo de Garantia):** 8%. **Base:** Total da folha. (Não é um imposto, mas um custo/depósito).

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
O custo anual total no Brasil inclui o 13º Salário (1 salário extra) e Férias (1 salário + 1/3 de bônus constitucional).
- O fator de meses `13.33` (12 + 1 + 0.33) reflete essa base de custo anual.
- Todos os encargos do empregador (INSS, RAT, Sistema S, FGTS) incidem sobre o 13º e as Férias.
""")
        else: # Inglês/Espanhol (Simplificado para brevidade, lógica é a mesma)
            st.markdown(f"""
### 🇧🇷 {T["rules_emp"]}
- **INSS (Social Security):** Progressive rate (7.5% to 14%) applied in brackets.
  - **Base:** Gross Salary, capped at {fmt_money(BR_INSS_DEFAULT.get('teto_base', 8157.41), 'R$')}.
  - **Contribution Cap (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_contribuicao', 1146.68), 'R$')}.
- **IRRF (Income Tax):** Progressive rate (0% to 27.5%) with fixed deductions.
  - **Base:** Gross Salary - INSS - ( {fmt_money(BR_IRRF_DEFAULT.get('deducao_dependente', 189.59), 'R$')} × No. of Dependents).

### 🇧🇷 {T["rules_er"]}
- **INSS Patronal (CPP):** 20% (General rule). **Base:** Total payroll.
- **RAT/FAP (Work Accident):** ~2%. **Base:** Total payroll.
- **"Sistema S" (Third-parties):** ~5.8%. **Base:** Total payroll.
- **FGTS (Severance Fund):** 8%. **Base:** Total payroll.

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
The annual cost factor `13.33` (12 + 1 + 0.33) reflects the 13th Salary (1 extra) and Vacation (1 salary + 1/3 bonus). All employer charges apply to this full base.
""")

    elif country == "Estados Unidos":
        if idioma == "Português":
            st.markdown(f"""
### 🇺🇸 {T["rules_emp"]}
- **FICA (Social Security):** 6.2%.
  - **Base:** Salário Bruto, aplicado **somente** até o teto anual de {fmt_money(ANNUAL_CAPS["US_FICA"], 'US$')}. Salários acima disso não pagam esta contribuição.
- **Medicare:** 1.45%.
  - **Base:** Salário Bruto total (sem teto).
- **State Tax (Imposto Estadual):** Varia (0% a ~8%+). **Base:** Salário Bruto.

### 🇺🇸 {T["rules_er"]}
- **FICA (Social Security) Match:** 6.2%. **Base:** Mesma base e teto do empregado ({fmt_money(ANNUAL_CAPS["US_FICA"], 'US$')}/ano).
- **Medicare Match:** 1.45%. **Base:** Salário Bruto total (sem teto).
- **SUTA/FUTA (Desemprego):** ~2.0% (Média).
  - **Base:** Aplicado sobre uma base salarial muito baixa, com teto de aprox. {fmt_money(ANNUAL_CAPS["US_SUTA_BASE"], 'US$')}/ano. O custo real deste item é baixo para salários altos.

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
- Não há 13º salário obrigatório por lei.
- Férias (PTO - Paid Time Off) são um benefício negociado, não uma provisão com encargos adicionais.
- O fator de meses usado para custo é `12.00`.
""")
        else: # Inglês/Espanhol
            st.markdown(f"""
### 🇺🇸 {T["rules_emp"]}
- **FICA (Social Security):** 6.2%.
  - **Base:** Gross Salary, applied **only** up to the annual cap of {fmt_money(ANNUAL_CAPS["US_FICA"], 'US$')}.
- **Medicare:** 1.45%.
  - **Base:** Total Gross Salary (no cap).
- **State Tax:** Varies (0% to ~8%+).

### 🇺🇸 {T["rules_er"]}
- **FICA (Social Security) Match:** 6.2%. **Base:** Same base and cap as the employee ({fmt_money(ANNUAL_CAPS["US_FICA"], 'US$')}/year).
- **Medicare Match:** 1.45%. **Base:** Total Gross Salary (no cap).
- **SUTA/FUTA (Unemployment):** ~2.0% (Average).
  - **Base:** Applied only on a low wage base, capped at ~{fmt_money(ANNUAL_CAPS["US_SUTA_BASE"], 'US$')}/year.

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
- No mandatory 13th salary.
- Vacation (PTO) is a negotiated benefit.
- The months factor used for cost is `12.00`.
""")

    elif country == "México":
        if idioma == "Português":
            st.markdown(f"""
### 🇲🇽 {T["rules_emp"]}
- **ISR (Imposto de Renda):** Alíquota progressiva (complexa).
- **IMSS (Seguro Social):** Taxa percentual sobre o salário (com teto).
- *Nota: O simulador usa taxas fixas como uma **simplificação**.*

### 🇲🇽 {T["rules_er"]}
- **IMSS Patronal:** Cota do empregador (~7%).
- **INFONAVIT (Habitação):** 5%.
- **SAR (Aposentadoria):** 2% (REQ 1: Adicionado).
- **ISN (Imposto Estadual):** ~2.5% (REQ 1: Adicionado).
- **Base:** Salário de Contribuição (com tetos, não totalmente modelado).

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
- **Aguinaldo (13º):** Obrigatório, mínimo de 15 dias de salário.
- **Prima Vacacional:** 25% pagos sobre o salário dos dias de férias.
- O fator de meses `12.50` (12 + 15/30 dias) reflete o custo do Aguinaldo.
""")
        else: # Inglês/Espanhol
            st.markdown(f"""
### 🇲🇽 {T["rules_emp"]}
- **ISR (Income Tax):** Complex progressive rate.
- **IMSS (Social Security):** Percentage rate on salary (capped).
- *Note: The simulator uses flat rates as a **simplification**.*

### 🇲🇽 {T["rules_er"]}
- **IMSS (Employer):** Employer's share (~7%).
- **INFONAVIT (Housing):** 5%.
- **SAR (Retirement):** 2% (REQ 1: Added).
- **ISN (State Tax):** ~2.5% (REQ 1: Added).
- **Base:** Contribution Salary (with caps, not fully modeled).

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
- **Aguinaldo (13th):** Mandatory, minimum 15 days of salary.
- **Prima Vacacional (Vacation Bonus):** 25% paid on vacation days.
- The `12.50` months factor (12 + 15/30 days) reflects the Aguinaldo cost.
""")

    elif country == "Chile":
        if idioma == "Português":
            st.markdown(f"""
### 🇨🇱 {T["rules_emp"]}
- **AFP (Pensão):** 10% (obrigatório) + comissão da administradora (ex: ~1.15%).
  - **Base:** Salário Bruto, com teto de ~{ANNUAL_CAPS["CL_TETO_UF"]} UF.
- **Saúde (FONASA ou ISAPRE):** 7% (obrigatório).
  - **Base:** Salário Bruto, com o mesmo teto.
- *O simulador usa 11.15% (AFP+comissão média) e 7%.*

### 🇨🇱 {T["rules_er"]}
- **Seguro de Cesantía (Seguro Desemprego):** 2.4%.
  - **Base:** Salário Bruto, com teto de ~{ANNUAL_CAPS["CL_TETO_CESANTIA_UF"]} UF.
- **SIS (Seguro Invalidez):** 1.53% (REQ 1: Adicionado).
  - **Base:** Salário Bruto, com teto de ~{ANNUAL_CAPS["CL_TETO_UF"]} UF.

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
- **Aguinaldo (13º):** Não é obrigatório por lei (opcional/negociado).
- O fator de meses usado para custo é `12.00`.
""")
        else: # Inglês/Espanhol
            st.markdown(f"""
### 🇨🇱 {T["rules_emp"]}
- **AFP (Pension):** 10% (mandatory) + admin fee (e.g., ~1.15%).
  - **Base:** Gross Salary, capped at ~{ANNUAL_CAPS["CL_TETO_UF"]} UF.
- **Health (FONASA or ISAPRE):** 7% (mandatory).
  - **Base:** Gross Salary, with the same cap.
- *Simulator uses 11.15% (AFP+avg. fee) and 7%.*

### 🇨🇱 {T["rules_er"]}
- **Seguro de Cesantía (Unemployment):** 2.4%.
  - **Base:** Gross Salary, capped at ~{ANNUAL_CAPS["CL_TETO_CESANTIA_UF"]} UF.
- **SIS (Disability Insurance):** 1.53% (REQ 1: Added).
  - **Base:** Gross Salary, capped at ~{ANNUAL_CAPS["CL_TETO_UF"]} UF.

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
- **Aguinaldo (13th):** Not mandatory by law (optional/negotiated).
- The months factor used for cost is `12.00`.
""")

    elif country == "Argentina":
        if idioma == "Português":
            st.markdown(f"""
### 🇦🇷 {T["rules_emp"]}
- **Jubilación (SIPA):** 11%.
- **Obra Social (Saúde):** 3%.
- **PAMI (INSSJP):** 3%.
- **Base:** Total (17%) aplicado sobre o Salário Bruto, com teto salarial (não modelado).

### 🇦🇷 {T["rules_er"]}
- **Contribuições Patronais:** Total de ~23.5% (REQ 1: Ajustado).
- **Base:** Salário Bruto, também com teto (não modelado).

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
- **SAC (Sueldo Anual Complementario):** É o 13º salário, pago em duas parcelas.
- O fator de meses `13.00` (12 + 1) reflete essa base de custo anual.
- Os encargos patronais incidem sobre o SAC.
""")
        else: # Inglês/Espanhol
            st.markdown(f"""
### 🇦🇷 {T["rules_emp"]}
- **Jubilación (SIPA - Pension):** 11%.
- **Obra Social (Health Care):** 3%.
- **PAMI (INSSJP):** 3%.
- **Base:** Total (17%) applied to Gross Salary, with a salary cap (not modeled).

### 🇦🇷 {T["rules_er"]}
- **Employer Contributions:** Total of ~23.5% (REQ 1: Adjusted).
- **Base:** Gross Salary, also with a salary cap (not modeled).

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
- **SAC (Sueldo Anual Complementario):** This is the 13th salary, paid in two installments.
- The `13.00` months factor (12 + 1) reflects this annual cost base.
- Employer contributions apply to the SAC.
""")

    elif country == "Colômbia":
        if idioma == "Português":
            st.markdown(f"""
### 🇨🇴 {T["rules_emp"]}
- **Salud (EPS):** 4%. **Base:** Salário Bruto.
- **Pensión:** 4%. **Base:** Salário Bruto.

### 🇨🇴 {T["rules_er"]}
- **Salud (EPS):** 8.5%. **Base:** Salário Bruto.
- **Pensão:** 12%. **Base:** Salário Bruto.
- **Parafiscales (SENA, ICBF...):** 9% (REQ 1: Adicionado).
- **Cesantías (Fundo):** 8.33% (1/12) (REQ 1: Adicionado).

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
- **Prima de Servicios:** É o 13º salário (1 salário/ano, pago em duas parcelas).
- **Cesantías:** É um custo adicional (1 salário/ano) depositado em um fundo.
- **REQ 1: Fator de meses ajustado para `14.00` (12 Sal + 1 Prima + 1 Cesantías).**
""")
        else: # Inglês/Espanhol
            st.markdown(f"""
### 🇨🇴 {T["rules_emp"]}
- **Salud (EPS - Health):** 4%. **Base:** Gross Salary.
- **Pensión (Pension):** 4%. **Base:** Gross Salary.

### 🇨🇴 {T["rules_er"]}
- **Salud (EPS):** 8.5%. **Base:** Gross Salary.
- **Pensión:** 12%. **Base:** Gross Salary.
- **Parafiscales (SENA, ICBF...):** 9% (REQ 1: Added).
- **Cesantías (Fund):** 8.33% (1/12) (REQ 1: Added).

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
- **Prima de Servicios:** This is the 13th salary (1 salary/year, paid in two installments).
- **Cesantías:** This is a separate additional cost (1 salary/year) deposited into a fund.
- **REQ 1: Months factor adjusted to `14.00` (12 Sal + 1 Prima + 1 Cesantías).**
""")

    elif country == "Canadá":
        if idioma == "Português":
            st.markdown(f"""
### 🇨🇦 {T["rules_emp"]}
- **CPP (Canada Pension Plan):** 5.95%.
  - **Base:** Salário Bruto, (após isenção) até o teto 1 (YMPE - ~{fmt_money(ANNUAL_CAPS["CA_CPP_YMPEx1"], 'CAD$')}).
- **CPP2 (Segundo Nível):** 4.0%.
  - **Base:** Salário Bruto, (após teto 1) até o teto 2 (YMPE2 - ~{fmt_money(ANNUAL_CAPS["CA_CPP_YMPEx2"], 'CAD$')}).
- **EI (Employment Insurance):** 1.63%.
  - **Base:** Salário Bruto, até o teto de ganhos (MIE - ~{fmt_money(ANNUAL_CAPS["CA_EI_MIE"], 'CAD$')}).
- **Income Tax (Imposto de Renda):** Progressivo (Federal + Provincial) (Simplificado no simulador).

### 🇨🇦 {T["rules_er"]}
- **CPP Match:** 5.95% (sobre Teto 1).
- **CPP2 Match:** 4.0% (sobre Teto 2).
- **EI Match:** 1.4x a cota do empregado (~2.28%).
- **Base:** Mesmas bases e tetos do empregado.

#### {T['cost_header_13th']} e {T['cost_header_vacation']}
- **13º Salário:** Não é obrigatório por lei.
- O fator de meses usado para custo é `12.00`.
""")
        else: # Inglês/Espanhol
            st.markdown(f"""
### 🇨🇦 {T["rules_emp"]}
- **CPP (Canada Pension Plan):** 5.95%.
  - **Base:** Gross Salary, (after exemption) up to Cap 1 (YMPE - ~{fmt_money(ANNUAL_CAPS["CA_CPP_YMPEx1"], 'CAD$')}).
- **CPP2 (Second Tier):** 4.0%.
  - **Base:** Gross Salary, (after Cap 1) up to Cap 2 (YMPE2 - ~{fmt_money(ANNUAL_CAPS["CA_CPP_YMPEx2"], 'CAD$')}).
- **EI (Employment Insurance):** 1.63%.
  - **Base:** Gross Salary, up to max earnings (MIE - ~{fmt_money(ANNUAL_CAPS["CA_EI_MIE"], 'CAD$')}).
- **Income Tax:** Progressive (Federal + Provincial) (Simplified in simulator).

### 🇨🇦 {T["rules_er"]}
- **CPP Match:** 5.95% (on Cap 1).
- **CPP2 Match:** 4.0% (on Cap 2).
- **EI Match:** 1.4x the employee's rate (~2.28%).
- **Base:** Same bases and caps as the employee.

#### {T['cost_header_13th']} & {T['cost_header_vacation']}
- **13th Salary:** Not mandatory by law.
- The months factor used for cost is `12.00`.
""")

# =========================== REGRAS DE CÁLCULO DO STI ==================
elif menu == T["menu_rules_sti"]:
    st.markdown(f"#### {T['sti_area_non_sales']}")
    header_level = T["sti_table_header_level"]
    header_pct = T["sti_table_header_pct"]
    
    df_ns = pd.DataFrame([
        {header_level: T[STI_I18N_KEYS["CEO"]], header_pct: "100%"},
        {header_level: T[STI_I18N_KEYS["Members of the GEB"]], header_pct: "50–80%"},
        {header_level: T[STI_I18N_KEYS["Executive Manager"]], header_pct: "45–70%"},
        {header_level: T[STI_I18N_KEYS["Senior Group Manager"]], header_pct: "40–60%"},
        {header_level: T[STI_I18N_KEYS["Group Manager"]], header_pct: "30–50%"},
        {header_level: T[STI_I18N_KEYS["Lead Expert / Program Manager"]], header_pct: "25–40%"},
        {header_level: T[STI_I18N_KEYS["Senior Manager"]], header_pct: "20–40%"},
        {header_level: T[STI_I18N_KEYS["Senior Expert / Senior Project Manager"]], header_pct: "15–35%"},
        {header_level: T[STI_I18N_KEYS["Manager / Selected Expert / Project Manager"]], header_pct: "10–30%"},
        {header_level: T[STI_I18N_KEYS["Others"]], header_pct: "≤ 10%"},
    ])
    st.table(df_ns)

    st.markdown(f"#### {T['sti_area_sales']}")
    df_s = pd.DataFrame([
        {header_level: T[STI_I18N_KEYS["Executive Manager / Senior Group Manager"]], header_pct: "45–70%"},
        {header_level: T[STI_I18N_KEYS["Group Manager / Lead Sales Manager"]], header_pct: "35–50%"},
        {header_level: T[STI_I18N_KEYS["Senior Manager / Senior Sales Manager"]], header_pct: "25–45%"},
        {header_level: T[STI_I18N_KEYS["Manager / Selected Sales Manager"]], header_pct: "20–35%"},
        {header_level: T[STI_I18N_KEYS["Others"]], header_pct: "≤ 15%"},
    ])
    st.table(df_s)

# ========================= CUSTO DO EMPREGADOR (REQ 1) ========================
else:
    c1, c2 = st.columns(2)
    salario = c1.number_input(
        f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    bonus_anual = c2.number_input(
            f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_cost_input")
    
    st.write("---")
    
    anual, mult, df_cost, months = calc_employer_cost(
        country, salario, bonus_anual, T, tables_ext=COUNTRY_TABLES)
    
    st.markdown(
        f"**{T['employer_cost_total']} (Salário + Bônus + Encargos):** {fmt_money(anual, symbol)}  \n"
        f"**Multiplicador de Custo (vs Salário Base 12 meses):** {mult:.3f} × (12 meses)  \n"
        f"**{T['months_factor']} (Base Salarial):** {months}"
    )
    if not df_cost.empty:
        st.dataframe(df_cost, use_container_width=True)
    else:
        st.info("Sem encargos configurados para este país (no JSON).")
