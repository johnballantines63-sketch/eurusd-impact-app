#!/usr/bin/env python3
"""
SESSION 125 - RE-SCAN AVEC DÉTECTION MATHÉMATIQUE (FINAL)
==========================================================
Utilise approche ZigZag Session 117 (pas fenêtres arbitraires)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import json

# Ajouter chemin Session 117
sys.path.insert(0, str(Path(__file__).parent.parent / "session117"))
from detect_double_wave import detect_double_waves

print("="*80)
print("SESSION 125 - DÉTECTION MATHÉMATIQUE PATTERNS")
print("="*80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "rescan_results"
OUTPUT_DIR.mkdir(exist_ok=True)

SCAN_START = '2024-01-01'
SCAN_END = '2025-12-31'
ZZ_MIN_PIPS = 10.0
W1_MIN_PIPS = 30.0
EXT_MIN_PIPS = 35.0

print(f"📁 Base de données : {DB_PATH}")
print(f"📊 Période : {SCAN_START} → {SCAN_END}")
print(f"📈 Seuils : ZZ={ZZ_MIN_PIPS}, W1={W1_MIN_PIPS}, Ext={EXT_MIN_PIPS} pips")
print()

# ============================================================================
# ÉTAPE 1 : CHARGER DONNÉES
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger prix
print("📊 Chargement prix...")
df_prices = conn.execute("""
    SELECT datetime as ts, close as price
    FROM prices_bern
    WHERE datetime >= ? AND datetime <= ?
    ORDER BY datetime
""", [SCAN_START, SCAN_END]).df()

df_prices['ts'] = pd.to_datetime(df_prices['ts'], utc=True)
df_prices.set_index('ts', inplace=True)

print(f"✅ {len(df_prices):,} prix chargés")
print()

# Charger événements
print("📊 Chargement événements...")
df_events = conn.execute("""
    SELECT datetime_utc, event_name, country, importance
    FROM economic_events
    WHERE datetime_utc >= ? AND datetime_utc <= ?
      AND importance = 'HIGH'
    ORDER BY datetime_utc
""", [SCAN_START, SCAN_END]).df()

df_events['datetime_utc'] = pd.to_datetime(df_events['datetime_utc'], utc=True)

# Mapper scores
df_scores = pd.read_csv(SCORES_PATH)
df_events = df_events.merge(
    df_scores[['event_name', 'country', 'empirical_score', 'sample_size']],
    on=['event_name', 'country'],
    how='left'
)

df_events_measurable = df_events[
    df_events['sample_size'].notna() & (df_events['sample_size'] > 0)
].copy()

print(f"✅ {len(df_events_measurable):,} événements HIGH mesurables")
print()

conn.close()

# ============================================================================
# ÉTAPE 2 : DÉTECTION PATTERNS (APPROCHE MATHÉMATIQUE)
# ============================================================================

print("="*80)
print("ÉTAPE 2 : DÉTECTION PATTERNS ZIGZAG")
print("="*80)
print()

print("🔍 Détection extrema ZigZag...")
patterns_df = detect_double_waves(
    df_prices['price'],
    zz_min_pips=ZZ_MIN_PIPS,
    w1_min_pips=W1_MIN_PIPS,
    ext_min_pips=EXT_MIN_PIPS
)

print(f"✅ {len(patterns_df)} patterns détectés (> {EXT_MIN_PIPS} pips)")
print()

# Convertir DataFrame en liste de dicts
patterns = patterns_df.to_dict('records')

# ============================================================================
# ÉTAPE 3 : ASSOCIER ÉVÉNEMENTS
# ============================================================================

print("="*80)
print("ÉTAPE 3 : ASSOCIATION ÉVÉNEMENTS")
print("="*80)
print()

patterns_with_events = []
patterns_without_events = []

for pattern in patterns:
    # Timestamp pattern (high3 = peak final)
    pattern_time = pd.to_datetime(pattern['high3_time'], utc=True)
    
    # Chercher événements ±10 min
    window_start = pattern_time - pd.Timedelta(minutes=10)
    window_end = pattern_time + pd.Timedelta(minutes=10)
    
    mask = (df_events_measurable['datetime_utc'] >= window_start) & \
           (df_events_measurable['datetime_utc'] <= window_end)
    
    events = df_events_measurable[mask]
    
    if len(events) > 0:
        pattern_enriched = pattern.copy()
        pattern_enriched['events'] = events.to_dict('records')
        pattern_enriched['num_events'] = len(events)
        pattern_enriched['total_score'] = float(events['empirical_score'].sum())
        pattern_enriched['events_summary'] = ', '.join(events['event_name'].head(3).tolist())
        
        patterns_with_events.append(pattern_enriched)
    else:
        patterns_without_events.append(pattern)

print(f"✅ {len(patterns_with_events)} patterns AVEC événements")
print(f"⚠️  {len(patterns_without_events)} patterns SANS événements")
print()

# ============================================================================
# ÉTAPE 4 : SAUVEGARDER
# ============================================================================

print("="*80)
print("ÉTAPE 4 : SAUVEGARDE")
print("="*80)
print()

# Convertir pour JSON
def convert_for_json(obj):
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, np.datetime64)):
        return str(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    else:
        return obj

patterns_clean = convert_for_json(patterns_with_events)

output_json = OUTPUT_DIR / "patterns_with_events.json"
with open(output_json, 'w') as f:
    json.dump(patterns_clean, f, indent=2)

print(f"💾 JSON : {output_json.name}")

# CSV résumé
summary_data = []
for p in patterns_with_events:
    summary_data.append({
        'pattern_time': str(p['high3_time']),
        'amplitude_pips': p.get('ext_total_pips', 0),
        'wave1_pips': p.get('wave1_pips', 0),
        'wave2_pips': p.get('wave2_pips', 0),
        'num_events': p['num_events'],
        'total_score': p['total_score'],
        'events_summary': p['events_summary'][:100]
    })

if summary_data:
    df_summary = pd.DataFrame(summary_data)
    output_csv = OUTPUT_DIR / "patterns_summary.csv"
    df_summary.to_csv(output_csv, index=False)
    print(f"💾 CSV : {output_csv.name}")
print()

# ============================================================================
# ÉTAPE 5 : VALIDATION 11 SEPTEMBRE
# ============================================================================

print("="*80)
print("ÉTAPE 5 : VALIDATION 11 SEPTEMBRE")
print("="*80)
print()

sept_11_patterns = [
    p for p in patterns_with_events
    if '2025-09-11' in str(p['high3_time'])
]

if sept_11_patterns:
    print(f"✅ {len(sept_11_patterns)} pattern(s) 11 septembre")
    print()
    
    for i, p in enumerate(sept_11_patterns, 1):
        print(f"📊 Pattern #{i} :")
        print(f"   High3 time  : {p['high3_time']}")
        print(f"   Amplitude   : {p.get('ext_total_pips', 0):.2f} pips")
        print(f"   Wave 1      : {p.get('wave1_pips', 0):.2f} pips")
        print(f"   Wave 2      : {p.get('wave2_pips', 0):.2f} pips")
        print(f"   Événements  : {p['num_events']}")
        print(f"   Score total : {p['total_score']:.2f}")
        print(f"   Résumé      : {p['events_summary']}")
        print()
else:
    print("⚠️  Aucun pattern 11 septembre")
    print()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("="*80)
print("RÉSUMÉ FINAL")
print("="*80)
print()

print(f"📊 Période        : {SCAN_START} → {SCAN_END}")
print(f"📈 Seuil          : {EXT_MIN_PIPS} pips")
print(f"✅ Total patterns : {len(patterns)}")
print(f"✅ Avec événements: {len(patterns_with_events)}")
print(f"⚠️  Sans événements: {len(patterns_without_events)}")
print()

print("="*80)
print("DÉTECTION MATHÉMATIQUE TERMINÉE ✅")
print("="*80)
