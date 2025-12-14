#!/usr/bin/env python3
"""
Script Session 24 : Réimport complet des prix 1m pour septembre 2025
Objectif : Corriger les données prices_1m qui donnent 18 pips au lieu de 522 pips
"""

import os
import sys
from pathlib import Path
import duckdb
import pandas as pd
import requests
from datetime import datetime, timedelta

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

def fetch_eodhd_intraday(symbol, start_date, end_date, api_key):
    """
    Récupère les données intraday 1m depuis EODHD
    
    Args:
        symbol: Ex "EURUSD.FOREX"
        start_date: datetime UTC
        end_date: datetime UTC
        api_key: Clé API EODHD
    
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
    
    print(f"📡 Requête EODHD intraday...")
    print(f"   Symbol: {symbol}")
    print(f"   From: {start_date} ({from_ts})")
    print(f"   To: {end_date} ({to_ts})")
    
    try:
        r = requests.get(url, params=params, timeout=60)
        
        if r.status_code != 200:
            print(f"❌ Erreur API: {r.status_code} {r.reason}")
            print(f"   URL: {r.url}")
            print(f"   Body: {r.text[:500]}")
            return pd.DataFrame()
        
        data = r.json()
        
        if not data:
            print(f"⚠️ Aucune donnée retournée pour cette période")
            return pd.DataFrame()
        
        print(f"✅ {len(data)} lignes reçues de l'API")
        
        # Créer DataFrame
        df = pd.DataFrame(data)
        
        # Normaliser les colonnes
        if "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        elif "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        else:
            print("❌ Pas de colonne timestamp/datetime dans la réponse")
            return pd.DataFrame()
        
        # Vérifier les colonnes de prix
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                print(f"⚠️ Colonne manquante: {col}")
                # Essayer avec majuscule
                col_upper = col.upper()
                if col_upper in df.columns:
                    df[col] = df[col_upper]
                elif col[0] in df.columns:  # 'o', 'h', 'l', 'c'
                    df[col] = df[col[0]]
                else:
                    df[col] = None
        
        # Ajouter volume si absent
        if "volume" not in df.columns and "v" in df.columns:
            df["volume"] = df["v"]
        elif "volume" not in df.columns:
            df["volume"] = 0
        
        # Sélectionner et réordonner colonnes
        df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()
        
        # Convertir en numeric
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Supprimer lignes avec valeurs manquantes
        df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
        
        # Trier par datetime
        df = df.sort_values("datetime").reset_index(drop=True)
        
        # Supprimer doublons
        df = df.drop_duplicates(subset=["datetime"], keep="last")
        
        print(f"✅ {len(df)} lignes nettoyées et validées")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def import_to_database(df, db_path):
    """
    Importe les données dans la table prices_1m
    
    Args:
        df: DataFrame avec colonnes [datetime, open, high, low, close, volume]
        db_path: Chemin vers warehouse.duckdb
    
    Returns:
        Tuple (nb_before, nb_inserted)
    """
    if df.empty:
        print("⚠️ DataFrame vide, rien à importer")
        return 0, 0
    
    print(f"\n💾 Import dans {db_path}...")
    
    with duckdb.connect(db_path) as con:
        con.execute("SET TimeZone='UTC'")
        
        # Compter lignes avant
        n_before = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        print(f"   Lignes avant: {n_before}")
        
        # Vérifier structure table
        cols_info = con.execute("PRAGMA table_info('prices_1m')").df()
        existing_cols = set(cols_info["name"].str.lower())
        
        print(f"   Colonnes existantes: {existing_cols}")
        
        # Adapter les colonnes du DataFrame
        if existing_cols == {"datetime", "close"}:
            # Table simple: seulement datetime et close
            df_insert = df[["datetime", "close"]].copy()
            insert_cols = "(datetime, close)"
            select_cols = "n.datetime, n.close"
        else:
            # Table complète: toutes les colonnes
            df_insert = df.copy()
            insert_cols = "(datetime, open, high, low, close, volume)"
            select_cols = "n.datetime, n.open, n.high, n.low, n.close, n.volume"
        
        # Enregistrer le DataFrame temporairement
        con.register("new_prices", df_insert)
        
        # Insérer seulement les nouvelles lignes (pas de doublons)
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
        
        # Compter lignes après
        n_after = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        n_inserted = n_after - n_before
        
        print(f"   Lignes après: {n_after}")
        print(f"   Lignes insérées: {n_inserted}")
        
        # Vérifier les dates min/max
        stats = con.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(datetime) as min_date,
                MAX(datetime) as max_date
            FROM prices_1m
        """).df().iloc[0]
        
        print(f"\n📊 Statistiques prices_1m:")
        print(f"   Total: {stats['total']} lignes")
        print(f"   Min: {stats['min_date']}")
        print(f"   Max: {stats['max_date']}")
        
        return n_before, n_inserted

def validate_september_11(db_path):
    """
    Valide que le 11 septembre 2025 donne bien ~522 pips Phase 1
    
    Args:
        db_path: Chemin vers warehouse.duckdb
    
    Returns:
        Tuple (phase1_pips, is_valid)
    """
    print(f"\n🔍 VALIDATION CRITIQUE: 11 septembre 2025 14:30-14:45 UTC")
    
    with duckdb.connect(db_path) as con:
        # Récupérer données Phase 1 (14:30-14:45)
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 14:30:00'
          AND datetime < '2025-09-11 14:45:00'
        ORDER BY datetime
        """
        
        df = con.execute(query).df()
        
        if df.empty:
            print("❌ AUCUNE DONNÉE pour 11 septembre 14:30-14:45")
            return 0, False
        
        print(f"   Lignes trouvées: {len(df)}")
        print(f"   Période: {df['datetime'].min()} → {df['datetime'].max()}")
        
        # Calculer mouvement Phase 1
        # Prix de départ = close à 14:30
        start_price = df.iloc[0]["close"]
        
        # Max et min sur toute la période
        high_price = df["high"].max()
        low_price = df["low"].min()
        
        # Mouvement = distance max depuis le départ
        move_up = (high_price - start_price) * 10000  # en pips
        move_down = (start_price - low_price) * 10000  # en pips
        
        phase1_pips = max(move_up, move_down)
        
        print(f"\n   Prix départ (14:30): {start_price:.5f}")
        print(f"   Prix high: {high_price:.5f}")
        print(f"   Prix low: {low_price:.5f}")
        print(f"   Mouvement UP: {move_up:.2f} pips")
        print(f"   Mouvement DOWN: {move_down:.2f} pips")
        print(f"   PHASE 1: {phase1_pips:.2f} pips")
        
        # Valider (attendu ~522 pips ±50)
        is_valid = 450 <= phase1_pips <= 600
        
        if is_valid:
            print(f"\n   ✅ VALIDATION OK: {phase1_pips:.2f} pips (~522 attendu)")
        else:
            print(f"\n   ❌ VALIDATION ÉCHOUÉE: {phase1_pips:.2f} pips (522 attendu)")
            print(f"   Écart: {abs(phase1_pips - 522):.2f} pips")
        
        return phase1_pips, is_valid

def main():
    """
    Script principal : Import septembre 2025 + validation
    """
    print("=" * 80)
    print("🚀 SESSION 24 - RÉIMPORT PRICES 1M SEPTEMBRE 2025")
    print("=" * 80)
    
    # Configuration
    symbol = "EURUSD.FOREX"
    
    # Période: tout septembre 2025 (large pour être sûr)
    start_date = datetime(2025, 9, 1, 0, 0, 0)
    end_date = datetime(2025, 9, 30, 23, 59, 59)
    
    db_path = get_db_path()
    api_key = get_api_key()
    
    print(f"\n📋 Configuration:")
    print(f"   Symbol: {symbol}")
    print(f"   Période: {start_date} → {end_date}")
    print(f"   DB: {db_path}")
    print(f"   API Key: {api_key[:10]}...")
    
    # Étape 1: Récupérer les données
    print(f"\n{'=' * 80}")
    print("ÉTAPE 1: RÉCUPÉRATION DONNÉES EODHD")
    print("=" * 80)
    
    df = fetch_eodhd_intraday(symbol, start_date, end_date, api_key)
    
    if df.empty:
        print("\n❌ ÉCHEC: Aucune donnée récupérée")
        print("Vérifier:")
        print("  - La clé API EODHD est valide")
        print("  - Le symbol EURUSD.FOREX est correct")
        print("  - La période est disponible sur EODHD")
        return False
    
    # Étape 2: Importer dans la DB
    print(f"\n{'=' * 80}")
    print("ÉTAPE 2: IMPORT DANS DATABASE")
    print("=" * 80)
    
    n_before, n_inserted = import_to_database(df, db_path)
    
    if n_inserted == 0:
        print("\n⚠️ Aucune nouvelle ligne insérée (déjà présentes?)")
    else:
        print(f"\n✅ {n_inserted} nouvelles lignes insérées")
    
    # Étape 3: VALIDATION CRITIQUE
    print(f"\n{'=' * 80}")
    print("ÉTAPE 3: VALIDATION 11 SEPTEMBRE")
    print("=" * 80)
    
    phase1_pips, is_valid = validate_september_11(db_path)
    
    # Résumé final
    print(f"\n{'=' * 80}")
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"Lignes récupérées: {len(df)}")
    print(f"Lignes insérées: {n_inserted}")
    print(f"11 septembre Phase 1: {phase1_pips:.2f} pips")
    print(f"Validation: {'✅ OK' if is_valid else '❌ ÉCHEC'}")
    
    if is_valid:
        print("\n🎉 SUCCÈS! Les données sont correctes.")
        print("   Continuer avec Phase 2: Recalcul des mouvements")
    else:
        print("\n⚠️ ATTENTION! La validation a échoué.")
        print("   STOP - Ne pas continuer avec Phase 2")
        print("   Investiguer pourquoi les données ne correspondent pas")
    
    return is_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
