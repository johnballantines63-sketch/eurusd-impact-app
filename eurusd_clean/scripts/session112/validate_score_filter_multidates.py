#!/usr/bin/env python3
"""
VALIDATION MULTI-DATES - FILTRE SCORE > 40
===========================================

Test rigoureux sur 10+ dates pour prouver que le filtre score > 40
donne systématiquement de meilleurs résultats que sans filtre.

HYPOTHÈSE À VALIDER:
Le filtre score > 40 (HIGH impact uniquement) améliore la précision
en excluant les événements MEDIUM qui diluent le signal.

MÉTHODOLOGIE:
1. Sélectionner 10+ dates CPI avec impacts MT5 connus
2. Pour chaque date:
   a. Calculer impact AVEC filtre score > 40
   b. Calculer impact SANS filtre (score IS NOT NULL)
   c. Comparer aux impacts MT5 réels
3. Calculer statistiques (MAE, RMSE, précision)
4. Déterminer quelle méthode est supérieure

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Chemins
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent.parent
src_path = project_root / 'fx_impact_app' / 'src'
db_path = project_root / 'eurusd_clean' / 'app' / 'data' / 'warehouse.duckdb'

sys.path.insert(0, str(src_path))

from event_loader import load_high_impact_events
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)
import duckdb

print("="*80)
print("🧪 VALIDATION MULTI-DATES - FILTRE SCORE > 40")
print("="*80)

# ══════════════════════════════════════════════════════════════════════
# DATES DE TEST AVEC IMPACTS MT5 CONNUS (Session 106)
# ══════════════════════════════════════════════════════════════════════

TEST_DATES = [
    {'date': datetime(2025, 9, 11), 'impact_mt5': 56.2, 'description': 'CPI US Sep (référence)'},
    {'date': datetime(2025, 8, 12), 'impact_mt5': 62.6, 'description': 'CPI US Aug'},
    {'date': datetime(2025, 7, 15), 'impact_mt5': 24.7, 'description': 'CPI US Jul'},
    {'date': datetime(2025, 6, 11), 'impact_mt5': 53.9, 'description': 'CPI US Jun'},
    {'date': datetime(2025, 5, 13), 'impact_mt5': 34.8, 'description': 'CPI US May'},
    {'date': datetime(2025, 4, 10), 'impact_mt5': 40.2, 'description': 'CPI US Apr'},
    {'date': datetime(2025, 2, 12), 'impact_mt5': 5.0, 'description': 'CPI US Feb'},
    {'date': datetime(2025, 1, 15), 'impact_mt5': 49.9, 'description': 'CPI US Jan'},
    {'date': datetime(2024, 12, 11), 'impact_mt5': 21.6, 'description': 'CPI US Dec'},
    {'date': datetime(2024, 11, 13), 'impact_mt5': 26.4, 'description': 'CPI US Nov'},
]

print(f"\n📋 {len(TEST_DATES)} dates de test sélectionnées")
print(f"   Range impacts MT5: [{min(d['impact_mt5'] for d in TEST_DATES):.1f}, {max(d['impact_mt5'] for d in TEST_DATES):.1f}] pips")

# ══════════════════════════════════════════════════════════════════════
# FONCTION DE CALCUL IMPACT (AVEC OU SANS FILTRE)
# ══════════════════════════════════════════════════════════════════════

def calculate_impact_for_date(
    db_path: Path,
    target_date: datetime,
    min_score: float = None,
    amplification: float = 2.5
) -> dict:
    """
    Calcule impact pour une date avec ou sans filtre score.
    
    Args:
        db_path: Chemin DB
        target_date: Date cible
        min_score: Score minimum (None = pas de filtre, 40 = HIGH uniquement)
        amplification: Facteur amplification
    
    Returns:
        dict avec résultats
    """
    con = duckdb.connect(str(db_path), read_only=True)
    
    try:
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Query avec ou sans filtre
        if min_score is None:
            # SANS FILTRE (charge tout)
            query = """
            SELECT 
                e.event_key,
                e.event_title as label,
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
            ORDER BY e.ts_utc
            """
            params = [date_str]
        else:
            # AVEC FILTRE score > min_score
            query = """
            SELECT 
                e.event_key,
                e.event_title as label,
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
                AND ef.empirical_score > ?
            ORDER BY e.ts_utc
            """
            params = [date_str, min_score]
        
        df = con.execute(query, params).df()
        
        if df.empty:
            return None
        
        # Calculer impact
        base_score = df['empirical_score'].mean()
        
        # Surprise max
        surprises = []
        for _, event in df.iterrows():
            if pd.notna(event['actual']) and pd.notna(event['estimate']) and abs(event['estimate']) > 0.01:
                surp = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
                surprises.append(min(surp, 500.0))
        
        max_surprise = max(surprises) if surprises else 0.0
        
        # Score ajusté
        adjusted_score = calculate_adjusted_empirical_score(base_score, max_surprise)
        
        # Impact
        impact = calculate_impact_d(
            empirical_score=adjusted_score,
            num_events=len(df),
            amplification=amplification
        )
        
        return {
            'num_events': len(df),
            'base_score': base_score,
            'max_surprise': max_surprise,
            'adjusted_score': adjusted_score,
            'impact_pips': impact
        }
        
    finally:
        con.close()

# ══════════════════════════════════════════════════════════════════════
# TEST SUR TOUTES LES DATES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 1 : CALCUL IMPACTS AVEC ET SANS FILTRE")
print("="*80)

results = []

for test_case in TEST_DATES:
    date = test_case['date']
    impact_mt5 = test_case['impact_mt5']
    desc = test_case['description']
    
    print(f"\n📅 {date.strftime('%Y-%m-%d')} - {desc}")
    
    # SANS FILTRE
    result_no_filter = calculate_impact_for_date(db_path, date, min_score=None)
    
    # AVEC FILTRE score > 40
    result_with_filter = calculate_impact_for_date(db_path, date, min_score=40.0)
    
    if result_no_filter and result_with_filter:
        error_no_filter = abs(result_no_filter['impact_pips'] - impact_mt5)
        error_with_filter = abs(result_with_filter['impact_pips'] - impact_mt5)
        
        print(f"   SANS filtre: {result_no_filter['num_events']} events, {result_no_filter['impact_pips']:.1f} pips (MAE {error_no_filter:.1f})")
        print(f"   AVEC filtre: {result_with_filter['num_events']} events, {result_with_filter['impact_pips']:.1f} pips (MAE {error_with_filter:.1f})")
        
        improvement = ((error_no_filter - error_with_filter) / error_no_filter * 100) if error_no_filter > 0 else 0
        
        if error_with_filter < error_no_filter:
            print(f"   ✅ AMÉLIORATION: {improvement:.1f}%")
        else:
            print(f"   ⚠️ DÉGRADATION: {-improvement:.1f}%")
        
        results.append({
            'date': date,
            'description': desc,
            'impact_mt5': impact_mt5,
            'no_filter_events': result_no_filter['num_events'],
            'no_filter_impact': result_no_filter['impact_pips'],
            'no_filter_error': error_no_filter,
            'with_filter_events': result_with_filter['num_events'],
            'with_filter_impact': result_with_filter['impact_pips'],
            'with_filter_error': error_with_filter,
            'improvement_pct': improvement
        })
    else:
        print(f"   ⚠️ Données insuffisantes")

# ══════════════════════════════════════════════════════════════════════
# STATISTIQUES GLOBALES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 2 : STATISTIQUES GLOBALES")
print("="*80)

if results:
    df_results = pd.DataFrame(results)
    
    # MAE (Mean Absolute Error)
    mae_no_filter = df_results['no_filter_error'].mean()
    mae_with_filter = df_results['with_filter_error'].mean()
    
    # RMSE (Root Mean Square Error)
    rmse_no_filter = np.sqrt((df_results['no_filter_error']**2).mean())
    rmse_with_filter = np.sqrt((df_results['with_filter_error']**2).mean())
    
    # Taux de réussite (< 5 pips)
    success_no_filter = (df_results['no_filter_error'] < 5.0).sum() / len(df_results) * 100
    success_with_filter = (df_results['with_filter_error'] < 5.0).sum() / len(df_results) * 100
    
    # Amélioration globale
    improvement_global = ((mae_no_filter - mae_with_filter) / mae_no_filter * 100) if mae_no_filter > 0 else 0
    
    print(f"\n📈 SANS FILTRE (tous événements score IS NOT NULL):")
    print(f"   MAE:  {mae_no_filter:.2f} pips")
    print(f"   RMSE: {rmse_no_filter:.2f} pips")
    print(f"   Succès (< 5 pips): {success_no_filter:.1f}%")
    
    print(f"\n📉 AVEC FILTRE (score > 40 uniquement):")
    print(f"   MAE:  {mae_with_filter:.2f} pips")
    print(f"   RMSE: {rmse_with_filter:.2f} pips")
    print(f"   Succès (< 5 pips): {success_with_filter:.1f}%")
    
    print(f"\n💡 AMÉLIORATION GLOBALE:")
    print(f"   MAE: {improvement_global:+.1f}%")
    print(f"   RMSE: {((rmse_no_filter - rmse_with_filter) / rmse_no_filter * 100):+.1f}%")
    print(f"   Taux succès: {(success_with_filter - success_no_filter):+.1f}%")
    
    # ══════════════════════════════════════════════════════════════════════
    # CONCLUSION
    # ══════════════════════════════════════════════════════════════════════
    
    print("\n" + "="*80)
    print("📊 CONCLUSION")
    print("="*80)
    
    if mae_with_filter < mae_no_filter:
        print(f"\n✅✅✅ HYPOTHÈSE VALIDÉE !")
        print(f"   Le filtre score > 40 AMÉLIORE la précision de {improvement_global:.1f}%")
        print(f"   MAE passe de {mae_no_filter:.2f} à {mae_with_filter:.2f} pips")
        print(f"\n📋 RECOMMANDATION:")
        print(f"   ✅ Utiliser SYSTÉMATIQUEMENT le filtre score > 40")
        print(f"   ✅ Exclure événements MEDIUM impact (Jobless Claims, etc.)")
        print(f"   ✅ Intégrer dans cluster_impact_calculator.py")
    else:
        print(f"\n❌ HYPOTHÈSE REJETÉE")
        print(f"   Le filtre score > 40 DÉGRADE la précision de {-improvement_global:.1f}%")
        print(f"   Nécessite investigation supplémentaire")
    
    # Sauvegarder résultats
    output_file = script_dir / "validation_score_filter_results.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n💾 Résultats sauvegardés: {output_file}")

else:
    print("\n❌ Aucun résultat à analyser")

print("\n" + "="*80)
print("FIN DE LA VALIDATION")
print("="*80)
