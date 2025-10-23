import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
from forex_python.converter import CurrencyRates

# ============================================
# 🔹 CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(
    page_title="Calculadora Internacional de Salário Líquido",
    page_icon="🌍",
    layout="centered"
)

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
        "menu_calc": "📊 Cálculo do Salário Líquido",
        "menu_rules": "📘 Regras de Cálculo",
        "title": "Calculadora Internacional de Salário Líquido",
        "subtitle": "Versão 2025.9 • Layout Executivo Global • FGTS como crédito 🇧🇷 • Conversão cambial 🌍",
        "choose_country": "🌎 Escolha o país",
        "enter_salary": "Informe o salário bruto ({})",
        "choose_state": "🗽 Escolha o Estado (para EUA)",
        "result_title": "📊 Resultado do Cálculo",
        "gross": "Salário Bruto",
        "net": "Salário Líquido",
        "fgts_credit": "Crédito FGTS",
        "deductions": "💼 Detalhamento dos descontos:",
        "rules_select": "Selecione o país para visualizar as regras:",
        "update_note": "🔄 Atualização automática via GitHub • INSS 🇧🇷 • FGTS • INFONAVIT 🇲🇽 • State Tax 🇺🇸",
        "total_deductions": "Descontos Totais",
        "usd_equivalent": "Equivalente aproximado em USD"
    },
    "en": {
        "menu_calc": "📊 Net Salary Calculation",
        "menu_rules": "📘 Calculation Rules",
        "title": "International Net Salary Calculator",
        "subtitle": "Version 2025.9 • Executive Layout • FGTS as Credit 🇧🇷 • Currency conversion 🌍",
        "choose_country": "🌎 Select Country",
        "enter_salary": "Enter Gross Salary ({})",
        "choose_state": "🗽 Select State (for USA)",
        "result_title": "📊 Calculation Result",
        "gross": "Gross Salary",
        "net": "Net Salary",
        "fgts_credit": "FGTS Credit",
        "deductions": "💼 Deductions Breakdown:",
        "rules_select": "Select a country to view calculation rules:",
        "update_note": "🔄 Auto-updated from GitHub • INSS 🇧🇷 • FGTS • INFONAVIT 🇲🇽 • State Tax 🇺🇸",
        "total_deductions": "Total Deductions",
        "usd_equivalent": "Approx. Equivalent in USD"
    },
    "es": {
        "menu_calc": "📊 Cálculo del Salario Neto",
        "menu_rules": "📘 Reglas de Cálculo",
        "title": "Calculadora Internacional de Salario Neto",
        "subtitle": "Versión 2025.9 • Diseño Ejecutivo Global • FGTS como crédito 🇧🇷 • Conversión monetaria 🌍",
        "choose_country": "🌎 Elige el país",
        "enter_salary": "Introduce el salario bruto ({})",
        "choose_state": "🗽 Elige el Estado (para EE.UU.)",
        "result_title": "📊 Resultado del Cálculo",
        "gross": "Salario Bruto",
        "net": "Salario Neto",
        "fgts_credit": "Crédito FGTS",
        "deductions": "💼 Detalle de deducciones:",
        "rules_select": "Selecciona el país para ver las reglas:",
        "update_note": "🔄 Actualización automática desde GitHub • INSS 🇧🇷 • FGTS • INFONAVIT 🇲🇽 • State Tax 🇺🇸",
        "total_deductions": "Descuentos Totales",
        "usd_equivalent": "Equivalente aproximado en USD"
    }
}

# ============================================
# 🔹 CARREGAR TABELAS DO GITHUB
# ============================================
URL_JSON_GITHUB = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"

@st.cache_data(ttl=86400)
def carregar_tabelas():
    try:
        r = requests.get(URL_JSON_GITHUB, timeout=10)
        if r.status_code == 200:
            return r.json()
        with open("tabelas_salarios.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
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
# 🔹 MENU LATERAL
# ============================================
menu = st.sidebar.radio("📂 Menu Principal", [T[lang]["menu_calc"], T[lang]["menu_rules"]])

# ============================================
# 🔹 LAYOUT PRINCIPAL
# ============================================
st.markdown(f"## {T[lang]['title']}")
st.caption(T[lang]["subtitle"])

# =========================================================
# 🧮 CÁLCULO DO SALÁRIO LÍQUIDO
# =========================================================
if menu == T[lang]["menu_calc"]:

    paises = [p["pais"] for p in dados["paises"]]
    pais_selecionado = st.selectbox(T[lang]["choose_country"], paises)
    pais_dados = next((p for p in dados["paises"] if p["pais"] == pais_selecionado), None)
    moeda = pais_dados.get("moeda", "")
    bandeira = bandeiras.get(pais_selecionado, "🌍")

    st.markdown(f"### {bandeira} {pais_selecionado}")
    salario_bruto = st.number_input(T[lang]["enter_salary"].format(moeda), min_value=0.0, step=100.0, format="%.2f")

    # Estados (EUA)
    state_tax_rate, estado_selecionado = 0.0, None
    if pais_selecionado == "Estados Unidos":
        state_tax_rates = {
            "California": 0.093, "Florida": 0.00, "New York": 0.0645, "Texas": 0.00, "Illinois": 0.0495
        }
        estado_selecionado = st.selectbox(T[lang]["choose_state"], list(state_tax_rates.keys()))
        state_tax_rate = state_tax_rates[estado_selecionado]

    if salario_bruto > 0:
        # Cálculo
        def calcular_liquido(pais, salario):
            descontos_aplicados, total_descontos, fgts_credito = [], 0.0, 0.0
            for d in pais["descontos"]:
                aliquota = d.get("parte_empregado", 0)
                valor_desc = salario * aliquota
                # INSS progressivo 🇧🇷
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
                # FGTS como crédito 🇧🇷
                if pais["pais"] == "Brasil" and "FGTS" in d["tipo"].upper():
                    fgts_credito = salario * 0.08
                    continue
                # INFONAVIT 🇲🇽
                if pais["pais"] == "México" and "INFONAVIT" in d["tipo"].upper():
                    if aliquota == 0:
                        aliquota = 0.05
                        valor_desc = salario * aliquota
                total_descontos += valor_desc
                descontos_aplicados.append((d["tipo"], aliquota * 100, valor_desc))
            # State Tax 🇺🇸
            if pais["pais"] == "Estados Unidos" and state_tax_rate > 0:
                stax = salario * state_tax_rate
                total_descontos += stax
                descontos_aplicados.append((f"State Tax ({estado_selecionado})", state_tax_rate * 100, stax))
            salario_liquido = salario - total_descontos
            return salario_liquido, descontos_aplicados, fgts_credito

        salario_liquido, descontos, fgts_credito = calcular_liquido(pais_dados, salario_bruto)

        # Exibição
        st.subheader(T[lang]["result_title"])
        st.metric(T[lang]["gross"], f"{salario_bruto:,.2f} {moeda}")
        st.metric(T[lang]["net"], f"{salario_liquido:,.2f} {moeda}")
        st.metric(T[lang]["fgts_credit"], f"{fgts_credito:,.2f} {moeda}")

        total_desc_percent = ((salario_bruto - salario_liquido) / salario_bruto) * 100
        st.markdown(f"**{T[lang]['total_deductions']}:** {total_desc_percent:.1f}%")

        # Gráfico
        if descontos:
            labels = [d[0] for d in descontos]
            sizes = [d[2] for d in descontos]
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis("equal")
            st.pyplot(fig)

        # Conversão USD
        try:
            c = CurrencyRates()
            valor_usd = c.convert(moeda, 'USD', salario_liquido)
            st.caption(f"💵 {T[lang]['usd_equivalent']}: {valor_usd:,.2f} USD")
        except Exception:
            st.caption("💵 Conversão cambial indisponível no momento.")

        # Tabela
        st.markdown("### " + T[lang]["deductions"])
        tabela = [{"Tipo": tipo, "Alíquota (%)": round(aliquota, 2), f"Valor ({moeda})": round(valor, 2)} for tipo, aliquota, valor in descontos]
        st.table(tabela)

        st.markdown("---")
        st.caption(T[lang]["update_note"])

# =========================================================
# 📘 REGRAS DE CÁLCULO
# =========================================================
elif menu == T[lang]["menu_rules"]:
    pais_regra = st.selectbox(T[lang]["rules_select"], list(bandeiras.keys()))
    bandeira = bandeiras[pais_regra]
    st.markdown(f"### {bandeira} {pais_regra}")

    regras = {
        "Brasil": """
**INSS:** progressivo até R$ 8.157,41 (7,5% a 14%), teto R$ 908,85  
**IRRF:** progressivo conforme Receita Federal  
**FGTS:** 8% do salário bruto — crédito do empregador (não descontado)
        """,
        "Chile": "**AFP:** ~10% • **Saúde:** 7% • **Desemprego:** 0,6%",
        "México": "**IMSS:** ~6% • **ISR:** 1,9%–35% • **INFONAVIT:** 5%",
        "Argentina": "**Jubilación:** 11% • **Obra Social:** 3% • **PAMI:** 3%",
        "Colômbia": "**Saúde:** 4% • **Pensão:** 4% • **Solidariedade:** +1%",
        "Estados Unidos": "**Federal Tax:** até 37% • **Social Security:** 6,2% • **Medicare:** 1,45% • **State Tax:** variável",
        "Canadá": "**CPP:** 5,95% • **EI:** 1,63% • **IR:** federal + provincial"
    }
    st.markdown(regras[pais_regra])
