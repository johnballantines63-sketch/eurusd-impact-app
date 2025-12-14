#!/usr/bin/env python3
"""
Clarification Tables - Session 126
Vérifie quelle(s) table(s) existent et leurs structures
"""
import duckdb
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb")

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("CLARIFICATION TABLES - Session 126")
print("=" * 80)
print()

# Lister toutes les tables
print("[1] TABLES DISPONIBLES :")
print("-" * 80)
tables = conn.execute("SHOW TABLES").df()
print(f"  {len(tables)} tables trouvées :\n")
for _, row in tables.iterrows():
    print(f"    • {row['name']}")

print()

# Vérifier si 'events' existe
print("[2] TABLE 'events' :")
print("-" * 80)
if 'events' in tables['name'].values:
    print("  ✅ Existe")
    
    # Schéma
    schema = conn.execute("DESCRIBE events").df()
    print(f"\n  Colonnes ({len(schema)}) :")
    for _, col in schema.iterrows():
        print(f"    - {col['column_name']:<30} {col['column_type']}")
    
    # Stats
    count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"\n  Total lignes : {count:,}")
    
    # Échantillon
    sample = conn.execute("""
        SELECT ts_utc, event_key, country, importance_n 
        FROM events 
        WHERE importance_n = 3 
        LIMIT 3
    """).fetchall()
    
    print(f"\n  Échantillon (importance_n=3) :")
    for row in sample:
        print(f"    {row[0]} | {row[1]:30s} | country={row[2]} | imp={row[3]}")
else:
    print("  ✗ N'existe PAS")

print()

# Vérifier si 'economic_events' existe
print("[3] TABLE 'economic_events' :")
print("-" * 80)
if 'economic_events' in tables['name'].values:
    print("  ✅ Existe")
    
    # Schéma
    schema = conn.execute("DESCRIBE economic_events").df()
    print(f"\n  Colonnes ({len(schema)}) :")
    for _, col in schema.iterrows():
        print(f"    - {col['column_name']:<30} {col['column_type']}")
    
    # Stats
    count = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"\n  Total lignes : {count:,}")
    
    # Échantillon
    sample = conn.execute("""
        SELECT datetime_utc, event_name, country, importance 
        FROM economic_events 
        WHERE importance = 'HIGH' 
        LIMIT 3
    """).fetchall()
    
    print(f"\n  Échantillon (importance='HIGH') :")
    for row in sample:
        print(f"    {row[0]} | {row[1]:30s} | country={row[2]} | imp={row[3]}")
else:
    print("  ✗ N'existe PAS")

print()

# Comparer CPI dans les 2 tables (si les 2 existent)
if 'events' in tables['name'].values and 'economic_events' in tables['name'].values:
    print("[4] COMPARAISON CPI ENTRE LES 2 TABLES :")
    print("-" * 80)
    
    count_events = conn.execute("""
        SELECT COUNT(*) FROM events
        WHERE country = 'US' 
          AND importance_n = 3
          AND LOWER(event_key) LIKE '%cpi%'
    """).fetchone()[0]
    
    count_economic = conn.execute("""
        SELECT COUNT(*) FROM economic_events
        WHERE country = 'usd'
          AND importance = 'HIGH'
          AND LOWER(event_name) LIKE '%cpi%'
    """).fetchone()[0]
    
    print(f"  Table 'events'          : {count_events:3d} CPI (country='US', importance_n=3)")
    print(f"  Table 'economic_events' : {count_economic:3d} CPI (country='usd', importance='HIGH')")
    
    if count_events == count_economic:
        print("\n  ✅ Même nombre → Probablement DONNÉES IDENTIQUES")
    else:
        print(f"\n  ⚠️  Différence de {abs(count_events - count_economic)} événements")

conn.close()

print()
print("=" * 80)
print("RECOMMANDATION POUR SESSION 126 :")
print("=" * 80)
print()
print("  Utiliser la table qui contient le plus d'événements")
print("  OU celle utilisée dans Session 125 pour cohérence")
print()
