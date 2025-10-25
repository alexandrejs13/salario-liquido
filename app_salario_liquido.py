# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.47)
# Tema azul plano, multilíngue, responsivo e com STI corrigido
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import altair as alt
import requests
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
hr { border:0; height:2px; background:linear-gradient(to right, #0a3d62, #e2e6ea); margin:16px 0; border-radius:1px; }

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

/* Cards Mensais (Req 3: Reduzir espaço) */
.metric-card{ background:#fff; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); padding:16px; text-align:center; transition: all 0.3s ease; }
.metric-card:hover{ box-shadow:0 6px 16px rgba(0,0,0,0.15); transform: translateY(-2px); }


.metric-card h4{ margin:0; font-size:13px; color:#0a3d62;}
.metric-card h3{ margin:2px 0 0; color:#0a3d62; font-size:18px; } /* REQ 3: margin-top reduzido de 4px para 2px */

/* Tabela */
.table-wrap{ background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }

/* Título com bandeira */
.country-header{ display:flex; align-items:center; gap:10px; }
.country-flag{ font-size:28px; }
.country-title{ font-size:32px; font-weight:700; color:#0a3d62; }

/* Espaço extra abaixo do gráfico para legenda */
.vega-embed{ padding-bottom: 16px; }

/* CSS dos Cards Anuais (Req 2 e Ajuste de Altura) */
.annual-card-base { /* Base comum para label e value */
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    padding: 10px 15px;
    margin-bottom: 8px; /* Espaçamento entre linhas */
    border-left: 5px solid #0a3d62; /* Cor principal */

    /* SUGESTÃO LAYOUT: Altura igual e Centralização */
    min-height: 95px; /* REQ: Altura mínima p/ acomodar o card de Bônus com fonte maior */
    display: flex;
    flex-direction: column;
    justify-content: center; /* Alinha verticalmente o conteúdo */
    box-sizing: border-box;
}
.annual-card-label {
    /* Herda .annual-card-base */
    align-items: flex-start; /* Alinha texto à esquerda */
}
.annual-card-value {
    /* Herda .annual-card-base */
    align-items: flex-end; /* Alinha valor à direita */
}

.annual-card-label h4,
.annual-card-value h3 {
    margin: 0;
    font-size: 17px; /* REQ 2: Tamanho da fonte aumentado de 16px para 17px */
    color: #0a3d62;
}
.annual-card-label h4 {
    font-weight: 600;
}
.annual-card-value h3 {
    font-weight: 700;
}
.annual-card-label .sti-note { /* sti-note agora fica no label */
    display: block;
    font-size: 12px; /* REQ 2: Tamanho da fonte aumentado de 10px para 12px */
    line-height: 1.2;
    margin-top: 4px; /* Espaço leve abaixo do título */
}
</style>
""", unsafe_allow_html=True)

# ============================== I18N ================================
I18N = {
    "Português": {
        "app_title": "Simulador de Salário Líquido e Custo do Empregador",
        "menu_calc": "Cálculo de Salário",
        "menu_rules": "Regras de Contribuições",
        "menu_rules_sti": "Regras de Cálculo do STI",
        "menu_cost": "Custo do Empregador",
        "title_calc": "Cálculo de Salário – {pais}",
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
        # REQ 3 (Textos dos cards)
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
        "menu_calc": "Net Salary Calculation",
        "menu_rules": "Contribution Rules",
        "menu_rules_sti": "STI Calculation Rules",
        "menu_cost": "Employer Cost",
        "title_calc": "Net Salary Calculation – {pais}",
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
        "menu_calc": "Cálculo de Salario",
        "menu_rules": "Reglas de Contribuciones",
        "menu_rules_sti": "Reglas de Cálculo del STI",
        "menu_cost": "Costo del Empleador",
        "title_calc": "Cálculo de Salario – {pais}",
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
    "Colômbia": 13.00, "Estados Unidos": 12.00, "Canadá": 12.00
}

# ========================== FALLBACKS LOCAIS ============================
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
    "Chile": {"rates": {"AFP": 0.10, "Saúde": 0.07}},
    "Argentina": {"rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}},
    "Colômbia": {"rates": {"Saúde": 0.04, "Pensão": 0.04}},
    "Canadá": {"rates": {"CPP": 0.0595, "EI": 0.0163, "Income Tax": 0.15}}
}
EMPLOYER_COST_DEFAULT = {
    "Brasil": [
        {"nome": "INSS Patronal", "percentual": 20.0, "base": "Salário Bruto",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Previdência"},
        {"nome": "RAT", "percentual": 2.0, "base": "Salário Bruto",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Risco"},
        {"nome": "Sistema S", "percentual": 5.8, "base": "Salário Bruto",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Terceiros"},
        {"nome": "FGTS", "percentual": 8.0, "base": "Salário Bruto",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Crédito empregado"}
    ],
    "México": [
        {"nome": "IMSS Patronal", "percentual": 7.0, "base": "Salário",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Seguro social"},
        {"nome": "INFONAVIT Empregador", "percentual": 5.0, "base": "Salário",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Habitação"}
    ],
    "Chile": [
        {"nome": "Seguro Desemprego", "percentual": 2.4, "base": "Salário",
            "ferias": True, "decimo": False, "bonus": True, "obs": "Empregador (com teto)"}
    ],
    "Argentina": [
        {"nome": "Contribuições Patronais", "percentual": 18.0, "base": "Salário",
            "ferias": True, "decimo": True, "bonus": True, "obs": "Média setores (com teto)"}
    ],
    "Colômbia": [
        {"nome": "Saúde Empregador", "percentual": 8.5, "base": "Salário",
            "ferias": True, "decimo": True, "bonus": True, "obs": "—"},
        {"nome": "Pensão Empregador", "percentual": 12.0, "base": "Salário",
            "ferias": True, "decimo": True, "bonus": True, "obs": "—"}
    ],
    "Estados Unidos": [
        {"nome": "Social Security (ER)", "percentual": 6.2, "base": "Salário",
           "ferias": False, "decimo": False, "bonus": True, "obs": "Até teto ($168.6k/ano)"},
        {"nome": "Medicare (ER)", "percentual": 1.45, "base": "Salário",
           "ferias": False, "decimo": False, "bonus": True, "obs": "Sem teto"},
        {"nome": "SUTA (avg)", "percentual": 2.0, "base": "Salário",
           "ferias": False, "decimo": False, "bonus": True, "obs": "Média (sobre teto baixo)"}
    ],
    "Canadá": [
        {"nome": "CPP (ER)", "percentual": 5.95, "base": "Salário",
           "ferias": False, "decimo": False, "bonus": True, "obs": "Até teto (YMPE)"},
        {"nome": "EI (ER)", "percentual": 2.28, "base": "Salário",
           "ferias": False, "decimo": False, "bonus": True, "obs": "1.4x Empregado (até teto)"}
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
        "Others": (0.0, 0.10)  # ≤ 10%
    },
    "Sales": {
        "Executive Manager / Senior Group Manager": (0.45, 0.70),
        "Group Manager / Lead Sales Manager": (0.35, 0.50),
        "Senior Manager / Senior Sales Manager": (0.25, 0.45),
        "Manager / Selected Sales Manager": (0.20, 0.35),
        "Others": (0.0, 0.15)  # ≤ 15%
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

# Mapeamento de chaves internas do STI para chaves I18N (Req 2)
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


# ============================== HELPERS ===============================


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

# -------- INSS/IRRF (Brasil) ----------


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
    # REQ 4: Correção para Teto da Social Security (FICA)
    # Usando dados de 2024 como fallback para 2025
    FICA_WAGE_BASE_ANNUAL = 168600.0 
    FICA_WAGE_BASE_MONTHLY = FICA_WAGE_BASE_ANNUAL / 12.0
    
    lines = [("Base Pay", salary, 0.0)]
    total_earn = salary
    
    # Aplica o teto mensalizado
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


def calc_country_net(country: str, salary: float, state_code=None, state_rate=None,
                     dependentes=0, tables_ext=None, br_inss_tbl=None, br_irrf_tbl=None):
    if country == "Brasil":
        lines, te, td, net, fgts = br_net(
            salary, dependentes, br_inss_tbl, br_irrf_tbl)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": fgts}
    elif country == "Estados Unidos":
        lines, te, td, net = us_net(salary, state_code, state_rate)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    else:
        # Simplificação: Outros países usam taxas fixas
        # Nota: O ideal seria ter funções 'calc_cpp_ei_progressivo' (Canadá) etc.
        rates = (tables_ext or {}).get("TABLES", {}).get(
            country, {}).get("rates", {})
        if not rates:
            rates = TABLES_DEFAULT.get(country, {}).get("rates", {})
        lines, te, td, net = generic_net(salary, rates)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}


def calc_employer_cost(country: str, salary: float, T: Dict[str, str], tables_ext=None):
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(
        country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    enc_list = (tables_ext or {}).get("EMPLOYER_COST", {}).get(
        country, EMPLOYER_COST_DEFAULT.get(country, []))
    benefits = COUNTRY_BENEFITS.get(
        country, {"ferias": False, "decimo": False})
    df = pd.DataFrame(enc_list)

    if not df.empty:
        df[T["cost_header_charge"]] = df["nome"]
        df[T["cost_header_percent"]] = df["percentual"].apply(lambda p: f"{p:.2f}%")
        df[T["cost_header_base"]] = df["base"]
        df[T["cost_header_obs"]] = df["obs"]
        df[T["cost_header_bonus"]] = ["✅" if b else "❌" for b in df["bonus"]]
        cols = [T["cost_header_charge"], T["cost_header_percent"],
                T["cost_header_base"], T["cost_header_bonus"], T["cost_header_obs"]]
        
        # REQ 5: Lógica para ocultar colunas (já implementada)
        if benefits.get("ferias", False):
            df[T["cost_header_vacation"]] = ["✅" if b else "❌" for b in df["ferias"]]
            cols.insert(3, T["cost_header_vacation"])
        if benefits.get("decimo", False):
            df[T["cost_header_13th"]] = ["✅" if b else "❌" for b in df["decimo"]]
            insert_pos = 4 if benefits.get("ferias", False) else 3
            cols.insert(insert_pos, T["cost_header_13th"])
        df = df[cols]

    # Lógica simplificada: Soma percentuais e aplica sobre a base anual
    # Nota: Esta lógica não aplica tetos (ex: FICA, CPP) no cálculo do CUSTO,
    # embora o salário LÍQUIDO (us_net) tenha sido corrigido.
    perc_total = sum(e.get("percentual", 0.0) for e in enc_list)
    anual = salary * months * (1 + perc_total/100.0)
    mult = (anual / (salary * 12.0)) if salary > 0 else 0.0
    return anual, mult, df, months

# -------- Helpers de Tradução (Req 2) ----------


def get_sti_area_map(T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    """Retorna a lista de exibição e o mapa de display->chave para Áreas STI."""
    display_list = [T["sti_area_non_sales"], T["sti_area_sales"]]
    keys = ["Non Sales", "Sales"]
    key_map = dict(zip(display_list, keys))
    return display_list, key_map


def get_sti_level_map(area: str, T: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    """Retorna a lista de exibição e o mapa de display->chave para Níveis STI."""
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


# ============================== SIDEBAR ===============================
with st.sidebar:
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

US_STATE_RATES, COUNTRY_TABLES, BR_INSS_TBL, BR_IRRF_TBL = load_tables()

# === dados do país ===
symbol = COUNTRIES[country]["symbol"]
flag = COUNTRIES[country]["flag"]
valid_from = COUNTRIES[country]["valid_from"]

# ======================= TÍTULO DINÂMICO ==============================
if menu == T["menu_calc"]:
    title = T["title_calc"].format(pais=country)
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
st.write("---")

# ========================= CÁLCULO DE SALÁRIO ==========================
if menu == T["menu_calc"]:

    # Helpers de tradução do STI (Req 2)
    area_options_display, area_display_map = get_sti_area_map(T)

    if country == "Brasil":
        # Título (Req 1 e 2)
        st.subheader(T["calc_params_title"])
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1.6, 1.6, 2.4])
        salario = c1.number_input(
            f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        dependentes = c2.number_input(
            f"{T['dependents']}", min_value=0, value=0, step=1, key="dep_input")
        bonus_anual = c3.number_input(
            f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        # Selectbox traduzido (Req 2)
        area_display = c4.selectbox(
            T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = c5.selectbox(T["level"], level_options_display, index=len(
            level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]

        # Divisor e Título (Req 1 e 2)
        st.write("---")
        st.subheader(T["monthly_comp_title"])
        state_code, state_rate = None, None

    elif country == "Estados Unidos":
        st.subheader(T["calc_params_title"])  # Adicionado para consistência
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
        # Selectbox traduzido (Req 2)
        area_display = r1.selectbox(
            T["area"], area_options_display, index=0, key="sti_area")
        area = area_display_map[area_display]
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_display = r2.selectbox(T["level"], level_options_display, index=len(
            level_options_display)-1, key="sti_level")
        level = level_display_map[level_display]
        dependentes = 0
        st.write("---")
        st.subheader(T["monthly_comp_title"])  # Adicionado para consistência

    else:
        st.subheader(T["calc_params_title"])  # Adicionado para consistência
        c1, c2 = st.columns([2, 1.6])
        salario = c1.number_input(
            f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        bonus_anual = c2.number_input(
            f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        # Selectbox traduzido (Req 2)
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
        st.subheader(T["monthly_comp_title"])  # Adicionado para consistência

    # ---- Cálculo do país selecionado
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

    # ---- Cards totais (linha única)
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
    st.write("---")  # Divisor entre blocos

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
    # Status traduzido (Req 2)
    status_txt = T["sti_in_range"] if dentro else T["sti_out_range"]
    # Cor de fundo (Req 4)
    bg_cor = "#e6f7ff" if dentro else "#ffe6e6"
    
    # Linha de status do STI (com tradução)
    sti_line = (
        f"STI ratio do bônus: <strong>{pct_txt}</strong> — "
        f"<strong>{status_txt}</strong> ({faixa_txt}) — "
        f"<em>{area_display} • {level_display}</em>"
    )

    # ==== Layout (Req 4: Títulos à esquerda, valores à direita) ====
    c1, c2 = st.columns(2)

    # --- Coluna 1: Labels ---

    # Card Salário Anual (Label)
    c1.markdown(
        f"""
        <div class='annual-card-base annual-card-label' style='border-left-color: #28a745; background: #e6ffe6;'>
            <h4>{T['annual_salary']}</h4>
            <span class='sti-note'>({T['months_factor']}: {months})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Card Bônus Anual (Label)
    c1.markdown(
        f"""
        <div class='annual-card-base annual-card-label' style='border-left-color: {cor}; background: {bg_cor};'>
            <h4>{T['annual_bonus']}</h4>
            <span class='sti-note' style='color:{cor}'>{sti_line}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Card Remuneração Total Anual (Label) (REQ 1: Cor alterada)
    c1.markdown(
        f"""
        <div class='annual-card-base annual-card-label' style='border-left-color: #0a3d62; background: #e6f0f8;'>
            <h4>{T['annual_total']}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Coluna 2: Valores ---

    # Card Salário Anual (Valor)
    c2.markdown(
        f"""
        <div class='annual-card-base annual-card-value' style='border-left-color: #28a745; background: #e6ffe6;'>
            <h3>{fmt_money(salario_anual, symbol)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Card Bônus Anual (Valor)
    c2.markdown(
        f"""
        <div class='annual-card-base annual-card-value' style='border-left-color: {cor}; background: {bg_cor};'>
            <h3>{fmt_money(bonus_anual, symbol)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Card Remuneração Total Anual (Valor) (REQ 1: Cor alterada)
    c2.markdown(
        f"""
        <div class='annual-card-base annual-card-value' style='border-left-color: #0a3d62; background: #e6f0f8;'>
            <h3>{fmt_money(total_anual, symbol)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Gráfico de Pizza (abaixo dos cards) ---
    st.write("---")
    st.markdown(f"### {T['pie_title']}")

    chart_df = pd.DataFrame(
        {"Componente": [T["annual_salary"].split(" (")[0], T["annual_bonus"]], # Remove texto extra p/ legenda
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
                title=None, labelLimit=250, labelFontSize=11, symbolSize=90
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
        .properties(title=T["pie_title"])
        .configure_legend(orient="bottom", title=None, labelLimit=250)
        .configure_view(strokeWidth=0)
        # Garante que a legenda não se sobreponha
        .resolve_scale(color='independent')
    )

    st.altair_chart(chart, use_container_width=True)


# =========================== REGRAS DE CONTRIBUIÇÕES (REQ 4 e 5) ===================
elif menu == T["menu_rules"]:
    st.subheader(T["rules_expanded"])

    # REQ 4: Lógica de filtro por país
    if country == "Brasil":
        if idioma == "Português":
            st.markdown(f"""
### 🇧🇷 {T["rules_emp"]}
- **INSS (Previdência Social):** Alíquota progressiva (7.5% a 14%) aplicada por faixas de salário.
  - **Base:** Salário Bruto.
  - **Teto da Base (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_base', 8157.41), 'R$')}.
  - **Teto da Contribuição (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_contribuicao', 1146.68), 'R$')}. O cálculo é `(Faixa1 * 7.5%) + (Faixa2 * 9%) + ...` até o teto.
- **IRRF (Imposto de Renda):** Alíquota progressiva (0% a 27.5%) com parcelas a deduzir.
  - **Base:** Salário Bruto - INSS - ( {fmt_money(BR_IRRF_DEFAULT.get('deducao_dependente', 189.59), 'R$')} × Nº de Dependentes).

### 🇧🇷 {T["rules_er"]}
- **INSS Patronal (CPP):** 20% (Regra Geral). **Base:** Total da folha (Salário Bruto).
- **RAT/FAP (Risco Acidente):** 1% a 3% (usamos 2% no simulador). **Base:** Total da folha.
- **Sistema S (Terceiros):** ~5.8%. **Base:** Total da folha.
- **FGTS (Fundo de Garantia):** 8%. **Base:** Total da folha. (Não é um imposto, mas um custo/depósito).

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
O custo anual total no Brasil inclui o 13º Salário (1 salário extra) e Férias (1 salário + 1/3 de bônus constitucional).
- O fator de meses `13.33` (12 + 1 + 0.33) reflete essa base de custo anual.
- Todos os encargos do empregador (INSS, RAT, Sistema S, FGTS) incidem sobre o 13º e as Férias, por isso o simulador aplica os percentuais sobre a base total (`Salário × 13.33`).
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇧🇷 {T["rules_emp"]}
- **INSS (Social Security):** Progressive rate (7.5% to 14%) applied in brackets.
  - **Base:** Gross Salary.
  - **Base Cap (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_base', 8157.41), 'R$')}.
  - **Contribution Cap (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_contribuicao', 1146.68), 'R$')}. The calculation is `(Bracket1 * 7.5%) + (Bracket2 * 9%) + ...` up to the cap.
- **IRRF (Income Tax):** Progressive rate (0% to 27.5%) with fixed deductions per bracket.
  - **Base:** Gross Salary - INSS - ( {fmt_money(BR_IRRF_DEFAULT.get('deducao_dependente', 189.59), 'R$')} × No. of Dependents).

### 🇧🇷 {T["rules_er"]}
- **INSS Patronal (CPP):** 20% (General rule). **Base:** Total payroll (Gross Salary).
- **RAT/FAP (Work Accident):** 1% to 3% (we use 2% in the simulator). **Base:** Total payroll.
- **"Sistema S" (Third-parties):** ~5.8%. **Base:** Total payroll.
- **FGTS (Severance Fund):** 8%. **Base:** Total payroll. (Not a tax, but a cost/deposit).

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
The total annual cost in Brazil includes the 13th Salary (1 extra salary) and Vacations (1 salary + 1/3 constitutional bonus).
- The `13.33` months factor (12 + 1 + 0.33) reflects this annual cost base.
- All employer charges (INSS, RAT, System S, FGTS) apply to the 13th salary and vacation pay, which is why the simulator applies the percentages to the total base (`Salary × 13.33`).
""")
        else: # Español
            st.markdown(f"""
### 🇧🇷 {T["rules_emp"]}
- **INSS (Seguridad Social):** Tasa progresiva (7.5% a 14%) aplicada por tramos de salario.
  - **Base:** Salario Bruto.
  - **Tope Base (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_base', 8157.41), 'R$')}.
  - **Tope de Contribución (2025):** {fmt_money(BR_INSS_DEFAULT.get('teto_contribuicao', 1146.68), 'R$')}. El cálculo es `(Tramo1 * 7.5%) + (Tramo2 * 9%) + ...` hasta el tope.
- **IRRF (Impuesto de Renta):** Tasa progresiva (0% a 27.5%) con deducciones fijas.
  - **Base:** Salario Bruto - INSS - ( {fmt_money(BR_IRRF_DEFAULT.get('deducao_dependente', 189.59), 'R$')} × Nº de Dependientes).

### 🇧🇷 {T["rules_er"]}
- **INSS Patronal (CPP):** 20% (Regla General). **Base:** Nómina total (Salario Bruto).
- **RAT/FAP (Riesgo Accidente):** 1% a 3% (usamos 2% en el simulador). **Base:** Nómina total.
- **"Sistema S" (Terceros):** ~5.8%. **Base:** Nómina total.
- **FGTS (Fondo de Garantía):** 8%. **Base:** Nómina total. (No es un impuesto, sino un costo/depósito).

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
El costo anual total en Brasil incluye el 13º Salario (1 salario extra) y Vacaciones (1 salario + 1/3 de bono constitucional).
- El factor de meses `13.33` (12 + 1 + 0.33) refleja esta base de costo anual.
- Todas las cargas del empleador (INSS, RAT, Sistema S, FGTS) se aplican al 13º y a las vacaciones, por lo que el simulador aplica los porcentajes sobre la base total (`Salario × 13.33`).
""")

    elif country == "Estados Unidos":
        if idioma == "Português":
            st.markdown(f"""
### 🇺🇸 {T["rules_emp"]}
- **FICA (Social Security):** 6.2%.
  - **Base:** Salário Bruto, aplicado **somente** até o teto anual de $168,600 (valor 2024). Salários acima disso não pagam esta contribuição.
- **Medicare:** 1.45%.
  - **Base:** Salário Bruto total (sem teto). (Uma taxa adicional de 0.9% pode ser aplicada para rendas muito altas, não incluída no simulador).
- **State Tax (Imposto Estadual):** Varia (0% a ~8%+). **Base:** Salário Bruto (varia por estado).

### 🇺🇸 {T["rules_er"]}
- **FICA (Social Security) Match:** 6.2%. **Base:** Mesma base e teto do empregado ($168,600/ano).
- **Medicare Match:** 1.45%. **Base:** Salário Bruto total (sem teto).
- **FUTA/SUTA (Desemprego):** Impostos de desemprego (Federal/Estadual).
  - **Base:** Varia, mas geralmente é uma % (ex: 2-3%) aplicada sobre um teto salarial baixo (ex: os primeiros $7,000 - $10,000 do salário). O simulador usa uma média de 2% sobre o salário total para simplificar.

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
- Não há 13º salário obrigatório por lei.
- Férias (PTO - Paid Time Off) são um benefício negociado, não uma provisão contábil com encargos adicionais como no Brasil.
- O fator de meses usado para custo é `12.00`.
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇺🇸 {T["rules_emp"]}
- **FICA (Social Security):** 6.2%.
  - **Base:** Gross Salary, applied **only** up to the annual cap of $168,600 (2024 value). Earnings above this cap are not subject to this tax.
- **Medicare:** 1.45%.
  - **Base:** Total Gross Salary (no cap). (An additional 0.9% "Additional Medicare Tax" may apply for very high earners, not included in the simulator).
- **State Tax:** Varies (0% to ~8%+). **Base:** Gross Salary (varies by state).

### 🇺🇸 {T["rules_er"]}
- **FICA (Social Security) Match:** 6.2%. **Base:** Same base and cap as the employee ($168,600/year).
- **Medicare Match:** 1.45%. **Base:** Total Gross Salary (no cap).
- **FUTA/SUTA (Unemployment):** Federal/State unemployment taxes.
  - **Base:** Varies, but it's typically a % (e.g., 2-3%) applied on a low wage base (e.g., the first $7,000 - $10,000 of salary). The simulator uses an average of 2% on the total salary for simplicity.

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
- There is no mandatory 13th salary by law.
- Vacation (PTO - Paid Time Off) is a negotiated benefit, not an accounting provision with additional payroll taxes as in other countries.
- The months factor used for cost is `12.00`.
""")
        else: # Español
            st.markdown(f"""
### 🇺🇸 {T["rules_emp"]}
- **FICA (Social Security):** 6.2%.
  - **Base:** Salario Bruto, aplicado **solo** hasta el tope anual de $168,600 (valor 2024). Los salarios por encima de esto no pagan esta contribución.
- **Medicare:** 1.45%.
  - **Base:** Salario Bruto total (sin tope). (Una tasa adicional de 0.9% puede aplicarse para ingresos muy altos, no incluida en el simulador).
- **State Tax (Impuesto Estatal):** Varía (0% a ~8%+). **Base:** Salario Bruto (varía por estado).

### 🇺🇸 {T["rules_er"]}
- **FICA (Social Security) Match:** 6.2%. **Base:** Misma base y tope que el empleado ($168,600/año).
- **Medicare Match:** 1.45%. **Base:** Salario Bruto total (sin tope).
- **FUTA/SUTA (Desempleo):** Impuestos de desempleo (Federal/Estatal).
  - **Base:** Varía, pero generalmente es un % (ej: 2-3%) aplicado sobre un tope salarial bajo (ej: los primeros $7,000 - $10,000 de salario). El simulador usa un promedio de 2% sobre el salario total para simplificar.

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
- No hay 13º salario obligatorio por ley.
- Las vacaciones (PTO) son un beneficio negociado, no una provisión contable con cargas adicionales como en otros países.
- El factor de meses usado para el costo es `12.00`.
""")

    elif country == "México":
        if idioma == "Português":
            st.markdown(f"""
### 🇲🇽 {T["rules_emp"]}
- **ISR (Imposto de Renda):** Alíquota progressiva complexa.
- **IMSS (Seguro Social):** Taxa percentual sobre o salário (com teto).
- **INFONAVIT (Habitação):** Não é uma dedução, mas o empregador pode reter pagamentos de crédito.
- *Nota: O simulador usa taxas fixas (ex: ISR 15%, IMSS 5%) como uma **simplificação**. O cálculo real é baseado em tabelas progressivas.*

### 🇲🇽 {T["rules_er"]}
- **IMSS Patronal:** Cota do empregador para o seguro social (complexa, ~7% no simulador).
- **INFONAVIT:** 5%. **Base:** Salário Bruto.
- **SAR (Sistema de Aposentadoria):** 2%. **Base:** Salário Bruto.

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
- **Aguinaldo (13º):** Obrigatório, mínimo de 15 dias de salário, pago anualmente.
- O fator de meses `12.50` (12 + 15/30 dias) reflete essa base de custo anual.
- **Prima Vacacional:** 25% pagos sobre o salário dos dias de férias.
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇲🇽 {T["rules_emp"]}
- **ISR (Income Tax):** Complex progressive rate.
- **IMSS (Social Security):** Percentage rate on salary (with cap).
- **INFONAVIT (Housing):** Not a deduction, but employer may withhold credit payments.
- *Note: The simulator uses flat rates (e.g., ISR 15%, IMSS 5%) as a **simplification**. The actual calculation is based on progressive tables.*

### 🇲🇽 {T["rules_er"]}
- **IMSS (Employer):** Employer's share for social security (complex, ~7% in simulator).
- **INFONAVIT:** 5%. **Base:** Gross Salary.
- **SAR (Retirement System):** 2%. **Base:** Gross Salary.

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
- **Aguinaldo (13th):** Mandatory, minimum 15 days of salary, paid annually.
- The `12.50` months factor (12 + 15/30 days) reflects this annual cost base.
- **Prima Vacacional (Vacation Bonus):** 25% paid on the salary for vacation days.
""")
        else: # Español
            st.markdown(f"""
### 🇲🇽 {T["rules_emp"]}
- **ISR (Impuesto Sobre la Renta):** Tasa progresiva compleja.
- **IMSS (Seguro Social):** Tasa porcentual sobre el salario (con tope).
- **INFONAVIT (Vivienda):** No es una deducción, pero el empleador puede retener pagos de crédito.
- *Nota: El simulador usa tasas fijas (ej: ISR 15%, IMSS 5%) como una **simplificación**. El cálculo real se basa en tablas progresivas.*

### 🇲🇽 {T["rules_er"]}
- **IMSS Patronal:** Cuota del empleador para el seguro social (compleja, ~7% en simulador).
- **INFONAVIT:** 5%. **Base:** Salario Bruto.
- **SAR (Sistema de Ahorro para el Retiro):** 2%. **Base:** Salario Bruto.

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
- **Aguinaldo (13º):** Obligatorio, mínimo 15 días de salario, pagado anualmente.
- El factor de meses `12.50` (12 + 15/30 días) refleja esta base de costo anual.
- **Prima Vacacional:** 25% pagado sobre el salario de los días de vacaciones.
""")

    elif country == "Chile":
        if idioma == "Português":
            st.markdown(f"""
### 🇨🇱 {T["rules_emp"]}
- **AFP (Pensão):** 10% (obrigatório) + comissão da administradora (ex: ~1.15%).
  - **Base:** Salário Bruto, com teto de ~84.3 UF.
- **Saúde (FONASA ou ISAPRE):** 7% (obrigatório).
  - **Base:** Salário Bruto, com o mesmo teto de ~84.3 UF.
- *O simulador usa 10% e 7% para simplificar (não inclui a comissão da AFP).*

### 🇨🇱 {T["rules_er"]}
- **Seguro de Cesantía (Seguro Desemprego):** 2.4%.
  - **Base:** Salário Bruto, com teto de ~126.6 UF.
- **SIS (Seguro Invalidez):** ~1.53% (varia por licitação).

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
- **Aguinaldo (13º):** Não é obrigatório por lei (comum no setor público, mas opcional/negociado no privado).
- O fator de meses usado para custo é `12.00`.
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇨🇱 {T["rules_emp"]}
- **AFP (Pension):** 10% (mandatory) + administration fee (e.g., ~1.15%).
  - **Base:** Gross Salary, with a cap of ~84.3 UF.
- **Health (FONASA or ISAPRE):** 7% (mandatory).
  - **Base:** Gross Salary, with the same cap of ~84.3 UF.
- *The simulator uses 10% and 7% for simplicity (does not include the AFP fee).*

### 🇨🇱 {T["rules_er"]}
- **Seguro de Cesantía (Unemployment Insurance):** 2.4%.
  - **Base:** Gross Salary, with a cap of ~126.6 UF.
- **SIS (Disability Insurance):** ~1.53% (varies by auction).

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
- **Aguinaldo (13th):** Not mandatory by law (common in public sector, but optional/negotiated in private).
- The months factor used for cost is `12.00`.
""")
        else: # Español
            st.markdown(f"""
### 🇨🇱 {T["rules_emp"]}
- **AFP (Pensión):** 10% (obligatorio) + comisión de la administradora (ej: ~1.15%).
  - **Base:** Salario Bruto, con tope de ~84.3 UF.
- **Salud (FONASA o ISAPRE):** 7% (obligatorio).
  - **Base:** Salario Bruto, con el mismo tope de ~84.3 UF.
- *El simulador usa 10% y 7% para simplificar (no incluye la comisión de la AFP).*

### 🇨🇱 {T["rules_er"]}
- **Seguro de Cesantía:** 2.4%.
  - **Base:** Salario Bruto, con tope de ~126.6 UF.
- **SIS (Seguro de Invalidez):** ~1.53% (varía por licitación).

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
- **Aguinaldo (13º):** No es obligatorio por ley (común en sector público, pero opcional/negociado en privado).
- El factor de meses usado para el costo es `12.00`.
""")

    elif country == "Argentina":
        if idioma == "Português":
            st.markdown(f"""
### 🇦🇷 {T["rules_emp"]}
- **Jubilación (SIPA):** 11%.
- **Obra Social (Saúde):** 3%.
- **PAMI (INSSJP):** 3%.
- **Base:** Total das contribuições (17%) aplicado sobre o Salário Bruto, com teto salarial.

### 🇦🇷 {T["rules_er"]}
- **Contribuições Patronais:** Um total de ~18% (varia por setor/tamanho da empresa).
- **Base:** Salário Bruto, também com teto.

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
- **SAC (Sueldo Anual Complementario):** É o 13º salário, pago em duas parcelas (meio do ano e fim do ano).
- O fator de meses `13.00` (12 + 1) reflete essa base de custo anual.
- Os encargos patronais incidem sobre o SAC.
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇦🇷 {T["rules_emp"]}
- **Jubilación (SIPA - Pension):** 11%.
- **Obra Social (Health Care):** 3%.
- **PAMI (INSSJP):** 3%.
- **Base:** Total contributions (17%) applied to Gross Salary, with a salary cap.

### 🇦🇷 {T["rules_er"]}
- **Employer Contributions:** A total of ~18% (varies by industry/company size).
- **Base:** Gross Salary, also with a salary cap.

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
- **SAC (Sueldo Anual Complementario):** This is the 13th salary, paid in two installments (mid-year and end-of-year).
- The `13.00` months factor (12 + 1) reflects this annual cost base.
- Employer contributions apply to the SAC.
""")
        else: # Español
            st.markdown(f"""
### 🇦🇷 {T["rules_emp"]}
- **Jubilación (SIPA):** 11%.
- **Obra Social:** 3%.
- **PAMI (INSSJP):** 3%.
- **Base:** Total de contribuciones (17%) aplicado sobre el Salario Bruto, con tope salarial.

### 🇦🇷 {T["rules_er"]}
- **Contribuciones Patronales:** Un total de ~18% (varía por sector/tamaño de empresa).
- **Base:** Salario Bruto, también con tope salarial.

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
- **SAC (Sueldo Anual Complementario):** Es el 13º salario, pagado en dos cuotas (mitad de año y fin de año).
- El factor de meses `13.00` (12 + 1) refleja esta base de costo anual.
- Las contribuciones patronales se aplican sobre el SAC.
""")

    elif country == "Colômbia":
        if idioma == "Português":
            st.markdown(f"""
### 🇨🇴 {T["rules_emp"]}
- **Salud (EPS):** 4%. **Base:** Salário Bruto.
- **Pensión:** 4%. **Base:** Salário Bruto.

### 🇨🇴 {T["rules_er"]}
- **Salud (EPS):** 8.5%. **Base:** Salário Bruto.
- **Pensión:** 12%. **Base:** Salário Bruto.
- **Outros Custos:** O empregador também paga "Parafiscales" (ICBF, SENA, Caja de Compensación ~9%) e "Prestaciones Sociales" (Cesantías, Intereses, Dotación).
- *Nota: O simulador simplifica, incluindo apenas Saúde e Pensão nos encargos.*

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
- **Prima de Servicios:** É o 13º salário, pago em duas parcelas (Junho/Dezembro).
- O fator de meses `13.00` (12 + 1) reflete essa base de custo.
- **Cesantías:** É um custo adicional separado (1 salário por ano) depositado em um fundo para o empregado.
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇨🇴 {T["rules_emp"]}
- **Salud (EPS - Health):** 4%. **Base:** Gross Salary.
- **Pensión (Pension):** 4%. **Base:** Gross Salary.

### 🇨🇴 {T["rules_er"]}
- **Salud (EPS):** 8.5%. **Base:** Gross Salary.
- **Pensión:** 12%. **Base:** Gross Salary.
- **Other Costs:** The employer also pays "Parafiscales" (ICBF, SENA, Compensation Fund ~9%) and "Prestaciones Sociales" (Severance, Interest, etc.).
- *Note: The simulator simplifies this, including only Health and Pension in the charges.*

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
- **Prima de Servicios:** This is the 13th salary, paid in two installments (June/December).
- The `13.00` months factor (12 + 1) reflects this cost base.
- **Cesantías (Severance):** This is a separate additional cost (1 salary per year) deposited into a fund for the employee.
""")
        else: # Español
            st.markdown(f"""
### 🇨🇴 {T["rules_emp"]}
- **Salud (EPS):** 4%. **Base:** Salario Bruto.
- **Pensión:** 4%. **Base:** Salario Bruto.

### 🇨🇴 {T["rules_er"]}
- **Salud (EPS):** 8.5%. **Base:** Salario Bruto.
- **Pensión:** 12%. **Base:** Salario Bruto.
- **Otros Costos:** El empleador también paga "Parafiscales" (ICBF, SENA, Caja de Compensación ~9%) y "Prestaciones Sociales" (Cesantías, Intereses, Dotación).
- *Nota: El simulador simplifica esto, incluyendo solo Salud y Pensión en los cargos.*

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
- **Prima de Servicios:** Es el 13º salario, pagado en dos cuotas (Junio/Diciembre).
- El factor de meses `13.00` (12 + 1) refleja esta base de costo.
- **Cesantías:** Es un costo adicional separado (1 salario por año) depositado en un fondo para el empleado.
""")

    elif country == "Canadá":
        if idioma == "Português":
            st.markdown(f"""
### 🇨🇦 {T["rules_emp"]}
- **CPP (Canada Pension Plan):** 5.95%.
  - **Base:** Salário Bruto, aplicado *após* uma isenção básica ($3,500/ano) e *até* um teto anual (YMPE - $68,500 em 2024).
- **EI (Employment Insurance):** 1.63%.
  - **Base:** Salário Bruto, até um teto de ganhos ($63,200 em 2024).
- **Income Tax (Imposto de Renda):** Progressivo (Federal + Provincial).
- *Nota: O simulador usa taxas fixas (5.95%, 1.63%, 15%) como uma **simplificação extrema**. O cálculo real é muito mais complexo.*

### 🇨🇦 {T["rules_er"]}
- **CPP Match:** 5.95%. **Base:** Mesma base e teto do empregado.
- **EI Match:** 1.4x a cota do empregado (~2.28%). **Base:** Mesma base e teto do empregado.

#### {T['cost_header_13th']} e {T['cost_header_vacation']} (Req 5)
- **13º Salário:** Não é obrigatório por lei.
- **Férias:** Obrigatório por lei (ex: 2 semanas), e o pagamento de férias ("vacation pay") é tipicamente 4% do salário.
- O fator de meses usado para custo é `12.00` (o "vacation pay" é geralmente pago no lugar do salário durante as férias, ou como um adicional).
""")
        elif idioma == "English":
            st.markdown(f"""
### 🇨🇦 {T["rules_emp"]}
- **CPP (Canada Pension Plan):** 5.95%.
  - **Base:** Gross Salary, applied *after* a basic exemption ($3,500/year) and *up to* an annual cap (YMPE - $68,500 in 2024).
- **EI (Employment Insurance):** 1.63%.
  - **Base:** Gross Salary, up to a maximum insurable earnings cap ($63,200 in 2024).
- **Income Tax:** Progressive (Federal + Provincial).
- *Note: The simulator uses flat rates (5.95%, 1.63%, 15%) as an **extreme simplification**. The real calculation is much more complex.*

### 🇨🇦 {T["rules_er"]}
- **CPP Match:** 5.95%. **Base:** Same base and cap as the employee.
- **EI Match:** 1.4x the employee's rate (~2.28%). **Base:** Same base and cap as the employee.

#### {T['cost_header_13th']} & {T['cost_header_vacation']} (Req 5)
- **13th Salary:** Not mandatory by law.
- **Vacation:** Mandatory by law (e.g., 2 weeks), and "vacation pay" is typically 4% of earnings.
- The months factor used for cost is `12.00` (vacation pay is often paid in lieu of salary during time off, or as a top-up).
""")
        else: # Español
            st.markdown(f"""
### 🇨🇦 {T["rules_emp"]}
- **CPP (Canada Pension Plan):** 5.95%.
  - **Base:** Salario Bruto, aplicado *después* de una exención básica ($3,500/año) y *hasta* un tope anual (YMPE - $68,500 en 2024).
- **EI (Employment Insurance):** 1.63%.
  - **Base:** Salario Bruto, hasta un tope de ganancias asegurables ($63,200 en 2024).
- **Income Tax (Impuesto de Renta):** Progresivo (Federal + Provincial).
- *Nota: El simulador usa tasas fijas (5.95%, 1.63%, 15%) como una **simplificación extrema**. El cálculo real es mucho más complejo.*

### 🇨🇦 {T["rules_er"]}
- **CPP Match:** 5.95%. **Base:** Misma base y tope que el empleado.
- **EI Match:** 1.4x la tasa del empleado (~2.28%). **Base:** Misma base y tope que el empleado.

#### {T['cost_header_13th']} y {T['cost_header_vacation']} (Req 5)
- **13º Salario:** No es obligatorio por ley.
- **Vacaciones:** Obligatorio por ley (ej: 2 semanas), y el pago de vacaciones ("vacation pay") es típicamente el 4% del salario.
- El factor de meses usado para el costo es `12.00` (el pago de vacaciones se paga en lugar del salario durante el descanso, o como un adicional).
""")

# =========================== REGRAS DE CÁLCULO DO STI ==================
elif menu == T["menu_rules_sti"]:
    # Títulos e tabelas traduzidos (Req 2)
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

# ========================= CUSTO DO EMPREGADOR ========================
else:
    salario = st.number_input(
        f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    # Passa o T para a função (Req 2)
    anual, mult, df_cost, months = calc_employer_cost(
        country, salario, T, tables_ext=COUNTRY_TABLES)
    st.markdown(
        f"**{T['employer_cost_total']}:** {fmt_money(anual, symbol)}  \n**Equivalente:** {mult:.3f} × (12 meses)  \n**{T['months_factor']}:** {months}")
    if not df_cost.empty:
        st.dataframe(df_cost, use_container_width=True)
    else:
        st.info("Sem encargos configurados para este país (no JSON).")
