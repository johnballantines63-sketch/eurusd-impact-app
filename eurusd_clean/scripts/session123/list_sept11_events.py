"""
Lister TOUS événements 11 septembre avec importance

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Debug complet
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def list_all_sept11_events():
    """Lister tous événements 11 septembre"""
    
    print("=" * 80)
    print("TOUS ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Tous événements USD/EUR
    query_all = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND country IN ('usd', 'eur')
    ORDER BY datetime_utc
    """
    
    all_events = conn.execute(query_all).df()
    
    print(f"Total événements USD/EUR : {len(all_events)}")
    print()
    
    # Par importance
    for imp in ['HIGH', 'MEDIUM', 'LOW']:
        events_imp = all_events[all_events['importance'] == imp]
        print(f"{imp} : {len(events_imp)} événements")
        
        if len(events_imp) > 0 and imp == 'HIGH':
            print()
            for idx, row in events_imp.iterrows():
                print(f"   {row['datetime_utc']} - {row['country'].upper()} - {row['event_name']}")
    
    print()
    print("=" * 80)
    print("HEURES DISTRIBUTION")
    print("=" * 80)
    print()
    
    # Distribution par heure
    all_events['hour'] = pd.to_datetime(all_events['datetime_utc']).dt.hour
    
    hour_dist = all_events.groupby('hour').size().sort_index()
    
    for hour, count in hour_dist.items():
        print(f"   {hour:02d}h : {count:3d} événements")
    
    print()
    
    # Événements entre 10h-15h (zone critique)
    print("=" * 80)
    print("ÉVÉNEMENTS 10h-15h (ZONE CRITIQUE)")
    print("=" * 80)
    print()
    
    critical = all_events[
        (all_events['hour'] >= 10) & 
        (all_events['hour'] <= 15)
    ].sort_values('datetime_utc')
    
    print(f"Total : {len(critical)} événements")
    print()
    
    if len(critical) > 0:
        for idx, row in critical.iterrows():
            marker = "🔴" if row['importance'] == 'HIGH' else "🟡" if row['importance'] == 'MEDIUM' else "⚪"
            print(f"{marker} {row['datetime_utc']} - {row['country'].upper():3s} - {row['importance']:6s} - {row['event_name']}")
    
    print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    list_all_sept11_events()
