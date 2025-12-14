"""
Analyse diagnostic : Pourquoi formules 92.xx échouent vs Session 92-93
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

# Charger résultats hybrides
df_hybrid = pd.read_csv(BASE_DIR / "scripts/session98/validation_hybrid_s51_55_92xx.csv")

print("=" * 80)
print("🔍 DIAGNOSTIC ÉCHEC FORMULES 92.XX")
print("=" * 80)

# Analyser clusters trouvés vs fallback
print("\n📊 CLUSTERS RECONNUS vs FALLBACK:")
print(f"Total dates: {len(df_hybrid)}")

clusters_found = df_hybrid[df_hybrid['cluster_found'] == True]
clusters_fallback = df_hybrid[df_hybrid['cluster_found'] == False]

print(f"Clusters reconnus ✅: {len(clusters_found)}/{len(df_hybrid)} ({len(clusters_found)/len(df_hybrid)*100:.1f}%)")
print(f"Fallback utilisé ⚠️: {len(clusters_fallback)}/{len(df_hybrid)} ({len(clusters_fallback)/len(df_hybrid)*100:.1f}%)")

# Distribution nombre d'événements
print("\n📊 DISTRIBUTION NOMBRE ÉVÉNEMENTS:")
event_counts = df_hybrid['num_events'].value_counts().sort_index()
for count, freq in event_counts.items():
    found = df_hybrid[(df_hybrid['num_events'] == count) & (df_hybrid['cluster_found'] == True)]
    print(f"   {count} events: {freq} dates ({len(found)} reconnus)")

# Clusters définis dans formulas_hybrid_empirical.py
print("\n🎯 CLUSTERS DÉFINIS (Session 92):")
clusters_defined = [
    ('CONSTRUCTION', 6),
    ('NFP', 12),
    ('CPI', 9),
    ('CPI', 11),
    ('FOMC', 12)
]
for cluster_type, cluster_size in clusters_defined:
    print(f"   {cluster_type}-{cluster_size}")

# Clusters dans nos 23 dates
print("\n📊 CLUSTERS DANS NOS 23 DATES:")
for idx, row in df_hybrid.iterrows():
    cluster_str = f"{row['cluster_type']}-{row['num_events']}"
    found_str = "✅" if row['cluster_found'] else "⚠️ fallback"
    print(f"   Date {idx+1}: {cluster_str} {found_str} | Impact prédit: {row['impact_hybrid']:.1f} pips")

# Performance par type
print("\n📈 PERFORMANCE PAR TYPE:")
print(f"\n✅ CLUSTERS RECONNUS ({len(clusters_found)} dates):")
if len(clusters_found) > 0:
    mae_found = clusters_found['error_hybrid'].mean()
    print(f"   MAE: {mae_found:.2f} pips")
    for idx, row in clusters_found.iterrows():
        print(f"   {row['date']}: {row['cluster_type']}-{row['num_events']} | Erreur: {row['error_hybrid']:.2f} pips")

print(f"\n⚠️ FALLBACK ({len(clusters_fallback)} dates):")
if len(clusters_fallback) > 0:
    mae_fallback = clusters_fallback['error_hybrid'].mean()
    print(f"   MAE: {mae_fallback:.2f} pips")

# Comparaison impacts prédits
print("\n📊 DISTRIBUTION IMPACTS PRÉDITS HYBRIDE:")
bins = [0, 10, 15, 20, 30, 50, 100]
df_hybrid['impact_bin'] = pd.cut(df_hybrid['impact_hybrid'], bins=bins)
dist = df_hybrid['impact_bin'].value_counts().sort_index()
for bin_label, count in dist.items():
    print(f"   {bin_label}: {count} dates")

print("\n" + "=" * 80)
print("💡 CONCLUSION")
print("=" * 80)

pct_fallback = len(clusters_fallback) / len(df_hybrid) * 100
print(f"""
PROBLÈME IDENTIFIÉ:

1. {pct_fallback:.0f}% des dates utilisent FALLBACK (DEFAULT_PARAMS)
   → base_impact = 15.0 pips (trop faible)
   → sensitivity = 0.01

2. Formules 92.xx calibrées sur configurations SPÉCIFIQUES:
   - CPI-9 events (16 occurrences Session 92)
   - CPI-11 events (8 occurrences Session 92)
   - NFP-12 events (19 occurrences Session 92)
   
3. Nos 23 dates ont configurations DIFFÉRENTES:
   - CPI-5, CPI-8, CPI-12, CPI-13, CPI-14, CPI-15, CPI-16, CPI-17...
   → Ne matchent PAS les clusters calibrés exactement

4. Session 92-93 avait MAE 6.5 pips car:
   → Les 12 dates testées correspondaient AUX clusters calibrés
   → OVERFITTING sur configurations spécifiques

SOLUTIONS POSSIBLES:
A. Recalibrer formules 92.xx sur nos 23 dates
B. Assouplir matching clusters (tolérance ±1-2 events)
C. Accepter que baseline S51-55 est plus robuste
""")
