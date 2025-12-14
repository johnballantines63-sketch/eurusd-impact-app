#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MISE À JOUR DONNÉES FINNHUB JUSQU'À AUJOURD'HUI
================================================

Met à jour automatiquement :
1. Prix EUR/USD M1 depuis dernière date jusqu'à aujourd'hui
2. Événements économiques depuis dernière date jusqu'à aujourd'hui

Utilise les scripts existants :
- scripts/update_finnhub_prices_to_today.py
- scripts/finnhub_import.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent

# Charger .env AVANT tout import
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
except:
    pass

# S'assurer que la clé API est dans l'environnement
if not os.environ.get('FINNHUB_API_KEY'):
    # Essayer de charger depuis .env manuellement
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                if key.strip() == 'FINNHUB_API_KEY':
                    os.environ[key.strip()] = value.strip()
                    break

print("=" * 80)
print("MISE À JOUR DONNÉES FINNHUB JUSQU'À AUJOURD'HUI")
print("=" * 80)
print()

# 1. Mise à jour des PRIX
print("📊 ÉTAPE 1 : Mise à jour PRIX")
print("-" * 80)
print()

try:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "update_finnhub_prices_to_today.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✅ Prix mis à jour avec succès")
    else:
        print(f"\n⚠️  Erreur mise à jour prix (code: {result.returncode})")
        print("   Vérifiez les logs ci-dessus")
except Exception as e:
    print(f"\n❌ Erreur exécution script prix: {e}")

print()
print()

# 2. Mise à jour des ÉVÉNEMENTS
print("📅 ÉTAPE 2 : Mise à jour ÉVÉNEMENTS")
print("-" * 80)
print()

# Calculer période : depuis il y a 7 jours jusqu'à aujourd'hui (pour couvrir les événements futurs)
from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
to_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')  # +30 jours pour événements futurs

print(f"📅 Période : {from_date} → {to_date}")
print()

# Importer directement la fonction pour éviter les problèmes de subprocess
try:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    
    from finnhub_import import import_finnhub_events
    from config import DB_PATH
    
    import_finnhub_events(
        db_path=DB_PATH,
        from_date=from_date,
        to_date=to_date,
        countries=None,  # Tous les pays
        replace=False  # Ne pas remplacer, juste ajouter les nouveaux
    )
    
    print("\n✅ Événements mis à jour avec succès")
except Exception as e:
    print(f"\n❌ Erreur mise à jour événements: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("✅ MISE À JOUR TERMINÉE")
print("=" * 80)


