# -------------------------------------------------------------
# 📄 Demonstrativo de Pagamento Internacional – v2025.18
# Layout Corporativo Executivo com Menu Lateral e Cards
# Autor: Alexandre Savoy + ChatGPT HR Dev | Outubro/2025
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="Demonstrativo de Pagamento Internacional", layout="wide")

# -------------------------------------------------------------
# 🎨 CSS Corporativo
# -------------------------------------------------------------
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', Helvetica, sans-serif;
    background-color: #f7f9fb;
    color: #1a1a1a;
}
.sidebar .sidebar-content {
    background-color: #0a3d62 !important;
    color: white !important;
}
button[kind="secondary"] {
    background-color: #1e90ff !important;
    color: white !important;
}
h1, h2, h3 {
    color: #0a3d62;
}
.table-container {
    margin-top: 25px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    background-color: white;
}
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
}
tr:nth-child(even) {
    background-color: #f2f7fb;
}
th {
    background-color: #f0f3f8;
    color: #0a3d62;
    font-weight: 600;
}
.metric-card {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    padding: 16px;
    text-align: center;
    margin: 10px;
}
.metric-card h4 {
    margin: 0;
    font-size: 15px;
    color: #0a3d62;
}
.metric-card h3 {
    margin: 4px 0 0;
    color: #0a3d62;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🌐 Idiomas embutidos
# -------------------------------------------------------------
idiomas = {
    "Português": {
        "menu_calc": "Demonstrativo",
        "menu_rules": "Regras de Cálculo",
        "menu_cost": "Custo do Empregador",
        "title": "📄 Demonstrativo de Pagamento Internacional",
        "country_label": "🌎 País",
        "salary_label": "💰 Salário Bruto",
        "gross": "Proventos",
        "discounts": "Descontos",
        "net": "Salário Líquido",
        "fgts": "FGTS / Crédito Empregador",
        "employer_cost": "Custo Total do Empregador",
        "discount_detail": "Detalhamento dos Descontos",
        "no_data": "Nenhum dado disponível para este país."
    },
    "English": {
        "menu_calc": "Payslip",
        "menu_rules": "Calculation Rules",
        "menu_cost": "Employer Cost",
        "title": "📄 International Payroll Statement",
        "country_label": "🌎 Country",
        "salary_label": "💰 Gross Salary",
        "gross": "Earnings",
        "discounts": "Deductions",
        "net": "Net Salary",
        "fgts": "Employer Credit / FGTS",
        "employer_cost": "Total Employer Cost",
        "discount_detail": "Deductions Breakdown",
        "no_data": "No data available for this country."
    },
    "Español": {
        "menu_calc": "Demostrativo",
        "menu_rules": "Reglas de Cálculo",
        "menu_cost": "Costo del Empleador",
        "title": "📄 Comprobante de Pago Internacional",
        "country_label": "🌎 País",
        "salary_label": "💰 Salario Bruto",
        "gross": "Ingresos",
        "discounts": "Descuentos",
        "net": "Salario Neto",
        "fgts": "Crédito del Empleador / FGTS",
        "employer_cost": "Costo Total del Empleador",
        "discount_detail": "Detalle de Descuentos",
        "no_data": "No hay datos disponibles para este país."
    }
}

idioma_escolhido = st.sidebar.selectbox("🌐 Idioma / Language / Idioma", list(idiomas.keys()), index=0)
txt = idiomas[idioma_escolhido]

# -------------------------------------------------------------
# 🌍 Moedas e bandeiras
# -------------------------------------------------------------
moedas = {
    "Brasil": {"simbolo": "R$", "bandeira": "🇧🇷"},
    "Chile": {"simbolo": "CLP$", "bandeira": "🇨🇱"},
    "México": {"simbolo": "MX$", "bandeira": "🇲🇽"},
    "Estados Unidos": {"simbolo": "US$", "bandeira": "🇺🇸"},
    "Canadá": {"simbolo": "CAD$", "bandeira": "🇨🇦"},
    "Colômbia": {"simbolo": "COP$", "bandeira": "🇨🇴"},
    "Argentina": {"simbolo": "ARS$", "bandeira": "🇦🇷"}
}
# -------------------------------------------------------------
# 🔧 Funções utilitárias e cálculo
# -------------------------------------------------------------
def carregar_json(url):
    try:
        if url.startswith("http"):
            r = requests.get(url)
            if r.status_code == 200:
                return r.json()
        else:
            with open(url, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {}

URL_TABELAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"
URL_REGRAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/regras_fiscais.json"
URL_CUSTOS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/custos_empregador.json"

tabelas = carregar_json(URL_TABELAS)
regras = carregar_json(URL_REGRAS)
custos = carregar_json(URL_CUSTOS)

def formatar_moeda(valor, simbolo):
    return f"{simbolo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_salario_liquido(pais, salario):
    if pais not in tabelas:
        if pais == "Brasil":
            data = {"descontos": [
                {"nome": "INSS", "percentual": 11, "tipo": "desconto"},
                {"nome": "IRRF", "percentual": 15, "tipo": "desconto"},
                {"nome": "FGTS", "percentual": 8, "tipo": "credito"}
            ]}
        else:
            data = {"descontos": []}
    else:
        data = tabelas[pais]

    descontos, total_desc, fgts = {}, 0, 0
    for d in data["descontos"]:
        valor = salario * d["percentual"] / 100
        if d["tipo"] == "desconto":
            total_desc += valor
        elif d["tipo"] == "credito":
            fgts += valor
        descontos[d["nome"]] = valor

    liquido = salario - total_desc
    custo_total = salario + fgts
    return liquido, descontos, fgts, custo_total

def calcular_custo_empregador(pais, salario):
    if pais not in custos:
        return None
    dados = custos[pais]
    fator = dados["fator_salarios_ano"]
    encargos = dados["encargos"]
    total_percentual = sum([e["percentual"] for e in encargos])
    custo_anual = salario * fator * (1 + total_percentual / 100)
    custo_mensal_equiv = custo_anual / 12
    multiplicador = custo_anual / (salario * 12)
    return custo_anual, custo_mensal_equiv, multiplicador, encargos
# -------------------------------------------------------------
# 🖥️ Interface principal
# -------------------------------------------------------------
menu_ativo = st.sidebar.radio("📋 Menu", [txt["menu_calc"], txt["menu_rules"], txt["menu_cost"]])

st.title(txt["title"])

col_t1, col_t2 = st.columns([2, 2])
pais = col_t1.selectbox(txt["country_label"], list(moedas.keys()))
simbolo = moedas[pais]["simbolo"]
bandeira = moedas[pais]["bandeira"]
salario = col_t2.number_input(f"{txt['salary_label']} ({simbolo})", min_value=0.0, value=10000.00, step=100.0)

# -------------------------------------------------------------
# 📄 Demonstrativo
# -------------------------------------------------------------
if menu_ativo == txt["menu_calc"]:
    liquido, descontos, fgts, custo_total = calcular_salario_liquido(pais, salario)
    total_desc = sum(descontos.values())
    dados = [
        {"Descrição": "Salário Base", "Proventos": salario, "Descontos": 0},
    ]
    for nome, valor in descontos.items():
        if nome in ["FGTS"]:
            dados.append({"Descrição": nome, "Proventos": valor, "Descontos": 0})
        else:
            dados.append({"Descrição": nome, "Proventos": 0, "Descontos": valor})

    df = pd.DataFrame(dados)
    df["Proventos"] = df["Proventos"].apply(lambda x: formatar_moeda(x, simbolo))
    df["Descontos"] = df["Descontos"].apply(lambda x: formatar_moeda(x, simbolo))
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    st.table(df[["Descrição", "Proventos", "Descontos"]])
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h4>{txt['net']}</h4><h3>{formatar_moeda(liquido, simbolo)}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h4>{txt['fgts']}</h4><h3>{formatar_moeda(fgts, simbolo)}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h4>{txt['employer_cost']}</h4><h3>{formatar_moeda(custo_total, simbolo)}</h3></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 📘 Regras de Cálculo
# -------------------------------------------------------------
elif menu_ativo == txt["menu_rules"]:
    st.subheader(txt["menu_rules"])
    if pais in regras:
        regras_pais = regras[pais].get("pt", {}).get("regras", [])
        for r in regras_pais:
            st.markdown(f"**{r['tipo']}** – {r['explicacao']}")
            if "faixas" in r:
                df = pd.DataFrame(r["faixas"])
                st.dataframe(df)
    else:
        st.info(txt["no_data"])

# -------------------------------------------------------------
# 💼 Custo do Empregador
# -------------------------------------------------------------
elif menu_ativo == txt["menu_cost"]:
    st.subheader(txt["menu_cost"])
    resultado = calcular_custo_empregador(pais, salario)
    if resultado:
        custo_anual, custo_mensal_equiv, multiplicador, encargos = resultado
        st.markdown(f"**Custo Anual:** {formatar_moeda(custo_anual, simbolo)}")
        st.markdown(f"**Equivalente a:** {multiplicador:.3f} × salário mensal")
        st.markdown(f"**Custo Mensal Equivalente:** {formatar_moeda(custo_mensal_equiv, simbolo)}")

        st.markdown("### Encargos Patronais")
        df = pd.DataFrame(encargos)
        df["Aplica sobre"] = df["base"]
        df["Férias"] = df["ferias"].apply(lambda x: "✅" if x else "❌")
        df["13º"] = df["decimo"].apply(lambda x: "✅" if x else "❌")
        df["Bônus"] = df["bonus"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df[["nome", "percentual", "Aplica sobre", "Férias", "13º", "Bônus", "obs"]])
    else:
        st.info(txt["no_data"])
