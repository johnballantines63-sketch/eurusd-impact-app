"""
Insérer la section d'affichage des événements non mappés
après le tableau des événements mappés
"""

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

print("🔧 Insertion section unmapped events...")

# Chercher "selected_indices = []" qui est après le tableau des événements
insert_line = None
for i, line in enumerate(lines):
    if "selected_indices = []" in line:
        insert_line = i
        break

if insert_line:
    print(f"✅ Position trouvée : ligne {insert_line + 1}")
    
    # Code à insérer AVANT selected_indices = []
    unmapped_section = '''    
    # ═══════════════════════════════════════════════════════════
    # ÉVÉNEMENTS SANS FAMILLE (Non mappés)
    # ═══════════════════════════════════════════════════════════
    
    if 'all_events' in st.session_state and len(st.session_state.all_events['unmapped']) > 0:
        st.divider()
        
        unmapped_count = len(st.session_state.all_events['unmapped'])
        
        with st.expander(
            f"⚠️ {unmapped_count} événement{'s' if unmapped_count > 1 else ''} sans famille",
            expanded=False
        ):
            st.warning(
                "**Ces événements n'ont pas de famille configurée** → Pas de prédiction automatique. "
                "Ils peuvent néanmoins impacter les marchés !"
            )
            
            unmapped_df = st.session_state.all_events['unmapped']
            
            st.markdown("### 📋 Liste")
            
            for idx, row in unmapped_df.iterrows():
                col_time, col_event, col_data = st.columns([1, 3, 2])
                
                with col_time:
                    event_time = row['ts_utc'].strftime('%H:%M')
                    importance = "🔴" if row['importance_n'] >= 3 else "🟡" if row['importance_n'] == 2 else "🟢"
                    st.markdown(f"**{event_time}** {importance}")
                
                with col_event:
                    st.markdown(f"**{row['event_key']}** ({row['country']})")
                    
                    # Surprise si disponible
                    if pd.notna(row['actual']) and pd.notna(row['estimate']) and row['estimate'] != 0:
                        surprise = row['actual'] - row['estimate']
                        surprise_pct = (surprise / row['estimate'] * 100)
                        icon = "🔺" if surprise > 0 else "🔻" if surprise < 0 else "➖"
                        st.caption(f"{icon} Surprise: {surprise_pct:+.1f}%")
                
                with col_data:
                    parts = []
                    if pd.notna(row['previous']):
                        parts.append(f"Prev: {row['previous']:.2f}")
                    if pd.notna(row['estimate']):
                        parts.append(f"Fcst: {row['estimate']:.2f}")
                    if pd.notna(row['actual']):
                        parts.append(f"**{row['actual']:.2f}**")
                    
                    if parts:
                        st.caption(" | ".join(parts))
                
                st.markdown("---")
            
            st.info(
                "💡 **Ex:** Le **Current Account (DE) à 14:45** peut relancer EUR/USD même sans prédiction. "
                "Surveillez ces événements manuellement !"
            )
    
    st.divider()
    
'''
    
    # Insérer avant selected_indices
    lines.insert(insert_line, unmapped_section)
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Section unmapped insérée !")
else:
    print("❌ Position 'selected_indices = []' non trouvée")

print("\n📋 Relancer streamlit et charger 11/09/2025")
print("   Tu devrais voir la section 'X événements sans famille' !")
