#!/usr/bin/env python3
"""
GRID SEARCH DIRECTION_FACTOR - Trouver calibration optimale

Teste différentes combinaisons de facteurs pour minimiser MAE
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import numpy as np

# Chemins
script_dir = Path(__file__).parent
eurusd_clean_dir = script_dir.parents[1]
sys.path.insert(0, str(script_dir))

# Import formulas_validated depuis fx_impact_app
fx_impact_app_src = eurusd_clean_dir.parent / "fx_impact_app" / "src"
sys.path.insert(0, str(fx_impact_app_src))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

# ════════════════════════════════════════════════════════════════
# DONNÉES RÉFÉRENCE
# ════════════════════════════════════════════════════════════════

DB_PATH = eurusd_clean_dir / "app" / "data" / "warehouse.duckdb"

TARGET_DATES = {
    '2025-09-11': {'impact': 51.7, 'surprise_net': +33.6},
    '2025-01-15': {'impact': 49.9, 'surprise_net': +27.5},
    '2025-05-13': {'impact': 34.0, 'surprise_net': -108.5},
    '2025-07-15': {'impact': 24.6, 'surprise_net': -70.0}
}

# ════════════════════════════════════════════════════════════════
# FONCTIONS
# ════════════════════════════════════════════════════════════════

def calculate_surprise_net(events_data: list) -> float:
    """Calcule surprise nette"""
    surprise_net = 0.0
    for event in events_data:
        actual = event.get('actual')
        estimate = event.get('estimate')
        if actual is not None and estimate is not None and estimate != 0:
            surprise_signed = ((actual - estimate) / abs(estimate)) * 100
            surprise_net += surprise_signed
    return surprise_net


def calculate_direction_factor_v2(surprise_net: float, 
                                   factor_positive: float,
                                   factor_negative: float,
                                   threshold: float = 30) -> float:
    """
    Version paramétrable du direction_factor
    
    Args:
        surprise_net: Surprise nette
        factor_positive: Facteur max pour surprise positive (ex: 1.2)
        factor_negative: Facteur min pour surprise négative (ex: 0.7)
        threshold: Seuil ±X% pour facteurs extrêmes
    """
    if surprise_net > threshold:
        return factor_positive
    elif surprise_net > 0:
        # Interpolation linéaire 1.0 → factor_positive
        return 1.0 + ((surprise_net / threshold) * (factor_positive - 1.0))
    elif surprise_net >= -threshold:
        # Interpolation linéaire 1.0 → factor_negative
        return 1.0 + ((surprise_net / threshold) * (1.0 - factor_negative))
    else:
        return factor_negative


def load_events(date_str: str, conn) -> pd.DataFrame:
    """Charge événements pour une date"""
    query = """
    SELECT 
        e.actual,
        e.estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    """
    return conn.execute(query, [date_str]).df()


def test_configuration(factor_pos: float, factor_neg: float, threshold: float, conn) -> dict:
    """
    Teste une configuration de direction_factor
    
    Returns:
        dict avec MAE et détails par date
    """
    errors_without = []
    errors_with = []
    details = []
    
    for date_str, info in TARGET_DATES.items():
        # Charger événements
        events_df = load_events(date_str, conn)
        
        if events_df.empty:
            continue
        
        # Préparer events_data
        events_data = []
        for _, event in events_df.iterrows():
            actual = event['actual']
            estimate = event['estimate']
            
            if pd.isna(actual):
                actual = None
            if pd.isna(estimate):
                estimate = None
            
            events_data.append({'actual': actual, 'estimate': estimate})
        
        # Surprise nette
        surprise_net = calculate_surprise_net(events_data)
        
        # Baseline (SANS direction)
        max_surprise = 33.3
        base_score = events_df['empirical_score'].mean()
        adjusted_score_base = calculate_adjusted_empirical_score(base_score, max_surprise)
        impact_without = calculate_impact_d(adjusted_score_base, len(events_df), 2.5)
        
        # AVEC direction
        direction_factor = calculate_direction_factor_v2(
            surprise_net, factor_pos, factor_neg, threshold
        )
        adjusted_score_with = adjusted_score_base * direction_factor
        impact_with = calculate_impact_d(adjusted_score_with, len(events_df), 2.5)
        
        # Erreurs
        impact_real = info['impact']
        error_without = abs(impact_without - impact_real)
        error_with = abs(impact_with - impact_real)
        
        errors_without.append(error_without)
        errors_with.append(error_with)
        
        details.append({
            'date': date_str,
            'surprise_net': surprise_net,
            'direction_factor': direction_factor,
            'impact_real': impact_real,
            'impact_without': impact_without,
            'impact_with': impact_with,
            'error_without': error_without,
            'error_with': error_with,
            'improvement': error_without - error_with
        })
    
    mae_without = np.mean(errors_without)
    mae_with = np.mean(errors_with)
    mae_improvement = mae_without - mae_with
    mae_improvement_pct = (mae_improvement / mae_without * 100) if mae_without > 0 else 0
    
    return {
        'factor_pos': factor_pos,
        'factor_neg': factor_neg,
        'threshold': threshold,
        'mae_without': mae_without,
        'mae_with': mae_with,
        'mae_improvement': mae_improvement,
        'mae_improvement_pct': mae_improvement_pct,
        'details': details,
        'dates_improved': sum(1 for d in details if d['improvement'] > 0),
        'dates_regressed': sum(1 for d in details if d['improvement'] < 0)
    }


def main():
    """Point d'entrée - Grid Search"""
    
    print("="*80)
    print("GRID SEARCH DIRECTION_FACTOR - RE-CALIBRATION")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Configurations à tester
        configs = []
        
        # Test 1 : Variantes facteur positif (réduire de 1.2 vers 1.0)
        for factor_pos in [1.0, 1.05, 1.10, 1.15, 1.20]:
            for factor_neg in [0.70, 0.75, 0.80, 0.85]:
                configs.append((factor_pos, factor_neg, 30))
        
        # Test 2 : Variantes threshold
        for threshold in [20, 25, 30, 35, 40]:
            configs.append((1.10, 0.75, threshold))
        
        print(f"🔍 Test de {len(configs)} configurations...")
        print()
        
        results = []
        
        for factor_pos, factor_neg, threshold in configs:
            result = test_configuration(factor_pos, factor_neg, threshold, conn)
            results.append(result)
        
        # Trier par amélioration MAE
        results_sorted = sorted(results, key=lambda x: x['mae_improvement'], reverse=True)
        
        print("="*80)
        print("🏆 TOP 10 MEILLEURES CONFIGURATIONS")
        print("="*80)
        print()
        print(f"{'Factor+':<10} {'Factor-':<10} {'Thresh':<8} {'MAE Sans':<10} {'MAE Avec':<10} {'Amélioration':<15} {'OK/KO'}")
        print("─"*80)
        
        for i, r in enumerate(results_sorted[:10], 1):
            print(f"{r['factor_pos']:<10.2f} {r['factor_neg']:<10.2f} {r['threshold']:<8.0f} "
                  f"{r['mae_without']:<10.1f} {r['mae_with']:<10.1f} "
                  f"{r['mae_improvement']:+6.1f} ({r['mae_improvement_pct']:+5.1f}%) "
                  f"{r['dates_improved']}/{r['dates_regressed']}")
        
        # Meilleure configuration
        best = results_sorted[0]
        
        print("\n" + "="*80)
        print("✅ MEILLEURE CONFIGURATION")
        print("="*80)
        print()
        print(f"Factor positif  : {best['factor_pos']:.2f}")
        print(f"Factor négatif  : {best['factor_neg']:.2f}")
        print(f"Threshold       : ±{best['threshold']:.0f}%")
        print()
        print(f"MAE SANS        : {best['mae_without']:.1f} pips")
        print(f"MAE AVEC        : {best['mae_with']:.1f} pips")
        print(f"Amélioration    : {best['mae_improvement']:+.1f} pips ({best['mae_improvement_pct']:+.1f}%)")
        print(f"Dates améliorées: {best['dates_improved']}/4")
        print(f"Dates régressées: {best['dates_regressed']}/4")
        
        # Détails par date
        print("\n" + "─"*80)
        print("DÉTAILS PAR DATE")
        print("─"*80)
        print()
        print(f"{'Date':<12} {'Surp Net':<10} {'Factor':<8} {'Réel':<8} {'Avec':<8} {'Erreur':<10} {'Amélio'}")
        print("─"*80)
        
        for d in best['details']:
            status = "✅" if d['improvement'] > 0 else "❌"
            print(f"{d['date']:<12} {d['surprise_net']:>+8.1f}% {d['direction_factor']:<8.3f} "
                  f"{d['impact_real']:<8.1f} {d['impact_with']:<8.1f} "
                  f"{d['error_with']:<10.1f} {d['improvement']:+7.1f} {status}")
        
        # Validation critères
        print("\n" + "="*80)
        print("VALIDATION CRITÈRES SESSION 92.7")
        print("="*80)
        print()
        
        criteria_met = []
        
        # Critère 1 : MAE avec < MAE sans
        c1 = best['mae_with'] < best['mae_without']
        criteria_met.append(c1)
        print(f"1. MAE avec < MAE sans : {c1} {'✅' if c1 else '❌'}")
        
        # Critère 2 : Amélioration > 30%
        c2 = best['mae_improvement_pct'] > 30
        criteria_met.append(c2)
        print(f"2. Amélioration > 30%  : {best['mae_improvement_pct']:.1f}% {'✅' if c2 else '❌'}")
        
        # Critère 3 : Toutes dates améliorées
        c3 = best['dates_improved'] == 4 and best['dates_regressed'] == 0
        criteria_met.append(c3)
        print(f"3. Toutes dates OK     : {best['dates_improved']}/4 {'✅' if c3 else '❌'}")
        
        # Critère 4 : Pas de régression sur dates OK
        dates_ok = ['2025-09-11', '2025-01-15']
        regressed_ok = [d for d in best['details'] if d['date'] in dates_ok and d['improvement'] < 0]
        c4 = len(regressed_ok) == 0
        criteria_met.append(c4)
        print(f"4. Pas régression OK   : {c4} {'✅' if c4 else '❌'}")
        
        print()
        if all(criteria_met):
            print("🎉 TOUS LES CRITÈRES VALIDÉS !")
            print("   → Prêt pour test sur 40 dates")
        else:
            print("⚠️  Certains critères non atteints")
            print("   → Calibration additionnelle nécessaire ou approche alternative")
        
    finally:
        conn.close()
    
    print("\n" + "="*80)
    print("GRID SEARCH TERMINÉ")
    print("="*80)


if __name__ == "__main__":
    main()
