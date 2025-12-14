#!/usr/bin/env python3
"""
ÉTAPE 5 : TESTER STRATÉGIES D'AMPLIFICATION
============================================

Pour chaque date :
1. Lire impact_predit, impact_real, amp_parfaite, métriques tendance
2. TESTER différentes stratégies d'amplification :
   - Baseline (2.5 fixe)
   - Surprise (formule actuelle planificateur)
   - R² (hypothèse Session 102)
   - Durée
   - R² + Durée combiné
3. Pour chaque stratégie :
   - Recalculer impact = impact_predit / 2.5 × amp_strategy
   - Comparer erreur vs impact_real EN PIPS
4. Afficher gains/pertes PAR CAS
5. Statistiques globales

ENTRÉE : step4_avec_tendances_NEW.csv
SORTIE : step5_resultats_finaux_NEW.csv + rapport détaillé
"""

from pathlib import Path
import pandas as pd
import numpy as np

print("=" * 100)
print("ÉTAPE 5 : TESTER STRATÉGIES D'AMPLIFICATION")
print("=" * 100)
print()

# ============================================================================
# CHARGER RÉSULTATS STEP4
# ============================================================================

data_dir = Path(__file__).parent / "data"
step4_path = data_dir / "step4_avec_tendances_NEW.csv"

if not step4_path.exists():
    print(f"❌ Fichier manquant : {step4_path.name}")
    print(f"   → Exécuter d'abord : python3 step4_detecter_tendances_NEW.py")
    exit(1)

df = pd.read_csv(step4_path)
df['event_date'] = pd.to_datetime(df['event_date'])

print(f"✅ {len(df)} cas à analyser")
print()

# ============================================================================
# DÉFINIR STRATÉGIES D'AMPLIFICATION
# ============================================================================

def amp_baseline():
    """Baseline : toujours 2.5"""
    return 2.5

def amp_surprise(max_surprise_pct):
    """Selon surprise (formule actuelle planificateur)"""
    if max_surprise_pct <= 5:
        return 1.0
    elif max_surprise_pct <= 15:
        return 1.0 + (max_surprise_pct - 5) / 10 * 1.5
    else:
        return 2.5

def amp_r2(r_squared):
    """Selon R² observé (moyenne par zone)"""
    if r_squared < 0.3:
        return 3.0  # Amp moyenne zone faible : 1.21 × 2.5
    elif r_squared < 0.6:
        return 4.2  # Amp moyenne zone modérée : 1.70 × 2.5 (sweet spot)
    else:
        return 2.4  # Amp moyenne zone forte : 0.97 × 2.5

def amp_duration(duration_hours):
    """Selon durée observée"""
    if duration_hours < 5:
        return 2.4  # Amp moyenne court : 0.96 × 2.5
    elif duration_hours < 15:
        return 4.3  # Amp moyenne moyen : 1.71 × 2.5 (sweet spot)
    else:
        return 2.3  # Amp moyenne long : 0.93 × 2.5

def amp_combined(r_squared, duration_hours):
    """Combiné R² + Durée"""
    # Sweet spot
    if 0.3 <= r_squared <= 0.6 and 5 <= duration_hours <= 15:
        return 4.2  # Amplification élevée
    # Zone risque
    elif r_squared > 0.7 and duration_hours < 5:
        return 2.0  # Amplification faible
    # Standard
    else:
        return 2.8

strategies = {
    'baseline': ('Baseline (2.5)', lambda row: amp_baseline()),
    'surprise': ('Surprise', lambda row: amp_surprise(row['max_surprise'])),
    'r2': ('R²', lambda row: amp_r2(row['r_squared'])),
    'duree': ('Durée', lambda row: amp_duration(row['duration_hours'])),
    'r2_duree': ('R²+Durée', lambda row: amp_combined(row['r_squared'], row['duration_hours']))
}

# ============================================================================
# TESTER CHAQUE STRATÉGIE SUR CHAQUE CAS
# ============================================================================

print("=" * 100)
print("ANALYSE CAS PAR CAS")
print("=" * 100)

# Préparer colonnes résultats
for key in strategies.keys():
    df[f'amp_{key}'] = 0.0
    df[f'impact_{key}'] = 0.0
    df[f'error_{key}'] = 0.0

# Calculer pour chaque cas
for idx, row in df.iterrows():
    print(f"\n{'-'*100}")
    print(f"{row['event_date'].strftime('%Y-%m-%d')} | "
          f"R²={row['r_squared']:.3f}, Dur={row['duration_hours']:.1f}h, Surp={row['max_surprise']:.0f}%")
    print(f"{'-'*100}")
    print(f"Impact prédit (amp=2.5) : {row['impact_predit']:6.1f} pips")
    print(f"Impact réel             : {row['impact_real']:6.1f} pips")
    print(f"Amp parfaite            : {row['amp_parfaite']:6.3f}")
    print()
    
    for key, (label, func) in strategies.items():
        # Calculer amp selon stratégie
        amp = func(row)
        
        # Recalculer impact avec cette amp
        impact_pred = (row['impact_predit'] / 2.5) * amp
        
        # Erreur en pips
        error = abs(row['impact_real'] - impact_pred)
        
        # Sauvegarder
        df.at[idx, f'amp_{key}'] = amp
        df.at[idx, f'impact_{key}'] = impact_pred
        df.at[idx, f'error_{key}'] = error
        
        # Gain vs baseline
        gain = df.at[idx, 'error_baseline'] - error
        status = "✅✅" if gain > 10 else "✅" if gain > 5 else "⚠️" if gain > 0 else "❌"
        
        print(f"{status} {label:15s} : amp={amp:4.1f} → impact={impact_pred:6.1f} pips, "
              f"erreur={error:5.1f} pips ({gain:+5.1f})")

# ============================================================================
# STATISTIQUES GLOBALES
# ============================================================================

print(f"\n{'='*100}")
print("STATISTIQUES GLOBALES")
print(f"{'='*100}\n")

print(f"{'Stratégie':<20} {'MAE (pips)':>12} {'Amélioration':>14} {'Cas améliorés':>15}")
print(f"{'-'*100}")

mae_baseline = df['error_baseline'].mean()

for key, (label, _) in strategies.items():
    mae = df[f'error_{key}'].mean()
    improvement = ((mae_baseline - mae) / mae_baseline) * 100
    n_improved = (df['error_baseline'] - df[f'error_{key}'] > 0).sum()
    
    status = "✅✅" if improvement > 15 else "✅" if improvement > 5 else "⚠️" if improvement > 0 else "❌"
    
    print(f"{status} {label:<17} {mae:>12.1f} {improvement:>+13.1f}% {n_improved:>7}/{len(df):<5}")

# ============================================================================
# ANALYSES DÉTAILLÉES
# ============================================================================

print(f"\n{'='*100}")
print("TOP 5 GAINS (Meilleure stratégie non-baseline)")
print(f"{'='*100}\n")

# Pour chaque cas, trouver meilleure stratégie
df['best_non_baseline'] = ''
df['best_gain'] = 0.0

for idx, row in df.iterrows():
    gains = {}
    for key in ['surprise', 'r2', 'duree', 'r2_duree']:
        gain = row['error_baseline'] - row[f'error_{key}']
        gains[key] = gain
    
    best_key = max(gains, key=gains.get)
    df.at[idx, 'best_non_baseline'] = strategies[best_key][0]
    df.at[idx, 'best_gain'] = gains[best_key]

# TOP 5 gains
top_gains = df.nlargest(5, 'best_gain')

for _, row in top_gains.iterrows():
    print(f"{row['event_date'].strftime('%Y-%m-%d')} : {row['best_non_baseline']:15s} "
          f"gain={row['best_gain']:+5.1f} pips")
    print(f"   R²={row['r_squared']:.3f}, Durée={row['duration_hours']:.1f}h, Surprise={row['max_surprise']:.0f}%")
    print()

# ============================================================================
# SAUVEGARDER
# ============================================================================

output_path = data_dir / "step5_resultats_finaux_NEW.csv"
df.to_csv(output_path, index=False)

print(f"{'='*100}")
print(f"✅ ÉTAPE 5 TERMINÉE : {len(df)} cas analysés")
print(f"✅ Sauvegardé : {output_path.name}")
print(f"{'='*100}")

# ============================================================================
# CONCLUSION
# ============================================================================

print(f"\n{'='*100}")
print("CONCLUSION")
print(f"{'='*100}\n")

best_strategy = min(
    [(key, df[f'error_{key}'].mean()) for key in strategies.keys()],
    key=lambda x: x[1]
)

print(f"🏆 Meilleure stratégie : {strategies[best_strategy[0]][0]}")
print(f"   MAE : {best_strategy[1]:.1f} pips")

if best_strategy[0] == 'baseline':
    print(f"\n❌ BASELINE GAGNE")
    print(f"   Aucune stratégie dynamique n'améliore le résultat")
    print(f"   Avec {len(df)} points, relation non généralisable")
else:
    improvement = ((mae_baseline - best_strategy[1]) / mae_baseline) * 100
    print(f"\n✅ STRATÉGIE DYNAMIQUE MEILLEURE")
    print(f"   Amélioration : {improvement:+.1f}%")
    print(f"   À considérer pour intégration")
