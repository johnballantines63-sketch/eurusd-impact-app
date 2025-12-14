#!/usr/bin/env python3
"""
SESSION 126 - INVESTIGATION RETAIL SALES
=========================================
Trouver pourquoi 'retail sales' n'existe pas dans events

Hypothèses:
1. Event_key différent (variante du nom)
2. Importance = 2 (MEDIUM) au lieu de 3 (HIGH)
3. Country différent
4. Données manquantes période récente
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

print("=" * 80)
print("INVESTIGATION : RETAIL SALES")
print("=" * 80)
print()

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# INVESTIGATION 1 : Chercher TOUTES variantes "retail"
# ============================================================================

print("[1] RECHERCHE LARGE : Tous événements contenant 'retail'")
print("-" * 80)
print()

query_all_retail = """
SELECT 
    event_key,
    importance_n,
    COUNT(*) as count,
    MIN(ts_utc) as first_date,
    MAX(ts_utc) as last_date
FROM events
WHERE country = 'US'
  AND LOWER(event_key) LIKE '%retail%'
GROUP BY event_key, importance_n
ORDER BY importance_n DESC, count DESC
"""

df_retail_all = conn.execute(query_all_retail).df()

if len(df_retail_all) > 0:
    print(f"✅ {len(df_retail_all)} variante(s) trouvée(s) :\n")
    
    for _, row in df_retail_all.iterrows():
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(row['importance_n'], "?")
        print(f"  event_key: '{row['event_key']}'")
        print(f"    Importance: [{imp_label}] ({row['importance_n']})")
        print(f"    Count: {row['count']} événements")
        print(f"    Période: {row['first_date'].strftime('%Y-%m-%d')} → {row['last_date'].strftime('%Y-%m-%d')}")
        print()
else:
    print("❌ AUCUN événement 'retail' trouvé dans table events")
    print()

# ============================================================================
# INVESTIGATION 2 : Vérifier event_title (fallback)
# ============================================================================

print("[2] FALLBACK : Chercher dans event_title")
print("-" * 80)
print()

query_title = """
SELECT 
    event_key,
    event_title,
    importance_n,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND LOWER(event_title) LIKE '%retail%'
GROUP BY event_key, event_title, importance_n
ORDER BY importance_n DESC, count DESC
LIMIT 10
"""

df_title = conn.execute(query_title).df()

if len(df_title) > 0:
    print(f"✅ {len(df_title)} résultat(s) dans event_title :\n")
    
    for _, row in df_title.iterrows():
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(row['importance_n'], "?")
        print(f"  [{imp_label}] event_key='{row['event_key']}'")
        print(f"       event_title='{row['event_title']}'")
        print(f"       {row['count']} événements")
        print()
else:
    print("❌ Aucun résultat dans event_title")
    print()

# ============================================================================
# INVESTIGATION 3 : Comparer avec fichier scores
# ============================================================================

print("[3] COMPARAISON : Scores CSV vs Table events")
print("-" * 80)
print()

df_scores = pd.read_csv(SCORES_PATH)

# Tous les event_names "retail" dans scores
retail_scores = df_scores[
    (df_scores['country'] == 'usd') &
    (df_scores['event_name'].str.contains('retail', case=False, na=False))
]

print(f"📊 Scores CSV avec 'retail' (country='usd') :")
print()

if len(retail_scores) > 0:
    for _, row in retail_scores.iterrows():
        event_name = row['event_name']
        score = row['empirical_score']
        
        # Convertir event_name → event_key (underscores → espaces)
        event_key_variant = event_name.replace('_', ' ')
        
        print(f"  event_name: '{event_name}'")
        print(f"  event_key attendu: '{event_key_variant}'")
        print(f"  score: {score:.2f}")
        
        # Vérifier si existe dans events
        check_query = """
        SELECT COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND event_key = ?
        """
        
        count_in_db = conn.execute(check_query, [event_key_variant]).fetchone()[0]
        
        if count_in_db > 0:
            print(f"  ✅ Trouvé dans events : {count_in_db} événements")
        else:
            print(f"  ❌ INTROUVABLE dans events")
        
        print()
else:
    print("❌ Aucun score 'retail' dans CSV")
    print()

# ============================================================================
# INVESTIGATION 4 : Top événements US par importance
# ============================================================================

print("[4] CONTEXTE : Top événements US HIGH")
print("-" * 80)
print()

query_top = """
SELECT 
    event_key,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND ts_utc >= '2023-01-01'
GROUP BY event_key
ORDER BY count DESC
LIMIT 15
"""

df_top = conn.execute(query_top).df()

print("Top 15 événements US HIGH (2023+) :\n")
for idx, row in df_top.iterrows():
    print(f"  {idx+1:2d}. '{row['event_key']:<40s}' : {row['count']:3d} événements")

print()

# ============================================================================
# INVESTIGATION 5 : Échantillon détaillé si trouvé
# ============================================================================

print("[5] ÉCHANTILLON : Si variante trouvée")
print("-" * 80)
print()

if len(df_retail_all) > 0:
    # Prendre la première variante (plus fréquente)
    best_match = df_retail_all.iloc[0]
    event_key_found = best_match['event_key']
    importance_found = best_match['importance_n']
    
    print(f"Meilleure correspondance : '{event_key_found}' (importance={importance_found})")
    print()
    
    query_sample = """
    SELECT 
        ts_utc,
        event_key,
        importance_n,
        actual,
        estimate,
        previous
    FROM events
    WHERE country = 'US'
      AND event_key = ?
      AND ts_utc >= '2023-01-01'
    ORDER BY ts_utc DESC
    LIMIT 5
    """
    
    df_sample = conn.execute(query_sample, [event_key_found]).df()
    
    print(f"Échantillon (5 derniers depuis 2023) :\n")
    for _, row in df_sample.iterrows():
        print(f"  {row['ts_utc'].strftime('%Y-%m-%d %H:%M')} | imp={row['importance_n']} | "
              f"actual={row['actual']} | estimate={row['estimate']}")
    
    print()

conn.close()

# ============================================================================
# RECOMMANDATION
# ============================================================================

print("=" * 80)
print("RECOMMANDATION")
print("=" * 80)
print()

if len(df_retail_all) > 0:
    best = df_retail_all.iloc[0]
    
    if best['importance_n'] == 3:
        print(f"✅ SOLUTION TROUVÉE : Utiliser event_key = '{best['event_key']}'")
        print()
        print(f"   Commande test :")
        print(f"   python calibrate_universal_amplification.py --event_type=\"{best['event_key']}\"")
    else:
        imp_label = {1: "LOW", 2: "MED"}.get(best['importance_n'], "?")
        print(f"⚠️  RETAIL SALES trouvé mais importance = {imp_label} (pas HIGH)")
        print(f"   event_key: '{best['event_key']}'")
        print()
        print(f"   OPTIONS :")
        print(f"   A) Utiliser quand même (adapter importance_n = {best['importance_n']})")
        print(f"   B) Chercher autre famille HIGH (déjà Fed Decision disponible)")
else:
    print("❌ RETAIL SALES introuvable dans DB")
    print()
    print("   ACTIONS POSSIBLES :")
    print("   1. Vérifier données source (JBlanked API)")
    print("   2. Utiliser Fed Decision à la place (17 événements HIGH)")
    print("   3. Tester autre famille : GDP, PPI, ISM Manufacturing, etc.")

print()
print("=" * 80)
