#!/usr/bin/env python3
"""
Diagnostic complet des doublons - Session 39
Analyse pourquoi CPI et Jobless Claims apparaissent 3-4x
"""

import duckdb
from pathlib import Path
from datetime import datetime
import pandas as pd

def diagnose_duplicates():
    """Diagnostic complet des événements dupliqués"""
    
    db_path = Path("fx_impact_app/data/warehouse.duckdb")
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée : {db_path}")
        return
    
    conn = duckdb.connect(str(db_path), read_only=True)
    
    print("=" * 80)
    print("🔍 DIAGNOSTIC DOUBLONS - SESSION 39")
    print("=" * 80)
    print()
    print("📅 Date cible : 11 septembre 2025")
    print()
    
    # === ANALYSE 1 : Événements bruts du 11 septembre ===
    print("=" * 80)
    print("1️⃣  ÉVÉNEMENTS BRUTS (table events)")
    print("=" * 80)
    print()
    
    query_raw = """
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        forecast,
        previous
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
    ORDER BY ts_utc, event_key
    """
    
    df_raw = conn.execute(query_raw).fetchdf()
    
    print(f"Total événements bruts : {len(df_raw)}")
    print()
    
    # Grouper par event_key pour trouver doublons
    duplicates = df_raw.groupby('event_key').size()
    duplicates = duplicates[duplicates > 1].sort_values(ascending=False)
    
    if len(duplicates) > 0:
        print("⚠️  DOUBLONS DÉTECTÉS dans table events :")
        print()
        for event_key, count in duplicates.items():
            print(f"   {event_key} : {count}x")
            # Montrer les lignes en détail
            dups = df_raw[df_raw['event_key'] == event_key]
            for idx, row in dups.iterrows():
                print(f"      → {row['ts_utc']} | Actual: {row['actual']} | Forecast: {row['forecast']} | Previous: {row['previous']}")
            print()
    else:
        print("✅ Aucun doublon dans table events")
        print()
    
    # === ANALYSE 2 : Événements avec familles (JOIN event_families) ===
    print("=" * 80)
    print("2️⃣  ÉVÉNEMENTS AVEC FAMILLES (events + event_families)")
    print("=" * 80)
    print()
    
    query_with_families = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country,
        e.importance_n,
        ef.family,
        ef.empirical_score
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key
    WHERE DATE(e.ts_utc) = '2025-09-11'
    ORDER BY e.ts_utc, e.event_key
    """
    
    df_families = conn.execute(query_with_families).fetchdf()
    
    print(f"Total événements avec famille : {len(df_families)}")
    print()
    
    # Grouper par event_key
    duplicates_families = df_families.groupby('event_key').size()
    duplicates_families = duplicates_families[duplicates_families > 1].sort_values(ascending=False)
    
    if len(duplicates_families) > 0:
        print("⚠️  DOUBLONS DÉTECTÉS après JOIN event_families :")
        print()
        for event_key, count in duplicates_families.items():
            print(f"   {event_key} : {count}x")
            # Montrer les familles associées
            dups = df_families[df_families['event_key'] == event_key]
            for idx, row in dups.iterrows():
                print(f"      → {row['ts_utc']} | Family: {row['family']} | Score: {row['empirical_score']}")
            print()
    else:
        print("✅ Aucun doublon après JOIN")
        print()
    
    # === ANALYSE 3 : Vérifier event_families pour patterns multiples ===
    print("=" * 80)
    print("3️⃣  PATTERNS MULTIPLES dans event_families")
    print("=" * 80)
    print()
    
    query_patterns = """
    SELECT 
        event_key,
        family,
        COUNT(*) as n_patterns
    FROM event_families
    WHERE event_key LIKE '%CPI%' 
       OR event_key LIKE '%Jobless%'
       OR event_key LIKE '%Claims%'
    GROUP BY event_key, family
    HAVING COUNT(*) > 1
    ORDER BY event_key, n_patterns DESC
    """
    
    df_patterns = conn.execute(query_patterns).fetchdf()
    
    if len(df_patterns) > 0:
        print("⚠️  Patterns multiples trouvés :")
        print()
        print(df_patterns.to_string())
        print()
    else:
        print("✅ Aucun pattern multiple détecté")
        print()
    
    # === ANALYSE 4 : Query AVEC DISTINCT ===
    print("=" * 80)
    print("4️⃣  TEST AVEC SELECT DISTINCT")
    print("=" * 80)
    print()
    
    query_distinct = """
    SELECT DISTINCT
        e.ts_utc,
        e.event_key,
        e.country,
        e.importance_n,
        ef.family,
        ef.empirical_score
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key
    WHERE DATE(e.ts_utc) = '2025-09-11'
    ORDER BY e.ts_utc, e.event_key
    """
    
    df_distinct = conn.execute(query_distinct).fetchdf()
    
    print(f"Total avec DISTINCT : {len(df_distinct)}")
    print(f"Total sans DISTINCT : {len(df_families)}")
    print(f"Différence : {len(df_families) - len(df_distinct)} événements éliminés")
    print()
    
    if len(df_families) > len(df_distinct):
        print("✅ DISTINCT résout le problème des doublons")
    else:
        print("⚠️  DISTINCT ne change rien → doublons ailleurs")
    
    print()
    
    # === ANALYSE 5 : Détail des événements 14:30 ===
    print("=" * 80)
    print("5️⃣  FOCUS SUR 14:30 UTC (peak doublons)")
    print("=" * 80)
    print()
    
    query_1430 = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country,
        e.importance_n,
        ef.family,
        e.actual,
        e.forecast,
        e.previous
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key
    WHERE DATE(e.ts_utc) = '2025-09-11'
      AND HOUR(e.ts_utc) = 14
      AND MINUTE(e.ts_utc) = 30
    ORDER BY e.event_key
    """
    
    df_1430 = conn.execute(query_1430).fetchdf()
    
    print(f"Total événements à 14:30 : {len(df_1430)}")
    print()
    
    if len(df_1430) > 0:
        print("Détail :")
        print()
        for idx, row in df_1430.iterrows():
            print(f"  {row['event_key']}")
            print(f"     Family: {row['family']}")
            print(f"     Actual: {row['actual']}, Forecast: {row['forecast']}, Previous: {row['previous']}")
            print()
    
    # === RÉSUMÉ ===
    print("=" * 80)
    print("📊 RÉSUMÉ")
    print("=" * 80)
    print()
    print(f"Événements bruts (events) : {len(df_raw)}")
    print(f"Après JOIN event_families : {len(df_families)}")
    print(f"Avec SELECT DISTINCT : {len(df_distinct)}")
    print()
    print(f"Doublons dans events : {len(duplicates)}")
    print(f"Doublons après JOIN : {len(duplicates_families)}")
    print()
    
    if len(df_families) > len(df_distinct):
        print("🎯 CONCLUSION : DISTINCT nécessaire dans la query Streamlit")
        print()
        print("   La query load_all_events_for_date() a déjà DISTINCT ✅")
        print("   Mais vérifier qu'elle est bien utilisée partout.")
    else:
        print("🎯 CONCLUSION : Doublons viennent de la table events elle-même")
        print("   → Nettoyage de la DB nécessaire")
    
    print()
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    diagnose_duplicates()
