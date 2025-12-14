#!/usr/bin/env python3
"""
Mesure des Impacts Réels pour Toutes les Dates de Test
=======================================================

Ce script mesure les impacts réels depuis les données Finnhub pour toutes
les dates utilisées dans les tests de validation.

Objectif : Remplacer les valeurs incorrectes dans les CSV par des mesures fraîches.

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import pytz

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from core.price_loader_finnhub import measure_impact_from_finnhub
from run_pipeline_complete import PipelineExecutor

# Dates de test à mesurer
TEST_DATES = [
    {
        'date': '2025-09-11',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'Cas de référence principal - CPI'
    },
    {
        'date': '2025-08-01',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'Single Wave Fort - NFP'
    },
    {
        'date': '2025-11-20',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'Double Wave - NFP'
    },
    {
        'date': '2025-10-10',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'Double Wave'
    },
    {
        'date': '2025-06-23',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'Double Wave'
    },
    {
        'date': '2025-01-15',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'CPI'
    },
    {
        'date': '2025-05-29',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'JOBLESS_PCE'
    },
    {
        'date': '2024-09-11',
        'event_time': '14:30',
        'timezone': 'Europe/Zurich',
        'notes': 'CPI historique'
    },
]

def measure_impact_for_date(date_str, event_time_str, timezone_str='Europe/Zurich'):
    """
    Mesure l'impact réel pour une date donnée.
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        event_time_str: Heure au format 'HH:MM'
        timezone_str: Timezone (défaut: 'Europe/Zurich')
    
    Returns:
        Dict avec les résultats de mesure
    """
    # Parser date et heure
    date_parts = date_str.split('-')
    time_parts = event_time_str.split(':')
    
    tz = pytz.timezone(timezone_str)
    event_datetime = datetime(
        int(date_parts[0]),
        int(date_parts[1]),
        int(date_parts[2]),
        int(time_parts[0]),
        int(time_parts[1]),
        0,
        tzinfo=tz
    )
    
    print(f"   📅 Mesure pour {date_str} à {event_time_str} ({timezone_str})...")
    
    try:
        # Mesurer impact réel
        result = measure_impact_from_finnhub(
            db_path=DB_PATH,
            event_timestamp=event_datetime,
            lookback_minutes=5,
            lookahead_minutes=120,
            debug=False
        )
        
        if result:
            return {
                'success': True,
                'impact_pips': result.get('impact_pips'),
                'baseline_price': result.get('baseline_price'),
                'peak_price': result.get('peak_price'),
                'peak_time': result.get('peak_time'),
                'direction': result.get('direction', 'UNKNOWN')
            }
        else:
            return {
                'success': False,
                'error': 'Aucun résultat retourné'
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print('='*80)
    print('MESURE DES IMPACTS RÉELS - TOUTES LES DATES DE TEST')
    print('='*80)
    print()
    
    results = []
    
    for test_case in TEST_DATES:
        date_str = test_case['date']
        event_time = test_case['event_time']
        timezone = test_case.get('timezone', 'Europe/Zurich')
        notes = test_case.get('notes', '')
        
        print(f"[{len(results)+1}/{len(TEST_DATES)}] {date_str} - {notes}")
        print('-'*80)
        
        result = measure_impact_for_date(date_str, event_time, timezone)
        
        if result['success']:
            print(f"   ✅ Impact réel : {result['impact_pips']:.2f} pips")
            if result.get('baseline_price'):
                print(f"      Baseline : {result['baseline_price']:.5f}")
            if result.get('peak_price'):
                print(f"      Peak : {result['peak_price']:.5f}")
            if result.get('peak_time'):
                print(f"      Peak time : {result['peak_time']}")
            print(f"      Direction : {result['direction']}")
            
            results.append({
                'date': date_str,
                'event_time': event_time,
                'timezone': timezone,
                'impact_real_pips': result['impact_pips'],
                'baseline_price': result['baseline_price'],
                'peak_price': result['peak_price'],
                'peak_time': result['peak_time'].isoformat() if result.get('peak_time') else None,
                'direction': result['direction'],
                'notes': notes,
                'success': True
            })
        else:
            print(f"   ❌ Erreur : {result.get('error', 'Erreur inconnue')}")
            
            results.append({
                'date': date_str,
                'event_time': event_time,
                'timezone': timezone,
                'impact_real_pips': None,
                'baseline_price': None,
                'peak_price': None,
                'peak_time': None,
                'direction': None,
                'notes': notes,
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            })
        
        print()
    
    # Sauvegarder résultats
    df_results = pd.DataFrame(results)
    output_path = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures.csv'
    df_results.to_csv(output_path, index=False)
    
    print('='*80)
    print('RÉSUMÉ')
    print('='*80)
    print()
    
    n_success = df_results['success'].sum()
    n_total = len(df_results)
    
    print(f"✅ Succès : {n_success}/{n_total}")
    print(f"❌ Échecs : {n_total - n_success}/{n_total}")
    print()
    
    if n_success > 0:
        print("📊 Impacts réels mesurés :")
        print()
        for _, row in df_results[df_results['success']].iterrows():
            print(f"   {row['date']} : {row['impact_real_pips']:.2f} pips ({row['direction']})")
        print()
    
    print(f"💾 Résultats sauvegardés : {output_path}")
    print()
    
    return df_results

if __name__ == '__main__':
    df_results = main()

