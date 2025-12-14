"""
DEBUG - INSPECTION TABLE PRICES_1M
==================================

Vérifie la structure et les données réelles de prices_1m
pour comprendre le problème de timezone/colonne
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).resolve().parents[3]
DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

print("="*80)
print("🔍 INSPECTION TABLE PRICES_1M")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Structure de la table
print("\n📊 STRUCTURE TABLE prices_1m:")
structure = conn.execute("DESCRIBE prices_1m").fetchdf()
print(structure.to_string())

# 2. Colonnes disponibles
print("\n📋 COLONNES DISPONIBLES:")
columns = conn.execute("SELECT * FROM prices_1m LIMIT 1").fetchdf().columns.tolist()
print(f"   {columns}")

# 3. Échantillon de données autour du 11 septembre 14:30
print("\n📅 DONNÉES 11 SEPTEMBRE 2025 (14:25-14:35):")
query = """
SELECT *
FROM prices_1m
WHERE datetime >= '2025-09-11 14:25:00'
  AND datetime <= '2025-09-11 14:35:00'
ORDER BY datetime
"""
df = conn.execute(query).fetchdf()
print(df.to_string())

# 4. Vérifier si la colonne s'appelle 'timestamp' au lieu de 'datetime'
print("\n🔍 TEST AUTRES NOMS DE COLONNES:")
try:
    test_ts = conn.execute("SELECT timestamp FROM prices_1m LIMIT 1").fetchdf()
    print("   ✅ Colonne 'timestamp' existe aussi !")
    print(f"   Type: {test_ts['timestamp'].dtype}")
except:
    print("   ❌ Pas de colonne 'timestamp'")

# 5. Peak réel sur 11 septembre
print("\n📈 RECHERCHE PEAK 11 SEPTEMBRE (14:30-16:30):")
query_peak = """
SELECT datetime, high, low, close
FROM prices_1m
WHERE datetime >= '2025-09-11 14:30:00'
  AND datetime <= '2025-09-11 16:30:00'
ORDER BY high DESC
LIMIT 10
"""
df_peak = conn.execute(query_peak).fetchdf()
print(df_peak.to_string())

# 6. Prix à 14:30 exact
print("\n📊 PRIX À 14:30:00 (événement):")
query_event = """
SELECT *
FROM prices_1m
WHERE datetime >= '2025-09-11 14:30:00'
LIMIT 1
"""
df_event = conn.execute(query_event).fetchdf()
print(df_event.to_string())

conn.close()

print("\n" + "="*80)
print("✅ INSPECTION TERMINÉE")
print("="*80)
