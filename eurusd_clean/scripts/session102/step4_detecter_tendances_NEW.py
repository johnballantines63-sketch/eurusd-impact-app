#!/usr/bin/env python3
"""
ÉTAPE 4 : DÉTECTER TENDANCES
=============================

Pour chaque date :
1. Charger 14 jours de prix avant événement
2. Détecter inversions (peaks/troughs avec prominence 20 pips)
3. Calculer tendance DEPUIS dernière inversion
4. Métriques : R², amplitude, durée RÉELLE

ENTRÉE : step3_amplifications_parfaites_NEW.csv
SORTIE : step4_avec_tendances_NEW.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from scipy import signal
import sys

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("ÉTAPE 4 : DÉTECTER TENDANCES")
print("=" * 80)
print()

# ============================================================================
# CHARGER RÉSULTATS STEP3
# ============================================================================

data_dir = Path(__file__).parent / "data"
step3_path = data_dir / "step3_amplifications_parfaites_NEW.csv"

if not step3_path.exists():
    print(f"❌ Fichier manquant : {step3_path.name}")
    print(f"   → Exécuter d'abord : python3 step3_amplifications_parfaites_NEW.py")
    sys.exit(1)

df_step3 = pd.read_csv(step3_path)
df_step3['event_date'] = pd.to_datetime(df_step3['event_date'])

print(f"✅ {len(df_step3)} dates à traiter")
print()

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# DÉTECTER TENDANCE POUR CHAQUE DATE
# ============================================================================

results = []

for idx, row in df_step3.iterrows():
    event_date = row['event_date']
    
    print(f"\n{'='*80}")
    print(f"{event_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}")
    
    # Charger 14 jours de prix avant événement
    time_start = event_date - timedelta(days=14)
    time_end = event_date - timedelta(hours=1)
    
    query = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= ? AND datetime < ?
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query, [time_start, time_end]).fetchdf()
    
    if len(df_prices) < 100:
        print(f"   ⚠️ Pas assez de données ({len(df_prices)} points)")
        continue
    
    prices = df_prices['close'].values
    
    # Détecter inversions (peaks et troughs)
    peaks, _ = signal.find_peaks(prices, prominence=0.0020)  # 20 pips
    troughs, _ = signal.find_peaks(-prices, prominence=0.0020)
    
    # Tous les extrema (triés par index)
    extrema = sorted(list(peaks) + list(troughs))
    
    print(f"   {len(peaks)} peaks, {len(troughs)} troughs → {len(extrema)} extrema")
    
    if len(extrema) == 0:
        # Pas d'inversion : tendance sur 14j complets
        last_idx = 0
        print(f"   Pas d'inversion → tendance depuis début (14j)")
    else:
        # Dernière inversion
        last_idx = extrema[-1]
        print(f"   Dernière inversion : index {last_idx}")
    
    # Tendance depuis dernière inversion
    trend_prices = prices[last_idx:]
    
    if len(trend_prices) < 10:
        print(f"   ⚠️ Tendance trop courte ({len(trend_prices)} points)")
        continue
    
    # Régression linéaire
    x = np.arange(len(trend_prices))
    coeffs = np.polyfit(x, trend_prices, 1)
    trend_line = np.polyval(coeffs, x)
    
    # R² (coefficient de détermination)
    ss_res = np.sum((trend_prices - trend_line) ** 2)
    ss_tot = np.sum((trend_prices - np.mean(trend_prices)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Amplitude (pips)
    amplitude_pips = (np.max(trend_prices) - np.min(trend_prices)) * 10000
    
    # Durée RÉELLE (heures)
    duration_hours = len(trend_prices) / 60  # minutes → heures
    
    print(f"   R² : {r_squared:.3f}")
    print(f"   Amplitude : {amplitude_pips:.1f} pips")
    print(f"   Durée : {duration_hours:.1f}h ({len(trend_prices)} min)")
    
    # Ajouter aux résultats
    result = row.to_dict()
    result['r_squared'] = r_squared
    result['amplitude_pips'] = amplitude_pips
    result['duration_hours'] = duration_hours
    result['num_extrema'] = len(extrema)
    result['trend_length_min'] = len(trend_prices)
    
    results.append(result)

conn.close()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_results = pd.DataFrame(results)
output_path = data_dir / "step4_avec_tendances_NEW.csv"
df_results.to_csv(output_path, index=False)

print(f"\n{'='*80}")
print(f"✅ ÉTAPE 4 TERMINÉE : {len(results)} cas traités")
print(f"✅ Sauvegardé : {output_path.name}")
print(f"{'='*80}")
print()

print("📊 STATISTIQUES TENDANCES :")
print(f"   R² moyen : {df_results['r_squared'].mean():.3f}")
print(f"   Amplitude moyenne : {df_results['amplitude_pips'].mean():.1f} pips")
print(f"   Durée moyenne : {df_results['duration_hours'].mean():.1f}h")
print()
print("➡️  PROCHAINE ÉTAPE : python3 step5_tester_strategies_NEW.py")
