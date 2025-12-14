#!/usr/bin/env python3
"""Affiche les résultats du test d'intégration"""

import pandas as pd
from pathlib import Path

csv_file = Path(__file__).parent / 'outputs' / 'direction_router_test' / 'test_integration_first_leg.csv'

if not csv_file.exists():
    print(f"❌ Fichier non trouvé : {csv_file}")
    exit(1)

df = pd.read_csv(csv_file)

print("=" * 80)
print("RÉSULTATS TEST INTÉGRATION FIRST-LEG")
print("=" * 80)
print()

print("📊 Répartition patterns :")
print(df['pattern_type'].value_counts())
print()

# Filtrer double_wave et zig_zag
multi_wave = df[df['pattern_type'].isin(['double_wave', 'zig_zag'])]

if len(multi_wave) > 0:
    print(f"✅ {len(multi_wave)} cas multi-wave détectés")
    print()
    print("=" * 80)
    print("EXEMPLES MULTI-WAVE (10 premiers)")
    print("=" * 80)
    print()
    
    for idx, row in multi_wave.head(10).iterrows():
        print(f"📅 {row['date']} ({row['cluster_type']})")
        print(f"   Direction first-leg : {row['direction_first_leg']}")
        print(f"   Impact total : {row['impact_pips']:.1f} pips")
        print(f"   Pattern : {row['pattern_type']}")
        print(f"   Strength : {row['trigger_strength']:.2f}")
        if pd.notna(row['leg1_amp_pips']):
            print(f"   Jambe 1 : {row['leg1_direction']} {row['leg1_amp_pips']:.1f} pips (peak T+{row['leg1_t_peak_min']}min)")
            print(f"   Jambe 2 : {row['leg2_direction']} {row['leg2_amp_pips']:.1f} pips (peak T+{row['leg2_t_peak_min']}min)")
        print()
else:
    print("⚠️  Aucun cas multi-wave détecté")
    print("   (Peut-être que le seuil de détection est trop élevé)")

