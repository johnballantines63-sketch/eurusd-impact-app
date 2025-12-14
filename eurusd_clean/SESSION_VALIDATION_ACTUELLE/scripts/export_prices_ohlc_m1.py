#!/usr/bin/env python3
"""
Export OHLC M1 pour Analyse Empirique EURUSD

Objectif :
- Générer prices_ohlc_m1.csv avec colonnes : ts_utc, open, high, low, close, volume, spread
- Période : 3 ans glissants
- Timeframe : 1 minute
- Format : UTC strict +00:00
- Pas de remplissage des trous (weekends OK)

Date : 2025-12-08
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Config
DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
if not DB_PATH.exists():
    DB_PATH = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb')

OUTPUT_DIR = Path(__file__).parent.parent / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Période : 3 ans glissants
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=3*365)

def floor_to_minute(dt):
    """Snap timestamp vers le bas à la minute"""
    return dt.replace(second=0, microsecond=0)

def export_ohlc_m1():
    """Exporte prix OHLC M1 sur 3 ans (UTC strict)"""
    print("="*80)
    print("📊 EXPORT OHLC M1 (prices_ohlc_m1.csv)")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    start_str = START_DATE.strftime('%Y-%m-%d %H:%M:%S')
    end_str = END_DATE.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Période : {start_str} → {end_str}")
    print(f"Source : prices_1m")
    print()
    
    # Requête SQL pour extraire OHLC + volume
    query = f"""
    SELECT 
        datetime as ts_utc,
        open,
        high,
        low,
        close,
        volume
    FROM prices_1m
    WHERE datetime >= '{start_str}'::TIMESTAMP
      AND datetime < '{end_str}'::TIMESTAMP
    ORDER BY datetime
    """
    
    try:
        df = conn.execute(query).df()
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")
        conn.close()
        return None, None
    
    conn.close()
    
    if len(df) == 0:
        print("❌ Aucun prix trouvé")
        return None, None
    
    print(f"✅ {len(df):,} lignes extraites")
    print()
    
    # Convertir ts_utc en datetime si nécessaire
    if df['ts_utc'].dtype == 'object':
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    # S'assurer que ts_utc est timezone-aware UTC
    if df['ts_utc'].dt.tz is None:
        # Supposer UTC si pas de timezone
        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)
    else:
        # Convertir en UTC si autre timezone
        df['ts_utc'] = df['ts_utc'].dt.tz_convert('UTC')
    
    # Snap vers minute (floor) pour garantir alignement
    df['ts_utc'] = df['ts_utc'].apply(floor_to_minute)
    
    # Formater en ISO 8601 UTC strict (+00:00)
    df['ts_utc'] = df['ts_utc'].dt.strftime('%Y-%m-%d %H:%M:%S+00:00')
    
    # Calculer spread si possible (high - low)
    # Note: spread réel n'est pas disponible dans la table, on calcule high-low comme approximation
    df['spread'] = df['high'] - df['low']
    
    # Réorganiser colonnes selon format demandé
    df_output = df[[
        'ts_utc',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'spread'
    ]].copy()
    
    # Vérifier valeurs manquantes
    missing_cols = []
    for col in ['open', 'high', 'low', 'close']:
        missing = df_output[col].isna().sum()
        if missing > 0:
            missing_cols.append(f"{col}: {missing} ({missing/len(df_output)*100:.1f}%)")
    
    if missing_cols:
        print("⚠️  Colonnes avec valeurs manquantes :")
        for msg in missing_cols:
            print(f"   {msg}")
        print()
    
    # Volume manquant
    volume_missing = df_output['volume'].isna().sum()
    if volume_missing > 0:
        print(f"⚠️  Volume manquant : {volume_missing} ({volume_missing/len(df_output)*100:.1f}%)")
        print("   (Remplacé par 0 pour compatibilité)")
        df_output['volume'] = df_output['volume'].fillna(0).astype(int)
    else:
        df_output['volume'] = df_output['volume'].astype(int)
    
    # Sauvegarder CSV
    output_file = OUTPUT_DIR / 'prices_ohlc_m1.csv'
    df_output.to_csv(output_file, index=False)
    
    print(f"✅ Prix OHLC exportés : {output_file}")
    print(f"   Total : {len(df_output):,} lignes")
    print(f"   Colonnes : {', '.join(df_output.columns)}")
    print()
    
    # Stats
    print("📊 Statistiques :")
    print(f"   Prix min (low) : {df_output['low'].min():.5f}")
    print(f"   Prix max (high) : {df_output['high'].max():.5f}")
    print(f"   Spread moyen : {df_output['spread'].mean():.5f}")
    print(f"   Volume total : {df_output['volume'].sum():,}")
    print()
    
    # Vérifier fréquence
    df_ts = df_output.copy()
    df_ts['ts_utc'] = pd.to_datetime(df_ts['ts_utc'])
    df_ts['dt'] = df_ts['ts_utc'].diff()
    mode_dt = df_ts['dt'].mode()
    if len(mode_dt) > 0:
        mode_minutes = mode_dt.iloc[0].total_seconds() / 60
        print(f"   Fréquence dominante : {mode_minutes:.0f} minutes")
    
    # Range temporel
    min_ts = df_ts['ts_utc'].min()
    max_ts = df_ts['ts_utc'].max()
    print(f"   Range temporel : {min_ts} → {max_ts}")
    print()
    
    return df_output, output_file

def main():
    print("="*80)
    print("EXPORT OHLC M1 - EURUSD")
    print("="*80)
    print()
    
    # Export OHLC
    df_ohlc, ohlc_file = export_ohlc_m1()
    
    if df_ohlc is not None:
        print("="*80)
        print("✅ EXPORT TERMINÉ")
        print("="*80)
        print()
        print("📁 Fichier généré :")
        print(f"   📊 {ohlc_file}")
        print()
        print(f"💾 Taille : {ohlc_file.stat().st_size / 1024 / 1024:.2f} MB")
        print()
        
        # Aperçu des premières lignes
        print("📋 Aperçu (5 premières lignes) :")
        print(df_ohlc.head().to_string(index=False))
        print()
    else:
        print("❌ Échec de l'export")
        print()

if __name__ == '__main__':
    main()


