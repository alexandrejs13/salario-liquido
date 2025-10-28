# ========================= COMPARADOR DE REMUNERAÇÃO (NOVO BLOCO - CORRIGIDO) ==========================
elif active_menu == T.get("menu_compare"):
    st.subheader(T.get("calc_params_title", "Parâmetros de Cálculo da Remuneração"))
    
    # --- Colunas para inputs ---
    col_empresa, col_candidato = st.columns(2)

    # 1. Inputs da Empresa
    with col_empresa:
        st.markdown(f"#### 🏢 {T.get('company_side', 'Remuneração da Empresa')}")
        empresa_data = render_compensation_inputs("Empresa", country, symbol, T, INPUT_FORMAT)

    # 2. Inputs do Candidato
    with col_candidato:
        st.markdown(f"#### 👤 {T.get('candidate_side', 'Remuneração do Candidato')}")
        candidato_data = render_compensation_inputs("Candidato", country, symbol, T, INPUT_FORMAT)

    st.write("---")
    st.subheader("📊 Resumo da Comparação")
    
    # --- Cálculos para Empresa ---
    calc_empresa = calc_country_net(
        country, 
        empresa_data.get("salario", 0.0), 
        empresa_data.get("other_deductions", 0.0), 
        state_code=empresa_data.get("state_code"), 
        state_rate=empresa_data.get("state_rate"), 
        dependentes=empresa_data.get("dependentes", 0), 
        tables_ext=COUNTRY_TABLES, 
        br_inss_tbl=BR_INSS_TBL, 
        br_irrf_tbl=BR_IRRF_TBL
    )
    
    annual_total_empresa, months = get_annual_total_brute(
        country, 
        empresa_data.get("salario", 0.0), 
        empresa_data.get("bonus_anual", 0.0), 
        COUNTRY_TABLES
    )
    
    # --- Cálculos para Candidato ---
    calc_candidato = calc_country_net(
        country, 
        candidato_data.get("salario", 0.0), 
        candidato_data.get("other_deductions", 0.0), 
        state_code=candidato_data.get("state_code"), 
        state_rate=candidato_data.get("state_rate"), 
        dependentes=candidato_data.get("dependentes", 0), 
        tables_ext=COUNTRY_TABLES, 
        br_inss_tbl=BR_INSS_TBL, 
        br_irrf_tbl=BR_IRRF_TBL
    )
    
    annual_total_candidato, _ = get_annual_total_brute(
        country, 
        candidato_data.get("salario", 0.0), 
        candidato_data.get("bonus_anual", 0.0), 
        COUNTRY_TABLES
    )
    
    # --- Preparação da Tabela de Comparação ---
    
    def format_delta(delta: float, symbol: str) -> str:
        if abs(delta) < 1e-9: return fmt_money(0.0, symbol)
        
        # Classe para cor
        delta_class = "positive-delta" if delta > 0 else "negative-delta"
        # Sinal (só precisa do '+' se for positivo, o '-' já vem no valor)
        sign = "+" if delta > 0 else ""
        
        return f"<span class='{delta_class}'>{sign}{fmt_money(delta, symbol)}</span>"


    # Dados da tabela
    data_comparison = [
        # Mensal Bruta
        [T.get('monthly_brute', 'Monthly Gross'), 
         calc_empresa.get("monthly_brute", 0.0), 
         calc_candidato.get("monthly_brute", 0.0)],
        
        # Mensal Líquida
        [T.get('monthly_net', 'Monthly Net'), 
         calc_empresa.get("net", 0.0), 
         calc_candidato.get("net", 0.0)],
        
        # Anual Total Bruta
        [T.get('annual_total_brute', 'Annual Total Gross'), 
         annual_total_empresa, 
         annual_total_candidato]
    ]

    # Criação do DataFrame
    df_comp = pd.DataFrame(data_comparison, columns=["Métrica", "Empresa", "Candidato"])
    df_comp["Diferença (Candidato - Empresa)"] = df_comp["Candidato"] - df_comp["Empresa"]
    
    # Conversão para HTML com formatação e cores no Delta
    table_rows = []
    header = f"""
    <thead>
        <tr>
            <th>{df_comp.columns[0]}</th>
            <th>🏢 {T.get('company_side', 'Empresa')}</th>
            <th>👤 {T.get('candidate_side', 'Candidato')}</th>
            <th>Δ (Diferença)</th>
        </tr>
    </thead>
    """
    
    for index, row in df_comp.iterrows():
        delta_formatted = format_delta(row["Diferença (Candidato - Empresa)"], symbol)
        row_html = f"""
        <tr>
            <th>{row['Métrica']}</th>
            <td>{fmt_money(row['Empresa'], symbol)}</td>
            <td>{fmt_money(row['Candidato'], symbol)}</td>
            <td>{delta_formatted}</td>
        </tr>
        """
        table_rows.append(row_html)
        
    table_body = "<tbody>" + "\n".join(table_rows) + "</tbody>"
    final_table_html = f"<table class='comparison-table'>{header}{table_body}</table>"
    
    st.markdown(final_table_html, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="margin-top: 20px; padding: 5px 0;">
            <p style="font-size: 15px; font-weight: 500; color: #555; margin: 0;">
                <span style="font-weight: 600;">Regras de Cálculo:</span> Todos os valores levam em consideração as regras do país ({country}) e um fator de meses considerado de <span style="font-weight: 600;">{months}</span>.
            </p>
        </div>
        """, unsafe_allow_html=True)
