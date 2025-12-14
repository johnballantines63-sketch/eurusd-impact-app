#!/usr/bin/env python3
"""Debug LatencyAnalyzer pour comprendre pourquoi pas de données"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'fx_impact_app' / 'src'))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
import duckdb

# Tester avec Michigan_Inflation_Expectations
family = 'Michigan_Inflation_Expectations'
pattern = FAMILY_PATTERNS.get(family)

print(f"🔍 DEBUG LATENCY ANALYZER")
print(f"=" * 60)
print(f"Famille: {family}")
print(f"Pattern: {pattern}\n")

# 1. Vérifier events dans la DB avec le pattern
conn = duckdb.connect(get_db_path(), read_only=True)

print("📊 Test 1: Events matchant le pattern LIKE\n")
simple_pattern = "michigan%inflation%expectation%"
query = f"""
SELECT event_key, ts_utc, country
FROM events
WHERE LOWER(event_key) LIKE '{simple_pattern}'
LIMIT 5
"""
results = conn.execute(query).fetchall()
print(f"Résultats LIKE: {len(results)} events")
for r in results:
    print(f"  - {r[0]} | {r[1]} | {r[2]}")

conn.close()  # ✅ FERMER AVANT LatencyAnalyzer

print("\n" + "=" * 60)

# 2. Vérifier si LatencyAnalyzer utilise les bons paramètres
print("\n📊 Test 2: Appel LatencyAnalyzer\n")

analyzer = LatencyAnalyzer(get_db_path())

# Afficher les paramètres utilisés
print(f"Paramètres:")
print(f"  - family_pattern: {pattern}")
print(f"  - threshold_pips: 5.0")
print(f"  - min_events: 5")
print(f"  - lookback_days: {3 * 365}")

latency_stats = analyzer.calculate_family_latency_stats(
    family_pattern=pattern,
    threshold_pips=5.0,
    min_events=5,
    lookback_days=3 * 365
)

analyzer.close()

print(f"\nRésultat LatencyAnalyzer:")
if latency_stats:
    print(f"  ✅ Données trouvées")
    print(f"  - events_analyzed: {latency_stats.get('events_analyzed', 0)}")
    if 'initial_reaction' in latency_stats:
        print(f"  - median_minutes: {latency_stats['initial_reaction'].get('median_minutes', 'N/A')}")
else:
    print(f"  ❌ Aucune donnée")

print("\n" + "=" * 60)

# 3. Inspecter la méthode de LatencyAnalyzer
print("\n📊 Test 3: Méthodes disponibles dans LatencyAnalyzer\n")
print("Méthodes:")
for method in dir(analyzer):
    if not method.startswith('_'):
        print(f"  - {method}")
