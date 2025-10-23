# -------------------------------------------------------------
# 📄 Cálculo de Salário Internacional – v2025.21
# Ajustes: sidebar legível, State Tax visível (EUA), regras detalhadas,
# custo do empregador adaptado por país, remoção do menu "Tabelas",
# zeros como branco na tabela, FGTS só BR fora dos totais.
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Cálculo de Salário Internacional", layout="wide")

# ========================= CSS ==============================
st.markdown("""
<style>
/* Base */
body { font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e2e6ea; margin:16px 0; }

/* Sidebar */
section[data-testid="stSidebar"] { background:#0a3d62 !important; }
section[data-testid="stSidebar"] * { color:#ffffff !important; }
section[data-testid="stSidebar"] .stSelectbox > div, 
section[data-testid="stSidebar"] .stNumberInput > div,
section[data-testid="stSidebar"] .stTextInput > div {
    background:#ffffff !important; border-radius:8px; padding:2px 6px;
}
section[data-testid="stSidebar"] input, 
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] .st-bb { color:#0a0a0a !important; }
.sidebar-title { font-weight:700; margin:8px 0 6px; color:#ffffff; }
.sidebar-help { color:#cfe3ff !important; font-size:13px; margin-bottom:8px; }

/* Cards */
.metric-card { background:#fff; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08); padding:16px; text-align:center; }
.metric-card h4 { margin:0; font-size:15px; color:#0a3d62; }
.metric-card h3 { margin:4px 0 0; color:#0a3d62; }

/* Tabela demonstrativo */
.table-wrap { background:#fff; border:1px solid #d0d7de; border-radius:8px; overflow:hidden; }
.demo-table { width:100%; border-collapse:collapse; }
.demo-table th, .demo-table td { padding:10px 12px; border-bottom:1px solid #e6e9ef; }
.demo-table th { background:#eff3f9; color:#0a3d62; text-align:left; }
.demo-table tr:nth-child(even) { background:#f4f8fd; }

/* Bandeira + título */
.country-header { display:flex; align-items:center; gap:10px; }
.country-flag { font-size:28px; }
.country-title { font-size:24px; font-weight:700; color:#0a3d62; }

.small { color:#445; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ========================= I18N =============================
I18N = {
    "Português": {
        "menu_calc": "Cálculo de Salário",
        "menu_rules": "Regras de Cálculo",
        "menu_cost": "Custo do Empregador",
        "title_calc": "Cálculo de Salário – {pais}",
        "title_rules": "Regras de Cálculo – {pais}",
        "title_cost": "Custo do Empregador – {pais}",
        "country": "País",
        "salary": "Salário Bruto",
        "state": "Estado (EUA)",
        "earnings": "Proventos",
        "deductions": "Descontos",
        "net": "Salário Líquido",
        "fgts_deposit": "Depósito FGTS",
        "tot_earnings": "Total de Proventos",
        "tot_deductions": "Total de Descontos",
        "valid_from": "Vigência",
        "rules_emp": "Parte do Empregado",
        "rules_er": "Parte do Empregador"
    },
    "English": {
        "menu_calc": "Net Salary Calculation",
        "menu_rules": "Calculation Rules",
        "menu_cost": "Employer Cost",
        "title_calc": "Net Salary Calculation – {pais}",
        "title_rules": "Calculation Rules – {pais}",
        "title_cost": "Employer Cost – {pais}",
        "country": "Country",
        "salary": "Gross Salary",
        "state": "State (USA)",
        "earnings": "Earnings",
        "deductions": "Deductions",
        "net": "Net Salary",
        "fgts_deposit": "FGTS Deposit",
        "tot_earnings": "Total Earnings",
        "tot_deductions": "Total Deductions",
        "valid_from": "Valid from",
        "rules_emp": "Employee Portion",
        "rules_er": "Employer Portion"
    },
    "Español": {
        "menu_calc": "Cálculo de Salario",
        "menu_rules": "Reglas de Cálculo",
        "menu_cost": "Costo del Empleador",
        "title_calc": "Cálculo de Salario – {pais}",
        "title_rules": "Reglas de Cálculo – {pais}",
        "title_cost": "Costo del Empleador – {pais}",
        "country": "País",
        "salary": "Salario Bruto",
        "state": "Estado (EE. UU.)",
        "earnings": "Ingresos",
        "deductions": "Descuentos",
        "net": "Salario Neto",
        "fgts_deposit": "Depósito de FGTS",
        "tot_earnings": "Total Ingresos",
        "tot_deductions": "Total Descuentos",
        "valid_from": "Vigencia",
        "rules_emp": "Parte del Trabajador",
        "rules_er": "Parte del Empleador"
    }
}

# ================== Países, moedas, bandeiras =================
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

# ================== Tabelas simplificadas =====================
def br_inss_2025(sal):
    faixas = [
        (0.00, 1412.00, 0.075),
        (1412.01, 2666.68, 0.09),
        (2666.69, 4000.03, 0.12),
        (4000.04, 8157.41, 0.14)
    ]
    contrib = 0.0
    for ini, fim, aliq in faixas:
        if sal > ini:
            contrib += (min(sal, fim) - ini) * aliq
    return min(max(contrib, 0.0), 1146.68)

def br_irrf_2025(base):
    faixas = [
        (0.00, 2259.20, 0.00, 0.00),
        (2259.21, 2826.65, 0.075, 169.44),
        (2826.66, 3751.05, 0.15, 381.44),
        (3751.06, 4664.68, 0.225, 662.77),
        (4664.69, 9e9, 0.275, 896.00),
    ]
    for ini, fim, aliq, ded in faixas:
        if base >= ini and base <= fim:
            return max(base * aliq - ded, 0.0)
    return 0.0

TABLES = {
    "México": {"rates": {"ISR": 0.15, "IMSS": 0.05, "INFONAVIT": 0.05}},
    "Chile": {"rates": {"AFP": 0.10, "Saúde": 0.07}},
    "Argentina": {"rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}},
    "Colômbia": {"rates": {"Saúde": 0.04, "Pensão": 0.04}},
    "Estados Unidos": {
        "rates": {"FICA": 0.062, "Medicare": 0.0145},
        "states": {"No State Tax": 0.00, "CA": 0.06, "NY": 0.064, "TX": 0.00, "FL": 0.00, "WA": 0.00, "IL": 0.0495, "MA": 0.05}
    },
    "Canadá": {"rates": {"CPP": 0.0595, "EI": 0.0163, "Income Tax": 0.15}}
}

EMPLOYER_COST = {
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
        {"nome":"Seguro Desemprego","percentual":2.4,"base":"Salário","ferias":True,"decimo":False,"bonus":True,"obs":"Empregador"},
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

EMPLOYER_FACTOR = {"Brasil":13.33,"México":12.50,"Chile":12.00,"Argentina":13.00,"Colômbia":13.00,"Estados Unidos":12.00,"Canadá":12.00}

# ========================== Helpers ==========================
def fmt_money(v, sym):
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v, sym):
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def calc_country_net(country, salary, state_code=None):
    lines = []
    total_earn = 0.0
    total_ded = 0.0
    fgts_value = 0.0

    if country == "Brasil":
        lines.append(("Salário Base", salary, 0.0)); total_earn += salary
        inss = br_inss_2025(salary); total_ded += inss; lines.append(("INSS", 0.0, inss))
        base_ir = max(salary - inss, 0.0); irrf = br_irrf_2025(base_ir); total_ded += irrf; lines.append(("IRRF", 0.0, irrf))
        fgts_value = salary * 0.08

    elif country == "México":
        r = TABLES["México"]["rates"]
        lines.append(("Salario Base", salary, 0.0)); total_earn += salary
        for k in ["ISR","IMSS","INFONAVIT"]:
            v = salary * r[k]; total_ded += v; lines.append((k, 0.0, v))

    elif country == "Chile":
        r = TABLES["Chile"]["rates"]
        lines.append(("Sueldo Base", salary, 0.0)); total_earn += salary
        for k in ["AFP","Saúde"]:
            v = salary * r[k]; total_ded += v; lines.append((k, 0.0, v))

    elif country == "Argentina":
        r = TABLES["Argentina"]["rates"]
        lines.append(("Salario Base", salary, 0.0)); total_earn += salary
        for k in ["Jubilación","Obra Social","PAMI"]:
            v = salary * r[k]; total_ded += v; lines.append((k, 0.0, v))

    elif country == "Colômbia":
        r = TABLES["Colômbia"]["rates"]
        lines.append(("Salario Base", salary, 0.0)); total_earn += salary
        for k in ["Saúde","Pensão"]:
            v = salary * r[k]; total_ded += v; lines.append((k, 0.0, v))

    elif country == "Estados Unidos":
        r = TABLES["Estados Unidos"]["rates"]; states = TABLES["Estados Unidos"]["states"]
        st_rate = states.get(state_code or "No State Tax", 0.0)
        lines.append(("Base Pay", salary, 0.0)); total_earn += salary
        fica = salary * r["FICA"]; total_ded += fica; lines.append(("FICA (Social Security)", 0.0, fica))
        medicare = salary * r["Medicare"]; total_ded += medicare; lines.append(("Medicare", 0.0, medicare))
        if st_rate > 0:
            sttax = salary * st_rate; total_ded += sttax; lines.append((f"State Tax ({state_code})", 0.0, sttax))

    elif country == "Canadá":
        r = TABLES["Canadá"]["rates"]
        lines.append(("Base Pay", salary, 0.0)); total_earn += salary
        for k in ["CPP","EI","Income Tax"]:
            v = salary * r[k]; total_ded += v; lines.append((k, 0.0, v))

    net = total_earn - total_ded
    return {"lines": lines, "total_earn": total_earn, "total_ded": total_ded, "net": net, "fgts": fgts_value}

def calc_employer_cost(country, salary):
    enc = EMPLOYER_COST.get(country, [])
    factor = EMPLOYER_FACTOR.get(country, 12.0)
    perc_total = sum(e["percentual"] for e in enc)
    anual = salary * factor * (1 + perc_total/100.0)
    mensal_equiv = anual / 12.0
    mult = anual / (salary * 12.0) if salary > 0 else 0.0
    return anual, mensal_equiv, mult, enc, factor

def render_rules(country, T):
    st.markdown(f"### {T['rules_emp']}")
    if country == "Brasil":
        st.markdown("- **INSS (empregado)**: progressivo até o teto (R$ 8.157,41). A contribuição é a soma por faixa, limitada a ~R$ 1.146,68.")
        st.markdown("- **IRRF (empregado)**: base após INSS. Faixas 2025 com alíquotas e deduções por faixa.")
        st.markdown(f"- **{T['fgts_deposit']}**: não é desconto; é depósito do empregador (8%).")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- **INSS Patronal 20%**, **RAT 2%**, **Sistema S 5,8%**, **FGTS 8%** sobre o salário (incidem em férias e 13º).")
    elif country == "Estados Unidos":
        st.markdown("- **FICA/Empregado**: 6,2% até o wage base anual; **Medicare** 1,45% (sem teto).")
        st.markdown("- **State Tax**: varia por estado (ex.: CA 6%, NY 6,4%, FL/TX 0%).")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- **Social Security (ER) 6,2%**, **Medicare (ER) 1,45%**, **SUTA** médio ~2%.")
    elif country == "México":
        st.markdown("- **ISR** renda, **IMSS** seguridade, **INFONAVIT** habitação (alíquotas variam por base).")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- **IMSS Patronal** ~7%, **INFONAVIT** ~5% (médias).")
    elif country == "Chile":
        st.markdown("- **AFP** 10% (aposentadoria), **Saúde** 7%.")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- **Seguro desemprego** ~2,4% para empregador.")
    elif country == "Argentina":
        st.markdown("- **Jubilación** 11%, **Obra Social** 3%, **PAMI** 3%.")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- Contribuições patronais médias ~18%.")
    elif country == "Colômbia":
        st.markdown("- **Saúde** 4% e **Pensão** 4% (empregado).")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- **Saúde (ER)** ~8,5% e **Pensão (ER)** ~12%.")
    elif country == "Canadá":
        st.markdown("- **CPP** ~5,95%, **EI** ~1,63%, **Income Tax** progressivo por província.")
        st.markdown("")
        st.markdown(f"### {T['rules_er']}")
        st.markdown("- **CPP (ER)** ~5,95%, **EI (ER)** ~2,28%.")
    else:
        st.info("—")

# ========================= Sidebar ===========================
idioma = st.sidebar.selectbox("🌐 Idioma / Language / Idioma", list(I18N.keys()), index=0, key="lang_select")
T = I18N[idioma]

st.sidebar.markdown(f"### {T['country']}")
country = st.sidebar.selectbox(" ", list(COUNTRIES.keys()), index=0, key="country_select")
symbol = COUNTRIES[country]["symbol"]; flag = COUNTRIES[country]["flag"]; valid_from = COUNTRIES[country]["valid_from"]

st.sidebar.markdown("### Menu")
menu = st.sidebar.radio(" ", [T["menu_calc"], T["menu_rules"], T["menu_cost"]], index=0, key="menu_radio")

# State Tax (sempre visível quando EUA)
state_code = None
if country == "Estados Unidos":
    st.sidebar.markdown(f"### {T['state']}")
    state_code = st.sidebar.selectbox(" ", list(TABLES["Estados Unidos"]["states"].keys()), index=0, key="state_select")

# ================== Título dinâmico ==========================
if menu == T["menu_calc"]:
    title = T["title_calc"].format(pais=country)
elif menu == T["menu_rules"]:
    title = T["title_rules"].format(pais=country)
else:
    title = T["title_cost"].format(pais=country)

st.markdown(f"<div class='country-header'><div class='country-flag'>{flag}</div><div class='country-title'>{title}</div></div>", unsafe_allow_html=True)
st.write(f"**{T['valid_from']}:** {valid_from}")
st.write("---")

# ================= Seção: Cálculo de Salário =================
if menu == T["menu_calc"]:
    salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")

    calc = calc_country_net(country, salario, state_code=state_code)

    df = pd.DataFrame(calc["lines"], columns=["Descrição", T["earnings"], T["deductions"]])
    df[T["earnings"]] = df[T["earnings"]].apply(lambda v: money_or_blank(v, symbol))
    df[T["deductions"]] = df[T["deductions"]].apply(lambda v: money_or_blank(v, symbol))

    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True)
    st.table(df)
    st.markdown("</div>", unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(f"<div class='metric-card'><h4>🟩 {T['tot_earnings']}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card'><h4>🟥 {T['tot_deductions']}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card'><h4>🟦 {T['net']}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)

    if country == "Brasil":
        st.write("")
        st.markdown(f"**💼 {T['fgts_deposit']}:** {fmt_money(calc['fgts'], symbol)}")

# ================= Seção: Regras de Cálculo ==================
elif menu == T["menu_rules"]:
    render_rules(country, T)

# =============== Seção: Custo do Empregador ==================
else:
    salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    anual, mensal_equiv, mult, enc, factor = calc_employer_cost(country, salario)

    st.markdown(f"**{T['net']} (equivalência 12 meses)**: {fmt_money(salario*factor, symbol)}")
    st.markdown(f"**{T['employer_cost_total']}:** {fmt_money(anual, symbol)}  \n**Equivalente:** {mult:.3f} × (12 meses)  \n**Fator anual usado:** {factor} salários/ano")

    df = pd.DataFrame(enc)
    benefits = COUNTRY_BENEFITS.get(country, {"ferias": False, "decimo": False})
    df["Incide Férias"] = ["✅" if (row and benefits["ferias"]) else ("—" if not benefits["ferias"] else "❌") for row in df["ferias"]]
    if benefits["decimo"]:
        df["Incide 13º"] = ["✅" if row else "❌" for row in df["decimo"]]
    df["Incide Bônus"] = ["✅" if row else "❌" for row in df["bonus"]]
    df.rename(columns={"nome":"Encargo","percentual":"Percentual (%)","obs":"Observação","base":"Base"}, inplace=True)

    cols_show = ["Encargo","Percentual (%)","Base","Incide Bônus","Observação"]
    if benefits["ferias"]:
        cols_show.insert(3, "Incide Férias")
    if benefits["decimo"]:
        cols_show.insert(4, "Incide 13º")

    st.dataframe(df[cols_show], use_container_width=True)
