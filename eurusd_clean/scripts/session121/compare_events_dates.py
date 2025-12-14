#!/usr/bin/env python3
"""
Comparer événements 1er août vs 11 septembre 2025
"""

import duckdb
import pandas as pd
import pytz

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
tz_bern = pytz.timezone('Europe/Zurich')

def display_events_for_date(date_str, title):
    """Afficher tous événements d'une date"""
    conn = duckdb.connect(db_path, read_only=True)
    
    query = f"""
    SELECT 
        ts_utc,
        country,
        event_title,
        importance_n,
        actual,
        forecast
    FROM events
    WHERE ts_utc >= '{date_str} 00:00:00'
      AND ts_utc < '{date_str} 23:59:59'
    ORDER BY ts_utc
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    print(f"\n{'='*120}")
    print(f"{title} - {len(df)} événements")
    print(f"{'='*120}\n")
    
    if len(df) == 0:
        print("❌ Aucun événement trouvé\n")
        return
    
    # Grouper par heure pour faciliter lecture
    for _, row in df.iterrows():
        event_utc = pd.to_datetime(row['ts_utc'])
        event_bern = event_utc.tz_convert(tz_bern)
        importance = "HIGH" if row['importance_n'] == 3 else ("MED" if row['importance_n'] == 2 else "LOW")
        
        title_str = row['event_title'] if row['event_title'] else "Unknown Event"
        actual = f"A:{row['actual']}" if row['actual'] is not None else "A:-"
        forecast = f"F:{row['forecast']}" if row['forecast'] is not None else "F:-"
        
        print(f"{event_bern.strftime('%H:%M')} CEST | {event_utc.strftime('%H:%M')} UTC | "
              f"{importance:4s} | {row['country']:3s} | {title_str[:45]:45s} | {actual:10s} | {forecast:10s}")

print("="*120)
print("COMPARAISON ÉVÉNEMENTS DB")
print("="*120)

# 11 septembre 2025 (référence connue correcte)
display_events_for_date('2025-09-11', '11 SEPTEMBRE 2025 (RÉFÉRENCE)')

# 1er août 2025 (problème)
display_events_for_date('2025-08-01', '1ER AOÛT 2025 (À VÉRIFIER)')

print("\n" + "="*120)
print("ANALYSE:")
print("="*120)
print("Vérifiez si:")
print("1. Les événements HIGH US du 11 sept (CPI) apparaissent à 14:30 CEST / 12:30 UTC")
print("2. Les événements du 1er août apparaissent aux mêmes heures ou décalés")
print("3. Les titres sont 'Unknown Event' ou corrects")
print("="*120)
