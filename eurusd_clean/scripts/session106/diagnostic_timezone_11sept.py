#!/usr/bin/env python3
"""
SESSION 106 - DIAGNOSTIC TIMEZONE : CAS 11.09.2025
===================================================

Applique EXACTEMENT méthode Session 92.5 documentée :
- Event 14:30 Bern = 12:30:00+02:00 dans DB
- Prix à chercher : 12:30:00 dans prices_1m.datetime
- Pas de conversion, juste extraire datetime

Date   : 2 novembre 2025
Auteur : Session 106
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime, timedelta

print("="*80)
print("SESSION 106 - DIAGNOSTIC TIMEZONE : CAS 11.09.2025")
print("="*80)
print()

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

script_path = Path(__file__).resolve()
project_root = script_path.parents[3]
db_path = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

DATE_TEST = '2025-09-11'
EXPECTED_IMPACT = 56.8  # Session 103

print("📋 PARAMÈTRES")
print(f"   Date test        : {DATE_TEST}")
print(f"   Impact attendu   : {EXPECTED_IMPACT:.2f} pips (Session 103)")
print()

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1 : CHARGER ÉVÉNEMENT
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("ÉTAPE 1 : CHARGER ÉVÉNEMENT 11.09.2025")
print("-"*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

# Charger premier événement HIGH IMPACT
query_event = """
SELECT 
    e.event_key,
    e.ts_utc,
    e.actual,
    e.estimate,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
LIMIT 1
"""

df_event = conn.execute(query_event, [DATE_TEST]).df()

if df_event.empty:
    print("❌ Aucun événement trouvé")
    conn.close()
    sys.exit(1)

event = df_event.iloc[0]
event_timestamp_db = event['ts_utc']

print(f"✅ Événement trouvé : {event['event_key']}")
print(f"   Timestamp DB : {event_timestamp_db}")
print()

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2 : MÉTHODE SESSION 92.5
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("ÉTAPE 2 : APPLICATION MÉTHODE SESSION 92.5")
print("-"*80)
print()

print("📖 RÈGLE SESSION 92.5 :")
print("   Event 14:30 Bern = 12:30:00+02:00 dans DB")
print("   Prix à chercher : 12:30:00 dans prices_1m.datetime")
print("   → Extraire datetime sans timezone")
print()

# Extraire datetime sans timezone
event_dt = pd.to_datetime(event_timestamp_db)

# Méthode 1 : Utiliser tz_localize(None) pour supprimer timezone
event_dt_naive = event_dt.tz_localize(None) if event_dt.tzinfo else event_dt

print(f"Timestamp DB avec timezone : {event_timestamp_db}")
print(f"Datetime Python            : {event_dt}")
print(f"Datetime sans timezone     : {event_dt_naive}")
print()

# Calculer heure Berne réelle
event_time_bern = event_dt.tz_convert('Europe/Zurich')
print(f"Heure réelle Berne         : {event_time_bern.strftime('%H:%M:%S')} CEST")
print()

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3 : CHARGER PRIX (FENÊTRE 120 MIN)
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("ÉTAPE 3 : CHARGER PRIX DEPUIS prices_1m")
print("-"*80)
print()

# Fenêtre : 120 minutes après événement
window_end = event_dt_naive + timedelta(minutes=120)

print(f"Fenêtre recherche :")
print(f"   Start : {event_dt_naive.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   End   : {window_end.strftime('%Y-%m-%d %H:%M:%S')}")
print()

query_prices = """
SELECT datetime, close, high, low
FROM prices_1m
WHERE datetime >= ?
  AND datetime <= ?
ORDER BY datetime ASC
"""

df_prices = conn.execute(query_prices, [
    event_dt_naive.strftime('%Y-%m-%d %H:%M:%S'),
    window_end.strftime('%Y-%m-%d %H:%M:%S')
]).df()

conn.close()

print(f"✅ {len(df_prices)} candles chargées")
print()

if df_prices.empty:
    print("❌ Aucun prix trouvé !")
    sys.exit(1)

# Afficher premières et dernières candles
print("PREMIÈRES CANDLES :")
for i in range(min(5, len(df_prices))):
    row = df_prices.iloc[i]
    print(f"   {row['datetime']} : close={row['close']:.5f}")
print()

print("DERNIÈRES CANDLES :")
for i in range(max(0, len(df_prices)-5), len(df_prices)):
    row = df_prices.iloc[i]
    print(f"   {row['datetime']} : close={row['close']:.5f}")
print()

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4 : CALCULER IMPACT (3 MÉTHODES)
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("ÉTAPE 4 : CALCUL IMPACT (3 MÉTHODES)")
print("-"*80)
print()

price_start = df_prices.iloc[0]['close']

# Méthode 1 : Close max-min
price_max_close = df_prices['close'].max()
price_min_close = df_prices['close'].min()
impact_up_close = (price_max_close - price_start) * 10000
impact_down_close = (price_start - price_min_close) * 10000

# Méthode 2 : High-Low absolus
price_max_high = df_prices['high'].max()
price_min_low = df_prices['low'].min()
impact_up_high = (price_max_high - price_start) * 10000
impact_down_low = (price_start - price_min_low) * 10000

# Méthode 3 : Max amplitude (High max - Low min)
amplitude_total = (price_max_high - price_min_low) * 10000

print("MÉTHODE 1 : CLOSE (max-min)")
print(f"   Prix start       : {price_start:.5f}")
print(f"   Prix max (close) : {price_max_close:.5f}")
print(f"   Prix min (close) : {price_min_close:.5f}")
print(f"   Impact UP        : {impact_up_close:.2f} pips")
print(f"   Impact DOWN      : {impact_down_close:.2f} pips")
print(f"   Impact dominant  : {max(abs(impact_up_close), abs(impact_down_close)):.2f} pips")
print()

print("MÉTHODE 2 : HIGH-LOW absolus")
print(f"   Prix start       : {price_start:.5f}")
print(f"   High max         : {price_max_high:.5f}")
print(f"   Low min          : {price_min_low:.5f}")
print(f"   Impact UP        : {impact_up_high:.2f} pips")
print(f"   Impact DOWN      : {impact_down_low:.2f} pips")
print(f"   Impact dominant  : {max(abs(impact_up_high), abs(impact_down_low)):.2f} pips")
print()

print("MÉTHODE 3 : AMPLITUDE TOTALE")
print(f"   High max         : {price_max_high:.5f}")
print(f"   Low min          : {price_min_low:.5f}")
print(f"   Amplitude        : {amplitude_total:.2f} pips")
print()

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5 : COMPARAISON AVEC 56.8 PIPS
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("ÉTAPE 5 : COMPARAISON AVEC IMPACT ATTENDU")
print("-"*80)
print()

impact_methods = [
    ("Close dominant", max(abs(impact_up_close), abs(impact_down_close))),
    ("High-Low dominant", max(abs(impact_up_high), abs(impact_down_low))),
    ("Amplitude totale", amplitude_total),
    ("Close UP", abs(impact_up_close)),
    ("High UP", abs(impact_up_high)),
]

print(f"Impact attendu (Session 103) : {EXPECTED_IMPACT:.2f} pips")
print()

best_match = None
best_error = float('inf')

for method_name, impact_value in impact_methods:
    error = abs(impact_value - EXPECTED_IMPACT)
    error_pct = (error / EXPECTED_IMPACT) * 100
    
    status = "✅" if error < 5.0 else "⚠️" if error < 10.0 else "❌"
    
    print(f"{status} {method_name:20s} : {impact_value:6.2f} pips (erreur {error:5.2f} pips, {error_pct:5.1f}%)")
    
    if error < best_error:
        best_error = error
        best_match = (method_name, impact_value)

print()
print("="*80)
print("MEILLEURE MÉTHODE")
print("-"*80)
print()

print(f"🏆 {best_match[0]}")
print(f"   Impact mesuré : {best_match[1]:.2f} pips")
print(f"   Impact attendu : {EXPECTED_IMPACT:.2f} pips")
print(f"   Erreur : {best_error:.2f} pips ({(best_error/EXPECTED_IMPACT)*100:.1f}%)")
print()

if best_error < 5.0:
    print("✅✅✅ MÉTHODE VALIDÉE !")
    print()
    print("Cette méthode de mesure est correcte pour Session 106")
elif best_error < 10.0:
    print("✅ MÉTHODE ACCEPTABLE")
    print()
    print("Erreur < 10 pips : Performance correcte")
else:
    print("⚠️  ÉCART IMPORTANT")
    print()
    print("Investigation supplémentaire nécessaire")
    print()
    print("Vérifier :")
    print("  - Fenêtre de temps (60 vs 120 min ?)")
    print("  - Méthode calcul (peak absolu vs départ ?)")
    print("  - Timestamps (timezone correcte ?)")

print()
print("="*80)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*80)
