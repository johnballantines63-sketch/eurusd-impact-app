#!/usr/bin/env python3
"""
SESSION 105 - MESURES CLUSTER #3 - 6 DATES
============================================

Mesure impact réel + métriques contextuelles pour toutes les dates Cluster #3
Méthode : Session 102 validée (56.8 pips exact sur 11.09)

Auteur : André Valentin
Date   : 2 novembre 2025
Phase  : 3.2 (Mesures empiriques)
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import importlib.util
import json

print("="*80)
print("SESSION 105 - MESURES CLUSTER #3 - 6 DATES")
print("="*80)
print()

# Configuration Cluster #3
DATES_CLUSTER3 = [
    '2025-09-11',  # Référence (56.8 pips validé)
    '2025-08-12',  # Test 1
    '2025-07-15',  # Test 2
    '2025-06-11',  # Test 3
    '2025-05-13',  # Test 4
    '2025-04-10'   # Test 5
]

EVENT_TIME_DB = "12:30:00"  # 14:30 Bern = 12:30+02:00 DB
WINDOW_MINUTES = 120

print(f"📊 Cluster #3 (CPI) : {len(DATES_CLUSTER3)} dates à mesurer")
print(f"⏰ Heure événement DB : {EVENT_TIME_DB}+02:00")
print(f"🔍 Fenêtre analyse : {WINDOW_MINUTES} minutes")
print()

# Setup paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import config (méthode importlib - pas besoin venv)
spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

print(f"📂 Database : {db_path}")
print()

def measure_impact_corrected(date):
    """
    Méthode Session 102 validée (56.8 pips exact)
    """
    query = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{date} {EVENT_TIME_DB}+02:00'::TIMESTAMP - INTERVAL '1 minute'
      AND datetime < '{date} {EVENT_TIME_DB}+02:00'::TIMESTAMP + INTERVAL '{WINDOW_MINUTES} minutes'
    ORDER BY datetime
    """
    
    with duckdb.connect(str(db_path), read_only=True) as conn:
        prices_df = conn.execute(query).fetchdf()
    
    if len(prices_df) < 10:
        return None
    
    bern_tz = pytz.timezone('Europe/Zurich')
    event_dt = bern_tz.localize(
        datetime.strptime(f"{date} {EVENT_TIME_DB}", "%Y-%m-%d %H:%M:%S")
    )
    
    # Prix départ (candle avant)
    prices_before = prices_df[prices_df['datetime'] < event_dt]
    if len(prices_before) == 0:
        return None
    
    price_start = prices_before.iloc[-1]['close']
    time_start = prices_before.iloc[-1]['datetime']
    
    # Pics après
    prices_after = prices_df[prices_df['datetime'] >= event_dt]
    if len(prices_after) == 0:
        return None
    
    price_max = prices_after['close'].max()
    price_min = prices_after['close'].min()
    idx_max = prices_after['close'].idxmax()
    idx_min = prices_after['close'].idxmin()
    
    # Direction (plus grand mouvement)
    move_up = abs(price_max - price_start)
    move_down = abs(price_start - price_min)
    
    if move_up > move_down:
        direction = "UP"
        price_peak = price_max
        time_peak = prices_after.loc[idx_max, 'datetime']
        impact_pips = (price_peak - price_start) * 10000
    else:
        direction = "DOWN"
        price_peak = price_min
        time_peak = prices_after.loc[idx_min, 'datetime']
        impact_pips = (price_start - price_peak) * 10000
    
    duration_minutes = (time_peak - event_dt).total_seconds() / 60
    
    return {
        'impact_pips': float(impact_pips),
        'direction': direction,
        'price_start': float(price_start),
        'price_peak': float(price_peak),
        'time_peak': str(time_peak),
        'duration_minutes': float(duration_minutes)
    }

def load_events(date):
    """
    Charge événements pour une date
    """
    query = f"""
    SELECT 
        e.event_key,
        e.actual,
        e.estimate,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.country = 'US'
      AND DATE(e.ts_utc) = '{date}'
      AND ef.empirical_score > 40
    ORDER BY e.event_key
    """
    
    with duckdb.connect(str(db_path), read_only=True) as conn:
        events_df = conn.execute(query).fetchdf()
    
    return events_df

def calculate_adjusted_score(events_df):
    """
    Calcul score ajusté (formule Sessions 51-55)
    Simplifié : moyenne pondérée par surprise
    """
    if len(events_df) == 0:
        return 0.0
    
    # Calcul surprise
    events_df['surprise'] = abs(
        (events_df['actual'] - events_df['estimate']) / events_df['estimate']
    )
    
    # Score ajusté = moyenne empirical_score pondérée par (1 + surprise)
    weights = 1 + events_df['surprise']
    score_adjusted = np.average(
        events_df['empirical_score'], 
        weights=weights
    )
    
    return float(score_adjusted)

def calculate_r2_72h(date):
    """
    R² régression linéaire 72h pré-événement
    """
    event_dt_str = f"{date} {EVENT_TIME_DB}"
    event_dt = datetime.strptime(event_dt_str, "%Y-%m-%d %H:%M:%S")
    start_dt = event_dt - timedelta(hours=72)
    
    query = f"""
    SELECT close 
    FROM prices_1m
    WHERE datetime >= '{start_dt.strftime('%Y-%m-%d %H:%M:%S')}+02:00'::TIMESTAMP
      AND datetime < '{event_dt_str}+02:00'::TIMESTAMP
    ORDER BY datetime
    """
    
    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            prices_df = conn.execute(query).fetchdf()
        
        if len(prices_df) < 50:
            return 0.0
        
        X = np.arange(len(prices_df)).reshape(-1, 1)
        y = prices_df['close'].values
        
        # Régression linéaire manuelle
        x_mean = X.mean()
        y_mean = y.mean()
        
        numerator = np.sum((X.flatten() - x_mean) * (y - y_mean))
        denominator = np.sum((X.flatten() - x_mean) ** 2)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        y_pred = slope * X.flatten() + intercept
        
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return float(max(0.0, min(1.0, r2)))
    
    except Exception as e:
        print(f"  ⚠️  R² calculation error: {e}")
        return 0.0

def calculate_amplitude_24h(date):
    """
    Écart-type prix 24h pré-événement
    """
    event_dt_str = f"{date} {EVENT_TIME_DB}"
    event_dt = datetime.strptime(event_dt_str, "%Y-%m-%d %H:%M:%S")
    start_dt = event_dt - timedelta(hours=24)
    
    query = f"""
    SELECT close 
    FROM prices_1m
    WHERE datetime >= '{start_dt.strftime('%Y-%m-%d %H:%M:%S')}+02:00'::TIMESTAMP
      AND datetime < '{event_dt_str}+02:00'::TIMESTAMP
    """
    
    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            prices_df = conn.execute(query).fetchdf()
        
        if len(prices_df) < 10:
            return 0.0
        
        return float(np.std(prices_df['close']))
    
    except Exception as e:
        print(f"  ⚠️  Amplitude calculation error: {e}")
        return 0.0

def measure_date_complete(date):
    """
    Mesure complète pour une date : impact + métriques
    """
    print(f"📊 {date}...", end=" ", flush=True)
    
    try:
        # Événements
        events_df = load_events(date)
        
        if len(events_df) == 0:
            print(f"❌ Pas d'événements")
            return None
        
        num_events = len(events_df)
        
        # Score ajusté
        score_adj = calculate_adjusted_score(events_df)
        
        # Surprises
        events_df['surprise'] = abs(
            (events_df['actual'] - events_df['estimate']) / events_df['estimate']
        )
        surprise_max = float(events_df['surprise'].max())
        surprise_avg = float(events_df['surprise'].mean())
        
        # Impact réel
        impact_data = measure_impact_corrected(date)
        
        if impact_data is None:
            print(f"❌ Erreur mesure impact")
            return None
        
        # Métriques contextuelles
        r2_72h = calculate_r2_72h(date)
        amplitude = calculate_amplitude_24h(date)
        
        print(f"✅ {impact_data['impact_pips']:.1f} pips {impact_data['direction']}")
        
        return {
            'date': date,
            'num_events': num_events,
            'score_adjusted': score_adj,
            'impact_real_pips': impact_data['impact_pips'],
            'direction': impact_data['direction'],
            'price_start': impact_data['price_start'],
            'price_peak': impact_data['price_peak'],
            'time_peak': impact_data['time_peak'],
            'duration_minutes': impact_data['duration_minutes'],
            'surprise_max': surprise_max,
            'surprise_avg': surprise_avg,
            'R2_72h': r2_72h,
            'amplitude_24h': amplitude
        }
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return None

if __name__ == "__main__":
    print("🚀 DÉMARRAGE MESURES")
    print()
    
    results = []
    
    for date in DATES_CLUSTER3:
        result = measure_date_complete(date)
        if result is not None:
            results.append(result)
    
    print()
    print("="*80)
    print("CONSOLIDATION RÉSULTATS")
    print("="*80)
    print()
    
    if len(results) == 0:
        print("❌ Aucune mesure réussie")
        sys.exit(1)
    
    # Créer DataFrame
    df = pd.DataFrame(results)
    
    print(f"✅ {len(df)} dates mesurées avec succès")
    print()
    
    # Statistiques
    print("📊 STATISTIQUES CLUSTER #3")
    print("-"*80)
    print(f"Impact (pips) :")
    print(f"  Moyenne : {df['impact_real_pips'].mean():.1f}")
    print(f"  σ       : {df['impact_real_pips'].std():.1f}")
    print(f"  Min/Max : {df['impact_real_pips'].min():.1f} / {df['impact_real_pips'].max():.1f}")
    print()
    print(f"Score ajusté :")
    print(f"  Moyenne : {df['score_adjusted'].mean():.1f}")
    print(f"  Min/Max : {df['score_adjusted'].min():.1f} / {df['score_adjusted'].max():.1f}")
    print()
    print(f"Surprise max :")
    print(f"  Moyenne : {df['surprise_max'].mean():.2%}")
    print(f"  Min/Max : {df['surprise_max'].min():.2%} / {df['surprise_max'].max():.2%}")
    print()
    
    # Validation référence 11.09
    ref = df[df['date'] == '2025-09-11']
    if len(ref) > 0:
        ref_impact = ref['impact_real_pips'].values[0]
        print(f"🎯 Référence 11.09 : {ref_impact:.1f} pips")
        if abs(ref_impact - 56.8) < 2:
            print(f"   ✅ Cohérent avec validation (56.8 pips)")
        else:
            print(f"   ⚠️  Écart vs validation (attendu 56.8)")
        print()
    
    # Sauvegarde CSV
    output_csv = Path(__file__).parent / 'cluster3_impacts_all_6dates.csv'
    df.to_csv(output_csv, index=False)
    
    print("="*80)
    print("✅✅✅ MESURES COMPLÉTÉES")
    print("="*80)
    print()
    print(f"💾 Output : {output_csv.name}")
    print()
    print("📋 PROCHAINE ÉTAPE : Phase 3.3 (Calculs amp_optimal)")
    print()
    
    # Sauvegarder aussi en JSON
    output_json = Path(__file__).parent / 'cluster3_impacts_all_6dates.json'
    df.to_json(output_json, orient='records', indent=2, date_format='iso')
    
    print(f"💾 Output JSON : {output_json.name}")
