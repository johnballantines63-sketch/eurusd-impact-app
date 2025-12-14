"""
Script de Validation : Identification des Noyaux Durs (V2)

NOUVELLE APPROCHE :
1. Détecter mouvements forts depuis les prix (dates + heures)
2. Comparer avec événements économiques (correspondance temporelle)
3. Filtrer événements SANS estimate (discours Fed, etc.) - pas de surprise possible
4. Identifier noyau dur basé sur correspondance mouvement ↔ événements

Date : 2025-12-06
Référence : Problème 2025-05-29 (cluster 18:00 sélectionné au lieu de 14:30)
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

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

# Paramètres
MIN_MOVEMENT_PIPS = 20.0  # Seuil minimum mouvement fort
WINDOW_MINUTES = 30  # Fenêtre de correspondance mouvement ↔ événement
MIN_EVENTS_FOR_CORE = 1  # Minimum événements pour noyau dur

# Patterns pour exclure événements sans estimate (discours, etc.)
EVENTS_WITHOUT_ESTIMATE_PATTERNS = [
    r'(?i)(speech|discours|statement|remarks|testimony|testifies)',
    r'(?i)(fed.*speech|ecb.*speech|boe.*speech)',
    r'(?i)(press conference|conference de presse)',
    r'(?i)(meeting minutes|compte-rendu)',
    r'(?i)(beige book|livre beige)',
]

def is_event_without_estimate(event: pd.Series) -> bool:
    """
    Vérifie si un événement ne peut pas avoir de surprise calculée
    
    Critères :
    1. Pas d'estimate (estimate, forecast, previous tous None/NaN)
    2. Pattern correspond à discours/statement (même si estimate existe)
    3. Événements avec estimate=NaN mais forecast/previous aussi NaN
    
    Args:
        event: Série pandas avec colonnes event_key, event_title, estimate, forecast, previous
    
    Returns:
        True si événement sans estimate (à exclure)
    """
    event_key = str(event.get('event_key', '') or '')
    event_title = str(event.get('event_title', '') or '')
    estimate = event.get('estimate')
    forecast = event.get('forecast')
    previous = event.get('previous')
    
    # Vérifier si estimate/forecast/previous sont tous absents ou NaN
    has_valid_estimate = (
        (estimate is not None and not pd.isna(estimate) and estimate != 'nan') or
        (forecast is not None and not pd.isna(forecast) and forecast != 'nan') or
        (previous is not None and not pd.isna(previous) and previous != 'nan')
    )
    
    if not has_valid_estimate:
        return True  # Pas d'estimate valide → exclure
    
    # Vérifier patterns discours/statement (même si estimate existe, souvent non fiable)
    text_to_check = f"{event_key} {event_title}".lower()
    for pattern in EVENTS_WITHOUT_ESTIMATE_PATTERNS:
        if re.search(pattern, text_to_check):
            return True  # Discours/statement → exclure
    
    return False  # Événement valide avec estimate

def detect_strong_movements(
    conn: duckdb.DuckDBPyConnection,
    date_str: str,
    min_pips: float = MIN_MOVEMENT_PIPS
) -> List[Dict]:
    """
    Détecte les mouvements forts depuis les prix pour une date
    
    Args:
        conn: Connexion DuckDB
        date_str: Date au format YYYY-MM-DD
        min_pips: Seuil minimum en pips
    
    Returns:
        Liste de dict avec :
        - start_time: datetime de début mouvement
        - peak_time: datetime du pic
        - impact_pips: Impact en pips
        - direction: 'UP' ou 'DOWN'
    """
    movements = []
    
    try:
        # Fenêtre de scan : 14:00-20:00 (heures principales trading)
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
        
        # Détecter mouvements significatifs
        # Baseline : OPEN première bougie à 14:30 (ou première disponible)
        baseline_time = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=30)))
        prices_at_baseline = df_prices[df_prices.index >= baseline_time]
        
        if prices_at_baseline.empty:
            # Fallback : première bougie disponible
            baseline_time = df_prices.index[0]
            prices_at_baseline = df_prices
        
        baseline_price = prices_at_baseline.iloc[0]['open']
        
        # Scanner pour trouver pics significatifs
        current_high = baseline_price
        current_low = baseline_price
        movement_start = None
        peak_time = None
        direction = None
        
        for idx, row in prices_at_baseline.iterrows():
            high_pips = (row['high'] - baseline_price) * 10000
            low_pips = (baseline_price - row['low']) * 10000
            
            # Détecter début mouvement (> 5 pips)
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
            
            # Continuer mouvement
            if movement_start is not None:
                if direction == 'UP':
                    if row['high'] > current_high:
                        current_high = row['high']
                        peak_time = idx
                else:  # DOWN
                    if row['low'] < current_low:
                        current_low = row['low']
                        peak_time = idx
        
        # Calculer impact final
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
    
    except Exception as e:
        print(f"   ⚠️ Erreur détection mouvement : {e}")
    
    return movements

def find_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement: Dict,
    window_minutes: int = WINDOW_MINUTES
) -> pd.DataFrame:
    """
    Trouve les événements correspondant à un mouvement
    
    Critères :
    1. Événement dans fenêtre temporelle (mouvement.start_time ± window_minutes)
    2. Événement AVEC estimate (pas de discours, etc.)
    3. Événement US/EU/DE/GB (principaux pour EUR/USD)
    
    Args:
        conn: Connexion DuckDB
        movement: Dict avec start_time, peak_time, etc.
        window_minutes: Fenêtre de correspondance
    
    Returns:
        DataFrame avec événements correspondants (filtrés)
    """
    start_time = movement['start_time']
    
    # Fenêtre de recherche
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
    
    # Filtrer événements SANS estimate (discours, etc.)
    valid_events = []
    for idx, event in df_events.iterrows():
        if not is_event_without_estimate(event):
            valid_events.append(idx)
    
    if not valid_events:
        return pd.DataFrame()
    
    df_valid = df_events.loc[valid_events].copy()
    return df_valid

def identify_core_type_from_events(events: pd.DataFrame) -> Tuple[str, List[str]]:
    """
    Identifie le type de noyau dur depuis les événements
    
    Patterns (par ordre de priorité) :
    1. CPI (≥2 événements CPI)
    2. NFP (≥1 événement NFP)
    3. JOBLESS_PCE (≥2 Jobless ET ≥1 PCE)
    4. GDP (≥2 événements GDP)
    5. JOBLESS (≥2 événements Jobless)
    6. PCE (≥1 événement PCE)
    7. GENERIC (autres)
    
    Args:
        events: DataFrame avec événements
    
    Returns:
        Tuple (core_type, core_event_keys)
    """
    if events.empty:
        return 'GENERIC', []
    
    # Patterns
    CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
    NFP_PATTERN = r'(?i)(non farm payrolls|nonfarm)'
    JOBLESS_PATTERN = r'(?i)(jobless claims|unemployment claims|initial jobless|continuing jobless)'
    PCE_PATTERN = r'(?i)(pce prices|personal consumption expenditure|core pce)'
    GDP_PATTERN = r'(?i)(gdp|gross domestic product)'
    
    # Compter occurrences
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
    
    # Déterminer type (par ordre de priorité)
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

def validate_noyau_dur_identification_v2(
    date_str: str,
    expected_anchor_time: str,
    expected_core_type: str,
    expected_movement_start: str,
    description: str
) -> Dict:
    """
    Valide l'identification du noyau dur avec nouvelle approche
    
    Processus :
    1. Détecter mouvements forts depuis prix
    2. Trouver événements correspondants (avec estimate)
    3. Identifier noyau dur
    4. Vérifier correspondance avec attentes
    
    Returns:
        Dict avec résultats de validation
    """
    print(f"\n{'='*100}")
    print(f"VALIDATION V2 : {date_str}")
    print(f"{'='*100}")
    print(f"Description : {description}")
    print(f"Attendu : anchor_time={expected_anchor_time}, core_type={expected_core_type}, mouvement={expected_movement_start}")
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    results = {
        'date': date_str,
        'success': False,
        'movements_detected': [],
        'main_movement': None,
        'anchor_time_detected': None,
        'anchor_time_expected': expected_anchor_time,
        'anchor_time_match': False,
        'events_for_movement': pd.DataFrame(),
        'events_filtered_count': 0,
        'core_type_detected': None,
        'core_type_expected': expected_core_type,
        'core_type_match': False,
        'movement_start_detected': None,
        'movement_start_expected': expected_movement_start,
        'movement_start_match': False,
        'errors': []
    }
    
    try:
        # 1. Détecter mouvements forts
        print("1. DÉTECTION MOUVEMENTS FORTS")
        print("-" * 100)
        movements = detect_strong_movements(conn, date_str, min_pips=MIN_MOVEMENT_PIPS)
        results['movements_detected'] = movements
        
        if not movements:
            results['errors'].append("Aucun mouvement fort détecté")
            print("   ❌ Aucun mouvement fort détecté")
            return results
        
        # Sélectionner mouvement principal (plus fort)
        main_movement = max(movements, key=lambda m: m['impact_pips'])
        results['main_movement'] = main_movement
        
        movement_start_str = main_movement['start_time'].strftime('%H:%M')
        results['movement_start_detected'] = movement_start_str
        results['movement_start_match'] = (movement_start_str == expected_movement_start)
        
        print(f"   ✅ {len(movements)} mouvement(s) détecté(s)")
        print(f"   Mouvement principal : {movement_start_str} → {main_movement['peak_time'].strftime('%H:%M')} ({main_movement['impact_pips']:.1f} pips, {main_movement['direction']})")
        print()
        
        # 2. Trouver événements correspondants
        print("2. RECHERCHE ÉVÉNEMENTS CORRESPONDANTS")
        print("-" * 100)
        events = find_events_for_movement(conn, main_movement, window_minutes=WINDOW_MINUTES)
        results['events_for_movement'] = events
        
        # Compter événements filtrés (sans estimate)
        query_all = f"""
        SELECT COUNT(*) as n_total
        FROM events e
        WHERE e.ts_utc >= '{main_movement['start_time'] - timedelta(minutes=WINDOW_MINUTES)}'
          AND e.ts_utc <= '{main_movement['start_time'] + timedelta(minutes=WINDOW_MINUTES)}'
          AND e.country IN ('US', 'EU', 'DE', 'GB')
          AND e.importance_n >= 2
        """
        n_total = conn.execute(query_all).fetchone()[0]
        results['events_filtered_count'] = n_total - len(events)
        
        if events.empty:
            results['errors'].append("Aucun événement avec estimate trouvé")
            print("   ❌ Aucun événement avec estimate trouvé")
            print(f"   (Événements filtrés : {results['events_filtered_count']} sans estimate)")
            return results
        
        print(f"   ✅ {len(events)} événement(s) avec estimate trouvé(s)")
        if results['events_filtered_count'] > 0:
            print(f"   ⚠️  {results['events_filtered_count']} événement(s) exclu(s) (sans estimate : discours, etc.)")
        
        # Afficher événements
        for _, event in events.iterrows():
            event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
            event_key = event.get('event_key', 'Unknown')
            importance = event.get('importance_n', 'N/A')
            estimate = event.get('estimate') or event.get('forecast') or 'N/A'
            print(f"      {event_time} : {event_key} (importance: {importance}, estimate: {estimate})")
        print()
        
        # 3. Identifier noyau dur
        print("3. IDENTIFICATION NOYAU DUR")
        print("-" * 100)
        core_type, core_keys = identify_core_type_from_events(events)
        results['core_type_detected'] = core_type
        results['core_type_match'] = (core_type == expected_core_type)
        
        # Anchor time = événement US HIGH le plus important dans le noyau dur
        us_high_events = events[
            (events['country'] == 'US') &
            (events['importance_n'] == 3) &
            (events['event_key'].isin(core_keys))
        ]
        
        if not us_high_events.empty:
            # Prioriser événement avec score empirique le plus élevé
            if 'empirical_score' in us_high_events.columns:
                us_high_events = us_high_events.sort_values('empirical_score', ascending=False)
            anchor_time_detected = pd.to_datetime(us_high_events.iloc[0]['ts_utc'])
        else:
            # Fallback : premier événement core
            core_events = events[events['event_key'].isin(core_keys)]
            if not core_events.empty:
                anchor_time_detected = pd.to_datetime(core_events.iloc[0]['ts_utc'])
            else:
                anchor_time_detected = pd.to_datetime(events.iloc[0]['ts_utc'])
        
        anchor_time_str = anchor_time_detected.strftime('%H:%M')
        results['anchor_time_detected'] = anchor_time_str
        results['anchor_time_match'] = (anchor_time_str == expected_anchor_time)
        
        print(f"   Core Type : {core_type}")
        print(f"   Anchor Time : {anchor_time_str}")
        print(f"   Événements core : {len(core_keys)}")
        print()
        
        # 4. Évaluer succès
        results['success'] = (
            results['anchor_time_match'] and
            results['core_type_match'] and
            results['movement_start_match']
        )
        
    except Exception as e:
        results['errors'].append(str(e))
        print(f"   ❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    # Afficher résultats
    print(f"📊 RÉSULTATS :")
    print(f"   Mouvement   : {results['movement_start_detected']} (attendu: {expected_movement_start}) {'✅' if results['movement_start_match'] else '❌'}")
    print(f"   Anchor Time : {results['anchor_time_detected']} (attendu: {expected_anchor_time}) {'✅' if results['anchor_time_match'] else '❌'}")
    print(f"   Core Type   : {results['core_type_detected']} (attendu: {expected_core_type}) {'✅' if results['core_type_match'] else '❌'}")
    
    if results['events_filtered_count'] > 0:
        print(f"   ⚠️  Événements exclus (sans estimate) : {results['events_filtered_count']}")
    
    if results['success']:
        print(f"\n   ✅ VALIDATION RÉUSSIE")
    else:
        print(f"\n   ❌ VALIDATION ÉCHOUÉE")
        if results['errors']:
            print(f"   Erreurs : {', '.join(results['errors'])}")
    
    return results

def main():
    """Exécute la validation sur dates de test"""
    print("="*100)
    print("VALIDATION IDENTIFICATION NOYAUX DURS (V2)")
    print("="*100)
    print()
    print("NOUVELLE APPROCHE :")
    print("1. Détecter mouvements forts depuis prix")
    print("2. Comparer avec événements (correspondance temporelle)")
    print("3. Filtrer événements SANS estimate (discours, etc.)")
    print("4. Identifier noyau dur basé sur correspondance")
    print()
    
    TEST_DATES = [
        {
            'date': '2025-05-29',
            'expected_anchor_time': '14:30',
            'expected_core_type': 'JOBLESS_PCE',
            'expected_movement_start': '14:30',
            'description': 'Jobless Claims + PCE à 14:30'
        },
        {
            'date': '2025-09-11',
            'expected_anchor_time': '14:30',
            'expected_core_type': 'CPI',
            'expected_movement_start': '14:30',
            'description': 'CPI US à 14:30'
        },
    ]
    
    all_results = []
    
    for test_case in TEST_DATES:
        result = validate_noyau_dur_identification_v2(
            test_case['date'],
            test_case['expected_anchor_time'],
            test_case['expected_core_type'],
            test_case['expected_movement_start'],
            test_case['description']
        )
        all_results.append(result)
    
    # Résumé
    print(f"\n{'='*100}")
    print("RÉSUMÉ GLOBAL")
    print(f"{'='*100}")
    print()
    
    n_success = sum(1 for r in all_results if r['success'])
    n_total = len(all_results)
    
    print(f"Dates validées : {n_success}/{n_total}")
    print()
    
    anchor_matches = sum(1 for r in all_results if r['anchor_time_match'])
    core_matches = sum(1 for r in all_results if r['core_type_match'])
    movement_matches = sum(1 for r in all_results if r['movement_start_match'])
    
    print(f"   Mouvement correct   : {movement_matches}/{n_total}")
    print(f"   Anchor Time correct : {anchor_matches}/{n_total}")
    print(f"   Core Type correct   : {core_matches}/{n_total}")
    print()
    
    total_filtered = sum(r['events_filtered_count'] for r in all_results)
    if total_filtered > 0:
        print(f"   ⚠️  Total événements exclus (sans estimate) : {total_filtered}")
        print()
    
    if n_success == n_total:
        print("✅ VALIDATION COMPLÈTE : La méthode est correcte")
        print("   → On peut procéder au recalcul des scores historiques")
    else:
        print("❌ VALIDATION INCOMPLÈTE : Des corrections sont nécessaires")
    
    print(f"{'='*100}")

if __name__ == '__main__':
    main()

