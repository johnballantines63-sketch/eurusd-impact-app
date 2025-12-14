"""
RECHERCHE DATES DOUBLE_WAVE - LOGIQUE PLANIFICATEUR V3.0
==========================================================

Chercher dates 2023-2025 qui seraient classées DOUBLE_WAVE
par le Planificateur V3.0 avec les mêmes critères exacts.
"""

import duckdb
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import config
DB_PATH = config.DB_PATH

print("="*80)
print("RECHERCHE DATES DOUBLE_WAVE - LOGIQUE PLANIFICATEUR V3.0")
print("="*80)
print()
print("🔍 Critères de détection (exactement comme Planificateur V3.0):")
print("   - Events HIGH : score > 40")
print("   - Impact minimum : 35 pips")
print("   - Classification DOUBLE_WAVE : total_score >= 150 ET num_scored >= 5")
print("   - Scanner : 6h après premier événement")
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Étape 1 : Trouver toutes les dates avec events HIGH
print("📊 ÉTAPE 1 : Identifier dates candidates (2023-2025)...")
print()

query_dates = """
SELECT 
    DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') as date,
    COUNT(*) as num_events,
    SUM(f.empirical_score) as total_score
FROM events e
LEFT JOIN event_families f 
    ON e.event_key = f.event_key 
    AND e.country = f.country
WHERE e.ts_utc >= '2023-01-01'
  AND e.ts_utc < '2026-01-01'
  AND f.empirical_score > 40.0
GROUP BY DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich')
HAVING COUNT(*) >= 5
ORDER BY date
"""

df_dates = conn.execute(query_dates).df()
print(f"   Trouvé {len(df_dates)} dates avec ≥5 events HIGH (score > 40)")
print()

# Étape 2 : Pour chaque date, simuler détection pattern
print("🔍 ÉTAPE 2 : Simulation détection pattern pour chaque date...")
print("   (même logique que detect_pattern_type() du Planificateur V3.0)")
print()

results = []
min_pips = 35.0
timezone_str = "Europe/Zurich"

for idx, row in df_dates.iterrows():
    date = row['date']
    date_str = date.strftime('%Y-%m-%d')
    
    # Charger événements HIGH pour cette date
    query_events = """
    SELECT 
        e.ts_utc,
        f.empirical_score as score
    FROM events e
    LEFT JOIN event_families f
        ON e.event_key = f.event_key
        AND e.country = f.country
    WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = ?
      AND f.empirical_score > 40.0
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query_events, [date_str]).df()
    
    if len(df_events) == 0:
        continue
    
    # Charger prix pour cette date
    query_prices = """
    SELECT datetime, close
    FROM prices_bern
    WHERE DATE(datetime) = ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query_prices, [date_str]).df()
    
    if len(df_prices) == 0:
        continue
    
    # Convertir timestamps
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True)
    df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc'])
    
    # Trouver baseline (1 min avant premier événement)
    first_event_time = df_events['ts_utc'].min()
    
    # Trouver prix avant événement
    df_before = df_prices[df_prices['datetime'] < first_event_time]
    if len(df_before) == 0:
        continue
    
    baseline_time = df_before['datetime'].iloc[-1]
    baseline = df_before['close'].iloc[-1]
    
    # Scanner 6h après premier événement
    scan_end = first_event_time + pd.Timedelta(hours=6)
    df_after = df_prices[(df_prices['datetime'] >= first_event_time) & (df_prices['datetime'] <= scan_end)]
    
    if len(df_after) == 0:
        continue
    
    # Calculer impact maximum
    impact_pips = (df_after['close'] - baseline).abs().max() * 10000
    
    # Calculs pour classification
    total_score = df_events['score'].sum()
    num_scored = len(df_events)
    
    # Classification (même logique que detect_pattern_type)
    if impact_pips < min_pips:
        pattern_type = 'INCONNU'
    elif total_score >= 150 and num_scored >= 5:
        pattern_type = 'DOUBLE_WAVE'
    elif impact_pips > 40:
        pattern_type = 'SINGLE_WAVE_FORT'
    elif impact_pips >= 20:
        pattern_type = 'SINGLE_WAVE_STANDARD'
    else:
        pattern_type = 'INCONNU'
    
    results.append({
        'date': date_str,
        'pattern': pattern_type,
        'impact_pips': impact_pips,
        'total_score': total_score,
        'num_events': num_scored
    })

conn.close()

# Afficher résultats
df_results = pd.DataFrame(results)

print(f"✅ Analyse terminée : {len(df_results)} dates analysées")
print()

# Filtrer DOUBLE_WAVE uniquement
df_doublewave = df_results[df_results['pattern'] == 'DOUBLE_WAVE'].copy()

print("="*80)
print(f"🌊 DATES CLASSÉES DOUBLE_WAVE PAR PLANIFICATEUR V3.0")
print("="*80)
print()

if len(df_doublewave) == 0:
    print("❌ Aucune date DOUBLE_WAVE trouvée !")
else:
    print(f"✅ {len(df_doublewave)} dates DOUBLE_WAVE trouvées")
    print()
    
    # Séparer outliers et standards
    df_doublewave['type'] = df_doublewave['total_score'].apply(
        lambda x: 'OUTLIER' if x > 500 else 'STANDARD'
    )
    
    # Trier par score
    df_doublewave = df_doublewave.sort_values('total_score', ascending=False)
    
    print(f"{'Date':<12} {'Type':<10} {'Impact':<10} {'Score':<10} {'Events':<8}")
    print("-" * 80)
    
    for idx, row in df_doublewave.iterrows():
        print(f"{row['date']:<12} {row['type']:<10} {row['impact_pips']:<10.1f} {row['total_score']:<10.1f} {row['num_events']:<8}")
    
    print()
    print("="*80)
    print("📋 RECOMMANDATIONS POUR TESTS SESSION 135")
    print("="*80)
    print()
    
    # Outliers
    outliers = df_doublewave[df_doublewave['type'] == 'OUTLIER']
    if len(outliers) > 0:
        print(f"🎯 OUTLIERS (score > 500) : {len(outliers)} date(s)")
        for idx, row in outliers.iterrows():
            print(f"   - {row['date']} : score {row['total_score']:.1f}, impact {row['impact_pips']:.1f} pips")
        print()
    
    # Standards
    standards = df_doublewave[df_doublewave['type'] == 'STANDARD']
    if len(standards) > 0:
        print(f"✅ STANDARDS (score 150-500) : {len(standards)} date(s)")
        
        # Recommander top 3-5 standards
        top_standards = standards.head(5)
        for idx, row in top_standards.iterrows():
            print(f"   - {row['date']} : score {row['total_score']:.1f}, impact {row['impact_pips']:.1f} pips")
        print()
    
    print("💡 SUGGESTION TESTS :")
    if len(outliers) > 0:
        print(f"   - 1 OUTLIER  : {outliers.iloc[0]['date']}")
    if len(standards) >= 3:
        print(f"   - STANDARD 1 : {standards.iloc[0]['date']}")
        print(f"   - STANDARD 2 : {standards.iloc[1]['date']}")
        print(f"   - STANDARD 3 : {standards.iloc[2]['date']}")
    elif len(standards) > 0:
        for idx, row in standards.iterrows():
            print(f"   - STANDARD : {row['date']}")

print()
print("="*80)
print("✅ RECHERCHE TERMINÉE")
print("="*80)
