# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.47)
# Tema azul plano, multilíngue, responsivo e com STI corrigido
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import altair as alt
import requests
from typing import Dict, Any, Tuple

st.set_page_config(page_title="Simulador de Salário Líquido", layout="wide")

# ======================== ENDPOINTS REMOTOS =========================
RAW_BASE = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main"
URL_US_STATES      = f"{RAW_BASE}/us_state_tax_rates.json"
URL_COUNTRY_TABLES = f"{RAW_BASE}/country_tables.json"
URL_BR_INSS        = f"{RAW_BASE}/br_inss.json"
URL_BR_IRRF        = f"{RAW_BASE}/br_irrf.json"

# ============================== CSS ================================
st.markdown("""
<style>
html, body { font-family:'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e2e6ea; margin:16px 0; }

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

/* Cards */
.metric-card{ background:#fff; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08); padding:12px; text-align:center; }
.metric-card h4{ margin:0; font-size:13px; color:#0a3d62;}
.metric-card h3{ margin:4px 0 0; color:#0a3d62; font-size:18px; }

/* Tabela */
.table-wrap{ background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }

/* Título com bandeira */
.country-header{ display:flex; align-items:center; gap:10px; }
.country-flag{ font-size:28px; }
.country-title{ font-size:24px; font-weight:700; color:#0a3d62; }

/* Cards compactos (anual) */
.metric-card.compact{ padding:12px; min-height:100px; }

/* Grid para os 3 cards anuais lado a lado (desktop) e empilhados (mobile) */
.annual-cards-grid{
  display:grid; gap:12px; grid-template-columns: repeat(3, 1fr);
}
@media (max-width: 992px){
  .annual-cards-grid{ grid-template-columns: 1fr; }
}

/* Espaço extra abaixo do gráfico para legenda */
.vega-embed{ padding-bottom: 16px; }
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
        "annual_salary": "Salário Anual (Salário × Meses do País)",
        "annual_bonus": "Bônus Anual",
        "annual_total": "Remuneração Total Anual",
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
        "rules_expanded": "Regras detalhadas, fórmulas e exemplos práticos"
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
        "annual_salary": "Annual Salary (Salary × Country Months)",
        "annual_bonus": "Annual Bonus",
        "annual_total": "Total Annual Compensation",
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
        "rules_expanded": "Detailed rules, formulas and worked examples"
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
        "annual_salary": "Salario Anual (Salario × Meses del País)",
        "annual_bonus": "Bono Anual",
        "annual_total": "Remuneración Anual Total",
        "months_factor": "Meses considerados",
        "pie_title": "Distribución Anual: Salario vs Bono",
        "reload": "Recargar tablas",
        "source_remote": "Tablas remotas",
        "source_local": "Copia local",
        "menu": "Menú",
        "choose_country": "Seleccione un país",
        "choose_menu": "Elija una opción",
        "area": "Área (STI)",
        "level": "Career Level (STI)",
        "rules_expanded": "Reglas detalladas, fórmulas y ejemplos prácticos"
    }
}

# ====================== PAÍSES / MOEDAS / BANDEIRAS =====================
COUNTRIES = {
    "Brasil":   {"symbol": "R$",   "flag": "🇧🇷", "valid_from": "2025-01-01"},
    "México":   {"symbol": "MX$",  "flag": "🇲🇽", "valid_from": "2025-01-01"},
    "Chile":    {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01"},
    "Argentina":{"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01"},
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
    "Brasil":13.33, "México":12.50, "Chile":12.00, "Argentina":13.00,
    "Colômbia":13.00, "Estados Unidos":12.00, "Canadá":12.00
}

# ========================== FALLBACKS LOCAIS ============================
US_STATE_RATES_DEFAULT = {
    "No State Tax": 0.00, "AK": 0.00, "FL": 0.00, "NV": 0.00, "SD": 0.00, "TN": 0.00, "TX": 0.00, "WA": 0.00, "WY": 0.00, "NH": 0.00,
    "AL": 0.05, "AR": 0.049, "AZ": 0.025, "CA": 0.06,  "CO": 0.044, "CT": 0.05, "DC": 0.06,  "DE": 0.055, "GA": 0.054, "HI": 0.08,
    "IA": 0.05, "ID": 0.055, "IL": 0.0495, "IN": 0.0323, "KS": 0.052, "KY": 0.045, "LA": 0.045, "MA": 0.05, "MD": 0.047, "ME": 0.058,
    "MI": 0.0425, "MN": 0.058, "MO": 0.045, "MS": 0.05, "MT": 0.054, "NC": 0.045, "ND": 0.02,  "NE": 0.05,  "NJ": 0.055, "NM": 0.049,
    "NY": 0.064, "OH": 0.030, "OK": 0.0475,"OR": 0.08,  "PA": 0.0307, "RI": 0.0475,"SC": 0.052, "UT": 0.0485,"VA": 0.05,  "VT": 0.06,
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
        {"nome":"INSS Patronal", "percentual":20.0, "base":"Salário Bruto", "ferias":True, "decimo":True, "bonus":True, "obs":"Previdência"},
        {"nome":"RAT", "percentual":2.0, "base":"Salário Bruto", "ferias":True, "decimo":True, "bonus":True, "obs":"Risco"},
        {"nome":"Sistema S", "percentual":5.8, "base":"Salário Bruto", "ferias":True, "decimo":True, "bonus":True, "obs":"Terceiros"},
        {"nome":"FGTS", "percentual":8.0, "base":"Salário Bruto", "ferias":True, "decimo":True, "bonus":True, "obs":"Crédito empregado"}
    ],
    "México": [
        {"nome":"IMSS Patronal","percentual":7.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Seguro social"},
        {"nome":"INFONAVIT Empregador","percentual":5.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Habitação"}
    ],
    "Chile": [
        {"nome":"Seguro Desemprego","percentual":2.4,"base":"Salário","ferias":True,"decimo":False,"bonus":True,"obs":"Empregador"}
    ],
    "Argentina": [
        {"nome":"Contribuições Patronais","percentual":18.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Média setores"}
    ],
    "Colômbia": [
        {"nome":"Saúde Empregador","percentual":8.5,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"—"},
        {"nome":"Pensão Empregador","percentual":12.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"—"}
    ],
    "Estados Unidos": [
        {"nome":"Social Security (ER)","percentual":6.2,"base":"Salário","ferias":False,"decimo":False,"bonus":True,"obs":"Até wage base"},
        {"nome":"Medicare (ER)","percentual":1.45,"base":"Salário","ferias":False,"decimo":False,"bonus":True,"obs":"Sem teto"},
        {"nome":"SUTA (avg)","percentual":2.0,"base":"Salário","ferias":False,"decimo":False,"bonus":True,"obs":"Média estado"}
    ],
    "Canadá": [
        {"nome":"CPP (ER)","percentual":5.95,"base":"Salário","ferias":False,"decimo":False,"bonus":True,"obs":"Até limite"},
        {"nome":"EI (ER)","percentual":2.28,"base":"Salário","ferias":False,"decimo":False,"bonus":True,"obs":"—"}
    ]
}
BR_INSS_DEFAULT = {
    "vigencia": "2025-01-01",
    "teto_contribuicao": 1146.68,
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
# Observação: "Others" é validado por teto (≤). Demais níveis usam faixa min–max.
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
        "CEO","Members of the GEB","Executive Manager","Senior Group Manager","Group Manager",
        "Lead Expert / Program Manager","Senior Manager","Senior Expert / Senior Project Manager",
        "Manager / Selected Expert / Project Manager","Others"
    ],
    "Sales": [
        "Executive Manager / Senior Group Manager","Group Manager / Lead Sales Manager",
        "Senior Manager / Senior Sales Manager","Manager / Selected Sales Manager","Others"
    ]
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
        aliquota  = float(faixa["aliquota"])
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
    ded_dep   = float(irrf_tbl.get("deducao_dependente", 0.0))
    base_calc = max(base - ded_dep * max(int(dep), 0), 0.0)
    for faixa in irrf_tbl.get("faixas", []):
        if base_calc <= float(faixa["ate"]):
            aliq = float(faixa["aliquota"])
            ded  = float(faixa.get("deducao", 0.0))
            return max(base_calc * aliq - ded, 0.0)
    return 0.0

def br_net(salary: float, dependentes: int, br_inss_tbl: Dict[str,Any], br_irrf_tbl: Dict[str,Any]):
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
    lines = [("Base Pay", salary, 0.0)]
    total_earn = salary
    fica = salary * 0.062
    medicare = salary * 0.0145
    total_ded = fica + medicare
    lines += [("FICA (Social Security)", 0.0, fica), ("Medicare", 0.0, medicare)]
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
        lines, te, td, net, fgts = br_net(salary, dependentes, br_inss_tbl, br_irrf_tbl)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": fgts}
    elif country == "Estados Unidos":
        lines, te, td, net = us_net(salary, state_code, state_rate)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    else:
        rates = (tables_ext or {}).get("TABLES", {}).get(country, {}).get("rates", {})
        if not rates:
            rates = TABLES_DEFAULT.get(country, {}).get("rates", {})
        lines, te, td, net = generic_net(salary, rates)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}

def calc_employer_cost(country: str, salary: float, tables_ext=None):
    months = (tables_ext or {}).get("REMUN_MONTHS", {}).get(country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    enc_list = (tables_ext or {}).get("EMPLOYER_COST", {}).get(country, EMPLOYER_COST_DEFAULT.get(country, []))
    benefits = COUNTRY_BENEFITS.get(country, {"ferias": False, "decimo": False})
    df = pd.DataFrame(enc_list)

    if not df.empty:
        df.rename(columns={"nome":"Encargo","percentual":"Percentual (%)","obs":"Observação","base":"Base"}, inplace=True)
        df["Incide Bônus"] = ["✅" if b else "❌" for b in df["bonus"]]
        cols = ["Encargo","Percentual (%)","Base","Incide Bônus","Observação"]
        if benefits.get("ferias", False):
            df["Incide Férias"] = ["✅" if b else "❌" for b in df["ferias"]]
            cols.insert(3, "Incide Férias")
        if benefits.get("decimo", False):
            df["Incide 13º"] = ["✅" if b else "❌" for b in df["decimo"]]
            insert_pos = 4 if benefits.get("ferias", False) else 3
            cols.insert(insert_pos, "Incide 13º")
        df = df[cols]

    perc_total = sum(e.get("percentual", 0.0) for e in enc_list)
    anual = salary * months * (1 + perc_total/100.0)
    mult = (anual / (salary * 12.0)) if salary > 0 else 0.0
    return anual, mult, df, months

# ======================== FETCH REMOTO (sem cache) =====================
def fetch_json_no_cache(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    return r.json()

def load_tables():
    # Sem cache: busca a cada acesso
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
    idioma = st.selectbox("🌐 Idioma / Language / Idioma", list(I18N.keys()), index=0, key="lang_select")
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
symbol     = COUNTRIES[country]["symbol"]
flag       = COUNTRIES[country]["flag"]
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
st.write(f"**{T['valid_from'] if 'valid_from' in T else 'Vigência'}:** {valid_from}")
st.write("---")

# ========================= CÁLCULO DE SALÁRIO ==========================
if menu == T["menu_calc"]:
    if country == "Brasil":
        c1, c2, c3, c4, c5 = st.columns([2,1,1.6,1.6,2.4])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        dependentes = c2.number_input(f"{T['dependents']}", min_value=0, value=0, step=1, key="dep_input")
        bonus_anual = c3.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        area = c4.selectbox(T["area"], ["Non Sales","Sales"], index=0, key="sti_area")
        level = c5.selectbox(T["level"], STI_LEVEL_OPTIONS[area], index=len(STI_LEVEL_OPTIONS[area])-1, key="sti_level")
        state_code, state_rate = None, None

    elif country == "Estados Unidos":
        c1, c2, c3, c4 = st.columns([2,1.4,1.2,1.4])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        state_code = c2.selectbox(f"{T['state']}", list(US_STATE_RATES.keys()), index=0, key="state_select_main")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input(f"{T['state_rate']}", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input")
        bonus_anual = c4.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        area = r1.selectbox(T["area"], ["Non Sales","Sales"], index=0, key="sti_area")
        level = r2.selectbox(T["level"], STI_LEVEL_OPTIONS[area], index=len(STI_LEVEL_OPTIONS[area])-1, key="sti_level")
        dependentes = 0

    else:
        c1, c2 = st.columns([2,1.6])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        bonus_anual = c2.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        r1, r2 = st.columns([1.2, 2.2])
        area = r1.selectbox(T["area"], ["Non Sales","Sales"], index=0, key="sti_area")
        level = r2.selectbox(T["level"], STI_LEVEL_OPTIONS[area], index=len(STI_LEVEL_OPTIONS[area])-1, key="sti_level")
        dependentes = 0
        state_code, state_rate = None, None

    # ---- Cálculo do país selecionado
    calc = calc_country_net(
        country, salario,
        state_code=state_code, state_rate=state_rate, dependentes=dependentes,
        tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL
    )

    # ---- Tabela de proventos/descontos
    df = pd.DataFrame(calc["lines"], columns=["Descrição", T["earnings"], T["deductions"]])
    df[T["earnings"]] = df[T["earnings"]].apply(lambda v: money_or_blank(v, symbol))
    df[T["deductions"]] = df[T["deductions"]].apply(lambda v: money_or_blank(v, symbol))
    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True)
    st.table(df)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Cards totais (linha única)
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(f"<div class='metric-card'><h4>🟩 {T['tot_earnings']}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card'><h4>🟥 {T['tot_deductions']}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card'><h4>🟦 {T['net']}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)

    if country == "Brasil":
        st.write("")
        st.markdown(f"**💼 {T['fgts_deposit']}:** {fmt_money(calc['fgts'], symbol)}")

           # ---------- Composição da Remuneração Total Anual ----------
    st.write("---")
    st.subheader(T["annual_comp_title"])

    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual

    # --- Validação do bônus vs STI range
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0
    pct_txt = f"{bonus_pct*100:.1f}%"
    if level == "Others":
        faixa_txt = f"≤ {(max_pct or 0)*100:.0f}%"
        dentro = bonus_pct <= (max_pct or 0)
    else:
        faixa_txt = f"{min_pct*100:.0f}% – {max_pct*100:.0f}%"
        dentro = (bonus_pct >= min_pct) and (bonus_pct <= max_pct)
    cor = "#1976d2" if dentro else "#d32f2f"
    status_txt = (
        "Dentro do range" if idioma == "Português"
        else "Within range" if idioma == "English"
        else "Dentro del rango"
    )

    # ---- Layout: blocos à esquerda (títulos) + valores ao lado + gráfico à direita
    col_left, col_values, col_chart = st.columns([2, 1, 1.6])

    # ================= LEFT COLUMN (titles + notes)
    with col_left:
        st.markdown("""
        <style>
        .annual-block {display:flex; flex-direction:column; gap:12px;}
        .annual-item {
          background:#fff; border-radius:12px; box-shadow:0 2px 6px rgba(0,0,0,0.06);
          padding:10px 14px;
        }
        .annual-item h4 {margin:0; font-size:13px; color:#0a3d62;}
        .annual-item .sti-note {margin-top:4px; font-size:12px;}
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div class='annual-block'>", unsafe_allow_html=True)

        # --- Salário anual
        st.markdown(
            f"<div class='annual-item'>"
            f"<h4>📅 {T['annual_salary']} — ({T['months_factor']}: {months})</h4>"
            f"</div>",
            unsafe_allow_html=True
        )

        # --- Bônus anual + STI ratio
        if level == "Others":
            sti_line = f"STI ratio do bônus: <strong>{pct_txt}</strong> — <strong>{status_txt}</strong> (≤ {(max_pct or 0)*100:.0f} %) — <em>{area} • {level}</em>"
        else:
            sti_line = f"STI ratio do bônus: <strong>{pct_txt}</strong> — <strong>{status_txt}</strong> ({faixa_txt}) — <em>{area} • {level}</em>"
        st.markdown(
            f"<div class='annual-item'>"
            f"<h4>🎯 {T['annual_bonus']}<br>"
            f"<span class='sti-note' style='color:{cor}'>{sti_line}</span></h4>"
            f"</div>",
            unsafe_allow_html=True
        )

        # --- Total
        st.markdown(
            f"<div class='annual-item'>"
            f"<h4>💼 {T['annual_total']}</h4>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ================= CENTER COLUMN (values only)
    with col_values:
        st.markdown("""
        <style>
        .value-block {display:flex; flex-direction:column; gap:12px;}
        .value-card {
          background:#fff; border-radius:12px; box-shadow:0 2px 6px rgba(0,0,0,0.06);
          text-align:center; padding:12px;
        }
        .value-card h3 {margin:0; font-size:18px; color:#0a3d62;}
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div class='value-block'>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-card'><h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-card'><h3>{fmt_money(bonus_anual, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value-card'><h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ================= RIGHT COLUMN (chart)
    with col_chart:
        chart_df = pd.DataFrame({
            "Componente": [T["annual_salary"], T["annual_bonus"]],
            "Valor": [salario_anual, bonus_anual]
        })
        base = (
            alt.Chart(chart_df)
            .transform_joinaggregate(Total='sum(Valor)')
            .transform_calculate(Percent='datum.Valor / datum.Total')
        )
        pie = (
            base.mark_arc(innerRadius=70, outerRadius=110)
            .encode(
                theta=alt.Theta('Valor:Q', stack=True),
                color=alt.Color('Componente:N',
                    legend=alt.Legend(orient='bottom', direction='horizontal', title=None,
                                      columns=2, labelLimit=300)
                ),
                tooltip=[
                    alt.Tooltip('Componente:N'),
                    alt.Tooltip('Valor:Q', format=",.2f"),
                    alt.Tooltip('Percent:Q', format=".1%")
                ]
            )
        )
        labels = (
            base.transform_filter(alt.datum.Percent >= 0.01)
            .mark_text(radius=85, fontWeight='bold', color='white')
            .encode(theta=alt.Theta('Valor:Q', stack=True), text=alt.Text('Percent:Q', format='.1%'))
        )
        chart = (
            alt.layer(pie, labels)
            .properties(width=360, height=300, title=T["pie_title"])
            .configure_legend(orient="bottom", padding=8)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart, use_container_width=True)


# =========================== REGRAS DE CONTRIBUIÇÕES ===================
elif menu == T["menu_rules"]:
    st.subheader(T["rules_expanded"])
    # Textos por idioma
    if idioma == "Português":
        st.markdown(f"""
### 🇧🇷 Brasil
**Empregado – INSS (progressivo)**  
Soma por faixas até o salário, com **teto de contribuição**.  
Faixas vigentes (ex.): 7,5% até 1.412; 9% até 2.666,68; 12% até 4.000,03; 14% até 8.157,41 (teto).  
**Exemplo**: salário **R$ 4.000,00** ⇒ INSS = 1.412×7,5% + (2.666,68−1.412)×9% + (4.000,03−2.666,68)×12% = **R$ {fmt_money(calc_inss_progressivo(4000, BR_INSS_TBL), 'R$')[3:]}** aprox.

**Empregado – IRRF (progressivo com dedução)**  
Base = salário bruto − INSS − **{fmt_money(BR_IRRF_TBL['deducao_dependente'],'R$')}** por dependente.  
Aplica-se a alíquota e dedução fixa da faixa.  
**Exemplo**: salário 4.000, 0 dep. ⇒ base = 4.000 − INSS. Sobre a base, aplicar tabela (7,5% a 27,5%) menos dedução fixa da faixa.

**Empregador**  
INSS Patronal (~20%), RAT (~2%), Sistema S (~5,8%), **FGTS 8%**. Em geral incidem em 13º e férias (meses ~ **13,33**).

---

### 🇺🇸 Estados Unidos
**Employee**  
- FICA: 6,2% (até wage base anual federal).  
- Medicare: 1,45% (sem teto).  
- State Tax: conforme estado (0%–~8%); configurável no app.

**Exemplo**: salário US$ 10.000 (estado 5%) ⇒ FICA 620, Medicare 145, State 500 ⇒ total **US$ 1.265**.

**Employer**  
Contribuições espelhadas (FICA/Medicare) + SUTA (média ~2%).

---

### 🇲🇽 México
**Empleado**: ISR (progressivo), IMSS ~5%, INFONAVIT ~5% (valores aproximados, variam por base e salário).  
**Empleador**: IMSS patronal ~7%, INFONAVIT ~5%. **Aguinaldo** ⇒ meses ~**12,5**.

---

### 🇨🇱 Chile
**Trabajador**: AFP ~10% (fundo), Salud ~7% (Isapre/Fonasa).  
**Empleador**: Seguro de cesantía ~2,4% (contrato indefinido).

---

### 🇦🇷 Argentina
**Empleado**: Jubilación 11%, Obra Social 3%, PAMI 3%.  
**Empleador**: Contribuciones ~18% (promédio setorial). **SAC (13º)** ⇒ meses **13**.

---

### 🇨🇴 Colômbia
**Trabajador**: Salud 4%, Pensión 4%.  
**Empleador**: Salud 8,5%, Pensión 12%. **Prima de servicios** ⇒ meses **13**.

---

### 🇨🇦 Canadá
**Employee**: CPP ~5,95%, EI ~1,63% (até limites).  
**Employer**: CPP ~5,95%, EI ~2,28%. Meses **12** (sem 13º).
""")
    elif idioma == "English":
        st.markdown(f"""
### 🇧🇷 Brazil
**Employee – Social Security (INSS, progressive):** tiered brackets with a contribution cap.  
**Example:** BRL 4,000 ⇒ apply each bracket rate up to salary (cap applies).

**Employee – Income Tax (IRRF):** Base = Gross − INSS − **{BR_IRRF_TBL['deducao_dependente']}** per dependent.  
Apply bracket rate minus fixed deduction.

**Employer:** Employer social security (~20%), risk (RAT ~2%), “System S” (~5.8%), **FGTS 8%**. Often applies to 13th salary and vacations (≈ **13.33 months**).

---

### 🇺🇸 United States
**Employee:** FICA 6.2%, Medicare 1.45%, State Tax per state (0–~8%).  
**Example:** US$10,000 in a 5% state ⇒ total deductions ≈ US$1,265.

**Employer:** Mirrors FICA/Medicare + SUTA (~2% avg).

---

### 🇲🇽 Mexico
**Employee:** ISR (progressive), IMSS ~5%, INFONAVIT ~5%.  
**Employer:** IMSS ~7%, INFONAVIT ~5%. Aguinaldo ⇒ months ≈ **12.5**.

---

### 🇨🇱 Chile
**Employee:** AFP ~10%, Health ~7%.  
**Employer:** Unemployment insurance ~2.4%.

---

### 🇦🇷 Argentina
**Employee:** Retirement 11%, Health 3%, PAMI 3%.  
**Employer:** Contributions ~18%. SAC (13th) ⇒ **13 months**.

---

### 🇨🇴 Colombia
**Employee:** Health 4%, Pension 4%.  
**Employer:** Health 8.5%, Pension 12%. “Prima de servicios” ⇒ **13 months**.

---

### 🇨🇦 Canada
**Employee:** CPP ~5.95%, EI ~1.63% (to limits).  
**Employer:** CPP ~5.95%, EI ~2.28%. Months **12**.
""")
    else:  # Español
        st.markdown(f"""
### 🇧🇷 Brasil
**Trabajador – INSS (progresivo):** por tramos con tope de contribución.  
**Ejemplo:** BRL 4.000 ⇒ aplicar cada tramo hasta el salario (con tope).

**Trabajador – IRRF:** Base = Bruto − INSS − **{BR_IRRF_TBL['deducao_dependente']}** por dependiente.  
Aplicar tasa del tramo menos deducción fija.

**Empleador:** Aportes ~20%, riesgo (RAT ~2%), “Sistema S” ~5,8%, **FGTS 8%**. Suele aplicar a 13º y vacaciones (≈ **13,33 meses**).

---

### 🇺🇸 Estados Unidos
**Empleado:** FICA 6,2%, Medicare 1,45%, impuesto estatal (0–~8%).  
**Ejemplo:** US$10.000 con 5% estatal ⇒ deducciones ≈ US$1.265.

**Empleador:** Aportes espejo (FICA/Medicare) + SUTA (~2% promedio).

---

### 🇲🇽 México
**Empleado:** ISR (progresivo), IMSS ~5%, INFONAVIT ~5%.  
**Empleador:** IMSS ~7%, INFONAVIT ~5%. Aguinaldo ⇒ **12,5 meses**.

---

### 🇨🇱 Chile
**Trabajador:** AFP ~10%, Salud ~7%.  
**Empleador:** Seguro de cesantía ~2,4%.

---

### 🇦🇷 Argentina
**Empleado:** Jubilación 11%, Obra Social 3%, PAMI 3%.  
**Empleador:** Contribuciones ~18%. SAC (13º) ⇒ **13 meses**.

---

### 🇨🇴 Colombia
**Trabajador:** Salud 4%, Pensión 4%.  
**Empleador:** Salud 8,5%, Pensión 12%. “Prima de servicios” ⇒ **13 meses**.

---

### 🇨🇦 Canadá
**Empleado:** CPP ~5,95%, EI ~1,63% (hasta topes).  
**Empleador:** CPP ~5,95%, EI ~2,28%. Meses **12**.
""")

# =========================== REGRAS DE CÁLCULO DO STI ==================
elif menu == T["menu_rules_sti"]:
    st.markdown("#### Non Sales")
    df_ns = pd.DataFrame([
        {"Career Level":"CEO","STI %":"100%"},
        {"Career Level":"Members of the GEB","STI %":"50–80%"},
        {"Career Level":"Executive Manager","STI %":"45–70%"},
        {"Career Level":"Senior Group Manager","STI %":"40–60%"},
        {"Career Level":"Group Manager","STI %":"30–50%"},
        {"Career Level":"Lead Expert / Program Manager","STI %":"25–40%"},
        {"Career Level":"Senior Manager","STI %":"20–40%"},
        {"Career Level":"Senior Expert / Senior Project Manager","STI %":"15–35%"},
        {"Career Level":"Manager / Selected Expert / Project Manager","STI %":"10–30%"},
        {"Career Level":"Others","STI %":"≤ 10%"},
    ])
    st.table(df_ns)

    st.markdown("#### Sales")
    df_s = pd.DataFrame([
        {"Career Level":"Executive Manager / Senior Group Manager","STI %":"45–70%"},
        {"Career Level":"Group Manager / Lead Sales Manager","STI %":"35–50%"},
        {"Career Level":"Senior Manager / Senior Sales Manager","STI %":"25–45%"},
        {"Career Level":"Manager / Selected Sales Manager","STI %":"20–35%"},
        {"Career Level":"Others","STI %":"≤ 15%"},
    ])
    st.table(df_s)

# ========================= CUSTO DO EMPREGADOR ========================
else:
    salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    anual, mult, df_cost, months = calc_employer_cost(country, salario, tables_ext=COUNTRY_TABLES)
    st.markdown(f"**{T['employer_cost_total']}:** {fmt_money(anual, symbol)}  \n**Equivalente:** {mult:.3f} × (12 meses)  \n**{T['months_factor']}:** {months}")
    if not df_cost.empty:
        st.dataframe(df_cost, use_container_width=True)
    else:
        st.info("Sem encargos configurados para este país (no JSON).")
