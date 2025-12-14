#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXÉCUTION PIPELINE ÉTAPE PAR ÉTAPE
===================================

Exécute le pipeline étape par étape et affiche les résultats détaillés
de chaque étape pour identifier précisément où le problème se produit.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def print_separator(title=""):
    """Affiche un séparateur visuel"""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print("=" * 80)
    else:
        print("=" * 80)
    print()

def executer_etape_par_etape():
    """Exécute le pipeline étape par étape avec traçage détaillé"""
    
    date_str = '2025-08-01'
    
    print_separator(f"EXÉCUTION PIPELINE ÉTAPE PAR ÉTAPE - {date_str}")
    
    executor = PipelineExecutor(DB_PATH, verbose=True)
    
    # ÉTAPE 1 : Chargement événements
    print_separator("ÉTAPE 1 : CHARGEMENT ÉVÉNEMENTS")
    
    events_etape1 = executor.etape1_charger_evenements(
        date_str=date_str,
        countries=['US'],
        min_score=40.0
    )
    
    print(f"✅ Événements chargés : {len(events_etape1)}")
    print(f"\nÉvénements :")
    for idx, (_, event) in enumerate(events_etape1.iterrows(), 1):
        print(f"  {idx}. {event.get('event_title', 'N/A')[:50]}")
        print(f"     Score : {event.get('empirical_score', 'N/A')}")
        print(f"     Actual : {event.get('actual', 'N/A')}")
        print(f"     Estimate : {event.get('estimate', 'N/A')}")
    
    # Calculer surprise maximale manuellement
    max_surprise = 0.0
    for _, event in events_etape1.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        if actual is not None and estimate is not None and estimate != 0:
            surprise = abs(actual - estimate) / abs(estimate) * 100
            max_surprise = max(max_surprise, surprise)
    
    print(f"\n📊 Surprise maximale calculée : {max_surprise:.1f}%")
    
    # ÉTAPE 2 : Détection clusters
    print_separator("ÉTAPE 2 : DÉTECTION CLUSTERS")
    
    clusters_etape2 = executor.etape2_detecter_clusters(
        events=events_etape1,
        window_minutes=30
    )
    
    print(f"✅ Clusters détectés : {len(clusters_etape2)}")
    if clusters_etape2:
        cluster_cible = clusters_etape2[0]
        print(f"\nCluster cible :")
        print(f"  Nombre événements : {len(cluster_cible['events'])}")
        print(f"  Anchor time : {cluster_cible.get('anchor_time', 'N/A')}")
    else:
        print("❌ Aucun cluster détecté")
        return
    
    # ÉTAPE 3 : Définir noyau dur
    print_separator("ÉTAPE 3 : DÉFINIR NOYAU DUR")
    
    cluster_info_etape3 = executor.etape3_definir_noyau_dur(
        cluster=cluster_cible,
        support_threshold=0.8
    )
    
    print(f"✅ Noyau dur défini")
    print(f"  Type : {cluster_info_etape3.get('core_type', 'N/A')}")
    print(f"  Événements core : {cluster_info_etape3.get('n_core_events', 0)}/{cluster_info_etape3.get('n_total_events', 0)}")
    
    # ÉTAPE 4 : Rechercher clusters identiques
    print_separator("ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES")
    
    identical_clusters_etape4 = executor.etape4_rechercher_clusters_identiques(
        cluster_info=cluster_info_etape3,
        jaccard_threshold=0.60,
        years_lookback=5
    )
    
    print(f"✅ Clusters identiques trouvés : {len(identical_clusters_etape4)}")
    
    # ÉTAPE 5 : Calculer tendances
    print_separator("ÉTAPE 5 : CALCULER TENDANCES")
    
    trends_etape5 = executor.etape5_calculer_tendances_impacts(
        identical_clusters=identical_clusters_etape4,
        db_path=DB_PATH
    )
    
    print(f"✅ Tendances calculées")
    if not trends_etape5.empty:
        n_trends = trends_etape5['trend_exists'].sum() if 'trend_exists' in trends_etape5.columns else 0
        print(f"  Clusters avec tendance : {n_trends}/{len(trends_etape5)}")
    
    # ÉTAPE 6 : Calculer impacts base & amplifications
    print_separator("ÉTAPE 6 : CALCULER IMPACTS BASE & AMPLIFICATIONS")
    
    impacts_etape6 = executor.etape6_calculer_impacts_base_amplifications(
        identical_clusters=identical_clusters_etape4,
        trends_df=trends_etape5,
        db_path=DB_PATH
    )
    
    print(f"✅ Impacts calculés")
    if not impacts_etape6.empty:
        print(f"  Nombre clusters avec impacts : {len(impacts_etape6)}")
        if 'amplification_parfaite' in impacts_etape6.columns:
            amp_mean = impacts_etape6['amplification_parfaite'].mean()
            print(f"  Amplification moyenne historique : {amp_mean:.3f}x")
    
    # ÉTAPE 7 : Analyser relation tendance → amplification
    print_separator("ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION")
    
    analysis_etape7 = executor.etape7_analyser_relation_tendance_amplification(
        trends_df=trends_etape5,
        impacts_df=impacts_etape6
    )
    
    print(f"✅ Analyse terminée")
    
    # ÉTAPE 8 : Application au cluster cible
    print_separator("ÉTAPE 8 : APPLICATION AU CLUSTER CIBLE")
    print("⚠️  ATTENTION : Cette étape est longue, traçage détaillé ci-dessous...")
    print()
    
    # Exécuter étape 8 avec traçage détaillé
    try:
        result_etape8 = executor.etape8_appliquer_cluster_cible(
            cluster_info=cluster_info_etape3,
            analysis_results=analysis_etape7,
            identical_clusters=identical_clusters_etape4
        )
        
        print_separator("RÉSULTATS ÉTAPE 8 - ANALYSE DÉTAILLÉE")
        
        # Afficher tous les résultats de l'étape 8
        print("📊 RÉSULTATS COMPLETS ÉTAPE 8 :")
        print()
        
        impact_base = result_etape8.get('impact_base', 0.0)
        amplification_predite = result_etape8.get('amplification_predite', 0.0)
        adjustment_factor = result_etape8.get('adjustment_factor', 1.0)
        prediction_finale = result_etape8.get('prediction_finale', 0.0)
        
        print(f"1. Impact de base : {impact_base:.2f} pips")
        print(f"2. Amplification prédite : {amplification_predite:.3f}x")
        print(f"3. Ajustement (S/R + Patterns) : {adjustment_factor:.3f}x")
        print()
        
        # Calculer impact_formules théorique
        impact_formules_theorique = impact_base * amplification_predite * adjustment_factor
        print(f"4. Impact formules théorique : {impact_base:.2f} × {amplification_predite:.3f} × {adjustment_factor:.3f} = {impact_formules_theorique:.2f} pips")
        print()
        
        # Pattern info
        pattern_info = result_etape8.get('pattern_info', {})
        pattern_type = result_etape8.get('pattern_type', 'NONE')
        pattern_impact = pattern_info.get('wave2_peak_pips_absolute', 0.0) or pattern_info.get('wave2_pips', 0.0)
        
        print(f"5. Pattern type : {pattern_type}")
        print(f"6. Pattern impact (pic absolu) : {pattern_impact:.2f} pips")
        print()
        
        # Détails du pattern
        if pattern_info:
            print("   Détails pattern :")
            print(f"     Wave1 pips : {pattern_info.get('wave1_pips', 0.0):.2f}")
            print(f"     Wave2 pips : {pattern_info.get('wave2_pips', 0.0):.2f}")
            print(f"     Wave2 peak absolute : {pattern_info.get('wave2_peak_pips_absolute', 0.0):.2f}")
            print(f"     Pullback pips : {pattern_info.get('pullback_pips', 0.0):.2f}")
            print()
        
        # Écart
        ecart_absolu = abs(pattern_impact - impact_formules_theorique) if pattern_impact > 0 else 0
        print(f"7. Écart pattern vs formules : {ecart_absolu:.2f} pips")
        print()
        
        # Stratégie
        prediction_method = "N/A"
        if ecart_absolu < 10 or pattern_impact == 0:
            prediction_method = "Formules"
        else:
            prediction_method = "Pattern"
        
        print(f"8. Stratégie choisie : {prediction_method}")
        print(f"   (Écart {'<' : '<' if ecart_absolu < 10 else '>='} 10 pips)")
        print()
        
        # Prédiction finale
        print(f"9. Prédiction finale : {prediction_finale:.2f} pips")
        print()
        
        # Vérification
        if prediction_method == "Formules":
            expected = impact_formules_theorique
        else:
            expected = pattern_impact
        
        print(f"10. Vérification :")
        print(f"    Attendu ({prediction_method}) : {expected:.2f} pips")
        print(f"    Obtenu : {prediction_finale:.2f} pips")
        
        if abs(prediction_finale - expected) > 0.01:
            print(f"    ⚠️  DIFFÉRENCE : {abs(prediction_finale - expected):.2f} pips")
        else:
            print(f"    ✅ Cohérent")
        
        print()
        
        # Comparaison avec impact réel
        print_separator("COMPARAISON AVEC IMPACT RÉEL")
        
        impact_reel = 188.4  # Valeur connue
        erreur = abs(prediction_finale - impact_reel)
        erreur_pct = (erreur / impact_reel * 100) if impact_reel > 0 else 0
        
        print(f"Impact réel : {impact_reel:.1f} pips")
        print(f"Prédiction : {prediction_finale:.2f} pips")
        print(f"Erreur absolue : {erreur:.1f} pips")
        print(f"Erreur relative : {erreur_pct:.1f}%")
        print()
        
        # Analyse des problèmes
        print_separator("ANALYSE DES PROBLÈMES")
        
        if prediction_finale > 1000:
            print("❌ PROBLÈME CRITIQUE : Prédiction finale > 1000 pips (irréaliste)")
            print()
            print("Causes possibles :")
            print("  1. Pattern impact mal calculé")
            print("  2. Multiplication multiple de l'amplification")
            print("  3. Stratégie hybride incorrecte")
        
        if pattern_impact > 1000:
            print(f"❌ PROBLÈME : Pattern impact = {pattern_impact:.2f} pips (trop élevé)")
            print(f"   → Le pic absolu devrait être ~183 pips selon les logs")
        
        if impact_formules_theorique > 1000:
            print(f"❌ PROBLÈME : Impact formules = {impact_formules_theorique:.2f} pips (trop élevé)")
            print(f"   → Vérifier le calcul : {impact_base:.2f} × {amplification_predite:.3f} × {adjustment_factor:.3f}")
        
    except Exception as e:
        print(f"❌ Erreur étape 8 : {e}")
        import traceback
        traceback.print_exc()
    
    print_separator("FIN DE L'ANALYSE ÉTAPE PAR ÉTAPE")

if __name__ == "__main__":
    executer_etape_par_etape()




