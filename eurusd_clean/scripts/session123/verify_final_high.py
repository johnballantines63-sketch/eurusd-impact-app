"""
Vérification finale événements HIGH 11 septembre

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Vérification finale
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def verify_final_high_events():
    """Vérifier tous HIGH 11 septembre"""
    
    print("=" * 80)
    print("VÉRIFICATION FINALE - ÉVÉNEMENTS HIGH 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND importance = 'HIGH'
    ORDER BY datetime_utc
    """
    
    high_events = conn.execute(query).df()
    
    print(f"✅ TOTAL HIGH : {len(high_events)}")
    print()
    
    for idx, row in high_events.iterrows():
        dt_utc = pd.to_datetime(row['datetime_utc']).tz_localize('UTC')
        dt_bern = dt_utc.tz_convert('Europe/Zurich')
        marker = "🔴"
        if 'current_account' in row['event_name'].lower():
            marker = "⭐"
        print(f"{marker} {dt_bern.strftime('%H:%M')} Bern - {row['country'].upper():3s} - {row['event_name']}")
    
    print()
    
    # Vérifier Current Account spécifiquement
    has_current_account = any('current_account' in name.lower() for name in high_events['event_name'])
    
    if has_current_account:
        print("✅✅✅ Current Account DE inclus comme HIGH !")
    else:
        print("❌ Current Account manquant")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("PRÊT POUR VALIDATION FINALE")
    print("=" * 80)
    print()
    print("python validate_cluster_sept11.py")
    print("python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    verify_final_high_events()
