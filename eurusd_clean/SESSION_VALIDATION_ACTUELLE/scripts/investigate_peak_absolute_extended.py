#!/usr/bin/env python3
"""
Investigation Pic Absolu Étendu
=================================

Objectif : Comprendre pourquoi le pic absolu étendu trouve 15.00 pips au lieu de 74.40 pips
"""

import sys
from pathlib import Path
import pandas as pd
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor
from scripts.session120.double_wave_detector_rev12 import detect_for_date_duckdb_rev12

PROBLEMATIC_DATES = [
    '2025-05-29',  # Pic absolu étendu = 15.00, Impact réel = 74.40
    '2025-06-23',  # Pic absolu étendu = 15.50, Impact réel = 88.60
]

print('='*100)
print('INVESTIGATION PIC ABSOLU ÉTENDU')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

for date_str in PROBLEMATIC_DATES:
    print('='*100)
    print(f'📅 DATE : {date_str}')
    print('='*100)
    print()
    
    try:
        # 1. Exécuter pipeline pour obtenir anchor_time et baseline
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur: {result.get("error")}')
            continue
        
        # Obtenir anchor_time
        clusters = result.get('etape2_clusters', [])
        anchor_time = None
        if clusters and len(clusters) > 0:
            anchor_time = clusters[0].get('anchor_time')
        
        if anchor_time is None:
            tz_bern = pytz.timezone('Europe/Zurich')
            anchor_time = tz_bern.localize(pd.to_datetime(f"{date_str} 14:30:00"))
        
        print('📊 INFORMATIONS PIPELINE')
        print('-'*100)
        print(f'Anchor time: {anchor_time}')
        print()
        
        # 2. Détecter pattern réel
        anchor_time_naive = anchor_time.replace(tzinfo=None) if anchor_time.tz else anchor_time
        pattern_real = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=anchor_time_naive,
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=180,
            trading_window=True,
            debug=False,
            event_time=anchor_time_naive
        )
        
        if pattern_real:
            baseline_price_pattern = pattern_real.get('baseline_price', 0.0)
            wave2_real = pattern_real.get('wave2_amp_pips', 0.0)
            
            print('📊 PATTERN RÉEL DÉTECTÉ')
            print('-'*100)
            print(f'Baseline pattern: {baseline_price_pattern:.5f}')
            print(f'Wave2 amp pips: {wave2_real:.2f} pips')
            print(f'Confidence: {pattern_real.get("confidence", 0.0):.1f}%')
            print()
        else:
            print('⚠️ Pattern réel non détecté')
            baseline_price_pattern = 0.0
            wave2_real = 0.0
            print()
        
        # 3. Rechercher pic absolu étendu (comme dans le pipeline)
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        window_start_event = anchor_time - pd.Timedelta(hours=1)
        window_end_extended = anchor_time + pd.Timedelta(hours=2)
        
        query_extended = f"""
        SELECT datetime, high, low, close, open
        FROM prices_finnhub_m1
        WHERE datetime >= '{window_start_event.isoformat()}' 
          AND datetime <= '{window_end_extended.isoformat()}'
        ORDER BY datetime ASC
        """
        
        df_extended = conn.execute(query_extended).df()
        conn.close()
        
        if df_extended.empty:
            print('⚠️ Aucune donnée prix trouvée')
            continue
        
        df_extended['datetime'] = pd.to_datetime(df_extended['datetime'])
        df_extended = df_extended.set_index('datetime')
        
        print('📊 RECHERCHE PIC ABSOLU ÉTENDU')
        print('-'*100)
        print(f'Fenêtre: {window_start_event} → {window_end_extended}')
        print(f'Nombre de bougies: {len(df_extended)}')
        print()
        
        if baseline_price_pattern > 0:
            # Méthode pipeline : pic absolu depuis baseline pattern
            peak_absolute_price = df_extended['high'].max()
            peak_absolute_time = df_extended['high'].idxmax()
            wave2_absolute_extended = (peak_absolute_price - baseline_price_pattern) * 10000
            
            print('📊 PIC ABSOLU ÉTENDU (Méthode Pipeline)')
            print('-'*100)
            print(f'Baseline utilisé: {baseline_price_pattern:.5f} (baseline pattern)')
            print(f'Peak price: {peak_absolute_price:.5f}')
            print(f'Peak time: {peak_absolute_time}')
            print(f'Impact calculé: {wave2_absolute_extended:.2f} pips')
            print()
        
        # 4. Mesurer impact réel (méthode correcte)
        prices_at_event = df_extended[df_extended.index >= anchor_time]
        
        if not prices_at_event.empty:
            start_price = prices_at_event.iloc[0]['open']
            
            prices_after = df_extended[df_extended.index >= anchor_time].copy()
            peak_high = prices_after['high'].max()
            peak_high_time = prices_after['high'].idxmax()
            impact_real = (peak_high - start_price) * 10000
            
            print('📊 IMPACT RÉEL MESURÉ (Méthode Correcte)')
            print('-'*100)
            print(f'Start price (OPEN première bougie): {start_price:.5f}')
            print(f'Peak high: {peak_high:.5f}')
            print(f'Peak time: {peak_high_time}')
            print(f'Impact réel: {impact_real:.2f} pips')
            print()
            
            # 5. Comparaison
            print('📊 COMPARAISON')
            print('-'*100)
            if baseline_price_pattern > 0:
                print(f'Pic absolu étendu (baseline pattern): {wave2_absolute_extended:.2f} pips')
                print(f'Impact réel (OPEN première bougie): {impact_real:.2f} pips')
                print(f'Différence: {abs(wave2_absolute_extended - impact_real):.2f} pips')
                print()
                
                # Vérifier baseline
                print('📊 ANALYSE BASELINE')
                print('-'*100)
                print(f'Baseline pattern: {baseline_price_pattern:.5f}')
                print(f'Start price (OPEN): {start_price:.5f}')
                print(f'Différence baseline: {abs(baseline_price_pattern - start_price):.5f} ({abs(baseline_price_pattern - start_price) * 10000:.2f} pips)')
                print()
                
                # Vérifier si le pic absolu est dans la bonne fenêtre
                minutes_after_event = (peak_absolute_time - anchor_time).total_seconds() / 60.0
                print(f'Minutes après événement (pic absolu): {minutes_after_event:.1f} min')
                print(f'Minutes après événement (pic réel): {(peak_high_time - anchor_time).total_seconds() / 60.0:.1f} min')
                print()
                
                # Vérifier si le pic absolu est le même que le pic réel
                if abs(peak_absolute_time - peak_high_time).total_seconds() < 60:
                    print('✅ Pic absolu et pic réel sont au même moment')
                else:
                    print('⚠️ Pic absolu et pic réel sont à des moments différents')
                    print(f'   Pic absolu: {peak_absolute_time}')
                    print(f'   Pic réel: {peak_high_time}')
                print()
        
        # 6. Vérifier toutes les bougies pour comprendre
        print('📊 ANALYSE DÉTAILLÉE DES PRIX')
        print('-'*100)
        print('Premières bougies après événement:')
        prices_after = df_extended[df_extended.index >= anchor_time].head(10)
        for idx, row in prices_after.iterrows():
            pips_from_baseline = (row['high'] - baseline_price_pattern) * 10000 if baseline_price_pattern > 0 else 0
            pips_from_start = (row['high'] - start_price) * 10000 if not prices_at_event.empty else 0
            print(f'  {idx.strftime("%H:%M")}: High={row["high"]:.5f}, Open={row["open"]:.5f}, Pips(baseline)={pips_from_baseline:.2f}, Pips(start)={pips_from_start:.2f}')
        print()
        
        # 7. Trouver le vrai pic dans une fenêtre plus large
        print('📊 RECHERCHE PIC DANS FENÊTRE ÉLARGIE')
        print('-'*100)
        window_end_large = anchor_time + pd.Timedelta(hours=4)  # 4h au lieu de 2h
        
        query_large = f"""
        SELECT datetime, high, low, close, open
        FROM prices_finnhub_m1
        WHERE datetime >= '{window_start_event.isoformat()}' 
          AND datetime <= '{window_end_large.isoformat()}'
        ORDER BY datetime ASC
        """
        
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        df_large = conn.execute(query_large).df()
        conn.close()
        
        if not df_large.empty:
            df_large['datetime'] = pd.to_datetime(df_large['datetime'])
            df_large = df_large.set_index('datetime')
            
            prices_after_large = df_large[df_large.index >= anchor_time]
            if not prices_after_large.empty:
                start_price_large = prices_after_large.iloc[0]['open']
                peak_high_large = prices_after_large['high'].max()
                peak_high_time_large = prices_after_large['high'].idxmax()
                impact_real_large = (peak_high_large - start_price_large) * 10000
                
                print(f'Fenêtre élargie: {window_start_event} → {window_end_large}')
                print(f'Start price: {start_price_large:.5f}')
                print(f'Peak high: {peak_high_large:.5f}')
                print(f'Peak time: {peak_high_time_large}')
                print(f'Impact réel (fenêtre 4h): {impact_real_large:.2f} pips')
                print()
                
                if baseline_price_pattern > 0:
                    wave2_absolute_large = (peak_high_large - baseline_price_pattern) * 10000
                    print(f'Impact depuis baseline pattern (fenêtre 4h): {wave2_absolute_large:.2f} pips')
                    print()
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        continue

print('='*100)
print('✅ INVESTIGATION TERMINÉE')
print('='*100)




