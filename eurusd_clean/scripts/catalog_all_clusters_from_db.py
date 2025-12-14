#!/usr/bin/env python3
"""
Catalogage automatique de tous les clusters depuis la DB
========================================================

Objectif : Scanner la DB pour identifier et cataloguer TOUS les clusters
d'événements qui ont provoqué de forts mouvements, puis créer un cache complet.

Workflow :
1. Scanner toutes les dates dans la DB
2. Pour chaque date, identifier les clusters d'événements (US + DE current account)
3. Construire la signature ADN de chaque cluster
4. Pour chaque cluster unique, trouver toutes ses occurrences historiques
5. Calculer les stats (impact, pattern, etc.) en utilisant les données de prix
6. Générer un cache complet avec tous les clusters catalogués

Usage:
    python3 scripts/catalog_all_clusters_from_db.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

import pandas as pd
import duckdb
import numpy as np
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'pages'))

from Planificateur_V3_CLEAN import (
    build_cluster_signature,
    normalize_event_keys_list,
    load_events_for_date,
    scan_price_movements,
    detect_pattern_type,
    enrich_events_with_surprises
)

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'
OUTPUT_CACHE = PROJECT_ROOT / 'data' / 'cache_clusters_catalogued.csv'

TIMEZONE_BERN = 'Europe/Zurich'
MIN_EVENTS_FOR_CLUSTER = 7  # Minimum d'événements pour considérer un cluster
MIN_IMPACT_PIPS = 35.0  # Impact minimum pour considérer un mouvement significatif


def safe_median(series: pd.Series) -> float:
    """Calcule la médiane de manière sûre"""
    if series.empty or series.isna().all():
        return 0.0
    return float(series.median())


def safe_mean(series: pd.Series) -> float:
    """Calcule la moyenne de manière sûre"""
    if series.empty or series.isna().all():
        return 0.0
    return float(series.mean())


def get_all_dates_with_events(conn, min_importance: int = 1) -> List[datetime]:
    """Récupère toutes les dates uniques avec des événements"""
    # Utiliser la table 'events' (comme load_events_for_date)
    query = """
    SELECT DISTINCT DATE(ts_utc) as date
    FROM events
    WHERE country IN ('US', 'DE', 'EU')
      AND importance_n <= ?
    ORDER BY date
    """
    
    df = conn.execute(query, [min_importance]).df()
    dates = [pd.to_datetime(row['date']).to_pydatetime() for _, row in df.iterrows()]
    return dates


def identify_clusters_for_date(
    date: datetime,
    conn,
    timezone_str: str = TIMEZONE_BERN,
    window_minutes: int = 30,
    min_importance: int = 1,
    min_events: int = MIN_EVENTS_FOR_CLUSTER
) -> List[Dict]:
    """
    Identifie tous les clusters pour une date donnée
    
    Returns:
        Liste de dicts avec cluster_signature, event_keys, anchor_time, df_events
    """
    # Charger tous les événements de la date
    df_events = load_events_for_date(
        date,
        DB_PATH,
        timezone_str,
        min_importance,
        countries=['US', 'DE', 'EU'],
        exclude_no_actual=False  # Inclure tous pour l'identification
    )
    
    if df_events.empty:
        return []
    
    clusters = []
    df_events = df_events.sort_values('ts_bern').reset_index(drop=True)
    
    # Séparer US et autres
    df_us_events = df_events[df_events['country'] == 'US'].copy()
    df_other_events = df_events[df_events['country'] != 'US'].copy()
    
    # Construire clusters à partir des événements US
    i = 0
    while i < len(df_us_events):
        anchor_time = df_us_events.iloc[i]['ts_bern']
        window_end = anchor_time + pd.Timedelta(minutes=window_minutes)
        
        # Trouver tous les événements US dans cette fenêtre
        mask_us = (df_us_events['ts_bern'] >= anchor_time) & (df_us_events['ts_bern'] <= window_end)
        events_us_in_window = df_us_events[mask_us]
        
        if len(events_us_in_window) > 0:
            # Inclure aussi les événements DE Current Account proches
            window_de_end = anchor_time + pd.Timedelta(minutes=15)
            mask_de = (
                (df_other_events['country'] == 'DE') &
                (df_other_events['ts_bern'] >= anchor_time) &
                (df_other_events['ts_bern'] <= window_de_end) &
                (df_other_events['event_key'].str.contains('current account', case=False, na=False))
            )
            events_de_in_window = df_other_events[mask_de]
            
            # Combiner US + DE
            events_in_window = pd.concat([events_us_in_window, events_de_in_window], ignore_index=True)
            
            # Filtrer par nombre minimum d'événements
            if len(events_in_window) >= min_events:
                event_keys = events_in_window['event_key'].dropna().tolist()
                if event_keys:
                    signature = build_cluster_signature(event_keys)
                    if signature:
                        clusters.append({
                            'cluster_signature': signature,
                            'event_keys': event_keys,
                            'anchor_time': anchor_time,
                            'n_events': len(events_in_window),
                            'n_us_events': len(events_us_in_window),
                            'df_events': events_in_window.copy(),
                            'date': date
                        })
        
        # Passer au prochain événement US après la fenêtre
        i = df_us_events[df_us_events['ts_bern'] > window_end].index
        if len(i) == 0:
            break
        i = i[0]
    
    return clusters


def measure_impact_for_cluster(
    date: datetime,
    cluster: Dict,
    conn,
    timezone_str: str = TIMEZONE_BERN,
    min_pips: float = MIN_IMPACT_PIPS
) -> Optional[Dict]:
    """
    Mesure l'impact réel d'un cluster en analysant les prix
    
    Returns:
        Dict avec impact_pips, direction, pattern_type, latency, etc. ou None
    """
    # Charger les prix pour cette date
    query_prices = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE DATE(datetime) = ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query_prices, [date.strftime('%Y-%m-%d')]).df()
    
    if df_prices.empty:
        return None
    
    # Convertir en timezone
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    if df_prices['datetime'].dt.tz is None:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_localize(timezone_str)
    else:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_convert(timezone_str)
    df_prices = df_prices.set_index('datetime')
    
    # Enrichir les événements
    df_events = cluster['df_events'].copy()
    df_events_enriched = enrich_events_with_surprises(df_events)
    
    # Détecter le pattern
    anchor_time = cluster['anchor_time']
    pattern_result = detect_pattern_type(
        df_prices,
        df_events_enriched,
        min_pips=min_pips,
        timezone=timezone_str,
        cluster_anchor_time=anchor_time
    )
    
    if pattern_result.get('pattern_type') == 'INCONNU':
        return None
    
    movement = pattern_result.get('movement')
    if not movement:
        return None
    
    impact_pips = movement.get('impact_pips', 0)
    if impact_pips < min_pips:
        return None
    
    # Calculer la latence (temps entre premier événement et début du mouvement)
    first_event_time = df_events_enriched['ts_bern'].min()
    start_time = movement.get('start_time')
    
    latency_minutes = None
    if start_time and first_event_time:
        if isinstance(start_time, pd.Timestamp):
            latency_minutes = (start_time - first_event_time).total_seconds() / 60
        else:
            latency_minutes = (pd.Timestamp(start_time) - first_event_time).total_seconds() / 60
    
    # Calculer TTR (temps jusqu'au pic)
    peak_time = movement.get('peak_time')
    peak_minutes_from_start = None
    if peak_time and start_time:
        if isinstance(peak_time, pd.Timestamp) and isinstance(start_time, pd.Timestamp):
            peak_minutes_from_start = (peak_time - start_time).total_seconds() / 60
        else:
            peak_minutes_from_start = (pd.Timestamp(peak_time) - pd.Timestamp(start_time)).total_seconds() / 60
    
    # Calculer pullback (si Double Wave)
    pullback_pips = None
    if pattern_result.get('pattern_type') == 'DOUBLE_WAVE':
        metrics = pattern_result.get('metrics', {})
        pullback_pips = metrics.get('pullback_pips')
    
    return {
        'impact_pips': impact_pips,
        'direction': movement.get('direction', 'UNKNOWN'),
        'pattern_type': pattern_result.get('pattern_type', 'INCONNU'),
        'latency_minutes': latency_minutes,
        'peak_minutes_from_start': peak_minutes_from_start,
        'pullback_pips': pullback_pips,
        'detection_confidence': pattern_result.get('detection_confidence', 0.0)
    }


def catalog_all_clusters(date_from: Optional[datetime] = None, date_to: Optional[datetime] = None):
    """
    Fonction principale pour cataloguer tous les clusters
    
    Args:
        date_from: Date de début (None = toutes les dates)
        date_to: Date de fin (None = toutes les dates)
    """
    print("=" * 80)
    print("📚 CATALOGAGE AUTOMATIQUE DES CLUSTERS DEPUIS LA DB")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Récupérer toutes les dates avec événements
    print("1️⃣ Récupération de toutes les dates avec événements...")
    all_dates = get_all_dates_with_events(conn, min_importance=1)
    
    # Filtrer par période si spécifiée
    if date_from:
        all_dates = [d for d in all_dates if d >= date_from]
    if date_to:
        all_dates = [d for d in all_dates if d <= date_to]
    
    dates = sorted(all_dates)
    
    print(f"   ✅ {len(dates)} dates trouvées")
    if dates:
        print(f"   Période : {dates[0].strftime('%Y-%m-%d')} à {dates[-1].strftime('%Y-%m-%d')}")
    print()
    
    # 2. Identifier tous les clusters pour chaque date
    print("2️⃣ Identification des clusters pour chaque date...")
    print("-" * 80)
    
    all_clusters = []  # Liste de tous les clusters trouvés avec leurs dates
    
    for date in tqdm(dates, desc="Scan dates"):
        clusters = identify_clusters_for_date(
            date,
            conn,
            timezone_str=TIMEZONE_BERN,
            window_minutes=30,
            min_importance=1,
            min_events=MIN_EVENTS_FOR_CLUSTER
        )
        
        for cluster in clusters:
            all_clusters.append({
                'date': date,
                'cluster_signature': cluster['cluster_signature'],
                'event_keys': cluster['event_keys'],
                'anchor_time': cluster['anchor_time'],
                'n_events': cluster['n_events'],
                'n_us_events': cluster['n_us_events'],
                'df_events': cluster['df_events']
            })
    
    print(f"   ✅ {len(all_clusters)} clusters identifiés au total")
    print()
    
    # 3. Grouper par signature ADN et mesurer l'impact pour chaque occurrence
    print("3️⃣ Groupement par signature ADN et mesure des impacts...")
    print("-" * 80)
    
    clusters_by_signature = defaultdict(list)
    for cluster_data in all_clusters:
        sig = cluster_data['cluster_signature']
        clusters_by_signature[sig].append(cluster_data)
    
    print(f"   ✅ {len(clusters_by_signature)} clusters uniques identifiés")
    print()
    
    # 4. Pour chaque cluster unique, mesurer l'impact de toutes ses occurrences
    print("4️⃣ Mesure des impacts pour chaque occurrence...")
    print("-" * 80)
    
    catalogued_clusters = []
    
    for signature, occurrences in tqdm(clusters_by_signature.items(), desc="Mesure impacts"):
        impacts = []
        directions = []
        patterns = []
        latencies = []
        ttrs = []
        pullbacks = []
        total_scores = []
        num_events_list = []
        
        for occ in occurrences:
            # Mesurer l'impact
            impact_data = measure_impact_for_cluster(
                occ['date'],
                occ,
                conn,
                timezone_str=TIMEZONE_BERN,
                min_pips=MIN_IMPACT_PIPS
            )
            
            if impact_data:
                impacts.append(impact_data['impact_pips'])
                directions.append(impact_data['direction'])
                patterns.append(impact_data['pattern_type'])
                
                if impact_data['latency_minutes'] is not None:
                    latencies.append(impact_data['latency_minutes'])
                if impact_data['peak_minutes_from_start'] is not None:
                    ttrs.append(impact_data['peak_minutes_from_start'])
                if impact_data.get('pullback_pips') is not None:
                    pullbacks.append(impact_data['pullback_pips'])
                
                # Calculer le score total
                df_events = occ['df_events']
                df_events_enriched = enrich_events_with_surprises(df_events)
                total_score = df_events_enriched['score_adjusted'].sum()
                total_scores.append(total_score)
                
                num_events_list.append(occ['n_events'])
        
        # Si au moins une occurrence a un impact mesuré
        if impacts:
            # Calculer les stats
            catalogued_clusters.append({
                'cluster_signature': signature,
                'n_samples': len(impacts),
                'num_events_median': safe_median(pd.Series(num_events_list)) if num_events_list else 0.0,
                'total_score_median': safe_median(pd.Series(total_scores)) if total_scores else 0.0,
                'impact_median': safe_median(pd.Series(impacts)),
                'impact_mean': safe_mean(pd.Series(impacts)),
                'impact_std': float(pd.Series(impacts).std(ddof=0)) if len(impacts) > 1 else 0.0,
                'latency_median': safe_median(pd.Series(latencies)) if latencies else None,
                'ttr_median': safe_median(pd.Series(ttrs)) if ttrs else None,
                'pullback_median': safe_median(pd.Series(pullbacks)) if pullbacks else None,
                'dominant_pattern': pd.Series(patterns).value_counts().idxmax() if patterns else 'INCONNU',
                'dominant_direction': pd.Series(directions).value_counts().idxmax() if directions else 'UNKNOWN',
                'ratio_up': (pd.Series(directions) == 'UP').sum() / len(directions) if directions else 0.0,
                'ratio_down': (pd.Series(directions) == 'DOWN').sum() / len(directions) if directions else 0.0,
            })
    
    conn.close()
    
    # 5. Créer le DataFrame et sauvegarder
    print()
    print("5️⃣ Sauvegarde du cache catalogué...")
    print("-" * 80)
    
    df_catalogued = pd.DataFrame(catalogued_clusters)
    df_catalogued = df_catalogued.sort_values('n_samples', ascending=False)
    
    # Sauvegarder
    df_catalogued.to_csv(OUTPUT_CACHE, index=False)
    
    print(f"   ✅ {len(df_catalogued)} clusters catalogués sauvegardés dans {OUTPUT_CACHE}")
    print()
    
    # Statistiques
    print("📊 STATISTIQUES")
    print("-" * 80)
    print(f"   Clusters avec >= 3 occurrences : {len(df_catalogued[df_catalogued['n_samples'] >= 3])}")
    print(f"   Clusters avec >= 5 occurrences : {len(df_catalogued[df_catalogued['n_samples'] >= 5])}")
    print(f"   Clusters avec >= 10 occurrences : {len(df_catalogued[df_catalogued['n_samples'] >= 10])}")
    print()
    print(f"   Impact médian moyen : {df_catalogued['impact_median'].mean():.1f} pips")
    print(f"   Impact médian max : {df_catalogued['impact_median'].max():.1f} pips")
    print()
    
    # Top clusters
    print("🏆 TOP 10 CLUSTERS PAR NOMBRE D'OCCURRENCES")
    print("-" * 80)
    for idx, row in df_catalogued.head(10).iterrows():
        sig = row['cluster_signature']
        n_samples = row['n_samples']
        n_events = row['num_events_median']
        impact = row['impact_median']
        pattern = row['dominant_pattern']
        
        print(f"   {n_samples:2d} occ. | {n_events:.0f} évts | {impact:5.1f} pips | {pattern:20s}")
        print(f"      {sig[:90]}...")
        print()
    
    print("=" * 80)
    print("✅ CATALOGAGE TERMINÉ")
    print("=" * 80)
    print()
    print(f"💡 Le cache a été sauvegardé dans : {OUTPUT_CACHE}")
    print(f"   Vous pouvez maintenant remplacer cache_clusters.csv par ce fichier")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cataloguer tous les clusters depuis la DB")
    parser.add_argument("--from-date", type=str, help="Date de début (YYYY-MM-DD)", default=None)
    parser.add_argument("--to-date", type=str, help="Date de fin (YYYY-MM-DD)", default=None)
    parser.add_argument("--test", action="store_true", help="Mode test : analyser seulement les 30 derniers jours")
    
    args = parser.parse_args()
    
    date_from = None
    date_to = None
    
    if args.test:
        # Mode test : 30 derniers jours
        date_to = datetime.now()
        date_from = date_to - timedelta(days=30)
        print("🧪 MODE TEST : Analyse des 30 derniers jours uniquement")
        print()
    else:
        if args.from_date:
            date_from = datetime.strptime(args.from_date, '%Y-%m-%d')
        if args.to_date:
            date_to = datetime.strptime(args.to_date, '%Y-%m-%d')
    
    catalog_all_clusters(date_from=date_from, date_to=date_to)

