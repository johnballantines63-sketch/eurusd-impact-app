#!/usr/bin/env python3
"""
Mise à Jour CSV avec Mesures Correctes
======================================

Objectif : Mettre à jour le CSV impacts_reels_mesures.csv avec les valeurs correctes
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Fichiers
CSV_CORRIGE = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures_CORRIGE.csv'
CSV_ORIGINAL = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures.csv'

print('='*100)
print('MISE À JOUR CSV AVEC MESURES CORRECTES')
print('='*100)
print()

# Charger CSV corrigé
if not CSV_CORRIGE.exists():
    print(f'❌ CSV corrigé non trouvé : {CSV_CORRIGE}')
    sys.exit(1)

df_corrige = pd.read_csv(CSV_CORRIGE)
print(f'✅ CSV corrigé chargé : {len(df_corrige)} dates')
print()

# Créer nouveau CSV avec format correct
df_new = pd.DataFrame()

for _, row in df_corrige.iterrows():
    # Extraire heure depuis anchor_time
    anchor_time_str = str(row['anchor_time'])
    if 'T' in anchor_time_str:
        # Format ISO
        anchor_time = pd.to_datetime(anchor_time_str)
    else:
        anchor_time = pd.to_datetime(anchor_time_str)
    
    event_time = anchor_time.strftime('%H:%M')
    
    df_new = pd.concat([df_new, pd.DataFrame([{
        'date': row['date'],
        'event_time': event_time,
        'timezone': row['timezone'],
        'impact_real_pips': row['impact_real_pips'],
        'baseline_price': row['baseline_price'],
        'peak_price': row['peak_price'],
        'peak_time': row['peak_time'],
        'direction': row['direction'],
        'notes': f"Mesuré avec anchor_time réel: {row['anchor_time']} (diff CSV: {row['diff_csv']:.2f} pips)" if pd.notna(row.get('diff_csv')) else f"Mesuré avec anchor_time réel: {row['anchor_time']}",
        'success': True
    }])], ignore_index=True)

# Sauvegarder nouveau CSV
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures.csv'
df_new.to_csv(output_file, index=False)
print(f'💾 CSV mis à jour : {output_file}')
print()

# Afficher comparaison
print('='*100)
print('📊 COMPARAISON AVANT/APRÈS')
print('='*100)
print()

if CSV_ORIGINAL.exists():
    df_old = pd.read_csv(CSV_ORIGINAL)
    
    for _, row_new in df_new.iterrows():
        date = row_new['date']
        row_old = df_old[df_old['date'] == date]
        
        if not row_old.empty:
            old_impact = row_old.iloc[0].get('impact_real_pips', 'N/A')
            new_impact = row_new['impact_real_pips']
            
            if pd.notna(old_impact):
                diff = abs(new_impact - old_impact)
                pct = (diff / old_impact * 100) if old_impact > 0 else 0
                print(f'{date} : {old_impact:.2f} → {new_impact:.2f} pips (diff: {diff:.2f} pips, {pct:.1f}%)')
            else:
                print(f'{date} : N/A → {new_impact:.2f} pips')
        else:
            print(f'{date} : Nouvelle date → {row_new["impact_real_pips"]:.2f} pips')
else:
    print('⚠️ CSV original non trouvé, toutes les dates sont nouvelles')
    for _, row in df_new.iterrows():
        print(f'{row["date"]} : {row["impact_real_pips"]:.2f} pips')

print()
print('='*100)
print('✅ MISE À JOUR TERMINÉE')
print('='*100)




