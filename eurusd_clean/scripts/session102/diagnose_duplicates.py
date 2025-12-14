#!/usr/bin/env python3
"""
DIAGNOSTIC DOUBLONS - CSV ORIGINAL
==================================

Vérifie si les 16 événements 2023-06-13 sont réels ou doublons
"""

import pandas as pd
from pathlib import Path

print("=" * 80)
print("DIAGNOSTIC DOUBLONS CSV ORIGINAL")
print("=" * 80)

project_root = Path(__file__).resolve().parents[3]
csv_orig = project_root / "eurusd_clean" / "scripts" / "session102" / "analysis_real_data_complete.csv"
csv_opt = project_root / "eurusd_clean" / "scripts" / "session102" / "analysis_real_data_optimized.csv"

print(f"\n📂 Chargement fichiers...")

df_orig = pd.read_csv(csv_orig)
df_opt = pd.read_csv(csv_opt)

print(f"   CSV original : {len(df_orig)} lignes")
print(f"   CSV optimisé : {len(df_opt)} lignes")

# Compter doublons par date
print(f"\n📊 DATES AVEC DOUBLONS :\n")
duplicates = df_opt['date'].value_counts()
duplicates_only = duplicates[duplicates > 1]

if len(duplicates_only) > 0:
    print(f"   {'Date':<15} {'Count':>6} {'Status'}")
    print("   " + "-" * 40)
    for date, count in duplicates_only.items():
        status = "🚨 SUSPECT" if count > 10 else "⚠️  Doublon"
        print(f"   {date:<15} {count:>6} {status}")
else:
    print("   ✅ Aucun doublon détecté")

# Vérifier 2023-06-13
print(f"\n{'='*80}")
print("ANALYSE DÉTAILLÉE 2023-06-13")
print(f"{'='*80}")

df_suspect = df_opt[df_opt['date'] == '2023-06-13']

if len(df_suspect) > 1:
    print(f"\n🚨 {len(df_suspect)} lignes pour 2023-06-13 !")
    
    # Vérifier si toutes colonnes identiques
    print(f"\n   Colonnes importantes :")
    cols_check = ['amp_parfaite', 'trend_r2_optimized', 'trend_amplitude_optimized', 
                  'trend_duration_optimized', 'impact_real', 'score']
    
    for col in cols_check:
        if col in df_suspect.columns:
            unique_vals = df_suspect[col].nunique()
            if unique_vals == 1:
                print(f"   ❌ {col:<30} : {unique_vals} valeur unique (DOUBLON !)")
            else:
                print(f"   ✅ {col:<30} : {unique_vals} valeurs différentes")
    
    # Afficher toutes les lignes
    print(f"\n   Détail des {len(df_suspect)} lignes :")
    print(df_suspect[['date', 'amp_parfaite', 'trend_r2_optimized', 'impact_real']].to_string())
    
    print(f"\n💡 DIAGNOSTIC :")
    print(f"   Si toutes colonnes identiques → ERREUR de duplication")
    print(f"   Si colonnes différentes → Événements distincts même jour")
else:
    print(f"\n✅ Une seule ligne pour 2023-06-13")

# Vérifier événements amp=0.500
print(f"\n{'='*80}")
print("ANALYSE ÉVÉNEMENTS amp=0.500")
print(f"{'='*80}")

df_min = df_opt[df_opt['amp_parfaite'] == 0.500]
print(f"\n⚠️  {len(df_min)} événements avec amp_parfaite = 0.500 EXACTEMENT")

if len(df_min) > 0:
    print(f"\n   Dates concernées :")
    for idx, row in df_min.iterrows():
        print(f"   - {row['date']}")
    
    print(f"\n💡 Valeur plancher artificielle ?")
    print(f"   Si calculée, peu probable d'avoir 6× exactement 0.500")

# Vérifier événements amp=5.000
df_max = df_opt[df_opt['amp_parfaite'] == 5.000]
if len(df_max) > 0:
    print(f"\n⚠️  {len(df_max)} événements avec amp_parfaite = 5.000 EXACTEMENT")
    print(f"   Valeur plafond artificielle ?")

# Distribution sans doublons
print(f"\n{'='*80}")
print("DISTRIBUTION NETTOYÉE (sans doublons)")
print(f"{'='*80}")

df_clean = df_opt.drop_duplicates(subset=['date'])
print(f"\n✅ Après suppression doublons : {len(df_clean)} événements uniques")

amp_clean = df_clean['amp_parfaite'].values
print(f"\n📊 Statistiques nettoyées :")
print(f"   Moyenne  : {amp_clean.mean():.3f}")
print(f"   Médiane  : {pd.Series(amp_clean).median():.3f}")
print(f"   Min      : {amp_clean.min():.3f}")
print(f"   Max      : {amp_clean.max():.3f}")

# Comparaison
print(f"\n📊 Impact des doublons :")
amp_all = df_opt['amp_parfaite'].values
print(f"   Moyenne AVEC doublons    : {amp_all.mean():.3f}")
print(f"   Moyenne SANS doublons    : {amp_clean.mean():.3f}")
print(f"   Différence               : {abs(amp_all.mean() - amp_clean.mean()):.3f}")

if abs(amp_all.mean() - amp_clean.mean()) > 0.1:
    print(f"\n   🚨 IMPACT SIGNIFICATIF ! Doublons biaisent l'analyse")
else:
    print(f"\n   ✅ Impact mineur")

print(f"\n{'='*80}")
print("RECOMMANDATION")
print(f"{'='*80}")

if len(duplicates_only) > 0:
    print(f"\n🔧 ACTIONS REQUISES :")
    print(f"   1. Vérifier CSV original (analysis_real_data_complete.csv)")
    print(f"   2. Si doublons → Nettoyer avant analyse")
    print(f"   3. Relancer calibration sur données nettoyées")
else:
    print(f"\n✅ Données propres, continuer analyse")

print(f"\n{'='*80}")
