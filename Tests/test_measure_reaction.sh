#!/bin/bash

# Test de la fonction measure_actual_market_reaction

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

echo "🔬 Test de mesure de réaction marché..."
echo ""

python3 << 'PYEOF'
import duckdb
import pandas as pd
from datetime import datetime, timedelta

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# Prendre un événement récent
event = conn.execute("""
SELECT e.ts_utc, e.event_key, e.country, e.actual, e.previous
FROM events e
JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE ef.empirical_score >= 60
    AND e.actual IS NOT NULL
    AND e.previous IS NOT NULL
    AND e.country = 'US'
ORDER BY e.ts_utc DESC
LIMIT 1
""").fetchone()

print(f"Événement test: {event[1]}")
print(f"Date: {event[0]}")
print(f"Actual: {event[3]}, Previous: {event[4]}")

# Simuler measure_actual_market_reaction
event_ts = pd.to_datetime(event[0])
end_time = event_ts + timedelta(minutes=60)

print(f"\nEvent timestamp: {event_ts}")
print(f"End timestamp: {end_time}")

# Convertir en epoch
event_epoch = int(event_ts.timestamp())
end_epoch = int(end_time.timestamp())

print(f"Event epoch: {event_epoch}")
print(f"End epoch: {end_epoch}")

# Query prices
query = f"""
SELECT timestamp, close
FROM prices_1m
WHERE timestamp >= {event_epoch}
    AND timestamp <= {end_epoch}
ORDER BY timestamp ASC
"""

print(f"\nQuery SQL:\n{query}")

try:
    prices = conn.execute(query).fetchall()
    print(f"\n✅ Prix trouvés: {len(prices)} bars")
    
    if len(prices) >= 2:
        ref_price = prices[0][1]
        print(f"Prix référence: {ref_price:.5f}")
        
        # Calculer mouvement
        max_movement = 0
        latency = None
        
        for i, (ts, price) in enumerate(prices):
            movement_pips = abs(price - ref_price) * 10000
            if movement_pips > max_movement:
                max_movement = movement_pips
            
            # Détecter première réaction > 5 pips
            if latency is None and movement_pips >= 5.0:
                latency = i
        
        print(f"Mouvement max: {max_movement:.2f} pips")
        print(f"Latence: {latency} minutes" if latency else "Latence: Aucune réaction > 5 pips")
        
        # Calculer surprise
        if event[4] is not None and event[4] != 0:
            surprise = abs((event[3] - event[4]) / event[4]) * 100
            print(f"Surprise: {surprise:.2f}%")
        
        print("\n✅ La fonction devrait fonctionner !")
    else:
        print("❌ Pas assez de prix")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

conn.close()
PYEOF

echo ""
echo "Si ce test fonctionne mais pas le backtesting,"
echo "le problème est ailleurs dans le script."
