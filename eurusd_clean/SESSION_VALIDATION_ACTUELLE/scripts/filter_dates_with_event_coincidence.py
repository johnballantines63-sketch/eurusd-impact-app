"""
Filtrage : Dates avec événement coïncidant avec le début du mouvement

Objectif :
1. Identifier le début réel du mouvement pour chaque date
2. Vérifier s'il y a un événement dans une fenêtre de ±15 minutes
3. Éliminer les dates sans événement coïncidant

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

# Fenêtre de coïncidence : ±15 minutes
COINCIDENCE_WINDOW_MINUTES = 15

# Seuil de mouvement significatif : 10 pips (REF-035 : détecter mouvement FORT, pas juste ≥5 pips)
MIN_MOVEMENT_PIPS = 10.0

def detect_movement_start(df_prices, baseline_time, window_hours=6):
    """
    Détecte le début réel du mouvement FORT principal
    
    Stratégie améliorée (REF-035) :
    1. Identifier le pic maximum (mouvement le plus fort)
    2. Calculer seuil = 30% du pic maximum (mouvement FORT, pas juste ≥5 pips)
    3. Remonter depuis le pic pour trouver la première bougie ≥seuil
    4. Utiliser ce début pour vérifier la coïncidence
    
    Retourne :
    - movement_start_time : datetime du début du mouvement FORT
    - movement_start_pips : amplitude du mouvement au début
    - movement_direction : 'UP' ou 'DOWN'
    """
    
    # Fenêtre d'analyse : baseline_time à baseline_time + window_hours
    window_end = baseline_time + pd.Timedelta(hours=window_hours)
    
    df_window = df_prices[
        (df_prices.index >= baseline_time) & 
        (df_prices.index <= window_end)
    ].copy()
    
    if df_window.empty:
        return None, 0.0, None
    
    baseline_price = df_window.iloc[0]['open']
    
    # 1. Identifier le pic maximum (mouvement le plus fort)
    max_high = df_window['high'].max()
    min_low = df_window['low'].min()
    
    high_pips = (max_high - baseline_price) * 10000
    low_pips = (baseline_price - min_low) * 10000
    
    # Déterminer direction du mouvement principal
    if high_pips > low_pips and high_pips >= MIN_MOVEMENT_PIPS:
        # Mouvement UP principal
        peak_time = df_window[df_window['high'] == max_high].index[0]
        peak_price = max_high
        direction = 'UP'
        max_pips = high_pips
    elif low_pips >= MIN_MOVEMENT_PIPS:
        # Mouvement DOWN principal
        low_time = df_window[df_window['low'] == min_low].index[0]
        peak_time = low_time
        peak_price = min_low
        direction = 'DOWN'
        max_pips = low_pips
    else:
        # Pas de mouvement significatif
        return None, 0.0, None
    
    # 2. ⚠️ AMÉLIORATION : Seuil pour détecter le début = 30% du mouvement maximum
    # Cela détecte le début du mouvement FORT, pas juste le premier mouvement ≥5 pips
    threshold_pips = max_pips * 0.30
    
    # Minimum absolu : au moins 10 pips pour être considéré comme mouvement FORT
    threshold_pips = max(threshold_pips, 10.0)
    
    # 3. Remonter depuis le pic pour trouver le début du mouvement FORT
    # Le début est la première bougie qui atteint ≥seuil avant le pic
    df_before_peak = df_window[df_window.index <= peak_time]
    
    movement_start_time = peak_time  # Fallback : utiliser le pic si pas trouvé
    movement_start_pips = max_pips
    
    # Parcourir depuis le pic vers le début pour trouver la première bougie ≥seuil
    for idx in reversed(df_before_peak.index):
        row = df_before_peak.loc[idx]
        
        if direction == 'UP':
            current_pips = (row['high'] - baseline_price) * 10000
            if current_pips >= threshold_pips:
                # On a trouvé le début du mouvement FORT
                movement_start_time = idx
                movement_start_pips = current_pips
            else:
                # On est passé sous le seuil, le début est la bougie suivante
                next_idx = df_before_peak.index[df_before_peak.index > idx]
                if len(next_idx) > 0:
                    movement_start_time = next_idx[0]
                    movement_start_pips = (df_before_peak.loc[movement_start_time]['high'] - baseline_price) * 10000
                break
        else:
            current_pips = (baseline_price - row['low']) * 10000
            if current_pips >= threshold_pips:
                # On a trouvé le début du mouvement FORT
                movement_start_time = idx
                movement_start_pips = current_pips
            else:
                # On est passé sous le seuil, le début est la bougie suivante
                next_idx = df_before_peak.index[df_before_peak.index > idx]
                if len(next_idx) > 0:
                    movement_start_time = next_idx[0]
                    movement_start_pips = (baseline_price - df_before_peak.loc[movement_start_time]['low']) * 10000
                break
    
    return movement_start_time, movement_start_pips, direction

def check_event_coincidence(date_str, movement_start_time, conn):
    """
    Vérifie s'il y a un événement dans la fenêtre de coïncidence
    
    Retourne :
    - has_coincidence : bool
    - coinciding_events : list of events
    """
    
    if movement_start_time is None:
        return False, []
    
    # Fenêtre de coïncidence : ±15 minutes
    window_start = movement_start_time - pd.Timedelta(minutes=COINCIDENCE_WINDOW_MINUTES)
    window_end = movement_start_time + pd.Timedelta(minutes=COINCIDENCE_WINDOW_MINUTES)
    
    query_events = f"""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        estimate
    FROM events
    WHERE DATE(ts_utc) = '{date_str}'
      AND ts_utc >= '{window_start.isoformat()}'
      AND ts_utc <= '{window_end.isoformat()}'
      AND importance_n <= 3
    ORDER BY ts_utc
    """
    
    df_events = conn.execute(query_events).df()
    
    if df_events.empty:
        return False, []
    
    return True, df_events.to_dict('records')

def analyze_date(date_str, conn):
    """Analyse une date pour vérifier la coïncidence événement-mouvement"""
    
    # Charger prix
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    
    if df_prices.empty:
        return {
            'date': date_str,
            'has_data': False,
            'has_coincidence': False,
            'movement_start_time': None,
            'coinciding_events': []
        }
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices = df_prices.set_index('datetime')
    
    # Baseline : 14:00 (heure standard d'événements US)
    baseline_time = TZ_BERN.localize(
        datetime.combine(
            pd.to_datetime(date_str).date(),
            datetime.min.time().replace(hour=14, minute=0)
        )
    )
    
    # Si pas de données à 14:00, utiliser première bougie
    if baseline_time not in df_prices.index:
        baseline_time = df_prices.index[0]
    
    # Détecter début du mouvement
    movement_start_time, movement_start_pips, movement_direction = detect_movement_start(
        df_prices, baseline_time
    )
    
    if movement_start_time is None:
        return {
            'date': date_str,
            'has_data': True,
            'has_coincidence': False,
            'movement_start_time': None,
            'movement_start_pips': 0.0,
            'movement_direction': None,
            'coinciding_events': []
        }
    
    # Vérifier coïncidence
    has_coincidence, coinciding_events = check_event_coincidence(
        date_str, movement_start_time, conn
    )
    
    return {
        'date': date_str,
        'has_data': True,
        'has_coincidence': has_coincidence,
        'movement_start_time': movement_start_time,
        'movement_start_pips': movement_start_pips,
        'movement_direction': movement_direction,
        'coinciding_events': coinciding_events
    }

def analyze_all_test_dates():
    """Analyse toutes les dates de test"""
    
    # Dates de test actuelles
    TEST_DATES = [
        '2025-11-20',
        '2025-09-11',
        '2025-08-01',
        '2025-05-29',
        '2025-06-23',
        '2025-10-10',
        '2025-04-10',
        '2025-03-12',
        '2025-02-07',
        '2025-01-10',
        '2024-12-13',
        '2024-11-08',
        '2024-10-11',
        '2024-09-06',
        '2024-08-02',
        '2024-07-11',
        '2024-06-07',
        '2024-05-10',
        '2024-04-05',
        '2024-03-08',
        '2024-02-13',
        '2024-01-12',
    ]
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    results = []
    
    print("="*100)
    print("ANALYSE : COÏNCIDENCE ÉVÉNEMENT-MOUVEMENT")
    print("="*100)
    print()
    print(f"Fenêtre de coïncidence : ±{COINCIDENCE_WINDOW_MINUTES} minutes")
    print(f"Seuil mouvement significatif : {MIN_MOVEMENT_PIPS} pips")
    print()
    
    for date_str in TEST_DATES:
        print(f"Analyse : {date_str}...", end=" ")
        result = analyze_date(date_str, conn)
        results.append(result)
        
        if result['has_data']:
            if result['has_coincidence']:
                print(f"✅ COÏNCIDENCE ({len(result['coinciding_events'])} événements)")
            else:
                movement_time_str = result['movement_start_time'].strftime('%H:%M') if result['movement_start_time'] else 'N/A'
                print(f"❌ PAS DE COÏNCIDENCE (mouvement à {movement_time_str})")
        else:
            print("❌ PAS DE DONNÉES")
    
    print()
    conn.close()
    
    # Résumé
    print("="*100)
    print("RÉSUMÉ")
    print("="*100)
    print()
    
    dates_with_coincidence = [r for r in results if r['has_coincidence']]
    dates_without_coincidence = [r for r in results if r['has_data'] and not r['has_coincidence']]
    dates_no_data = [r for r in results if not r['has_data']]
    
    print(f"✅ Dates avec coïncidence : {len(dates_with_coincidence)}")
    print(f"❌ Dates sans coïncidence : {len(dates_without_coincidence)}")
    print(f"⚠️  Dates sans données : {len(dates_no_data)}")
    print()
    
    if dates_without_coincidence:
        print("Dates à éliminer (pas de coïncidence) :")
        print("-"*100)
        for r in dates_without_coincidence:
            movement_time_str = r['movement_start_time'].strftime('%H:%M') if r['movement_start_time'] else 'N/A'
            print(f"  - {r['date']} : mouvement à {movement_time_str} ({r['movement_start_pips']:.1f} pips, {r['movement_direction']})")
        print()
    
    if dates_with_coincidence:
        print("Dates à conserver (avec coïncidence) :")
        print("-"*100)
        for r in dates_with_coincidence:
            movement_time_str = r['movement_start_time'].strftime('%H:%M') if r['movement_start_time'] else 'N/A'
            events_str = ", ".join([f"{e['event_key'][:30]} ({e['country']})" for e in r['coinciding_events'][:2]])
            if len(r['coinciding_events']) > 2:
                events_str += f" ... (+{len(r['coinciding_events'])-2} autres)"
            print(f"  - {r['date']} : mouvement à {movement_time_str} → {events_str}")
        print()
    
    # Sauvegarder résultats
    df_results = pd.DataFrame(results)
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'dates_coincidence_analysis.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Préparer pour CSV
    df_csv = df_results.copy()
    df_csv['movement_start_time'] = df_csv['movement_start_time'].apply(
        lambda x: x.strftime('%H:%M') if x is not None else None
    )
    df_csv['n_coinciding_events'] = df_csv['coinciding_events'].apply(len)
    df_csv = df_csv.drop(columns=['coinciding_events'])
    
    df_csv.to_csv(output_file, index=False)
    print(f"📋 Résultats sauvegardés : {output_file}")
    print()
    
    return results

if __name__ == '__main__':
    analyze_all_test_dates()

