#!/usr/bin/env python3
"""
ÉTAPE 2.2 - EXTRACTION CORRIGÉE (MÉTHODE SESSION 92.5)
=======================================================
Correction : Utilise EXACTEMENT la méthode validée Session 92.5
Filtre : Seulement clusters ≥8 events (comparables à 11.09)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
from datetime import datetime
import pytz

print("="*80)
print("ÉTAPE 2.2 - EXTRACTION CORRIGÉE (MÉTHODE SESSION 92.5)")
print("="*80)
print()

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
df_dates['event_date'] = pd.to_datetime(df_dates['event_date'])
df_dates = df_dates[df_dates['event_date'] <= '2025-10-20']

print(f"✅ {len(df_dates)} dates chargées")
print()

conn = duckdb.connect(str(db_path), read_only=True)
bern_tz = pytz.timezone('Europe/Zurich')

results = []

for idx, row in df_dates.iterrows():
    date_str = str(row['event_date']).split()[0]
    
    # 1. Charger événements HIGH de la date
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
    
    if len(events) == 0:
        continue
    
    # FILTRE : Seulement clusters ≥8 events
    if len(events) < 8:
        continue
    
    # 2. Événement principal (premier HIGH)
    event_main = events.iloc[0]
    event_ts = event_main['ts_utc']
    
    # 3. MÉTHODE SESSION 92.5 : Extraire timestamp DB exact
    # Le timestamp dans events.ts_utc est DÉJÀ au bon format
    # Ex: "2025-09-11 12:30:00+02:00" pour événement 14:30 Bern
    
    event_str = str(event_ts)
    
    # 4. Charger prix (MÉTHODE SESSION 92.5)
    query_prices = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{event_str}'::TIMESTAMP - INTERVAL '1 minute'
      AND datetime < '{event_str}'::TIMESTAMP + INTERVAL '120 minutes'
    ORDER BY datetime
    """
    
    prices = conn.execute(query_prices).fetchdf()
    
    if len(prices) == 0:
        continue
    
    # 5. MÉTHODE SESSION 92.5 : Prix départ = candle AVANT événement
    event_dt = pd.to_datetime(event_ts)
    
    # Convertir event_dt en timezone aware si pas déjà
    if event_dt.tzinfo is None:
        event_dt = bern_tz.localize(event_dt)
    
    # Prix avant événement
    prices_before = prices[prices['datetime'] < event_dt]
    if len(prices_before) == 0:
        price_start = prices.iloc[0]['close']
    else:
        price_start = prices_before.iloc[-1]['close']
    
    # 6. Chercher pic APRÈS événement (120 min)
    prices_after = prices[prices['datetime'] >= event_dt]
    
    if len(prices_after) == 0:
        continue
    
    price_max = prices_after['close'].max()
    price_min = prices_after['close'].min()
    
    # 7. Direction mouvement (comme Session 92.5)
    move_up = abs(price_max - price_start)
    move_down = abs(price_start - price_min)
    
    if move_up > move_down:
        # Mouvement UP
        price_peak = price_max
        impact_pips = (price_peak - price_start) * 10000
        direction = "UP"
    else:
        # Mouvement DOWN
        price_peak = price_min
        impact_pips = (price_start - price_peak) * 10000
        direction = "DOWN"
    
    # 8. Calculer surprise
    surprise_vals = []
    for _, ev in events.iterrows():
        if pd.notna(ev['actual']) and pd.notna(ev['estimate']) and ev['estimate'] != 0:
            surprise_vals.append(abs((ev['actual'] - ev['estimate']) / ev['estimate']))
    
    surprise_max = max(surprise_vals) if surprise_vals else 0
    surprise_avg = sum(surprise_vals) / len(surprise_vals) if surprise_vals else 0
    
    # 9. Sauvegarder
    results.append({
        'date': date_str,
        'event_time': event_dt.strftime('%H:%M:%S'),
        'num_events': len(events),
        'max_score': events['empirical_score'].max(),
        'avg_score': events['empirical_score'].mean(),
        'surprise_max': surprise_max,
        'surprise_avg': surprise_avg,
        'impact_real_pips': impact_pips,
        'direction': direction,
        'price_start': price_start,
        'price_peak': price_peak,
        'families': '|'.join(events['family'].unique())
    })
    
    # Vérification cas 11.09
    if date_str == '2025-09-11':
        print(f"🔍 VALIDATION CAS 11.09.2025 :")
        print(f"   Impact mesuré : {impact_pips:.1f} pips")
        print(f"   Attendu S103  : 56.8 pips")
        if abs(impact_pips - 56.8) < 2:
            print(f"   ✅ VALIDÉ !")
        else:
            print(f"   ❌ ÉCART : {abs(impact_pips - 56.8):.1f} pips")
        print()
    
    print(f"✅ {len(results):2d}/{len(df_dates)} | {date_str} | {len(events):2d} events | {impact_pips:5.1f} pips {direction}")

conn.close()

print("="*80)
print(f"✅ {len(results)} dates extraites (clusters ≥8 events)")
print()

# Sauvegarder
df_results = pd.DataFrame(results)
output_file = Path(__file__).parent / "dataset_44_dates_METHOD_SESSION92_5.csv"
df_results.to_csv(output_file, index=False)

print(f"📁 {output_file.name}")
print()

# Stats
print("📊 STATISTIQUES :")
print(f"   Impact moyen   : {df_results['impact_real_pips'].mean():.1f} pips")
print(f"   Impact médian  : {df_results['impact_real_pips'].median():.1f} pips")
print(f"   Impact min     : {df_results['impact_real_pips'].min():.1f} pips")
print(f"   Impact max     : {df_results['impact_real_pips'].max():.1f} pips")
print(f"   Events moyen   : {df_results['num_events'].mean():.1f}")
print(f"   Score moyen    : {df_results['max_score'].mean():.1f}")
print()

print("✅ ÉTAPE 2.2 TERMINÉE (MÉTHODE SESSION 92.5)")
