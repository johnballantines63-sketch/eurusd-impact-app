#!/usr/bin/env python3
"""
SESSION 108 - PHASE 2E : MÉTHODE INVERSION SUR CLUSTER #1
==========================================================
Application de la méthode d'inversion validée Session 107
sur les 11 dates du Cluster #1 (Manufacturing + Consumer + Employment)
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from scipy.stats import linregress

print("="*80)
print("SESSION 108 - PHASE 2E : INVERSION SUR CLUSTER #1")
print("="*80)
print()
print("💡 MÉTHODE D'ANDRÉ (validée Session 107) :")
print("   Chercher pic lors d'inversion suivant tendance opposée")
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

# Charger dates Cluster #1
dates_file = Path(__file__).parent / "cluster1_dates.csv"
df_dates = pd.read_csv(dates_file)

print(f"✅ {len(df_dates)} dates Cluster #1 chargées")
print()

# =============================================================================
# FONCTION MESURE IMPACT RÉEL (Session 106)
# =============================================================================

def measure_real_impact(conn, event_datetime_bern, date_str):
    """
    Mesure impact réel selon méthode Session 106 validée
    - Timezone : Soustraire 2h pour query
    - Prix référence : OPEN première bougie
    """
    event_dt = pd.to_datetime(event_datetime_bern)
    query_dt = event_dt - timedelta(hours=2)
    
    # Query prix
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{query_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP - INTERVAL '5 minutes'
      AND datetime <= '{query_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP + INTERVAL '120 minutes'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).fetchdf()
    
    if len(df_prices) == 0:
        return None
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # Prix référence = OPEN première bougie >= événement
    event_timestamp = pd.to_datetime(f"{query_dt.strftime('%Y-%m-%d %H:%M:%S')}+02:00")
    prices_at_event = df_prices[df_prices['datetime'] >= event_timestamp]
    
    if len(prices_at_event) == 0:
        return None
    
    first_candle = prices_at_event.iloc[0]
    start_price = first_candle['open']
    
    # Calculer impacts UP et DOWN
    prices_after = df_prices[df_prices['datetime'] >= event_timestamp].copy()
    prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
    prices_after['pips_low'] = (start_price - prices_after['low']) * 10000
    
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
    ttr_minutes = (peak_time - event_timestamp).total_seconds() / 60
    
    return {
        'impact_pips': impact_pips,
        'direction': direction,
        'price_start': start_price,
        'price_peak': peak_price,
        'ttr_minutes': ttr_minutes,
        'peak_time': peak_time
    }

# =============================================================================
# FONCTION DÉTECTION PAR INVERSION (Session 107)
# =============================================================================

def detect_trend_by_inversion(conn, event_datetime_bern, 
                              lookback_days=14,
                              segment_hours=12,
                              min_r2_for_trend=0.3,
                              min_hours_before_event=24):
    """
    Détecte tendance en cherchant dernière inversion majeure
    """
    event_dt = pd.to_datetime(event_datetime_bern)
    query_dt = event_dt - timedelta(hours=2)
    
    start_dt = query_dt - timedelta(days=lookback_days)
    
    query = f"""
    SELECT datetime, close, high, low
    FROM prices_1m
    WHERE datetime >= '{start_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
      AND datetime < '{query_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).fetchdf()
    
    if len(df_prices) < 1000:
        return None
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # ÉTAPE 1 : DÉCOUPER EN SEGMENTS
    segment_duration = timedelta(hours=segment_hours)
    current_time = start_dt
    segments = []
    
    while current_time < query_dt:
        end_time = current_time + segment_duration
        
        mask = (df_prices['datetime'] >= current_time) & (df_prices['datetime'] < end_time)
        df_segment = df_prices[mask].copy()
        
        if len(df_segment) < 100:
            current_time = end_time
            continue
        
        df_segment['time_numeric'] = (df_segment['datetime'] - df_segment['datetime'].iloc[0]).dt.total_seconds()
        X = df_segment['time_numeric'].values
        y = df_segment['close'].values
        
        try:
            slope, intercept, r_value, p_value, std_err = linregress(X, y)
            r2 = r_value ** 2
            
            direction = 'UP' if slope > 0 else ('DOWN' if slope < 0 else 'FLAT')
            amplitude = (df_segment['high'].max() - df_segment['low'].min()) * 10000
            
            segments.append({
                'start': current_time,
                'end': end_time,
                'direction': direction,
                'slope': slope,
                'r2': r2,
                'amplitude_pips': amplitude,
                'num_points': len(df_segment),
                'price_start': df_segment['close'].iloc[0],
                'price_end': df_segment['close'].iloc[-1]
            })
            
        except Exception:
            pass
        
        current_time = end_time
    
    if len(segments) < 3:
        return None
    
    # ÉTAPE 2 : DÉTECTER INVERSIONS
    inversions = []
    
    for i in range(len(segments) - 1):
        seg_before = segments[i]
        seg_after = segments[i + 1]
        
        if seg_before['direction'] == seg_after['direction']:
            continue
        
        if seg_before['direction'] == 'FLAT' or seg_after['direction'] == 'FLAT':
            continue
        
        if seg_before['r2'] < min_r2_for_trend and seg_after['r2'] < min_r2_for_trend:
            continue
        
        if seg_before['direction'] == 'UP' and seg_after['direction'] == 'DOWN':
            inversion_type = 'PEAK'
        elif seg_before['direction'] == 'DOWN' and seg_after['direction'] == 'UP':
            inversion_type = 'TROUGH'
        else:
            continue
        
        search_start = seg_before['start']
        search_end = seg_after['end']
        
        mask = (df_prices['datetime'] >= search_start) & \
               (df_prices['datetime'] <= search_end)
        df_inv = df_prices[mask]
        
        if len(df_inv) == 0:
            continue
        
        if inversion_type == 'PEAK':
            inv_idx = df_inv['high'].idxmax()
            inv_price = df_inv.loc[inv_idx, 'high']
        else:
            inv_idx = df_inv['low'].idxmin()
            inv_price = df_inv.loc[inv_idx, 'low']
        
        inv_datetime = df_inv.loc[inv_idx, 'datetime']
        hours_before = (query_dt - inv_datetime).total_seconds() / 3600
        
        inversions.append({
            'type': inversion_type,
            'datetime': inv_datetime,
            'price': inv_price,
            'hours_before_event': hours_before,
            'seg_before': seg_before,
            'seg_after': seg_after,
            'quality_score': (seg_before['r2'] + seg_after['r2']) / 2
        })
    
    if len(inversions) == 0:
        return None
    
    # ÉTAPE 3 : FILTRER
    valid_inversions = [inv for inv in inversions 
                       if inv['hours_before_event'] >= min_hours_before_event]
    
    if len(valid_inversions) == 0:
        return None
    
    # ÉTAPE 4 : PRENDRE DERNIÈRE
    valid_inversions = sorted(valid_inversions, 
                             key=lambda x: (x['datetime'], x['quality_score']), 
                             reverse=True)
    
    reversal = valid_inversions[0]
    
    # ÉTAPE 5 : MESURER TENDANCE
    reversal_datetime = reversal['datetime']
    df_trend = df_prices[df_prices['datetime'] >= reversal_datetime].copy()
    
    if len(df_trend) < 100:
        return None
    
    duration_hours = (query_dt - reversal_datetime).total_seconds() / 3600
    
    df_trend['timestamp_numeric'] = (df_trend['datetime'] - reversal_datetime).dt.total_seconds()
    X = df_trend['timestamp_numeric'].values
    y = df_trend['close'].values
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
    except:
        r2 = 0
    
    amplitude_pips = (df_trend['high'].max() - df_trend['low'].min()) * 10000
    volatility_pips = df_trend['close'].std() * 10000
    
    return {
        'r2': r2,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'volatility_pips': volatility_pips,
        'reversal_time': reversal_datetime,
        'reversal_type': reversal['type'],
        'reversal_price': reversal['price'],
        'quality_score': reversal['quality_score'],
        'num_segments': len(segments),
        'num_inversions_found': len(inversions),
        'num_inversions_valid': len(valid_inversions)
    }

# =============================================================================
# TRAITEMENT CLUSTER #1
# =============================================================================

print("="*80)
print("TRAITEMENT 11 DATES CLUSTER #1")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

results = []

for idx, row in df_dates.iterrows():
    date_str = row['date']
    
    print(f"📅 {date_str}")
    print("-"*80)
    
    # Événements Cluster #1 sont à 15:45:00 (pas 14:30:00)
    event_datetime_bern = f"{date_str} 15:45:00+02:00"
    
    # 1. Mesurer impact réel
    impact_result = measure_real_impact(conn, event_datetime_bern, date_str)
    
    if impact_result is None:
        print("  ❌ Impossible de mesurer impact réel")
        print()
        continue
    
    print(f"  📊 Impact réel : {impact_result['impact_pips']:.1f} pips")
    
    # 2. Calculer amp_optimal (formules Session 51-55)
    # Note : Pour Cluster #1, on utilise les mêmes formules que Cluster #3
    # Score constant 87.1, num_events = 8
    
    score_ajuste = 87.1  # Score constant Cluster #1
    num_events = 8
    
    # Formule Session 51 (multi-événements)
    impact_brut = -10.47 + 0.477 * score_ajuste
    impact_predit_baseline = abs(impact_brut) * 2.5 * 0.758
    
    # amp_optimal = amp qui donnerait impact_predit = impact_reel
    if abs(impact_brut * 0.758) > 0:
        amp_optimal = impact_result['impact_pips'] / abs(impact_brut * 0.758)
    else:
        amp_optimal = 2.5  # Fallback
    
    # Limiter amp_optimal entre 0.5 et 5.0 (bornes Session 103)
    amp_optimal = max(0.5, min(5.0, amp_optimal))
    
    error_baseline = abs(impact_predit_baseline - impact_result['impact_pips'])
    
    print(f"  📊 amp_optimal : {amp_optimal:.3f}")
    print(f"  📊 Erreur baseline (amp=2.5) : {error_baseline:.1f} pips")
    
    # 3. Détection inversion
    inversion_result = detect_trend_by_inversion(conn, event_datetime_bern,
                                                segment_hours=12,
                                                min_r2_for_trend=0.3,
                                                min_hours_before_event=24)
    
    if inversion_result is None:
        print("  ❌ Aucune inversion détectée")
        print()
        
        results.append({
            'date': date_str,
            'impact_real_pips': impact_result['impact_pips'],
            'direction': impact_result['direction'],
            'amp_optimal': amp_optimal,
            'error_baseline': error_baseline,
            'r2_inversion': np.nan,
            'duration_hours': np.nan,
            'reversal_type': None,
            'quality_score': np.nan
        })
        continue
    
    print(f"  ✅ {inversion_result['reversal_type']} : {inversion_result['reversal_time']}")
    print(f"  📊 Durée : {inversion_result['duration_hours']:.1f}h | "
          f"R² : {inversion_result['r2']:.4f} | "
          f"Qualité : {inversion_result['quality_score']:.3f}")
    print()
    
    results.append({
        'date': date_str,
        'impact_real_pips': impact_result['impact_pips'],
        'direction': impact_result['direction'],
        'amp_optimal': amp_optimal,
        'error_baseline': error_baseline,
        'r2_inversion': inversion_result['r2'],
        'duration_hours': inversion_result['duration_hours'],
        'reversal_type': inversion_result['reversal_type'],
        'quality_score': inversion_result['quality_score']
    })

conn.close()

# Sauvegarder
df_results = pd.DataFrame(results)
output_file = Path(__file__).parent / "cluster1_inversion_analysis.csv"
df_results.to_csv(output_file, index=False)

print("="*80)
print("STATISTIQUES CLUSTER #1")
print("="*80)
print()

print(f"Dates traitées : {len(df_results)}")
print(f"Inversions détectées : {df_results['r2_inversion'].notna().sum()}")
print()

if df_results['r2_inversion'].notna().sum() > 0:
    print("📊 amp_optimal :")
    print(f"   Moyenne : {df_results['amp_optimal'].mean():.3f}")
    print(f"   Médiane : {df_results['amp_optimal'].median():.3f}")
    print(f"   Min/Max : {df_results['amp_optimal'].min():.3f} / {df_results['amp_optimal'].max():.3f}")
    print()
    
    print("📊 Erreur baseline (amp=2.5) :")
    print(f"   MAE : {df_results['error_baseline'].mean():.1f} pips")
    print()
    
    # Corrélation
    df_valid = df_results[df_results['r2_inversion'].notna()]
    if len(df_valid) > 2:
        corr = df_valid['amp_optimal'].corr(df_valid['r2_inversion'])
        n = len(df_valid)
        
        t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2 + 1e-10)
        from scipy.stats import t as t_dist
        p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
        
        print(f"📊 Corrélation R²_inversion vs amp_optimal :")
        print(f"   r = {corr:+.3f}")
        print(f"   p-value = {p_value:.4f}")
        print()

print("="*80)
print("PHASE 2E CLUSTER #1 TERMINÉE ✅")
print("="*80)
print()
print(f"✅ Résultats : {output_file.name}")
print()
print("PROCHAINE ÉTAPE : Calibration formule sur 17 dates (6 C#3 + 11 C#1)")
