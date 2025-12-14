#!/usr/bin/env python3
"""
Investigation CRITIQUE - Pourquoi prix incorrect pour 11 septembre
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*70)
print("INVESTIGATION PRIX 11 SEPTEMBRE")
print("="*70)

# 1. Récupérer timestamp exact de l'événement
print("\n1. TIMESTAMP ÉVÉNEMENT")
print("-"*70)

event = con.execute("""
    SELECT ts_utc, event_key, country
    FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
    AND country = 'US'
    AND event_key = 'inflation rate_mom'
""").fetchone()

print(f"Timestamp DB : {event[0]}")
print(f"Type : {type(event[0])}")

# 2. Convertir en UTC pur
event_ts = pd.to_datetime(event[0], utc=True)
print(f"\nConverti UTC : {event_ts}")
print(f"Heure UTC : {event_ts.hour}:{event_ts.minute}")

# 3. Chercher prix à cette heure EXACTE
print("\n2. PRIX À L'HEURE EXACTE")
print("-"*70)

# Essai 1 : Avec timezone
query1 = f"""
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime = '{event[0]}'
LIMIT 5
"""
result1 = con.execute(query1).df()
print(f"\nRequête avec timezone '{event[0]}' :")
print(f"Résultats : {len(result1)}")
if len(result1) > 0:
    print(result1[['datetime', 'open']])

# Essai 2 : Sans timezone (UTC pur)
utc_str = event_ts.strftime('%Y-%m-%d %H:%M:%S')
query2 = f"""
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime >= '{utc_str}'::timestamp
AND datetime < ('{utc_str}'::timestamp + INTERVAL '1 minute')
LIMIT 5
"""
result2 = con.execute(query2).df()
print(f"\nRequête UTC pur '{utc_str}' :")
print(f"Résultats : {len(result2)}")
if len(result2) > 0:
    print(result2[['datetime', 'open']])

# 3. Chercher tous les prix autour de 12:30 UTC
print("\n3. TOUS LES PRIX 12:25-12:35 UTC")
print("-"*70)

query3 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime::DATE = '2025-09-11'
AND EXTRACT(HOUR FROM datetime) = 12
AND EXTRACT(MINUTE FROM datetime) BETWEEN 25 AND 35
ORDER BY datetime
"""
result3 = con.execute(query3).df()
print(f"\nRésultats : {len(result3)}")
print(result3[['datetime', 'open', 'close']])

# 4. Chercher le prix 1.16874 (référence)
print("\n4. RECHERCHE PRIX RÉFÉRENCE ~1.16874")
print("-"*70)

query4 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime::DATE = '2025-09-11'
AND (
    ABS(open - 1.16874) < 0.0001
    OR ABS(high - 1.16874) < 0.0001
    OR ABS(low - 1.16874) < 0.0001
    OR ABS(close - 1.16874) < 0.0001
)
ORDER BY datetime
"""
result4 = con.execute(query4).df()
print(f"\nRésultats : {len(result4)}")
if len(result4) > 0:
    print(result4[['datetime', 'open', 'high', 'low', 'close']])

# 5. Chercher le prix 1.17321 (ce qu'on a trouvé)
print("\n5. D'OÙ VIENT LE PRIX 1.17321 ?")
print("-"*70)

query5 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime::DATE = '2025-09-11'
AND (
    ABS(open - 1.17321) < 0.00001
    OR ABS(close - 1.17321) < 0.00001
)
ORDER BY datetime
"""
result5 = con.execute(query5).df()
print(f"\nRésultats : {len(result5)}")
if len(result5) > 0:
    print(result5[['datetime', 'open', 'high', 'low', 'close']])

con.close()

print("\n" + "="*70)
print("ANALYSE")
print("="*70)
print("\nPrix attendu : 1.16874 (cas référence)")
print("Prix trouvé : 1.17321")
print("Différence : 447 pips")
print("\nLe script lit probablement les prix au mauvais moment.")
