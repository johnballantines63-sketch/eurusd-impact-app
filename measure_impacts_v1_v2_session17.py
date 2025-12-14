"""
SESSION 17 - MESURE IMPACTS V1 vs V2
Compare les deux formules d'amplification sur 120 groupes
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 80)
print("📊 SESSION 17 - MESURE IMPACTS V1 vs V2")
print("=" * 80)
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Charger les données
# ════════════════════════════════════════════════════════════════

print("📂 Chargement des groupes extraits...")

data_file = Path(__file__).parent / "extracted_groups_session17.csv"
df = pd.read_csv(data_file)

print(f"   ✅ {len(df)} groupes chargés")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Définir les formules
# ════════════════════════════════════════════════════════════════

def calculate_base_impact(empirical_score):
    """
    Formule v9-CLEAN (Session 9)
    Formule de base sans amplification
    """
    return -7.08 + 0.419 * empirical_score


def calculate_amplification_v1(surprise_pct):
    """
    Formule V1 (Session 14)
    Amplification agressive avec plafond élevé
    """
    surprise_abs = abs(surprise_pct)
    
    if surprise_abs < 5.0:
        return 1.0
    elif surprise_abs < 10.0:
        # Zone linéaire 5-10% : ×1.0 → ×3.0
        return 1.0 + (surprise_abs - 5.0) * 0.4
    else:
        # Zone logarithmique >10% : ×3.0 → ×10+
        return 3.0 + np.log1p(surprise_abs - 10.0) * 2.0


def calculate_amplification_v2(surprise_pct, empirical_score):
    """
    Formule V2 (Session 15)
    Amplification modérée avec plafonds
    """
    surprise_abs = abs(surprise_pct)
    
    # Plafond surprise à 30%
    if surprise_abs > 30:
        surprise_abs = 30.0
    
    # Filtrage : score < 40 = pas d'amplification
    if empirical_score < 40:
        return 1.0
    
    # Zone 1 (0-5%) : Pas d'amplification
    if surprise_abs < 5.0:
        return 1.0
    
    # Zone 2 (5-15%) : Amplification linéaire modérée
    elif surprise_abs < 15.0:
        return 1.0 + (surprise_abs - 5.0) * 0.15
    
    # Zone 3 (>15%) : Plafond à ×2.5
    else:
        return 2.5


# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Calculer les impacts
# ════════════════════════════════════════════════════════════════

print("🔧 Calcul des impacts prédits...")
print()

# Facteur de calibration MT5 (Session 14)
CALIBRATION_FACTOR = 0.758

# Impact de base (sans amplification)
df['impact_base'] = df['max_empirical_score'].apply(calculate_base_impact)

# V1 : Amplification Session 14
df['amplification_v1'] = df['surprise_pct'].apply(calculate_amplification_v1)
df['impact_v1_brut'] = abs(df['impact_base']) * df['amplification_v1']
df['impact_v1_final'] = df['impact_v1_brut'] * CALIBRATION_FACTOR

# V2 : Amplification Session 15
df['amplification_v2'] = df.apply(
    lambda row: calculate_amplification_v2(row['surprise_pct'], row['max_empirical_score']),
    axis=1
)
df['impact_v2_brut'] = abs(df['impact_base']) * df['amplification_v2']
df['impact_v2_final'] = df['impact_v2_brut'] * CALIBRATION_FACTOR

# Impact réel
df['impact_reel'] = df['impact_reel_pips']

print("   ✅ Impacts calculés pour 120 groupes")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Calculer les erreurs
# ════════════════════════════════════════════════════════════════

print("📊 Calcul des métriques d'erreur...")
print()

# Erreurs absolues
df['erreur_v1'] = abs(df['impact_v1_final'] - df['impact_reel'])
df['erreur_v2'] = abs(df['impact_v2_final'] - df['impact_reel'])

# Erreurs en pourcentage
df['erreur_pct_v1'] = (df['erreur_v1'] / df['impact_reel']) * 100
df['erreur_pct_v2'] = (df['erreur_v2'] / df['impact_reel']) * 100

# Amélioration (positif = V2 meilleure)
df['amelioration_pct'] = df['erreur_pct_v1'] - df['erreur_pct_v2']

print("   ✅ Métriques calculées")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Résultats globaux
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📈 RÉSULTATS GLOBAUX (120 GROUPES)")
print("=" * 80)
print()

# MAE (Mean Absolute Error)
mae_v1 = df['erreur_pct_v1'].mean()
mae_v2 = df['erreur_pct_v2'].mean()
reduction_mae = ((mae_v1 - mae_v2) / mae_v1) * 100

print("🎯 MEAN ABSOLUTE ERROR (MAE) :")
print(f"   V1 (Session 14) : {mae_v1:.1f}%")
print(f"   V2 (Session 15) : {mae_v2:.1f}%")
print(f"   Réduction MAE   : {reduction_mae:+.1f}%")
print()

# Amélioration moyenne
amelioration_moy = df['amelioration_pct'].mean()
print(f"🔄 AMÉLIORATION MOYENNE : {amelioration_moy:+.1f} points")
print()

# Distribution des résultats
v2_meilleure = (df['amelioration_pct'] > 0).sum()
v2_pire = (df['amelioration_pct'] < 0).sum()
v2_neutre = (df['amelioration_pct'] == 0).sum()

print("📊 DISTRIBUTION :")
print(f"   V2 meilleure : {v2_meilleure} / 120 ({v2_meilleure/120*100:.1f}%)")
print(f"   V2 pire      : {v2_pire} / 120 ({v2_pire/120*100:.1f}%)")
print(f"   Neutre       : {v2_neutre} / 120 ({v2_neutre/120*100:.1f}%)")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 6 : Résultats par tranche de surprise
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 RÉSULTATS PAR TRANCHE DE SURPRISE")
print("=" * 80)
print()

df['surprise_range'] = pd.cut(
    df['surprise_pct'],
    bins=[0, 5, 10, 20, 50],
    labels=['0-5%', '5-10%', '10-20%', '20-50%']
)

for tranche in ['0-5%', '5-10%', '10-20%', '20-50%']:
    subset = df[df['surprise_range'] == tranche]
    if len(subset) == 0:
        continue
    
    mae_v1_tranche = subset['erreur_pct_v1'].mean()
    mae_v2_tranche = subset['erreur_pct_v2'].mean()
    amelioration_tranche = subset['amelioration_pct'].mean()
    
    print(f"📌 TRANCHE {tranche} ({len(subset)} groupes)")
    print(f"   MAE V1 : {mae_v1_tranche:.1f}%")
    print(f"   MAE V2 : {mae_v2_tranche:.1f}%")
    print(f"   Gain   : {amelioration_tranche:+.1f} points")
    print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 7 : Top améliorations et régressions
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("🏆 TOP 5 AMÉLIORATIONS (V2 beaucoup mieux que V1)")
print("=" * 80)
print()

top_ameliorations = df.nlargest(5, 'amelioration_pct')
for idx, row in top_ameliorations.iterrows():
    print(f"📈 {row['event_titles'][:60]}")
    print(f"   Pays : {row['countries']}, Surprise : {row['surprise_pct']:.1f}%")
    print(f"   Impact réel : {row['impact_reel']:.1f} pips")
    print(f"   V1 : {row['impact_v1_final']:.1f} pips (erreur {row['erreur_pct_v1']:.0f}%)")
    print(f"   V2 : {row['impact_v2_final']:.1f} pips (erreur {row['erreur_pct_v2']:.0f}%)")
    print(f"   Gain : {row['amelioration_pct']:+.0f} points")
    print()

print("=" * 80)
print("⚠️ TOP 5 RÉGRESSIONS (V2 moins bonne que V1)")
print("=" * 80)
print()

top_regressions = df.nsmallest(5, 'amelioration_pct')
for idx, row in top_regressions.iterrows():
    print(f"📉 {row['event_titles'][:60]}")
    print(f"   Pays : {row['countries']}, Surprise : {row['surprise_pct']:.1f}%")
    print(f"   Impact réel : {row['impact_reel']:.1f} pips")
    print(f"   V1 : {row['impact_v1_final']:.1f} pips (erreur {row['erreur_pct_v1']:.0f}%)")
    print(f"   V2 : {row['impact_v2_final']:.1f} pips (erreur {row['erreur_pct_v2']:.0f}%)")
    print(f"   Perte : {row['amelioration_pct']:+.0f} points")
    print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 8 : Sauvegarder les résultats
# ════════════════════════════════════════════════════════════════

output_file = Path(__file__).parent / "impacts_comparison_session17.csv"
df.to_csv(output_file, index=False)

print("=" * 80)
print("💾 RÉSULTATS SAUVEGARDÉS")
print("=" * 80)
print()
print(f"📁 Fichier : {output_file.name}")
print(f"📊 Colonnes : {len(df.columns)}")
print()

print("=" * 80)
print("🎯 PROCHAINE ÉTAPE : Analyse multidimensionnelle")
print("=" * 80)
print()
print("Analyses à réaliser :")
print("  • Par pays (US, EU, GB, IT, DE, etc.)")
print("  • Par type d'événement (GDP, CPI, Employment, etc.)")
print("  • Par année (2024 vs 2025)")
print("  • Par nombre d'événements dans le groupe")
