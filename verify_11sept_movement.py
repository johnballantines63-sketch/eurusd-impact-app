"""
VÉRIFICATION MOUVEMENT 11 SEPTEMBRE 14:30
Compare MFE calculé vs mouvement observé sur MT5
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

print("=" * 80)
print("🔍 VÉRIFICATION MOUVEMENT 11 SEPTEMBRE 2025 - 14:30")
print("=" * 80)
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Charger les prix minute par minute
# ════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("📊 Chargement des prix 1-minute pour le 11 septembre 14:30...")
print()

# Heure de l'événement : 14:30 UTC
event_time = "2025-09-11 14:30:00"

# Charger les prix de 14:25 à 15:30 (65 minutes)
query_prices = """
SELECT 
    timestamp,
    strftime(to_timestamp(timestamp), '%H:%M:%S') as time_str,
    close,
    high,
    low,
    (high + low) / 2.0 as mid
FROM prices_1m
WHERE to_timestamp(timestamp) >= TIMESTAMP '2025-09-11 14:25:00'
  AND to_timestamp(timestamp) <= TIMESTAMP '2025-09-11 15:30:00'
ORDER BY timestamp
"""

prices_df = conn.execute(query_prices).fetchdf()

if len(prices_df) == 0:
    print("❌ ERREUR : Aucune donnée de prix trouvée pour cette période !")
    print("   Vérifiez si les données existent dans prices_1m")
    conn.close()
    exit(1)

print(f"✅ {len(prices_df)} bougies 1-minute chargées")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Identifier le prix de référence (14:30)
# ════════════════════════════════════════════════════════════════

reference_row = prices_df[prices_df['time_str'] == '14:30:00']

if len(reference_row) == 0:
    print("⚠️ Pas de bougie exactement à 14:30, utilisation de la bougie la plus proche")
    reference_row = prices_df.iloc[0]
    reference_price = reference_row['close'].values[0] if hasattr(reference_row['close'], 'values') else reference_row['close']
else:
    reference_price = reference_row['close'].values[0]

print(f"📍 Prix de référence (14:30) : {reference_price:.5f}")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Calculer le MFE (60 minutes)
# ════════════════════════════════════════════════════════════════

print("📊 Calcul du MFE sur 60 minutes (14:30 → 15:30)...")
print()

# Filtrer fenêtre 60 minutes
window_60min = prices_df[prices_df['time_str'] <= '15:30:00'].copy()

# Calculer excursions depuis référence
window_60min['excursion_up'] = (window_60min['high'] - reference_price) * 10000  # pips
window_60min['excursion_down'] = (reference_price - window_60min['low']) * 10000  # pips

# MFE = max des excursions
max_excursion_up = window_60min['excursion_up'].max()
max_excursion_down = window_60min['excursion_down'].max()
mfe_60min = max(max_excursion_up, max_excursion_down)

print(f"   Excursion max UP   : {max_excursion_up:.1f} pips")
print(f"   Excursion max DOWN : {max_excursion_down:.1f} pips")
print(f"   MFE (60 min)       : {mfe_60min:.1f} pips")
print()

# Identifier le moment du MFE
if max_excursion_up > max_excursion_down:
    mfe_row = window_60min.loc[window_60min['excursion_up'].idxmax()]
    direction = "UP"
    peak_price = mfe_row['high']
else:
    mfe_row = window_60min.loc[window_60min['excursion_down'].idxmax()]
    direction = "DOWN"
    peak_price = mfe_row['low']

print(f"   Direction MFE      : {direction}")
print(f"   Heure du pic       : {mfe_row['time_str']}")
print(f"   Prix du pic        : {peak_price:.5f}")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Comparer avec la DB
# ════════════════════════════════════════════════════════════════

print("🔍 Comparaison avec event_group_impacts...")
print()

query_db_impact = """
SELECT 
    mfe_pips,
    direction,
    peak_price,
    strftime(peak_time, '%H:%M:%S') as peak_time_str,
    reference_price
FROM event_group_impacts
WHERE time_group = TIMESTAMP '2025-09-11 14:30:00'
"""

db_impact = conn.execute(query_db_impact).fetchdf()

if len(db_impact) > 0:
    db_mfe = db_impact['mfe_pips'].values[0]
    db_direction = db_impact['direction'].values[0]
    db_peak_price = db_impact['peak_price'].values[0]
    db_peak_time = db_impact['peak_time_str'].values[0]
    db_reference = db_impact['reference_price'].values[0]
    
    print(f"   MFE DB             : {db_mfe:.1f} pips")
    print(f"   Direction DB       : {db_direction}")
    print(f"   Prix référence DB  : {db_reference:.5f}")
    print(f"   Prix pic DB        : {db_peak_price:.5f}")
    print(f"   Heure pic DB       : {db_peak_time}")
    print()
    
    # Comparaison
    diff_mfe = abs(mfe_60min - db_mfe)
    print(f"   Différence MFE     : {diff_mfe:.1f} pips")
    
    if diff_mfe < 1:
        print(f"   ✅ CONCORDANCE PARFAITE")
    elif diff_mfe < 5:
        print(f"   ✅ Concordance bonne")
    else:
        print(f"   ⚠️ Écart significatif")
else:
    print("   ❌ Aucune donnée dans event_group_impacts pour 14:30")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Analyser le mouvement total observé
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 ANALYSE DU MOUVEMENT TOTAL")
print("=" * 80)
print()

# Prix min et max sur toute la période
min_price = window_60min['low'].min()
max_price = window_60min['high'].max()
total_range = (max_price - min_price) * 10000

print(f"   Prix minimum       : {min_price:.5f}")
print(f"   Prix maximum       : {max_price:.5f}")
print(f"   Range total        : {total_range:.1f} pips")
print()

# Heure du min et max
min_row = window_60min.loc[window_60min['low'].idxmin()]
max_row = window_60min.loc[window_60min['high'].idxmax()]

print(f"   Heure du min       : {min_row['time_str']}")
print(f"   Heure du max       : {max_row['time_str']}")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 6 : Graphique ASCII simple
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📈 ÉVOLUTION DES PRIX (14:30 → 15:30)")
print("=" * 80)
print()

# Afficher quelques points clés
print(f"{'Heure':<10} {'Close':<12} {'Excursion':<15} {'Direction'}")
print("-" * 60)

for idx, row in window_60min.iterrows():
    if row['time_str'] in ['14:30:00', '14:35:00', '14:40:00', '14:45:00', '15:00:00', '15:15:00', '15:30:00'] or row['time_str'] == mfe_row['time_str']:
        exc_up = row['excursion_up']
        exc_down = row['excursion_down']
        
        if exc_up > exc_down:
            direction_symbol = f"↑ +{exc_up:.1f} pips"
        else:
            direction_symbol = f"↓ -{exc_down:.1f} pips"
        
        marker = " ⭐ MFE" if row['time_str'] == mfe_row['time_str'] else ""
        
        print(f"{row['time_str']:<10} {row['close']:<12.5f} {direction_symbol:<15} {marker}")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 7 : Verdict final
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("🎯 VERDICT FINAL")
print("=" * 80)
print()

print(f"MFE calculé (méthode DB)    : {mfe_60min:.1f} pips")
print(f"MFE stocké dans DB          : {db_mfe:.1f} pips" if len(db_impact) > 0 else "MFE stocké dans DB          : N/A")
print(f"Range total observé         : {total_range:.1f} pips")
print()

print("💡 INTERPRÉTATION :")
print(f"   • Le MFE (59.2 pips) mesure l'excursion MAX depuis le prix de référence")
print(f"   • Le Range total ({total_range:.1f} pips) mesure du min au max absolu")
print(f"   • Si vous observez ~200 pips sur MT5, cela peut être :")
print(f"     - Un mouvement sur une fenêtre plus large (>60 min)")
print(f"     - Une mesure différente (bougies 5min ou 15min)")
print(f"     - Ou un mouvement cumulé sur plusieurs phases")

print()
print("=" * 80)
print("✅ ANALYSE TERMINÉE")
print("=" * 80)

conn.close()
