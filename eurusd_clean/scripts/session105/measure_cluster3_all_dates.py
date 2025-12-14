#!/usr/bin/env python3
"""
SESSION 105 - MESURE CLUSTER #3 (6 DATES CPI)
==============================================
Mesure impact réel pour les 6 dates du Cluster #3
Méthode Session 92.5 validée

Cluster #3 : CPI mensuel (11 événements)
Dates : 2025-09-11, 2025-08-12, 2025-07-15, 2025-06-11, 2025-05-13, 2025-04-10
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
from datetime import datetime
import pytz
import json

print("="*80)
print("SESSION 105 - MESURE CLUSTER #3 (6 DATES CPI)")
print("="*80)
print()

# Configuration
CLUSTER_3_DATES = [
    "2025-09-11",  # Référence (validé 56.8 pips)
    "2025-08-12",
    "2025-07-15",
    "2025-06-11",
    "2025-05-13",
    "2025-04-10"
]

# CPI US publié à 14:30 Bern = 12:30:00+02:00 dans DB
EVENT_TIME_DB = "12:30:00"
WINDOW_MINUTES = 120

print(f"📊 Cluster #3 : CPI mensuel US")
print(f"   Nombre dates : {len(CLUSTER_3_DATES)}")
print(f"   Événement : 14:30 Bern → {EVENT_TIME_DB}+02:00 dans DB")
print()

# Config DB
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

print(f"🗄️  DB : {db_path}")
print()

# Mesurer chaque date
results = []
bern_tz = pytz.timezone('Europe/Zurich')

for idx, date_str in enumerate(CLUSTER_3_DATES, 1):
    print(f"📅 [{idx}/6] Mesure {date_str}...")
    print("-"*80)
    
    # Query prix
    query_prices = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{date_str} {EVENT_TIME_DB}+02:00'::TIMESTAMP - INTERVAL '1 minute'
      AND datetime < '{date_str} {EVENT_TIME_DB}+02:00'::TIMESTAMP + INTERVAL '{WINDOW_MINUTES} minutes'
    ORDER BY datetime
    """
    
    with duckdb.connect(str(db_path), read_only=True) as conn:
        prices_df = conn.execute(query_prices).fetchdf()
    
    if len(prices_df) == 0:
        print(f"   ❌ Pas de prix disponibles pour {date_str}")
        print()
        continue
    
    print(f"   ✅ {len(prices_df)} points chargés")
    
    # Conversion timezone
    event_dt = bern_tz.localize(
        datetime.strptime(f"{date_str} {EVENT_TIME_DB}", "%Y-%m-%d %H:%M:%S")
    )
    
    # Prix départ = candle -1 min
    prices_before = prices_df[prices_df['datetime'] < event_dt]
    if len(prices_before) == 0:
        price_start = prices_df.iloc[0]['close']
        time_start = prices_df.iloc[0]['datetime']
    else:
        price_start_candle = prices_before.iloc[-1]
        price_start = price_start_candle['close']
        time_start = price_start_candle['datetime']
    
    # Chercher pic APRÈS événement
    prices_after = prices_df[prices_df['datetime'] >= event_dt]
    
    if len(prices_after) == 0:
        print(f"   ❌ Pas de prix après événement")
        print()
        continue
    
    price_max = prices_after['close'].max()
    price_min = prices_after['close'].min()
    idx_max = prices_after['close'].idxmax()
    idx_min = prices_after['close'].idxmin()
    
    # Direction
    move_up = abs(price_max - price_start)
    move_down = abs(price_start - price_min)
    
    if move_up > move_down:
        direction = "UP"
        price_peak = price_max
        time_peak = prices_after.loc[idx_max, 'datetime']
        impact = (price_peak - price_start) * 10000
    else:
        direction = "DOWN"
        price_peak = price_min
        time_peak = prices_after.loc[idx_min, 'datetime']
        impact = (price_start - price_peak) * 10000
    
    duration = (time_peak - event_dt).total_seconds() / 60
    
    # Affichage
    print(f"   Prix départ : {price_start:.5f} (candle {time_start.strftime('%H:%M')})")
    print(f"   Prix pic    : {price_peak:.5f} à {time_peak.strftime('%H:%M')}")
    print(f"   Direction   : {direction}")
    print(f"   Durée       : {duration:.1f} min")
    print(f"   Impact      : {impact:.1f} pips")
    
    # Sauvegarder
    results.append({
        'date': date_str,
        'event_time_bern': '14:30:00',
        'event_time_db': EVENT_TIME_DB,
        'price_start': float(price_start),
        'price_peak': float(price_peak),
        'direction': direction,
        'impact_pips': float(impact),
        'duration_min': float(duration),
        'num_candles': len(prices_df)
    })
    
    print()

# Résultats
print("="*80)
print("RÉSULTATS CLUSTER #3")
print("="*80)
print()

df_results = pd.DataFrame(results)

print("📊 Impacts mesurés :")
print("-"*80)
for _, row in df_results.iterrows():
    ref = " (référence)" if row['date'] == "2025-09-11" else ""
    print(f"   {row['date']} : {row['impact_pips']:6.1f} pips {row['direction']:4s}{ref}")

print()
print(f"   Moyenne : {df_results['impact_pips'].mean():.1f} pips")
print(f"   Médiane : {df_results['impact_pips'].median():.1f} pips")
print(f"   Min     : {df_results['impact_pips'].min():.1f} pips")
print(f"   Max     : {df_results['impact_pips'].max():.1f} pips")
print(f"   Écart-type : {df_results['impact_pips'].std():.1f} pips")
print()

# Validation référence
ref_row = df_results[df_results['date'] == "2025-09-11"]
if len(ref_row) > 0:
    ref_impact = ref_row.iloc[0]['impact_pips']
    if abs(ref_impact - 56.8) < 2:
        print("✅ Date référence 11.09 validée : {:.1f} pips ≈ 56.8 pips ✅".format(ref_impact))
    else:
        print(f"⚠️ Date référence 11.09 : {ref_impact:.1f} pips (attendu 56.8)")
    print()

# Sauvegarder CSV
output_dir = Path(__file__).parent
output_csv = output_dir / "cluster3_impacts_measured.csv"
df_results.to_csv(output_csv, index=False)

print(f"💾 Résultats CSV : {output_csv.name}")

# Sauvegarder JSON détaillé
output_json = output_dir / "cluster3_impacts_measured.json"
with open(output_json, 'w') as f:
    json.dump({
        'cluster': 'Cluster #3 - CPI mensuel',
        'num_dates': len(results),
        'method': 'session_92.5_validated',
        'event_time_bern': '14:30:00',
        'event_time_db': EVENT_TIME_DB,
        'measurements': results,
        'statistics': {
            'mean': float(df_results['impact_pips'].mean()),
            'median': float(df_results['impact_pips'].median()),
            'std': float(df_results['impact_pips'].std()),
            'min': float(df_results['impact_pips'].min()),
            'max': float(df_results['impact_pips'].max())
        }
    }, f, indent=2)

print(f"💾 Résultats JSON : {output_json.name}")
print()
print("="*80)
print("✅ MESURE CLUSTER #3 TERMINÉE")
print("="*80)
