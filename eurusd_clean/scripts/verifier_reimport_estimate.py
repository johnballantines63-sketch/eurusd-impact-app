#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verifier_reimport_estimate.py
-----------------------------
Vérifie si les événements sans estimate peuvent être réimportés depuis Finnhub
avec un estimate disponible.

Usage:
    python scripts/verifier_reimport_estimate.py --date 2025-08-01
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import duckdb
import requests

# Ajouter src au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

# Clé API Finnhub fournie par l'utilisateur
FINNHUB_API_KEY = "d4f3bq1r01qkcvvgcavgd4f3bq1r01qkcvvgcb00"

def fetch_finnhub_events(api_key: str, from_date: str, to_date: str):
    """
    Récupère les événements depuis Finnhub API
    """
    url = "https://finnhub.io/api/v1/calendar/economic"
    params = {
        "from": from_date,
        "to": to_date,
        "token": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('economicCalendar', [])
        elif response.status_code == 403:
            raise Exception("403 Forbidden - Vérifiez que votre plan Premium est actif")
        elif response.status_code == 401:
            raise Exception("401 Unauthorized - Clé API invalide")
        else:
            raise Exception(f"Erreur API: {response.status_code} - {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erreur requête: {e}")


def normalize_event_key(event_name: str) -> str:
    """
    Normalise le nom d'événement pour correspondre à event_key dans la DB
    """
    # Convertir en minuscules et remplacer certains caractères
    key = event_name.lower().strip()
    # Remplacer espaces multiples par un seul espace
    key = ' '.join(key.split())
    return key


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Vérifie si les événements sans estimate peuvent être réimportés depuis Finnhub"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2025-08-01",
        help="Date à vérifier (YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    
    date_str = args.date
    
    print("=" * 100)
    print(f"VÉRIFICATION RÉIMPORT ESTIMATE - {date_str}")
    print("=" * 100)
    print()
    
    # 1. Identifier les événements sans estimate dans la DB
    print("📊 Étape 1 : Identification des événements sans estimate dans la DB")
    print("-" * 100)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Vérifier aussi les événements avec estimate=0 (pas seulement NULL)
    query = """
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        e.country
    FROM events e
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND (e.estimate IS NULL OR e.estimate = 0)
    ORDER BY e.ts_utc
    """
    
    df_db = conn.execute(query, [date_str]).df()
    conn.close()
    
    if df_db.empty:
        print("✅ Aucun événement sans estimate trouvé dans la DB")
        return
    
    print(f"❌ {len(df_db)} événements sans estimate trouvés :")
    print()
    for _, row in df_db.iterrows():
        print(f"  - {row['event_title']} ({row['event_key']})")
        print(f"    Actual: {row['actual']}, Previous: {row['previous']}")
    print()
    
    # 2. Récupérer les événements depuis Finnhub
    print("📡 Étape 2 : Récupération depuis Finnhub API")
    print("-" * 100)
    
    try:
        events_finnhub = fetch_finnhub_events(FINNHUB_API_KEY, date_str, date_str)
        print(f"✅ {len(events_finnhub)} événements récupérés depuis Finnhub")
        print()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # 3. Comparer les événements
    print("🔍 Étape 3 : Comparaison DB vs Finnhub")
    print("-" * 100)
    print()
    
    # Créer un DataFrame depuis Finnhub
    events_finnhub_list = []
    for event in events_finnhub:
        if event.get('country') == 'US':
            event_key_normalized = normalize_event_key(event.get('event', ''))
            events_finnhub_list.append({
                'event_key_normalized': event_key_normalized,
                'event_name': event.get('event', ''),
                'actual': event.get('actual'),
                'estimate': event.get('estimate'),
                'prev': event.get('prev'),
                'time': event.get('time', ''),
                'country': event.get('country', '')
            })
    
    df_finnhub = pd.DataFrame(events_finnhub_list)
    
    print(f"Événements US dans Finnhub : {len(df_finnhub)}")
    print()
    
    # Comparer chaque événement sans estimate
    found_matches = []
    not_found = []
    
    for _, row_db in df_db.iterrows():
        event_key_db = row_db['event_key'].lower().strip()
        event_title_db = row_db['event_title']
        
        # Chercher correspondance dans Finnhub
        match = None
        for _, row_fh in df_finnhub.iterrows():
            event_key_fh = row_fh['event_key_normalized']
            event_name_fh = row_fh['event_name']
            
            # Comparer event_key ou event_title
            if (event_key_db == event_key_fh or 
                event_title_db.lower().strip() == event_name_fh.lower().strip()):
                match = row_fh
                break
        
        if match is not None:
            found_matches.append({
                'db': row_db,
                'finnhub': match
            })
        else:
            not_found.append(row_db)
    
    # 4. Afficher les résultats
    print("=" * 100)
    print("RÉSULTATS")
    print("=" * 100)
    print()
    
    if found_matches:
        print(f"✅ {len(found_matches)} événements trouvés dans Finnhub :")
        print()
        
        for match in found_matches:
            db_event = match['db']
            fh_event = match['finnhub']
            
            print(f"📋 {db_event['event_title']}")
            print(f"   Event Key DB: {db_event['event_key']}")
            print(f"   Event Name Finnhub: {fh_event['event_name']}")
            print()
            print(f"   DB:")
            print(f"     Actual: {db_event['actual']}")
            print(f"     Estimate: {db_event['estimate']} {'❌ MANQUANT' if pd.isna(db_event['estimate']) or db_event['estimate'] == 0 else '✅'}")
            print(f"     Previous: {db_event['previous']}")
            print()
            print(f"   Finnhub:")
            print(f"     Actual: {fh_event['actual']}")
            print(f"     Estimate: {fh_event['estimate']} {'✅ DISPONIBLE' if pd.notna(fh_event['estimate']) and fh_event['estimate'] != 0 else '❌ MANQUANT'}")
            print(f"     Previous: {fh_event['prev']}")
            print()
            
            if pd.notna(fh_event['estimate']) and fh_event['estimate'] != 0:
                print(f"   ✅✅✅ ESTIMATE DISPONIBLE DANS FINNHUB - RÉIMPORT POSSIBLE")
            else:
                print(f"   ⚠️ Estimate également manquant dans Finnhub")
            print("-" * 100)
            print()
    else:
        print("❌ Aucun événement correspondant trouvé dans Finnhub")
        print()
    
    if not_found:
        print(f"⚠️ {len(not_found)} événements non trouvés dans Finnhub :")
        for event in not_found:
            print(f"  - {event['event_title']} ({event['event_key']})")
        print()
    
    # 5. Proposer réimport si estimate disponible
    events_to_reimport = []
    for match in found_matches:
        fh_event = match['finnhub']
        if pd.notna(fh_event['estimate']) and fh_event['estimate'] != 0:
            events_to_reimport.append(match)
    
    if events_to_reimport:
        print("=" * 100)
        print("PROPOSITION DE RÉIMPORT")
        print("=" * 100)
        print()
        print(f"✅ {len(events_to_reimport)} événements peuvent être réimportés avec estimate :")
        print()
        for match in events_to_reimport:
            print(f"  - {match['db']['event_title']}")
        print()
        print("Pour réimporter, exécutez :")
        print(f"  python scripts/finnhub_import.py --from-date {date_str} --to-date {date_str} --countries US")
    else:
        print("⚠️ Aucun événement ne peut être réimporté avec estimate (estimate manquant dans Finnhub)")


if __name__ == "__main__":
    main()

