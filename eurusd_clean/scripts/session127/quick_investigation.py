import duckdb
import pandas as pd

# Connexion DB
db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
conn = duckdb.connect(db_path, read_only=True)

# Charger tous event_key US uniques
query = """
SELECT DISTINCT 
    event_key, 
    importance_n,
    COUNT(*) as event_count
FROM events
WHERE country = 'US'
GROUP BY event_key, importance_n
ORDER BY event_count DESC
"""

df = conn.execute(query).df()

print("=" * 80)
print("INVESTIGATION SCORES MANQUANTS - FOCUS HIGH")
print("=" * 80)
print()

# Scores HIGH à chercher
high_scores = [
    ('u_6_unemployment_rate', 63.96),
    ('gross_domestic_product', 39.70),
]

results = {}

for event_name, score in high_scores:
    print(f"Recherche : {event_name} (score={score:.2f})")
    print("-" * 80)
    
    # Recherche par mots-clés
    keywords = event_name.lower().replace('_', ' ').split()
    
    matches = []
    for keyword in keywords:
        if len(keyword) > 2:  # Ignorer mots courts
            mask = df['event_key'].str.lower().str.contains(keyword, na=False)
            found = df[mask]
            if not found.empty:
                matches.append(found)
    
    if matches:
        # Combiner et dédupliquer
        combined = pd.concat(matches).drop_duplicates()
        print(f"✅ {len(combined)} correspondances trouvées :\n")
        
        # Afficher top 5
        for idx, row in combined.head(10).iterrows():
            imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
            print(f"  → {row['event_key']}")
            print(f"     Importance: {imp}, Count: {row['event_count']}")
        
        results[event_name] = combined.to_dict('records')
    else:
        print("❌ Aucune correspondance trouvée")
        results[event_name] = None
    
    print()

conn.close()

# Export résultats
import json
output_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session127/investigation_results_high.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print(f"✅ Résultats sauvegardés : investigation_results_high.json")
print("=" * 80)
