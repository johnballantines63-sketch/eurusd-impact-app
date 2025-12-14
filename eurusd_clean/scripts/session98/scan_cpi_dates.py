#!/usr/bin/env python3
"""
Scan DB pour dates CPI 2025 réelles
Session 98 - Sélection dates test
"""

import duckdb
from pathlib import Path
import sys

# Path DB direct
DB_PATH = Path(__file__).resolve().parents[2] / 'fx_impact_app' / 'data' / 'warehouse.duckdb'

def scan_cpi_dates():
    """Scan toutes les dates CPI 2025 avec événements HIGH"""
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = """
    SELECT 
        DATE(e.ts_utc) as date,
        COUNT(*) as num_events,
        MAX(ef.empirical_score) as max_score,
        MIN(TIME(e.ts_utc)) as event_time
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE YEAR(e.ts_utc) = 2025
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
        AND (e.event_title LIKE '%CPI%' OR e.event_title LIKE '%Consumer Price%')
    GROUP BY DATE(e.ts_utc)
    ORDER BY date DESC
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    print("=" * 80)
    print("DATES CPI 2025 DISPONIBLES DANS DB (score > 40)")
    print("=" * 80)
    print()
    
    if len(df) == 0:
        print("❌ Aucune date CPI trouvée")
        return None
    
    print(f"Total dates trouvées : {len(df)}\n")
    
    for idx, row in df.iterrows():
        print(f"{idx+1:2d}. {row['date']} - {row['num_events']:2d} events - score: {row['max_score']:.1f} - time: {row['event_time']}")
    
    print("\n" + "=" * 80)
    return df

if __name__ == "__main__":
    df = scan_cpi_dates()
    
    if df is not None and len(df) >= 10:
        print(f"\n✅ {len(df)} dates disponibles - Sélection 10 pour tests\n")
        selected = df.head(10)
        print("DATES SÉLECTIONNÉES POUR SESSION 98:")
        for idx, row in selected.iterrows():
            print(f"  {idx+1}. {row['date']}")
