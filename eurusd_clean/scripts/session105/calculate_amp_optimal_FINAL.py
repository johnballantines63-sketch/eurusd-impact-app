#!/usr/bin/env python3
"""
SESSION 105 - CALCUL amp_optimal SIMPLIFIÉ
===========================================
Version simplifiée : même requête pour toutes dates

Filtre : événements US high impact (score ≥ 40) à 14:30 Bern
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
import json
from scipy.optimize import minimize_scalar

print("="*80)
print("SESSION 105 - CALCUL amp_optimal SIMPLIFIÉ")
print("="*80)
print()

# Charger impacts réels
impacts_file = Path(__file__).parent / "cluster3_impacts_CORRECTED_5h.json"
with open(impacts_file, 'r') as f:
    data = json.load(f)
    measurements = {m['date']: m for m in data['measurements']}

print(f"✅ {len(measurements)} impacts réels chargés")
print()

# Config DB
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

print(f"🗄️  DB : {db_path}")
print()

# FAMILY_SENTIMENT
FAMILY_SENTIMENT = {
    'CPI': 1, 'CPI_Core': 1, 'PPI': 1, 'Inflation': 1,
    'Unemployment_Rate': -1, 'Jobless_Claims': -1,
    'NFP': 1, 'Payrolls': 1, 'Employment': 1,
    'Retail_Sales': 1, 'Consumer_Confidence': 1,
    'GDP': 1, 'Manufacturing': 1, 'Consumer': 1,
    'Other': 1
}

def get_event_direction(family: str, surprise: float) -> int:
    """Direction événement"""
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    return sentiment if surprise > 0 else -sentiment

def calculate_impact_d(events):
    """Formule D EXACTE"""
    contributions = []
    surprises_pct = []
    num_events = len(events)
    
    for event in events:
        family = event['family']
        surprise = event['surprise']
        score = event['empirical_score']
        surprise_pct = event['surprise_pct']
        
        surprises_pct.append(abs(surprise_pct))
        
        # Formule C
        if num_events >= 2:
            impact_abs = -10.47 + 0.477 * score
        else:
            impact_abs = -7.08 + 0.419 * score
        
        direction = get_event_direction(family, surprise)
        contribution = impact_abs * direction
        contributions.append(contribution)
    
    impact_brut = sum(contributions)
    max_surprise_pct = max(surprises_pct) if surprises_pct else 0
    
    # Amplification (baseline amp=2.5)
    if max_surprise_pct <= 5:
        amplification_factor = 1.0
    elif max_surprise_pct <= 15:
        amplification_factor = 1.0 + (max_surprise_pct - 5) / 10 * 1.5
    else:
        amplification_factor = 2.5
    
    impact_amplifie = abs(impact_brut) * amplification_factor
    impact_final = impact_amplifie * 0.758
    direction_finale = 1 if impact_brut >= 0 else -1
    
    return impact_final * direction_finale

def optimize_amp(events, impact_real):
    """Trouve amp_optimal"""
    def calculate_with_amp(amp_factor):
        contributions = []
        surprises_pct = []
        num_events = len(events)
        
        for event in events:
            family = event['family']
            surprise = event['surprise']
            score = event['empirical_score']
            surprise_pct = event['surprise_pct']
            
            surprises_pct.append(abs(surprise_pct))
            
            if num_events >= 2:
                impact_abs = -10.47 + 0.477 * score
            else:
                impact_abs = -7.08 + 0.419 * score
            
            direction = get_event_direction(family, surprise)
            contributions.append(impact_abs * direction)
        
        impact_brut = sum(contributions)
        max_surprise_pct = max(surprises_pct) if surprises_pct else 0
        
        # Amplification avec amp_factor
        if max_surprise_pct <= 5:
            amplification_factor = 1.0
        elif max_surprise_pct <= 15:
            ratio = (max_surprise_pct - 5) / 10
            amplification_factor = 1.0 + ratio * (amp_factor - 1.0)
        else:
            amplification_factor = amp_factor
        
        impact_amplifie = abs(impact_brut) * amplification_factor
        impact_final = impact_amplifie * 0.758
        
        return abs(impact_final)
    
    def error(amp):
        pred = calculate_with_amp(amp)
        return abs(pred - abs(impact_real))
    
    result = minimize_scalar(error, bounds=(0.1, 10.0), method='bounded')
    return result.x

# Traiter chaque date
results = []
conn = duckdb.connect(str(db_path), read_only=True)

for idx, date_str in enumerate(sorted(measurements.keys()), 1):
    print(f"📅 [{idx}/6] {date_str}")
    print("-"*80)
    
    impact_real = measurements[date_str]['impact_pips']
    print(f"   Impact réel : {impact_real:.1f} pips")
    
    # Charger événements US 14:30 Bern = 12:30+02:00 dans DB
    query = f"""
    SELECT 
        ef.family,
        COALESCE(
            CASE WHEN e.estimate != 0 THEN (e.actual - e.estimate) / e.estimate ELSE 0 END,
            CASE WHEN e.forecast != 0 THEN (e.actual - e.forecast) / e.forecast ELSE 0 END,
            0
        ) as surprise,
        COALESCE(
            CASE WHEN e.estimate != 0 THEN ((e.actual - e.estimate) / e.estimate) * 100 ELSE 0 END,
            CASE WHEN e.forecast != 0 THEN ((e.actual - e.forecast) / e.forecast) * 100 ELSE 0 END,
            0
        ) as surprise_pct,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
        AND e.country = 'US'
        AND ef.empirical_score > 40
        AND e.ts_utc >= '{date_str} 12:00:00+02:00'::TIMESTAMP
        AND e.ts_utc < '{date_str} 13:00:00+02:00'::TIMESTAMP
    ORDER BY e.ts_utc
    """
    
    events_df = conn.execute(query).fetchdf()
    
    if len(events_df) == 0:
        print(f"   ❌ Pas d'événements trouvés")
        print()
        continue
    
    print(f"   ✅ {len(events_df)} événements chargés")
    
    # Convertir
    events = events_df.to_dict('records')
    
    # Stats
    surprises = [abs(e['surprise_pct']) for e in events]
    scores = [e['empirical_score'] for e in events]
    
    print(f"   Surprise max : {max(surprises):.1f}%")
    print(f"   Score moyen  : {sum(scores)/len(scores):.1f}")
    
    # Prédiction baseline
    impact_baseline = calculate_impact_d(events)
    error_baseline = impact_real - impact_baseline
    print(f"   Prédiction baseline (amp=2.5) : {impact_baseline:.1f} pips")
    print(f"   Erreur baseline : {error_baseline:+.1f} pips")
    
    # Optimiser
    amp_optimal = optimize_amp(events, impact_real)
    print(f"   amp_optimal : {amp_optimal:.3f}")
    
    delta_amp = amp_optimal - 2.5
    delta_amp_pct = (delta_amp / 2.5) * 100
    print(f"   Delta amp : {delta_amp:+.3f} ({delta_amp_pct:+.1f}%)")
    
    results.append({
        'date': date_str,
        'num_events': len(events),
        'impact_real': impact_real,
        'surprise_max': max(surprises),
        'score_avg': sum(scores)/len(scores),
        'impact_baseline': impact_baseline,
        'error_baseline': error_baseline,
        'amp_baseline': 2.5,
        'amp_optimal': amp_optimal,
        'delta_amp': delta_amp,
        'delta_amp_pct': delta_amp_pct
    })
    
    print()

conn.close()

# Résultats
print("="*80)
print("RÉSULTATS amp_optimal CLUSTER #3")
print("="*80)
print()

df = pd.DataFrame(results)

print("📊 Tableau récapitulatif :")
print("-"*80)
print(f"{'Date':<12} {'Impact':<8} {'Baseline':<8} {'Erreur':<8} {'amp_opt':<8} {'Delta':<8}")
print("-"*80)
for _, row in df.iterrows():
    ref = "*" if row['date'] == "2025-09-11" else " "
    print(f"{row['date']:<12} {row['impact_real']:>6.1f} p "
          f"{row['impact_baseline']:>6.1f} p {row['error_baseline']:>+6.1f} p "
          f"{row['amp_optimal']:>6.3f}   {row['delta_amp_pct']:>+6.1f}% {ref}")

print()
print(f"   Baseline amp=2.5 MAE : {abs(df['error_baseline']).mean():.1f} pips")
print(f"   amp_optimal moyen    : {df['amp_optimal'].mean():.3f}")
print(f"   amp_optimal médian   : {df['amp_optimal'].median():.3f}")
print(f"   Écart-type amp       : {df['amp_optimal'].std():.3f}")
print()

# Corrélations
if len(df) > 2:
    corr_surprise = df['delta_amp'].corr(df['surprise_max'])
    corr_impact = df['delta_amp'].corr(df['impact_real'])
    print("📊 CORRÉLATIONS :")
    print(f"   delta_amp vs surprise_max : {corr_surprise:+.3f}")
    print(f"   delta_amp vs impact_real  : {corr_impact:+.3f}")
    print()

# Sauvegarder
output_csv = Path(__file__).parent / "cluster3_amp_optimal_FINAL.csv"
df.to_csv(output_csv, index=False)

output_json = Path(__file__).parent / "cluster3_amp_optimal_FINAL.json"
with open(output_json, 'w') as f:
    json.dump({
        'cluster': 'Cluster #3 - CPI mensuel',
        'baseline_amp': 2.5,
        'num_dates': len(results),
        'statistics': {
            'amp_optimal_mean': float(df['amp_optimal'].mean()),
            'amp_optimal_median': float(df['amp_optimal'].median()),
            'amp_optimal_std': float(df['amp_optimal'].std()),
            'baseline_mae': float(abs(df['error_baseline']).mean())
        },
        'results': results
    }, f, indent=2)

print(f"💾 Résultats : {output_csv.name}, {output_json.name}")
print()
print("="*80)
print("✅ TERMINÉ")
print("="*80)
