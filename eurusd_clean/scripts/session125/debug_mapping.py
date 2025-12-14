#!/usr/bin/env python3
"""
Debug exact du mapping
"""
import pandas as pd
from pathlib import Path

SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"

print("="*80)
print("DEBUG EXACT MAPPING NFP")
print("="*80)
print()

df_scores = pd.read_csv(SCORES_PATH)

print(f"📊 Fichier chargé : {SCORES_PATH}")
print(f"   Lignes : {len(df_scores)}")
print(f"   Colonnes : {df_scores.columns.tolist()}")
print()

# Recherche EXACTE
print("🔍 RECHERCHE EXACTE 'non_farm_payrolls' :")
print()

exact_match = df_scores[
    (df_scores['event_name'] == 'non_farm_payrolls') & 
    (df_scores['country'] == 'US')
]

print(f"   Résultats : {len(exact_match)}")

if len(exact_match) > 0:
    print()
    print("   ✅ TROUVÉ :")
    for idx, row in exact_match.iterrows():
        print(f"      event_name = '{row['event_name']}'")
        print(f"      country = '{row['country']}'")
        print(f"      empirical_score = {row['empirical_score']}")
        print(f"      sample_size = {row['sample_size']}")
else:
    print("   ❌ PAS TROUVÉ")
    
    # Chercher variations
    print()
    print("🔍 VARIATIONS POSSIBLES :")
    print()
    
    variations = [
        'non_farm_payrolls',
        'non farm payrolls',
        'Non_Farm_Payrolls',
        'nonfarm_payrolls',
        'NonFarm_Payrolls'
    ]
    
    for var in variations:
        matches = df_scores[df_scores['event_name'].str.contains(var, case=False, na=False)]
        if len(matches) > 0:
            print(f"   ✅ '{var}' : {len(matches)} résultats")
            for idx, row in matches.head(2).iterrows():
                print(f"      → event_name='{row['event_name']}', score={row['empirical_score']}")
        else:
            print(f"   ❌ '{var}' : 0 résultat")

# Afficher toutes les lignes contenant "farm" ou "payroll"
print()
print("="*80)
print("TOUTES LES LIGNES US CONTENANT 'farm' OU 'payroll' :")
print("="*80)
print()

farm_payroll = df_scores[
    (df_scores['country'] == 'US') &
    (
        df_scores['event_name'].str.contains('farm', case=False, na=False) |
        df_scores['event_name'].str.contains('payroll', case=False, na=False)
    )
]

for idx, row in farm_payroll.iterrows():
    print(f"   event_name = '{row['event_name']}'")
    print(f"      score = {row['empirical_score']}, n = {row['sample_size']}")
    print()

print("="*80)
