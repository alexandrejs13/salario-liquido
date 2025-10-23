import streamlit as st
import requests
import json

# ============================================
# 🔹 CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(page_title="Calculadora Internacional de Salário Líquido", page_icon="💰", layout="centered")
st.title("💰 Calculadora Internacional de Salário Líquido")
st.caption("Versão 2025.3 • Dados oficiais com atualizações fiscais automáticas via GitHub")

# ============================================
# 🔹 URL DO ARQUIVO JSON NO GITHUB
# ============================================
URL_JSON_GITHUB = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main/tabelas_salarios.json"

# ============================================
# 🔹 FUNÇÃO PARA CARREGAR AS TABELAS
# ============================================
@st.cache_data(ttl=86400)
def carregar_tabelas():
    try:
        resp = requests.get(URL_JSON_GITHUB, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.warning(f"⚠️ Não foi possível baixar do GitHub (HTTP {resp.status_code}). Usando cópia local.")
            with open("tabelas_salarios.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar tabelas: {e}")
        st.stop()

dados = carregar_tabelas()

if not dados or "paises" not in dados:
    st.error("❌ Não foi possível carregar as tabelas de países. Verifique o arquivo JSON no GitHub.")
    st.stop()

# ============================================
# 🔹 MAPA DE BANDEIRAS POR PAÍS
# ============================================
bandeiras = {
    "Brasil": "🇧🇷",
    "Chile": "🇨🇱",
    "Argentina": "🇦🇷",
    "Colômbia": "🇨🇴",
    "México": "🇲🇽",
    "Estados Unidos": "🇺🇸",
    "Canadá": "🇨🇦"
}

# ============================================
# 🔹 SELEÇÃO DE PAÍS
# ============================================
paises = [p["pais"] for p in dados["paises"]]
pais_selecionado = st.selectbox("🌎 Escolha o país", paises)

pais_dados = next((p for p in dados["paises"] if p["pais"] == pais_selecionado), None)
if not pais_dados:
    st.error("❌ Dados do país selecionado não encontrados.")
    st.stop()

moeda = pais_dados.get("moeda", "")

# ============================================
# 🔹 EXIBE BANDEIRA E NOME DO PAÍS
# ============================================
bandeira = bandeiras.get(pais_selecionado, "🌍")
st.markdown(f"### {bandeira} {pais_selecionado}")

# ============================================
# 🔹 SELETOR ADICIONAL PARA ESTADOS (EUA)
# ============================================
estado_selecionado = None
state_tax_rate = 0.0
if pais_selecionado == "Estados Unidos":
    estados = {
        "California": 0.093,
        "Florida": 0.00,
        "New York": 0.0645,
        "Texas": 0.00,
        "Illinois": 0.0495,
        "Massachusetts": 0.05,
        "Washington": 0.00
    }
    estado_selecionado = st.selectbox("🗽 Escolha o Estado", list(estados.keys()))
    state_tax_rate = estados[estado_selecionado]

# ============================================
# 🔹 ENTRADA DE SALÁRIO
# ============================================
salario_bruto = st.number_input(
    f"Informe o salário bruto ({moeda})",
    min_value=0.0,
    step=100.0,
    format="%.2f"
)

if salario_bruto <= 0:
    st.info("💡 Digite um valor de salário para calcular.")
    st.stop()

# ============================================
# 🔹 FUNÇÃO DE CÁLCULO
# ============================================
def calcular_liquido(pais, salario):
    descontos_aplicados = []
    total_descontos = 0.0

    for d in pais["descontos"]:
        aliquota = 0.0

        # Faixas progressivas (ex: IR)
        if isinstance(d.get("parte_empregado"), list):
            for faixa in d["parte_empregado"]:
                if faixa["faixa_fim"] is None or salario <= faixa["faixa_fim"]:
                    aliquota = faixa["aliquota"]
                    break
        else:
            aliquota = d.get("parte_empregado", 0)

        valor_desc = salario * aliquota

        # ✅ INSS com teto (Brasil)
        if pais["pais"] == "Brasil" and "INSS" in d["tipo"].upper():
            valor_desc = min(valor_desc, pais.get("teto_inss", 908.85))

        # ✅ INFONAVIT México
        if pais["pais"] == "México" and "INFONAVIT" in d["tipo"].upper():
            if aliquota == 0:
                aliquota = 0.05
                valor_desc = salario * aliquota

        total_descontos += valor_desc
        descontos_aplicados.append((d["tipo"], aliquota * 100, valor_desc))

    # ✅ State Tax EUA
    if pais["pais"] == "Estados Unidos" and state_tax_rate > 0:
        state_tax = salario * state_tax_rate
        total_descontos += state_tax
        descontos_aplicados.append((f"State Tax ({estado_selecionado})", state_tax_rate * 100, state_tax))

    salario_liquido = salario - total_descontos
    return salario_liquido, descontos_aplicados

# ============================================
# 🔹 EXECUTA O CÁLCULO
# ============================================
salario_liquido, descontos = calcular_liquido(pais_dados, salario_bruto)

# ============================================
# 🔹 EXIBE RESULTADOS
# ============================================
st.subheader("📊 Resultado do Cálculo")

col1, col2 = st.columns(2)
col1.metric("Salário Bruto", f"{salario_bruto:,.2f} {moeda}")
col2.metric("Salário Líquido", f"{salario_liquido:,.2f} {moeda}")

st.markdown("---")
st.markdown(f"**Data de Vigência:** {pais_dados.get('vigencia_inicio', '-')}")
st.markdown(f"**Última atualização:** {pais_dados.get('ultima_atualizacao', '-')}")
st.markdown(f"**Fonte oficial:** {pais_dados.get('fonte', '-')}")

# ============================================
# 🔹 TABELA DE DESCONTOS
# ============================================
st.markdown("### 💼 Detalhamento dos descontos:")

tabela = []
for tipo, aliquota, valor in descontos:
    tabela.append({
        "Tipo": tipo,
        "Alíquota (%)": round(aliquota, 2),
        f"Valor ({moeda})": round(valor, 2)
    })

st.table(tabela)

# ============================================
# 🔹 RODAPÉ
# ============================================
st.markdown("---")
st.caption("🔄 Atualização automática via GitHub • Inclui teto INSS 🇧🇷 • State Tax 🇺🇸 • INFONAVIT 🇲🇽 • Bandeiras oficiais 🌍")
