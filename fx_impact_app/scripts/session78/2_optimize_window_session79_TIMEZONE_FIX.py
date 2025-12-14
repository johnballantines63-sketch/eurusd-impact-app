#!/usr/bin/env python3
"""
OPTIMISATION FENÊTRE TEMPORELLE - SESSION 79 TIMEZONE FIX
=========================================================

Teste différentes fenêtres temporelles pour identifier l'optimale.
Fenêtres testées : ±15, ±20, ±30, ±45, ±60 minutes

CORRECTION TIMEZONE DÉFINITIVE SESSION 79:
- Utilise timezone_utils.get_event_window_utc()
- Plus de double conversion timezone
- Logique EXACTE de formulas_validated.py
- FAMILY_SENTIMENT complet (35+ familles)

Date : 25 octobre 2025
Session : 79
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

# Import fonctions validées + timezone utils
from src.formulas_validated import calculate_adjusted_empirical_score
from src.utils.timezone_utils import get_event_window_utc

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"

print("\n" + "="*70)
print("OPTIMISATION FENÊTRE TEMPORELLE - SESSION 79 TIMEZONE FIX")
print("="*70 + "\n")

# ════════════════════════════════════════════════════════════════
# FAMILY_SENTIMENT COMPLET (Sessions 51-55)
# ════════════════════════════════════════════════════════════════

FAMILY_SENTIMENT = {
    'NFP': -1, 'Unemployment_Rate': 1, 'Average_Hourly_Earnings': -1,
    'CPI': 1, 'Core_CPI': 1, 'PPI': 1, 'Core_PPI': 1,
    'Retail_Sales': -1, 'GDP': -1, 'ISM_Manufacturing_PMI': -1,
    'ISM_Services_PMI': -1, 'Consumer_Confidence': -1,
    'Durable_Goods_Orders': -1, 'Trade_Balance': -1,
    'Industrial_Production': -1, 'Housing_Starts': -1,
    'Building_Permits': -1, 'Existing_Home_Sales': -1,
    'New_Home_Sales': -1, 'Jobless_Claims': 1,
    'Continuing_Claims': 1, 'Core_PCE_Price_Index': 1,
    'ECB_Interest_Rate_Decision': 1, 'ECB_Press_Conference': 1,
    'EU_CPI': -1, 'EU_Core_CPI': -1, 'EU_GDP': -1,
    'EU_Unemployment_Rate': 1, 'German_IFO_Business_Climate': -1,
    'German_ZEW_Economic_Sentiment': -1, 'German_GDP': -1,
    'German_CPI': -1, 'BOE_Interest_Rate_Decision': 0,
    'UK_CPI': 0, 'UK_GDP': 0, 'UK_Unemployment_Rate': 0,
    'Michigan_Consumer_Sentiment': -1, 'CB_Consumer_Confidence': -1,
    'ADP_Employment_Change': -1, 'Philadelphia_Fed_Manufacturing_Index': -1,
    'Chicago_PMI': -1, 'Factory_Orders': -1, 'Wholesale_Inventories': -1,
}


# ════════════════════════════════════════════════════════════════
# FONCTION AMPLIFICATION (Sessions 14-15)
# ════════════════════════════════════════════════════════════════

def calculate_amplification_factor(score_ajuste: float, surprise_pct: float) -> float:
    """Facteur amplification surprise (Sessions 14-15)"""
    if score_ajuste < 40:
        return 1.0
    
    surprise_capped = min(surprise_pct, 30.0)
    
    if surprise_capped < 5:
        return 1.0
    elif surprise_capped < 15:
        return 1.0 + (surprise_capped - 5) / 10 * 1.5
    else:
        return 2.5


# ════════════════════════════════════════════════════════════════
# FONCTION IMPACT AVEC PARAMÈTRES (Session 77)
# ════════════════════════════════════════════════════════════════

def calculate_impact_with_params(
    events_cluster: list,
    intercept_multi: float,
    coef_multi: float,
    intercept_single: float,
    coef_single: float
) -> float:
    """
    Calcule impact avec paramètres donnés
    Structure EXACTE Sessions 51-55 + Session 77
    """
    if not events_cluster:
        return 0.0
    
    nb_events = len(events_cluster)
    surprise_max = max(e.get('surprise_pct', 0) for e in events_cluster)
    
    # ÉTAPE 1 : Impacts individuels signés (somme vectorielle)
    impacts_signes = []
    
    for event in events_cluster:
        score_base = event.get('empirical_score', 0)
        surprise_pct = event.get('surprise_pct', 0)
        
        # Ajustement score selon surprise (Session 55)
        score_ajuste = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        # Impact brut selon nombre d'événements
        if nb_events >= 2:
            impact_brut = intercept_multi + coef_multi * score_ajuste
        else:
            impact_brut = intercept_single + coef_single * score_ajuste
        
        # Direction selon FAMILY_SENTIMENT
        famille = event.get('family', 'Unknown')
        direction = FAMILY_SENTIMENT.get(famille, 0)
        
        impact_signe = impact_brut * direction
        impacts_signes.append(impact_signe)
    
    # ÉTAPE 2 : Somme vectorielle
    impact_total = sum(impacts_signes)
    
    # ÉTAPE 3 : Amplification selon surprise
    scores_ajustes = [
        calculate_adjusted_empirical_score(e.get('empirical_score', 0), e.get('surprise_pct', 0))
        for e in events_cluster
    ]
    score_ajuste_moyen = np.mean(scores_ajustes)
    
    amplification = calculate_amplification_factor(score_ajuste_moyen, surprise_max)
    impact_amplifie = impact_total * amplification
    
    # ÉTAPE 4 : Correction vectorielle 0.758
    impact_final = abs(impact_amplifie) * 0.758
    
    return impact_final


# ════════════════════════════════════════════════════════════════
# CHARGEMENT DATASET
# ════════════════════════════════════════════════════════════════

DATASET_PATH = ROOT_DIR / "data" / "movements_strong_session75_v3.csv"
df_movements = pd.read_csv(DATASET_PATH)

# Filtrer 7 mouvements qualité par date (impact max)
dates_qualite = [
    '2024-12-18', '2024-04-10', '2024-02-13', 
    '2024-06-07', '2024-01-05', '2024-12-04', 
    '2025-09-17'
]

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


# ════════════════════════════════════════════════════════════════
# CONNEXION DB + PARAMÈTRES V2
# ════════════════════════════════════════════════════════════════

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Paramètres V2 (Session 77)
INTERCEPT_MULTI_V2 = -18.00
COEF_MULTI_V2 = 0.300
INTERCEPT_SINGLE_V2 = -15.00
COEF_SINGLE_V2 = 0.300


# ════════════════════════════════════════════════════════════════
# TEST FENÊTRES TEMPORELLES
# ════════════════════════════════════════════════════════════════

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
        # ✅ SOLUTION TIMEZONE DÉFINITIVE (Session 79)
        # Utilise timezone_utils.get_event_window_utc()
        start_utc, end_utc = get_event_window_utc(
            row['datetime'],
            window_minutes=window
        )
        
        # Query events avec filtres qualité
        query = f"""
        SELECT 
            e.event_key, e.event_title, e.country,
            e.actual, e.previous, e.estimate, e.forecast,
            e.importance_n,
            AVG(ef.empirical_score) as empirical_score,
            MIN(ef.family) as family
        FROM events e
        INNER JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.ts_utc >= '{start_utc}'
          AND e.ts_utc <= '{end_utc}'
          AND e.importance_n >= 2
          AND ef.empirical_score > 20
          AND e.event_title IS NOT NULL
        GROUP BY 
            e.event_key, e.event_title, e.country,
            e.actual, e.previous, e.estimate, e.forecast,
            e.ts_utc, e.importance_n
        ORDER BY e.ts_utc
        """
        
        df_events = conn.execute(query).fetchdf()
        
        if df_events.empty:
            impacts_pred.append(0.0)
            nb_events_list.append(0)
        else:
            # Construire cluster événements
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
            
            # Calculer impact avec paramètres V2
            impact = calculate_impact_with_params(
                events,
                INTERCEPT_MULTI_V2,
                COEF_MULTI_V2,
                INTERCEPT_SINGLE_V2,
                COEF_SINGLE_V2
            )
            
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


# ════════════════════════════════════════════════════════════════
# RÉSULTATS
# ════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════
# SAUVEGARDE
# ════════════════════════════════════════════════════════════════

OUTPUT_PATH = SCRIPT_DIR / "optimize_window_results_session79_timezone_fix.txt"
with open(OUTPUT_PATH, 'w') as f:
    f.write("OPTIMISATION FENÊTRE TEMPORELLE - SESSION 79 TIMEZONE FIX\n")
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
