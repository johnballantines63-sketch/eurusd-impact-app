#!/usr/bin/env python3
"""
Mise à Jour CSV Final avec Mesures Correctes
=============================================

Objectif : Mettre à jour impacts_reels_mesures.csv avec les valeurs correctes
basées sur le pattern détecté (pic 2 pour DOUBLE_WAVE, pic 1 pour SINGLE_WAVE)
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Fichiers
CSV_CORRECT = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures_CORRECT.csv'
CSV_FINAL = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures.csv'

print('='*100)
print('MISE À JOUR CSV FINAL')
print('='*100)
print()

# Charger CSV correct
if not CSV_CORRECT.exists():
    print(f'❌ CSV correct non trouvé : {CSV_CORRECT}')
    sys.exit(1)

df_correct = pd.read_csv(CSV_CORRECT)
print(f'✅ CSV correct chargé : {len(df_correct)} dates')
print()

# Créer CSV final avec format simplifié
df_final = pd.DataFrame()

for _, row in df_correct.iterrows():
    # Utiliser event_time depuis CSV ou extraire depuis date
    if 'event_time' in row and pd.notna(row['event_time']):
        event_time = str(row['event_time'])
    else:
        # Extraire depuis date (par défaut 14:30 pour événements US)
        event_time = '14:30'
    
    # Déterminer note selon pattern
    if row['pattern_type'] == 'DOUBLE_WAVE':
        note = f"DOUBLE_WAVE - Pic 2 utilisé ({row['wave2_peak_pips_absolute']:.2f} pips)"
    elif 'SINGLE_WAVE' in str(row['pattern_type']):
        note = f"{row['pattern_type']} - Pic unique utilisé ({row['wave1_peak_pips_absolute']:.2f} pips)"
    else:
        note = f"{row['pattern_type']} - Pic utilisé: {row['peak_used']}"
    
    df_final = pd.concat([df_final, pd.DataFrame([{
        'date': row['date'],
        'event_time': event_time,
        'timezone': 'Europe/Zurich',
        'impact_real_pips': row['impact_real_pips'],
        'baseline_price': row['baseline_price'] if pd.notna(row['baseline_price']) else None,
        'peak_price': row['peak_price'] if pd.notna(row['peak_price']) and row['peak_price'] > 0 else None,
        'peak_time': row['peak_time'] if pd.notna(row['peak_time']) else None,
        'direction': int(row['direction']) if pd.notna(row['direction']) else 1,
        'notes': note,
        'success': True
    }])], ignore_index=True)

# Sauvegarder
df_final.to_csv(CSV_FINAL, index=False)
print(f'💾 CSV final sauvegardé : {CSV_FINAL}')
print()

# Afficher comparaison
print('='*100)
print('📊 VALEURS CORRIGÉES')
print('='*100)
print()

for _, row in df_final.iterrows():
    print(f'{row["date"]} ({row["notes"].split(" - ")[0]}) : {row["impact_real_pips"]:.2f} pips')

print()
print('='*100)
print('✅ MISE À JOUR TERMINÉE')
print('='*100)

