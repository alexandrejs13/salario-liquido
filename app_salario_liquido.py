# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.44)
# -------------------------------------------------------------
import streamlit as st
import pandas as pd
import altair as alt
import requests
from typing import Dict, Any, Tuple, Optional

st.set_page_config(
    page_title="Simulador de Salário Líquido e Custo do Empregador",
    layout="wide",
)

# ======================== ENDPOINTS REMOTOS =========================
RAW_BASE = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main"
URL_US_STATES      = f"{RAW_BASE}/us_state_tax_rates.json"
URL_COUNTRY_TABLES = f"{RAW_BASE}/country_tables.json"
URL_BR_INSS        = f"{RAW_BASE}/br_inss.json"
URL_BR_IRRF        = f"{RAW_BASE}/br_irrf.json"

# ============================== CSS (tema plano/moderninho) ================================
st.markdown("""
<style>
html, body { font-family:'Segoe UI', Helvetica, Arial, sans-serif; background:#f8fafc; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e0e6ed; margin:16px 0; }

/* Sidebar */
section[data-testid="stSidebar"]{ background:#0a3d62 !important; padding-top:8px; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label { color:#ffffff !important; }

/* Inputs na sidebar: texto escuro */
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox input,
section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{
  color:#0b1f33 !important; background:#fff !important;
}

/* Cards padrão */
.metric-card {
  background:#ffffff;
  border:1px solid #dfe4ea;
  border-radius:10px;
  padding:12px;
  text-align:center;
  box-shadow:none;
}
.metric-card h4 { margin:0; font-size:13px; color:#0a3d62; font-weight:600; }
.metric-card h3 { margin:4px 0 0; font-size:18px; color:#0a3d62; font-weight:700; }

/* Tabela estilo box */
.table-wrap { background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }

/* Cabeçalho país */
.country-header{ display:flex; align-items:center; gap:10px; }
.country-flag{ font-size:28px; }
.country-title{ font-size:24px; font-weight:700; color:#0a3d62; }

/* Cards compactos (composição anual) — mesmo estilo/altura dos cards de totais */
.metric-card.compact{ min-height:100px; }

/* Nota do STI */
.sti-note{ margin-top:6px; font-size:12px; }

/* Responsivo: em telas estreitas, gráficos em largura total */
@media (max-width: 768px){
  .country-title{ font-size:20px; }
}
</style>
""", unsafe_allow_html=True)

# ============================== I18N (mínimo necessário) ================================
I18N = {
    "Português": {
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
        "menu": "Menu",
        "choose_country": "Selecione o país",
        "choose_menu": "Escolha uma opção",
        "area": "Área (STI)",
        "level": "Career Level (STI)",
    }
}

# ====================== Países / Moedas / Bandeiras =====================
COUNTRIES = {
    "Brasil": {"symbol": "R$", "flag": "🇧🇷", "valid_from": "2025-01-01"},
    "México": {"symbol": "MX$", "flag": "🇲🇽", "valid_from": "2025-01-01"},
    "Chile": {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01"},
    "Argentina": {"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01"},
    "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01"},
    "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01"},
    "Canadá": {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01"},
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

# ========================== Fallbacks locais ============================
US_STATE_RATES_DEFAULT = {
    "No State Tax": 0.00, "AK": 0.00, "FL": 0.00, "NV": 0.00, "SD": 0.00, "TN": 0.00, "TX": 0.00,
    "WA": 0.00, "WY": 0.00, "NH": 0.00, "AL": 0.05, "AR": 0.049, "AZ": 0.025, "CA": 0.06,
    "CO": 0.044, "CT": 0.05, "DC": 0.06, "DE": 0.055, "GA": 0.054, "HI": 0.08, "IA": 0.05,
    "ID": 0.055, "IL": 0.0495, "IN": 0.0323, "KS": 0.052, "KY": 0.045, "LA": 0.045, "MA": 0.05,
    "MD": 0.047, "ME": 0.058, "MI": 0.0425, "MN": 0.058, "MO": 0.045, "MS": 0.05, "MT": 0.054,
    "NC": 0.045, "ND": 0.02, "NE": 0.05, "NJ": 0.055, "NM": 0.049, "NY": 0.064, "OH": 0.030,
    "OK": 0.0475, "OR": 0.08, "PA": 0.0307, "RI": 0.0475, "SC": 0.052, "UT": 0.0485, "VA": 0.05,
    "VT": 0.06, "WI": 0.053, "WV": 0.05
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
    "Chile": [{"nome":"Seguro Desemprego","percentual":2.4,"base":"Salário","ferias":True,"decimo":False,"bonus":True,"obs":"Empregador"}],
    "Argentina": [{"nome":"Contribuições Patronais","percentual":18.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Média setores"}],
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
        "Others": (0.0, 0.10),  # ≤ 10%
    },
    "Sales": {
        "Executive Manager / Senior Group Manager": (0.45, 0.70),
        "Group Manager / Lead Sales Manager": (0.35, 0.50),
        "Senior Manager / Senior Sales Manager": (0.25, 0.45),
        "Manager / Selected Sales Manager": (0.20, 0.35),
        "Others": (0.0, 0.15),  # ≤ 15%
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

def get_sti_range(area: str, level: str) -> Tuple[float, Optional[float]]:
    return STI_RANGES.get(area, {}).get(level, (0.0, None))

# -------- BR: INSS/IRRF ----------
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
    teto = inss_tbl.get("teto_contribuicao")
    if teto is not None:
        contrib = min(contrib, float(teto))
    return max(contrib, 0.0)

def calc_irrf(base: float, dep: int, irrf_tbl: Dict[str, Any]) -> float:
    ded_dep = float(irrf_tbl.get("deducao_dependente", 0.0))
    base_calc = max(base - ded_dep * max(int(dep), 0), 0.0)
    for faixa in irrf_tbl.get("faixas", []):
        if base_calc <= float(faixa["ate"]):
            aliq = float(faixa["aliquota"]); ded = float(faixa.get("deducao", 0.0))
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
    fgts_value = salary * 0.08  # depósito patronal (informativo)
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

def us_net(salary: float, state_code: Optional[str], state_rate: Optional[float]):
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
            df["Incide Férias"] = ["✅" if b else "❌" for b in df["ferias"]]; cols.insert(3, "Incide Férias")
        if benefits.get("decimo", False):
            df["Incide 13º"] = ["✅" if b else "❌" for b in df["decimo"]]
            insert_pos = 4 if benefits.get("ferias", False) else 3
            cols.insert(insert_pos, "Incide 13º")
        df = df[cols]
    perc_total = sum(e.get("percentual", 0.0) for e in enc_list)
    anual = salary * months * (1 + perc_total/100.0)
    mult = (anual / (salary * 12.0)) if salary > 0 else 0.0
    return anual, mult, df, months

# ======================== Carregar tabelas (SEM cache) =======================
def fetch_json_now(url: str) -> Dict[str, Any]:
    try:
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def load_tables_no_cache():
    us_states = fetch_json_now(URL_US_STATES) or US_STATE_RATES_DEFAULT
    country_tables = fetch_json_now(URL_COUNTRY_TABLES) or {
        "TABLES": TABLES_DEFAULT,
        "EMPLOYER_COST": EMPLOYER_COST_DEFAULT,
        "REMUN_MONTHS": REMUN_MONTHS_DEFAULT,
    }
    br_inss = fetch_json_now(URL_BR_INSS) or BR_INSS_DEFAULT
    br_irrf = fetch_json_now(URL_BR_IRRF) or BR_IRRF_DEFAULT
    return us_states, country_tables, br_inss, br_irrf

US_STATE_RATES, COUNTRY_TABLES, BR_INSS_TBL, BR_IRRF_TBL = load_tables_no_cache()

# ============================== SIDEBAR ===============================
with st.sidebar:
    idioma = st.selectbox("🌐 Idioma / Language", list(I18N.keys()), index=0)
    T = I18N[idioma]
    st.markdown(f"### {T['country']}")
    country = st.selectbox(T["choose_country"], list(COUNTRIES.keys()), index=0)
    st.markdown(f"### {T['menu']}")
    menu = st.radio(T["choose_menu"], [T["menu_calc"], T["menu_rules"], T["menu_rules_sti"], T["menu_cost"]], index=0)

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
st.write(f"**{T['valid_from']}:** {valid_from}")
st.write("---")

# ========================= CÁLCULO DE SALÁRIO ==========================
if menu == T["menu_calc"]:
    if country == "Brasil":
        c1, c2, c3, c4, c5 = st.columns([2,1,1.6,1.6,2.0])
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

    # --- Cálculo líquido mensal (por país)
    calc = calc_country_net(
        country, salario,
        state_code=state_code, state_rate=state_rate, dependentes=dependentes,
        tables_ext=COUNTRY_TABLES, br_inss_tbl=BR_INSS_TBL, br_irrf_tbl=BR_IRRF_TBL
    )

    # Demonstrativo (tabela)
    df = pd.DataFrame(calc["lines"], columns=["Descrição", T["earnings"], T["deductions"]])
    df[T["earnings"]] = df[T["earnings"]].apply(lambda v: money_or_blank(v, symbol))
    df[T["deductions"]] = df[T["deductions"]].apply(lambda v: money_or_blank(v, symbol))
    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True)
    st.table(df)
    st.markdown("</div>", unsafe_allow_html=True)

    # Totais (cards horizontais)
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

    # Validação do bônus vs STI range (inclui os limites “Others” com ≤)
    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0

    if max_pct is not None:
        dentro = bonus_pct <= max_pct
        faixa_txt = f"≤ {max_pct*100:.0f}%"
    else:
        dentro = (bonus_pct >= min_pct)
        faixa_txt = f"≥ {min_pct*100:.0f}%"

    cor = "#1976d2" if dentro else "#d32f2f"
    status_txt = "Dentro do range" if dentro else "Fora do range"

    # Cards horizontais (mesmo estilo/altura dos cards de totais)
    a1, a2, a3 = st.columns(3)
    a1.markdown(
        f"<div class='metric-card compact'><h4>📅 {T['annual_salary']} — ({T['months_factor']}: {months})</h4>"
        f"<h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True
    )
    a2.markdown(
        f"<div class='metric-card compact'><h4>🎯 {T['annual_bonus']}</h4>"
        f"<h3>{fmt_money(bonus_anual, symbol)}</h3>"
        f"<div class='sti-note' style='color:{cor}'>"
        f"STI ratio do bônus: <strong>{bonus_pct*100:.1f}%</strong> — "
        f"<strong>{status_txt}</strong> ({faixa_txt}) — <em>{area} • {level}</em>"
        f"</div></div>", unsafe_allow_html=True
    )
    a3.markdown(
        f"<div class='metric-card compact'><h4>💼 {T['annual_total']}</h4>"
        f"<h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True
    )

    # Gráfico pizza abaixo dos cards (legenda embaixo, sem sobreposição)
    st.write("")
    chart_df = pd.DataFrame({"Componente": [T["annual_salary"], T["annual_bonus"]], "Valor": [salario_anual, bonus_anual]})
    base = alt.Chart(chart_df).transform_joinaggregate(Total="sum(Valor)").transform_calculate(Percent="datum.Valor / datum.Total")
    pie = base.mark_arc(innerRadius=70, outerRadius=120).encode(
        theta=alt.Theta("Valor:Q", stack=True),
        color=alt.Color("Componente:N", legend=alt.Legend(orient="bottom", direction="horizontal", title=None)),
        tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f"), alt.Tooltip("Percent:Q", format=".1%")]
    )
    labels = base.transform_filter(alt.datum.Percent >= 0.01).mark_text(radius=95, fontWeight="bold", color="white").encode(
        theta=alt.Theta("Valor:Q", stack=True),
        text=alt.Text("Percent:Q", format=".1%")
    )
    chart = alt.layer(pie, labels).properties(width="container", height=340, title=T["pie_title"]).configure_legend(orient="bottom", padding=12)
    st.altair_chart(chart, use_container_width=True)

# =========================== REGRAS DE CONTRIBUIÇÕES ===================
elif menu == T["menu_rules"]:
    st.markdown(f"### {T['rules_emp']}")
    if country == "Brasil":
        st.markdown("""
**Empregado (Brasil)**
- **INSS (progressivo)** por faixas, com **teto de contribuição**.
- **IRRF**: base = **salário − INSS − dedução por dependentes**; aplica **alíquota** e **dedução fixa** da faixa.
- **FGTS**: depósito do empregador (8%); não é desconto do empregado.
""")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empregador (Brasil)**
- **INSS Patronal, RAT, Sistema S** sobre a folha.
- **FGTS (8%)**; normalmente incide sobre **férias** e **13º** (meses ~ **13,33**).
""")
    elif country == "Estados Unidos":
        st.markdown("""
**Empregado (EUA)**
- **FICA** 6,2% (até wage base) e **Medicare** 1,45%.
- **State Tax**: conforme estado (ajustável).
""")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empregador (EUA)**
- **Social Security (ER)** 6,2%, **Medicare (ER)** 1,45%, **SUTA** ~2%.
- Meses: **12**.
""")
    else:
        st.info("Resumo de regras disponível conforme dados configurados para cada país.")

# =========================== REGRAS DE CÁLCULO DO STI ==================
elif menu == T["menu_rules_sti"]:
    st.markdown("#### Non Sales")
    df_ns = pd.DataFrame([
        {"Career Level":"CEO","STI ratio (% do salário anual)":"100%"},
        {"Career Level":"Members of the GEB","STI ratio (% do salário anual)":"50–80%"},
        {"Career Level":"Executive Manager","STI ratio (% do salário anual)":"45–70%"},
        {"Career Level":"Senior Group Manager","STI ratio (% do salário anual)":"40–60%"},
        {"Career Level":"Group Manager","STI ratio (% do salário anual)":"30–50%"},
        {"Career Level":"Lead Expert / Program Manager","STI ratio (% do salário anual)":"25–40%"},
        {"Career Level":"Senior Manager","STI ratio (% do salário anual)":"20–40%"},
        {"Career Level":"Senior Expert / Senior Project Manager","STI ratio (% do salário anual)":"15–35%"},
        {"Career Level":"Manager / Selected Expert / Project Manager","STI ratio (% do salário anual)":"10–30%"},
        {"Career Level":"Others","STI ratio (% do salário anual)":"≤ 10%"},
    ])
    st.dataframe(df_ns, use_container_width=True)

    st.markdown("#### Sales")
    df_s = pd.DataFrame([
        {"Career Level":"Executive Manager / Senior Group Manager","STI ratio (% do salário anual)":"45–70%"},
        {"Career Level":"Group Manager / Lead Sales Manager","STI ratio (% do salário anual)":"35–50%"},
        {"Career Level":"Senior Manager / Senior Sales Manager","STI ratio (% do salário anual)":"25–45%"},
        {"Career Level":"Manager / Selected Sales Manager","STI ratio (% do salário anual)":"20–35%"},
        {"Career Level":"Others","STI ratio (% do salário anual)":"≤ 15%"},
    ])
    st.dataframe(df_s, use_container_width=True)

# ========================= CUSTO DO EMPREGADOR ========================
else:
    salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    anual, mult, df_cost, months = calc_employer_cost(country, salario, tables_ext=COUNTRY_TABLES)
    st.markdown(f"**{T['employer_cost_total']}:** {fmt_money(anual, symbol)}  \n**Equivalente:** {mult:.3f} × (12 meses)  \n**{T['months_factor']}:** {months}")
    if not df_cost.empty:
        st.dataframe(df_cost, use_container_width=True)
    else:
        st.info("Sem encargos configurados para este país (no JSON).")
