#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFICHAGE VALEURS 1.8 et 29.5
==============================

Affiche toutes les valeurs pour identifier où apparaissent 1.8 et 29.5
dans les calculs ou résultats.

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

TZ_BERN = pytz.timezone('Europe/Zurich')

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Affiche valeurs 1.8 et 29.5')
    parser.add_argument('--date', type=str, default='2025-09-11', help='Date au format YYYY-MM-DD')
    
    args = parser.parse_args()
    date_str = args.date
    
    print("\n" + "=" * 80)
    print(f"  RECHERCHE DES VALEURS 1.8 et 29.5 - {date_str}")
    print("=" * 80)
    print()
    
    # 1. Détection réelle
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    pattern_date = event_time.replace(tzinfo=None)
    
    print("1️⃣ DÉTECTION RÉELLE DANS LES PRIX :")
    print("-" * 80)
    
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
            wave1_detected = pattern_real.get('wave1_pips', 0.0)
            wave2_detected = pattern_real.get('wave2_pips', 0.0)
            pullback1_detected = pattern_real.get('pullback1_pips', 0.0)
            baseline_price = pattern_real.get('baseline_price', 0.0)
            
            print(f"   Wave 1 détecté : {wave1_detected:.1f} pips")
            print(f"   Wave 2 détecté : {wave2_detected:.1f} pips")
            print(f"   Pullback 1 détecté : {pullback1_detected:.1f} pips")
            print(f"   Baseline price : {baseline_price:.5f}")
            
            # Calculer ratios
            if wave1_detected > 0:
                extension_factor = wave2_detected / wave1_detected
                pullback_ratio = abs(pullback1_detected) / wave1_detected
                print(f"\n   Ratios calculés :")
                print(f"      Extension (Wave2/Wave1) : {extension_factor:.3f}x")
                print(f"      Pullback ratio : {pullback_ratio:.3f} ({pullback_ratio*100:.1f}%)")
                
                # Vérifier 1.8
                if abs(extension_factor - 1.8) < 0.2:
                    print(f"      ✅ Extension proche de 1.8 : {extension_factor:.3f}x")
        else:
            print("   ⚠️ Aucun pattern détecté")
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
    
    print()
    
    # 2. Prédictions pipeline
    print("2️⃣ PRÉDICTIONS DU PIPELINE :")
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
            
            impact_base = final_prediction.get('impact_base', 0.0)
            wave1_predicted = pattern_info.get('wave1_pips', 0.0)
            wave2_predicted = pattern_info.get('wave2_peak_pips_absolute', 0.0)
            pullback_predicted = pattern_info.get('pullback_pips', 0.0)
            amplification = final_prediction.get('amplification_predite', 1.0)
            
            print(f"   Impact de base : {impact_base:.2f} pips")
            print(f"   Wave 1 prédit : {wave1_predicted:.1f} pips")
            print(f"   Wave 2 prédit : {wave2_predicted:.1f} pips")
            print(f"   Pullback prédit : {pullback_predicted:.1f} pips")
            print(f"   Amplification : {amplification:.3f}x")
            
            # Calculer ratios
            if wave1_predicted > 0:
                extension_factor_pred = wave2_predicted / wave1_predicted
                pullback_ratio_pred = abs(pullback_predicted) / wave1_predicted
                
                ratio_w1_base = wave1_predicted / impact_base if impact_base > 0 else 0
                ratio_w2_base = wave2_predicted / impact_base if impact_base > 0 else 0
                
                print(f"\n   Ratios calculés :")
                print(f"      Extension (Wave2/Wave1) : {extension_factor_pred:.3f}x")
                print(f"      Pullback ratio : {pullback_ratio_pred:.3f} ({pullback_ratio_pred*100:.1f}%)")
                print(f"      Wave1/ImpactBase : {ratio_w1_base:.3f}")
                print(f"      Wave2/ImpactBase : {ratio_w2_base:.3f}")
                
                # Vérifier 1.8
                if abs(extension_factor_pred - 1.8) < 0.2:
                    print(f"      ✅ Extension proche de 1.8 : {extension_factor_pred:.3f}x")
                if abs(ratio_w1_base - 1.8) < 0.2:
                    print(f"      ✅ Ratio Wave1/Base proche de 1.8 : {ratio_w1_base:.3f}")
                if abs(ratio_w2_base - 1.8) < 0.2:
                    print(f"      ✅ Ratio Wave2/Base proche de 1.8 : {ratio_w2_base:.3f}")
        else:
            print(f"   ❌ Erreur : {result.get('error', 'Erreur inconnue')}")
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. Recherche systématique de 1.8 et 29.5
    print("3️⃣ RECHERCHE SYSTÉMATIQUE :")
    print("-" * 80)
    
    print("\n   Valeurs autour de 1.8 :")
    valeurs_18 = []
    
    if pattern_real:
        wave1_d = pattern_real.get('wave1_pips', 0.0)
        wave2_d = pattern_real.get('wave2_pips', 0.0)
        if wave1_d > 0:
            ext = wave2_d / wave1_d
            if abs(ext - 1.8) < 0.3:
                valeurs_18.append(f"Extension détectée : {ext:.3f}x (Wave2 {wave2_d:.1f} / Wave1 {wave1_d:.1f})")
    
    if result['success']:
        final_pred = result['final_prediction']
        pattern_info = final_pred.get('pattern_info', {})
        
        w1_p = pattern_info.get('wave1_pips', 0.0)
        w2_p = pattern_info.get('wave2_peak_pips_absolute', 0.0)
        impact_b = final_pred.get('impact_base', 0.0)
        amplif = final_pred.get('amplification_predite', 1.0)
        
        if w1_p > 0:
            ext_p = w2_p / w1_p
            if abs(ext_p - 1.8) < 0.3:
                valeurs_18.append(f"Extension prédite : {ext_p:.3f}x (Wave2 {w2_p:.1f} / Wave1 {w1_p:.1f})")
        
        if impact_b > 0:
            r1 = w1_p / impact_b
            r2 = w2_p / impact_b
            if abs(r1 - 1.8) < 0.3:
                valeurs_18.append(f"Ratio Wave1/Base : {r1:.3f} (Wave1 {w1_p:.1f} / Base {impact_b:.2f})")
            if abs(r2 - 1.8) < 0.3:
                valeurs_18.append(f"Ratio Wave2/Base : {r2:.3f} (Wave2 {w2_p:.1f} / Base {impact_b:.2f})")
        
        if abs(amplif - 1.8) < 0.3:
            valeurs_18.append(f"Amplification : {amplif:.3f}x")
    
    if valeurs_18:
        for v in valeurs_18:
            print(f"      • {v}")
    else:
        print("      Aucune valeur proche de 1.8 trouvée")
    
    print("\n   Valeurs autour de 29.5 :")
    valeurs_295 = []
    
    if pattern_real:
        w1_d = pattern_real.get('wave1_pips', 0.0)
        w2_d = pattern_real.get('wave2_pips', 0.0)
        pb1_d = abs(pattern_real.get('pullback1_pips', 0.0))
        
        if abs(w1_d - 29.5) < 3.0:
            valeurs_295.append(f"Wave 1 détecté : {w1_d:.1f} pips")
        if abs(w2_d - 29.5) < 3.0:
            valeurs_295.append(f"Wave 2 détecté : {w2_d:.1f} pips")
        if abs(pb1_d - 29.5) < 3.0:
            valeurs_295.append(f"Pullback détecté : {pb1_d:.1f} pips")
    
    if result['success']:
        final_pred = result['final_prediction']
        pattern_info = final_pred.get('pattern_info', {})
        
        w1_p = pattern_info.get('wave1_pips', 0.0)
        w2_p = pattern_info.get('wave2_peak_pips_absolute', 0.0)
        pb_p = abs(pattern_info.get('pullback_pips', 0.0))
        impact_b = final_pred.get('impact_base', 0.0)
        
        if abs(w1_p - 29.5) < 3.0:
            valeurs_295.append(f"Wave 1 prédit : {w1_p:.1f} pips")
        if abs(w2_p - 29.5) < 3.0:
            valeurs_295.append(f"Wave 2 prédit : {w2_p:.1f} pips")
        if abs(pb_p - 29.5) < 3.0:
            valeurs_295.append(f"Pullback prédit : {pb_p:.1f} pips")
        if abs(impact_b - 29.5) < 3.0:
            valeurs_295.append(f"Impact de base : {impact_b:.2f} pips")
    
    if valeurs_295:
        for v in valeurs_295:
            print(f"      • {v}")
    else:
        print("      Aucune valeur proche de 29.5 trouvée")
    
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()




