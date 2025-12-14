#!/usr/bin/env python3
"""
VALIDATION FINALE - SESSION 79 TIMEZONE FIX
===========================================

Valide formules V2 avec fenêtre optimale et timezone fix.

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
import re

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

# Import fonctions validées + timezone utils
from src.formulas_validated import calculate_adjusted_empirical_score
from src.utils.timezone_utils import get_event_window_utc

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"

print("\n" + "="*70)
print("VALIDATION FINALE - SESSION 79 TIMEZONE FIX")
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
# LIRE FENÊTRE OPTIMALE
# ════════════════════════════════════════════════════════════════

WINDOW_FILE = SCRIPT_DIR / "optimize_window_results_session79_timezone_fix.txt"
if WINDOW_FILE.exists():
    with open(WINDOW_FILE, 'r') as f:
        content = f.read()
    match = re.search(r'Fenêtre optimale : ±(\d+) min', content)
    OPTIMAL_WINDOW = int(match.group(1)) if match else 30
    print(f"📂 Fenêtre optimale : ±{OPTIMAL_WINDOW} min\n")
else:
    OPTIMAL_WINDOW = 30
    print(f"⚠️  Fenêtre par défaut : ±{OPTIMAL_WINDOW} min\n")


# ════════════════════════════════════════════════════════════════
# PARAMÈTRES V2
# ════════════════════════════════════════════════════════════════

INTERCEPT_MULTI_V2 = -18.00
COEF_MULTI_V2 = 0.300
INTERCEPT_SINGLE_V2 = -15.00
COEF_SINGLE_V2 = 0.300


# ════════════════════════════════════════════════════════════════
# CONNEXION DB
# ════════════════════════════════════════════════════════════════

conn = duckdb.connect(str(DB_PATH), read_only=True)


# ════════════════════════════════════════════════════════════════
# TEST 1 : CAS RÉFÉRENCE 11 SEPTEMBRE 2025
# ════════════════════════════════════════════════════════════════

print("🎯 TEST 1 : CAS RÉFÉRENCE 11 SEPTEMBRE 2025")
print("="*70 + "\n")

# ✅ SOLUTION TIMEZONE DÉFINITIVE (Session 79)
# 11 septembre 14:30 Berne (UTC+2 été) = 12:30 UTC
start_utc, end_utc = get_event_window_utc('2025-09-11 14:30:00+02:00', 30)

query_11sept = f"""
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
  AND e.country = 'US'
  AND e.importance_n >= 2
  AND ef.empirical_score > 20
  AND e.event_title IS NOT NULL
GROUP BY 
    e.event_key, e.event_title, e.country,
    e.actual, e.previous, e.estimate, e.forecast,
    e.ts_utc, e.importance_n
ORDER BY e.ts_utc
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

# Calculer impact 11 septembre
impact_pred_11sept = calculate_impact_with_params(
    events_11sept,
    INTERCEPT_MULTI_V2,
    COEF_MULTI_V2,
    INTERCEPT_SINGLE_V2,
    COEF_SINGLE_V2
)

impact_real_11sept = 53.0
mae_11sept = abs(impact_pred_11sept - impact_real_11sept)

print(f"Événements : {len(events_11sept)}")
print(f"Impact prédit : {impact_pred_11sept:.1f} pips")
print(f"Impact réel   : {impact_real_11sept:.1f} pips")
print(f"MAE           : {mae_11sept:.1f} pips")
print(f"Statut        : {'✅ EXCELLENT' if mae_11sept < 10 else '⚠️ À AMÉLIORER'}\n")


# ════════════════════════════════════════════════════════════════
# TEST 2 : DATASET SESSION 75
# ════════════════════════════════════════════════════════════════

print("🎯 TEST 2 : DATASET SESSION 75")
print("="*70 + "\n")

DATASET_PATH = ROOT_DIR / "data" / "movements_strong_session75_v3.csv"
df_movements = pd.read_csv(DATASET_PATH)

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

impacts_pred_s75 = []
impacts_real_s75 = []

for _, row in df_selected.iterrows():
    # ✅ SOLUTION TIMEZONE DÉFINITIVE (Session 79)
    start_utc, end_utc = get_event_window_utc(
        row['datetime'],
        window_minutes=OPTIMAL_WINDOW
    )
    
    # Query events
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
        impacts_pred_s75.append(0.0)
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
        
        # Calculer impact
        impact = calculate_impact_with_params(
            events,
            INTERCEPT_MULTI_V2,
            COEF_MULTI_V2,
            INTERCEPT_SINGLE_V2,
            COEF_SINGLE_V2
        )
        impacts_pred_s75.append(impact)
    
    impacts_real_s75.append(row['impact_pips'])
    
    # Afficher ligne
    mae_mvt = abs(impacts_pred_s75[-1] - impacts_real_s75[-1])
    print(f"{row['date']} | Réel: {row['impact_pips']:.1f} | Prédit: {impacts_pred_s75[-1]:.1f} | MAE: {mae_mvt:.1f}")

conn.close()


# ════════════════════════════════════════════════════════════════
# MÉTRIQUES FINALES
# ════════════════════════════════════════════════════════════════

mae_s75 = np.mean([abs(p - r) for p, r in zip(impacts_pred_s75, impacts_real_s75)])
mae_s77 = 87.5
target = 50.0

print(f"\n📊 MÉTRIQUES SESSION 75")
print("="*70)
print(f"MAE Session 77 : {mae_s77:.1f} pips")
print(f"MAE Session 79 : {mae_s75:.1f} pips")
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


# ════════════════════════════════════════════════════════════════
# SAUVEGARDE
# ════════════════════════════════════════════════════════════════

OUTPUT_PATH = SCRIPT_DIR / "validation_finale_session79_timezone_fix.txt"
with open(OUTPUT_PATH, 'w') as f:
    f.write("VALIDATION FINALE - SESSION 79 TIMEZONE FIX\n")
    f.write("="*70 + "\n\n")
    f.write(f"Fenêtre optimale : ±{OPTIMAL_WINDOW} min\n")
    f.write(f"MAE 11 septembre : {mae_11sept:.1f} pips\n")
    f.write(f"MAE Session 75   : {mae_s75:.1f} pips\n")
    f.write(f"Statut           : {status}\n\n")
    f.write("DÉTAILS PAR MOUVEMENT\n")
    f.write("-"*70 + "\n")
    for i, row in df_selected.iterrows():
        mae_mvt = abs(impacts_pred_s75[i] - impacts_real_s75[i])
        f.write(f"{row['date']} | Réel: {impacts_real_s75[i]:.1f} | Prédit: {impacts_pred_s75[i]:.1f} | MAE: {mae_mvt:.1f}\n")

print(f"💾 Résultats sauvegardés : {OUTPUT_PATH.name}\n")

print("="*70)
print("✅ VALIDATION FINALE TERMINÉE")
print("="*70 + "\n")
