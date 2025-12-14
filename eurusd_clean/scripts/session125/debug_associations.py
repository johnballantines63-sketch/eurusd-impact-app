#!/usr/bin/env python3
"""
DEBUG - Pourquoi 0 associations ?
"""
import duckdb
import pandas as pd
from pathlib import Path
import pytz

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
TZ_BERN = pytz.timezone('Europe/Zurich')

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("DEBUG - ANALYSE ÉVÉNEMENTS")
print("="*80)
print()

# 1. Vérifier valeurs importance
print("1️⃣ VALEURS IMPORTANCE :")
importance_vals = conn.execute("""
    SELECT importance, COUNT(*) as count
    FROM economic_events
    WHERE datetime_utc >= '2024-01-01'
      AND datetime_utc <= '2025-12-31'
    GROUP BY importance
    ORDER BY count DESC
""").df()
print(importance_vals)
print()

# 2. Événements avec actual ET forecast
print("2️⃣ ÉVÉNEMENTS MESURABLES (actual ET forecast non null) :")
measurable = conn.execute("""
    SELECT 
        importance,
        COUNT(*) as count
    FROM economic_events
    WHERE datetime_utc >= '2024-01-01'
      AND datetime_utc <= '2025-12-31'
      AND actual IS NOT NULL
      AND forecast IS NOT NULL
    GROUP BY importance
    ORDER BY count DESC
""").df()
print(measurable)
print()

# 3. Échantillon événements HIGH
print("3️⃣ ÉCHANTILLON ÉVÉNEMENTS HIGH (10 premiers) :")
sample_high = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE datetime_utc >= '2024-01-01'
      AND datetime_utc <= '2025-12-31'
      AND importance = 'HIGH'
    ORDER BY datetime_utc DESC
    LIMIT 10
""").df()
print(sample_high)
print()

# 4. Événements HIGH mesurables
print("4️⃣ ÉVÉNEMENTS HIGH + MESURABLES :")
high_measurable = conn.execute("""
    SELECT COUNT(*) as count
    FROM economic_events
    WHERE datetime_utc >= '2024-01-01'
      AND datetime_utc <= '2025-12-31'
      AND importance = 'HIGH'
      AND actual IS NOT NULL
      AND forecast IS NOT NULL
""").fetchone()[0]
print(f"   Total : {high_measurable}")
print()

# 5. Événements autour 11 septembre 2025
print("5️⃣ ÉVÉNEMENTS 11 SEPTEMBRE 2025 (±1 jour) :")
sept_11 = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast
    FROM economic_events
    WHERE datetime_utc >= '2025-09-10'
      AND datetime_utc <= '2025-09-12'
    ORDER BY datetime_utc
""").df()

if len(sept_11) > 0:
    print(sept_11.to_string())
    print()
    print(f"   Total événements : {len(sept_11)}")
    
    # Convertir en Bern
    sept_11['datetime_bern'] = pd.to_datetime(sept_11['datetime_utc'], utc=True).dt.tz_convert(TZ_BERN)
    print(f"\n   En timezone Bern :")
    print(sept_11[['datetime_bern', 'event_name', 'importance']].to_string())
else:
    print("   ⚠️ AUCUN événement trouvé le 11 septembre !")
print()

# 6. Vérifier toutes valeurs importance possibles
print("6️⃣ TOUTES VALEURS IMPORTANCE (unique) :")
all_importance = conn.execute("""
    SELECT DISTINCT importance
    FROM economic_events
    ORDER BY importance
""").df()
print(all_importance)
print()

conn.close()

print("="*80)
print("DEBUG TERMINÉ")
print("="*80)
