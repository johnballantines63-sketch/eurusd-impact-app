#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MISE À JOUR ÉVÉNEMENTS EODHD JUSQU'À AUJOURD'HUI
=================================================

Import incrémental des événements économiques depuis EODHD.
Met à jour depuis la dernière date en DB jusqu'à aujourd'hui.

Source : EODHD API (Economic Calendar)
Table : events
"""

import sys
from pathlib import Path
from datetime import datetime, date
import subprocess

# Ajouter fx_impact_app au path
PROJECT_ROOT = Path(__file__).parent.parent
FX_APP_ROOT = PROJECT_ROOT.parent / 'fx_impact_app'
sys.path.insert(0, str(FX_APP_ROOT))

print("=" * 80)
print("MISE À JOUR ÉVÉNEMENTS EODHD JUSQU'À AUJOURD'HUI")
print("=" * 80)
print()

# Vérifier dernière date en DB
import duckdb
db_path = FX_APP_ROOT / 'data' / 'warehouse.duckdb'

if not db_path.exists():
    print(f"❌ Base de données introuvable : {db_path}")
    sys.exit(1)

conn = duckdb.connect(str(db_path), read_only=True)

try:
    # Vérifier dernière date événements
    result = conn.execute("SELECT MAX(DATE(ts_utc)) FROM events").fetchone()
    last_date_str = result[0] if result[0] else None
    
    if last_date_str:
        if isinstance(last_date_str, str):
            last_date = date.fromisoformat(last_date_str.split()[0])
        else:
            last_date = last_date_str
        print(f"📊 Dernière date événements en DB: {last_date}")
    else:
        print("⚠️  Aucune date trouvée, import depuis aujourd'hui")
        last_date = date.today()
    
    # Date de fin = aujourd'hui
    today = date.today()
    
    # Période à importer
    if last_date >= today:
        print("✅ Événements à jour !")
        sys.exit(0)
    
    from_date = (last_date + datetime.timedelta(days=1)).isoformat()
    to_date = today.isoformat()
    
    print(f"   Période à importer: {from_date} → {to_date}")
    print()
    
    response = input("Confirmer l'import ? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Annulé")
        sys.exit(1)
    
    # Utiliser le script existant
    script_path = FX_APP_ROOT / 'scripts' / 'ingest_eodhd_calendar.py'
    
    if not script_path.exists():
        print(f"❌ Script introuvable : {script_path}")
        sys.exit(1)
    
    print("\n🚀 Import en cours...")
    print("-" * 80)
    
    # Exécuter script
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            '--from', from_date,
            '--to', to_date
        ],
        cwd=str(FX_APP_ROOT),
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode == 0:
        print("\n✅ Import terminé !")
    else:
        print(f"\n❌ Erreur (code {result.returncode})")
        sys.exit(1)

finally:
    conn.close()

print("=" * 80)


