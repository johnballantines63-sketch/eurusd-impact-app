"""
DEBUG - VÉRIFICATION TIMEZONE PRICES_1M
========================================

Compare les prix autour de 14:30 avec/sans offset timezone
pour déterminer si prices_1m est en UTC ou UTC+2
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime, timedelta

project_root = Path(__file__).resolve().parents[3]
DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

print("="*80)
print("🔍 VÉRIFICATION TIMEZONE PRICES_1M")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Event timestamp (supposé UTC+2)
EVENT_TIME_BERN = "2025-09-11 14:30:00"
EVENT_TIME_UTC = "2025-09-11 12:30:00"  # -2h si conversion en UTC

print("\n📊 CONTEXTE :")
print(f"   Event time (Bern UTC+2) : {EVENT_TIME_BERN}")
print(f"   Event time (UTC)        : {EVENT_TIME_UTC}")
print(f"   Impact attendu MT5      : 56.2 pips dans les 5 premières minutes")

# Scénario 1 : Si prices_1m est en UTC+2 (même que events)
print("\n" + "="*80)
print("SCÉNARIO 1 : prices_1m en UTC+2 (comme events)")
print("="*80)
print(f"On cherche les prix à partir de {EVENT_TIME_BERN}")

query_bern = f"""
SELECT 
    datetime,
    open,
    high,
    low,
    close,
    (high - LAG(close) OVER (ORDER BY datetime)) * 10000 as pips_move
FROM prices_1m
WHERE datetime >= '{EVENT_TIME_BERN}'
  AND datetime <= '{EVENT_TIME_BERN}'::TIMESTAMP + INTERVAL '10 minutes'
ORDER BY datetime
"""

df_bern = conn.execute(query_bern).fetchdf()
print("\n📈 Prix 14:30-14:40 (Bern time) :")
print(df_bern.to_string(index=False))

if len(df_bern) > 0:
    first_close = df_bern.iloc[0]['close']
    max_high = df_bern['high'].max()
    impact_bern = (max_high - first_close) * 10000
    print(f"\n   📊 Impact calculé : {impact_bern:.1f} pips")
    
    if abs(impact_bern - 56.2) < 5:
        print(f"   ✅ ✅ PROCHE DE 56.2 PIPS → prices_1m est probablement en UTC+2")
    else:
        print(f"   ❌ {impact_bern:.1f} pips loin de 56.2 → pas UTC+2")

# Scénario 2 : Si prices_1m est en UTC (décalé de -2h)
print("\n" + "="*80)
print("SCÉNARIO 2 : prices_1m en UTC (décalé -2h)")
print("="*80)
print(f"On cherche les prix à partir de {EVENT_TIME_UTC}")

query_utc = f"""
SELECT 
    datetime,
    open,
    high,
    low,
    close,
    (high - LAG(close) OVER (ORDER BY datetime)) * 10000 as pips_move
FROM prices_1m
WHERE datetime >= '{EVENT_TIME_UTC}'
  AND datetime <= '{EVENT_TIME_UTC}'::TIMESTAMP + INTERVAL '10 minutes'
ORDER BY datetime
"""

df_utc = conn.execute(query_utc).fetchdf()
print("\n📈 Prix 12:30-12:40 (UTC) :")
print(df_utc.to_string(index=False))

if len(df_utc) > 0:
    first_close = df_utc.iloc[0]['close']
    max_high = df_utc['high'].max()
    impact_utc = (max_high - first_close) * 10000
    print(f"\n   📊 Impact calculé : {impact_utc:.1f} pips")
    
    if abs(impact_utc - 56.2) < 5:
        print(f"   ✅ ✅ PROCHE DE 56.2 PIPS → prices_1m est probablement en UTC")
    else:
        print(f"   ❌ {impact_utc:.1f} pips loin de 56.2 → pas UTC")

# Comparaison directe
print("\n" + "="*80)
print("📊 COMPARAISON IMPACTS")
print("="*80)

if len(df_bern) > 0 and len(df_utc) > 0:
    first_close_bern = df_bern.iloc[0]['close']
    max_high_bern = df_bern['high'].max()
    impact_bern = (max_high_bern - first_close_bern) * 10000
    
    first_close_utc = df_utc.iloc[0]['close']
    max_high_utc = df_utc['high'].max()
    impact_utc = (max_high_utc - first_close_utc) * 10000
    
    print(f"\nImpact avec Bern time (14:30) : {impact_bern:.1f} pips")
    print(f"Impact avec UTC (12:30)       : {impact_utc:.1f} pips")
    print(f"Impact attendu MT5            : 56.2 pips")
    
    ecart_bern = abs(impact_bern - 56.2)
    ecart_utc = abs(impact_utc - 56.2)
    
    print(f"\nÉcart Bern : {ecart_bern:.1f} pips")
    print(f"Écart UTC  : {ecart_utc:.1f} pips")
    
    if ecart_utc < ecart_bern:
        print("\n✅ ✅ ✅ CONCLUSION : prices_1m est en UTC !")
        print("   → Il faut CONVERTIR event_time de UTC+2 vers UTC")
        print("   → Soustraire 2 heures à event_timestamp avant la requête")
    else:
        print("\n⚠️ CONCLUSION : prices_1m semble en UTC+2")
        print("   → Mais alors pourquoi l'impact mesuré est faux ?")
        print("   → Investiguer d'autres causes...")

# Bonus : Vérifier métadonnées timezone
print("\n" + "="*80)
print("🔍 MÉTADONNÉES TIMEZONE")
print("="*80)

# Check si datetime a timezone info
sample = conn.execute("SELECT datetime FROM prices_1m LIMIT 1").fetchdf()
print(f"\nType colonne datetime : {sample['datetime'].dtype}")
print(f"Timezone info : {sample['datetime'].dt.tz}")

conn.close()

print("\n" + "="*80)
print("✅ VÉRIFICATION TERMINÉE")
print("="*80)
