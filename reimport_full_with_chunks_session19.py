#!/usr/bin/env python3
"""
Script Session 19 : Re-import COMPLET avec boucle sur les dates
===============================================================

Le script ingest_eodhd_calendar.py fait un seul appel API.
Ce script boucle sur TOUS les mois de 2023 à 2025.

Temps estimé : 45-60 minutes
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import duckdb

# Setup path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.eodhd_client import (
    fetch_calendar_json,
    calendar_to_events_df,
    upsert_events_df
)

# Couleurs
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(msg: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[STEP]{Colors.END} {msg}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def generate_date_ranges(start_date: str, end_date: str, chunk_days: int = 30):
    """Génère des plages de dates pour découper les requêtes API"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    ranges = []
    current = start
    
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end)
        ranges.append((
            current.strftime('%Y-%m-%d'),
            chunk_end.strftime('%Y-%m-%d')
        ))
        current = chunk_end + timedelta(days=1)
    
    return ranges


def reimport_full_history():
    """Re-import complet par chunks de 30 jours"""
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}SESSION 19 : Re-import COMPLET avec fix 'comparison'{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    
    # Paramètres
    START_DATE = '2023-01-01'
    END_DATE = '2025-10-19'
    COUNTRIES = ['US', 'EU', 'GB', 'DE', 'FR', 'JP', 'AU', 'ES', 'IT']
    
    db_path = get_db_path()
    
    # Stats avant
    print_step("Statistiques AVANT re-import")
    conn = duckdb.connect(str(db_path))
    
    total_before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    mom_yoy_before = conn.execute("""
        SELECT COUNT(*) FROM events 
        WHERE event_key LIKE '%_mom' 
           OR event_key LIKE '%_yoy'
           OR event_key LIKE '%_qoq'
    """).fetchone()[0]
    
    print(f"   Total événements : {total_before:,}")
    print(f"   Avec MoM/YoY/QoQ : {mom_yoy_before:,}")
    
    conn.close()
    
    # Générer plages
    date_ranges = generate_date_ranges(START_DATE, END_DATE, chunk_days=30)
    total_chunks = len(date_ranges)
    
    print_step(f"Import par chunks de 30 jours ({total_chunks} chunks)")
    print(f"   Période : {START_DATE} → {END_DATE}")
    print(f"   Pays : {', '.join(COUNTRIES)}")
    
    # Progress
    total_events = 0
    total_errors = 0
    
    for i, (d1, d2) in enumerate(date_ranges, 1):
        try:
            # Afficher progression
            pct = (i / total_chunks) * 100
            print(f"\n   [{i:>3}/{total_chunks}] {pct:>5.1f}% | {d1} → {d2} ... ", end='', flush=True)
            
            # Fetch
            items = fetch_calendar_json(d1, d2, countries=COUNTRIES)
            
            if not items:
                print("⏭️  Aucune donnée")
                continue
            
            # Normalize
            df = calendar_to_events_df(items)
            
            if df.empty:
                print("⏭️  DataFrame vide")
                continue
            
            # Upsert
            n = upsert_events_df(df, str(db_path))
            total_events += n
            
            print(f"✅ {n:>4} événements", flush=True)
            
        except Exception as e:
            print(f"❌ Erreur : {e}", flush=True)
            total_errors += 1
            
            if total_errors > 10:
                print_error("\nTrop d'erreurs consécutives. Abandon.")
                return False
    
    # Stats après
    print_step("Statistiques APRÈS re-import")
    conn = duckdb.connect(str(db_path))
    
    total_after = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    mom_yoy_after = conn.execute("""
        SELECT COUNT(*) FROM events 
        WHERE event_key LIKE '%_mom' 
           OR event_key LIKE '%_yoy'
           OR event_key LIKE '%_qoq'
    """).fetchone()[0]
    
    print(f"   Total événements : {total_after:,}")
    print(f"   Avec MoM/YoY/QoQ : {mom_yoy_after:,}")
    
    # Comparaison
    print("\n   📊 COMPARAISON :")
    print(f"      Total : {total_before:,} → {total_after:,} ({total_after - total_before:+,})")
    print(f"      MoM/YoY/QoQ : {mom_yoy_before:,} → {mom_yoy_after:,} ({mom_yoy_after - mom_yoy_before:+,})")
    
    # Vérification 11 septembre
    print_step("Vérification 11 septembre 2025")
    
    result = conn.execute("""
        SELECT 
            event_key,
            actual,
            estimate,
            CASE 
                WHEN estimate IS NOT NULL AND estimate != 0 
                THEN ABS((actual - estimate) / estimate) * 100
                ELSE 0
            END as surprise_pct
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
          AND event_key LIKE '%inflation%rate%'
        ORDER BY event_key
    """).fetchall()
    
    if result:
        print("\n   Événements Inflation Rate 11 septembre :")
        print(f"   {'Event Key':<45} {'Actual':>10} {'Estimate':>10} {'Surprise':>10}")
        print("   " + "-" * 80)
        
        has_mom = False
        has_yoy = False
        
        for event_key, actual, estimate, surprise in result:
            actual_str = f"{actual:.2f}" if actual is not None else "N/A"
            estimate_str = f"{estimate:.2f}" if estimate is not None else "N/A"
            surprise_str = f"{surprise:.1f}%" if surprise is not None else "N/A"
            
            print(f"   {event_key:<45} {actual_str:>10} {estimate_str:>10} {surprise_str:>10}")
            
            if '_mom' in event_key.lower():
                has_mom = True
            if '_yoy' in event_key.lower():
                has_yoy = True
        
        if has_mom and has_yoy:
            print_success("\n   ✅ Versions MoM et YoY présentes !")
        else:
            print_warning("\n   ⚠️  Versions MoM ou YoY manquantes")
    else:
        print_warning("   Aucun événement inflation trouvé")
    
    conn.close()
    
    # Résumé
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ RE-IMPORT TERMINÉ{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
    
    print(f"\n   📊 Résumé :")
    print(f"      Chunks traités : {total_chunks}")
    print(f"      Total événements importés : {total_events:,}")
    print(f"      Erreurs : {total_errors}")
    
    print(f"\n{Colors.BOLD}Prochaines étapes :{Colors.END}")
    print("1. Vérifier que 11 septembre a les bonnes données")
    print("2. Mettre à jour event_families (variantes MoM/YoY)")
    print("3. Re-valider Session 17")
    
    return True


if __name__ == "__main__":
    try:
        success = reimport_full_history()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nInterrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nErreur fatale : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
