#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION TENDANCE CLUSTER CIBLE - 1ER AOÛT 2025
====================================================

Vérifie en détail pourquoi la tendance n'est pas détectée pour le cluster cible.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT))

from config import DB_PATH
from src.core.trend_detection_pre_event_s107 import detect_trend_by_inversion_s107

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_tendance_cluster_cible():
    """Investigation détaillée de la détection de tendance"""
    
    date_str = '2025-08-01'
    anchor_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION TENDANCE CLUSTER CIBLE - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    print(f"📅 Date : {date_str}")
    print(f"⏰ Anchor time : {anchor_time}")
    print()
    
    # Charger les prix M30
    conn = duckdb.connect(str(DB_PATH))
    
    lookback_days = 14
    start_dt = anchor_time - timedelta(days=lookback_days)
    end_dt = anchor_time + timedelta(days=6)
    
    print(f"📊 Période requise :")
    print(f"   De : {start_dt}")
    print(f"   À : {end_dt}")
    print()
    
    # Charger prix M30
    start_dt_iso = start_dt.isoformat()
    end_dt_iso = end_dt.isoformat()
    
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m30
    WHERE datetime >= '{start_dt_iso}' AND datetime <= '{end_dt_iso}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).df()
    conn.close()
    
    print(f"✅ Prix chargés : {len(df_prices)} barres")
    print()
    
    if df_prices.empty:
        print("❌ Aucun prix disponible !")
        return
    
    # Convertir datetime
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices = df_prices.set_index('datetime')
    prices_series = df_prices['close']
    
    # Trouver index événement
    event_time_idx = None
    for idx, dt in enumerate(prices_series.index):
        if dt >= anchor_time:
            event_time_idx = idx
            break
    
    if event_time_idx is None:
        print("❌ Index événement non trouvé !")
        return
    
    print(f"✅ Index événement : {event_time_idx} (datetime: {prices_series.index[event_time_idx]})")
    print()
    
    # Test 1 : Paramètres par défaut (comme dans l'étape 8)
    print("=" * 80)
    print("  TEST 1 : Paramètres par défaut (étape 8)")
    print("=" * 80)
    print()
    
    print("Paramètres utilisés :")
    print("  - lookback_days: 14")
    print("  - segment_hours: 12")
    print("  - min_r2_for_trend: 0.3")
    print("  - min_hours_before_event: 24")
    print("  - timeframe: 'M30'")
    print()
    
    trend_result_default = detect_trend_by_inversion_s107(
        prices=prices_series,
        event_time_idx=event_time_idx,
        lookback_days=14,
        segment_hours=12,
        min_r2_for_trend=0.3,
        min_hours_before_event=24,
        timeframe='M30'
    )
    
    print("Résultat :")
    if trend_result_default:
        print(f"  trend_exists: {trend_result_default.get('trend_exists', False)}")
        print(f"  r2: {trend_result_default.get('r2', 0.0):.3f}")
        print(f"  direction: {trend_result_default.get('direction', 'UNKNOWN')}")
        print(f"  amplitude_pips: {trend_result_default.get('amplitude_pips', 0.0):.1f}")
        if 'error' in trend_result_default:
            print(f"  error: {trend_result_default['error']}")
        if 'reason' in trend_result_default:
            print(f"  reason: {trend_result_default['reason']}")
    else:
        print("  ❌ Aucun résultat retourné")
    print()
    
    # Test 2 : Paramètres assouplis (comme dans l'étape 8 avec fallback)
    print("=" * 80)
    print("  TEST 2 : Paramètres assouplis")
    print("=" * 80)
    print()
    
    print("Paramètres utilisés :")
    print("  - lookback_days: 14")
    print("  - segment_hours: 12")
    print("  - min_r2_for_trend: 0.15 (ASSOUPLI)")
    print("  - min_hours_before_event: 12 (ASSOUPLI)")
    print("  - timeframe: 'M30'")
    print()
    
    trend_result_relaxed = detect_trend_by_inversion_s107(
        prices=prices_series,
        event_time_idx=event_time_idx,
        lookback_days=14,
        segment_hours=12,
        min_r2_for_trend=0.15,  # Assoupli
        min_hours_before_event=12,  # Assoupli
        timeframe='M30'
    )
    
    print("Résultat :")
    if trend_result_relaxed:
        print(f"  trend_exists: {trend_result_relaxed.get('trend_exists', False)}")
        print(f"  r2: {trend_result_relaxed.get('r2', 0.0):.3f}")
        print(f"  direction: {trend_result_relaxed.get('direction', 'UNKNOWN')}")
        print(f"  amplitude_pips: {trend_result_relaxed.get('amplitude_pips', 0.0):.1f}")
        if 'error' in trend_result_relaxed:
            print(f"  error: {trend_result_relaxed['error']}")
        if 'reason' in trend_result_relaxed:
            print(f"  reason: {trend_result_relaxed['reason']}")
    else:
        print("  ❌ Aucun résultat retourné")
    print()
    
    # Test 3 : Paramètres très assouplis
    print("=" * 80)
    print("  TEST 3 : Paramètres très assouplis")
    print("=" * 80)
    print()
    
    print("Paramètres utilisés :")
    print("  - lookback_days: 14")
    print("  - segment_hours: 6 (RÉDUIT)")
    print("  - min_r2_for_trend: 0.10 (TRÈS ASSOUPLI)")
    print("  - min_hours_before_event: 6 (TRÈS ASSOUPLI)")
    print("  - timeframe: 'M30'")
    print()
    
    trend_result_very_relaxed = detect_trend_by_inversion_s107(
        prices=prices_series,
        event_time_idx=event_time_idx,
        lookback_days=14,
        segment_hours=6,  # Réduit
        min_r2_for_trend=0.10,  # Très assoupli
        min_hours_before_event=6,  # Très assoupli
        timeframe='M30'
    )
    
    print("Résultat :")
    if trend_result_very_relaxed:
        print(f"  trend_exists: {trend_result_very_relaxed.get('trend_exists', False)}")
        print(f"  r2: {trend_result_very_relaxed.get('r2', 0.0):.3f}")
        print(f"  direction: {trend_result_very_relaxed.get('direction', 'UNKNOWN')}")
        print(f"  amplitude_pips: {trend_result_very_relaxed.get('amplitude_pips', 0.0):.1f}")
        if 'error' in trend_result_very_relaxed:
            print(f"  error: {trend_result_very_relaxed['error']}")
        if 'reason' in trend_result_very_relaxed:
            print(f"  reason: {trend_result_very_relaxed['reason']}")
    else:
        print("  ❌ Aucun résultat retourné")
    print()
    
    # Analyse des prix autour de l'événement
    print("=" * 80)
    print("  ANALYSE PRIX AUTOUR DE L'ÉVÉNEMENT")
    print("=" * 80)
    print()
    
    # 14 jours avant l'événement
    start_analysis = anchor_time - timedelta(days=14)
    
    # Filtrer prix
    mask = (prices_series.index >= start_analysis) & (prices_series.index <= anchor_time)
    df_analysis = prices_series[mask].to_frame()
    
    print(f"📊 Prix sur 14 jours avant événement :")
    print(f"   Nombre de barres : {len(df_analysis)}")
    print(f"   Première barre : {df_analysis.index[0]}")
    print(f"   Dernière barre : {df_analysis.index[-1]}")
    print()
    
    # Statistiques de base
    print("📈 Statistiques :")
    print(f"   Prix min : {df_analysis['close'].min():.5f}")
    print(f"   Prix max : {df_analysis['close'].max():.5f}")
    print(f"   Amplitude : {(df_analysis['close'].max() - df_analysis['close'].min()) * 10000:.1f} pips")
    print(f"   Prix moyen : {df_analysis['close'].mean():.5f}")
    print(f"   Écart-type : {df_analysis['close'].std():.5f}")
    print()
    
    print("=" * 80)
    print()

if __name__ == "__main__":
    investiguer_tendance_cluster_cible()




