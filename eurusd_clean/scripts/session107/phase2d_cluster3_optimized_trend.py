#!/usr/bin/env python3
"""
SESSION 107 - DÉTECTION TENDANCE OPTIMISÉE (Sans parasites)
============================================================
Améliorations vs Phase 2C :
1. Prominence élevée (60+ pips) pour vrais extrema
2. Filtre temporel : ignore <24h avant événement
3. Prend dernier extremum MAJEUR valide
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from scipy.signal import find_peaks
from scipy.stats import linregress

print("="*80)
print("SESSION 107 - DÉTECTION TENDANCE OPTIMISÉE")
print("="*80)
print()
print("🔧 PARAMÈTRES OPTIMISÉS :")
print("   - Prominence min : 60 pips (vrais extrema seulement)")
print("   - Filtre temporel : ignore <24h avant événement")
print("   - Lookback       : 14 jours")
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

# Charger résultats Phase 1
results_file = Path(__file__).parent.parent / "session106" / "phase1_cluster3_results_FINAL_CORRECTED.csv"
df = pd.read_csv(results_file)

print(f"✅ {len(df)} dates Cluster #3 chargées")
print()

# =============================================================================
# FONCTION DÉTECTION OPTIMISÉE
# =============================================================================

def detect_trend_optimized(conn, event_datetime_bern, lookback_days=14, 
                          prominence_pips=60, min_hours_before_event=24):
    """
    Détecte tendance en filtrant parasites récents
    
    Params:
    - prominence_pips: Seuil pour extrema majeurs (60+ pips)
    - min_hours_before_event: Ignore extrema trop récents (24h)
    """
    # Timestamp
    event_dt = pd.to_datetime(event_datetime_bern)
    query_dt = event_dt - timedelta(hours=2)  # Event 14:30 Bern → 12:30+02:00 DB
    
    # Charger prix
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
    df_prices['high_pips'] = df_prices['high'] * 10000
    df_prices['low_pips'] = df_prices['low'] * 10000
    
    # === ÉTAPE 1 : DÉTECTER EXTREMA MAJEURS ===
    
    window = 720  # 12h window pour prominence
    
    # PEAKS (HIGH)
    peaks_idx, peak_props = find_peaks(
        df_prices['high_pips'].values, 
        distance=window, 
        prominence=prominence_pips
    )
    
    # TROUGHS (LOW)
    troughs_idx, trough_props = find_peaks(
        -df_prices['low_pips'].values,
        distance=window,
        prominence=prominence_pips
    )
    
    # Créer liste extrema avec prominence
    extrema = []
    
    for i, idx in enumerate(peaks_idx):
        dt = df_prices.iloc[idx]['datetime']
        hours_before = (query_dt - dt).total_seconds() / 3600
        
        extrema.append({
            'type': 'HIGH',
            'index': idx,
            'datetime': dt,
            'price': df_prices.iloc[idx]['high'],
            'price_pips': df_prices.iloc[idx]['high_pips'],
            'prominence': peak_props['prominences'][i],
            'hours_before_event': hours_before
        })
    
    for i, idx in enumerate(troughs_idx):
        dt = df_prices.iloc[idx]['datetime']
        hours_before = (query_dt - dt).total_seconds() / 3600
        
        extrema.append({
            'type': 'LOW',
            'index': idx,
            'datetime': dt,
            'price': df_prices.iloc[idx]['low'],
            'price_pips': df_prices.iloc[idx]['low_pips'],
            'prominence': trough_props['prominences'][i],
            'hours_before_event': hours_before
        })
    
    if len(extrema) == 0:
        return None
    
    # === ÉTAPE 2 : FILTRER PARASITES RÉCENTS ===
    
    # Garder seulement extrema > min_hours_before_event
    valid_extrema = [e for e in extrema if e['hours_before_event'] >= min_hours_before_event]
    
    if len(valid_extrema) == 0:
        return None
    
    # Trier par temps (plus récent d'abord)
    valid_extrema = sorted(valid_extrema, key=lambda x: x['datetime'], reverse=True)
    
    # === ÉTAPE 3 : PRENDRE DERNIER EXTREMUM MAJEUR VALIDE ===
    
    reversal = valid_extrema[0]  # Le plus récent qui respecte critères
    
    # === ÉTAPE 4 : MESURER TENDANCE DEPUIS CET EXTREMUM ===
    
    reversal_datetime = pd.to_datetime(reversal['datetime'])
    df_trend = df_prices[df_prices['datetime'] >= reversal_datetime].copy()
    
    if len(df_trend) < 100:
        return None
    
    # Durée
    duration_hours = (query_dt - reversal_datetime).total_seconds() / 3600
    
    # Régression
    df_trend['timestamp_numeric'] = (df_trend['datetime'] - reversal_datetime).dt.total_seconds()
    X = df_trend['timestamp_numeric'].values
    y = df_trend['close'].values
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
    except:
        r2 = 0
    
    # Métriques
    amplitude_pips = (df_trend['high'].max() - df_trend['low'].min()) * 10000
    volatility_pips = df_trend['close'].std() * 10000
    
    return {
        'r2': r2,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'volatility_pips': volatility_pips,
        'reversal_time': reversal_datetime,
        'reversal_type': reversal['type'],
        'reversal_prominence': reversal['prominence'],
        'num_points': len(df_trend),
        'num_extrema_found': len(extrema),
        'num_extrema_valid': len(valid_extrema),
        'all_valid_extrema': valid_extrema  # Pour debug
    }

# =============================================================================
# TEST SUR 11.09.2025
# =============================================================================

print("="*80)
print("TEST : 11.09.2025 (cas problématique)")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

event_datetime = "2025-09-11 14:30:00+02:00"
result = detect_trend_optimized(conn, event_datetime, 
                                prominence_pips=60, 
                                min_hours_before_event=24)

if result:
    print("✅ TENDANCE DÉTECTÉE (Optimisée)")
    print()
    print(f"  📊 Type extremum   : {result['reversal_type']}")
    print(f"  📊 Point détecté   : {result['reversal_time']}")
    print(f"  📊 Prominence      : {result['reversal_prominence']:.1f} pips")
    print(f"  📊 Durée tendance  : {result['duration_hours']:.1f}h")
    print(f"  📈 R²              : {result['r2']:.4f}")
    print(f"  📊 Amplitude       : {result['amplitude_pips']:.1f} pips")
    print()
    
    print(f"  🔍 Extrema trouvés : {result['num_extrema_found']}")
    print(f"  ✅ Extrema valides : {result['num_extrema_valid']} (>24h avant événement)")
    print()
    
    # Afficher tous extrema valides pour debug
    print("  📋 TOUS LES EXTREMA VALIDES (du plus récent au plus ancien) :")
    print("  " + "-"*76)
    for i, ext in enumerate(result['all_valid_extrema'][:5], 1):
        print(f"  {i}. {ext['type']:4s} | {ext['datetime']} | "
              f"{ext['price_pips']:.1f} pips | Prominence: {ext['prominence']:.1f} | "
              f"{ext['hours_before_event']:.1f}h avant")
    print()
    
    # Comparaison
    print("="*80)
    print("COMPARAISON MÉTHODES")
    print("="*80)
    print()
    
    print("📊 Phase 2C (détection basique) :")
    print("   Point : 2025-09-10 07:01 (parasite)")
    print("   Durée : 29.5h")
    print("   R²    : 0.4540")
    print()
    
    print("📊 Phase 2B (72h fixe) :")
    print("   Durée : 72h (fixe)")
    print("   R²    : 0.7420")
    print()
    
    print("📊 OPTIMISÉE (filtre parasites) :")
    print(f"   Point : {result['reversal_time']}")
    print(f"   Durée : {result['duration_hours']:.1f}h")
    print(f"   R²    : {result['r2']:.4f}")
    print()
    
    # Verdict
    if result['reversal_time'].hour >= 6 and result['reversal_time'].hour <= 10 and result['reversal_time'].day == 9:
        print("✅✅✅ SUCCÈS : Capte le pic du 9 sept matin (vraie tendance) !")
    else:
        print("⚠️ Attention : Point détecté ne correspond pas au pic attendu 9 sept ~8h")

else:
    print("❌ Échec détection")

print()

# =============================================================================
# TEST SUR TOUTES DATES CLUSTER #3
# =============================================================================

print("="*80)
print("APPLICATION SUR TOUTES DATES CLUSTER #3")
print("="*80)
print()

metrics = []

for _, row in df.iterrows():
    date_str = row['date']
    
    print(f"📅 {date_str}")
    print("-"*80)
    
    event_datetime_bern = f"{date_str} 14:30:00+02:00"
    
    result = detect_trend_optimized(conn, event_datetime_bern,
                                   prominence_pips=60,
                                   min_hours_before_event=24)
    
    if result is None:
        print(f"  ❌ Échec détection")
        print()
        continue
    
    print(f"  ✅ {result['reversal_type']} détecté : {result['reversal_time']}")
    print(f"  📊 Durée : {result['duration_hours']:.1f}h | R² : {result['r2']:.4f} | "
          f"Amplitude : {result['amplitude_pips']:.1f} pips")
    print()
    
    metrics.append({
        'date': date_str,
        'r2_optimized': result['r2'],
        'duration_hours': result['duration_hours'],
        'amplitude_optimized': result['amplitude_pips'],
        'reversal_type': result['reversal_type'],
        'reversal_prominence': result['reversal_prominence']
    })

conn.close()

# Fusion et corrélations
df_metrics = pd.DataFrame(metrics)
df_complete = df.merge(df_metrics, on='date', how='left')

print("="*80)
print("CORRÉLATIONS amp_optimal vs MÉTRIQUES OPTIMISÉES")
print("="*80)
print()

if 'r2_optimized' in df_complete.columns:
    corr = df_complete['amp_optimal'].corr(df_complete['r2_optimized'])
    n = len(df_complete['r2_optimized'].dropna())
    
    if n > 2:
        t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2 + 1e-10)
        from scipy.stats import t as t_dist
        p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
    else:
        p_value = 1.0
    
    print(f"📊 R² optimisé :")
    print(f"   Corrélation : {corr:+.3f}")
    print(f"   P-value     : {p_value:.4f}")
    print()
    
    # Comparaison
    print("COMPARAISON CORRÉLATIONS :")
    print(f"   R² 72h fixe     : r = +0.301 (p=0.562)")
    print(f"   R² dynamique    : r = +0.266 (p=0.610)")
    print(f"   R² OPTIMISÉ     : r = {corr:+.3f} (p={p_value:.3f})")

# Sauvegarder
output_file = Path(__file__).parent / "cluster3_optimized_analysis.csv"
df_complete.to_csv(output_file, index=False)

print()
print("="*80)
print("ANALYSE OPTIMISÉE TERMINÉE ✅")
print("="*80)
print()
print(f"✅ Résultats sauvegardés : {output_file.name}")
