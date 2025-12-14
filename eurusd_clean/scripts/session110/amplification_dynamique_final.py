"""
SESSION 110 - AMPLIFICATION DYNAMIQUE FINALE
=============================================

Implémentation EXACTE des formules validées Session 109 :
- C#1 : amp = 0.0339 × volatility_pips + 0.5352 (+41.8%)
- C#3 : amp = 0.5490 × R²_72h + 1.6988 (+95%)

Utilise détection inversion Session 107

Date : 3 novembre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.stats import linregress
from typing import List, Dict, Optional
import duckdb

# Setup
session110_dir = Path(__file__).parent
scripts_dir = session110_dir.parent
project_root = scripts_dir.parent
sys.path.insert(0, str(project_root / "app"))
sys.path.insert(0, str(session110_dir))

from detection_inversion_s107 import detect_trend_by_inversion_S107

# FORMULES VALIDÉES SESSION 109
# Cluster #1
C1_SLOPE = 0.0339
C1_INTERCEPT = 0.5352
C1_BASELINE = 1.451

# Cluster #3
C3_SLOPE = 0.5490
C3_INTERCEPT = 1.6988
C3_BASELINE = 2.545


def detect_cluster(events_list: List[dict]) -> int:
    """
    Détecte cluster d'événements
    
    Returns 1 (Manufacturing) ou 3 (CPI)
    """
    # Chercher CPI dans les events
    has_cpi = any('cpi' in str(e.get('name', '')).lower() for e in events_list)
    
    return 3 if has_cpi else 1


def load_prices_from_db(db_path: Path, event_time: pd.Timestamp) -> pd.DataFrame:
    """Charge prix depuis DuckDB"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Période : 14 jours avant événement
    start_time = event_time - timedelta(days=14)
    
    query = f"""
    SELECT datetime, close, high, low
    FROM prices_1m
    WHERE datetime >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
      AND datetime < '{event_time.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df['datetime'] = df['datetime'].dt.tz_convert('Europe/Zurich')
    
    return df


def calculate_r2_72h(prices_df: pd.DataFrame, event_time: pd.Timestamp) -> float:
    """
    Calcule R² sur 72h fixes AVANT événement
    Méthode Session 101/107
    """
    # 72h avant
    start_time = event_time - timedelta(hours=72)
    
    mask = (prices_df['datetime'] >= start_time) & (prices_df['datetime'] < event_time)
    df_72h = prices_df[mask].copy()
    
    if len(df_72h) < 100:
        return 0.0
    
    # Régression linéaire
    df_72h['time_numeric'] = (df_72h['datetime'] - df_72h['datetime'].iloc[0]).dt.total_seconds()
    X = df_72h['time_numeric'].values
    y = df_72h['close'].values
    
    try:
        _, _, r_value, _, _ = linregress(X, y)
        return r_value ** 2
    except:
        return 0.0


def calculate_amplification(
    events_list: List[dict],
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp,
    verbose: bool = True
) -> Dict:
    """
    CALCUL AMPLIFICATION DYNAMIQUE - SESSION 109/110
    
    Returns dict avec amplification et métadonnées
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 CALCUL AMPLIFICATION DYNAMIQUE (SESSION 109)")
        print("="*80)
    
    result = {
        'cluster': None,
        'amplification': None,
        'method': None,
        'metric_name': None,
        'metric_value': None,
        'baseline': None,
        'fallback_used': False
    }
    
    # ÉTAPE 1 : Détecter cluster
    cluster = detect_cluster(events_list)
    result['cluster'] = cluster
    baseline = C1_BASELINE if cluster == 1 else C3_BASELINE
    result['baseline'] = baseline
    
    if verbose:
        print(f"\n📊 Cluster : C#{cluster}")
        print(f"   Baseline : {baseline:.3f}")
    
    # ÉTAPE 2 : Détecter inversion (Session 107)
    if verbose:
        print(f"\n🔍 Détection inversion (Session 107)...")
    
    inversion = detect_trend_by_inversion_S107(
        prices_df,
        event_time,
        lookback_days=14,
        segment_hours=12,
        min_r2_for_trend=0.3,
        min_hours_before_event=24
    )
    
    if not inversion:
        # Fallback baseline
        result['fallback_used'] = True
        result['amplification'] = baseline
        result['method'] = 'fallback_no_inversion'
        
        if verbose:
            print(f"   ⚠️ Aucune inversion détectée")
            print(f"   → Fallback baseline : {baseline:.3f}")
        
        return result
    
    if verbose:
        print(f"   ✅ Inversion détectée !")
        print(f"   Type : {inversion['inversion_type']}")
        print(f"   Time : {inversion['inversion_time']}")
        print(f"   Duration : {inversion['hours_before_event']:.2f}h")
    
    # ÉTAPE 3 : Calculer métrique selon cluster
    if cluster == 1:
        # C#1 : Utiliser volatility_pips depuis inversion
        metric_value = inversion['volatility_pips']
        metric_name = 'volatility_pips'
        
        # Formule C#1
        amp = C1_SLOPE * metric_value + C1_INTERCEPT
        method = 'volatility_since_inversion'
        
        if verbose:
            print(f"\n📊 CLUSTER #1 - Volatility depuis inversion")
            print(f"   Volatility : {metric_value:.2f} pips")
            print(f"   Formule : amp = 0.0339 × {metric_value:.2f} + 0.5352")
            print(f"   amp = {amp:.3f}")
        
    else:
        # C#3 : Utiliser R² 72h fixe
        metric_value = calculate_r2_72h(prices_df, event_time)
        metric_name = 'r2_72h'
        
        # Formule C#3
        amp = C3_SLOPE * metric_value + C3_INTERCEPT
        method = 'r2_72h_fixed'
        
        if verbose:
            print(f"\n📊 CLUSTER #3 - R² 72h fixe")
            print(f"   R² 72h : {metric_value:.4f}")
            print(f"   Formule : amp = 0.5490 × {metric_value:.4f} + 1.6988")
            print(f"   amp = {amp:.3f}")
    
    # Limites sécurité
    amp = max(0.5, min(amp, 5.0))
    
    result['amplification'] = amp
    result['method'] = method
    result['metric_name'] = metric_name
    result['metric_value'] = metric_value
    
    if verbose:
        print(f"\n🎯 AMPLIFICATION FINALE : {amp:.3f}")
        print("="*80 + "\n")
    
    return result


if __name__ == "__main__":
    print("Module amplification dynamique SESSION 110 - Chargé ✅")
