#!/usr/bin/env python3
"""
DEBUG DÉTECTION EXTREMA - SESSION 103
=====================================

Objectif : Comprendre POURQUOI aucune inversion n'est détectée
alors qu'on les voit sur les graphiques MT5
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Ajouter chemin config
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("DEBUG DÉTECTION EXTREMA - CAS 11.09.2025")
print("=" * 80)

# Cas référence
event_time_utc = datetime(2025, 9, 11, 12, 30)
start_time = event_time_utc - timedelta(hours=72)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT datetime, close
FROM prices_1m
WHERE datetime >= ?
  AND datetime < ?
ORDER BY datetime ASC
"""

df_prices = conn.execute(query, [start_time, event_time_utc]).fetchdf()
conn.close()

prices = df_prices['close'].values
timestamps = pd.to_datetime(df_prices['datetime']).tolist()

print(f"\n✅ Chargé {len(df_prices)} points prix (M1)")
print(f"   Prix min : {prices.min():.4f}")
print(f"   Prix max : {prices.max():.4f}")
print(f"   Range    : {(prices.max() - prices.min()) * 10000:.1f} pips")

# Index du pic attendu (9/09 06:00 UTC)
target_time = pd.Timestamp('2025-09-09 06:00:00', tz='UTC')

# Convertir timestamps en pandas si nécessaire
if isinstance(timestamps[0], pd.Timestamp):
    timestamps_tz = [t.tz_localize('UTC') if t.tz is None else t.tz_convert('UTC') for t in timestamps]
else:
    timestamps_tz = [pd.Timestamp(t, tz='UTC') for t in timestamps]

# Trouver index le plus proche
time_diffs = [abs((t - target_time).total_seconds()) for t in timestamps_tz]
target_idx = np.argmin(time_diffs)

print(f"\n🎯 PIC ATTENDU (9/09 08:00 Bern = 06:00 UTC) :")
print(f"   Index trouvé : {target_idx}")
print(f"   Timestamp    : {timestamps[target_idx]}")
print(f"   Prix         : {prices[target_idx]:.4f}")

# Vérifier que c'est bien un maximum local
window_check = 120  # 2h de chaque côté
if target_idx > window_check and target_idx < len(prices) - window_check:
    left = prices[target_idx - window_check : target_idx]
    right = prices[target_idx + 1 : target_idx + window_check + 1]
    
    is_local_max = prices[target_idx] > left.max() and prices[target_idx] > right.max()
    
    print(f"\n   Vérification maximum local (±{window_check}min) :")
    print(f"   Prix centre  : {prices[target_idx]:.4f}")
    print(f"   Max gauche   : {left.max():.4f}")
    print(f"   Max droite   : {right.max():.4f}")
    print(f"   Est max local: {'✅ OUI' if is_local_max else '❌ NON'}")

# ============================================================================
# TEST DÉTECTION AVEC DIFFÉRENTS PARAMÈTRES
# ============================================================================

def detect_swing_highs_debug(prices, window=240, threshold=0.0):
    """Version debug avec threshold flexible"""
    swing_highs = []
    
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    
    return swing_highs

print("\n" + "=" * 80)
print("TEST DÉTECTION SWING HIGHS AVEC DIFFÉRENTS PARAMÈTRES")
print("=" * 80)

# Tester différentes combinaisons
test_configs = [
    {'window': 120, 'threshold': 0.0, 'label': 'Window 2h, threshold 0'},
    {'window': 240, 'threshold': 0.0, 'label': 'Window 4h, threshold 0'},
    {'window': 480, 'threshold': 0.0, 'label': 'Window 8h, threshold 0'},
    {'window': 720, 'threshold': 0.0, 'label': 'Window 12h, threshold 0'},
    {'window': 1440, 'threshold': 0.0, 'label': 'Window 24h, threshold 0'},
]

for config in test_configs:
    highs = detect_swing_highs_debug(prices, config['window'], config['threshold'])
    
    print(f"\n{config['label']} :")
    print(f"   Nombre pics détectés : {len(highs)}")
    
    if len(highs) > 0:
        # Afficher les 5 pics les plus hauts
        high_prices = [(idx, prices[idx]) for idx in highs]
        high_prices.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   Top 5 pics :")
        for rank, (idx, price) in enumerate(high_prices[:5], 1):
            time_str = timestamps[idx].strftime('%Y-%m-%d %H:%M') if idx < len(timestamps) else 'N/A'
            is_target = idx == target_idx or abs(idx - target_idx) < 60
            marker = " ← CIBLE !" if is_target else ""
            print(f"      {rank}. Index {idx:5d} | {time_str} | {price:.4f}{marker}")
        
        # Vérifier si target est dans les pics détectés
        if target_idx in highs:
            print(f"   ✅ Pic cible (9/09) DÉTECTÉ !")
        else:
            # Chercher le plus proche
            closest_idx = min(highs, key=lambda x: abs(x - target_idx))
            time_diff_minutes = abs(closest_idx - target_idx)
            print(f"   ⚠️  Pic cible NON détecté")
            print(f"   Pic le plus proche : index {closest_idx} (écart {time_diff_minutes} min)")

# ============================================================================
# MÉTHODE ALTERNATIVE : TROUVER MAX/MIN DANS SEGMENTS
# ============================================================================

print("\n" + "=" * 80)
print("MÉTHODE ALTERNATIVE : MAX/MIN PAR SEGMENTS")
print("=" * 80)

# Diviser 72h en segments et trouver max de chaque
segments = [
    {'start': 0, 'end': 24*60, 'label': 'Jour 1 (0-24h)'},
    {'start': 24*60, 'end': 48*60, 'label': 'Jour 2 (24-48h)'},
    {'start': 48*60, 'end': 72*60, 'label': 'Jour 3 (48-72h)'},
]

print("\nMax de chaque segment 24h :")
for seg in segments:
    seg_prices = prices[seg['start']:seg['end']]
    max_idx_relative = np.argmax(seg_prices)
    max_idx_absolute = seg['start'] + max_idx_relative
    
    time_str = timestamps[max_idx_absolute].strftime('%Y-%m-%d %H:%M')
    is_target = abs(max_idx_absolute - target_idx) < 60
    marker = " ← CIBLE !" if is_target else ""
    
    print(f"\n   {seg['label']}")
    print(f"   Max : {seg_prices.max():.4f}")
    print(f"   Index : {max_idx_absolute}")
    print(f"   Time  : {time_str}{marker}")

# ============================================================================
# SOLUTION SIMPLE : TOP N EXTREMA PAR AMPLITUDE
# ============================================================================

print("\n" + "=" * 80)
print("SOLUTION SIMPLE : IDENTIFIER TOP EXTREMA PAR PROMINENCE")
print("=" * 80)

# Pour chaque point, calculer "prominence" = distance vs voisins
window_prominence = 6 * 60  # 6 heures

prominences = []

for i in range(window_prominence, len(prices) - window_prominence):
    center = prices[i]
    
    # Prix min et max dans fenêtre autour
    left = prices[i - window_prominence : i]
    right = prices[i + 1 : i + window_prominence + 1]
    
    # Prominence = à quel point ce point est plus haut que l'environnement
    min_around = min(left.min(), right.min())
    prominence = (center - min_around) * 10000  # en pips
    
    prominences.append({
        'index': i,
        'price': center,
        'prominence': prominence,
        'time': timestamps[i] if i < len(timestamps) else None
    })

# Trier par prominence
prominences.sort(key=lambda x: x['prominence'], reverse=True)

print(f"\nTop 10 points avec plus grande prominence (fenêtre {window_prominence}min) :")
for rank, prom in enumerate(prominences[:10], 1):
    time_str = prom['time'].strftime('%Y-%m-%d %H:%M') if prom['time'] else 'N/A'
    is_target = abs(prom['index'] - target_idx) < 60
    marker = " ← CIBLE !" if is_target else ""
    print(f"   {rank:2d}. {time_str} | Prix {prom['price']:.4f} | Prominence {prom['prominence']:6.1f} pips{marker}")

# ============================================================================
# RECOMMANDATION
# ============================================================================

print("\n" + "=" * 80)
print("RECOMMANDATION")
print("=" * 80)

# Vérifier si cible est dans top 10
target_in_top10 = any(abs(p['index'] - target_idx) < 60 for p in prominences[:10])

if target_in_top10:
    print("\n✅ Le pic du 9/09 est dans le TOP 10 par prominence !")
    print("\n   Recommandation :")
    print("   1. Utiliser méthode 'prominence' pour identifier extrema majeurs")
    print("   2. Prendre les N extrema les plus prominents (ex: top 3)")
    print("   3. Analyser inversions entre ces extrema")
else:
    print("\n⚠️  Le pic du 9/09 n'est PAS dans le top 10 par prominence")
    print("\n   Cela suggère que :")
    print("   - Soit le pic n'est pas aussi 'majeur' dans le contexte 72h")
    print("   - Soit la fenêtre prominence (6h) est inadaptée")
    print("   - Soit il faut une autre méthode")

print("\n" + "=" * 80)
