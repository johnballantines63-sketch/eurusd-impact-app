"""
Script Diagnostic - Vérifier Événements DB
==========================================

Vérifie quels événements existent dans la DB pour les dates tests.

Auteur: Session 132
Date: 13 novembre 2025
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
DB_PATH = project_root / 'data' / 'warehouse.duckdb'

print("\n" + "="*70)
print(" DIAGNOSTIC DB - ÉVÉNEMENTS DISPONIBLES")
print("="*70)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Test dates Session 131
test_dates = [
    ("2023-02-03", "NFP US + Inflation EU"),
    ("2023-03-22", "EIA Energy US"),
    ("2025-02-03", "ISM Manufacturing US"),
    ("2025-09-11", "11 septembre ECB+US"),
]

for date_str, description in test_dates:
    print(f"\n{'─'*70}")
    print(f"DATE : {date_str} ({description})")
    print(f"{'─'*70}")
    
    # Chercher événements ce jour (toute la journée)
    query = """
    SELECT 
        ts_utc,
        country,
        event_key,
        event_title,
        importance_n,
        actual,
        estimate
    FROM events
    WHERE DATE(ts_utc) = ?
      AND country IN ('US', 'EU', 'UK', 'CA', 'JP')
      AND importance_n >= 2
    ORDER BY ts_utc
    LIMIT 20
    """
    
    df = conn.execute(query, [date_str]).df()
    
    if len(df) == 0:
        print(f"❌ AUCUN ÉVÉNEMENT trouvé pour {date_str}")
        
        # Chercher dates proches
        print(f"\n🔍 Recherche dates proches (±7 jours)...")
        query_nearby = """
        SELECT 
            DATE(ts_utc) as date,
            COUNT(*) as n_events,
            COUNT(DISTINCT country) as n_countries
        FROM events
        WHERE DATE(ts_utc) BETWEEN DATE(?) - INTERVAL 7 DAY 
                               AND DATE(?) + INTERVAL 7 DAY
          AND country IN ('US', 'EU', 'UK')
          AND importance_n >= 2
        GROUP BY DATE(ts_utc)
        ORDER BY date
        LIMIT 15
        """
        df_nearby = conn.execute(query_nearby, [date_str, date_str]).df()
        
        if len(df_nearby) > 0:
            print("\nDates disponibles proches :")
            for _, row in df_nearby.iterrows():
                print(f"  {row['date']}: {row['n_events']} events, {row['n_countries']} pays")
    else:
        print(f"✅ {len(df)} événements trouvés\n")
        
        # Afficher échantillon
        for i, row in df.head(10).iterrows():
            ts = pd.to_datetime(row['ts_utc'])
            print(f"  {ts.strftime('%H:%M')} {row['country']:3s} {row['event_key']:30s} (imp={row['importance_n']})")
        
        if len(df) > 10:
            print(f"  ... +{len(df)-10} autres événements")

conn.close()

print("\n" + "="*70)
print(" DIAGNOSTIC TERMINÉ")
print("="*70)
print("\n💡 CONCLUSION :")
print("   Si dates manquantes → Tests ne peuvent pas être validés avec DB actuelle")
print("   Si dates présentes → Ajuster timestamps dans test_doublewave_prediction.py")
print()
