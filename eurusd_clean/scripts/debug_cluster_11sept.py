#!/usr/bin/env python3
"""
DEBUG: Pourquoi le cluster du 11.09.2025 à 14h30 n'apparaît pas ?
==================================================================
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import config
from core.event_utils import normalize_event_keys_list

def build_cluster_signature(event_keys: list):
    """Construit la signature normalisée d'un cluster"""
    if not event_keys:
        return ""
    normalized = normalize_event_keys_list(event_keys, method='with_variants')
    return '|'.join(sorted(set(normalized)))

DB_PATH = config.DB_PATH
CACHE_CLUSTERS_PATH = PROJECT_ROOT / "data" / "cache_clusters.csv"

# Date cible
TARGET_DATE = datetime(2025, 9, 11)
TARGET_TIME = "14:30"  # Heure de Berne

print(f"🔍 Investigation cluster {TARGET_DATE.strftime('%Y-%m-%d')} à {TARGET_TIME}")
print("=" * 80)

# 1. Charger le cache
print("\n1️⃣ Chargement du cache...")
if not CACHE_CLUSTERS_PATH.exists():
    print(f"❌ Cache non trouvé : {CACHE_CLUSTERS_PATH}")
    sys.exit(1)

df_cache = pd.read_csv(CACHE_CLUSTERS_PATH)
print(f"✅ Cache chargé : {len(df_cache)} clusters")

# 2. Charger événements du 11.09.2025
print(f"\n2️⃣ Chargement événements du {TARGET_DATE.strftime('%Y-%m-%d')}...")
conn = duckdb.connect(str(DB_PATH), read_only=True)

query = """
SELECT 
    e.ts_utc,
    e.country,
    e.event_title,
    e.event_key,
    e.importance_n,
    e.actual,
    e.estimate,
    e.previous
FROM events e
WHERE DATE(e.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich') = ?
  AND e.importance_n <= 2
  AND e.country IN ('US', 'DE', 'EU')
ORDER BY e.ts_utc
"""

df_events = conn.execute(query, [TARGET_DATE.strftime('%Y-%m-%d')]).df()
conn.close()

if df_events.empty:
    print("❌ Aucun événement trouvé pour cette date")
    sys.exit(1)

# Convertir timezone
df_events['ts_bern'] = pd.to_datetime(df_events['ts_utc']).dt.tz_convert('Europe/Zurich')
df_events['time_bern'] = df_events['ts_bern'].dt.strftime('%H:%M')

print(f"✅ {len(df_events)} événement(s) trouvé(s)")

# Afficher événements autour de 14h30
print(f"\n📋 Événements autour de {TARGET_TIME}:")
events_around = df_events[
    (df_events['time_bern'] >= '14:25') & 
    (df_events['time_bern'] <= '14:50')
].copy()

if events_around.empty:
    print("❌ Aucun événement trouvé autour de 14h30")
    print("\n📋 Tous les événements du jour:")
    for idx, row in df_events.iterrows():
        print(f"  {row['time_bern']} | {row['country']} | {row['event_title']} | {row['event_key']}")
else:
    print(f"✅ {len(events_around)} événement(s) trouvé(s) autour de 14h30")
    for idx, row in events_around.iterrows():
        print(f"  {row['time_bern']} | {row['country']} | {row['event_title']} | {row['event_key']}")

# 3. Construire cluster pour 14h30 (fenêtre 30 min)
print(f"\n3️⃣ Construction du cluster à {TARGET_TIME} (fenêtre 30 min)...")
target_time_dt = pd.Timestamp(f"{TARGET_DATE.strftime('%Y-%m-%d')} {TARGET_TIME}", tz='Europe/Zurich')
window_start = target_time_dt - pd.Timedelta(minutes=15)
window_end = target_time_dt + pd.Timedelta(minutes=30)

mask = (df_events['ts_bern'] >= window_start) & (df_events['ts_bern'] <= window_end)
events_cluster = df_events[mask].copy()

# Exclure événements ECB (press conference, etc.)
print(f"\n3️⃣b Exclure événements ECB...")
def is_event_without_actual(event_key: str, event_title: str) -> bool:
    """Identifie événements sans actual (press conferences, etc.)"""
    title_lower = str(event_title).lower()
    key_lower = str(event_key).lower()
    keywords = ['press conference', 'conference', 'speech', 'testimony', 'hearing', 'meeting', 'minutes', 'statement']
    return any(keyword in title_lower or keyword in key_lower for keyword in keywords)

mask_no_ecb = events_cluster.apply(
    lambda row: not is_event_without_actual(row['event_key'], row['event_title']),
    axis=1
)
events_cluster_no_ecb = events_cluster[mask_no_ecb].copy()
print(f"   Avant exclusion ECB: {len(events_cluster)} événements")
print(f"   Après exclusion ECB: {len(events_cluster_no_ecb)} événements")

# Tester les deux versions
for name, events_df in [("avec ECB", events_cluster), ("sans ECB", events_cluster_no_ecb)]:
    print(f"\n   Version {name}:")
    if events_df.empty:
        print("   ❌ Aucun événement")
        continue
    
    event_keys = events_df['event_key'].dropna().tolist()
    print(f"   Event keys ({len(event_keys)}): {event_keys[:5]}...")  # Afficher les 5 premiers
    
    signature = build_cluster_signature(event_keys)
    print(f"   Signature: {signature[:100]}...")  # Afficher les 100 premiers caractères
    
    # Chercher dans cache
    normalized_keys = normalize_event_keys_list(event_keys, method='with_variants')
    signature_normalized = '|'.join(sorted(set(normalized_keys)))
    
    matches = []
    for idx, row in df_cache.iterrows():
        cache_sig = str(row.get('cluster_signature', ''))
        if pd.isna(cache_sig) or cache_sig == '':
            continue
        
        cache_keys = cache_sig.split('|')
        cache_normalized = normalize_event_keys_list(cache_keys, method='with_variants')
        cache_signature_normalized = '|'.join(sorted(set(cache_normalized)))
        
        if signature_normalized == cache_signature_normalized:
            matches.append({
                'type': 'EXACT',
                'cache_signature': cache_sig,
                'impact_median': row.get('impact_median'),
                'n_samples': row.get('n_samples'),
            })
        else:
            current_set = set(normalized_keys)
            cache_set = set(cache_normalized)
            intersection = current_set & cache_set
            if len(intersection) > 0:
                jaccard = len(intersection) / len(current_set | cache_set)
                if jaccard >= 0.8:
                    matches.append({
                        'type': 'PARTIAL',
                        'jaccard': jaccard,
                        'cache_signature': cache_sig,
                        'impact_median': row.get('impact_median'),
                        'n_samples': row.get('n_samples'),
                    })
    
    if matches:
        print(f"   ✅ {len(matches)} match(s) trouvé(s)")
        for match in matches[:3]:  # Afficher les 3 premiers
            print(f"      - {match['type']}: Impact={match['impact_median']} pips, Occ={match['n_samples']}")
    else:
        print(f"   ❌ Aucun match")

# 4. Vérifier filtres pour les matches trouvés
print(f"\n4️⃣ Vérification des filtres...")
if events_cluster_no_ecb.empty:
    print("❌ Aucun événement dans le cluster (après exclusion ECB)")
else:
    # Chercher matches pour la version sans ECB
    event_keys = events_cluster_no_ecb['event_key'].dropna().tolist()
    normalized_keys = normalize_event_keys_list(event_keys, method='with_variants')
    signature_normalized = '|'.join(sorted(set(normalized_keys)))
    
    matches = []
    for idx, row in df_cache.iterrows():
        cache_sig = str(row.get('cluster_signature', ''))
        if pd.isna(cache_sig) or cache_sig == '':
            continue
        
        cache_keys = cache_sig.split('|')
        cache_normalized = normalize_event_keys_list(cache_keys, method='with_variants')
        cache_signature_normalized = '|'.join(sorted(set(cache_normalized)))
        
        if signature_normalized == cache_signature_normalized:
            matches.append({
                'type': 'EXACT',
                'cache_signature': cache_sig,
                'impact_median': row.get('impact_median'),
                'n_samples': row.get('n_samples'),
                'dominant_pattern': row.get('dominant_pattern'),
            })
        else:
            current_set = set(normalized_keys)
            cache_set = set(cache_normalized)
            intersection = current_set & cache_set
            if len(intersection) > 0:
                jaccard = len(intersection) / len(current_set | cache_set)
                if jaccard >= 0.8:
                    matches.append({
                        'type': 'PARTIAL',
                        'jaccard': jaccard,
                        'cache_signature': cache_sig,
                        'impact_median': row.get('impact_median'),
                        'n_samples': row.get('n_samples'),
                        'dominant_pattern': row.get('dominant_pattern'),
                    })
    
    if matches:
        print(f"✅ {len(matches)} match(s) trouvé(s) dans le cache (version sans ECB):")
        for match in matches:
            impact_med = match.get('impact_median', 0)
            n_samples = match.get('n_samples', 0)
            print(f"   - {match['type']}: Impact={impact_med:.1f} pips, Occurrences={n_samples}, Pattern={match.get('dominant_pattern', 'N/A')}")
            if 'jaccard' in match:
                print(f"     Jaccard: {match['jaccard']:.2%}")
            print(f"     Filtre impact min=30: {'✅ PASS' if impact_med >= 30 else '❌ FILTRÉ'}")
            print(f"     Filtre occurrences min=3: {'✅ PASS' if n_samples >= 3 else '❌ FILTRÉ'}")
    else:
        print("❌ Aucun match trouvé dans le cache (version sans ECB)")
        print("\n💡 Raisons possibles:")
        print("   - Le cluster n'existe pas dans le cache (cache_refresh.py pas exécuté)")
        print("   - La signature ne correspond pas (normalisation différente)")
        print("   - Les événements ne sont pas les mêmes")

print("\n" + "=" * 80)
print("✅ Investigation terminée")

