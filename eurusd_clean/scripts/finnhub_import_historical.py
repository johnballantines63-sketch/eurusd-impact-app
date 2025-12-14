#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finnhub_import_historical.py
-----------------------------
Import historique complet depuis Finnhub (remplacement MyFXBook)

Usage:
    python3 scripts/finnhub_import_historical.py --start-year 2023 --end-year 2025
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta
import sys

from tqdm import tqdm

# Ajouter scripts au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from finnhub_import import import_finnhub_events
from config import DB_PATH

def import_historical(start_year: int, end_year: int, countries: list = None):
    """
    Import historique par mois pour éviter les limites API
    
    Args:
        start_year: Année début
        end_year: Année fin
        countries: Liste pays (None = tous)
    """
    print("=" * 80)
    print(f"IMPORT HISTORIQUE FINNHUB ({start_year}-{end_year})")
    print("=" * 80)
    print()
    
    # Générer toutes les dates de début de mois
    current = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    
    months = []
    while current <= end:
        # Premier jour du mois
        month_start = current
        # Dernier jour du mois
        if current.month == 12:
            month_end = datetime(current.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(current.year, current.month + 1, 1) - timedelta(days=1)
        
        months.append((month_start, month_end))
        
        # Mois suivant
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    print(f"📅 {len(months)} mois à importer\n")
    
    # Importer mois par mois avec barre de progression
    for i, (month_start, month_end) in enumerate(tqdm(months, desc="Import"), 1):
        from_date = month_start.strftime('%Y-%m-%d')
        to_date = month_end.strftime('%Y-%m-%d')
        
        try:
            import_finnhub_events(
                db_path=DB_PATH,
                from_date=from_date,
                to_date=to_date,
                countries=countries,
                replace=True
            )
        except Exception as e:
            print(f"\n⚠️  Erreur pour {from_date} à {to_date}: {e}")
            continue
    
    print("\n" + "=" * 80)
    print("✅ IMPORT HISTORIQUE TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import historique complet depuis Finnhub"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2023,
        help="Année début (défaut: 2023)"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="Année fin (défaut: 2025)"
    )
    parser.add_argument(
        "--countries",
        type=str,
        nargs="+",
        help="Pays à importer (ex: US DE FR)"
    )
    
    args = parser.parse_args()
    
    import_historical(
        start_year=args.start_year,
        end_year=args.end_year,
        countries=args.countries
    )


