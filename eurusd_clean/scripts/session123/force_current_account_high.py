"""
Forcer Current Account DE HIGH pour 11 septembre

Ajustement manuel basé sur connaissance trading

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Ajustement Current Account
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def force_current_account_high():
    """Forcer Current Account DE HIGH le 11 septembre"""
    
    print("=" * 80)
    print("AJUSTEMENT CURRENT ACCOUNT 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # Forcer HIGH
    query_update = """
    UPDATE economic_events
    SET importance = 'HIGH'
    WHERE event_name = 'current_account'
      AND DATE(datetime_utc) = '2025-09-11'
      AND country = 'de'
    """
    
    conn.execute(query_update)
    
    print("✅ Current Account DE forcé à HIGH")
    print()
    
    # Vérifier
    query_verify = """
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
    
    high_events = conn.execute(query_verify).df()
    
    print(f"Total HIGH 11 septembre : {len(high_events)}")
    print()
    
    # Afficher avec timezone Bern
    import pandas as pd
    
    for idx, row in high_events.iterrows():
        dt_utc = pd.to_datetime(row['datetime_utc']).tz_localize('UTC')
        dt_bern = dt_utc.tz_convert('Europe/Zurich')
        print(f"   {dt_bern.strftime('%H:%M')} - {row['country'].upper():3s} - {row['event_name']}")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ AJUSTEMENT TERMINÉ")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   python validate_cluster_sept11.py")
    print("   python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    force_current_account_high()
