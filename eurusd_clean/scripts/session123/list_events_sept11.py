"""
Lister événements 11 septembre 2025 depuis DB unifiée

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123
"""

import duckdb
from pathlib import Path
import pandas as pd

# DB unifiée
DB_PATH = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb')

def list_events_sept11():
    """Lister tous événements 11 septembre 2025"""
    
    print("=" * 80)
    print("ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Requête events
    query = """
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
    ORDER BY datetime_utc
    """
    
    df = conn.execute(query).df()
    
    if len(df) == 0:
        print("⚠️  Aucun événement trouvé pour le 11 septembre 2025")
        conn.close()
        return
    
    print(f"📊 Total événements : {len(df)}")
    print()
    
    # Par pays
    by_country = df.groupby('country').size().sort_values(ascending=False)
    
    print("Par pays :")
    for country, count in by_country.items():
        print(f"   {country.upper():5s} : {count:2d} événements")
    
    print()
    print("=" * 80)
    print("LISTE COMPLÈTE")
    print("=" * 80)
    print()
    
    # Afficher tous
    for i, row in df.iterrows():
        # Timezone
        dt_utc = pd.to_datetime(row['datetime_utc'], utc=True)
        dt_bern = dt_utc.tz_convert('Europe/Zurich')
        
        print(f"[{i+1:2d}] {dt_bern.strftime('%H:%M')} Bern | {dt_utc.strftime('%H:%M')} UTC")
        print(f"     {row['country'].upper()} - {row['event_name']}")
        print(f"     Importance: {row['importance'] if row['importance'] else 'N/A'}")
        
        # Valeurs
        actual = f"{row['actual']:.2f}" if pd.notna(row['actual']) else "N/A"
        forecast = f"{row['forecast']:.2f}" if pd.notna(row['forecast']) else "N/A"
        previous = f"{row['previous']:.2f}" if pd.notna(row['previous']) else "N/A"
        
        print(f"     Actual: {actual} | Forecast: {forecast} | Previous: {previous}")
        print()
    
    conn.close()
    
    print("=" * 80)

if __name__ == '__main__':
    list_events_sept11()
