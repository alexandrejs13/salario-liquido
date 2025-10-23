# -------------------------------------------------------------
# 📘 Calculadora Global de Salário Líquido – v2025.16
# Layout Executivo Global HR com bandeiras, cards e custos
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import json

# -------------------------------------------------------------
# ⚙️ Configuração inicial
# -------------------------------------------------------------
st.set_page_config(page_title="Calculadora Global de Salário Líquido", layout="wide")

st.markdown("""
    <style>
    /* Layout corporativo */
    .metric-card {
        text-align: center;
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }
    h1, h2, h3 {
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        color: #222;
    }
    .stTable tr th {
        background-color: #f0f2f6;
        font-weight: 600;
    }
    .country-flag {
        font-size: 42px;
        margin-right: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🌍 Configurações básicas
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
# 📦 Funções de carregamento
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

# URLs dos JSONs
URL_TABELAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"
URL_REGRAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/regras_fiscais.json"
URL_CUSTOS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/custos_empregador.json"

tabelas = carregar_json(URL_TABELAS)
regras = carregar_json(URL_REGRAS)
custos = carregar_json(URL_CUSTOS)

# -------------------------------------------------------------
# 💰 Funções de cálculo
# -------------------------------------------------------------
def calcular_salario_liquido(pais, salario):
    """Aplica as alíquotas de desconto de cada país"""
    if pais not in tabelas:
        # Fallback local se JSON não estiver carregado
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


def formatar_moeda(valor, simbolo):
    return f"{simbolo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# -------------------------------------------------------------
# 🧾 Cálculo do custo do empregado
# -------------------------------------------------------------
def calcular_custo_empregado(pais, salario):
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
st.markdown("<h1>🌍 Calculadora Global de Salário Líquido – v2025.16</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("Menu", ["📊 Cálculo do Salário Líquido", "📘 Regras de Cálculo", "💼 Custo do Empregado"])

# Seleção de país e exibição da bandeira
pais = st.selectbox("🌎 Escolha o país", list(moedas.keys()))
simbolo = moedas[pais]["simbolo"]
bandeira = moedas[pais]["bandeira"]

st.markdown(f"<h2>{bandeira} {pais}</h2>", unsafe_allow_html=True)
salario = st.number_input(f"💰 Informe o salário bruto ({simbolo})", min_value=0.0, value=10000.00, step=100.0)

# -------------------------------------------------------------
# 📊 Módulo 1 – Cálculo do Salário Líquido
# -------------------------------------------------------------
if menu == "📊 Cálculo do Salário Líquido":
    st.markdown("## 📊 Cálculo do Salário Líquido")

    liquido, descontos, fgts, custo_total = calcular_salario_liquido(pais, salario)
    total_descontos = sum(descontos.values())

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><h4>💰 Salário Bruto</h4><h3>{formatar_moeda(salario, simbolo)}</h3></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h4>💸 Descontos</h4><h3>{formatar_moeda(total_descontos, simbolo)}</h3></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h4>🟦 Salário Líquido</h4><h3>{formatar_moeda(liquido, simbolo)}</h3></div>", unsafe_allow_html=True)

    c4, c5 = st.columns(2)
    with c4:
        st.markdown(f"<div class='metric-card'><h4>🟩 FGTS / Crédito Empregador</h4><h3>{formatar_moeda(fgts, simbolo)}</h3></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='metric-card'><h4>🟧 Custo Total Empregador</h4><h3>{formatar_moeda(custo_total, simbolo)}</h3></div>", unsafe_allow_html=True)

    st.markdown("### 📋 Detalhamento dos Descontos")
    if descontos:
        df = pd.DataFrame(list(descontos.items()), columns=["Tipo", "Valor"])
        df["Valor"] = df["Valor"].apply(lambda x: formatar_moeda(x, simbolo))
        st.table(df)
    else:
        st.info("Nenhum desconto configurado para este país.")

# -------------------------------------------------------------
# 📘 Módulo 2 – Regras de Cálculo
# -------------------------------------------------------------
elif menu == "📘 Regras de Cálculo":
    st.markdown("## 📘 Regras de Cálculo")
    if pais in regras:
        for r in regras[pais]["pt"]["regras"]:
            st.markdown(f"**{r['tipo']}** – {r['explicacao']}")
            if "faixas" in r:
                df = pd.DataFrame(r["faixas"])
                st.dataframe(df)
    else:
        st.info("Nenhuma regra cadastrada para este país.")

# -------------------------------------------------------------
# 💼 Módulo 3 – Custo do Empregado
# -------------------------------------------------------------
elif menu == "💼 Custo do Empregado":
    st.markdown("## 💼 Custo do Empregado")
    resultado = calcular_custo_empregado(pais, salario)
    if resultado:
        custo_anual, custo_mensal_equiv, multiplicador, encargos = resultado
        st.markdown(f"💵 **Custo anual total:** {formatar_moeda(custo_anual, simbolo)}")
        st.markdown(f"📈 **Equivalente a:** {multiplicador:.3f} × salário bruto mensal")
        st.markdown(f"🗓 **Custo mensal equivalente:** {formatar_moeda(custo_mensal_equiv, simbolo)}")

        st.markdown("### 📑 Encargos Patronais")
        df = pd.DataFrame(encargos)
        df["Aplica sobre"] = df["base"]
        df["Incide Férias"] = df["ferias"].apply(lambda x: "✅" if x else "❌")
        df["Incide 13º"] = df["decimo"].apply(lambda x: "✅" if x else "❌")
        df["Incide Bônus"] = df["bonus"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df[["nome", "percentual", "Aplica sobre", "Incide Férias", "Incide 13º", "Incide Bônus", "obs"]])
    else:
        st.info("Nenhum dado disponível para este país.")
