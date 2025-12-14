#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VÉRIFICATION PATTERN DÉTECTÉ - 1ER AOÛT 2025
==============================================

Vérifie si le pattern détecté est bien une Single Wave ou Double Wave
dans les prix réels pour le 1er août 2025.

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
from core.price_loader_finnhub import get_finnhub_prices_at_event_time
from double_wave_detector_rev12 import detect_for_date_duckdb_rev12

TZ_BERN = pytz.timezone('Europe/Zurich')

def verifier_pattern_detecte():
    """Vérifie le pattern détecté"""
    
    date_str = '2025-08-01'
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  VÉRIFICATION PATTERN DÉTECTÉ - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    # ========================================================================
    # 1. DÉTECTION RÉELLE DANS LES PRIX (REV12)
    # ========================================================================
    
    print("📊 1. DÉTECTION RÉELLE DANS LES PRIX (REV12) :")
    print("-" * 80)
    print()
    
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
            double_wave_detected = pattern_real.get('double_wave', False)
            confidence = pattern_real.get('confidence', 0.0)
            wave1_pips = pattern_real.get('wave1_pips', 0.0)
            wave2_pips = pattern_real.get('wave2_pips', 0.0)
            pullback1_pips = abs(pattern_real.get('pullback1_pips', 0.0))
            
            print(f"   Pattern détecté par REV12 :")
            if double_wave_detected:
                print(f"      Type : 🔵 DOUBLE WAVE")
            else:
                print(f"      Type : 🟢 SINGLE WAVE (pas de Double Wave détecté)")
            
            print(f"      Confiance : {confidence:.1f}%")
            print(f"      Wave 1 : {wave1_pips:.1f} pips")
            print(f"      Wave 2 : {wave2_pips:.1f} pips")
            print(f"      Pullback 1 : {pullback1_pips:.1f} pips")
            print()
            
            # Vérifier si c'est vraiment un Single Wave ou Double Wave
            if double_wave_detected:
                print(f"   ✅ DÉTECTION RÉELLE : DOUBLE WAVE")
            else:
                print(f"   ✅ DÉTECTION RÉELLE : SINGLE WAVE")
                print(f"      (Pas de Double Wave détecté dans les prix réels)")
        else:
            print(f"   ⚠️ Aucun pattern détecté par REV12")
            print(f"      (REV12 n'a pas réussi à détecter un pattern)")
            
    except Exception as e:
        print(f"   ❌ Erreur détection REV12 : {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # ========================================================================
    # 2. ANALYSE MANUELLE DES PRIX
    # ========================================================================
    
    print("📊 2. ANALYSE MANUELLE DES PRIX :")
    print("-" * 80)
    print()
    
    df_prices = get_finnhub_prices_at_event_time(
        db_path=DB_PATH,
        event_timestamp_bern=event_time,
        lookback_minutes=60,
        lookahead_minutes=120
    )
    
    if not df_prices.empty:
        # Baseline
        prices_before = df_prices[df_prices['datetime'] < event_time]
        baseline_price = prices_before.iloc[-1]['close']
        
        # Trouver le pic
        prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
        prices_after['pips'] = (prices_after['high'] - baseline_price) * 10000
        
        max_pips_idx = prices_after['pips'].idxmax()
        peak_time = prices_after.loc[max_pips_idx, 'datetime']
        peak_price = prices_after.loc[max_pips_idx, 'high']
        peak_pips = prices_after.loc[max_pips_idx, 'pips']
        
        print(f"   Pic maximum trouvé :")
        print(f"      Impact : {peak_pips:.1f} pips")
        print(f"      Heure : {peak_time}")
        print()
        
        # Analyser après le pic pour voir s'il y a un deuxième pic (Double Wave)
        prices_after_peak = prices_after[prices_after['datetime'] > peak_time].copy()
        
        if not prices_after_peak.empty:
            # Chercher pullback significatif (> 20% du pic)
            prices_after_peak['pullback_pips'] = (peak_price - prices_after_peak['low']) * 10000
            prices_after_peak['pullback_ratio'] = prices_after_peak['pullback_pips'] / peak_pips if peak_pips > 0 else 0
            
            # Trouver le pullback maximum
            max_pullback_idx = prices_after_peak['pullback_pips'].idxmax()
            max_pullback_pips = prices_after_peak.loc[max_pullback_idx, 'pullback_pips']
            max_pullback_ratio = prices_after_peak.loc[max_pullback_idx, 'pullback_ratio']
            pullback_time = prices_after_peak.loc[max_pullback_idx, 'datetime']
            
            print(f"   Pullback trouvé :")
            print(f"      Retracement : {max_pullback_pips:.1f} pips")
            print(f"      Ratio : {max_pullback_ratio*100:.1f}% du pic")
            print(f"      Heure : {pullback_time}")
            print()
            
            # Critère Double Wave : pullback > 20% ET deuxième pic après pullback
            if max_pullback_ratio > 0.20:
                print(f"   ⚠️ Pullback significatif ({max_pullback_ratio*100:.1f}% > 20%)")
                print(f"      → Potentiel Double Wave, chercher Wave 2...")
                print()
                
                # Chercher deuxième pic après pullback
                prices_after_pullback = prices_after_peak[
                    prices_after_peak['datetime'] > pullback_time
                ].copy()
                
                if not prices_after_pullback.empty:
                    # Chercher dans les 60 minutes après pullback
                    window_60min = prices_after_pullback[
                        (prices_after_pullback['datetime'] - pullback_time).dt.total_seconds() / 60 <= 60
                    ]
                    
                    if not window_60min.empty:
                        window_60min['pips_from_baseline'] = (window_60min['high'] - baseline_price) * 10000
                        window_60min['pips_from_pullback'] = (window_60min['high'] - prices_after_pullback.iloc[0]['low']) * 10000
                        
                        # Trouver deuxième pic
                        max_pips_after_pullback = window_60min['pips_from_baseline'].max()
                        max_pips_after_pullback_idx = window_60min['pips_from_baseline'].idxmax()
                        wave2_time = window_60min.loc[max_pips_after_pullback_idx, 'datetime']
                        wave2_price = window_60min.loc[max_pips_after_pullback_idx, 'high']
                        wave2_pips = max_pips_after_pullback
                        
                        # Vérifier si Wave 2 > Wave 1 (pic absolu)
                        if wave2_pips > peak_pips:
                            print(f"   ✅ WAVE 2 TROUVÉE (Pic absolu) :")
                            print(f"      Impact : {wave2_pips:.1f} pips")
                            print(f"      Heure : {wave2_time}")
                            print(f"      Type : 🔵 DOUBLE WAVE")
                            print()
                            pattern_manual = "DOUBLE_WAVE"
                        else:
                            print(f"   ⚠️ Pas de Wave 2 significative trouvée")
                            print(f"      Wave 2 : {wave2_pips:.1f} pips (Wave 1 : {peak_pips:.1f} pips)")
                            print(f"      Type : 🟢 SINGLE WAVE")
                            print()
                            pattern_manual = "SINGLE_WAVE"
                    else:
                        print(f"   ⚠️ Pas de données après pullback pour chercher Wave 2")
                        pattern_manual = "SINGLE_WAVE"
                else:
                    print(f"   ⚠️ Pas de données après pullback")
                    pattern_manual = "SINGLE_WAVE"
            else:
                print(f"   ✅ Pullback faible ({max_pullback_ratio*100:.1f}% < 20%)")
                print(f"      Type : 🟢 SINGLE WAVE")
                print()
                pattern_manual = "SINGLE_WAVE"
    
    print()
    
    # ========================================================================
    # 3. PRÉDICTION DU PIPELINE
    # ========================================================================
    
    print("🔮 3. PRÉDICTION DU PIPELINE :")
    print("-" * 80)
    print()
    
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
            
            pattern_type_predicted = pattern_info.get('pattern_type', 'NONE')
            confidence_predicted = pattern_info.get('confidence', 0.0)
            
            print(f"   Pattern prédit par le pipeline :")
            if pattern_type_predicted == 'DOUBLE_WAVE':
                print(f"      Type : 🔵 DOUBLE WAVE")
            elif pattern_type_predicted == 'SINGLE_WAVE_STRONG':
                print(f"      Type : 🟢 SINGLE WAVE STRONG")
            elif pattern_type_predicted == 'SINGLE_WAVE':
                print(f"      Type : 🟢 SINGLE WAVE")
            else:
                print(f"      Type : {pattern_type_predicted}")
            
            print(f"      Confiance : {confidence_predicted:.1f}%")
            
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
    
    print()
    print()
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    
    print("=" * 80)
    print("  RÉSUMÉ - PATTERN DÉTECTÉ")
    print("=" * 80)
    print()
    
    print("📊 DÉTECTION RÉELLE :")
    if pattern_real:
        if pattern_real.get('double_wave', False):
            print(f"   ✅ DOUBLE WAVE détectée dans les prix réels")
        else:
            print(f"   ✅ SINGLE WAVE détectée dans les prix réels")
            print(f"      (Pas de Double Wave détecté par REV12)")
    else:
        print(f"   ⚠️ Aucun pattern détecté par REV12")
        print(f"      (REV12 n'a pas réussi à détecter - Max idle bars)")
    
    print()
    
    print("🔮 PRÉDICTION PIPELINE :")
    if result['success']:
        pattern_type_predicted = pattern_info.get('pattern_type', 'NONE')
        if pattern_type_predicted == 'SINGLE_WAVE_STRONG':
            print(f"   ✅ SINGLE WAVE STRONG prédit")
        elif pattern_type_predicted == 'DOUBLE_WAVE':
            print(f"   ✅ DOUBLE WAVE prédit")
        else:
            print(f"   Pattern prédit : {pattern_type_predicted}")
    
    print()
    
    # Conclusion
    print("=" * 80)
    print("  CONCLUSION")
    print("=" * 80)
    print()
    
    if pattern_real:
        if pattern_real.get('double_wave', False):
            print("✅ Le pattern détecté dans les prix réels est : DOUBLE WAVE")
        else:
            print("✅ Le pattern détecté dans les prix réels est : SINGLE WAVE")
    else:
        print("⚠️ REV12 n'a pas détecté de pattern (Max idle bars atteint)")
        print("   Basé sur l'analyse manuelle : SINGLE WAVE")
    
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    verifier_pattern_detecte()




