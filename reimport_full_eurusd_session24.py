#!/usr/bin/env python3
"""
Script Session 24 : Import COMPLET des prix EURUSD 1m depuis EODHD
Mode 1: Test septembre 2025 uniquement (validation rapide)
Mode 2: Import complet 3 dernières années (2022-2025)
"""

import os
import sys
from pathlib import Path
import duckdb
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import argparse

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from fx_impact_app.src.config import get_db_path
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

def get_api_key():
    """Récupère la clé API EODHD"""
    key = os.getenv("EODHD_API_KEY", "").strip()
    if not key:
        raise RuntimeError("❌ EODHD_API_KEY manquante dans .env")
    return key

def fetch_eodhd_intraday(symbol, start_date, end_date, api_key, retry=3):
    """
    Récupère les données intraday 1m depuis EODHD avec retry
    
    Args:
        symbol: Ex "EURUSD.FOREX"
        start_date: datetime UTC
        end_date: datetime UTC
        api_key: Clé API EODHD
        retry: Nombre de tentatives en cas d'erreur
    
    Returns:
        DataFrame avec colonnes [datetime, open, high, low, close, volume]
    """
    # Convertir en timestamps UNIX
    from_ts = int(start_date.timestamp())
    to_ts = int(end_date.timestamp())
    
    url = f"https://eodhd.com/api/intraday/{symbol}"
    params = {
        "interval": "1m",
        "from": from_ts,
        "to": to_ts,
        "fmt": "json",
        "api_token": api_key,
    }
    
    print(f"   📡 Requête: {start_date.date()} → {end_date.date()}")
    
    for attempt in range(retry):
        try:
            r = requests.get(url, params=params, timeout=60)
            
            if r.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"      ⏳ Rate limit, attente {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if r.status_code != 200:
                print(f"      ⚠️ Erreur {r.status_code}: {r.reason}")
                if attempt < retry - 1:
                    time.sleep(1)
                    continue
                return pd.DataFrame()
            
            data = r.json()
            
            if not data:
                print(f"      ℹ️ Aucune donnée (weekend/férié?)")
                return pd.DataFrame()
            
            # Créer DataFrame
            df = pd.DataFrame(data)
            
            # Normaliser les colonnes
            if "timestamp" in df.columns:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            elif "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
            else:
                print("      ❌ Pas de colonne timestamp/datetime")
                return pd.DataFrame()
            
            # Mapper les colonnes de prix (gérer différents formats)
            col_mapping = {
                "open": ["open", "o", "Open", "OPEN"],
                "high": ["high", "h", "High", "HIGH"],
                "low": ["low", "l", "Low", "LOW"],
                "close": ["close", "c", "Close", "CLOSE"],
                "volume": ["volume", "v", "Volume", "VOLUME"]
            }
            
            for target_col, possible_cols in col_mapping.items():
                if target_col not in df.columns:
                    for col in possible_cols:
                        if col in df.columns:
                            df[target_col] = df[col]
                            break
                    else:
                        # Si toujours pas trouvé, mettre valeur par défaut
                        if target_col == "volume":
                            df[target_col] = 0
                        else:
                            df[target_col] = None
            
            # Sélectionner colonnes finales
            df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()
            
            # Convertir en numeric
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Supprimer lignes avec valeurs manquantes
            df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
            
            # Trier et dédupliquer
            df = df.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last").reset_index(drop=True)
            
            print(f"      ✅ {len(df)} lignes récupérées")
            
            return df
            
        except Exception as e:
            print(f"      ❌ Erreur tentative {attempt + 1}/{retry}: {e}")
            if attempt < retry - 1:
                time.sleep(2)
                continue
            return pd.DataFrame()
    
    return pd.DataFrame()

def import_batch_to_database(df_batch, db_path, table_cols):
    """
    Importe un batch de données dans prices_1m
    
    Args:
        df_batch: DataFrame à importer
        db_path: Chemin DB
        table_cols: Colonnes de la table (set)
    
    Returns:
        Nombre de lignes insérées
    """
    if df_batch.empty:
        return 0
    
    with duckdb.connect(db_path) as con:
        con.execute("SET TimeZone='UTC'")
        
        # Adapter selon structure table
        if table_cols == {"datetime", "close"}:
            df_insert = df_batch[["datetime", "close"]].copy()
            insert_cols = "(datetime, close)"
            select_cols = "n.datetime, n.close"
        else:
            df_insert = df_batch.copy()
            insert_cols = "(datetime, open, high, low, close, volume)"
            select_cols = "n.datetime, n.open, n.high, n.low, n.close, n.volume"
        
        # Insérer
        con.register("new_prices", df_insert)
        con.execute(f"""
            INSERT INTO prices_1m {insert_cols}
            SELECT {select_cols}
            FROM new_prices n
            WHERE NOT EXISTS (
                SELECT 1 FROM prices_1m p
                WHERE p.datetime = n.datetime
            )
        """)
        con.unregister("new_prices")
        
        # Compter insertions
        count = con.execute("""
            SELECT COUNT(*) FROM prices_1m 
            WHERE datetime >= ? AND datetime <= ?
        """, [df_batch['datetime'].min(), df_batch['datetime'].max()]).fetchone()[0]
        
        return count

def import_period(symbol, start_date, end_date, api_key, db_path, chunk_days=7):
    """
    Importe une période en la découpant en chunks
    
    Args:
        symbol: Symbol à importer
        start_date: Date début
        end_date: Date fin
        api_key: Clé API
        db_path: Chemin DB
        chunk_days: Taille des chunks en jours
    
    Returns:
        Tuple (total_fetched, total_inserted)
    """
    # Vérifier structure table
    with duckdb.connect(db_path) as con:
        cols_info = con.execute("PRAGMA table_info('prices_1m')").df()
        table_cols = set(cols_info["name"].str.lower())
    
    total_fetched = 0
    total_inserted = 0
    
    current = start_date
    
    while current < end_date:
        chunk_end = min(current + timedelta(days=chunk_days), end_date)
        
        # Fetch
        df = fetch_eodhd_intraday(symbol, current, chunk_end, api_key)
        
        if not df.empty:
            total_fetched += len(df)
            
            # Import
            n_inserted = import_batch_to_database(df, db_path, table_cols)
            total_inserted += n_inserted
        
        # Pause pour éviter rate limiting
        time.sleep(0.5)
        
        current = chunk_end
    
    return total_fetched, total_inserted

def validate_september_11(db_path):
    """
    Validation CRITIQUE: 11 septembre 2025 = ~522 pips Phase 1
    """
    print(f"\n{'=' * 80}")
    print("🔍 VALIDATION CRITIQUE: 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    with duckdb.connect(db_path) as con:
        # Vérifier présence données
        count = con.execute("""
            SELECT COUNT(*) FROM prices_1m
            WHERE datetime >= '2025-09-11 14:00:00'
              AND datetime <= '2025-09-11 15:00:00'
        """).fetchone()[0]
        
        if count == 0:
            print("❌ AUCUNE DONNÉE pour 11 septembre 14:00-15:00")
            return None, False
        
        print(f"✅ {count} lignes trouvées pour cette période")
        
        # Récupérer Phase 1 (14:30-14:45)
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 14:30:00'
          AND datetime < '2025-09-11 14:45:00'
        ORDER BY datetime
        """
        
        df = con.execute(query).df()
        
        if df.empty:
            print("❌ Aucune donnée exactement 14:30-14:45")
            return None, False
        
        print(f"\n📊 Analyse Phase 1 (14:30-14:45):")
        print(f"   Nombre de minutes: {len(df)}")
        print(f"   Première minute: {df.iloc[0]['datetime']}")
        print(f"   Dernière minute: {df.iloc[-1]['datetime']}")
        
        # Calculer mouvement
        start_price = df.iloc[0]["close"]
        high_price = df["high"].max()
        low_price = df["low"].min()
        
        move_up = (high_price - start_price) * 10000
        move_down = (start_price - low_price) * 10000
        phase1_pips = max(move_up, move_down)
        direction = "UP" if move_up > move_down else "DOWN"
        
        print(f"\n💰 Calcul mouvement:")
        print(f"   Prix départ (14:30): {start_price:.5f}")
        print(f"   Prix HIGH: {high_price:.5f}")
        print(f"   Prix LOW: {low_price:.5f}")
        print(f"   Mouvement UP: {move_up:.2f} pips")
        print(f"   Mouvement DOWN: {move_down:.2f} pips")
        print(f"   PHASE 1: {phase1_pips:.2f} pips {direction}")
        
        # Valider
        expected = 522
        tolerance = 50
        is_valid = (expected - tolerance) <= phase1_pips <= (expected + tolerance)
        
        print(f"\n🎯 Validation:")
        print(f"   Attendu: {expected} pips ±{tolerance}")
        print(f"   Obtenu: {phase1_pips:.2f} pips")
        print(f"   Écart: {abs(phase1_pips - expected):.2f} pips")
        
        if is_valid:
            print(f"   ✅ VALIDATION RÉUSSIE!")
        else:
            print(f"   ❌ VALIDATION ÉCHOUÉE!")
            print(f"   ⚠️ STOP - Investiguer avant de continuer")
        
        return phase1_pips, is_valid

def show_database_stats(db_path):
    """Affiche les statistiques de la base de données"""
    print(f"\n{'=' * 80}")
    print("📊 STATISTIQUES BASE DE DONNÉES")
    print("=" * 80)
    
    with duckdb.connect(db_path) as con:
        stats = con.execute("""
            SELECT 
                COUNT(*) as total_rows,
                MIN(datetime) as min_date,
                MAX(datetime) as max_date,
                COUNT(DISTINCT DATE(datetime)) as distinct_days
            FROM prices_1m
        """).df().iloc[0]
        
        print(f"Total lignes: {stats['total_rows']:,}")
        print(f"Date min: {stats['min_date']}")
        print(f"Date max: {stats['max_date']}")
        print(f"Jours distincts: {stats['distinct_days']}")
        
        # Stats par année
        yearly = con.execute("""
            SELECT 
                YEAR(datetime) as year,
                COUNT(*) as rows,
                MIN(datetime) as first_date,
                MAX(datetime) as last_date
            FROM prices_1m
            GROUP BY YEAR(datetime)
            ORDER BY year
        """).df()
        
        if not yearly.empty:
            print(f"\n📅 Répartition par année:")
            for _, row in yearly.iterrows():
                print(f"   {int(row['year'])}: {row['rows']:,} lignes ({row['first_date']} → {row['last_date']})")

def main():
    parser = argparse.ArgumentParser(description="Import EURUSD 1m depuis EODHD")
    parser.add_argument("--mode", choices=["test", "full"], default="test",
                       help="test=septembre 2025 uniquement, full=3 dernières années")
    parser.add_argument("--chunk-days", type=int, default=7,
                       help="Taille des chunks en jours (défaut: 7)")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 SESSION 24 - IMPORT EURUSD 1M DEPUIS EODHD")
    print("=" * 80)
    
    symbol = "EURUSD.FOREX"
    db_path = get_db_path()
    api_key = get_api_key()
    
    print(f"\n📋 Configuration:")
    print(f"   Mode: {args.mode.upper()}")
    print(f"   Symbol: {symbol}")
    print(f"   DB: {db_path}")
    print(f"   API Key: {api_key[:10]}***")
    print(f"   Chunk size: {args.chunk_days} jours")
    
    # Stats avant
    print(f"\n{'=' * 80}")
    print("📊 ÉTAT AVANT IMPORT")
    print("=" * 80)
    show_database_stats(db_path)
    
    with duckdb.connect(db_path) as con:
        n_before = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    
    # Définir périodes selon mode
    if args.mode == "test":
        print(f"\n{'=' * 80}")
        print("MODE TEST: SEPTEMBRE 2025 UNIQUEMENT")
        print("=" * 80)
        periods = [
            ("Septembre 2025", datetime(2025, 9, 1), datetime(2025, 10, 1))
        ]
    else:  # full
        print(f"\n{'=' * 80}")
        print("MODE COMPLET: 3 DERNIÈRES ANNÉES (2022-2025)")
        print("=" * 80)
        print("⚠️ Ceci peut prendre 30-60 minutes selon l'API")
        
        # Découper par année pour mieux suivre la progression
        periods = [
            ("2022", datetime(2022, 1, 1), datetime(2023, 1, 1)),
            ("2023", datetime(2023, 1, 1), datetime(2024, 1, 1)),
            ("2024", datetime(2024, 1, 1), datetime(2025, 1, 1)),
            ("2025", datetime(2025, 1, 1), datetime(2025, 10, 21))  # Jusqu'à aujourd'hui
        ]
    
    # Import période par période
    total_fetched = 0
    total_inserted = 0
    
    for period_name, start_date, end_date in periods:
        print(f"\n{'=' * 80}")
        print(f"📥 IMPORT: {period_name}")
        print(f"   Période: {start_date.date()} → {end_date.date()}")
        print("=" * 80)
        
        start_time = time.time()
        fetched, inserted = import_period(symbol, start_date, end_date, api_key, db_path, args.chunk_days)
        elapsed = time.time() - start_time
        
        total_fetched += fetched
        total_inserted += inserted
        
        print(f"\n   ✅ {period_name} terminé en {elapsed:.1f}s")
        print(f"      Récupéré: {fetched:,} lignes")
        print(f"      Inséré: {inserted:,} nouvelles lignes")
    
    # Stats après
    print(f"\n{'=' * 80}")
    print("📊 ÉTAT APRÈS IMPORT")
    print("=" * 80)
    show_database_stats(db_path)
    
    with duckdb.connect(db_path) as con:
        n_after = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    
    # VALIDATION CRITIQUE
    phase1_pips, is_valid = validate_september_11(db_path)
    
    # Résumé final
    print(f"\n{'=' * 80}")
    print("🎉 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"Mode: {args.mode.upper()}")
    print(f"Lignes avant: {n_before:,}")
    print(f"Lignes après: {n_after:,}")
    print(f"Nouvelles lignes: {total_inserted:,}")
    print(f"\n11 septembre Phase 1: {phase1_pips:.2f} pips" if phase1_pips else "11 septembre: NON VALIDÉ")
    print(f"Validation: {'✅ RÉUSSIE' if is_valid else '❌ ÉCHOUÉE'}")
    
    if is_valid:
        print(f"\n{'🎉' * 40}")
        print("✅ SUCCÈS COMPLET!")
        print("Les données sont correctes et validées.")
        if args.mode == "test":
            print("\n💡 Pour importer les 3 dernières années complètes:")
            print("   python3 reimport_full_eurusd_session24.py --mode full")
        else:
            print("\n➡️ Prochaine étape: Phase 2 - Recalcul des mouvements")
            print("   Exécuter: calculate_extreme_cases_session23.py")
        print("🎉" * 40)
    else:
        print(f"\n{'⚠️' * 40}")
        print("❌ ATTENTION - Validation échouée")
        print("Ne pas continuer avec Phase 2.")
        print("Investiguer pourquoi les données ne correspondent pas.")
        print("⚠️" * 40)
        return False
    
    return is_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
