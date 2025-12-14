#!/usr/bin/env python3
"""
GRID SEARCH CALIBRATION - SESSION 77
====================================

Calibre les coefficients de la formule D (Sessions 51-55) sur 27 mouvements.

STRUCTURE VALIDÉE SESSIONS 51-55 (À RESPECTER) :
1. Score ajusté par surprise (Session 55)
2. Impact D avec params à calibrer (Session 51)
3. Somme vectorielle + direction (FAMILY_SENTIMENT)
4. Amplification surprise (zones 1-3, Sessions 14-15)
5. Correction 0.758 (Session 11)

OPTIMISATION : 4 paramètres uniquement
- intercept_multi, coef_multi (multi-événements, nb_events ≥ 2)
- intercept_single, coef_single (événement isolé, nb_events = 1)

VALIDATION : Leave-One-Out Cross-Validation (27 iterations)

Date : 25 octobre 2025
Session : 77
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"


# ════════════════════════════════════════════════════════════════
# FAMILY_SENTIMENT (Direction événements)
# ════════════════════════════════════════════════════════════════

FAMILY_SENTIMENT = {
    # US ECONOMIC DATA
    'NFP': -1,
    'Unemployment_Rate': 1,
    'Average_Hourly_Earnings': -1,
    'CPI': 1,
    'Core_CPI': 1,
    'PPI': 1,
    'Core_PPI': 1,
    'Retail_Sales': -1,
    'GDP': -1,
    'ISM_Manufacturing_PMI': -1,
    'ISM_Services_PMI': -1,
    'Consumer_Confidence': -1,
    'Durable_Goods_Orders': -1,
    'Trade_Balance': -1,
    'Industrial_Production': -1,
    'Housing_Starts': -1,
    'Building_Permits': -1,
    'Existing_Home_Sales': -1,
    'New_Home_Sales': -1,
    'Jobless_Claims': 1,
    'Continuing_Claims': 1,
    'Core_PCE_Price_Index': 1,
    'ECB_Interest_Rate_Decision': 1,
    'ECB_Press_Conference': 1,
    'EU_CPI': -1,
    'EU_Core_CPI': -1,
    'EU_GDP': -1,
    'EU_Unemployment_Rate': 1,
    'German_IFO_Business_Climate': -1,
    'German_ZEW_Economic_Sentiment': -1,
    'German_GDP': -1,
    'German_CPI': -1,
    'BOE_Interest_Rate_Decision': 0,
    'UK_CPI': 0,
    'UK_GDP': 0,
    'UK_Unemployment_Rate': 0,
    'Michigan_Consumer_Sentiment': -1,
    'CB_Consumer_Confidence': -1,
    'ADP_Employment_Change': -1,
    'Philadelphia_Fed_Manufacturing_Index': -1,
    'Chicago_PMI': -1,
    'Factory_Orders': -1,
    'Wholesale_Inventories': -1,
}


# ════════════════════════════════════════════════════════════════
# FONCTIONS FORMULES SESSIONS 51-55
# ════════════════════════════════════════════════════════════════

def calculate_adjusted_empirical_score(
    base_score: float,
    surprise_pct: float
) -> float:
    """Ajuste score empirique selon surprise (Session 55)"""
    if surprise_pct < 5:
        factor = 1.0
    elif surprise_pct < 15:
        factor = 1.0 + (surprise_pct - 5) / 10 * 0.5
    elif surprise_pct < 30:
        factor = 1.5 + (surprise_pct - 15) / 15 * 0.4
    else:
        factor = 1.9
    return base_score * factor


def calculate_amplification_factor(
    score_ajuste: float,
    surprise_pct: float
) -> float:
    """Calcule facteur amplification surprise (Sessions 14-15)"""
    if score_ajuste < 40:
        return 1.0
    surprise_capped = min(surprise_pct, 30.0)
    if surprise_capped < 5:
        return 1.0
    elif surprise_capped < 15:
        return 1.0 + (surprise_capped - 5) / 10 * 1.5
    else:
        return 2.5


def calculate_impact_with_params(
    events_cluster: List[Dict],
    intercept_multi: float,
    coef_multi: float,
    intercept_single: float,
    coef_single: float
) -> float:
    """Calcule impact avec paramètres donnés (structure Sessions 51-55)"""
    if not events_cluster:
        return 0.0
    
    nb_events = len(events_cluster)
    surprise_max = max(e.get('surprise_pct', 0) for e in events_cluster)
    
    # Impacts individuels
    impacts_signes = []
    for event in events_cluster:
        score_base = event.get('empirical_score', 0)
        surprise_pct = event.get('surprise_pct', 0)
        score_ajuste = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        if nb_events >= 2:
            impact_brut = intercept_multi + coef_multi * score_ajuste
        else:
            impact_brut = intercept_single + coef_single * score_ajuste
        
        famille = event.get('family', 'Unknown')
        direction = FAMILY_SENTIMENT.get(famille, 0)
        impact_signe = impact_brut * direction
        impacts_signes.append(impact_signe)
    
    # Somme vectorielle
    impact_total = sum(impacts_signes)
    
    # Amplification
    scores_ajustes = [
        calculate_adjusted_empirical_score(e.get('empirical_score', 0), e.get('surprise_pct', 0))
        for e in events_cluster
    ]
    score_ajuste_moyen = np.mean(scores_ajustes)
    amplification = calculate_amplification_factor(score_ajuste_moyen, surprise_max)
    impact_amplifie = impact_total * amplification
    
    # Correction 0.758
    impact_final = abs(impact_amplifie) * 0.758
    
    return impact_final


# ════════════════════════════════════════════════════════════════
# RECONSTITUTION CLUSTERS ÉVÉNEMENTS
# ════════════════════════════════════════════════════════════════

def reconstitute_event_cluster(
    movement_row: pd.Series,
    conn: duckdb.DuckDBPyConnection
) -> List[Dict]:
    """Reconstruit cluster événements pour 1 mouvement"""
    date_str = movement_row['date']
    time_str = movement_row['time']
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    start_time = dt - timedelta(minutes=10)
    end_time = dt + timedelta(minutes=10)
    
    query = f"""
    SELECT 
        e.event_key, e.event_title, e.country,
        e.actual, e.previous, e.estimate, e.forecast,
        AVG(ef.empirical_score) as empirical_score,
        MIN(ef.family) as family
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.ts_utc <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
    GROUP BY e.event_key, e.event_title, e.country, e.actual, e.previous, e.estimate, e.forecast, e.ts_utc
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query).fetchdf()
    
    if df_events.empty:
        return []
    
    events = []
    for _, row in df_events.iterrows():
        actual = row.get('actual')
        estimate = row.get('estimate') or row.get('forecast') or row.get('previous')
        
        surprise_pct = 0.0
        if actual is not None and estimate is not None and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
        
        event = {
            'event_key': row.get('event_key', ''),
            'event_title': row.get('event_title', ''),
            'family': row.get('family', 'Unknown'),
            'empirical_score': row.get('empirical_score', 0),
            'surprise_pct': surprise_pct,
            'actual': actual,
            'estimate': estimate
        }
        events.append(event)
    
    return events


# ════════════════════════════════════════════════════════════════
# GRID SEARCH CALIBRATION
# ════════════════════════════════════════════════════════════════

def grid_search_calibration(
    df_movements: pd.DataFrame,
    conn: duckdb.DuckDBPyConnection,
    param_ranges: Dict
) -> Tuple[Dict, float, List]:
    """Grid search exhaustif avec Leave-One-Out CV"""
    print("🔍 GRID SEARCH CALIBRATION")
    print("=" * 60)
    print(f"Dataset : {len(df_movements)} mouvements")
    print(f"Validation : Leave-One-Out CV ({len(df_movements)} iterations)")
    print()
    
    # Générer grille paramètres
    intercept_multi_range = param_ranges['intercept_multi']
    coef_multi_range = param_ranges['coef_multi']
    intercept_single_range = param_ranges['intercept_single']
    coef_single_range = param_ranges['coef_single']
    
    total_combinations = (
        len(intercept_multi_range) * 
        len(coef_multi_range) * 
        len(intercept_single_range) * 
        len(coef_single_range)
    )
    
    print(f"Plages paramètres :")
    print(f"  intercept_multi : {intercept_multi_range[0]:.1f} à {intercept_multi_range[-1]:.1f} (n={len(intercept_multi_range)})")
    print(f"  coef_multi      : {coef_multi_range[0]:.2f} à {coef_multi_range[-1]:.2f} (n={len(coef_multi_range)})")
    print(f"  intercept_single: {intercept_single_range[0]:.1f} à {intercept_single_range[-1]:.1f} (n={len(intercept_single_range)})")
    print(f"  coef_single     : {coef_single_range[0]:.2f} à {coef_single_range[-1]:.2f} (n={len(coef_single_range)})")
    print()
    print(f"Total combinaisons : {total_combinations:,}")
    print(f"Durée estimée : 2-3 minutes")
    print()
    
    # Stocker résultats
    results = []
    best_mae = float('inf')
    best_params = None
    
    # Compteur progression
    combo_count = 0
    start_time = time.time()
    last_print_time = start_time
    
    print("Progression : ", end='', flush=True)
    
    # Grid search
    for intercept_multi in intercept_multi_range:
        for coef_multi in coef_multi_range:
            for intercept_single in intercept_single_range:
                for coef_single in coef_single_range:
                    combo_count += 1
                    
                    # Afficher progression toutes les 1000 combinaisons
                    current_time = time.time()
                    if combo_count % 1000 == 0 or (current_time - last_print_time) > 5:
                        elapsed = current_time - start_time
                        pct = combo_count / total_combinations * 100
                        rate = combo_count / elapsed if elapsed > 0 else 0
                        eta = (total_combinations - combo_count) / rate if rate > 0 else 0
                        print(f"\rProgression : {combo_count:,}/{total_combinations:,} ({pct:.1f}%) - ETA: {eta:.0f}s - Meilleur MAE: {best_mae:.2f} pips", end='', flush=True)
                        last_print_time = current_time
                    
                    # Leave-One-Out CV
                    mae_folds = []
                    
                    for i in range(len(df_movements)):
                        test_row = df_movements.iloc[i]
                        events = reconstitute_event_cluster(test_row, conn)
                        
                        if not events:
                            continue
                        
                        impact_pred = calculate_impact_with_params(
                            events,
                            intercept_multi,
                            coef_multi,
                            intercept_single,
                            coef_single
                        )
                        
                        impact_real = test_row['impact_pips']
                        mae_fold = abs(impact_pred - impact_real)
                        mae_folds.append(mae_fold)
                    
                    # MAE CV
                    if mae_folds:
                        mae_cv = np.mean(mae_folds)
                        std_cv = np.std(mae_folds)
                        
                        results.append({
                            'intercept_multi': intercept_multi,
                            'coef_multi': coef_multi,
                            'intercept_single': intercept_single,
                            'coef_single': coef_single,
                            'mae_cv': mae_cv,
                            'std_cv': std_cv
                        })
                        
                        if mae_cv < best_mae:
                            best_mae = mae_cv
                            best_params = {
                                'intercept_multi': intercept_multi,
                                'coef_multi': coef_multi,
                                'intercept_single': intercept_single,
                                'coef_single': coef_single
                            }
    
    elapsed_total = time.time() - start_time
    print(f"\rProgression : {total_combinations:,}/{total_combinations:,} (100.0%) - Terminé en {elapsed_total:.0f}s")
    print()
    print("✅ Grid Search terminé !")
    print()
    
    # Top 100 combinaisons
    results_sorted = sorted(results, key=lambda x: x['mae_cv'])
    top_results = results_sorted[:100]
    
    return best_params, best_mae, top_results


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 60)
    print("GRID SEARCH CALIBRATION - SESSION 77")
    print("=" * 60)
    print()
    
    # Charger dataset
    INPUT_PATH = SCRIPT_DIR.parent / "session76" / "dataset_session76_ultra.csv"
    
    if not INPUT_PATH.exists():
        print(f"❌ Dataset non trouvé : {INPUT_PATH}")
        return 1
    
    print(f"📂 Dataset : {INPUT_PATH.name}")
    df = pd.read_csv(INPUT_PATH)
    print(f"✅ {len(df)} mouvements chargés")
    
    if len(df) != 27:
        print(f"⚠️  ATTENTION : {len(df)} mouvements au lieu de 27")
    
    print()
    
    # Connexion DB
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée : {DB_PATH}")
        return 1
    
    print(f"💾 Base de données : warehouse.duckdb")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    print(f"✅ Connexion établie")
    print()
    
    # Plages paramètres
    param_ranges = {
        'intercept_multi': np.arange(-20, 1, 1),
        'coef_multi': np.arange(0.30, 0.81, 0.05),
        'intercept_single': np.arange(-15, 1, 1),
        'coef_single': np.arange(0.30, 0.71, 0.05)
    }
    
    # Grid search
    best_params, best_mae, top_results = grid_search_calibration(df, conn, param_ranges)
    conn.close()
    
    # Afficher résultats
    print("🏆 MEILLEURS PARAMÈTRES")
    print("=" * 60)
    print(f"MAE CV : {best_mae:.2f} pips")
    print()
    print(f"intercept_multi  : {best_params['intercept_multi']:.2f}")
    print(f"coef_multi       : {best_params['coef_multi']:.3f}")
    print(f"intercept_single : {best_params['intercept_single']:.2f}")
    print(f"coef_single      : {best_params['coef_single']:.3f}")
    print()
    
    # Vérifier coefficients
    print("🔍 VÉRIFICATION COHÉRENCE COEFFICIENTS")
    print("=" * 60)
    
    issues = []
    if best_params['coef_multi'] < 0:
        issues.append(f"⚠️  RED FLAG : coef_multi négatif ({best_params['coef_multi']:.3f})")
    else:
        print(f"✅ coef_multi positif : {best_params['coef_multi']:.3f}")
    
    if best_params['coef_single'] < 0:
        issues.append(f"⚠️  RED FLAG : coef_single négatif ({best_params['coef_single']:.3f})")
    else:
        print(f"✅ coef_single positif : {best_params['coef_single']:.3f}")
    
    if issues:
        print()
        for issue in issues:
            print(issue)
        print()
        print("⚠️  ATTENTION : Coefficients contre-intuitifs détectés")
    
    print()
    
    # Sauvegarder résultats
    OUTPUT_PATH = SCRIPT_DIR / "calibration_results_session77.txt"
    
    with open(OUTPUT_PATH, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("GRID SEARCH CALIBRATION - SESSION 77\n")
        f.write("=" * 60 + "\n\n")
        f.write("CONFIGURATION\n")
        f.write("-" * 60 + "\n")
        f.write(f"Dataset : dataset_session76_ultra.csv\n")
        f.write(f"Mouvements : {len(df)}\n")
        f.write(f"Validation : Leave-One-Out CV\n\n")
        f.write("MEILLEURS PARAMÈTRES\n")
        f.write("-" * 60 + "\n")
        f.write(f"MAE CV : {best_mae:.2f} pips\n\n")
        f.write(f"intercept_multi  : {best_params['intercept_multi']:.2f}\n")
        f.write(f"coef_multi       : {best_params['coef_multi']:.3f}\n")
        f.write(f"intercept_single : {best_params['intercept_single']:.2f}\n")
        f.write(f"coef_single      : {best_params['coef_single']:.3f}\n\n")
        f.write("COMPARAISON AVEC V1\n")
        f.write("-" * 60 + "\n")
        f.write(f"V1 intercept_multi  : -10.47\n")
        f.write(f"V2 intercept_multi  : {best_params['intercept_multi']:.2f}\n\n")
        f.write(f"V1 coef_multi       : 0.477\n")
        f.write(f"V2 coef_multi       : {best_params['coef_multi']:.3f}\n\n")
    
    print(f"💾 Résultats sauvegardés : {OUTPUT_PATH.name}")
    
    # Sauvegarder top 100
    OUTPUT_CSV = SCRIPT_DIR / "calibration_grid_analysis.csv"
    df_top = pd.DataFrame(top_results)
    df_top.to_csv(OUTPUT_CSV, index=False)
    print(f"💾 Top 100 combinaisons : {OUTPUT_CSV.name}")
    print()
    
    # Critères succès
    print("🎯 CRITÈRES SUCCÈS")
    print("=" * 60)
    if best_mae < 30:
        print(f"✅ MAE CV < 30 pips : {best_mae:.2f} pips (EXCELLENT)")
    elif best_mae < 40:
        print(f"⚠️  MAE CV < 40 pips : {best_mae:.2f} pips (BON)")
    else:
        print(f"❌ MAE CV ≥ 40 pips : {best_mae:.2f} pips (INSUFFISANT)")
    
    print()
    print("=" * 60)
    print("✅ ÉTAPE 1 TERMINÉE")
    print("=" * 60)
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
