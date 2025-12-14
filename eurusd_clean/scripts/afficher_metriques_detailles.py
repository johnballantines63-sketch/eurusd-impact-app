#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFICHAGE MÉTRIQUES DÉTAILLÉES - Toutes les Valeurs
====================================================

Affiche toutes les métriques calculées par le pipeline
pour identifier les valeurs spécifiques demandées.

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

def afficher_toutes_metriques(result):
    """Affiche toutes les métriques du pipeline"""
    
    if not result['success']:
        print(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
        return
    
    final_prediction = result['final_prediction']
    pattern_info = final_prediction.get('pattern_info', {})
    
    print("\n" + "=" * 80)
    print("  TOUTES LES MÉTRIQUES CALCULÉES")
    print("=" * 80)
    print()
    
    # 1. Impacts
    print("📊 IMPACTS :")
    print(f"   Impact de base : {final_prediction.get('impact_base', 0):.2f} pips")
    print(f"   Amplification prédite : {final_prediction.get('amplification_predite', 1.0):.3f}x")
    print(f"   Impact prédit final : {final_prediction.get('prediction_finale', 0):.2f} pips")
    print(f"   Target sortie : {final_prediction.get('exit_target', 0):.2f} pips")
    print()
    
    # 2. Tendance
    print("📈 TENDANCE :")
    print(f"   Existe : {final_prediction.get('trend_exists', False)}")
    print(f"   R² : {final_prediction.get('trend_r2', 0.0):.3f}")
    print(f"   Direction : {final_prediction.get('trend_direction', 'UNKNOWN')}")
    print(f"   Amplitude : {final_prediction.get('trend_amplitude_pips', 0.0):.1f} pips")
    print()
    
    # 3. Pattern - Toutes les valeurs
    print("🔍 PATTERN - TOUTES LES VALEURS :")
    print(f"   Type : {pattern_info.get('pattern_type', 'NONE')}")
    print(f"   Direction : {pattern_info.get('direction', 'UNKNOWN')}")
    print(f"   Confiance : {pattern_info.get('confidence', 0.0):.1f}%")
    print()
    
    print("   Wave 1 :")
    print(f"      Pips : {pattern_info.get('wave1_pips', 0.0):.1f}")
    print(f"      Heure : {pattern_info.get('wave1_peak_time', 'N/A')}")
    print()
    
    print("   Pullback :")
    print(f"      Pips : {pattern_info.get('pullback_pips', 0.0):.1f}")
    print(f"      Heure : {pattern_info.get('pullback_low_time', 'N/A')}")
    print()
    
    print("   Wave 2 :")
    print(f"      Pips : {pattern_info.get('wave2_pips', 0.0):.1f}")
    print(f"      Pic absolu (pips) : {pattern_info.get('wave2_peak_pips_absolute', 0.0):.1f}")
    print(f"      Heure : {pattern_info.get('wave2_peak_time', 'N/A')}")
    print()
    
    print("   Autres :")
    print(f"      Baseline price : {pattern_info.get('baseline_price', 'N/A')}")
    print(f"      Stabilization time : {pattern_info.get('stabilization_time', 'N/A')}")
    print(f"      Timings prédits : {pattern_info.get('timings_predicted', False)}")
    print()
    
    # 4. Ratios et facteurs
    print("🔢 RATIOS ET FACTEURS :")
    
    wave1_pips = pattern_info.get('wave1_pips', 0.0)
    pullback_pips = pattern_info.get('pullback_pips', 0.0)
    wave2_pips = pattern_info.get('wave2_peak_pips_absolute', 0.0)
    impact_base = final_prediction.get('impact_base', 0.0)
    amplification = final_prediction.get('amplification_predite', 1.0)
    
    if wave1_pips > 0 and pullback_pips > 0:
        pullback_ratio = (pullback_pips / wave1_pips) * 100
        print(f"   Ratio pullback/Wave1 : {pullback_ratio:.1f}%")
        print(f"   Valeur : {pullback_pips / wave1_pips:.3f}")
    
    if wave1_pips > 0 and wave2_pips > 0:
        extension_factor = wave2_pips / wave1_pips
        print(f"   Extension Wave2/Wave1 : {extension_factor:.2f}x")
        print(f"   Valeur : {extension_factor:.3f}")
    
    if impact_base > 0:
        ratio_wave1_base = wave1_pips / impact_base if wave1_pips > 0 else 0
        ratio_wave2_base = wave2_pips / impact_base if wave2_pips > 0 else 0
        print(f"   Ratio Wave1/ImpactBase : {ratio_wave1_base:.3f}")
        print(f"   Ratio Wave2/ImpactBase : {ratio_wave2_base:.3f}")
    
    print(f"   Amplification : {amplification:.3f}x")
    print()
    
    # 5. Résultats intermédiaires
    if 'results' in result:
        results = result['results']
        
        print("📋 RÉSULTATS INTERMÉDIAIRES :")
        
        # Étape 6
        if 'etape6_impacts' in results and not results['etape6_impacts'].empty:
            impacts_df = results['etape6_impacts']
            print(f"\n   Étape 6 - Impacts calculés ({len(impacts_df)} clusters) :")
            for idx, row in impacts_df.iterrows():
                print(f"      Cluster {idx+1}:")
                print(f"         Impact base : {row.get('impact_base', 0):.2f} pips")
                print(f"         Impact réel : {row.get('impact_reel', 0):.2f} pips")
                print(f"         Amplification parfaite : {row.get('amplification_parfaite', 1.0):.3f}x")
                print(f"         Direction : {row.get('direction', 0)}")
        
        print()

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Affiche toutes les métriques détaillées')
    parser.add_argument('--date', type=str, default='2025-09-11', help='Date au format YYYY-MM-DD')
    
    args = parser.parse_args()
    
    date_str = args.date
    
    print()
    print("=" * 80)
    print(f"  MÉTRIQUES DÉTAILLÉES - {date_str}")
    print("=" * 80)
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
        
        afficher_toutes_metriques(result)
        
        # Rechercher valeurs spécifiques
        print("=" * 80)
        print("  RECHERCHE DE VALEURS SPÉCIFIQUES")
        print("=" * 80)
        print()
        
        final_prediction = result['final_prediction']
        pattern_info = final_prediction.get('pattern_info', {})
        
        # Rechercher 1.8
        print("🔍 Valeurs proches de 1.8 :")
        values_18 = []
        
        amplification = final_prediction.get('amplification_predite', 1.0)
        if abs(amplification - 1.8) < 0.2:
            values_18.append(f"Amplification prédite : {amplification:.3f}x")
        
        wave1_pips = pattern_info.get('wave1_pips', 0.0)
        wave2_pips = pattern_info.get('wave2_peak_pips_absolute', 0.0)
        if wave1_pips > 0 and wave2_pips > 0:
            extension = wave2_pips / wave1_pips
            if abs(extension - 1.8) < 0.2:
                values_18.append(f"Extension Wave2/Wave1 : {extension:.2f}x")
        
        if values_18:
            for v in values_18:
                print(f"   ✅ {v}")
        else:
            print("   Aucune valeur proche de 1.8 trouvée")
        
        print()
        
        # Rechercher 29.5
        print("🔍 Valeurs proches de 29.5 :")
        values_295 = []
        
        impact_base = final_prediction.get('impact_base', 0.0)
        if abs(impact_base - 29.5) < 2.0:
            values_295.append(f"Impact de base : {impact_base:.2f} pips")
        
        if abs(wave1_pips - 29.5) < 2.0:
            values_295.append(f"Wave 1 pips : {wave1_pips:.1f} pips")
        
        pullback_pips = pattern_info.get('pullback_pips', 0.0)
        if abs(pullback_pips - 29.5) < 2.0:
            values_295.append(f"Pullback pips : {pullback_pips:.1f} pips")
        
        trend_amplitude = final_prediction.get('trend_amplitude_pips', 0.0)
        if abs(trend_amplitude - 29.5) < 2.0:
            values_295.append(f"Tendance amplitude : {trend_amplitude:.1f} pips")
        
        if values_295:
            for v in values_295:
                print(f"   ✅ {v}")
        else:
            print("   Aucune valeur proche de 29.5 trouvée")
        
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

