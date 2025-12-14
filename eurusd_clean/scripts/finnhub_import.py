#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finnhub_import.py
-----------------
Import des événements économiques depuis l'API Finnhub Economic Calendar
dans DuckDB.

✅ Source unique : Finnhub uniquement (plan Premium requis)
✅ Support historique et futur
✅ Normalisation des événements au format DB
✅ Gestion des timezones (UTC → Europe/Zurich)

🧰 Prérequis : requests, pandas, duckdb, tqdm
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import re

import requests
import pandas as pd
import duckdb
from tqdm import tqdm
import pytz

# Ajouter src au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import get_finnhub_api_key, DB_PATH, TIMEZONE_BERN

# Mapping pays Finnhub → codes DB
COUNTRY_MAPPING = {
    'US': 'US',
    'GB': 'UK',
    'DE': 'DE',
    'FR': 'FR',
    'IT': 'IT',
    'ES': 'ES',
    'EU': 'EU',
    'CA': 'CA',
    'JP': 'JP',
    'CH': 'CH',
    'AU': 'AU',
    'NZ': 'NZ',
    'CN': 'CN',
    'IN': 'IN',
    'BR': 'BR',
    'MX': 'MX',
    'KR': 'KR',
    'SG': 'SG',
    'HK': 'HK',
    'TW': 'TW',
    'ZA': 'ZA',
    'TR': 'TR',
    'RU': 'RU',
    'PL': 'PL',
    'NL': 'NL',
    'BE': 'BE',
    'AT': 'AT',
    'PT': 'PT',
    'IE': 'IE',
    'GR': 'GR',
    'FI': 'FI',
    'SE': 'SE',
    'NO': 'NO',
    'DK': 'DK',
}

# Mapping impact Finnhub → importance_n
IMPACT_MAPPING = {
    'low': 3,
    'medium': 2,
    'high': 1,
}


def normalize_event_key(event_name: str, country: str) -> str:
    """
    Normalise le nom d'événement en event_key
    
    Args:
        event_name: Nom de l'événement (ex: "US - Initial Jobless Claims")
        country: Code pays (ex: "US")
    
    Returns:
        event_key normalisé (ex: "initial jobless claims")
    """
    # Retirer préfixe pays (ex: "US - " ou "United States - ")
    key = event_name
    if ' - ' in key:
        key = key.split(' - ', 1)[1]
    elif ': ' in key:
        key = key.split(': ', 1)[1]
    
    # Normaliser : minuscules, retirer caractères spéciaux
    key = key.lower().strip()
    key = re.sub(r'[^\w\s]', '', key)  # Retirer ponctuation
    key = re.sub(r'\s+', ' ', key)  # Normaliser espaces
    
    return key


def parse_finnhub_event(event: dict) -> Optional[dict]:
    """
    Parse un événement Finnhub et le convertit au format DB
    
    Args:
        event: Dictionnaire événement depuis Finnhub API
    
    Returns:
        Dictionnaire au format DB ou None si invalide
    """
    try:
        # Time (format: "2020-06-02 01:30:00")
        time_str = event.get('time')
        if not time_str:
            return None
        
        # Parser timestamp (Finnhub retourne en UTC)
        dt_utc = pd.to_datetime(time_str, utc=True)
        
        # Country
        country_code = event.get('country', '').upper()
        country = COUNTRY_MAPPING.get(country_code, country_code)
        
        # Event name
        event_name = event.get('event', '').strip()
        if not event_name:
            return None
        
        # Event key (normalisé)
        event_key = normalize_event_key(event_name, country)
        
        # Importance
        impact_str = event.get('impact', 'medium').lower()
        importance_n = IMPACT_MAPPING.get(impact_str, 2)  # Default: medium
        
        # Values
        actual = event.get('actual')
        estimate = event.get('estimate')
        previous = event.get('prev')  # Finnhub utilise 'prev' pas 'previous'
        
        # Convertir en float si possible
        def to_float(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace(',', '.'))
                except:
                    return None
            return None
        
        actual = to_float(actual)
        estimate = to_float(estimate)
        previous = to_float(previous)
        
        # Unit
        unit = event.get('unit', '')
        
        return {
            'ts_utc': dt_utc,
            'country': country,
            'event_title': event_name,
            'event_key': event_key,
            'importance_n': importance_n,
            'actual': actual,
            'previous': previous,
            'estimate': estimate,
            'forecast': None,  # Finnhub n'a pas de forecast séparé
            'unit': unit if unit else None,
            'type': None,
            'label': None,
            'comparison': None,
            'period': None,
            'change': None,
            'change_percentage': None,
            'event_type': None,
        }
    except Exception as e:
        print(f"   ⚠️  Erreur parsing événement: {e}")
        return None


def fetch_finnhub_events(
    api_key: str,
    from_date: str,
    to_date: str,
    countries: Optional[List[str]] = None
) -> List[dict]:
    """
    Récupère les événements depuis Finnhub API
    
    Args:
        api_key: Clé API Finnhub
        from_date: Date début (YYYY-MM-DD)
        to_date: Date fin (YYYY-MM-DD)
        countries: Liste pays à filtrer (None = tous)
    
    Returns:
        Liste d'événements parsés
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
            events_raw = data.get('economicCalendar', [])
            
            # Parser événements
            events_parsed = []
            for event_raw in events_raw:
                event = parse_finnhub_event(event_raw)
                if event:
                    # Filtrer par pays si demandé
                    if countries and event['country'] not in countries:
                        continue
                    events_parsed.append(event)
            
            return events_parsed
        
        elif response.status_code == 403:
            raise Exception("403 Forbidden - Vérifiez que votre plan Premium est actif")
        elif response.status_code == 401:
            raise Exception("401 Unauthorized - Clé API invalide")
        else:
            raise Exception(f"Erreur API: {response.status_code} - {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erreur requête: {e}")


def delete_events_for_date_range(conn, from_date: datetime, to_date: datetime, tz: str):
    """Supprime les événements existants pour une plage de dates"""
    query = f"""
    DELETE FROM events
    WHERE DATE(ts_utc + INTERVAL '2 hours') >= DATE(? + INTERVAL '2 hours')
      AND DATE(ts_utc + INTERVAL '2 hours') <= DATE(? + INTERVAL '2 hours')
    """
    conn.execute(query, [from_date, to_date])


def upsert_events(conn, events: List[dict]):
    """Insère les événements dans la DB"""
    if not events:
        return 0
    
    # Créer DataFrame
    df = pd.DataFrame(events)
    
    # S'assurer que ts_utc est en UTC avec timezone info
    df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    if df['ts_utc'].dt.tz is None:
        # Si naive, supposer UTC et localiser
        df['ts_utc'] = df['ts_utc'].dt.tz_localize('UTC')
    else:
        # Si déjà avec timezone, convertir en UTC
        df['ts_utc'] = df['ts_utc'].dt.tz_convert('UTC')
    
    # Créer table si nécessaire (avec TIMESTAMP WITH TIME ZONE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            ts_utc TIMESTAMP WITH TIME ZONE,
            country VARCHAR,
            event_title VARCHAR,
            event_key VARCHAR,
            importance_n BIGINT,
            actual DOUBLE,
            previous DOUBLE,
            estimate DOUBLE,
            forecast DOUBLE,
            unit VARCHAR,
            type VARCHAR,
            label VARCHAR,
            comparison VARCHAR,
            period VARCHAR,
            change DOUBLE,
            change_percentage DOUBLE,
            event_type VARCHAR
        )
    """)
    
    # UPSERT : Mettre à jour si existe, insérer sinon
    # Utiliser ts_utc + event_key + country comme clé unique
    conn.register("df_events", df)
    
    # Pour chaque événement, vérifier s'il existe déjà
    for idx, row in df.iterrows():
        # Vérifier si l'événement existe déjà
        existing = conn.execute("""
            SELECT ts_utc, event_key, country, actual
            FROM events
            WHERE ts_utc = ?
              AND event_key = ?
              AND country = ?
            LIMIT 1
        """, [row['ts_utc'], row['event_key'], row['country']]).fetchone()
        
        if existing:
            # Mettre à jour seulement si l'actual est disponible (non NULL)
            if pd.notna(row.get('actual')) and row.get('actual') is not None:
                conn.execute("""
                    UPDATE events
                    SET actual = ?,
                        previous = ?,
                        estimate = ?,
                        forecast = ?,
                        importance_n = ?,
                        event_title = ?
                    WHERE ts_utc = ?
                      AND event_key = ?
                      AND country = ?
                """, [
                    row.get('actual'),
                    row.get('previous'),
                    row.get('estimate'),
                    row.get('forecast'),
                    row.get('importance_n'),
                    row.get('event_title'),
                    row['ts_utc'],
                    row['event_key'],
                    row['country']
                ])
        else:
            # Insérer nouveau
            conn.execute("""
                INSERT INTO events (
                    ts_utc, country, event_title, event_key, importance_n,
                    actual, previous, estimate, forecast, unit, type,
                    label, comparison, period, change, change_percentage, event_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                row['ts_utc'],
                row['country'],
                row.get('event_title', ''),
                row['event_key'],
                row.get('importance_n', 3),
                row.get('actual'),
                row.get('previous'),
                row.get('estimate'),
                row.get('forecast'),
                row.get('unit'),
                row.get('type'),
                row.get('label'),
                row.get('comparison'),
                row.get('period'),
                row.get('change'),
                row.get('change_percentage'),
                row.get('event_type')
            ])
    
    conn.unregister("df_events")
    
    return len(df)


def import_finnhub_events(
    db_path: Path,
    from_date: str,
    to_date: str,
    countries: Optional[List[str]] = None,
    replace: bool = True
):
    """
    Importe les événements Finnhub dans la DB
    
    Args:
        db_path: Chemin vers la DB DuckDB
        from_date: Date début (YYYY-MM-DD)
        to_date: Date fin (YYYY-MM-DD)
        countries: Liste pays à importer (None = tous)
        replace: Si True, remplace les événements existants pour cette période
    """
    print("=" * 80)
    print("IMPORT ÉVÉNEMENTS FINNHUB")
    print("=" * 80)
    print()
    
    # Charger clé API
    api_key = get_finnhub_api_key()
    if not api_key:
        print("❌ Clé API Finnhub non trouvée")
        print("   Vérifiez que le fichier .env contient : FINNHUB_API_KEY=...")
        return
    
    print(f"✅ Clé API chargée : {api_key[:10]}...{api_key[-5:]}\n")
    
    # Parser dates
    try:
        dt_from = pd.to_datetime(from_date)
        dt_to = pd.to_datetime(to_date)
    except Exception as e:
        print(f"❌ Erreur format date: {e}")
        return
    
    print(f"📅 Période : {from_date} à {to_date}")
    if countries:
        print(f"🌍 Pays : {', '.join(countries)}")
    print()
    
    # Récupérer événements
    print("📡 Récupération depuis Finnhub API...")
    try:
        events = fetch_finnhub_events(api_key, from_date, to_date, countries)
        print(f"✅ {len(events)} événements récupérés\n")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    if not events:
        print("⚠️  Aucun événement à importer")
        return
    
    # Connexion DB
    print("💾 Import dans la DB...")
    conn = duckdb.connect(str(db_path))
    
    try:
        # Supprimer événements existants si replace=True
        if replace:
            print(f"   🗑️  Suppression événements existants pour cette période...")
            delete_events_for_date_range(conn, dt_from, dt_to, TIMEZONE_BERN)
        
        # Insérer nouveaux événements
        count = upsert_events(conn, events)
        print(f"   ✅ {count} événements importés")
        
        # Vérification
        query_check = f"""
        SELECT COUNT(*) 
        FROM events 
        WHERE DATE(ts_utc + INTERVAL '2 hours') >= DATE(? + INTERVAL '2 hours')
          AND DATE(ts_utc + INTERVAL '2 hours') <= DATE(? + INTERVAL '2 hours')
        """
        total_after = conn.execute(query_check, [dt_from, dt_to]).fetchone()[0]
        print(f"   📊 Total événements dans DB pour cette période : {total_after}")
        
    finally:
        conn.close()
    
    print("\n✅ Import terminé !")


def main():
    parser = argparse.ArgumentParser(
        description="Import événements économiques depuis Finnhub"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help="Chemin vers la DB DuckDB"
    )
    parser.add_argument(
        "--from-date",
        type=str,
        required=True,
        help="Date début (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to-date",
        type=str,
        required=True,
        help="Date fin (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--countries",
        type=str,
        nargs="+",
        help="Pays à importer (ex: US DE FR)"
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Ne pas remplacer les événements existants (ajouter seulement)"
    )
    
    args = parser.parse_args()
    
    import_finnhub_events(
        db_path=args.db_path,
        from_date=args.from_date,
        to_date=args.to_date,
        countries=args.countries,
        replace=not args.no_replace
    )


if __name__ == "__main__":
    main()

