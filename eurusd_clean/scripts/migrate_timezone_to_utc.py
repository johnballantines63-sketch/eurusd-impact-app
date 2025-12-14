#!/usr/bin/env python3
"""
MIGRATION TIMEZONE → UTC
========================

Corrige toutes les tables pour stocker les données en UTC avec timezone info.

Étapes :
1. Backup des tables avant migration
2. Corriger prices_1m : Convertir Europe/Zurich → UTC
3. Corriger events : Ajouter timezone UTC
4. Corriger economic_events : Ajouter timezone UTC
5. Mettre à jour la vue prices_bern pour conversion UTC → Europe/Zurich

⚠️  IMPORTANT : Faire un backup complet de la DB avant d'exécuter ce script !
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import duckdb
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'
BACKUP_DIR = PROJECT_ROOT / 'data' / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

parser = argparse.ArgumentParser(description="Migration timezone → UTC")
parser.add_argument('--yes', action='store_true', help="Skip confirmation prompts")
args = parser.parse_args()

print("=" * 80)
print("🔄 MIGRATION TIMEZONE → UTC")
print("=" * 80)
print()
print("⚠️  ATTENTION : Cette migration va modifier les données de la DB")
print("   Assurez-vous d'avoir fait un backup complet avant de continuer !")
print()

# Demander confirmation (sauf si --yes)
if not args.yes:
    response = input("Avez-vous fait un backup de la DB ? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Migration annulée. Faites d'abord un backup de la DB.")
        sys.exit(1)
    
    response = input("Confirmer la migration ? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Migration annulée.")
        sys.exit(1)
else:
    print("✅ Mode non-interactif activé (--yes)")
    print("   Assurez-vous d'avoir fait un backup avant de continuer !")
    print()

print()
print("🚀 Début de la migration...")
print()

conn = duckdb.connect(str(DB_PATH), read_only=False)

# ═══════════════════════════════════════════════════════════════
# 1. BACKUP DES TABLES
# ═══════════════════════════════════════════════════════════════

print("1️⃣ Création des backups...")
print("-" * 80)

backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

try:
    # Backup prices_1m
    print("   Backup prices_1m...")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS prices_1m_backup_tz_{backup_timestamp} AS
        SELECT * FROM prices_1m
    """)
    print("   ✅ Backup prices_1m créé")
    
    # Backup events
    print("   Backup events...")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS events_backup_tz_{backup_timestamp} AS
        SELECT * FROM events
    """)
    print("   ✅ Backup events créé")
    
    # Backup economic_events
    print("   Backup economic_events...")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS economic_events_backup_tz_{backup_timestamp} AS
        SELECT * FROM economic_events
    """)
    print("   ✅ Backup economic_events créé")
    
except Exception as e:
    print(f"   ❌ ERREUR lors du backup : {e}")
    conn.close()
    sys.exit(1)

print()

# ═══════════════════════════════════════════════════════════════
# 2. CORRIGER PRICES_1M (Europe/Zurich → UTC)
# ═══════════════════════════════════════════════════════════════

print("2️⃣ Correction prices_1m (Europe/Zurich → UTC)...")
print("-" * 80)

try:
    # Vérifier l'état actuel
    sample = conn.execute("""
        SELECT datetime
        FROM prices_1m
        WHERE DATE(datetime) = '2025-11-20'
        LIMIT 1
    """).fetchone()
    
    if sample:
        dt_sample = sample[0]
        print(f"   Échantillon avant : {dt_sample} (type: {type(dt_sample).__name__})")
        
        # Si c'est un Timestamp avec timezone Europe/Zurich, convertir en UTC
        if isinstance(dt_sample, pd.Timestamp) and dt_sample.tz is not None:
            # Charger toutes les données
            print("   Chargement des données...")
            df = conn.execute("SELECT * FROM prices_1m ORDER BY datetime").df()
            
            # Convertir datetime de Europe/Zurich vers UTC
            print("   Conversion Europe/Zurich → UTC...")
            df['datetime'] = pd.to_datetime(df['datetime'])
            if df['datetime'].dt.tz is not None:
                # Si déjà avec timezone, convertir en UTC
                df['datetime'] = df['datetime'].dt.tz_convert('UTC')
            else:
                # Si naive, supposer que c'est Europe/Zurich et convertir
                df['datetime'] = df['datetime'].dt.tz_localize('Europe/Zurich').dt.tz_convert('UTC')
            
            # Recréer la table avec les données corrigées
            print("   Recréation de la table...")
            conn.execute("DROP TABLE prices_1m")
            conn.execute("""
                CREATE TABLE prices_1m (
                    datetime TIMESTAMP WITH TIME ZONE,
                    timestamp BIGINT,
                    gmtoffset BIGINT,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume BIGINT
                )
            """)
            
            # Réinsérer les données
            print("   Réinsertion des données...")
            conn.register("df_prices_utc", df)
            conn.execute("""
                INSERT INTO prices_1m
                SELECT datetime, timestamp, gmtoffset, open, high, low, close, volume
                FROM df_prices_utc
            """)
            conn.unregister("df_prices_utc")
            
            # Vérifier
            sample_after = conn.execute("""
                SELECT datetime
                FROM prices_1m
                WHERE DATE(datetime AT TIME ZONE 'UTC') = '2025-11-20'
                LIMIT 1
            """).fetchone()
            
            if sample_after:
                print(f"   Échantillon après : {sample_after[0]} (type: {type(sample_after[0]).__name__})")
            
            print("   ✅ prices_1m corrigé")
        else:
            print("   ℹ️  Les données semblent déjà en UTC ou sans timezone")
    
except Exception as e:
    print(f"   ❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

print()

# ═══════════════════════════════════════════════════════════════
# 3. CORRIGER EVENTS (Ajouter timezone UTC)
# ═══════════════════════════════════════════════════════════════

print("3️⃣ Correction events (Ajouter timezone UTC)...")
print("-" * 80)

try:
    # Vérifier l'état actuel
    sample = conn.execute("""
        SELECT ts_utc
        FROM events
        WHERE DATE(ts_utc) = '2025-11-20'
        LIMIT 1
    """).fetchone()
    
    if sample:
        ts_sample = sample[0]
        print(f"   Échantillon avant : {ts_sample} (type: {type(ts_sample).__name__})")
        
        # Charger toutes les données
        print("   Chargement des données...")
        df = conn.execute("SELECT * FROM events ORDER BY ts_utc").df()
        
        # Corriger timezone : les valeurs numériques sont DÉJÀ en UTC
        # Le timezone +01:00 est une erreur d'import
        # Exemple : 13:30+01:00 devrait être 13:30 UTC (pas 12:30 UTC)
        print("   Correction timezone UTC...")
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
        if df['ts_utc'].dt.tz is None:
            # Si naive, supposer UTC et localiser
            df['ts_utc'] = df['ts_utc'].dt.tz_localize('UTC')
        else:
            # Si déjà avec timezone (probablement +01:00), les valeurs numériques
            # sont DÉJÀ en UTC, donc on retire le timezone incorrect et on re-localise en UTC
            # Exemple : 13:30+01:00 → retirer +01:00 → 13:30 → localiser UTC → 13:30 UTC
            # IMPORTANT : Ne pas convertir (tz_convert) car cela changerait l'heure
            df['ts_utc'] = df['ts_utc'].dt.tz_localize(None).dt.tz_localize('UTC')
        
        # Vérification
        sample_check = df['ts_utc'].iloc[0]
        if sample_check.tz is not None:
            tz_name = str(sample_check.tz)
            print(f"   Échantillon après correction : {sample_check} (TZ: {tz_name})")
        else:
            print(f"   Échantillon après correction : {sample_check} (TZ: None)")
        
        # Recréer la table avec TIMESTAMP WITH TIME ZONE
        print("   Recréation de la table...")
        conn.execute("DROP TABLE events")
        conn.execute("""
            CREATE TABLE events (
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
        
        # Réinsérer les données
        # IMPORTANT : S'assurer que ts_utc est bien en UTC avant insertion
        print("   Réinsertion des données...")
        # Forcer la conversion en UTC si nécessaire
        df_insert = df.copy()
        if df_insert['ts_utc'].dt.tz is not None:
            # Convertir en UTC
            df_insert['ts_utc'] = df_insert['ts_utc'].dt.tz_convert('UTC')
        else:
            # Localiser en UTC
            df_insert['ts_utc'] = df_insert['ts_utc'].dt.tz_localize('UTC')
        
        # Vérifier que c'est bien UTC
        sample_before_insert = df_insert['ts_utc'].iloc[0]
        print(f"   Vérification avant insertion : {sample_before_insert} (TZ: {sample_before_insert.tz})")
        
        conn.register("df_events_utc", df_insert)
        conn.execute("""
            INSERT INTO events
            SELECT ts_utc, country, event_title, event_key, importance_n,
                   actual, previous, estimate, forecast, unit, type, label,
                   comparison, period, change, change_percentage, event_type
            FROM df_events_utc
        """)
        conn.unregister("df_events_utc")
        
        print("   ✅ events corrigé")
    else:
        print("   ℹ️  Aucune donnée dans events")
    
except Exception as e:
    print(f"   ❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

print()

# ═══════════════════════════════════════════════════════════════
# 4. CORRIGER ECONOMIC_EVENTS (Ajouter timezone UTC)
# ═══════════════════════════════════════════════════════════════

print("4️⃣ Correction economic_events (Ajouter timezone UTC)...")
print("-" * 80)

try:
    # Vérifier l'état actuel
    sample = conn.execute("""
        SELECT datetime_utc
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-11-20'
        LIMIT 1
    """).fetchone()
    
    if sample:
        dt_sample = sample[0]
        print(f"   Échantillon avant : {dt_sample} (type: {type(dt_sample).__name__})")
        
        # Charger toutes les données
        print("   Chargement des données...")
        df = conn.execute("SELECT * FROM economic_events ORDER BY datetime_utc").df()
        
        # Corriger timezone : convertir en UTC
        print("   Correction timezone UTC...")
        df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
        if df['datetime_utc'].dt.tz is None:
            # Si naive, supposer UTC et localiser
            df['datetime_utc'] = df['datetime_utc'].dt.tz_localize('UTC')
        else:
            # Si déjà avec timezone, CONVERTIR en UTC (pas juste re-localiser)
            df['datetime_utc'] = df['datetime_utc'].dt.tz_convert('UTC')
        
        # Recréer la table avec TIMESTAMP WITH TIME ZONE
        print("   Recréation de la table...")
        conn.execute("DROP TABLE economic_events")
        conn.execute("""
            CREATE TABLE economic_events (
                event_id VARCHAR,
                datetime_utc TIMESTAMP WITH TIME ZONE,
                event_name VARCHAR,
                country VARCHAR,
                importance VARCHAR,
                actual DOUBLE,
                forecast DOUBLE,
                previous DOUBLE,
                source VARCHAR,
                raw_data JSON
            )
        """)
        
        # Réinsérer les données
        print("   Réinsertion des données...")
        conn.register("df_economic_events_utc", df)
        conn.execute("""
            INSERT INTO economic_events
            SELECT event_id, datetime_utc, event_name, country, importance,
                   actual, forecast, previous, source, raw_data
            FROM df_economic_events_utc
        """)
        conn.unregister("df_economic_events_utc")
        
        print("   ✅ economic_events corrigé")
    else:
        print("   ℹ️  Aucune donnée dans economic_events")
    
except Exception as e:
    print(f"   ❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

print()

# ═══════════════════════════════════════════════════════════════
# 5. METTRE À JOUR LA VUE PRICES_BERN
# ═══════════════════════════════════════════════════════════════

print("5️⃣ Mise à jour de la vue prices_bern (UTC → Europe/Zurich)...")
print("-" * 80)

try:
    # Supprimer l'ancienne vue
    conn.execute("DROP VIEW IF EXISTS prices_bern")
    
    # Créer la nouvelle vue avec conversion UTC → Europe/Zurich
    conn.execute("""
        CREATE VIEW prices_bern AS
        SELECT 
            datetime AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich' as datetime,
            open,
            high,
            low,
            close,
            volume
        FROM prices_1m
    """)
    
    # Vérifier
    sample = conn.execute("""
        SELECT datetime
        FROM prices_bern
        WHERE DATE(datetime) = '2025-11-20'
        LIMIT 1
    """).fetchone()
    
    if sample:
        print(f"   Échantillon : {sample[0]}")
    
    print("   ✅ Vue prices_bern mise à jour")
    
except Exception as e:
    print(f"   ❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

print()

# ═══════════════════════════════════════════════════════════════
# 6. VÉRIFICATION FINALE
# ═══════════════════════════════════════════════════════════════

print("6️⃣ Vérification finale...")
print("-" * 80)

try:
    # Vérifier prices_1m
    count_prices = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    print(f"   ✅ prices_1m : {count_prices:,} lignes")
    
    # Vérifier events
    count_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"   ✅ events : {count_events:,} lignes")
    
    # Vérifier economic_events
    count_economic = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"   ✅ economic_events : {count_economic:,} lignes")
    
    # Test de cohérence : Prix et événements à 14:30 heure de Berne (20.11.2025)
    print()
    print("   Test de cohérence (20.11.2025 14:30 heure de Berne) :")
    
    # Prix à 14:30 heure de Berne
    price_query = """
    SELECT datetime, (high - low) * 10000 as range_pips
    FROM prices_bern
    WHERE datetime >= '2025-11-20 14:29:00' AND datetime < '2025-11-20 14:31:00'
    ORDER BY range_pips DESC
    LIMIT 1
    """
    price_result = conn.execute(price_query).fetchone()
    
    # Événements à 13:30 UTC (devrait être 14:30 heure de Berne)
    event_query = """
    SELECT ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich' as ts_bern, event_key
    FROM events
    WHERE DATE(ts_utc) = '2025-11-20'
      AND EXTRACT(HOUR FROM ts_utc) = 13
      AND EXTRACT(MINUTE FROM ts_utc) = 30
      AND country = 'US'
    LIMIT 1
    """
    event_result = conn.execute(event_query).fetchone()
    
    if price_result and event_result:
        price_dt = price_result[0]
        event_ts_bern = event_result[0]
        print(f"      Prix à 14:30 (Berne) : {price_dt}")
        print(f"      Event à 14:30 (Berne) : {event_ts_bern}")
        
        if isinstance(price_dt, pd.Timestamp) and isinstance(event_ts_bern, pd.Timestamp):
            if price_dt.hour == event_ts_bern.hour == 14:
                print("      ✅ COHÉRENCE : Les heures correspondent !")
            else:
                print(f"      ⚠️  DÉCALAGE : Prix à {price_dt.hour}:XX, Event à {event_ts_bern.hour}:XX")
    
except Exception as e:
    print(f"   ❌ ERREUR : {e}")

conn.close()

print()
print("=" * 80)
print("✅ MIGRATION TERMINÉE")
print("=" * 80)
print()
print(f"📋 Backups créés avec le suffixe : _tz_{backup_timestamp}")
print("   Vous pouvez restaurer avec :")
print("   DROP TABLE prices_1m;")
print(f"   CREATE TABLE prices_1m AS SELECT * FROM prices_1m_backup_tz_{backup_timestamp};")
print()

