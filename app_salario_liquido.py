import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
from forex_python.converter import CurrencyRates

# ============================================
# 🔹 CONFIGURAÇÃO INICIAL
# ============================================
st.set_page_config(page_title="Calculadora Internacional de Salário Líquido", page_icon="🌍", layout="centered")

# ============================================
# 🔹 IDIOMA
# ============================================
idiomas = {"Português 🇧🇷": "pt", "English 🇺🇸": "en", "Español 🇪🇸": "es"}
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
        "subtitle": "Versão 2025.12 • Layout Executivo Global • Custo Total do Empregador • Conversão cambial 🌍",
        "choose_country": "🌎 Escolha o país",
        "enter_salary": "Informe o salário bruto ({})",
        "choose_state": "🗽 Escolha o Estado (para EUA)",
        "result_title": "📊 Resultado do Cálculo",
        "gross": "Salário Bruto",
        "net": "Salário Líquido",
        "fgts_credit": "Crédito FGTS",
        "deductions": "💼 Detalhamento dos descontos:",
        "total_deductions": "Descontos Totais",
        "usd_equivalent": "Equivalente aproximado em USD",
        "employer_cost": "Custo Total do Empregador",
        "rules_select": "Selecione o país para visualizar as regras de cálculo:",
        "update_note": "🔄 Atualização automática via GitHub • INSS 🇧🇷 • FGTS • INFONAVIT 🇲🇽 • State Tax 🇺🇸"
    }
}

# ============================================
# 🔹 CARREGAR DADOS DO GITHUB
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
# 🔹 MENU
# ============================================
menu = st.sidebar.radio("📂 Menu Principal", [T["pt"]["menu_calc"], T["pt"]["menu_rules"]])

# ============================================
# 🔹 INTERFACE PRINCIPAL
# ============================================
st.markdown(f"## {T['pt']['title']}")
st.caption(T["pt"]["subtitle"])

# =========================================================
# 📊 CÁLCULO DO SALÁRIO LÍQUIDO
# =========================================================
if menu == T["pt"]["menu_calc"]:
    paises = [p["pais"] for p in dados["paises"]]
    pais = st.selectbox(T["pt"]["choose_country"], paises)
    info = next(p for p in dados["paises"] if p["pais"] == pais)
    moeda = info.get("moeda", "")
    flag = bandeiras.get(pais, "🌍")

    st.markdown(f"### {flag} {pais}")
    salario = st.number_input(T["pt"]["enter_salary"].format(moeda), min_value=0.0, step=100.0, format="%.2f")

    # Estados EUA
    state_tax_rate, estado = 0.0, None
    if pais == "Estados Unidos":
        state_tax_rates = {"California": 0.093, "Florida": 0.00, "New York": 0.0645, "Texas": 0.00, "Illinois": 0.0495}
        estado = st.selectbox(T["pt"]["choose_state"], list(state_tax_rates.keys()))
        state_tax_rate = state_tax_rates[estado]

    if salario > 0:
        # === CÁLCULO ===
        def calcular(pais, salario):
            descontos, total, fgts, patronal = [], 0, 0, 0
            for d in pais["descontos"]:
                tipo = d["tipo"]
                aliquota = d.get("parte_empregado", 0)
                valor = salario * aliquota

                if pais["pais"] == "Brasil" and "INSS" in tipo.upper():
                    teto = pais.get("teto_inss", 908.85)
                    faixas = [(1412, 0.075), (2666.68, 0.09), (4000.03, 0.12), (8157.41, 0.14)]
                    inss = 0
                    restante = salario
                    for lim, a in faixas:
                        if restante > lim:
                            inss += lim * a
                            restante -= lim
                        else:
                            inss += restante * a
                            break
                    valor = min(inss, teto)

                if pais["pais"] == "Brasil" and "FGTS" in tipo.upper():
                    fgts = salario * 0.08
                    patronal += fgts
                    continue

                if pais["pais"] == "México" and "INFONAVIT" in tipo.upper():
                    valor = salario * 0.05

                total += valor
                descontos.append((tipo, aliquota * 100, valor))

            if pais["pais"] == "Estados Unidos" and state_tax_rate > 0:
                stax = salario * state_tax_rate
                total += stax
                descontos.append((f"State Tax ({estado})", state_tax_rate * 100, stax))

            liquido = salario - total
            custo_total = salario + patronal
            return liquido, descontos, fgts, custo_total

        liquido, desc, fgts, custo = calcular(info, salario)

        # === EXIBIÇÃO ===
        st.subheader(T["pt"]["result_title"])
        st.metric(T["pt"]["gross"], f"{salario:,.2f} {moeda}")
        st.metric(T["pt"]["net"], f"{liquido:,.2f} {moeda}")
        st.metric(T["pt"]["fgts_credit"], f"{fgts:,.2f} {moeda}")
        st.metric(T["pt"]["employer_cost"], f"{custo:,.2f} {moeda}")

        perc = (salario - liquido) / salario * 100
        st.markdown(f"**{T['pt']['total_deductions']}:** {perc:.1f}%")

        if desc:
            labels = [d[0] for d in desc]
            sizes = [d[2] for d in desc]
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)

        try:
            c = CurrencyRates()
            usd = c.convert(moeda, "USD", liquido)
            st.caption(f"💵 {T['pt']['usd_equivalent']}: {usd:,.2f} USD")
        except:
            st.caption("💵 Conversão cambial indisponível no momento.")

        st.markdown("### " + T["pt"]["deductions"])
        st.table([{"Tipo": t, "Alíquota (%)": round(a, 2), f"Valor ({moeda})": round(v, 2)} for t, a, v in desc])
        st.markdown("---")
        st.caption(T["pt"]["update_note"])

# =========================================================
# 📘 REGRAS DE CÁLCULO
# =========================================================
elif menu == T["pt"]["menu_rules"]:
    pais = st.selectbox(T["pt"]["rules_select"], list(bandeiras.keys()))
    flag = bandeiras[pais]
    st.markdown(f"### {flag} {pais}")

    regras = {
        "Brasil": """
**INSS:** progressivo de 7,5 a 14 % até R$ 8.157,41 → R$ 908,85 de teto.  
**IRRF:** tabela progressiva (0 a 27,5 %), após deduzir INSS + dependentes.  
**FGTS:** 8 % do salário bruto — crédito pago pelo empregador.  
**Cálculo:**  
Salário Líquido = Bruto − INSS − IRRF.  
Custo Empregador = Bruto + FGTS.
""",
        "México": """
**IMSS:** ≈ 6 % do salário para seguro social.  
**ISR:** 1,9 % a 35 % progressivo conforme faixa do SAT.  
**INFONAVIT:** 5 % habitação.  
**Cálculo:**  
Líquido = Bruto − (IMSS + ISR + INFONAVIT).  
""",
        "Estados Unidos": """
**Federal Tax:** 10 % a 37 %.  
**Social Security:** 6,2 % até US$ 168 600.  
**Medicare:** 1,45 %.  
**State Tax:** 0 a 10 % (estado dependente).  
**Cálculo:** Bruto − todas as alíquotas.  
""",
        "Argentina": """
**Jubilación:** 11 %.  
**Obra Social:** 3 %.  
**PAMI:** 3 %.  
**Ganancias (IRPF):** 5 a 35 %.  
**Cálculo:** Bruto − soma de encargos sobre a base total.  
""",
        "Chile": """
**AFP:** 10 %.  
**Saúde:** 7 %.  
**Desemprego:** 0,6 %.  
**Cálculo:** Bruto − 17,6 % de descontos totais.  
""",
        "Canadá": """
**CPP:** 5,95 %.  
**EI:** 1,63 %.  
**Imposto de Renda:** progressivo federal + provincial.  
**Cálculo:** Bruto − (IR + CPP + EI).  
""",
        "Colômbia": """
**Saúde:** 4 %.  
**Pensão:** 4 %.  
**Fundo de Solidariedade:** 1 %.  
**Cálculo:** Bruto − (9 % total).  
"""
    }
    st.markdown(regras[pais])
