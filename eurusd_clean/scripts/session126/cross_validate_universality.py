#!/usr/bin/env python3
"""
SESSION 126 - VALIDATION CROISÉE UNIVERSALITÉ
==============================================
Test CRITIQUE : Fonction calibrée sur famille A → testée sur famille B

Si amélioration significative (>30%) → Fonction universelle confirmée
Sinon → Fonctions spécifiques nécessaires par famille
"""
import sys
import json
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

# Import modules
from utils_mapping import get_empirical_score
from validate_predictions import validate_predictions_with_baseline
from decide_integration import decide_integration

print("=" * 80)
print("VALIDATION CROISÉE - TEST UNIVERSALITÉ FONCTION AMPLIFICATION")
print("=" * 80)
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
CALIBRATION_DIR = Path(__file__).parent / "calibration_results"

# ============================================================================
# CHARGER FONCTION CALIBRÉE
# ============================================================================

def load_calibrated_function(json_path: Path):
    """Charge fonction calibrée depuis JSON"""
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    model_type = data['calibration']['best_model']
    params = data['calibration']['parameters']
    formula = data['calibration']['formula']
    
    print(f"📊 Fonction source : {data['event_type']}")
    print(f"   Modèle : {model_type.upper()}")
    print(f"   Formule : {formula}")
    print()
    
    # Reconstruire fonction
    if model_type == 'linear':
        a, b = params
        def amp_function(r2):
            r2 = max(0.0, min(1.0, r2))
            return max(0.01, min(0.20, a + b * r2))
    
    elif model_type == 'quadratic':
        a, b, c = params
        def amp_function(r2):
            r2 = max(0.0, min(1.0, r2))
            return max(0.01, min(0.20, a + b * r2 + c * r2**2))
    
    else:  # logarithmic
        a, b = params
        def amp_function(r2):
            r2 = max(0.0, min(1.0, r2))
            return max(0.01, min(0.20, a + b * np.log(r2 + 0.01)))
    
    return amp_function, data['event_type']

# ============================================================================
# CHARGER ÉVÉNEMENTS TARGET
# ============================================================================

def load_target_events_data(target_event_type: str):
    """
    Charge données événements target (avec impacts + R² déjà calculés)
    
    Pour Session 126, on utilise les résultats Session 125 :
    - CPI : cross_validate_nfp_final.py résultats
    - NFP : idem
    
    Pour simplifier, on recharge depuis DB
    """
    from datetime import timedelta
    from calibrate_universal_amplification import (
        find_events_by_type,
        measure_real_impact,
        calculate_r2_for_event
    )
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    print(f"📊 Chargement événements target : {target_event_type}")
    print()
    
    # Chercher événements
    df_events = find_events_by_type(target_event_type, conn)
    
    print(f"   Calcul impacts + R² pour {len(df_events)} événements...")
    print()
    
    events_with_data = []
    
    for idx, row in df_events.iterrows():
        event_time = pd.to_datetime(row['ts_utc'])
        
        print(f"   [{idx+1}/{len(df_events)}] {event_time.strftime('%Y-%m-%d')}...", end=' ')
        
        # Mesurer impact
        impact = measure_real_impact(event_time, conn)
        if impact is None or impact < 5:
            print("⏭️  skip")
            continue
        
        # Calculer R²
        r2_info = calculate_r2_for_event(event_time, conn)
        if r2_info is None:
            print("⏭️  skip (no R²)")
            continue
        
        events_with_data.append({
            'event_time': event_time,
            'event_key': row['event_key'],
            'country': row['country'],
            'impact_measured': impact,
            'r2_trend': r2_info['r2'],
            'duration_hours': r2_info['duration_hours'],
            'amplitude_pips': r2_info['amplitude_pips']
        })
        
        print(f"✅ {impact:.1f}p | R²={r2_info['r2']:.3f}")
    
    print()
    print(f"   ✅ {len(events_with_data)} événements exploitables")
    print()
    
    conn.close()
    
    return events_with_data

# ============================================================================
# VALIDATION CROISÉE
# ============================================================================

def cross_validate(source_json: Path, target_event_type: str):
    """
    Validation croisée complète
    
    Args:
        source_json: JSON fonction calibrée source
        target_event_type: Type événement pour test
    
    Returns:
        Dict résultats validation croisée
    """
    
    print("=" * 80)
    print(f"VALIDATION CROISÉE")
    print("=" * 80)
    print()
    
    # Charger fonction source
    amp_function, source_type = load_calibrated_function(source_json)
    
    print(f"🔄 Test : Fonction {source_type.upper()} → Événements {target_event_type.upper()}")
    print()
    print("-" * 80)
    print()
    
    # Charger événements target
    target_events = load_target_events_data(target_event_type)
    
    if len(target_events) < 3:
        print(f"❌ Pas assez d'événements target (n={len(target_events)} < 3)")
        return None
    
    # Charger scores
    df_scores = pd.read_csv(SCORES_PATH)
    
    # Convertir format pour validation
    clusters_format = [{
        'cluster_time': e['event_time'],
        'events': [{'event_key': e['event_key'], 'country': e['country']}],
        'impact_measured': e['impact_measured'],
        'r2_trend': e['r2_trend'],
        'duration_hours': e['duration_hours'],
        'amplitude_pips': e['amplitude_pips']
    } for e in target_events]
    
    # VALIDATION
    print("[VALIDATION] Prédictions avec fonction source...")
    print()
    
    validation_result = validate_predictions_with_baseline(
        amp_function,
        clusters_format,
        df_scores,
        baseline_amp=2.5
    )
    
    metrics = validation_result['metrics']
    
    print(f"✅ Validation complétée")
    print(f"   Événements testés : {metrics['n_samples']}")
    print(f"   MAE fonction      : {metrics['mae_function']:.2f} pips")
    print(f"   MAE baseline      : {metrics['mae_baseline']:.2f} pips")
    print(f"   RMSE fonction     : {metrics['rmse_function']:.2f} pips")
    print(f"   RMSE baseline     : {metrics['rmse_baseline']:.2f} pips")
    print(f"   Amélioration MAE  : {metrics['improvement_mae_pct']:+.1f}%")
    print(f"   Amélioration RMSE : {metrics['improvement_rmse_pct']:+.1f}%")
    print()
    
    # DÉCISION
    print("[DÉCISION] Universalité fonction...")
    print()
    
    decision_result = decide_integration(
        metrics,
        threshold_excellent=50.0,
        threshold_good=30.0,
        threshold_moderate=10.0
    )
    
    print(f"{'='*80}")
    print(f"RÉSULTAT : {decision_result['decision']}")
    print(f"{'='*80}")
    print()
    print(f"Confiance    : {decision_result['confidence']}")
    print(f"Amélioration : {decision_result['improvement_pct']:+.1f}%")
    print()
    print(f"Interprétation :")
    if decision_result['decision'] in ['EXCELLENT', 'GOOD']:
        print(f"  ✅ UNIVERSALITÉ CONFIRMÉE")
        print(f"     Fonction {source_type} généralise bien à {target_event_type}")
        print(f"     → Fonction UNIVERSELLE validée !")
    else:
        print(f"  ❌ UNIVERSALITÉ NON CONFIRMÉE")
        print(f"     Fonction {source_type} ne généralise pas à {target_event_type}")
        print(f"     → Fonctions SPÉCIFIQUES nécessaires par famille")
    print()
    
    return {
        'source_type': source_type,
        'target_type': target_event_type,
        'metrics': metrics,
        'decision': decision_result,
        'universality_confirmed': decision_result['decision'] in ['EXCELLENT', 'GOOD']
    }

# ============================================================================
# TESTS MULTIPLES
# ============================================================================

def run_all_cross_validations():
    """
    Lance TOUTES validations croisées possibles
    
    Tests :
    1. Fed → CPI
    2. Fed → NFP
    3. (Si temps) CPI → NFP, NFP → CPI, etc.
    """
    
    print("=" * 80)
    print("BATTERIE COMPLÈTE VALIDATIONS CROISÉES")
    print("=" * 80)
    print()
    
    # Fichiers calibration disponibles
    fed_json = CALIBRATION_DIR / "fed_interest_rate_decision_calibration.json"
    
    results = []
    
    # Test 1 : Fed → CPI
    if fed_json.exists():
        print("\n")
        print("▶️  TEST 1/2 : Fonction FED → Événements CPI")
        print("=" * 80)
        print()
        
        result = cross_validate(fed_json, "cpi")
        if result:
            results.append(result)
        
        input("\nAppuyer sur ENTRÉE pour continuer vers Test 2/2...")
    
    # Test 2 : Fed → NFP
    if fed_json.exists():
        print("\n")
        print("▶️  TEST 2/2 : Fonction FED → Événements NFP")
        print("=" * 80)
        print()
        
        result = cross_validate(fed_json, "non farm payrolls")
        if result:
            results.append(result)
    
    # SYNTHÈSE FINALE
    print("\n")
    print("=" * 80)
    print("SYNTHÈSE FINALE - UNIVERSALITÉ FONCTION")
    print("=" * 80)
    print()
    
    if not results:
        print("❌ Aucun test validé")
        return
    
    print(f"Tests effectués : {len(results)}")
    print()
    
    for i, res in enumerate(results, 1):
        status = "✅" if res['universality_confirmed'] else "❌"
        print(f"  {status} Test {i} : {res['source_type']} → {res['target_type']}")
        print(f"     Amélioration : {res['metrics']['improvement_mae_pct']:+.1f}%")
        print(f"     Décision : {res['decision']['decision']}")
        print()
    
    # Verdict global
    all_confirmed = all(r['universality_confirmed'] for r in results)
    
    print("-" * 80)
    print()
    if all_confirmed:
        print("🎉 VERDICT : FONCTION UNIVERSELLE VALIDÉE")
        print()
        print("   ✅ Tous les tests croisés confirment l'universalité")
        print("   ✅ Fonction amp(R²) généralise bien entre familles événements")
        print("   ✅ INTÉGRATION RECOMMANDÉE dans Planificateur V2.5")
        print()
        print("   Next step : Documentation complète pipeline")
    else:
        print("⚠️  VERDICT : UNIVERSALITÉ PARTIELLE")
        print()
        print("   ⚠️  Certains tests croisés échouent")
        print("   ⚠️  Fonction peut nécessiter ajustements par famille")
        print()
        print("   Next step : Analyser échecs + fonctions spécifiques si nécessaire")
    print()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validation croisée universalité")
    
    parser.add_argument(
        '--source',
        type=str,
        help='JSON fonction source (ex: fed_interest_rate_decision_calibration.json)'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        help='Type événement target (ex: "cpi", "non farm payrolls")'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Lancer tous tests croisés disponibles'
    )
    
    args = parser.parse_args()
    
    if args.all:
        run_all_cross_validations()
    elif args.source and args.target:
        source_path = CALIBRATION_DIR / args.source
        if not source_path.exists():
            print(f"❌ Fichier source introuvable : {source_path}")
            sys.exit(1)
        
        result = cross_validate(source_path, args.target)
        
        if result and result['universality_confirmed']:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
