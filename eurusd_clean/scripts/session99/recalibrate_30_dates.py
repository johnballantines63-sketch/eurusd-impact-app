"""
RECALIBRATION AMPLIFICATION - 30 DATES (SESSION 99 ÉTENDUE)
============================================================

Session 99 - Extension : Validation sur 30 dates pour tester stabilité coefficients

OBJECTIF :
    Recalibrer formule sur 30 dates (vs 20 en S99, 10 en S98)
    Mesurer stabilité coefficients
    Valider robustesse finale

MÉTHODOLOGIE :
    1. Pour chaque date : trouver amplification OPTIMALE minimisant erreur Planificateur
    2. Régression R²_72h vs amplification optimale
    3. Comparer coefficients avec S98 (10 dates) et S99 (20 dates)
    4. Calculer intervalles de confiance

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
print("🔧 RECALIBRATION AMPLIFICATION - 30 DATES (SESSION 99 ÉTENDUE)")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

# Charger les 30 dates depuis CSV
dates_file = Path(__file__).parent / "dates_validation_30plus.csv"
df_dates = pd.read_csv(dates_file)

print(f"\n📅 Dates chargées : {len(df_dates)}")
print(f"   Dates S98 (10)   : {len(df_dates[df_dates['tested_s98']=='OUI'])}")
print(f"   Dates S99 (10)   : {len(df_dates[df_dates['tested_s98']=='NON'][:10])}")
print(f"   Nouvelles (10)   : {len(df_dates[df_dates['tested_s98']=='NON'][10:])}")

# ============================================================================
# FONCTIONS (identiques S99)
# ============================================================================

def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

def calculate_r_squared_72h(date_str: str, conn) -> float:
    """Calcule R² 72h"""
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
        AND ef.empirical_score > 35
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query, [date_str]).df()
    return df_events

def get_real_impact(date_str: str, event_time_str: str, conn) -> float:
    """Calcule impact réel mesuré sur MT5"""
    try:
        date_obj = datetime.strptime(f"{date_str} {event_time_str}", "%Y-%m-%d %H:%M:%S")
        timestamp_event_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        
        query_event = f"""
        SELECT open as prix_event
        FROM prices_1m
        WHERE datetime = '{timestamp_event_str}+02:00'::TIMESTAMP
        LIMIT 1
        """
        
        result_event = conn.execute(query_event).fetchone()
        if not result_event:
            return 0.0
        prix_event = result_event[0]
        
        timestamp_end = (date_obj + timedelta(minutes=90)).strftime('%Y-%m-%d %H:%M:%S')
        
        query_pic = f"""
        SELECT high, low
        FROM prices_1m
        WHERE datetime >= '{timestamp_event_str}+02:00'::TIMESTAMP
          AND datetime <= '{timestamp_end}+02:00'::TIMESTAMP
        """
        
        df_pic = conn.execute(query_pic).df()
        if df_pic.empty:
            return 0.0
        
        high_max = df_pic['high'].max()
        low_min = df_pic['low'].min()
        
        mouvement_haut = abs(high_max - prix_event) * 10000
        mouvement_bas = abs(low_min - prix_event) * 10000
        
        impact_pips = max(mouvement_haut, mouvement_bas)
        
        return impact_pips
        
    except Exception as e:
        print(f"   ⚠️  Erreur calcul impact : {e}")
        return 0.0

def calculate_planificateur_prediction(events_df: pd.DataFrame, amplification: float) -> float:
    """Calcule prédiction Planificateur V2.4"""
    if events_df.empty:
        return 0.0
    
    base_score_avg = events_df['empirical_score'].mean()
    
    max_surprise = 0
    for _, event in events_df.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score_avg,
        surprise_pct=max_surprise
    )
    
    impact_predicted = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(events_df),
        amplification=amplification
    )
    
    return impact_predicted

def find_optimal_amplification(events_df: pd.DataFrame, impact_real: float) -> float:
    """Trouve amplification optimale qui minimise erreur Planificateur"""
    def objective(amp):
        impact_pred = calculate_planificateur_prediction(events_df, amp)
        error = abs(impact_pred - impact_real)
        return error
    
    result = minimize_scalar(objective, bounds=(0.5, 5.0), method='bounded')
    return result.x

# ============================================================================
# PHASE 1 : CALCULER IMPACTS RÉELS + R² + AMP OPTIMALE
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 1 : Calcul impacts réels + R² + Amplification optimale")
print(f"{'='*80}\n")

conn = get_db_connection()

results = []

for idx, row in df_dates.iterrows():
    date_str = row['date']
    heure_str = row['heure']
    tested_s98 = row['tested_s98']
    
    print(f"📅 {date_str} ({tested_s98})...")
    
    events = load_high_impact_events(date_str, conn)
    
    if events.empty:
        print(f"   ❌ Pas d'événements HIGH\n")
        continue
    
    impact_real = get_real_impact(date_str, heure_str, conn)
    
    if impact_real == 0.0:
        print(f"   ❌ Pas de données prix\n")
        continue
    
    r_squared_72h = calculate_r_squared_72h(date_str, conn)
    amp_optimal = find_optimal_amplification(events, impact_real)
    
    impact_pred_optimal = calculate_planificateur_prediction(events, amp_optimal)
    error_optimal = abs(impact_pred_optimal - impact_real)
    
    impact_pred_baseline = calculate_planificateur_prediction(events, 2.5)
    error_baseline = abs(impact_pred_baseline - impact_real)
    
    print(f"   Impact réel         : {impact_real:.1f} pips")
    print(f"   R² 72h              : {r_squared_72h:.3f}")
    print(f"   Amp OPTIMALE        : {amp_optimal:.3f}")
    print(f"   Erreur (amp opt)    : {error_optimal:.1f} pips")
    print(f"   Erreur (amp 2.5)    : {error_baseline:.1f} pips")
    
    if error_optimal < error_baseline:
        print(f"   ✅ Optimale meilleur : -{(error_baseline - error_optimal):.1f} pips\n")
    else:
        print(f"   ⚠️  Baseline déjà optimal\n")
    
    results.append({
        'date': date_str,
        'tested_s98': tested_s98,
        'impact_real': impact_real,
        'r_squared_72h': r_squared_72h,
        'amp_optimal': amp_optimal,
        'error_optimal': error_optimal,
        'error_baseline': error_baseline
    })

conn.close()

print(f"✅ Dates valides : {len(results)}")

# ============================================================================
# PHASE 2 : RÉGRESSION R² vs AMP OPTIMALE
# ============================================================================

print(f"\n{'='*80}")
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

print(f"\n📐 FORMULE S99-EXT ({len(results)} dates) :")
print(f"   amplification = {a:.4f} × R²_72h + {b:.4f}")

print(f"\n📐 COMPARAISON HISTORIQUE :")
print(f"   S98 (10 dates)  : amp = 1.9938 × R²_72h + 1.4448  (corr: 0.472)")
print(f"   S99 (20 dates)  : amp = 1.2798 × R²_72h + 1.0928  (corr: ~0.37)")
print(f"   S99-EXT (30 dates) : amp = {a:.4f} × R²_72h + {b:.4f}  (corr: {corr:.3f})")

# Stabilité coefficients vs S99
if len(results) >= 20:
    delta_a_vs_s99 = abs(a - 1.2798) / 1.2798 * 100
    delta_b_vs_s99 = abs(b - 1.0928) / 1.0928 * 100
    
    print(f"\n📊 STABILITÉ vs S99 (20 dates) :")
    print(f"   Delta coefficient a : {delta_a_vs_s99:.1f}%")
    print(f"   Delta coefficient b : {delta_b_vs_s99:.1f}%")
    
    if delta_a_vs_s99 < 10 and delta_b_vs_s99 < 10:
        print(f"   ✅ COEFFICIENTS STABLES (<10%)")
    elif delta_a_vs_s99 < 20 and delta_b_vs_s99 < 20:
        print(f"   ⚠️  COEFFICIENTS MODÉRÉMENT STABLES (10-20%)")
    else:
        print(f"   ❌ COEFFICIENTS INSTABLES (>20%)")

# Sauvegarder résultats
output_csv = Path(__file__).parent / "recalibration_30_dates_results.csv"
df.to_csv(output_csv, index=False)

print(f"\n💾 Résultats sauvegardés : {output_csv}")

print("\n" + "="*80)
print("✅ PHASE 2 RECALIBRATION 30 DATES TERMINÉE")
print("="*80)
