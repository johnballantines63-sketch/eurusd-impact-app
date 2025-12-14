#!/usr/bin/env python3
"""
Inspection event_impacts_calculated - Session 25
Trouve les vrais événements avec surprise > 30%
"""

import duckdb
import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 INSPECTION EVENT_IMPACTS_CALCULATED")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # Structure
    print("\n📋 Structure:")
    schema = con.execute("DESCRIBE event_impacts_calculated").df()
    print(schema.to_string(index=False))
    
    # Échantillon
    print("\n📋 Échantillon (5 lignes):")
    sample = con.execute("""
        SELECT * FROM event_impacts_calculated
        LIMIT 5
    """).df()
    print(sample.to_string(index=False))
    
    # Stats
    print("\n📊 Statistiques:")
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(ts_utc) as min_dt,
            MAX(ts_utc) as max_dt,
            COUNT(DISTINCT event_key) as unique_events
        FROM event_impacts_calculated
    """).df().iloc[0]
    
    print(f"   Total: {stats['total']:,}")
    print(f"   Période: {stats['min_dt']} → {stats['max_dt']}")
    print(f"   Events uniques: {stats['unique_events']}")
    
    # Chercher surprise > 30%
    print("\n" + "=" * 80)
    print("🔥 ÉVÉNEMENTS SURPRISE > 30%")
    print("=" * 80)
    
    count_extreme = con.execute("""
        SELECT COUNT(*) 
        FROM event_impacts_calculated
        WHERE ABS(surprise_pct) > 30
    """).fetchone()[0]
    
    print(f"\nTotal: {count_extreme:,} événements")
    
    # Top 10
    print("\nTop 10 plus grandes surprises:")
    top = con.execute("""
        SELECT 
            ts_utc,
            event_title,
            surprise_pct,
            empirical_score,
            phase1_pips
        FROM event_impacts_calculated
        WHERE ABS(surprise_pct) > 30
        ORDER BY ABS(surprise_pct) DESC
        LIMIT 10
    """).df()
    
    for idx, row in top.iterrows():
        print(f"\n{idx+1}. {row['ts_utc']}")
        print(f"   Event: {row['event_title']}")
        print(f"   Surprise: {row['surprise_pct']:.1f}%")
        print(f"   Score: {row['empirical_score']:.1f}")
        print(f"   Phase1: {row['phase1_pips']:.2f} pips")
    
    # 11 septembre
    print("\n" + "=" * 80)
    print("🎯 CAS RÉFÉRENCE - 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    sept11 = con.execute("""
        SELECT 
            ts_utc,
            event_title,
            surprise_pct,
            empirical_score,
            phase1_pips
        FROM event_impacts_calculated
        WHERE DATE(ts_utc) = '2025-09-11'
        ORDER BY ts_utc
    """).df()
    
    if not sept11.empty:
        print(f"\n{len(sept11)} événements:")
        for idx, row in sept11.iterrows():
            print(f"\n   {row['ts_utc']}")
            print(f"   {row['event_title']}")
            print(f"   Surprise: {row['surprise_pct']:.1f}% | Phase1: {row['phase1_pips']:.2f} pips")
    else:
        print("\n⚠️ Aucun événement")
    
    # Recommandation
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATION")
    print("=" * 80)
    
    print("\nPOUR RECALCUL CORRECT:")
    print("\n1. Utiliser event_impacts_calculated")
    print("2. Filtrer ABS(surprise_pct) > 30")
    print("3. Utiliser ts_utc comme heure exacte")
    print("4. Recalculer Phase 1 depuis ts_utc")
    
    con.close()

if __name__ == "__main__":
    main()
