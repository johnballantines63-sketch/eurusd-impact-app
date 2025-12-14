"""
Script diagnostic : Analyser problèmes détectés dans step1_price_movements.csv
"""
import pandas as pd
from pathlib import Path

csv_path = Path(__file__).parent / "step1_price_movements.csv"
df = pd.read_csv(csv_path)

print("="*80)
print("ANALYSE PROBLÈMES STEP1")
print("="*80)

# Problème 1 : minutes_to_peak ≤ 0
print("\n1️⃣ PROBLÈME : minutes_to_peak ≤ 0")
df_neg = df[df['minutes_to_peak'] <= 0]
print(f"   Nombre cas : {len(df_neg)}")
if len(df_neg) > 0:
    print("\n   Échantillon (5 premiers) :")
    for idx, row in df_neg.head().iterrows():
        print(f"   - {row['datetime']} : minutes_to_peak = {row['minutes_to_peak']}")
else:
    print("   ✅ Aucun cas trouvé !")

# Problème 2 : peak > 60 min
print("\n2️⃣ PROBLÈME : peak > 60 min")
df_over60 = df[df['minutes_to_peak'] > 60]
print(f"   Nombre cas : {len(df_over60)}")
if len(df_over60) > 0:
    print("\n   Échantillon (5 premiers) :")
    for idx, row in df_over60.head().iterrows():
        print(f"   - {row['datetime']} : minutes_to_peak = {row['minutes_to_peak']:.1f} min")

# Statistiques générales
print("\n3️⃣ STATISTIQUES minutes_to_peak")
print(f"   Min : {df['minutes_to_peak'].min():.1f} min")
print(f"   Max : {df['minutes_to_peak'].max():.1f} min")
print(f"   Moyenne : {df['minutes_to_peak'].mean():.1f} min")
print(f"   Médiane : {df['minutes_to_peak'].median():.1f} min")
