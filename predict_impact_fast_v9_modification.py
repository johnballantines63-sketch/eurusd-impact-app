"""
MODIFICATION POUR predict_impact_fast()
Session 11 - Intégration v9-CLEAN

Ce fichier contient la nouvelle version de la fonction predict_impact_fast()
qui utilise la formule v9-CLEAN au lieu du facteur multiplicateur basique.

CHANGEMENTS:
1. Remplace: mfe * score_factor
2. Par: ForecastEngine.predict_impact_v9_clean()
3. Compte le nombre d'événements simultanés pour choisir la bonne formule
"""

def predict_impact_fast_v9(family, surprise, precomputed_stats, years_back=3, empirical_score=None, num_events=1):
    """
    Version AMÉLIORÉE avec formule v9-CLEAN (Session 11)
    
    Args:
        family: Nom de la famille d'événement
        surprise: Écart entre actual et forecast
        precomputed_stats: Stats pré-calculées
        years_back: Années d'historique
        empirical_score: Score empirique 0-100 (si disponible depuis la DB)
        num_events: Nombre d'événements simultanés (pour choisir formule v9)
    
    Returns:
        Dict avec prédiction d'impact
    """
    # Gérer le cas où family est None
    if family is None:
        return None
    
    # Normaliser le nom de famille (espaces → underscores)
    family_normalized = family.replace(' ', '_')
    if family_normalized in precomputed_stats:
        stats = precomputed_stats[family_normalized]
        
        # ✅ NOUVEAU: Utiliser formule v9-CLEAN si score empirique disponible
        if empirical_score is not None and empirical_score > 0:
            # Créer instance temporaire de ForecastEngine pour accéder à predict_impact_v9_clean
            from forecaster_mvp import ForecastEngine
            from config import get_db_path
            
            engine = ForecastEngine(get_db_path())
            predicted_impact = engine.predict_impact_v9_clean(empirical_score, num_events)
            engine.close()
            
            # La formule v9-CLEAN donne l'impact absolu, pas besoin de direction ici
            mfe = abs(predicted_impact) if predicted_impact is not None else stats['mfe_p80']
            
            print(f"   🎯 v9-CLEAN: {family_normalized} (score {empirical_score:.0f}/100, {num_events} evt) → {mfe:.1f} pips")
        else:
            # Fallback: utiliser mfe_p80 historique
            mfe = stats['mfe_p80']
            print(f"   📊 Historique: {family_normalized} → {mfe:.1f} pips (pas de score)")
        
        # Ajustement surprise (facteur de modulation)
        impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
        impact = mfe * impact_factor
        
        # Direction selon surprise
        direction = get_event_direction(family, surprise)
        
        # TTR correction (comme avant)
        ttr_corrected = stats['ttr_median']
        ttr_p20_corrected = stats['ttr_p20']
        ttr_p80_corrected = stats['ttr_p80']
        
        if ttr_corrected > 20:
            correction_factor = 0.23
            ttr_corrected = stats['ttr_median'] * correction_factor
            ttr_p20_corrected = stats['ttr_p20'] * correction_factor
            ttr_p80_corrected = stats['ttr_p80'] * correction_factor
        
        return {
            'predicted_pips': impact,
            'direction': direction,
            'latency_median': stats['latency_median'],
            'latency_p20': stats['latency_p20'],
            'latency_p80': stats['latency_p80'],
            'ttr_median': ttr_corrected,
            'ttr_p20': ttr_p20_corrected,
            'ttr_p80': ttr_p80_corrected,
            'n_similar': stats['n_events'],
            'mfe_p80': stats['mfe_p80'],
            'source': 'v9_clean' if empirical_score else 'precomputed_db_corrected'
        }
    else:
        # Si pas dans stats pré-calculées, utiliser predict_impact classique
        result = predict_impact(family, surprise, years_back)
        if result:
            result['source'] = 'calculated'
        return result


# ════════════════════════════════════════════════════════════════
# INSTRUCTIONS D'INTÉGRATION
# ════════════════════════════════════════════════════════════════

"""
ÉTAPE 1: Backup
---------------
Créer backup du fichier actuel:
cp fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py \\
   fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py.backup_session11

ÉTAPE 2: Modifier la fonction
-----------------------------
Localiser la fonction predict_impact_fast() (ligne ~380-450)

Remplacer le bloc:
    if empirical_score is not None and empirical_score > 0:
        score_factor = empirical_score / 20.0
        mfe = mfe * score_factor

Par:
    if empirical_score is not None and empirical_score > 0:
        from forecaster_mvp import ForecastEngine
        from config import get_db_path
        
        engine = ForecastEngine(get_db_path())
        predicted_impact = engine.predict_impact_v9_clean(empirical_score, num_events)
        engine.close()
        
        mfe = abs(predicted_impact) if predicted_impact is not None else stats['mfe_p80']
        print(f"   🎯 v9-CLEAN: {family_normalized} (score {empirical_score:.0f}/100, {num_events} evt) → {mfe:.1f} pips")

ÉTAPE 3: Ajouter paramètre num_events
-------------------------------------
Modifier signature de la fonction:

DE:
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3, empirical_score=None):

VERS:
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3, empirical_score=None, num_events=1):

ÉTAPE 4: Modifier les appels
-----------------------------
Chercher tous les appels à predict_impact_fast() dans le fichier

Ajouter le paramètre num_events en comptant le nombre d'événements sélectionnés
dans la même fenêtre temporelle (< 30 min)

Exemple:
    # Ancien
    pred = predict_impact_fast(
        event['family'], 
        surprise, 
        precomputed_stats,
        empirical_score=empirical_score
    )
    
    # Nouveau
    pred = predict_impact_fast(
        event['family'], 
        surprise, 
        precomputed_stats,
        empirical_score=empirical_score,
        num_events=len(st.session_state.selected_events)  # ou calcul plus précis
    )

ÉTAPE 5: Tester
--------------
1. Lancer Streamlit:
   streamlit run fx_impact_app/streamlit_app/Home.py

2. Aller sur "Planificateur Multi-Événements"

3. Sélectionner 11 septembre 2025, 14:30

4. Vérifier logs console pour message:
   🎯 v9-CLEAN: CPI (score 81/100, 6 evt) → 28.6 pips

5. Comparer impact prédit vs ancien système
"""
