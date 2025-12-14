#!/usr/bin/env python3
"""
Analyse Complète Toutes Dates
==============================

Objectif : Extraire tous les détails pour toutes les dates de test (pic1, pullback, pic2, timings, cours, pips, baseline)
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

# Dates à tester : Utiliser uniquement les dates valides (avec événement coïncidant)
# REF-027 : Filtrage des dates avec événement coïncidant avec début du mouvement
# Note : 2025-10-10 et 2025-11-26 ont été éliminées si pas de coïncidence
TEST_DATES = [d for d in VALID_TEST_DATES if d in [
    '2025-09-11',  # Alternative 1
    '2025-11-20',  # Alternative 3
    '2025-06-23',  # Alternative 3
    '2025-05-29',  # Alternative 5
    '2025-08-01',  # Single Wave
]]

print('='*100)
print('ANALYSE COMPLÈTE - TOUTES LES DATES')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

all_results = []

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 DATE : {date_str}')
    print('='*100)
    print()
    
    try:
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur: {result.get("error")}')
            continue
        
        final_pred = result.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        
        # Extraire informations
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        alternative = pattern_info.get('alternative', 'NONE')
        alternative_reason = pattern_info.get('alternative_reason', '')
        
        wave1_time = pattern_info.get('wave1_peak_time')
        pullback_time = pattern_info.get('pullback_low_time')
        wave2_time = pattern_info.get('wave2_peak_time')
        stabilization_time = pattern_info.get('stabilization_time')
        
        wave1_pips = pattern_info.get('wave1_pips', 0.0)
        pullback_pips = pattern_info.get('pullback_pips', 0.0)
        wave2_pips = pattern_info.get('wave2_pips', 0.0)
        wave2_peak_pips_absolute = pattern_info.get('wave2_peak_pips_absolute', 0.0)
        
        baseline_price = pattern_info.get('baseline_price')
        impact_base = final_pred.get('impact_base', 0.0)
        amplification = final_pred.get('amplification_predite', 1.0)
        impact_predicted = final_pred.get('prediction_finale', 0.0)
        
        print(f'📊 RÉSULTATS PIPELINE')
        print('-'*100)
        print(f'Pattern : {pattern_type}')
        print(f'Alternative : {alternative}')
        print(f'Raison : {alternative_reason}')
        print()
        
        # Charger les prix depuis la DB pour obtenir les cours réels
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Fenêtre de recherche : ±2 heures autour de l'anchor_time
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
                # S'assurer que le timezone est Europe/Zurich
                if df_prices['datetime'].dt.tz is None:
                    df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('Europe/Zurich')
                else:
                    df_prices['datetime'] = df_prices['datetime'].dt.tz_convert('Europe/Zurich')
                df_prices = df_prices.set_index('datetime')
                
                print('='*100)
                print('📊 BASELINE')
                print('='*100)
                print()
                
                # Afficher baseline
                if baseline_price:
                    print(f'  Prix baseline : {baseline_price:.5f}')
                    # Trouver la barre baseline
                    baseline_time = anchor_time - pd.Timedelta(minutes=1)
                    if baseline_time.tzinfo:
                        baseline_time_tz = baseline_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else baseline_time.tz_localize(None)
                    else:
                        baseline_time_tz = baseline_time
                    if df_prices.index.tz:
                        baseline_time_tz = baseline_time_tz.tz_localize(df_prices.index.tz) if not baseline_time_tz.tzinfo else baseline_time_tz
                    
                    closest_baseline_idx = df_prices.index.get_indexer([baseline_time_tz], method='nearest')[0]
                    if closest_baseline_idx >= 0:
                        baseline_bar = df_prices.iloc[closest_baseline_idx]
                        print(f'  Barre baseline : {df_prices.index[closest_baseline_idx].strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  OPEN : {baseline_bar["open"]:.5f}')
                        print(f'  HIGH : {baseline_bar["high"]:.5f}')
                        print(f'  LOW : {baseline_bar["low"]:.5f}')
                        print(f'  CLOSE : {baseline_bar["close"]:.5f}')
                else:
                    # Utiliser le prix de la première barre comme baseline
                    first_bar = df_prices.iloc[0]
                    baseline_price = first_bar['close']
                    print(f'  Prix baseline (première barre) : {baseline_price:.5f}')
                    print(f'  Barre baseline : {df_prices.index[0].strftime("%Y-%m-%d %H:%M:%S")}')
                    print(f'  OPEN : {first_bar["open"]:.5f}')
                    print(f'  HIGH : {first_bar["high"]:.5f}')
                    print(f'  LOW : {first_bar["low"]:.5f}')
                    print(f'  CLOSE : {first_bar["close"]:.5f}')
                print()
                
                print('='*100)
                print('📈 TIMINGS ET COURS RÉELS')
                print('='*100)
                print()
                
                # PIC 1 (Wave1)
                if wave1_time:
                    # Convertir wave1_time au même timezone que df_prices
                    if wave1_time.tzinfo:
                        wave1_time_tz = wave1_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else wave1_time.tz_localize(None)
                    else:
                        wave1_time_tz = wave1_time
                    if df_prices.index.tz:
                        wave1_time_tz = wave1_time_tz.tz_localize(df_prices.index.tz) if not wave1_time_tz.tzinfo else wave1_time_tz
                    closest_idx = df_prices.index.get_indexer([wave1_time_tz], method='nearest')[0]
                    
                    if closest_idx >= 0:
                        wave1_price_data = df_prices.iloc[closest_idx]
                        wave1_high = wave1_price_data['high']
                        wave1_low = wave1_price_data['low']
                        wave1_close = wave1_price_data['close']
                        
                        # Calculer pips depuis baseline
                        wave1_pips_high = (wave1_high - baseline_price) * 10000
                        wave1_pips_low = (wave1_low - baseline_price) * 10000
                        wave1_pips_close = (wave1_close - baseline_price) * 10000
                        
                        print(f'🎯 PIC 1 (Wave1)')
                        print('-'*100)
                        print(f'  Timing prédit : {wave1_time.strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  Timing réel (barre la plus proche) : {df_prices.index[closest_idx].strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  Cours HIGH : {wave1_high:.5f} → {wave1_pips_high:.2f} pips')
                        print(f'  Cours LOW : {wave1_low:.5f} → {wave1_pips_low:.2f} pips')
                        print(f'  Cours CLOSE : {wave1_close:.5f} → {wave1_pips_close:.2f} pips')
                        print(f'  Pips prédits (pattern) : {wave1_pips:.2f} pips')
                        print()
                
                # PULLBACK
                if pullback_time:
                    # Convertir pullback_time au même timezone que df_prices
                    if pullback_time.tzinfo:
                        pullback_time_tz = pullback_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else pullback_time.tz_localize(None)
                    else:
                        pullback_time_tz = pullback_time
                    if df_prices.index.tz:
                        pullback_time_tz = pullback_time_tz.tz_localize(df_prices.index.tz) if not pullback_time_tz.tzinfo else pullback_time_tz
                    closest_idx = df_prices.index.get_indexer([pullback_time_tz], method='nearest')[0]
                    
                    if closest_idx >= 0:
                        pullback_price_data = df_prices.iloc[closest_idx]
                        pullback_high = pullback_price_data['high']
                        pullback_low = pullback_price_data['low']
                        pullback_close = pullback_price_data['close']
                        
                        # Calculer pips depuis baseline
                        pullback_pips_high = (pullback_high - baseline_price) * 10000
                        pullback_pips_low = (pullback_low - baseline_price) * 10000
                        pullback_pips_close = (pullback_close - baseline_price) * 10000
                        
                        print(f'📉 PULLBACK')
                        print('-'*100)
                        print(f'  Timing prédit : {pullback_time.strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  Timing réel (barre la plus proche) : {df_prices.index[closest_idx].strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  Cours HIGH : {pullback_high:.5f} → {pullback_pips_high:.2f} pips')
                        print(f'  Cours LOW : {pullback_low:.5f} → {pullback_pips_low:.2f} pips')
                        print(f'  Cours CLOSE : {pullback_close:.5f} → {pullback_pips_close:.2f} pips')
                        print(f'  Pips prédits (pattern) : {abs(pullback_pips):.2f} pips')
                        print()
                
                # PIC 2 (Wave2) - seulement si DOUBLE_WAVE
                if wave2_time and pattern_type == 'DOUBLE_WAVE':
                    # Convertir wave2_time au même timezone que df_prices
                    if wave2_time.tzinfo:
                        wave2_time_tz = wave2_time.tz_convert(df_prices.index.tz) if df_prices.index.tz else wave2_time.tz_localize(None)
                    else:
                        wave2_time_tz = wave2_time
                    if df_prices.index.tz:
                        wave2_time_tz = wave2_time_tz.tz_localize(df_prices.index.tz) if not wave2_time_tz.tzinfo else wave2_time_tz
                    closest_idx = df_prices.index.get_indexer([wave2_time_tz], method='nearest')[0]
                    
                    if closest_idx >= 0:
                        wave2_price_data = df_prices.iloc[closest_idx]
                        wave2_high = wave2_price_data['high']
                        wave2_low = wave2_price_data['low']
                        wave2_close = wave2_price_data['close']
                        
                        # Calculer pips depuis baseline
                        wave2_pips_high = (wave2_high - baseline_price) * 10000
                        wave2_pips_low = (wave2_low - baseline_price) * 10000
                        wave2_pips_close = (wave2_close - baseline_price) * 10000
                        
                        print(f'🎯 PIC 2 (Wave2)')
                        print('-'*100)
                        print(f'  Timing prédit : {wave2_time.strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  Timing réel (barre la plus proche) : {df_prices.index[closest_idx].strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  Cours HIGH : {wave2_high:.5f} → {wave2_pips_high:.2f} pips')
                        print(f'  Cours LOW : {wave2_low:.5f} → {wave2_pips_low:.2f} pips')
                        print(f'  Cours CLOSE : {wave2_close:.5f} → {wave2_pips_close:.2f} pips')
                        print(f'  Pips prédits (pattern) : {wave2_pips:.2f} pips')
                        print(f'  Pips absolus (prédit) : {wave2_peak_pips_absolute:.2f} pips')
                        print()
                
                # Rechercher le pic absolu réel dans la fenêtre
                if baseline_price and baseline_price > 0:
                    # Trouver le HIGH maximum dans la fenêtre
                    max_high_idx = df_prices['high'].idxmax()
                    max_high_price = df_prices.loc[max_high_idx, 'high']
                    max_high_pips = (max_high_price - baseline_price) * 10000
                    
                    # Trouver le LOW minimum dans la fenêtre
                    min_low_idx = df_prices['low'].idxmin()
                    min_low_price = df_prices.loc[min_low_idx, 'low']
                    min_low_pips = (min_low_price - baseline_price) * 10000
                    
                    print('='*100)
                    print('📊 PIC ABSOLU RÉEL (dans fenêtre ±2h)')
                    print('='*100)
                    print()
                    print(f'  Pic HIGH maximum : {max_high_price:.5f} @ {max_high_idx.strftime("%Y-%m-%d %H:%M:%S")} → {max_high_pips:.2f} pips')
                    print(f'  Creux LOW minimum : {min_low_price:.5f} @ {min_low_idx.strftime("%Y-%m-%d %H:%M:%S")} → {min_low_pips:.2f} pips')
                    print()
            
            else:
                print('⚠️ Aucune donnée de prix trouvée dans la fenêtre')
        else:
            print('⚠️ Anchor time non disponible')
        
        # Résumé
        print('='*100)
        print('📊 RÉSUMÉ')
        print('='*100)
        print()
        
        print(f'Impact base : {impact_base:.2f} pips')
        print(f'Amplification : {amplification:.3f}x')
        print(f'Impact prédit final : {impact_predicted:.2f} pips')
        print()
        
        if wave1_time:
            print('Timings prédits :')
            print(f'  Pic 1 : {wave1_time.strftime("%H:%M")} ({wave1_pips:.2f} pips)')
            if pullback_time:
                print(f'  Pullback : {pullback_time.strftime("%H:%M")} ({abs(pullback_pips):.2f} pips)')
            if wave2_time:
                print(f'  Pic 2 : {wave2_time.strftime("%H:%M")} ({wave2_pips:.2f} pips)')
                print(f'  Pic 2 absolu (prédit) : {wave2_peak_pips_absolute:.2f} pips')
            print()
            
            # Afficher le pic absolu réel si disponible
            if baseline_price and baseline_price > 0 and not df_prices.empty:
                max_high_idx = df_prices['high'].idxmax()
                max_high_price = df_prices.loc[max_high_idx, 'high']
                max_high_pips = (max_high_price - baseline_price) * 10000
                print(f'  Pic absolu réel (HIGH max) : {max_high_idx.strftime("%H:%M")} ({max_high_pips:.2f} pips @ {max_high_price:.5f})')
                print()
        
        # Stocker résultats pour CSV
        all_results.append({
            'date': date_str,
            'pattern_type': pattern_type,
            'alternative': alternative,
            'baseline_price': baseline_price,
            'baseline_time': df_prices.index[0].strftime('%Y-%m-%d %H:%M:%S') if not df_prices.empty else None,
            'wave1_time': wave1_time.strftime('%H:%M') if wave1_time else None,
            'wave1_pips_predicted': wave1_pips,
            'wave1_pips_real_high': wave1_pips_high if wave1_time and not df_prices.empty else None,
            'pullback_time': pullback_time.strftime('%H:%M') if pullback_time else None,
            'pullback_pips_predicted': abs(pullback_pips),
            'pullback_pips_real_low': pullback_pips_low if pullback_time and not df_prices.empty else None,
            'wave2_time': wave2_time.strftime('%H:%M') if wave2_time else None,
            'wave2_pips_predicted': wave2_pips,
            'wave2_pips_real_high': wave2_pips_high if wave2_time and not df_prices.empty else None,
            'wave2_peak_pips_absolute': wave2_peak_pips_absolute,
            'max_high_pips_real': max_high_pips if baseline_price and not df_prices.empty else None,
            'max_high_time_real': max_high_idx.strftime('%H:%M') if baseline_price and not df_prices.empty else None,
            'impact_base': impact_base,
            'amplification': amplification,
            'impact_predicted': impact_predicted
        })
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

# Sauvegarder résultats dans CSV
df_results = pd.DataFrame(all_results)
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'analyse_complete_toutes_dates.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df_results.to_csv(output_file, index=False)
print('='*100)
print(f'✅ Résultats sauvegardés : {output_file}')
print('='*100)

