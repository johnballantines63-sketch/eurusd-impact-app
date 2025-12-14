#!/usr/bin/env python3
"""
ÉTAPE 3 : CALCULER AMPLIFICATIONS PARFAITES
============================================

Pour chaque date :
1. Lire impact_predit (step1) et impact_real (step2)
2. Calculer amp_parfaite = (impact_real / impact_predit) × 2.5
   → Quel facteur d'amplification aurait donné le résultat parfait ?

ENTRÉES : step1_impacts_predits_NEW.csv + step2_impacts_reels_NEW.csv
SORTIE  : step3_amplifications_parfaites_NEW.csv
"""

from pathlib import Path
import pandas as pd

print("=" * 80)
print("ÉTAPE 3 : CALCULER AMPLIFICATIONS PARFAITES")
print("=" * 80)
print()

# ============================================================================
# CHARGER RÉSULTATS STEPS 1 & 2
# ============================================================================

data_dir = Path(__file__).parent / "data"

step1_path = data_dir / "step1_impacts_predits_NEW.csv"
step2_path = data_dir / "step2_impacts_reels_NEW.csv"

if not step1_path.exists():
    print(f"❌ Fichier manquant : {step1_path.name}")
    print(f"   → Exécuter d'abord : python3 step1_calculer_impacts_NEW.py")
    exit(1)

if not step2_path.exists():
    print(f"❌ Fichier manquant : {step2_path.name}")
    print(f"   → Exécuter d'abord : python3 step2_mesurer_reels_NEW.py")
    exit(1)

df_step1 = pd.read_csv(step1_path)
df_step2 = pd.read_csv(step2_path)

print(f"✅ Step1 : {len(df_step1)} cas")
print(f"✅ Step2 : {len(df_step2)} cas")
print()

# ============================================================================
# MERGER ET CALCULER AMP_PARFAITE
# ============================================================================

# Merger sur event_date
df_merged = pd.merge(
    df_step1,
    df_step2,
    on='event_date',
    how='inner'
)

print(f"✅ {len(df_merged)} cas avec impacts predit ET reel")
print()

# Calculer amplification parfaite
# Formule : amp_parfaite = (impact_real / impact_predit) × 2.5
df_merged['amp_parfaite'] = (df_merged['impact_real'] / df_merged['impact_predit']) * 2.5

# Calculer erreur baseline
df_merged['erreur_baseline'] = abs(df_merged['impact_real'] - df_merged['impact_predit'])

print("=" * 80)
print("AMPLIFICATIONS PARFAITES CALCULÉES")
print("=" * 80)
print()

# Afficher quelques cas
for idx in range(min(5, len(df_merged))):
    row = df_merged.iloc[idx]
    print(f"{row['event_date']} :")
    print(f"   Impact prédit : {row['impact_predit']:6.1f} pips (amp=2.5)")
    print(f"   Impact réel   : {row['impact_real']:6.1f} pips")
    print(f"   Amp parfaite  : {row['amp_parfaite']:6.3f} (facteur idéal)")
    print(f"   Erreur base   : {row['erreur_baseline']:6.1f} pips")
    print()

# ============================================================================
# STATISTIQUES
# ============================================================================

print("=" * 80)
print("STATISTIQUES AMPLIFICATIONS PARFAITES")
print("=" * 80)
print()

print(f"Moyenne   : {df_merged['amp_parfaite'].mean():.3f}")
print(f"Médiane   : {df_merged['amp_parfaite'].median():.3f}")
print(f"Std       : {df_merged['amp_parfaite'].std():.3f}")
print(f"Min       : {df_merged['amp_parfaite'].min():.3f}")
print(f"Max       : {df_merged['amp_parfaite'].max():.3f}")
print()

# Distribution
print("Distribution :")
for quantile in [0.25, 0.5, 0.75]:
    val = df_merged['amp_parfaite'].quantile(quantile)
    print(f"   Q{int(quantile*100):2d} : {val:.3f}")
print()

# Combien au-dessus/en-dessous baseline 2.5
above = (df_merged['amp_parfaite'] > 2.5).sum()
below = (df_merged['amp_parfaite'] < 2.5).sum()
equal = (df_merged['amp_parfaite'] == 2.5).sum()

print(f"Par rapport à baseline (2.5) :")
print(f"   Au-dessus : {above} cas ({above/len(df_merged)*100:.0f}%)")
print(f"   En-dessous : {below} cas ({below/len(df_merged)*100:.0f}%)")
print(f"   Égal      : {equal} cas")
print()

# ============================================================================
# SAUVEGARDER
# ============================================================================

output_path = data_dir / "step3_amplifications_parfaites_NEW.csv"
df_merged.to_csv(output_path, index=False)

print("=" * 80)
print(f"✅ ÉTAPE 3 TERMINÉE : {len(df_merged)} cas traités")
print(f"✅ Sauvegardé : {output_path.name}")
print("=" * 80)
print()
print("➡️  PROCHAINE ÉTAPE : python3 step4_detecter_tendances_NEW.py")
