"""
Calculer Ratios Moyens Impact/Score par Core Type

Objectif : 
1. Calculer ratio Impact réel / Score core_scores pour chaque date avec core_scores
2. Calculer moyenne par core_type
3. Identifier outliers et causes

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime
import pytz
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def measure_real_impact(date_str: str, anchor_time: pd.Timestamp) -> Optional[float]:
    """Mesurer impact réel depuis prix Finnhub"""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    date_dt = pd.to_datetime(date_str)
    window_start = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=0)))
    window_end = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=20, minute=0)))
    
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
      AND datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
      AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    conn.close()
    
    if df_prices.empty:
        return None
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices = df_prices.set_index('datetime')
    
    # Utiliser anchor_time pour baseline
    if isinstance(anchor_time, str):
        anchor_time = pd.to_datetime(anchor_time)
    
    if not hasattr(anchor_time, 'tz'):
        anchor_time = TZ_BERN.localize(anchor_time)
    
    prices_at_baseline = df_prices[df_prices.index >= anchor_time]
    
    if prices_at_baseline.empty:
        return None
    
    baseline_price = prices_at_baseline.iloc[0]['open']
    max_high = prices_at_baseline['high'].max()
    min_low = prices_at_baseline['low'].min()
    impact_up = (max_high - baseline_price) * 10000
    impact_down = (baseline_price - min_low) * 10000
    impact = max(impact_up, impact_down)
    
    return impact

def calculate_ratios_all_dates():
    """Calculer ratios pour toutes les dates avec core_scores"""
    
    print("="*100)
    print("CALCUL RATIOS MOYENS PAR CORE TYPE")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=False)
    
    # Dates de test connues (on peut étendre cette liste)
    TEST_DATES = [
        '2025-09-11', '2025-05-29', '2025-08-01', '2025-11-20',
        '2025-06-23', '2025-10-10', '2024-09-11', '2024-10-11',
        '2024-11-08', '2024-12-13', '2025-01-10', '2025-02-07',
        '2025-03-12', '2025-04-10'
    ]
    
    print(f"📊 {len(TEST_DATES)} dates à analyser")
    print()
    
    results = []
    
    for date_str in TEST_DATES:
        
        print(f"Analyse {date_str} ({core_type}, {country})...", end=" ")
        
        try:
            # Exécuter pipeline
            result = executor.execute_complete_pipeline(
                date_str,
                window_minutes=30,
                support_threshold=0.8,
                jaccard_threshold=0.6,
                years_lookback=5
            )
            
            if not result or not result.get('success'):
                print("❌ Pipeline échoué")
                continue
            
            # Extraire informations
            results_dict = result.get('results', {})
            etape3_cluster_info = results_dict.get('etape3_cluster_info', {})
            main_cluster = etape3_cluster_info.get('cluster', {})
            anchor_time = main_cluster.get('anchor_time')
            
            if not anchor_time:
                print("❌ Pas d'anchor_time")
                continue
            
            # Récupérer score core_scores (table agrégée par core_type/country)
            query_score = """
            SELECT empirical_score
            FROM core_scores
            WHERE core_type = ? AND country = ?
            """
            
            score_row = conn.execute(query_score, [core_type, country]).fetchone()
            if not score_row:
                print("❌ Pas de score")
                continue
            
            core_score_db = score_row[0]
            
            # Mesurer impact réel
            impact_real = measure_real_impact(date_str, anchor_time)
            
            if impact_real is None:
                print("❌ Pas d'impact")
                continue
            
            # Calculer ratio
            ratio = impact_real / core_score_db if core_score_db > 0 else 0.0
            
            results.append({
                'date': date_str,
                'core_type': core_type,
                'country': country,
                'core_score_db': core_score_db,
                'impact_real': impact_real,
                'ratio': ratio
            })
            
            print(f"✅ Ratio: {ratio:.3f}")
            
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            continue
    
    conn.close()
    
    if not results:
        print("❌ Aucun résultat")
        return
    
    # Créer DataFrame
    df_results = pd.DataFrame(results)
    
    # Calculer statistiques par core_type
    print()
    print("="*100)
    print("STATISTIQUES PAR CORE TYPE")
    print("="*100)
    print()
    
    stats_by_type = []
    
    for core_type in df_results['core_type'].unique():
        df_type = df_results[df_results['core_type'] == core_type]
        
        stats = {
            'core_type': core_type,
            'n_dates': len(df_type),
            'ratio_mean': df_type['ratio'].mean(),
            'ratio_median': df_type['ratio'].median(),
            'ratio_std': df_type['ratio'].std(),
            'ratio_min': df_type['ratio'].min(),
            'ratio_max': df_type['ratio'].max(),
            'impact_mean': df_type['impact_real'].mean(),
            'score_mean': df_type['core_score_db'].mean()
        }
        
        stats_by_type.append(stats)
        
        print(f"{core_type}:")
        print(f"  N dates : {stats['n_dates']}")
        print(f"  Ratio moyen : {stats['ratio_mean']:.3f}")
        print(f"  Ratio médian : {stats['ratio_median']:.3f}")
        print(f"  Ratio std : {stats['ratio_std']:.3f}")
        print(f"  Ratio min : {stats['ratio_min']:.3f}")
        print(f"  Ratio max : {stats['ratio_max']:.3f}")
        print(f"  Impact moyen : {stats['impact_mean']:.2f} pips")
        print(f"  Score moyen : {stats['score_mean']:.2f}")
        print()
    
    # Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'ratios_impact_score_par_core_type.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    
    stats_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'statistiques_ratios_par_core_type.csv'
    df_stats = pd.DataFrame(stats_by_type)
    df_stats.to_csv(stats_file, index=False)
    
    print(f"💾 Résultats sauvegardés :")
    print(f"   - {output_file}")
    print(f"   - {stats_file}")
    print()
    
    # Identifier outliers
    print("="*100)
    print("OUTLIERS (Ratio > 2.0 ou < 0.5)")
    print("="*100)
    print()
    
    outliers_high = df_results[df_results['ratio'] > 2.0]
    outliers_low = df_results[df_results['ratio'] < 0.5]
    
    if not outliers_high.empty:
        print("Ratio > 2.0 (sous-estimation) :")
        print(f"{'Date':<12} {'Core Type':<15} {'Score':<10} {'Impact':<12} {'Ratio':<10}")
        print("-"*70)
        for _, row in outliers_high.iterrows():
            print(f"{row['date']:<12} {row['core_type']:<15} {row['core_score_db']:>9.2f} {row['impact_real']:>11.2f} {row['ratio']:>9.3f}")
        print()
    
    if not outliers_low.empty:
        print("Ratio < 0.5 (sur-estimation) :")
        print(f"{'Date':<12} {'Core Type':<15} {'Score':<10} {'Impact':<12} {'Ratio':<10}")
        print("-"*70)
        for _, row in outliers_low.iterrows():
            print(f"{row['date']:<12} {row['core_type']:<15} {row['core_score_db']:>9.2f} {row['impact_real']:>11.2f} {row['ratio']:>9.3f}")
        print()
    
    print("="*100)
    print("ANALYSE TERMINÉE")
    print("="*100)

if __name__ == '__main__':
    calculate_ratios_all_dates()

