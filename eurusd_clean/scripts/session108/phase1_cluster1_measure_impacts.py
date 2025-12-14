#!/usr/bin/env python3
"""
SESSION 108 - PHASE 1 CLUSTER #1 : MESURE IMPACTS RÉELS
=========================================================
Mesure impact réel des 11 dates du Cluster #1 (Manufacturing|Consumer|Employment)
Utilise méthode validée Session 106 (précision 0.1 pips)

Cluster #1 : 8 événements à 15:45 Bern
Dates : 2025-10-01, 2025-09-02, 2025-07-01, 2025-06-02, 2025-05-01,
        2025-04-01, 2025-03-03, 2025-02-03, 2024-12-02, 2024-10-01, 2024-09-03
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta

print("="*80)
print("SESSION 108 - PHASE 1 CLUSTER #1 : MESURE IMPACTS RÉELS")
print("="*80)
print()

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import importlib.util
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# =============================================================================
# FONCTION MESURE IMPACT (MÉTHODE SESSION 106)
# =============================================================================

def measure_real_impact_FINAL(event_timestamp_db, date_str, event_hour_bern=15, event_minute_bern=45):
    """
    Mesure impact réel selon méthode validée Session 106
    
    RÈGLE TIMEZONE :
    - Event 15:45 Bern (CEST +02:00)
    - Query DB : 15:45 - 2h = 13:45+02:00
    
    PRIX RÉFÉRENCE :
    - OPEN de la première bougie événement
    
    FENÊTRE :
    - 5 min avant → 120 min après
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    try:
        # Timestamp événement (Bern)
        event_dt = pd.to_datetime(event_timestamp_db)
        
        # Query DB : Soustraire 2h pour obtenir timestamp DB correct
        hour_db = event_hour_bern - 2
        event_datetime_db_query = f"{date_str} {hour_db:02d}:{event_minute_bern:02d}:00+02:00"
        
        # Charger prix : 5 min avant → 120 min après
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '{event_datetime_db_query}'::TIMESTAMP - INTERVAL '5 minutes'
          AND datetime <= '{event_datetime_db_query}'::TIMESTAMP + INTERVAL '120 minutes'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query).fetchdf()
        
        if len(df_prices) == 0:
            print(f"  ❌ Aucune donnée prix disponible")
            return None
        
        # Timestamp événement pour filtre
        event_timestamp = pd.to_datetime(event_datetime_db_query)
        
        # Filtrer >= événement
        prices_at_event = df_prices[df_prices['datetime'] >= event_timestamp]
        
        if len(prices_at_event) == 0:
            print(f"  ❌ Aucune donnée après événement")
            return None
        
        # PRIX RÉFÉRENCE = OPEN première bougie
        first_candle = prices_at_event.iloc[0]
        start_price = first_candle['open']
        
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
        else:
            impact_pips = peak_low
            direction = -1  # DOWN
            peak_idx = prices_after['pips_low'].idxmax()
            peak_price = prices_after.loc[peak_idx, 'low']
        
        # TTR (Time To Reach)
        peak_datetime = prices_after.loc[peak_idx, 'datetime']
        ttr_minutes = (peak_datetime - event_timestamp).total_seconds() / 60
        
        result = {
            'date': date_str,
            'impact_real_pips': impact_pips,
            'direction': direction,
            'start_price': start_price,
            'peak_price': peak_price,
            'ttr_minutes': ttr_minutes,
            'peak_datetime': peak_datetime,
            'num_candles': len(prices_after)
        }
        
        return result
        
    finally:
        conn.close()

# =============================================================================
# DATES CLUSTER #1
# =============================================================================

# 11 dates avec composition Manufacturing|Consumer|Employment (8 événements, 15:45)
cluster1_dates = [
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

print(f"📅 {len(cluster1_dates)} dates Cluster #1 à mesurer")
print()

# =============================================================================
# MESURE IMPACTS POUR CHAQUE DATE
# =============================================================================

results = []

for date_str in cluster1_dates:
    print(f"📅 {date_str}")
    print("-"*80)
    
    # Timestamp événement (15:45 Bern)
    event_timestamp_db = f"{date_str} 15:45:00+02:00"
    
    # Mesurer
    result = measure_real_impact_FINAL(event_timestamp_db, date_str, 
                                       event_hour_bern=15, event_minute_bern=45)
    
    if result is not None:
        results.append(result)
        
        print(f"  ✅ Impact réel : {result['impact_real_pips']:.2f} pips")
        print(f"  📊 Direction   : {['DOWN','UP'][result['direction']>0]}")
        print(f"  ⏱️ TTR         : {result['ttr_minutes']:.1f} minutes")
        print(f"  📈 Prix départ : {result['start_price']:.5f}")
        print(f"  📈 Prix pic    : {result['peak_price']:.5f}")
        print()
    else:
        print(f"  ❌ Échec mesure")
        print()

# =============================================================================
# CALCUL AMP_OPTIMAL ET STATISTIQUES
# =============================================================================

print("="*80)
print("CALCUL amp_optimal (BASELINE 2.5)")
print("="*80)
print()

# Pour calculer amp_optimal, on a besoin du score_ajusté et nombre d'événements
# Cluster #1 = 8 événements Manufacturing|Consumer|Employment

# Charger événements pour calculer scores
conn = duckdb.connect(str(db_path), read_only=True)

for res in results:
    date_str = res['date']
    
    # Charger événements
    query_events = f"""
    SELECT e.*, f.normalized_name as family_name
    FROM events e
    LEFT JOIN families f ON e.family = f.id
    WHERE DATE(e.ts_utc) = DATE('{date_str}')
      AND e.importance = 'HIGH'
      AND f.normalized_name IN ('Manufacturing', 'Consumer', 'Employment')
      AND EXTRACT(HOUR FROM e.ts_utc) = 13
      AND EXTRACT(MINUTE FROM e.ts_utc) = 45
    ORDER BY e.score DESC
    """
    
    df_events = conn.execute(query_events).fetchdf()
    
    if len(df_events) == 0:
        print(f"⚠️ {date_str} : Aucun événement trouvé")
        continue
    
    # Calculer score_ajusté (moyenne des scores)
    avg_score = df_events['score'].mean()
    
    # Calculer surprise max
    surprises = []
    for _, event in df_events.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
            surprises.append(surprise_pct)
    
    max_surprise = max(surprises) if surprises else 0
    
    # Formule impact_D (Session 51-55)
    # impact_D = score_ajusté × sqrt(nb_events) × amplification
    num_events = len(df_events)
    impact_pred_baseline = avg_score * np.sqrt(num_events) * 2.5
    
    # Calculer amp_optimal
    impact_real = res['impact_real_pips']
    amp_optimal = impact_real / (avg_score * np.sqrt(num_events))
    
    # Erreur baseline
    error_baseline = abs(impact_pred_baseline - impact_real)
    
    # Ajouter au résultat
    res['num_events'] = num_events
    res['score_ajusté'] = avg_score
    res['max_surprise'] = max_surprise
    res['impact_pred_baseline'] = impact_pred_baseline
    res['amp_optimal'] = amp_optimal
    res['error_baseline'] = error_baseline
    
    print(f"📅 {date_str}")
    print(f"   Score ajusté       : {avg_score:.2f}")
    print(f"   Surprise max       : {max_surprise:.2f}%")
    print(f"   Impact réel        : {impact_real:.2f} pips")
    print(f"   Impact baseline    : {impact_pred_baseline:.2f} pips")
    print(f"   amp_optimal        : {amp_optimal:.3f}")
    print(f"   Erreur baseline    : {error_baseline:.2f} pips")
    print()

conn.close()

# =============================================================================
# STATISTIQUES GLOBALES
# =============================================================================

print("="*80)
print("STATISTIQUES CLUSTER #1 (11 dates)")
print("="*80)
print()

df_results = pd.DataFrame(results)

if len(df_results) > 0:
    print("📊 Distribution amp_optimal :")
    print(f"   Moyenne  : {df_results['amp_optimal'].mean():.3f}")
    print(f"   Médiane  : {df_results['amp_optimal'].median():.3f}")
    print(f"   Min      : {df_results['amp_optimal'].min():.3f}")
    print(f"   Max      : {df_results['amp_optimal'].max():.3f}")
    print(f"   Std      : {df_results['amp_optimal'].std():.3f}")
    print()
    
    print("📊 Performance baseline (amp=2.5) :")
    print(f"   MAE      : {df_results['error_baseline'].mean():.2f} pips")
    print(f"   RMSE     : {np.sqrt((df_results['error_baseline']**2).mean()):.2f} pips")
    print()
    
    # Tableau complet
    print("📊 Résultats par date :")
    print("-"*80)
    print(df_results[['date', 'impact_real_pips', 'amp_optimal', 'max_surprise', 'error_baseline']].to_string(index=False))
    print()
    
    # Sauvegarder
    output_file = Path(__file__).parent / "phase1_cluster1_results.csv"
    df_results.to_csv(output_file, index=False)
    print(f"✅ Résultats sauvegardés : {output_file.name}")
    print()

print("="*80)
print("PHASE 1 CLUSTER #1 TERMINÉE ✅")
print("="*80)
