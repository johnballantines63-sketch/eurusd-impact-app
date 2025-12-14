#!/usr/bin/env python3
"""
Diagnostic de la détection double-wave

Analyse pourquoi les cas avec 2 turning points ne passent pas les critères double-wave.
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import timedelta

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from integrate_direction_first_leg import _detect_pattern_type, _find_turning_points, _analyze_turning_points_sequence
from test_direction_router_batch import DB_PATH, MOVEMENTS_FILE, identify_tradable_dates, load_events_for_window
from direction_router_v6 import CORE_FAMILIES_V6

def main():
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Charger quelques dates tradables
    movements_df = pd.read_csv(MOVEMENTS_FILE)
    movements_df['movement_start_time'] = pd.to_datetime(movements_df['movement_start_time'], utc=True)
    
    dates_df = identify_tradable_dates(
        conn,
        movements_df,
        sample_size=20,
        min_date='2024-01-01',
        max_date='2025-12-31'
    )
    
    print("=" * 80)
    print("DIAGNOSTIC DÉTECTION DOUBLE-WAVE")
    print("=" * 80)
    print()
    
    for idx, row in dates_df.iterrows():
        date_str = str(row['date'])
        movement_start = row['movement_start_time']
        
        # Charger prix
        t0 = pd.to_datetime(movement_start)
        t_end = t0 + pd.Timedelta(hours=2)
        
        price_tables = ['prices_finnhub_m1', 'prices_1m', 'prices_bern']
        df_prices = None
        
        for table in price_tables:
            try:
                query = f"""
                SELECT datetime, close, high, low
                FROM {table}
                WHERE datetime >= ? AND datetime <= ?
                ORDER BY datetime ASC
                """
                df_prices = conn.execute(query, [t0, t_end]).df()
                if len(df_prices) > 0:
                    break
            except:
                continue
        
        if df_prices is None or len(df_prices) < 10:
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True)
        baseline_price = df_prices.iloc[0]['close']
        
        # Détecter turning points
        TURN_PIPS = 10.0
        threshold_price = TURN_PIPS / 10000
        turning_points = _find_turning_points(df_prices, baseline_price, threshold_price)
        
        # Filtrer peaks/troughs selon direction
        impact_pips = 50.0  # Approximation pour test
        if impact_pips >= 0:
            relevant_points = [tp for tp in turning_points if tp['type'] == 'peak']
            direction_base = 'UP'
        else:
            relevant_points = [tp for tp in turning_points if tp['type'] == 'trough']
            direction_base = 'DOWN'
        
        nb_turning_points = len(relevant_points)
        
        # Analyser seulement les cas avec 2 turning points
        if nb_turning_points == 2:
            peak1 = relevant_points[0]
            peak2 = relevant_points[1]
            
            # Chercher trough entre
            troughs_between = [
                tp for tp in turning_points 
                if tp['type'] == 'trough' 
                and peak1['time'] < tp['time'] < peak2['time']
            ]
            
            print(f"📅 {date_str}")
            print(f"   Turning points : {nb_turning_points}")
            print(f"   Troughs entre peaks : {len(troughs_between)}")
            
            if len(troughs_between) > 0:
                trough = min(troughs_between, key=lambda x: x['price'] if direction_base == 'UP' else -x['price'])
                
                amp_leg1 = abs(peak1['pips'])
                if direction_base == 'UP':
                    retrace_pips = peak1['price'] - trough['price']
                    leg2_amp_from_trough = peak2['price'] - trough['price']
                    leg2_makes_new_extreme = peak2['price'] > peak1['price']
                else:
                    retrace_pips = trough['price'] - peak1['price']
                    leg2_amp_from_trough = trough['price'] - peak2['price']
                    leg2_makes_new_extreme = peak2['price'] < peak1['price']
                
                retrace_ratio = retrace_pips / amp_leg1 if amp_leg1 > 0 else 0
                leg2_amp_pips = abs(leg2_amp_from_trough) * 10000
                leg1_amp_pips = amp_leg1
                
                LEG2_EXTEND_RATIO = 0.80
                leg2_extends = (leg2_amp_pips >= leg1_amp_pips * LEG2_EXTEND_RATIO) and leg2_makes_new_extreme
                
                print(f"   Retrace ratio : {retrace_ratio:.2%} (min: 30%)")
                print(f"   Leg1 amp : {leg1_amp_pips:.1f} pips")
                print(f"   Leg2 amp : {leg2_amp_pips:.1f} pips (min: {leg1_amp_pips * LEG2_EXTEND_RATIO:.1f})")
                print(f"   Leg2 fait nouveau extreme : {leg2_makes_new_extreme}")
                print(f"   Leg2 extends : {leg2_extends}")
                print(f"   → Double-wave : {retrace_ratio >= 0.30 and leg2_extends}")
                print()
            else:
                print(f"   ⚠️  Pas de trough entre peaks → single-wave")
                print()
    
    conn.close()

if __name__ == '__main__':
    main()

