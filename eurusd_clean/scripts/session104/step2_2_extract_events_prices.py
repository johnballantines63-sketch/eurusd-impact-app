#!/usr/bin/env python3
"""
ÉTAPE 2.2 - EXTRACTION ÉVÉNEMENTS + PRIX (44 DATES)
====================================================
Mode: CONCIS pour économiser tokens
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
from datetime import timedelta
import pytz

print("ÉTAPE 2.2 - EXTRACTION 44 DATES")
print("="*60)

# Config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
spec_config = importlib.util.spec_from_file_location("config", project_root / "app" / "config.py")
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger dates
dates_file = Path(__file__).parent / "dates_44_high_impact.csv"
df_dates = pd.read_csv(dates_file)

# Filtrer dates avec prix disponibles (jusqu'au 20 oct 2025)
df_dates['event_date'] = pd.to_datetime(df_dates['event_date'])
df_dates = df_dates[df_dates['event_date'] <= '2025-10-20']

print(f"✅ {len(df_dates)} dates chargées (avec prix disponibles)")

conn = duckdb.connect(str(db_path), read_only=True)
bern_tz = pytz.timezone('Europe/Zurich')

results = []

for idx, row in df_dates.iterrows():
    date_str = str(row['event_date'])
    
    if idx == 0:  # Debug première date
        print(f"\nDEBUG première date: {date_str}")
    
    # Charger événements HIGH de la date
    query_events = f"""
    SELECT e.event_key, e.ts_utc, e.actual, e.estimate, 
           ef.family, ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
        AND e.country = 'US'
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    events = conn.execute(query_events).fetchdf()
    
    if idx == 0:
        print(f"  Events trouvés: {len(events)}")
        if len(events) > 0:
            print(f"  Premier event: {events.iloc[0]['ts_utc']}")
    
    if len(events) == 0:
        if idx == 0:
            print(f"  ❌ Aucun event, skip")
        continue
    
    # Événement principal (premier HIGH)
    event_main = events.iloc[0]
    event_dt = pd.to_datetime(event_main['ts_utc'])
    
    # CORRECTION : Extraire heure directement depuis ts_utc (déjà correct dans DB)
    # Le timestamp DB a déjà la bonne timezone (+01:00 ou +02:00)
    event_dt_str = str(event_dt)
    date_part = event_dt_str.split()[0]  # 2025-10-29
    time_part = event_dt_str.split()[1].split('+')[0]  # 19:00:00
    tz_part = event_dt_str.split('+')[1] if '+' in event_dt_str else '02:00'  # 01:00 ou 02:00
    event_time_local = time_part  # Garder pour output
    
    if idx == 0:
        print(f"  Event datetime DB: {event_dt}")
        print(f"  Query timestamp: {date_part} {time_part}+{tz_part}")
    
    # Charger prix
    query_prices = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{date_part} {time_part}+{tz_part}'::TIMESTAMP - INTERVAL '1 minute'
      AND datetime < '{date_part} {time_part}+{tz_part}'::TIMESTAMP + INTERVAL '120 minutes'
    ORDER BY datetime
    """
    
    prices = conn.execute(query_prices).fetchdf()
    
    if idx == 0:
        print(f"  Prix trouvés: {len(prices)}")
        if len(prices) > 0:
            print(f"  Premier prix: {prices.iloc[0]['datetime']}")
    
    if len(prices) == 0:
        if idx == 0:
            print(f"  ❌ Aucun prix, skip")
        continue
    
    # Mesurer impact (méthode Session 92.5)
    event_dt_aware = bern_tz.localize(event_dt.replace(tzinfo=None))
    price_start = prices[prices['datetime'] < event_dt_aware].iloc[-1]['close'] if len(prices[prices['datetime'] < event_dt_aware]) > 0 else prices.iloc[0]['close']
    
    prices_after = prices[prices['datetime'] >= event_dt_aware]
    if len(prices_after) == 0:
        continue
        
    price_max = prices_after['close'].max()
    price_min = prices_after['close'].min()
    
    if abs(price_max - price_start) > abs(price_min - price_start):
        price_peak = price_max
        impact = (price_peak - price_start) * 10000
    else:
        price_peak = price_min
        impact = (price_start - price_peak) * 10000
    
    # Calculer surprise
    surprise_vals = []
    for _, ev in events.iterrows():
        if pd.notna(ev['actual']) and pd.notna(ev['estimate']) and ev['estimate'] != 0:
            surprise_vals.append(abs((ev['actual'] - ev['estimate']) / ev['estimate']))
    
    surprise_max = max(surprise_vals) if surprise_vals else 0
    
    results.append({
        'date': date_str,
        'event_time': event_time_local,
        'num_events': len(events),
        'max_score': events['empirical_score'].max(),
        'avg_score': events['empirical_score'].mean(),
        'surprise_max': surprise_max,
        'impact_real_pips': impact,
        'price_start': price_start,
        'price_peak': price_peak
    })
    
    print(f"✅ {idx+1}/{len(df_dates)} | {date_str} | {impact:.1f} pips")

conn.close()

# Sauvegarder
df_results = pd.DataFrame(results)
output_file = Path(__file__).parent / "dataset_44_dates_extracted.csv"
df_results.to_csv(output_file, index=False)

print("="*60)
print(f"✅ {len(df_results)} dates extraites")
print(f"📁 {output_file.name}")
print("🎯 Étape 2.2 TERMINÉE")
