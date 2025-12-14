#!/usr/bin/env python3
"""
Analyse Différences Prédiction vs Réel
========================================

Objectif : Comparer prédictions et valeurs réelles, identifier surestimation/sous-estimation
"""

import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor
import duckdb

# Charger dates valides (avec événement coïncidant)
sys.path.insert(0, str(PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'utils'))
from test_dates import VALID_TEST_DATES

# Dates à tester avec impacts réels mesurés
# REF-027 : Filtrage des dates avec événement coïncidant avec début du mouvement
# Note : 2025-10-10 et 2025-11-26 éliminées si pas de coïncidence
ALL_TEST_DATES = {
    '2025-09-11': {'real_impact': 60.0, 'pattern': 'DOUBLE_WAVE'},
    '2025-11-20': {'real_impact': 35.5, 'pattern': 'DOUBLE_WAVE'},
    '2025-10-10': {'real_impact': 61.4, 'pattern': 'DOUBLE_WAVE'},
    '2025-06-23': {'real_impact': 5.7, 'pattern': 'DOUBLE_WAVE'},
    '2025-05-29': {'real_impact': 39.0, 'pattern': 'DOUBLE_WAVE'},
    '2025-11-26': {'real_impact': 28.0, 'pattern': 'DOUBLE_WAVE'},
    '2025-08-01': {'real_impact': 188.3, 'pattern': 'SINGLE_WAVE'},
}

# Filtrer pour garder seulement les dates valides
TEST_DATES = {k: v for k, v in ALL_TEST_DATES.items() if k in VALID_TEST_DATES}

print('='*100)
print('ANALYSE DIFFÉRENCES PRÉDICTION VS RÉEL')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

results = []

for date_str, date_info in TEST_DATES.items():
    print(f'📅 {date_str}...', end=' ', flush=True)
    
    try:
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur')
            continue
        
        final_pred = result.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        
        # Extraire informations
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        alternative = pattern_info.get('alternative', 'NONE')
        
        # Impacts
        impact_predicted = final_pred.get('prediction_finale', 0.0)
        real_impact = date_info['real_impact']
        
        # Calculer différences
        difference_pips = impact_predicted - real_impact
        difference_pct = (difference_pips / real_impact * 100) if real_impact > 0 else 0.0
        
        # Déterminer type d'erreur
        if difference_pips > 0:
            error_type = 'SURESTIMATION'
            error_icon = '⬆️'
        elif difference_pips < 0:
            error_type = 'SOUS-ESTIMATION'
            error_icon = '⬇️'
        else:
            error_type = 'PARFAIT'
            error_icon = '✅'
        
        # Timings
        wave1_time = pattern_info.get('wave1_peak_time')
        pullback_time = pattern_info.get('pullback_low_time')
        wave2_time = pattern_info.get('wave2_peak_time')
        
        # Charger les prix pour obtenir les valeurs réelles
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        anchor_time = wave1_time - pd.Timedelta(minutes=5) if wave1_time else None
        
        if anchor_time:
            window_start = anchor_time - pd.Timedelta(hours=1)
            window_end = anchor_time + pd.Timedelta(hours=3)
            
            query = f"""
            SELECT datetime, open, high, low, close
            FROM prices_finnhub_m1
            WHERE datetime >= '{window_start.isoformat()}' 
              AND datetime <= '{window_end.isoformat()}'
            ORDER BY datetime ASC
            """
            
            df_prices = conn.execute(query).df()
            conn.close()
            
            if not df_prices.empty:
                df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
                if df_prices['datetime'].dt.tz is None:
                    df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('Europe/Zurich')
                else:
                    df_prices['datetime'] = df_prices['datetime'].dt.tz_convert('Europe/Zurich')
                df_prices = df_prices.set_index('datetime')
                
                # Baseline
                baseline_price = pattern_info.get('baseline_price')
                if not baseline_price:
                    baseline_price = df_prices.iloc[0]['close']
                
                # Pic absolu réel
                max_high_idx = df_prices['high'].idxmax()
                max_high_price = df_prices.loc[max_high_idx, 'high']
                max_high_pips_real = (max_high_price - baseline_price) * 10000
                
                # Pic 1 réel
                wave1_pips_real = None
                if wave1_time:
                    if wave1_time.tzinfo:
                        wave1_time_tz = wave1_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else wave1_time.tz_localize(None)
                    else:
                        wave1_time_tz = wave1_time
                    if df_prices.index.tz:
                        wave1_time_tz = wave1_time_tz.tz_localize(df_prices.index.tz) if not wave1_time_tz.tzinfo else wave1_time_tz
                    closest_idx = df_prices.index.get_indexer([wave1_time_tz], method='nearest')[0]
                    if closest_idx >= 0:
                        wave1_high = df_prices.iloc[closest_idx]['high']
                        wave1_pips_real = (wave1_high - baseline_price) * 10000
                
                # Pic 2 réel
                wave2_pips_real = None
                if wave2_time:
                    if wave2_time.tzinfo:
                        wave2_time_tz = wave2_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else wave2_time.tz_localize(None)
                    else:
                        wave2_time_tz = wave2_time
                    if df_prices.index.tz:
                        wave2_time_tz = wave2_time_tz.tz_localize(df_prices.index.tz) if not wave2_time_tz.tzinfo else wave2_time_tz
                    closest_idx = df_prices.index.get_indexer([wave2_time_tz], method='nearest')[0]
                    if closest_idx >= 0:
                        wave2_high = df_prices.iloc[closest_idx]['high']
                        wave2_pips_real = (wave2_high - baseline_price) * 10000
                
                # Pullback réel
                pullback_pips_real = None
                if pullback_time:
                    if pullback_time.tzinfo:
                        pullback_time_tz = pullback_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else pullback_time.tz_localize(None)
                    else:
                        pullback_time_tz = pullback_time
                    if df_prices.index.tz:
                        pullback_time_tz = pullback_time_tz.tz_localize(df_prices.index.tz) if not pullback_time_tz.tzinfo else pullback_time_tz
                    closest_idx = df_prices.index.get_indexer([pullback_time_tz], method='nearest')[0]
                    if closest_idx >= 0:
                        pullback_low = df_prices.iloc[closest_idx]['low']
                        pullback_pips_real = (pullback_low - baseline_price) * 10000
                
                results.append({
                    'date': date_str,
                    'pattern_type': pattern_type,
                    'alternative': alternative,
                    'impact_predicted': impact_predicted,
                    'real_impact': real_impact,
                    'difference_pips': difference_pips,
                    'difference_pct': difference_pct,
                    'error_type': error_type,
                    'error_icon': error_icon,
                    'wave1_pips_predicted': pattern_info.get('wave1_pips', 0.0),
                    'wave1_pips_real': wave1_pips_real,
                    'wave1_diff_pct': ((pattern_info.get('wave1_pips', 0.0) - wave1_pips_real) / wave1_pips_real * 100) if wave1_pips_real and wave1_pips_real != 0 else None,
                    'pullback_pips_predicted': abs(pattern_info.get('pullback_pips', 0.0)),
                    'pullback_pips_real': abs(pullback_pips_real) if pullback_pips_real else None,
                    'wave2_pips_predicted': pattern_info.get('wave2_pips', 0.0),
                    'wave2_pips_real': wave2_pips_real,
                    'wave2_diff_pct': ((pattern_info.get('wave2_pips', 0.0) - wave2_pips_real) / wave2_pips_real * 100) if wave2_pips_real and wave2_pips_real != 0 else None,
                    'max_high_pips_real': max_high_pips_real
                })
        
        print('✅')
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        continue

# Créer DataFrame
df_results = pd.DataFrame(results)

# Afficher tableau
print()
print('='*100)
print('📊 TABLEAU COMPARATIF - PRÉDICTION VS RÉEL')
print('='*100)
print()

# Tableau principal
if not df_results.empty:
    print(f"{'Date':<12} {'Pattern':<15} {'Alt':<12} {'Prédit':<10} {'Réel':<10} {'Diff (pips)':<12} {'Diff (%)':<12} {'Type':<15}")
    print('-'*100)
    
    for _, row in df_results.iterrows():
        alt_str = str(row['alternative']) if not pd.isna(row['alternative']) else 'NONE'
        print(f"{row['date']:<12} {row['pattern_type']:<15} {alt_str:<12} "
              f"{row['impact_predicted']:>9.2f} {row['real_impact']:>9.2f} "
              f"{row['difference_pips']:>11.2f} {row['difference_pct']:>11.1f}% "
              f"{row['error_icon']} {row['error_type']:<15}")
else:
    print('⚠️ Aucun résultat disponible')

print()
print('='*100)
print('📊 ANALYSE PAR TYPE D\'ERREUR')
print('='*100)
print()

# Surestimation
surestimation = df_results[df_results['error_type'] == 'SURESTIMATION']
if not surestimation.empty:
    print(f'⬆️ SURESTIMATION ({len(surestimation)} cas) :')
    print('-'*100)
    for _, row in surestimation.iterrows():
        print(f"  {row['date']} : {row['difference_pips']:+.2f} pips ({row['difference_pct']:+.1f}%)")
    print(f"  → Moyenne : {surestimation['difference_pct'].mean():+.1f}%")
    print()

# Sous-estimation
sous_estimation = df_results[df_results['error_type'] == 'SOUS-ESTIMATION']
if not sous_estimation.empty:
    print(f'⬇️ SOUS-ESTIMATION ({len(sous_estimation)} cas) :')
    print('-'*100)
    for _, row in sous_estimation.iterrows():
        print(f"  {row['date']} : {row['difference_pips']:+.2f} pips ({row['difference_pct']:+.1f}%)")
    print(f"  → Moyenne : {sous_estimation['difference_pct'].mean():+.1f}%")
    print()

# Parfait
parfait = df_results[df_results['error_type'] == 'PARFAIT']
if not parfait.empty:
    print(f'✅ PARFAIT ({len(parfait)} cas) :')
    print('-'*100)
    for _, row in parfait.iterrows():
        print(f"  {row['date']} : {row['difference_pips']:.2f} pips ({row['difference_pct']:.1f}%)")
    print()

print('='*100)
print('📊 STATISTIQUES GLOBALES')
print('='*100)
print()

total = len(df_results)
surestimation_count = len(surestimation)
sous_estimation_count = len(sous_estimation)
parfait_count = len(parfait)

print(f'Total cas : {total}')
print(f'⬆️ Surestimation : {surestimation_count} ({surestimation_count/total*100:.1f}%)')
print(f'⬇️ Sous-estimation : {sous_estimation_count} ({sous_estimation_count/total*100:.1f}%)')
print(f'✅ Parfait : {parfait_count} ({parfait_count/total*100:.1f}%)')
print()

avg_diff_pct = df_results['difference_pct'].mean()
avg_abs_diff_pct = df_results['difference_pct'].abs().mean()

print(f'Différence moyenne : {avg_diff_pct:+.1f}%')
print(f'Différence absolue moyenne : {avg_abs_diff_pct:.1f}%')
print()

# Analyse par alternative
print('='*100)
print('📊 ANALYSE PAR ALTERNATIVE')
print('='*100)
print()

for alt in df_results['alternative'].unique():
    if pd.isna(alt) or alt == 'NONE':
        continue
    alt_df = df_results[df_results['alternative'] == alt]
    print(f'{alt} ({len(alt_df)} cas) :')
    print('-'*100)
    
    alt_surestimation = alt_df[alt_df['error_type'] == 'SURESTIMATION']
    alt_sous_estimation = alt_df[alt_df['error_type'] == 'SOUS-ESTIMATION']
    
    if not alt_surestimation.empty:
        print(f"  ⬆️ Surestimation : {len(alt_surestimation)} cas, moyenne {alt_surestimation['difference_pct'].mean():+.1f}%")
    if not alt_sous_estimation.empty:
        print(f"  ⬇️ Sous-estimation : {len(alt_sous_estimation)} cas, moyenne {alt_sous_estimation['difference_pct'].mean():+.1f}%")
    
    print(f"  Différence moyenne : {alt_df['difference_pct'].mean():+.1f}%")
    print(f"  Différence absolue moyenne : {alt_df['difference_pct'].abs().mean():.1f}%")
    print()

# Sauvegarder résultats
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'analyse_differences_prediction_reel.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df_results.to_csv(output_file, index=False)
print(f'✅ Résultats sauvegardés : {output_file}')

print('='*100)
print('✅ ANALYSE TERMINÉE')
print('='*100)

