#!/usr/bin/env python3
"""
Régénération correcte du CSV depuis DuckDB
Session 26 - Calcul correct de Phase 1 pour tous les événements
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

print("=" * 80)
print("RÉGÉNÉRATION CSV DEPUIS DUCKDB")
print("=" * 80)

# Connexion DB
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# 1. Récupérer tous les événements avec surprise > 30%
print("\n📊 Extraction événements avec surprise > 30%...")

query_events = """
SELECT 
    e.id,
    e.ts_utc,
    e.event_key,
    e.event_title,
    e.country,
    e.actual,
    e.forecast,
    e.previous,
    e.surprise_index_corrected as surprise_pct,
    e.importance
FROM events e
WHERE e.surprise_index_corrected > 30
  AND e.ts_utc >= '2022-10-01'
  AND e.ts_utc < '2025-11-01'
ORDER BY e.ts_utc
"""

events_df = con.execute(query_events).df()
print(f"✅ {len(events_df):,} événements trouvés")

# 2. Pour chaque événement, calculer Phase 1 depuis prices_1m
print("\n🔄 Calcul Phase 1 pour chaque événement...")

results = []
errors = 0

for idx, event in events_df.iterrows():
    if idx % 1000 == 0:
        print(f"   Traité: {idx:,} / {len(events_df):,}")
    
    event_time = event['ts_utc']
    
    # Convertir en datetime si nécessaire
    if isinstance(event_time, str):
        event_time = pd.to_datetime(event_time)
    
    # Calculer la fenêtre : event_time → event_time + 15 min
    end_time = event_time + timedelta(minutes=15)
    
    # Requête pour récupérer les prix
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
        
        # Prix de départ = OPEN de la première minute
        start_price = prices_df.iloc[0]['open']
        
        # Trouver le pic (TTR)
        max_high = prices_df['high'].max()
        min_low = prices_df['low'].min()
        
        # Phase 1 = mouvement maximum
        phase1_up = (max_high - start_price) * 10000
        phase1_down = (start_price - min_low) * 10000
        
        if phase1_up > phase1_down:
            phase1_pips = phase1_up
            direction = 'UP'
            ttr_price = max_high
            # Trouver l'index du TTR
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
            'ttr_price': ttr_price
        })
        
    except Exception as e:
        errors += 1
        continue

print(f"\n✅ Calcul terminé")
print(f"   Succès: {len(results):,}")
print(f"   Erreurs: {errors:,}")

# 3. Créer le DataFrame final
result_df = pd.DataFrame(results)

# 4. Sauvegarder
output_file = 'events_extreme_surprise_dukascopy_CORRECTED_session26.csv'
result_df.to_csv(output_file, index=False)

print(f"\n💾 Fichier sauvegardé: {output_file}")

# 5. Vérifier le cas référence
print("\n" + "=" * 80)
print("VÉRIFICATION CAS RÉFÉRENCE 11 SEPTEMBRE")
print("=" * 80)

sept11 = result_df[result_df['ts_utc'].astype(str).str.contains('2025-09-11')]
sept11_1230 = sept11[sept11['ts_utc'].astype(str).str.contains('12:30')]

if len(sept11_1230) > 0:
    print(f"\n✅ {len(sept11_1230)} événements trouvés à 12:30 UTC")
    
    for idx, row in sept11_1230.iterrows():
        print(f"\n  📰 {row['event_title']}")
        print(f"  🎯 Phase 1: {row['phase1_pips']:.2f} pips")
        print(f"  💰 Prix: {row['start_price']:.5f} → {row['ttr_price']:.5f}")
        
        expected = 37.4
        error = abs(row['phase1_pips'] - expected)
        print(f"  ✅ Écart vs MT5: {error:.2f} pips ({error/expected*100:.1f}%)")
else:
    print("\n❌ Aucun événement à 12:30 UTC le 11 septembre")

# 6. Statistiques globales
print("\n" + "=" * 80)
print("STATISTIQUES GLOBALES")
print("=" * 80)

print(f"\nPhase 1 (pips):")
print(f"  Moyenne:  {result_df['phase1_pips'].mean():.2f}")
print(f"  Médiane:  {result_df['phase1_pips'].median():.2f}")
print(f"  Q25:      {result_df['phase1_pips'].quantile(0.25):.2f}")
print(f"  Q75:      {result_df['phase1_pips'].quantile(0.75):.2f}")
print(f"  Max:      {result_df['phase1_pips'].max():.2f}")

print(f"\nTTR (minutes):")
print(f"  Moyen:    {result_df['ttr_minutes'].mean():.1f}")
print(f"  Médian:   {result_df['ttr_minutes'].median():.1f}")

print(f"\nDirection:")
print(f"  UP:   {(result_df['direction'] == 'UP').sum():,} ({(result_df['direction'] == 'UP').sum() / len(result_df) * 100:.1f}%)")
print(f"  DOWN: {(result_df['direction'] == 'DOWN').sum():,} ({(result_df['direction'] == 'DOWN').sum() / len(result_df) * 100:.1f}%)")

print("\n" + "=" * 80)
print("✅ RÉGÉNÉRATION TERMINÉE")
print("=" * 80)

con.close()
