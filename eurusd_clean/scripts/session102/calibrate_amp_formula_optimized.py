#!/usr/bin/env python3
"""
CALIBRATION FORMULE AMPLIFICATION - MÉTRIQUES OPTIMISÉES SESSION 103
=====================================================================

Utilise les métriques de tendance OPTIMISÉES (méthode TOP-N + dynamique)
au lieu des anciennes métriques (72h + calcul amplitude faux)

Objectif : Tester si formule dynamique amp = f(R², amplitude) fonctionne
avec métriques correctes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize
import sys

print("=" * 80)
print("CALIBRATION FORMULE AMPLIFICATION - MÉTRIQUES OPTIMISÉES")
print("=" * 80)

# Charger données avec métriques optimisées
project_root = Path(__file__).resolve().parents[3]  # eurusd_news_impact_calculator_MPC
csv_path = project_root / "eurusd_clean" / "scripts" / "session102" / "analysis_real_data_optimized.csv"

if not csv_path.exists():
    print(f"\n❌ ERREUR : Fichier introuvable")
    print(f"   {csv_path}")
    print(f"\n   Lancer d'abord : python3 recalculate_metrics_optimized.py")
    sys.exit(1)

df = pd.read_csv(csv_path)
print(f"\n✅ Chargé {len(df)} dates")

# Vérifier colonnes optimisées
required_cols = ['trend_duration_optimized', 'trend_amplitude_optimized', 'trend_r2_optimized']
missing = [col for col in required_cols if col not in df.columns]

if missing:
    print(f"\n❌ ERREUR : Colonnes manquantes : {missing}")
    print(f"   Lancer d'abord : python3 recalculate_metrics_optimized.py")
    sys.exit(1)

# Filtrer données valides
df_valid = df.dropna(subset=['trend_r2_optimized', 'trend_amplitude_optimized', 'amp_parfaite'])

print(f"✅ {len(df_valid)} dates avec métriques complètes")

if len(df_valid) < 10:
    print(f"\n⚠️  ATTENTION : Seulement {len(df_valid)} dates valides")
    print(f"   Risque de sur-apprentissage élevé")

# ============================================================================
# CAS RÉFÉRENCE
# ============================================================================

print(f"\n{'='*80}")
print("CAS RÉFÉRENCE 11.09.2025")
print(f"{'='*80}")

ref_date = '2025-09-11'
df_ref = df_valid[df_valid['date'] == ref_date]

if len(df_ref) > 0:
    ref_r2 = df_ref.iloc[0]['trend_r2_optimized']
    ref_amplitude = df_ref.iloc[0]['trend_amplitude_optimized']
    ref_duration = df_ref.iloc[0]['trend_duration_optimized']
    ref_amp_parfaite = df_ref.iloc[0]['amp_parfaite']
    
    print(f"\n📍 Métriques optimisées :")
    print(f"   R²              : {ref_r2:.3f}")
    print(f"   Amplitude       : {ref_amplitude:.1f} pips")
    print(f"   Durée           : {ref_duration:.1f}h")
    print(f"   Amp parfaite    : {ref_amp_parfaite:.3f}")
else:
    print(f"\n⚠️  Cas référence non trouvé avec métriques valides")
    ref_r2 = 0.6
    ref_amplitude = 100.0

# ============================================================================
# STATISTIQUES
# ============================================================================

print(f"\n{'='*80}")
print("STATISTIQUES GÉNÉRALES")
print(f"{'='*80}")

print(f"\n📊 Métriques tendances optimisées :")
print(f"   Durée moyenne     : {df_valid['trend_duration_optimized'].mean():.1f}h")
print(f"   Amplitude moyenne : {df_valid['trend_amplitude_optimized'].mean():.1f} pips")
print(f"   R² moyen          : {df_valid['trend_r2_optimized'].mean():.3f}")

# ============================================================================
# DÉFINITION FORMULES
# ============================================================================

print(f"\n{'='*80}")
print("DÉFINITION FORMULES CANDIDATES")
print(f"{'='*80}")

class AmplificationFormula:
    """Classe formule amplification"""
    
    def __init__(self, name, func, n_params, param_names, bounds=None):
        self.name = name
        self.func = func
        self.n_params = n_params
        self.param_names = param_names
        self.bounds = bounds
        self.params = None
        self.mae = None
    
    def predict(self, r2, amplitude=None):
        if self.params is None:
            raise ValueError("Formule non calibrée")
        return self.func(r2, amplitude, *self.params)

# Formules
def formula_linear(r2, amplitude, a, b):
    """amp = a × R² + b"""
    return a * r2 + b

def formula_linear_dual(r2, amplitude, a, b, c):
    """amp = a × R² + b × amplitude_tendance + c"""
    return a * r2 + b * (amplitude / 100.0) + c  # Normaliser amplitude

def formula_inverse(r2, amplitude, a, b):
    """amp = a / (R² + 0.1) + b"""
    return a / (r2 + 0.1) + b

def formula_ratio(r2, amplitude, k):
    """amp = ref_amp × (R² / R²_ref)^k"""
    return ref_amp_parfaite * ((r2 / ref_r2) ** k)

def formula_combined(r2, amplitude, a, b, c, d):
    """amp = a × R² + b × amplitude + c / (R² + 0.1) + d"""
    return a * r2 + b * (amplitude / 100.0) + c / (r2 + 0.1) + d

formulas = [
    AmplificationFormula(
        "F1: Linéaire simple (R² seul)",
        formula_linear,
        2,
        ['a', 'b'],
        bounds=[(0, 10), (0, 5)]
    ),
    AmplificationFormula(
        "F2: Linéaire dual (R² + amplitude)",
        formula_linear_dual,
        3,
        ['a', 'b', 'c'],
        bounds=[(0, 10), (-0.05, 0.05), (0, 5)]
    ),
    AmplificationFormula(
        "F3: Inverse (R² faible → amp forte)",
        formula_inverse,
        2,
        ['a', 'b'],
        bounds=[(0, 10), (0, 5)]
    ),
    AmplificationFormula(
        "F4: Ratio proportionnel ancré",
        formula_ratio,
        1,
        ['k'],
        bounds=[(0.1, 3)]
    ),
    AmplificationFormula(
        "F5: Combinée (R² + amplitude + inverse)",
        formula_combined,
        4,
        ['a', 'b', 'c', 'd'],
        bounds=[(0, 5), (-0.05, 0.05), (0, 5), (0, 5)]
    ),
]

print(f"\n✅ Défini {len(formulas)} formules candidates")

# ============================================================================
# CALIBRATION
# ============================================================================

print(f"\n{'='*80}")
print("CALIBRATION PARAMÈTRES")
print(f"{'='*80}")

def objective_function(params, formula_func, r2_data, amp_data, amp_target):
    """MAE à minimiser"""
    amp_pred = formula_func(r2_data, amp_data, *params)
    amp_pred = np.clip(amp_pred, 0.5, 5.0)
    return np.mean(np.abs(amp_pred - amp_target))

print(f"\nCalibration en cours...\n")

for formula in formulas:
    print(f"🔧 {formula.name}")
    
    r2_data = df_valid['trend_r2_optimized'].values
    amp_data = df_valid['trend_amplitude_optimized'].values
    target_data = df_valid['amp_parfaite'].values
    
    # Initial guess
    x0 = [1.0] * formula.n_params
    
    try:
        result = minimize(
            objective_function,
            x0,
            args=(formula.func, r2_data, amp_data, target_data),
            bounds=formula.bounds,
            method='L-BFGS-B'
        )
        
        formula.params = result.x
        
        # MAE calibration
        amp_pred = formula.func(r2_data, amp_data, *formula.params)
        amp_pred = np.clip(amp_pred, 0.5, 5.0)
        mae = np.mean(np.abs(amp_pred - target_data))
        
        print(f"   ✅ Paramètres : {', '.join([f'{name}={val:.3f}' for name, val in zip(formula.param_names, formula.params)])}")
        print(f"   MAE : {mae:.3f}\n")
        
    except Exception as e:
        print(f"   ❌ Échec : {e}\n")
        formula.params = None

# ============================================================================
# TEST
# ============================================================================

print(f"{'='*80}")
print("TEST SUR TOUTES LES DATES")
print(f"{'='*80}")

# Baseline
baseline_pred = np.full(len(df_valid), 2.5)
baseline_mae = np.mean(np.abs(baseline_pred - df_valid['amp_parfaite'].values))

print(f"\n📊 BASELINE amp=2.5 fixe :")
print(f"   MAE : {baseline_mae:.3f}")

print(f"\n📊 TEST FORMULES :\n")

results = []

for formula in formulas:
    if formula.params is None:
        continue
    
    r2_test = df_valid['trend_r2_optimized'].values
    amp_test = df_valid['trend_amplitude_optimized'].values
    target_test = df_valid['amp_parfaite'].values
    
    try:
        amp_pred = formula.func(r2_test, amp_test, *formula.params)
        amp_pred = np.clip(amp_pred, 0.5, 5.0)
        
        mae = np.mean(np.abs(amp_pred - target_test))
        corr = np.corrcoef(amp_pred, target_test)[0, 1]
        
        formula.mae = mae
        
        improvement = ((baseline_mae - mae) / baseline_mae) * 100
        
        status = "✅✅" if mae < baseline_mae and improvement > 10 else "✅" if mae < baseline_mae else "❌"
        
        print(f"{status} {formula.name}")
        print(f"   MAE={mae:.3f} (vs baseline {baseline_mae:.3f}, {improvement:+.1f}%)")
        print(f"   Corrélation={corr:+.3f}\n")
        
        results.append({
            'formula': formula,
            'mae': mae,
            'corr': corr,
            'improvement': improvement
        })
        
    except Exception as e:
        print(f"❌ {formula.name} : Erreur - {e}\n")

# ============================================================================
# SÉLECTION
# ============================================================================

print(f"{'='*80}")
print("SÉLECTION MEILLEURE FORMULE")
print(f"{'='*80}")

if len(results) == 0:
    print(f"\n❌ Aucune formule testable")
    sys.exit(1)

results_sorted = sorted(results, key=lambda x: x['mae'])
best = results_sorted[0]

print(f"\n🏆 MEILLEURE FORMULE : {best['formula'].name}")
print(f"\n   Paramètres : {', '.join([f'{name}={val:.3f}' for name, val in zip(best['formula'].param_names, best['formula'].params)])}")
print(f"\n   Métriques :")
print(f"   - MAE                : {best['mae']:.3f}")
print(f"   - Corrélation        : {best['corr']:+.3f}")
print(f"   - vs Baseline (2.5)  : {best['improvement']:+.1f}%")

# ============================================================================
# DÉCISION FINALE
# ============================================================================

print(f"\n{'='*80}")
print("DÉCISION FINALE")
print(f"{'='*80}")

mae_threshold = baseline_mae * 0.9
corr_threshold = 0.3

# Vérifier si coefficient dynamique existe
has_dynamic_coef = False
if best['formula'].n_params > 1:
    # Vérifier si au moins un coefficient est significatif (≠ 0)
    for param in best['formula'].params:
        if abs(param) > 0.1:
            has_dynamic_coef = True
            break

if best['mae'] < mae_threshold and best['corr'] > corr_threshold and has_dynamic_coef:
    decision = "VALIDÉE"
    print(f"\n✅✅ FORMULE DYNAMIQUE VALIDÉE !")
    print(f"\n   Critères satisfaits :")
    print(f"   ✅ MAE < baseline × 0.9 ({best['mae']:.3f} < {mae_threshold:.3f})")
    print(f"   ✅ Corrélation > 0.3 ({best['corr']:.3f})")
    print(f"   ✅ Coefficient dynamique significatif")
    print(f"\n   Amélioration : {best['improvement']:.1f}%")
    print(f"\n   🎉 HYPOTHÈSE CONFIRMÉE : Tendance prédit amplification !")
    print(f"\n   RECOMMANDATION : Intégrer formule dans Planificateur V2.7")
    
elif best['mae'] < baseline_mae:
    decision = "PARTIELLE"
    print(f"\n⚠️  VALIDATION PARTIELLE")
    print(f"\n   Amélioration détectée : {best['improvement']:.1f}%")
    print(f"   Mais critères incomplets :")
    if best['mae'] >= mae_threshold:
        print(f"   ⚠️  MAE insuffisant ({best['mae']:.3f} >= {mae_threshold:.3f})")
    if best['corr'] <= corr_threshold:
        print(f"   ⚠️  Corrélation faible ({best['corr']:.3f} <= {corr_threshold})")
    if not has_dynamic_coef:
        print(f"   ⚠️  Pas de coefficient dynamique significatif")
    
    print(f"\n   RECOMMANDATION : Utiliser amp constant optimisé (1.2)")
    
else:
    decision = "REJETÉE"
    print(f"\n❌ FORMULE REJETÉE")
    print(f"\n   Aucune amélioration vs baseline")
    print(f"   RECOMMANDATION : Utiliser amp constant 1.2 ou 2.5")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print(f"\n{'='*80}")
print("RÉSUMÉ COMPARATIF")
print(f"{'='*80}")

print(f"\n{'Formule':<45} {'MAE':>8} {'Amélioration':>12} {'Corr':>8}")
print("-" * 80)
print(f"{'BASELINE amp=2.5':<45} {baseline_mae:>8.3f} {'0.0%':>12} {'N/A':>8}")

for res in results_sorted:
    print(f"{res['formula'].name:<45} {res['mae']:>8.3f} {res['improvement']:>11.1f}% {res['corr']:>8.3f}")

print(f"\n{'='*80}")
print("FIN CALIBRATION")
print(f"{'='*80}")

if decision == "VALIDÉE":
    print(f"\n🎉 SUCCÈS ! Formule dynamique validée avec métriques correctes !")
elif decision == "PARTIELLE":
    print(f"\n⚠️  Amélioration partielle - amp constant 1.2 recommandé")
else:
    print(f"\n📊 Formule dynamique non validée - continuer avec amp constant")
