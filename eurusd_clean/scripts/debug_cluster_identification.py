#!/usr/bin/env python3
"""
Debug Identification Cluster
==============================
Analyse pourquoi identify_cluster_from_date ne trouve pas le cluster
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'pages'))

import config

# Importer les fonctions
from Planificateur_V3_CLEAN import (
    load_events_for_date,
    build_cluster_signature,
    find_cluster_in_cache,
    normalize_event_keys_list
)

DB_PATH = config.DB_PATH
test_date = datetime(2025, 11, 20)

print("=" * 80)
print("DEBUG IDENTIFICATION CLUSTER - 20.11.2025")
print("=" * 80)
print()

# 1. Charger les événements
print("1️⃣ Chargement des événements...")
print("-" * 80)

df_events = load_events_for_date(
    test_date,
    DB_PATH,
    "Europe/Zurich",
    min_importance=3,  # Inclure tous les événements (High, Medium, Low)
    countries=None,
    exclude_no_actual=False
)

if df_events.empty:
    print("   ❌ Aucun événement trouvé")
    sys.exit(1)

print(f"   ✅ {len(df_events)} événements chargés")
print()

# 2. Filtrer les événements US à 14:30
print("2️⃣ Filtrage événements US à 14:30...")
print("-" * 80)

df_us_events = df_events[df_events['country'] == 'US'].copy()
df_us_1430 = df_us_events[
    (df_us_events['ts_bern'].dt.hour == 14) &
    (df_us_events['ts_bern'].dt.minute == 30)
].copy()

if df_us_1430.empty:
    print("   ❌ Aucun événement US à 14:30")
    sys.exit(1)

print(f"   ✅ {len(df_us_1430)} événements US à 14:30")
print()

# 3. Construire la signature
print("3️⃣ Construction de la signature ADN...")
print("-" * 80)

event_keys = df_us_1430['event_key'].dropna().tolist()
signature = build_cluster_signature(event_keys)

print(f"   Nombre d'événements : {len(event_keys)}")
print(f"   Signature : {signature[:200]}...")
print(f"   Longueur signature : {len(signature)} caractères")
print()

# 4. Charger le cache
print("4️⃣ Chargement du cache...")
print("-" * 80)

cache_path = PROJECT_ROOT / "data" / "cache_clusters_catalogued_simple.csv"
if not cache_path.exists():
    print("   ❌ Cache non trouvé")
    sys.exit(1)

df_cache = pd.read_csv(cache_path)
print(f"   ✅ Cache chargé : {len(df_cache)} clusters")
print()

# 5. Chercher dans le cache
print("5️⃣ Recherche dans le cache...")
print("-" * 80)

# Test direct avec find_cluster_in_cache
matched_cluster = find_cluster_in_cache(df_us_1430, df_cache)

if matched_cluster:
    print(f"   ✅ Cluster trouvé !")
    print(f"      Signature cache : {matched_cluster.get('cluster_signature', 'N/A')[:100]}...")
    print(f"      Similarité Jaccard : {matched_cluster.get('jaccard_similarity', 0):.2%}")
    print(f"      Occurrences : {matched_cluster.get('n_samples', 0)}")
    print(f"      Impact médian : {matched_cluster.get('impact_median', 0):.1f} pips")
    print(f"      Pattern dominant : {matched_cluster.get('dominant_pattern', 'N/A')}")
else:
    print("   ❌ Aucun cluster trouvé")
    print()
    print("   Analyse détaillée :")
    print("-" * 80)
    
    # Normaliser les clés
    normalized_keys = normalize_event_keys_list(event_keys, method='with_variants')
    current_set = set(normalized_keys)
    print(f"   Clés normalisées actuelles ({len(current_set)}):")
    for key in sorted(list(current_set))[:10]:
        print(f"      - {key}")
    if len(current_set) > 10:
        print(f"      ... et {len(current_set) - 10} autres")
    print()
    
    # Chercher les meilleurs matches dans le cache
    print("   Meilleurs matches dans le cache :")
    best_matches = []
    
    for idx, row in df_cache.iterrows():
        cache_sig = str(row.get('cluster_signature', ''))
        if pd.isna(cache_sig) or cache_sig == '':
            continue
        
        # Match exact
        if signature == cache_sig:
            best_matches.append({
                'jaccard': 1.0,
                'signature': cache_sig,
                'n_samples': row.get('n_samples', 0),
                'type': 'EXACT'
            })
            continue
        
        # Match partiel
        cache_keys = cache_sig.split('|')
        cache_normalized = normalize_event_keys_list(cache_keys, method='with_variants')
        cache_set = set(cache_normalized)
        
        intersection = current_set & cache_set
        union = current_set | cache_set
        
        if len(union) > 0:
            jaccard = len(intersection) / len(union)
            if jaccard > 0.5:  # Afficher seulement si > 50%
                best_matches.append({
                    'jaccard': jaccard,
                    'signature': cache_sig,
                    'n_samples': row.get('n_samples', 0),
                    'type': 'PARTIAL',
                    'intersection': len(intersection),
                    'union': len(union)
                })
    
    # Trier par Jaccard
    best_matches.sort(key=lambda x: x['jaccard'], reverse=True)
    
    print(f"   {len(best_matches)} matches trouvés (Jaccard > 50%)")
    for i, match in enumerate(best_matches[:5], 1):
        print(f"   {i}. Jaccard: {match['jaccard']:.2%} ({match['type']}) - {match['n_samples']} occurrences")
        if match['type'] == 'PARTIAL':
            print(f"      Intersection: {match['intersection']}, Union: {match['union']}")
        print(f"      Signature: {match['signature'][:100]}...")
        print()
    
    if best_matches:
        best = best_matches[0]
        if best['jaccard'] < 0.7:
            print(f"   ⚠️  Le meilleur match a un Jaccard de {best['jaccard']:.2%} < 0.7")
            print(f"   → Suggestion : baisser le seuil à {best['jaccard']:.2%} ou améliorer la normalisation")

print()
print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)

