import streamlit as st
import pandas as pd
import json
import requests

# -------------------------------------------------------------
# Configuração inicial
# -------------------------------------------------------------
st.set_page_config(page_title="Calculadora Global de Salário Líquido", layout="wide")

# Idioma padrão
idioma_padrao = "Português"

# -------------------------------------------------------------
# Funções utilitárias
# -------------------------------------------------------------
def carregar_json(url):
    """Carrega arquivos JSON locais ou do GitHub"""
    try:
        if url.startswith("http"):
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp.json()
            else:
                st.warning(f"Não foi possível carregar {url}")
                return {}
        else:
            with open(url, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar {url}: {e}")
        return {}

def formatar_moeda(valor, simbolo):
    """Formata o valor monetário com o símbolo do país"""
    try:
        if simbolo in ["R$", "MX$", "US$", "CAD$", "CLP$", "COP$", "ARS$"]:
            return f"{simbolo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"{simbolo} {valor:,.2f}"
    except:
        return f"{simbolo} {valor}"

# -------------------------------------------------------------
# URLs dos arquivos JSON
# -------------------------------------------------------------
URL_TABELAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"
URL_REGRAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/regras_fiscais.json"
URL_CUSTOS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/custos_empregador.json"

# -------------------------------------------------------------
# Carregamento de dados
# -------------------------------------------------------------
tabelas = carregar_json(URL_TABELAS)
regras = carregar_json(URL_REGRAS)
custos = carregar_json(URL_CUSTOS)

# -------------------------------------------------------------
# Funções de cálculo
# -------------------------------------------------------------
def calcular_salario_liquido(pais, salario):
    if pais not in tabelas:
        return 0, {}, 0, 0

    data = tabelas[pais]
    descontos = {}
    total_descontos = 0
    fgts = 0

    for d in data["descontos"]:
        nome = d["nome"]
        tipo = d["tipo"]
        perc = d["percentual"]
        if tipo == "desconto":
            valor = salario * perc / 100
            total_descontos += valor
        else:
            valor = salario * perc / 100
            fgts += valor
        descontos[nome] = valor

    liquido = salario - total_descontos
    custo_total = salario + fgts
    return liquido, descontos, fgts, custo_total

def calcular_custo_empregado(pais, salario):
    if pais not in custos:
        return None
    dados = custos[pais]
    fator = dados["fator_salarios_ano"]
    encargos = dados["encargos"]
    total_encargos = sum([e["percentual"] for e in encargos])
    custo_anual = salario * fator * (1 + total_encargos / 100)
    custo_mensal_equiv = custo_anual / 12
    multiplicador = custo_anual / (salario * 12)
    return custo_anual, custo_mensal_equiv, multiplicador, encargos

# -------------------------------------------------------------
# Dicionário de símbolos monetários
# -------------------------------------------------------------
moedas = {
    "Brasil": "R$",
    "Chile": "CLP$",
    "México": "MX$",
    "Estados Unidos": "US$",
    "Canadá": "CAD$",
    "Colômbia": "COP$",
    "Argentina": "ARS$"
}

# -------------------------------------------------------------
# Interface principal
# -------------------------------------------------------------
st.title("🌍 Calculadora Global de Salário Líquido – v2025.15")

menu = st.sidebar.radio("Menu", ["📊 Cálculo do Salário Líquido", "📘 Regras de Cálculo", "💼 Custo do Empregado"])

paises = list(moedas.keys())
pais = st.sidebar.selectbox("Selecione o país", paises, index=0)
simbolo = moedas.get(pais, "R$")

salario = st.sidebar.number_input("Informe o salário bruto mensal", min_value=0.0, value=10000.0, step=100.0)

# -------------------------------------------------------------
# 📊 Cálculo do Salário Líquido
# -------------------------------------------------------------
if menu == "📊 Cálculo do Salário Líquido":
    st.header(f"📊 Cálculo do Salário Líquido – {pais}")
    liquido, descontos, fgts, custo_total = calcular_salario_liquido(pais, salario)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Salário Bruto", formatar_moeda(salario, simbolo))
    col2.metric("💸 Descontos", formatar_moeda(sum(descontos.values()), simbolo))
    col3.metric("🟩 FGTS / Crédito Empregador", formatar_moeda(fgts, simbolo))
    col4.metric("🟦 Salário Líquido", formatar_moeda(liquido, simbolo))
    col5.metric("🟧 Custo Total Empregador", formatar_moeda(custo_total, simbolo))

    st.subheader("Detalhamento dos Descontos")
    df = pd.DataFrame(descontos.items(), columns=["Tipo", "Valor"])
    df["Valor"] = df["Valor"].apply(lambda x: formatar_moeda(x, simbolo))
    st.table(df)

# -------------------------------------------------------------
# 📘 Regras de Cálculo
# -------------------------------------------------------------
elif menu == "📘 Regras de Cálculo":
    st.header(f"📘 Regras de Cálculo – {pais}")
    if pais in regras:
        regras_pais = regras[pais]["pt"]["regras"]
        for r in regras_pais:
            st.markdown(f"**{r['tipo']}** – {r['explicacao']}")
            if "faixas" in r:
                df = pd.DataFrame(r["faixas"])
                st.dataframe(df)
    else:
        st.info("Nenhuma regra cadastrada para este país.")

# -------------------------------------------------------------
# 💼 Custo do Empregado
# -------------------------------------------------------------
elif menu == "💼 Custo do Empregado":
    st.header(f"💼 Custo do Empregado – {pais}")
    resultado = calcular_custo_empregado(pais, salario)
    if resultado:
        custo_anual, custo_mensal_equiv, multiplicador, encargos = resultado
        st.markdown(f"💵 **Custo anual total:** {formatar_moeda(custo_anual, simbolo)}")
        st.markdown(f"📈 **Equivalente a:** {multiplicador:.3f} × salário bruto mensal")
        st.markdown(f"🗓 **Custo mensal equivalente:** {formatar_moeda(custo_mensal_equiv, simbolo)}")

        st.subheader("Encargos Patronais")
        df = pd.DataFrame(encargos)
        df["Aplica sobre"] = df["base"]
        df["Incide sobre Férias"] = df["ferias"].apply(lambda x: "✅" if x else "❌")
        df["Incide sobre 13º"] = df["decimo"].apply(lambda x: "✅" if x else "❌")
        df["Incide sobre Bônus"] = df["bonus"].apply(lambda x: "✅" if x else "❌")
        df["Percentual (%)"] = df["percentual"]
        st.dataframe(df[["nome", "Percentual (%)", "Aplica sobre", "Incide sobre Férias", "Incide sobre 13º", "Incide sobre Bônus", "obs"]])
    else:
        st.info("Nenhum dado disponível para este país.")
