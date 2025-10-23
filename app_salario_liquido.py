import streamlit as st
import requests
import json

# ============================================
# 🔹 CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(page_title="Calculadora Internacional de Salário Líquido", page_icon="💰", layout="centered")

# ============================================
# 🔹 SELEÇÃO DE IDIOMA
# ============================================
idiomas = {
    "Português 🇧🇷": "pt",
    "English 🇺🇸": "en",
    "Español 🇪🇸": "es"
}
idioma_escolhido = st.sidebar.radio("🌐 Idioma / Language / Idioma", list(idiomas.keys()))
lang = idiomas[idioma_escolhido]

# ============================================
# 🔹 TEXTOS MULTILÍNGUES
# ============================================
T = {
    "pt": {
        "title": "💰 Calculadora Internacional de Salário Líquido",
        "subtitle": "Versão 2025.6 • Multilíngue • INSS progressivo 🇧🇷 • INFONAVIT 🇲🇽 • State Tax 🇺🇸",
        "choose_country": "🌎 Escolha o país",
        "enter_salary": "Informe o salário bruto ({})",
        "choose_state": "🗽 Escolha o Estado",
        "result_title": "📊 Resultado do Cálculo",
        "gross": "Salário Bruto",
        "net": "Salário Líquido",
        "no_salary": "💡 Digite um valor de salário para calcular.",
        "deductions": "💼 Detalhamento dos descontos:",
        "update_note": "🔄 Atualização automática via GitHub • INSS 🇧🇷 • INFONAVIT 🇲🇽 • 50 estados 🇺🇸",
        "date": "Data de Vigência",
        "last_update": "Última atualização",
        "source": "Fonte oficial"
    },
    "en": {
        "title": "💰 International Net Salary Calculator",
        "subtitle": "Version 2025.6 • Multilingual • Progressive INSS 🇧🇷 • INFONAVIT 🇲🇽 • State Tax 🇺🇸",
        "choose_country": "🌎 Select Country",
        "enter_salary": "Enter Gross Salary ({})",
        "choose_state": "🗽 Select State",
        "result_title": "📊 Calculation Result",
        "gross": "Gross Salary",
        "net": "Net Salary",
        "no_salary": "💡 Please enter a salary amount to calculate.",
        "deductions": "💼 Deductions Breakdown:",
        "update_note": "🔄 Auto-updated from GitHub • INSS 🇧🇷 • INFONAVIT 🇲🇽 • 50 U.S. States 🇺🇸",
        "date": "Effective Date",
        "last_update": "Last Update",
        "source": "Official Source"
    },
    "es": {
        "title": "💰 Calculadora Internacional de Salario Neto",
        "subtitle": "Versión 2025.6 • Multilingüe • INSS progresivo 🇧🇷 • INFONAVIT 🇲🇽 • Impuesto estatal 🇺🇸",
        "choose_country": "🌎 Elige el país",
        "enter_salary": "Introduce el salario bruto ({})",
        "choose_state": "🗽 Elige el Estado",
        "result_title": "📊 Resultado del Cálculo",
        "gross": "Salario Bruto",
        "net": "Salario Neto",
        "no_salary": "💡 Escribe un monto salarial para calcular.",
        "deductions": "💼 Detalle de deducciones:",
        "update_note": "🔄 Actualización automática desde GitHub • INSS 🇧🇷 • INFONAVIT 🇲🇽 • 50 estados 🇺🇸",
        "date": "Fecha de Vigencia",
        "last_update": "Última actualización",
        "source": "Fuente oficial"
    }
}

# ============================================
# 🔹 CARREGAR TABELAS
# ============================================
URL_JSON_GITHUB = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"

@st.cache_data(ttl=86400)
def carregar_tabelas():
    try:
        resp = requests.get(URL_JSON_GITHUB, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        with open("tabelas_salarios.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar tabelas: {e}")
        st.stop()

dados = carregar_tabelas()

# ============================================
# 🔹 BANDEIRAS
# ============================================
bandeiras = {
    "Brasil": "🇧🇷", "Chile": "🇨🇱", "Argentina": "🇦🇷", "Colômbia": "🇨🇴",
    "México": "🇲🇽", "Estados Unidos": "🇺🇸", "Canadá": "🇨🇦"
}

# ============================================
# 🔹 INTERFACE DE SELEÇÃO
# ============================================
st.title(T[lang]["title"])
st.caption(T[lang]["subtitle"])

paises = [p["pais"] for p in dados["paises"]]
pais_selecionado = st.selectbox(T[lang]["choose_country"], paises)
pais_dados = next((p for p in dados["paises"] if p["pais"] == pais_selecionado), None)
moeda = pais_dados.get("moeda", "")
bandeira = bandeiras.get(pais_selecionado, "🌍")
st.markdown(f"### {bandeira} {pais_selecionado}")

# ============================================
# 🔹 STATE TAX EUA
# ============================================
state_tax_rates = {
    "California": 0.093, "Florida": 0.00, "New York": 0.0645, "Texas": 0.00, "Illinois": 0.0495,
    "Massachusetts": 0.05, "Washington": 0.00, "Oregon": 0.0875, "Georgia": 0.0575, "Colorado": 0.045
}
estado_selecionado, state_tax_rate = None, 0.0
if pais_selecionado == "Estados Unidos":
    estado_selecionado = st.selectbox(T[lang]["choose_state"], list(state_tax_rates.keys()))
    state_tax_rate = state_tax_rates[estado_selecionado]

# ============================================
# 🔹 ENTRADA DE SALÁRIO
# ============================================
salario_bruto = st.number_input(T[lang]["enter_salary"].format(moeda), min_value=0.0, step=100.0, format="%.2f")
if salario_bruto <= 0:
    st.info(T[lang]["no_salary"])
    st.stop()

# ============================================
# 🔹 CÁLCULO
# ============================================
def calcular_liquido(pais, salario):
    descontos_aplicados = []
    total_descontos = 0.0

    for d in pais["descontos"]:
        aliquota = 0.0
        if isinstance(d.get("parte_empregado"), list):
            for faixa in d["parte_empregado"]:
                if faixa["faixa_fim"] is None or salario <= faixa["faixa_fim"]:
                    aliquota = faixa["aliquota"]
                    break
        else:
            aliquota = d.get("parte_empregado", 0)

        valor_desc = salario * aliquota

        # INSS progressivo com teto
        if pais["pais"] == "Brasil" and "INSS" in d["tipo"].upper():
            teto_inss = pais.get("teto_inss", 908.85)
            if salario > 8157.41:
                valor_desc = teto_inss
            else:
                faixas = [(1412.00, 0.075), (2666.68, 0.09), (4000.03, 0.12), (8157.41, 0.14)]
                inss = 0
                restante = salario
                for limite, aliquota_faixa in faixas:
                    if restante > limite:
                        inss += limite * aliquota_faixa
                        restante -= limite
                    else:
                        inss += restante * aliquota_faixa
                        break
                valor_desc = min(inss, teto_inss)

        # INFONAVIT México
        if pais["pais"] == "México" and "INFONAVIT" in d["tipo"].upper():
            if aliquota == 0:
                aliquota = 0.05
                valor_desc = salario * aliquota

        total_descontos += valor_desc
        descontos_aplicados.append((d["tipo"], aliquota * 100, valor_desc))

    # STATE TAX EUA
    if pais["pais"] == "Estados Unidos" and state_tax_rate > 0:
        state_tax = salario * state_tax_rate
        total_descontos += state_tax
        descontos_aplicados.append((f"State Tax ({estado_selecionado})", state_tax_rate * 100, state_tax))

    salario_liquido = salario - total_descontos
    return salario_liquido, descontos_aplicados

# ============================================
# 🔹 RESULTADOS
# ============================================
salario_liquido, descontos = calcular_liquido(pais_dados, salario_bruto)
st.subheader(T[lang]["result_title"])

col1, col2 = st.columns(2)
col1.metric(T[lang]["gross"], f"{salario_bruto:,.2f} {moeda}")
col2.metric(T[lang]["net"], f"{salario_liquido:,.2f} {moeda}")

st.markdown("---")
st.markdown(f"**{T[lang]['date']}:** {pais_dados.get('vigencia_inicio', '-')}")
st.markdown(f"**{T[lang]['last_update']}:** {pais_dados.get('ultima_atualizacao', '-')}")
st.markdown(f"**{T[lang]['source']}:** {pais_dados.get('fonte', '-')}")

st.markdown("### " + T[lang]["deductions"])
tabela = []
for tipo, aliquota, valor in descontos:
    tabela.append({"Tipo": tipo, "Alíquota (%)": round(aliquota, 2), f"Valor ({moeda})": round(valor, 2)})
st.table(tabela)

st.markdown("---")
st.caption(T[lang]["update_note"])
