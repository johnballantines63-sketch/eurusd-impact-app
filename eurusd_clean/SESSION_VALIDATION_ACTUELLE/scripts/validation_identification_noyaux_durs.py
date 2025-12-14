"""
Script de Validation : Identification des Noyaux Durs

Objectif : Valider que la méthode d'identification des noyaux durs est correcte
avant de recalculer les scores historiques.

Date : 2025-12-06
Référence : Problème 2025-05-29 (cluster 18:00 sélectionné au lieu de 14:30)

Tests :
1. Identification du cluster principal (score_qualite)
2. Identification du type de noyau dur (CPI, NFP, JOBLESS_PCE, etc.)
3. Vérification anchor_time (doit être événement US HIGH le plus important)
4. Comparaison avec mouvements réels observés
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime
import pytz
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

# Dates de test avec mouvements réels connus
TEST_DATES = [
    {
        'date': '2025-05-29',
        'expected_anchor_time': '14:30',
        'expected_core_type': 'JOBLESS_PCE',
        'expected_movement_start': '14:30',
        'description': 'Jobless Claims + PCE à 14:30 (mouvement réel à 14:30, pas 18:00)'
    },
    {
        'date': '2025-09-11',
        'expected_anchor_time': '14:30',
        'expected_core_type': 'CPI',
        'expected_movement_start': '14:30',
        'description': 'CPI US à 14:30 (mouvement réel à 14:30)'
    },
    {
        'date': '2025-08-01',
        'expected_anchor_time': '14:30',
        'expected_core_type': 'CPI',  # ou autre selon événements
        'expected_movement_start': '14:30',
        'description': 'Mouvement single wave fort à 14:30'
    },
    {
        'date': '2025-11-20',
        'expected_anchor_time': '14:30',
        'expected_core_type': 'CPI',  # ou autre selon événements
        'expected_movement_start': '14:30',
        'description': 'Mouvement double wave fort à 14:30'
    },
    {
        'date': '2025-06-23',
        'expected_anchor_time': '14:30',
        'expected_core_type': 'GENERIC',  # ou autre selon événements
        'expected_movement_start': '14:30',
        'description': 'Mouvement à 14:30'
    },
]

def get_movement_start_time(conn: duckdb.DuckDBPyConnection, date_str: str) -> Optional[str]:
    """
    Détecte l'heure de début du mouvement réel depuis les prix
    
    Args:
        conn: Connexion DuckDB
        date_str: Date au format YYYY-MM-DD
    
    Returns:
        Heure de début du mouvement (HH:MM) ou None
    """
    try:
        # Chercher mouvement dans fenêtre 14:00-20:00
        date_dt = pd.to_datetime(date_str)
        window_start = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=0)))
        window_end = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=20, minute=0)))
        
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE DATE(datetime) = '{date_str}'
          AND datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
          AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query).df()
        
        if df_prices.empty:
            return None
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        # Baseline : OPEN première bougie à 14:30
        baseline_time = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=30)))
        prices_at_1430 = df_prices[df_prices.index >= baseline_time]
        
        if prices_at_1430.empty:
            return None
        
        baseline_price = prices_at_1430.iloc[0]['open']
        
        # Chercher premier mouvement significatif (> 5 pips)
        for idx, row in prices_at_1430.iterrows():
            high_pips = (row['high'] - baseline_price) * 10000
            low_pips = (baseline_price - row['low']) * 10000
            max_move = max(high_pips, low_pips)
            
            if max_move >= 5.0:
                return idx.strftime('%H:%M')
        
        return None
    
    except Exception as e:
        print(f"   ⚠️ Erreur détection mouvement : {e}")
        return None

def validate_noyau_dur_identification(
    date_str: str,
    expected_anchor_time: str,
    expected_core_type: str,
    expected_movement_start: str,
    description: str
) -> Dict:
    """
    Valide l'identification du noyau dur pour une date
    
    Returns:
        Dict avec résultats de validation
    """
    print(f"\n{'='*100}")
    print(f"VALIDATION : {date_str}")
    print(f"{'='*100}")
    print(f"Description : {description}")
    print(f"Attendu : anchor_time={expected_anchor_time}, core_type={expected_core_type}, mouvement={expected_movement_start}")
    print()
    
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=True)
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    results = {
        'date': date_str,
        'success': False,
        'anchor_time_detected': None,
        'anchor_time_expected': expected_anchor_time,
        'anchor_time_match': False,
        'core_type_detected': None,
        'core_type_expected': expected_core_type,
        'core_type_match': False,
        'movement_start_detected': None,
        'movement_start_expected': expected_movement_start,
        'movement_start_match': False,
        'clusters_info': [],
        'errors': []
    }
    
    try:
        # Exécuter pipeline jusqu'à Étape 3
        result = executor.execute_complete_pipeline(
            date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.6,
            years_lookback=5,
            stop_at_etape=3  # S'arrêter après Étape 3
        )
        
        if not result or not result.get('success'):
            results['errors'].append("Pipeline échoué")
            return results
        
        # Extraire informations
        etape2_clusters = result.get('etape2_clusters', [])
        etape3_result = result.get('etape3_noyau_dur', {})
        main_cluster = result.get('main_cluster', {})
        
        # 1. Vérifier cluster principal sélectionné
        if main_cluster:
            anchor_time_detected = main_cluster.get('anchor_time')
            if anchor_time_detected:
                if hasattr(anchor_time_detected, 'strftime'):
                    anchor_time_str = anchor_time_detected.strftime('%H:%M')
                else:
                    anchor_time_str = str(anchor_time_detected)
                
                results['anchor_time_detected'] = anchor_time_str
                results['anchor_time_match'] = (anchor_time_str == expected_anchor_time)
        
        # 2. Vérifier type noyau dur
        core_type_detected = etape3_result.get('core_type', 'UNKNOWN')
        results['core_type_detected'] = core_type_detected
        results['core_type_match'] = (core_type_detected == expected_core_type)
        
        # 3. Détecter mouvement réel
        movement_start_detected = get_movement_start_time(conn, date_str)
        results['movement_start_detected'] = movement_start_detected
        results['movement_start_match'] = (movement_start_detected == expected_movement_start) if movement_start_detected else False
        
        # 4. Collecter infos sur tous les clusters
        for cluster in etape2_clusters:
            cluster_anchor = cluster.get('anchor_time')
            if hasattr(cluster_anchor, 'strftime'):
                cluster_anchor_str = cluster_anchor.strftime('%H:%M')
            else:
                cluster_anchor_str = str(cluster_anchor)
            
            cluster_events = cluster.get('events', pd.DataFrame())
            n_events = len(cluster_events) if not cluster_events.empty else 0
            
            # Calculer score qualité pour ce cluster
            score_qualite = 0.0
            n_events_with_score = 0
            scores_individuels = []
            
            if not cluster_events.empty:
                for _, event in cluster_events.iterrows():
                    empirical_score = event.get('empirical_score')
                    importance_n = event.get('importance_n')
                    
                    if pd.isna(empirical_score) or pd.isna(importance_n):
                        continue
                    
                    score_individuel = importance_n * empirical_score
                    scores_individuels.append(abs(score_individuel))
                    n_events_with_score += 1
                
                if n_events_with_score > 0:
                    score_qualite = sum(scores_individuels) / n_events_with_score
            
            results['clusters_info'].append({
                'anchor_time': cluster_anchor_str,
                'n_events': n_events,
                'score_qualite': score_qualite,
                'is_main': (cluster_anchor_str == results['anchor_time_detected'])
            })
        
        # 5. Évaluer succès global
        results['success'] = (
            results['anchor_time_match'] and
            results['core_type_match'] and
            results['movement_start_match']
        )
        
    except Exception as e:
        results['errors'].append(str(e))
        print(f"   ❌ Erreur : {e}")
    
    finally:
        conn.close()
    
    # Afficher résultats
    print(f"\n📊 RÉSULTATS :")
    print(f"   Anchor Time : {results['anchor_time_detected']} (attendu: {expected_anchor_time}) {'✅' if results['anchor_time_match'] else '❌'}")
    print(f"   Core Type   : {results['core_type_detected']} (attendu: {expected_core_type}) {'✅' if results['core_type_match'] else '❌'}")
    print(f"   Mouvement   : {results['movement_start_detected']} (attendu: {expected_movement_start}) {'✅' if results['movement_start_match'] else '❌'}")
    print(f"\n   Clusters détectés :")
    for cluster_info in results['clusters_info']:
        marker = "⭐" if cluster_info['is_main'] else "  "
        print(f"   {marker} {cluster_info['anchor_time']:5s} : {cluster_info['n_events']:2d} événements, score qualité: {cluster_info['score_qualite']:6.2f}")
    
    if results['success']:
        print(f"\n   ✅ VALIDATION RÉUSSIE")
    else:
        print(f"\n   ❌ VALIDATION ÉCHOUÉE")
        if results['errors']:
            print(f"   Erreurs : {', '.join(results['errors'])}")
    
    return results

def main():
    """Exécute la validation sur toutes les dates de test"""
    print("="*100)
    print("VALIDATION IDENTIFICATION NOYAUX DURS")
    print("="*100)
    print()
    print("Objectif : Vérifier que la méthode d'identification des noyaux durs est correcte")
    print("avant de recalculer les scores historiques.")
    print()
    
    all_results = []
    
    for test_case in TEST_DATES:
        result = validate_noyau_dur_identification(
            test_case['date'],
            test_case['expected_anchor_time'],
            test_case['expected_core_type'],
            test_case['expected_movement_start'],
            test_case['description']
        )
        all_results.append(result)
    
    # Résumé global
    print(f"\n{'='*100}")
    print("RÉSUMÉ GLOBAL")
    print(f"{'='*100}")
    print()
    
    n_success = sum(1 for r in all_results if r['success'])
    n_total = len(all_results)
    
    print(f"Dates validées : {n_success}/{n_total}")
    print()
    
    print("Détails par critère :")
    anchor_matches = sum(1 for r in all_results if r['anchor_time_match'])
    core_matches = sum(1 for r in all_results if r['core_type_match'])
    movement_matches = sum(1 for r in all_results if r['movement_start_match'])
    
    print(f"   Anchor Time correct : {anchor_matches}/{n_total}")
    print(f"   Core Type correct   : {core_matches}/{n_total}")
    print(f"   Mouvement correct   : {movement_matches}/{n_total}")
    print()
    
    # Dates avec problèmes
    failed_dates = [r['date'] for r in all_results if not r['success']]
    if failed_dates:
        print(f"⚠️  Dates avec problèmes : {', '.join(failed_dates)}")
        print()
        print("Analyse détaillée des problèmes :")
        for result in all_results:
            if not result['success']:
                print(f"\n   {result['date']} :")
                if not result['anchor_time_match']:
                    print(f"      - Anchor Time : {result['anchor_time_detected']} ≠ {result['anchor_time_expected']}")
                if not result['core_type_match']:
                    print(f"      - Core Type : {result['core_type_detected']} ≠ {result['core_type_expected']}")
                if not result['movement_start_match']:
                    print(f"      - Mouvement : {result['movement_start_detected']} ≠ {result['movement_start_expected']}")
    else:
        print("✅ Toutes les dates sont correctement identifiées")
    
    # Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'validation_noyaux_durs.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df_results = pd.DataFrame(all_results)
    df_results.to_csv(output_file, index=False)
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    
    # Conclusion
    print(f"\n{'='*100}")
    if n_success == n_total:
        print("✅ VALIDATION COMPLÈTE : La méthode d'identification est correcte")
        print("   → On peut procéder au recalcul des scores historiques")
    else:
        print("❌ VALIDATION INCOMPLÈTE : Des corrections sont nécessaires")
        print("   → Corriger la méthode avant de recalculer les scores")
    print(f"{'='*100}")

if __name__ == '__main__':
    main()




