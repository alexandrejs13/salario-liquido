# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.25)
# -------------------------------------------------------------
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Simulador de Salário Líquido e Custo do Empregador",
    layout="wide"
)

# ========================= CSS ==============================
st.markdown("""
<style>
body { font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background:#f7f9fb; color:#1a1a1a;}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e2e6ea; margin:16px 0; }

/* Sidebar */
section[data-testid="stSidebar"] { background:#0a3d62 !important; }
section[data-testid="stSidebar"] * { color:#ffffff !important; }
section[data-testid="stSidebar"] .stSelectbox > div, 
section[data-testid="stSidebar"] .stNumberInput > div {
    background:#ffffff !important; border-radius:8px; padding:2px 6px;
}
section[data-testid="stSidebar"] input, 
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] .st-bb { color:#0a0a0a !important; }

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

/* Bandeira + título dinâmico */
.country-header { display:flex; align-items:center; gap:10px; }
.country-flag { font-size:28px; }
.country-title { font-size:24px; font-weight:700; color:#0a3d62; }

.small { color:#445; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ========================= I18N =============================
I18N = {
    "Português": {
        "app_title": "Simulador de Salário Líquido e Custo do Empregador",
        "menu_calc": "Cálculo de Salário",
        "menu_rules": "Regras de Cálculo",
        "menu_cost": "Custo do Empregador",
        "title_calc": "Cálculo de Salário – {pais}",
        "title_rules": "Regras de Cálculo – {pais}",
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
    },
    "English": {
        "app_title": "Net Salary & Employer Cost Simulator",
        "menu_calc": "Net Salary Calculation",
        "menu_rules": "Calculation Rules",
        "menu_cost": "Employer Cost",
        "title_calc": "Net Salary Calculation – {pais}",
        "title_rules": "Calculation Rules – {pais}",
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
    },
    "Español": {
        "app_title": "Simulador de Salario Neto y Costo del Empleador",
        "menu_calc": "Cálculo de Salario",
        "menu_rules": "Reglas de Cálculo",
        "menu_cost": "Costo del Empleador",
        "title_calc": "Cálculo de Salario – {pais}",
        "title_rules": "Reglas de Cálculo – {pais}",
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
    }
}

# ================== Países, moedas, bandeiras ================
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

# Fator de meses para REMUNERAÇÃO anual (não altera líquido mensal)
REMUN_MONTHS = {
    "Brasil":13.33,   # 12 salários + 1 férias + 1/3 adicional (≈ 13,33)
    "México":12.50,   # aguinaldo mínimo (indicativo)
    "Chile":12.00,
    "Argentina":13.00, # SAC (13º)
    "Colômbia":13.00, # prima de serviços
    "Estados Unidos":12.00,
    "Canadá":12.00
}

# ================== Tabelas BR (exemplo simplificado) ========
def br_inss_2025(sal: float) -> float:
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
    return min(max(contrib, 0.0), 1146.68)  # teto aprox.

def br_irrf_2025(base: float, dependentes: int = 0) -> float:
    ded_por_dep = 189.59
    base = max(base - ded_por_dep * max(int(dependentes), 0), 0.0)
    faixas = [
        (0.00, 2259.20, 0.00, 0.00),
        (2259.21, 2826.65, 0.075, 169.44),
        (2826.66, 3751.05, 0.15, 381.44),
        (3751.06, 4664.68, 0.225, 662.77),
        (4664.69, 9e9, 0.275, 896.00),
    ]
    for ini, fim, aliq, ded in faixas:
        if ini <= base <= fim:
            return max(base * aliq - ded, 0.0)
    return 0.0

# ================== Tabelas dos países (simples) =============
TABLES = {
    "México": {"rates": {"ISR": 0.15, "IMSS": 0.05, "INFONAVIT": 0.05}},
    "Chile": {"rates": {"AFP": 0.10, "Saúde": 0.07}},
    "Argentina": {"rates": {"Jubilación": 0.11, "Obra Social": 0.03, "PAMI": 0.03}},
    "Colômbia": {"rates": {"Saúde": 0.04, "Pensão": 0.04}},
    "Canadá": {"rates": {"CPP": 0.0595, "EI": 0.0163, "Income Tax": 0.15}}
}

# ================== EUA: todos os estados + taxas padrão =====
US_STATE_RATES = {
    "No State Tax": 0.00, "AK": 0.00, "FL": 0.00, "NV": 0.00, "SD": 0.00, "TN": 0.00, "TX": 0.00, "WA": 0.00, "WY": 0.00, "NH": 0.00,
    "AL": 0.05, "AR": 0.049, "AZ": 0.025, "CA": 0.06,  "CO": 0.044,
    "CT": 0.05, "DC": 0.06,  "DE": 0.055, "GA": 0.054, "HI": 0.08,
    "IA": 0.05, "ID": 0.055, "IL": 0.0495, "IN": 0.0323, "KS": 0.052,
    "KY": 0.045, "LA": 0.045, "MA": 0.05, "MD": 0.047, "ME": 0.058,
    "MI": 0.0425, "MN": 0.058, "MO": 0.045, "MS": 0.05, "MT": 0.054,
    "NC": 0.045, "ND": 0.02,  "NE": 0.05,  "NJ": 0.055, "NM": 0.049,
    "NY": 0.064, "OH": 0.030, "OK": 0.0475,"OR": 0.08,  "PA": 0.0307,
    "RI": 0.0475,"SC": 0.052, "UT": 0.0485,"VA": 0.05,  "VT": 0.06,
    "WI": 0.053, "WV": 0.05
}

# ================== Employer cost (indicativo) ================
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

# ========================== Helpers ==========================
def fmt_money(v, sym): 
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v, sym):
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

def br_net(country, salary, dependentes):
    lines = []
    total_earn = salary
    # INSS progressivo com teto
    inss = br_inss_2025(salary)
    # IRRF com dedução por dependente, após INSS
    base_ir = max(salary - inss, 0.0)
    irrf = br_irrf_2025(base_ir, dependentes=dependentes)
    lines.append(("Salário Base", salary, 0.0))
    lines.append(("INSS", 0.0, inss))
    lines.append(("IRRF", 0.0, irrf))
    fgts_value = salary * 0.08
    net = total_earn - (inss + irrf)
    return lines, total_earn, inss + irrf, net, fgts_value

def generic_net(country, salary, table_key):
    r = TABLES[table_key]["rates"]
    lines = [( "Base", salary, 0.0 )]
    total_earn = salary
    total_ded = 0.0
    for k, aliq in r.items():
        v = salary * aliq
        total_ded += v
        lines.append((k, 0.0, v))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def us_net(salary, state_code, state_rate):
    lines = [("Base Pay", salary, 0.0)]
    total_earn = salary
    fica = salary * 0.062
    medicare = salary * 0.0145
    total_ded = fica + medicare
    lines += [("FICA (Social Security)", 0.0, fica), ("Medicare", 0.0, medicare)]
    sr = state_rate if state_rate is not None else US_STATE_RATES.get(state_code, 0.0)
    if sr > 0:
        sttax = salary * sr
        total_ded += sttax
        lines.append((f"State Tax ({state_code})", 0.0, sttax))
    net = total_earn - total_ded
    return lines, total_earn, total_ded, net

def calc_country_net(country, salary, state_code=None, state_rate=None, dependentes=0):
    if country == "Brasil":
        lines, te, td, net, fgts = br_net(country, salary, dependentes)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": fgts}
    elif country == "Estados Unidos":
        lines, te, td, net = us_net(salary, state_code, state_rate)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    elif country in ("México","Chile","Argentina","Colômbia","Canadá"):
        key = country
        if country == "Colômbia": key = "Colômbia"
        lines, te, td, net = generic_net(country, salary, key)
        return {"lines": lines, "total_earn": te, "total_ded": td, "net": net, "fgts": 0.0}
    else:
        return {"lines": [("Base", salary, 0.0)], "total_earn": salary, "total_ded": 0.0, "net": salary, "fgts": 0.0}

def calc_employer_cost(country, salary):
    enc = EMPLOYER_COST.get(country, [])
    # Colunas variáveis: só mostramos Férias/13º se o país tiver esses benefícios
    benefits = COUNTRY_BENEFITS.get(country, {"ferias": False, "decimo": False})
    df = pd.DataFrame(enc)
    # Marcação de incidência condicionada
    if benefits.get("ferias", False):
        df["Incide Férias"] = ["✅" if row else "❌" for row in df["ferias"]]
    if benefits.get("decimo", False):
        df["Incide 13º"] = ["✅" if row else "❌" for row in df["decimo"]]
    df["Incide Bônus"] = ["✅" if row else "❌" for row in df["bonus"]]
    df.rename(columns={"nome":"Encargo","percentual":"Percentual (%)","obs":"Observação","base":"Base"}, inplace=True)
    # Seleção de colunas dinâmica
    cols_show = ["Encargo","Percentual (%)","Base"]
    if benefits.get("ferias", False):
        cols_show.append("Incide Férias")
    if benefits.get("decimo", False):
        cols_show.append("Incide 13º")
    cols_show.append("Incide Bônus")
    cols_show.append("Observação")
    # Cálculo do custo total anual (apenas um indicativo multiplicando percentuais sobre salário × meses)
    months = REMUN_MONTHS.get(country, 12.0)
    perc_total = sum(e["percentual"] for e in enc)
    anual = salary * months * (1 + perc_total/100.0)
    mult = (anual / (salary * 12.0)) if salary > 0 else 0.0
    return anual, mult, df[cols_show], months

def render_rules(country, T):
    # Texto detalhado dividindo empregado × empregador
    st.markdown(f"### {T['rules_emp']}")
    if country == "Brasil":
        st.markdown("""
**Empregado (Brasil)**  
- **INSS (progressivo)**: calcula-se por faixas de salário, somando a contribuição de cada faixa até o seu salário. Há **teto mensal** de contribuição (valor indicativo).  
- **IRRF**: base = **salário bruto − INSS − dedução por dependentes** (R$ 189,59/mês por dependente). Aplica-se a **tabela progressiva** com **deduções fixas por faixa**; resultado não pode ser negativo.
- **FGTS**: **não** é desconto do empregado.

Exemplo de lógica:  
1) Calcular INSS por faixas com teto.  
2) Base do IRRF = bruto − INSS − (dependentes × dedução).  
3) Aplicar alíquota e dedução da faixa → **IRRF devido**.
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empregador (Brasil)**  
- **INSS Patronal (20%)**, **RAT (≈2%)**, **Sistema S (≈5,8%)**: percentuais sobre a folha (variam por CNAE/regra específica).  
- **FGTS (8%)**: depósito mensal.  
- Em geral, **incidem também sobre férias e 13º**, compondo o custo anual.
        """)

    elif country == "Estados Unidos":
        st.markdown("""
**Empregado (EUA)**  
- **FICA**: 6,2% para Social Security até o **wage base** anual.  
- **Medicare**: 1,45% sem teto (adicional para altas rendas pode existir).  
- **State Tax**: depende do estado; neste simulador, você escolhe o estado e pode **ajustar a taxa** no campo **State Tax (%)**.  
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empregador (EUA)**  
- **Social Security (ER)** 6,2% (espelha o empregado, respeitando wage base).  
- **Medicare (ER)** 1,45%.  
- **SUTA** (desemprego estadual): varia por estado (usamos ~2% indicativo).  
- Benefícios como férias/13º não são mandatórios federais, por isso **não entram** como meses adicionais por padrão.
        """)

    elif country == "México":
        st.markdown("""
**Empleado (México)**  
- **ISR** (impuesto sobre la renta): progresivo por tablas oficiales.  
- **IMSS**: seguridad social del trabajador.  
- **INFONAVIT**: contribución habitacional (puede retenerse en nómina).
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empleador (México)**  
- **IMSS patronal** y **INFONAVIT** patronal: porcentajes sobre la base salarial, con variaciones por riesgo/actividad.  
- **Aguinaldo** mínimo suele equivaler a fracción de mes; por eso consideramos **12,5 meses** como indicativo en la remuneração anual.
        """)

    elif country == "Chile":
        st.markdown("""
**Trabajador (Chile)**  
- **AFP** (~10%): pensiones.  
- **Salud** (~7%): FONASA/ISAPRE.  
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empleador (Chile)**  
- **Seguro de cesantía (empleador)** ~2,4% (indicativo).  
- No há 13º mandatário; meses considerados **12**.
        """)

    elif country == "Argentina":
        st.markdown("""
**Empleado (Argentina)**  
- **Jubilación** 11%, **Obra Social** 3%, **PAMI** 3% (indicativos).  
- Puede existir retención de Ganancias por escalas (no detalhado aquí).
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empleador (Argentina)**  
- **Contribuciones patronales** promedian ~18% (según actividad/región).  
- Existe **SAC (13º)** → meses considerados **13**.
        """)

    elif country == "Colômbia":
        st.markdown("""
**Trabajador (Colombia)**  
- **Salud** 4% y **Pensión** 4% (indicativos).  
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Empleador (Colombia)**  
- **Salud (empleador)** ~8,5% y **Pensión (empleador)** ~12%.  
- Suele existir **prima de servicios** → meses considerados **13**.
        """)

    elif country == "Canadá":
        st.markdown("""
**Employee (Canada)**  
- **CPP** ~5,95%, **EI** ~1,63%, **Income Tax** provincial/federal progresivo (indicativo).  
        """)
        st.markdown(f"### {T['rules_er']}")
        st.markdown("""
**Employer (Canada)**  
- **CPP (ER)** ~5,95% y **EI (ER)** ~2,28% (indicativos).  
- Meses considerados **12**.
        """)
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
    # Inputs no corpo (condicionais por país)
    if country == "Brasil":
        c1, c2, c3 = st.columns([2,1,1])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        dependentes = c2.number_input(f"{T['dependents']}", min_value=0, value=0, step=1, key="dep_input")
        bonus_anual = c3.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        state_code, state_rate = None, None

    elif country == "Estados Unidos":
        c1, c2, c3, c4 = st.columns([2,1.4,1.2,1.4])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        state_code = c2.selectbox(f"{T['state']}", list(US_STATE_RATES.keys()), index=0, key="state_select_main")
        default_rate = US_STATE_RATES.get(state_code, 0.0)
        state_rate = c3.number_input(f"{T['state_rate']}", min_value=0.0, max_value=0.20, value=float(default_rate), step=0.001, format="%.3f", key="state_rate_input")
        bonus_anual = c4.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        dependentes = 0

    else:
        c1, c2 = st.columns([2,1])
        salario = c1.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_input")
        bonus_anual = c2.number_input(f"{T['bonus']} ({symbol})", min_value=0.0, value=0.0, step=100.0, key="bonus_input")
        dependentes = 0
        state_code, state_rate = None, None

    calc = calc_country_net(country, salario, state_code=state_code, state_rate=state_rate, dependentes=dependentes)

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

    # ---------- Composição da Remuneração Total Anual ----------
    st.write("---")
    st.subheader(T["annual_comp_title"])
    months = REMUN_MONTHS.get(country, 12.0)
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual

    # Cards verticais (um abaixo do outro)
    st.markdown(f"<div class='metric-card'><h4>📅 {T['annual_salary']} — ({T['months_factor']}: {months})</h4><h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card'><h4>🎯 {T['annual_bonus']}</h4><h3>{fmt_money(bonus_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card'><h4>💼 {T['annual_total']}</h4><h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True)

    # Gráfico de Pizza: salário vs bônus
    chart_df = pd.DataFrame({
        "Componente": [T["annual_salary"], T["annual_bonus"]],
        "Valor": [salario_anual, bonus_anual]
    })
    pie = alt.Chart(chart_df).mark_arc(innerRadius=60).encode(
        theta=alt.Theta(field="Valor", type="quantitative"),
        color=alt.Color(field="Componente", type="nominal"),
        tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f")]
    ).properties(title=T["pie_title"], width=380, height=320)
    st.altair_chart(pie, use_container_width=False)

# ================= Seção: Regras de Cálculo ==================
elif menu == T["menu_rules"]:
    render_rules(country, T)

# =============== Seção: Custo do Empregador ==================
else:
    salario = st.number_input(f"{T['salary']} ({symbol})", min_value=0.0, value=10000.0, step=100.0, key="salary_cost")
    anual, mult, df_cost, months = calc_employer_cost(country, salario)

    st.markdown(f"**{T['employer_cost_total']}:** {fmt_money(anual, symbol)}  \n**Equivalente:** {mult:.3f} × (12 meses)  \n**{T['months_factor']}:** {months}")
    st.dataframe(df_cost, use_container_width=True)
