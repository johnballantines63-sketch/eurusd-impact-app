#!/usr/bin/env python3
"""
Vérification manuelle du fix 'comparison' sur 11 septembre 2025
"""

import sys
from pathlib import Path
import pandas as pd

# Setup path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fx_impact_app.src.eodhd_client import fetch_calendar_json, calendar_to_events_df

print("\n" + "="*70)
print("TEST MANUEL : Fix 'comparison' sur 11 septembre 2025")
print("="*70)

# Récupérer données
print("\n[1] Récupération données EODHD...")
data = fetch_calendar_json('2025-09-11', '2025-09-11', countries=['US'])
print(f"    ✅ {len(data)} événements bruts récupérés")

# Normaliser
print("\n[2] Normalisation...")
df = calendar_to_events_df(data)
print(f"    ✅ {len(df)} événements normalisés")

# Filtrer Inflation Rate
print("\n[3] Recherche événements 'inflation'...")
inflation_events = df[
    df['event_key'].str.contains('inflation', case=False, na=False)
].copy()

if inflation_events.empty:
    print("    ❌ Aucun événement inflation trouvé")
    sys.exit(1)

print(f"    ✅ {len(inflation_events)} événements trouvés")

# Afficher résultats
print("\n[4] Résultats détaillés :")
print("-"*90)
print(f"{'Event Key':<35} {'Actual':>10} {'Estimate':>10} {'Surprise':>10}")
print("-"*90)

has_mom = False
has_yoy = False

for _, row in inflation_events.iterrows():
    event_key = row['event_key']
    actual = row.get('actual', None)
    estimate = row.get('estimate', None)
    
    # Calculer surprise
    if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
        surprise = abs((actual - estimate) / estimate) * 100
        surprise_str = f"{surprise:.1f}%"
    else:
        surprise_str = "0.0%"
    
    # Formater valeurs
    actual_str = f"{actual:.2f}" if pd.notna(actual) else "N/A"
    estimate_str = f"{estimate:.2f}" if pd.notna(estimate) else "N/A"
    
    print(f"{event_key:<35} {actual_str:>10} {estimate_str:>10} {surprise_str:>10}")
    
    # Vérifier présence suffixes
    if '_mom' in event_key.lower():
        has_mom = True
    if '_yoy' in event_key.lower():
        has_yoy = True

print("-"*90)

# Validation finale
print("\n[5] Validation :")
if has_mom:
    print("    ✅ Version MoM détectée")
else:
    print("    ⚠️  Version MoM absente")

if has_yoy:
    print("    ✅ Version YoY détectée")
else:
    print("    ⚠️  Version YoY absente")

if has_mom and has_yoy:
    print("\n" + "="*70)
    print("✅ SUCCÈS : Les versions MoM et YoY sont bien distinctes !")
    print("="*70)
    
    # Vérifier surprise significative sur MoM
    mom_events = inflation_events[
        inflation_events['event_key'].str.contains('_mom', case=False, na=False)
    ]
    
    if not mom_events.empty:
        mom_row = mom_events.iloc[0]
        if pd.notna(mom_row.get('actual')) and pd.notna(mom_row.get('estimate')):
            actual = float(mom_row['actual'])
            estimate = float(mom_row['estimate'])
            if estimate != 0:
                surprise = abs((actual - estimate) / estimate) * 100
                print(f"\n📊 Surprise sur version MoM : {surprise:.1f}%")
                if surprise > 20:
                    print("✅ Surprise significative (>20%) détectée !")
    
    sys.exit(0)
else:
    print("\n" + "="*70)
    print("❌ ÉCHEC : Les versions ne sont pas correctement séparées")
    print("="*70)
    sys.exit(1)
