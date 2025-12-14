#!/usr/bin/env python3
"""
Vérification Tables DB
======================

Objectif : Vérifier quelles tables existent dans la DB et leur origine
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH

print('='*100)
print('VÉRIFICATION TABLES DB')
print('='*100)
print(f'DB Path: {DB_PATH}')
print(f'Existe: {DB_PATH.exists()}')
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Lister toutes les tables
try:
    tables = conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).df()
    
    print('='*100)
    print('TOUTES LES TABLES')
    print('='*100)
    print()
    
    finnhub_tables = []
    dukascopy_tables = []
    event_tables = []
    other_tables = []
    
    for _, row in tables.iterrows():
        table_name = row['table_name']
        
        if 'finnhub' in table_name.lower():
            finnhub_tables.append(table_name)
        elif any(x in table_name.lower() for x in ['prices_1m', 'prices_bern', 'prices_1h', 'prices_m', 'prices_h']):
            dukascopy_tables.append(table_name)
        elif 'event' in table_name.lower():
            event_tables.append(table_name)
        else:
            other_tables.append(table_name)
    
    # Afficher tables Finnhub
    if finnhub_tables:
        print('📊 TABLES FINNHUB (Prix)')
        print('-'*100)
        for table in sorted(finnhub_tables):
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                print(f'  ✅ {table}: {count:,} lignes')
            except Exception as e:
                print(f'  ❌ {table}: Erreur ({e})')
        print()
    
    # Afficher tables Dukascopy
    if dukascopy_tables:
        print('📊 TABLES DUKASCOPY (Prix - Obsolètes ?)')
        print('-'*100)
        for table in sorted(dukascopy_tables):
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                print(f'  ⚠️ {table}: {count:,} lignes')
            except Exception as e:
                print(f'  ❌ {table}: Erreur ({e})')
        print()
    
    # Afficher tables événements
    if event_tables:
        print('📅 TABLES ÉVÉNEMENTS')
        print('-'*100)
        for table in sorted(event_tables):
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                print(f'  ✅ {table}: {count:,} lignes')
                
                # Échantillon pour events
                if table == 'events':
                    sample = conn.execute(f'SELECT ts_utc, event_title, country, importance_n FROM {table} LIMIT 3').df()
                    print('    Échantillon:')
                    for _, row in sample.iterrows():
                        print(f'      {row["ts_utc"]} | {row["event_title"]} | {row["country"]} | importance={row["importance_n"]}')
            except Exception as e:
                print(f'  ❌ {table}: Erreur ({e})')
        print()
    
    # Afficher autres tables
    if other_tables:
        print('📋 AUTRES TABLES')
        print('-'*100)
        for table in sorted(other_tables):
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                print(f'  {table}: {count:,} lignes')
            except Exception as e:
                print(f'  ❌ {table}: Erreur ({e})')
        print()
    
    # Vérifier tables utilisées par le pipeline
    print('='*100)
    print('VÉRIFICATION TABLES UTILISÉES PAR PIPELINE')
    print('='*100)
    print()
    
    pipeline_tables = {
        'events': 'Événements économiques',
        'event_families': 'Scores empiriques',
        'prices_finnhub_m1': 'Prix M1 Finnhub',
        'prices_finnhub_m30': 'Prix M30 Finnhub',
        'prices_finnhub_h1': 'Prix H1 Finnhub',
    }
    
    for table, description in pipeline_tables.items():
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            print(f'✅ {table} ({description}): {count:,} lignes')
        except Exception as e:
            print(f'❌ {table} ({description}): N\'existe pas ({e})')
    
    print()
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()

conn.close()

print('='*100)
print('✅ VÉRIFICATION TERMINÉE')
print('='*100)




