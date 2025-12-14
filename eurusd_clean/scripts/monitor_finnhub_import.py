#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_finnhub_import.py
--------------------------
Script de monitoring pour suivre la progression de l'import Finnhub.
Affiche le nombre de bougies importées par timeframe et la progression.
"""
import sys
from pathlib import Path
from datetime import datetime
import pytz

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import DB_PATH, TIMEZONE_BERN
import duckdb

RESOLUTIONS = ['M1', 'M5', 'M15', 'M30', 'H1', 'D', 'W', 'M']

def get_table_stats(conn, resolution: str) -> dict:
    """Récupère les statistiques d'une table."""
    table_name = f"prices_finnhub_{resolution.lower()}"
    
    try:
        query = f"""
        SELECT 
            COUNT(*) as count,
            MIN(datetime) as date_min,
            MAX(datetime) as date_max
        FROM {table_name}
        """
        result = conn.execute(query).fetchone()
        if result and result[0]:
            return {
                'count': result[0],
                'date_min': result[1],
                'date_max': result[2],
                'exists': True
            }
    except:
        pass
    
    return {'count': 0, 'date_min': None, 'date_max': None, 'exists': False}

def format_number(n: int) -> str:
    """Formate un nombre avec séparateurs."""
    return f"{n:,}".replace(',', ' ')

def main():
    import pandas as pd
    
    conn = duckdb.connect(str(DB_PATH))
    
    print('='*80)
    print('MONITORING IMPORT FINNHUB')
    print('='*80)
    print(f'Heure : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    total_bougies = 0
    tables_ok = 0
    
    for resolution in RESOLUTIONS:
        stats = get_table_stats(conn, resolution)
        
        if stats['exists']:
            tables_ok += 1
            total_bougies += stats['count']
            
            date_min = pd.to_datetime(stats['date_min']) if stats['date_min'] else None
            date_max = pd.to_datetime(stats['date_max']) if stats['date_max'] else None
            
            if date_min and date_max:
                duration_days = (date_max - date_min).days
                status = '✅'
            else:
                duration_days = 0
                status = '⚠️'
            
            print(f'{status} {resolution:4s} : {format_number(stats["count"]):>12s} bougies', end='')
            if date_min and date_max:
                print(f' | {date_min.strftime("%Y-%m-%d")} → {date_max.strftime("%Y-%m-%d")} ({duration_days} jours)')
            else:
                print()
        else:
            print(f'⏳ {resolution:4s} : En attente...')
    
    conn.close()
    
    print()
    print('='*80)
    print(f'RÉSUMÉ : {tables_ok}/{len(RESOLUTIONS)} timeframes importés')
    print(f'Total : {format_number(total_bougies)} bougies')
    print('='*80)

if __name__ == '__main__':
    import pandas as pd
    main()

