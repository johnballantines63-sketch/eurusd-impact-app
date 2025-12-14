#!/usr/bin/env python3
"""
SESSION 26 - ÉTAPE 2 CORRIGÉE : event_impacts_v2 avec conversion timezone
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 80)
print("SESSION 26 - ÉTAPE 2 CORRIGÉE : event_impacts_v2")
print("=" * 80)

# Connexion
db_path = Path("fx_impact_app/data/warehouse.duckdb")
con = duckdb.connect(str(db_path))

# 1. Supprimer et recréer table
print("\n📋 ÉTAPE 1 : Recréation table event_impacts_v2...")

con.execute("DROP TABLE IF EXISTS event_impacts_v2")

create_table_query = """
CREATE TABLE event_impacts_v2 (
    ts_utc TIMESTAMP WITH TIME ZONE,
    event_key VARCHAR,
    event_title VARCHAR,
    country VARCHAR,
    actual DOUBLE,
    forecast DOUBLE,
    previous DOUBLE,
    surprise_pct DOUBLE,
    importance INTEGER,
    phase1_pips DOUBLE,
    ttr_minutes INTEGER,
    direction VARCHAR,
    start_price DOUBLE,
    ttr_price DOUBLE,
    source VARCHAR,
    created_at TIMESTAMP
)
"""

con.execute(create_table_query)
print("✅ Table créée")

# 2. Extraire événements
print("\n📊 ÉTAPE 2 : Extraction événements...")

query_events = """
SELECT 
    ts_utc,
    event_key,
    event_title,
    country,
    actual,
    forecast,
    previous,
    importance_n as importance
FROM events
WHERE actual IS NOT NULL
  AND ts_utc >= '2022-10-01'
  AND ts_utc < '2025-11-01'
  AND (forecast IS NOT NULL OR previous IS NOT NULL)
ORDER BY ts_utc
"""

events_df = con.execute(query_events).df()
print(f"✅ {len(events_df):,} événements extraits")

# 3. Calculer surprise
print("\n🔢 ÉTAPE 3 : Calcul surprise...")

def calculate_surprise(row):
    actual = row['actual']
    forecast = row['forecast']
    previous = row['previous']
    
    if pd.notna(forecast) and forecast != 0:
        return abs((actual - forecast) / forecast) * 100
    elif pd.notna(previous) and previous != 0:
        return abs((actual - previous) / previous) * 100
    else:
        return None

events_df['surprise_pct'] = events_df.apply(calculate_surprise, axis=1)
events_high_surprise = events_df[events_df['surprise_pct'] > 30].copy()
print(f"✅ {len(events_high_surprise):,} événements avec surprise > 30%")

# 4. Calculer Phase 1 - AVEC CORRECTION TIMEZONE
print("\n⚙️  ÉTAPE 4 : Calcul Phase 1 (CORRECTION TIMEZONE)...")
print("   CRITIQUE : Conversion explicite des timestamps en UTC")

results = []
errors = 0
processed = 0

for idx, event in events_high_surprise.iterrows():
    processed += 1
    
    if processed % 500 == 0:
        print(f"   Traité : {processed:,} / {len(events_high_surprise):,} ({processed/len(events_high_surprise)*100:.1f}%)")
    
    event_time = event['ts_utc']
    
    # CORRECTION CRITIQUE : Convertir en UTC pur
    if isinstance(event_time, str):
        event_time = pd.to_datetime(event_time, utc=True)
    elif hasattr(event_time, 'tz_convert'):
        event_time = event_time.tz_convert('UTC')
    
    # Enlever timezone pour requête DuckDB
    event_time_str = event_time.strftime('%Y-%m-%d %H:%M:%S')
    
    end_time = event_time + timedelta(minutes=15)
    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Requête prices SANS timezone dans le WHERE
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{event_time_str}'::timestamp
      AND datetime <= '{end_time_str}'::timestamp
    ORDER BY datetime
    """
    
    try:
        prices_df = con.execute(query_prices).df()
        
        if len(prices_df) == 0:
            errors += 1
            continue
        
        # Prix départ
        start_price = prices_df.iloc[0]['open']
        
        # Trouver pic
        max_high = prices_df['high'].max()
        min_low = prices_df['low'].min()
        
        # Phase 1
        phase1_up = (max_high - start_price) * 10000
        phase1_down = (start_price - min_low) * 10000
        
        if phase1_up > phase1_down:
            phase1_pips = phase1_up
            direction = 'UP'
            ttr_price = max_high
            ttr_idx = prices_df['high'].idxmax()
        else:
            phase1_pips = phase1_down
            direction = 'DOWN'
            ttr_price = min_low
            ttr_idx = prices_df['low'].idxmin()
        
        ttr_minutes = ttr_idx
        
        results.append({
            'ts_utc': event['ts_utc'],
            'event_key': event['event_key'],
            'event_title': event['event_title'],
            'country': event['country'],
            'actual': event['actual'],
            'forecast': event['forecast'],
            'previous': event['previous'],
            'surprise_pct': event['surprise_pct'],
            'importance': event['importance'],
            'phase1_pips': phase1_pips,
            'ttr_minutes': ttr_minutes,
            'direction': direction,
            'start_price': start_price,
            'ttr_price': ttr_price,
            'source': 'dukascopy_session26_v2',
            'created_at': datetime.now()
        })
        
    except Exception as e:
        errors += 1
        if errors < 5:
            print(f"   ⚠️  Erreur {event_time_str} : {e}")
        continue

print(f"\n✅ Calcul terminé")
print(f"   Succès : {len(results):,}")
print(f"   Erreurs : {errors:,}")

# 5. Insertion
print("\n💾 ÉTAPE 5 : Insertion...")

if len(results) > 0:
    results_df = pd.DataFrame(results)
    con.register('results_temp', results_df)
    con.execute("INSERT INTO event_impacts_v2 SELECT * FROM results_temp")
    con.unregister('results_temp')
    print(f"✅ {len(results_df):,} événements insérés")

# 6. VALIDATION 11 SEPTEMBRE
print("\n" + "=" * 80)
print("VALIDATION 11 SEPTEMBRE 2025")
print("=" * 80)

# Convertir 14:30 Berne en UTC pour la recherche
validation_query = """
SELECT 
    ts_utc,
    event_title,
    surprise_pct,
    phase1_pips,
    ttr_minutes,
    start_price,
    ttr_price
FROM event_impacts_v2
WHERE ts_utc::DATE = '2025-09-11'
  AND (
    EXTRACT(HOUR FROM ts_utc) = 12 OR
    EXTRACT(HOUR FROM ts_utc) = 14
  )
  AND EXTRACT(MINUTE FROM ts_utc) = 30
ORDER BY phase1_pips DESC
"""

sept11 = con.execute(validation_query).df()

if len(sept11) > 0:
    print(f"\n✅ {len(sept11)} événements trouvés\n")
    
    for idx, row in sept11.iterrows():
        title = row['event_title'] if row['event_title'] else 'N/A'
        print(f"  📰 {title}")
        print(f"  🎯 Phase 1 : {row['phase1_pips']:.2f} pips")
        print(f"  💰 Prix : {row['start_price']:.5f} → {row['ttr_price']:.5f}")
        
        expected = 37.4
        error = abs(row['phase1_pips'] - expected)
        error_pct = (error / expected) * 100
        
        print(f"  ✅ Validation : {error:.2f} pips ({error_pct:.1f}%)")
        
        if error <= 5:
            print(f"  Statut : ✅ EXCELLENT\n")
        elif error <= 10:
            print(f"  Statut : ⚠️  ACCEPTABLE\n")
        else:
            print(f"  Statut : ❌ PROBLÈME\n")
else:
    print("\n❌ Aucun événement trouvé")

# 7. Stats
print("=" * 80)
print("STATISTIQUES")
print("=" * 80)

stats = con.execute("""
SELECT 
    COUNT(*) as total,
    AVG(phase1_pips) as avg,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY phase1_pips) as median
FROM event_impacts_v2
""").df()

print(f"\nPhase 1 : Moyenne {stats['avg'].iloc[0]:.2f} pips, Médiane {stats['median'].iloc[0]:.2f} pips")

con.close()

print("\n✅ TERMINÉ")
print("=" * 80)
