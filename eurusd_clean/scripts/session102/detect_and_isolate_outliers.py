#!/usr/bin/env python3
"""
DÉTECTION & ISOLATION OUTLIERS - MÉTHODOLOGIE RIGOUREUSE
=========================================================

Phase 1 : Détection statistique outliers
Phase 2 : Liste outliers pour examen contexte externe
Phase 3 : Test hypothèse sur données PROPRES (sans outliers)
Phase 4 : Analyse séparée outliers

Objectif : Ne pas biaiser analyse avec événements exceptionnels
           causés par facteurs externes (Trump, guerre, etc.)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr

print("=" * 80)
print("DÉTECTION & ISOLATION OUTLIERS - ANALYSE RIGOUREUSE")
print("=" * 80)

# Charger données propres (déjà sans doublons)
project_root = Path(__file__).resolve().parents[3]
csv_path = project_root / "eurusd_clean" / "scripts" / "session102" / "analysis_real_data_CLEAN.csv"

df = pd.read_csv(csv_path)
df_valid = df.dropna(subset=['amp_parfaite', 'trend_r2_optimized']).copy()

print(f"\n✅ Chargé {len(df_valid)} événements valides")

# ============================================================================
# PHASE 1 : DÉTECTION STATISTIQUE OUTLIERS
# ============================================================================

print(f"\n{'='*80}")
print("PHASE 1 : DÉTECTION STATISTIQUE OUTLIERS")
print(f"{'='*80}")

amp_values = df_valid['amp_parfaite'].values

# Méthode IQR (Inter-Quartile Range) - Standard en statistique
Q1 = np.percentile(amp_values, 25)
Q3 = np.percentile(amp_values, 75)
IQR = Q3 - Q1

# Seuils outliers (1.5×IQR est standard, mais on peut ajuster)
outlier_low = Q1 - 1.5 * IQR
outlier_high = Q3 + 1.5 * IQR

print(f"\n📊 Statistiques amp_parfaite :")
print(f"   Q1 (25%)         : {Q1:.3f}")
print(f"   Médiane (50%)    : {np.median(amp_values):.3f}")
print(f"   Q3 (75%)         : {Q3:.3f}")
print(f"   IQR              : {IQR:.3f}")
print(f"\n   Seuils outliers (méthode IQR 1.5×) :")
print(f"   Bas  (< Q1-1.5×IQR) : {outlier_low:.3f}")
print(f"   Haut (> Q3+1.5×IQR) : {outlier_high:.3f}")

# Identifier outliers
df_valid['is_outlier_low'] = df_valid['amp_parfaite'] < outlier_low
df_valid['is_outlier_high'] = df_valid['amp_parfaite'] > outlier_high
df_valid['is_outlier'] = df_valid['is_outlier_low'] | df_valid['is_outlier_high']

n_outliers = df_valid['is_outlier'].sum()
n_clean = len(df_valid) - n_outliers

print(f"\n✅ Détection terminée :")
print(f"   Événements normaux  : {n_clean} ({n_clean/len(df_valid)*100:.1f}%)")
print(f"   Outliers détectés   : {n_outliers} ({n_outliers/len(df_valid)*100:.1f}%)")
print(f"   - Outliers BAS      : {df_valid['is_outlier_low'].sum()}")
print(f"   - Outliers HAUT     : {df_valid['is_outlier_high'].sum()}")

# ============================================================================
# PHASE 2 : LISTE OUTLIERS POUR EXAMEN MANUEL
# ============================================================================

print(f"\n{'='*80}")
print("PHASE 2 : OUTLIERS À EXAMINER (Contexte externe)")
print(f"{'='*80}")

df_outliers = df_valid[df_valid['is_outlier']].sort_values('amp_parfaite', ascending=False)

if len(df_outliers) > 0:
    print(f"\n🚨 {len(df_outliers)} OUTLIERS IDENTIFIÉS\n")
    print(f"{'Date':<12} {'Amp':>8} {'Type':>10} {'R²':>8} {'Amp.trend':>12} {'Durée':>10}")
    print("-" * 80)
    
    for idx, row in df_outliers.iterrows():
        outlier_type = "🔴 HAUT" if row['is_outlier_high'] else "🔵 BAS"
        print(f"{row['date']:<12} {row['amp_parfaite']:>8.3f} {outlier_type:>10} "
              f"{row['trend_r2_optimized']:>8.3f} {row['trend_amplitude_optimized']:>10.1f} p "
              f"{row['trend_duration_optimized']:>8.1f} h")
    
    print(f"\n{'='*80}")
    print("EXAMEN CONTEXTE EXTERNE REQUIS")
    print(f"{'='*80}")
    
    print(f"\n📋 Pour CHAQUE outlier ci-dessus, vérifier :")
    print(f"\n   1. Événements géopolitiques :")
    print(f"      • Annonces Trump (tarifs douaniers, tweets)")
    print(f"      • Conflits (Ukraine, Moyen-Orient, Chine)")
    print(f"      • Sanctions économiques")
    
    print(f"\n   2. Crises économiques/financières :")
    print(f"      • Faillites bancaires (SVB, Credit Suisse)")
    print(f"      • Crises souveraines")
    print(f"      • Flash crashes")
    
    print(f"\n   3. Décisions monétaires extraordinaires :")
    print(f"      • Interventions d'urgence BCE/Fed")
    print(f"      • Changements politique monétaire majeurs")
    
    print(f"\n   4. Événements sanitaires/catastrophes :")
    print(f"      • COVID-19 vagues/variants")
    print(f"      • Catastrophes naturelles majeures")
    
    print(f"\n💡 MÉTHODOLOGIE :")
    print(f"   - Rechercher actualités pour chaque date")
    print(f"   - Documenter facteur externe identifié")
    print(f"   - Décider : INCLURE ou EXCLURE de l'analyse")
    print(f"   - Si exclu : créer règle spéciale pour ces cas")
    
    # Créer fichier outliers à examiner
    outliers_csv = project_root / "eurusd_clean" / "scripts" / "session102" / "outliers_to_examine.csv"
    
    df_outliers_export = df_outliers[['date', 'amp_parfaite', 'is_outlier_high', 'is_outlier_low',
                                       'trend_r2_optimized', 'trend_amplitude_optimized', 
                                       'trend_duration_optimized']].copy()
    df_outliers_export['external_factor'] = ''  # À remplir manuellement
    df_outliers_export['include_in_analysis'] = ''  # YES/NO à décider
    df_outliers_export['notes'] = ''
    
    df_outliers_export.to_csv(outliers_csv, index=False)
    print(f"\n💾 Liste exportée : {outliers_csv.name}")
    print(f"   Remplir colonnes 'external_factor' et 'include_in_analysis'")

else:
    print(f"\n✅ Aucun outlier détecté avec critère IQR 1.5×")
    print(f"   Distribution relativement normale")

# ============================================================================
# PHASE 3 : ANALYSE SUR DONNÉES PROPRES (Sans outliers)
# ============================================================================

print(f"\n{'='*80}")
print("PHASE 3 : ANALYSE DONNÉES PROPRES (Sans outliers)")
print(f"{'='*80}")

df_clean = df_valid[~df_valid['is_outlier']].copy()

print(f"\n✅ Dataset propre : {len(df_clean)} événements (sans {n_outliers} outliers)")

# Statistiques propres
amp_clean = df_clean['amp_parfaite'].values

print(f"\n📊 Statistiques PROPRES (sans outliers) :")
print(f"   Moyenne      : {amp_clean.mean():.3f}")
print(f"   Médiane      : {np.median(amp_clean):.3f}")
print(f"   Écart-type   : {amp_clean.std():.3f}")
print(f"   Min          : {amp_clean.min():.3f}")
print(f"   Max          : {amp_clean.max():.3f}")

# Comparaison avec/sans outliers
amp_all = df_valid['amp_parfaite'].values

print(f"\n📊 Impact outliers sur statistiques :")
print(f"   {'Métrique':<20} {'AVEC outliers':>15} {'SANS outliers':>15} {'Δ':>10}")
print(f"   {'-'*60}")
print(f"   {'Moyenne':<20} {amp_all.mean():>15.3f} {amp_clean.mean():>15.3f} {amp_clean.mean()-amp_all.mean():>10.3f}")
print(f"   {'Médiane':<20} {np.median(amp_all):>15.3f} {np.median(amp_clean):>15.3f} {np.median(amp_clean)-np.median(amp_all):>10.3f}")
print(f"   {'Écart-type':<20} {amp_all.std():>15.3f} {amp_clean.std():>15.3f} {amp_clean.std()-amp_all.std():>10.3f}")

if abs(amp_clean.mean() - amp_all.mean()) > 0.2:
    print(f"\n   🚨 IMPACT MAJEUR : Outliers biaisent significativement l'analyse !")
elif abs(amp_clean.mean() - amp_all.mean()) > 0.1:
    print(f"\n   ⚠️  IMPACT MODÉRÉ : Outliers influencent les résultats")
else:
    print(f"\n   ✅ Impact mineur : Outliers peu d'effet")

# Corrélations sur données propres
print(f"\n📊 CORRÉLATIONS (données propres uniquement) :")

if len(df_clean) >= 10:
    corr_r2_clean = df_clean['amp_parfaite'].corr(df_clean['trend_r2_optimized'])
    corr_amp_clean = df_clean['amp_parfaite'].corr(df_clean['trend_amplitude_optimized'])
    corr_dur_clean = df_clean['amp_parfaite'].corr(df_clean['trend_duration_optimized'])
    
    # Avec outliers (référence)
    corr_r2_all = df_valid['amp_parfaite'].corr(df_valid['trend_r2_optimized'])
    corr_amp_all = df_valid['amp_parfaite'].corr(df_valid['trend_amplitude_optimized'])
    
    print(f"   {'Variable':<20} {'AVEC outliers':>15} {'SANS outliers':>15} {'Δ':>10}")
    print(f"   {'-'*60}")
    print(f"   {'amp vs R²':<20} {corr_r2_all:>15.3f} {corr_r2_clean:>15.3f} {corr_r2_clean-corr_r2_all:>10.3f}")
    print(f"   {'amp vs Amplitude':<20} {corr_amp_all:>15.3f} {corr_amp_clean:>15.3f} {corr_amp_clean-corr_amp_all:>10.3f}")
    print(f"   {'amp vs Durée':<20} {corr_dur_clean:>15.3f} {corr_dur_clean:>10.3f}")
    
    if abs(corr_r2_clean - corr_r2_all) > 0.2:
        print(f"\n   🚨 Outliers changent SIGNIFICATIVEMENT les corrélations !")
        print(f"      → Analyse DOIT être faite sans outliers")

else:
    print(f"\n   ⚠️  Trop peu de données propres ({len(df_clean)}) pour corrélations fiables")

# Sauvegarder dataset propre
clean_csv = project_root / "eurusd_clean" / "scripts" / "session102" / "analysis_real_data_NO_OUTLIERS.csv"
df_clean.to_csv(clean_csv, index=False)
print(f"\n💾 Dataset propre sauvegardé : {clean_csv.name}")

# ============================================================================
# PHASE 4 : RECOMMANDATION ANALYSE SUITE
# ============================================================================

print(f"\n{'='*80}")
print("RECOMMANDATION PROCHAINES ÉTAPES")
print(f"{'='*80}")

print(f"\n1️⃣  EXAMINER OUTLIERS ({n_outliers} cas)")
print(f"    → Ouvrir : outliers_to_examine.csv")
print(f"    → Rechercher contexte externe pour chaque date")
print(f"    → Décider : inclure ou exclure")

print(f"\n2️⃣  TEST HYPOTHÈSE SUR DONNÉES PROPRES")
print(f"    → Utiliser : analysis_real_data_NO_OUTLIERS.csv")
print(f"    → Lancer : test_hypothesis_per_cluster.py")
print(f"    → Sur {len(df_clean)} événements normaux uniquement")

print(f"\n3️⃣  ANALYSE OUTLIERS SÉPARÉE (après)")
print(f"    → Si patterns détectés (ex: tous pendant Trump)")
print(f"    → Créer règles spéciales pour ces cas")
print(f"    → Ou simplement documenter comme non-prédictibles")

print(f"\n💡 POURQUOI C'EST CRITIQUE :")
print(f"   Si outliers = facteurs externes exceptionnels")
print(f"   → Ne DOIVENT PAS influencer analyse tendance normale")
print(f"   → Sinon : corrélations artificielles, conclusions fausses")

print(f"\n{'='*80}")
print("MÉTHODOLOGIE RIGOUREUSE APPLIQUÉE ✅")
print(f"{'='*80}")
