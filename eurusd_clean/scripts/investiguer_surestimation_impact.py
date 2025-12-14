#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION SUREESTIMATION IMPACT - 1ER AOÛT 2025
====================================================

Investigation pourquoi l'impact prédit (250.82 pips) est surestimé
par rapport à la mesure réelle (188.3 pips).

Questions :
1. Le Random Forest est-il appliqué ?
2. Est-il appliqué au bon endroit ?
3. Quels sont les facteurs qui contribuent à la surestimation ?

Date: 2025-01-XX
"""

import sys
from pathlib import Path
from datetime import datetime
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_surestimation():
    """Investigation de la surestimation"""
    
    date_str = '2025-08-01'
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION SUREESTIMATION IMPACT - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    print(f"📊 Mesure réelle : 188.3 pips")
    print(f"🔮 Impact prédit : 250.82 pips")
    print(f"⚠️ Écart : 62.5 pips (33% d'erreur)")
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=True)
    
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
            results = result.get('results', {})
            
            print()
            print("=" * 80)
            print("  ANALYSE DÉTAILLÉE DES CALCULS")
            print("=" * 80)
            print()
            
            # Étape 5 : Tendances
            if 'etape5_tendances' in results:
                tendances = results['etape5_tendances']
                if not tendances.empty:
                    print("📊 ÉTAPE 5 - TENDANCES :")
                    print("-" * 80)
                    for idx, row in tendances.iterrows():
                        print(f"   R² : {row.get('r2', 0):.3f}")
                        print(f"   Direction : {row.get('direction', 'UNKNOWN')}")
                        print(f"   Amplitude : {row.get('amplitude_pips', 0):.1f} pips")
                    print()
            
            # Étape 6 : Impacts
            if 'etape6_impacts' in results:
                impacts = results['etape6_impacts']
                if not impacts.empty:
                    print("📊 ÉTAPE 6 - IMPACTS :")
                    print("-" * 80)
                    for idx, row in impacts.iterrows():
                        impact_base = row.get('impact_base', 0.0)
                        impact_reel = row.get('impact_reel', 0.0)
                        amplification_parfaite = row.get('amplification_parfaite', 1.0)
                        
                        print(f"   Cluster {idx+1}:")
                        print(f"      Impact de base : {impact_base:.2f} pips")
                        print(f"      Impact réel : {impact_reel:.2f} pips")
                        print(f"      Amplification parfaite : {amplification_parfaite:.3f}x")
                        print()
            
            # Étape 7 : Analyse relation tendance/amplification
            if 'etape7_analysis' in results:
                etape7 = results['etape7_analysis']
                print("📊 ÉTAPE 7 - ANALYSE RELATION TENDANCE/AMPLIFICATION :")
                print("-" * 80)
                
                amplification_predite = etape7.get('amplification_predite', 1.0)
                method_used = etape7.get('method_used', 'unknown')
                trend_r2 = etape7.get('trend_r2', 0.0)
                
                print(f"   Amplification prédite : {amplification_predite:.3f}x")
                print(f"   Méthode utilisée : {method_used}")
                print(f"   R² tendance : {trend_r2:.3f}")
                
                # Vérifier si Random Forest est utilisé
                if 'random_forest' in method_used.lower():
                    print(f"   ✅ Random Forest utilisé")
                    rf_prediction = etape7.get('rf_prediction', None)
                    if rf_prediction:
                        print(f"      Prédiction RF : {rf_prediction:.3f}x")
                else:
                    print(f"   ⚠️ Random Forest NON utilisé")
                    print(f"      Méthode : {method_used}")
                
                print()
            
            # Calcul final
            impact_base = final_prediction.get('impact_base', 0.0)
            amplification_predite = final_prediction.get('amplification_predite', 1.0)
            adjustment_factor = final_prediction.get('adjustment_factor', 1.0)
            prediction_finale = final_prediction.get('prediction_finale', 0.0)
            
            print("🔮 CALCUL FINAL DE L'IMPACT :")
            print("-" * 80)
            print()
            print(f"   Impact de base : {impact_base:.2f} pips")
            print(f"   Amplification prédite : {amplification_predite:.3f}x")
            print(f"   Facteur d'ajustement : {adjustment_factor:.3f}x")
            print()
            print(f"   Calcul : {impact_base:.2f} × {amplification_predite:.3f} × {adjustment_factor:.3f}")
            print(f"   = {impact_base * amplification_predite * adjustment_factor:.2f} pips")
            print()
            print(f"   Prédiction finale : {prediction_finale:.2f} pips")
            print()
            
            # Comparaison
            mesure_reelle = 188.3
            ecart = abs(prediction_finale - mesure_reelle)
            ecart_pct = (ecart / mesure_reelle) * 100
            
            print("📊 COMPARAISON :")
            print("-" * 80)
            print()
            print(f"   Mesure réelle : {mesure_reelle:.1f} pips")
            print(f"   Prédiction finale : {prediction_finale:.2f} pips")
            print(f"   Écart : {ecart:.1f} pips ({ecart_pct:.1f}%)")
            print()
            
            # Analyse des contributions
            print("🔍 ANALYSE DES CONTRIBUTIONS À LA SUREESTIMATION :")
            print("-" * 80)
            print()
            
            # Impact de base
            impact_base_ratio = impact_base / mesure_reelle
            print(f"1. Impact de base :")
            print(f"   {impact_base:.2f} pips / {mesure_reelle:.1f} pips = {impact_base_ratio:.2f}x")
            if impact_base > mesure_reelle:
                surestimation_base = impact_base - mesure_reelle
                print(f"   ⚠️ Surestimation de base : {surestimation_base:.1f} pips")
            print()
            
            # Amplification
            if amplification_predite != 1.0:
                print(f"2. Amplification :")
                print(f"   {amplification_predite:.3f}x")
                if amplification_predite > 1.0:
                    contribution_amplif = (impact_base * (amplification_predite - 1.0))
                    print(f"   ⚠️ Contribution à la surestimation : {contribution_amplif:.1f} pips")
            else:
                print(f"2. Amplification : 1.0x (pas d'amplification)")
            print()
            
            # Ajustements
            if adjustment_factor != 1.0:
                print(f"3. Facteur d'ajustement :")
                print(f"   {adjustment_factor:.3f}x")
                if adjustment_factor > 1.0:
                    contribution_ajust = (impact_base * amplification_predite * (adjustment_factor - 1.0))
                    print(f"   ⚠️ Contribution à la surestimation : {contribution_ajust:.1f} pips")
            else:
                print(f"3. Facteur d'ajustement : 1.0x (pas d'ajustement)")
            print()
            
            # Diagnostic
            print("=" * 80)
            print("  DIAGNOSTIC")
            print("=" * 80)
            print()
            
            if impact_base > mesure_reelle:
                print("⚠️ PROBLÈME PRINCIPAL : Impact de base trop élevé")
                print(f"   Impact de base ({impact_base:.2f} pips) > Mesure réelle ({mesure_reelle:.1f} pips)")
                print(f"   → La formule D surestime l'impact")
                print()
            
            if amplification_predite > 1.0:
                print(f"⚠️ AMPLIFICATION APPLIQUÉE : {amplification_predite:.3f}x")
                if 'random_forest' not in method_used.lower():
                    print(f"   ⚠️ Random Forest NON utilisé - amplification basée sur {method_used}")
                    print(f"   → L'amplification pourrait être mal calculée")
                else:
                    print(f"   ✅ Random Forest utilisé")
            else:
                print("ℹ️ Pas d'amplification appliquée (1.0x)")
            
            if adjustment_factor != 1.0:
                print(f"ℹ️ Ajustements appliqués : {adjustment_factor:.3f}x")
            
        else:
            print(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    investiguer_surestimation()




