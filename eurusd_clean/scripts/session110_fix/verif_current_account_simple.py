"""
VÉRIFICATION RAPIDE - Current Account 11.09.2025
"""

import duckdb
import sys
from pathlib import Path

# Ajouter chemin
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fx_impact_app" / "src"))
from config import get_db_path

conn = duckdb.connect(get_db_path(), read_only=True)

print("=" * 80)
print("TOUS ÉVÉNEMENTS 11.09.2025 ENTRE 13:00 ET 15:00 UTC")
print("=" * 80)

query = """
SELECT 
    ts_utc,
    event_key,
    country,
    actual,
    estimate,
    importance_n
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND TIME(ts_utc) BETWEEN '13:00:00' AND '15:00:00'
ORDER BY ts_utc, country
"""

results = conn.execute(query).fetchdf()

print(f"\n✅ {len(results)} événement(s) trouvé(s) :\n")

for _, row in results.iterrows():
    surprise = ""
    if row['actual'] and row['estimate'] and row['estimate'] != 0:
        surprise_pct = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
        surprise = f" | Surprise: {surprise_pct:.1f}%"
    
    print(f"{row['ts_utc']} | {row['country']:3s} | {row['event_key'][:60]}{surprise}")

# Chercher spécifiquement Current Account
print("\n" + "=" * 80)
print("RECHERCHE SPÉCIFIQUE 'CURRENT' OU 'ACCOUNT'")
print("=" * 80)

query2 = """
SELECT 
    ts_utc,
    event_key,
    country,
    actual,
    estimate
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND (LOWER(event_key) LIKE '%current%' OR LOWER(event_key) LIKE '%account%')
ORDER BY ts_utc
"""

results2 = conn.execute(query2).fetchdf()

if results2.empty:
    print("\n❌ AUCUN événement contenant 'current' ou 'account' trouvé")
else:
    print(f"\n✅ {len(results2)} événement(s) trouvé(s) :\n")
    for _, row in results2.iterrows():
        print(f"{row['ts_utc']} | {row['country']} | {row['event_key']}")
        print(f"  Actual: {row['actual']} | Estimate: {row['estimate']}")

conn.close()
