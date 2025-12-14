#!/usr/bin/env python3
"""
SESSION 107 - DÉTECTION PAR SÉQUENCE TENDANCE + INVERSION
===========================================================
Méthode d'André : Chercher pic lors d'inversion qui suit tendance opposée

Algorithme :
1. Découper période en segments (ex: 12h)
2. Calculer tendance (régression) pour chaque segment
3. Détecter inversions : UP→DOWN (pic) ou DOWN→UP (creux)
4. Valider que les deux côtés ont tendance claire (R² > seuil)
5. Prendre dernière inversion valide
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from scipy.stats import linregress

print("="*80)
print("SESSION 107 - DÉTECTION PAR INVERSION DE TENDANCE")
print("="*80)
print()
print("💡 MÉTHODE D'ANDRÉ :")
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

# Charger résultats Phase 1
results_file = Path(__file__).parent.parent / "session106" / "phase1_cluster3_results_FINAL_CORRECTED.csv"
df = pd.read_csv(results_file)

print(f"✅ {len(df)} dates Cluster #3 chargées")
print()

# =============================================================================
# FONCTION DÉTECTION PAR INVERSION
# =============================================================================

def detect_trend_by_inversion(conn, event_datetime_bern, 
                              lookback_days=14,
                              segment_hours=12,
                              min_r2_for_trend=0.3,
                              min_hours_before_event=24):
    """
    Détecte tendance en cherchant dernière inversion majeure
    
    Params:
    - segment_hours: Durée segments pour analyse tendance
    - min_r2_for_trend: R² minimum pour considérer tendance valide
    - min_hours_before_event: Ignore inversions trop récentes
    """
    # Timestamp
    event_dt = pd.to_datetime(event_datetime_bern)
    query_dt = event_dt - timedelta(hours=2)
    
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
    
    # === ÉTAPE 1 : DÉCOUPER EN SEGMENTS ET CALCULER TENDANCES ===
    
    segment_duration = timedelta(hours=segment_hours)
    current_time = start_dt
    segments = []
    
    while current_time < query_dt:
        end_time = current_time + segment_duration
        
        # Filtrer données segment
        mask = (df_prices['datetime'] >= current_time) & (df_prices['datetime'] < end_time)
        df_segment = df_prices[mask].copy()
        
        if len(df_segment) < 100:
            current_time = end_time
            continue
        
        # Régression linéaire
        df_segment['time_numeric'] = (df_segment['datetime'] - df_segment['datetime'].iloc[0]).dt.total_seconds()
        X = df_segment['time_numeric'].values
        y = df_segment['close'].values
        
        try:
            slope, intercept, r_value, p_value, std_err = linregress(X, y)
            r2 = r_value ** 2
            
            # Déterminer direction
            if slope > 0:
                direction = 'UP'
            elif slope < 0:
                direction = 'DOWN'
            else:
                direction = 'FLAT'
            
            # Amplitude segment
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
            
        except Exception as e:
            pass
        
        current_time = end_time
    
    if len(segments) < 3:
        return None
    
    # === ÉTAPE 2 : DÉTECTER INVERSIONS ===
    
    inversions = []
    
    for i in range(len(segments) - 1):
        seg_before = segments[i]
        seg_after = segments[i + 1]
        
        # Vérifier inversion de direction
        if seg_before['direction'] == seg_after['direction']:
            continue
        
        if seg_before['direction'] == 'FLAT' or seg_after['direction'] == 'FLAT':
            continue
        
        # Vérifier qualité tendances (R² suffisant)
        if seg_before['r2'] < min_r2_for_trend and seg_after['r2'] < min_r2_for_trend:
            continue  # Au moins un côté doit avoir tendance claire
        
        # Type inversion
        if seg_before['direction'] == 'UP' and seg_after['direction'] == 'DOWN':
            inversion_type = 'PEAK'  # Pic
        elif seg_before['direction'] == 'DOWN' and seg_after['direction'] == 'UP':
            inversion_type = 'TROUGH'  # Creux
        else:
            continue
        
        # Point d'inversion = chercher dans zone transition
        # Chercher pic/creux entre fin segment avant et début segment après
        search_start = seg_before['start']
        search_end = seg_after['end']
        
        mask = (df_prices['datetime'] >= search_start) & \
               (df_prices['datetime'] <= search_end)
        df_inv = df_prices[mask]
        
        if len(df_inv) == 0:
            continue  # Skip si pas de données
        
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
    
    # === ÉTAPE 3 : FILTRER INVERSIONS TROP RÉCENTES ===
    
    valid_inversions = [inv for inv in inversions 
                       if inv['hours_before_event'] >= min_hours_before_event]
    
    if len(valid_inversions) == 0:
        return None
    
    # === ÉTAPE 4 : PRENDRE DERNIÈRE INVERSION VALIDE ===
    
    # Trier par qualité et temps
    valid_inversions = sorted(valid_inversions, 
                             key=lambda x: (x['datetime'], x['quality_score']), 
                             reverse=True)
    
    reversal = valid_inversions[0]
    
    # === ÉTAPE 5 : MESURER TENDANCE DEPUIS INVERSION ===
    
    reversal_datetime = reversal['datetime']
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
        'reversal_price': reversal['price'],
        'quality_score': reversal['quality_score'],
        'num_segments': len(segments),
        'num_inversions_found': len(inversions),
        'num_inversions_valid': len(valid_inversions),
        'all_inversions': valid_inversions  # Pour debug
    }

# =============================================================================
# TEST SUR 11.09.2025
# =============================================================================

print("="*80)
print("TEST : 11.09.2025")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

event_datetime = "2025-09-11 14:30:00+02:00"

print("🔧 PARAMÈTRES :")
print("   - Segments      : 12h")
print("   - R² min trend  : 0.3")
print("   - Min avant evt : 24h")
print()

result = detect_trend_by_inversion(conn, event_datetime,
                                   segment_hours=12,
                                   min_r2_for_trend=0.3,
                                   min_hours_before_event=24)

if result:
    print("✅ INVERSION DÉTECTÉE")
    print()
    print(f"  📊 Type inversion  : {result['reversal_type']}")
    print(f"  📊 Point détecté   : {result['reversal_time']}")
    print(f"  📊 Prix            : {result['reversal_price']:.5f}")
    print(f"  📊 Qualité         : {result['quality_score']:.3f} (moy R² avant+après)")
    print(f"  📊 Durée tendance  : {result['duration_hours']:.1f}h")
    print(f"  📈 R²              : {result['r2']:.4f}")
    print(f"  📊 Amplitude       : {result['amplitude_pips']:.1f} pips")
    print()
    
    print(f"  🔍 Segments analysés      : {result['num_segments']}")
    print(f"  🔍 Inversions trouvées    : {result['num_inversions_found']}")
    print(f"  ✅ Inversions valides     : {result['num_inversions_valid']}")
    print()
    
    # Afficher toutes inversions valides
    print("  📋 TOUTES INVERSIONS VALIDES :")
    print("  " + "-"*76)
    for i, inv in enumerate(result['all_inversions'][:5], 1):
        print(f"  {i}. {inv['type']:6s} | {inv['datetime']} | "
              f"Prix: {inv['price']:.5f} | "
              f"Qualité: {inv['quality_score']:.3f} | "
              f"{inv['hours_before_event']:.1f}h avant")
        print(f"     Avant: {inv['seg_before']['direction']} (R²={inv['seg_before']['r2']:.3f}) | "
              f"Après: {inv['seg_after']['direction']} (R²={inv['seg_after']['r2']:.3f})")
    print()
    
    # Verdict
    expected_date = 9  # On attend pic 9 sept
    detected_date = result['reversal_time'].day
    detected_hour = result['reversal_time'].hour
    
    if detected_date == expected_date and 6 <= detected_hour <= 12:
        print("✅✅✅ PARFAIT : Capte le pic du 9 sept matin (~8h) !")
    elif detected_date == expected_date:
        print(f"✅ BON : Capte pic du 9 sept (heure {detected_hour}h)")
    else:
        print(f"⚠️ ATTENTION : Capte date {detected_date} sept (attendu : 9 sept)")

else:
    print("❌ Aucune inversion détectée")

print()

# =============================================================================
# COMPARAISON MÉTHODES
# =============================================================================

print("="*80)
print("COMPARAISON TOUTES MÉTHODES")
print("="*80)
print()

print("Méthode                    | Point détecté      | Durée  | R²")
print("-"*80)
print("Phase 2C (basique)         | 2025-09-10 07:01   | 29.5h  | 0.4540")
print("Phase 2B (72h fixe)        | (72h avant)        | 72.0h  | 0.7420")
print("Phase 2D (prominence)      | (à tester)         | ?      | ?")
if result:
    print(f"Phase 2E (INVERSION)       | {result['reversal_time']} | {result['duration_hours']:5.1f}h | {result['r2']:.4f}")
print()

# =============================================================================
# TEST SUR TOUTES DATES
# =============================================================================

print("="*80)
print("APPLICATION SUR CLUSTER #3")
print("="*80)
print()

metrics = []

for _, row in df.iterrows():
    date_str = row['date']
    
    print(f"📅 {date_str}")
    print("-"*80)
    
    event_datetime_bern = f"{date_str} 14:30:00+02:00"
    
    result = detect_trend_by_inversion(conn, event_datetime_bern,
                                      segment_hours=12,
                                      min_r2_for_trend=0.3,
                                      min_hours_before_event=24)
    
    if result is None:
        print(f"  ❌ Aucune inversion détectée")
        print()
        continue
    
    print(f"  ✅ {result['reversal_type']} : {result['reversal_time']}")
    print(f"  📊 Durée : {result['duration_hours']:.1f}h | R² : {result['r2']:.4f} | "
          f"Amplitude : {result['amplitude_pips']:.1f} pips")
    print()
    
    metrics.append({
        'date': date_str,
        'r2_inversion': result['r2'],
        'duration_hours': result['duration_hours'],
        'amplitude_inversion': result['amplitude_pips'],
        'reversal_type': result['reversal_type'],
        'quality_score': result['quality_score']
    })

conn.close()

# Fusion et corrélations
df_metrics = pd.DataFrame(metrics)
df_complete = df.merge(df_metrics, on='date', how='left')

print("="*80)
print("CORRÉLATIONS")
print("="*80)
print()

if 'r2_inversion' in df_complete.columns and not df_complete['r2_inversion'].isna().all():
    corr = df_complete['amp_optimal'].corr(df_complete['r2_inversion'])
    n = len(df_complete['r2_inversion'].dropna())
    
    if n > 2:
        t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2 + 1e-10)
        from scipy.stats import t as t_dist
        p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
    else:
        p_value = 1.0
    
    print(f"📊 R² par inversion :")
    print(f"   Corrélation : {corr:+.3f}")
    print(f"   P-value     : {p_value:.4f}")
    print()
    
    print("RÉCAPITULATIF :")
    print(f"   R² 72h fixe     : r = +0.301")
    print(f"   R² dynamique    : r = +0.266")
    print(f"   R² INVERSION    : r = {corr:+.3f}")

# Sauvegarder
output_file = Path(__file__).parent / "cluster3_inversion_analysis.csv"
df_complete.to_csv(output_file, index=False)

print()
print("="*80)
print("ANALYSE PAR INVERSION TERMINÉE ✅")
print("="*80)
print()
print(f"✅ Résultats : {output_file.name}")
