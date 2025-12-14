#!/usr/bin/env python3
"""
Export Prix et Événements en CSV

Objectif :
1. Extraire prix depuis prices_1m_v pour les dates de validation
2. Extraire événements depuis events pour les dates de validation
3. Générer 2 CSV séparés pour analyse externe

Date : 2025-12-07
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Config
DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
if not DB_PATH.exists():
    DB_PATH = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb')

RESULTS_FILE = Path(__file__).parent.parent / 'outputs' / 'validation_new_dates_results.csv'
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs'

def get_validation_dates():
    """Récupère les dates de validation"""
    if not RESULTS_FILE.exists():
        print(f"❌ Fichier résultats introuvable : {RESULTS_FILE}")
        return []
    
    df = pd.read_csv(RESULTS_FILE)
    return df['date'].unique().tolist()

def export_prices(dates: list):
    """Exporte prix pour les dates de validation"""
    print("📊 Export prix...")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    all_prices = []
    
    for date_str in dates:
        # Fenêtre : 24h avant événement jusqu'à 2h après
        # On charge prix pour toute la journée + fenêtre
        start_dt = f"{date_str} 00:00:00"
        end_dt = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        query = f"""
        SELECT 
            ts_utc,
            close
        FROM prices_1m_v
        WHERE ts_utc >= '{start_dt}'::TIMESTAMP
          AND ts_utc < '{end_dt}'::TIMESTAMP
        ORDER BY ts_utc
        """
        
        df_prices = conn.execute(query).df()
        
        if len(df_prices) > 0:
            df_prices['date'] = date_str
            all_prices.append(df_prices)
            print(f"   ✅ {date_str}: {len(df_prices)} prix")
        else:
            print(f"   ⚠️  {date_str}: Aucun prix trouvé")
    
    conn.close()
    
    if len(all_prices) > 0:
        df_all = pd.concat(all_prices, ignore_index=True)
        output_file = OUTPUT_DIR / 'prices_export.csv'
        df_all.to_csv(output_file, index=False)
        print(f"\n✅ Prix exportés : {output_file}")
        print(f"   Total : {len(df_all)} lignes")
        print(f"   Colonnes : {', '.join(df_all.columns)}")
        return output_file
    else:
        print("❌ Aucun prix à exporter")
        return None

def export_events(dates: list):
    """Exporte événements pour les dates de validation"""
    print("\n📅 Export événements...")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    all_events = []
    
    for date_str in dates:
        query = f"""
        SELECT 
            e.event_key,
            e.event_title,
            e.ts_utc,
            e.country,
            e.actual,
            e.estimate,
            e.previous,
            ef.family,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE DATE(e.ts_utc) = '{date_str}'
            AND e.country = 'US'
        ORDER BY e.ts_utc
        """
        
        df_events = conn.execute(query).df()
        
        if len(df_events) > 0:
            df_events['date'] = date_str
            all_events.append(df_events)
            print(f"   ✅ {date_str}: {len(df_events)} événements")
        else:
            print(f"   ⚠️  {date_str}: Aucun événement trouvé")
    
    conn.close()
    
    if len(all_events) > 0:
        df_all = pd.concat(all_events, ignore_index=True)
        output_file = OUTPUT_DIR / 'events_export.csv'
        df_all.to_csv(output_file, index=False)
        print(f"\n✅ Événements exportés : {output_file}")
        print(f"   Total : {len(df_all)} lignes")
        print(f"   Colonnes : {', '.join(df_all.columns)}")
        return output_file
    else:
        print("❌ Aucun événement à exporter")
        return None

def main():
    print("="*80)
    print("EXPORT PRIX ET ÉVÉNEMENTS EN CSV")
    print("="*80)
    print()
    
    # Récupérer dates de validation
    dates = get_validation_dates()
    
    if len(dates) == 0:
        print("❌ Aucune date de validation trouvée")
        return
    
    print(f"📋 {len(dates)} dates à exporter")
    print()
    
    # Exporter prix
    prices_file = export_prices(dates)
    
    # Exporter événements
    events_file = export_events(dates)
    
    print()
    print("="*80)
    print("✅ EXPORT TERMINÉ")
    print("="*80)
    print()
    
    if prices_file:
        print(f"📊 Prix : {prices_file}")
    if events_file:
        print(f"📅 Événements : {events_file}")
    print()

if __name__ == '__main__':
    main()


