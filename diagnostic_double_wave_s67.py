"""
DIAGNOSTIC DOUBLE WAVE - Pourquoi pas détecté sur 11 septembre ?
==================================================================
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter chemins
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path
from double_wave import detect_double_wave_conditions
import duckdb

# Date référence
target_date = '2025-09-11'

print("="*80)
print("DIAGNOSTIC DOUBLE WAVE - 11 SEPTEMBRE 2025")
print("="*80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# Charger TOUS les événements du jour
query = f"""
    SELECT 
        event_title,
        ts_utc,
        actual,
        estimate,
        forecast,
        previous,
        importance_n,
        country
    FROM events
    WHERE DATE(ts_utc) = '{target_date}'
    AND actual IS NOT NULL
    ORDER BY ts_utc
"""

df = conn.execute(query).fetchdf()
print(f"\n✅ {len(df)} événements chargés pour {target_date}")

# Afficher tous les événements
print("\n" + "="*80)
print("LISTE COMPLÈTE DES ÉVÉNEMENTS")
print("="*80)

for idx, row in df.iterrows():
    print(f"\n{idx+1}. {row['event_title']}")
    print(f"   Timestamp: {row['ts_utc']}")
    print(f"   Actual: {row['actual']}")
    print(f"   Estimate: {row['estimate']}")
    print(f"   Forecast: {row['forecast']}")
    print(f"   Previous: {row['previous']}")
    print(f"   Importance: {row['importance_n']}")
    print(f"   Country: {row['country']}")
    
    # Calculer surprise
    ref = row['estimate'] or row['forecast'] or row['previous']
    if ref and ref != 0:
        surprise = abs(row['actual'] - ref) / abs(ref) * 100
        print(f"   Surprise: {surprise:.2f}%")

# Filtrer événements 14:30 (12:30 UTC) - L'heure du CPI US
print("\n" + "="*80)
print("ÉVÉNEMENTS À 14:30 BERNE (12:30 UTC)")
print("="*80)

df_1430 = df[df['ts_utc'].dt.hour == 12]
df_1430 = df_1430[df_1430['ts_utc'].dt.minute == 30]

print(f"\n✅ {len(df_1430)} événements à 14:30")

for idx, row in df_1430.iterrows():
    print(f"\n{idx+1}. {row['event_title']}")
    print(f"   Importance: {row['importance_n']}")
    ref = row['estimate'] or row['forecast'] or row['previous']
    if ref and ref != 0:
        surprise = abs(row['actual'] - ref) / abs(ref) * 100
        print(f"   Surprise: {surprise:.2f}%")

# Tester détection Double Wave
print("\n" + "="*80)
print("TEST DÉTECTION DOUBLE WAVE")
print("="*80)

events = df_1430.to_dict('records')

print(f"\nNombre événements: {len(events)}")

# Vérifier critères un par un
print("\n🔍 CRITÈRES DOUBLE WAVE:")

# Critère 1: Cluster ≥5
print(f"\n1. Cluster size ≥ 5 ?")
print(f"   Actuel: {len(events)}")
print(f"   Status: {'✅ OUI' if len(events) >= 5 else '❌ NON'}")

# Critère 2: Au moins un HIGH importance
has_high = any(e.get('importance_n') == 3 for e in events)
print(f"\n2. Au moins un HIGH importance ?")
print(f"   Status: {'✅ OUI' if has_high else '❌ NON'}")
if has_high:
    high_events = [e['event_title'] for e in events if e.get('importance_n') == 3]
    print(f"   Événements HIGH: {high_events}")

# Critère 3: Surprise ≥ 20%
max_surprise = 0.0
for event in events:
    actual = event.get('actual')
    if actual is None:
        continue
    ref = event.get('estimate') or event.get('forecast') or event.get('previous')
    if ref is None or ref == 0:
        continue
    surprise_pct = abs(actual - ref) / abs(ref) * 100
    max_surprise = max(max_surprise, surprise_pct)

print(f"\n3. Surprise max ≥ 20% ?")
print(f"   Actuel: {max_surprise:.2f}%")
print(f"   Status: {'✅ OUI' if max_surprise >= 20 else '❌ NON'}")

# Test final
is_double_wave = detect_double_wave_conditions(events)

print(f"\n" + "="*80)
print(f"RÉSULTAT FINAL: {'🌊 DOUBLE WAVE' if is_double_wave else '❌ SINGLE WAVE'}")
print("="*80)

if not is_double_wave:
    print("\n⚠️ PROBLÈME: Le cas de référence n'est PAS détecté comme Double Wave!")
    print("   Raisons possibles:")
    if len(events) < 5:
        print(f"   - Cluster trop petit ({len(events)} < 5)")
    if not has_high:
        print("   - Aucun événement HIGH importance")
    if max_surprise < 20:
        print(f"   - Surprise trop faible ({max_surprise:.2f}% < 20%)")
    print("\n   Il faut probablement:")
    print("   1. Filtrer uniquement les événements US/CPI à 14:30")
    print("   2. Ou ajuster les critères de détection")

conn.close()
