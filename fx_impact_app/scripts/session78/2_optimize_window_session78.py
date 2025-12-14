#!/usr/bin/env python3
"""
OPTIMISATION FENÊTRE TEMPORELLE - SESSION 78
============================================

Teste différentes fenêtres temporelles pour identifier l'optimale.
Fenêtres testées : ±15, ±20, ±30, ±45, ±60 minutes

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

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"

print("\n" + "="*70)
print("OPTIMISATION FENÊTRE TEMPORELLE - SESSION 78")
print("="*70 + "\n")

# Charger dataset
DATASET_PATH = ROOT_DIR / "data" / "movements_strong_session75_v3.csv"
df_movements = pd.read_csv(DATASET_PATH)

# Filtrer 7 mouvements qualité par date (impact max)
dates_qualite = ['2024-12-18', '2024-04-10', '2024-02-13', '2024-06-07', '2024-01-05', '2024-12-04', '2025-09-17']

df_selected = []
for date in dates_qualite:
    df_date = df_movements[df_movements['date'] == date]
    if len(df_date) > 0:
        max_idx = df_date['abs_impact'].idxmax()
        df_selected.append(df_date.loc[max_idx])

df_selected = pd.DataFrame(df_selected).reset_index(drop=True)

print(f"📂 Dataset : {len(df_selected)} mouvements qualité")
print()

# Afficher mouvements sélectionnés
print("📋 Mouvements sélectionnés :")
for i, row in df_selected.iterrows():
    print(f"  {i+1}. {row['date']} {row['time']} | Impact: {row['impact_pips']:.1f} pips")
print()

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Paramètres V2
params_v2 = {'intercept_multi': -18.00, 'coef_multi': 0.300, 'intercept_single': -15.00, 'coef_single': 0.300}

# Helper function
def calculate_impact_v2(events, intercept_multi, coef_multi, intercept_single, coef_single):
    """Calcule impact selon formule V2 (Sessions 51-55 structure)"""
    if not events:
        return 0.0
    
    nb_events = len(events)
    surprise_max = max(e.get('surprise_pct', 0) for e in events)
    
    # Adjusted score
    def calc_adj_score(base, surp):
        if surp < 5: 
            return base
        elif surp < 15: 
            return base * (1.0 + (surp - 5) / 10 * 0.5)
        elif surp < 30: 
            return base * (1.5 + (surp - 15) / 15 * 0.4)
        else: 
            return base * 1.9
    
    # Signed impacts
    family_sentiment = {
        'NFP': -1, 'Unemployment_Rate': 1, 'Average_Hourly_Earnings': -1,
        'CPI': 1, 'Core_CPI': 1, 'PPI': 1, 'Core_PPI': 1,
        'Retail_Sales': -1, 'GDP': -1, 'Jobless_Claims': 1,
        'Continuing_Claims': 1, 'Core_PCE_Price_Index': 1
    }
    
    impacts = []
    for e in events:
        score_adj = calc_adj_score(e.get('empirical_score', 0), e.get('surprise_pct', 0))
        
        if nb_events >= 2:
            impact_brut = intercept_multi + coef_multi * score_adj
        else:
            impact_brut = intercept_single + coef_single * score_adj
        
        direction = family_sentiment.get(e.get('family', ''), 0)
        impacts.append(impact_brut * direction)
    
    impact_total = sum(impacts)
    
    # Amplification
    scores_adj = [calc_adj_score(e.get('empirical_score', 0), e.get('surprise_pct', 0)) for e in events]
    score_adj_mean = np.mean(scores_adj)
    
    if score_adj_mean < 40:
        amp = 1.0
    else:
        surp_capped = min(surprise_max, 30.0)
        if surp_capped < 5: 
            amp = 1.0
        elif surp_capped < 15: 
            amp = 1.0 + (surp_capped - 5) / 10 * 1.5
        else: 
            amp = 2.5
    
    # Correction vectorielle
    return abs(impact_total * amp * 0.758)

# Tester fenêtres
windows = [15, 20, 30, 45, 60]
results = {}

print("🔍 TEST FENÊTRES TEMPORELLES")
print("="*70 + "\n")

for window in windows:
    print(f"Test fenêtre ±{window} min...")
    
    impacts_pred = []
    impacts_real = []
    nb_events_list = []
    
    for _, row in df_selected.iterrows():
        # Parser datetime
        dt_dataset = dateutil.parser.parse(row['datetime'])
        tz_berne = pytz.timezone('Europe/Zurich')
        dt_berne = dt_dataset.astimezone(tz_berne)
        
        start_time = dt_berne - timedelta(minutes=window)
        end_time = dt_berne + timedelta(minutes=window)
        
        # Query events
        query = f"""
        SELECT e.event_key, e.event_title, e.country, e.actual, e.previous, e.estimate, e.forecast,
               e.importance_n, AVG(ef.empirical_score) as empirical_score, MIN(ef.family) as family
        FROM events e
        INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE e.ts_utc >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
          AND e.ts_utc <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
          AND e.importance_n >= 2
          AND ef.empirical_score > 20
          AND e.event_title IS NOT NULL
        GROUP BY e.event_key, e.event_title, e.country, e.actual, e.previous, e.estimate, e.forecast, e.ts_utc, e.importance_n
        """
        
        df_events = conn.execute(query).fetchdf()
        
        if df_events.empty:
            impacts_pred.append(0.0)
            nb_events_list.append(0)
        else:
            # Calculer impact
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
            
            # Calculate impact using V2 params
            impact = calculate_impact_v2(events, **params_v2)
            impacts_pred.append(impact)
            nb_events_list.append(len(events))
        
        impacts_real.append(row['impact_pips'])
    
    # Métriques
    mae = np.mean([abs(p - r) for p, r in zip(impacts_pred, impacts_real)])
    rmse = np.sqrt(np.mean([(p - r)**2 for p, r in zip(impacts_pred, impacts_real)]))
    avg_events = np.mean(nb_events_list)
    
    results[window] = {
        'mae': mae, 
        'rmse': rmse, 
        'avg_events': avg_events, 
        'impacts_pred': impacts_pred, 
        'impacts_real': impacts_real,
        'nb_events_list': nb_events_list
    }
    
    print(f"  MAE: {mae:.1f} pips | RMSE: {rmse:.1f} | Events: {avg_events:.1f}\n")

conn.close()

# Meilleure fenêtre
best_window = min(results.keys(), key=lambda w: results[w]['mae'])
best_mae = results[best_window]['mae']

print("📊 COMPARAISON FENÊTRES")
print("="*70)
print("Fenêtre | MAE (pips) | RMSE (pips) | Nb Events")
print("-"*70)
for w in windows:
    r = results[w]
    marker = " ✅" if w == best_window else ""
    print(f"±{w:2d} min | {r['mae']:10.1f} | {r['rmse']:11.1f} | {r['avg_events']:9.1f}{marker}")

print(f"\n🏆 Meilleure fenêtre : ±{best_window} min (MAE {best_mae:.1f} pips)\n")

# Détails meilleure fenêtre
print(f"📋 DÉTAILS FENÊTRE OPTIMALE (±{best_window} min)")
print("="*70)
best_results = results[best_window]
for i, row in df_selected.iterrows():
    impact_real = best_results['impacts_real'][i]
    impact_pred = best_results['impacts_pred'][i]
    nb_events = best_results['nb_events_list'][i]
    mae_mvt = abs(impact_pred - impact_real)
    
    print(f"{row['date']} ({nb_events} events) | Réel: {impact_real:.1f} | Prédit: {impact_pred:.1f} | MAE: {mae_mvt:.1f}")

print()

# Comparaison objectif
mae_s77 = 87.5
target = 50.0

print("🎯 COMPARAISON OBJECTIFS")
print("="*70)
print(f"MAE Session 77 : {mae_s77:.1f} pips")
print(f"Cible Session 78 : {target:.1f} pips")
print(f"MAE optimal : {best_mae:.1f} pips")
print()

if best_mae < target:
    improvement = (mae_s77 - best_mae) / mae_s77 * 100
    print(f"✅ OBJECTIF ATTEINT : {best_mae:.1f} < {target:.1f} pips")
    print(f"   Amélioration vs S77 : {improvement:.1f}%")
elif best_mae < 60:
    improvement = (mae_s77 - best_mae) / mae_s77 * 100
    print(f"⚠️  PROCHE OBJECTIF : {best_mae:.1f} pips")
    print(f"   Amélioration vs S77 : {improvement:.1f}%")
else:
    print(f"❌ OBJECTIF NON ATTEINT : {best_mae:.1f} pips")

print()

# Sauvegarder
OUTPUT_PATH = SCRIPT_DIR / "optimize_window_results_session78.txt"
with open(OUTPUT_PATH, 'w') as f:
    f.write("OPTIMISATION FENÊTRE TEMPORELLE - SESSION 78\n")
    f.write("="*70 + "\n\n")
    f.write(f"Fenêtre optimale : ±{best_window} min\n")
    f.write(f"MAE              : {best_mae:.1f} pips\n")
    f.write(f"RMSE             : {best_results['rmse']:.1f} pips\n")
    f.write(f"Événements moy   : {best_results['avg_events']:.1f}\n\n")
    f.write("COMPARAISON FENÊTRES\n")
    f.write("-"*70 + "\n")
    for w in windows:
        r = results[w]
        f.write(f"±{w:2d} min | MAE: {r['mae']:.1f} | RMSE: {r['rmse']:.1f} | Events: {r['avg_events']:.1f}\n")

print(f"💾 Résultats sauvegardés : {OUTPUT_PATH.name}\n")

print("="*70)
print("✅ OPTIMISATION TERMINÉE")
print("="*70 + "\n")
