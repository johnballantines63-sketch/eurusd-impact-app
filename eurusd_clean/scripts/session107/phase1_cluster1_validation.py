#!/usr/bin/env python3
"""
SESSION 107 - VALIDATION CLUSTER #1 (MANUFACTURING/CONSUMER/EMPLOYMENT)
========================================================================
Méthode validée Session 106 appliquée au Cluster #1

Cluster #1 : 11 occurrences
  - 8 événements (Manufacturing, Consumer, Employment)
  - Heure : 15:45 Bern
  - Pattern : Premier vendredi du mois (ISM Manufacturing PMI)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import importlib.util

print("="*80)
print("SESSION 107 - VALIDATION CLUSTER #1")
print("="*80)
print()

# Setup paths
project_root = Path(__file__).resolve().parents[2]  # Remonte à eurusd_clean/
sys.path.insert(0, str(project_root))

# Load config
spec_config = importlib.util.spec_from_file_location("config", project_root / "app" / "config.py")
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Load formulas (dans fx_impact_app, pas eurusd_clean)
formulas_path = project_root.parent / "fx_impact_app" / "src" / "formulas_validated.py"
spec_formulas = importlib.util.spec_from_file_location(
    "formulas_validated",
    formulas_path
)
formulas_module = importlib.util.module_from_spec(spec_formulas)
spec_formulas.loader.exec_module(formulas_module)

# Dates Cluster #1 (11 occurrences)
CLUSTER1_DATES = [
    '2025-10-01',
    '2025-09-02',
    '2025-07-01',
    '2025-06-02',
    '2025-05-01',
    '2025-04-01',
    '2025-03-03',
    '2025-02-03',
    '2024-12-02',
    '2024-10-01',
    '2024-09-03'
]

print(f"✅ {len(CLUSTER1_DATES)} dates Cluster #1 identifiées")
print()
print("Composition : 8 événements (Manufacturing, Consumer, Employment)")
print("Heure       : 15:45 Bern")
print()

def measure_real_impact_FINAL(event_timestamp_db, date_str):
    """
    Mesure impact réel avec méthode validée Session 106
    
    RÈGLE TIMEZONE :
      Event 15:45 Bern → Query 13:45:00+02:00 (soustraire 2h)
    
    PRIX RÉFÉRENCE :
      OPEN première bougie événement
    
    Args:
        event_timestamp_db: Timestamp DB format "2025-10-01 15:45:00+02:00"
        date_str: Date format "2025-10-01"
    
    Returns:
        dict avec impact_pips, direction, ttr_minutes, peak_price, start_price
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Parse timestamp
    event_dt = pd.to_datetime(event_timestamp_db)
    hour_bern = event_dt.hour      # 15
    minute_bern = event_dt.minute  # 45
    
    # RÈGLE : Soustraire 2h pour query DB
    hour_db = hour_bern - 2  # 15 - 2 = 13
    
    # Timestamp pour query
    event_datetime_db_query = f"{date_str} {hour_db:02d}:{minute_bern:02d}:00+02:00"
    
    print(f"  🔍 Query timestamp : {event_datetime_db_query}")
    
    # Charger prix (5 min avant → 120 min après)
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{event_datetime_db_query}'::TIMESTAMP - INTERVAL '5 minutes'
      AND datetime <= '{event_datetime_db_query}'::TIMESTAMP + INTERVAL '120 minutes'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).fetchdf()
    conn.close()
    
    if len(df_prices) == 0:
        print(f"  ❌ Aucun prix trouvé pour {event_datetime_db_query}")
        return None
    
    print(f"  ✅ {len(df_prices)} bougies 1min chargées")
    
    # Convertir datetime en timezone-aware
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    event_timestamp = pd.to_datetime(event_datetime_db_query)
    
    # Filtrer prix >= événement
    prices_at_event = df_prices[df_prices['datetime'] >= event_timestamp]
    
    if len(prices_at_event) == 0:
        print(f"  ❌ Aucun prix après événement")
        return None
    
    # PRIX RÉFÉRENCE : OPEN première bougie
    first_candle = prices_at_event.iloc[0]
    start_price = first_candle['open']
    
    print(f"  📍 Prix référence (OPEN) : {start_price:.5f}")
    
    # Calculer impacts dans les deux directions
    prices_after = df_prices[df_prices['datetime'] >= event_timestamp].copy()
    prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
    prices_after['pips_low'] = (start_price - prices_after['low']) * 10000
    
    # Trouver direction dominante
    peak_high = prices_after['pips_high'].max()
    peak_low = prices_after['pips_low'].max()
    
    if peak_high > peak_low:
        impact_pips = peak_high
        direction = 1  # UP
        peak_idx = prices_after['pips_high'].idxmax()
        peak_price = prices_after.loc[peak_idx, 'high']
        peak_time = prices_after.loc[peak_idx, 'datetime']
    else:
        impact_pips = peak_low
        direction = -1  # DOWN
        peak_idx = prices_after['pips_low'].idxmax()
        peak_price = prices_after.loc[peak_idx, 'low']
        peak_time = prices_after.loc[peak_idx, 'datetime']
    
    # TTR (Time To Reversal)
    ttr_minutes = (peak_time - event_timestamp).total_seconds() / 60.0
    
    print(f"  📊 Impact mesuré : {impact_pips:.1f} pips {['DOWN','UP'][direction>0]}")
    print(f"  ⏱️  TTR : {ttr_minutes:.1f} minutes")
    print()
    
    return {
        'impact_pips': float(impact_pips),
        'direction': int(direction),
        'ttr_minutes': float(ttr_minutes),
        'peak_price': float(peak_price),
        'start_price': float(start_price),
        'peak_time': peak_time
    }

def optimize_amplification(score_adjusted, num_events, impact_real):
    """
    Trouve amp_optimal qui minimise erreur
    
    Formule Impact D (Session 51) :
      impact_brut = -10.47 + 0.477 × score (si num_events >= 2)
      impact_final = |impact_brut| × amplification × 0.758
    """
    # Calcul impact brut (formule multi-événements)
    impact_brut = -10.47 + 0.477 * score_adjusted
    
    # amp_optimal
    amp_optimal = impact_real / (abs(impact_brut) * 0.758)
    
    return amp_optimal

# =============================================================================
# VALIDATION CLUSTER #1
# =============================================================================

print("="*80)
print("DÉBUT VALIDATION")
print("="*80)
print()

results = []

conn = duckdb.connect(str(db_path), read_only=True)

for date_str in CLUSTER1_DATES:
    print(f"📅 {date_str}")
    print("-"*80)
    
    # Charger événements de cette date
    query_events = f"""
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.previous,
        e.forecast,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
        AND e.country = 'US'
        AND strftime(e.ts_utc, '%H:%M') = '15:45'
    ORDER BY e.ts_utc
    """
    
    events = conn.execute(query_events).fetchdf()
    
    if len(events) == 0:
        print(f"  ⚠️ Aucun événement à 15:45")
        print()
        continue
    
    num_events = len(events)
    print(f"  📦 {num_events} événements chargés")
    
    # Calculer base_score (moyenne empirical_score)
    base_score_avg = events['empirical_score'].mean()
    print(f"  📈 Score base moyen : {base_score_avg:.2f}")
    
    # Calculer surprise max
    surprises = []
    for _, event in events.iterrows():
        actual = event['actual']
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        
        if pd.notna(actual) and estimate and estimate != 0:
            surprise = abs((actual - estimate) / estimate) * 100
            surprises.append(surprise)
    
    max_surprise = max(surprises) if surprises else 0.0
    print(f"  🎯 Surprise max : {max_surprise:.2f}%")
    
    # Score ajusté (Session 55)
    adjusted_score = formulas_module.calculate_adjusted_empirical_score(
        base_score_avg,
        max_surprise
    )
    print(f"  📊 Score ajusté : {adjusted_score:.2f}")
    
    # Prédiction baseline (amp=2.5)
    impact_pred_baseline = formulas_module.calculate_impact_d(
        adjusted_score,
        num_events,
        amplification=2.5
    )
    print(f"  🔮 Impact prédit (baseline amp=2.5) : {impact_pred_baseline:.2f} pips")
    print()
    
    # Mesurer impact réel
    event_timestamp = events.iloc[0]['ts_utc']
    real_result = measure_real_impact_FINAL(event_timestamp, date_str)
    
    if real_result is None:
        print(f"  ❌ Échec mesure impact réel")
        print()
        continue
    
    impact_real = real_result['impact_pips']
    ttr_minutes = real_result['ttr_minutes']
    
    # Calculer amp_optimal
    amp_optimal = optimize_amplification(adjusted_score, num_events, impact_real)
    
    # Impact prédit avec amp_optimal
    impact_pred_optimal = formulas_module.calculate_impact_d(
        adjusted_score,
        num_events,
        amplification=amp_optimal
    )
    
    # Erreurs
    error_baseline = abs(impact_pred_baseline - impact_real)
    error_optimal = abs(impact_pred_optimal - impact_real)
    improvement = error_baseline - error_optimal
    
    # Résumé
    print(f"  📊 RÉSULTATS :")
    print(f"     Impact réel            : {impact_real:.1f} pips")
    print(f"     Error baseline (2.5)   : {error_baseline:.1f} pips")
    print(f"     amp_optimal            : {amp_optimal:.3f}")
    print(f"     Error optimal          : {error_optimal:.1f} pips")
    print(f"     Amélioration           : {improvement:.1f} pips")
    print()
    
    # Stocker résultats
    results.append({
        'date': date_str,
        'num_events': num_events,
        'base_score_avg': base_score_avg,
        'max_surprise': max_surprise,
        'adjusted_score': adjusted_score,
        'impact_pred_baseline': impact_pred_baseline,
        'impact_real': impact_real,
        'error_baseline': error_baseline,
        'amp_optimal': amp_optimal,
        'impact_pred_optimal': impact_pred_optimal,
        'error_optimal': error_optimal,
        'improvement': improvement,
        'ttr_minutes': ttr_minutes
    })

conn.close()

# =============================================================================
# STATISTIQUES GLOBALES
# =============================================================================

print("="*80)
print("STATISTIQUES CLUSTER #1")
print("="*80)
print()

if len(results) == 0:
    print("❌ Aucun résultat disponible")
    sys.exit(1)

df_results = pd.DataFrame(results)

# Sauvegarder résultats
output_file = Path(__file__).parent / "phase1_cluster1_results.csv"
df_results.to_csv(output_file, index=False)
print(f"✅ Résultats sauvegardés : {output_file.name}")
print()

# Statistiques amp_optimal
print("📊 Amplification Optimale :")
print(f"   Moyenne : {df_results['amp_optimal'].mean():.3f}")
print(f"   Médiane : {df_results['amp_optimal'].median():.3f}")
print(f"   Min     : {df_results['amp_optimal'].min():.3f}")
print(f"   Max     : {df_results['amp_optimal'].max():.3f}")
print(f"   Std     : {df_results['amp_optimal'].std():.3f}")
print()

# Statistiques erreur baseline (amp=2.5)
print("📊 Erreur Baseline (amp=2.5) :")
print(f"   MAE     : {df_results['error_baseline'].mean():.2f} pips")
print(f"   RMSE    : {np.sqrt((df_results['error_baseline']**2).mean()):.2f} pips")
print(f"   Médiane : {df_results['error_baseline'].median():.2f} pips")
print(f"   Max     : {df_results['error_baseline'].max():.2f} pips")
print()

# Statistiques erreur optimal
print("📊 Erreur Optimal (amp variable) :")
print(f"   MAE     : {df_results['error_optimal'].mean():.2f} pips")
print(f"   RMSE    : {np.sqrt((df_results['error_optimal']**2).mean()):.2f} pips")
print(f"   Médiane : {df_results['error_optimal'].median():.2f} pips")
print()

# Amélioration
print("📊 Amélioration :")
print(f"   Moyenne : {df_results['improvement'].mean():.2f} pips")
print(f"   Total   : {df_results['improvement'].sum():.2f} pips sur {len(results)} dates")
print()

# Résumé par date
print("="*80)
print("RÉSUMÉ PAR DATE")
print("="*80)
print()

for _, row in df_results.iterrows():
    status = "✅" if row['error_baseline'] < 10 else "⚠️" if row['error_baseline'] < 20 else "❌"
    print(f"{status} {row['date']} : {row['impact_real']:5.1f} pips | "
          f"amp={row['amp_optimal']:.3f} | "
          f"error={row['error_baseline']:.1f}p")

print()
print("="*80)
print("VALIDATION CLUSTER #1 TERMINÉE ✅")
print("="*80)
