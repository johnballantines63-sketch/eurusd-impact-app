#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MISE À JOUR PRIX FINNHUB JUSQU'À AUJOURD'HUI
============================================

Import incrémental des prix EUR/USD M1 depuis Finnhub.
Met à jour depuis la dernière date en DB jusqu'à aujourd'hui.

Source : Finnhub API (Forex Candles)
Table : prices_1m / prices_1m_compat (vue prices_1m_v)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pandas as pd
import duckdb
import requests
import time
from typing import Optional

# Ajouter src au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
DB_PATH = Path('../fx_impact_app/data/warehouse.duckdb')
SYMBOL = 'OANDA:EUR_USD'  # Symbole Finnhub pour EUR/USD
RESOLUTION = '1'  # 1 minute
FINNHUB_API_KEY = None

# Charger clé API depuis .env ou environnement
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
except:
    pass

import os
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')

if not FINNHUB_API_KEY:
    print("❌ FINNHUB_API_KEY non trouvée dans l'environnement")
    print("   Vérifiez que le fichier .env contient : FINNHUB_API_KEY=...")
    sys.exit(1)


def fetch_finnhub_candles(symbol: str, resolution: str, from_ts: int, to_ts: int) -> Optional[pd.DataFrame]:
    """
    Récupère les chandeliers Finnhub pour une période donnée.
    
    Args:
        symbol: Symbole (ex: OANDA:EUR_USD)
        resolution: Résolution (1, 5, 15, 30, 60, D, W, M)
        from_ts: Timestamp début (Unix seconds)
        to_ts: Timestamp fin (Unix seconds)
    
    Returns:
        DataFrame avec colonnes: datetime, open, high, low, close, volume
        ou None en cas d'erreur
    """
    url = 'https://finnhub.io/api/v1/forex/candle'
    params = {
        'symbol': symbol,
        'resolution': resolution,
        'from': from_ts,
        'to': to_ts,
        'token': FINNHUB_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('s') != 'ok':
            print(f"⚠️  Erreur API: {data.get('s')} - {data.get('msg', '')}")
            return None
        
        if not data.get('t') or len(data['t']) == 0:
            return pd.DataFrame()
        
        # Créer DataFrame
        df = pd.DataFrame({
            'datetime': pd.to_datetime(data['t'], unit='s', utc=True),
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data.get('v', [0] * len(data['t']))
        })
        
        return df
    
    except Exception as e:
        print(f"❌ Erreur fetch Finnhub: {e}")
        return None


def get_last_price_date(conn: duckdb.DuckDBPyConnection) -> Optional[datetime]:
    """Récupère la dernière date dans prices_1m_v"""
    try:
        result = conn.execute("SELECT MAX(ts_utc) FROM prices_1m_v").fetchone()
        if result and result[0]:
            last_ts = result[0]
            if isinstance(last_ts, str):
                return pd.to_datetime(last_ts, utc=True).to_pydatetime()
            elif isinstance(last_ts, pd.Timestamp):
                return last_ts.to_pydatetime()
            return last_ts
        return None
    except Exception as e:
        print(f"⚠️  Erreur lecture dernière date: {e}")
        return None


def ensure_storage(conn: duckdb.DuckDBPyConnection) -> str:
    """
    S'assure que les tables existent et retourne la table cible.
    """
    conn.execute("SET TimeZone='UTC'")
    
    # Créer prices_1m_compat si absente
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices_1m_compat (
            datetime TIMESTAMPTZ,
            close DOUBLE
        )
    """)
    
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_1m_compat_dt ON prices_1m_compat(datetime)")
    except:
        pass
    
    # Vérifier si prices_1m existe et sa structure
    try:
        info = conn.execute("PRAGMA table_info('prices_1m')").df()
        if info.empty:
            # Créer prices_1m avec structure minimale
            conn.execute("""
                CREATE TABLE prices_1m (
                    datetime TIMESTAMPTZ,
                    close DOUBLE
                )
            """)
            try:
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_1m_dt ON prices_1m(datetime)")
            except:
                pass
            return 'prices_1m_compat'
        else:
            cols = set(info['name'].str.lower())
            if cols == {'datetime', 'close'}:
                return 'prices_1m'
            else:
                return 'prices_1m_compat'
    except:
        return 'prices_1m_compat'
    
    # Recréer vue
    conn.execute("""
        CREATE OR REPLACE VIEW prices_1m_v AS
        SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
        FROM prices_1m
        WHERE datetime IS NOT NULL
        UNION ALL
        SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
        FROM prices_1m_compat
        WHERE datetime IS NOT NULL
        ORDER BY ts_utc
    """)


def upsert_prices(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame, target_table: str) -> int:
    """Insère les prix en évitant les doublons"""
    if df.empty:
        return 0
    
    # Préparer DataFrame (garder seulement datetime et close)
    df_insert = df[['datetime', 'close']].copy()
    
    # S'assurer que datetime est timezone-aware UTC
    if df_insert['datetime'].dt.tz is None:
        df_insert['datetime'] = df_insert['datetime'].dt.tz_localize('UTC')
    else:
        df_insert['datetime'] = df_insert['datetime'].dt.tz_convert('UTC')
    
    n_before = conn.execute("SELECT COUNT(*) FROM prices_1m_v").fetchone()[0]
    
    # Insérer avec anti-doublon
    conn.register("new_prices_df", df_insert)
    conn.execute(f"""
        INSERT INTO {target_table} (datetime, close)
        SELECT n.datetime, n.close
        FROM new_prices_df n
        WHERE NOT EXISTS (
            SELECT 1 FROM prices_1m_v v
            WHERE v.ts_utc = CAST(n.datetime AS TIMESTAMP)
        )
    """)
    conn.unregister("new_prices_df")
    
    n_after = conn.execute("SELECT COUNT(*) FROM prices_1m_v").fetchone()[0]
    return n_after - n_before


# ============================================================================
# MAIN
# ============================================================================

print("=" * 80)
print("MISE À JOUR PRIX FINNHUB JUSQU'À AUJOURD'HUI")
print("=" * 80)
print()

if not DB_PATH.exists():
    print(f"❌ Base de données introuvable : {DB_PATH}")
    sys.exit(1)

conn = duckdb.connect(str(DB_PATH))

try:
    # Vérifier dernière date
    last_date = get_last_price_date(conn)
    
    if last_date is None:
        print("❌ Table prices_1m_v vide !")
        print("   Utiliser un script d'import complet pour l'historique initial")
        conn.close()
        sys.exit(1)
    
    print(f"📊 État actuel:")
    print(f"   Dernière date en DB: {last_date}")
    
    # Calculer période à importer
    # Commencer 1 minute après dernière date
    # S'assurer que last_date est timezone-aware
    if last_date.tzinfo is None:
        last_date = last_date.replace(tzinfo=timezone.utc)
    
    start_utc = last_date + timedelta(minutes=1)
    end_utc = datetime.now(timezone.utc)
    
    days_to_import = (end_utc - start_utc).days + 1
    
    print(f"   Période manquante: {start_utc.date()} → {end_utc.date()}")
    print(f"   Jours à importer: {days_to_import}")
    print()
    
    if days_to_import <= 0:
        print("✅ Données à jour !")
        conn.close()
        sys.exit(0)
    
    response = input("Confirmer l'import ? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Annulé")
        conn.close()
        sys.exit(1)
    
    # Préparer storage
    target_table = ensure_storage(conn)
    print(f"\n📦 Table cible: {target_table}")
    print()
    
    # Import par chunks (max 1 jour par requête pour éviter limites API)
    print("🚀 Import en cours...")
    print("-" * 80)
    
    all_prices = []
    current_date = start_utc.date()
    end_date = end_utc.date()
    
    chunk_days = 1  # 1 jour par requête (sécuritaire)
    total_chunks = (end_date - current_date).days + 1
    
    for chunk_num in range(total_chunks):
        chunk_start = datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc)
        chunk_end = min(
            datetime.combine(current_date + timedelta(days=chunk_days), datetime.min.time(), tzinfo=timezone.utc),
            end_utc
        )
        
        from_ts = int(chunk_start.timestamp())
        to_ts = int(chunk_end.timestamp())
        
        print(f"  [{chunk_num+1}/{total_chunks}] {current_date}...", end=' ', flush=True)
        
        df_chunk = fetch_finnhub_candles(SYMBOL, RESOLUTION, from_ts, to_ts)
        
        if df_chunk is not None and not df_chunk.empty:
            all_prices.append(df_chunk)
            print(f"✅ {len(df_chunk)} chandeliers")
        else:
            print("⚠️  Aucune donnée")
        
        # Rate limiting (30 calls/second max)
        time.sleep(0.1)
        
        current_date += timedelta(days=chunk_days)
        if current_date > end_date:
            break
    
    if not all_prices:
        print("\n⚠️  Aucune donnée téléchargée")
        conn.close()
        sys.exit(0)
    
    # Concaténer et nettoyer
    df_all = pd.concat(all_prices, ignore_index=True)
    df_all = df_all.drop_duplicates(subset=['datetime']).sort_values('datetime').reset_index(drop=True)
    
    print(f"\n✅ Téléchargement terminé: {len(df_all):,} chandeliers")
    
    # Insérer dans DB
    print("\n💾 Insertion dans DB...")
    n_inserted = upsert_prices(conn, df_all, target_table)
    
    # Stats finales
    stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(ts_utc) as min_date,
            MAX(ts_utc) as max_date
        FROM prices_1m_v
    """).fetchone()
    
    print("\n" + "=" * 80)
    print("MISE À JOUR TERMINÉE")
    print("=" * 80)
    print(f"\n📊 RÉSULTATS:")
    print(f"   Chandeliers téléchargés: {len(df_all):,}")
    print(f"   Chandeliers insérés: {n_inserted:,}")
    print(f"   Total en DB: {stats[0]:,}")
    print(f"   Plage: {stats[1]} → {stats[2]}")
    print("\n✅ Prix à jour !")
    print("=" * 80)

finally:
    conn.close()


