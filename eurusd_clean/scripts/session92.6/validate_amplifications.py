"""
VALIDATION AMPLIFICATIONS GRID SEARCH - SESSION 92.6
====================================================

OBJECTIF:
Valider les amplifications trouvées par le Grid Search Session 92.6
sur le cas référence (11 septembre 2025) et autres dates.

RÉSULTATS GRID SEARCH À VALIDER:
- CPI  : 2.2 (MAE 10.8 pips sur 10 dates)
- NFP  : 1.4 (MAE 27.8 pips sur 10 dates)
- FOMC : 1.0 (MAE 2.8 pips sur 3 dates)
- ISM  : 0.5 (MAE 7.4 pips sur 9 dates)

VALIDATIONS OBLIGATOIRES:
1. Test 11 septembre avec CPI amp 2.2 → MAE doit être < 1 pip ✅
2. Test 11 septembre avec baseline 2.5 → Comparaison
3. Test sur autres dates CPI, NFP, FOMC, ISM
4. Calcul MAE global projeté vs Baseline V2.4

Date : 28 octobre 2025 - Session 92.6
Auteur : André Valentin avec Claude
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from typing import Dict, List

# Ajouter chemin vers formules validées
script_dir = Path(__file__).parent  # session92.6/
scripts_dir = script_dir.parent      # scripts/
eurusd_clean_dir = scripts_dir.parent  # eurusd_clean/
project_root = eurusd_clean_dir.parent  # eurusd_news_impact_calculator_MPC/
fx_impact_app_src = project_root / "fx_impact_app" / "src"

sys.path.insert(0, str(fx_impact_app_src))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

# ════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════

DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"
CSV_PATH = eurusd_clean_dir / "scripts" / "session90" / "validation_results_planificateur_40dates.csv"

# Amplifications trouvées par Grid Search
AMPLIFICATIONS_OPTIMALES = {
    'CPI': 2.2,
    'NFP': 1.4,
    'FOMC': 1.0,
    'ISM': 0.5,
    'Employment': 0.6,
    'PMI': 0.6
}

# Baseline actuelle
BASELINE_AMP = 2.5

# ════════════════════════════════════════════════════════════════
# FONCTIONS
# ════════════════════════════════════════════════════════════════

def get_events_for_date(date_str: str, conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Charge événements pour une date donnée"""
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        e.actual,
        e.estimate,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    return conn.execute(query, [date_str]).df()


def calculate_prediction(events_df: pd.DataFrame, amplification: float) -> float:
    """Calcule prédiction impact pour une date avec amplification donnée"""
    if events_df.empty:
        return None
    
    # Calcul surprise
    surprises = []
    for _, event in events_df.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
        else:
            surprise_pct = 0
        
        surprises.append(surprise_pct)
    
    max_surprise = max(surprises) if surprises else 0
    
    # Ajustement score
    base_score_avg = events_df['empirical_score'].mean()
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # Calcul impact
    num_events = len(events_df)
    impact_predicted = calculate_impact_d(adjusted_score, num_events, amplification)
    
    return impact_predicted


def validate_september_11():
    """VALIDATION CRITIQUE : 11 septembre 2025"""
    print("=" * 70)
    print("VALIDATION 11 SEPTEMBRE 2025 (Cas Référence)")
    print("=" * 70)
    
    date_str = "2025-09-11"
    real_impact = 51.0  # Impact réel validé Session 92.5
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Charger événements
        events_df = get_events_for_date(date_str, conn)
        
        if events_df.empty:
            print("❌ ERREUR: Pas d'événements trouvés pour le 11 septembre 2025!")
            return
        
        print(f"\n📅 Date : {date_str}")
        print(f"📊 Événements trouvés : {len(events_df)}")
        print(f"📌 Impact réel validé : {real_impact:.1f} pips")
        print(f"📋 Type dominant : CPI")
        
        # Tester avec amplification CPI optimale (2.2)
        print("\n" + "─" * 70)
        print("TEST 1 : Amplification CPI Optimale (2.2)")
        print("─" * 70)
        
        impact_cpi_optimal = calculate_prediction(events_df, AMPLIFICATIONS_OPTIMALES['CPI'])
        error_cpi = abs(impact_cpi_optimal - real_impact)
        precision_cpi = (1 - error_cpi / real_impact) * 100
        
        print(f"Amplification    : {AMPLIFICATIONS_OPTIMALES['CPI']}")
        print(f"Impact prédit    : {impact_cpi_optimal:.1f} pips")
        print(f"Impact réel      : {real_impact:.1f} pips")
        print(f"Erreur absolue   : {error_cpi:.1f} pips")
        print(f"Précision        : {precision_cpi:.1f}%")
        
        if error_cpi < 1.0:
            print("✅ SUCCÈS: Erreur < 1 pip (critère Session 92.6 respecté)")
        else:
            print(f"⚠️  ATTENTION: Erreur {error_cpi:.1f} pips > 1 pip attendu")
        
        # Tester avec baseline (2.5)
        print("\n" + "─" * 70)
        print("TEST 2 : Baseline V2.4 (2.5)")
        print("─" * 70)
        
        impact_baseline = calculate_prediction(events_df, BASELINE_AMP)
        error_baseline = abs(impact_baseline - real_impact)
        precision_baseline = (1 - error_baseline / real_impact) * 100
        
        print(f"Amplification    : {BASELINE_AMP}")
        print(f"Impact prédit    : {impact_baseline:.1f} pips")
        print(f"Impact réel      : {real_impact:.1f} pips")
        print(f"Erreur absolue   : {error_baseline:.1f} pips")
        print(f"Précision        : {precision_baseline:.1f}%")
        
        # Comparaison
        print("\n" + "─" * 70)
        print("COMPARAISON CPI 2.2 vs Baseline 2.5")
        print("─" * 70)
        
        improvement = error_baseline - error_cpi
        improvement_pct = (improvement / error_baseline) * 100
        
        print(f"Amélioration erreur : {improvement:.1f} pips ({improvement_pct:.1f}%)")
        
        if improvement > 0:
            print(f"✅ Amplification 2.2 MEILLEURE que baseline 2.5")
        else:
            print(f"❌ Amplification 2.2 MOINS BONNE que baseline 2.5")
        
    finally:
        conn.close()


def validate_by_type():
    """Validation par type sur toutes les dates disponibles"""
    print("\n\n" + "=" * 70)
    print("VALIDATION PAR TYPE (40 dates)")
    print("=" * 70)
    
    # Charger CSV validation
    df_validation = pd.read_csv(CSV_PATH)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Grouper par type
        types = df_validation['type'].unique()
        
        results_by_type = {}
        
        for event_type in types:
            if event_type not in AMPLIFICATIONS_OPTIMALES:
                continue
            
            print(f"\n{'─' * 70}")
            print(f"TYPE : {event_type}")
            print(f"{'─' * 70}")
            
            # Filtrer dates de ce type
            dates_type = df_validation[df_validation['type'] == event_type]
            n_dates = len(dates_type)
            
            print(f"Nombre de dates : {n_dates}")
            print(f"Amplification optimale Grid Search : {AMPLIFICATIONS_OPTIMALES[event_type]}")
            
            # Calculer MAE avec amplification optimale
            errors_optimal = []
            errors_baseline = []
            
            for _, row in dates_type.iterrows():
                date_str = row['date']
                real_impact = row['impact_reel_pips']
                
                # Charger événements
                events_df = get_events_for_date(date_str, conn)
                
                if events_df.empty:
                    continue
                
                # Prédiction avec amp optimale
                pred_optimal = calculate_prediction(events_df, AMPLIFICATIONS_OPTIMALES[event_type])
                if pred_optimal is not None:
                    error_optimal = abs(pred_optimal - real_impact)
                    errors_optimal.append(error_optimal)
                
                # Prédiction avec baseline
                pred_baseline = calculate_prediction(events_df, BASELINE_AMP)
                if pred_baseline is not None:
                    error_baseline = abs(pred_baseline - real_impact)
                    errors_baseline.append(error_baseline)
            
            # Statistiques
            mae_optimal = sum(errors_optimal) / len(errors_optimal) if errors_optimal else 0
            mae_baseline = sum(errors_baseline) / len(errors_baseline) if errors_baseline else 0
            
            improvement = mae_baseline - mae_optimal
            improvement_pct = (improvement / mae_baseline * 100) if mae_baseline > 0 else 0
            
            print(f"\nMAE Amplification Optimale : {mae_optimal:.1f} pips")
            print(f"MAE Baseline V2.4          : {mae_baseline:.1f} pips")
            print(f"Amélioration               : {improvement:.1f} pips ({improvement_pct:.1f}%)")
            
            if improvement > 0:
                print("✅ Amplification optimale MEILLEURE")
            elif improvement == 0:
                print("➖ Amplification optimale ÉGALE")
            else:
                print("❌ Amplification optimale MOINS BONNE")
            
            results_by_type[event_type] = {
                'n_dates': n_dates,
                'amplification': AMPLIFICATIONS_OPTIMALES[event_type],
                'mae_optimal': mae_optimal,
                'mae_baseline': mae_baseline,
                'improvement_pips': improvement,
                'improvement_pct': improvement_pct
            }
        
        # Résumé global
        print("\n\n" + "=" * 70)
        print("RÉSUMÉ GLOBAL PAR TYPE")
        print("=" * 70)
        
        print(f"\n{'Type':<12} {'Amp':<6} {'MAE Opt':<10} {'MAE Base':<10} {'Amélioration':<15}")
        print("─" * 70)
        
        total_improvement = 0
        total_dates = 0
        
        for event_type, results in results_by_type.items():
            print(f"{event_type:<12} {results['amplification']:<6.1f} "
                  f"{results['mae_optimal']:<10.1f} {results['mae_baseline']:<10.1f} "
                  f"{results['improvement_pips']:>6.1f} pips ({results['improvement_pct']:>5.1f}%)")
            
            total_improvement += results['improvement_pips'] * results['n_dates']
            total_dates += results['n_dates']
        
        avg_improvement = total_improvement / total_dates if total_dates > 0 else 0
        
        print("─" * 70)
        print(f"Amélioration moyenne pondérée : {avg_improvement:.1f} pips")
        
    finally:
        conn.close()


def main():
    """Point d'entrée principal"""
    print("\n" + "=" * 70)
    print("VALIDATION AMPLIFICATIONS GRID SEARCH SESSION 92.6")
    print("=" * 70)
    print()
    print("📋 Amplifications à valider :")
    for event_type, amp in AMPLIFICATIONS_OPTIMALES.items():
        print(f"   {event_type:<15} : {amp}")
    
    # Validation 11 septembre (CRITIQUE)
    validate_september_11()
    
    # Validation par type
    validate_by_type()
    
    print("\n" + "=" * 70)
    print("VALIDATION TERMINÉE")
    print("=" * 70)


if __name__ == "__main__":
    main()
