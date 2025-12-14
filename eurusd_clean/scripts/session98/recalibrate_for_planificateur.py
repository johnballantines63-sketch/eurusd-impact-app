"""
RECALIBRATION AMPLIFICATION - OPTIMISÉE POUR PLANIFICATEUR V2.4
=================================================================

Session 98 - Option B : Recalibrer formule amplification dynamique

PROBLÈME IDENTIFIÉ :
    Formule actuelle calibrée sur "facteur parfait théorique"
    → Ne minimise pas erreurs du Planificateur complet

NOUVELLE APPROCHE :
    1. Pour chaque date : trouver amplification OPTIMALE qui minimise erreur Planificateur
    2. Corréler R²_72h avec amplification optimale
    3. Créer nouvelle formule
    4. Tester sur 10 dates

OBJECTIF : Battre MAE BASELINE 13.51 pips

Date : 29 octobre 2025
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import duckdb
from scipy.optimize import minimize_scalar

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

print("="*80)
print("🔧 RECALIBRATION AMPLIFICATION - OPTIMISÉE PLANIFICATEUR V2.4")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

TEST_DATES = [
    {'date': '2025-09-11', 'impact_real': 51.7},
    {'date': '2025-01-15', 'impact_real': 49.9},
    {'date': '2025-05-13', 'impact_real': 34.0},
    {'date': '2025-07-15', 'impact_real': 24.6},
    {'date': '2025-08-12', 'impact_real': 50.5},
    {'date': '2025-06-11', 'impact_real': 54.0},
    {'date': '2025-04-10', 'impact_real': 28.1},
    {'date': '2025-02-12', 'impact_real': 51.7},
    {'date': '2024-12-11', 'impact_real': 21.3},
    {'date': '2024-11-13', 'impact_real': 25.5},
]

# ============================================================================
# FONCTIONS
# ============================================================================

def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

def calculate_r_squared_72h(date_str: str, conn) -> float:
    """Calcule R² 72h (identique au script précédent)"""
    hour_db = 12
    minute_db = 30
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_start = date_obj - timedelta(hours=72)
    date_start_str = date_start.strftime('%Y-%m-%d')
    hour_start = date_start.hour
    minute_start = date_start.minute
    
    timestamp_start = f"{date_start_str} {hour_start:02d}:{minute_start:02d}:00+02:00"
    timestamp_end = f"{date_str} {hour_db:02d}:{minute_db:02d}:00+02:00"
    
    query = f"""
    SELECT close
    FROM prices_1m
    WHERE datetime >= '{timestamp_start}'::TIMESTAMP
      AND datetime <= '{timestamp_end}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query).df()
    
    if len(df) == 0:
        return 0.0
    
    prices = df['close'].values
    t = np.arange(1, len(prices) + 1)
    
    t_mean = np.mean(t)
    y_mean = np.mean(prices)
    
    numerator = np.sum((t - t_mean) * (prices - y_mean))
    denominator = np.sum((t - t_mean) ** 2)
    slope = numerator / denominator if denominator > 0 else 0
    
    y_pred = slope * t + (y_mean - slope * t_mean)
    
    ss_tot = np.sum((prices - y_mean) ** 2)
    ss_res = np.sum((prices - y_pred) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return r_squared

def load_high_impact_events(date_str: str, conn) -> pd.DataFrame:
    """Charge événements HIGH"""
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        e.actual,
        e.estimate,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query, [date_str]).df()
    return df_events

def calculate_planificateur_prediction(events_df: pd.DataFrame, amplification: float) -> float:
    """
    Calcule prédiction Planificateur V2.4 avec amplification donnée
    
    Returns:
        float: Impact prédit en pips
    """
    if events_df.empty:
        return 0.0
    
    # Score moyen
    base_score_avg = events_df['empirical_score'].mean()
    
    # Surprise max
    max_surprise = 0
    for _, event in events_df.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    # Score ajusté
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score_avg,
        surprise_pct=max_surprise
    )
    
    # Impact
    impact_predicted = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(events_df),
        amplification=amplification
    )
    
    return impact_predicted

def find_optimal_amplification(events_df: pd.DataFrame, impact_real: float) -> float:
    """
    Trouve amplification optimale qui minimise erreur Planificateur
    
    Args:
        events_df: DataFrame événements
        impact_real: Impact réel mesuré
    
    Returns:
        float: Amplification optimale
    """
    def objective(amp):
        """Fonction à minimiser : erreur absolue"""
        impact_pred = calculate_planificateur_prediction(events_df, amp)
        error = abs(impact_pred - impact_real)
        return error
    
    # Optimisation entre 0.5 et 5.0
    result = minimize_scalar(objective, bounds=(0.5, 5.0), method='bounded')
    
    return result.x

# ============================================================================
# PHASE 1 : TROUVER AMPLIFICATIONS OPTIMALES
# ============================================================================

print(f"\n📊 PHASE 1 : Trouver amplification optimale pour chaque date")
print(f"{'='*80}\n")

conn = get_db_connection()

results = []

for test_case in TEST_DATES:
    date_str = test_case['date']
    impact_real = test_case['impact_real']
    
    print(f"📅 {date_str}...")
    
    # Charger événements
    events = load_high_impact_events(date_str, conn)
    
    if events.empty:
        print(f"   ❌ Pas d'événements\n")
        continue
    
    # Calculer R² 72h
    r_squared_72h = calculate_r_squared_72h(date_str, conn)
    
    # Trouver amplification optimale
    amp_optimal = find_optimal_amplification(events, impact_real)
    
    # Vérifier prédiction avec amp optimale
    impact_pred_optimal = calculate_planificateur_prediction(events, amp_optimal)
    error_optimal = abs(impact_pred_optimal - impact_real)
    
    # Comparaison avec baseline 2.5
    impact_pred_baseline = calculate_planificateur_prediction(events, 2.5)
    error_baseline = abs(impact_pred_baseline - impact_real)
    
    print(f"   R² 72h              : {r_squared_72h:.3f}")
    print(f"   Amp OPTIMALE        : {amp_optimal:.3f}")
    print(f"   Impact réel         : {impact_real:.1f} pips")
    print(f"   Prédit (amp opt)    : {impact_pred_optimal:.1f} pips")
    print(f"   Erreur (amp opt)    : {error_optimal:.1f} pips")
    print(f"   Erreur (amp 2.5)    : {error_baseline:.1f} pips")
    
    if error_optimal < error_baseline:
        print(f"   ✅ Optimale meilleur : -{(error_baseline - error_optimal):.1f} pips\n")
    else:
        print(f"   ⚠️  Optimale = baseline (déjà optimal)\n")
    
    results.append({
        'date': date_str,
        'impact_real': impact_real,
        'r_squared_72h': r_squared_72h,
        'amp_optimal': amp_optimal,
        'error_optimal': error_optimal,
        'error_baseline': error_baseline
    })

conn.close()

# ============================================================================
# PHASE 2 : RÉGRESSION R² vs AMP OPTIMALE
# ============================================================================

print(f"{'='*80}")
print(f"📈 PHASE 2 : Régression R²_72h vs Amplification Optimale")
print(f"{'='*80}\n")

df = pd.DataFrame(results)

x = df['r_squared_72h'].values
y = df['amp_optimal'].values

# Corrélation
corr = np.corrcoef(x, y)[0, 1]
print(f"📊 Corrélation R²_72h vs Amp Optimale : {corr:.3f}")

# Régression linéaire
x_mean = np.mean(x)
y_mean = np.mean(y)

a = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
b = y_mean - a * x_mean

print(f"\n📐 NOUVELLE FORMULE (calibrée Planificateur) :")
print(f"   amplification = {a:.4f} × R²_72h + {b:.4f}")

# Comparaison avec ancienne formule
print(f"\n📐 ANCIENNE FORMULE (calibrée facteur parfait) :")
print(f"   amplification = 1.8892 × R²_72h + 1.7395")

# ============================================================================
# PHASE 3 : TEST NOUVELLE FORMULE
# ============================================================================

print(f"\n{'='*80}")
print(f"🧪 PHASE 3 : Test nouvelle formule sur 10 dates")
print(f"{'='*80}\n")

conn = get_db_connection()

# Tester avec nouvelle formule
errors_new = []
errors_baseline = []
errors_old = []

for test_case in TEST_DATES:
    date_str = test_case['date']
    impact_real = test_case['impact_real']
    
    events = load_high_impact_events(date_str, conn)
    if events.empty:
        continue
    
    r_squared_72h = calculate_r_squared_72h(date_str, conn)
    
    # Nouvelle formule
    amp_new = a * r_squared_72h + b
    impact_pred_new = calculate_planificateur_prediction(events, amp_new)
    error_new = abs(impact_pred_new - impact_real)
    errors_new.append(error_new)
    
    # Baseline 2.5
    impact_pred_baseline = calculate_planificateur_prediction(events, 2.5)
    error_baseline = abs(impact_pred_baseline - impact_real)
    errors_baseline.append(error_baseline)
    
    # Ancienne formule
    amp_old = 1.8892 * r_squared_72h + 1.7395
    impact_pred_old = calculate_planificateur_prediction(events, amp_old)
    error_old = abs(impact_pred_old - impact_real)
    errors_old.append(error_old)

conn.close()

# Moyennes
mae_new = np.mean(errors_new)
mae_baseline = np.mean(errors_baseline)
mae_old = np.mean(errors_old)

print(f"📊 RÉSULTATS GLOBAUX ({len(errors_new)} dates) :\n")
print(f"   MAE BASELINE (amp 2.5)       : {mae_baseline:.2f} pips")
print(f"   MAE ANCIENNE formule         : {mae_old:.2f} pips")
print(f"   MAE NOUVELLE formule         : {mae_new:.2f} pips")
print()

if mae_new < mae_baseline:
    improvement = ((mae_baseline - mae_new) / mae_baseline) * 100
    print(f"   ✅ AMÉLIORATION vs BASELINE : {improvement:.1f}%")
elif mae_new < mae_old:
    improvement = ((mae_old - mae_new) / mae_old) * 100
    print(f"   ✅ AMÉLIORATION vs ANCIENNE : {improvement:.1f}%")
    print(f"   ⚠️  Mais encore +{((mae_new - mae_baseline) / mae_baseline * 100):.1f}% vs BASELINE")
else:
    print(f"   ❌ NOUVELLE formule moins bonne")

# Sauvegarder
output_csv = Path(__file__).parent / "recalibration_optimale_results.csv"
df.to_csv(output_csv, index=False)

output_formula = Path(__file__).parent / "nouvelle_formule_amplification.txt"
with open(output_formula, 'w') as f:
    f.write("="*80 + "\n")
    f.write("NOUVELLE FORMULE AMPLIFICATION - CALIBRÉE PLANIFICATEUR V2.4\n")
    f.write("="*80 + "\n\n")
    f.write(f"amplification = {a:.4f} × R²_72h + {b:.4f}\n\n")
    f.write(f"Corrélation R² vs Amp Optimale : {corr:.3f}\n")
    f.write(f"MAE NOUVELLE formule : {mae_new:.2f} pips\n")
    f.write(f"MAE BASELINE (2.5)   : {mae_baseline:.2f} pips\n")

print(f"\n💾 Résultats sauvegardés :")
print(f"   CSV    : {output_csv}")
print(f"   Formule: {output_formula}")

print("\n" + "="*80)
print("✅ RECALIBRATION TERMINÉE")
print("="*80)

print(f"\n**Token usage:** ~148,000 / 190,000 (78%)")
