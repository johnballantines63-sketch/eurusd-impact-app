#!/usr/bin/env python3
"""
DIAGNOSTIC CALENDRIER - Vérifier données chargées
==================================================

Vérifie que les événements futurs sont bien chargés avec toutes les colonnes.
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import config

print("="*80)
print("🔍 DIAGNOSTIC DONNÉES CALENDRIER")
print("="*80)

# Charger événements futurs (7 jours)
date_from = datetime.now()
date_to = datetime.now() + timedelta(days=7)

conn = duckdb.connect(str(config.DB_PATH), read_only=True)

query = f"""
SELECT 
    ts_utc, event_key, event_title, country, importance_n,
    actual, forecast, previous
FROM events 
WHERE ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M')}'
  AND ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M')}'
  AND country IN ('US', 'EU', 'GB')
ORDER BY ts_utc
LIMIT 10
"""

print(f"\n📅 Période: {date_from.strftime('%Y-%m-%d')} → {date_to.strftime('%Y-%m-%d')}\n")

results = conn.execute(query).fetchall()

print(f"✅ {len(results)} événements trouvés\n")

if len(results) > 0:
    print("📋 Premiers événements:\n")
    for row in results[:10]:
        ts, event_key, event_title, country, importance = row[:5]
        print(f"  • {ts} | {country} | IMP:{importance}")
        print(f"    event_key: {event_key}")
        print(f"    event_title: {event_title}")
        print()
else:
    print("⚠️ Aucun événement futur trouvé")

# Vérifier stats pré-chargées
print("\n" + "="*80)
print("📊 VÉRIFICATION STATS PRÉ-CHARGÉES")
print("="*80)

stats_query = """
SELECT 
    event_key, country, event_title, importance_n
FROM events 
WHERE event_key IS NOT NULL
  AND event_title IS NOT NULL
LIMIT 10
"""

stats_results = conn.execute(stats_query).fetchall()

print(f"\n✅ {len(stats_results)} événements avec event_key ET event_title\n")

for row in stats_results[:5]:
    print(f"  • {row[0]} | {row[1]} | {row[2]} | IMP:{row[3]}")

conn.close()

print("\n" + "="*80)
print("FIN DIAGNOSTIC")
print("="*80)
