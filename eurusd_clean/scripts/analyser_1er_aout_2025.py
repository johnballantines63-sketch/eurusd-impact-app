#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE 1ER AOÛT 2025 - SINGLE WAVE FORT
=========================================

Analyse détaillée du 1er août 2025 pour identifier les valeurs 1.8 et 29.5
dans le contexte d'un Single Wave Fort.

Date: 2025-01-XX
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor
from double_wave_detector_rev12 import detect_for_date_duckdb_rev12
from core.price_loader_finnhub import get_finnhub_prices_at_event_time

TZ_BERN = pytz.timezone('Europe/Zurich')

def analyser_single_wave_1er_aout():
    """Analyse détaillée du 1er août 2025"""
    
    date_str = '2025-08-01'
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  ANALYSE 1ER AOÛT 2025 - SINGLE WAVE FORT")
    print("=" * 80)
    print()
    
    # 1. Charger les prix autour de l'événement
    print("1️⃣ CHARGEMENT DES PRIX AUTOUR DE 14:30 :")
    print("-" * 80)
    
    df_prices = get_finnhub_prices_at_event_time(
        db_path=DB_PATH,
        event_timestamp_bern=event_time,
        lookback_minutes=60,
        lookahead_minutes=120
    )
    
    if df_prices.empty:
        print("   ❌ Aucun prix trouvé")
        return
    
    print(f"   ✅ {len(df_prices)} barres chargées")
    print(f"   Période : {df_prices['datetime'].min()} → {df_prices['datetime'].max()}")
    print()
    
    # 2. Trouver baseline (prix juste avant 14:30)
    prices_before = df_prices[df_prices['datetime'] < event_time]
    if not prices_before.empty:
        baseline_price = prices_before.iloc[-1]['close']
        baseline_time = prices_before.iloc[-1]['datetime']
        print(f"2️⃣ BASELINE :")
        print(f"   Prix : {baseline_price:.5f}")
        print(f"   Heure : {baseline_time}")
        print()
    else:
        baseline_price = df_prices.iloc[0]['open']
        baseline_time = df_prices.iloc[0]['datetime']
        print(f"2️⃣ BASELINE (fallback) :")
        print(f"   Prix : {baseline_price:.5f}")
        print(f"   Heure : {baseline_time}")
        print()
    
    # 3. Analyser le mouvement après 14:30
    prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
    prices_after['pips_from_baseline'] = (prices_after['high'] - baseline_price) * 10000
    
    # Trouver le pic maximum
    max_pips_idx = prices_after['pips_from_baseline'].idxmax()
    peak_time = prices_after.loc[max_pips_idx, 'datetime']
    peak_price = prices_after.loc[max_pips_idx, 'high']
    peak_pips = prices_after.loc[max_pips_idx, 'pips_from_baseline']
    
    print(f"3️⃣ PIC MAXIMUM (SINGLE WAVE) :")
    print(f"   Impact : {peak_pips:.1f} pips")
    print(f"   Heure : {peak_time}")
    print(f"   Prix : {peak_price:.5f}")
    print()
    
    # 4. Analyser le pullback après le pic
    prices_after_peak = prices_after[prices_after['datetime'] > peak_time].copy()
    
    if not prices_after_peak.empty:
        # Calculer retracement depuis le pic
        prices_after_peak['pips_retracement'] = (peak_price - prices_after_peak['low']) * 10000
        
        # Trouver le creux maximum (pullback le plus profond)
        max_retrace_idx = prices_after_peak['pips_retracement'].idxmax()
        pullback_time = prices_after_peak.loc[max_retrace_idx, 'datetime']
        pullback_price = prices_after_peak.loc[max_retrace_idx, 'low']
        pullback_pips = prices_after_peak.loc[max_retrace_idx, 'pips_retracement']
        
        pullback_ratio = (pullback_pips / peak_pips * 100) if peak_pips > 0 else 0
        
        print(f"4️⃣ PULLBACK :")
        print(f"   Retracement : {pullback_pips:.1f} pips")
        print(f"   Heure : {pullback_time}")
        print(f"   Prix : {pullback_price:.5f}")
        print(f"   Ratio : {pullback_ratio:.1f}% du pic")
        print()
        
        # Vérifier si pullback ≈ 29.5 pips
        if abs(pullback_pips - 29.5) < 1.0:
            print(f"   ✅ PULLBACK TROUVÉ ≈ 29.5 pips : {pullback_pips:.1f} pips")
            print()
        
        # Chercher dans les 60 premières minutes après le pic
        window_60min = prices_after_peak[
            (prices_after_peak['datetime'] - peak_time).dt.total_seconds() / 60 <= 60
        ]
        
        if not window_60min.empty:
            max_retrace_60min_idx = window_60min['pips_retracement'].idxmax()
            pullback_60min_pips = window_60min.loc[max_retrace_60min_idx, 'pips_retracement']
            pullback_60min_time = window_60min.loc[max_retrace_60min_idx, 'datetime']
            
            print(f"5️⃣ PULLBACK (dans les 60 premières minutes) :")
            print(f"   Retracement : {pullback_60min_pips:.1f} pips")
            print(f"   Heure : {pullback_60min_time}")
            print()
            
            if abs(pullback_60min_pips - 29.5) < 1.0:
                print(f"   ✅ PULLBACK 60MIN ≈ 29.5 pips : {pullback_60min_pips:.1f} pips")
                print()
    
    # 5. Détection REV12
    print(f"6️⃣ DÉTECTION REV12 :")
    print("-" * 80)
    
    pattern_date = event_time.replace(tzinfo=None)
    
    try:
        pattern_real = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=pattern_date,
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=120,
            trading_window=True,
            debug=False
        )
        
        if pattern_real:
            double_wave = pattern_real.get('double_wave', False)
            wave1_pips = pattern_real.get('wave1_pips', 0.0)
            wave2_pips = pattern_real.get('wave2_pips', 0.0)
            pullback1_pips = abs(pattern_real.get('pullback1_pips', 0.0))
            
            print(f"   Pattern détecté : {'DOUBLE WAVE' if double_wave else 'SINGLE WAVE'}")
            print(f"   Wave 1 : {wave1_pips:.1f} pips")
            print(f"   Wave 2 : {wave2_pips:.1f} pips")
            print(f"   Pullback 1 : {pullback1_pips:.1f} pips")
            
            if not double_wave:
                print(f"\n   ✅ SINGLE WAVE confirmé")
            
            if abs(pullback1_pips - 29.5) < 1.0:
                print(f"   ✅ PULLBACK ≈ 29.5 pips : {pullback1_pips:.1f} pips")
        else:
            print("   ⚠️ Aucun pattern détecté par REV12")
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
    
    print()
    
    # 6. Pipeline complet
    print(f"7️⃣ RÉSULTATS DU PIPELINE :")
    print("-" * 80)
    
    executor = PipelineExecutor(DB_PATH, verbose=False)
    
    try:
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if result['success']:
            final_prediction = result['final_prediction']
            pattern_info = final_prediction.get('pattern_info', {})
            
            pattern_type = pattern_info.get('pattern_type', 'NONE')
            wave1_pips_pred = pattern_info.get('wave1_pips', 0.0)
            wave2_pips_pred = pattern_info.get('wave2_peak_pips_absolute', 0.0)
            pullback_pips_pred = abs(pattern_info.get('pullback_pips', 0.0))
            impact_base = final_prediction.get('impact_base', 0.0)
            amplification = final_prediction.get('amplification_predite', 1.0)
            
            print(f"   Pattern prédit : {pattern_type}")
            print(f"   Impact de base : {impact_base:.2f} pips")
            print(f"   Wave 1 prédit : {wave1_pips_pred:.1f} pips")
            print(f"   Wave 2 prédit : {wave2_pips_pred:.1f} pips")
            print(f"   Pullback prédit : {pullback_pips_pred:.1f} pips")
            print(f"   Amplification : {amplification:.3f}x")
            
            # Calculer extension factor
            if wave1_pips_pred > 0 and wave2_pips_pred > 0:
                extension = wave2_pips_pred / wave1_pips_pred
                print(f"   Extension factor : {extension:.3f}x")
                
                if abs(extension - 1.8) < 0.2:
                    print(f"\n   ✅ EXTENSION FACTOR ≈ 1.8 : {extension:.3f}x")
            
            if abs(pullback_pips_pred - 29.5) < 1.0:
                print(f"\n   ✅ PULLBACK PRÉDIT ≈ 29.5 pips : {pullback_pips_pred:.1f} pips")
            
            if abs(amplification - 1.8) < 0.2:
                print(f"\n   ✅ AMPLIFICATION ≈ 1.8 : {amplification:.3f}x")
            
            if impact_base > 0:
                ratio_w1 = wave1_pips_pred / impact_base
                print(f"   Ratio Wave1/Base : {ratio_w1:.3f}")
                
                if abs(ratio_w1 - 1.8) < 0.2:
                    print(f"\n   ✅ RATIO WAVE1/BASE ≈ 1.8 : {ratio_w1:.3f}")
        else:
            print(f"   ❌ Erreur : {result.get('error', 'Erreur inconnue')}")
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    analyser_single_wave_1er_aout()




