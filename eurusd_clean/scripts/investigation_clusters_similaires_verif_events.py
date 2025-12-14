#!/usr/bin/env python3
"""
VÉRIFICATION ÉVÉNEMENTS CLUSTER DE RÉFÉRENCE
============================================

Vérifie dans la DB quels événements correspondent au cluster de référence :
- Tous les événements US à 14h30 (heure de Berne = 12:30 UTC)
- Current account à 14h45 (heure de Berne = 12:45 UTC)

Date référence : 2025-09-11
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = "data/warehouse.duckdb"
REFERENCE_DATE = "2025-09-11"

# Heures de référence (heure de Berne)
TIME_1430_BERNE = "14:30:00"  # Heure de Berne
TIME_1445_BERNE = "14:45:00"  # Heure de Berne


def main():
    print("=" * 80)
    print("VÉRIFICATION ÉVÉNEMENTS CLUSTER DE RÉFÉRENCE")
    print("=" * 80)
    
    print(f"\n📅 Date référence : {REFERENCE_DATE}")
    print(f"🕐 Critères :")
    print(f"   1. Tous événements US à 14h30 (heure Berne) - fenêtre 14:25-14:35")
    print(f"   2. Current account à 14h45 (heure Berne) - fenêtre 14:40-14:50")
    print(f"   Filtre : importance_n = 3 OU empirical_score > 40 (HIGH impact)")
    
    # Connexion DB
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Requête 1 : Événements US à 12:30 UTC (14h30 heure Berne)
    print(f"\n{'='*80}")
    print("ÉVÉNEMENTS US À 12:30 UTC (14h30 heure Berne)")
    print(f"{'='*80}\n")
    
    # Utiliser fenêtre temporelle comme dans session115/test_double_wave_overlapping_11sept.py
    # Fenêtre ±5 minutes autour de 14h30 heure Berne
    # 14h30 heure Berne = 12:30 UTC (en été, UTC+2)
    window_start = f"{REFERENCE_DATE} 14:25:00+02:00"
    window_end = f"{REFERENCE_DATE} 14:35:00+02:00"
    
    query_us_1430 = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country,
        e.importance_n,
        e.actual,
        e.forecast,
        e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= ?
      AND e.ts_utc < ?
      AND e.country = 'US'
      -- Pas de filtre importance pour capturer TOUS les événements US à 14h30
    ORDER BY e.ts_utc, e.event_key
    """
    
    df_us_1430 = conn.execute(query_us_1430, [window_start, window_end]).df()
    
    if len(df_us_1430) == 0:
        print("❌ Aucun événement US trouvé à 12:30 UTC")
    else:
        print(f"✅ {len(df_us_1430)} événements US trouvés :\n")
        for idx, row in df_us_1430.iterrows():
            print(f"   {idx+1:2d}. {row['event_key']:<50} (importance: {row['importance_n']})")
            if pd.notna(row['actual']):
                print(f"       Actual: {row['actual']}, Forecast: {row['forecast']}, Previous: {row['previous']}")
    
    # Requête 2 : Current account à 12:45 UTC (14h45 heure Berne)
    print(f"\n{'='*80}")
    print("CURRENT ACCOUNT À 12:45 UTC (14h45 heure Berne)")
    print(f"{'='*80}\n")
    
    # Fenêtre ±5 minutes autour de 14h45 heure Berne
    window_ca_start = f"{REFERENCE_DATE} 14:40:00+02:00"
    window_ca_end = f"{REFERENCE_DATE} 14:50:00+02:00"
    
    query_current_account = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country,
        e.importance_n,
        e.actual,
        e.forecast,
        e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= ?
      AND e.ts_utc < ?
      AND LOWER(e.event_key) LIKE '%current account%'
      -- Inclure même si importance_n=2 (comme pour le 11 septembre)
    ORDER BY e.country, e.ts_utc, e.event_key
    """
    
    df_current_account = conn.execute(query_current_account, [window_ca_start, window_ca_end]).df()
    
    if len(df_current_account) == 0:
        print("❌ Aucun 'current account' trouvé à 14h45 (importance_n=3 ou score>40)")
        # Essayer sans filtre pour voir s'il existe
        query_ca_no_filter = """
        SELECT 
            e.ts_utc,
            e.event_key,
            e.country,
            e.importance_n,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.ts_utc >= ?
          AND e.ts_utc < ?
          AND LOWER(e.event_key) LIKE '%current account%'
        ORDER BY e.country, e.ts_utc, e.event_key
        """
        df_ca_no_filter = conn.execute(query_ca_no_filter, [window_ca_start, window_ca_end]).df()
        # Utiliser les résultats sans filtre pour current account
        df_current_account = df_ca_no_filter
        if len(df_ca_no_filter) > 0:
            print(f"\n   ✅ {len(df_ca_no_filter)} 'current account' trouvé(s) (sans filtre importance) :")
            for idx, row in df_ca_no_filter.iterrows():
                print(f"      {idx+1:2d}. {row['event_key']:<50} [{row['country']}] (importance: {row['importance_n']}, score: {row['empirical_score']})")
    else:
        print(f"✅ {len(df_current_account)} événements 'current account' trouvés :\n")
        for idx, row in df_current_account.iterrows():
            print(f"   {idx+1:2d}. {row['event_key']:<50} (country: {row['country']}, importance: {row['importance_n']})")
            if pd.notna(row['actual']):
                print(f"       Actual: {row['actual']}, Forecast: {row['forecast']}, Previous: {row['previous']}")
    
    # Composition complète du cluster
    print(f"\n{'='*80}")
    print("COMPOSITION COMPLÈTE DU CLUSTER DE RÉFÉRENCE")
    print(f"{'='*80}\n")
    
    all_events = pd.concat([df_us_1430, df_current_account], ignore_index=True)
    
    if len(all_events) == 0:
        print("❌ Aucun événement trouvé pour ce cluster")
        conn.close()
        return 1
    
    print(f"📊 Total événements dans le cluster : {len(all_events)}")
    print(f"\nListe complète des event_key :\n")
    
    event_keys = sorted(all_events['event_key'].unique().tolist())
    for i, key in enumerate(event_keys, 1):
        print(f"   {i:2d}. {key}")
    
    # Normalisation
    print(f"\n{'='*80}")
    print("COMPOSITION NORMALISÉE (pour recherche)")
    print(f"{'='*80}\n")
    
    event_keys_normalized = [k.lower().strip() for k in event_keys]
    composition_set = set(event_keys_normalized)
    
    print(f"📋 Composition unique (normalisée basic) : {len(composition_set)} événements")
    print(f"\n{sorted(composition_set)}")
    
    # Sauvegarder pour utilisation dans le script de recherche
    output_file = Path(__file__).parent / "investigation_clusters" / "cluster_reference_composition.json"
    output_file.parent.mkdir(exist_ok=True)
    
    import json
    output_data = {
        "reference_date": REFERENCE_DATE,
        "criteria": {
            "us_events_1430_berne": "12:30 UTC",
            "current_account_1445_berne": "12:45 UTC"
        },
        "events": all_events.to_dict('records'),
        "event_keys_raw": event_keys,
        "event_keys_normalized": sorted(composition_set),
        "composition_set": sorted(list(composition_set))
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Composition sauvegardée dans : {output_file}")
    
    conn.close()
    return 0


if __name__ == "__main__":
    exit(main())

