#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calcul de la direction de la première jambe (1h post-release)

Objectif : Créer un label directionnel cohérent avec ce que prédit le router.
Le router prédit la direction de la première jambe post-release, pas la direction
totale d'un mouvement multi-wave.

Définition :
- t0 = timestamp du premier event core déclencheur (ou premier event core de la fenêtre)
- Δpips_1h = price(t0+1h) - price(t0)
- UP si Δpips_1h > 0, DOWN si Δpips_1h < 0, NEUTRAL si |Δpips_1h| < ε
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
import argparse
import random

# Ajouter le répertoire racine au path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from direction_router_v6 import (
    map_event_to_family,
    CORE_FAMILIES_V6,
    DEFAULT_TRIGGER_Z,
    load_direction_router_dependencies
)
from test_direction_router_batch import (
    identify_tradable_dates,
    load_events_for_window,
    DB_PATH,
    MOVEMENTS_FILE,
    LOOKBACK_HOURS,
    LOOKAHEAD_MINUTES,
    ALPHA_WEIGHTS_FILE
)

# ============================================================================
# CONFIGURATION
# ============================================================================

FIRST_LEG_HORIZON_HOURS = 1.0  # Horizon pour première jambe
NEUTRAL_THRESHOLD_PIPS = 5.0  # Seuil pour NEUTRAL (pips)

# ============================================================================
# CHARGEMENT PRIX
# ============================================================================

def find_price_table(db_path: Path) -> Optional[str]:
    """Trouve la table de prix disponible"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    tables_to_try = [
        'prices_finnhub_m1',
        'prices_finnhub_h1',
        'prices_bern',
        'prices_1m',
        'prices_h1'
    ]
    
    for table in tables_to_try:
        try:
            result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            if result and result[0] > 0:
                conn.close()
                return table
        except:
            continue
    
    conn.close()
    return None

def get_price_at_time(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    timestamp: pd.Timestamp,
    tolerance_minutes: int = 5
) -> Optional[float]:
    """
    Récupère le prix (close) à un timestamp donné.
    
    Args:
        conn: Connexion DuckDB
        table_name: Nom de la table de prix
        timestamp: Timestamp cible
        tolerance_minutes: Tolérance en minutes pour trouver le prix le plus proche
    
    Returns:
        Prix (close) ou None si non trouvé
    """
    # Convertir timestamp en UTC si nécessaire
    if timestamp.tz is None:
        timestamp_utc = timestamp.tz_localize('UTC')
    else:
        timestamp_utc = timestamp.tz_convert('UTC')
    
    window_start = timestamp_utc - timedelta(minutes=tolerance_minutes)
    window_end = timestamp_utc + timedelta(minutes=tolerance_minutes)
    
    # Vérifier structure de la table (datetime peut être ts_utc ou datetime)
    try:
        # Essayer avec datetime d'abord
        query = f"""
        SELECT datetime, close
        FROM {table_name}
        WHERE datetime >= ? 
          AND datetime <= ?
        ORDER BY ABS(EXTRACT(EPOCH FROM (datetime - ?)))
        LIMIT 1
        """
        
        df = conn.execute(query, [window_start, window_end, timestamp_utc]).df()
        
        if len(df) > 0:
            return float(df.iloc[0]['close'])
        
        # Si pas trouvé, essayer avec ts_utc
        query = f"""
        SELECT ts_utc as datetime, close
        FROM {table_name}
        WHERE ts_utc >= ? 
          AND ts_utc <= ?
        ORDER BY ABS(EXTRACT(EPOCH FROM (ts_utc - ?)))
        LIMIT 1
        """
        
        df = conn.execute(query, [window_start, window_end, timestamp_utc]).df()
        
        if len(df) > 0:
            return float(df.iloc[0]['close'])
            
    except Exception as e:
        # Essayer sans timezone dans la requête
        try:
            timestamp_naive = timestamp_utc.tz_localize(None) if timestamp_utc.tz else timestamp_utc
            window_start_naive = window_start.tz_localize(None) if window_start.tz else window_start
            window_end_naive = window_end.tz_localize(None) if window_end.tz else window_end
            
            query = f"""
            SELECT datetime, close
            FROM {table_name}
            WHERE datetime >= ? 
              AND datetime <= ?
            ORDER BY ABS(EXTRACT(EPOCH FROM (datetime - ?)))
            LIMIT 1
            """
            
            df = conn.execute(query, [window_start_naive, window_end_naive, timestamp_naive]).df()
            
            if len(df) > 0:
                return float(df.iloc[0]['close'])
        except Exception as e2:
            # Dernier essai : requête simple avec CAST
            try:
                query = f"""
                SELECT datetime, close
                FROM {table_name}
                WHERE datetime >= CAST(? AS TIMESTAMP)
                  AND datetime <= CAST(? AS TIMESTAMP)
                ORDER BY datetime
                LIMIT 1
                """
                df = conn.execute(query, [str(window_start_naive), str(window_end_naive)]).df()
                if len(df) > 0:
                    return float(df.iloc[0]['close'])
            except:
                pass
    
    return None

# ============================================================================
# CALCUL DIRECTION PREMIÈRE JAMBE
# ============================================================================

def find_trigger_event_timestamp(
    events_df: pd.DataFrame,
    stats_map: dict,
    trigger_z: float = DEFAULT_TRIGGER_Z
) -> Optional[pd.Timestamp]:
    """
    Trouve le timestamp du premier event déclencheur (|surprise_z| >= trigger_z).
    
    Utilise les stats réelles pour calculer surprise_z.
    Si aucun trigger, retourne le timestamp du premier event core.
    """
    from direction_router_v6 import normalize_event_key
    
    # Filtrer core families
    events_core = events_df[events_df['family'].isin(CORE_FAMILIES_V6)].copy()
    
    if len(events_core) == 0:
        return None
    
    # Calculer surprise_z avec stats réelles
    events_core['surprise'] = events_core['actual'] - events_core['estimate']
    events_core['surprise_z'] = None
    
    SIGMA_FLOOR = 0.1
    
    for idx, row in events_core.iterrows():
        event_key_norm = normalize_event_key(row['event_key'])
        
        if event_key_norm in stats_map:
            mu, sigma = stats_map[event_key_norm]
            sigma = max(sigma, SIGMA_FLOOR)
            
            if pd.notna(row['surprise']) and sigma > 0:
                surprise_z = (row['surprise'] - mu) / sigma
                events_core.at[idx, 'surprise_z'] = surprise_z
    
    # Chercher trigger (|surprise_z| >= trigger_z)
    # Filtrer d'abord les NaN avant d'appeler abs()
    events_core['abs_surprise_z'] = events_core['surprise_z'].apply(
        lambda x: abs(x) if pd.notna(x) and x is not None else None
    )
    triggers = events_core[
        (events_core['abs_surprise_z'].notna()) & 
        (events_core['abs_surprise_z'] >= trigger_z)
    ].copy()
    
    if len(triggers) > 0:
        # Prendre le premier trigger chronologiquement
        triggers = triggers.sort_values('ts_utc')
        return pd.to_datetime(triggers.iloc[0]['ts_utc'])
    
    # Si aucun trigger, prendre le premier event core avec surprise_z valide
    events_with_z = events_core[events_core['surprise_z'].notna()].copy()
    if len(events_with_z) > 0:
        events_with_z = events_with_z.sort_values('ts_utc')
        return pd.to_datetime(events_with_z.iloc[0]['ts_utc'])
    
    # Dernier recours : premier event core chronologiquement
    events_core = events_core.sort_values('ts_utc')
    return pd.to_datetime(events_core.iloc[0]['ts_utc'])

def load_prices_batch(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    timestamps: list
) -> dict:
    """
    Charge les prix en batch pour une liste de timestamps.
    
    Returns:
        Dict {timestamp: price} pour les timestamps trouvés
    """
    if len(timestamps) == 0:
        return {}
    
    # Créer DataFrame des timestamps requis et harmoniser types
    req_df = pd.DataFrame({"t_req": sorted(set(timestamps))})
    req_df["t_req"] = pd.to_datetime(req_df["t_req"], utc=True).astype('datetime64[ns, UTC]')
    
    # Fenêtre SQL batch avec marge
    t_min = req_df["t_req"].min() - pd.Timedelta(minutes=10)
    t_max = req_df["t_req"].max() + pd.Timedelta(minutes=10)
    
    # Requête batch
    try:
        prices_df = conn.execute(f"""
            SELECT ts_utc AS ts, close
            FROM {table_name}
            WHERE ts_utc BETWEEN ? AND ?
            ORDER BY ts_utc
        """, [t_min, t_max]).df()
    except:
        # Fallback si ts_utc n'existe pas, essayer datetime
        try:
            prices_df = conn.execute(f"""
                SELECT datetime AS ts, close
                FROM {table_name}
                WHERE datetime BETWEEN ? AND ?
                ORDER BY datetime
            """, [t_min, t_max]).df()
        except:
            return {}
    
    if len(prices_df) == 0:
        return {}
    
    # Harmoniser types datetime (convertir en ns pour compatibilité)
    prices_df["ts"] = pd.to_datetime(prices_df["ts"], utc=True).astype('datetime64[ns, UTC]')
    prices_df = prices_df.sort_values("ts")
    
    # S'assurer que req_df est aussi en ns
    req_df["t_req"] = req_df["t_req"].astype('datetime64[ns, UTC]')
    
    # Matching avec merge_asof
    matched = pd.merge_asof(
        req_df, prices_df,
        left_on="t_req", right_on="ts",
        direction="backward",
        tolerance=pd.Timedelta(minutes=5)
    )
    
    # Vérifier les manquants
    if matched["close"].isna().any():
        missing = matched[matched["close"].isna()]
        print(f"   ⚠️  WARNING: {len(missing)} timestamps sans prix trouvé")
    
    # Construire dict
    price_map = {}
    for _, row in matched.iterrows():
        if pd.notna(row["close"]):
            price_map[row["t_req"]] = row["close"]
    
    return price_map

def calculate_first_leg_direction(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    date_str: str,
    movement_start_time: pd.Timestamp,
    stats_map: dict,
    price_map: dict,
    trigger_z: float = DEFAULT_TRIGGER_Z,
    debug: bool = False
) -> Optional[Tuple[str, float, pd.Timestamp, Optional[float], Optional[float]]]:
    """
    Calcule la direction de la première jambe pour une date tradable.
    
    Args:
        price_map: Dict {timestamp: price} pré-chargé en batch
    
    Returns:
        Tuple (direction, delta_pips, t0_event, price_t0, price_t1) ou None si erreur
    """
    # Charger events dans fenêtre
    events_df = load_events_for_window(conn, movement_start_time)
    
    if len(events_df) == 0:
        return None
    
    # Trouver t0 (timestamp du premier event déclencheur)
    t0 = find_trigger_event_timestamp(events_df, stats_map, trigger_z)
    
    if t0 is None:
        return None
    
    # Calculer t1 = t0 + 1h
    t1 = t0 + timedelta(hours=FIRST_LEG_HORIZON_HOURS)
    
    # Récupérer prix depuis price_map
    price_t0 = price_map.get(t0)
    price_t1 = price_map.get(t1)
    
    if debug:
        print(f"         DEBUG: t0={t0}, p0={price_t0}, t1={t1}, p1={price_t1}")
    
    if price_t0 is None or price_t1 is None:
        return None
    
    # Calculer Δpips (convertir différence de prix en pips : multiplier par 10000)
    delta_price = price_t1 - price_t0
    delta_pips = delta_price * 10000.0
    
    # Déterminer direction
    if abs(delta_pips) < NEUTRAL_THRESHOLD_PIPS:
        direction = 'NEUTRAL'
    elif delta_pips > 0:
        direction = 'UP'
    else:
        direction = 'DOWN'
    
    return (direction, delta_pips, t0, price_t0, price_t1)

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Calcul direction première jambe (1h post-release)')
    parser.add_argument('--sample-size', type=int, default=None, help='Taille échantillon dates (défaut: toutes)')
    parser.add_argument('--seed', type=int, default=42, help='Seed pour random sampling')
    parser.add_argument('--debug', action='store_true', help='Afficher debug détaillé pour 5 premières dates')
    args = parser.parse_args()
    
    print("=" * 80)
    print("CALCUL DIRECTION PREMIÈRE JAMBE (1h post-release)")
    print("=" * 80)
    print()
    
    if args.sample_size:
        print(f"📊 Mode échantillon : {args.sample_size} dates (seed={args.seed})")
    else:
        print("📊 Mode complet : toutes les dates")
    print()
    
    # Charger mouvements
    print("📊 Chargement mouvements...")
    if not MOVEMENTS_FILE.exists():
        print(f"   ⚠️  Fichier non trouvé : {MOVEMENTS_FILE}")
        return
    
    movements_df = pd.read_csv(MOVEMENTS_FILE)
    movements_df['movement_start_time'] = pd.to_datetime(movements_df['movement_start_time'], utc=True)
    print(f"   ✅ {len(movements_df)} mouvements chargés")
    print()
    
    # Trouver table de prix
    print("📊 Recherche table de prix...")
    table_name = find_price_table(DB_PATH)
    if table_name is None:
        print("   ❌ Aucune table de prix trouvée")
        return
    print(f"   ✅ Table : {table_name}")
    print()
    
    # Identifier dates tradables
    print("📊 Identification dates tradables...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        dates_df = identify_tradable_dates(
            conn,
            movements_df,
            sample_size=None  # On échantillonne après
        )
    finally:
        conn.close()
    
    print(f"   ✅ {len(dates_df)} dates tradables identifiées")
    
    # Échantillonner si demandé
    if args.sample_size is not None and args.sample_size < len(dates_df):
        random.seed(args.seed)
        indices = random.sample(range(len(dates_df)), args.sample_size)
        dates_df = dates_df.iloc[indices].reset_index(drop=True)
        print(f"   📊 Échantillon : {len(dates_df)} dates sélectionnées")
    
    print()
    
    # Charger stats pour calculer surprise_z
    print("📊 Chargement stats...")
    stats_map, _ = load_direction_router_dependencies(
        db_path=DB_PATH,
        alpha_file=ALPHA_WEIGHTS_FILE,
        horizon='1h'
    )
    print(f"   ✅ {len(stats_map)} event_keys avec stats")
    print()
    
    # Calculer direction première jambe pour chaque date
    print("=" * 80)
    print("CALCUL DIRECTION PREMIÈRE JAMBE")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Étape 1 : Collecter tous les t0 nécessaires
    print("📊 Étape 1/3 : Collecte des timestamps t0...")
    t0_list = []
    date_to_movement = {}
    
    try:
        for idx, row in dates_df.iterrows():
            date_str = str(row['date'])
            movement_start = row['movement_start_time']
            
            # Charger events pour trouver t0
            events_df = load_events_for_window(conn, movement_start)
            if len(events_df) == 0:
                continue
            
            t0 = find_trigger_event_timestamp(events_df, stats_map, DEFAULT_TRIGGER_Z)
            if t0 is None:
                continue
            
            t0_list.append(t0)
            t0_list.append(t0 + timedelta(hours=FIRST_LEG_HORIZON_HOURS))
            date_to_movement[date_str] = {
                'movement_start': movement_start,
                't0': t0,
                'cluster_type': row['cluster_type'],
                'peak_pips': row.get('peak_pips', None)
            }
        
        print(f"   ✅ {len(date_to_movement)} dates avec t0 trouvé")
        print(f"   ✅ {len(t0_list)} timestamps à charger")
        print()
        
        # Étape 2 : Charger prix en batch
        print("📊 Étape 2/3 : Chargement prix en batch...")
        price_map = load_prices_batch(conn, table_name, t0_list)
        print(f"   ✅ {len(price_map)} prix chargés")
        print()
        
        # Étape 3 : Calculer directions avec price_map
        print("📊 Étape 3/3 : Calcul directions...")
        print()
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la préparation : {e}")
        conn.close()
        return
    
    results = []
    debug_count = 0
    
    try:
        for idx, (date_str, info) in enumerate(date_to_movement.items(), 1):
            cluster_type = info['cluster_type']
            movement_start = info['movement_start']
            t0 = info['t0']
            
            print(f"[{idx}/{len(date_to_movement)}] {date_str} ({cluster_type})... ", end='', flush=True)
            
            # Calculer t1
            t1 = t0 + timedelta(hours=FIRST_LEG_HORIZON_HOURS)
            
            # Récupérer prix depuis price_map
            price_t0 = price_map.get(t0)
            price_t1 = price_map.get(t1)
            
            if price_t0 is None or price_t1 is None:
                print("⚠️  Prix manquant")
                continue
            
            # Calculer Δpips
            delta_price = price_t1 - price_t0
            delta_pips = delta_price * 10000.0
            
            # Déterminer direction
            if abs(delta_pips) < NEUTRAL_THRESHOLD_PIPS:
                direction = 'NEUTRAL'
            elif delta_pips > 0:
                direction = 'UP'
            else:
                direction = 'DOWN'
            
            # Debug pour 5 premières dates
            if args.debug and debug_count < 5:
                print()
                print(f"      DEBUG #{debug_count+1}:")
                print(f"         t0: {t0}")
                print(f"         p0: {price_t0}")
                print(f"         t1: {t1}")
                print(f"         p1: {price_t1}")
                print(f"         delta_price: {delta_price:.6f}")
                print(f"         delta_pips: {delta_pips:.1f}")
                print(f"         direction: {direction}")
                print()
                debug_count += 1
            
            results.append({
                'date': date_str,
                't0_event': t0.isoformat(),
                'direction_first_leg_1h': direction,
                'delta_pips_1h': delta_pips,
                'type_cluster': cluster_type,
                'movement_start_time': movement_start.isoformat(),
                'peak_pips': info['peak_pips']
            })
            
            print(f"✅ {direction} ({delta_pips:+.1f} pips)")
            
            # Debug pour 5 premières dates
            if args.debug and debug_count < 5:
                print()
                print(f"      DEBUG #{debug_count+1}:")
                print(f"         t0: {t0}")
                print(f"         p0: {price_t0}")
                print(f"         t1: {t0 + timedelta(hours=FIRST_LEG_HORIZON_HOURS)}")
                print(f"         p1: {price_t1}")
                print(f"         delta_price: {(price_t1 - price_t0):.6f}")
                print(f"         delta_pips: {delta_pips:.1f}")
                print(f"         direction: {direction}")
                print()
                debug_count += 1
            
            results.append({
                'date': date_str,
                't0_event': t0.isoformat(),
                'direction_first_leg_1h': direction,
                'delta_pips_1h': delta_pips,
                'type_cluster': cluster_type,
                'movement_start_time': movement_start.isoformat(),
                'peak_pips': row.get('peak_pips', None)
            })
            
            print(f"✅ {direction} ({delta_pips:+.1f} pips)")
    
    finally:
        conn.close()
    
    if len(results) == 0:
        print("❌ Aucun résultat")
        return
    
    # Sauvegarder résultats
    df_results = pd.DataFrame(results)
    
    output_dir = Path(__file__).parent.parent / 'outputs' / 'direction_router_test'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'first_leg_directions.csv'
    df_results.to_csv(output_file, index=False)
    
    print()
    print("=" * 80)
    print("📊 RÉSULTATS")
    print("=" * 80)
    print()
    print(f"   - Dates traitées : {len(df_results)}")
    print(f"   - UP : {len(df_results[df_results['direction_first_leg_1h'] == 'UP'])}")
    print(f"   - DOWN : {len(df_results[df_results['direction_first_leg_1h'] == 'DOWN'])}")
    print(f"   - NEUTRAL : {len(df_results[df_results['direction_first_leg_1h'] == 'NEUTRAL'])}")
    print()
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()

if __name__ == '__main__':
    main()

