"""
Debug : Pourquoi le 11.09.2025 n'est pas trouvé dans la recherche de clusters
============================================================================
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from core.event_utils import normalize_event_key_with_variants

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔍 DEBUG : RECHERCHE CLUSTER 11.09.2025")
print("=" * 80)
print()

# 1. Charger le cache
print("1️⃣ Chargement du cache...")
print("-" * 80)
df_cache = pd.read_csv(PROJECT_ROOT / 'data' / 'cache_clusters.csv')
print(f"   ✅ {len(df_cache)} clusters dans le cache")
print()

# 2. Chercher le cluster du 11.09 dans le cache
print("2️⃣ Recherche du cluster 11.09 dans le cache...")
print("-" * 80)

# Charger les événements du 11.09 pour construire la signature
import duckdb
conn = duckdb.connect(str(DB_PATH), read_only=True)

target_date = datetime(2025, 9, 11)
date_start = target_date.replace(hour=12, minute=0, second=0)
date_end = target_date.replace(hour=16, minute=0, second=0)

query = """
SELECT 
    e.datetime_utc as ts_utc,
    e.event_name as event_key,
    e.country,
    e.actual,
    e.forecast as estimate
FROM economic_events e
WHERE e.datetime_utc >= ? AND e.datetime_utc <= ?
  AND e.actual IS NOT NULL
  AND e.forecast IS NOT NULL
  AND e.forecast != 0
  AND e.country IN ('US', 'DE', 'EU')
  AND e.event_name NOT LIKE '%conference%'
  AND e.event_name NOT LIKE '%speech%'
  AND e.event_name NOT LIKE '%statement%'
  AND e.event_name NOT LIKE '%meeting%'
  AND e.event_name NOT LIKE '%minutes%'
ORDER BY e.datetime_utc
"""

df_events_11sept = conn.execute(query, [date_start, date_end]).df()
print(f"   ✅ {len(df_events_11sept)} événements trouvés pour 11.09.2025")
print()

# Filtrer autour de 14h30 (heure de Berne)
df_events_11sept['ts_bern'] = pd.to_datetime(df_events_11sept['ts_utc']).dt.tz_localize('UTC').dt.tz_convert('Europe/Zurich')
df_events_11sept = df_events_11sept[
    (df_events_11sept['ts_bern'].dt.hour == 14) & 
    (df_events_11sept['ts_bern'].dt.minute >= 30) &
    (df_events_11sept['ts_bern'].dt.minute <= 45)
]

print(f"   ✅ {len(df_events_11sept)} événements autour de 14h30-14h45")
print()

# Construire la signature
event_keys = df_events_11sept['event_key'].tolist()
normalized_keys = [normalize_event_key_with_variants(k) for k in event_keys]
signature = '|'.join(sorted(set(normalized_keys)))

print(f"   Signature du cluster 11.09 :")
print(f"   {signature[:100]}...")
print()

# Chercher dans le cache
matches = []
for idx, row in df_cache.iterrows():
    cache_sig = row.get('cluster_signature', '')
    # Gérer les valeurs NaN
    if pd.isna(cache_sig) or not isinstance(cache_sig, str) or not cache_sig:
        continue
    cache_normalized = '|'.join(sorted(set([normalize_event_key_with_variants(k) for k in cache_sig.split('|')])))
    
    # Calculer Jaccard
    sig_set = set(normalized_keys)
    cache_set = set(cache_normalized.split('|'))
    intersection = sig_set & cache_set
    union = sig_set | cache_set
    
    if len(union) > 0:
        jaccard = len(intersection) / len(union)
        # Garder tous les matches pour analyse, même si Jaccard < 0.7
        matches.append({
            'jaccard': jaccard,
            'impact_median': row.get('impact_median', 0),
            'n_samples': row.get('n_samples', 0),
            'num_events_median': row.get('num_events_median', 0),
            'signature': cache_sig[:100],
            'cache_normalized': cache_normalized[:100]
        })

matches_above_threshold = [m for m in matches if m['jaccard'] >= 0.7]
print(f"   ✅ {len(matches_above_threshold)} clusters similaires trouvés (Jaccard >= 0.7)")
print(f"   📊 {len(matches)} clusters au total analysés")
print()

if matches:
    print("   Top 5 matches (tous Jaccard) :")
    matches_sorted = sorted(matches, key=lambda x: x['jaccard'], reverse=True)[:5]
    for i, match in enumerate(matches_sorted, 1):
        print(f"   {i}. Jaccard: {match['jaccard']:.3f}, Impact: {match['impact_median']:.1f} pips, "
              f"Occurrences: {match['n_samples']}, Events: {match['num_events_median']:.0f}")
        print(f"      Cache signature: {match['signature']}...")
        print(f"      Cache normalized: {match['cache_normalized']}...")
    print()
    
    print(f"   Signature recherchée (11.09) :")
    print(f"   {signature[:150]}...")
    print()
    
    # Vérifier les filtres
    print("3️⃣ Vérification des filtres...")
    print("-" * 80)
    
    best_match = matches_sorted[0]
    print(f"   Meilleur match :")
    print(f"   → Jaccard : {best_match['jaccard']:.3f} (>= 0.7 ✅)")
    print(f"   → Impact médian : {best_match['impact_median']:.1f} pips")
    print(f"   → Occurrences : {best_match['n_samples']}")
    print(f"   → Nombre d'événements : {best_match['num_events_median']:.0f}")
    print()
    
    print("   Filtres appliqués (par défaut) :")
    print(f"   → Impact médian min : 30 pips")
    print(f"      {'✅ PASS' if best_match['impact_median'] >= 30 else '❌ FAIL'}")
    print(f"   → Occurrences min : 1")
    print(f"      {'✅ PASS' if best_match['n_samples'] >= 1 else '❌ FAIL'}")
    print(f"   → Événements min : 7")
    print(f"      {'✅ PASS' if best_match['num_events_median'] >= 7 else '❌ FAIL'}")
    print()
else:
    print("   ❌ Aucun cluster similaire trouvé")
    print()
    print("   Vérification de la signature...")
    print(f"   Événements du 11.09 :")
    for idx, row in df_events_11sept.head(10).iterrows():
        print(f"   - {row['event_key']} ({row['country']}) à {row['ts_bern'].strftime('%H:%M')}")

conn.close()

print()
print("=" * 80)
print("💡 CONCLUSION")
print("=" * 80)
print()
if matches:
    best = matches_sorted[0]
    if best['impact_median'] < 30:
        print("   ⚠️  Le cluster est trouvé mais FILTRÉ par 'Impact médian min' (30 pips)")
    elif best['num_events_median'] < 7:
        print("   ⚠️  Le cluster est trouvé mais FILTRÉ par 'Événements min' (7)")
    else:
        print("   ✅ Le cluster devrait être trouvé. Vérifier la logique de search_future_clusters")
else:
    print("   ⚠️  Le cluster n'est pas trouvé dans le cache (Jaccard < 0.7)")
    print("   → Vérifier la normalisation des event_keys")
    print("   → Vérifier que le cluster existe bien dans le cache")
print()

