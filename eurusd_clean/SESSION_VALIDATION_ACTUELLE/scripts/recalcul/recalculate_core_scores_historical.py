"""
Script de Recalcul des Scores pour les Noyaux Durs - Historique

Méthode validée (REF-006) :
1. Détecter mouvements forts depuis prix (dates + heures)
2. Comparer avec événements économiques (correspondance temporelle)
3. Filtrer événements SANS estimate (discours Fed, etc.)
4. Identifier noyau dur basé sur correspondance
5. Mesurer impact réel
6. Calculer statistiques par type noyau dur

Date : 2025-12-06
Référence : REF-006_METHODE_IDENTIFICATION_NOYAUX_DURS.md
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Tuple
import re
from tqdm import tqdm
import argparse

# Calculer PROJECT_ROOT (3 niveaux au-dessus depuis scripts/recalcul/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

# Paramètres
MIN_MOVEMENT_PIPS = 20.0  # Seuil minimum mouvement fort
WINDOW_MINUTES = 30  # Fenêtre de correspondance mouvement ↔ événement
MIN_SAMPLE_SIZE = 3  # Minimum occurrences pour calculer score
LOOKBACK_YEARS = 3  # 3 dernières années

# Patterns pour exclure événements sans estimate
EVENTS_WITHOUT_ESTIMATE_PATTERNS = [
    r'(?i)(speech|discours|statement|remarks|testimony|testifies)',
    r'(?i)(fed.*speech|ecb.*speech|boe.*speech)',
    r'(?i)(press conference|conference de presse)',
    r'(?i)(meeting minutes|compte-rendu)',
    r'(?i)(beige book|livre beige)',
]

def is_event_without_estimate(event: pd.Series) -> bool:
    """Vérifie si un événement ne peut pas avoir de surprise calculée"""
    event_key = str(event.get('event_key', '') or '')
    event_title = str(event.get('event_title', '') or '')
    estimate = event.get('estimate')
    forecast = event.get('forecast')
    previous = event.get('previous')
    
    has_valid_estimate = (
        (estimate is not None and not pd.isna(estimate) and estimate != 'nan') or
        (forecast is not None and not pd.isna(forecast) and forecast != 'nan') or
        (previous is not None and not pd.isna(previous) and previous != 'nan')
    )
    
    if not has_valid_estimate:
        return True
    
    text_to_check = f"{event_key} {event_title}".lower()
    for pattern in EVENTS_WITHOUT_ESTIMATE_PATTERNS:
        if re.search(pattern, text_to_check):
            return True
    
    return False

def detect_strong_movements(
    conn: duckdb.DuckDBPyConnection,
    date_str: str,
    min_pips: float = MIN_MOVEMENT_PIPS
) -> List[Dict]:
    """Détecte les mouvements forts depuis les prix pour une date"""
    movements = []
    
    try:
        date_dt = pd.to_datetime(date_str)
        window_start = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=0)))
        window_end = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=20, minute=0)))
        
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE DATE(datetime) = '{date_str}'
          AND datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
          AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query).df()
        
        if df_prices.empty:
            return movements
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        baseline_time = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=30)))
        prices_at_baseline = df_prices[df_prices.index >= baseline_time]
        
        if prices_at_baseline.empty:
            baseline_time = df_prices.index[0]
            prices_at_baseline = df_prices
        
        baseline_price = prices_at_baseline.iloc[0]['open']
        
        current_high = baseline_price
        current_low = baseline_price
        movement_start = None
        peak_time = None
        direction = None
        
        for idx, row in prices_at_baseline.iterrows():
            high_pips = (row['high'] - baseline_price) * 10000
            low_pips = (baseline_price - row['low']) * 10000
            
            if movement_start is None:
                if high_pips >= 5.0 or low_pips >= 5.0:
                    movement_start = idx
                    if high_pips > low_pips:
                        direction = 'UP'
                        current_high = row['high']
                        peak_time = idx
                    else:
                        direction = 'DOWN'
                        current_low = row['low']
                        peak_time = idx
            
            if movement_start is not None:
                if direction == 'UP':
                    if row['high'] > current_high:
                        current_high = row['high']
                        peak_time = idx
                else:
                    if row['low'] < current_low:
                        current_low = row['low']
                        peak_time = idx
        
        if movement_start is not None and peak_time is not None:
            if direction == 'UP':
                impact_pips = (current_high - baseline_price) * 10000
            else:
                impact_pips = (baseline_price - current_low) * 10000
            
            if impact_pips >= min_pips:
                movements.append({
                    'start_time': movement_start,
                    'peak_time': peak_time,
                    'impact_pips': impact_pips,
                    'direction': direction,
                    'baseline_price': baseline_price
                })
    
    except Exception:
        pass
    
    return movements

def find_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement: Dict,
    window_minutes: int = WINDOW_MINUTES
) -> pd.DataFrame:
    """Trouve les événements correspondant à un mouvement (avec estimate)"""
    start_time = movement['start_time']
    window_start = start_time - timedelta(minutes=window_minutes)
    window_end = start_time + timedelta(minutes=window_minutes)
    
    query = f"""
    SELECT 
        e.ts_utc,
        e.country,
        e.event_key,
        e.event_title,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key
    WHERE e.ts_utc >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.ts_utc <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.country IN ('US', 'EU', 'DE', 'GB')
      AND e.importance_n >= 2
    ORDER BY e.ts_utc ASC
    """
    
    df_events = conn.execute(query).df()
    
    if df_events.empty:
        return pd.DataFrame()
    
    # Filtrer événements SANS estimate
    valid_events = []
    for idx, event in df_events.iterrows():
        if not is_event_without_estimate(event):
            valid_events.append(idx)
    
    if not valid_events:
        return pd.DataFrame()
    
    return df_events.loc[valid_events].copy()

def identify_core_type_from_events(events: pd.DataFrame) -> Tuple[str, List[str]]:
    """Identifie le type de noyau dur depuis les événements"""
    if events.empty:
        return 'GENERIC', []
    
    CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
    NFP_PATTERN = r'(?i)(non farm payrolls|nonfarm)'
    JOBLESS_PATTERN = r'(?i)(jobless claims|unemployment claims|initial jobless|continuing jobless)'
    PCE_PATTERN = r'(?i)(pce prices|personal consumption expenditure|core pce)'
    GDP_PATTERN = r'(?i)(gdp|gross domestic product)'
    
    cpi_count = 0
    nfp_count = 0
    jobless_count = 0
    pce_count = 0
    gdp_count = 0
    
    cpi_keys = []
    nfp_keys = []
    jobless_keys = []
    pce_keys = []
    gdp_keys = []
    
    for _, event in events.iterrows():
        event_key = str(event.get('event_key', '') or '').lower()
        event_title = str(event.get('event_title', '') or '').lower()
        text = f"{event_key} {event_title}"
        
        if re.search(CPI_PATTERN, text):
            cpi_count += 1
            cpi_keys.append(event.get('event_key', ''))
        if re.search(NFP_PATTERN, text):
            nfp_count += 1
            nfp_keys.append(event.get('event_key', ''))
        if re.search(JOBLESS_PATTERN, text):
            jobless_count += 1
            jobless_keys.append(event.get('event_key', ''))
        if re.search(PCE_PATTERN, text):
            pce_count += 1
            pce_keys.append(event.get('event_key', ''))
        if re.search(GDP_PATTERN, text):
            gdp_count += 1
            gdp_keys.append(event.get('event_key', ''))
    
    if cpi_count >= 2:
        return 'CPI', cpi_keys
    elif nfp_count >= 1:
        return 'NFP', nfp_keys
    elif jobless_count >= 2 and pce_count >= 1:
        return 'JOBLESS_PCE', jobless_keys + pce_keys
    elif gdp_count >= 2:
        return 'GDP', gdp_keys
    elif jobless_count >= 2:
        return 'JOBLESS', jobless_keys
    elif pce_count >= 1:
        return 'PCE', pce_keys
    else:
        return 'GENERIC', events['event_key'].tolist()

def calculate_empirical_score_current(avg_movement: float, p80_movement: float, sample_size: int) -> float:
    """Formule actuelle : 50% avg + 50% p80"""
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = base_score * robustness
    return min(100.0, score)

def recalculate_core_scores_historical(
    start_date: str = None,
    end_date: str = None,
    min_movement_pips: float = MIN_MOVEMENT_PIPS,
    lookback_years: int = LOOKBACK_YEARS,
    min_sample_size: int = MIN_SAMPLE_SIZE,
    dry_run: bool = False
):
    """
    Recalcule les scores pour les noyaux durs sur historique
    
    Méthode validée (REF-006) :
    1. Détecter mouvements forts depuis prix
    2. Comparer avec événements (avec estimate)
    3. Identifier noyau dur
    4. Mesurer impact réel
    5. Calculer statistiques par type
    """
    print("="*100)
    print("RECALCUL SCORES NOYAUX DURS - HISTORIQUE")
    print("="*100)
    print()
    print("Méthode validée (REF-006) :")
    print("  1. Détecter mouvements forts depuis prix")
    print("  2. Comparer avec événements (avec estimate)")
    print("  3. Filtrer événements SANS estimate (discours, etc.)")
    print("  4. Identifier noyau dur")
    print("  5. Mesurer impact réel")
    print("  6. Calculer statistiques par type")
    print()
    
    if end_date is None:
        end_date_dt = datetime.now()
    else:
        end_date_dt = pd.to_datetime(end_date)
    
    if start_date is None:
        start_date_dt = end_date_dt - timedelta(days=lookback_years * 365)
    else:
        start_date_dt = pd.to_datetime(start_date)
    
    print(f"Période : {start_date_dt.date()} à {end_date_dt.date()}")
    print(f"Seuil mouvement fort : {min_movement_pips} pips")
    print(f"Mode : {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # 1. Scanner toutes les dates
    print("1. SCAN MOUVEMENTS FORTS")
    print("-"*100)
    print()
    
    all_movements = []
    current_date = start_date_dt
    
    date_list = []
    while current_date <= end_date_dt:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    print(f"Scan de {len(date_list)} dates...")
    
    for date_str in tqdm(date_list, desc="Détection mouvements"):
        movements = detect_strong_movements(conn, date_str, min_pips=min_movement_pips)
        for movement in movements:
            movement['date'] = date_str
            all_movements.append(movement)
    
    print(f"✅ {len(all_movements)} mouvements forts détectés")
    print()
    
    if not all_movements:
        print("❌ Aucun mouvement fort détecté")
        conn.close()
        return
    
    # 2. Identifier noyaux durs pour chaque mouvement
    print("2. IDENTIFICATION NOYAUX DURS")
    print("-"*100)
    print()
    
    core_data = []
    
    for movement in tqdm(all_movements, desc="Identification noyaux durs"):
        date_str = movement['date']
        
        # Trouver événements correspondants
        events = find_events_for_movement(conn, movement, window_minutes=WINDOW_MINUTES)
        
        if events.empty:
            continue
        
        # Identifier noyau dur
        core_type, core_keys = identify_core_type_from_events(events)
        
        # Anchor time = événement US HIGH le plus important
        us_high_events = events[
            (events['country'] == 'US') &
            (events['importance_n'] == 3) &
            (events['event_key'].isin(core_keys))
        ]
        
        if not us_high_events.empty:
            if 'empirical_score' in us_high_events.columns:
                us_high_events = us_high_events.sort_values('empirical_score', ascending=False)
            anchor_time = pd.to_datetime(us_high_events.iloc[0]['ts_utc'])
        else:
            core_events = events[events['event_key'].isin(core_keys)]
            if not core_events.empty:
                anchor_time = pd.to_datetime(core_events.iloc[0]['ts_utc'])
            else:
                anchor_time = pd.to_datetime(events.iloc[0]['ts_utc'])
        
        # Mesurer impact réel (déjà dans movement['impact_pips'])
        impact_real = movement['impact_pips']
        
        if impact_real > 0:
            core_data.append({
                'date': date_str,
                'anchor_time': anchor_time,
                'core_type': core_type,
                'country': us_high_events.iloc[0]['country'] if not us_high_events.empty else events.iloc[0]['country'],
                'impact_pips': impact_real,
                'direction': movement['direction'],
                'n_events': len(events),
                'n_core_events': len(core_keys)
            })
    
    if not core_data:
        print("❌ Aucun noyau dur identifié")
        conn.close()
        return
    
    df_core_data = pd.DataFrame(core_data)
    print(f"✅ {len(df_core_data)} dates avec noyaux durs identifiés")
    print()
    
    # 3. Grouper par type noyau dur et calculer statistiques
    print("3. CALCUL SCORES PAR TYPE NOYAU DUR")
    print("-"*100)
    print()
    
    results = []
    
    for (core_type, country), group in df_core_data.groupby(['core_type', 'country']):
        if len(group) < min_sample_size:
            continue
        
        impacts = group['impact_pips'].values
        
        avg = np.mean(impacts)
        median = np.median(impacts)
        p80 = np.percentile(impacts, 80)
        std = np.std(impacts)
        min_impact = np.min(impacts)
        max_impact = np.max(impacts)
        
        score_empirical = calculate_empirical_score_current(avg, p80, len(impacts))
        
        pattern_types = group['direction'].value_counts().to_dict()
        
        results.append({
            'core_type': core_type,
            'country': country,
            'empirical_score': score_empirical,
            'avg_impact_pips': avg,
            'p80_impact_pips': p80,
            'median_impact_pips': median,
            'std_impact_pips': std,
            'min_impact_pips': min_impact,
            'max_impact_pips': max_impact,
            'sample_size': len(impacts),
            'pattern_distribution': str(pattern_types)
        })
        
        print(f"✅ {core_type} ({country}) : {len(impacts)} occurrences, score: {score_empirical:.2f}, avg: {avg:.2f} pips, p80: {p80:.2f} pips")
    
    if not results:
        print("❌ Aucun score calculé (sample_size insuffisant)")
        conn.close()
        return
    
    df_results = pd.DataFrame(results)
    print()
    print(f"✅ {len(df_results)} scores calculés")
    print()
    
    # 4. Afficher statistiques
    print("4. STATISTIQUES")
    print("-"*100)
    print()
    
    print(f"Scores calculés :")
    print(f"  Moyenne : {df_results['empirical_score'].mean():.2f}")
    print(f"  Médiane : {df_results['empirical_score'].median():.2f}")
    print(f"  Min : {df_results['empirical_score'].min():.2f}")
    print(f"  Max : {df_results['empirical_score'].max():.2f}")
    print()
    
    print("Top 10 noyaux durs par score :")
    for _, row in df_results.nlargest(10, 'empirical_score').iterrows():
        print(f"  {row['core_type']:20s} ({row['country']:2s}) : {row['empirical_score']:6.2f} (n={row['sample_size']:3d}, avg={row['avg_impact_pips']:6.2f} pips)")
    print()
    
    # 5. Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / f'core_scores_historical_{start_date_dt.date()}_{end_date_dt.date()}.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    # 6. Créer/mettre à jour table core_scores
    if not dry_run:
        print("5. MISE À JOUR BASE DE DONNÉES")
        print("-"*100)
        print()
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS core_scores (
                core_type VARCHAR,
                country VARCHAR,
                empirical_score DOUBLE,
                avg_impact_pips DOUBLE,
                p80_impact_pips DOUBLE,
                median_impact_pips DOUBLE,
                std_impact_pips DOUBLE,
                min_impact_pips DOUBLE,
                max_impact_pips DOUBLE,
                sample_size INTEGER,
                pattern_distribution VARCHAR,
                created_at TIMESTAMP,
                PRIMARY KEY (core_type, country)
            )
        """)
        
        for _, row in df_results.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO core_scores (
                    core_type, country, empirical_score,
                    avg_impact_pips, p80_impact_pips, median_impact_pips,
                    std_impact_pips, min_impact_pips, max_impact_pips,
                    sample_size, pattern_distribution, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                row['core_type'],
                row['country'],
                round(row['empirical_score'], 6),
                round(row['avg_impact_pips'], 6),
                round(row['p80_impact_pips'], 6),
                round(row['median_impact_pips'], 6),
                round(row['std_impact_pips'], 6),
                round(row['min_impact_pips'], 6),
                round(row['max_impact_pips'], 6),
                row['sample_size'],
                row['pattern_distribution'],
                datetime.now()
            ])
        
        print(f"✅ {len(df_results)} scores mis à jour dans core_scores")
    else:
        print("5. DRY RUN - Pas de mise à jour DB")
        print("-"*100)
        print()
        print("✅ Mode dry run : aucune modification de la DB")
    
    conn.close()
    
    print()
    print("="*100)
    print("TERMINÉ")
    print("="*100)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recalcul scores noyaux durs historiques')
    parser.add_argument('--start-date', type=str, default=None, help='Date début (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None, help='Date fin (YYYY-MM-DD)')
    parser.add_argument('--min-movement-pips', type=float, default=MIN_MOVEMENT_PIPS, help='Seuil mouvement fort')
    parser.add_argument('--lookback-years', type=int, default=LOOKBACK_YEARS, help='Années lookback')
    parser.add_argument('--min-sample-size', type=int, default=MIN_SAMPLE_SIZE, help='Minimum occurrences')
    parser.add_argument('--dry-run', action='store_true', help='Mode dry run')
    
    args = parser.parse_args()
    
    recalculate_core_scores_historical(
        start_date=args.start_date,
        end_date=args.end_date,
        min_movement_pips=args.min_movement_pips,
        lookback_years=args.lookback_years,
        min_sample_size=args.min_sample_size,
        dry_run=args.dry_run
    )
