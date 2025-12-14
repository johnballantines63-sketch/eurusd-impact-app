#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFICHAGE PICS ET PULLBACKS DÉTECTÉS
=====================================

Affiche les détails des pics et pullbacks détectés par le pipeline
pour une date donnée.

Date: 2025-01-XX
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

# Ajouter le chemin parent pour les imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def format_timestamp(ts):
    """Formate un timestamp pour affichage"""
    if ts is None:
        return "N/A"
    if isinstance(ts, pd.Timestamp):
        return ts.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(ts, datetime):
        return ts.strftime('%Y-%m-%d %H:%M:%S')
    return str(ts)

def format_price(price):
    """Formate un prix pour affichage"""
    if price is None:
        return "N/A"
    return f"{price:.5f}"

def format_pips(pips):
    """Formate des pips pour affichage"""
    if pips is None or pips == 0:
        return "N/A"
    return f"{pips:.1f} pips"

def afficher_pattern_info(pattern_info, baseline_price=None):
    """Affiche les informations détaillées d'un pattern"""
    print("\n" + "=" * 80)
    print("  DÉTAILS DU PATTERN DÉTECTÉ")
    print("=" * 80)
    print()
    
    pattern_type = pattern_info.get('pattern_type', 'NONE')
    print(f"📊 Type de pattern : {pattern_type}")
    print(f"   Direction : {pattern_info.get('direction', 'UNKNOWN')}")
    print(f"   Confiance : {pattern_info.get('confidence', 0.0):.1f}%")
    print()
    
    if baseline_price:
        print(f"💰 Prix de référence (baseline) : {format_price(baseline_price)}")
        print()
    
    # Informations Wave 1
    wave1_pips = pattern_info.get('wave1_pips', 0.0)
    wave1_peak_time = pattern_info.get('wave1_peak_time')
    print("📈 WAVE 1 (Premier pic) :")
    print(f"   Impact : {format_pips(wave1_pips)}")
    print(f"   Heure du pic : {format_timestamp(wave1_peak_time)}")
    
    if wave1_peak_time and baseline_price:
        if wave1_pips > 0:
            wave1_price = baseline_price + (wave1_pips / 10000)
            print(f"   Prix au pic : {format_price(wave1_price)}")
    
    print()
    
    # Informations Pullback
    pullback_pips = pattern_info.get('pullback_pips', 0.0)
    pullback_low_time = pattern_info.get('pullback_low_time')
    print("📉 PULLBACK (Creux) :")
    print(f"   Retracement : {format_pips(pullback_pips)}")
    print(f"   Heure du creux : {format_timestamp(pullback_low_time)}")
    
    if pullback_low_time and baseline_price and wave1_pips > 0:
        pullback_price = baseline_price + ((wave1_pips - pullback_pips) / 10000)
        print(f"   Prix au creux : {format_price(pullback_price)}")
        if wave1_pips > 0:
            pullback_ratio = (pullback_pips / wave1_pips) * 100 if wave1_pips > 0 else 0
            print(f"   Ratio de retracement : {pullback_ratio:.1f}% de Wave 1")
    
    print()
    
    # Informations Wave 2 (Pic absolu)
    wave2_pips_absolute = pattern_info.get('wave2_peak_pips_absolute', 0.0)
    wave2_peak_time = pattern_info.get('wave2_peak_time')
    print("📈 WAVE 2 (Pic absolu) :")
    print(f"   Impact total : {format_pips(wave2_pips_absolute)}")
    print(f"   Heure du pic absolu : {format_timestamp(wave2_peak_time)}")
    
    if wave2_peak_time and baseline_price:
        if wave2_pips_absolute > 0:
            wave2_price = baseline_price + (wave2_pips_absolute / 10000)
            print(f"   Prix au pic absolu : {format_price(wave2_price)}")
    
    print()
    
    # Timings depuis l'événement
    timings_predicted = pattern_info.get('timings_predicted', False)
    print(f"⏰ Timings : {'PRÉDITS (Session 64)' if timings_predicted else 'DÉTECTÉS dans les prix'}")
    print()
    
    stabilization_time = pattern_info.get('stabilization_time')
    if stabilization_time:
        print(f"🛑 Stabilisation : {format_timestamp(stabilization_time)}")
        print()

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Affiche les pics et pullbacks détectés')
    parser.add_argument('--date', type=str, default='2025-09-11', help='Date au format YYYY-MM-DD')
    parser.add_argument('--verbose', action='store_true', help='Mode verbose')
    
    args = parser.parse_args()
    
    date_str = args.date
    
    print()
    print("=" * 80)
    print(f"  ANALYSE DES PICS ET PULLBACKS DÉTECTÉS - {date_str}")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=args.verbose)
    
    print(f"🚀 Exécution du pipeline pour {date_str}...")
    print()
    
    try:
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if not result['success']:
            print(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
            return 1
        
        print()
        print("=" * 80)
        print("  RÉSULTATS")
        print("=" * 80)
        print()
        
        final_prediction = result['final_prediction']
        
        # Informations générales
        print("📊 PRÉDICTION FINALE :")
        print(f"   Impact de base : {final_prediction.get('impact_base', 0):.2f} pips")
        print(f"   Amplification prédite : {final_prediction.get('amplification_predite', 1.0):.3f}x")
        print(f"   Impact prédit final : {final_prediction.get('prediction_finale', 0):.2f} pips")
        print(f"   Target de sortie : {final_prediction.get('exit_target', 0):.2f} pips")
        print()
        
        # Informations tendance
        if final_prediction.get('trend_exists', False):
            print("📈 TENDANCE DÉTECTÉE :")
            print(f"   Direction : {final_prediction.get('trend_direction', 'UNKNOWN')}")
            print(f"   R² : {final_prediction.get('trend_r2', 0.0):.3f}")
            print(f"   Amplitude : {final_prediction.get('trend_amplitude_pips', 0.0):.1f} pips")
            print()
        
        # Informations pattern
        pattern_info = final_prediction.get('pattern_info', {})
        baseline_price = final_prediction.get('baseline_price')
        
        if pattern_info and pattern_info.get('pattern_type') != 'NONE':
            afficher_pattern_info(pattern_info, baseline_price)
        else:
            print("⚠️ Aucun pattern détecté (NONE)")
            print()
        
        # Tableau récapitulatif des timings
        print()
        print("=" * 80)
        print("  TABLEAU RÉCAPITULATIF DES TIMINGS")
        print("=" * 80)
        print()
        
        timings_data = []
        
        if baseline_price:
            timings_data.append({
                'Étape': 'Baseline (Départ)',
                'Heure': format_timestamp(final_prediction.get('baseline_price_time')),
                'Prix': format_price(baseline_price),
                'Pips': '0.0'
            })
        
        wave1_peak_time = pattern_info.get('wave1_peak_time')
        if wave1_peak_time:
            wave1_pips = pattern_info.get('wave1_pips', 0.0)
            wave1_price = baseline_price + (wave1_pips / 10000) if baseline_price and wave1_pips > 0 else None
            timings_data.append({
                'Étape': 'Wave 1 (Pic 1)',
                'Heure': format_timestamp(wave1_peak_time),
                'Prix': format_price(wave1_price) if wave1_price else 'N/A',
                'Pips': format_pips(wave1_pips)
            })
        
        pullback_low_time = pattern_info.get('pullback_low_time')
        if pullback_low_time:
            pullback_pips = pattern_info.get('pullback_pips', 0.0)
            wave1_pips = pattern_info.get('wave1_pips', 0.0)
            pullback_price = baseline_price + ((wave1_pips - pullback_pips) / 10000) if baseline_price and wave1_pips > 0 else None
            timings_data.append({
                'Étape': 'Pullback (Creux)',
                'Heure': format_timestamp(pullback_low_time),
                'Prix': format_price(pullback_price) if pullback_price else 'N/A',
                'Pips': format_pips(pullback_pips) + " retrace"
            })
        
        wave2_peak_time = pattern_info.get('wave2_peak_time')
        if wave2_peak_time:
            wave2_pips = pattern_info.get('wave2_peak_pips_absolute', 0.0)
            wave2_price = baseline_price + (wave2_pips / 10000) if baseline_price and wave2_pips > 0 else None
            timings_data.append({
                'Étape': 'Wave 2 (Pic Absolu)',
                'Heure': format_timestamp(wave2_peak_time),
                'Prix': format_price(wave2_price) if wave2_price else 'N/A',
                'Pips': format_pips(wave2_pips)
            })
        
        stabilization_time = pattern_info.get('stabilization_time')
        if stabilization_time:
            timings_data.append({
                'Étape': 'Stabilisation',
                'Heure': format_timestamp(stabilization_time),
                'Prix': 'N/A',
                'Pips': 'N/A'
            })
        
        if timings_data:
            df_timings = pd.DataFrame(timings_data)
            print(df_timings.to_string(index=False))
        else:
            print("⚠️ Aucun timing disponible")
        
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)




