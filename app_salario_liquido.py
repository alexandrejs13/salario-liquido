# [CÓDIGO ANTERIOR ATÉ A LINHA 601 É MANTIDO]

# ========================= SIMULADOR DE REMUNERAÇÃO (CORRIGIDO) ==========================
if active_menu == T.get("menu_calc"):
    area_options_display, area_display_map = get_sti_area_map(T)
    st.subheader(T.get("calc_params_title", "Parameters"))

    # CORREÇÃO: Usar st.columns com rótulos em Markdown acima para garantir alinhamento vertical
    
    if country == "Brasil":
        # 6 campos: Salário, Dependentes, Outras Ded, Bônus, Área STI, Nível STI
        
        # RÓTULOS EM HTML ACIMA DAS COLUNAS
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 16.66%;"><h5>{T.get('salary', 'Salário Bruto')}<br>({symbol})</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('dependents', 'Dependentes')}<br>(IR)</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('other_deductions', 'Outras Deduções')}<br>({symbol})</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('bonus', 'Bônus Anual')}<br>({symbol})</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('area', 'Área')}<br>(STI)</h5></div>
            <div style="width: 16.66%;"><h5>{T.get('level', 'Career Level')}<br>(STI)</h5></div>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(6) 
        salario = cols[0].number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed")
        dependentes = cols[1].number_input("Dependentes", min_value=0, value=0, step=1, key="dep_input", help=T.get("dependents_tooltip"), label_visibility="collapsed")
        other_deductions = cols[2].number_input("Outras Deduções", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed")
        bonus_anual = cols[3].number_input("Bônus Anual", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed")
        area_display = cols[4].selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = cols[5].selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        state_code, state_rate = None, None
        
    elif country == "Estados Unidos":
        # 5 campos + 2 STI
        
        # RÓTULOS EM HTML ACIMA DAS COLUNAS
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 20%;"><h5>{T.get('salary', 'Gross Salary')}<br>({symbol})</h5></div>
            <div style="width: 20%;"><h5>{T.get('state', 'State')}<br>(USA)</h5></div>
            <div style="width: 20%;"><h5>{T.get('state_rate', 'State Tax')}<br>(%)</h5></div>
            <div style="width: 20%;"><h5>{T.get('other_deductions', 'Other Deductions')}<br>({symbol})</h5></div>
            <div style="width: 20%;"><h5>{T.get('bonus', 'Annual Bonus')}<br>({symbol})</h5></div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5 = st.columns(5)
        salario = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed")
        state_code = c2.selectbox("Estado", list(US_STATE_RATES.keys()), index=0, key="state_select_main", label_visibility="collapsed")
        default_rate = float(US_STATE_RATES.get(state_code, 0.0))
        state_rate = c3.number_input("Taxa Estadual", min_value=0.0, max_value=0.20, value=default_rate, step=0.001, format="%.3f", key="state_rate_input", label_visibility="collapsed")
        other_deductions = c4.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed")
        bonus_anual = c5.number_input("Bônus Anual", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed")
        
        # RÓTULOS STI em uma nova linha de 4 colunas (usando 2 colunas vazias)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 20%;"><h5>{T.get('area', 'Área')}<br>(STI)</h5></div>
            <div style="width: 20%;"><h5>{T.get('level', 'Career Level')}<br>(STI)</h5></div>
            <div style="width: 60%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, _ = st.columns([1, 1, 3]) 
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes = 0
        
    else: # Outros países (3 campos + 2 STI)
        # RÓTULOS PRINCIPAIS EM HTML ACIMA DAS COLUNAS (3 campos + 1 vazio)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 25%;"><h5>{T.get('salary', 'Salário Bruto')}<br>({symbol})</h5></div>
            <div style="width: 25%;"><h5>{T.get('other_deductions', 'Outras Deduções')}<br>({symbol})</h5></div>
            <div style="width: 25%;"><h5>{T.get('bonus', 'Bônus Anual')}<br>({symbol})</h5></div>
            <div style="width: 25%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, _ = st.columns(4)
        salario = c1.number_input("Salário", min_value=0.0, value=10000.0, step=100.0, key="salary_input", help=T.get("salary_tooltip"), label_visibility="collapsed")
        other_deductions = c2.number_input("Outras Ded.", min_value=0.0, value=0.0, step=10.0, key="other_ded_input", help=T.get("other_deductions_tooltip"), label_visibility="collapsed")
        bonus_anual = c3.number_input("Bônus Anual", min_value=0.0, value=0.0, step=100.0, key="bonus_input", help=T.get("bonus_tooltip"), label_visibility="collapsed")
        
        # RÓTULOS STI em uma nova linha de 4 colunas (usando 2 colunas vazias)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 25%;"><h5>{T.get('area', 'Área')}<br>(STI)</h5></div>
            <div style="width: 25%;"><h5>{T.get('level', 'Career Level')}<br>(STI)</h5></div>
            <div style="width: 50%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        r1, r2, _ = st.columns([1, 1, 2])
        area_display = r1.selectbox("Área STI", area_options_display, index=0, key="sti_area", help=T.get("sti_area_tooltip"), label_visibility="collapsed")
        area = area_display_map.get(area_display, "Non Sales")
        level_options_display, level_display_map = get_sti_level_map(area, T)
        level_default_index = len(level_options_display) - 1 if level_options_display else 0
        level_display = r2.selectbox("Nível STI", level_options_display, index=level_default_index, key="sti_level", help=T.get("sti_level_tooltip"), label_visibility="collapsed")
        level = level_display_map.get(level_display, level_options_display[level_default_index] if level_options_display else "Others")
        dependentes = 0
        state_code, state_rate = None, None

    st.subheader(T.get("monthly_comp_title", "Monthly Comp"))
    
    # [RESTANTE DO CÓDIGO É MANTIDO]
    # ...
