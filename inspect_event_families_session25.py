#!/usr/bin/env python3
"""
Inspection event_families - Session 25
Trouve les vraies heures d'annonce pour recalculer correctement
"""

import duckdb
import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 INSPECTION EVENT_FAMILIES")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # 1. Structure table
    print("\n📋 Structure event_families:")
    schema = con.execute("DESCRIBE event_families").df()
    print(schema.to_string(index=False))
    
    # 2. Colonnes disponibles
    print("\n📊 Colonnes:")
    for col in schema['column_name']:
        print(f"   - {col}")
    
    # 3. Stats générales
    print("\n📊 Statistiques:")
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(datetime) as min_dt,
            MAX(datetime) as max_dt,
            COUNT(DISTINCT event_name) as unique_events
        FROM event_families
    """).df().iloc[0]
    
    print(f"   Total événements: {stats['total']:,}")
    print(f"   Période: {stats['min_dt']} → {stats['max_dt']}")
    print(f"   Événements uniques: {stats['unique_events']}")
    
    # 4. Échantillon
    print("\n📋 Échantillon (10 premiers):")
    sample = con.execute("""
        SELECT 
            datetime,
            event_name,
            actual,
            forecast,
            surprise_pct,
            impact_score
        FROM event_families
        ORDER BY datetime DESC
        LIMIT 10
    """).df()
    
    print(sample.to_string(index=False))
    
    # 5. Chercher événements avec surprise > 30%
    print("\n" + "=" * 80)
    print("🔥 ÉVÉNEMENTS SURPRISE > 30%")
    print("=" * 80)
    
    extreme = con.execute("""
        SELECT 
            datetime,
            event_name,
            actual,
            forecast,
            surprise_pct,
            impact_score
        FROM event_families
        WHERE ABS(surprise_pct) > 30
        ORDER BY ABS(surprise_pct) DESC
        LIMIT 10
    """).df()
    
    print(f"\nTotal événements surprise > 30%: ", end="")
    count_extreme = con.execute("""
        SELECT COUNT(*) 
        FROM event_families 
        WHERE ABS(surprise_pct) > 30
    """).fetchone()[0]
    print(f"{count_extreme:,}")
    
    print("\nTop 10:")
    for idx, row in extreme.iterrows():
        print(f"\n{idx+1}. {row['datetime']}")
        print(f"   Event: {row['event_name']}")
        print(f"   Surprise: {row['surprise_pct']:.1f}%")
        print(f"   Score: {row['impact_score']:.1f}")
    
    # 6. Vérifier le cas du 11 septembre
    print("\n" + "=" * 80)
    print("🎯 CAS RÉFÉRENCE - 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    sept11 = con.execute("""
        SELECT 
            datetime,
            event_name,
            actual,
            forecast,
            surprise_pct,
            impact_score
        FROM event_families
        WHERE DATE(datetime) = '2025-09-11'
        ORDER BY datetime
    """).df()
    
    if not sept11.empty:
        print(f"\n{len(sept11)} événements le 11 septembre:")
        for idx, row in sept11.iterrows():
            print(f"\n   {row['datetime']}")
            print(f"   {row['event_name']}")
            print(f"   Surprise: {row['surprise_pct']:.1f}% | Score: {row['impact_score']:.1f}")
    else:
        print("\n⚠️ Aucun événement trouvé")
    
    # 7. Compter événements simultanés
    print("\n" + "=" * 80)
    print("📊 ÉVÉNEMENTS SIMULTANÉS")
    print("=" * 80)
    
    simultaneous = con.execute("""
        SELECT 
            datetime,
            COUNT(*) as num_events,
            MAX(impact_score) as max_score,
            MAX(ABS(surprise_pct)) as max_surprise
        FROM event_families
        GROUP BY datetime
        HAVING COUNT(*) > 1
        ORDER BY num_events DESC
        LIMIT 10
    """).df()
    
    print(f"\nTop 10 moments avec plus d'événements:")
    for idx, row in simultaneous.iterrows():
        print(f"\n{idx+1}. {row['datetime']}")
        print(f"   Events: {int(row['num_events'])} | Max score: {row['max_score']:.1f} | Max surprise: {row['max_surprise']:.1f}%")
    
    # 8. Recommandation
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATION POUR RECALCUL")
    print("=" * 80)
    
    print("\nPour recalculer correctement les 944 cas:")
    print("\n1. Charger event_families (pas les time_group agrégés)")
    print("2. Filtrer surprise_pct > 30%")
    print("3. Grouper par datetime (événements simultanés)")
    print("4. Calculer Phase 1 depuis datetime exact")
    print("\nQuery suggérée:")
    print("""
    SELECT 
        datetime,
        COUNT(*) as num_events,
        MAX(impact_score) as max_score,
        MAX(ABS(surprise_pct)) as max_surprise
    FROM event_families
    WHERE ABS(surprise_pct) > 30
    GROUP BY datetime
    ORDER BY datetime
    """)
    
    con.close()
    
    print("\n" + "=" * 80)
    print("Fin inspection")
    print("=" * 80)

if __name__ == "__main__":
    main()
