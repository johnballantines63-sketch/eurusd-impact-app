#!/usr/bin/env python3
"""
Catalogage simplifié des clusters depuis la DB
==============================================

Version rapide qui :
1. Identifie tous les clusters uniques (signature ADN)
2. Compte leurs occurrences historiques
3. Ne mesure PAS l'impact (sera fait séparément si nécessaire)

Usage:
    python3 scripts/catalog_clusters_simple.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

import pandas as pd
import numpy as np
import duckdb
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'pages'))

from Planificateur_V3_CLEAN import (
    build_cluster_signature
)

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'
OUTPUT_CACHE = PROJECT_ROOT / 'data' / 'cache_clusters_catalogued_simple.csv'

TIMEZONE_BERN = 'Europe/Zurich'
MIN_EVENTS_FOR_CLUSTER = 7


def load_events_from_economic_events(
    date: datetime,
    conn,
    timezone_str: str = TIMEZONE_BERN,
    min_importance: int = 1,
    countries: List[str] = None,
    exclude_no_actual: bool = False
) -> pd.DataFrame:
    """Charge les événements depuis la table economic_events"""
    if countries is None:
        countries = ['US', 'DE', 'EU']
    
    date_str = date.strftime('%Y-%m-%d')
    date_next_str = (date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    countries_str = "', '".join(countries)
    
    query = f"""
    SELECT 
        datetime_utc as ts_utc,
        country,
        event_name as event_title,
        event_name as event_key,
        importance,
        actual,
        forecast as estimate,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '{date_str}'
      AND country IN ('{countries_str}')
    ORDER BY datetime_utc
    """
    
    df = conn.execute(query).df()
    
    if df.empty:
        return pd.DataFrame()
    
    # Convertir ts_utc en datetime
    df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    # Convertir en timezone de Berne
    if df['ts_utc'].dt.tz is None:
        df['ts_utc'] = df['ts_utc'].dt.tz_localize('UTC')
    df['ts_bern'] = df['ts_utc'].dt.tz_convert(timezone_str)
    
    # Normaliser event_key (lowercase, sans underscores)
    df['event_key'] = df['event_key'].str.lower().str.replace('_', ' ')
    
    # Filtrer par importance (importance est un string dans economic_events)
    # High=1, Medium=2, Low=3 (insensible à la casse)
    importance_map = {'high': 1, 'medium': 2, 'low': 3}
    df['importance_n'] = df['importance'].str.lower().map(importance_map).fillna(3)
    df = df[df['importance_n'] <= min_importance]
    
    # Exclure les événements sans actual si demandé
    if exclude_no_actual:
        df = df[df['actual'].notna()]
    
    return df.reset_index(drop=True)


def get_all_dates_with_events(conn) -> List[datetime]:
    """Récupère toutes les dates uniques avec des événements"""
    query = """
    SELECT DISTINCT DATE(datetime_utc) as date
    FROM economic_events
    WHERE country IN ('US', 'DE', 'EU')
    ORDER BY date
    """
    
    df = conn.execute(query).df()
    dates = [pd.to_datetime(row['date']).to_pydatetime() for _, row in df.iterrows()]
    return dates


def identify_clusters_for_date_simple(
    date: datetime,
    conn,
    timezone_str: str = TIMEZONE_BERN,
    window_minutes: int = 30,
    min_events: int = MIN_EVENTS_FOR_CLUSTER
) -> List[Dict]:
    """
    Identifie tous les clusters pour une date donnée (version simplifiée)
    
    Returns:
        Liste de dicts avec cluster_signature, event_keys, anchor_time, n_events
    """
    # Charger tous les événements de la date depuis economic_events
    # min_importance=3 pour inclure High (1), Medium (2) et Low (3)
    df_events = load_events_from_economic_events(
        date,
        conn,
        timezone_str,
        min_importance=3,  # Inclure tous les niveaux d'importance
        countries=['US', 'DE', 'EU'],
        exclude_no_actual=False
    )
    
    if df_events.empty:
        return []
    
    clusters = []
    df_events = df_events.sort_values('ts_bern').reset_index(drop=True)
    
    # Séparer US et autres
    df_us_events = df_events[df_events['country'] == 'US'].copy()
    df_other_events = df_events[df_events['country'] != 'US'].copy()
    
    # Construire clusters à partir des événements US
    # Grouper les événements US par fenêtre de 30 minutes
    processed_indices = set()
    
    for i in range(len(df_us_events)):
        if i in processed_indices:
            continue
        
        anchor_time = df_us_events.iloc[i]['ts_bern']
        window_end = anchor_time + pd.Timedelta(minutes=window_minutes)
        
        # Trouver tous les événements US dans cette fenêtre
        mask_us = (df_us_events['ts_bern'] >= anchor_time) & (df_us_events['ts_bern'] <= window_end)
        events_us_in_window = df_us_events[mask_us]
        
        # Marquer tous les indices de cette fenêtre comme traités
        processed_indices.update(events_us_in_window.index.tolist())
        
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
                            'date': date
                        })
    
    return clusters


def catalog_clusters_simple(date_from: datetime = None, date_to: datetime = None):
    """Fonction principale pour cataloguer les clusters (version simplifiée)"""
    print("=" * 80)
    print("📚 CATALOGAGE SIMPLIFIÉ DES CLUSTERS DEPUIS LA DB")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Récupérer toutes les dates
    print("1️⃣ Récupération de toutes les dates avec événements...")
    all_dates = get_all_dates_with_events(conn)
    
    if date_from:
        all_dates = [d for d in all_dates if d >= date_from]
    if date_to:
        all_dates = [d for d in all_dates if d <= date_to]
    
    dates = sorted(all_dates)
    
    print(f"   ✅ {len(dates)} dates trouvées")
    if dates:
        print(f"   Période : {dates[0].strftime('%Y-%m-%d')} à {dates[-1].strftime('%Y-%m-%d')}")
    print()
    
    # 2. Identifier tous les clusters
    print("2️⃣ Identification des clusters pour chaque date...")
    print("-" * 80)
    
    all_clusters = []
    
    for date in tqdm(dates, desc="Scan dates"):
        clusters = identify_clusters_for_date_simple(
            date,
            conn,
            timezone_str=TIMEZONE_BERN,
            window_minutes=30,
            min_events=MIN_EVENTS_FOR_CLUSTER
        )
        
        for cluster in clusters:
            all_clusters.append(cluster)
    
    conn.close()
    
    print(f"   ✅ {len(all_clusters)} clusters identifiés au total")
    print()
    
    # 3. Grouper par signature ADN
    print("3️⃣ Groupement par signature ADN...")
    print("-" * 80)
    
    clusters_by_signature = defaultdict(list)
    for cluster_data in all_clusters:
        sig = cluster_data['cluster_signature']
        clusters_by_signature[sig].append(cluster_data)
    
    print(f"   ✅ {len(clusters_by_signature)} clusters uniques identifiés")
    print()
    
    # 4. Créer le catalogue
    print("4️⃣ Création du catalogue...")
    print("-" * 80)
    
    catalogued = []
    for signature, occurrences in clusters_by_signature.items():
        # Calculer les stats de base
        n_events_list = [occ['n_events'] for occ in occurrences]
        n_us_events_list = [occ['n_us_events'] for occ in occurrences]
        
        # Extraire les event_keys (tous identiques pour un même cluster)
        event_keys = occurrences[0]['event_keys'] if occurrences else []
        
        catalogued.append({
            'cluster_signature': signature,
            'n_samples': len(occurrences),
            'num_events_median': float(np.median(n_events_list)) if n_events_list else 0.0,
            'num_events_mean': float(np.mean(n_events_list)) if n_events_list else 0.0,
            'num_events_min': float(np.min(n_events_list)) if n_events_list else 0.0,
            'num_events_max': float(np.max(n_events_list)) if n_events_list else 0.0,
            'n_us_events_median': float(np.median(n_us_events_list)) if n_us_events_list else 0.0,
            'event_keys': ','.join(event_keys),
            'first_occurrence': min(occ['date'] for occ in occurrences).strftime('%Y-%m-%d'),
            'last_occurrence': max(occ['date'] for occ in occurrences).strftime('%Y-%m-%d'),
            'dates': ','.join(sorted(set(occ['date'].strftime('%Y-%m-%d') for occ in occurrences)))
        })
    
    # 5. Sauvegarder
    print("5️⃣ Sauvegarde du catalogue...")
    print("-" * 80)
    
    if not catalogued:
        print("   ⚠️  Aucun cluster trouvé. Vérifiez les critères de détection.")
        print(f"      - Minimum d'événements requis : {MIN_EVENTS_FOR_CLUSTER}")
        print(f"      - Fenêtre temporelle : 30 minutes")
        return
    
    df_catalogued = pd.DataFrame(catalogued)
    df_catalogued = df_catalogued.sort_values('n_samples', ascending=False)
    
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
    
    # Top clusters
    print("🏆 TOP 15 CLUSTERS PAR NOMBRE D'OCCURRENCES")
    print("-" * 80)
    for idx, row in df_catalogued.head(15).iterrows():
        sig = row['cluster_signature']
        n_samples = row['n_samples']
        n_events = row['num_events_median']
        first_date = row['first_occurrence']
        last_date = row['last_occurrence']
        
        print(f"   {n_samples:2d} occ. | {n_events:.0f} évts | {first_date} → {last_date}")
        print(f"      {sig[:100]}...")
        print()
    
    print("=" * 80)
    print("✅ CATALOGAGE TERMINÉ")
    print("=" * 80)
    print()
    print(f"💡 Le catalogue a été sauvegardé dans : {OUTPUT_CACHE}")
    print(f"   Ce fichier liste tous les clusters identifiés avec leurs occurrences")
    print(f"   Vous pouvez maintenant utiliser ce catalogue pour l'identification dans le Planificateur")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cataloguer les clusters (version simplifiée)")
    parser.add_argument("--from-date", type=str, help="Date de début (YYYY-MM-DD)", default=None)
    parser.add_argument("--to-date", type=str, help="Date de fin (YYYY-MM-DD)", default=None)
    parser.add_argument("--test", action="store_true", help="Mode test : 30 derniers jours")
    
    args = parser.parse_args()
    
    date_from = None
    date_to = None
    
    if args.test:
        date_to = datetime.now()
        date_from = date_to - timedelta(days=30)
        print("🧪 MODE TEST : Analyse des 30 derniers jours uniquement")
        print()
    else:
        if args.from_date:
            date_from = datetime.strptime(args.from_date, '%Y-%m-%d')
        if args.to_date:
            date_to = datetime.strptime(args.to_date, '%Y-%m-%d')
    
    catalog_clusters_simple(date_from=date_from, date_to=date_to)

