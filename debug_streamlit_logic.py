import duckdb
import pandas as pd
from datetime import datetime

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# 1. Charger le cache (comme Streamlit)
print("=== 1. Chargement cache ===")
query = """
    SELECT 
        event_key, country, family,
        empirical_score, empirical_impact, 
        avg_movement_pips, reaction_rate, avg_latency_min,
        latency_median, latency_p20, latency_p80,
        ttr_median, ttr_p20, ttr_p80, 
        mfe_p80, n_events_latency
    FROM event_families 
    WHERE empirical_score IS NOT NULL
"""
results = conn.execute(query).fetchall()

precomputed_stats = {}
for row in results:
    key = (row[0], row[1])  # (event_key, country)
    precomputed_stats[key] = {
        'family': row[2],
        'empirical_score': row[3],
        'empirical_impact': row[4],
        'avg_movement_pips': row[5],
        'reaction_rate': row[6],
        'avg_latency_min': row[7],
    }

print(f"✅ {len(precomputed_stats)} familles en cache\n")

# 2. Charger événements futurs (comme get_future_events)
print("=== 2. Chargement événements futurs ===")
query_events = """
SELECT 
    e.ts_utc, e.event_key, e.country, e.importance_n,
    e.actual, e.forecast, e.previous
FROM events e
WHERE e.ts_utc >= '2025-09-11 00:00'
  AND e.ts_utc <= '2025-09-11 23:59'
  AND e.country IN ('US', 'EU')
ORDER BY e.ts_utc
"""

df = conn.execute(query_events).fetchdf()
print(f"✅ {len(df)} événements trouvés\n")

# 3. Simuler l'enrichissement (comme dans la boucle for)
print("=== 3. Test enrichissement ===")
for idx, event in df.iterrows():
    event_key = event['event_key']
    country = event['country']
    
    print(f"\n--- Event #{idx+1} ---")
    print(f"Event: {event_key}")
    print(f"Country: {country}")
    
    # EXACTEMENT comme dans le code Streamlit
    stats = precomputed_stats.get((event_key, country), {})
    if not stats:
        if country == 'EU':
            stats = precomputed_stats.get((event_key, 'EA'), {})
        elif country == 'EA':
            stats = precomputed_stats.get((event_key, 'EU'), {})
    
    has_empirical = stats.get('empirical_score') is not None
    
    print(f"Stats trouvés: {bool(stats)}")
    print(f"has_empirical: {has_empirical}")
    
    if has_empirical:
        score = stats['empirical_score']
        print(f"✅ SCORE: {score}")
    else:
        print(f"❌ PAS DE SCORE (stats={stats})")
    
    if idx >= 9:  # Limiter à 10 premiers
        break

conn.close()
