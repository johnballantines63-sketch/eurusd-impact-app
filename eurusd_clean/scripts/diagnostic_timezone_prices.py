#!/usr/bin/env python3
"""
Diagnostic Timezone Prices
==========================
Analyse complète du problème de timezone dans prices_1m et prices_bern
"""

import duckdb
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("DIAGNOSTIC TIMEZONE PRICES")
print("=" * 80)
print()

# 1. Vérifier la structure de la table prices_1m
print("1️⃣ Structure de la table prices_1m")
print("-" * 80)

query_structure = """
DESCRIBE prices_1m
"""
df_structure = conn.execute(query_structure).df()
print(df_structure.to_string())
print()

# 2. Analyser les données stockées
print("2️⃣ Analyse des données stockées (20.11.2025)")
print("-" * 80)

query_data = """
SELECT 
    datetime,
    datetime AT TIME ZONE 'UTC' as datetime_utc,
    datetime AT TIME ZONE 'Europe/Zurich' as datetime_bern,
    EXTRACT(HOUR FROM datetime AT TIME ZONE 'UTC') as hour_utc,
    EXTRACT(HOUR FROM datetime AT TIME ZONE 'Europe/Zurich') as hour_bern,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE DATE(datetime AT TIME ZONE 'UTC') = '2025-11-20'
  AND EXTRACT(HOUR FROM datetime AT TIME ZONE 'UTC') IN (13, 14)
  AND EXTRACT(MINUTE FROM datetime AT TIME ZONE 'UTC') = 29
ORDER BY datetime AT TIME ZONE 'UTC'
LIMIT 5
"""

df_data = conn.execute(query_data).df()
if not df_data.empty:
    print("Données dans prices_1m :")
    for idx, row in df_data.iterrows():
        print(f"   Stocké: {row['datetime']}")
        print(f"   → UTC: {row['datetime_utc']} (heure: {int(row['hour_utc'])})")
        print(f"   → Berne: {row['datetime_bern']} (heure: {int(row['hour_bern'])})")
        print(f"   Prix: O:{row['open']:.5f}")
        print()
else:
    print("   Aucune donnée trouvée")

# 3. Vérifier la vue prices_bern actuelle
print("3️⃣ Vue prices_bern actuelle")
print("-" * 80)

try:
    query_view = """
    SELECT sql FROM duckdb_views() WHERE view_name = 'prices_bern'
    """
    result_view = conn.execute(query_view).fetchone()
    if result_view:
        print("Définition actuelle :")
        print(result_view[0])
        print()
except:
    print("   Vue non trouvée ou erreur")

# 4. Tester la vue prices_bern
print("4️⃣ Test de la vue prices_bern")
print("-" * 80)

query_view_test = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_bern
WHERE DATE(datetime) = '2025-11-20'
  AND EXTRACT(HOUR FROM datetime) = 14
  AND EXTRACT(MINUTE FROM datetime) = 29
LIMIT 1
"""

df_view = conn.execute(query_view_test).df()
if not df_view.empty:
    row_view = df_view.iloc[0]
    print(f"Prix à 14:29 dans prices_bern :")
    print(f"   datetime: {row_view['datetime']}")
    print(f"   Prix: O:{row_view['open']:.5f} H:{row_view['high']:.5f} L:{row_view['low']:.5f} C:{row_view['close']:.5f}")
    print()
    
    # Comparer avec les données attendues
    query_expected = """
    SELECT 
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE DATE(datetime AT TIME ZONE 'UTC') = '2025-11-20'
      AND EXTRACT(HOUR FROM datetime AT TIME ZONE 'UTC') = 13
      AND EXTRACT(MINUTE FROM datetime AT TIME ZONE 'UTC') = 29
    LIMIT 1
    """
    
    df_expected = conn.execute(query_expected).df()
    if not df_expected.empty:
        expected = df_expected.iloc[0]
        print("Prix attendus (13:29 UTC = 14:29 Berne) :")
        print(f"   Prix: O:{expected['open']:.5f} H:{expected['high']:.5f} L:{expected['low']:.5f} C:{expected['close']:.5f}")
        print()
        
        if abs(row_view['open'] - expected['open']) < 0.00001:
            print("✅ CORRECT : Les prix correspondent")
        else:
            print("❌ INCORRECT : Décalage détecté")
            print(f"   Différence: {abs(row_view['open'] - expected['open']) * 10000:.2f} pips")

# 5. Conclusion
print()
print("5️⃣ CONCLUSION")
print("-" * 80)
print("Les données dans prices_1m sont stockées avec timezone +01:00")
print("Elles représentent l'heure UTC (13:29 UTC = 14:29 Berne en novembre)")
print("La vue prices_bern doit convertir correctement : UTC → Europe/Zurich")
print()

conn.close()

print("=" * 80)
print("✅ DIAGNOSTIC TERMINÉ")
print("=" * 80)


