#!/usr/bin/env python3
"""
Classification Dates - Stratégie Hybride
=========================================

Objectif : Classifier chaque date selon les cas de la stratégie hybride
"""

import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

# Dates à tester
TEST_DATES = [
    '2025-09-11',  # Clusters multiples (14:30 + 14:45)
    '2025-11-20',  # Un seul cluster (14:30)
    '2025-10-10',  # Clusters multiples
    '2025-06-23',  # Clusters multiples
    '2025-05-29',  # Clusters multiples
    '2025-11-26',  # Clusters multiples
]

print('='*100)
print('CLASSIFICATION DATES - STRATÉGIE HYBRIDE')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

results = []

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 DATE : {date_str}')
    print('='*100)
    print()
    
    try:
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur: {result.get("error")}')
            continue
        
        final_pred = result.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        pattern_confidence = pattern_info.get('confidence', 0.0)
        
        print(f'📊 INFORMATIONS')
        print('-'*100)
        print(f'Pattern : {pattern_type}')
        print(f'Confiance pattern : {pattern_confidence:.1f}%')
        print(f'Anchor time : {anchor_time}')
        print()
        
        # Charger tous les événements de la date
        all_events = executor.etape1_charger_evenements(date_str)
        clusters = executor.etape2_detecter_clusters(all_events, window_minutes=30)
        
        print(f'📊 CLUSTERS DÉTECTÉS')
        print('-'*100)
        print(f'Nombre de clusters : {len(clusters)}')
        print()
        
        # Analyser clusters
        clusters_with_us = []
        cluster_principal = None
        cluster2 = None
        
        for idx, cluster_info in enumerate(clusters, 1):
            cluster_anchor = cluster_info.get('anchor_time')
            cluster_events = cluster_info.get('events', pd.DataFrame())
            
            # Calculer métriques
            if not cluster_events.empty:
                n_us = len(cluster_events[cluster_events['country'] == 'US'])
                n_high = len(cluster_events[cluster_events['importance_n'] == 3])
                if 'empirical_score' in cluster_events.columns:
                    total_score = cluster_events['empirical_score'].sum()
                else:
                    total_score = 0.0
            else:
                n_us = 0
                n_high = 0
                total_score = 0.0
            
            print(f'Cluster {idx}:')
            print(f'  Anchor time : {cluster_anchor.strftime("%H:%M")}')
            print(f'  Événements : {len(cluster_events)}')
            print(f'  Événements US : {n_us}')
            print(f'  Événements HIGH : {n_high}')
            print(f'  Score total : {total_score:.1f}')
            
            # Identifier cluster principal (US avec score max)
            if n_us > 0:
                clusters_with_us.append({
                    'index': idx,
                    'anchor_time': cluster_anchor,
                    'n_us': n_us,
                    'n_high': n_high,
                    'total_score': total_score,
                    'cluster': cluster_info
                })
            
            print()
        
        # ⚠️ CORRECTION : Utiliser anchor_time corrigé du pipeline (cluster principal US)
        # au lieu de l'anchor_time du cluster détecté
        cluster_principal_time = anchor_time  # Utiliser anchor_time corrigé
        
        # Identifier cluster principal dans la liste (pour affichage)
        if clusters_with_us:
            cluster_principal = max(clusters_with_us, key=lambda x: (x['n_us'], x['total_score']))
            print(f'✅ Cluster principal identifié : Cluster {cluster_principal["index"]} ({cluster_principal["anchor_time"].strftime("%H:%M")})')
            print(f'   ⚠️ Anchor time corrigé utilisé : {cluster_principal_time.strftime("%H:%M")} (cluster principal US)')
            print()
        
        # Identifier cluster 2 (après anchor_time corrigé)
        clusters_after = [c for c in clusters if c['anchor_time'] > cluster_principal_time]
        if clusters_after:
            cluster2 = min(clusters_after, key=lambda x: x['anchor_time'])
            ΔT = (cluster2['anchor_time'] - cluster_principal_time).total_seconds() / 60.0
            print(f'✅ Cluster 2 identifié : {cluster2["anchor_time"].strftime("%H:%M")} (ΔT = {ΔT:.0f} min depuis anchor corrigé)')
            print()
        
        # Détecter pattern réel
        pattern_detected = False
        pattern_confidence_real = 0.0
        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))
            from double_wave_detector_rev12 import detect_for_date_duckdb_rev12
            
            pattern_date = anchor_time
            if pattern_date.tzinfo is not None:
                pattern_date = pattern_date.replace(tzinfo=None)
            
            pattern_result = detect_for_date_duckdb_rev12(
                db_path=str(DB_PATH),
                table='prices_finnhub_m1',
                date=pattern_date,
                tz='Europe/Zurich',
                baseline_mode='prev_close_14_29',
                minutes_after_hint=180,
                trading_window=True,
                debug=False,
                event_time=anchor_time
            )
            
            if pattern_result and pattern_result.get('double_wave', False):
                pattern_detected = True
                pattern_confidence_real = pattern_result.get('confidence', 0.0)
        except Exception as e:
            pass
        
        # CLASSIFICATION
        print('='*100)
        print('🎯 CLASSIFICATION STRATÉGIE HYBRIDE')
        print('='*100)
        print()
        
        case = None
        case_description = ""
        
        # CAS 1 : Clusters multiples avec délai ~15 min → Alternative 1
        if len(clusters) > 1 and cluster2:
            ΔT = (cluster2['anchor_time'] - cluster_principal_time).total_seconds() / 60.0
            if 10 <= ΔT <= 20:  # Délai proche de 15 min (±5 min)
                case = "CAS_1_ALTERNATIVE_1"
                case_description = f"Clusters multiples avec délai standard (ΔT = {ΔT:.0f} min) → Alternative 1 (basée sur événements)"
                print(f'✅ {case_description}')
            else:
                # Clusters multiples mais délai non standard
                case = "CAS_1B_CLUSTERS_MULTIPLES_NON_STANDARD"
                case_description = f"Clusters multiples mais délai non standard (ΔT = {ΔT:.0f} min) → Nécessite adaptation"
                print(f'⚠️ {case_description}')
        
        # CAS 2 : Pattern détecté avec confiance élevée → Alternative 3
        if case is None and pattern_detected and pattern_confidence_real > 80:
            case = "CAS_2_ALTERNATIVE_3"
            case_description = f"Pattern détecté avec confiance élevée ({pattern_confidence_real:.1f}%) → Alternative 3 (basée sur pattern)"
            print(f'✅ {case_description}')
        
        # CAS 3 : Sinon → Alternative 5 (timings standard)
        if case is None:
            if pattern_detected:
                case = "CAS_3_ALTERNATIVE_5_PATTERN_FAIBLE"
                case_description = f"Pattern détecté mais confiance faible ({pattern_confidence_real:.1f}%) → Alternative 5 (timings standard)"
            else:
                case = "CAS_3_ALTERNATIVE_5_PAS_PATTERN"
                case_description = f"Pas de pattern détecté → Alternative 5 (timings standard)"
            print(f'ℹ️ {case_description}')
        
        print()
        
        results.append({
            'date': date_str,
            'pattern_type': pattern_type,
            'pattern_confidence': pattern_confidence,
            'pattern_detected': pattern_detected,
            'pattern_confidence_real': pattern_confidence_real,
            'n_clusters': len(clusters),
            'cluster_principal_time': cluster_principal_time.strftime('%H:%M'),
            'cluster2_time': cluster2['anchor_time'].strftime('%H:%M') if cluster2 else None,
            'delta_t_minutes': (cluster2['anchor_time'] - cluster_principal_time).total_seconds() / 60.0 if cluster2 else None,
            'case': case,
            'case_description': case_description
        })
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

# Résumé
print('='*100)
print('📊 RÉSUMÉ CLASSIFICATION')
print('='*100)
print()

df_results = pd.DataFrame(results)

if not df_results.empty:
    print('Classification par date:')
    print('-'*100)
    for _, row in df_results.iterrows():
        print(f"\n{row['date']}:")
        print(f"  Pattern : {row['pattern_type']}")
        print(f"  Clusters : {row['n_clusters']}")
        if row['cluster_principal_time']:
            print(f"  Cluster principal : {row['cluster_principal_time']}")
        if row['cluster2_time']:
            print(f"  Cluster 2 : {row['cluster2_time']} (ΔT = {row['delta_t_minutes']:.0f} min)")
        print(f"  Pattern détecté : {row['pattern_detected']} (confiance: {row['pattern_confidence_real']:.1f}%)")
        print(f"  → {row['case_description']}")
    
    print()
    print('='*100)
    print('📊 STATISTIQUES PAR CAS')
    print('='*100)
    print()
    
    case_counts = df_results['case'].value_counts()
    for case, count in case_counts.items():
        case_name = case.replace('CAS_', '').replace('_', ' ').title()
        print(f"{case_name} : {count} date(s)")
        dates_in_case = df_results[df_results['case'] == case]['date'].tolist()
        print(f"  Dates : {', '.join(dates_in_case)}")
        print()

# Sauvegarder résultats
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'classification_dates_hybrid_strategy.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df_results.to_csv(output_file, index=False)
print(f'✅ Résultats sauvegardés : {output_file}')

print('='*100)
print('✅ CLASSIFICATION TERMINÉE')
print('='*100)

