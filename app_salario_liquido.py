# -------------------------------------------------------------
# 📄 Simulador de Salário Líquido e Custo do Empregador (v2025.37)
# -------------------------------------------------------------
import streamlit as st
import pandas as pd
import altair as alt
import requests
from typing import Dict, Any, Tuple

st.set_page_config(
    page_title="Simulador de Salário Líquido e Custo do Empregador",
    layout="wide"
)

# ======================== ENDPOINTS REMOTOS =========================
RAW_BASE = "https://raw.githubusercontent.com/alexandrejs13/salario-liquido/main"
URL_US_STATES      = f"{RAW_BASE}/us_state_tax_rates.json"
URL_COUNTRY_TABLES = f"{RAW_BASE}/country_tables.json"
URL_BR_INSS        = f"{RAW_BASE}/br_inss.json"
URL_BR_IRRF        = f"{RAW_BASE}/br_irrf.json"

# ============================== CSS ================================
st.markdown("""
<style>
html, body {font-family:'Segoe UI',Helvetica,Arial,sans-serif;background:#f7f9fb;color:#1a1a1a;}
h1,h2,h3 {color:#0a3d62;} hr{border:0;height:1px;background:#e2e6ea;margin:16px 0;}
section[data-testid="stSidebar"]{background:#0a3d62!important;padding-top:8px;}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown,section[data-testid="stSidebar"] label{color:#fff!important;}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox input,
section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] div[role="option"]{
 color:#0b1f33!important;background:#fff!important;}
section[data-testid="stSidebar"] .stButton>button,section[data-testid="stSidebar"] .stButton>button *{
 color:#0b1f33!important;}
section[data-testid="stSidebar"] .stButton>button{
 background:#fff!important;border:1px solid #c9d6e2!important;border-radius:10px!important;
 font-weight:600!important;box-shadow:0 1px 3px rgba(0,0,0,.06);}
section[data-testid="stSidebar"] .stButton>button:hover{background:#f5f8ff!important;border-color:#9bb4d1!important;}
.metric-card{background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);
 padding:12px;text-align:center;margin-bottom:12px;}
.metric-card h4{margin:0;font-size:13px;color:#0a3d62;}
.metric-card h3{margin:4px 0 0;color:#0a3d62;font-size:18px;}
.table-wrap{background:#fff;border:1px solid #d0d7de;border-radius:8px;overflow:hidden;}
.country-header{display:flex;align-items:center;gap:10px;}
.country-flag{font-size:28px;}
.country-title{font-size:24px;font-weight:700;color:#0a3d62;}
.metric-card.compact{padding:12px;border-radius:12px;background:#fff;
 box-shadow:0 2px 8px rgba(0,0,0,.08);min-height:100px;}
.metric-row{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px;}
.metric-row .metric-card{flex:1;min-width:200px;}
@media(max-width:992px){.metric-row{flex-direction:column;}}
</style>
""", unsafe_allow_html=True)

# ============================== I18N ================================
I18N = {
 "Português": {
  "app_title": "Simulador de Salário Líquido e Custo do Empregador",
  "menu_calc": "Cálculo de Salário",
  "menu_rules": "Regras de Contribuições",
  "menu_rules_sti": "Regras de Cálculo do STI",
  "menu_cost": "Custo do Empregador",
  "title_calc": "Cálculo de Salário – {pais}",
  "title_rules": "Regras de Contribuições – {pais}",
  "title_rules_sti": "Regras de Cálculo do STI",
  "title_cost": "Custo do Empregador – {pais}",
  "country": "País",
  "salary": "Salário Bruto",
  "state": "Estado (EUA)",
  "state_rate": "State Tax (%)",
  "dependents": "Dependentes (IR)",
  "bonus": "Bônus Anual",
  "earnings": "Proventos",
  "deductions": "Descontos",
  "net": "Salário Líquido",
  "fgts_deposit": "Depósito FGTS",
  "tot_earnings": "Total de Proventos",
  "tot_deductions": "Total de Descontos",
  "valid_from": "Vigência",
  "rules_emp": "Parte do Empregado",
  "rules_er": "Parte do Empregador",
  "employer_cost_total": "Custo Total do Empregador",
  "annual_comp_title": "Composição da Remuneração Total Anual Bruta",
  "annual_salary": "Salário Anual (Salário × Meses do País)",
  "annual_bonus": "Bônus Anual",
  "annual_total": "Remuneração Total Anual",
  "months_factor": "Meses considerados",
  "pie_title": "Distribuição Anual: Salário vs Bônus",
  "reload": "Recarregar tabelas",
  "menu": "Menu",
  "choose_country": "Selecione o país",
  "choose_menu": "Escolha uma opção",
  "area": "Área (STI)",
  "level": "Career Level (STI)"
 }
}

# ====================== PAÍSES / MOEDAS =====================
COUNTRIES = {
 "Brasil":{"symbol":"R$","flag":"🇧🇷","valid_from":"2025-01-01"},
 "México":{"symbol":"MX$","flag":"🇲🇽","valid_from":"2025-01-01"},
 "Chile":{"symbol":"CLP$","flag":"🇨🇱","valid_from":"2025-01-01"},
 "Argentina":{"symbol":"ARS$","flag":"🇦🇷","valid_from":"2025-01-01"},
 "Colômbia":{"symbol":"COP$","flag":"🇨🇴","valid_from":"2025-01-01"},
 "Estados Unidos":{"symbol":"US$","flag":"🇺🇸","valid_from":"2025-01-01"},
 "Canadá":{"symbol":"CAD$","flag":"🇨🇦","valid_from":"2025-01-01"}
}

REMUN_MONTHS_DEFAULT = {
 "Brasil":13.33,"México":12.5,"Chile":12,"Argentina":13,"Colômbia":13,
 "Estados Unidos":12,"Canadá":12
}

# ========================== FALLBACKS ============================
US_STATE_RATES_DEFAULT = {
 "No State Tax":0.00,"CA":0.06,"FL":0.00,"NY":0.064,"TX":0.00,"WA":0.00,"IL":0.0495
}

TABLES_DEFAULT = {
 "México":{"rates":{"ISR":0.15,"IMSS":0.05,"INFONAVIT":0.05}},
 "Chile":{"rates":{"AFP":0.10,"Saúde":0.07}},
 "Argentina":{"rates":{"Jubilación":0.11,"Obra Social":0.03,"PAMI":0.03}},
 "Colômbia":{"rates":{"Saúde":0.04,"Pensão":0.04}},
 "Canadá":{"rates":{"CPP":0.0595,"EI":0.0163,"Income Tax":0.15}}
}

EMPLOYER_COST_DEFAULT = {
 "Brasil":[{"nome":"INSS Patronal","percentual":20.0},{"nome":"FGTS","percentual":8.0}],
 "Estados Unidos":[{"nome":"Social Security (ER)","percentual":6.2},{"nome":"Medicare (ER)","percentual":1.45}]
}

# ============== STI RANGES ==============
STI_RANGES = {
 "Non Sales":{"Others":(0.10,None)},
 "Sales":{"Others":(0.01,None)}
}

STI_LEVEL_OPTIONS = {"Non Sales":["Others"],"Sales":["Others"]}

# ============================== HELPERS ===============================
def fmt_money(v,sym): return f"{sym} {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def money_or_blank(v,sym): return "" if abs(v)<1e-9 else fmt_money(v,sym)
def get_sti_range(area,level): return STI_RANGES.get(area,{}).get(level,(0.0,None))

def generic_net(salary,rates):
 lines=[("Base",salary,0.0)]
 total_earn=salary; total_ded=0
 for k,a in rates.items():
  v=salary*float(a); total_ded+=v; lines.append((k,0.0,v))
 net=total_earn-total_ded; return lines,total_earn,total_ded,net
# ======================== FETCH REMOTO =======================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_json(url:str)->Dict[str,Any]:
 try:
  r=requests.get(url,timeout=8)
  r.raise_for_status()
  return r.json()
 except Exception:
  return {}

def load_tables(force=False):
 if force: fetch_json.clear()
 try: us_states=fetch_json(URL_US_STATES)
 except: us_states=US_STATE_RATES_DEFAULT
 try: country_tables=fetch_json(URL_COUNTRY_TABLES)
 except: country_tables={"TABLES":TABLES_DEFAULT,"EMPLOYER_COST":EMPLOYER_COST_DEFAULT,"REMUN_MONTHS":REMUN_MONTHS_DEFAULT}
 return us_states,country_tables

# ============================== SIDEBAR ===============================
with st.sidebar:
 idioma=st.selectbox("🌐 Idioma",list(I18N.keys()),index=0,key="lang_select")
 T=I18N[idioma]
 reload_clicked=st.button(f"🔄 {T['reload']}")

US_STATE_RATES,COUNTRY_TABLES=load_tables(force=reload_clicked)

with st.sidebar:
 st.markdown(f"### {T['country']}")
 country=st.selectbox(T["choose_country"],list(COUNTRIES.keys()),index=0)
 st.markdown(f"### {T['menu']}")
 menu=st.radio(T["choose_menu"],[T["menu_calc"],T["menu_rules"],T["menu_rules_sti"],T["menu_cost"]],index=0)

symbol=COUNTRIES[country]["symbol"]
flag=COUNTRIES[country]["flag"]
valid_from=COUNTRIES[country]["valid_from"]

if menu==T["menu_calc"]:
 title=T["title_calc"].format(pais=country)
elif menu==T["menu_rules"]:
 title=T["title_rules"].format(pais=country)
elif menu==T["menu_rules_sti"]:
 title=T["title_rules_sti"]
else:
 title=T["title_cost"].format(pais=country)

st.markdown(f"<div class='country-header'><div class='country-flag'>{flag}</div><div class='country-title'>{title}</div></div>",unsafe_allow_html=True)
st.write(f"**{T['valid_from']}:** {valid_from}")
st.write("---")

# ========================= CÁLCULO ==========================
if menu==T["menu_calc"]:
 c1,c2=st.columns([2,1.6])
 salario=c1.number_input(f"{T['salary']} ({symbol})",min_value=0.0,value=10000.0,step=100.0)
 bonus=c2.number_input(f"{T['bonus']} ({symbol})",min_value=0.0,value=0.0,step=100.0)
 r1,r2=st.columns([1.2,2.2])
 area=r1.selectbox(T["area"],["Non Sales","Sales"],index=0)
 level=r2.selectbox(T["level"],STI_LEVEL_OPTIONS[area],index=0)

 rates=(COUNTRY_TABLES or {}).get("TABLES",{}).get(country,{}).get("rates",{})
 if not rates: rates=TABLES_DEFAULT.get(country,{}).get("rates",{})
 lines,te,td,net=generic_net(salario,rates)
 df=pd.DataFrame(lines,columns=["Descrição",T["earnings"],T["deductions"]])
 df[T["earnings"]]=df[T["earnings"]].apply(lambda v:money_or_blank(v,symbol))
 df[T["deductions"]]=df[T["deductions"]].apply(lambda v:money_or_blank(v,symbol))
 st.markdown("<div class='table-wrap'>",unsafe_allow_html=True)
 st.table(df)
 st.markdown("</div>",unsafe_allow_html=True)

 cc1,cc2,cc3=st.columns(3)
 cc1.markdown(f"<div class='metric-card'><h4>🟩 {T['tot_earnings']}</h4><h3>{fmt_money(te,symbol)}</h3></div>",unsafe_allow_html=True)
 cc2.markdown(f"<div class='metric-card'><h4>🟥 {T['tot_deductions']}</h4><h3>{fmt_money(td,symbol)}</h3></div>",unsafe_allow_html=True)
 cc3.markdown(f"<div class='metric-card'><h4>🟦 {T['net']}</h4><h3>{fmt_money(net,symbol)}</h3></div>",unsafe_allow_html=True)

 # ---------- Composição Anual ----------
 st.write("---")
 st.subheader(T["annual_comp_title"])
 months=COUNTRY_TABLES.get("REMUN_MONTHS",{}).get(country,REMUN_MONTHS_DEFAULT.get(country,12.0))
 sal_anual=salario*months
 total_anual=sal_anual+bonus
 min_pct,max_pct=get_sti_range(area,level)
 pct=(bonus/sal_anual) if sal_anual>0 else 0.0
 faixa_txt=f"≥ {min_pct*100:.0f}%" if max_pct is None else f"{min_pct*100:.0f}%–{max_pct*100:.0f}%"
 dentro=(pct>=min_pct) if max_pct is None else (pct>=min_pct and pct<=max_pct)
 cor="#1976d2" if dentro else "#d32f2f"
 status="Dentro do range" if dentro else "Fora do range"

 # --- Cards horizontais ---
 st.markdown("<div class='metric-row'>",unsafe_allow_html=True)
 st.markdown(f"<div class='metric-card'><h4>📅 {T['annual_salary']} ({T['months_factor']}: {months})</h4><h3>{fmt_money(sal_anual,symbol)}</h3></div>",unsafe_allow_html=True)
 st.markdown(f"<div class='metric-card'><h4>🎯 {T['annual_bonus']}</h4><h3>{fmt_money(bonus,symbol)}</h3><div style='font-size:12px;color:{cor};margin-top:6px;'>STI: {pct*100:.1f}% — {status} ({faixa_txt}) — <em>{area} • {level}</em></div></div>",unsafe_allow_html=True)
 st.markdown(f"<div class='metric-card'><h4>💼 {T['annual_total']}</h4><h3>{fmt_money(total_anual,symbol)}</h3></div>",unsafe_allow_html=True)
 st.markdown("</div>",unsafe_allow_html=True)

 # --- Gráfico pizza abaixo ---
 chart_df=pd.DataFrame({"Componente":[T["annual_salary"],T["annual_bonus"]],"Valor":[sal_anual,bonus]})
 pie_base=alt.Chart(chart_df).transform_joinaggregate(Total='sum(Valor)').transform_calculate(Percent='datum.Valor / datum.Total')
 pie=pie_base.mark_arc(innerRadius=70,outerRadius=120).encode(
  theta=alt.Theta('Valor:Q',stack=True),
  color=alt.Color('Componente:N',legend=alt.Legend(orient='bottom',columns=2,title=None)),
  tooltip=[alt.Tooltip('Componente:N'),alt.Tooltip('Valor:Q',format=",.2f"),alt.Tooltip('Percent:Q',format=".1%")]
 ).properties(width=420,height=320,title=T["pie_title"])
 labels=pie_base.transform_filter(alt.datum.Percent>=0.01).mark_text(radius=95,fontWeight='bold',color='white').encode(
  theta=alt.Theta('Valor:Q',stack=True),
  text=alt.Text('Percent:Q',format='.1%'))
 st.altair_chart(pie+labels,use_container_width=True)

# ==================== REGRAS DE CONTRIBUIÇÕES ====================
elif menu==T["menu_rules"]:
 st.markdown("### Regras de Contribuições Gerais")
 st.info("As regras variam conforme país e legislação vigente. Incluem INSS, IRRF, FGTS no Brasil; FICA, Medicare e State Tax nos EUA; AFP e Saúde no Chile, etc.")

# ==================== REGRAS DE CÁLCULO DO STI ====================
elif menu==T["menu_rules_sti"]:
 st.markdown("#### Non Sales")
 df_ns=pd.DataFrame([
  {"Career Level":"CEO","STI ratio (% do salário anual)":"100%"},
  {"Career Level":"Members of the GEB","STI ratio (% do salário anual)":"50–80%"},
  {"Career Level":"Executive Manager","STI ratio (% do salário anual)":"45–70%"},
  {"Career Level":"Senior Group Manager","STI ratio (% do salário anual)":"40–60%"},
  {"Career Level":"Group Manager","STI ratio (% do salário anual)":"30–50%"},
  {"Career Level":"Lead Expert / Program Manager","STI ratio (% do salário anual)":"25–40%"},
  {"Career Level":"Senior Manager","STI ratio (% do salário anual)":"20–40%"},
  {"Career Level":"Senior Expert / Senior Project Manager","STI ratio (% do salário anual)":"15–35%"},
  {"Career Level":"Manager / Selected Expert / Project Manager","STI ratio (% do salário anual)":"10–30%"},
  {"Career Level":"Others","STI ratio (% do salário anual)":"≥10%"}
 ])
 st.dataframe(df_ns,use_container_width=True)

 st.markdown("#### Sales")
 df_s=pd.DataFrame([
  {"Career Level":"Executive Manager / Senior Group Manager","STI ratio (% do salário anual)":"45–70%"},
  {"Career Level":"Group Manager / Lead Sales Manager","STI ratio (% do salário anual)":"35–50%"},
  {"Career Level":"Senior Manager / Senior Sales Manager","STI ratio (% do salário anual)":"25–45%"},
  {"Career Level":"Manager / Selected Sales Manager","STI ratio (% do salário anual)":"20–35%"},
  {"Career Level":"Others","STI ratio (% do salário anual)":"≥1%"}
 ])
 st.dataframe(df_s,use_container_width=True)

# ==================== CUSTO DO EMPREGADOR ====================
else:
 salario=st.number_input(f"{T['salary']} ({symbol})",min_value=0.0,value=10000.0,step=100.0)
 months=COUNTRY_TABLES.get("REMUN_MONTHS",{}).get(country,REMUN_MONTHS_DEFAULT.get(country,12.0))
 enc_list=COUNTRY_TABLES.get("EMPLOYER_COST",{}).get(country,EMPLOYER_COST_DEFAULT.get(country,[]))
 df=pd.DataFrame(enc_list)
 if not df.empty:
  total=sum(e.get("percentual",0) for e in enc_list)
  anual=salario*months*(1+total/100)
  mult=(anual/(salario*12)) if salario>0 else 0
  st.markdown(f"**{T['employer_cost_total']}:** {fmt_money(anual,symbol)}  \n**Equivalente:** {mult:.3f}× (12 meses)")
  st.dataframe(df,use_container_width=True)
 else:
  st.info("Sem encargos configurados para este país.")
