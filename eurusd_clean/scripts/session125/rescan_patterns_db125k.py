#!/usr/bin/env python3
"""
SESSION 125 - RE-SCAN PATTERNS (FINAL - SCORES EMPIRIQUES)
===========================================================
Utilise scores empiriques Session 124 pour identifier événements mesurables
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json

print("="*80)
print("SESSION 125 - RE-SCAN AVEC SCORES EMPIRIQUES")
print("="*80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "rescan_results"
OUTPUT_DIR.mkdir(exist_ok=True)

SCAN_START = '2024-01-01'
SCAN_END = '2025-12-31'
SPIKE_THRESHOLD_PIPS = 35.0
TZ_BERN = pytz.timezone('Europe/Zurich')

print(f"📁 Base de données : {DB_PATH}")
print(f"📊 Scores empiriques : {SCORES_PATH.name}")
print(f"📊 Période scan : {SCAN_START} → {SCAN_END}")
print(f"📈 Seuil spike : {SPIKE_THRESHOLD_PIPS} pips")
print()

# ============================================================================
# ÉTAPE 1 : CHARGER DONNÉES
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT DONNÉES")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1.1 Charger prix
print("📊 Chargement prix 1-minute...")
df_prices = conn.execute("""
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ? AND datetime <= ?
    ORDER BY datetime
""", [SCAN_START, SCAN_END]).df()
print(f"✅ {len(df_prices):,} prix chargés")
print()

# 1.2 Charger événements
print("📊 Chargement événements économiques...")
df_events = conn.execute("""
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
print(f"✅ {len(df_events):,} événements HIGH chargés")
print()

conn.close()

# 1.3 Charger scores empiriques
print("📊 Chargement scores empiriques...")
df_scores = pd.read_csv(SCORES_PATH)
print(f"✅ {len(df_scores):,} familles avec scores empiriques")
print()

# 1.4 Mapper événements avec scores
print("📊 Mapping événements → scores...")
df_events = df_events.merge(
    df_scores[['event_name', 'country', 'empirical_score', 'sample_size']],
    on=['event_name', 'country'],
    how='left'
)

# Filtrer événements MESURABLES (avec score empirique)
df_events_measurable = df_events[df_events['sample_size'].notna() & (df_events['sample_size'] > 0)].copy()

print(f"✅ {len(df_events_measurable):,} événements HIGH mesurables ({len(df_events_measurable)/len(df_events)*100:.1f}%)")
print()

# Convertir timezone
df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True).dt.tz_convert(TZ_BERN)
df_prices.set_index('datetime', inplace=True)

df_events_measurable['datetime_utc'] = pd.to_datetime(df_events_measurable['datetime_utc'], utc=True)
df_events_measurable['datetime_bern'] = df_events_measurable['datetime_utc'].dt.tz_convert(TZ_BERN)

# ============================================================================
# ÉTAPE 2 : DÉTECTER SPIKES
# ============================================================================

print("="*80)
print("ÉTAPE 2 : DÉTECTION SPIKES (> 35 pips)")
print("="*80)
print()

def detect_spikes(df_prices, threshold_pips=35.0, window_minutes=60):
    """Détecte spikes > seuil"""
    spikes = []
    times = df_prices.index.values
    highs = df_prices['high'].values
    lows = df_prices['low'].values
    
    print(f"🔍 Scan {len(df_prices):,} prix...")
    
    for i in range(0, len(df_prices) - window_minutes, 30):
        if i % 50000 == 0:
            print(f"   Progression: {i/len(df_prices)*100:.1f}%")
        
        window_highs = highs[i:i+window_minutes]
        window_lows = lows[i:i+window_minutes]
        
        max_high = np.max(window_highs)
        min_low = np.min(window_lows)
        amplitude_pips = (max_high - min_low) * 10000
        
        if amplitude_pips >= threshold_pips:
            peak_idx = i + np.argmax(window_highs)
            trough_idx = i + np.argmin(window_lows)
            
            direction = 'bearish' if peak_idx < trough_idx else 'bullish'
            
            spike = {
                'start_time': times[i],
                'peak_time': times[peak_idx],
                'trough_time': times[trough_idx],
                'amplitude_pips': amplitude_pips,
                'direction': direction,
                'high': max_high,
                'low': min_low
            }
            
            # Éviter doublons
            is_duplicate = False
            for existing in spikes:
                time_diff = abs((times[i] - existing['start_time']).astype('timedelta64[m]').astype(int))
                if time_diff < 30:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                spikes.append(spike)
    
    print(f"   Progression: 100.0%")
    return spikes

spikes = detect_spikes(df_prices, threshold_pips=SPIKE_THRESHOLD_PIPS)

print(f"✅ {len(spikes)} spikes détectés")
print()

if spikes:
    amplitudes = [s['amplitude_pips'] for s in spikes]
    print(f"📊 Statistiques :")
    print(f"   Min  : {min(amplitudes):.1f} pips")
    print(f"   Max  : {max(amplitudes):.1f} pips")
    print(f"   Moy  : {np.mean(amplitudes):.1f} pips")
    print(f"   Med  : {np.median(amplitudes):.1f} pips")
    print()

# ============================================================================
# ÉTAPE 3 : ASSOCIER ÉVÉNEMENTS
# ============================================================================

print("="*80)
print("ÉTAPE 3 : ASSOCIATION ÉVÉNEMENTS")
print("="*80)
print()

def associate_events_to_spike(spike, df_events, window_minutes=10):
    """Trouve événements MESURABLES ±10 min"""
    spike_time = pd.Timestamp(spike['start_time']).tz_localize('UTC').tz_convert(TZ_BERN)
    
    window_start = spike_time - timedelta(minutes=window_minutes)
    window_end = spike_time + timedelta(minutes=window_minutes)
    
    mask = (df_events['datetime_bern'] >= window_start) & (df_events['datetime_bern'] <= window_end)
    events_window = df_events[mask].copy()
    
    return events_window

print(f"🔍 Association événements aux {len(spikes)} spikes...")

spikes_with_events = []
spikes_without_events = []

for spike in spikes:
    events = associate_events_to_spike(spike, df_events_measurable)
    
    if len(events) > 0:
        spike_enriched = spike.copy()
        spike_enriched['events'] = events.to_dict('records')
        spike_enriched['num_events'] = len(events)
        spike_enriched['events_summary'] = ', '.join(events['event_name'].head(3).tolist())
        spike_enriched['total_score'] = events['empirical_score'].sum()
        
        spikes_with_events.append(spike_enriched)
    else:
        spikes_without_events.append(spike)

print(f"✅ {len(spikes_with_events)} spikes AVEC événements mesurables")
print(f"⚠️  {len(spikes_without_events)} spikes SANS événements")
print()

# ============================================================================
# ÉTAPE 4 : SAUVEGARDER
# ============================================================================

print("="*80)
print("ÉTAPE 4 : SAUVEGARDE")
print("="*80)
print()

# Convertir timestamps pour JSON
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

spikes_clean = convert_for_json(spikes_with_events)

output_json = OUTPUT_DIR / "spikes_with_events.json"
with open(output_json, 'w') as f:
    json.dump(spikes_clean, f, indent=2)

print(f"💾 JSON : {output_json.name}")

# CSV résumé
summary_data = []
for spike in spikes_with_events:
    summary_data.append({
        'start_time': str(spike['start_time']),
        'amplitude_pips': spike['amplitude_pips'],
        'direction': spike['direction'],
        'num_events': spike['num_events'],
        'total_score': spike['total_score'],
        'events_summary': spike['events_summary'][:100]
    })

df_summary = pd.DataFrame(summary_data)
output_csv = OUTPUT_DIR / "spikes_summary.csv"
df_summary.to_csv(output_csv, index=False)

print(f"💾 CSV : {output_csv.name}")
print()

# ============================================================================
# ÉTAPE 5 : VALIDATION 11 SEPTEMBRE
# ============================================================================

print("="*80)
print("ÉTAPE 5 : VALIDATION CAS RÉFÉRENCE - 11 SEPTEMBRE 2025")
print("="*80)
print()

sept_11_cases = [
    s for s in spikes_with_events 
    if '2025-09-11' in str(s['start_time'])
]

if sept_11_cases:
    print(f"✅ {len(sept_11_cases)} spike(s) détecté(s) le 11 septembre 2025")
    print()
    
    for i, case in enumerate(sept_11_cases, 1):
        print(f"📊 Spike #{i} :")
        print(f"   Heure       : {case['start_time']}")
        print(f"   Amplitude   : {case['amplitude_pips']:.2f} pips")
        print(f"   Direction   : {case['direction']}")
        print(f"   Événements  : {case['num_events']}")
        print(f"   Score total : {case['total_score']:.2f}")
        print(f"   Résumé      : {case['events_summary']}")
        print()
else:
    print("⚠️  AUCUN spike détecté le 11 septembre 2025")
    print()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("="*80)
print("RÉSUMÉ FINAL")
print("="*80)
print()

print(f"📊 Période         : {SCAN_START} → {SCAN_END}")
print(f"📈 Seuil           : {SPIKE_THRESHOLD_PIPS} pips")
print(f"✅ Total spikes    : {len(spikes)}")
print(f"✅ Avec événements : {len(spikes_with_events)} ({len(spikes_with_events)/len(spikes)*100:.1f}%)")
print(f"⚠️  Sans événements : {len(spikes_without_events)} ({len(spikes_without_events)/len(spikes)*100:.1f}%)")
print()

print("="*80)
print("RE-SCAN TERMINÉ ✅")
print("="*80)
