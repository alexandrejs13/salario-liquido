# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.43)
# -------------------------------------------------------------
import streamlit as st
import pandas as pd
import altair as alt
import requests
from typing import Dict, Any, Tuple

st.set_page_config(
    page_title="Simulador de Salário Líquido e Custo do Empregador",
    layout="wide",
)

# ======================== ENDPOINTS REMOTOS =========================
RAW_BASE = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main"
URL_US_STATES = f"{RAW_BASE}/us_state_tax_rates.json"
URL_COUNTRY_TABLES = f"{RAW_BASE}/country_tables.json"
URL_BR_INSS = f"{RAW_BASE}/br_inss.json"
URL_BR_IRRF = f"{RAW_BASE}/br_irrf.json"

# ============================== CSS ================================
st.markdown("""
<style>
html, body {
  font-family:'Segoe UI', Helvetica, Arial, sans-serif;
  background:#f8fafc;
  color:#1a1a1a;
}
h1,h2,h3 { color:#0a3d62; }
hr { border:0; height:1px; background:#e0e6ed; margin:16px 0; }

/* ===== Sidebar ===== */
section[data-testid="stSidebar"]{
  background:#0a3d62 !important;
  padding-top:8px;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
  color:#ffffff !important;
}
section[data-testid="stSidebar"] .stButton>button{
  background:#ffffff !important;
  color:#0a3d62 !important;
  border:none !important;
  border-radius:6px !important;
  font-weight:600 !important;
  box-shadow:none !important;
}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:#e5edf7 !important;
}

/* ===== Cards ===== */
.metric-card {
  background:#ffffff;
  border:1px solid #dfe4ea;
  border-radius:10px;
  padding:12px;
  text-align:center;
  box-shadow:none;
  transition:all 0.2s ease-in-out;
}
.metric-card:hover { background:#f7faff; }
.metric-card h4 {
  margin:0;
  font-size:13px;
  color:#0a3d62;
  font-weight:600;
}
.metric-card h3 {
  margin:4px 0 0;
  color:#0a3d62;
  font-size:18px;
  font-weight:700;
}

/* Tabela */
.table-wrap {
  background:#fff;
  border:1px solid #d0d7de;
  border-radius:8px;
  overflow:hidden;
}

/* Cabeçalho País */
.country-header {
  display:flex;
  align-items:center;
  gap:10px;
}
.country-flag { font-size:28px; }
.country-title { font-size:24px; font-weight:700; color:#0a3d62; }

/* Cards compactos horizontais */
.metric-card.compact {
  padding:12px;
  border:1px solid #dfe4ea;
  border-radius:10px;
  background:#fff;
  min-height:100px;
  box-shadow:none;
}
.metric-card.compact h4 { margin:0; font-size:13px; color:#0a3d62; font-weight:600;}
.metric-card.compact h3 { margin:4px 0 0; font-size:18px; color:#0a3d62; font-weight:700;}
.sti-note { margin-top:6px; font-size:12px; }

/* Responsivo */
@media (max-width: 768px){
  .metric-row { flex-direction:column; }
}
</style>
""", unsafe_allow_html=True)

# ============================== HELPERS ===============================
def fmt_money(v: float, sym: str) -> str:
    return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def money_or_blank(v: float, sym: str) -> str:
    return "" if abs(v) < 1e-9 else fmt_money(v, sym)

# ======================== CONFIGURAÇÕES E DADOS ======================
COUNTRIES = {
    "Brasil": {"symbol": "R$", "flag": "🇧🇷", "valid_from": "2025-01-01"},
    "México": {"symbol": "MX$", "flag": "🇲🇽", "valid_from": "2025-01-01"},
    "Chile": {"symbol": "CLP$", "flag": "🇨🇱", "valid_from": "2025-01-01"},
    "Argentina": {"symbol": "ARS$", "flag": "🇦🇷", "valid_from": "2025-01-01"},
    "Colômbia": {"symbol": "COP$", "flag": "🇨🇴", "valid_from": "2025-01-01"},
    "Estados Unidos": {"symbol": "US$", "flag": "🇺🇸", "valid_from": "2025-01-01"},
    "Canadá": {"symbol": "CAD$", "flag": "🇨🇦", "valid_from": "2025-01-01"},
}

REMUN_MONTHS_DEFAULT = {
    "Brasil": 13.33, "México": 12.5, "Chile": 12.0, "Argentina": 13.0,
    "Colômbia": 13.0, "Estados Unidos": 12.0, "Canadá": 12.0
}

# ============== STI RANGES (Sales / Non Sales) ==============
STI_RANGES = {
    "Non Sales": {
        "CEO": (1.00, 1.00),
        "Members of the GEB": (0.50, 0.80),
        "Executive Manager": (0.45, 0.70),
        "Senior Group Manager": (0.40, 0.60),
        "Group Manager": (0.30, 0.50),
        "Lead Expert / Program Manager": (0.25, 0.40),
        "Senior Manager": (0.20, 0.40),
        "Senior Expert / Senior Project Manager": (0.15, 0.35),
        "Manager / Selected Expert / Project Manager": (0.10, 0.30),
        "Others": (0.0, 0.10),  # ≤ 10%
    },
    "Sales": {
        "Executive Manager / Senior Group Manager": (0.45, 0.70),
        "Group Manager / Lead Sales Manager": (0.35, 0.50),
        "Senior Manager / Senior Sales Manager": (0.25, 0.45),
        "Manager / Selected Sales Manager": (0.20, 0.35),
        "Others": (0.0, 0.15),  # ≤ 15%
    },
}

STI_LEVEL_OPTIONS = {
    "Non Sales": [
        "CEO", "Members of the GEB", "Executive Manager", "Senior Group Manager",
        "Group Manager", "Lead Expert / Program Manager", "Senior Manager",
        "Senior Expert / Senior Project Manager", "Manager / Selected Expert / Project Manager", "Others"
    ],
    "Sales": [
        "Executive Manager / Senior Group Manager", "Group Manager / Lead Sales Manager",
        "Senior Manager / Senior Sales Manager", "Manager / Selected Sales Manager", "Others"
    ],
}

def get_sti_range(area: str, level: str) -> Tuple[float, float]:
    return STI_RANGES.get(area, {}).get(level, (0.0, None))

# ======================== FETCH REMOTO AUTO =======================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=6)
    r.raise_for_status()
    return r.json()

def load_tables() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    try:
        us_states = fetch_json(URL_US_STATES)
    except Exception:
        us_states = {}
    try:
        country_tables = fetch_json(URL_COUNTRY_TABLES)
    except Exception:
        country_tables = {}
    try:
        br_inss = fetch_json(URL_BR_INSS)
    except Exception:
        br_inss = {}
    try:
        br_irrf = fetch_json(URL_BR_IRRF)
    except Exception:
        br_irrf = {}
    return us_states, country_tables, br_inss, br_irrf

US_STATE_RATES, COUNTRY_TABLES, BR_INSS_TBL, BR_IRRF_TBL = load_tables()

# ============================== SIDEBAR ===============================
with st.sidebar:
    idioma = st.selectbox("🌐 Idioma / Language", ["Português", "English", "Español"], index=0)
    st.markdown("### País")
    country = st.selectbox("Selecione o país", list(COUNTRIES.keys()), index=0)
    st.markdown("### Menu")
    menu = st.radio("Escolha uma opção", ["Cálculo de Salário", "Regras de Contribuições", "Regras de Cálculo do STI", "Custo do Empregador"], index=0)

symbol = COUNTRIES[country]["symbol"]
flag = COUNTRIES[country]["flag"]
valid_from = COUNTRIES[country]["valid_from"]

st.markdown(f"<div class='country-header'><div class='country-flag'>{flag}</div><div class='country-title'>Simulador de Salário – {country}</div></div>", unsafe_allow_html=True)
st.write(f"**Vigência:** {valid_from}")
st.write("---")

# ========================= CÁLCULO ==========================
if menu == "Cálculo de Salário":
    c1, c2, c3 = st.columns([2, 1, 1])
    salario = c1.number_input(f"Salário Bruto ({symbol})", min_value=0.0, value=10000.0, step=100.0)
    bonus_anual = c2.number_input(f"Bônus Anual ({symbol})", min_value=0.0, value=1000.0, step=100.0)
    area = c3.selectbox("Área (STI)", ["Non Sales", "Sales"])
    level = st.selectbox("Career Level (STI)", STI_LEVEL_OPTIONS[area])

    months = COUNTRY_TABLES.get("REMUN_MONTHS", {}).get(country, REMUN_MONTHS_DEFAULT.get(country, 12.0))
    salario_anual = salario * months
    total_anual = salario_anual + bonus_anual

    min_pct, max_pct = get_sti_range(area, level)
    bonus_pct = (bonus_anual / salario_anual) if salario_anual > 0 else 0.0

    if max_pct is not None:
        dentro = bonus_pct <= max_pct
        faixa_txt = f"≤ {max_pct*100:.0f}%"
    else:
        dentro = bonus_pct >= min_pct
        faixa_txt = f"≥ {min_pct*100:.0f}%"

    cor = "#1976d2" if dentro else "#d32f2f"
    status_txt = "Dentro do range" if dentro else "Fora do range"

    # === Cards Horizontais ===
    cA, cB, cC = st.columns(3)
    cA.markdown(f"<div class='metric-card compact'><h4>📅 Salário Anual ({months} meses)</h4><h3>{fmt_money(salario_anual, symbol)}</h3></div>", unsafe_allow_html=True)
    cB.markdown(f"<div class='metric-card compact'><h4>🎯 Bônus Anual</h4><h3>{fmt_money(bonus_anual, symbol)}</h3><div class='sti-note' style='color:{cor}'>STI ratio do bônus: <strong>{bonus_pct*100:.1f}%</strong> — <strong>{status_txt}</strong> ({faixa_txt})</div></div>", unsafe_allow_html=True)
    cC.markdown(f"<div class='metric-card compact'><h4>💼 Remuneração Total Anual</h4><h3>{fmt_money(total_anual, symbol)}</h3></div>", unsafe_allow_html=True)

    st.write("")

    # === Gráfico Pizza Responsivo ===
    chart_df = pd.DataFrame({
        "Componente": ["Salário", "Bônus"],
        "Valor": [salario_anual, bonus_anual]
    })

    base = alt.Chart(chart_df).transform_joinaggregate(Total="sum(Valor)").transform_calculate(Percent="datum.Valor / datum.Total")

    pie = base.mark_arc(innerRadius=70, outerRadius=120).encode(
        theta=alt.Theta("Valor:Q", stack=True),
        color=alt.Color("Componente:N", legend=alt.Legend(orient="bottom", direction="horizontal", title=None)),
        tooltip=[alt.Tooltip("Componente:N"), alt.Tooltip("Valor:Q", format=",.2f"), alt.Tooltip("Percent:Q", format=".1%")]
    )

    labels = base.transform_filter(alt.datum.Percent >= 0.01).mark_text(radius=95, fontWeight="bold", color="white").encode(
        theta=alt.Theta("Valor:Q", stack=True),
        text=alt.Text("Percent:Q", format=".1%")
    )

    chart = alt.layer(pie, labels).properties(width="container", height=340, title="Distribuição Anual: Salário vs Bônus").configure_legend(orient="bottom", padding=10)
    st.altair_chart(chart, use_container_width=True)

# ==================== REGRAS DE CÁLCULO DO STI =====================
elif menu == "Regras de Cálculo do STI":
    st.markdown("#### Non Sales")
    df_ns = pd.DataFrame([
        {"Career Level": "CEO", "STI ratio (% do salário anual)": "100%"},
        {"Career Level": "Members of the GEB", "STI ratio (% do salário anual)": "50–80%"},
        {"Career Level": "Executive Manager", "STI ratio (% do salário anual)": "45–70%"},
        {"Career Level": "Senior Group Manager", "STI ratio (% do salário anual)": "40–60%"},
        {"Career Level": "Group Manager", "STI ratio (% do salário anual)": "30–50%"},
        {"Career Level": "Lead Expert / Program Manager", "STI ratio (% do salário anual)": "25–40%"},
        {"Career Level": "Senior Manager", "STI ratio (% do salário anual)": "20–40%"},
        {"Career Level": "Senior Expert / Senior Project Manager", "STI ratio (% do salário anual)": "15–35%"},
        {"Career Level": "Manager / Selected Expert / Project Manager", "STI ratio (% do salário anual)": "10–30%"},
        {"Career Level": "Others", "STI ratio (% do salário anual)": "≤ 10%"},
    ])
    st.dataframe(df_ns, use_container_width=True)

    st.markdown("#### Sales")
    df_s = pd.DataFrame([
        {"Career Level": "Executive Manager / Senior Group Manager", "STI ratio (% do salário anual)": "45–70%"},
        {"Career Level": "Group Manager / Lead Sales Manager", "STI ratio (% do salário anual)": "35–50%"},
        {"Career Level": "Senior Manager / Senior Sales Manager", "STI ratio (% do salário anual)": "25–45%"},
        {"Career Level": "Manager / Selected Sales Manager", "STI ratio (% do salário anual)": "20–35%"},
        {"Career Level": "Others", "STI ratio (% do salário anual)": "≤ 15%"},
    ])
    st.dataframe(df_s, use_container_width=True)

else:
    st.info("Outras seções mantidas conforme configuração anterior.")
