#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRACEUR VALEURS ÉTAPE 8 - DÉTAIL COMPLET
==========================================

Ajoute des logs détaillés dans l'étape 8 pour tracer précisément
chaque valeur intermédiaire et identifier où le problème se produit.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

def tracer_etape8_detaille():
    """Exécute le pipeline et trace toutes les valeurs de l'étape 8"""
    
    date_str = '2025-08-01'
    
    print("\n" + "=" * 80)
    print(f"  TRACEUR VALEURS ÉTAPE 8 - {date_str}")
    print("=" * 80)
    print()
    print("⚠️  Les logs détaillés ci-dessous montrent toutes les valeurs")
    print("    intermédiaires de l'étape 8 pour identifier le problème.")
    print()
    print("=" * 80)
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
        
        if not result['success']:
            print(f"\n❌ Erreur pipeline : {result.get('error', 'Erreur inconnue')}")
            return
        
        final_prediction = result['final_prediction']
        
        print("\n" + "=" * 80)
        print("  RÉSUMÉ FINAL - TRACEUR DÉTAILLÉ")
        print("=" * 80)
        print()
        
        # Extraire toutes les valeurs importantes
        impact_base = final_prediction.get('impact_base', 0.0)
        amplification_predite = final_prediction.get('amplification_predite', 0.0)
        adjustment_factor = final_prediction.get('adjustment_factor', 1.0)
        prediction_finale = final_prediction.get('prediction_finale', 0.0)
        
        pattern_info = final_prediction.get('pattern_info', {})
        pattern_type = final_prediction.get('pattern_type', 'NONE')
        pattern_impact = pattern_info.get('wave2_peak_pips_absolute', 0.0) or pattern_info.get('wave2_pips', 0.0)
        
        # Calculs intermédiaires
        impact_formules = impact_base * amplification_predite * adjustment_factor
        
        print("📊 VALEURS INTERMÉDIAIRES :")
        print()
        print(f"   1. Impact de base : {impact_base:.2f} pips")
        print(f"   2. Amplification prédite : {amplification_predite:.3f}x")
        print(f"   3. Ajustement (S/R + Patterns) : {adjustment_factor:.3f}x")
        print()
        print(f"   → Impact formules = {impact_base:.2f} × {amplification_predite:.3f} × {adjustment_factor:.3f}")
        print(f"   → Impact formules = {impact_formules:.2f} pips")
        print()
        
        print("📉 PATTERN :")
        print()
        print(f"   4. Pattern type : {pattern_type}")
        print(f"   5. Pattern impact (wave2_peak_pips_absolute) : {pattern_info.get('wave2_peak_pips_absolute', 0.0):.2f} pips")
        print(f"   6. Pattern impact (wave2_pips) : {pattern_info.get('wave2_pips', 0.0):.2f} pips")
        print(f"   7. Pattern impact utilisé : {pattern_impact:.2f} pips")
        print()
        
        if pattern_info:
            print("   Détails pattern :")
            print(f"     - Wave1 pips : {pattern_info.get('wave1_pips', 0.0):.2f}")
            print(f"     - Wave2 pips : {pattern_info.get('wave2_pips', 0.0):.2f}")
            print(f"     - Pullback pips : {pattern_info.get('pullback_pips', 0.0):.2f}")
            print(f"     - Baseline price : {pattern_info.get('baseline_price', 0.0):.4f}")
            print()
        
        # Écart et stratégie
        ecart_absolu = abs(pattern_impact - impact_formules) if pattern_impact > 0 else 0
        
        print("🎯 STRATÉGIE HYBRIDE :")
        print()
        print(f"   8. Écart pattern vs formules : {ecart_absolu:.2f} pips")
        print()
        
        if ecart_absolu < 10 or pattern_impact == 0:
            strategy = "Formules"
            expected = impact_formules
        else:
            strategy = "Pattern"
            expected = pattern_impact
        
        print(f"   9. Stratégie choisie : {strategy}")
        print(f"      (Écart {'<' : '<' if ecart_absolu < 10 else '>='} 10 pips)")
        print()
        print(f"   10. Valeur attendue ({strategy}) : {expected:.2f} pips")
        print(f"   11. Prédiction finale obtenue : {prediction_finale:.2f} pips")
        print()
        
        # Vérification
        diff = abs(prediction_finale - expected)
        print("✅ VÉRIFICATION :")
        print()
        if diff < 0.01:
            print(f"   ✅ Cohérent : Différence = {diff:.2f} pips < 0.01")
        else:
            print(f"   ⚠️  DIFFÉRENCE : {diff:.2f} pips")
            print(f"      → La prédiction finale ne correspond pas à la stratégie choisie !")
        print()
        
        # Analyse des problèmes
        print("=" * 80)
        print("  ANALYSE DES PROBLÈMES")
        print("=" * 80)
        print()
        
        if prediction_finale > 1000:
            print("❌ PROBLÈME CRITIQUE : Prédiction finale > 1000 pips (irréaliste)")
            print()
            if pattern_impact > 1000:
                print(f"   → Pattern impact = {pattern_impact:.2f} pips est trop élevé")
                print(f"   → Vérifier pourquoi le pic absolu est si élevé")
            if impact_formules > 1000:
                print(f"   → Impact formules = {impact_formules:.2f} pips est trop élevé")
                print(f"   → Vérifier : {impact_base:.2f} × {amplification_predite:.3f} × {adjustment_factor:.3f}")
            print()
        
        if diff > 0.01:
            print(f"⚠️  PROBLÈME : Prédiction finale ({prediction_finale:.2f}) ≠ Attendu ({expected:.2f})")
            print(f"   → La stratégie hybride ne fonctionne pas correctement")
            print()
        
        # Impact réel
        impact_reel = 188.4
        erreur = abs(prediction_finale - impact_reel)
        erreur_pct = (erreur / impact_reel * 100) if impact_reel > 0 else 0
        
        print("=" * 80)
        print("  COMPARAISON AVEC RÉALITÉ")
        print("=" * 80)
        print()
        print(f"Impact réel : {impact_reel:.1f} pips")
        print(f"Prédiction : {prediction_finale:.2f} pips")
        print(f"Erreur : {erreur:.1f} pips ({erreur_pct:.1f}%)")
        print()
        
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    tracer_etape8_detaille()




