"""
INTERFACE SÉLECTION ÉVÉNEMENTS - SESSION 110
============================================

Code pour ajouter au Planificateur V27 entre la sélection de date
et le bouton "Calculer Prédictions"
"""

# ═══════════════════════════════════════════════════════════════
# SECTION : CHARGEMENT ET SÉLECTION ÉVÉNEMENTS
# ═══════════════════════════════════════════════════════════════

# Bouton pour charger les événements
if st.button("🔍 Charger Événements", type="secondary"):
    with st.spinner("Chargement événements..."):
        date_to_query = datetime.combine(target_date, datetime.min.time())
        df_events = get_high_impact_events_for_date(date_to_query)
        
        if df_events.empty:
            st.warning(f"❌ Aucun événement trouvé pour le {target_date.strftime('%d/%m/%Y')}")
        else:
            st.session_state.events_loaded = True
            st.session_state.df_events = df_events
            st.success(f"✅ {len(df_events)} événement(s) chargé(s)")

# Afficher interface de sélection SI événements chargés
if st.session_state.get('events_loaded', False) and 'df_events' in st.session_state:
    df_events = st.session_state.df_events
    
    st.markdown("---")
    st.markdown("## 📋 Sélection des Événements")
    st.caption(f"**{len(df_events)} événements disponibles** - Cochez ceux à inclure dans le calcul")
    
    # Initialiser selected_events dans session_state si nécessaire
    if 'selected_event_indices' not in st.session_state:
        st.session_state.selected_event_indices = set()
    
    if 'event_actuals' not in st.session_state:
        st.session_state.event_actuals = {}
    
    # Header
    header_cols = st.columns([0.5, 1.5, 2.5, 1, 1, 1, 1, 1.5])
    with header_cols[0]:
        st.markdown("**✓**")
    with header_cols[1]:
        st.markdown("**Heure**")
    with header_cols[2]:
        st.markdown("**Événement**")
    with header_cols[3]:
        st.markdown("**Pays**")
    with header_cols[4]:
        st.markdown("**Score**")
    with header_cols[5]:
        st.markdown("**Previous**")
    with header_cols[6]:
        st.markdown("**Forecast**")
    with header_cols[7]:
        st.markdown("**Actual**")
    
    st.markdown("---")
    
    # Liste des événements
    for idx, event in df_events.iterrows():
        cols = st.columns([0.5, 1.5, 2.5, 1, 1, 1, 1, 1.5])
        
        with cols[0]:
            # Checkbox pour sélection
            is_selected = st.checkbox(
                "",
                key=f"select_{idx}",
                value=idx in st.session_state.selected_event_indices,
                label_visibility="collapsed"
            )
            
            if is_selected:
                st.session_state.selected_event_indices.add(idx)
            else:
                st.session_state.selected_event_indices.discard(idx)
        
        with cols[1]:
            # Heure (convertie en heure locale si besoin)
            event_time = pd.to_datetime(event['ts_utc'])
            st.write(event_time.strftime('%H:%M'))
        
        with cols[2]:
            # Nom événement (formaté)
            event_name = format_event_name(event['label'])
            st.write(event_name)
        
        with cols[3]:
            # Pays
            st.write(event['country'])
        
        with cols[4]:
            # Score
            score_val = event.get('empirical_score', 0)
            if score_val >= 40:
                st.markdown(f"🔴 **{score_val:.0f}**")
            elif score_val >= 25:
                st.markdown(f"🟡 {score_val:.0f}")
            else:
                st.write(f"{score_val:.0f}")
        
        with cols[5]:
            # Previous
            prev_val = event.get('previous')
            if pd.notna(prev_val):
                st.write(f"{prev_val:.2f}" if abs(prev_val) < 1000 else f"{prev_val:.0f}")
            else:
                st.write("—")
        
        with cols[6]:
            # Forecast
            forecast_val = event.get('estimate') or event.get('forecast')
            if pd.notna(forecast_val):
                st.write(f"{forecast_val:.2f}" if abs(forecast_val) < 1000 else f"{forecast_val:.0f}")
            else:
                st.write("—")
        
        with cols[7]:
            # Actual - CHAMP INPUT si manquant, sinon affichage
            actual_val = event.get('actual')
            
            # Vérifier si événement dans le futur OU actual manquant
            event_time_aware = pd.to_datetime(event['ts_utc'])
            is_future = event_time_aware > pd.Timestamp.now(tz='UTC')
            
            if pd.isna(actual_val) or is_future:
                # Champ input pour saisir actual
                actual_input = st.number_input(
                    "Actual",
                    key=f"actual_{idx}",
                    value=st.session_state.event_actuals.get(idx, None),
                    label_visibility="collapsed",
                    format="%.2f" if event.get('previous', 0) < 1000 else "%.0f"
                )
                
                # Sauvegarder dans session_state
                if actual_input is not None:
                    st.session_state.event_actuals[idx] = actual_input
            else:
                # Afficher actual existant
                st.write(f"{actual_val:.2f}" if abs(actual_val) < 1000 else f"{actual_val:.0f}")
    
    st.markdown("---")
    
    # Résumé sélection
    n_selected = len(st.session_state.selected_event_indices)
    if n_selected > 0:
        st.info(f"✅ **{n_selected} événement(s) sélectionné(s)**")
        
        # Grouper par heure pour détecter clusters
        selected_df = df_events.loc[list(st.session_state.selected_event_indices)]
        selected_df['hour_minute'] = pd.to_datetime(selected_df['ts_utc']).dt.strftime('%H:%M')
        time_groups = selected_df.groupby('hour_minute').size()
        
        if len(time_groups) > 1:
            st.warning(f"⚠️ **Attention** : Événements sur {len(time_groups)} horaires différents")
            for time, count in time_groups.items():
                st.caption(f"  • {time} : {count} événement(s)")
        else:
            st.success(f"✅ Tous les événements à {time_groups.index[0]}")
    else:
        st.warning("⚠️ Aucun événement sélectionné")

# ═══════════════════════════════════════════════════════════════
# FIN SECTION SÉLECTION
# ═══════════════════════════════════════════════════════════════

# CONTINUER AVEC LE RESTE DU CODE (SECTION AMPLIFICATION, ETC.)
