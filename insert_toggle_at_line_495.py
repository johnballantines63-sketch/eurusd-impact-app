"""
Insertion manuelle du toggle à la ligne 495 (avant la boucle enumerate)
"""

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

print("🔧 Insertion du toggle mode fenêtres à la ligne 495...")

# Code du toggle et de l'affichage conditionnel
toggle_code = '''
                # ═══════════════════════════════════════════════════════════
                # MODE D'ANALYSE : Individuel vs Fenêtres Temporelles
                # ═══════════════════════════════════════════════════════════
                
                st.subheader("⚙️ Mode d'Analyse")
                
                col_mode1, col_mode2 = st.columns([3, 1])
                
                with col_mode1:
                    use_time_windows = st.checkbox(
                        "🕐 Activer le mode Fenêtres Temporelles",
                        value=True,
                        help="Groupe automatiquement les événements proches (< 30 min) pour analyser leur impact cumulé"
                    )
                
                with col_mode2:
                    if use_time_windows:
                        window_gap = st.number_input(
                            "Écart max (min)",
                            min_value=10,
                            max_value=60,
                            value=30,
                            step=5,
                            help="Écart maximum entre deux événements d'une même fenêtre"
                        )
                    else:
                        window_gap = 30
                
                if use_time_windows:
                    st.info(
                        f"ℹ️ **Mode Fenêtres activé** : Événements espacés de < {window_gap} min seront groupés. "
                        "Capture les effets cumulés (ex: 14:30 + 14:45)."
                    )
                else:
                    st.info("ℹ️ **Mode Individuel** : Chaque événement analysé isolément.")
                
                st.divider()
                
                # ═══════════════════════════════════════════════════════════
                # AFFICHAGE FENÊTRES TEMPORELLES (si activé)
                # ═══════════════════════════════════════════════════════════
                
                if use_time_windows:
                    st.subheader("🕐 Fenêtres Temporelles d'Événements")
                    
                    # Créer liste d'événements pour clustering
                    from datetime import datetime, timedelta
                    event_list = [{
                        'event_time': pred['event']['time'], 
                        'family': pred['event']['family']
                    } for pred in predictions]
                    
                    # Grouper par proximité
                    clusters = group_events_by_time_window(event_list, max_gap_minutes=window_gap)
                    
                    # Dict pour lookup rapide
                    pred_dict = {}
                    for pred in predictions:
                        key = f"{pred['event']['family']}_{pred['event']['time'].strftime('%Y%m%d_%H%M')}"
                        pred_dict[key] = pred
                    
                    # Message info
                    if len(clusters) > 1:
                        st.success(f"✅ {len(clusters)} fenêtres détectées")
                    elif len(clusters) == 1 and len(clusters[0]['events']) > 1:
                        st.success(f"✅ 1 fenêtre avec {len(clusters[0]['events'])} événements groupés")
                    else:
                        st.info("ℹ️ Un seul événement ou événements espacés")
                    
                    # Afficher chaque cluster
                    for cluster_idx, cluster in enumerate(clusters):
                        cluster_impact = calculate_cluster_impact(cluster, pred_dict)
                        
                        with st.expander(
                            f"🕐 Fenêtre {cluster_idx + 1} : "
                            f"{cluster['window_start'].strftime('%H:%M')} → "
                            f"{cluster['window_end'].strftime('%H:%M')} "
                            f"({cluster_impact['events_count']} événement{'s' if cluster_impact['events_count'] > 1 else ''})",
                            expanded=True
                        ):
                            # Métriques cluster
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                direction_icon = "🔺 UP" if cluster_impact['total_pips'] > 0 else "🔻 DOWN"
                                st.metric(
                                    "Impact Cumulé",
                                    f"{abs(cluster_impact['total_pips']):.1f} pips",
                                    delta=direction_icon
                                )
                            
                            with col2:
                                st.metric(
                                    "Réaction",
                                    f"{cluster_impact['min_latency']:.0f} min",
                                    help="Latence du 1er événement"
                                )
                            
                            with col3:
                                st.metric(
                                    "Durée totale",
                                    f"{cluster_impact['max_ttr']:.0f} min",
                                    help="TTR du dernier événement"
                                )
                            
                            with col4:
                                duration = (cluster['window_end'] - cluster['window_start']).total_seconds() / 60
                                st.metric(
                                    "Fenêtre",
                                    f"{duration:.0f} min"
                                )
                            
                            # Détail événements
                            st.markdown("**📋 Événements :**")
                            for event_detail in cluster_impact['events']:
                                impact = event_detail['impact']
                                icon = "🔺" if impact > 0 else "🔻"
                                st.caption(
                                    f"⏰ {event_detail['time'].strftime('%H:%M')} - "
                                    f"**{event_detail['family']}** : {icon} {abs(impact):.1f} pips "
                                    f"(latence: {event_detail['prediction']['latency_median']:.0f} min)"
                                )
                    
                    st.divider()
                    st.subheader("📊 Détails Individuels")
                else:
                    st.subheader("📊 Prédictions Individuelles")
                
'''

# Insérer avant la ligne 495 (index 494 car 0-based)
# Trouver la ligne exacte avec "for i, pred in enumerate(predictions):"
insert_line = None
for i, line in enumerate(lines):
    if "for i, pred in enumerate(predictions):" in line:
        insert_line = i
        break

if insert_line is not None:
    print(f"✅ Trouvé la boucle à la ligne {insert_line + 1}")
    
    # Insérer le toggle avant
    lines.insert(insert_line, toggle_code + "\n")
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Toggle inséré avant la ligne {insert_line + 1}")
else:
    print("❌ Boucle enumerate(predictions) non trouvée")

print("\n📋 Fichier modifié !")
print("   Relance streamlit pour voir le toggle")
