#!/usr/bin/env python3
"""
Validation visuelle des double_wave détectés

Objectif : Confirmer que les doubles sont bien des "deux jambes avec retrace"
et pas un zig_zag mal recollé.

Pour chaque double_wave :
- Affiche les valeurs exactes des pattern_meta
- Vérifie les critères : retrace_ratio ≥ 30%, leg2_amp ≥ 0.8×leg1_amp, peak2 fait nouveau extreme
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import timedelta

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from integrate_direction_first_leg import calculate_cluster_impact_with_direction
from test_direction_router_batch import (
    load_direction_router_dependencies,
    identify_tradable_dates,
    load_events_for_window,
    DB_PATH,
    MOVEMENTS_FILE
)
from direction_router_v6 import CORE_FAMILIES_V6

def main():
    # Charger résultats scan
    patterns_file = SCRIPT_DIR / 'outputs' / 'direction_router_test' / 'patterns_detected.csv'
    
    # Debug : vérifier chemin
    print(f"🔍 Looking for: {patterns_file}")
    print(f"   Exists: {patterns_file.exists()}")
    print()
    
    if not patterns_file.exists():
        print("❌ Fichier patterns_detected.csv non trouvé")
        print("   Lance d'abord : python3 scan_patterns_historique_complet.py")
        return
    
    df = pd.read_csv(patterns_file)
    double_wave = df[df['pattern_type'] == 'double_wave'].drop_duplicates(subset=['date'])
    
    if len(double_wave) == 0:
        print("❌ Aucun double_wave trouvé dans patterns_detected.csv")
        return
    
    print("=" * 80)
    print("VALIDATION VISUELLE DOUBLE-WAVE")
    print("=" * 80)
    print()
    print(f"📊 {len(double_wave)} cas double_wave uniques à valider")
    print()
    
    # Charger dépendances
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    stats_map, alpha_map = load_direction_router_dependencies(
        db_path=DB_PATH,
        alpha_file=None,
        horizon='1h'
    )
    
    movements_df = pd.read_csv(MOVEMENTS_FILE)
    movements_df['movement_start_time'] = pd.to_datetime(
        movements_df['movement_start_time'], 
        utc=True
    )
    
    # Pour chaque double_wave, recharger et valider
    for idx, row in double_wave.iterrows():
        date_str = str(row['date'])
        cluster_type = row['cluster_type']
        
        # Patch D : utiliser movement_start_time exact du CSV
        if 'movement_start_time' not in row or pd.isna(row['movement_start_time']):
            print(f"⚠️  {date_str} : movement_start_time manquant dans CSV")
            print("   → Relancer scan_patterns_historique_complet.py pour générer CSV avec movement_start_time")
            continue
        
        movement_start = pd.to_datetime(row['movement_start_time'], utc=True)
        
        print("=" * 80)
        print(f"📅 {date_str} ({cluster_type})")
        print("=" * 80)
        print()
        
        # Charger events
        events_df = load_events_for_window(conn, movement_start)
        events_core = events_df[events_df['family'].isin(CORE_FAMILIES_V6)].copy()
        
        if len(events_core) == 0:
            print("   ⚠️  Pas d'events core")
            continue
        
        events_core = events_core.copy()
        if 'empirical_score' not in events_core.columns:
            events_core['empirical_score'] = 10.0
        if 'latency_median' not in events_core.columns:
            events_core['latency_median'] = 2.0
        
        try:
            # Recalculer pour obtenir pattern_meta complet
            result = calculate_cluster_impact_with_direction(
                cluster_events=events_core,
                stats_map=stats_map,
                alpha_map=alpha_map,
                trigger_z=1.0,
                theta=0.05,
                first_leg_mode=True,
                use_linear_formula=True,
                movement_start_time=movement_start,
                conn=conn
            )
            
            if result.get('pattern_type') != 'double_wave':
                print(f"   ⚠️  Pattern recalculé : {result.get('pattern_type')} (attendu: double_wave)")
                continue
            
            # Extraire pattern_meta
            pattern_meta = result.get('pattern_meta', {})
            leg1 = result.get('leg1', {})
            leg2 = result.get('leg2', {})
            
            print("📊 MÉTADONNÉES PATTERN")
            print()
            
            # Informations générales
            print(f"   Direction first-leg : {result.get('direction_first_leg')}")
            print(f"   Impact total : {result.get('impact_pips', 0):.1f} pips")
            print(f"   Trigger strength : {result.get('trigger_strength', 0):.2f}")
            print()
            
            # Peak1
            peak1 = pattern_meta.get('peak1', {})
            if peak1:
                print(f"   Peak1 :")
                print(f"      Time : {peak1.get('time')}")
                print(f"      Price : {peak1.get('price', 0):.5f}")
                print(f"      Pips depuis baseline : {peak1.get('pips', 0):.1f}")
                print()
            
            # Trough
            trough = pattern_meta.get('trough', {})
            if trough:
                print(f"   Trough :")
                print(f"      Time : {trough.get('time')}")
                print(f"      Price : {trough.get('price', 0):.5f}")
                print(f"      Pips depuis baseline : {trough.get('pips', 0):.1f}")
                print()
            
            # Peak2
            peak2 = pattern_meta.get('peak2', {})
            if peak2:
                print(f"   Peak2 :")
                print(f"      Time : {peak2.get('time')}")
                print(f"      Price : {peak2.get('price', 0):.5f}")
                print(f"      Pips depuis baseline : {peak2.get('pips', 0):.1f}")
                print()
            
            # Jambes
            if leg1:
                print(f"   Jambe 1 :")
                print(f"      Direction : {leg1.get('direction')}")
                print(f"      Amplitude : {leg1.get('amplitude_pips', 0):.1f} pips")
                print(f"      T peak : T+{leg1.get('t_peak_min', 0):.0f} min")
                print()
            
            if leg2:
                print(f"   Jambe 2 :")
                print(f"      Direction : {leg2.get('direction')}")
                print(f"      Amplitude : {leg2.get('amplitude_pips', 0):.1f} pips")
                print(f"      T peak : T+{leg2.get('t_peak_min', 0):.0f} min")
                print()
            
            # Critères validation
            print("✅ CRITÈRES VALIDATION")
            print()
            
            retrace_ratio = pattern_meta.get('retrace_ratio', 0)
            leg1_amp_pips = pattern_meta.get('leg1_amp_pips', 0)
            leg2_amp_pips = pattern_meta.get('leg2_amp_pips', 0)
            leg2_extends = pattern_meta.get('leg2_extends', False)
            
            # Critère 1 : retrace_ratio ≥ 30%
            crit1_ok = retrace_ratio >= 0.30
            print(f"   [{'✅' if crit1_ok else '❌'}] Retrace ratio ≥ 30%")
            print(f"      Valeur : {retrace_ratio:.2%}")
            print()
            
            # Critère 2 : leg2_amp ≥ 0.8×leg1_amp
            leg2_min = leg1_amp_pips * 0.8
            crit2_ok = leg2_amp_pips >= leg2_min
            print(f"   [{'✅' if crit2_ok else '❌'}] Leg2 amplitude ≥ 0.8×leg1")
            print(f"      Leg1 : {leg1_amp_pips:.1f} pips")
            print(f"      Leg2 : {leg2_amp_pips:.1f} pips (min: {leg2_min:.1f})")
            print()
            
            # Critère 3 : peak2 fait nouveau extreme
            crit3_ok = leg2_extends
            print(f"   [{'✅' if crit3_ok else '❌'}] Peak2 fait nouveau high/low")
            print(f"      Valeur : {leg2_extends}")
            print()
            
            # Résumé validation
            all_ok = crit1_ok and crit2_ok and crit3_ok
            print(f"   {'✅ VALIDATION OK' if all_ok else '⚠️  VALIDATION PARTIELLE'}")
            print()
            
            # Calculs détaillés
            if peak1 and peak2 and trough:
                direction_base = result.get('direction_first_leg', 'UP')
                if direction_base == 'UP':
                    retrace_pips_calc = (peak1.get('price', 0) - trough.get('price', 0)) * 10000
                    leg2_amp_calc = (peak2.get('price', 0) - trough.get('price', 0)) * 10000
                else:
                    retrace_pips_calc = (trough.get('price', 0) - peak1.get('price', 0)) * 10000
                    leg2_amp_calc = (trough.get('price', 0) - peak2.get('price', 0)) * 10000
                
                print("📐 CALCULS DÉTAILLÉS")
                print()
                print(f"   Retrace pips (calculé) : {retrace_pips_calc:.1f}")
                print(f"   Leg2 amp depuis trough (calculé) : {leg2_amp_calc:.1f}")
                print()
            
        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    conn.close()
    print("=" * 80)
    print("✅ VALIDATION TERMINÉE")
    print("=" * 80)

if __name__ == '__main__':
    main()

