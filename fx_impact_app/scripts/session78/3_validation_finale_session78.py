#!/usr/bin/env python3
"""
VALIDATION FINALE - SESSION 78
==============================

Valide formules V2 avec fenêtre optimale.

Date : 25 octobre 2025
Session : 78
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
import numpy as np
import dateutil.parser
import pytz
import re

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"

print("\n" + "="*70)
print("VALIDATION FINALE - SESSION 78")
print("="*70 + "\n")

# Lire fenêtre optimale
WINDOW_FILE = SCRIPT_DIR / "optimize_window_results_session78.txt"
if WINDOW_FILE.exists():
    with open(WINDOW_FILE, 'r') as f:
        content = f.read()
    match = re.search(r'Fenêtre optimale : ±(\d+) min', content)
    OPTIMAL_WINDOW = int(match.group(1)) if match else 30
    print(f"📂 Fenêtre optimale : ±{OPTIMAL_WINDOW} min\n")
else:
    OPTIMAL_WINDOW = 30
    print(f"⚠️  Fenêtre par défaut : ±{OPTIMAL_WINDOW} min\n")

# Paramètres V2
params_v2 = {'intercept_multi': -18.00, 'coef_multi': 0.300, 'intercept_single': -15.00, 'coef_single': 0.300}

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

# TEST 1: 11 septembre
print("🎯 TEST 1 : CAS RÉFÉRENCE 11 SEPTEMBRE 2025")
print("="*70 + "\n")

query_11sept = """
SELECT e.event_key, e.event_title, e.actual, e.previous, e.estimate, e.forecast,
       AVG(ef.empirical_score) as empirical_score, MIN(ef.family) as family
FROM events e
INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND strftime(e.ts_utc, '%H:%M') BETWEEN '14:28' AND '14:32'
  AND e.country = 'US'
  AND e.importance_n >= 2
  AND ef.empirical_score > 20
GROUP BY e.event_key, e.event_title, e.actual, e.previous, e.estimate, e.forecast, e.ts_utc
"""

df_11sept = conn.execute(query_11sept).fetchdf()

events_11sept = []
for _, e in df_11sept.iterrows():
    actual = e.get('actual')
    estimate = e.get('estimate') or e.get('forecast') or e.get('previous')
    surprise_pct = 0.0
    if actual is not None and estimate is not None and estimate != 0:
        surprise_pct = abs((actual - estimate) / estimate) * 100
    
    events_11sept.append({
        'empirical_score': e.get('empirical_score', 0),
        'surprise_pct': surprise_pct,
        'family': e.get('family', 'Unknown')
    })

impact_pred_11sept = calculate_impact_v2(events_11sept, **params_v2)
impact_real_11sept = 53.0
mae_11sept = abs(impact_pred_11sept - impact_real_11sept)

print(f"Événements : {len(events_11sept)}")
print(f"Impact prédit : {impact_pred_11sept:.1f} pips")
print(f"Impact réel   : {impact_real_11sept:.1f} pips")
print(f"MAE           : {mae_11sept:.1f} pips")
print(f"Statut        : {'✅ EXCELLENT' if mae_11sept < 10 else '⚠️ À AMÉLIORER'}\n")

# TEST 2: Session 75
print("🎯 TEST 2 : DATASET SESSION 75")
print("="*70 + "\n")

DATASET_PATH = ROOT_DIR / "data" / "movements_strong_session75_v3.csv"
df_movements = pd.read_csv(DATASET_PATH)

dates_qualite = ['2024-12-18', '2024-04-10', '2024-02-13', '2024-06-07', '2024-01-05', '2024-12-04', '2025-09-17']

df_selected = []
for date in dates_qualite:
    df_date = df_movements[df_movements['date'] == date]
    if len(df_date) > 0:
        max_idx = df_date['abs_impact'].idxmax()
        df_selected.append(df_date.loc[max_idx])

df_selected = pd.DataFrame(df_selected).reset_index(drop=True)

impacts_pred_s75 = []
impacts_real_s75 = []

for _, row in df_selected.iterrows():
    dt_dataset = dateutil.parser.parse(row['datetime'])
    tz_berne = pytz.timezone('Europe/Zurich')
    dt_berne = dt_dataset.astimezone(tz_berne)
    
    start_time = dt_berne - timedelta(minutes=OPTIMAL_WINDOW)
    end_time = dt_berne + timedelta(minutes=OPTIMAL_WINDOW)
    
    query = f"""
    SELECT e.event_key, e.event_title, e.actual, e.previous, e.estimate, e.forecast,
           AVG(ef.empirical_score) as empirical_score, MIN(ef.family) as family
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.ts_utc <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.importance_n >= 2
      AND ef.empirical_score > 20
      AND e.event_title IS NOT NULL
    GROUP BY e.event_key, e.event_title, e.actual, e.previous, e.estimate, e.forecast, e.ts_utc
    """
    
    df_events = conn.execute(query).fetchdf()
    
    if df_events.empty:
        impacts_pred_s75.append(0.0)
    else:
        events = []
        for _, e in df_events.iterrows():
            actual = e.get('actual')
            estimate = e.get('estimate') or e.get('forecast') or e.get('previous')
            surprise_pct = 0.0
            if actual is not None and estimate is not None and estimate != 0:
                surprise_pct = abs((actual - estimate) / estimate) * 100
            
            events.append({
                'empirical_score': e.get('empirical_score', 0),
                'surprise_pct': surprise_pct,
                'family': e.get('family', 'Unknown')
            })
        
        impact = calculate_impact_v2(events, **params_v2)
        impacts_pred_s75.append(impact)
    
    impacts_real_s75.append(row['impact_pips'])
    
    mae_mvt = abs(impacts_pred_s75[-1] - impacts_real_s75[-1])
    print(f"{row['date']} | Réel: {row['impact_pips']:.1f} | Prédit: {impacts_pred_s75[-1]:.1f} | MAE: {mae_mvt:.1f}")

conn.close()

mae_s75 = np.mean([abs(p - r) for p, r in zip(impacts_pred_s75, impacts_real_s75)])
mae_s77 = 87.5
target = 50.0

print(f"\n📊 MÉTRIQUES SESSION 75")
print("="*70)
print(f"MAE Session 77 : {mae_s77:.1f} pips")
print(f"MAE Session 78 : {mae_s75:.1f} pips")
print(f"Cible          : {target:.1f} pips")

if mae_s75 < target:
    improvement = (mae_s77 - mae_s75) / mae_s77 * 100
    print(f"\n✅ OBJECTIF ATTEINT : {mae_s75:.1f} < {target:.1f} pips")
    print(f"   Amélioration : {improvement:.1f}%")
    status = "SUCCÈS"
elif mae_s75 < 60:
    improvement = (mae_s77 - mae_s75) / mae_s77 * 100
    print(f"\n⚠️  PROCHE OBJECTIF : {mae_s75:.1f} pips")
    print(f"   Amélioration : {improvement:.1f}%")
    status = "ACCEPTABLE"
else:
    print(f"\n❌ OBJECTIF NON ATTEINT : {mae_s75:.1f} pips")
    status = "INSUFFISANT"

print(f"\n📊 STATUT FINAL : {status}\n")

# Sauvegarder
OUTPUT_PATH = SCRIPT_DIR / "validation_finale_session78.txt"
with open(OUTPUT_PATH, 'w') as f:
    f.write("VALIDATION FINALE - SESSION 78\n")
    f.write("="*70 + "\n\n")
    f.write(f"Fenêtre optimale : ±{OPTIMAL_WINDOW} min\n")
    f.write(f"MAE 11 septembre : {mae_11sept:.1f} pips\n")
    f.write(f"MAE Session 75   : {mae_s75:.1f} pips\n")
    f.write(f"Statut           : {status}\n")

print(f"💾 Résultats sauvegardés : {OUTPUT_PATH.name}\n")

print("="*70)
print("✅ VALIDATION FINALE TERMINÉE")
print("="*70 + "\n")


def calculate_impact_v2(events, intercept_multi, coef_multi, intercept_single, coef_single):
    if not events:
        return 0.0
    
    nb_events = len(events)
    surprise_max = max(e.get('surprise_pct', 0) for e in events)
    
    def calc_adj_score(base, surp):
        if surp < 5: return base
        elif surp < 15: return base * (1.0 + (surp - 5) / 10 * 0.5)
        elif surp < 30: return base * (1.5 + (surp - 15) / 15 * 0.4)
        else: return base * 1.9
    
    impacts = []
    for e in events:
        score_adj = calc_adj_score(e.get('empirical_score', 0), e.get('surprise_pct', 0))
        impact_brut = (intercept_multi + coef_multi * score_adj) if nb_events >= 2 else (intercept_single + coef_single * score_adj)
        
        family_sentiment = {'NFP': -1, 'Unemployment_Rate': 1, 'CPI': 1, 'Core_CPI': 1, 'Jobless_Claims': 1}
        direction = family_sentiment.get(e.get('family', ''), 0)
        impacts.append(impact_brut * direction)
    
    impact_total = sum(impacts)
    
    scores_adj = [calc_adj_score(e.get('empirical_score', 0), e.get('surprise_pct', 0)) for e in events]
    score_adj_mean = np.mean(scores_adj)
    
    if score_adj_mean < 40:
        amp = 1.0
    else:
        surp_capped = min(surprise_max, 30.0)
        if surp_capped < 5: amp = 1.0
        elif surp_capped < 15: amp = 1.0 + (surp_capped - 5) / 10 * 1.5
        else: amp = 2.5
    
    return abs(impact_total * amp * 0.758)
