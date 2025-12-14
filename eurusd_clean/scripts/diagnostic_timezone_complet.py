#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSTIC COMPLET DES TIMEZONES - Dukascopy vs Finnhub
========================================================

Vérifie les timezones réelles stockées dans la base de données pour :
- Événements (events.ts_utc)
- Prix Dukascopy (prices_1m, prices_bern si existe)
- Prix Finnhub (prices_finnhub_m1)

Gère correctement l'heure d'hiver/été (DST).

Date: 2025-01-XX
Auteur: Diagnostic automatique
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz
import duckdb

# Ajouter le chemin parent pour les imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH

# Timezone de référence
TZ_BERN = pytz.timezone('Europe/Zurich')
TZ_UTC = pytz.UTC

def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_table_exists(conn, table_name):
    """Vérifie si une table existe"""
    try:
        conn.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
        return True
    except:
        return False

def analyze_timestamp_timezone(ts_str, column_name, table_name):
    """Analyse la timezone d'un timestamp"""
    # Essayer de parser le timestamp
    try:
        if isinstance(ts_str, str):
            ts = pd.to_datetime(ts_str)
        else:
            ts = pd.to_datetime(ts_str)
        
        info = {
            'timestamp': str(ts),
            'has_timezone': ts.tzinfo is not None,
            'timezone_name': str(ts.tzinfo) if ts.tzinfo else 'Naive (sans timezone)',
            'hour': ts.hour,
            'minute': ts.minute,
            'date': ts.date()
        }
        
        # Si timezone-aware, extraire offset
        if ts.tzinfo:
            offset = ts.utcoffset()
            if offset:
                offset_hours = offset.total_seconds() / 3600
                info['offset_hours'] = offset_hours
                
                # Déterminer si c'est UTC, Bern, etc.
                if offset_hours == 0:
                    info['likely_timezone'] = 'UTC'
                elif offset_hours in [1, 2]:
                    info['likely_timezone'] = f'Europe/Zurich (UTC{offset_hours:+.0f})'
                else:
                    info['likely_timezone'] = f'Offset UTC{offset_hours:+.0f}'
        
        return info
    except Exception as e:
        return {'error': str(e)}

def analyze_table_timezones(conn, table_name, datetime_column):
    """Analyse les timezones dans une table"""
    print(f"\n📊 Analyse de la table : {table_name}")
    print(f"   Colonne : {datetime_column}")
    print("-" * 80)
    
    if not check_table_exists(conn, table_name):
        print(f"   ❌ Table {table_name} n'existe pas")
        return None
    
    # Vérifier la structure de la table
    try:
        describe_query = f"DESCRIBE {table_name}"
        structure = conn.execute(describe_query).df()
        print("\n   Structure de la table :")
        for _, row in structure.iterrows():
            print(f"      - {row['column_name']}: {row['column_type']}")
    except Exception as e:
        print(f"   ⚠️  Impossible de décrire la table : {e}")
    
    # Prendre quelques échantillons
    try:
        query = f"""
        SELECT {datetime_column}
        FROM {table_name}
        WHERE {datetime_column} IS NOT NULL
        ORDER BY {datetime_column}
        LIMIT 5
        """
        
        df_sample = conn.execute(query).df()
        
        if df_sample.empty:
            print(f"   ⚠️  Aucune donnée dans {table_name}")
            return None
        
        print(f"\n   Échantillons (5 premiers) :")
        timezone_info_list = []
        
        for idx, row in df_sample.iterrows():
            ts_value = row[datetime_column]
            info = analyze_timestamp_timezone(ts_value, datetime_column, table_name)
            
            if 'error' not in info:
                timezone_info_list.append(info)
                
                print(f"\n   [{idx+1}] Timestamp: {info['timestamp']}")
                print(f"       Date: {info['date']}")
                print(f"       Heure: {info['hour']:02d}:{info['minute']:02d}")
                print(f"       Timezone: {info['timezone_name']}")
                if 'offset_hours' in info:
                    print(f"       Offset: UTC{info['offset_hours']:+.0f}")
                    print(f"       Probable: {info['likely_timezone']}")
            else:
                print(f"   ⚠️  Erreur analyse timestamp: {info['error']}")
        
        # Prendre aussi quelques échantillons récents
        print(f"\n   Échantillons récents (5 derniers) :")
        query_recent = f"""
        SELECT {datetime_column}
        FROM {table_name}
        WHERE {datetime_column} IS NOT NULL
        ORDER BY {datetime_column} DESC
        LIMIT 5
        """
        
        df_recent = conn.execute(query_recent).df()
        for idx, row in df_recent.iterrows():
            ts_value = row[datetime_column]
            info = analyze_timestamp_timezone(ts_value, datetime_column, table_name)
            
            if 'error' not in info:
                print(f"\n   [{idx+1}] Timestamp: {info['timestamp']}")
                print(f"       Date: {info['date']}")
                print(f"       Heure: {info['hour']:02d}:{info['minute']:02d}")
                print(f"       Timezone: {info['timezone_name']}")
                if 'offset_hours' in info:
                    print(f"       Offset: UTC{info['offset_hours']:+.0f}")
        
        return timezone_info_list
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'analyse : {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_event_price_timezone(conn, date_str="2025-09-11"):
    """Compare les timezones entre événements et prix pour une date donnée"""
    print_section(f"COMPARAISON ÉVÉNEMENTS ↔ PRIX - Date: {date_str}")
    
    # Convertir date en datetime pour gérer DST
    target_date = pd.to_datetime(date_str).date()
    
    # Déterminer si c'est l'heure d'été ou d'hiver pour cette date
    # Europe/Zurich : UTC+1 (hiver) ou UTC+2 (été)
    sample_dt = TZ_BERN.localize(datetime(target_date.year, target_date.month, target_date.day, 12, 0))
    offset_hours = sample_dt.utcoffset().total_seconds() / 3600
    is_dst = offset_hours == 2
    season = "ÉTÉ (UTC+2)" if is_dst else "HIVER (UTC+1)"
    
    print(f"📅 Date analysée: {date_str}")
    print(f"   Saison: {season}")
    print(f"   Offset Bern: UTC{offset_hours:+.0f}")
    print()
    
    # CPI US typiquement à 14:30 Bern (12:30 UTC été / 13:30 UTC hiver)
    if is_dst:
        event_hour_bern = 14
        event_hour_utc = 12  # 14:30 Bern = 12:30 UTC en été
    else:
        event_hour_bern = 14
        event_hour_utc = 13  # 14:30 Bern = 13:30 UTC en hiver
    
    print(f"🎯 Événement attendu: CPI US à 14:30 Bern")
    print(f"   En UTC: {event_hour_utc:02d}:30 (saison {season})")
    print()
    
    # Chercher événements CPI US pour cette date
    if check_table_exists(conn, "events"):
        try:
            query_events = f"""
            SELECT ts_utc, event_title, country
            FROM events
            WHERE DATE(ts_utc) = '{date_str}'
              AND event_title ILIKE '%CPI%'
              AND country = 'US'
            ORDER BY ts_utc
            LIMIT 5
            """
            
            df_events = conn.execute(query_events).df()
            
            if not df_events.empty:
                print(f"✅ Événements CPI US trouvés: {len(df_events)}")
                
                for idx, event in df_events.iterrows():
                    ts_utc = event['ts_utc']
                    print(f"\n   Événement {idx+1}: {event['event_title']}")
                    
                    # Analyser timestamp
                    if isinstance(ts_utc, str):
                        ts = pd.to_datetime(ts_utc)
                    else:
                        ts = pd.to_datetime(ts_utc)
                    
                    # Convertir en Bern pour affichage
                    if ts.tzinfo:
                        ts_bern = ts.astimezone(TZ_BERN)
                        ts_utc_clean = ts.astimezone(TZ_UTC)
                    else:
                        # Naive - supposer UTC
                        ts_utc_clean = pd.to_datetime(ts).tz_localize('UTC')
                        ts_bern = ts_utc_clean.astimezone(TZ_BERN)
                    
                    print(f"      ts_utc dans DB: {ts}")
                    print(f"      Heure UTC: {ts_utc_clean.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print(f"      Heure Bern: {ts_bern.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print(f"      Offset UTC: {ts_utc_clean.utcoffset().total_seconds() / 3600:+.0f}h")
                    
                    # Vérifier si c'est bien 14:30 Bern
                    if ts_bern.hour == 14 and ts_bern.minute == 30:
                        print(f"      ✅ CORRECT: 14:30 Bern")
                    else:
                        print(f"      ⚠️  ATTENTION: {ts_bern.hour:02d}:{ts_bern.minute:02d} Bern (attendu 14:30)")
                
                # Prendre le premier événement pour comparaison avec prix
                if len(df_events) > 0:
                    first_event = df_events.iloc[0]
                    event_ts = pd.to_datetime(first_event['ts_utc'])
                    
                    if event_ts.tzinfo:
                        event_utc = event_ts.astimezone(TZ_UTC)
                    else:
                        event_utc = pd.to_datetime(event_ts).tz_localize('UTC')
                    
                    print(f"\n   🔍 Utilisation du premier événement pour comparaison prix:")
                    print(f"      Timestamp UTC: {event_utc.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Comparer avec prix Dukascopy
                    if check_table_exists(conn, "prices_1m"):
                        print(f"\n   📊 Prix Dukascopy (prices_1m):")
                        query_prices_duka = f"""
                        SELECT datetime, open, close
                        FROM prices_1m
                        WHERE DATE(datetime) = '{date_str}'
                          AND EXTRACT(HOUR FROM datetime) = {event_utc.hour}
                          AND EXTRACT(MINUTE FROM datetime) BETWEEN {max(0, event_utc.minute - 5)} AND {min(59, event_utc.minute + 5)}
                        ORDER BY datetime
                        LIMIT 3
                        """
                        
                        try:
                            df_prices_duka = conn.execute(query_prices_duka).df()
                            if not df_prices_duka.empty:
                                for idx, price in df_prices_duka.iterrows():
                                    price_ts = pd.to_datetime(price['datetime'])
                                    print(f"      [{idx+1}] {price_ts} | Open: {price['open']:.5f}")
                            else:
                                print(f"      ⚠️  Aucun prix trouvé à {event_utc.hour:02d}:{event_utc.minute:02d}")
                        except Exception as e:
                            print(f"      ❌ Erreur: {e}")
                    
                    # Comparer avec prix Finnhub
                    if check_table_exists(conn, "prices_finnhub_m1"):
                        print(f"\n   📊 Prix Finnhub (prices_finnhub_m1):")
                        query_prices_finn = f"""
                        SELECT datetime, open, close
                        FROM prices_finnhub_m1
                        WHERE DATE(datetime) = '{date_str}'
                          AND EXTRACT(HOUR FROM datetime) = {event_utc.hour}
                          AND EXTRACT(MINUTE FROM datetime) BETWEEN {max(0, event_utc.minute - 5)} AND {min(59, event_utc.minute + 5)}
                        ORDER BY datetime
                        LIMIT 3
                        """
                        
                        try:
                            df_prices_finn = conn.execute(query_prices_finn).df()
                            if not df_prices_finn.empty:
                                for idx, price in df_prices_finn.iterrows():
                                    price_ts = pd.to_datetime(price['datetime'])
                                    print(f"      [{idx+1}] {price_ts} | Open: {price['open']:.5f}")
                                    
                                    # Analyser timezone
                                    if isinstance(price_ts, pd.Timestamp) and price_ts.tzinfo:
                                        price_utc = price_ts.astimezone(TZ_UTC)
                                        price_bern = price_ts.astimezone(TZ_BERN)
                                        print(f"         UTC: {price_utc.strftime('%H:%M')} | Bern: {price_bern.strftime('%H:%M')}")
                            else:
                                print(f"      ⚠️  Aucun prix trouvé à {event_utc.hour:02d}:{event_utc.minute:02d}")
                        except Exception as e:
                            print(f"      ❌ Erreur: {e}")
            else:
                print(f"⚠️  Aucun événement CPI US trouvé pour {date_str}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche d'événements: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Fonction principale"""
    print_section("DIAGNOSTIC COMPLET DES TIMEZONES - Dukascopy vs Finnhub")
    print("Ce script analyse les timezones réelles stockées dans la base de données")
    print("et identifie les conversions nécessaires, en tenant compte de l'heure d'hiver/été.")
    print()
    
    # Vérifier que la DB existe
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable: {DB_PATH}")
        return 1
    
    print(f"✅ Base de données trouvée: {DB_PATH}")
    print()
    
    # Connexion
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # 1. Analyser les événements
        print_section("1. ANALYSE DES ÉVÉNEMENTS (events.ts_utc)")
        analyze_table_timezones(conn, "events", "ts_utc")
        
        # 2. Analyser prix Dukascopy
        print_section("2. ANALYSE DES PRIX DUKASCOPY")
        analyze_table_timezones(conn, "prices_1m", "datetime")
        
        # Vérifier vue prices_bern si existe
        if check_table_exists(conn, "prices_bern"):
            print("\n📋 Vue prices_bern détectée:")
            analyze_table_timezones(conn, "prices_bern", "datetime")
        
        # 3. Analyser prix Finnhub
        print_section("3. ANALYSE DES PRIX FINNHUB")
        analyze_table_timezones(conn, "prices_finnhub_m1", "datetime")
        
        # 4. Comparaison événements vs prix
        print_section("4. COMPARAISON ÉVÉNEMENTS ↔ PRIX")
        compare_event_price_timezone(conn, "2025-09-11")  # Date référence CPI US
        
        # Tester aussi une date en hiver
        print()
        compare_event_price_timezone(conn, "2025-01-15")  # Date en hiver
        
        # 5. Résumé et recommandations
        print_section("5. RÉSUMÉ ET RECOMMANDATIONS")
        print("Analyse terminée. Vérifier les résultats ci-dessus pour identifier:")
        print("  - Les timezones réelles stockées")
        print("  - Les conversions nécessaires")
        print("  - La gestion DST (heure d'hiver/été)")
        print()
        print("⚠️  IMPORTANT: Comparer les heures entre événements et prix")
        print("   pour la même date et déterminer la règle de conversion correcte.")
        
    finally:
        conn.close()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)




