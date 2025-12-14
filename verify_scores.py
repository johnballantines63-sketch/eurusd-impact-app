"""
Script pour vérifier si les scores empiriques sont bien dans la base de données
et sont correctement chargés
"""

import duckdb
from pathlib import Path
import sys

# Ajouter le path pour config
sys.path.insert(0, str(Path(__file__).parent / 'fx_impact_app' / 'src'))

from config import get_db_path

print("🔍 Vérification des scores empiriques\n")
print("=" * 80)

# Connexion DB
db_path = get_db_path()
print(f"📂 Base de données: {db_path}")

conn = duckdb.connect(str(db_path), read_only=False)

# 1. Vérifier les événements du 11 septembre 2025
print("\n1️⃣ Événements du 11 septembre 2025 dans la table 'events':")
print("-" * 80)

query_events = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.country,
    e.importance_n,
    ef.family,
    ef.empirical_score,
    ef.empirical_impact
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND e.country IN ('US', 'DE', 'EU', 'EA')
ORDER BY e.ts_utc
"""

events = conn.execute(query_events).fetchdf()

if len(events) > 0:
    print(f"✅ {len(events)} événements trouvés\n")
    
    for _, event in events.iterrows():
        score = event['empirical_score']
        score_str = f"{score:.0f}/100" if score and score > 0 else "N/A"
        
        print(f"  {event['ts_utc'].strftime('%H:%M')} - {event['event_key']} ({event['country']})")
        print(f"    Family: {event['family']}")
        print(f"    Score: {score_str}")
        print(f"    Impact: {event.get('empirical_impact', 'N/A')}")
        print()
else:
    print("❌ Aucun événement trouvé pour cette date")

# 2. Vérifier les scores dans event_families pour ces événements
print("\n2️⃣ Scores dans event_families pour CPI, Jobless, Current Account:")
print("-" * 80)

query_scores = """
SELECT 
    event_key,
    country,
    family,
    empirical_score,
    empirical_impact,
    avg_movement_pips,
    reaction_rate
FROM event_families
WHERE (
    event_key LIKE '%cpi%' 
    OR event_key LIKE '%jobless%' 
    OR event_key LIKE '%current%account%'
    OR family LIKE '%CPI%'
    OR family LIKE '%Jobless%'
    OR family LIKE '%Current%'
)
AND empirical_score IS NOT NULL
ORDER BY empirical_score DESC
"""

scores = conn.execute(query_scores).fetchdf()

if len(scores) > 0:
    print(f"✅ {len(scores)} entrées trouvées\n")
    
    for _, row in scores.iterrows():
        print(f"  {row['event_key']} ({row['country']})")
        print(f"    Family: {row['family']}")
        print(f"    Score: {row['empirical_score']:.0f}/100")
        print(f"    Impact: {row['empirical_impact']}")
        print(f"    Avg Movement: {row['avg_movement_pips']:.1f} pips")
        print(f"    Reaction Rate: {row['reaction_rate']:.0%}")
        print()
else:
    print("❌ Aucun score trouvé")

# 3. Statistiques globales
print("\n3️⃣ Statistiques globales event_families:")
print("-" * 80)

stats_query = """
SELECT 
    COUNT(*) as total_families,
    SUM(CASE WHEN empirical_score IS NOT NULL THEN 1 ELSE 0 END) as with_score,
    AVG(empirical_score) as avg_score,
    MIN(empirical_score) as min_score,
    MAX(empirical_score) as max_score
FROM event_families
"""

stats = conn.execute(stats_query).fetchone()

print(f"  Total families: {stats[0]}")
print(f"  Avec score: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
print(f"  Score moyen: {stats[2]:.1f}/100")
print(f"  Score min: {stats[3]:.0f}/100")
print(f"  Score max: {stats[4]:.0f}/100")

conn.close()

print("\n" + "=" * 80)
print("✅ Analyse terminée")
print("=" * 80)
