"""
GRID SEARCH AMPLIFICATION PAR TYPE - SESSION 92.6
=================================================

OBJECTIF:
Trouver l'amplification optimale PAR TYPE d'événement (CPI, NFP, FOMC, ISM)
en répliquant EXACTEMENT la méthodologie du Planificateur V2.4

CONTEXTE SESSION 92.6:
- Session 92.5 a validé : Amplification CPI optimale = 2.27 (MAE 0.1 pip sur 11 sept 2025)
- Données Dukascopy = MT5 confirmées (écart 1-3 pips normal)
- Grid Search Session 92.2 amp 2.2 était correcte (très proche 2.27)

AMPLIFICATIONS ATTENDUES:
- CPI  : ~2.27 (validé Session 92.5)
- NFP  : ~1.8-2.0 (Session 92.1)
- FOMC : ~0.8-1.0 (Session 92.1, 3 dates seulement)
- ISM  : ~0.3-0.5 (Session 92.1, problématique)

MÉTHODOLOGIE CORRECTE (Planificateur V2.4):
1. Query SQL (lignes 189-210) : Charger événements score > 40
2. Calcul surprise (lignes 230-242) : Surprise max depuis actual/estimate
3. Ajustement score : calculate_adjusted_empirical_score(base_score, surprise)
4. Calcul impact : calculate_impact_d(adjusted_score, num_events, amplification)
5. Validation : Comparer impact prédit vs réel (MAE)

GRID SEARCH:
- Amplifications testées : 0.5 à 3.0 (pas 0.1) = 26 valeurs
- Par type : CPI, NFP, FOMC, ISM, etc.
- Métrique : MAE (Mean Absolute Error)
- Objectif : Amplification minimisant MAE par type

Date : 28 octobre 2025 - Session 92.6
Auteur : André Valentin avec Claude
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime
from typing import Dict, List, Tuple

# Ajouter chemin vers formules validées
script_dir = Path(__file__).parent  # session92.6/
scripts_dir = script_dir.parent      # scripts/
eurusd_clean_dir = scripts_dir.parent  # eurusd_clean/
project_root = eurusd_clean_dir.parent  # eurusd_news_impact_calculator_MPC/
fx_impact_app_src = project_root / "fx_impact_app" / "src"

if not fx_impact_app_src.exists():
    print(f"❌ ERREUR: Répertoire src non trouvé: {fx_impact_app_src}")
    sys.exit(1)

sys.path.insert(0, str(fx_impact_app_src))

from formulas_validated import (
    calculate_adjusted_empirical_score,  # Session 55
    calculate_impact_d                    # Session 51
)


# ════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════

DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"
CSV_PATH = eurusd_clean_dir / "scripts" / "session90" / "validation_results_planificateur_40dates.csv"

# Range amplifications à tester
AMPLIFICATIONS = [round(x * 0.1, 1) for x in range(5, 31)]  # 0.5 à 3.0, pas 0.1


# ════════════════════════════════════════════════════════════════
# FONCTION RÉPLICATION PLANIFICATEUR
# ════════════════════════════════════════════════════════════════

def replicate_planificateur_prediction(
    date_str: str,
    amplification: float,
    conn: duckdb.DuckDBPyConnection
) -> float:
    """
    RÉPLIQUE EXACTE du Planificateur V2.4 (lignes 189-277)
    
    Cette fonction reproduit TOUTE la chaîne de calcul du Planificateur :
    1. Query SQL identique
    2. Calcul surprise
    3. Ajustement score
    4. Calcul impact avec amplification variable
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        amplification: Facteur d'amplification à tester
        conn: Connexion DuckDB
    
    Returns:
        float: Impact prédit en pips (ou None si pas d'événements)
    """
    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 1 : QUERY SQL IDENTIQUE PLANIFICATEUR (lignes 189-210)
    # ─────────────────────────────────────────────────────────────
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
    
    events_df = conn.execute(query, [date_str]).df()
    
    if events_df.empty:
        return None
    
    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 2 : CALCUL SURPRISE (lignes 230-242)
    # ─────────────────────────────────────────────────────────────
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
    
    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 3 : AJUSTEMENT SCORE (ligne 244 Planificateur)
    # ─────────────────────────────────────────────────────────────
    base_score_avg = events_df['empirical_score'].mean()
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 4 : CALCUL IMPACT (ligne 246-277)
    # ─────────────────────────────────────────────────────────────
    num_events = len(events_df)
    
    # ← Variable à optimiser (grid search)
    impact_predicted = calculate_impact_d(
        adjusted_score, 
        num_events, 
        amplification  # ← PARAMÈTRE TESTÉ
    )
    
    return impact_predicted


# ════════════════════════════════════════════════════════════════
# FONCTION GRID SEARCH PAR TYPE
# ════════════════════════════════════════════════════════════════

def grid_search_by_type(
    csv_path: Path,
    db_path: Path,
    amplifications: List[float]
) -> Dict[str, Dict]:
    """
    Grid search amplification optimale PAR TYPE
    
    Pour chaque type (CPI, NFP, FOMC, etc.):
    1. Charger dates de ce type depuis CSV
    2. Pour chaque amplification testée:
        a. Pour chaque date:
            - Recalculer impact avec cette amplification
            - Comparer vs impact réel
        b. Calculer MAE global
    3. Trouver amplification minimisant MAE
    
    Args:
        csv_path: Chemin vers CSV validation Session 90
        db_path: Chemin vers warehouse.duckdb
        amplifications: Liste amplifications à tester
    
    Returns:
        Dict[type] -> {'amplification': float, 'mae': float, 'n_dates': int}
    """
    # Charger CSV validation
    df_validation = pd.read_csv(csv_path)
    
    # Connexion DB
    conn = duckdb.connect(str(db_path), read_only=True)
    
    results = {}
    
    # Pour chaque type unique
    for event_type in sorted(df_validation['type'].unique()):
        print(f"\n{'='*60}")
        print(f"TYPE : {event_type}")
        print(f"{'='*60}")
        
        # Subset dates de ce type
        subset = df_validation[df_validation['type'] == event_type].copy()
        n_dates = len(subset)
        
        print(f"Nombre de dates : {n_dates}")
        
        best_amp = None
        best_mae = float('inf')
        
        # Tester chaque amplification
        for amp in amplifications:
            errors = []
            
            # Pour chaque date
            for idx, row in subset.iterrows():
                date_str = row['date']
                impact_real = row['impact_real']
                
                # RECALCULER impact avec cette amplification
                impact_predicted_new = replicate_planificateur_prediction(
                    date_str,
                    amp,
                    conn
                )
                
                # Si pas d'événements trouvés, skip
                if impact_predicted_new is None:
                    continue
                
                # Calculer erreur
                error = abs(impact_predicted_new - impact_real)
                errors.append(error)
            
            # Calculer MAE pour cette amplification
            if errors:
                mae = sum(errors) / len(errors)
                
                # Si meilleur MAE, sauvegarder
                if mae < best_mae:
                    best_mae = mae
                    best_amp = amp
                
                # Afficher progression
                if amp in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:  # Afficher jalons
                    print(f"  Amp {amp:4.1f} → MAE {mae:5.1f} pips")
        
        # Sauvegarder résultat optimal pour ce type
        results[event_type] = {
            'amplification': best_amp,
            'mae': best_mae,
            'n_dates': n_dates
        }
        
        print(f"\n✅ OPTIMAL : Amp {best_amp:.1f} → MAE {best_mae:.1f} pips")
    
    conn.close()
    return results


# ════════════════════════════════════════════════════════════════
# FONCTION AFFICHAGE RÉSULTATS
# ════════════════════════════════════════════════════════════════

def display_results(results: Dict[str, Dict]):
    """
    Affiche les résultats du grid search
    """
    print("\n" + "="*80)
    print("📊 RÉSULTATS GRID SEARCH - AMPLIFICATIONS OPTIMALES PAR TYPE")
    print("="*80)
    
    print(f"\n{'Type':<15} {'Amp Optimal':<12} {'MAE (pips)':<12} {'N Dates':<10}")
    print("-"*80)
    
    for event_type, data in sorted(results.items()):
        amp = data['amplification']
        mae = data['mae']
        n = data['n_dates']
        
        # Marquer CPI si proche de 2.27 (validation Session 92.5)
        marker = ""
        if event_type == 'CPI' and 2.2 <= amp <= 2.3:
            marker = " ✅ (Session 92.5 validé)"
        
        print(f"{event_type:<15} {amp:<12.1f} {mae:<12.1f} {n:<10}{marker}")
    
    print("-"*80)
    
    # Validation CPI
    cpi_amp = results.get('CPI', {}).get('amplification')
    if cpi_amp:
        if 2.2 <= cpi_amp <= 2.3:
            print("\n✅ CPI: Amplification cohérente avec Session 92.5 (2.27 validé)")
        else:
            print(f"\n⚠️  CPI: Amplification {cpi_amp:.1f} diverge de Session 92.5 (2.27)")
            print("    → Investigation recommandée")
    
    # Comparaison Baseline
    print("\n📌 BASELINE V2.4 (amp fixe 2.5):")
    print("  MAE global : 43.7 pips")
    print("  CPI  : MAE 13.7 pips")
    print("  NFP  : MAE 36.9 pips")
    print("  FOMC : MAE 24.1 pips")
    print("  ISM  : MAE 93.2 pips")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    """
    Fonction principale
    """
    print("="*80)
    print("🔬 GRID SEARCH AMPLIFICATION PAR TYPE - SESSION 92.6")
    print("="*80)
    print(f"\nDate : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"CSV  : {CSV_PATH.name}")
    print(f"DB   : {DB_PATH.name}")
    print(f"Amplifications testées : {len(AMPLIFICATIONS)} valeurs ({AMPLIFICATIONS[0]} à {AMPLIFICATIONS[-1]})")
    
    print("\n📌 VALIDATION SESSION 92.5:")
    print("  CPI : Amplification 2.27 validée (MAE 0.1 pip sur 11 sept 2025)")
    print("  → Grid Search devrait trouver ~2.2-2.3 pour CPI")
    
    # Vérifier fichiers existent
    if not CSV_PATH.exists():
        print(f"\n❌ ERREUR : CSV non trouvé")
        print(f"   Chemin : {CSV_PATH}")
        return
    
    if not DB_PATH.exists():
        print(f"\n❌ ERREUR : DB non trouvée")
        print(f"   Chemin : {DB_PATH}")
        return
    
    print("\n✅ Fichiers trouvés")
    
    # Lancer grid search
    print("\n🚀 Lancement grid search...")
    print("⚠️  Cela peut prendre plusieurs minutes...")
    
    results = grid_search_by_type(CSV_PATH, DB_PATH, AMPLIFICATIONS)
    
    # Afficher résultats
    display_results(results)
    
    # Sauvegarder résultats
    output_path = Path(__file__).parent / "grid_search_results_session92.6.csv"
    
    df_results = pd.DataFrame([
        {
            'type': event_type,
            'amplification_optimal': data['amplification'],
            'mae_pips': data['mae'],
            'n_dates': data['n_dates']
        }
        for event_type, data in results.items()
    ])
    
    df_results.to_csv(output_path, index=False)
    print(f"\n💾 Résultats sauvegardés : {output_path.name}")
    
    print("\n" + "="*80)
    print("✅ GRID SEARCH TERMINÉ")
    print("="*80)
    print("\n📋 PROCHAINES ÉTAPES:")
    print("  1. Valider CPI ~2.27 confirmé")
    print("  2. Tester amplifications trouvées sur 11 sept + autres dates")
    print("  3. Si MAE global < 20 pips → Implémenter dans Planificateur V2.5")


if __name__ == "__main__":
    main()
