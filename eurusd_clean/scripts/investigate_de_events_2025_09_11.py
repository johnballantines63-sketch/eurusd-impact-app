"""
Investigation Événements DE pour 2025-09-11
===========================================

Vérifier pourquoi les événements DE ne sont pas chargés pour cette date.
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
import config

# Connexion DB
conn = duckdb.connect(str(config.DB_PATH), read_only=True)

date_str = '2025-09-11'
target_date = datetime(2025, 9, 11)

print("=" * 80)
print(f"INVESTIGATION ÉVÉNEMENTS DE POUR {date_str}")
print("=" * 80)
print()

# 1. Vérifier tous les événements DE pour cette date (sans filtre)
print("1. TOUS les événements DE pour cette date (sans filtre empirical_score) :")
print("-" * 80)

query_all = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.country,
    e.importance_n,
    ef.family,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'DE'
ORDER BY e.ts_utc
"""

df_all_de = conn.execute(query_all, [date_str]).df()

if df_all_de.empty:
    print("❌ AUCUN événement DE trouvé dans la table events pour cette date !")
else:
    print(f"✅ {len(df_all_de)} événement(s) DE trouvé(s) :")
    print()
    for idx, row in df_all_de.iterrows():
        print(f"  📌 {row['event_title'] if pd.notna(row['event_title']) else row['event_key']}")
        print(f"     event_key      : {row['event_key']}")
        print(f"     ts_utc         : {row['ts_utc']}")
        print(f"     country        : {row['country']}")
        print(f"     family         : {row['family'] if pd.notna(row['family']) else 'NULL'}")
        print(f"     empirical_score: {row['empirical_score'] if pd.notna(row['empirical_score']) else 'NULL'}")
        print(f"     importance_n   : {row['importance_n'] if pd.notna(row['importance_n']) else 'NULL'}")
        print(f"     actual         : {row['actual'] if pd.notna(row['actual']) else 'NULL'}")
        print(f"     estimate       : {row['estimate'] if pd.notna(row['estimate']) else 'NULL'}")
        print()

# 2. Vérifier événements avec empirical_score > 40
print("\n2. Événements DE avec empirical_score > 40 (filtre actuel) :")
print("-" * 80)

query_filtered = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.country,
    e.importance_n,
    ef.family,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'DE'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""

df_filtered_de = conn.execute(query_filtered, [date_str]).df()

if df_filtered_de.empty:
    print("❌ AUCUN événement DE avec empirical_score > 40")
    print()
    if not df_all_de.empty:
        print("📊 Analyse des scores empiriques des événements DE trouvés :")
        scores = df_all_de['empirical_score'].dropna()
        if len(scores) > 0:
            print(f"   Scores disponibles : {scores.tolist()}")
            print(f"   Score max          : {scores.max():.2f}")
            print(f"   Score min          : {scores.min():.2f}")
            print(f"   Score moyen        : {scores.mean():.2f}")
            print()
            print("⚠️ PROBLÈME : Les événements DE ont des scores < 40, donc exclus par le filtre !")
            print("   → Ces événements sont essentiels selon l'utilisateur")
            print("   → Solution possible : Réduire le seuil pour DE ou charger séparément")
        else:
            print("   ⚠️ Aucun score empirique disponible pour ces événements")
            print("   → Vérifier si les événements sont dans event_families")
else:
    print(f"✅ {len(df_filtered_de)} événement(s) DE avec empirical_score > 40 :")
    for idx, row in df_filtered_de.iterrows():
        print(f"  📌 {row['event_title'] if pd.notna(row['event_title']) else row['event_key']}")
        print(f"     empirical_score: {row['empirical_score']:.2f}")

# 3. Vérifier si événements DE dans event_families
print("\n3. Vérification event_families pour DE :")
print("-" * 80)

if not df_all_de.empty:
    event_keys_de = df_all_de['event_key'].unique()
    print(f"   Clés événements DE trouvées : {list(event_keys_de)}")
    print()
    
    for event_key in event_keys_de:
        query_family = """
        SELECT 
            event_key,
            country,
            family,
            empirical_score
        FROM event_families
        WHERE event_key = ? AND country = 'DE'
        """
        df_family = conn.execute(query_family, [event_key]).df()
        
        if df_family.empty:
            print(f"   ❌ {event_key} : PAS dans event_families")
        else:
            for _, row in df_family.iterrows():
                print(f"   ✅ {event_key} :")
                print(f"      family         : {row['family'] if pd.notna(row['family']) else 'NULL'}")
                print(f"      empirical_score: {row['empirical_score'] if pd.notna(row['empirical_score']) else 'NULL'}")
                print()

# 4. Recommandations
print("\n" + "=" * 80)
print("RECOMMANDATIONS")
print("=" * 80)
print()

if df_all_de.empty:
    print("❌ Aucun événement DE dans la base de données pour cette date")
    print("   → Vérifier l'import des données DE")
elif df_filtered_de.empty and not df_all_de.empty:
    print("⚠️ Événements DE présents mais exclus par filtre empirical_score > 40")
    print()
    print("   Solutions possibles :")
    print("   1. Réduire le seuil pour DE (ex: > 30 au lieu de > 40)")
    print("   2. Charger événements DE séparément avec seuil différent")
    print("   3. Vérifier si les scores empiriques DE sont correctement calculés")
    print("   4. Ajouter événements DE manuellement si essentiels")
else:
    print("✅ Événements DE correctement chargés avec filtre > 40")

conn.close()

