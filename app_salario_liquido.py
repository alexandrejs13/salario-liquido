# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.50.45 - FIX FINAL ESTILO EMOJI/ALINHAMENTO)
# Correção: Layout reestruturado para simetria de colunas nos inputs.
# Modificação: Cards com estilo refinado (removida borda colorida e ajuste de cor).
# Ajuste: Rótulos Bônus e Remuneração Total ajustados conforme solicitado.
# NOVO AJUSTE: Tabela de Remuneração Mensal estilizada (HTML) e índice removido.
# ÚLTIMO AJUSTE: Cards Mensais/Anuais centralizados e espaçamento entre Tabela e Cards corrigido.
# NOTA IMPORTANTE: Problemas de tela branca no iOS (iPhone) são geralmente causados por bugs de compatibilidade do JavaScript/WebSocket em versões Streamlit > 1.32.0. Recomenda-se fixar a versão para 1.32.0 no requirements.txt.
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

# ======================== HELPERS INICIAIS (Formatação - NOVO TOPO ABSOLUTO) =========================
# Variável global temporária para o código do país, será definida na sidebar
_COUNTRY_CODE_FOR_FMT = "Brasil" 
INPUT_FORMAT = "%.2f" # Variável de formato para number_input (escopo global)

def fmt_money(v: float, sym: str) -> str:
    """Formata um float como moeda no padrão brasileiro (1.000,00) a partir do padrão en_US."""
    # Formato padrão americano com separador de milhar (, ) e decimal ( . ), depois inverte para o BR/EUR
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    """Retorna a string formatada ou vazia se o valor for zero."""
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def fmt_percent(v: float) -> str:
    """Formata um float como porcentagem."""
    if v is None: return ""
    return f"{v:.2f}%"

def fmt_cap(cap_value: Any, sym: str = None) -> str:
    """Formata tetos, lidando com UF (Chile) e moedas."""
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

# --- Fallbacks Mínimos (COM TEXTOS ANUAIS AJUSTADOS) ---
I18N_FALLBACK = { 
    "Português": { 
        "sidebar_title": "Simulador de Remuneração<br>(Região das Americas)", 
        "app_title": "Simulador de Salário Líquido e Custo do Empregador", 
        "menu_calc": "Simulador de Remuneração", 
        "menu_rules": "Regras de Contribuições", 
        "menu_rules_sti": "Regras de Cálculo do STI", 
        "menu_cost": "Custo do Empregador", 
        "title_calc": "Simulador de Remuneração", 
        "title_rules": "Regras de Contribuições", 
        "title_rules_sti": "Regras de Cálculo do STI", 
        "title_cost": "Custo do Empregador", 
        "country": "País", 
        "salary": "Salário Bruto", 
        "state": "Estado (EUA)", 
        "state_rate": "State Tax (%)", 
        "dependents": "Dependentes (IR)", 
        "bonus": "Bônus", 
        "other_deductions": "Outras Deduções Mensais", 
        "earnings": "Proventos", 
        "deductions": "Descontos", 
        "net": "Salário Líquido", 
        "fgts_deposit": "Depósito FGTS", 
        "tot_earnings": "Total de Proventos", 
        "tot_deductions": "Total de Descontos", 
        "valid_from": "Vigência", 
        "rules_emp": "Contribuições do Empregado", 
        "rules_er": "Contribuições do Empregador", 
        "rules_table_desc": "Descrição", 
        "rules_table_rate": "Alíquota (%)", 
        "rules_table_base": "Base de Cálculo", 
        "rules_table_obs": "Observações / Teto", 
        "official_source": "Fonte Oficial", 
        "employer_cost_total": "Custo Total do Empregador", 
        "annual_comp_title": "Composição da Remuneração Total Bruta", 
        "calc_params_title": "Parâmetros de Cálculo da Remuneração", 
        "monthly_comp_title": "Remuneração Mensal Bruta e Líquida", 
        "annual_salary": "Salário Anual", 
        "annual_bonus": "Bônus", 
        "annual_total": "Remuneração Total", 
        "months_factor": "Meses considerados", "pie_title": "Distribuição Anual: Salário vs Bônus", "pie_chart_title_dist": "Distribuição da Remuneração Total", "reload": "Recarregar tabelas", "source_remote": "Tabelas remotas", "source_local": "Fallback local", "choose_country": "Selecione o país", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalhes das Contribuições Obrigatórias", "salary_tooltip": "Seu salário mensal antes de impostos e deduções.", "dependents_tooltip": "Número de dependentes para dedução no Imposto de Renda (aplicável apenas no Brasil).", 
        "bonus_tooltip": "Valor total do bônus esperado no ano (pago de uma vez ou parcelado).", 
        "other_deductions_tooltip": "Soma de outras deduções mensais recorrentes (ex: plano de saúde, vale-refeição, contribuição sindical).", "sti_area_tooltip": "Selecione sua área de atuação (Vendas ou Não Vendas) para verificar a faixa de bônus (STI).", "sti_level_tooltip": "Selecione seu nível de carreira para verificar a faixa de bônus (STI). 'Others' inclui níveis não listados.", "sti_area_non_sales": "Não Vendas", "sti_area_sales": "Vendas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Membros do GEB", "sti_level_executive_manager": "Gerente Executivo", "sti_level_senior_group_manager": "Gerente de Grupo Sênior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Especialista Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sênior", "sti_level_senior_expert_senior_project_manager": "Especialista Sênior / Gerente de Projeto Sênior", "sti_level_manager_selected_expert_project_manager": "Gerente / Especialista Selecionado / Gerente de Projeto", "sti_level_others": "Outros", "sti_level_executive_manager_senior_group_manager": "Gerente Executivo / Gerente de Grupo Sênior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Vendas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sênior / Gerente de Vendas Sênior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Vendas Selecionado", "sti_in_range": "Dentro do range", "sti_out_range": "Fora do range", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observação", "cost_header_bonus": "Incide Bônus", "cost_header_vacation": "Incide Férias", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nível de Carreira", "sti_table_header_pct": "STI %" 
    }, 
    "English": { 
        "sidebar_title": "Compensation Simulator<br>(Americas Region)", 
        "other_deductions": "Other Monthly Deductions", 
        "salary_tooltip": "Your monthly salary before taxes and deductions.", 
        "dependents_tooltip": "Number of dependents for Income Tax deduction (applicable only in Brazil).", 
        "bonus_tooltip": "Total expected bonus amount for the year (paid lump sum or installments).", 
        "other_deductions_tooltip": "Sum of other recurring monthly deductions (e.g., health plan, meal voucher, union dues).", 
        "sti_area_tooltip": "Select your area (Sales or Non Sales) to check the bonus (STI) range.", 
        "sti_level_tooltip": "Select your career level to check the bonus (STI) range. 'Others' includes unlisted levels.", 
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
        "dependents": "Dependentes (Tax)", 
        "bonus": "Bonus", 
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
        "official_source": "Official Source", 
        "employer_cost_total": "Total Employer Cost", 
        "annual_comp_title": "Total Gross Compensation", 
        "annual_salary": "Annual Salary", 
        "annual_bonus": "Bonus", 
        "annual_total": "Total Compensation", 
        "months_factor": "Months considered", "pie_title": "Annual Split: Salary vs Bonus", "pie_chart_title_dist": "Total Compensation Distribution", "reload": "Reload tables", "source_remote": "Remote tables", "source_local": "Local fallback", "choose_country": "Select a country", "menu_title": "Menu", "language_title": "🌐 Idioma / Language / Idioma", "area": "Area (STI)", "level": "Career Level (STI)", "rules_expanded": "Details of Mandatory Contributions", "sti_area_non_sales": "Non Sales", "sti_area_sales": "Sales", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Members of the GEB", "sti_level_executive_manager": "Executive Manager", "sti_level_senior_group_manager": "Senior Group Manager", "sti_level_group_manager": "Group Manager", "sti_level_lead_expert_program_manager": "Lead Expert / Program Manager", "sti_level_senior_manager": "Senior Manager", "sti_level_senior_expert_senior_project_manager": "Senior Expert / Senior Project Manager", "sti_level_manager_selected_expert_project_manager": "Manager / Selected Expert / Project Manager", "sti_level_others": "Others", "sti_level_executive_manager_senior_group_manager": "Executive Manager / Senior Group Manager", "sti_level_group_manager_lead_sales_manager": "Group Manager / Lead Sales Manager", "sti_level_senior_manager_senior_sales_manager": "Senior Manager / Senior Sales Manager", "sti_level_manager_selected_sales_manager": "Manager / Selected Sales Manager", "sti_in_range": "Within range", "sti_out_range": "Outside range", "cost_header_charge": "Charge", "cost_header_percent": "Percent (%)", "cost_header_base": "Base", "cost_header_obs": "Observation", "cost_header_bonus": "Applies to Bonus", "cost_header_vacation": "Applies to Vacation", "cost_header_13th": "Applies to 13th", "sti_table_header_level": "Career Level", "sti_table_header_pct": "STI %" 
    }, 
    "Español": { 
        "sidebar_title": "Simulador de Remuneración<br>(Región Américas)", 
        "other_deductions": "Otras Deducciones Mensuales", 
        "salary_tooltip": "Su salario mensual antes de impuestos y deducciones.", 
        "dependents_tooltip": "Número de dependientes para deducción en el Impuesto de Renta (solo aplicable en Brasil).", 
        "bonus_tooltip": "Monto total del bono esperado en el año (pago único o en cuotas).", 
        "other_deductions_tooltip": "Suma de otras deducciones mensuales recurrentes (ej: plan de salud, ticket de comida, cuota sindical).", 
        "sti_area_tooltip": "Seleccione su área (Ventas o No Ventas) para verificar el rango del bono (STI).", 
        "sti_level_tooltip": "Seleccione su nivel de carrera para verificar el rango del bono (STI). 'Otros' incluye niveles no listados.", 
        "app_title": "Simulador de Salario Neto y Costo del Empleador", 
        "menu_calc": "Simulador de Remuneração", 
        "menu_rules": "Regras de Contribuições", 
        "menu_rules_sti": "Regras de Cálculo del STI", 
        "menu_cost": "Costo del Empleador", 
        "title_calc": "Simulador de Remuneração", 
        "title_rules": "Regras de Contribuições", 
        "title_rules_sti": "Reglas de Cálculo del STI", 
        "title_cost": "Costo del Empleador", 
        "country": "País", 
        "salary": "Salario Bruto", 
        "state": "Estado (EE. UU.)", 
        "state_rate": "Impuesto Estatal (%)", 
        "dependents": "Dependientes (Impuesto)", 
        "bonus": "Bono", 
        "earnings": "Ingresos", 
        "deductions": "Descuentos", 
        "net": "Salario Neto", 
        "fgts_deposit": "Depósito de FGTS", 
        "tot_earnings": "Total Ingresos", 
        "tot_deductions": "Total Descuentos", 
        "valid_from": "Vigencia", 
        "rules_emp": "Contribuições del Empleado", 
        "rules_er": "Contribuições del Empleador", 
        "rules_table_desc": "Descripción", 
        "rules_table_rate": "Tasa (%)", 
        "rules_table_base": "Base de Cálculo", 
        "rules_table_obs": "Notas / Tope", 
        "official_source": "Fuente Oficial", 
        "employer_cost_total": "Costo Total del Empleador", 
        "annual_comp_title": "Composição de la Remuneração Total Bruta", 
        "annual_salary": "Salario Anual", 
        "annual_bonus": "Bono", 
        "annual_total": "Remuneração Total", 
        "months_factor": "Meses considerados", "pie_title": "Distribuição Anual: Salario vs Bono", "pie_chart_title_dist": "Distribución de la Remuneração Total", "reload": "Recarregar tablas", "source_remote": "Tablas remotas", "source_local": "Copia local", "choose_country": "Seleccione un país", "menu_title": "Menú", "language_title": "🌐 Idioma / Language / Idioma", "area": "Área (STI)", "level": "Career Level (STI)", "rules_expanded": "Detalles de las Contribuições Obligatorias", "sti_area_non_sales": "No Ventas", "sti_area_sales": "Ventas", "sti_level_ceo": "CEO", "sti_level_members_of_the_geb": "Miembros del GEB", "sti_level_executive_manager": "Gerente Ejecutivo", "sti_level_senior_group_manager": "Gerente de Grupo Sénior", "sti_level_group_manager": "Gerente de Grupo", "sti_level_lead_expert_program_manager": "Experto Líder / Gerente de Programa", "sti_level_senior_manager": "Gerente Sénior", "sti_level_senior_expert_senior_project_manager": "Experto Sénior / Gerente de Proyecto Sénior", "sti_level_manager_selected_expert_project_manager": "Gerente / Experto Seleccionado / Gerente de Proyecto", "sti_level_others": "Otros", "sti_level_executive_manager_senior_group_manager": "Gerente Ejecutivo / Gerente de Grupo Sénior", "sti_level_group_manager_lead_sales_manager": "Gerente de Grupo / Gerente de Ventas Líder", "sti_level_senior_manager_senior_sales_manager": "Gerente Sénior / Gerente de Ventas Sénior", "sti_level_manager_selected_sales_manager": "Gerente / Gerente de Ventas Seleccionado", "sti_in_range": "Dentro del rango", "sti_out_range": "Fuera del rango", "cost_header_charge": "Encargo", "cost_header_percent": "Percentual (%)", "cost_header_base": "Base", "cost_header_obs": "Observação", "cost_header_bonus": "Incide Bono", "cost_header_vacation": "Incide Vacaciones", "cost_header_13th": "Incide 13º", "sti_table_header_level": "Nivel de Carrera", "sti_table_header_pct": "STI %" 
    } 
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


# ======================== FUNÇÕES DE CÁLCULO E AUXÍLIO (Movidas para o topo) =========================

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
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(country_code, 12.0)
    enc_list = tables_ext.get("EMPLOYER_COST", {}).get(country_code, [])
    
    country_info = COUNTRIES.get(country_code, {})
    symbol_local = country_info.get("symbol", "")
    benefits = country_info.get("benefits", {"ferias": False, "decimo": False})
    
    df = pd.DataFrame(enc_list); df_display = pd.DataFrame()
    if not df.empty:
        df_display = df.copy()
        df_display[T["cost_header_charge"]] = df_display["nome"]
        df_display["percentual"] = df_display["percentual"].astype(float) 
        df_display[T["cost_header_percent"]] = df_display["percentual"].apply(lambda p: f"{p:.2f}%")
        df_display[T["cost_header_base"]] = df_display["base"]
        
        df_display[T["cost_header_obs"]] = df_display.apply(
            lambda row: fmt_cap(row.get('teto'), symbol_local) if row.get('teto') is not None else row.get('obs', '—'), 
            axis=1
        )
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
            if country_code == "Canadá": 
                 if item.get("nome") == "CPP2 (ER)": base_calc_anual = max(0, min(base_calc_anual, ANNUAL_CAPS["CA_CPP_YMPEx2"]) - ANNUAL_CAPS["CA_CPP_YMPEx1"])
                 else: base_calc_anual = min(base_calc_anual, teto)
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

# ============================== CSS (REFINADO E SIMPLIFICADO + TABELA) ================================
st.markdown("""
<style>
/* 1. LIMITA LARGURA MÁXIMA E CENTRALIZA O CONTEÚDO PRINCIPAL (REDUZIDO PARA MAIOR ELEGÂNCIA) */
div.block-container {
    max-width: 1100px; /* Largura máxima para visualização elegante */
    padding-left: 1rem;
    padding-right: 1rem;
}

/* 2. ESTILOS DE TÍTULOS E LABELS DE INPUT */
.stMarkdown h5 {
    font-size: 15px; /* Ligeiramente maior para visibilidade */
    font-weight: 500; 
    line-height: 1.2; 
    color: #0a3d62;
    margin-bottom: 0.2rem !important;
}
.stMarkdown h5 span { /* Para aplicar estilo ao símbolo dentro do h5, se houver */
    font-weight: 400;
    color: #555;
    font-size: 14px;
}

/* 3. PADRONIZAÇÃO DE CARDS: Elegância, Simetria e Centralização */
.metric-card, .annual-card-base {
    min-height: 95px !important; 
    padding: 10px 15px !important; 
    display: flex;
    flex-direction: column; 
    /* AJUSTE 1: Centralização Vertical */
    justify-content: center; 
    /* AJUSTE 2: Centralização Horizontal */
    text-align: center; 
    box-sizing: border-box;
    background: #fff;
    border-radius: 10px; 
    box-shadow: 0 1px 4px rgba(0,0,0,.08); 
    margin-bottom: 10px; 
    border-left: none !important; 
    transition: all 0.3s ease;
}
.metric-card:hover{ 
    box-shadow: 0 6px 16px rgba(0,0,0,0.12); 
    transform: translateY(-2px); 
}

/* Ajustes de tipografia dos cards */
.metric-card h4, .annual-card-base h4 {
    margin:0; 
    font-size:15px; 
    font-weight: 500; 
    color:#555; 
}
.metric-card h3, .annual-card-base h3 {
    margin: 2px 0 0; 
    color:#0a3d62; 
    font-size:22px; 
    font-weight: 700; 
}

/* Cores de Fundo Mais Sutis para Cards Mensais e Anuais */
.card-earn { background: #f7fff7 !important; }
.card-ded { background: #fff7f7 !important; }
.card-net { background: #f7faff !important; }
.card-bonus-in { background: #f7faff !important; }
.card-bonus-out { background: #fff7f7 !important; }
.card-total { background: #f5f5f5 !important; }

/* 4. Estilo de Tabela HTML (Para Remuneração Mensal - Tabela Injetada) */
.table-wrap {
    /* Manter bordas e sombra para o wrapper da tabela */
    background:#fff; 
    border:1px solid #d0d7de; 
    border-radius: 8px; 
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.monthly-table {
    width: 100%;
    border-collapse: collapse; /* Remover bordas duplas */
    margin: 0;
    border: none;
    font-size: 15px;
}
.monthly-table thead th {
    background-color: #0a3d62; /* Cor de destaque (Azul Escuro) */
    color: white;
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
}
.monthly-table tbody td {
    padding: 10px 15px;
    border-bottom: 1px solid #eee;
}
.monthly-table tbody tr:nth-child(even) {
    background-color: #fcfcfc; /* Linhas zebradas muito sutis */
}
.monthly-table tbody tr:last-child td {
    border-bottom: none;
}
/* Estilo para garantir que o Streamlit não interfira no header com o thead */
.stTable > div:first-child table {
    border-radius: 8px; /* Cantos arredondados na tabela Streamlit padrão */
    overflow: hidden;
}

/* O restante do seu CSS é mantido */
html, body { font-family:'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e2e6ea; margin:24px 0; border-radius:1px; }
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
section[data-testid="stSidebar"] .stNumberInput input:focus,
section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{ color:#0b1f33 !important; background:#fff !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span { color: #ffffff !important; }
.country-header{ display:flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 5px; }
.country-flag{ font-size:45px; }
.country-title{ font-size:36px; font-weight:700; color:#0a3d62; }
.vega-embed{ padding-bottom: 16px; }

.annual-card-label .sti-note { display: block; font-size: 14px; font-weight: 400; line-height: 1.3; margin-top: 2px; }
/* Container customizado para espaçamento */
.card-row-spacing {
    margin-top: 20px; /* Adiciona espaçamento entre a tabela e os cards de resumo */
}
</style>
""", unsafe_allow_html=True)


# ============================== SIDEBAR (MANTIDO) ===============================
with st.sidebar:
    # 1. TÍTULO PRINCIPAL (Ordem Corrigida)
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
    
    T = I18N.get(idioma, I18N_FALLBACK["Português"])
    
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

    # Captura o valor do radio e define o estado (FORÇA A NAVEGAÇÃO)
    new_active_menu = st.radio(
        label="Menu Select", options=menu_options, 
        index=active_menu_index,
        label_visibility="collapsed", 
        key="menu_radio_select_widget" # Usamos uma nova chave para o widget
    )
    
    # Lógica que força o rerun se o menu mudar
    if new_active_menu != st.session_state.active_menu:
        st.session_state.active_menu = new_active_menu
        st.rerun()


# ======================= INICIALIZAÇÃO PÓS-SIDEBAR (MANTIDO) =======================
if 'idioma' in st.session_state:
    T = I18N.get(st.session_state.idioma, I18N_FALLBACK["Português"])
else:
    T = I18N_FALLBACK["Português"]

country = st.session_state.get('country_select', 'Brasil') 
active_menu = st.session_state.get('active_menu', T.get("menu_calc", "Calc"))

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

# ========================= SIMULADOR DE REMUNERAÇÃO (REFINADO E CONSOLIDADO) ==========================
if active_menu == T.get("menu_calc"):
    area_options_display, area_display_map = get_sti_area_map(T)
    st.subheader(T.get("calc_params_title", "Parameters"))

    # Funções auxiliares para montar o HTML dos rótulos sem quebra de linha
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
        # Layout Brasil: 4 colunas uniformes (Linha 1 e 2)
        
        # RÓTULOS LINHA 1 (Salário, Dependentes, Outras Ded, Bônus)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 25%;"><h5>{get_simple_label('salary', 'Salário Bruto', symbol)}</h5></div>
            <div style="width: 25%;"><h5>{get_simple_label('dependents', 'Dependentes')} (IR)</h5></div>
            <div style="width: 25%;"><h5>{get_simple_label('other_deductions', 'Outras Deduções', symbol)}</h5></div>
            <div style="width: 25%;"><h5>{get_simple_label('bonus', 'Bônus', symbol)}</h5></div>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(4) 
        # INPUTS LINHA 1
        salario = cols[0].number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        dependentes = cols[1].number_input("Dependentes", min_value=0, value=0, step=1, key="dep_input", help=T.get("dependents_tooltip"), label_visibility="collapsed")
        other_deductions = cols[2].number_input("Outras Deduções", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        bonus_anual = cols[3].number_input("Bônus", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        
        # RÓTULOS LINHA 2 (STI)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div style="width: 25%;"><h5>{get_sti_label('area', 'Área')}</h5></div>
            <div style="width: 25%;"><h5>{get_sti_label('level', 'Career Level')}</h5></div>
            <div style="width: 50%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, r3, r4 = st.columns(4) # 4 COLUNAS para simetria
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        state_code, state_rate = None, None
        dependentes_fixed = dependentes 

    elif country == "Estados Unidos":
        # Layout EUA: 5 colunas uniformes (Linha 1 e 2)
        
        # RÓTULOS LINHA 1 (5 campos)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 20%;"><h5>{get_simple_label('salary', 'Gross Salary', symbol)}</h5></div>
            <div style="width: 20%;"><h5>{get_simple_label('state', 'State')}</h5></div>
            <div style="width: 20%;"><h5>{get_simple_label('state_rate', 'State Tax')} (%)</h5></div>
            <div style="width: 20%;"><h5>{get_simple_label('other_deductions', 'Other Deductions', symbol)}</h5></div>
            <div style="width: 20%;"><h5>{get_simple_label('bonus', 'Bonus', symbol)}</h5></div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5 = st.columns(5)
        # INPUTS LINHA 1
        salario = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        state_code = c2.selectbox("Estado", list(US_STATE_RATES.keys()), index=0, key="state_select_main", help=T.get("state"), label_visibility="collapsed")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input("Taxa Estadual", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input", help=T.get("state_rate"), label_visibility="collapsed")
        other_deductions = c4.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        bonus_anual = c5.number_input("Bônus", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        
        # RÓTULOS LINHA 2 (STI)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div style="width: 20%;"><h5>{get_sti_label('area', 'Area')}</h5></div>
            <div style="width: 20%;"><h5>{get_sti_label('level', 'Career Level')}</h5></div>
            <div style="width: 60%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, r3, r4, r5 = st.columns(5) # 5 COLUNAS para simetria
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes_fixed = 0
        
    else: # Outros países (4 colunas para simetria)
        
        # RÓTULOS PRINCIPAIS EM HTML ACIMA DAS COLUNAS (4 colunas)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 25%;"><h5>{get_simple_label('salary', 'Salário Bruto', symbol)}</h5></div>
            <div style="width: 25%;"><h5>{get_simple_label('other_deductions', 'Outras Deduções', symbol)}</h5></div>
            <div style="width: 25%;"><h5>{get_simple_label('bonus', 'Bônus', symbol)}</h5></div>
            <div style="width: 25%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4) # 4 COLUNAS para simetria
        # INPUTS LINHA 1
        salario = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        other_deductions = c2.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        bonus_anual = c3.number_input("Bônus", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed", format=INPUT_FORMAT)
        
        # RÓTULOS LINHA 2 (STI)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div style="width: 25%;"><h5>{get_sti_label('area', 'Área')}</h5></div>
            <div style="width: 25%;"><h5>{get_sti_label('level', 'Career Level')}</h5></div>
            <div style="width: 50%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, r3, r4 = st.columns(4) # 4 COLUNAS para simetria
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes_fixed = 0
        state_code, state_rate = None, None

    # 3) DIVISOR ACIMA DE REMUNERAÇÃO MENSAL
    st.write("---") 
    
    st.subheader(T.get("monthly_comp_title", "Remuneração Mensal Bruta e Líquida"))
    
    dependentes = dependentes_fixed

    calc = calc_country_net(country, salario, other_deductions, state_code=state_code, state_rate=state_rate, dependentes=dependentes, tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL)
    df_detalhe = pd.DataFrame(calc["lines"], columns=["Descrição", T.get("earnings","Earnings"), T.get("deductions","Deductions")])
    df_detalhe[T.get("earnings","Earnings")] = df_detalhe[T.get("earnings","Earnings")].apply(lambda v: money_or_blank(v, symbol))
    df_detalhe[T.get("deductions","Deductions")] = df_detalhe[T.get("deductions","Deductions")].apply(lambda v: money_or_blank(v, symbol))
    
    # 5) FORMATANDO TABELA MENSAL (CONVERTENDO PARA HTML E INJETANDO COM CSS)
    
    # O DataFrame deve ser convertido para HTML com o índice DESABILITADO.
    table_html = df_detalhe.to_html(index=False, classes='monthly-table')
    
    st.markdown(f"<div class='table-wrap'>{table_html}</div>", unsafe_allow_html=True)

    # NOVO CONTAINER COM MARGEM SUPERIOR PARA ESPAÇAMENTO
    st.markdown("<div class='card-row-spacing'>", unsafe_allow_html=True)
    
    cc1, cc2, cc3 = st.columns(3)
    # Cards Mensais (APLICADAS AS CORES MAIS SUTIS)
    cc1.markdown(f"<div class='metric-card card-earn'><h4>💰 {T.get('tot_earnings','Total Earnings')}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card card-ded'><h4>📉 {T.get('tot_deductions','Total Deductions')}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card card-net'><h4>💵 {T.get('net','Net Salary')}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True) # Fechando o container de espaçamento

    # 2) REPOSICIONAMENTO DO FGTS ABAIXO DOS CARDS MENSAIS
    if country == "Brasil": 
        st.markdown(f"""
        <div style="margin-top: 10px; padding: 5px 0;">
            <p style="font-size: 17px; font-weight: 600; color: #0a3d62; margin: 0;">
                💼 {T.get('fgts_deposit','Depósito FGTS')}: {fmt_money(calc['fgts'], symbol)}
            </p>
        </div>
        """, unsafe_allow_html=True)


    st.write("---")
    # NOVO LAYOUT ANUAL: Cards na Horizontal e Gráfico Abaixo
    st.subheader(T.get("annual_comp_title", "Composição da Remuneração Total Bruta"))
    
    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, 12.0)
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0
    pct_txt = f"{bonus_pct*100:.1f}%"
    faixa_txt = f"≤ {(max_pct or 0)*100:.0f}%" if level == "Others" else f"{min_pct*100:.0f}% – {max_pct*100:.0f}%"
    dentro = (bonus_pct <= (max_pct or 0)) if level == "Others" else (min_pct <= bonus_pct <= max_pct)
    cor = "#1976d2" if dentro else "#d32f2f"; status_txt = T.get("sti_in_range", "In") if dentro else T.get("sti_out_range", "Out"); 
    bg_cor = "card-bonus-in" if dentro else "card-bonus-out" # Usando as novas classes
    sti_note_text = f"<span style='color:{cor};'><strong>{pct_txt}</strong> — <strong>{status_txt}</strong></span> ({faixa_txt}) — <em>{area_display} • {level_display}</em>"


    # 1. LINHA DE CARDS NA HORIZONTAL COM ALTURA IGUAL
    col_salario, col_bonus, col_total = st.columns(3)

    # Card Salário Anual
    col_salario.markdown(f"""
    <div class='metric-card card-earn'>
        <h4> {T.get('annual_salary','Salário Anual')} </h4>
        <h3>{fmt_money(salario_anual, symbol)}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Card Bônus (Usando a cor STI para o texto, mas a cor sutil para o fundo)
    col_bonus.markdown(f"""
    <div class='metric-card {bg_cor}'>
        <h4 style='color:{cor};'> {T.get('annual_bonus','Bônus')} </h4>
        <h3 style='color:{cor};'>{fmt_money(bonus_anual, symbol)}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Card Remuneração Total
    col_total.markdown(f"""
    <div class='metric-card card-total'>
        <h4> {T.get('annual_total','Remuneração Total')} </h4>
        <h3>{fmt_money(total_anual, symbol)}</h3>
    </div>
    """, unsafe_allow_html=True)

    # 2. NOTAS ABAIXO DA LINHA DE CARDS (APLICANDO FORMATO FGTS E EMOJIS)
    st.markdown(f"""
    <div style="margin-top: 10px; padding: 5px 0;">
        <p style="font-size: 17px; font-weight: 600; color: #0a3d62; margin: 0;">
            📅 {T.get('months_factor','Meses considerados')}: {months}
        </p>
        <p style="font-size: 17px; font-weight: 600; color: #0a3d62; margin: 5px 0 0 0;">
            🎯 STI Ratio: {sti_note_text}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---") # Divisor visual

    # 3. GRÁFICO DE PIZZA ABAIXO DOS CARDS
    
    chart_df = pd.DataFrame({
        # Usa os rótulos atualizados do I18N
        "Componente": [T.get('annual_salary'), T.get('annual_bonus')], 
        "Valor": [salario_anual, bonus_anual]
    })
    
    # Renomeando colunas para a exibição no gráfico usando os rótulos dinâmicos
    salary_name = T.get('annual_salary')
    bonus_name = T.get('annual_bonus')
    
    chart_df['Componente'] = chart_df['Componente'].replace({
        T.get('annual_salary'): salary_name,
        T.get('annual_bonus'): bonus_name
    })

    base = alt.Chart(chart_df).transform_joinaggregate(
        Total='sum(Valor)'
    ).transform_calculate(
        Percent='datum.Valor / datum.Total',
        # Usando a template string nativa para formar o rótulo
        Label=alt.expr.if_(alt.datum.Valor > alt.datum.Total * 0.05, 
                            alt.datum.Componente + " (" + alt.expr.format(alt.datum.Percent, ".1%") + ")", 
                            "") 
    )
    
    pie = base.mark_arc(outerRadius=120, innerRadius=80, cornerRadius=2).encode(
        theta=alt.Theta("Valor:Q", stack=True),
        color=alt.Color("Componente:N", legend=None), # Remove a legenda
        order=alt.Order("Percent:Q", sort="descending"),
        tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f")]
    )
    
    text = base.mark_text(radius=140).encode(
        text=alt.Text("Label:N"),
        theta=alt.Theta("Valor:Q", stack=True),
        order=alt.Order("Percent:Q", sort="descending"),
        color=alt.value("black") 
    )

    final_chart = alt.layer(pie, text).properties(
        title=T.get("pie_chart_title_dist", "Distribuição da Remuneração Total")
    ).configure_view(
        strokeWidth=0
    ).configure_title(
        fontSize=17, anchor='middle', color='#0a3d62'
    )
    st.altair_chart(final_chart, use_container_width=True)


    
# =========================== REGRAS DE CONTRIBUIÇÕES (MANTIDO) ===================
elif active_menu == T.get("menu_rules"):
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
    
    # As tabelas de regras (que usam st.dataframe) manterão o índice por padrão, mas terão um visual melhor.
    if not df_emp.empty: st.markdown(f"#### {T.get('rules_emp', 'Employee')}"); st.dataframe(df_emp, use_container_width=True, hide_index=True)
    if not df_er.empty: st.markdown(f"#### {T.get('rules_er', 'Employer')}"); st.dataframe(df_er, use_container_width=True, hide_index=True)
    st.markdown("---")

    # --- Explicações Detalhadas (MANTIDO) ---
    if country == "Brasil":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **INSS:** Calculado de forma progressiva sobre faixas salariais (7.5% a 14%). A contribuição total é a soma do valor calculado em cada faixa, limitada ao teto de contribuição.\n- **IRRF:** Calculado sobre o Salário Bruto após deduzir o INSS e um valor fixo por dependente. Aplica-se a alíquota da faixa (0% a 27.5%) e subtrai-se a parcela a deduzir.\n\n**{T["rules_er"]} - Explicação:**\n- **INSS Patronal, RAT, Sistema S:** Percentuais aplicados sobre o total da folha.\n- **FGTS:** Depósito mensal de 8% sobre o Salário Bruto.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Custo anual inclui 13º (1 salário) e Férias (1 salário + 1/3). Fator `13.33`. Encargos incidem sobre essa base ampliada.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **INSS:** Progressive rate (7.5% to 14%) on brackets, capped.\n- **IRRF:** Progressive rate (0% to 27.5%) on (Gross - INSS - Dep. Allowance) minus deduction.\n\n**{T["rules_er"]} - Explanation:**\n- **INSS Patronal, RAT, Sistema S:** Percentages on total payroll.\n- **FGTS:** 8% deposit.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Annual cost factor `13.33` includes 13th Salary and Vacation + 1/3 bonus. Charges apply to this base.""", unsafe_allow_html=True)
    elif country == "Estados Unidos":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **FICA (Social Security):** 6.2% sobre Sal. Bruto, até teto anual ({fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}).\n- **Medicare:** 1.45% sobre Sal. Bruto total.\n- **State Tax:** Varia por estado.\n\n**{T["rules_er"]} - Explicação:**\n- **FICA & Medicare Match:** Empregador paga o mesmo que o empregado.\n- **SUTA/FUTA:** Desemprego sobre base baixa (~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}).\n\n**{T["rules_er"]} - Explanation:**\n- **FICA & Medicare Match:** Employer pays the same.\n- **SUTA/FUTA:** Unemployment on low base (~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Not mandatory. Factor `12.00`.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **FICA (Social Security):** 6.2% on Gross Salary, up to cap ({fmt_money(ANNUAL_CAPS['US_FICA'], 'US$')}).\n- **Medicare:** 1.45% on total Gross Salary.\n- **State Tax:** Varies.\n\n**{T["rules_er"]} - Explanation:**\n- **FICA & Medicare Match:** Employer pays the same.\n- **SUTA/FUTA:** Unemployment on low base (~{fmt_money(ANNUAL_CAPS['US_SUTA_BASE'], 'US$')}).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Not mandatory. Factor `12.00`.""", unsafe_allow_html=True)
    elif country == "Canadá":
          if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **CPP:** 5.95% sobre Sal. Bruto (após isenção {fmt_money(ANNUAL_CAPS['CA_CPP_EXEMPT'], 'CAD$')}) até Teto 1 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}).\n- **CPP2:** 4.0% sobre Sal. Bruto entre Teto 1 e Teto 2 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}).\n- **EI:** 1.63% sobre Sal. Bruto até Teto ({fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}).\n- **Income Tax:** Progressivo Federal + Provincial (Simplificado no simulador).\n\n**{T["rules_er"]} - Explicação:**\n- **CPP/CPP2 Match:** Empregador paga o mesmo.\n- **EI Match:** Empregador paga 1.4x (2.28%).\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Não obrigatórios. Fator `12.00`.""", unsafe_allow_html=True)
          else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **CPP:** 5.95% on Gross (after exempt {fmt_money(ANNUAL_CAPS['CA_CPP_EXEMPT'], 'CAD$')}) up to Cap 1 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx1'], 'CAD$')}).\n- **CPP2:** 4.0% on Gross between Cap 1 and Cap 2 ({fmt_money(ANNUAL_CAPS['CA_CPP_YMPEx2'], 'CAD$')}).\n- **EI:** 1.63% on Gross up to Cap ({fmt_money(ANNUAL_CAPS['CA_EI_MIE'], 'CAD$')}).\n- **Income Tax:** Progressive Federal + Provincial (Simplified in simulator).\n\n**{T["rules_er"]} - Explanation:**\n- **CPP/CPP2 Match:** Employer pays the same.\n- **EI Match:** Employer pays 1.4x (2.28%).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Not mandatory. Factor `12.00`.""", unsafe_allow_html=True)
    elif country == "México":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação (Simplificada):**\n- **ISR:** Imposto de renda progressivo. Cálculo exato usa tabelas complexas. O simulador usa uma taxa fixa como aproximação.\n- **IMSS:** Seguridade social (doenças, invalidez, etc.). Taxas variam e aplicam-se sobre o Salário Base de Contribuição (SBC), com teto (aprox. 25 UMAs). O simulador usa taxa e teto simplificados.\n\n**{T["rules_er"]} - Explicação:**\n- **IMSS, INFONAVIT, SAR, ISN:** Contribuições patronais sobre SBC (com tetos) e folha.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- **Aguinaldo (13º):** Mín. 15 dias. Fator `12.50`.\n- **Prima Vacacional:** 25% sobre dias de férias.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **ISR:** Progressive income tax. Exact calculation uses complex tables. Simulator uses a flat rate approximation.\n- **IMSS:** Social security (illness, disability, etc.). Rates vary and apply to the Contribution Base Salary (SBC), capped (approx. 25 UMAs). Simulator uses simplified rate and cap.\n\n**{T["rules_er"]} - Explanation:**\n- **IMSS, INFONAVIT, SAR, ISN:** Contributions on SBC (capped) and payroll.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- **Aguinaldo (13th):** Min. 15 days. Factor `12.50`.\n- **Prima Vacacional:** 25% on vacation days.""", unsafe_allow_html=True)
    elif country == "Chile":
        if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **AFP:** 10% + comissão (~1.15%) para pensão. Base com teto em UF.\n- **Saúde:** 7% para FONASA/ISAPRE. Base com teto em UF.\n\n**{T["rules_er"]} - Explicação:**\n- **Seguro de Cesantía:** 2.4%. Base com teto em UF.\n- **SIS:** ~1.53% para invalidez. Base com teto em UF.\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- Aguinaldo não obrigatório. Fator `12.00`.""", unsafe_allow_html=True)
        else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **AFP:** 10% + fee (~1.15%) for pension. Base capped in UF.\n\n**{T["rules_er"]} - Explanation:**\n- **Seguro de Cesantía:** 2.4%. Base capped in UF.\n- **SIS:** ~1.53% for disability. Base capped in UF.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- Aguinaldo not mandatory. Factor `12.00`.""", unsafe_allow_html=True)
    elif country == "Argentina":
          if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **Jubilación, Obra Social, PAMI:** Total 17% sobre Sal. Bruto (com teto).\n\n**{T["rules_er"]} - Explicação:**\n- **Cargas Sociales:** ~23.5% sobre Sal. Bruto (com teto).\n\n**{T['cost_header_13th']} e {T['cost_header_vacation']}:**\n- **SAC (13º):** 1 salário/ano em 2 parcelas. Fator `13.00`. Encargos incidem.""", unsafe_allow_html=True)
          else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **Jubilación, Obra Social, PAMI:** Total 17% on Gross Salary (capped).\n\n**{T["rules_er"]} - Explanation:**\n- **Cargas Sociales:** ~23.5% on Gross Salary (capped).\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- **SAC (13th):** 1 salary/year in 2 installments. Factor `13.00`. Charges apply.""", unsafe_allow_html=True)
    elif country == "Colômbia":
          if idioma == "Português": st.markdown(f""" **{T["rules_emp"]} - Explicação:**\n- **Salud & Pensión:** 4% cada sobre IBC.\n\n**{T["rules_er"]} - Explicação:**\n- **Salud & Pensión:** 8.5% e 12% sobre IBC.\n- **Parafiscales:** 9% sobre folha (salvo exceções).\n- **Cesantías:** 8.33% (1/12) sobre base anual, depositado em fundo.\n\n**{T["rules_er"]} - Explanation:**\n- **Salud & Pensión:** 8.5% and 12% on IBC.\n- **Parafiscales:** 9% on payroll (exceptions apply).\n- **Cesantías:** 8.33% (1/12) on annual base, deposited into fund.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- **Prima (13th):** 1 salary/year.\n- **Cesantías:** Additional cost of 1 salary/year.\n- Factor `14.00` reflects annual base for charges.""", unsafe_allow_html=True)
          else: st.markdown(f""" **{T["rules_emp"]} - Explanation:**\n- **Salud & Pensión:** 8.5% and 12% on IBC.\n- **Parafiscales:** 9% on payroll (exceptions apply).\n- **Cesantías:** 8.33% (1/12) on annual base, deposited into fund.\n\n**{T['cost_header_13th']} & {T['cost_header_vacation']}:**\n- No 13th. Paid vacation mandatory. Factor `12.00`.""", unsafe_allow_html=True)

    st.write(""); st.markdown(f"**{T['valid_from']}:** {valid_from}"); st.markdown(f"[{T['official_source']}]({link})", unsafe_allow_html=True)

# =========================== REGRAS DE CÁLCULO DO STI (MANTIDO) ==================
elif active_menu == T.get("menu_rules_sti"):
    header_level = T.get("sti_table_header_level", "Level"); header_pct = T.get("sti_table_header_pct", "STI %")
    st.markdown(f"#### {T.get('sti_area_non_sales', 'Non Sales')}")
    st.markdown(f"""
    | {header_level}                                               | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T.get(STI_I18N_KEYS.get("CEO", ""), "CEO")}                 |    100%    |
    | {T.get(STI_I18N_KEYS.get("Members of the GEB", ""), "GEB")}  |  50–80%  |
    | {T.get(STI_I18N_KEYS.get("Executive Manager", ""), "Exec Mgr")}   |  45–70%  |
    | {T.get(STI_I18N_KEYS.get("Senior Group Manager", ""), "Sr Grp Mgr")}  |  40–60%  |
    | {T.get(STI_I18N_KEYS.get("Group Manager", ""), "Grp Mgr")}    |  30–50%  |
    | {T.get(STI_I18N_KEYS.get("Lead Expert / Program Manager", ""), "Lead Exp")}   |  25–40%  |
    | {T.get(STI_I18N_KEYS.get("Senior Manager", ""), "Sr Mgr")}    |  20–40%  |
    | {T.get(STI_I18N_KEYS.get("Senior Expert / Senior Project Manager", ""), "Sr Exp")} |  15–35%  |
    | {T.get(STI_I18N_KEYS.get("Manager / Selected Expert / Project Manager", ""), "Mgr/Exp")} |  10–30%  |
    | {T.get(STI_I18N_KEYS.get("Others", ""), "Others")}             |  ≤ 10%   |
    """, unsafe_allow_html=True)
    st.markdown(f"#### {T.get('sti_area_sales', 'Sales')}")
    st.markdown(f"""
    | {header_level}                                               | {header_pct} |
    | :--------------------------------------------------- | :------: |
    | {T.get(STI_I18N_KEYS.get("Executive Manager / Senior Group Manager", ""), "Exec/Sr Grp Mgr")} |  45–70%  |
    | {T.get(STI_I18N_KEYS.get("Group Manager / Lead Sales Manager", ""), "Grp/Lead Sales Mgr")}    |  35–50%  |
    | {T.get(STI_I18N_KEYS.get("Senior Manager / Senior Sales Manager", ""), "Sr/Sr Sales Mgr")} |  25–45%  |
    | {T.get(STI_I18N_KEYS.get("Manager / Selected Sales Manager", ""), "Mgr/Sales Mgr")}    |  20–35%  |
    | {T.get(STI_I18N_KEYS.get("Others", ""), "Others")}             |  ≤ 15%   |
    """, unsafe_allow_html=True)

# ========================= CUSTO DO EMPREGADOR (MANTIDO) ========================
elif active_menu == T.get("menu_cost"):
    c1, c2 = st.columns(2)
    salario = c1.number_input(f"{T.get('salary', 'Salário Bruto')} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost", format=INPUT_FORMAT)
    # APLICADO: T.get('bonus', 'Bônus')
    bonus_anual = c2.number_input(f"{T.get('bonus', 'Bônus')} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_cost_input", format=INPUT_FORMAT)
    st.write("---")
    anual, mult, df_cost, months = calc_employer_cost(country, salario, bonus_anual, T, tables_ext=COUNTRY_TABLES)
    st.markdown(f"**{T.get('employer_cost_total', 'Total Cost')} (Salário + Bônus + Encargos):** {fmt_money(anual, symbol)}  \n"
                 f"**Multiplicador de Custo (vs Salário Base 12 meses):** {mult:.3f} × (12 meses)  \n"
                 f"**{T.get('months_factor', 'Meses')} (Base Salarial):** {months}")
    # As tabelas de custo (que usam st.dataframe) manterão o índice por padrão, mas terão um visual melhor.
    if not df_cost.empty: st.dataframe(df_cost, use_container_width=True, hide_index=True)
    else: st.info("Sem encargos configurados para este país.")
