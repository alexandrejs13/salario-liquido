import streamlit as st
import requests
import json

# ============================================
# 🔹 CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(page_title="Calculadora Internacional de Salário Líquido", page_icon="💰", layout="centered")
st.title("💰 Calculadora Internacional de Salário Líquido")
st.caption("Versão 2025.1 • Dados oficiais de cada país com atualização automática via GitHub")

# ============================================
# 🔹 URL DO ARQUIVO JSON NO GITHUB
# ============================================
URL_JSON_GITHUB = "https://raw.githubusercontent.com/alexandresavoy/salario-liquido/main/tabelas_salarios.json"

# ============================================
# 🔹 FUNÇÃO PARA CARREGAR OS DADOS
# ============================================
@st.cache_data(ttl=86400)  # Atualiza uma vez por dia
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

# ============================================
# 🔹 INTERFACE DE SELEÇÃO
# ============================================
paises = [p["pais"] for p in dados["paises"]]
pais_selecionado = st.selectbox("🌎 Escolha o país", paises)

pais_dados = next(p for p in dados["paises"] if p["pais"] == pais_selecionado)
moeda = pais_dados["moeda"]

salario_bruto = st.number_input(f"Informe o salário bruto ({moeda})", min_value=0.0, step=100.0, format="%.2f")

if salario_bruto <= 0:
    st.info("Digite um valor de salário para calcular.")
    st.stop()

# ============================================
# 🔹 CÁLCULO DO SALÁRIO LÍQUIDO
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
        total_descontos += valor_desc
        descontos_aplicados.append((d["tipo"], aliquota * 100, valor_desc))
    salario_liquido = salario - total_descontos
    return salario_liquido, descontos_aplicados

salario_liquido, descontos = calcular_liquido(pais_dados, salario_bruto)

# ============================================
# 🔹 EXIBIÇÃO DOS RESULTADOS
# ============================================
st.subheader("📊 Resultado do Cálculo")
col1, col2 = st.columns(2)
col1.metric("Salário Bruto", f"{salario_bruto:,.2f} {moeda}")
col2.metric("Salário Líquido", f"{salario_liquido:,.2f} {moeda}")

st.markdown("---")
st.markdown(f"**Data de Vigência:** {pais_dados['vigencia_inicio']}")
st.markdown(f"**Última atualização:** {pais_dados['ultima_atualizacao']}")
st.markdown(f"**Fonte oficial:** {pais_dados['fonte']}")

st.markdown("### 💼 Detalhamento dos descontos:")
tabela = []
for tipo, aliquota, valor in descontos:
    tabela.append({
        "Tipo": tipo,
        "Alíquota (%)": round(aliquota, 2),
        f"Valor ({moeda})": round(valor, 2)
    })
st.table(tabela)

st.markdown("---")
st.caption("🔄 Atualização automática diária via GitHub. "
           "Se o GitHub estiver offline, o app usa a cópia local do JSON.")
