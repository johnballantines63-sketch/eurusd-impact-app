#!/usr/bin/env python3
"""
Diagnostic Session 24: Identifier la vraie période du mouvement de 522 pips
Problème: Les données semblent avoir un décalage horaire
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from fx_impact_app.src.config import get_db_path

def analyze_period(con, start_time, label):
    """Analyse une période de 15 minutes"""
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{start_time}'
      AND datetime < '{start_time}'::timestamp + INTERVAL '15 minutes'
    ORDER BY datetime
    """
    
    df = con.execute(query).df()
    
    if df.empty:
        print(f"\n❌ {label}: AUCUNE DONNÉE")
        return None
    
    # Calculer mouvement
    start_price = df.iloc[0]["close"]
    high_price = df["high"].max()
    low_price = df["low"].min()
    
    move_up = (high_price - start_price) * 10000
    move_down = (start_price - low_price) * 10000
    phase1_pips = max(move_up, move_down)
    direction = "UP" if move_up > move_down else "DOWN"
    
    print(f"\n{'=' * 80}")
    print(f"📊 {label}")
    print(f"   Période: {df.iloc[0]['datetime']} → {df.iloc[-1]['datetime']}")
    print(f"   Lignes: {len(df)}")
    print(f"   Prix départ: {start_price:.5f}")
    print(f"   Prix HIGH: {high_price:.5f}")
    print(f"   Prix LOW: {low_price:.5f}")
    print(f"   Mouvement UP: {move_up:.2f} pips")
    print(f"   Mouvement DOWN: {move_down:.2f} pips")
    print(f"   ➡️ MOUVEMENT: {phase1_pips:.2f} pips {direction}")
    
    return phase1_pips

def scan_entire_day(con, date):
    """Scanne toute la journée par périodes de 15 min pour trouver le pic"""
    print(f"\n{'=' * 80}")
    print(f"🔍 SCAN COMPLET: {date}")
    print("=" * 80)
    
    query = f"""
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE DATE(datetime) = '{date}'
    ORDER BY datetime
    """
    
    df = con.execute(query).df()
    
    if df.empty:
        print(f"❌ Aucune donnée pour {date}")
        return
    
    print(f"\n✅ {len(df)} lignes disponibles pour {date}")
    print(f"   Première: {df.iloc[0]['datetime']}")
    print(f"   Dernière: {df.iloc[-1]['datetime']}")
    
    # Chercher la plus grande variation sur 15 minutes glissantes
    max_movement = 0
    max_period_start = None
    max_details = None
    
    for i in range(len(df) - 14):  # Fenêtre glissante de 15 minutes
        window = df.iloc[i:i+15]
        
        start_price = window.iloc[0]["close"]
        high_price = window["high"].max()
        low_price = window["low"].min()
        
        move_up = (high_price - start_price) * 10000
        move_down = (start_price - low_price) * 10000
        movement = max(move_up, move_down)
        
        if movement > max_movement:
            max_movement = movement
            max_period_start = window.iloc[0]["datetime"]
            max_details = {
                'start': start_price,
                'high': high_price,
                'low': low_price,
                'move_up': move_up,
                'move_down': move_down,
                'direction': "UP" if move_up > move_down else "DOWN"
            }
    
    print(f"\n🎯 PLUS GRAND MOUVEMENT SUR 15 MINUTES:")
    print(f"   Début période: {max_period_start}")
    print(f"   Mouvement: {max_movement:.2f} pips {max_details['direction']}")
    print(f"   Prix départ: {max_details['start']:.5f}")
    print(f"   Prix HIGH: {max_details['high']:.5f}")
    print(f"   Prix LOW: {max_details['low']:.5f}")
    print(f"   UP: {max_details['move_up']:.2f} pips")
    print(f"   DOWN: {max_details['move_down']:.2f} pips")
    
    return max_movement, max_period_start

def main():
    print("=" * 80)
    print("🔍 DIAGNOSTIC TIMEZONE - 11 SEPTEMBRE 2025")
    print("=" * 80)
    print("\nObjectif: Trouver où sont les 522 pips dans les données EODHD")
    
    db_path = get_db_path()
    print(f"\nDB: {db_path}")
    
    with duckdb.connect(db_path) as con:
        con.execute("SET TimeZone='UTC'")
        
        # Vérifier données disponibles pour le 11 septembre
        count = con.execute("""
            SELECT COUNT(*) FROM prices_1m
            WHERE DATE(datetime) = '2025-09-11'
        """).fetchone()[0]
        
        print(f"\n📊 Données disponibles pour 2025-09-11: {count} lignes")
        
        if count == 0:
            print("❌ Aucune donnée pour cette date!")
            return
        
        # Test 1: Période originale (celle qu'on testait)
        print(f"\n{'#' * 80}")
        print("TEST 1: Période supposée (14:30-14:45 dans les données)")
        print("#" * 80)
        analyze_period(con, "2025-09-11 14:30:00", "14:30 dans données (peut-être CEST)")
        
        # Test 2: Si c'est en CEST, le vrai UTC serait 2h plus tôt
        print(f"\n{'#' * 80}")
        print("TEST 2: Conversion CEST→UTC (14:30 CEST = 12:30 UTC)")
        print("#" * 80)
        analyze_period(con, "2025-09-11 12:30:00", "12:30 UTC (si données CEST)")
        
        # Test 3: Ou peut-être 2h plus tard
        print(f"\n{'#' * 80}")
        print("TEST 3: Si données en UTC, événement à 14:30 UTC")
        print("#" * 80)
        # Vérifier si on a des données à 14:30 UTC
        has_1430 = con.execute("""
            SELECT COUNT(*) FROM prices_1m
            WHERE datetime >= '2025-09-11 14:30:00'
              AND datetime < '2025-09-11 14:45:00'
        """).fetchone()[0]
        
        if has_1430 > 0:
            analyze_period(con, "2025-09-11 14:30:00", "14:30 UTC (hypothèse UTC)")
        else:
            print("\n❌ Pas de données à 14:30:00 dans cette représentation")
        
        # Test 4: Peut-être décalage dans l'autre sens
        print(f"\n{'#' * 80}")
        print("TEST 4: 16:30 dans les données (14:30 UTC + 2h)")
        print("#" * 80)
        has_1630 = con.execute("""
            SELECT COUNT(*) FROM prices_1m
            WHERE datetime >= '2025-09-11 16:30:00'
              AND datetime < '2025-09-11 16:45:00'
        """).fetchone()[0]
        
        if has_1630 > 0:
            analyze_period(con, "2025-09-11 16:30:00", "16:30 dans données (14:30 UTC + 2h CEST)")
        else:
            print("\n❌ Pas de données à 16:30:00")
        
        # Test 5: SCAN COMPLET de la journée
        print(f"\n{'#' * 80}")
        print("TEST 5: SCAN COMPLET - Chercher le plus grand mouvement")
        print("#" * 80)
        max_movement, max_time = scan_entire_day(con, "2025-09-11")
        
        # Récapitulatif
        print(f"\n{'=' * 80}")
        print("📋 RÉCAPITULATIF")
        print("=" * 80)
        print(f"Plus grand mouvement trouvé: {max_movement:.2f} pips")
        print(f"Heure de début: {max_time}")
        print(f"\nAttendu: 522 pips")
        print(f"Écart: {abs(max_movement - 522):.2f} pips")
        
        if 450 <= max_movement <= 600:
            print(f"\n✅ TROUVÉ! Les données sont correctes.")
            print(f"Le mouvement de 522 pips est à {max_time}")
            print(f"\n💡 CONCLUSION:")
            print(f"   Les données EODHD utilisent probablement un timestamp")
            print(f"   qui ne correspond pas exactement à 14:30 UTC.")
            print(f"   Le vrai mouvement commence à: {max_time}")
        else:
            print(f"\n❌ PROBLÈME: Même le plus grand mouvement ({max_movement:.2f} pips)")
            print(f"   est très loin des 522 pips attendus.")
            print(f"\n⚠️ Hypothèses:")
            print(f"   1. Les données EODHD ne capturent pas ce mouvement")
            print(f"   2. MT5 Session 20 utilisait une autre source de données")
            print(f"   3. Il y a un problème de qualité des données EODHD")

if __name__ == "__main__":
    main()
