"""
Ajout mode fenêtres temporelles avec toggle ON/OFF

L'utilisateur peut choisir entre :
- Mode INDIVIDUEL : Chaque événement analysé isolément (comportement actuel)
- Mode FENÊTRES : Groupement automatique des événements proches
"""

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    content = f.read()

print("=" * 70)
print("🔧 AJOUT : Mode Fenêtres Temporelles avec Toggle")
print("=" * 70)

# ============================================================
# PARTIE 1 : Ajouter les fonctions de clustering
# ============================================================
print("\n📋 PARTIE 1 : Ajout fonctions clustering...")

clustering_code = '''
def group_events_by_time_window(events, max_gap_minutes=30):
    """
    Groupe les événements en clusters selon leur proximité temporelle
    
    Args:
        events: Liste de dict avec 'event_time'
        max_gap_minutes: Écart max entre deux événements d'un même cluster
    
    Returns:
        Liste de clusters, chaque cluster = {
            'window_start': datetime,
            'window_end': datetime,
            'events': [event1, event2, ...],
            'event_times': [time1, time2, ...]
        }
    """
    if not events:
        return []
    
    # Trier par temps
    sorted_events = sorted(events, key=lambda e: e['event_time'])
    
    clusters = []
    current_cluster = {
        'events': [sorted_events[0]],
        'event_times': [sorted_events[0]['event_time']]
    }
    
    for event in sorted_events[1:]:
        # Calculer écart avec dernier événement du cluster actuel
        last_time = current_cluster['event_times'][-1]
        gap = (event['event_time'] - last_time).total_seconds() / 60
        
        if gap <= max_gap_minutes:
            # Ajouter au cluster actuel
            current_cluster['events'].append(event)
            current_cluster['event_times'].append(event['event_time'])
        else:
            # Finaliser cluster actuel
            current_cluster['window_start'] = current_cluster['event_times'][0]
            current_cluster['window_end'] = current_cluster['event_times'][-1] + timedelta(minutes=30)
            clusters.append(current_cluster)
            
            # Démarrer nouveau cluster
            current_cluster = {
                'events': [event],
                'event_times': [event['event_time']]
            }
    
    # Finaliser dernier cluster
    current_cluster['window_start'] = current_cluster['event_times'][0]
    current_cluster['window_end'] = current_cluster['event_times'][-1] + timedelta(minutes=30)
    clusters.append(current_cluster)
    
    return clusters

def calculate_cluster_impact(cluster, predictions_dict):
    """
    Calcule l'impact cumulé d'un cluster d'événements
    
    Args:
        cluster: Dict du cluster (de group_events_by_time_window)
        predictions_dict: Dict {event_key: prediction}
    
    Returns:
        Dict avec impact cumulé, latence min, TTR max
    """
    cluster_impact = {
        'total_pips': 0,
        'min_latency': float('inf'),
        'max_ttr': 0,
        'events_count': len(cluster['events']),
        'window_start': cluster['window_start'],
        'window_end': cluster['window_end'],
        'events': []
    }
    
    for event in cluster['events']:
        event_key = f"{event['family']}_{event['event_time'].strftime('%Y%m%d_%H%M')}"
        pred = predictions_dict.get(event_key)
        
        if pred:
            impact = pred['predicted_pips'] * pred['direction']
            cluster_impact['total_pips'] += impact
            cluster_impact['min_latency'] = min(cluster_impact['min_latency'], pred['latency_median'])
            cluster_impact['max_ttr'] = max(cluster_impact['max_ttr'], pred['ttr_median'])
            cluster_impact['events'].append({
                'time': event['event_time'],
                'family': event['family'],
                'impact': impact,
                'prediction': pred
            })
    
    if cluster_impact['min_latency'] == float('inf'):
        cluster_impact['min_latency'] = 5
    
    return cluster_impact

'''

# Trouver où insérer (après get_event_direction)
insert_pos = content.find("@st.cache_data")
if insert_pos > 0:
    content = content[:insert_pos] + clustering_code + "\n\n" + content[insert_pos:]
    print("✅ Fonctions clustering ajoutées")
else:
    print("⚠️ Position d'insertion non trouvée, ajout en début")
    content = clustering_code + "\n\n" + content

# ============================================================
# PARTIE 2 : Ajouter toggle mode et section fenêtres
# ============================================================
print("\n📋 PARTIE 2 : Ajout toggle et affichage...")

toggle_and_display = '''
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
                        "ℹ️ **Mode Fenêtres Temporelles activé** : Les événements espacés de moins de "
                        f"{window_gap} min seront groupés et leur impact cumulé sera calculé. "
                        "Utile pour capturer les effets de plusieurs annonces proches (ex: 14:30 + 14:45)."
                    )
                else:
                    st.info(
                        "ℹ️ **Mode Individuel** : Chaque événement est analysé isolément. "
                        "Mode classique, utile pour événements bien espacés."
                    )
                
                st.divider()
                
                # ═══════════════════════════════════════════════════════════
                # AFFICHAGE SELON LE MODE
                # ═══════════════════════════════════════════════════════════
                
                if use_time_windows:
                    # MODE FENÊTRES TEMPORELLES
                    st.subheader("🕐 Fenêtres Temporelles d'Événements")
                    
                    # Grouper événements
                    event_list = [{
                        'event_time': pred['event']['time'], 
                        'family': pred['event']['family']
                    } for pred in predictions]
                    
                    clusters = group_events_by_time_window(event_list, max_gap_minutes=window_gap)
                    
                    # Créer dict de prédictions pour lookup
                    pred_dict = {}
                    for pred in predictions:
                        key = f"{pred['event']['family']}_{pred['event']['time'].strftime('%Y%m%d_%H%M')}"
                        pred_dict[key] = pred
                    
                    if len(clusters) > 1:
                        st.success(f"✅ {len(clusters)} fenêtres d'événements détectées")
                    elif len(clusters) == 1 and len(clusters[0]['events']) > 1:
                        st.success(f"✅ 1 fenêtre avec {len(clusters[0]['events'])} événements groupés")
                    else:
                        st.info("ℹ️ Un seul événement → Mode individuel appliqué")
                    
                    for cluster_idx, cluster in enumerate(clusters):
                        cluster_impact = calculate_cluster_impact(cluster, pred_dict)
                        
                        # Titre du cluster
                        cluster_title = (
                            f"🕐 Fenêtre {cluster_idx + 1} : "
                            f"{cluster['window_start'].strftime('%H:%M')} → "
                            f"{cluster['window_end'].strftime('%H:%M')} "
                            f"({cluster_impact['events_count']} événement{'s' if cluster_impact['events_count'] > 1 else ''})"
                        )
                        
                        with st.expander(cluster_title, expanded=True):
                            # Métriques du cluster
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                impact_direction = "🔺 UP" if cluster_impact['total_pips'] > 0 else "🔻 DOWN"
                                st.metric(
                                    "Impact Cumulé",
                                    f"{abs(cluster_impact['total_pips']):.1f} pips",
                                    delta=impact_direction
                                )
                            
                            with col2:
                                st.metric(
                                    "Réaction",
                                    f"{cluster_impact['min_latency']:.0f} min",
                                    help="Latence du premier événement"
                                )
                            
                            with col3:
                                st.metric(
                                    "Durée totale",
                                    f"{cluster_impact['max_ttr']:.0f} min",
                                    help="Temps pour absorber tous les événements"
                                )
                            
                            with col4:
                                window_duration = (cluster['window_end'] - cluster['window_start']).total_seconds() / 60
                                st.metric(
                                    "Fenêtre",
                                    f"{window_duration:.0f} min",
                                    help="Durée de la fenêtre temporelle"
                                )
                            
                            # Liste des événements
                            st.markdown("**📋 Événements dans cette fenêtre :**")
                            
                            for event_detail in cluster_impact['events']:
                                impact = event_detail['impact']
                                direction_icon = "🔺" if impact > 0 else "🔻"
                                
                                col_time, col_event = st.columns([1, 4])
                                
                                with col_time:
                                    st.caption(f"⏰ {event_detail['time'].strftime('%H:%M')}")
                                
                                with col_event:
                                    st.caption(
                                        f"**{event_detail['family']}** : "
                                        f"{direction_icon} {abs(impact):.1f} pips "
                                        f"(latence: {event_detail['prediction']['latency_median']:.0f} min)"
                                    )
                    
                    st.divider()
                    st.subheader("📊 Détails Individuels")
                
                else:
                    # MODE INDIVIDUEL (comportement actuel)
                    st.subheader("📊 Prédictions Individuelles")
                
'''

# Chercher où insérer (avant "for pred in predictions:")
search_pattern = "                for pred in predictions:"
insert_pos = content.find(search_pattern)

if insert_pos > 0:
    content = content[:insert_pos] + toggle_and_display + "\n" + content[insert_pos:]
    print("✅ Toggle et section fenêtres ajoutés")
else:
    print("⚠️ Pattern non trouvé")

# ============================================================
# PARTIE 3 : Import datetime
# ============================================================
print("\n📋 PARTIE 3 : Vérification imports...")

if "from datetime import" not in content:
    import_pos = content.find("import streamlit as st")
    if import_pos > 0:
        content = content[:import_pos] + "from datetime import datetime, timedelta\n" + content[import_pos:]
        print("✅ Import datetime ajouté")
else:
    print("✅ Import datetime déjà présent")

# ============================================================
# Sauvegarder
# ============================================================
with open(file_path, 'w') as f:
    f.write(content)

print("\n" + "=" * 70)
print("✅ MODE FENÊTRES TEMPORELLES AJOUTÉ AVEC TOGGLE !")
print("=" * 70)

print("\n📊 Résumé:")
print("  ✅ Fonctions clustering ajoutées")
print("  ✅ Toggle 'Mode Fenêtres Temporelles' (ON par défaut)")
print("  ✅ Paramètre 'Écart max' configurable (30 min par défaut)")
print("  ✅ Mode Individuel toujours disponible")
print("  ✅ Affichage conditionnel selon le mode")

print("\n🎯 Utilisation:")
print("  • ☑️ Coché : Fenêtres temporelles (détection auto clusters)")
print("  • ☐ Décoché : Mode individuel (comportement actuel)")

print("\n📋 Avantages:")
print("  ✓ Pas de sauvegarde nécessaire (toggle ON/OFF)")
print("  ✓ Utilisateur garde le contrôle")
print("  ✓ Deux modes coexistent")
print("  ✓ Paramètre écart configurable (10-60 min)")
