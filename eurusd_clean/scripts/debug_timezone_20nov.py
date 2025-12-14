"""
Debug : Vérifier le timezone des données de prix pour le 20.11.2025
==========================================================================
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔍 DEBUG : TIMEZONE DES DONNÉES DE PRIX - 20.11.2025")
print("=" * 80)
print()

# Date cible
target_date = datetime(2025, 11, 20)

# Charger les prix depuis prices_1m (source originale)
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("1️⃣ DONNÉES DANS PRICES_1M (SOURCE ORIGINALE)")
print("-" * 80)

query_prices_1m = """
SELECT 
    datetime as ts,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE DATE(datetime) = ?
  AND EXTRACT(HOUR FROM datetime) >= 12
  AND EXTRACT(HOUR FROM datetime) < 16
ORDER BY datetime
LIMIT 20
"""

df_prices_1m = conn.execute(query_prices_1m, [target_date.strftime('%Y-%m-%d')]).df()

if not df_prices_1m.empty:
    print(f"   ✅ {len(df_prices_1m)} bougies trouvées dans prices_1m (12h-16h)")
    print()
    print("   Premières bougies :")
    for idx, row in df_prices_1m.head(10).iterrows():
        print(f"      {row['ts']} | Open: {row['open']:.5f}, High: {row['high']:.5f}, Low: {row['low']:.5f}, Close: {row['close']:.5f}")
    
    # Chercher le mouvement explosif (>= 15 pips)
    print()
    print("   Mouvements explosifs (>= 15 pips) dans prices_1m :")
    explosive_found = False
    for idx, row in df_prices_1m.iterrows():
        candle_range = (row['high'] - row['low']) * 10000
        if candle_range >= 15.0:
            explosive_found = True
            print(f"      💥 {row['ts']} : {candle_range:.1f} pips")
            print(f"         Open: {row['open']:.5f}, High: {row['high']:.5f}, Low: {row['low']:.5f}, Close: {row['close']:.5f}")
    if not explosive_found:
        print("      ❌ Aucun mouvement explosif trouvé")
else:
    print("   ❌ Aucune donnée trouvée dans prices_1m")

print()

print("2️⃣ DONNÉES DANS PRICES_BERN (VUE +2H)")
print("-" * 80)

query_prices_bern = """
SELECT 
    datetime as ts,
    open,
    high,
    low,
    close
FROM prices_bern
WHERE DATE(datetime) = ?
  AND EXTRACT(HOUR FROM datetime) >= 14
  AND EXTRACT(HOUR FROM datetime) < 18
ORDER BY datetime
LIMIT 20
"""

df_prices_bern = conn.execute(query_prices_bern, [target_date.strftime('%Y-%m-%d')]).df()

if not df_prices_bern.empty:
    print(f"   ✅ {len(df_prices_bern)} bougies trouvées dans prices_bern (14h-18h)")
    print()
    print("   Premières bougies :")
    for idx, row in df_prices_bern.head(10).iterrows():
        print(f"      {row['ts']} | Open: {row['open']:.5f}, High: {row['high']:.5f}, Low: {row['low']:.5f}, Close: {row['close']:.5f}")
    
    # Chercher le mouvement explosif (>= 15 pips)
    print()
    print("   Mouvements explosifs (>= 15 pips) dans prices_bern :")
    explosive_found = False
    for idx, row in df_prices_bern.iterrows():
        candle_range = (row['high'] - row['low']) * 10000
        if candle_range >= 15.0:
            explosive_found = True
            print(f"      💥 {row['ts']} : {candle_range:.1f} pips")
            print(f"         Open: {row['open']:.5f}, High: {row['high']:.5f}, Low: {row['low']:.5f}, Close: {row['close']:.5f}")
    if not explosive_found:
        print("      ❌ Aucun mouvement explosif trouvé")
else:
    print("   ❌ Aucune donnée trouvée dans prices_bern")

print()

print("3️⃣ COMPARAISON : PRICES_1M vs PRICES_BERN")
print("-" * 80)

# Chercher le mouvement explosif à 16:30 dans prices_bern
query_1630_bern = """
SELECT 
    datetime as ts,
    open,
    high,
    low,
    close
FROM prices_bern
WHERE datetime >= '2025-11-20 16:30:00'
  AND datetime < '2025-11-20 16:31:00'
LIMIT 1
"""

result_1630_bern = conn.execute(query_1630_bern).fetchone()

if result_1630_bern:
    ts_1630_bern, open_1630, high_1630, low_1630, close_1630 = result_1630_bern
    range_1630_bern = (high_1630 - low_1630) * 10000
    
    print(f"   📊 Mouvement à 16:30 dans prices_bern :")
    print(f"      Timestamp: {ts_1630_bern}")
    print(f"      Range: {range_1630_bern:.1f} pips")
    print(f"      Open: {open_1630:.5f}, High: {high_1630:.5f}, Low: {low_1630:.5f}, Close: {close_1630:.5f}")
    print()
    
    # Chercher le même prix dans prices_1m (devrait être à 14:30 si la vue fonctionne correctement)
    query_1430_1m = """
    SELECT 
        datetime as ts,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE datetime >= '2025-11-20 14:30:00'
      AND datetime < '2025-11-20 14:31:00'
    LIMIT 1
    """
    
    result_1430_1m = conn.execute(query_1430_1m).fetchone()
    
    if result_1430_1m:
        ts_1430_1m, open_1430, high_1430, low_1430, close_1430 = result_1430_1m
        range_1430_1m = (high_1430 - low_1430) * 10000
        
        print(f"   📊 Prix à 14:30 dans prices_1m (devrait être le même) :")
        print(f"      Timestamp: {ts_1430_1m}")
        print(f"      Range: {range_1430_1m:.1f} pips")
        print(f"      Open: {open_1430:.5f}, High: {high_1430:.5f}, Low: {low_1430:.5f}, Close: {close_1430:.5f}")
        print()
        
        # Vérifier si les prix correspondent
        if abs(open_1630 - open_1430) < 0.00001:
            print(f"   ✅ Les prix correspondent ! La vue fonctionne correctement.")
            print(f"   → prices_1m à 14:30 = prices_bern à 16:30")
            print(f"   → Mais MT5 montre le mouvement à 14:30, pas 16:30")
            print(f"   → PROBLÈME : Les données dans prices_1m sont déjà en UTC+2 !")
        else:
            print(f"   ⚠️ Les prix ne correspondent pas")
            print(f"      Différence Open: {abs(open_1630 - open_1430):.5f}")
    else:
        print(f"   ❌ Aucun prix trouvé à 14:30 dans prices_1m")
else:
    print(f"   ❌ Aucun mouvement explosif trouvé à 16:30 dans prices_bern")

conn.close()

print()
print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)
print()
print("💡 CONCLUSION :")
print("   Si les données dans prices_1m sont déjà en UTC+2 (heure de Berne),")
print("   alors la vue prices_bern ajoute 2 heures de trop, créant un décalage.")
print("   Il faut soit :")
print("   1. Corriger la vue prices_bern pour ne PAS ajouter 2h si les données sont déjà en UTC+2")
print("   2. Ou s'assurer que prices_1m stocke les données en UTC pur")
print()

