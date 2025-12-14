#!/usr/bin/env python3
"""
Nettoyage DB : Supprimer Événements JBlanked
=============================================

Objectif : Supprimer la table economic_events (JBlanked) pour avoir DB 100% Finnhub
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH

print('='*100)
print('NETTOYAGE DB : SUPPRESSION JBLANKED')
print('='*100)
print()

print(f'DB Path: {DB_PATH}')
print(f'Existe: {DB_PATH.exists()}')
print()

# Backup avant suppression
backup_path = DB_PATH.parent / f"warehouse_backup_before_jblanked_cleanup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.duckdb"
print(f'📦 Backup DB avant nettoyage...')
print(f'   Destination: {backup_path}')

import shutil
import pandas as pd

try:
    shutil.copy2(DB_PATH, backup_path)
    print(f'   ✅ Backup créé: {backup_path.stat().st_size / (1024*1024):.1f} MB')
except Exception as e:
    print(f'   ❌ Erreur backup: {e}')
    sys.exit(1)

print()

# Connexion DB
conn = duckdb.connect(str(DB_PATH))

# Vérifier tables JBlanked
print('🔍 Vérification tables JBlanked...')
print('-'*100)

jblanked_tables = []

# Vérifier economic_events
try:
    count = conn.execute('SELECT COUNT(*) FROM economic_events').fetchone()[0]
    jblanked_tables.append(('economic_events', count))
    print(f'  economic_events: {count:,} lignes')
except Exception as e:
    print(f'  economic_events: N\'existe pas ({e})')

# Vérifier backups economic_events
try:
    all_tables = conn.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name LIKE 'economic_events_backup%'
    """).df()
    
    if not all_tables.empty:
        print(f'  Backups economic_events: {len(all_tables)} tables')
        for _, row in all_tables.iterrows():
            table_name = row['table_name']
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
                jblanked_tables.append((table_name, count))
                print(f'    {table_name}: {count:,} lignes')
            except:
                pass
except Exception as e:
    print(f'  Erreur vérification backups: {e}')

print()

if not jblanked_tables:
    print('✅ Aucune table JBlanked trouvée')
    conn.close()
    sys.exit(0)

# Confirmation
print('⚠️  TABLES À SUPPRIMER:')
print('-'*100)
for table_name, count in jblanked_tables:
    print(f'  - {table_name}: {count:,} lignes')
print()

response = input('Confirmer suppression ? (oui/non): ')
if response.lower() != 'oui':
    print('❌ Suppression annulée')
    conn.close()
    sys.exit(0)

# Supprimer tables
print()
print('🗑️  Suppression tables JBlanked...')
print('-'*100)

for table_name, count in jblanked_tables:
    try:
        conn.execute(f'DROP TABLE IF EXISTS {table_name}')
        print(f'  ✅ {table_name} supprimée ({count:,} lignes)')
    except Exception as e:
        print(f'  ❌ Erreur suppression {table_name}: {e}')

print()

# Vérification finale
print('✅ VÉRIFICATION FINALE')
print('-'*100)

# Vérifier que economic_events n'existe plus
try:
    conn.execute('SELECT COUNT(*) FROM economic_events')
    print('  ⚠️ economic_events existe encore (erreur)')
except:
    print('  ✅ economic_events supprimée')

# Vérifier que events (Finnhub) existe toujours
try:
    count_events = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    print(f'  ✅ events (Finnhub): {count_events:,} lignes')
except Exception as e:
    print(f'  ❌ events n\'existe plus (erreur): {e}')

# Vérifier prix Finnhub
try:
    count_m1 = conn.execute('SELECT COUNT(*) FROM prices_finnhub_m1').fetchone()[0]
    print(f'  ✅ prices_finnhub_m1: {count_m1:,} lignes')
except Exception as e:
    print(f'  ❌ prices_finnhub_m1 n\'existe plus (erreur): {e}')

conn.close()

print()
print('='*100)
print('✅ NETTOYAGE TERMINÉ')
print('='*100)
print()
print(f'📦 Backup sauvegardé: {backup_path}')




