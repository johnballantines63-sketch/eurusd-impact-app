"""
Test DoubleWaveDetectorRev10 avec paramètres ajustés
Session 119 - Optimisation rev10

OBJECTIF:
Trouver paramètres optimaux pour détecter Wave2 complète (56.2 pips 11 sept)
"""

import duckdb
from pathlib import Path
import pandas as pd
import sys
from datetime import datetime

# Import rev10
sys.path.append(str(Path(__file__).parent))
from double_wave_detector_rev10 import detect_double_wave_on_df, load_ohlc_1m_duckdb


def test_with_params(db_path: str, date_str: str, case_name: str,
                    minutes_after_hint: int = 90,
                    max_idle_bars: int = 20,
                    baseline_mode: str = 'prev_close_14_29'):
    """
    Test rev10 avec paramètres personnalisés
    """
    print("="*80)
    print(f"🧪 TEST REV10 - {case_name}")
    print(f"   Paramètres: horizon={minutes_after_hint}min, idle={max_idle_bars}")
    print("="*80)
    
    date = datetime.fromisoformat(date_str)
    ts = pd.Timestamp(date, tz='Europe/Zurich')
    
    # Charger données OHLC
    start_dt = ts.replace(hour=13, minute=0, second=0)
    end_dt = ts.replace(hour=16, minute=30, second=0)
    
    df = load_ohlc_1m_duckdb(db_path, 'prices_bern', 'Europe/Zurich', start_dt, end_dt)
    
    if df.empty:
        print("❌ Aucune donnée")
        return None
    
    # Patcher temporairement les constantes dans le module
    import double_wave_detector_rev10 as dw_module
    original_idle = dw_module.MAX_IDLE_BARS
    original_scan = dw_module.SCAN_MINUTES_AFTER_HINT
    
    try:
        # Appliquer nouveaux paramètres
        dw_module.MAX_IDLE_BARS = max_idle_bars
        dw_module.SCAN_MINUTES_AFTER_HINT = minutes_after_hint
        
        result = detect_double_wave_on_df(
            df,
            date_label=date_str,
            symbol="EURUSD",
            tz='Europe/Zurich',
            baseline_mode=baseline_mode,
            minutes_after_hint=minutes_after_hint
        )
    finally:
        # Restaurer valeurs originales
        dw_module.MAX_IDLE_BARS = original_idle
        dw_module.SCAN_MINUTES_AFTER_HINT = original_scan
    
    if result is None:
        print(f"\n❌ Aucun pattern détecté")
        return None
    
    # Afficher résultats
    print(f"\n✅ DOUBLE WAVE DÉTECTÉE")
    print(f"\n📊 MÉTRIQUES:")
    print(f"   Confidence:    {result['confidence']:.1f}%")
    print(f"   Direction:     {result['direction']}")
    
    print(f"\n📊 STRUCTURE:")
    print(f"   Baseline:      {result['baseline_time']}")
    print(f"   Peak 1:        {result['peak1_time']}")
    print(f"   Peak 2 (Wave2): {result['peak2_time']}")
    
    print(f"\n📊 AMPLITUDES:")
    print(f"   Wave 1:        {result['wave1_amp_pips']:.1f} pips")
    print(f"   Wave 2:        {result['wave2_amp_pips']:.1f} pips")
    print(f"   Extension:     {result['wave2_amp_pips']/result['wave1_amp_pips']:.2f}x")
    
    print(f"\n📊 PULLBACKS:")
    print(f"   Pullback 1:    {result['pullback1_ratio']:.1%}")
    if result['pullback1_ratio'] > 1.0:
        print(f"   ⚠️ WARNING: Pullback > 100% (bug calcul)")
    
    return result


def grid_search_11_sept(db_path: str):
    """
    Grid search paramètres pour optimiser détection 11 septembre
    Objectif: Wave2 proche de 56.2 pips
    """
    print("="*80)
    print("🔍 GRID SEARCH PARAMÈTRES - 11 SEPTEMBRE 2025")
    print("   Objectif: Wave2 ≈ 56.2 pips (référence Session 118)")
    print("="*80)
    
    # Grille paramètres
    horizons = [90, 120, 150]
    idle_bars = [20, 30, 40]
    
    best_result = None
    best_mae = float('inf')
    best_params = None
    
    target_wave2 = 56.2
    
    results = []
    
    for horizon in horizons:
        for idle in idle_bars:
            result = test_with_params(
                db_path,
                '2025-09-11',
                f'11 sept (horizon={horizon}, idle={idle})',
                minutes_after_hint=horizon,
                max_idle_bars=idle
            )
            
            if result:
                wave2 = result['wave2_amp_pips']
                mae = abs(wave2 - target_wave2)
                
                results.append({
                    'horizon': horizon,
                    'idle': idle,
                    'wave2': wave2,
                    'mae': mae,
                    'peak2_time': result['peak2_time']
                })
                
                if mae < best_mae:
                    best_mae = mae
                    best_result = result
                    best_params = (horizon, idle)
            
            print()  # Ligne vide
    
    # Résumé
    print("="*80)
    print("📊 RÉSULTATS GRID SEARCH")
    print("="*80)
    
    if results:
        # Tableau résultats
        print(f"\n{'Horizon':<10} {'Idle':<10} {'Wave2':<10} {'MAE':<10} {'Peak2 Time'}")
        print("-" * 70)
        for r in sorted(results, key=lambda x: x['mae']):
            print(f"{r['horizon']:<10} {r['idle']:<10} {r['wave2']:<10.1f} {r['mae']:<10.1f} {r['peak2_time']}")
        
        print(f"\n🎯 MEILLEURS PARAMÈTRES:")
        print(f"   Horizon:     {best_params[0]} minutes")
        print(f"   Idle bars:   {best_params[1]}")
        print(f"   Wave2:       {best_result['wave2_amp_pips']:.1f} pips")
        print(f"   MAE:         {best_mae:.1f} pips")
        print(f"   Peak2 time:  {best_result['peak2_time']}")
        
        if best_mae < 5:
            print(f"\n✅✅✅ EXCELLENT - MAE < 5 pips")
        elif best_mae < 10:
            print(f"\n✅ BON - MAE < 10 pips")
        else:
            print(f"\n⚠️ MAE élevé - Ajustements supplémentaires nécessaires")
    else:
        print("\n❌ Aucune détection valide")


def main():
    """Test ajustement paramètres rev10"""
    
    # Connexion DB
    project_root = Path(__file__).parent.parent.parent
    warehouse_path = project_root / 'data' / 'warehouse.duckdb'
    db_path = str(warehouse_path)
    
    # Grid search sur 11 septembre
    grid_search_11_sept(db_path)


if __name__ == '__main__':
    main()
