#!/usr/bin/env python3
"""
Scan historique complet pour détecter tous les patterns multi-wave

Objectif : Scanner tout l'historique tradable avec triggers pour obtenir :
- ≥ 30 double_wave
- ≥ 10 zig_zag
- Table patterns_detected.csv avec métadonnées complètes

Usage:
    python3 scan_patterns_historique_complet.py --min-date 2024-01-01 --max-date 2025-12-31
"""

import sys
from pathlib import Path
import pandas as pd
import argparse
import duckdb
from datetime import timedelta
from typing import Optional

# Ajouter le répertoire au path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from integrate_direction_first_leg import calculate_cluster_impact_with_direction
from test_direction_router_batch import (
    load_direction_router_dependencies,
    DB_PATH,
    MOVEMENTS_FILE
)
# ⚠️ V8 : identify_tradable_dates et load_events_for_window non utilisés
# (remplacés par identify_tradable_dates_full_day et query directe)

# ⚠️ V8 : utiliser movements_historical.csv si disponible (contient 2022-2025)
MOVEMENTS_FILE_HIST = SCRIPT_DIR / "outputs" / "direction_router_test" / "movements_historical.csv"
if MOVEMENTS_FILE_HIST.exists():
    MOVEMENTS_FILE = MOVEMENTS_FILE_HIST
from datetime import timedelta


def identify_tradable_dates_full_day(
    conn: duckdb.DuckDBPyConnection,
    movements_df: pd.DataFrame,
    min_date: str = '2024-01-01',
    max_date: str = '2025-12-31',
    sample_size: Optional[int] = None
) -> pd.DataFrame:
    """
    Version modifiée de identify_tradable_dates qui cherche events sur TOUTE la journée.
    
    Problème V8 : mouvements détectés au début journée, events économiques plus tard.
    Solution : chercher events sur journée complète au lieu de fenêtre [-4h, +30min].
    
    Returns:
        DataFrame avec colonnes ['date', 'movement_start_time', 'cluster_type', 'n_events_core']
    """
    from direction_router_v6 import map_event_to_family, CORE_FAMILIES_V6
    
    movements_df = movements_df.copy()
    movements_df['movement_start_time'] = pd.to_datetime(movements_df['movement_start_time'], utc=True)
    movements_df['movement_date'] = movements_df['movement_start_time'].dt.date
    
    min_date_dt = pd.to_datetime(min_date).date()
    max_date_dt = pd.to_datetime(max_date).date()
    
    # ⚠️ V8 : gérer colonne peak_pips ou impact_pips
    peak_col = 'peak_pips' if 'peak_pips' in movements_df.columns else 'impact_pips'
    df_movements = movements_df[
        (movements_df['movement_date'] >= min_date_dt) &
        (movements_df['movement_date'] <= max_date_dt) &
        (movements_df[peak_col] >= 40.0)
    ].copy()
    
    # Renommer pour cohérence interne
    if peak_col != 'peak_pips':
        df_movements['peak_pips'] = df_movements[peak_col]
    
    if len(df_movements) == 0:
        return pd.DataFrame(columns=['date', 'movement_start_time', 'cluster_type', 'n_events_core'])
    
    tradable_dates = []
    
    for idx, row in df_movements.iterrows():
        movement_start = row['movement_start_time']
        movement_date = row['movement_date']
        
        # ⚠️ MODIFICATION V8 : chercher events sur TOUTE la journée
        day_start = pd.Timestamp(movement_date).tz_localize('UTC')
        day_end = day_start + timedelta(days=1)
        
        query = """
        SELECT 
            ts_utc,
            event_key,
            actual,
            estimate
        FROM events
        WHERE ts_utc >= ? 
          AND ts_utc < ?
          AND country IN ('US', 'EU', 'GB', 'DE')
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
        ORDER BY ts_utc ASC
        """
        
        try:
            df_events = conn.execute(query, [day_start, day_end]).df()
        except:
            continue
        
        if len(df_events) == 0:
            continue
        
        df_events['family'] = df_events['event_key'].apply(map_event_to_family)
        core_events = df_events[df_events['family'].isin(CORE_FAMILIES_V6)]
        
        if len(core_events) == 0:
            continue
        
        families_present = set(core_events['family'].unique())
        has_cpi = any(f in ['CPI'] for f in families_present)
        has_jobs = any(f in ['Jobless Claims', 'NFP', 'Unemployment'] for f in families_present)
        
        if has_cpi and has_jobs:
            cluster_type = 'CPI+Jobs'
        elif has_cpi:
            cluster_type = 'CPI'
        elif has_jobs:
            cluster_type = 'Jobs'
        else:
            cluster_type = 'Rates-Core'
        
        tradable_dates.append({
            'date': str(movement_date),
            'movement_start_time': movement_start,
            'cluster_type': cluster_type,
            'n_events_core': len(core_events),
            'peak_pips': row['peak_pips'],
            'direction': row.get('direction', None)
        })
    
    df_tradable = pd.DataFrame(tradable_dates)
    
    if len(df_tradable) == 0:
        return pd.DataFrame(columns=['date', 'movement_start_time', 'cluster_type', 'n_events_core'])
    
    # Dédupliquer par date (garder mouvement le plus fort)
    df_tradable = df_tradable.sort_values('peak_pips', ascending=False)
    df_tradable = df_tradable.drop_duplicates(subset=['date'], keep='first')
    
    if sample_size and len(df_tradable) > sample_size:
        df_tradable = df_tradable.sample(n=sample_size, random_state=42)
    
    return df_tradable.sort_values('date')
from direction_router_v6 import CORE_FAMILIES_V6

def main():
    parser = argparse.ArgumentParser(description='Scan historique complet patterns')
    parser.add_argument('--min-date', type=str, default='2024-01-01', help='Date min')
    parser.add_argument('--max-date', type=str, default='2025-12-31', help='Date max')
    parser.add_argument('--trigger-z', type=float, default=1.0, help='Seuil trigger |z|')
    parser.add_argument('--theta', type=float, default=0.05, help='Seuil neutralité')
    parser.add_argument('--output-file', type=str, 
                       default='outputs/direction_router_test/patterns_detected.csv',
                       help='Fichier CSV de sortie')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("SCAN HISTORIQUE COMPLET - PATTERNS MULTI-WAVE")
    print("=" * 80)
    print()
    print(f"Configuration :")
    print(f"   - Période : {args.min_date} → {args.max_date}")
    print(f"   - Trigger |z| : ≥ {args.trigger_z}")
    print(f"   - Theta : {args.theta}")
    print(f"   - Fichier sortie : {args.output_file}")
    print()
    
    # Charger dépendances
    print("📊 Chargement dépendances...")
    # ⚠️ V8 : étendre période stats pour inclure 2022-2025
    stats_map, alpha_map = load_direction_router_dependencies(
        db_path=DB_PATH,
        alpha_file=None,
        horizon='1h',
        min_date=V8_MIN_STATS_DATE,
        max_date=V8_MAX_STATS_DATE
    )
    print(f"   ✅ Stats : {len(stats_map)} event_keys")
    print(f"   ✅ Alpha : {len(alpha_map)} weights")
    print()
    
    # Charger mouvements et identifier dates tradables
    print("📊 Identification dates tradables...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    movements_df = pd.read_csv(MOVEMENTS_FILE)
    movements_df['movement_start_time'] = pd.to_datetime(
        movements_df['movement_start_time'], 
        utc=True
    )
    
    # Identifier TOUTES les dates tradables (pas d'échantillonnage)
    # ⚠️ V8 : utiliser version full_day pour capturer events sur journée complète
    dates_df = identify_tradable_dates_full_day(
        conn,
        movements_df,
        sample_size=None,  # Pas d'échantillonnage
        min_date=args.min_date,
        max_date=args.max_date
    )
    print(f"   ✅ {len(dates_df)} dates tradables identifiées")
    print()
    
    # Scanner toutes les dates
    print("=" * 80)
    print("SCAN PATTERNS SUR TOUTES LES DATES")
    print("=" * 80)
    print()
    
    results = []
    n_processed = 0
    n_triggered = 0
    n_multi_wave = 0
    
    for idx, row in dates_df.iterrows():
        date_str = str(row['date'])
        cluster_type = row['cluster_type']
        movement_start = row['movement_start_time']
        
        if (idx + 1) % 50 == 0:
            print(f"[{idx+1}/{len(dates_df)}] Traité... ({n_multi_wave} multi-wave détectés)")
        
        # ⚠️ V8 : charger events sur TOUTE la journée (pas fenêtre [-4h, +30min])
        movement_date = row['date']
        day_start = pd.Timestamp(movement_date).tz_localize('UTC')
        day_end = day_start + timedelta(days=1)
        
        query_events = """
        SELECT 
            ts_utc,
            country,
            event_title,
            event_key,
            importance_n,
            actual,
            estimate,
            previous,
            forecast
        FROM events
        WHERE ts_utc >= ? 
          AND ts_utc < ?
          AND country IN ('US', 'EU', 'GB', 'DE')
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
        ORDER BY ts_utc ASC
        """
        
        try:
            events_df = conn.execute(query_events, [day_start, day_end]).df()
        except:
            continue
        
        if len(events_df) == 0:
            continue
        
        # Mapper vers familles
        from direction_router_v6 import map_event_to_family
        events_df['family'] = events_df['event_key'].apply(map_event_to_family)
        
        events_core = events_df[events_df['family'].isin(CORE_FAMILIES_V6)].copy()
        
        if len(events_core) == 0:
            continue
        
        # Préparer colonnes requises
        events_core = events_core.copy()
        if 'empirical_score' not in events_core.columns:
            events_core['empirical_score'] = 10.0
        if 'latency_median' not in events_core.columns:
            events_core['latency_median'] = 2.0
        
        try:
            # Appeler wrapper intégration
            result = calculate_cluster_impact_with_direction(
                cluster_events=events_core,
                stats_map=stats_map,
                alpha_map=alpha_map,
                trigger_z=args.trigger_z,
                theta=args.theta,
                first_leg_mode=True,
                use_linear_formula=True,
                movement_start_time=movement_start,
                conn=conn
            )
            
            n_processed += 1
            
            # Filtrer seulement les cas avec trigger
            if not result.get('has_trigger', False) or result.get('skipped', False):
                continue
            
            n_triggered += 1
            
            # Extraire métadonnées
            row_result = {
                'date': date_str,
                'cluster_type': cluster_type,
                'movement_start_time': str(movement_start),  # Patch C : stocker movement_start_time
                'direction_first_leg': result['direction_first_leg'],
                'pattern_type': result['pattern_type'],
                'impact_pips': result['impact_pips'],
                'trigger_strength': result['trigger_strength'],
                'direction_score': result['direction_score']
            }
            
            # Ajouter détails multi-wave si disponible
            if result.get('leg1') and result.get('leg2'):
                leg1 = result['leg1']
                leg2 = result['leg2']
                row_result.update({
                    'leg1_direction': leg1['direction'],
                    'leg1_amp_pips': leg1['amplitude_pips'],
                    'leg1_t_peak_min': leg1['t_peak_min'],
                    'leg2_direction': leg2['direction'],
                    'leg2_amp_pips': leg2['amplitude_pips'],
                    'leg2_t_peak_min': leg2['t_peak_min'],
                    'total_amp_pips': result.get('combined', {}).get('total_amp_pips', result['impact_pips'])
                })
                
                # Extraire retrace ratio, turn_pips_used et impact_total_pips_used depuis pattern_meta
                pattern_meta = result.get('pattern_meta', {})
                if pattern_meta and 'retrace_ratio' in pattern_meta:
                    row_result['retrace_ratio'] = pattern_meta['retrace_ratio']
                else:
                    row_result['retrace_ratio'] = None
                
                # Extraire turn_pips_used pour audit
                if pattern_meta and 'turn_pips_used' in pattern_meta:
                    row_result['turn_pips_used'] = pattern_meta['turn_pips_used']
                else:
                    row_result['turn_pips_used'] = None
                
                # Extraire impact_total_pips_used pour audit (comparer avec impact_pips)
                if pattern_meta and 'impact_total_pips_used' in pattern_meta:
                    impact_used = pattern_meta['impact_total_pips_used']
                    row_result['impact_total_pips_used'] = impact_used
                    row_result['impact_used_for_turn_pips'] = impact_used  # Alias clair pour V8
                else:
                    row_result['impact_total_pips_used'] = None
                    row_result['impact_used_for_turn_pips'] = None
                
                if result['pattern_type'] in {'double_wave', 'zig_zag'}:
                    n_multi_wave += 1
            else:
                row_result.update({
                    'leg1_direction': None,
                    'leg1_amp_pips': None,
                    'leg1_t_peak_min': None,
                    'leg2_direction': None,
                    'leg2_amp_pips': None,
                    'leg2_t_peak_min': None,
                    'total_amp_pips': result['impact_pips'],
                    'retrace_ratio': None
                })
            
            results.append(row_result)
            
        except Exception as e:
            # Ignorer les erreurs pour continuer le scan
            if (idx + 1) % 100 == 0:
                print(f"   ⚠️  Erreur sur {date_str}: {e}")
            continue
    
    # Créer DataFrame résultats
    df_results = pd.DataFrame(results)
    
    # Afficher résumé
    print()
    print("=" * 80)
    print("📊 RÉSUMÉ SCAN")
    print("=" * 80)
    print()
    print(f"   - Dates traitées : {n_processed}")
    print(f"   - Dates avec trigger : {n_triggered}")
    print(f"   - Multi-wave détectés : {n_multi_wave}")
    print()
    
    if len(df_results) > 0:
        print("   Répartition patterns :")
        print(df_results['pattern_type'].value_counts())
        print()
        
        # Filtrer multi-wave
        multi_wave = df_results[df_results['pattern_type'].isin(['double_wave', 'zig_zag'])]
        if len(multi_wave) > 0:
            print(f"   ✅ {len(multi_wave)} cas multi-wave détectés")
            print(f"      - double_wave : {len(multi_wave[multi_wave['pattern_type'] == 'double_wave'])}")
            print(f"      - zig_zag : {len(multi_wave[multi_wave['pattern_type'] == 'zig_zag'])}")
            print()
    
    # Sauvegarder CSV
    output_path = Path(SCRIPT_DIR) / args.output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False)
    print(f"💾 Résultats sauvegardés : {output_path}")
    print(f"   - Total lignes : {len(df_results)}")
    print()
    
    conn.close()

if __name__ == '__main__':
    main()
