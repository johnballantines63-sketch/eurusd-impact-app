#!/usr/bin/env python3
"""
EXTRACTION COMPLÈTE PRIX 24H AVANT 2025-09-11 14:30
Session 92.9 - Debug pic fantôme 1.17445
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "data" / "warehouse.duckdb"
OUTPUT_CSV = Path(__file__).parent / "debug_prices_24h_2025-09-11.csv"

def main():
    print("="*80)
    print("EXTRACTION DONNÉES 24H AVANT 2025-09-11 14:30:00")
    print("="*80)
    
    # Event time (avec timezone +02:00 comme dans DB)
    from datetime import timezone
    tz_bern = timezone(timedelta(hours=2))
    event_time = datetime(2025, 9, 11, 14, 30, 0, tzinfo=tz_bern)
    start_time = event_time - timedelta(hours=24)
    
    print(f"\nPériode extraction:")
    print(f"  Début  : {start_time}")
    print(f"  Fin    : {event_time}")
    print(f"  Durée  : 24 heures")
    
    # Connexion DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    print(f"\n✅ DB connectée : {DB_PATH}")
    
    # Extraction complète
    query = """
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query, [start_time, event_time]).df()
    conn.close()
    
    print(f"\n✅ Lignes extraites : {len(df)}")
    
    if len(df) == 0:
        print("❌ ERREUR : Aucune donnée trouvée !")
        return
    
    # Statistiques
    print(f"\n📊 STATISTIQUES 24H:")
    print(f"  High maximum : {df['high'].max():.5f}")
    print(f"  Low minimum  : {df['low'].min():.5f}")
    print(f"  Range        : {(df['high'].max() - df['low'].min()) * 10000:.1f} pips")
    
    # Trouver où est le high maximum
    idx_high = df['high'].idxmax()
    row_high = df.loc[idx_high]
    print(f"\n🔍 HIGH MAXIMUM TROUVÉ:")
    print(f"  Prix      : {row_high['high']:.5f}")
    print(f"  Datetime  : {row_high['datetime']}")
    print(f"  Open      : {row_high['open']:.5f}")
    print(f"  Close     : {row_high['close']:.5f}")
    print(f"  Low       : {row_high['low']:.5f}")
    
    # Temps depuis high jusqu'à event
    hours_since_high = (event_time - row_high['datetime']).total_seconds() / 3600
    print(f"  Temps écoulé : {hours_since_high:.1f} heures")
    
    # Trouver où est le low minimum
    idx_low = df['low'].idxmin()
    row_low = df.loc[idx_low]
    print(f"\n🔍 LOW MINIMUM TROUVÉ:")
    print(f"  Prix      : {row_low['low']:.5f}")
    print(f"  Datetime  : {row_low['datetime']}")
    print(f"  Open      : {row_low['open']:.5f}")
    print(f"  Close     : {row_low['close']:.5f}")
    print(f"  High      : {row_low['high']:.5f}")
    
    # Temps depuis low jusqu'à event
    hours_since_low = (event_time - row_low['datetime']).total_seconds() / 3600
    print(f"  Temps écoulé : {hours_since_low:.1f} heures")
    
    # Prix au moment de l'event (dernière ligne)
    event_price = df.iloc[-1]['close']
    print(f"\n💰 PRIX AU MOMENT EVENT (14:30):")
    print(f"  Close : {event_price:.5f}")
    
    # Distance du prix event aux pics
    distance_to_high = abs(event_price - row_high['high'])
    distance_to_low = abs(event_price - row_low['low'])
    
    print(f"\n📏 DISTANCES:")
    print(f"  Distance au HIGH : {distance_to_high * 10000:.1f} pips")
    print(f"  Distance au LOW  : {distance_to_low * 10000:.1f} pips")
    
    if distance_to_high < distance_to_low:
        print(f"  → Prix plus proche du HIGH")
        selected_peak = "HIGH"
    else:
        print(f"  → Prix plus proche du LOW")
        selected_peak = "LOW"
    
    # Top 10 highs
    print(f"\n📊 TOP 10 HIGHS SUR PÉRIODE 24H:")
    print(f"{'Datetime':<20} {'High':>10} {'Close':>10} {'Temps (h)':>10}")
    print("-"*80)
    
    df_sorted_high = df.nlargest(10, 'high')
    for _, row in df_sorted_high.iterrows():
        hours = (event_time - row['datetime']).total_seconds() / 3600
        print(f"{str(row['datetime']):<20} {row['high']:>10.5f} {row['close']:>10.5f} {hours:>10.1f}")
    
    # Top 10 lows
    print(f"\n📊 TOP 10 LOWS SUR PÉRIODE 24H:")
    print(f"{'Datetime':<20} {'Low':>10} {'Close':>10} {'Temps (h)':>10}")
    print("-"*80)
    
    df_sorted_low = df.nsmallest(10, 'low')
    for _, row in df_sorted_low.iterrows():
        hours = (event_time - row['datetime']).total_seconds() / 3600
        print(f"{str(row['datetime']):<20} {row['low']:>10.5f} {row['close']:>10.5f} {hours:>10.1f}")
    
    # Sauvegarder CSV complet
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ CSV complet sauvegardé : {OUTPUT_CSV}")
    print(f"   {len(df)} lignes × {len(df.columns)} colonnes")
    
    # Vérifier si 1.17445 existe
    print(f"\n🔍 RECHERCHE PRIX 1.17445:")
    rows_17445 = df[(df['high'] >= 1.17440) & (df['high'] <= 1.17450)]
    
    if len(rows_17445) > 0:
        print(f"  ✅ TROUVÉ {len(rows_17445)} ligne(s) avec high ~1.17445:")
        for _, row in rows_17445.iterrows():
            print(f"     Datetime: {row['datetime']}, High: {row['high']:.5f}")
    else:
        print(f"  ❌ AUCUNE ligne avec high entre 1.17440 et 1.17450")
    
    # Vérifier si 1.17289 existe (pic observé par André)
    print(f"\n🔍 RECHERCHE PRIX 1.17289 (pic observé André):")
    rows_17289 = df[(df['high'] >= 1.17285) & (df['high'] <= 1.17295)]
    
    if len(rows_17289) > 0:
        print(f"  ✅ TROUVÉ {len(rows_17289)} ligne(s) avec high ~1.17289:")
        for _, row in rows_17289.iterrows():
            hours = (event_time - row['datetime']).total_seconds() / 3600
            print(f"     Datetime: {row['datetime']}, High: {row['high']:.5f}, Temps: {hours:.1f}h")
    else:
        print(f"  ❌ AUCUNE ligne avec high entre 1.17285 et 1.17295")
    
    print(f"\n{'='*80}")
    print(f"CONCLUSION:")
    print(f"  High maximum DB   : {df['high'].max():.5f}")
    print(f"  Pic sélectionné   : {selected_peak}")
    print(f"  CSV pour analyse  : {OUTPUT_CSV.name}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
