#!/usr/bin/env python3
"""
DEBUG CAS 11.09.2025 - SESSION 103
==================================

Test SOLUTION #1 : Calcul amplitude max-min
Vérification HYPOTHÈSE #1 : Prix revenu au niveau initial
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import numpy as np

# Ajouter chemin config
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path
from detect_trend_extremum import detect_trend_from_extremum

print("=" * 80)
print("DEBUG CAS 11.09.2025 - TEST SOLUTION #1")
print("=" * 80)

# Cas référence 11.09.2025
event_date = datetime(2025, 9, 11, 14, 30)  # Bern time
event_time_utc = datetime(2025, 9, 11, 12, 30)  # UTC time
start_time = event_time_utc - timedelta(hours=72)

print(f"\n📅 Période analyse :")
print(f"   Début  : {start_time} UTC")
print(f"   Fin    : {event_time_utc} UTC")
print(f"   Durée  : 72 heures")

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print(f"\n✅ Connexion DB : {db_path}")

# Query prix 72h
query = """
SELECT datetime, close
FROM prices_1m
WHERE datetime >= ?
  AND datetime < ?
ORDER BY datetime ASC
"""

df_prices = conn.execute(query, [start_time, event_time_utc]).fetchdf()
conn.close()

print(f"✅ Chargé {len(df_prices)} points prix (M1)")

# Extraire prix et timestamps
prices = df_prices['close'].values
timestamps = df_prices['datetime'].tolist()

print(f"\n📊 Statistiques prix 72h :")
print(f"   Min  : {prices.min():.4f}")
print(f"   Max  : {prices.max():.4f}")
print(f"   Range: {(prices.max() - prices.min()) * 10000:.1f} pips")

# Détecter tendance avec window=240 (4h)
print(f"\n🔍 Détection tendance (window=240 = 4h)...")
trend_info = detect_trend_from_extremum(prices, timestamps, window_swing=240)

print(f"\n📍 RÉSULTATS DÉTECTION TENDANCE :")
print("-" * 80)
print(f"   Type extremum     : {trend_info['extremum_type']}")
print(f"   Index début       : {trend_info['start_idx']}")
print(f"   Index fin         : {trend_info['end_idx']}")

if trend_info['start_idx'] < len(timestamps):
    print(f"   Timestamp début   : {timestamps[trend_info['start_idx']]}")
if trend_info['end_idx'] < len(timestamps):
    print(f"   Timestamp fin     : {timestamps[trend_info['end_idx']]}")

print(f"\n📊 MÉTRIQUES TENDANCE :")
print("-" * 80)
print(f"   Durée             : {trend_info['duration_hours']:.1f} heures")
print(f"   Amplitude         : {trend_info['amplitude_pips']:.1f} pips")
print(f"   Direction         : {trend_info['direction']}")
print(f"   R²                : {trend_info['r_squared']:.3f}")
print(f"   Pente (pips/h)    : {trend_info['slope_pips_hour']:.2f}")

# Comparaison avec valeurs attendues MT5
print(f"\n🎯 COMPARAISON AVEC MT5 (Ground Truth) :")
print("-" * 80)
print(f"   {'Métrique':<20} {'Détecté':>12} {'Attendu':>12} {'Écart':>12}")
print("-" * 80)

expected_amplitude = 83.0  # pips
expected_duration = 54.0   # heures
expected_r2 = 0.6         # approximatif

amplitude_error = abs(trend_info['amplitude_pips'] - expected_amplitude)
duration_error = abs(trend_info['duration_hours'] - expected_duration)

print(f"   {'Amplitude (pips)':<20} {trend_info['amplitude_pips']:>12.1f} {expected_amplitude:>12.1f} {amplitude_error:>11.1f}")
print(f"   {'Durée (heures)':<20} {trend_info['duration_hours']:>12.1f} {expected_duration:>12.1f} {duration_error:>11.1f}")
print(f"   {'R²':<20} {trend_info['r_squared']:>12.3f} {expected_r2:>12.3f} {abs(trend_info['r_squared'] - expected_r2):>11.3f}")

# Vérifier HYPOTHÈSE #1 : Prix revenu au niveau initial
print(f"\n🔬 VÉRIFICATION HYPOTHÈSE #1 : Prix revenu au niveau initial")
print("-" * 80)

start_idx = trend_info['start_idx']
end_idx = trend_info['end_idx']

if start_idx < len(prices) and end_idx < len(prices):
    price_start = prices[start_idx]
    price_end = prices[end_idx]
    
    # Amplitude avec ancienne méthode (end-start)
    amplitude_old_method = abs(price_end - price_start) * 10000
    
    # Amplitude avec nouvelle méthode (max-min)
    segment_prices = prices[start_idx:end_idx + 1]
    amplitude_new_method = (segment_prices.max() - segment_prices.min()) * 10000
    
    print(f"   Prix début (extremum) : {price_start:.4f}")
    print(f"   Prix fin (événement)  : {price_end:.4f}")
    print(f"   Différence abs        : {amplitude_old_method:.1f} pips")
    print(f"\n   Max segment           : {segment_prices.max():.4f}")
    print(f"   Min segment           : {segment_prices.min():.4f}")
    print(f"   Amplitude max-min     : {amplitude_new_method:.1f} pips")
    
    print(f"\n   {'Méthode':<25} {'Amplitude (pips)':>20}")
    print("   " + "-" * 45)
    print(f"   {'Ancienne (end-start)':<25} {amplitude_old_method:>20.1f}")
    print(f"   {'Nouvelle (max-min)':<25} {amplitude_new_method:>20.1f}")
    print(f"   {'Amélioration':<25} {amplitude_new_method - amplitude_old_method:>19.1f}")
    
    # Diagnostic
    print(f"\n   📋 DIAGNOSTIC :")
    
    if amplitude_old_method < 10 and amplitude_new_method > 70:
        print(f"   ✅✅ HYPOTHÈSE #1 CONFIRMÉE !")
        print(f"      → Prix est revenu près du niveau initial")
        print(f"      → Ancienne méthode sous-estime drastiquement")
        print(f"      → Nouvelle méthode capture vraie oscillation")
    elif amplitude_new_method >= 70:
        print(f"   ✅ SOLUTION #1 FONCTIONNE")
        print(f"      → Amplitude détectée : {amplitude_new_method:.1f} pips")
        print(f"      → Dans la plage attendue (70-90 pips)")
    elif amplitude_new_method >= 40:
        print(f"   ⚠️  AMÉLIORATION PARTIELLE")
        print(f"      → Amplitude : {amplitude_new_method:.1f} pips")
        print(f"      → Mieux mais sous cible (70-90 pips)")
    else:
        print(f"   ❌ PROBLÈME PERSISTE")
        print(f"      → Amplitude toujours sous-estimée")
        print(f"      → Nécessite investigation HYPOTHÈSE #2 ou #3")

# Critères de succès
print(f"\n🎯 CRITÈRES SUCCÈS SOLUTION #1 :")
print("-" * 80)

success_criteria = []
success_criteria.append(("Amplitude 70-90 pips", 70 <= trend_info['amplitude_pips'] <= 90))
success_criteria.append(("Durée 45-55h", 45 <= trend_info['duration_hours'] <= 55))
success_criteria.append(("R² > 0.4", trend_info['r_squared'] > 0.4))

for criterion, passed in success_criteria:
    status = "✅" if passed else "❌"
    print(f"   {status} {criterion}")

all_passed = all([passed for _, passed in success_criteria])

print(f"\n{'='*80}")
if all_passed:
    print("✅✅ SOLUTION #1 : SUCCÈS TOTAL")
    print("\nRECOMMANDATION : Procéder avec calibration formules")
elif any([passed for _, passed in success_criteria]):
    print("⚠️  SOLUTION #1 : SUCCÈS PARTIEL")
    print("\nRECOMMANDATION : Vérifier formules, debug additionnel si nécessaire")
else:
    print("❌ SOLUTION #1 : ÉCHEC")
    print("\nRECOMMANDATION : Tester HYPOTHÈSE #2 ou #3 (voir HANDOFF)")

print("=" * 80)
