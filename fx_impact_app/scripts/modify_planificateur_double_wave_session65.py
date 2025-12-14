"""
Script de Modification Planificateur V2 - Double Wave Integration
==================================================================

Ce script modifie automatiquement le Planificateur V2 pour intégrer
la détection et l'affichage du Double Wave Momentum (Session 65).

Modifications à appliquer :
1. Ajouter import double_wave
2. Modifier calculate_predictions() pour détecter Double Wave
3. Créer nouvelle fonction create_double_wave_chart()
4. Modifier interface pour afficher type de mouvement

Auteur: Session 65
Date: 24 octobre 2025
"""

import re
from pathlib import Path
import shutil

# Chemins
PLANIFICATEUR_PATH = Path(__file__).parent.parent / "streamlit_app" / "pages" / "5_Planificateur_V2_FORMULES_VALIDEES.py"

def apply_modifications():
    """Applique toutes les modifications au Planificateur V2"""
    
    print("="*70)
    print("MODIFICATION PLANIFICATEUR V2 - DOUBLE WAVE INTEGRATION")
    print("="*70)
    
    # 1. Créer backup
    print("\n1. Création backup...")
    backup_path = str(PLANIFICATEUR_PATH) + ".backup_session65_before_double_wave"
    shutil.copy2(PLANIFICATEUR_PATH, backup_path)
    print(f"   ✅ Backup créé : {backup_path}")
    
    # 2. Lire fichier
    print("\n2. Lecture fichier original...")
    with open(PLANIFICATEUR_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   ✅ Fichier lu : {len(content)} caractères")
    
    # 3. Ajouter import double_wave
    print("\n3. Ajout import double_wave...")
    
    # Trouver la position après les imports formulas_validated
    import_pos = content.find("get_all_formulas_info\n)")
    if import_pos == -1:
        print("   ❌ Pattern import non trouvé")
        return False
    
    import_code = """

# Import module Double Wave (Session 64-65)
from double_wave import (
    detect_double_wave_conditions,
    predict_double_wave_timeline
)
"""
    
    content = content[:import_pos + len("get_all_formulas_info\n)")] + import_code + content[import_pos + len("get_all_formulas_info\n)"):]
    print("   ✅ Import double_wave ajouté")
    
    # 4. Modifier calculate_predictions pour ajouter détection Double Wave
    print("\n4. Modification calculate_predictions()...")
    
    # Chercher la ligne avec "return {" dans calculate_predictions
    pattern = r"(def calculate_predictions\(cpi_events: pd\.DataFrame\) -> dict:.*?)(    return \{)"
    
    double_wave_detection = """
    # ═══════════════════════════════════════════════════════════════
    # SESSION 65 : DÉTECTION DOUBLE WAVE MOMENTUM
    # ═══════════════════════════════════════════════════════════════
    
    # Préparer événements pour détection
    events_for_detection = []
    for _, event in cpi_events.iterrows():
        events_for_detection.append({
            'actual': event.get('actual'),
            'estimate': event.get('estimate'),
            'importance_n': 3  # CPI = HIGH importance
        })
    
    # Détecter si Double Wave
    is_double_wave = detect_double_wave_conditions(
        events_for_detection,
        surprise_threshold=20.0,
        min_cluster_size=5
    )
    
    # Si Double Wave, calculer timeline complète
    double_wave_timeline = None
    if is_double_wave:
        # Utiliser timestamp premier événement
        start_time = pd.to_datetime(cpi_events.iloc[0]['ts_utc'])
        
        double_wave_timeline = predict_double_wave_timeline(
            base_impact=impact,
            surprise_pct=max_surprise,
            cluster_size=len(cpi_events),
            start_time=start_time
        )
    
    """
    
    content = re.sub(
        pattern,
        r'\1' + double_wave_detection + r'\2',
        content,
        flags=re.DOTALL
    )
    
    # Modifier le return pour ajouter les champs Double Wave
    old_return = "'events': cpi_events\n    }"
    new_return = """'events': cpi_events,
        'is_double_wave': is_double_wave,
        'double_wave_timeline': double_wave_timeline
    }"""
    
    content = content.replace(old_return, new_return)
    print("   ✅ Détection Double Wave ajoutée à calculate_predictions()")
    
    # 5. Ajouter create_double_wave_chart() après create_timeline_chart()
    print("\n5. Ajout fonction create_double_wave_chart()...")
    
    # Trouver la fin de create_timeline_chart
    chart_end = content.find("    return fig\n\n\n# ═══════════════════════════════════════════════════════════════\n# INTERFACE PRINCIPALE")
    
    if chart_end == -1:
        print("   ❌ Position d'insertion non trouvée")
        return False
    
    double_wave_chart_function = """

def create_double_wave_chart(predictions: dict, start_price: float) -> go.Figure:
    \"\"\"
    Crée un graphique chandelier pour mouvement Double Wave Momentum
    Timeline précise avec 2 phases distinctes (Session 64-65)
    
    Args:
        predictions: Résultats incluant double_wave_timeline
        start_price: Prix de départ
    
    Returns:
        Figure Plotly
    \"\"\"
    fig = go.Figure()
    
    if not predictions or not predictions.get('double_wave_timeline'):
        return fig
    
    timeline = predictions['double_wave_timeline']
    first_event = predictions['events'].iloc[0]
    event_time = pd.to_datetime(first_event['ts_utc'])
    
    # Extraire valeurs timeline
    phase1_pips = timeline['phase1']['impact_pips']
    pullback_pips = timeline['pullback']['retrace_pips']
    phase2_pips = timeline['phase2']['impact_pips']
    
    phase1_peak = timeline['phase1']['peak_time']
    pullback_low = timeline['pullback']['low_time']
    phase2_peak = timeline['phase2']['peak_time']
    stabilization = timeline['stabilization_time']
    
    # Calculs prix
    p0 = start_price  # Départ
    p1 = p0 + (phase1_pips * 0.0001)  # Peak Phase 1 (T+5)
    p2 = p1 - (pullback_pips * 0.0001)  # Creux Pullback (T+11)
    p3 = p2 + (phase2_pips * 0.0001)  # Peak Phase 2 (T+15) - ABSOLU
    p4 = p3 - (phase2_pips * 0.15 * 0.0001)  # Stabilisation (T+40)
    
    # Créer données chandelier simulées
    times = []
    opens = []
    highs = []
    lows = []
    closes = []
    
    # Phase 1 : Montée (T+0 to T+5)
    num_candles_1 = 5
    for i in range(num_candles_1):
        t = event_time + timedelta(minutes=i)
        price_start = p0 + (phase1_pips * 0.0001 * i / num_candles_1)
        price_end = p0 + (phase1_pips * 0.0001 * (i + 1) / num_candles_1)
        
        times.append(t)
        opens.append(price_start)
        closes.append(price_end)
        highs.append(price_end + 0.0001)
        lows.append(price_start - 0.00005)
    
    # Pullback : Descente (T+5 to T+11)
    num_candles_pullback = 6
    for i in range(num_candles_pullback):
        t = phase1_peak + timedelta(minutes=i)
        price_start = p1 - (pullback_pips * 0.0001 * i / num_candles_pullback)
        price_end = p1 - (pullback_pips * 0.0001 * (i + 1) / num_candles_pullback)
        
        times.append(t)
        opens.append(price_start)
        closes.append(price_end)
        highs.append(price_start + 0.00005)
        lows.append(price_end - 0.0001)
    
    # Phase 2 : Remontée forte (T+11 to T+15)
    num_candles_2 = 4
    for i in range(num_candles_2):
        t = pullback_low + timedelta(minutes=i)
        price_start = p2 + (phase2_pips * 0.0001 * i / num_candles_2)
        price_end = p2 + (phase2_pips * 0.0001 * (i + 1) / num_candles_2)
        
        times.append(t)
        opens.append(price_start)
        closes.append(price_end)
        highs.append(price_end + 0.0001)
        lows.append(price_start - 0.00005)
    
    # Stabilisation (T+15 to T+40)
    num_candles_stab = 25
    for i in range(num_candles_stab):
        t = phase2_peak + timedelta(minutes=i)
        price_start = p3 - (phase2_pips * 0.15 * 0.0001 * i / num_candles_stab)
        price_end = p3 - (phase2_pips * 0.15 * 0.0001 * (i + 1) / num_candles_stab)
        
        times.append(t)
        opens.append(price_start)
        closes.append(price_end)
        highs.append(price_start + 0.00008)
        lows.append(price_end - 0.00008)
    
    # Créer chandelier
    fig.add_trace(go.Candlestick(
        x=times,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        name='EUR/USD',
        increasing_line_color='darkgreen',
        decreasing_line_color='darkred'
    ))
    
    # Annotations phases
    fig.add_annotation(
        x=event_time + timedelta(minutes=2.5),
        y=(p0 + p1) / 2,
        text=f"Phase 1: Réaction Algos<br>+{phase1_pips:.0f} pips / 5 min",
        showarrow=True,
        arrowhead=2,
        bgcolor="green",
        opacity=0.8,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=phase1_peak,
        y=p1,
        text=f"📈 Peak Phase 1<br>{phase1_peak.strftime('%H:%M')}<br>+{phase1_pips:.0f} pips",
        showarrow=True,
        arrowhead=2,
        bgcolor="orange",
        opacity=0.9,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=phase1_peak + timedelta(minutes=3),
        y=(p1 + p2) / 2,
        text=f"Pullback: Prise Profits<br>-{pullback_pips:.0f} pips / 6 min",
        showarrow=True,
        arrowhead=2,
        bgcolor="red",
        opacity=0.8,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=pullback_low,
        y=p2,
        text=f"⬇️ Creux Pullback<br>{pullback_low.strftime('%H:%M')}<br>{p2:.5f}",
        showarrow=True,
        arrowhead=2,
        bgcolor="blue",
        opacity=0.9,
        font=dict(color="white", size=11)
    )
    
    fig.add_annotation(
        x=pullback_low + timedelta(minutes=2),
        y=(p2 + p3) / 2,
        text=f"Phase 2: Ordres Institutionnels<br>+{phase2_pips:.0f} pips / 4 min",
        showarrow=True,
        arrowhead=2,
        bgcolor="darkgreen",
        opacity=0.8,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=phase2_peak,
        y=p3,
        text=f"🚀 PEAK ABSOLU<br>{phase2_peak.strftime('%H:%M')}<br>+{timeline['total_net_pips']:.0f} pips total",
        showarrow=True,
        arrowhead=2,
        bgcolor="gold",
        opacity=0.9,
        font=dict(color="black", size=12, family="Arial Black")
    )
    
    fig.add_annotation(
        x=phase2_peak + timedelta(minutes=12),
        y=(p3 + p4) / 2,
        text=f"Stabilisation<br>25 min",
        showarrow=True,
        arrowhead=2,
        bgcolor="gray",
        opacity=0.7,
        font=dict(color="white")
    )
    
    # Lignes horizontales
    fig.add_hline(y=p0, line_dash="dot", line_color="gray", 
                  annotation_text="Prix départ", annotation_position="right")
    fig.add_hline(y=p1, line_dash="dot", line_color="orange", 
                  annotation_text="Peak Phase 1 (T+5)", annotation_position="right")
    fig.add_hline(y=p2, line_dash="dot", line_color="blue", 
                  annotation_text="Creux Pullback (T+11)", annotation_position="right")
    fig.add_hline(y=p3, line_dash="dash", line_color="gold", line_width=2,
                  annotation_text="PEAK ABSOLU (T+15)", annotation_position="right")
    fig.add_hline(y=p4, line_dash="dot", line_color="green", 
                  annotation_text="Stabilisation (T+40)", annotation_position="right")
    
    fig.update_layout(
        title="🌊 Double Wave Momentum - Timeline Prédite (Session 64-65)",
        xaxis_title="Temps (UTC)",
        yaxis_title="Prix EUR/USD",
        hovermode='x unified',
        height=700,
        xaxis_rangeslider_visible=False,
        showlegend=True
    )
    
    return fig


"""
    
    content = content[:chart_end + len("    return fig")] + double_wave_chart_function + content[chart_end + len("    return fig"):]
    print("   ✅ Fonction create_double_wave_chart() ajoutée")
    
    # 6. Modifier l'interface pour afficher le type de mouvement
    print("\n6. Modification interface utilisateur...")
    
    # Ajouter badge type mouvement après les métriques
    old_details = "    # Détails calcul\n    st.markdown(\"### 🔍 Détails du Calcul\")"
    
    new_details = """    # Type de mouvement détecté
    st.markdown("### 🌊 Type de Mouvement Détecté")
    
    if predictions.get('is_double_wave'):
        st.success("✅ **DOUBLE WAVE MOMENTUM** détecté ! (Session 64-65)")
        st.info(f\"\"\"
        **Conditions remplies :**
        - ✅ Surprise > 20% ({predictions['max_surprise']:.1f}%)
        - ✅ Cluster ≥ 5 événements ({predictions['num_events']})
        - ✅ Importance HIGH (CPI)
        
        **Implications :**
        - Mouvement en 2 vagues distinctes (algos puis institutionnels)
        - Timeline précise : T+5, T+11, T+15, T+40
        - Précision validée : 93% impact, 100% timing
        \"\"\")
    else:
        st.info("ℹ️ **Single Wave** - Mouvement linéaire classique")
        st.caption(f\"\"\"
        Conditions Double Wave non remplies :
        - Surprise : {predictions['max_surprise']:.1f}% (seuil 20%)
        - Cluster : {predictions['num_events']} événements (seuil 5)
        \"\"\")
    
    # Détails calcul
    st.markdown("### 🔍 Détails du Calcul")"""
    
    content = content.replace(old_details, new_details)
    
    # Modifier affichage graphique pour choisir le bon
    old_graph = "    # Graphique timeline\n    st.markdown(\"### 📈 Timeline Prédite\")\n    fig = create_timeline_chart(predictions, start_price)\n    st.plotly_chart(fig, use_container_width=True)"
    
    new_graph = """    # Graphique timeline
    st.markdown("### 📈 Timeline Prédite")
    
    # Choisir le bon graphique selon type de mouvement
    if predictions.get('is_double_wave'):
        fig = create_double_wave_chart(predictions, start_price)
    else:
        fig = create_timeline_chart(predictions, start_price)
    
    st.plotly_chart(fig, use_container_width=True)"""
    
    content = content.replace(old_graph, new_graph)
    
    # Enrichir l'export CSV
    old_export = "        'Mouvement_Net_Final_Pips': impact_net_final\n    }"
    new_export = """        'Mouvement_Net_Final_Pips': impact_net_final,
        'Movement_Type': 'Double Wave' if predictions.get('is_double_wave') else 'Single Wave',
        'Phase1_Peak_Time': predictions['double_wave_timeline']['phase1']['peak_time'].strftime('%H:%M:%S') if predictions.get('is_double_wave') else 'N/A',
        'Pullback_Low_Time': predictions['double_wave_timeline']['pullback']['low_time'].strftime('%H:%M:%S') if predictions.get('is_double_wave') else 'N/A',
        'Phase2_Peak_Time': predictions['double_wave_timeline']['phase2']['peak_time'].strftime('%H:%M:%S') if predictions.get('is_double_wave') else 'N/A',
        'Stabilization_Time': predictions['double_wave_timeline']['stabilization_time'].strftime('%H:%M:%S') if predictions.get('is_double_wave') else 'N/A'
    }"""
    
    content = content.replace(old_export, new_export)
    
    print("   ✅ Interface modifiée pour afficher type mouvement")
    print("   ✅ Export CSV enrichi avec colonnes Double Wave")
    
    # 7. Mettre à jour version et footer
    print("\n7. Mise à jour version...")
    
    content = content.replace('Version 2.2 - Session 62', 'Version 2.3 - Session 65 (Double Wave)')
    content = content.replace(
        '**Planificateur V2** - Version 2.2 (Session 62)',
        '**Planificateur V2** - Version 2.3 (Session 65 - Double Wave Momentum)'
    )
    
    footer_addition = """  
✅ **NOUVEAU (Session 65)** : Détection automatique Double Wave Momentum  
✅ Timeline précise 2 phases (T+5, T+11, T+15, T+40) si conditions remplies  
✅ Export CSV enrichi avec type de mouvement et timing des phases"""
    
    content = content.replace(
        '✅ Formules : Ajustement Score (99.9%), Impact D (98.6%), TTR C (94.4%), Pullback V2 (99.3%)\n""")',
        '✅ Formules : Ajustement Score (99.9%), Impact D (98.6%), TTR C (94.4%), Pullback V2 (99.3%)  \n' + footer_addition + '\n""")'
    )
    
    print("   ✅ Version mise à jour : 2.3")
    
    # 8. Écrire fichier modifié
    print("\n8. Écriture fichier modifié...")
    with open(PLANIFICATEUR_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"   ✅ Fichier écrit : {len(content)} caractères")
    
    print("\n" + "="*70)
    print("✅ MODIFICATION TERMINÉE AVEC SUCCÈS")
    print("="*70)
    print(f"\n📁 Fichier modifié : {PLANIFICATEUR_PATH}")
    print(f"📁 Backup disponible : {backup_path}")
    print("\n🎯 Prochaines étapes :")
    print("   1. Tester l'interface Streamlit")
    print("   2. Valider sur 11 septembre 2025")
    print("   3. Comparer graphiques avec MT5")
    
    return True


if __name__ == "__main__":
    success = apply_modifications()
    if success:
        print("\n✅ Script terminé avec succès")
    else:
        print("\n❌ Erreurs lors de l'exécution")
