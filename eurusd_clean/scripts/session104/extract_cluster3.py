#!/usr/bin/env python3
"""
EXTRACTION CLUSTER #3 - 6 DATES CPI MENSUEL
============================================
Préparation Phase 1 validation
"""
import pandas as pd
from pathlib import Path

# Charger dataset complet
data_file = Path(__file__).parent / "dataset_44_dates_METHOD_SESSION92_5.csv"
df = pd.read_csv(data_file)

# Les 6 dates du Cluster #3 (CPI mensuel - 11 événements)
cluster3_dates = [
    '2025-09-11',  # Référence (56.8 pips validé Session 103)
    '2025-08-12',
    '2025-07-15',
    '2025-06-11',
    '2025-05-13',
    '2025-04-10'
]

# Filtrer
df_cluster3 = df[df['date'].isin(cluster3_dates)].copy()

# Trier par date décroissante
df_cluster3 = df_cluster3.sort_values('date', ascending=False)

# Sauvegarder
output_file = Path(__file__).parent / "cluster3_cpi_6dates.csv"
df_cluster3.to_csv(output_file, index=False)

print("="*80)
print("CLUSTER #3 - 6 DATES CPI MENSUEL")
print("="*80)
print()
print(f"✅ {len(df_cluster3)} dates extraites")
print()
print("Dates :")
for idx, row in df_cluster3.iterrows():
    marker = "🎯" if row['date'] == '2025-09-11' else "  "
    print(f"  {marker} {row['date']} : {row['num_events']:2d} events | {row['impact_real_pips']:5.1f} pips")
print()
print(f"📁 {output_file.name}")
print()
print("⚠️  ATTENTION : impact_real_pips actuel est FAUX (11.09 = 12.7 au lieu de 56.8)")
print("    Session 105 doit CORRIGER la mesure avant utiliser ces valeurs")
