#!/usr/bin/env python3
"""
SESSION 26 - ÉTAPE 2 : Reconstruction event_impacts_v2 (CORRIGÉ)
Calcul propre Phase 1 depuis prices_1m Dukascopy
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 80)
print("SESSION 26 - ÉTAPE 2 : RECONSTRUCTION event_impacts_v2")
print("=" * 80)

# Connexion
db_path = Path("fx_impact_app/data/warehouse.duckdb")
con = duckdb.connect(str(db_path))

# 1. CRÉER TABLE event_impacts_v2
print("\n📋 ÉTAPE 1 : Création table event_impacts_v2...")

# Supprimer si existe
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
print("✅ Table event_impacts_v2 créée")

# 2. EXTRAIRE ÉVÉNEMENTS
print("\n📊 ÉTAPE 2 : Extraction événements depuis 'events'...")

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

# 3. CALCULER SURPRISE
print("\n🔢 ÉTAPE 3 : Calcul surprise...")

def calculate_surprise(row):
    """Calcule surprise en %"""
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

# Filtrer surprise > 30%
events_high_surprise = events_df[events_df['surprise_pct'] > 30].copy()
print(f"✅ {len(events_high_surprise):,} événements avec surprise > 30%")

# 4. CALCULER PHASE 1 POUR CHAQUE ÉVÉNEMENT
print("\n⚙️  ÉTAPE 4 : Calcul Phase 1 depuis prices_1m...")
print("   (Cela peut prendre quelques minutes...)")

results = []
errors = 0
processed = 0

for idx, event in events_high_surprise.iterrows():
    processed += 1
    
    if processed % 500 == 0:
        print(f"   Traité : {processed:,} / {len(events_high_surprise):,} ({processed/len(events_high_surprise)*100:.1f}%)")
    
    event_time = event['ts_utc']
    
    # Convertir en datetime si string
    if isinstance(event_time, str):
        event_time = pd.to_datetime(event_time)
    
    # Fenêtre 15 minutes
    end_time = event_time + timedelta(minutes=15)
    
    # Requête prices
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{event_time}'
      AND datetime <= '{end_time}'
    ORDER BY datetime
    """
    
    try:
        prices_df = con.execute(query_prices).df()
        
        if len(prices_df) == 0:
            errors += 1
            continue
        
        # Prix départ = OPEN première minute
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
        
        # TTR en minutes
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
            'source': 'dukascopy_session26',
            'created_at': datetime.now()
        })
        
    except Exception as e:
        errors += 1
        if errors < 5:
            print(f"   ⚠️  Erreur événement {event_time} : {e}")
        continue

print(f"\n✅ Calcul terminé")
print(f"   Succès : {len(results):,}")
print(f"   Erreurs : {errors:,}")
print(f"   Taux succès : {len(results)/(len(results)+errors)*100:.1f}%")

# 5. INSÉRER DANS TABLE
print("\n💾 ÉTAPE 5 : Insertion dans event_impacts_v2...")

if len(results) > 0:
    results_df = pd.DataFrame(results)
    
    # Insertion directe avec register
    con.register('results_temp', results_df)
    
    insert_query = """
    INSERT INTO event_impacts_v2 
    SELECT * FROM results_temp
    """
    
    con.execute(insert_query)
    con.unregister('results_temp')
    
    print(f"✅ {len(results_df):,} événements insérés")
else:
    print("❌ Aucun résultat à insérer")

# 6. VALIDATION CAS RÉFÉRENCE
print("\n" + "=" * 80)
print("VALIDATION CAS RÉFÉRENCE - 11 SEPTEMBRE 2025")
print("=" * 80)

validation_query = """
SELECT 
    ts_utc,
    event_title,
    surprise_pct,
    phase1_pips,
    ttr_minutes,
    direction,
    start_price,
    ttr_price
FROM event_impacts_v2
WHERE DATE(ts_utc) = '2025-09-11'
  AND EXTRACT(HOUR FROM ts_utc) = 12
  AND EXTRACT(MINUTE FROM ts_utc) = 30
ORDER BY phase1_pips DESC
"""

sept11 = con.execute(validation_query).df()

if len(sept11) > 0:
    print(f"\n✅ {len(sept11)} événements trouvés à 12:30 UTC")
    
    for idx, row in sept11.iterrows():
        print(f"\n  📰 {row['event_title']}")
        print(f"  🎯 Phase 1 : {row['phase1_pips']:.2f} pips")
        print(f"  💰 Prix : {row['start_price']:.5f} → {row['ttr_price']:.5f}")
        
        expected = 37.4
        actual = row['phase1_pips']
        error = abs(actual - expected)
        error_pct = (error / expected) * 100
        
        print(f"\n  ✅ VALIDATION:")
        print(f"     MT5 André : 37.4 pips")
        print(f"     Calculé : {actual:.2f} pips")
        print(f"     Écart : {error:.2f} pips ({error_pct:.1f}%)")
        
        if error <= 5:
            print(f"     Statut : ✅ EXCELLENT")
        elif error <= 10:
            print(f"     Statut : ⚠️  ACCEPTABLE")
        else:
            print(f"     Statut : ❌ PROBLÈME")
else:
    print("\n❌ AUCUN ÉVÉNEMENT TROUVÉ pour le 11 septembre à 12:30 UTC")

# 7. STATISTIQUES GLOBALES
print("\n" + "=" * 80)
print("STATISTIQUES GLOBALES")
print("=" * 80)

stats_query = """
SELECT 
    COUNT(*) as total,
    AVG(phase1_pips) as avg_phase1,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY phase1_pips) as median_phase1,
    MIN(phase1_pips) as min_phase1,
    MAX(phase1_pips) as max_phase1,
    AVG(ttr_minutes) as avg_ttr,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ttr_minutes) as median_ttr
FROM event_impacts_v2
"""

stats = con.execute(stats_query).df()

print(f"\nPhase 1 (pips) :")
print(f"  Total événements : {stats['total'].iloc[0]:,}")
print(f"  Moyenne : {stats['avg_phase1'].iloc[0]:.2f}")
print(f"  Médiane : {stats['median_phase1'].iloc[0]:.2f}")
print(f"  Min : {stats['min_phase1'].iloc[0]:.2f}")
print(f"  Max : {stats['max_phase1'].iloc[0]:.2f}")

print(f"\nTTR (minutes) :")
print(f"  Moyen : {stats['avg_ttr'].iloc[0]:.1f}")
print(f"  Médian : {stats['median_ttr'].iloc[0]:.1f}")

# Direction
dir_query = """
SELECT direction, COUNT(*) as count
FROM event_impacts_v2
GROUP BY direction
"""

directions = con.execute(dir_query).df()
print(f"\nDirection :")
for idx, row in directions.iterrows():
    pct = row['count'] / stats['total'].iloc[0] * 100
    print(f"  {row['direction']:<10} : {row['count']:>6,} ({pct:.1f}%)")

# Fermeture
con.close()

print("\n" + "=" * 80)
print("✅ ÉTAPE 2 TERMINÉE")
print("=" * 80)

print("\n🎯 RÉSUMÉ :")
print(f"   ✅ {len(results):,} événements calculés")
print(f"   ✅ Table event_impacts_v2 créée et peuplée")
print(f"   ✅ Source : Dukascopy Session 26")

print("\n" + "=" * 80)
