"""
SESSION 18 - RE-IMPORT CIBLÉ EODHD
Objectif : Récupérer estimates manquants pour événements HIGH importance
Auteur : Claude
Date : 19 octobre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import os
from fx_impact_app.src.eodhd_client import fetch_calendar_json, calendar_to_events_df

print("=" * 80)
print("🔄 RE-IMPORT CIBLÉ EODHD - ÉVÉNEMENTS HIGH IMPORTANCE")
print("=" * 80)

# Connexion DB
db_path = Path('fx_impact_app/data/warehouse.duckdb')
conn = duckdb.connect(str(db_path), read_only=False)

# ============================================================================
# ÉTAPE 1 : Identifier événements HIGH importance sans estimate
# ============================================================================

print("\n📊 ÉTAPE 1 : Identification événements critiques sans estimate")

query_missing = """
SELECT 
    e.event_key,
    e.country,
    MIN(e.ts_utc) as first_date,
    MAX(e.ts_utc) as last_date,
    COUNT(*) as total_events,
    SUM(CASE WHEN e.estimate IS NULL THEN 1 ELSE 0 END) as missing_estimate,
    MAX(ef.empirical_score) as score
FROM events e
INNER JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE ef.empirical_score >= 60  -- HIGH importance seulement
    AND e.ts_utc >= '2023-01-01'  -- Depuis 2023
GROUP BY e.event_key, e.country
HAVING SUM(CASE WHEN e.estimate IS NULL THEN 1 ELSE 0 END) > 0
ORDER BY MAX(ef.empirical_score) DESC, missing_estimate DESC
"""

df_missing = conn.execute(query_missing).df()

print(f"\n✅ Types événements HIGH importance avec estimates manquants : {len(df_missing)}")
print(f"\n📋 Top 20 prioritaires :")
print(df_missing.head(20).to_string(index=False))

# ============================================================================
# ÉTAPE 2 : Re-scraper par pays et période
# ============================================================================

print("\n" + "=" * 80)
print("🔄 ÉTAPE 2 : Re-scraping EODHD")
print("=" * 80)

# Vérifier API key
api_key = os.environ.get("EODHD_API_KEY")
if not api_key:
    print("❌ ERREUR : EODHD_API_KEY non défini dans l'environnement")
    conn.close()
    exit(1)

# Pays prioritaires
countries = ['US', 'EU', 'GB', 'DE', 'FR', 'JP', 'AU']

# Périodes à re-scraper (par trimestre pour éviter timeout)
periods = [
    ('2023-01-01', '2023-03-31'),
    ('2023-04-01', '2023-06-30'),
    ('2023-07-01', '2023-09-30'),
    ('2023-10-01', '2023-12-31'),
    ('2024-01-01', '2024-03-31'),
    ('2024-04-01', '2024-06-30'),
    ('2024-07-01', '2024-09-30'),
    ('2024-10-01', '2024-12-31'),
    ('2025-01-01', '2025-03-31'),
    ('2025-04-01', '2025-06-30'),
    ('2025-07-01', '2025-09-30'),
    ('2025-10-01', '2025-10-19'),
]

total_updated = 0
total_fetched = 0

for i, (start_date, end_date) in enumerate(periods, 1):
    print(f"\n📅 Période {i}/{len(periods)} : {start_date} → {end_date}")
    
    try:
        # Fetch depuis EODHD
        raw_data = fetch_calendar_json(
            start_date, 
            end_date, 
            countries=countries,
            api_key=api_key
        )
        
        total_fetched += len(raw_data)
        print(f"   ✅ Récupéré : {len(raw_data)} événements bruts")
        
        if len(raw_data) == 0:
            continue
        
        # Normaliser en DataFrame
        df_new = calendar_to_events_df(raw_data)
        print(f"   ✅ Normalisé : {len(df_new)} événements")
        
        if df_new.empty:
            continue
        
        # Filtrer seulement ceux avec estimate
        df_with_estimate = df_new[df_new['estimate'].notna()].copy()
        print(f"   ✅ Avec estimate : {len(df_with_estimate)}")
        
        if len(df_with_estimate) == 0:
            continue
        
        # Mettre à jour dans la DB
        for _, row in df_with_estimate.iterrows():
            try:
                # Update seulement si estimate est NULL dans DB
                update_query = """
                UPDATE events
                SET estimate = ?
                WHERE event_key = ?
                    AND country = ?
                    AND ts_utc = ?
                    AND estimate IS NULL
                """
                
                conn.execute(update_query, [
                    float(row['estimate']) if pd.notna(row['estimate']) else None,
                    row['event_key'],
                    row['country'],
                    row['ts_utc']
                ])
                
                total_updated += 1
                
            except Exception as e:
                print(f"   ⚠️ Erreur update : {e}")
                continue
        
        print(f"   ✅ Mis à jour : {total_updated} lignes cumulées")
        
    except Exception as e:
        print(f"   ❌ Erreur période : {e}")
        continue

# ============================================================================
# ÉTAPE 3 : Vérification résultats
# ============================================================================

print("\n" + "=" * 80)
print("📊 ÉTAPE 3 : VÉRIFICATION RÉSULTATS")
print("=" * 80)

# Re-compter estimates
new_stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN estimate IS NOT NULL THEN 1 ELSE 0 END) as with_estimate,
        ROUND(100.0 * SUM(CASE WHEN estimate IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_estimate
    FROM events
    WHERE ts_utc >= '2023-01-01'
""").fetchone()

print(f"\n📊 STATISTIQUES APRÈS RE-IMPORT (depuis 2023) :")
print(f"   Total événements : {new_stats[0]:,}")
print(f"   Avec estimate : {new_stats[1]:,} ({new_stats[2]}%)")

print(f"\n📈 RÉSUMÉ DU RE-IMPORT :")
print(f"   Événements récupérés API : {total_fetched:,}")
print(f"   Lignes mises à jour DB : {total_updated:,}")

# Vérifier événements HIGH importance
high_imp_stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN e.estimate IS NOT NULL THEN 1 ELSE 0 END) as with_estimate,
        ROUND(100.0 * SUM(CASE WHEN e.estimate IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_estimate
    FROM events e
    INNER JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE ef.empirical_score >= 60
        AND e.ts_utc >= '2023-01-01'
""").fetchone()

print(f"\n📊 STATISTIQUES HIGH IMPORTANCE (score ≥60) :")
print(f"   Total événements : {high_imp_stats[0]:,}")
print(f"   Avec estimate : {high_imp_stats[1]:,} ({high_imp_stats[2]}%)")

if high_imp_stats[2] >= 60:
    print("\n✅ SUCCÈS : >60% des événements HIGH importance ont estimate")
elif high_imp_stats[2] >= 50:
    print("\n⚠️ PARTIEL : 50-60% des événements HIGH importance ont estimate")
else:
    print("\n❌ INSUFFISANT : <50% des événements HIGH importance ont estimate")
    print("   → Nécessite correction manuelle (Phase 2)")

conn.close()

print("\n" + "=" * 80)
print("✅ RE-IMPORT TERMINÉ")
print("=" * 80)
