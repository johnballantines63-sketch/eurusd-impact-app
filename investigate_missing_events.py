#!/usr/bin/env python3
"""
Investigate pourquoi les événements n'ont pas assez de données
"""

import duckdb
import pandas as pd

def investigate():
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)
    
    print("="*80)
    print("  INVESTIGATION DES ÉVÉNEMENTS SANS DONNÉES")
    print("="*80)
    print()
    
    # 1. Vérifier ECB Interest Rate
    print("🔍 ECB Interest Rate Decision")
    print("-" * 80)
    
    ecb_family = conn.execute("""
        SELECT event_key, country, family, impact_level
        FROM event_families
        WHERE event_key LIKE '%ecb%interest%'
           OR family = 'Interest_Rate' AND country IN ('EA', 'EU')
        ORDER BY event_key
    """).fetchall()
    
    print(f"Événements dans event_families: {len(ecb_family)}")
    for ek, c, f, i in ecb_family:
        print(f"  [{c}] {ek} | Famille: {f} | Impact: {i}")
    print()
    
    # Chercher dans events
    ecb_events = conn.execute("""
        SELECT DISTINCT event_key, country, COUNT(*) as occurrences
        FROM events
        WHERE (event_key LIKE '%ecb%interest%' OR event_key LIKE '%ECB%')
            AND actual IS NOT NULL
            AND ts_utc >= '2022-09-01'
        GROUP BY event_key, country
        ORDER BY occurrences DESC
    """).fetchall()
    
    print(f"Événements dans events (avec actual): {len(ecb_events)}")
    for ek, c, cnt in ecb_events:
        print(f"  [{c}] {ek[:60]} | {cnt} occurrences")
    print()
    
    # 2. Vérifier tous les événements EA dans events
    print("🔍 TOUS les événements Eurozone (EA)")
    print("-" * 80)
    
    ea_events = conn.execute("""
        SELECT DISTINCT event_key, COUNT(*) as occurrences
        FROM events
        WHERE country = 'EA'
            AND actual IS NOT NULL
            AND ts_utc >= '2022-09-01'
        GROUP BY event_key
        ORDER BY occurrences DESC
        LIMIT 30
    """).fetchall()
    
    print(f"Total événements EA dans events: {len(ea_events)}")
    print(f"Top 30 par occurrences:")
    for ek, cnt in ea_events:
        print(f"  {ek[:70]} | {cnt} occurrences")
    print()
    
    # 3. Vérifier le mapping entre event_families et events
    print("🔍 PROBLÈME DE MAPPING")
    print("-" * 80)
    
    unmapped = conn.execute("""
        SELECT ef.event_key, ef.country, ef.family, ef.impact_level
        FROM event_families ef
        WHERE ef.impact_level = 'HIGH'
            AND ef.empirical_score IS NULL
            AND NOT EXISTS (
                SELECT 1 FROM events e
                WHERE e.event_key = ef.event_key
                    AND e.country = ef.country
                    AND e.actual IS NOT NULL
                    AND e.ts_utc >= '2022-09-01'
            )
        ORDER BY ef.family, ef.event_key
    """).fetchall()
    
    print(f"Événements HIGH dans event_families SANS correspondance dans events: {len(unmapped)}")
    for ek, c, f, i in unmapped:
        print(f"  [{c}] {ek[:60]}")
        print(f"      Famille: {f}")
    print()
    
    # 4. Suggestions de mapping
    print("🔍 SUGGESTIONS DE MAPPING")
    print("-" * 80)
    
    print("Pour ECB Interest Rate Decision:")
    print("  event_families: 'ecb interest rate decision'")
    print("  Cherchons dans events:")
    
    ecb_like = conn.execute("""
        SELECT DISTINCT event_key, country, COUNT(*) as cnt
        FROM events
        WHERE event_key LIKE '%interest%rate%'
            AND country IN ('EA', 'EU')
            AND actual IS NOT NULL
            AND ts_utc >= '2022-09-01'
        GROUP BY event_key, country
        ORDER BY cnt DESC
    """).fetchall()
    
    for ek, c, cnt in ecb_like:
        print(f"  [{c}] {ek[:60]} | {cnt} occ")
    print()
    
    # 5. Vérifier la période des données
    print("🔍 PÉRIODE DES DONNÉES")
    print("-" * 80)
    
    date_range = conn.execute("""
        SELECT 
            MIN(ts_utc) as first_date,
            MAX(ts_utc) as last_date,
            COUNT(*) as total_events
        FROM events
        WHERE actual IS NOT NULL
    """).fetchone()
    
    first, last, total = date_range
    print(f"Première date: {first}")
    print(f"Dernière date: {last}")
    print(f"Total événements avec actual: {total}")
    print()
    
    # 6. Vérifier les données de prix
    print("🔍 DONNÉES DE PRIX")
    print("-" * 80)
    
    price_range = conn.execute("""
        SELECT 
            MIN(timestamp) as first_ts,
            MAX(timestamp) as last_ts,
            COUNT(*) as total_rows
        FROM prices_1m
    """).fetchone()
    
    if price_range and price_range[0]:
        # Convertir epoch en date
        from datetime import datetime
        first_price = datetime.fromtimestamp(price_range[0])
        last_price = datetime.fromtimestamp(price_range[1])
        total_prices = price_range[2]
        
        print(f"Première date prix: {first_price}")
        print(f"Dernière date prix: {last_price}")
        print(f"Total lignes prix: {total_prices:,}")
    else:
        print("⚠️  Pas de données de prix trouvées")
    print()
    
    conn.close()

if __name__ == "__main__":
    investigate()
