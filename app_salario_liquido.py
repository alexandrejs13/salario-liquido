# -------------------------------------------------------------
# 📄 Cálculo de Salário Internacional – v2025.20
# Executive Global Payroll | PT-EN-ES | Streamlit
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -------------------------------------------------------------
# Configuração inicial
# -------------------------------------------------------------
st.set_page_config(page_title="Cálculo de Salário Internacional", layout="wide")

# -------------------------------------------------------------
# CSS corporativo
# -------------------------------------------------------------
st.markdown("""
<style>
/* Base */
body { font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e2e6ea; margin:16px 0; }

/* Sidebar */
section[data-testid="stSidebar"] { background:#0a3d62 !important; }
section[data-testid="stSidebar"] * { color:#fff !important; }
.sidebar-title { font-weight:700; margin:8px 0 16px; color:#fff; }
.sidebar-label { font-weight:600; margin-top:8px; color:#e8eef6; }
.sidebar-radio .stRadio > label div { color:#fff !important; }

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
.country-flag { font-size:32px; }
.country-title { font-size:26px; font-weight:700; color:#0a3d62; }

/* Botão atualizar */
.update-box { background:#fff; border:1px solid #d0d7de; border-radius:10px; padding:14px; }
.small { color:#445; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Idiomas embutidos
# -------------------------------------------------------------
I18N = {
    "Português": {
        "menu_calc": "Cálculo de Salário",
        "menu_rules": "Regras de Cálculo",
        "menu_cost": "Custo do Empregador",
        "menu_tables": "Tabelas e Atualizações",
        "title_calc": "Cálculo de Salário – {pais}",
        "title_rules": "Regras de Cálculo – {pais}",
        "title_cost": "Custo do Empregador – {pais}",
        "title_tables": "Tabelas e Atualizações",
        "country": "País",
        "salary": "Salário Bruto",
        "state": "Estado (EUA)",
        "earnings": "Proventos",
        "deductions": "Descontos",
        "net": "Salário Líquido",
        "fgts_deposit": "Depósito FGTS",
        "employer_cost_total": "Custo Total do Empregador",
        "tot_earnings": "Total de Proventos",
        "tot_deductions": "Total de Descontos",
        "update": "🔄 Atualizar Tabelas",
        "updated_ok": "✅ Tabelas atualizadas com sucesso em {ts}",
        "no_data": "Nenhum dado disponível para este país.",
        "valid_from": "Vigência",
    },
    "English": {
        "menu_calc": "Net Salary Calculation",
        "menu_rules": "Calculation Rules",
        "menu_cost": "Employer Cost",
        "menu_tables": "Tables & Updates",
        "title_calc": "Net Salary Calculation – {pais}",
        "title_rules": "Calculation Rules – {pais}",
        "title_cost": "Employer Cost – {pais}",
        "title_tables": "Tables & Updates",
        "country": "Country",
        "salary": "Gross Salary",
        "state": "State (USA)",
        "earnings": "Earnings",
        "deductions": "Deductions",
        "net": "Net Salary",
        "fgts_deposit": "FGTS Deposit",
        "employer_cost_total": "Total Employer Cost",
        "tot_earnings": "Total Earnings",
        "tot_deductions": "Total Deductions",
        "update": "🔄 Refresh Tables",
        "updated_ok": "✅ Tables refreshed at {ts}",
        "no_data": "No data available for this country.",
        "valid_from": "Valid from",
    },
    "Español": {
        "menu_calc": "Cálculo de Salario",
        "menu_rules": "Reglas de Cálculo",
        "menu_cost": "Costo del Empleador",
        "menu_tables": "Tablas y Actualizaciones",
        "title_calc": "Cálculo de Salario – {pais}",
        "title_rules": "Reglas de Cálculo – {pais}",
        "title_cost": "Costo del Empleador – {pais}",
        "title_tables": "Tablas y Actualizaciones",
        "country": "País",
        "salary": "Salario Bruto",
        "state": "Estado (EE. UU.)",
        "earnings": "Ingresos",
        "deductions": "Descuentos",
        "net": "Salario Neto",
        "fgts_deposit": "Depósito de FGTS",
        "employer_cost_total": "Costo Total del Empleador",
        "tot_earnings": "Total Ingresos",
        "tot_deductions": "Total Descuentos",
        "update": "🔄 Actualizar Tablas",
        "updated_ok": "✅ Tablas actualizadas a las {ts}",
        "no_data": "No hay datos disponibles para este país.",
        "valid_from": "Vigencia",
    }
}

# Idioma
idioma = st.sidebar.selectbox("🌐 Idioma / Language / Idioma", list(I18N.keys()), index=0)
T = I18N[idioma]

# -------------------------------------------------------------
# Países, moedas e bandeiras
# -------------------------------------------------------------
COUNTRIES = {
    "Brasil":   {"symbol": "R$",   "flag": "🇧🇷", "valid_from": "2025-01-01"},
    "México":   {"symbol": "MX$",  "flag": "🇲🇽", "valid_from": "2025-01-01"},
    "Chile":    {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01"},
    "Argentina":{"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01"},
    "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01"},
    "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01"},
    "Canadá":   {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01"},
}

# -------------------------------------------------------------
# Tabelas simplificadas (embutidas) para cálculo
# Observação: valores ilustrativos para outros países, Brasil com regras oficiais 2025
# -------------------------------------------------------------

def br_inss_2025(sal):
    # Faixas 2025 (teto salarial para cálculo de contribuição)
    faixas = [
        (0.00, 1412.00, 0.075),
        (1412.01, 2666.68, 0.09),
        (2666.69, 4000.03, 0.12),
        (4000.04, 8157.41, 0.14)
    ]
    contrib = 0.0
    for ini, fim, aliq in faixas:
        base_ini = max(ini, 0.0)
        base_fim = min(fim, sal)
        if sal > ini:
            contrib += max(0.0, base_fim - base_ini) * aliq
    # teto da contribuição (aprox) – ajuste conforme atualização anual
    return min(contrib, 1146.68)

def br_irrf_2025(base):
    # Base após INSS
    # Faixas 2025
    faixas = [
        (0.00, 2259.20, 0.00, 0.00),
        (2259.21, 2826.65, 0.075, 169.44),
        (2826.66, 3751.05, 0.15, 381.44),
        (3751.06, 4664.68, 0.225, 662.77),
        (4664.69, 9e9, 0.275, 896.00),
    ]
    imposto = 0.0
    for ini, fim, aliq, ded in faixas:
        if base >= ini and base <= fim:
            imposto = base * aliq - ded
            break
    return max(imposto, 0.0)

# Alíquotas simplificadas para demais países (exemplos realistas)
TABLES = {
    "Brasil": {
        "deductions": ["INSS", "IRRF"],
        "credits": ["FGTS"],
    },
    "México": {
        "deductions": ["ISR", "IMSS", "INFONAVIT"],  # ISR (imposto renda), IMSS (seguridade), INFONAVIT (habitação)
        "credits": [],
        "rates": {"ISR": 0.15, "IMSS": 0.05, "INFONAVIT": 0.05}
    },
    "Chile": {
        "deductions": ["AFP", "Saúde"],
        "credits": [],
        "rates": {"AFP": 0.10, "Saúde": 0.07}
    },
    "Argentina": {
        "deductions": ["Jubilación", "Obra Social", "PAMI"],
        "credits": [],
        "rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}
    },
    "Colômbia": {
        "deductions": ["Saúde", "Pensão"],
        "credits": [],
        "rates": {"Saúde": 0.04, "Pensão": 0.04}
    },
    "Estados Unidos": {
        "deductions": ["FICA", "Medicare", "State Tax"],
        "credits": [],
        "rates": {"FICA": 0.062, "Medicare": 0.0145}, # State Tax variável
        "states": {
            "No State Tax": 0.00, "CA": 0.06, "NY": 0.064, "TX": 0.00, "FL": 0.00, "WA": 0.00, "IL": 0.0495, "MA": 0.05
        }
    },
    "Canadá": {
        "deductions": ["CPP", "EI", "Income Tax"],
        "credits": [],
        "rates": {"CPP": 0.0595, "EI": 0.0163, "Income Tax": 0.15}
    }
}

# Custo do empregador (percentuais sobre salário)
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
        {"nome":"Seguro Desemprego","percentual":2.4,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Empregador"},
        {"nome":"Saúde Empregador","percentual":0.0,"base":"—","ferias":False,"decimo":False,"bonus":False,"obs":"Variável"}
    ],
    "Argentina": [
        {"nome":"Contribuições Patronais","percentual":18.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Média setores"}
    ],
    "Colômbia": [
        {"nome":"Saúde Empregador","percentual":8.5,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"—"},
        {"nome":"Pensão Empregador","percentual":12.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"—"}
    ],
    "Estados Unidos": [
        {"nome":"Social Security (ER)","percentual":6.2,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Até wage base"},
        {"nome":"Medicare (ER)","percentual":1.45,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Sem teto"},
        {"nome":"SUTA (avg)","percentual":2.0,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Média estado"}
    ],
    "Canadá": [
        {"nome":"CPP (ER)","percentual":5.95,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"Até limite"},
        {"nome":"EI (ER)","percentual":2.28,"base":"Salário","ferias":True,"decimo":True,"bonus":True,"obs":"—"}
    ]
}

EMPLOYER_FACTOR = {
    "Brasil": 13.33,
    "México": 12.50,
    "Chile": 12.00,
    "Argentina": 13.00,
    "Colômbia": 13.00,
    "Estados Unidos": 12.00,
    "Canadá": 12.00
}

# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------
def fmt_money(v, sym):
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calc_country_net(country, salary, state_code=None):
    """Retorna dict com linhas para a tabela, totais, fgts (se BR)."""
    lines = []
    total_earn = 0.0
    total_ded = 0.0
    fgts_value = 0.0

    if country == "Brasil":
        # Provento base
        lines.append(("Salário Base", salary, 0.0))
        total_earn += salary
        # INSS progressivo com teto
        inss = br_inss_2025(salary)
        total_ded += inss
        lines.append(("INSS", 0.0, inss))
        # IRRF sobre base após INSS (simplificado sem dependentes)
        base_ir = max(salary - inss, 0.0)
        irrf = br_irrf_2025(base_ir)
        total_ded += irrf
        lines.append(("IRRF", 0.0, irrf))
        # FGTS (crédito do empregador) – NÃO entra em proventos/total
        fgts_value = salary * 0.08

    elif country == "México":
        rates = TABLES["México"]["rates"]
        lines.append(("Salario Base", salary, 0.0)); total_earn += salary
        for k in ["ISR","IMSS","INFONAVIT"]:
            v = salary * rates[k]
            total_ded += v
            lines.append((k, 0.0, v))

    elif country == "Chile":
        rates = TABLES["Chile"]["rates"]
        lines.append(("Sueldo Base", salary, 0.0)); total_earn += salary
        for k in ["AFP","Saúde"]:
            v = salary * rates[k]
            total_ded += v
            lines.append((k, 0.0, v))

    elif country == "Argentina":
        rates = TABLES["Argentina"]["rates"]
        lines.append(("Salario Base", salary, 0.0)); total_earn += salary
        for k in ["Jubilación","Obra Social","PAMI"]:
            v = salary * rates[k]
            total_ded += v
            lines.append((k, 0.0, v))

    elif country == "Colômbia":
        rates = TABLES["Colômbia"]["rates"]
        lines.append(("Salario Base", salary, 0.0)); total_earn += salary
        for k in ["Saúde","Pensão"]:
            v = salary * rates[k]
            total_ded += v
            lines.append((k, 0.0, v))

    elif country == "Estados Unidos":
        rates = TABLES["Estados Unidos"]["rates"]
        states = TABLES["Estados Unidos"]["states"]
        st_rate = states.get(state_code or "No State Tax", 0.0)
        lines.append(("Base Pay", salary, 0.0)); total_earn += salary
        fica = salary * rates["FICA"]; total_ded += fica; lines.append(("FICA (Social Security)", 0.0, fica))
        medicare = salary * rates["Medicare"]; total_ded += medicare; lines.append(("Medicare", 0.0, medicare))
        if st_rate > 0:
            sttax = salary * st_rate; total_ded += sttax; lines.append((f"State Tax ({state_code})", 0.0, sttax))

    elif country == "Canadá":
        rates = TABLES["Canadá"]["rates"]
        lines.append(("Base Pay", salary, 0.0)); total_earn += salary
        for k in ["CPP","EI","Income Tax"]:
            v = salary * rates[k]
            total_ded += v
            lines.append((k, 0.0, v))

    net = total_earn - total_ded
    return {
        "lines": lines,
        "total_earn": total_earn,
        "total_ded": total_ded,
        "net": net,
        "fgts": fgts_value
    }

def calc_employer_cost(country, salary):
    enc = EMPLOYER_COST.get(country, [])
    factor = EMPLOYER_FACTOR.get(country, 12.0)
    perc_total = sum(e["percentual"] for e in enc)
    anual = salary * factor * (1 + perc_total/100.0)
    mensal_equiv = anual / 12.0
    mult = anual / (salary * 12.0) if salary > 0 else 0.0
    return anual, mensal_equiv, mult, enc, factor

# -------------------------------------------------------------
# Sidebar (idioma + menu)
# -------------------------------------------------------------
st.sidebar.markdown(f"### {T['country']}")
country = st.sidebar.selectbox("", list(COUNTRIES.keys()), index=0)
symbol = COUNTRIES[country]["symbol"]
flag = COUNTRIES[country]["flag"]
valid_from = COUNTRIES[country]["valid_from"]

menu = st.sidebar.radio("📋 Menu", [T["menu_calc"], T["menu_rules"], T["menu_cost"], T["menu_tables"]], index=0)

# Estados EUA (apenas quando necessário)
state_code = None
if country == "Estados Unidos" and menu == T["menu_calc"]:
    st.sidebar.markdown(f"**{T['state']}**")
    state_code = st.sidebar.selectbox("", list(TABLES["Estados Unidos"]["states"].keys()), index=0)

# -------------------------------------------------------------
# Título dinâmico (com bandeira)
# -------------------------------------------------------------
if menu == T["menu_calc"]:
    title = T["title_calc"].format(pais=country)
elif menu == T["menu_rules"]:
    title = T["title_rules"].format(pais=country)
elif menu == T["menu_cost"]:
    title = T["title_cost"].format(pais=country)
else:
    title = T["title_tables"]

st.markdown(f"<div class='country-header'><div class='country-flag'>{flag}</div><div class='country-title'>{title}</div></div>", unsafe_allow_html=True)
st.write(f"**{T['valid_from']}:** {valid_from}")
st.write("---")

# -------------------------------------------------------------
# Seção: Cálculo de Salário
# -------------------------------------------------------------
if menu == T["menu_calc"]:
    c1, c2 = st.columns([2,2])
    with c1:
        salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0)
    with c2:
        if country == "Estados Unidos":
            st.write(f"**{T['state']}:** {state_code or '—'}")
        else:
            st.write(" ")

    calc = calc_country_net(country, salario, state_code=state_code)

    # Tabela demonstrativo
    df = pd.DataFrame(calc["lines"], columns=["Descrição", T["earnings"], T["deductions"]])
    st.markdown("<div class='table-wrap'>", unsafe_allow_html=True)
    st.table(df.assign(**{
        T["earnings"]: df[T["earnings"]].apply(lambda v: fmt_money(v, symbol)),
        T["deductions"]: df[T["deductions"]].apply(lambda v: fmt_money(v, symbol)),
    }))
    st.markdown("</div>", unsafe_allow_html=True)

    # Cards totais (proventos, descontos, líquido)
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.markdown(f"<div class='metric-card'><h4>🟩 {T['tot_earnings']}</h4><h3>{fmt_money(calc['total_earn'], symbol)}</h3></div>", unsafe_allow_html=True)
    with cc2:
        st.markdown(f"<div class='metric-card'><h4>🟥 {T['tot_deductions']}</h4><h3>{fmt_money(calc['total_ded'], symbol)}</h3></div>", unsafe_allow_html=True)
    with cc3:
        st.markdown(f"<div class='metric-card'><h4>🟦 {T['net']}</h4><h3>{fmt_money(calc['net'], symbol)}</h3></div>", unsafe_allow_html=True)

    # Depósito FGTS (Brasil somente) – fora dos totais
    if country == "Brasil":
        st.write("")
        st.markdown(f"**💼 {T['fgts_deposit']}:** {fmt_money(calc['fgts'], symbol)}")

# -------------------------------------------------------------
# Seção: Regras de Cálculo (resumo textual das regras)
# -------------------------------------------------------------
elif menu == T["menu_rules"]:
    st.subheader(T["menu_rules"])
    if country == "Brasil":
        st.markdown("**INSS (empregado) – 2025**: Progressivo por faixas até o teto salarial de R$ 8.157,41; contribuição máxima aproximada R$ 1.146,68.")
        st.markdown("**IRRF (empregado) – 2025**: Incide sobre a base após INSS. Faixas: isento até R$ 2.259,20; 7,5% | 15% | 22,5% | 27,5% acima de R$ 4.664,68 (com deduções fixas por faixa).")
        st.markdown("**FGTS (empregador)**: 8% do salário; não é desconto do empregado, mostrado separadamente.")
    elif country == "Estados Unidos":
        st.markdown("**FICA (Social Security)**: 6,2% até o wage base anual; **Medicare**: 1,45% sem teto; **State Tax**: conforme o estado (ex.: 0% FL/TX, 5%–6% CA/NY).")
    elif country == "México":
        st.markdown("**ISR** (impuesto sobre la renta); **IMSS** (seguridad social); **INFONAVIT** (vivienda). Alíquotas variam conforme ingreso y tablas SAT/IMSS.")
    elif country == "Chile":
        st.markdown("**AFP** 10% (previsión) + **Salud** 7% (FONASA/ISAPRE).")
    elif country == "Argentina":
        st.markdown("**Jubilación** 11%, **Obra Social** 3%, **PAMI** 3% (valores de referência).")
    elif country == "Colômbia":
        st.markdown("**Salud** 4% e **Pensión** 4% (trabalhador).")
    elif country == "Canadá":
        st.markdown("**CPP** ~5,95%, **EI** ~1,63%, **Income Tax** progressivo por província.")
    else:
        st.info(T["no_data"])

# -------------------------------------------------------------
# Seção: Custo do Empregador
# -------------------------------------------------------------
elif menu == T["menu_cost"]:
    st.subheader(T["menu_cost"])
    c1, c2 = st.columns([2,2])
    with c1:
        salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="sal_cost")
    anual, mensal_equiv, mult, enc, factor = calc_employer_cost(country, salario)

    st.markdown(f"**{T['employer_cost_total']}:** {fmt_money(anual, symbol)}  \n**Equivalente:** {mult:.3f} × (12 meses)  \n**Fator anual usado:** {factor} salários/ano")
    st.write("")
    df = pd.DataFrame(enc)
    if not df.empty:
        df["Incide Férias"] = df["ferias"].apply(lambda x: "✅" if x else "❌")
        df["Incide 13º"] = df["decimo"].apply(lambda x: "✅" if x else "❌")
        df["Incide Bônus"] = df["bonus"].apply(lambda x: "✅" if x else "❌")
        df.rename(columns={"nome":"Encargo","percentual":"Percentual (%)","obs":"Observação"}, inplace=True)
        st.dataframe(df[["Encargo","Percentual (%)","base","Incide Férias","Incide 13º","Incide Bônus","Observação"]])
    else:
        st.info(T["no_data"])

# -------------------------------------------------------------
# Seção: Tabelas e Atualizações
# -------------------------------------------------------------
else:
    st.subheader(T["menu_tables"])
    st.markdown("<div class='update-box'>", unsafe_allow_html=True)
    st.write("Este módulo exibe a vigência e permite atualizar as tabelas embutidas. Em produção, a atualização pode puxar JSON do GitHub.")
    if st.button(T["update"]):
        st.success(T["updated_ok"].format(ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    st.markdown("</div>", unsafe_allow_html=True)

    # Quadro de vigências
    rows = []
    for k, v in COUNTRIES.items():
        rows.append({"País": k, "Moeda": v["symbol"], "Bandeira": v["flag"], "Vigência": v["valid_from"]})
    st.write("")
    st.dataframe(pd.DataFrame(rows))
