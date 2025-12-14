#!/usr/bin/env python3
"""
SESSION 125 - ÉTAPE 6 : CHERCHER CLUSTERS IDENTIQUES
=====================================================
Trouve toutes les dates historiques avec la MÊME composition d'événements

Workflow :
1. Définir signature cluster 11 septembre (composition événements)
2. Scanner toute la DB (2015-2025)
3. Grouper événements par fenêtres temporelles
4. Comparer signatures
5. Mesurer impacts réels pour les matches
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import json
from datetime import timedelta
from collections import Counter

print("="*80)
print("SESSION 125 - ÉTAPE 6 : RECHERCHE CLUSTERS IDENTIQUES")
print("="*80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
REF_CASE_PATH = Path(__file__).parent / "results_11sept" / "cas_reference_11sept.json"
OUTPUT_DIR = Path(__file__).parent / "matching_clusters"
OUTPUT_DIR.mkdir(exist_ok=True)

SCAN_START = '2015-01-01'  # Scanner tout l'historique
SCAN_END = '2025-12-31'
CLUSTER_WINDOW_MINUTES = 10  # ±5 min = 10 min window

print(f"📁 Base de données : {DB_PATH}")
print(f"📊 Période scan : {SCAN_START} → {SCAN_END}")
print(f"⏰ Fenêtre cluster : ±{CLUSTER_WINDOW_MINUTES//2} min")
print()

# ============================================================================
# ÉTAPE 1 : CHARGER CAS RÉFÉRENCE 11 SEPTEMBRE
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CAS RÉFÉRENCE 11 SEPTEMBRE")
print("="*80)
print()

with open(REF_CASE_PATH, 'r') as f:
    cas_reference = json.load(f)

ref_events = cas_reference['cluster']['events']
ref_signature = tuple(sorted([(e['event_name'], e['country']) for e in ref_events]))

print(f"📋 Signature cluster référence :")
print(f"   Date : {cas_reference['date']}")
print(f"   Événements : {len(ref_events)}")
print()

# Compter occurrences pour signature plus robuste
ref_counter = Counter(ref_signature)
print(f"📊 Composition cluster :")
for (event_name, country), count in ref_counter.most_common():
    print(f"   {event_name:40s} ({country}) × {count}")
print()

# ============================================================================
# ÉTAPE 2 : CHARGER TOUS ÉVÉNEMENTS HIGH
# ============================================================================

print("="*80)
print("ÉTAPE 2 : CHARGEMENT ÉVÉNEMENTS HIGH HISTORIQUES")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

df_events_all = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE datetime_utc >= ?
      AND datetime_utc <= ?
      AND importance = 'HIGH'
    ORDER BY datetime_utc
""", [SCAN_START, SCAN_END]).df()

print(f"✅ {len(df_events_all):,} événements HIGH chargés")
print()

df_events_all['datetime_utc'] = pd.to_datetime(df_events_all['datetime_utc'], utc=True)

# ============================================================================
# ÉTAPE 3 : GROUPER PAR CLUSTERS TEMPORELS
# ============================================================================

print("="*80)
print("ÉTAPE 3 : DÉTECTION CLUSTERS TEMPORELS")
print("="*80)
print()

print(f"🔍 Groupement par fenêtres {CLUSTER_WINDOW_MINUTES} minutes...")

# Créer groupes temporels (fenêtres de 10 min)
df_events_all['cluster_key'] = (
    df_events_all['datetime_utc'].dt.floor(f'{CLUSTER_WINDOW_MINUTES}T')
)

# Grouper par fenêtre
clusters_detected = []

for cluster_time, group in df_events_all.groupby('cluster_key'):
    if len(group) < 2:  # Ignorer clusters avec 1 seul événement
        continue
    
    # Créer signature
    events_list = [(row['event_name'], row['country']) for _, row in group.iterrows()]
    signature = tuple(sorted(events_list))
    
    clusters_detected.append({
        'cluster_time': cluster_time,
        'num_events': len(group),
        'signature': signature,
        'events': group.to_dict('records')
    })

print(f"✅ {len(clusters_detected):,} clusters détectés (≥2 événements)")
print()

# ============================================================================
# ÉTAPE 4 : COMPARER SIGNATURES
# ============================================================================

print("="*80)
print("ÉTAPE 4 : RECHERCHE SIGNATURES IDENTIQUES")
print("="*80)
print()

matching_clusters = []

for cluster in clusters_detected:
    if cluster['signature'] == ref_signature:
        matching_clusters.append(cluster)

print(f"✅ {len(matching_clusters)} cluster(s) avec SIGNATURE IDENTIQUE")
print()

if len(matching_clusters) == 0:
    print("⚠️  AUCUN cluster identique trouvé !")
    print()
    print("🔍 Essayons une recherche partielle (similarité >80%) :")
    
    for cluster in clusters_detected:
        cluster_counter = Counter(cluster['signature'])
        
        # Calculer similarité Jaccard
        intersection = sum((ref_counter & cluster_counter).values())
        union = sum((ref_counter | cluster_counter).values())
        similarity = intersection / union if union > 0 else 0
        
        if similarity >= 0.8:
            cluster['similarity'] = similarity
            matching_clusters.append(cluster)
    
    print(f"   ✅ {len(matching_clusters)} cluster(s) similaires trouvés (≥80%)")
    print()

if len(matching_clusters) == 0:
    print("❌ Aucun cluster similaire trouvé même avec 80% similarité")
    conn.close()
    sys.exit(0)

# Afficher matches
print("📋 Clusters identiques/similaires :")
for i, match in enumerate(matching_clusters[:10], 1):  # Limiter affichage à 10
    similarity = match.get('similarity', 1.0)
    print(f"\n   #{i} - {match['cluster_time']} ({match['num_events']} événements)")
    print(f"       Similarité : {similarity*100:.1f}%")
    
    if similarity < 1.0:
        print(f"       Événements :")
        for event in match['events'][:3]:
            print(f"         - {event['event_name']} ({event['country']})")

print()

# ============================================================================
# ÉTAPE 5 : MESURER IMPACTS RÉELS
# ============================================================================

print("="*80)
print("ÉTAPE 5 : MESURE IMPACTS RÉELS")
print("="*80)
print()

print("🔍 Chargement prix pour mesure impacts...")

# Charger prix pour toutes les dates des matches
for match in matching_clusters:
    cluster_time = pd.to_datetime(match['cluster_time'])
    
    # Convertir UTC → Bern pour requête prices_bern
    cluster_time_bern = cluster_time.tz_convert('Europe/Zurich')
    
    # Charger prix ±60 minutes
    time_start = cluster_time_bern - timedelta(minutes=5)
    time_end = cluster_time_bern + timedelta(minutes=60)
    
    try:
        df_prices = conn.execute("""
            SELECT datetime, close, high, low
            FROM prices_bern
            WHERE datetime >= ?
              AND datetime <= ?
            ORDER BY datetime
        """, [str(time_start), str(time_end)]).df()
        
        if len(df_prices) > 0:
            # Mesurer impact simple (baseline → max/min)
            baseline = df_prices.iloc[0]['close']
            max_high = df_prices['high'].max()
            min_low = df_prices['low'].min()
            
            impact_up = (max_high - baseline) * 10000
            impact_down = (baseline - min_low) * 10000
            impact_total = max(impact_up, impact_down)
            
            match['impact_measured'] = float(impact_total)
            match['baseline_price'] = float(baseline)
            match['prices_available'] = True
        else:
            match['impact_measured'] = None
            match['prices_available'] = False
            
    except Exception as e:
        match['impact_measured'] = None
        match['prices_available'] = False
        match['error'] = str(e)

conn.close()

# Compter combien ont des prix
with_prices = sum(1 for m in matching_clusters if m.get('prices_available', False))
print(f"✅ {with_prices}/{len(matching_clusters)} clusters avec prix disponibles")
print()

# ============================================================================
# ÉTAPE 6 : SAUVEGARDER RÉSULTATS
# ============================================================================

print("="*80)
print("ÉTAPE 6 : SAUVEGARDE RÉSULTATS")
print("="*80)
print()

# Préparer pour JSON (convertir timestamps)
def convert_for_json(obj):
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, np.datetime64)):
        return str(obj)
    elif isinstance(obj, tuple):
        return list(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    else:
        return obj

results = {
    'reference_case': {
        'date': cas_reference['date'],
        'signature': [list(item) for item in ref_signature],
        'num_events': len(ref_events),
        'impact_target': cas_reference['impact']['target_pips'],
        'amplification_ideal': cas_reference['amplification']['ideal_factor'],
        'r2_inversion': cas_reference['tendance_pre_cluster']['r2']
    },
    'matching_clusters': convert_for_json(matching_clusters),
    'summary': {
        'total_matches': len(matching_clusters),
        'with_prices': with_prices,
        'scan_period': f"{SCAN_START} to {SCAN_END}",
        'cluster_window_minutes': CLUSTER_WINDOW_MINUTES
    }
}

output_json = OUTPUT_DIR / "matching_clusters.json"
with open(output_json, 'w') as f:
    json.dump(results, f, indent=2)

print(f"💾 Résultats sauvegardés : {output_json.name}")
print()

# CSV résumé
if matching_clusters:
    summary_data = []
    for match in matching_clusters:
        summary_data.append({
            'cluster_time': str(match['cluster_time']),
            'num_events': match['num_events'],
            'similarity': match.get('similarity', 1.0) * 100,
            'impact_measured': match.get('impact_measured', 'N/A'),
            'prices_available': match.get('prices_available', False)
        })
    
    df_summary = pd.DataFrame(summary_data)
    output_csv = OUTPUT_DIR / "matching_clusters_summary.csv"
    df_summary.to_csv(output_csv, index=False)
    print(f"💾 CSV résumé : {output_csv.name}")
    print()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("="*80)
print("RÉSUMÉ - RECHERCHE CLUSTERS IDENTIQUES")
print("="*80)
print()

print(f"📅 Période scan       : {SCAN_START} → {SCAN_END}")
print(f"🔍 Clusters analysés  : {len(clusters_detected):,}")
print(f"✅ Matches trouvés    : {len(matching_clusters)}")
print(f"📊 Avec prix          : {with_prices}")
print()

if matching_clusters:
    print("📋 Top 5 matches :")
    for i, match in enumerate(matching_clusters[:5], 1):
        impact_str = f"{match['impact_measured']:.1f} pips" if match.get('impact_measured') else "N/A"
        similarity_str = f"{match.get('similarity', 1.0)*100:.0f}%"
        print(f"   {i}. {match['cluster_time']} - Impact: {impact_str} - Sim: {similarity_str}")
    print()

print("="*80)
print("ÉTAPE 6 TERMINÉE ✅")
print("="*80)
print()

print("🎯 PROCHAINE ÉTAPE :")
print("   7. Calculer tendances pré-cluster (R²) pour chaque match")
print("   8. Tester corrélation R² ↔ facteur amplification")
