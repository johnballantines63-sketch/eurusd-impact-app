#!/usr/bin/env python3
"""
SESSION 126 - MODULE 6 : DÉCISION INTÉGRATION
==============================================
Décision automatique intégration fonction calibrée

Basé sur : PIPELINE_AUTOMATISE_REUTILISABLE.md (Session 125)
"""
import sys
from pathlib import Path
from typing import Dict


def decide_integration(
    validation_metrics: Dict,
    threshold_excellent: float = 50.0,
    threshold_good: float = 30.0,
    threshold_moderate: float = 10.0
) -> Dict:
    """
    Décision automatique intégration fonction calibrée
    
    Args:
        validation_metrics: Métriques de validate_predictions_with_baseline()
            {
                'n_samples': int,
                'mae_function': float,
                'mae_baseline': float,
                'improvement_mae_pct': float,
                ...
            }
        threshold_excellent: % amélioration pour "EXCELLENT" (default: 50%)
        threshold_good: % amélioration pour "GOOD" (default: 30%)
        threshold_moderate: % amélioration pour "MODERATE" (default: 10%)
    
    Returns:
        {
            'decision': str,  # 'EXCELLENT' | 'GOOD' | 'MODERATE' | 'FAILED'
            'improvement_pct': float,
            'metrics_summary': Dict,
            'recommendation': str,
            'next_steps': List[str],
            'confidence': str  # 'HIGH' | 'MEDIUM' | 'LOW'
        }
    """
    
    improvement = validation_metrics['improvement_mae_pct']
    mae_function = validation_metrics['mae_function']
    mae_baseline = validation_metrics['mae_baseline']
    n_samples = validation_metrics['n_samples']
    
    # Vérifier échantillon suffisant
    if n_samples < 3:
        return {
            'decision': 'INSUFFICIENT_DATA',
            'improvement_pct': improvement,
            'metrics_summary': validation_metrics,
            'recommendation': 'REJETER - Pas assez de données',
            'next_steps': [
                'Augmenter période analyse (plus de clusters)',
                'Vérifier filtres données (importance, pays)',
                'Essayer autre famille événements'
            ],
            'confidence': 'NONE'
        }
    
    # Décision selon amélioration
    if improvement >= threshold_excellent:
        decision = "EXCELLENT"
        confidence = "HIGH"
        recommendation = "INTÉGRER IMMÉDIATEMENT - Fonction universelle validée"
        next_steps = [
            "Intégrer dans Planificateur V2.5 (formulas_validated.py)",
            "Validation croisée sur autre famille (CPI → NFP, NFP → Fed, etc.)",
            "Documentation production (README + exemples)",
            "Tests sur dates référence (11 septembre CPI, etc.)"
        ]
        
    elif improvement >= threshold_good:
        decision = "GOOD"
        confidence = "HIGH"
        recommendation = "INTÉGRER - Amélioration significative confirmée"
        next_steps = [
            "Intégrer dans Planificateur V2.5",
            "Validation croisée recommandée (confirmer universalité)",
            "Monitoring performance production (MAE réel vs prédit)",
            "Documentation complète"
        ]
        
    elif improvement >= threshold_moderate:
        decision = "MODERATE"
        confidence = "MEDIUM"
        recommendation = "TESTER PLUS - Amélioration modérée, validation supplémentaire requise"
        next_steps = [
            "Validation croisée OBLIGATOIRE sur autre famille",
            "Augmenter échantillon calibration (>30 clusters si possible)",
            "Tester window variable (120, 240, 480 min)",
            "Si amélioration <30% sur validation croisée → Fonction spécifique nécessaire"
        ]
        
    else:
        decision = "FAILED"
        confidence = "LOW"
        recommendation = "REJETER - Pas d'amélioration significative vs baseline"
        next_steps = [
            "Analyser pourquoi R² ne corrèle pas avec impact (scatter plot)",
            "Tester autres features (volatilité, spread, liquidité)",
            "Envisager fonction spécifique par famille événements",
            "Utiliser amplification fixe baseline (amp=2.5) en attendant"
        ]
    
    # Résumé métriques
    metrics_summary = {
        'n_samples': n_samples,
        'mae_function': mae_function,
        'mae_baseline': mae_baseline,
        'improvement_mae_pct': improvement,
        'rmse_function': validation_metrics.get('rmse_function', 0),
        'rmse_baseline': validation_metrics.get('rmse_baseline', 0),
        'improvement_rmse_pct': validation_metrics.get('improvement_rmse_pct', 0)
    }
    
    return {
        'decision': decision,
        'improvement_pct': improvement,
        'metrics_summary': metrics_summary,
        'recommendation': recommendation,
        'next_steps': next_steps,
        'confidence': confidence
    }


def cross_validate_to_other_family(
    amplification_function,
    source_event_type: str,
    target_event_type: str,
    conn,
    df_scores,
    lookback_days: int = 30,
    window: int = 240
) -> Dict:
    """
    Validation croisée : Fonction calibrée sur source_type testée sur target_type
    
    Args:
        amplification_function: Fonction amp(R²) calibrée sur source
        source_event_type: Type événement calibration (ex: "CPI")
        target_event_type: Type événement test (ex: "NFP")
        conn: Connexion DuckDB
        df_scores: DataFrame scores empiriques
        lookback_days: Historique prix (default: 30)
        window: Window détection inversions (default: 240)
    
    Returns:
        {
            'source_type': str,
            'target_type': str,
            'n_events': int,
            'mae_function': float,
            'mae_baseline': float,
            'improvement_pct': float,
            'decision': str,  # 'EXCELLENT' | 'GOOD' | 'FAILED'
            'generalization_validated': bool
        }
    """
    
    # Cette fonction nécessite import complet pipeline
    # Pour Session 126, on se concentre sur decide_integration()
    # cross_validate sera implémenté dans script master si nécessaire
    
    print("⚠️  cross_validate_to_other_family() non implémenté dans ce module")
    print("   Utiliser script master pour validation croisée complète")
    
    return {
        'source_type': source_event_type,
        'target_type': target_event_type,
        'n_events': 0,
        'mae_function': 0,
        'mae_baseline': 0,
        'improvement_pct': 0,
        'decision': 'NOT_IMPLEMENTED',
        'generalization_validated': False
    }


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTS UNITAIRES - DECIDE_INTEGRATION")
    print("=" * 80)
    print()
    
    # Test 1 : EXCELLENT (amélioration 88%)
    print("[TEST 1] Amélioration EXCELLENT (88%)")
    print("-" * 80)
    
    metrics_excellent = {
        'n_samples': 17,
        'mae_function': 19.5,
        'mae_baseline': 166.8,
        'rmse_function': 25.5,
        'rmse_baseline': 168.6,
        'improvement_mae_pct': 88.3,
        'improvement_rmse_pct': 84.9
    }
    
    result = decide_integration(metrics_excellent)
    
    print(f"✅ Décision : {result['decision']}")
    print(f"   Confiance : {result['confidence']}")
    print(f"   Amélioration : {result['improvement_pct']:.1f}%")
    print(f"   Recommandation : {result['recommendation']}")
    print()
    print("   Next steps :")
    for step in result['next_steps']:
        print(f"     • {step}")
    print()
    
    # Test 2 : GOOD (amélioration 45%)
    print("[TEST 2] Amélioration GOOD (45%)")
    print("-" * 80)
    
    metrics_good = {
        'n_samples': 12,
        'mae_function': 32.5,
        'mae_baseline': 59.0,
        'rmse_function': 42.0,
        'rmse_baseline': 68.5,
        'improvement_mae_pct': 44.9,
        'improvement_rmse_pct': 38.7
    }
    
    result = decide_integration(metrics_good)
    
    print(f"✅ Décision : {result['decision']}")
    print(f"   Confiance : {result['confidence']}")
    print(f"   Amélioration : {result['improvement_pct']:.1f}%")
    print()
    
    # Test 3 : MODERATE (amélioration 15%)
    print("[TEST 3] Amélioration MODERATE (15%)")
    print("-" * 80)
    
    metrics_moderate = {
        'n_samples': 8,
        'mae_function': 51.0,
        'mae_baseline': 60.0,
        'rmse_function': 65.0,
        'rmse_baseline': 72.0,
        'improvement_mae_pct': 15.0,
        'improvement_rmse_pct': 9.7
    }
    
    result = decide_integration(metrics_moderate)
    
    print(f"⚠️  Décision : {result['decision']}")
    print(f"   Confiance : {result['confidence']}")
    print(f"   Amélioration : {result['improvement_pct']:.1f}%")
    print()
    
    # Test 4 : FAILED (amélioration 2%)
    print("[TEST 4] Amélioration FAILED (2%)")
    print("-" * 80)
    
    metrics_failed = {
        'n_samples': 10,
        'mae_function': 58.8,
        'mae_baseline': 60.0,
        'rmse_function': 70.0,
        'rmse_baseline': 71.0,
        'improvement_mae_pct': 2.0,
        'improvement_rmse_pct': 1.4
    }
    
    result = decide_integration(metrics_failed)
    
    print(f"❌ Décision : {result['decision']}")
    print(f"   Confiance : {result['confidence']}")
    print(f"   Amélioration : {result['improvement_pct']:.1f}%")
    print()
    
    # Test 5 : INSUFFICIENT_DATA
    print("[TEST 5] Données insuffisantes (n=2)")
    print("-" * 80)
    
    metrics_insufficient = {
        'n_samples': 2,
        'mae_function': 25.0,
        'mae_baseline': 50.0,
        'improvement_mae_pct': 50.0
    }
    
    result = decide_integration(metrics_insufficient)
    
    print(f"⚠️  Décision : {result['decision']}")
    print(f"   Confiance : {result['confidence']}")
    print()
    
    print("=" * 80)
    print("TESTS TERMINÉS")
    print("=" * 80)
