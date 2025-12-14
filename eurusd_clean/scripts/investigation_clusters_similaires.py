#!/usr/bin/env python3
"""
INVESTIGATION MÉTHODIQUE - RECHERCHE CLUSTERS SIMILAIRES
=========================================================

Objectif : Identifier pourquoi les clusters similaires n'ont pas été trouvés
           dans Session 130, en testant différentes méthodes de recherche.

Hypothèses à tester :
1. Normalisation event_key incomplète (variantes MoM/YoY/QoQ non gérées)
2. Fenêtre de clustering incorrecte
3. Seuil Jaccard trop strict
4. Période de recherche trop courte
5. Structure DB mal comprise
6. Algorithme de clustering défaillant

Auteur : André Valentin avec Claude
Date : 17 novembre 2025
"""

import json
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from collections import Counter
import sys

# Import utils Session 127 (strip_variant_suffix)
sys.path.insert(0, str(Path(__file__).parent / 'session127'))
try:
    from utils_mapping_variants import strip_variant_suffix
    STRIP_VARIANT_AVAILABLE = True
except ImportError:
    print("⚠️  utils_mapping_variants.py non trouvé, strip_variant_suffix() non disponible")
    STRIP_VARIANT_AVAILABLE = False
    def strip_variant_suffix(x): return x

# Chemins
DB_PATH = "data/warehouse.duckdb"
REFERENCE_COMPOSITION_FILE = Path(__file__).parent / "investigation_clusters" / "cluster_reference_composition.json"
OUTPUT_DIR = Path(__file__).parent / "investigation_clusters"
OUTPUT_DIR.mkdir(exist_ok=True)

# Cas référence à analyser
REFERENCE_DATE = "2025-09-11"

# Périodes de recherche à tester
SEARCH_PERIODS = [
    ("2023-01-01", "2025-11-07", "3 ans (Session 130)"),
    ("2020-01-01", "2025-11-07", "6 ans"),
    ("2015-01-01", "2025-11-07", "10 ans"),
]

# Seuils Jaccard à tester
JACCARD_THRESHOLDS = [0.8, 0.7, 0.6, 0.5]

# Fenêtres clustering à tester
CLUSTER_WINDOWS = [5, 10, 15, 30]  # minutes


def normalize_event_key_basic(event_key: str) -> str:
    """Normalisation basique (Session 130)"""
    return event_key.lower().strip()


def normalize_event_key_with_variants(event_key: str) -> str:
    """Normalisation avec gestion variantes (Session 127)"""
    normalized = event_key.lower().strip()
    # Strip suffixe variante pour comparer base
    base = strip_variant_suffix(normalized)
    return base


def jaccard_similarity(set1: Set, set2: Set) -> float:
    """Calcule similarité Jaccard"""
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def load_reference_composition() -> Dict:
    """Charge la composition du cluster de référence depuis le fichier JSON"""
    if not REFERENCE_COMPOSITION_FILE.exists():
        raise FileNotFoundError(f"Fichier composition référence introuvable : {REFERENCE_COMPOSITION_FILE}")
    
    with open(REFERENCE_COMPOSITION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data['reference_date'] != REFERENCE_DATE:
        raise ValueError(f"Date référence attendue {REFERENCE_DATE}, trouvée {data['reference_date']}")
    
    return data


def analyze_reference_composition(composition_data: Dict) -> Dict:
    """Analyse détaillée de la composition du cluster de référence"""
    event_keys_raw = composition_data['event_keys_raw']
    
    # Composition normalisée
    event_keys_normalized_basic = [normalize_event_key_basic(k) for k in event_keys_raw]
    event_keys_normalized_variants = [normalize_event_key_with_variants(k) for k in event_keys_raw]
    
    # Comptage
    counter_raw = Counter(event_keys_raw)
    counter_basic = Counter(event_keys_normalized_basic)
    counter_variants = Counter(event_keys_normalized_variants)
    
    # Doublons
    duplicates_raw = {k: v for k, v in counter_raw.items() if v > 1}
    duplicates_basic = {k: v for k, v in counter_basic.items() if v > 1}
    duplicates_variants = {k: v for k, v in counter_variants.items() if v > 1}
    
    # Variantes détectées
    variants_detected = []
    for key in event_keys_raw:
        normalized = normalize_event_key_basic(key)
        base = normalize_event_key_with_variants(key)
        if normalized != base:
            variants_detected.append({
                'original': key,
                'normalized_basic': normalized,
                'base_variant': base
            })
    
    return {
        'n_events_total': len(event_keys_raw),
        'n_events_unique_raw': len(counter_raw),
        'n_events_unique_basic': len(counter_basic),
        'n_events_unique_variants': len(counter_variants),
        'duplicates_raw': duplicates_raw,
        'duplicates_basic': duplicates_basic,
        'duplicates_variants': duplicates_variants,
        'variants_detected': variants_detected,
        'event_keys_raw': event_keys_raw,
        'event_keys_normalized_basic': list(set(event_keys_normalized_basic)),
        'event_keys_normalized_variants': list(set(event_keys_normalized_variants)),
        'composition_basic': set(event_keys_normalized_basic),
        'composition_variants': set(event_keys_normalized_variants)
    }


def verify_db_structure(conn) -> Dict:
    """Vérifie la structure de la table events"""
    # Vérifier table existe
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    
    if 'events' not in table_names:
        return {'error': 'Table events non trouvée', 'tables': table_names}
    
    # Vérifier colonnes
    columns = conn.execute("DESCRIBE events").fetchall()
    column_names = [c[0] for c in columns]
    
    # Vérifier distribution importance_n
    importance_dist = conn.execute("""
        SELECT importance_n, COUNT(*) as count
        FROM events
        GROUP BY importance_n
        ORDER BY importance_n
    """).fetchall()
    
    # Vérifier distribution event_key (échantillon)
    sample_keys = conn.execute("""
        SELECT DISTINCT event_key
        FROM events
        LIMIT 20
    """).fetchall()
    
    # Vérifier événements 11 septembre
    events_11sept = conn.execute("""
        SELECT COUNT(*) as count
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
        AND importance_n >= 2
    """).fetchone()
    
    return {
        'table_exists': True,
        'columns': column_names,
        'importance_distribution': dict(importance_dist),
        'sample_event_keys': [k[0] for k in sample_keys],
        'events_11sept_count': events_11sept[0] if events_11sept else 0
    }


def find_clusters_specific_times(df_all: pd.DataFrame, ref_composition: Set[str],
                                 normalize_func=normalize_event_key_basic,
                                 jaccard_threshold: float = 0.8,
                                 include_current_account: bool = True) -> List[Dict]:
    """
    Recherche clusters similaires avec fenêtres temporelles spécifiques :
    - Événements US à 14h30 (heure Berne) - fenêtre ±5 min
    - Current account à 14h45 (heure Berne) - fenêtre ±5 min (optionnel)
    
    Si include_current_account=True : cherche dates avec US 14h30 ET current account 14h45
    Si include_current_account=False : cherche dates avec uniquement US 14h30
    
    Args:
        include_current_account: Si True, exige current account à 14h45. Si False, cherche uniquement US 14h30.
    """
    import pytz
    
    tz_berne = pytz.timezone('Europe/Zurich')
    clusters = []
    
    # Convertir ts_utc en heure Berne pour filtrage
    df_all = df_all.copy()
    df_all['ts_berne'] = pd.to_datetime(df_all['ts_utc']).dt.tz_convert(tz_berne)
    df_all['date'] = df_all['ts_berne'].dt.date
    df_all['hour'] = df_all['ts_berne'].dt.hour
    df_all['minute'] = df_all['ts_berne'].dt.minute
    
    # Grouper par date
    for date, date_group in df_all.groupby('date'):
        # Fenêtre 1 : Événements US à 14h30 (±5 min)
        us_1430_window = date_group[
            (date_group['country'] == 'US') &
            (date_group['hour'] == 14) &
            (date_group['minute'] >= 25) &
            (date_group['minute'] <= 35)
        ]
        
        # Fenêtre 2 : Current account à 14h45 (±5 min) - optionnel
        ca_1445_window = date_group[
            (date_group['event_key'].str.lower().str.contains('current account', na=False)) &
            (date_group['hour'] == 14) &
            (date_group['minute'] >= 40) &
            (date_group['minute'] <= 50)
        ]
        
        # Condition : US 14h30 obligatoire, current account selon paramètre
        if len(us_1430_window) > 0:
            if include_current_account:
                # Exiger current account
                if len(ca_1445_window) == 0:
                    continue
                # Combiner les deux fenêtres
                cluster_events = pd.concat([us_1430_window, ca_1445_window])
            else:
                # Uniquement US 14h30
                cluster_events = us_1430_window
            
            # Normaliser composition
            cluster_composition = set(
                normalize_func(k) for k in cluster_events['event_key'].unique()
            )
            
            # Calculer similarité
            similarity = jaccard_similarity(ref_composition, cluster_composition)
            
            if similarity >= jaccard_threshold:
                clusters.append({
                    'date': str(date),
                    'cluster_time': cluster_events['ts_berne'].min().isoformat(),
                    'similarity': similarity,
                    'n_events': len(cluster_events),
                    'n_us_1430': len(us_1430_window),
                    'n_ca_1445': len(ca_1445_window) if include_current_account else 0,
                    'has_current_account': len(ca_1445_window) > 0,
                    'composition': sorted(list(cluster_composition)),
                    'event_keys': cluster_events['event_key'].tolist(),
                    'countries': cluster_events['country'].unique().tolist()
                })
    
    return clusters


def find_clusters_improved(df_all: pd.DataFrame, ref_composition: Set[str], 
                           cluster_window_minutes: int = 5,
                           normalize_func=normalize_event_key_basic,
                           jaccard_threshold: float = 0.8,
                           progress_callback=None) -> List[Dict]:
    """
    Recherche clusters similaires avec méthode améliorée.
    
    Améliorations vs Session 130 :
    1. Normalisation avec gestion variantes
    2. Fenêtre clustering configurable
    3. Algorithme clustering amélioré (pas de "used" qui manque clusters)
    
    Args:
        df_all: DataFrame avec TOUS événements déjà chargés
        progress_callback: Fonction appelée pour progression (current, total)
    """
    if len(df_all) == 0:
        return []
    
    # Algorithme clustering optimisé - Version efficace
    # Au lieu d'itérer sur chaque événement, on groupe par fenêtres temporelles
    clusters = []
    
    # Trier et réinitialiser index
    df_all = df_all.sort_values('ts_utc').reset_index(drop=True)
    total_rows = len(df_all)
    
    if total_rows == 0:
        return []
    
    # Convertir en numpy array pour accès rapide
    ts_values = df_all['ts_utc'].values
    event_keys = df_all['event_key'].values
    
    # Créer un dictionnaire pour stocker les clusters uniques
    # Clé : (start_time, end_time) arrondi à la minute
    processed_clusters = {}
    
    # Itérer sur chaque événement comme point central de cluster
    print(f"      Analyse de {total_rows:,} événements...", end="", flush=True)
    
    for i in range(total_rows):
        if progress_callback and i % 1000 == 0:
            progress_callback(i, total_rows)
        
        cluster_time = ts_values[i]
        cluster_start = cluster_time - timedelta(minutes=cluster_window_minutes)
        cluster_end = cluster_time + timedelta(minutes=cluster_window_minutes)
        
        # Clé pour dédupliquer (arrondi à la minute pour éviter doublons)
        cluster_key = (
            cluster_start.replace(second=0, microsecond=0),
            cluster_end.replace(second=0, microsecond=0)
        )
        
        # Si cluster déjà traité, skip
        if cluster_key in processed_clusters:
            continue
        
        # Trouver TOUS événements dans cette fenêtre (utiliser numpy pour vitesse)
        # Utiliser searchsorted pour trouver les indices rapidement
        # Convertir datetime en timestamp pour searchsorted
        cluster_start_ts = pd.Timestamp(cluster_start).value
        cluster_end_ts = pd.Timestamp(cluster_end).value
        ts_values_ts = pd.Series(ts_values).astype('int64').values
        
        start_idx = np.searchsorted(ts_values_ts, cluster_start_ts, side='left')
        end_idx = np.searchsorted(ts_values_ts, cluster_end_ts, side='right')
        
        if end_idx - start_idx < 2:  # Minimum 2 événements
            continue
        
        # Extraire les event_keys dans cette fenêtre
        cluster_event_keys = event_keys[start_idx:end_idx]
        
        # Normaliser composition
        cluster_composition = set(
            normalize_func(k) for k in cluster_event_keys
        )
        
        # Calculer similarité
        similarity = jaccard_similarity(ref_composition, cluster_composition)
        
        # DEBUG : Afficher les premiers clusters avec similarité > 0 pour comprendre
        if similarity > 0 and len(processed_clusters) < 3:
            print(f"\n        DEBUG Cluster {len(processed_clusters)+1}:")
            print(f"          Date: {cluster_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"          Similarité: {similarity:.3f} (seuil: {jaccard_threshold:.1f})")
            print(f"          Composition ref: {sorted(list(ref_composition))[:5]}...")
            print(f"          Composition cluster: {sorted(list(cluster_composition))[:5]}...")
            print(f"          Intersection: {len(ref_composition & cluster_composition)}")
            print(f"          Union: {len(ref_composition | cluster_composition)}")
        
        if similarity >= jaccard_threshold:
            cluster_data = {
                'date': cluster_time.strftime("%Y-%m-%d"),
                'cluster_time': cluster_time.isoformat(),
                'similarity': similarity,
                'n_events': end_idx - start_idx,
                'composition': sorted(list(cluster_composition)),
                'event_keys': cluster_event_keys.tolist(),
                'countries': df_all.iloc[start_idx:end_idx]['country'].unique().tolist()
            }
            
            # Garder meilleur cluster pour cette fenêtre
            if cluster_key not in processed_clusters or similarity > processed_clusters[cluster_key]['similarity']:
                processed_clusters[cluster_key] = cluster_data
    
    print(f" ✅ {len(processed_clusters):,} clusters uniques trouvés")
    
    clusters = list(processed_clusters.values())
    
    # Dédupliquer clusters (même cluster_time peut apparaître plusieurs fois)
    # Garder celui avec meilleure similarité
    clusters_dedup = {}
    for cluster in clusters:
        key = cluster['cluster_time']
        if key not in clusters_dedup or cluster['similarity'] > clusters_dedup[key]['similarity']:
            clusters_dedup[key] = cluster
    
    return list(clusters_dedup.values())


def test_search_methods(conn, ref_composition_basic: Set, ref_composition_variants: Set) -> Dict:
    """Teste différentes méthodes de recherche"""
    results = {}
    
    total_combinations = len(SEARCH_PERIODS) * len(JACCARD_THRESHOLDS)
    current_combination = 0
    
    print(f"\n   Total combinaisons à tester : {total_combinations}")
    print(f"   Progression : ", end="", flush=True)
    
    for period_name, (start, end, desc) in enumerate(SEARCH_PERIODS):
        period_key = f"period_{period_name}"
        results[period_key] = {
            'description': desc,
            'start': start,
            'end': end,
            'methods': {}
        }
        
        # Charger données UNE FOIS pour cette période
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        
        print(f"\n   📅 Période {desc} ({start} → {end})")
        print(f"      Chargement données...", end="", flush=True)
        
        query = """
        SELECT 
            ts_utc,
            event_key,
            country,
            importance_n
        FROM events
        WHERE ts_utc >= ? AND ts_utc < ?
          AND importance_n >= 2
        ORDER BY ts_utc
        """
        
        df_period = conn.execute(query, [start_dt, end_dt]).df()
        df_period['ts_utc'] = pd.to_datetime(df_period['ts_utc'])
        
        print(f" ✅ {len(df_period):,} événements chargés")
        
        for threshold in JACCARD_THRESHOLDS:
            current_combination += 1
            progress_pct = (current_combination / total_combinations) * 100
            
            print(f"      [{current_combination}/{total_combinations}] "
                  f"Jaccard {threshold:.1f} "
                  f"({progress_pct:.1f}%)...", end="", flush=True)
            
            # Méthode 1 : Recherche avec US 14h30 + Current Account 14h45 (composition complète)
            clusters_basic_full = find_clusters_specific_times(
                df_period, ref_composition_basic,
                normalize_func=normalize_event_key_basic,
                jaccard_threshold=threshold,
                include_current_account=True
            )
            
            clusters_variants_full = find_clusters_specific_times(
                df_period, ref_composition_variants,
                normalize_func=normalize_event_key_with_variants,
                jaccard_threshold=threshold,
                include_current_account=True
            )
            
            # Méthode 2 : Recherche avec UNIQUEMENT US 14h30 (sans current account)
            clusters_basic_us_only = find_clusters_specific_times(
                df_period, ref_composition_basic,
                normalize_func=normalize_event_key_basic,
                jaccard_threshold=threshold,
                include_current_account=False
            )
            
            clusters_variants_us_only = find_clusters_specific_times(
                df_period, ref_composition_variants,
                normalize_func=normalize_event_key_with_variants,
                jaccard_threshold=threshold,
                include_current_account=False
            )
            
            print(f" ✅ Full (US+CA): Basic={len(clusters_basic_full)}, Variants={len(clusters_variants_full)}")
            print(f"      US only: Basic={len(clusters_basic_us_only)}, Variants={len(clusters_variants_us_only)}")
            
            method_key = f"jaccard_{threshold}"
            results[period_key]['methods'][method_key] = {
                'jaccard_threshold': threshold,
                'clusters_basic_full': len(clusters_basic_full),
                'clusters_variants_full': len(clusters_variants_full),
                'clusters_basic_us_only': len(clusters_basic_us_only),
                'clusters_variants_us_only': len(clusters_variants_us_only),
                'clusters_basic_full_details': clusters_basic_full[:10],  # Top 10
                'clusters_variants_full_details': clusters_variants_full[:10],
                'clusters_basic_us_only_details': clusters_basic_us_only[:10],
                'clusters_variants_us_only_details': clusters_variants_us_only[:10]
            }
    
    print(f"\n   ✅ Toutes combinaisons testées !")
    return results


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("INVESTIGATION MÉTHODIQUE - RECHERCHE CLUSTERS SIMILAIRES")
    print("=" * 80)
    
    # ÉTAPE 1 : Charger composition référence
    print(f"\n📂 ÉTAPE 1 : Chargement composition cluster référence")
    print(f"   Fichier : {REFERENCE_COMPOSITION_FILE}")
    
    try:
        composition_data = load_reference_composition()
        print(f"✅ Composition référence chargée : {composition_data['reference_date']}")
        print(f"   Critères :")
        print(f"     - Événements US à 14h30 (heure Berne)")
        print(f"     - Current account à 14h45 (heure Berne)")
        print(f"   Total événements : {len(composition_data['event_keys_raw'])}")
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return 1
    
    # ÉTAPE 2 : Analyser composition référence
    print(f"\n📊 ÉTAPE 2 : Analyse composition référence")
    composition_analysis = analyze_reference_composition(composition_data)
    
    print(f"\n   Composition brute :")
    print(f"      Total événements : {composition_analysis['n_events_total']}")
    print(f"      Événements uniques (raw) : {composition_analysis['n_events_unique_raw']}")
    print(f"      Événements uniques (basic) : {composition_analysis['n_events_unique_basic']}")
    print(f"      Événements uniques (variants) : {composition_analysis['n_events_unique_variants']}")
    
    if composition_analysis['duplicates_raw']:
        print(f"\n   ⚠️  Doublons détectés (raw) : {len(composition_analysis['duplicates_raw'])}")
        for key, count in list(composition_analysis['duplicates_raw'].items())[:5]:
            print(f"      - {key} : {count}x")
    
    if composition_analysis['variants_detected']:
        print(f"\n   ✅ Variantes détectées : {len(composition_analysis['variants_detected'])}")
        for var in composition_analysis['variants_detected'][:5]:
            print(f"      - {var['original']} → {var['base_variant']}")
    
    # ÉTAPE 3 : Vérifier structure DB
    print(f"\n🔍 ÉTAPE 3 : Vérification structure DB")
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    db_structure = verify_db_structure(conn)
    
    if 'error' in db_structure:
        print(f"❌ {db_structure['error']}")
        conn.close()
        return 1
    
    print(f"✅ Table events existe")
    print(f"   Colonnes : {len(db_structure['columns'])}")
    print(f"   Distribution importance_n : {db_structure['importance_distribution']}")
    print(f"   Événements 11 septembre : {db_structure['events_11sept_count']}")
    
    # ÉTAPE 4 : Tester méthodes de recherche
    print(f"\n🔬 ÉTAPE 4 : Tests méthodes de recherche")
    print(f"   Périodes : {len(SEARCH_PERIODS)}")
    print(f"   Seuils Jaccard : {len(JACCARD_THRESHOLDS)}")
    print(f"   Total combinaisons : {len(SEARCH_PERIODS) * len(JACCARD_THRESHOLDS)}")
    print(f"   Méthodes testées :")
    print(f"     - Composition complète (US 14h30 + Current Account 14h45)")
    print(f"     - Uniquement US 14h30 (sans Current Account)")
    print(f"\n   ⏳ Recherche en cours... (peut prendre plusieurs minutes)")
    
    search_results = test_search_methods(
        conn,
        composition_analysis['composition_basic'],
        composition_analysis['composition_variants']
    )
    
    conn.close()
    
    # ÉTAPE 5 : Analyser résultats
    print(f"\n📈 ÉTAPE 5 : Analyse résultats")
    
    # Trouver meilleures combinaisons
    best_results_full = []  # Composition complète (US + CA)
    best_results_us_only = []  # Uniquement US
    
    for period_key, period_data in search_results.items():
        for method_key, method_data in period_data['methods'].items():
            # Composition complète
            if method_data['clusters_variants_full'] > 0:
                best_results_full.append({
                    'period': period_data['description'],
                    'threshold': method_data['jaccard_threshold'],
                    'clusters_basic': method_data['clusters_basic_full'],
                    'clusters_variants': method_data['clusters_variants_full'],
                    'gain': method_data['clusters_variants_full'] - method_data['clusters_basic_full']
                })
            
            # Uniquement US
            if method_data['clusters_variants_us_only'] > 0:
                best_results_us_only.append({
                    'period': period_data['description'],
                    'threshold': method_data['jaccard_threshold'],
                    'clusters_basic': method_data['clusters_basic_us_only'],
                    'clusters_variants': method_data['clusters_variants_us_only'],
                    'gain': method_data['clusters_variants_us_only'] - method_data['clusters_basic_us_only']
                })
    
    # Trier par nombre clusters trouvés
    best_results_full.sort(key=lambda x: -x['clusters_variants'])
    best_results_us_only.sort(key=lambda x: -x['clusters_variants'])
    
    print(f"\n   📊 COMPOSITION COMPLÈTE (US 14h30 + Current Account 14h45)")
    print(f"   {'Période':<20s} | {'Jaccard':<8s} | {'Basic':<8s} | {'Variants':<10s} | {'Gain':<8s}")
    print(f"   {'-'*20} | {'-'*8} | {'-'*8} | {'-'*10} | {'-'*8}")
    
    if len(best_results_full) > 0:
        for result in best_results_full[:10]:
            print(f"   {result['period']:<20s} | "
                  f"{result['threshold']:>6.1f} | {result['clusters_basic']:>6d} | "
                  f"{result['clusters_variants']:>8d} | {result['gain']:>+6d}")
    else:
        print(f"   ❌ Aucun cluster trouvé avec composition complète")
    
    print(f"\n   📊 UNIQUEMENT US 14h30 (sans Current Account)")
    print(f"   {'Période':<20s} | {'Jaccard':<8s} | {'Basic':<8s} | {'Variants':<10s} | {'Gain':<8s}")
    print(f"   {'-'*20} | {'-'*8} | {'-'*8} | {'-'*10} | {'-'*8}")
    
    if len(best_results_us_only) > 0:
        for result in best_results_us_only[:10]:
            print(f"   {result['period']:<20s} | "
                  f"{result['threshold']:>6.1f} | {result['clusters_basic']:>6d} | "
                  f"{result['clusters_variants']:>8d} | {result['gain']:>+6d}")
    else:
        print(f"   ❌ Aucun cluster trouvé avec uniquement US")
    
    # ÉTAPE 6 : Sauvegarder résultats
    print(f"\n💾 ÉTAPE 6 : Sauvegarde résultats")
    
    output_data = {
        'reference_composition': {
            'date': REFERENCE_DATE,
            'composition_analysis': composition_analysis,
            'event_keys': composition_data['event_keys_raw']
        },
        'db_structure': db_structure,
        'search_results': search_results,
        'best_combinations_full': best_results_full[:20],
        'best_combinations_us_only': best_results_us_only[:20]
    }
    
    output_file = OUTPUT_DIR / "investigation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Résultats sauvegardés : {output_file}")
    
    # Rapport texte
    report_file = OUTPUT_DIR / "investigation_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 🔬 RAPPORT INVESTIGATION - RECHERCHE CLUSTERS SIMILAIRES\n\n")
        f.write(f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Cas référence :** {REFERENCE_DATE}\n")
        f.write(f"**Composition :** {len(composition_data['event_keys_raw'])} événements (US 14h30 + Current Account 14h45)\n\n")
        
        f.write("## 📊 Composition Référence\n\n")
        f.write(f"- Total événements : {composition_analysis['n_events_total']}\n")
        f.write(f"- Uniques (raw) : {composition_analysis['n_events_unique_raw']}\n")
        f.write(f"- Uniques (basic) : {composition_analysis['n_events_unique_basic']}\n")
        f.write(f"- Uniques (variants) : {composition_analysis['n_events_unique_variants']}\n\n")
        
        if composition_analysis['variants_detected']:
            f.write("### Variantes Détectées\n\n")
            for var in composition_analysis['variants_detected']:
                f.write(f"- `{var['original']}` → `{var['base_variant']}`\n")
            f.write("\n")
        
        f.write("## 🎯 Meilleures Combinaisons\n\n")
        
        f.write("### Composition Complète (US 14h30 + Current Account 14h45)\n\n")
        f.write("| Période | Jaccard | Basic | Variants | Gain |\n")
        f.write("|---------|---------|-------|----------|------|\n")
        for result in best_results_full[:20]:
            f.write(f"| {result['period']} | {result['threshold']:.1f} | "
                   f"{result['clusters_basic']} | {result['clusters_variants']} | {result['gain']:+d} |\n")
        
        f.write("\n### Uniquement US 14h30 (sans Current Account)\n\n")
        f.write("| Période | Jaccard | Basic | Variants | Gain |\n")
        f.write("|---------|---------|-------|----------|------|\n")
        for result in best_results_us_only[:20]:
            f.write(f"| {result['period']} | {result['threshold']:.1f} | "
                   f"{result['clusters_basic']} | {result['clusters_variants']} | {result['gain']:+d} |\n")
        
        f.write("\n## 💡 Conclusions\n\n")
        if best_results_full or best_results_us_only:
            if best_results_full:
                best_full = best_results_full[0]
                f.write(f"**Meilleure combinaison (Composition complète) :**\n")
                f.write(f"- Période : {best_full['period']}\n")
                f.write(f"- Seuil Jaccard : {best_full['threshold']}\n")
                f.write(f"- Clusters trouvés : {best_full['clusters_variants']}\n")
                f.write(f"- Gain vs basic : {best_full['gain']:+d}\n\n")
            
            if best_results_us_only:
                best_us = best_results_us_only[0]
                f.write(f"**Meilleure combinaison (Uniquement US) :**\n")
                f.write(f"- Période : {best_us['period']}\n")
                f.write(f"- Seuil Jaccard : {best_us['threshold']}\n")
                f.write(f"- Clusters trouvés : {best_us['clusters_variants']}\n")
                f.write(f"- Gain vs basic : {best_us['gain']:+d}\n\n")
        else:
            f.write("⚠️ **AUCUN cluster similaire trouvé avec aucune combinaison**\n\n")
            f.write("**Hypothèses :**\n")
            f.write("1. Le cas référence est vraiment unique\n")
            f.write("2. La composition est trop spécifique\n")
            f.write("3. Besoin d'autres critères de similarité (pays, timing, etc.)\n")
    
    print(f"✅ Rapport créé : {report_file}")
    
    print(f"\n{'='*80}")
    print("✅ INVESTIGATION TERMINÉE")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

