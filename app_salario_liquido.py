# -------------------------------------------------------------
# 📄 Calculadora Global de Salário Líquido – v2025.17
# Executive Payroll Layout | Multilíngue PT-EN-ES
# Autor: Alexandre Savoy + ChatGPT HR Dev | Outubro/2025
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import json

# -------------------------------------------------------------
# ⚙️ Configuração inicial do app
# -------------------------------------------------------------
st.set_page_config(page_title="Calculadora Global de Salário Líquido", layout="wide")

# -------------------------------------------------------------
# 🎨 CSS Corporativo
# -------------------------------------------------------------
st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', Helvetica, sans-serif;
        color: #1a1a1a;
        background-color: #f7f9fb;
    }
    .title-header {
        font-size: 30px;
        color: #0a3d62;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .sub-header {
        color: #1e3799;
        font-size: 22px;
        margin-top: 10px;
    }
    .metric-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        padding: 18px;
        text-align: center;
        margin-bottom: 18px;
    }
    .menu-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 15px;
        margin-bottom: 30px;
    }
    .menu-button {
        background-color: #1e90ff;
        border: none;
        color: white;
        font-weight: 600;
        padding: 10px 24px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .menu-button:hover {
        background-color: #155fa0;
    }
    .active-button {
        background-color: #0b5394 !important;
    }
    .flag {
        font-size: 42px;
        margin-right: 10px;
    }
    .lang-container {
        position: absolute;
        top: 12px;
        right: 25px;
        font-weight: 600;
        color: #0a3d62;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🌍 Idiomas embutidos (PT / EN / ES)
# -------------------------------------------------------------
idiomas = {
    "Português": {
        "menu_calc": "📄 Cálculo do Salário Líquido",
        "menu_rules": "📘 Regras de Cálculo",
        "menu_cost": "💼 Custo do Empregador",
        "title": "📄 Cálculo do Salário Líquido",
        "country_label": "🌎 Escolha o país",
        "salary_label": "💰 Informe o salário bruto",
        "gross": "Salário Bruto",
        "discounts": "Descontos",
        "net": "Salário Líquido",
        "fgts": "FGTS / Crédito Empregador",
        "employer_cost": "Custo Total do Empregador",
        "discount_detail": "📋 Detalhamento dos Descontos",
        "no_data": "Nenhum dado disponível para este país.",
        "rules_title": "📘 Regras de Cálculo",
        "cost_title": "💼 Custo do Empregador",
        "annual_cost": "💵 Custo anual total",
        "equivalent": "📈 Equivalente a",
        "monthly_equiv": "🗓 Custo mensal equivalente"
    },
    "English": {
        "menu_calc": "📄 Net Salary Calculation",
        "menu_rules": "📘 Calculation Rules",
        "menu_cost": "💼 Employer Cost",
        "title": "📄 Net Salary Calculation",
        "country_label": "🌎 Choose a country",
        "salary_label": "💰 Enter gross salary",
        "gross": "Gross Salary",
        "discounts": "Deductions",
        "net": "Net Salary",
        "fgts": "Employer Credit / FGTS",
        "employer_cost": "Total Employer Cost",
        "discount_detail": "📋 Deductions Breakdown",
        "no_data": "No data available for this country.",
        "rules_title": "📘 Calculation Rules",
        "cost_title": "💼 Employer Cost",
        "annual_cost": "💵 Total Annual Cost",
        "equivalent": "📈 Equivalent to",
        "monthly_equiv": "🗓 Monthly Equivalent Cost"
    },
    "Español": {
        "menu_calc": "📄 Cálculo del Salario Neto",
        "menu_rules": "📘 Reglas de Cálculo",
        "menu_cost": "💼 Costo del Empleador",
        "title": "📄 Cálculo del Salario Neto",
        "country_label": "🌎 Elige el país",
        "salary_label": "💰 Introduce el salario bruto",
        "gross": "Salario Bruto",
        "discounts": "Descuentos",
        "net": "Salario Neto",
        "fgts": "Crédito del Empleador / FGTS",
        "employer_cost": "Costo Total del Empleador",
        "discount_detail": "📋 Detalle de Descuentos",
        "no_data": "No hay datos disponibles para este país.",
        "rules_title": "📘 Reglas de Cálculo",
        "cost_title": "💼 Costo del Empleador",
        "annual_cost": "💵 Costo Anual Total",
        "equivalent": "📈 Equivalente a",
        "monthly_equiv": "🗓 Costo Mensual Equivalente"
    }
}

# -------------------------------------------------------------
# 🌐 Seletor de idioma (recarrega a interface)
# -------------------------------------------------------------
idioma_escolhido = st.sidebar.selectbox("🌐 Idioma / Language / Idioma", list(idiomas.keys()), index=0)
txt = idiomas[idioma_escolhido]

# -------------------------------------------------------------
# 🌎 Configuração de países e moedas
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
# 🧾 URLs dos JSONs (tabelas, regras e custos)
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
# -------------------------------------------------------------
# 💰 Funções utilitárias e de cálculo
# -------------------------------------------------------------

def formatar_moeda(valor, simbolo):
    """Formata valor monetário conforme país."""
    try:
        return f"{simbolo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"{simbolo} {valor}"

def calcular_salario_liquido(pais, salario):
    """Aplica as alíquotas de desconto e crédito por país."""
    if pais not in tabelas:
        # fallback local para o Brasil
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

    descontos = {}
    total_descontos = 0
    fgts = 0

    for d in data["descontos"]:
        nome = d["nome"]
        perc = d["percentual"]
        tipo = d["tipo"]
        valor = salario * perc / 100
        if tipo == "desconto":
            total_descontos += valor
        elif tipo == "credito":
            fgts += valor
        descontos[nome] = valor

    liquido = salario - total_descontos
    custo_total = salario + fgts
    return liquido, descontos, fgts, custo_total


def calcular_custo_empregador(pais, salario):
    """Calcula o custo total do empregador com base nos encargos."""
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
# 🧠 Função de tradução rápida de textos fixos
# -------------------------------------------------------------
def traduzir(txt_key):
    """Retorna a tradução de uma chave textual com base no idioma atual."""
    if idioma_escolhido in idiomas and txt_key in idiomas[idioma_escolhido]:
        return idiomas[idioma_escolhido][txt_key]
    return txt_key

# -------------------------------------------------------------
# 🧭 Função principal para seleção de país
# -------------------------------------------------------------
paises = list(moedas.keys())
pais = st.selectbox(traduzir("country_label"), paises)
simbolo = moedas[pais]["simbolo"]
bandeira = moedas[pais]["bandeira"]

st.markdown(f"<h2 class='sub-header'>{bandeira} {pais}</h2>", unsafe_allow_html=True)

# Campo de entrada de salário
salario = st.number_input(f"{traduzir('salary_label')} ({simbolo})", min_value=0.0, value=10000.00, step=100.0)

# -------------------------------------------------------------
# 📊 Controle de menu com botões horizontais
# -------------------------------------------------------------
menu_labels = {
    "calc": traduzir("menu_calc"),
    "rules": traduzir("menu_rules"),
    "cost": traduzir("menu_cost")
}

st.markdown("<div class='menu-container'>", unsafe_allow_html=True)
cols = st.columns(3)

menu_ativo = st.session_state.get("menu_ativo", "calc")

if cols[0].button(menu_labels["calc"]):
    st.session_state["menu_ativo"] = "calc"
    menu_ativo = "calc"
if cols[1].button(menu_labels["rules"]):
    st.session_state["menu_ativo"] = "rules"
    menu_ativo = "rules"
if cols[2].button(menu_labels["cost"]):
    st.session_state["menu_ativo"] = "cost"
    menu_ativo = "cost"

st.markdown("</div>", unsafe_allow_html=True)
# -------------------------------------------------------------
# 🖥️ Interface principal – Layout do dashboard
# -------------------------------------------------------------

st.markdown(f"<div class='title-header'>{txt['title']}</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 📄 Seção: Cálculo do Salário Líquido
# -------------------------------------------------------------
if menu_ativo == "calc":
    liquido, descontos, fgts, custo_total = calcular_salario_liquido(pais, salario)
    total_descontos = sum(descontos.values())

    # Cards principais
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><h4>{txt['gross']}</h4><h3>{formatar_moeda(salario, simbolo)}</h3></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h4>{txt['discounts']}</h4><h3>{formatar_moeda(total_descontos, simbolo)}</h3></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h4>{txt['net']}</h4><h3>{formatar_moeda(liquido, simbolo)}</h3></div>", unsafe_allow_html=True)

    c4, c5 = st.columns(2)
    with c4:
        st.markdown(f"<div class='metric-card'><h4>{txt['fgts']}</h4><h3>{formatar_moeda(fgts, simbolo)}</h3></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='metric-card'><h4>{txt['employer_cost']}</h4><h3>{formatar_moeda(custo_total, simbolo)}</h3></div>", unsafe_allow_html=True)

    # Detalhamento dos descontos
    st.markdown(f"### {txt['discount_detail']}")
    if descontos:
        df = pd.DataFrame(list(descontos.items()), columns=["Descrição", "Valor"])
        df["Valor"] = df["Valor"].apply(lambda x: formatar_moeda(x, simbolo))
        st.table(df)
    else:
        st.info(txt["no_data"])

# -------------------------------------------------------------
# 📘 Seção: Regras de Cálculo
# -------------------------------------------------------------
elif menu_ativo == "rules":
    st.markdown(f"## {txt['rules_title']}")
    if pais in regras:
        regras_pais = regras[pais].get("pt", {}).get("regras", [])
        if idioma_escolhido == "English":
            regras_pais = regras[pais].get("en", {}).get("regras", regras_pais)
        elif idioma_escolhido == "Español":
            regras_pais = regras[pais].get("es", {}).get("regras", regras_pais)

        for r in regras_pais:
            st.markdown(f"**{r['tipo']}** – {r['explicacao']}")
            if "faixas" in r:
                df = pd.DataFrame(r["faixas"])
                st.dataframe(df)
    else:
        st.info(txt["no_data"])

# -------------------------------------------------------------
# 💼 Seção: Custo do Empregador
# -------------------------------------------------------------
elif menu_ativo == "cost":
    st.markdown(f"## {txt['cost_title']}")
    resultado = calcular_custo_empregador(pais, salario)
    if resultado:
        custo_anual, custo_mensal_equiv, multiplicador, encargos = resultado

        st.markdown(f"### {txt['annual_cost']}: {formatar_moeda(custo_anual, simbolo)}")
        st.markdown(f"**{txt['equivalent']}**: {multiplicador:.3f} × {txt['gross'].lower()}")
        st.markdown(f"**{txt['monthly_equiv']}**: {formatar_moeda(custo_mensal_equiv, simbolo)}")

        st.markdown("### 📑 Encargos Patronais")
        df = pd.DataFrame(encargos)
        df["Aplica sobre"] = df["base"]
        df["Férias"] = df["ferias"].apply(lambda x: "✅" if x else "❌")
        df["13º"] = df["decimo"].apply(lambda x: "✅" if x else "❌")
        df["Bônus"] = df["bonus"].apply(lambda x: "✅" if x else "❌")
        df.rename(columns={"nome": "Encargo", "percentual": "Percentual (%)", "obs": "Observação"}, inplace=True)
        st.dataframe(df[["Encargo", "Percentual (%)", "Aplica sobre", "Férias", "13º", "Bônus", "Observação"]])
    else:
        st.info(txt["no_data"])
