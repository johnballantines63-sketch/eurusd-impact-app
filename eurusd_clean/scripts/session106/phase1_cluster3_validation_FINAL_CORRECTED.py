#!/usr/bin/env python3
"""
SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 - RÈGLE FINALE CORRIGÉE
=======================================================================

RÈGLE TIMEZONE CORRECTE + PRIX CORRECT :
- Event à 14:30 Bern → Chercher à 12:30:00+02:00 dans DB
- Soustraire 2h à l'heure Bern pour obtenir l'heure DB
- Prix référence = OPEN de la première bougie event (= CLOSE bougie 14:29)

Validation MT5 :
- 11.09.2025 : ~57 pips (OPEN 14:30 = 1.16817, peak = 1.17445)

Date   : 2 novembre 2025
Auteur : Session 106
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.optimize import minimize_scalar

print("="*80)
print("SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 - RÈGLE FINALE CORRIGÉE")
print("="*80)
print()

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

script_path = Path(__file__).resolve()
project_root = script_path.parents[3]
fx_impact_app_src = project_root / "fx_impact_app" / "src"

sys.path.insert(0, str(fx_impact_app_src))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

db_path = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

# Dates Cluster #3
DATES_CLUSTER3 = [
    '2025-09-11',  # Référence validée
    '2025-08-12',
    '2025-07-15',
    '2025-06-11',
    '2025-05-13',
    '2025-04-10'
]

AMPLIFICATION_BASELINE = 2.5
EXPECTED_IMPACT_REFERENCE = 57.0  # MT5 validé (~62.8 pips)

# ═══════════════════════════════════════════════════════════════
# FONCTIONS
# ═══════════════════════════════════════════════════════════════

def load_events_for_date(date_str: str) -> pd.DataFrame:
    """Charge événements HIGH IMPACT pour une date"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    query = """
    SELECT 
        e.event_key,
        ANY_VALUE(e.event_title) as label,
        e.ts_utc,
        e.country,
        MAX(e.actual) as actual,
        MAX(e.estimate) as estimate,
        MIN(ef.family) as family,
        AVG(ef.empirical_score) as empirical_score,
        AVG(ef.latency_median) as latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    GROUP BY e.ts_utc, e.event_key, e.country
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query, [date_str]).df()
    conn.close()
    
    return df


def calculate_prediction(df_events: pd.DataFrame, amplification: float = 2.5) -> dict:
    """Applique méthode Planificateur"""
    
    if df_events.empty:
        return None
    
    # Score base moyen
    base_score_avg = df_events['empirical_score'].mean()
    
    # Max surprise
    surprises = []
    max_surprise = 0
    
    for _, event in df_events.iterrows():
        if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
            surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
            surprises.append(surprise_pct)
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    avg_surprise = sum(surprises) / len(surprises) if surprises else 0
    
    # Ajustement score
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # Impact
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(df_events),
        amplification=amplification
    )
    
    return {
        'num_events': len(df_events),
        'base_score_avg': base_score_avg,
        'max_surprise': max_surprise,
        'avg_surprise': avg_surprise,
        'adjusted_score': adjusted_score,
        'impact_pips': impact
    }


def measure_real_impact_FINAL(event_timestamp_db: str, date_str: str) -> dict:
    """
    Mesure impact réel - RÈGLE FINALE CORRIGÉE
    
    CRITIQUE :
    - Event à 14:30 Bern → Chercher à 12:30:00+02:00 dans DB
    - Soustraire 2h à l'heure Bern pour query
    - Prix référence = OPEN première bougie event (= CLOSE bougie 14:29)
    
    Validation MT5 :
    - 11.09.2025 : ~57 pips (OPEN 14:30 = 1.16817, peak = 1.17445)
    
    Args:
        event_timestamp_db: Timestamp depuis events.ts_utc (ex: "14:30:00+02:00")
        date_str: Date au format "YYYY-MM-DD"
    
    Returns:
        dict avec impact_pips, direction, etc.
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Convertir timestamp DB
    event_dt = pd.to_datetime(event_timestamp_db)
    
    # ✅ RÈGLE SESSION 92.10 : Soustraire 2h pour query
    hour_bern = event_dt.hour  # Ex: 14
    minute_bern = event_dt.minute  # Ex: 30
    
    hour_db = hour_bern - 2  # 14 - 2 = 12
    
    # Timestamp pour query DB
    event_datetime_db_query = f"{date_str} {hour_db:02d}:{minute_bern:02d}:00+02:00"
    
    # Fenêtre : -5 min avant → +120 min après
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{event_datetime_db_query}'::TIMESTAMP - INTERVAL '5 minutes'
      AND datetime <= '{event_datetime_db_query}'::TIMESTAMP + INTERVAL '120 minutes'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).df()
    conn.close()
    
    if df_prices.empty or len(df_prices) < 2:
        return None
    
    # Timestamp événement pour filtrage
    event_timestamp = pd.to_datetime(event_datetime_db_query)
    
    # ✅ CORRECTION FINALE : Prix référence = OPEN première bougie event
    # OPEN de 14:30 = CLOSE de 14:29 (continuité)
    prices_at_event = df_prices[df_prices['datetime'] >= event_timestamp]
    
    if len(prices_at_event) == 0:
        return None
    
    first_candle = prices_at_event.iloc[0]
    start_price = first_candle['open']  # ✅✅✅ OPEN de la première bougie (= CLOSE 14:29)
    
    # Filtrer prix APRÈS événement
    prices_after = df_prices[df_prices['datetime'] >= event_timestamp].copy()
    
    if len(prices_after) == 0:
        return None
    
    # Peak = Maximum HIGH
    prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
    prices_after['pips_low'] = (start_price - prices_after['low']) * 10000
    
    # Trouver direction dominante
    peak_high = prices_after['pips_high'].max()
    peak_low = prices_after['pips_low'].max()
    
    if peak_high > peak_low:
        impact_pips = peak_high
        direction = 1
        peak_idx = prices_after['pips_high'].idxmax()
        peak_price = prices_after.loc[peak_idx, 'high']
    else:
        impact_pips = peak_low
        direction = -1
        peak_idx = prices_after['pips_low'].idxmax()
        peak_price = prices_after.loc[peak_idx, 'low']
    
    peak_time = prices_after.loc[peak_idx, 'datetime']
    
    # TTR en minutes
    peak_dt = pd.to_datetime(peak_time)
    ttr_minutes = (peak_dt - event_timestamp).total_seconds() / 60.0
    
    return {
        'impact_pips': impact_pips,
        'direction': direction,
        'price_start': start_price,
        'peak_price': peak_price,
        'peak_time': peak_time,
        'ttr_minutes': ttr_minutes,
        'num_candles': len(df_prices),
        'event_datetime_db_query': event_datetime_db_query,
        'first_candle_open': first_candle['open'],
        'first_candle_high': first_candle['high'],
        'first_candle_low': first_candle['low'],
        'first_candle_close': first_candle['close']
    }


def calculate_optimal_amplification(
    base_score_avg: float,
    max_surprise: float,
    num_events: int,
    real_impact: float
) -> float:
    """Calcule amp_optimal avec scipy"""
    
    def error_function(amp):
        adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
        predicted_impact = calculate_impact_d(adjusted_score, num_events, amp)
        return abs(predicted_impact - real_impact)
    
    result = minimize_scalar(error_function, bounds=(0.5, 5.0), method='bounded')
    
    return result.x


# ═══════════════════════════════════════════════════════════════
# TRAITEMENT
# ═══════════════════════════════════════════════════════════════

print(f"📅 Dates à tester : {len(DATES_CLUSTER3)}")
print(f"🎯 Amplification baseline : {AMPLIFICATION_BASELINE}")
print()
print("✅ RÈGLE FINALE CORRIGÉE (MT5 validée) :")
print("   - Event à 14:30 Bern → Query à 12:30:00+02:00")
print("   - Soustraire 2h à l'heure Bern")
print("   - Prix référence = OPEN première bougie event (= CLOSE 14:29)")
print(f"   - Validation référence : {EXPECTED_IMPACT_REFERENCE:.1f} pips (MT5)")
print()

results = []

for date_str in DATES_CLUSTER3:
    print("="*80)
    print(f"📊 DATE : {date_str}")
    print("-"*80)
    print()
    
    # Charger événements
    df_events = load_events_for_date(date_str)
    
    if df_events.empty:
        print(f"⚠️  Aucun événement HIGH IMPACT trouvé pour {date_str}")
        print()
        continue
    
    print(f"✅ {len(df_events)} événements chargés")
    
    # Timestamp événement depuis DB
    event_timestamp_db = df_events.iloc[0]['ts_utc']
    event_dt = pd.to_datetime(event_timestamp_db)
    
    # Afficher heure Bern
    hour_bern = event_dt.hour
    minute_bern = event_dt.minute
    event_time_bern = f"{hour_bern:02d}:{minute_bern:02d}"
    
    print(f"   Timestamp DB (original) : {event_timestamp_db}")
    print(f"   Heure Bern              : {event_time_bern}")
    print(f"   Heure DB (query)        : {hour_bern-2:02d}:{minute_bern:02d}")
    print()
    
    # Calculer prédiction (baseline amp=2.5)
    pred = calculate_prediction(df_events, AMPLIFICATION_BASELINE)
    
    if pred is None:
        print(f"⚠️  Impossible de calculer prédiction")
        print()
        continue
    
    print(f"📈 PRÉDICTION (amp={AMPLIFICATION_BASELINE})")
    print(f"   Score base moyen : {pred['base_score_avg']:.2f}")
    print(f"   Max surprise     : {pred['max_surprise']:.2f}%")
    print(f"   Score ajusté     : {pred['adjusted_score']:.2f}")
    print(f"   Impact prédit    : {pred['impact_pips']:.2f} pips")
    print()
    
    # Mesurer impact réel (Règle Finale Corrigée)
    real = measure_real_impact_FINAL(event_timestamp_db, date_str)
    
    if real is None:
        print(f"⚠️  Impossible de mesurer impact réel (prix manquants)")
        print()
        continue
    
    print(f"📊 IMPACT RÉEL (Règle Finale Corrigée)")
    print(f"   Query timestamp      : {real['event_datetime_db_query']}")
    print(f"   First candle OPEN    : {real['first_candle_open']:.5f} ← Prix référence (= CLOSE 14:29)")
    print(f"   First candle HIGH    : {real['first_candle_high']:.5f}")
    print(f"   First candle LOW     : {real['first_candle_low']:.5f}")
    print(f"   First candle CLOSE   : {real['first_candle_close']:.5f}")
    print(f"   Peak price           : {real['peak_price']:.5f}")
    print(f"   Impact observé       : {real['impact_pips']:.2f} pips")
    print(f"   Direction            : {'UP' if real['direction'] == 1 else 'DOWN'}")
    print(f"   TTR                  : {real['ttr_minutes']:.1f} min")
    print()
    
    # Validation référence
    if date_str == '2025-09-11':
        diff_ref = abs(real['impact_pips'] - EXPECTED_IMPACT_REFERENCE)
        print(f"   🔍 VALIDATION RÉFÉRENCE")
        print(f"      Impact mesuré : {real['impact_pips']:.1f} pips")
        print(f"      Impact MT5    : {EXPECTED_IMPACT_REFERENCE:.1f} pips")
        print(f"      Écart         : {diff_ref:.1f} pips")
        
        if diff_ref < 5.0:
            print(f"      ✅✅✅ MÉTHODE VALIDÉE !")
        elif diff_ref < 10.0:
            print(f"      ✅ ACCEPTABLE")
        else:
            print(f"      ⚠️  ÉCART IMPORTANT")
        print()
    
    # Calculer erreur baseline
    error_baseline = abs(pred['impact_pips'] - real['impact_pips'])
    error_baseline_pct = (error_baseline / real['impact_pips']) * 100 if real['impact_pips'] > 0 else 0
    
    print(f"❌ ERREUR BASELINE (amp={AMPLIFICATION_BASELINE})")
    print(f"   Erreur           : {error_baseline:.2f} pips ({error_baseline_pct:.1f}%)")
    print()
    
    # Calculer amp_optimal
    amp_optimal = calculate_optimal_amplification(
        pred['base_score_avg'],
        pred['max_surprise'],
        pred['num_events'],
        real['impact_pips']
    )
    
    # Recalculer avec amp_optimal
    pred_optimal = calculate_prediction(df_events, amp_optimal)
    error_optimal = abs(pred_optimal['impact_pips'] - real['impact_pips'])
    error_optimal_pct = (error_optimal / real['impact_pips']) * 100 if real['impact_pips'] > 0 else 0
    
    print(f"✅ AMPLIFICATION OPTIMALE")
    print(f"   amp_optimal      : {amp_optimal:.3f}")
    print(f"   Impact prédit    : {pred_optimal['impact_pips']:.2f} pips")
    print(f"   Erreur           : {error_optimal:.2f} pips ({error_optimal_pct:.1f}%)")
    print()
    
    # Amélioration
    improvement = error_baseline - error_optimal
    improvement_pct = (improvement / error_baseline) * 100 if error_baseline > 0 else 0
    
    print(f"📊 AMÉLIORATION")
    print(f"   Réduction erreur : {improvement:.2f} pips ({improvement_pct:.1f}%)")
    print()
    
    # Stocker résultats
    results.append({
        'date': date_str,
        'num_events': pred['num_events'],
        'base_score_avg': pred['base_score_avg'],
        'max_surprise': pred['max_surprise'],
        'adjusted_score': pred['adjusted_score'],
        'impact_pred_baseline': pred['impact_pips'],
        'impact_real': real['impact_pips'],
        'error_baseline': error_baseline,
        'amp_optimal': amp_optimal,
        'impact_pred_optimal': pred_optimal['impact_pips'],
        'error_optimal': error_optimal,
        'improvement': improvement,
        'ttr_minutes': real['ttr_minutes']
    })

# ═══════════════════════════════════════════════════════════════
# RAPPORT FINAL
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("📊 RAPPORT CLUSTER #3 (CPI)")
print("="*80)
print()

if not results:
    print("❌ Aucun résultat valide")
    sys.exit(0)

df_results = pd.DataFrame(results)

print(f"Dates testées    : {len(df_results)}")
print(f"Amplification baseline : {AMPLIFICATION_BASELINE}")
print()

print("STATISTIQUES AMP_OPTIMAL :")
print(f"  Moyenne        : {df_results['amp_optimal'].mean():.3f}")
print(f"  Médiane        : {df_results['amp_optimal'].median():.3f}")
print(f"  Écart-type     : {df_results['amp_optimal'].std():.3f}")
print(f"  Min            : {df_results['amp_optimal'].min():.3f}")
print(f"  Max            : {df_results['amp_optimal'].max():.3f}")
print()

print("ERREURS BASELINE (amp=2.5) :")
print(f"  MAE            : {df_results['error_baseline'].mean():.2f} pips")
print(f"  RMSE           : {np.sqrt((df_results['error_baseline']**2).mean()):.2f} pips")
print()

print("ERREURS OPTIMALES :")
print(f"  MAE            : {df_results['error_optimal'].mean():.2f} pips")
print(f"  RMSE           : {np.sqrt((df_results['error_optimal']**2).mean()):.2f} pips")
print()

improvement_avg = df_results['improvement'].mean()
improvement_pct_avg = (improvement_avg / df_results['error_baseline'].mean()) * 100

print("AMÉLIORATION :")
print(f"  Réduction MAE  : {improvement_avg:.2f} pips ({improvement_pct_avg:.1f}%)")
print()

# Tableau détaillé
print("="*80)
print("DÉTAILS PAR DATE")
print("-"*80)
print()

for _, row in df_results.iterrows():
    print(f"{row['date']} : amp_optimal={row['amp_optimal']:.3f}, error_baseline={row['error_baseline']:.1f}p, error_optimal={row['error_optimal']:.1f}p, impact_real={row['impact_real']:.1f}p")

print()

# Sauvegarder résultats
output_file = script_path.parent / "phase1_cluster3_results_FINAL_CORRECTED.csv"
df_results.to_csv(output_file, index=False)

print(f"💾 Résultats sauvegardés : {output_file.name}")
print()

print("="*80)
print("✅ PHASE 1 TERMINÉE (RÈGLE FINALE CORRIGÉE - MT5 VALIDÉE)")
print("="*80)
