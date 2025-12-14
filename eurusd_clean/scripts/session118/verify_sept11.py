"""
Script de vérification 11 septembre 2025
Récupérer les VRAIS prix MT5 pour valider les données
"""
import duckdb
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent.parent.parent
warehouse_path = project_root / 'data' / 'warehouse.duckdb'

conn = duckdb.connect(str(warehouse_path), read_only=True)

print("=" * 80)
print("🔍 VÉRIFICATION 11 SEPTEMBRE 2025 - PRIX MT5")
print("=" * 80)

# Récupérer prix autour de 14:20 - 15:30 (fenêtre du pattern)
query = """
    SELECT 
        datetime as time,
        open,
        high,
        low,
        close
    FROM prices_bern
    WHERE datetime >= '2025-09-11 14:00:00'
      AND datetime <= '2025-09-11 15:30:00'
    ORDER BY datetime
"""

df = conn.execute(query).df()

print(f"\n📊 Prix EUR/USD 11 septembre 2025 (14:00-15:30)")
print(f"   Lignes: {len(df)}")
print()

if not df.empty:
    # Chercher baseline (autour 14:21)
    baseline_window = df[(df['time'] >= '2025-09-11 14:20:00') & 
                         (df['time'] <= '2025-09-11 14:25:00')]
    
    print("🔹 BASELINE (14:20-14:25):")
    if not baseline_window.empty:
        baseline_low = baseline_window['low'].min()
        baseline_time = baseline_window.loc[baseline_window['low'].idxmin(), 'time']
        print(f"   Prix: {baseline_low:.5f}")
        print(f"   Time: {baseline_time}")
    
    # Chercher Peak1 (autour 14:32)
    peak1_window = df[(df['time'] >= '2025-09-11 14:30:00') & 
                      (df['time'] <= '2025-09-11 14:35:00')]
    
    print("\n🔹 PEAK 1 (14:30-14:35):")
    if not peak1_window.empty:
        peak1_high = peak1_window['high'].max()
        peak1_time = peak1_window.loc[peak1_window['high'].idxmax(), 'time']
        print(f"   Prix: {peak1_high:.5f}")
        print(f"   Time: {peak1_time}")
    
    # Chercher Pullback (autour 14:51)
    pullback_window = df[(df['time'] >= '2025-09-11 14:45:00') & 
                         (df['time'] <= '2025-09-11 14:55:00')]
    
    print("\n🔹 PULLBACK (14:45-14:55):")
    if not pullback_window.empty:
        pullback_low = pullback_window['low'].min()
        pullback_time = pullback_window.loc[pullback_window['low'].idxmin(), 'time']
        print(f"   Prix: {pullback_low:.5f}")
        print(f"   Time: {pullback_time}")
    
    # Chercher Wave2 Peak (autour 15:09)
    wave2_window = df[(df['time'] >= '2025-09-11 15:00:00') & 
                      (df['time'] <= '2025-09-11 15:15:00')]
    
    print("\n🔹 WAVE2 PEAK (15:00-15:15):")
    if not wave2_window.empty:
        wave2_high = wave2_window['high'].max()
        wave2_time = wave2_window.loc[wave2_window['high'].idxmax(), 'time']
        print(f"   Prix: {wave2_high:.5f}")
        print(f"   Time: {wave2_time}")
    
    # CALCUL IMPACT TOTAL
    if not baseline_window.empty and not wave2_window.empty:
        impact_pips = (wave2_high - baseline_low) * 10000
        print(f"\n📊 IMPACT TOTAL:")
        print(f"   Baseline → Wave2: {impact_pips:.2f} pips")
        print(f"   Référence Session 115: 56.2 pips")
        print(f"   Différence: {abs(impact_pips - 56.2):.2f} pips")
        
        if abs(impact_pips - 56.2) < 1:
            print(f"   ✅ COHÉRENT avec Session 115")
        else:
            print(f"   ⚠️ INCOHÉRENT avec Session 115")

# Afficher aussi les données du JSON pour comparaison
print("\n" + "=" * 80)
print("📋 COMPARAISON AVEC JSON")
print("=" * 80)

import json
json_path = project_root / 'scripts' / 'session117' / 'double_waves_enriched.json'
with open(json_path, 'r') as f:
    double_waves = json.load(f)

# Trouver le 11 septembre
sept_11 = None
for dw in double_waves:
    if '2025-09-11' in dw['baseline_time']:
        sept_11 = dw
        break

if sept_11:
    print(f"\n🔹 DONNÉES JSON (11 septembre):")
    print(f"   baseline_price:    {sept_11['baseline_price']:.5f}")
    print(f"   baseline_time:     {sept_11['baseline_time']}")
    print(f"   peak1_price:       {sept_11['peak1_price']:.5f}")
    print(f"   peak1_time:        {sept_11['peak1_time']}")
    print(f"   pullback_price:    {sept_11['pullback_price']:.5f}")
    print(f"   pullback_time:     {sept_11['pullback_time']}")
    print(f"   wave2_peak_price:  {sept_11['wave2_peak_price']:.5f}")
    print(f"   wave2_peak_time:   {sept_11['wave2_peak_time']}")
    print(f"   total_impact_pips: {sept_11['total_impact_pips']:.2f} pips")

conn.close()
