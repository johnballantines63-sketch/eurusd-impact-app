#!/usr/bin/env python3
"""
Script Session 96 : Identifier dates CPI US 2025 disponibles
Objectif : Lister les dates pour tests rigoureux V2.4
"""

import duckdb
from pathlib import Path
from datetime import datetime

# Chemin base de données
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

def identify_cpi_dates():
    """Identifie les dates CPI US 2025 avec score > 40"""
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = """
    SELECT 
        DATE(e.ts_utc) as date,
        COUNT(*) as num_events,
        MAX(ef.empirical_score) as max_score,
        STRING_AGG(DISTINCT e.event_title, ', ') as events
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.country = 'US'
        AND YEAR(e.ts_utc) = 2025
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
        AND (e.event_title LIKE '%CPI%' OR e.event_title LIKE '%Inflation%')
    GROUP BY DATE(e.ts_utc)
    ORDER BY date DESC
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    print("=" * 80)
    print("DATES CPI US 2025 DISPONIBLES (score > 40)")
    print("=" * 80)
    print(f"\nTotal dates trouvées : {len(result)}\n")
    
    for idx, row in result.iterrows():
        print(f"{idx+1}. {row['date']} - {row['num_events']} événements - Score max: {row['max_score']:.1f}")
        print(f"   Événements : {row['events'][:100]}...")
        print()
    
    return result

if __name__ == "__main__":
    dates_df = identify_cpi_dates()
    
    # Sauvegarder en CSV
    output_path = Path(__file__).parent / "dates_cpi_2025.csv"
    dates_df.to_csv(output_path, index=False)
    print(f"\n✅ Résultats sauvegardés : {output_path}")
