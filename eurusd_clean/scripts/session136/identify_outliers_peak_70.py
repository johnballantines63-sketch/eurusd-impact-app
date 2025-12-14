"""
Identifier les 8 mouvements avec peak > 70 min
"""
import pandas as pd
from pathlib import Path

csv_path = Path(__file__).parent / "step1_price_movements.csv"
df = pd.read_csv(csv_path)

# Filtrer mouvements avec peak > 70 min
df['minutes_to_peak'] = pd.to_numeric(df['minutes_to_peak'])
df_outliers = df[df['minutes_to_peak'] > 70].sort_values('minutes_to_peak', ascending=False)

print("="*80)
print("8 MOUVEMENTS AVEC PEAK > 70 MIN")
print("="*80)

print(f"\nTotal trouvés : {len(df_outliers)}")

for idx, row in df_outliers.iterrows():
    print(f"\n{idx+1}. {row['datetime']}")
    print(f"   Impact : {row['impact_pips']:.1f} pips")
    print(f"   Direction : {row['direction']}")
    print(f"   Peak time : {row['peak_time']}")
    print(f"   Minutes to peak : {row['minutes_to_peak']:.1f} min ⚠️")
    print(f"   Baseline : {row['baseline_price']:.5f}")
    print(f"   Peak : {row['peak_price']:.5f}")
