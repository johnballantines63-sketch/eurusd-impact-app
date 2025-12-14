"""
VÉRIFICATION CAS #310
Session 138

Mission:
- Vérifier que le cas #310 (2025-04-23) a été corrigé
- Comparer classification v1 vs v2
- Extraire détails prix pour validation manuelle

Contexte cas #310 (découvert Session 137):
- Date: 2025-04-23 15:14 Bern (13:14 UTC)
- Impact: ~80 pips DOWN
- v1: DOUBLE_WAVE (FAUX - dip_ratio 1314%)
- v2 attendu: SINGLE_WAVE_FORT_DOWN
- movement_id: 310

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import pandas as pd
from pathlib import Path

# =============================================================================
# CHEMINS
# =============================================================================

V1_CSV = Path(__file__).parent / "step3_movements_with_patterns.csv"
V2_CSV = Path(__file__).parent / "step3_movements_with_patterns_v2.csv"

print("=" * 80)
print("VÉRIFICATION CAS #310 - 2025-04-23")
print("=" * 80)

# =============================================================================
# CHARGER DONNÉES
# =============================================================================

print("\n📊 RECHERCHE CAS #310")
print("-" * 80)

df_v1 = pd.read_csv(V1_CSV)
df_v2 = pd.read_csv(V2_CSV)

df_v1['movement_datetime'] = pd.to_datetime(df_v1['movement_datetime'], utc=True)
df_v2['movement_datetime'] = pd.to_datetime(df_v2['movement_datetime'], utc=True)

# Chercher mouvements 2025-04-23
target_date = pd.Timestamp('2025-04-23').date()

df_v1['date'] = df_v1['movement_datetime'].dt.date
df_v2['date'] = df_v2['movement_datetime'].dt.date

candidates_v1 = df_v1[df_v1['date'] == target_date].copy()
candidates_v2 = df_v2[df_v2['date'] == target_date].copy()

print(f"   Mouvements trouvés pour 2025-04-23:")
print(f"      v1: {len(candidates_v1)} candidats")
print(f"      v2: {len(candidates_v2)} candidats")

if len(candidates_v1) == 0:
    print("\n   ❌ Aucun mouvement trouvé pour 2025-04-23")
    exit()

print("\n   Liste candidats:")
for idx, row in candidates_v1.iterrows():
    print(f"      [{row['movement_id']:3d}] {row['movement_datetime']} {row['direction']:4s} {row['impact_pips']:6.1f}p")

# =============================================================================
# IDENTIFIER CAS #310
# =============================================================================

print("\n📊 IDENTIFICATION CAS #310")
print("-" * 80)

# Chercher directement movement_id=310
if 310 in candidates_v1['movement_id'].values:
    case_310_v1 = candidates_v1[candidates_v1['movement_id'] == 310]
    print("   ✅ CAS #310 trouvé directement (movement_id=310)")
else:
    print("   ❌ movement_id=310 introuvable")
    exit()

# Extraire cas #310
row_v1 = case_310_v1.iloc[0]
movement_id = row_v1['movement_id']

print(f"\n   CAS #310 identifié:")
print(f"      movement_id : {movement_id}")
print(f"      datetime    : {row_v1['movement_datetime']}")
print(f"      direction   : {row_v1['direction']}")
print(f"      impact      : {row_v1['impact_pips']:.1f} pips")
print(f"      num_events  : {row_v1.get('num_events', 'N/A')}")

# Trouver même mouvement en v2
row_v2 = df_v2[df_v2['movement_id'] == movement_id].iloc[0]

# =============================================================================
# COMPARAISON v1 vs v2
# =============================================================================

print("\n📊 COMPARAISON v1 vs v2")
print("-" * 80)

print(f"\n   v1 (INCORRECT):")
print(f"      Pattern         : {row_v1['pattern_type']}")
print(f"      Confidence      : {row_v1.get('confidence', 'N/A')}")
if 'dip_ratio' in row_v1 and pd.notna(row_v1['dip_ratio']):
    print(f"      dip_ratio       : {row_v1['dip_ratio']:.3f}")
if 'peak1_amplitude_pips' in row_v1 and pd.notna(row_v1['peak1_amplitude_pips']):
    print(f"      peak1 amplitude : {row_v1['peak1_amplitude_pips']:.1f} pips")

print(f"\n   v2 (CORRECT attendu):")
print(f"      Pattern         : {row_v2['pattern_type']}")
print(f"      Confidence      : {row_v2.get('confidence', 'N/A')}")

# Métriques selon pattern v2
if row_v2['pattern_type'] == 'DOUBLE_WAVE_DOWN':
    print(f"      rise_ratio      : {row_v2.get('rise_ratio', 'N/A'):.3f}")
    print(f"      trough1 ampl    : {row_v2.get('trough1_amplitude_pips', 'N/A'):.1f} pips")
    print(f"      trough2 ampl    : {row_v2.get('trough2_amplitude_pips', 'N/A'):.1f} pips")
elif row_v2['pattern_type'] == 'SINGLE_WAVE_FORT_DOWN':
    print(f"      trough1 ampl    : {row_v2.get('trough1_amplitude_pips', 'N/A'):.1f} pips")
elif row_v2['pattern_type'] == 'SINGLE_WAVE_STANDARD_DOWN':
    print(f"      trough1 ampl    : {row_v2.get('trough1_amplitude_pips', 'N/A'):.1f} pips")

# =============================================================================
# VALIDATION CORRECTION
# =============================================================================

print("\n📊 VALIDATION CORRECTION")
print("-" * 80)

is_corrected = False
issues = []

# Check 1: Pattern changé
if row_v1['pattern_type'] == row_v2['pattern_type']:
    issues.append("Pattern identique v1/v2")
else:
    print("   ✅ Pattern a changé v1→v2")

# Check 2: Direction cohérente
if row_v2['pattern_type'].endswith('_DOWN') or row_v2['pattern_type'] == 'INCONNU':
    print(f"   ✅ Pattern v2 cohérent avec direction DOWN")
else:
    issues.append(f"Pattern v2 {row_v2['pattern_type']} incohérent avec direction DOWN")

# Check 3: Métriques raisonnables
if row_v2['pattern_type'] == 'DOUBLE_WAVE_DOWN':
    rise_ratio = row_v2.get('rise_ratio', 999)
    if 0.30 <= rise_ratio <= 0.70:
        print(f"   ✅ rise_ratio {rise_ratio:.3f} dans range [0.30,0.70]")
        is_corrected = True
    else:
        issues.append(f"rise_ratio {rise_ratio:.3f} hors range")
elif row_v2['pattern_type'] in ['SINGLE_WAVE_FORT_DOWN', 'SINGLE_WAVE_STANDARD_DOWN']:
    trough_amp = row_v2.get('trough1_amplitude_pips', 0)
    if trough_amp >= 20.0:
        print(f"   ✅ trough1 amplitude {trough_amp:.1f} pips >= 20 pips")
        is_corrected = True
    else:
        issues.append(f"trough1 amplitude {trough_amp:.1f} < 20 pips")
else:
    issues.append(f"Pattern v2 {row_v2['pattern_type']} inattendu")

# =============================================================================
# ÉVÉNEMENTS ASSOCIÉS
# =============================================================================

print("\n📊 ÉVÉNEMENTS ASSOCIÉS")
print("-" * 80)

if 'event_keys' in row_v2 and pd.notna(row_v2['event_keys']):
    events = row_v2['event_keys']
    print(f"   {events}")
else:
    print("   Aucun événement associé")

if 'num_events' in row_v2 and 'total_score' in row_v2:
    print(f"\n   Nombre événements : {row_v2['num_events']}")
    print(f"   Score total       : {row_v2['total_score']:.1f}")

# =============================================================================
# SYNTHÈSE
# =============================================================================

print("\n" + "=" * 80)
print("SYNTHÈSE VÉRIFICATION CAS #310")
print("=" * 80)

print(f"\n📋 CAS #310:")
print(f"   movement_id : {movement_id}")
print(f"   Date/heure  : {row_v1['movement_datetime']}")
print(f"   Impact      : {row_v1['impact_pips']:.1f} pips {row_v1['direction']}")

print(f"\n📊 CLASSIFICATION:")
print(f"   v1 (biaisé)        : {row_v1['pattern_type']}")
print(f"   v2 (direction-aware): {row_v2['pattern_type']}")

if len(issues) == 0 and is_corrected:
    print(f"\n✅ CAS #310 CORRIGÉ AVEC SUCCÈS")
    print(f"   - Pattern changé et cohérent avec direction")
    print(f"   - Métriques respectent critères stricts")
    print(f"   - Algorithme v2 fonctionne correctement sur ce cas")
else:
    print(f"\n⚠️ CAS #310 - PROBLÈMES DÉTECTÉS:")
    for issue in issues:
        print(f"   - {issue}")
    
    if not is_corrected:
        print(f"\n   ❌ Correction incomplète - Nécessite investigation")

print("\n" + "=" * 80)

# Sauvegarder détails cas #310
case_310_details = pd.DataFrame({
    'movement_id': [movement_id],
    'datetime': [row_v1['movement_datetime']],
    'direction': [row_v1['direction']],
    'impact_pips': [row_v1['impact_pips']],
    'pattern_v1': [row_v1['pattern_type']],
    'pattern_v2': [row_v2['pattern_type']],
    'corrected': [is_corrected],
    'issues': [', '.join(issues) if issues else 'None']
})

output_file = Path(__file__).parent / "case_310_verification.csv"
case_310_details.to_csv(output_file, index=False)

print(f"\n✅ Détails cas #310 sauvegardés : {output_file}")
print("=" * 80)
