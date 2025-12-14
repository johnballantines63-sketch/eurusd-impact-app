import duckdb
import pandas as pd

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# 1. Vérifier les event_key dans events pour le 11/09
query_events = """
SELECT DISTINCT event_key, country
FROM events 
WHERE ts_utc >= '2025-09-11'
  AND event_key LIKE '%ecb%'
"""
print("=== Events dans la table events ===")
events = conn.execute(query_events).fetchdf()
print(events)

# 2. Vérifier les event_key dans event_families
query_families = """
SELECT event_key, country, empirical_score
FROM event_families
WHERE event_key LIKE '%ecb%'
  AND empirical_score IS NOT NULL
"""
print("\n=== Event_families avec scores ===")
families = conn.execute(query_families).fetchdf()
print(families)

# 3. Test du mapping exact
print("\n=== Test de correspondance ===")
for _, ev in events.iterrows():
    print(f"\nCherche: ('{ev['event_key']}', '{ev['country']}')")
    
    # Exact match
    query_match = f"""
    SELECT event_key, country, empirical_score
    FROM event_families
    WHERE event_key = '{ev['event_key']}'
      AND country = '{ev['country']}'
    """
    match = conn.execute(query_match).fetchdf()
    
    if len(match) > 0:
        print(f"  ✅ Trouvé: Score = {match.iloc[0]['empirical_score']}")
    else:
        print(f"  ❌ PAS TROUVÉ avec country={ev['country']}")
        
        # Essayer variante
        alt_country = 'EA' if ev['country'] == 'EU' else 'EU'
        query_alt = f"""
        SELECT event_key, country, empirical_score
        FROM event_families
        WHERE event_key = '{ev['event_key']}'
          AND country = '{alt_country}'
        """
        match_alt = conn.execute(query_alt).fetchdf()
        
        if len(match_alt) > 0:
            print(f"  ⚠️ Trouvé avec country={alt_country}: Score = {match_alt.iloc[0]['empirical_score']}")
        else:
            print(f"  ❌ Aucune correspondance trouvée")

conn.close()
