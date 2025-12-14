"""
MISE À JOUR validation_events avec nouvelles stats TTR/Latency

Objectif : Mettre à jour les 11 événements du 11 sept avec les nouvelles valeurs
"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path

print("=" * 80)
print("💾 MISE À JOUR validation_events avec nouvelles stats")
print("=" * 80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# Nouvelles valeurs calculées
new_stats = {
    'CPI': {'latency_median': 120.0, 'ttr_median': 1134.0},
    'Jobless_Claims': {'latency_median': 60.0, 'ttr_median': 1194.0},
    'Current_Account': {'latency_median': 180.0, 'ttr_median': 1194.0},
    'Interest_Rate_Decision': {'latency_median': 180.0, 'ttr_median': 1122.0}
}

print("\n📊 Mise à jour validation_events...")
print("-" * 80)

for family, stats in new_stats.items():
    latency = stats['latency_median']
    ttr = stats['ttr_median']
    
    update_query = f"""
    UPDATE validation_events
    SET latency_median = {latency},
        ttr_median = {ttr}
    WHERE family = '{family}'
    """
    
    result = conn.execute(update_query)
    count = result.fetchone()
    
    print(f"\n✅ {family}")
    print(f"   Latency : {latency:.0f} sec ({latency/60:.1f} min)")
    print(f"   TTR     : {ttr:.0f} sec ({ttr/60:.1f} min)")

# Vérifier
print("\n\n" + "=" * 80)
print("✅ VÉRIFICATION validation_events")
print("=" * 80)

query = """
SELECT 
    family,
    event_key,
    latency_median,
    ttr_median
FROM validation_events
WHERE event_date = '2025-09-11'
ORDER BY family, event_key
LIMIT 11
"""

results = conn.execute(query).fetchall()

for row in results:
    fam, key, lat, ttr = row
    print(f"\n{key[:40]:<40} ({fam})")
    print(f"   Latency : {lat:.0f}s ({lat/60:.1f}min)   TTR : {ttr:.0f}s ({ttr/60:.1f}min)")

conn.close()

print("\n\n" + "=" * 80)
print("✅ MISE À JOUR TERMINÉE")
print("=" * 80)
print("\n💡 Maintenant : Re-tester avec validate_ttr_11sept_FIXED.py")
