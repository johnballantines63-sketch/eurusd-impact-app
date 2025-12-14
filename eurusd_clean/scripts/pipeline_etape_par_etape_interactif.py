#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Étape par Étape - Mode Interactif

Exécute le pipeline étape par étape avec pause après chaque étape
pour validation avant de passer à la suivante.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from run_pipeline_complete import PipelineExecutor
from config import get_db_path

print("=" * 80)
print("🔍 PIPELINE ÉTAPE PAR ÉTAPE - MODE INTERACTIF")
print("=" * 80)
print()

# Date de test
date_str = '2025-09-11'
print(f"📅 Date de test : {date_str}")
print()

# Initialiser pipeline
db_path = Path(get_db_path())
executor = PipelineExecutor(db_path=db_path, verbose=True)

# ============================================================================
# ÉTAPE 1 : CHARGER ÉVÉNEMENTS
# ============================================================================
print("=" * 80)
print("ÉTAPE 1 : CHARGER ÉVÉNEMENTS")
print("=" * 80)
print()

try:
    df_events = executor.etape1_charger_evenements(date_str)
    
    print(f"✅ Événements chargés : {len(df_events)}")
    print()
    
    if not df_events.empty:
        print("Aperçu des événements :")
        print("-" * 80)
        for idx, (_, event) in enumerate(df_events.head(10).iterrows(), 1):
            event_key = event.get('event_key', 'N/A')
            country = event.get('country', 'N/A')
            importance = event.get('importance_n', 'N/A')
            score = event.get('empirical_score', 'N/A')
            ts_utc = event.get('ts_utc', 'N/A')
            print(f"{idx:2d}. {ts_utc} | {country:<3} | {event_key[:50]:<50} | Imp: {importance} | Score: {score}")
        
        if len(df_events) > 10:
            print(f"... et {len(df_events) - 10} autres événements")
    else:
        print("❌ Aucun événement chargé")
        sys.exit(1)
    
    print()
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 2...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 1 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 2 : DÉTECTER CLUSTERS
# ============================================================================
print("=" * 80)
print("ÉTAPE 2 : DÉTECTER CLUSTERS")
print("=" * 80)
print()

try:
    clusters = executor.etape2_detecter_clusters(df_events, window_minutes=30)
    
    print(f"✅ Clusters détectés : {len(clusters)}")
    print()
    
    for idx, cluster in enumerate(clusters, 1):
        cluster_events = cluster['events']
        anchor_time = cluster['anchor_time']
        n_events = len(cluster_events)
        
        print(f"Cluster {idx} :")
        print(f"  - Anchor time : {anchor_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  - Nombre d'événements : {n_events}")
        print(f"  - Événements :")
        for _, event in cluster_events.head(5).iterrows():
            event_key = event.get('event_key', 'N/A')
            country = event.get('country', 'N/A')
            print(f"      • {country} - {event_key[:60]}")
        if n_events > 5:
            print(f"      ... et {n_events - 5} autres")
        print()
    
    if not clusters:
        print("❌ Aucun cluster détecté")
        sys.exit(1)
    
    # Sélectionner le cluster principal (premier ou celui avec CPI)
    main_cluster = clusters[0]
    for cluster in clusters:
        for _, event in cluster['events'].iterrows():
            event_key = str(event.get('event_key', '')).lower()
            if 'cpi' in event_key or 'consumer price' in event_key:
                main_cluster = cluster
                break
    
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 3...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 2 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 3 : DÉFINIR NOYAU DUR
# ============================================================================
print("=" * 80)
print("ÉTAPE 3 : DÉFINIR NOYAU DUR")
print("=" * 80)
print()

try:
    cluster_info = executor.etape3_definir_noyau_dur(
        main_cluster,
        support_threshold=0.60,
        years_lookback=5
    )
    
    print(f"✅ Noyau dur défini")
    print()
    print(f"Type détecté : {cluster_info.get('core_type', 'N/A')}")
    print(f"Événements core : {cluster_info.get('n_core_events', 0)}/{cluster_info.get('n_total_events', 0)}")
    print()
    
    core_events = cluster_info.get('core_events', [])
    support_scores = cluster_info.get('support_scores', {})
    
    print("Événements CORE :")
    print("-" * 80)
    for event_id in core_events:
        support = support_scores.get(event_id, 0.0)
        event_key = event_id.split('_')[0] if '_' in event_id else event_id
        print(f"  ✅ {event_key[:60]:<60} | Support: {support*100:.1f}%")
    
    print()
    print("Événements NON-CORE :")
    print("-" * 80)
    cluster_events = main_cluster['events']
    for _, event in cluster_events.iterrows():
        event_key = str(event.get('event_key', '')).lower().strip()
        country = event.get('country', '')
        importance = event.get('importance_n', 3)
        event_id_check = f"{event_key}_{country}_{importance}"
        if event_id_check not in core_events:
            support = support_scores.get(event_id_check, 0.0)
            print(f"  ❌ {event_key[:60]:<60} | Support: {support*100:.1f}% | Importance: {importance}")
    
    print()
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 4...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 3 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES
# ============================================================================
print("=" * 80)
print("ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES")
print("=" * 80)
print()

try:
    identical_clusters = executor.etape4_rechercher_clusters_identiques(
        cluster_info,
        jaccard_threshold=0.60,
        years_lookback=5
    )
    
    print(f"✅ Recherche terminée")
    print()
    print(f"Clusters identiques trouvés : {len(identical_clusters)}")
    print()
    
    if identical_clusters:
        print("Aperçu des clusters identiques :")
        print("-" * 80)
        for idx, cluster_hist in enumerate(identical_clusters[:5], 1):
            date_hist = cluster_hist.get('date', 'N/A')
            jaccard = cluster_hist.get('jaccard_similarity', 0.0)
            n_events = len(cluster_hist.get('cluster', {}).get('events', []))
            print(f"{idx}. Date: {date_hist} | Jaccard: {jaccard:.3f} | Événements: {n_events}")
        
        if len(identical_clusters) > 5:
            print(f"... et {len(identical_clusters) - 5} autres clusters")
    else:
        print("⚠️  AUCUN cluster identique trouvé !")
        print()
        print("Raisons possibles :")
        print("  - Seuil Jaccard (0.60) trop strict")
        print("  - Noyau dur trop spécifique (9 événements)")
        print("  - Jobless Claims inclus changent la composition")
    
    print()
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 5...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 4 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 5 : CALCULER TENDANCES
# ============================================================================
print("=" * 80)
print("ÉTAPE 5 : CALCULER TENDANCES")
print("=" * 80)
print()

try:
    trends_df = executor.etape5_calculer_tendances_impacts(identical_clusters)
    
    print(f"✅ Tendances calculées")
    print()
    
    if trends_df is not None and not trends_df.empty:
        print(f"Nombre de tendances calculées : {len(trends_df)}")
        print()
        print("Aperçu des tendances :")
        print("-" * 80)
        print(trends_df.head(10).to_string())
    else:
        print("⚠️  Aucune tendance calculée (pas de clusters identiques)")
    
    print()
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 6...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 5 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 6 : CALCULER IMPACTS BASE & AMPLIFICATIONS
# ============================================================================
print("=" * 80)
print("ÉTAPE 6 : CALCULER IMPACTS BASE & AMPLIFICATIONS")
print("=" * 80)
print()

try:
    impacts_df = executor.etape6_calculer_impacts_base_amplifications(
        identical_clusters,
        trends_df
    )
    
    print(f"✅ Impacts calculés")
    print()
    
    if impacts_df is not None and not impacts_df.empty:
        print(f"Nombre d'impacts calculés : {len(impacts_df)}")
        print()
        print("Aperçu des impacts :")
        print("-" * 80)
        print(impacts_df.head(10).to_string())
    else:
        print("⚠️  Aucun impact calculé")
    
    print()
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 7...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 6 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION
# ============================================================================
print("=" * 80)
print("ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION")
print("=" * 80)
print()

try:
    analysis_results = executor.etape7_analyser_relation_tendance_amplification(
        trends_df,
        impacts_df
    )
    
    print(f"✅ Analyse terminée")
    print()
    
    if analysis_results:
        correlations = analysis_results.get('correlations', {})
        results_df = analysis_results.get('results_df')
        
        print("Corrélations :")
        for key, value in correlations.items():
            print(f"  - {key} : {value:.3f}")
        
        if results_df is not None and not results_df.empty:
            print()
            print(f"Résultats DataFrame : {len(results_df)} lignes")
            print("Colonnes disponibles :", list(results_df.columns))
    else:
        print("⚠️  Aucun résultat d'analyse")
    
    print()
    print("─" * 80)
    input("⏸️  Appuyez sur ENTRÉE pour passer à l'ÉTAPE 8...")
    print()

except Exception as e:
    print(f"❌ Erreur Étape 7 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ÉTAPE 8 : APPLIQUER CLUSTER CIBLE
# ============================================================================
print("=" * 80)
print("ÉTAPE 8 : APPLIQUER CLUSTER CIBLE")
print("=" * 80)
print()

try:
    final_prediction = executor.etape8_appliquer_cluster_cible(
        cluster_info,
        analysis_results,
        identical_clusters
    )
    
    print(f"✅ Prédiction finale calculée")
    print()
    print("=" * 80)
    print("📊 RÉSULTAT FINAL")
    print("=" * 80)
    print()
    
    if final_prediction:
        print(f"Impact de base : {final_prediction.get('impact_base', 0):.2f} pips")
        print(f"Amplification prédite : {final_prediction.get('amplification_predite', 1.0):.3f}x")
        print(f"Prédiction finale : {final_prediction.get('prediction_finale', 0):.2f} pips")
        print(f"Méthode : {final_prediction.get('prediction_method', 'N/A')}")
        print(f"Pattern : {final_prediction.get('pattern_type', 'N/A')}")
        print(f"Exit target : {final_prediction.get('exit_target', 0):.2f} pips")
        
        pattern_info = final_prediction.get('pattern_info', {})
        if pattern_info.get('wave2_peak_pips_absolute', 0) > 0:
            print(f"Pattern impact : {pattern_info.get('wave2_peak_pips_absolute', 0):.2f} pips")
    
    print()
    print("=" * 80)
    print("✅ Pipeline terminé")
    print("=" * 80)

except Exception as e:
    print(f"❌ Erreur Étape 8 : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)




