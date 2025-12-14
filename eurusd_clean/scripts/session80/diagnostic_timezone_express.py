#!/usr/bin/env python3
"""
Session 80 - Diagnostic Express Timezone

Objectif : Vérifier rapidement si ts_utc dans events est vraiment UTC+2
Méthode : Comparer avec heures connues d'événements CPI/NFP
"""

import duckdb
from datetime import datetime
from pathlib import Path

# Chemin DB
DB_PATH = Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "data" / "warehouse.duckdb"

print("=" * 70)
print("DIAGNOSTIC TIMEZONE EXPRESS - SESSION 80")
print("=" * 70)
print()

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Test 1 : Événements CPI US du 11 septembre 2025
print("📅 TEST 1 : Événements 11 septembre 2025 (CPI US)")
print("-" * 70)

query_sept = """
SELECT 
    ts_utc,
    event_key,
    country,
    strftime(ts_utc, '%H:%M:%S') as heure_db,
    importance_n
FROM events 
WHERE DATE(ts_utc) = '2025-09-11'
  AND country = 'US'
  AND event_key LIKE '%CPI%'
ORDER BY ts_utc
LIMIT 5
"""

results_sept = conn.execute(query_sept).fetchall()

if results_sept:
    print(f"✅ {len(results_sept)} événements CPI trouvés\n")
    for row in results_sept:
        ts, key, country, heure, imp = row
        print(f"  {heure} UTC (DB) - {key[:50]}")
    
    print()
    print("💡 ANALYSE :")
    print("   CPI US publié à 08:30 ET (New York)")
    print("   → En UTC : 12:30 (été) ou 13:30 (hiver)")
    print("   → En UTC+2 (Berne) : 14:30")
    print()
    first_heure = results_sept[0][3]
    if first_heure.startswith('12:3') or first_heure.startswith('13:3'):
        print("   ✅ DB contient UTC (correct)")
    elif first_heure.startswith('14:3'):
        print("   ❌ DB contient UTC+2 (Berne) mal étiqueté 'utc'")
    else:
        print(f"   ⚠️ Heure inattendue : {first_heure}")
else:
    print("❌ Aucun événement CPI trouvé le 11 septembre 2025")

print()
print("=" * 70)

# Test 2 : Événements NFP (1er vendredi du mois, 08:30 ET)
print()
print("📅 TEST 2 : NFP août 2025 (1er août, normalement 08:30 ET)")
print("-" * 70)

query_nfp = """
SELECT 
    ts_utc,
    event_key,
    country,
    strftime(ts_utc, '%H:%M:%S') as heure_db
FROM events 
WHERE DATE(ts_utc) = '2025-08-01'
  AND country = 'US'
  AND (event_key LIKE '%Non%Farm%' OR event_key LIKE '%NFP%' OR event_key LIKE '%Payroll%')
ORDER BY ts_utc
LIMIT 5
"""

results_nfp = conn.execute(query_nfp).fetchall()

if results_nfp:
    print(f"✅ {len(results_nfp)} événements NFP trouvés\n")
    for row in results_nfp:
        ts, key, country, heure = row
        print(f"  {heure} UTC (DB) - {key[:50]}")
    
    print()
    print("💡 ANALYSE :")
    print("   NFP publié à 08:30 ET (New York)")
    print("   → En UTC : 12:30 (été) ou 13:30 (hiver)")
    print("   → En UTC+2 (Berne) : 14:30")
    print()
    first_heure = results_nfp[0][3]
    if first_heure.startswith('12:3') or first_heure.startswith('13:3'):
        print("   ✅ DB contient UTC (correct)")
    elif first_heure.startswith('14:3'):
        print("   ❌ DB contient UTC+2 (Berne) mal étiqueté 'utc'")
    else:
        print(f"   ⚠️ Heure inattendue : {first_heure}")
else:
    print("⚠️ Aucun événement NFP trouvé le 1er août 2025")

print()
print("=" * 70)

# Test 3 : Structure table prices_1m
print()
print("📊 TEST 3 : Structure table prices_1m")
print("-" * 70)

schema_prices = conn.execute("DESCRIBE prices_1m").fetchall()
print("Colonnes disponibles :")
for col in schema_prices:
    print(f"  - {col[0]:<15} {col[1]}")

print()
print("💡 Échantillon de données (3 premières lignes) :")
sample = conn.execute("SELECT * FROM prices_1m ORDER BY timestamp LIMIT 3").fetchall()
for row in sample:
    ts = datetime.fromtimestamp(row[0]) if len(row) > 0 else None
    print(f"  timestamp={row[0]} → {ts} UTC")
    print(f"  close={row[2] if len(row) > 2 else 'N/A'}")
    print()

conn.close()

print()
print("=" * 70)
print("🎯 CONCLUSION")
print("=" * 70)
print()
print("Si les événements affichent 14:30 → DB contient UTC+2 (Berne)")
print("Si les événements affichent 12:30/13:30 → DB contient UTC (correct)")
print()
print("Prix Dukascopy (prices_1m) utilisent TOUJOURS timestamp Unix = UTC")
print()
print("Recommandation :")
print("  → Si UTC+2 détecté : Corriger DB (Option B)")
print("  → Sinon : Problème ailleurs (vérifier scripts Session 75)")
print()
