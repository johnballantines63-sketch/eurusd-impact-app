"""
Vérification 11 septembre - AVEC BON BASELINE (14:30)
"""
import duckdb
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
warehouse_path = project_root / 'data' / 'warehouse.duckdb'

conn = duckdb.connect(str(warehouse_path), read_only=True)

print("=" * 80)
print("🔍 11 SEPTEMBRE - CALCUL CORRECT AVEC BASELINE À 14:30")
print("=" * 80)

# Prix minute par minute autour de 14:30 et 15:09
query = """
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_bern
    WHERE datetime >= '2025-09-11 14:28:00'
      AND datetime <= '2025-09-11 15:12:00'
    ORDER BY datetime
"""

df = conn.execute(query).df()

print(f"\n📊 Prix autour des moments clés:")
print()

# Trouver prix à 14:30 (BASELINE = moment du cluster 1)
baseline_row = df[df['datetime'] == '2025-09-11 14:30:00+02:00']
if not baseline_row.empty:
    # Utiliser le CLOSE de la bougie AVANT l'event (14:29) ou OPEN de 14:30
    baseline_prev = df[df['datetime'] == '2025-09-11 14:29:00+02:00']
    if not baseline_prev.empty:
        baseline_price = baseline_prev['close'].values[0]
        print(f"🔹 BASELINE (14:29 close, juste avant events 14:30):")
        print(f"   Prix: {baseline_price:.5f}")
    else:
        baseline_price = baseline_row['open'].values[0]
        print(f"🔹 BASELINE (14:30 open):")
        print(f"   Prix: {baseline_price:.5f}")
else:
    print("❌ Pas de prix à 14:30")
    baseline_price = None

# Peak1 (14:32)
peak1_rows = df[(df['datetime'] >= '2025-09-11 14:30:00+02:00') & 
                (df['datetime'] <= '2025-09-11 14:35:00+02:00')]
if not peak1_rows.empty:
    peak1_price = peak1_rows['high'].max()
    peak1_time = peak1_rows.loc[peak1_rows['high'].idxmax(), 'datetime']
    print(f"\n🔹 PEAK 1 (réaction cluster 1):")
    print(f"   Prix: {peak1_price:.5f}")
    print(f"   Time: {peak1_time}")

# Wave2 Peak (15:09)
wave2_rows = df[(df['datetime'] >= '2025-09-11 15:05:00+02:00') & 
                (df['datetime'] <= '2025-09-11 15:12:00+02:00')]
if not wave2_rows.empty:
    wave2_price = wave2_rows['high'].max()
    wave2_time = wave2_rows.loc[wave2_rows['high'].idxmax(), 'datetime']
    print(f"\n🔹 WAVE2 PEAK (pic final):")
    print(f"   Prix: {wave2_price:.5f}")
    print(f"   Time: {wave2_time}")

# CALCUL IMPACT CORRECT
if baseline_price and not wave2_rows.empty:
    impact_correct = (wave2_price - baseline_price) * 10000
    
    print(f"\n" + "=" * 80)
    print(f"📊 IMPACT TOTAL CORRECT:")
    print(f"=" * 80)
    print(f"   Baseline (14:29 close): {baseline_price:.5f}")
    print(f"   Wave2 Peak (15:09):     {wave2_price:.5f}")
    print(f"   Impact:                 {impact_correct:.2f} pips")
    print()
    print(f"   Référence Session 115:  56.2 pips")
    print(f"   Différence:             {abs(impact_correct - 56.2):.2f} pips")
    
    if abs(impact_correct - 56.2) < 2:
        print(f"   ✅ COHÉRENT avec Session 115 !")
    else:
        print(f"   ⚠️ Écart de {abs(impact_correct - 56.2):.2f} pips")

# Afficher aussi le calcul du JSON (FAUX)
print(f"\n" + "=" * 80)
print(f"❌ CALCUL INCORRECT DU JSON (pour comparaison):")
print(f"=" * 80)
import json
json_path = project_root / 'scripts' / 'session117' / 'double_waves_enriched.json'
with open(json_path, 'r') as f:
    double_waves = json.load(f)

sept_11 = [dw for dw in double_waves if '2025-09-11' in dw['baseline_time']][0]
print(f"   Baseline JSON (14:21):  {sept_11['baseline_price']:.5f}")
print(f"   Wave2 Peak (15:09):     {sept_11['wave2_peak_price']:.5f}")
print(f"   Impact JSON:            {sept_11['total_impact_pips']:.2f} pips")
print(f"   Erreur: Baseline pris 9 min AVANT les events !")

conn.close()
