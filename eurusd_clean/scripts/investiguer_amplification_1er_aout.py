#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION AMPLIFICATION - 1ER AOÛT 2025
===========================================

Vérifie pourquoi l'amplification calculée (0.246x) n'est pas appliquée
dans la prédiction finale.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_amplification():
    """Investigation détaillée de l'amplification"""
    
    date_str = '2025-08-01'
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION AMPLIFICATION - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=True)
    
    try:
        # Exécuter le pipeline
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if not result['success']:
            print(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
            return
        
        final_prediction = result['final_prediction']
        results = result['results']
        
        print()
        print("=" * 80)
        print("  ANALYSE AMPLIFICATION")
        print("=" * 80)
        print()
        
        # 1. Vérifier l'amplification calculée
        print("1️⃣ AMPLIFICATION CALCULÉE :")
        print("-" * 80)
        print()
        
        amplification_predite = final_prediction.get('amplification_predite', 1.0)
        impact_base = final_prediction.get('impact_base', 0.0)
        prediction_finale = final_prediction.get('prediction_finale', 0.0)
        
        print(f"   Impact de base : {impact_base:.2f} pips")
        print(f"   Amplification prédite : {amplification_predite:.3f}x")
        print(f"   Prédiction finale : {prediction_finale:.2f} pips")
        print()
        
        # Calculer ce que devrait être la prédiction avec amplification
        impact_avec_amplification = impact_base * amplification_predite
        print(f"   Calcul attendu (base * amplification) : {impact_base:.2f} * {amplification_predite:.3f} = {impact_avec_amplification:.2f} pips")
        print()
        
        if abs(prediction_finale - impact_avec_amplification) > 1.0:
            print(f"   ⚠️ INCOHÉRENCE : Prédiction finale ({prediction_finale:.2f}) ≠ Calcul attendu ({impact_avec_amplification:.2f})")
            print()
        
        # 2. Vérifier les résultats de l'étape 7
        print("2️⃣ RÉSULTATS ÉTAPE 7 (Analyse Relation Tendance → Amplification) :")
        print("-" * 80)
        print()
        
        etape7_analysis = results.get('etape7_analysis', {})
        results_df = etape7_analysis.get('results_df')
        
        if results_df is not None and not results_df.empty:
            print(f"   Nombre de clusters analysés : {len(results_df)}")
            print()
            
            if 'amplification_parfaite' in results_df.columns:
                amplification_moyenne = results_df['amplification_parfaite'].mean()
                print(f"   Amplification parfaite moyenne : {amplification_moyenne:.3f}x")
                print()
                
                # Afficher quelques exemples
                print("   Exemples d'amplifications parfaites :")
                for idx, row in results_df.head(5).iterrows():
                    amp = row.get('amplification_parfaite', 0.0)
                    impact_base_hist = row.get('impact_base', 0.0)
                    impact_reel = row.get('impact_reel', 0.0)
                    print(f"      Cluster {idx+1}: base={impact_base_hist:.1f}, réel={impact_reel:.1f}, amp={amp:.3f}x")
                print()
        else:
            print("   ⚠️ Aucun résultat de l'étape 7 disponible")
            print()
        
        # 3. Vérifier la stratégie hybride Pattern/Formules
        print("3️⃣ STRATÉGIE HYBRIDE PATTERN/FORMULES :")
        print("-" * 80)
        print()
        
        pattern_info = final_prediction.get('pattern_info', {})
        pattern_type = final_prediction.get('pattern_type', 'NONE')
        
        print(f"   Type de pattern : {pattern_type}")
        print()
        
        # Calculer impact_formules
        adjustment_factor = 1.0  # Par défaut
        impact_formules = impact_base * amplification_predite * adjustment_factor
        
        # Calculer pattern_impact
        pattern_impact = 0.0
        if pattern_info.get('wave2_peak_pips_absolute', 0) > 0:
            pattern_impact = pattern_info['wave2_peak_pips_absolute']
        elif pattern_info.get('wave2_pips', 0) > 0:
            pattern_impact = pattern_info['wave2_pips']
        
        print(f"   Impact formules (base * amplification) : {impact_formules:.2f} pips")
        print(f"   Impact pattern (pic absolu) : {pattern_impact:.2f} pips")
        print()
        
        if pattern_impact > 0:
            ecart_absolu = abs(pattern_impact - impact_formules)
            print(f"   Écart absolu : {ecart_absolu:.2f} pips")
            print()
            
            if ecart_absolu < 10:
                print(f"   ✅ Stratégie : Formules (écart < 10 pips)")
                print(f"      → Prédiction finale devrait être : {impact_formules:.2f} pips")
            else:
                print(f"   ✅ Stratégie : Pattern (écart >= 10 pips)")
                print(f"      → Prédiction finale devrait être : {pattern_impact:.2f} pips")
            print()
            
            if abs(prediction_finale - pattern_impact) < 1.0:
                print(f"   ✅ Cohérent : Prédiction finale utilise le pattern")
            elif abs(prediction_finale - impact_formules) < 1.0:
                print(f"   ✅ Cohérent : Prédiction finale utilise les formules")
            else:
                print(f"   ⚠️ INCOHÉRENT : Prédiction finale ({prediction_finale:.2f}) ne correspond ni au pattern ({pattern_impact:.2f}) ni aux formules ({impact_formules:.2f})")
        
        # 4. Vérifier les tendances
        print("4️⃣ TENDANCES :")
        print("-" * 80)
        print()
        
        trend_exists = final_prediction.get('trend_exists', False)
        trend_r2 = final_prediction.get('trend_r2', 0.0)
        trend_direction = final_prediction.get('trend_direction', 'UNKNOWN')
        
        print(f"   Tendance détectée : {trend_exists}")
        if trend_exists:
            print(f"   R² : {trend_r2:.3f}")
            print(f"   Direction : {trend_direction}")
        print()
        
        # 5. Résumé final
        print("=" * 80)
        print("  RÉSUMÉ")
        print("=" * 80)
        print()
        
        print(f"📊 Valeurs clés :")
        print(f"   Impact de base : {impact_base:.2f} pips")
        print(f"   Amplification prédite : {amplification_predite:.3f}x")
        print(f"   Impact avec amplification : {impact_avec_amplification:.2f} pips")
        print(f"   Pattern impact : {pattern_impact:.2f} pips")
        print(f"   Prédiction finale : {prediction_finale:.2f} pips")
        print()
        
        if pattern_impact > 0:
            if abs(prediction_finale - pattern_impact) < 1.0:
                print("✅ Conclusion : La prédiction finale utilise le pattern (stratégie hybride)")
                print(f"   → L'amplification n'est pas appliquée car le pattern l'emporte (écart >= 10 pips)")
            elif abs(prediction_finale - impact_formules) < 1.0:
                print("✅ Conclusion : La prédiction finale utilise les formules avec amplification")
                print(f"   → L'amplification est correctement appliquée")
            else:
                print("⚠️ Conclusion : La prédiction finale ne correspond ni au pattern ni aux formules")
                print(f"   → Investigation nécessaire")
        else:
            if abs(prediction_finale - impact_avec_amplification) < 1.0:
                print("✅ Conclusion : L'amplification est correctement appliquée")
            else:
                print("⚠️ Conclusion : L'amplification n'est pas appliquée correctement")
                print(f"   → Investigation nécessaire")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investiguer_amplification()




