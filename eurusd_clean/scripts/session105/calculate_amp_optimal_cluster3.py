#!/usr/bin/env python3
"""
SESSION 105 - CALCUL amp_optimal CLUSTER #3
============================================
Pour chaque date du Cluster #3 :
1. Charger événements + scores
2. Calculer score ajusté (avec surprise)
3. Prédire avec baseline amp=2.5
4. Calculer amp_optimal qui reproduit impact réel
5. Delta vs baseline

Formule baseline (Session 103) :
impact_d = score_adj * num_events * amp * 0.758
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
import json
from scipy.optimize import minimize_scalar

print("="*80)
print("SESSION 105 - CALCUL amp_optimal CLUSTER #3")
print("="*80)
print()

# Charger impacts réels mesurés
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

# Fonction ajustement score (Session 55)
def calculate_adjusted_empirical_score(base_score, surprise_pct):
    """
    Ajustement score selon surprise
    Session 55 - Validé à 99.9%
    """
    abs_surprise = abs(surprise_pct)
    
    if abs_surprise < 5:
        factor = 1.0
    elif abs_surprise < 15:
        factor = 1.0 + (abs_surprise - 5) / 10 * 0.5  # 1.0 → 1.5
    elif abs_surprise < 30:
        factor = 1.5 + (abs_surprise - 15) / 15 * 0.4  # 1.5 → 1.9
    else:
        factor = 1.9  # Plafond
    
    return base_score * factor

# Formule D (baseline amp=2.5)
def calculate_impact_d(score_adjusted, num_events, amp=2.5, correction_factor=0.758):
    """
    Formule D - Session 51
    Pour multi-événements simultanés
    """
    # Formule linéaire base
    impact_base = -10.47 + 0.477 * score_adjusted
    
    # Somme vectorielle simplifiée (même direction CPI)
    impact_total = impact_base * num_events
    
    # Amplification + correction empirique
    return abs(impact_total) * amp * correction_factor

# Fonction optimisation amp
def optimize_amp(score_adjusted, num_events, impact_real):
    """
    Trouve l'amp optimal qui reproduit impact_real
    """
    def error(amp):
        pred = calculate_impact_d(score_adjusted, num_events, amp)
        return abs(pred - impact_real)
    
    result = minimize_scalar(error, bounds=(0.5, 10.0), method='bounded')
    return result.x

# Traiter chaque date
results = []

conn = duckdb.connect(str(db_path), read_only=True)

for idx, date_str in enumerate(sorted(measurements.keys()), 1):
    print(f"📅 [{idx}/6] {date_str}")
    print("-"*80)
    
    impact_real = measurements[date_str]['impact_pips']
    print(f"   Impact réel : {impact_real:.1f} pips")
    
    # Charger événements CPI de cette date
    query = f"""
    SELECT 
        e.event_key,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
        AND e.country = 'US'
        AND ef.empirical_score > 40
        AND ef.family IN ('Inflation', 'Other')
    ORDER BY e.ts_utc
    """
    
    events = conn.execute(query).fetchdf()
    
    if len(events) == 0:
        print(f"   ❌ Pas d'événements trouvés")
        print()
        continue
    
    print(f"   ✅ {len(events)} événements chargés")
    
    # Calculer surprises
    surprises = []
    for _, ev in events.iterrows():
        actual = ev['actual']
        estimate = ev.get('estimate') or ev.get('forecast') or ev.get('previous')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise = abs((actual - estimate) / estimate) * 100  # en %
            surprises.append(surprise)
    
    surprise_max = max(surprises) if surprises else 0
    surprise_avg = sum(surprises) / len(surprises) if surprises else 0
    
    print(f"   Surprise max : {surprise_max:.1f}%")
    print(f"   Surprise avg : {surprise_avg:.1f}%")
    
    # Score de base (moyenne événements)
    base_score = events['empirical_score'].mean()
    print(f"   Score base   : {base_score:.1f}")
    
    # Score ajusté avec surprise max
    score_adjusted = calculate_adjusted_empirical_score(base_score, surprise_max)
    print(f"   Score ajusté : {score_adjusted:.1f}")
    
    # Prédiction baseline amp=2.5
    impact_baseline = calculate_impact_d(score_adjusted, len(events), amp=2.5)
    error_baseline = impact_real - impact_baseline
    print(f"   Prédiction baseline (amp=2.5) : {impact_baseline:.1f} pips")
    print(f"   Erreur baseline : {error_baseline:+.1f} pips")
    
    # Optimiser amp
    amp_optimal = optimize_amp(score_adjusted, len(events), impact_real)
    impact_optimal = calculate_impact_d(score_adjusted, len(events), amp_optimal)
    print(f"   amp_optimal : {amp_optimal:.3f}")
    print(f"   Prédiction optimal : {impact_optimal:.1f} pips")
    
    # Delta vs baseline
    delta_amp = amp_optimal - 2.5
    delta_amp_pct = (delta_amp / 2.5) * 100
    print(f"   Delta amp : {delta_amp:+.3f} ({delta_amp_pct:+.1f}%)")
    
    # Sauvegarder
    results.append({
        'date': date_str,
        'num_events': len(events),
        'impact_real': impact_real,
        'surprise_max': surprise_max,
        'surprise_avg': surprise_avg,
        'base_score': base_score,
        'score_adjusted': score_adjusted,
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

# Validation référence
ref_row = df[df['date'] == "2025-09-11"]
if len(ref_row) > 0:
    amp_ref = ref_row.iloc[0]['amp_optimal']
    if abs(amp_ref - 2.5) < 0.5:
        print(f"✅ Date référence 11.09 : amp = {amp_ref:.3f} ≈ 2.5 ✅")
    else:
        print(f"⚠️ Date référence 11.09 : amp = {amp_ref:.3f} (baseline 2.5)")
    print()

# Analyse corrélations
print("📊 ANALYSE CORRÉLATIONS :")
print("-"*80)

# Corrélation delta_amp vs surprise
corr_surprise = df['delta_amp'].corr(df['surprise_max'])
print(f"   delta_amp vs surprise_max : {corr_surprise:+.3f}")

# Corrélation delta_amp vs impact_real
corr_impact = df['delta_amp'].corr(df['impact_real'])
print(f"   delta_amp vs impact_real  : {corr_impact:+.3f}")

print()

# Sauvegarder
output_csv = Path(__file__).parent / "cluster3_amp_optimal.csv"
df.to_csv(output_csv, index=False)
print(f"💾 Résultats CSV : {output_csv.name}")

output_json = Path(__file__).parent / "cluster3_amp_optimal.json"
with open(output_json, 'w') as f:
    json.dump({
        'cluster': 'Cluster #3 - CPI mensuel',
        'baseline_amp': 2.5,
        'num_dates': len(results),
        'statistics': {
            'amp_optimal_mean': float(df['amp_optimal'].mean()),
            'amp_optimal_median': float(df['amp_optimal'].median()),
            'amp_optimal_std': float(df['amp_optimal'].std()),
            'baseline_mae': float(abs(df['error_baseline']).mean()),
            'correlation_surprise': float(corr_surprise),
            'correlation_impact': float(corr_impact)
        },
        'results': results
    }, f, indent=2)

print(f"💾 Résultats JSON : {output_json.name}")
print()
print("="*80)
print("✅ CALCUL amp_optimal TERMINÉ")
print("="*80)
