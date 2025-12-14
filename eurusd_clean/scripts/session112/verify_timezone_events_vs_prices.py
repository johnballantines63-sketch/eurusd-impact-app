#!/usr/bin/env python3
"""
VÉRIFICATION TIMEZONE - Events vs Prices
"""
import duckdb
from pathlib import Path

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

con = duckdb.connect(str(db_path), read_only=True)

print("="*80)
print("🔍 VÉRIFICATION TIMEZONE - Events vs Prices")
print("="*80)

# ══════════════════════════════════════════════════════════════════════
# 1. EVENTS - 11 septembre
# ══════════════════════════════════════════════════════════════════════

print("\n📅 TABLE EVENTS - 11 septembre 2025:")
print("-"*80)

events = con.execute("""
SELECT ts_utc, event_title
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
    AND event_title LIKE '%CPI%'
ORDER BY ts_utc
LIMIT 3
""").df()

print("\nPremiers événements CPI :")
for _, row in events.iterrows():
    print(f"  {row['ts_utc']} - {row['event_title']}")

# ══════════════════════════════════════════════════════════════════════
# 2. PRICES - Autour de ces heures
# ══════════════════════════════════════════════════════════════════════

print("\n💹 TABLE PRICES_1M - Vérification:")
print("-"*80)

# Tester plusieurs heures possibles
test_times = [
    '2025-09-11 12:30:00',  # Si events en UTC
    '2025-09-11 14:30:00',  # Si events en Bern
    '2025-09-11 16:30:00',  # Au cas où
]

for time_str in test_times:
    prices = con.execute(f"""
    SELECT datetime, open, close
    FROM prices_1m
    WHERE datetime >= '{time_str}'
        AND datetime < '{time_str}'::TIMESTAMP + INTERVAL '1 minute'
    """).df()
    
    if len(prices) > 0:
        print(f"\n✅ {time_str} trouvé :")
        print(f"   Open: {prices['open'].iloc[0]:.5f}")
        print(f"   Close: {prices['close'].iloc[0]:.5f}")
    else:
        print(f"\n❌ {time_str} - aucun prix")

# ══════════════════════════════════════════════════════════════════════
# 3. PRIX À 14:30 (ce qu'André dit être le bon moment)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🎯 SELON ANDRÉ : Événement réel 14:30 Bern")
print("="*80)

# Prix à 14:30
prices_1430 = con.execute("""
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime >= '2025-09-11 14:30:00'
    AND datetime < '2025-09-11 14:31:00'
""").df()

if len(prices_1430) > 0:
    print(f"\n💹 Prix à 14:30 dans DB :")
    print(f"   Timestamp: {prices_1430['datetime'].iloc[0]}")
    print(f"   Open: {prices_1430['open'].iloc[0]:.5f}")
    print(f"   (André dit que ça devrait être ~1.16816)")

# Prix à 14:29 pour comparaison
prices_1429 = con.execute("""
SELECT datetime, open, close
FROM prices_1m
WHERE datetime >= '2025-09-11 14:29:00'
    AND datetime < '2025-09-11 14:30:00'
""").df()

if len(prices_1429) > 0:
    print(f"\n💹 Prix à 14:29 (avant événement) :")
    print(f"   Close: {prices_1429['close'].iloc[0]:.5f}")
    print(f"   (Devrait être ~1.16816)")

# ══════════════════════════════════════════════════════════════════════
# 4. ÉVÉNEMENTS - quelle heure dans la table ?
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 ÉVÉNEMENTS CPI - À quelle heure sont-ils stockés ?")
print("="*80)

# Chercher événements entre 12:00 et 15:00
events_range = con.execute("""
SELECT 
    ts_utc,
    event_title,
    actual,
    estimate
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
    AND ts_utc >= '2025-09-11 12:00:00'
    AND ts_utc < '2025-09-11 15:00:00'
ORDER BY ts_utc
""").df()

print(f"\nÉvénements trouvés entre 12:00 et 15:00 :")
for _, row in events_range.iterrows():
    print(f"  {row['ts_utc']} - {row['event_title']}")

print("\n" + "="*80)
print("💡 CONCLUSION")
print("="*80)

print("\nSi l'événement réel est à 14:30 Bern :")
print("  - Dans events table : stocké à quelle heure ?")
print("  - Dans prices table : chercher à 14:30")
print("\nAnalisez les timestamps ci-dessus pour déterminer le décalage !")

con.close()
