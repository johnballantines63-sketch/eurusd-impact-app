"""
VÉRIFICATION PRÉCISE PRIX 1er AOÛT 2025
========================================

Compare prices_bern avec prix MT5 attendus.
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("VÉRIFICATION PRÉCISE PRIX 1er AOÛT 2025")
print("="*80)
print()

# Timestamps clés (en Bern time UTC+2)
timestamps = {
    '14:25': '2025-08-01 14:25:00+02:00',
    '14:26': '2025-08-01 14:26:00+02:00',
    '14:27': '2025-08-01 14:27:00+02:00',
    '14:28': '2025-08-01 14:28:00+02:00',
    '14:29': '2025-08-01 14:29:00+02:00',
    '14:30': '2025-08-01 14:30:00+02:00',
    '14:31': '2025-08-01 14:31:00+02:00',
    '14:32': '2025-08-01 14:32:00+02:00',
    '14:33': '2025-08-01 14:33:00+02:00',
    '14:34': '2025-08-01 14:34:00+02:00',
    '14:35': '2025-08-01 14:35:00+02:00',
    '14:37': '2025-08-01 14:37:00+02:00',
    '14:40': '2025-08-01 14:40:00+02:00',
    '14:45': '2025-08-01 14:45:00+02:00',
    '15:00': '2025-08-01 15:00:00+02:00',
    '15:30': '2025-08-01 15:30:00+02:00',
    '15:36': '2025-08-01 15:36:00+02:00',
}

print("PRIX MINUTES PAR MINUTE autour 14h30 :")
print("-"*80)
print()

for label, ts in timestamps.items():
    result = conn.execute(f"""
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE datetime = '{ts}'
    """).fetchone()
    
    if result:
        dt, o, h, l, c = result
        print(f"{label} ({dt})")
        print(f"   Open  : {o:.5f}")
        print(f"   High  : {h:.5f}")
        print(f"   Low   : {l:.5f}")
        print(f"   Close : {c:.5f}")
        print()
    else:
        print(f"{label} : ❌ Pas de données")
        print()

# Calculer impact EXACT
print("="*80)
print("CALCUL IMPACT")
print("="*80)
print()

# Baseline = dernier prix avant 14:30
baseline_result = conn.execute("""
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime < '2025-08-01 14:30:00+02:00'
    ORDER BY datetime DESC
    LIMIT 1
""").fetchone()

baseline_dt, baseline_price = baseline_result
print(f"📊 BASELINE (avant 14:30) :")
print(f"   {baseline_dt}")
print(f"   Prix : {baseline_price:.5f}")
print()

# Max/min dans fenêtre 14:30 - 15:30
result = conn.execute("""
    SELECT 
        MAX(high) as max_high,
        MIN(low) as min_low
    FROM prices_bern
    WHERE datetime >= '2025-08-01 14:30:00+02:00'
      AND datetime <= '2025-08-01 15:30:00+02:00'
""").fetchone()

max_high, min_low = result

impact_up = (max_high - baseline_price) * 10000
impact_down = (baseline_price - min_low) * 10000

print(f"📈 MAX HIGH (14:30-15:30) : {max_high:.5f} (+{impact_up:.1f} pips)")
print(f"📉 MIN LOW (14:30-15:30)  : {min_low:.5f} (-{impact_down:.1f} pips)")
print()

impact_total = max(impact_up, impact_down)
direction = "HAUT" if impact_up > impact_down else "BAS"

print(f"🎯 IMPACT TOTAL : {impact_total:.1f} pips ({direction})")
print()

# Moment du max
max_time = conn.execute("""
    SELECT datetime, high
    FROM prices_bern
    WHERE datetime >= '2025-08-01 14:30:00+02:00'
      AND datetime <= '2025-08-01 15:30:00+02:00'
    ORDER BY high DESC
    LIMIT 1
""").fetchone()

print(f"   Max atteint : {max_time[0]} ({max_time[1]:.5f})")
print()

print("="*80)
print("COMPARAISON MT5 ATTENDU")
print("="*80)
print()

print("D'après graphique MT5 :")
print("   Baseline : ~1.13975")
print(f"   prices_bern : {baseline_price:.5f}")
print(f"   Écart : {abs(baseline_price - 1.13975)*10000:.1f} pips")
print()

print("   Max spike : ~1.15870")
print(f"   prices_bern : {max_high:.5f}")
print(f"   Écart : {abs(max_high - 1.15870)*10000:.1f} pips")
print()

print("   Impact MT5 : ~189 pips")
print(f"   prices_bern : {impact_total:.1f} pips")
print(f"   Écart : {abs(impact_total - 189):.1f} pips")
print()

if abs(impact_total - 189) < 10:
    print("✅✅ COHÉRENT ! prices_bern correspond à MT5")
else:
    print(f"⚠️ ÉCART SIGNIFICATIF : {abs(impact_total - 189):.1f} pips")

conn.close()

print()
print("="*80)
print("FIN VÉRIFICATION")
print("="*80)
