import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from forex_python.converter import CurrencyRates

# ============================================
# 🔹 CONFIGURAÇÃO INICIAL
# ============================================
st.set_page_config(page_title="Calculadora Internacional de Salário Líquido",
                   page_icon="🌍", layout="centered")

# ============================================
# 🔹 CARREGAR ARQUIVOS DO GITHUB
# ============================================
URL_SALARIOS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"
URL_REGRAS = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/regras_fiscais.json"

@st.cache_data(ttl=86400)
def carregar_json(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Erro ao carregar {url}: {e}")
        st.stop()

dados = carregar_json(URL_SALARIOS)
regras_fiscais = carregar_json(URL_REGRAS)

# ============================================
# 🔹 BANDEIRAS E LINGUAGEM
# ============================================
bandeiras = {
    "Brasil": "🇧🇷", "Chile": "🇨🇱", "Argentina": "🇦🇷",
    "Colômbia": "🇨🇴", "México": "🇲🇽",
    "Estados Unidos": "🇺🇸", "Canadá": "🇨🇦"
}

idiomas = {"Português 🇧🇷": "pt", "English 🇺🇸": "en", "Español 🇪🇸": "es"}
idioma_escolhido = st.sidebar.radio("🌐 Idioma / Language / Idioma", list(idiomas.keys()))
lang = idiomas[idioma_escolhido]

menu = st.sidebar.radio("📂 Menu Principal", ["📊 Cálculo do Salário Líquido", "📘 Regras de Cálculo"])

# ============================================
# 🔹 CABEÇALHO
# ============================================
st.markdown("## 🌍 Calculadora Internacional de Salário Líquido")
st.caption("Versão 2025.13 • Layout Executivo Global • CTC Completo • Conversão Cambial")

# =========================================================
# 📊 CÁLCULO DO SALÁRIO LÍQUIDO
# =========================================================
if menu == "📊 Cálculo do Salário Líquido":

    paises = [p["pais"] for p in dados["paises"]]
    pais = st.selectbox("🌎 Escolha o país", paises)
    info = next(p for p in dados["paises"] if p["pais"] == pais)
    moeda = info.get("moeda", "")
    flag = bandeiras.get(pais, "🌍")

    st.markdown(f"### {flag} {pais}")
    salario = st.number_input(f"Informe o salário bruto ({moeda})",
                              min_value=0.0, step=100.0, format="%.2f")

    # Estados EUA
    state_tax_rate, estado = 0.0, None
    if pais == "Estados Unidos":
        state_tax_rates = {
            "California": 0.093, "Florida": 0.00,
            "New York": 0.0645, "Texas": 0.00, "Illinois": 0.0495
        }
        estado = st.selectbox("🗽 Escolha o Estado", list(state_tax_rates.keys()))
        state_tax_rate = state_tax_rates[estado]

    # =========================================================
    # FUNÇÃO DE CÁLCULO
    # =========================================================
    def calcular(pais, salario):
        descontos, total, fgts, patronal = [], 0, 0, 0
        for d in pais["descontos"]:
            tipo = d["tipo"]
            parte = d.get("parte_empregado", 0)
            # --- tratamento dinâmico de faixas ---
            if isinstance(parte, list):
                aliquota = 0.0
                for faixa in parte:
                    if faixa["faixa_fim"] is None or salario <= faixa["faixa_fim"]:
                        aliquota = faixa["aliquota"]
                        break
            else:
                aliquota = float(parte)
            valor = salario * aliquota

            # 🇧🇷 INSS progressivo
            if pais["pais"] == "Brasil" and "INSS" in tipo.upper():
                teto = pais.get("teto_inss", 908.85)
                if salario > 8157.41:
                    valor = teto
                else:
                    faixas = [(1412, 0.075), (2666.68, 0.09), (4000.03, 0.12), (8157.41, 0.14)]
                    inss, restante = 0, salario
                    for lim, a in faixas:
                        if restante > lim:
                            inss += lim * a
                            restante -= lim
                        else:
                            inss += restante * a
                            break
                    valor = min(inss, teto)

            # 🇧🇷 FGTS
            if pais["pais"] == "Brasil" and "FGTS" in tipo.upper():
                fgts = salario * 0.08
                patronal += fgts
                continue

            # 🇲🇽 INFONAVIT
            if pais["pais"] == "México" and "INFONAVIT" in tipo.upper():
                valor = salario * 0.05

            total += valor
            descontos.append((tipo, aliquota * 100, valor))

        # 🇺🇸 State Tax
        if pais["pais"] == "Estados Unidos" and state_tax_rate > 0:
            stax = salario * state_tax_rate
            total += stax
            descontos.append((f"State Tax ({estado})", state_tax_rate * 100, stax))

        liquido = salario - total
        custo_total = salario + patronal
        return liquido, descontos, fgts, custo_total

    # =========================================================
    # EXECUÇÃO DO CÁLCULO
    # =========================================================
    if salario > 0:
        liquido, desc, fgts, custo = calcular(info, salario)
        st.subheader("📊 Resultado do Cálculo")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bruto", f"{salario:,.2f} {moeda}")
        c2.metric("Líquido", f"{liquido:,.2f} {moeda}")
        c3.metric("FGTS", f"{fgts:,.2f} {moeda}")
        c4.metric("Custo Total", f"{custo:,.2f} {moeda}")

        perc = (salario - liquido) / salario * 100
        st.markdown(f"**Descontos Totais:** {perc:.1f}%")

        if desc:
            labels = [d[0] for d in desc]
            sizes = [d[2] for d in desc]
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)

        # Conversão cambial
        try:
            c = CurrencyRates()
            usd = c.convert(moeda, "USD", liquido)
            st.caption(f"💵 Equivalente aproximado: {usd:,.2f} USD")
        except:
            st.caption("💵 Conversão cambial indisponível no momento.")

        # Tabela detalhada
        st.markdown("### 💼 Detalhamento dos Descontos")
        st.table([{"Tipo": t, "Alíquota (%)": round(a, 2), f"Valor ({moeda})": round(v, 2)} for t, a, v in desc])

        # Exportar PDF/Excel
        df = pd.DataFrame(desc, columns=["Tipo", "Alíquota (%)", f"Valor ({moeda})"])
        excel = BytesIO()
        with pd.ExcelWriter(excel, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        st.download_button("⬇️ Baixar em Excel", data=excel.getvalue(),
                           file_name=f"calculo_{pais}.xlsx", mime="application/vnd.ms-excel")

        # PDF simples
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, f"Relatório de Cálculo - {pais}", ln=True)
        pdf.set_font("Arial", "", 12)
        for t, a, v in desc:
            pdf.cell(200, 8, f"{t}: {a:.1f}% → {v:,.2f} {moeda}", ln=True)
        pdf.cell(200, 10, f"Salário Bruto: {salario:,.2f} {moeda}", ln=True)
        pdf.cell(200, 10, f"Salário Líquido: {liquido:,.2f} {moeda}", ln=True)
        pdf_out = BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button("📄 Baixar PDF", data=pdf_out,
                           file_name=f"relatorio_{pais}.pdf", mime="application/pdf")

# =========================================================
# 📘 REGRAS DE CÁLCULO (JSON EXTERNO)
# =========================================================
elif menu == "📘 Regras de Cálculo":
    pais = st.selectbox("Selecione o país para visualizar as regras:", list(regras_fiscais.keys()))
    flag = bandeiras.get(pais, "🌍")
    st.markdown(f"### {flag} {pais}")

    bloco = regras_fiscais[pais][lang]
    st.markdown(f"#### {bloco['titulo']}")

    for r in bloco["regras"]:
        st.markdown(f"**{r['tipo']}**")
        if "faixas" in r:
            df = pd.DataFrame(r["faixas"])
            st.dataframe(df, use_container_width=True)
        st.markdown(r["explicacao"])
        st.markdown("---")

st.caption("🔄 Atualização automática via GitHub • INSS 🇧🇷 • FGTS • INFONAVIT 🇲🇽 • State Tax 🇺🇸")
