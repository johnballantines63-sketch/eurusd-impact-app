"""
CALIBRATION FORMULE AMPLIFICATION - SESSION 102
================================================

Méthodologie :
1. Ancrage sur cas référence 11.09.2025 (amp=2.537, R²=0.742)
2. Proposition de 5+ formules mathématiques candidates
3. Calibration paramètres sur clusters similaires
4. Test de chaque formule sur TOUS les clusters
5. Sélection meilleure formule (MAE minimal)

Objectif : Trouver formule amp = f(R², amplitude) qui prédit mieux que baseline 2.5
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import minimize, curve_fit
import sys
import duckdb
from datetime import datetime, timedelta

# Importer fonction détection tendance avec extrema (CORRIGÉE)
from detect_trend_extremum import detect_trend_from_extremum, calculate_trend_strength_score

# Ajouter chemin config
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("CALIBRATION FORMULE AMPLIFICATION - SESSION 102")
print("=" * 80)

# ============================================================================
# ÉTAPE 1 : CHARGEMENT DONNÉES + CAS RÉFÉRENCE
# ============================================================================

print("\n📂 ÉTAPE 1 : Chargement données + cas référence")
print("-" * 80)

# Charger résultats Session 102
csv_path = Path(__file__).parent / "analysis_real_data_complete.csv"

if not csv_path.exists():
    print(f"❌ ERREUR : {csv_path.name} introuvable")
    sys.exit(1)

df = pd.read_csv(csv_path)
print(f"✅ Chargé {len(df)} dates")

# Cas référence : 11.09.2025
ref_date = '2025-09-11'
df_ref = df[df['date'] == ref_date]

if len(df_ref) == 0:
    print(f"❌ ERREUR : Cas référence {ref_date} introuvable")
    sys.exit(1)

# NOTE: Les métriques PROPRES seront calculées dans l'étape 1.5
# On garde temporairement les anciennes pour initialisation
ref_amp_temp = df_ref.iloc[0]['amp_parfaite']
ref_impact = df_ref.iloc[0]['impact_real']

print(f"\n📍 CAS RÉFÉRENCE : {ref_date}")
print(f"   Amp parfaite    : {ref_amp_temp:.3f}")
print(f"   Impact réel     : {ref_impact:.1f} pips")
print(f"   (Métriques tendance PROPRES à recalculer...)")

# Variables globales à mettre à jour après étape 1.5
ref_amp = ref_amp_temp
ref_r2 = None
ref_amplitude = None

# ============================================================================
# ÉTAPE 1.5 : RECALCUL MÉTRIQUES TENDANCE PROPRES
# ============================================================================

print("\n📊 ÉTAPE 1.5 : Recalcul métriques tendance (Méthode EXTREMA corrigée)")
print("-" * 80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print(f"✅ Connexion DB : {db_path}")
print("\nRecalcul tendances en cours...\n")

tendances_propres = []

for idx, row in df.iterrows():
    date_str = row['date']
    
    # Parser date
    try:
        event_dt = pd.to_datetime(date_str)
    except:
        print(f"⚠️  Erreur parsing date : {date_str}")
        tendances_propres.append(None)
        continue
    
    # Événement à 14:30 Bern (+02:00) → 12:30 UTC
    event_time_utc = event_dt.replace(hour=12, minute=30, second=0)
    start_time = event_time_utc - timedelta(hours=72)
    
    # Query prix 72h
    query = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime ASC
    """
    
    try:
        df_prices = conn.execute(query, [start_time, event_time_utc]).fetchdf()
    except Exception as e:
        print(f"⚠️  {date_str} : Erreur query - {e}")
        tendances_propres.append(None)
        continue
    
    if len(df_prices) < 100:
        print(f"⚠️  {date_str} : Données insuffisantes ({len(df_prices)} points)")
        tendances_propres.append(None)
        continue
    
    # Détecter tendance depuis EXTREMUM (méthode corrigée)
    prices = df_prices['close'].values
    timestamps = pd.to_datetime(df_prices['datetime']).tolist()
    
    # Utiliser window_swing=240 pour M1 (240 minutes = 4 heures pour détecter extrema MAJEURS)
    trend_info = detect_trend_from_extremum(prices, timestamps, window_swing=240)
    
    # Calculer score force
    trend_info['strength_score'] = calculate_trend_strength_score(trend_info)
    
    tendances_propres.append(trend_info)
    
    # Affichage progrès
    if (idx + 1) % 10 == 0 or (idx + 1) == len(df):
        print(f"   Traité {idx + 1}/{len(df)} dates...")

conn.close()

print("\n✅ Recalcul tendances terminé")

# Ajouter au dataframe
df['trend_duration_proper'] = [t['duration_hours'] if t else None for t in tendances_propres]
df['trend_amplitude_proper'] = [t['amplitude_pips'] if t else None for t in tendances_propres]
df['trend_r2_proper'] = [t['r_squared'] if t else None for t in tendances_propres]
df['trend_strength_score'] = [t['strength_score'] if t else None for t in tendances_propres]
df['trend_direction'] = [t['direction'] if t else None for t in tendances_propres]

# Statistiques
df_valid_trend = df.dropna(subset=['trend_duration_proper'])

print(f"\n📊 Statistiques tendances PROPRES ({len(df_valid_trend)} dates) :")
print(f"   Durée moyenne     : {df_valid_trend['trend_duration_proper'].mean():.1f}h (std={df_valid_trend['trend_duration_proper'].std():.1f}h)")
print(f"   Amplitude moyenne : {df_valid_trend['trend_amplitude_proper'].mean():.1f} pips (std={df_valid_trend['trend_amplitude_proper'].std():.1f})")
print(f"   R² moyen          : {df_valid_trend['trend_r2_proper'].mean():.3f}")
print(f"   Score force moy   : {df_valid_trend['trend_strength_score'].mean():.1f}/100")

# Mettre à jour référence avec métriques PROPRES
df_ref_updated = df[df['date'] == ref_date]
if len(df_ref_updated) > 0 and not pd.isna(df_ref_updated.iloc[0]['trend_r2_proper']):
    ref_r2 = df_ref_updated.iloc[0]['trend_r2_proper']
    ref_amplitude = df_ref_updated.iloc[0]['trend_amplitude_proper']
    ref_duration = df_ref_updated.iloc[0]['trend_duration_proper']
    
    print(f"\n📍 CAS RÉFÉRENCE AVEC MÉTRIQUES PROPRES :")
    print(f"   R² PROPRE         : {ref_r2:.3f}")
    print(f"   Amplitude PROPRE  : {ref_amplitude:.1f} pips")
    print(f"   Durée PROPRE      : {ref_duration:.1f} heures")
else:
    print("\n⚠️  ATTENTION : Métriques PROPRES référence non disponibles")
    print("   Utilisation valeurs par défaut")
    ref_r2 = 0.5
    ref_amplitude = 100.0

# ============================================================================
# ÉTAPE 2 : DÉFINITION FORMULES CANDIDATES
# ============================================================================

print("\n📐 ÉTAPE 2 : Définition formules candidates")
print("-" * 80)

class AmplificationFormula:
    """Classe pour formule amplification avec calibration"""
    
    def __init__(self, name, func, n_params, param_names, bounds=None):
        self.name = name
        self.func = func
        self.n_params = n_params
        self.param_names = param_names
        self.bounds = bounds
        self.params = None
        self.mae = None
        self.rmse = None
        self.corr = None
    
    def predict(self, r2, amplitude=None):
        """Prédire amp avec paramètres calibrés"""
        if self.params is None:
            raise ValueError("Formule non calibrée")
        return self.func(r2, amplitude, *self.params)
    
    def __str__(self):
        if self.params is None:
            return f"{self.name} (non calibré)"
        param_str = ", ".join([f"{name}={val:.3f}" for name, val in zip(self.param_names, self.params)])
        return f"{self.name} ({param_str})"

# Formule 1 : Linéaire simple (R² seul)
def formula_linear(r2, amplitude, a, b):
    """amp = a × R² + b"""
    return a * r2 + b

# Formule 2 : Ratio proportionnel ancré
def formula_ratio(r2, amplitude, k):
    """amp = amp_ref × (R² / R²_ref)^k"""
    return ref_amp * ((r2 / ref_r2) ** k)

# Formule 3 : Delta additive
def formula_delta(r2, amplitude, k):
    """amp = amp_ref + k × (R² - R²_ref)"""
    return ref_amp + k * (r2 - ref_r2)

# Formule 4 : Exponentielle
def formula_exp(r2, amplitude, k):
    """amp = amp_ref × exp(k × (R² - R²_ref))"""
    return ref_amp * np.exp(k * (r2 - ref_r2))

# Formule 5 : Linéaire avec amplitude PROPRE
def formula_linear_dual(r2, amplitude, a, b, c):
    """amp = a × R² + b × amplitude + c"""
    return a * r2 + b * amplitude + c

# Formule 6 : Delta dual (R² + amplitude) PROPRES
def formula_delta_dual(r2, amplitude, k1, k2):
    """amp = amp_ref + k1×(R²-R²_ref) + k2×(amp-amp_ref)"""
    return ref_amp + k1 * (r2 - ref_r2) + k2 * (amplitude - ref_amplitude)

# Formule 8 : Avec durée tendance PROPRE
def formula_with_duration(r2, amplitude, duration, a, b, c):
    """amp = a × R² + b × amplitude + c × durée"""
    return a * r2 + b * amplitude + c * duration

# Formule 9 : Score force tendance
def formula_strength_score(r2, amplitude, strength_score, k):
    """amp = amp_ref + k × (strength_score - 50)"""
    return ref_amp + k * (strength_score - 50)  # Centeré sur 50

# Formule 7 : Inverse (hypothèse tendance forte → amp faible)
def formula_inverse(r2, amplitude, a, b):
    """amp = a / (R² + 0.1) + b"""
    return a / (r2 + 0.1) + b

# Liste formules
formulas = [
    AmplificationFormula(
        "F1: Linéaire simple",
        formula_linear,
        2,
        ['a', 'b'],
        bounds=[(0, 10), (0, 5)]
    ),
    AmplificationFormula(
        "F2: Ratio proportionnel",
        formula_ratio,
        1,
        ['k'],
        bounds=[(0.1, 3)]
    ),
    AmplificationFormula(
        "F3: Delta additive",
        formula_delta,
        1,
        ['k'],
        bounds=[(-5, 5)]
    ),
    AmplificationFormula(
        "F4: Exponentielle",
        formula_exp,
        1,
        ['k'],
        bounds=[(-5, 5)]
    ),
    AmplificationFormula(
        "F5: Linéaire dual (R²+amplitude)",
        formula_linear_dual,
        3,
        ['a', 'b', 'c'],
        bounds=[(0, 10), (-0.1, 0.1), (0, 5)]
    ),
    AmplificationFormula(
        "F6: Delta dual",
        formula_delta_dual,
        2,
        ['k1', 'k2'],
        bounds=[(-10, 10), (-0.1, 0.1)]
    ),
    AmplificationFormula(
        "F7: Inverse (tendance forte → amp faible)",
        formula_inverse,
        2,
        ['a', 'b'],
        bounds=[(0, 10), (0, 5)]
    ),
]

print(f"\n✅ Défini {len(formulas)} formules candidates :\n")
for i, formula in enumerate(formulas, 1):
    print(f"   {i}. {formula.name}")
    print(f"      Paramètres : {', '.join(formula.param_names)}")

# ============================================================================
# ÉTAPE 3 : FILTRAGE DATASET CALIBRATION
# ============================================================================

print("\n📊 ÉTAPE 3 : Filtrage dataset calibration")
print("-" * 80)

# Filtrer clusters similaires (9-11 events, score 43-46)
df_calib = df[
    (df['num_events_real'] >= 9) &
    (df['num_events_real'] <= 11) &
    (df['base_score_real'] >= 43) &
    (df['base_score_real'] <= 46)
].copy()

# Supprimer lignes avec valeurs manquantes (métriques PROPRES)
df_calib = df_calib.dropna(subset=['trend_r2_proper', 'trend_amplitude_proper', 'amp_parfaite'])

print(f"✅ Dataset calibration : {len(df_calib)} clusters similaires")
print(f"   (filtré de {len(df)} total)")

if len(df_calib) < 10:
    print(f"\n⚠️  ATTENTION : Seulement {len(df_calib)} points calibration")
    print("   Risque de surapprentissage élevé")

# ============================================================================
# ÉTAPE 4 : CALIBRATION PARAMÈTRES
# ============================================================================

print("\n📐 ÉTAPE 4 : Calibration paramètres (scipy.optimize)")
print("-" * 80)

def objective_function(params, formula_func, r2_data, amp_data, amp_target):
    """Fonction objectif : MAE à minimiser"""
    amp_pred = formula_func(r2_data, amp_data, *params)
    # Contraindre amp entre 0.5 et 5.0
    amp_pred = np.clip(amp_pred, 0.5, 5.0)
    return np.mean(np.abs(amp_pred - amp_target))

print("\nCalibration en cours...\n")

for formula in formulas:
    
    print(f"🔧 {formula.name}")
    
    # Données calibration (métriques PROPRES)
    r2_calib = df_calib['trend_r2_proper'].values
    amp_calib = df_calib['trend_amplitude_proper'].values
    target_calib = df_calib['amp_parfaite'].values
    
    # Initial guess
    if formula.n_params == 1:
        x0 = [1.0]
    elif formula.n_params == 2:
        x0 = [1.0, 1.0]
    else:
        x0 = [1.0] * formula.n_params
    
    try:
        # Optimisation
        result = minimize(
            objective_function,
            x0,
            args=(formula.func, r2_calib, amp_calib, target_calib),
            bounds=formula.bounds,
            method='L-BFGS-B'
        )
        
        formula.params = result.x
        
        # Calculer métriques calibration
        amp_pred_calib = formula.func(r2_calib, amp_calib, *formula.params)
        amp_pred_calib = np.clip(amp_pred_calib, 0.5, 5.0)
        
        mae_calib = np.mean(np.abs(amp_pred_calib - target_calib))
        rmse_calib = np.sqrt(np.mean((amp_pred_calib - target_calib) ** 2))
        
        print(f"   ✅ Paramètres : {', '.join([f'{name}={val:.3f}' for name, val in zip(formula.param_names, formula.params)])}")
        print(f"   MAE calibration : {mae_calib:.3f}")
        
    except Exception as e:
        print(f"   ❌ Échec calibration : {e}")
        formula.params = None

print("\n✅ Calibration terminée")

# ============================================================================
# ÉTAPE 5 : TEST SUR TOUS LES CLUSTERS
# ============================================================================

print("\n📊 ÉTAPE 5 : Test sur TOUS les clusters")
print("-" * 80)

# Dataset test = TOUS les clusters avec données complètes (métriques PROPRES)
df_test = df.dropna(subset=['trend_r2_proper', 'trend_amplitude_proper', 'amp_parfaite'])

print(f"✅ Dataset test : {len(df_test)} clusters")

# Baseline amp=2.5
baseline_pred = np.full(len(df_test), 2.5)
baseline_mae = np.mean(np.abs(baseline_pred - df_test['amp_parfaite'].values))
baseline_rmse = np.sqrt(np.mean((baseline_pred - df_test['amp_parfaite'].values) ** 2))

print(f"\n📊 BASELINE amp=2.5 fixe :")
print(f"   MAE  : {baseline_mae:.3f}")
print(f"   RMSE : {baseline_rmse:.3f}")

print(f"\n📊 TEST FORMULES :\n")

results = []

for formula in formulas:
    
    if formula.params is None:
        print(f"⚠️  {formula.name:40} : Non calibré")
        continue
    
    # Prédiction (métriques PROPRES)
    r2_test = df_test['trend_r2_proper'].values
    amp_test = df_test['trend_amplitude_proper'].values
    target_test = df_test['amp_parfaite'].values
    
    try:
        amp_pred = formula.func(r2_test, amp_test, *formula.params)
        amp_pred = np.clip(amp_pred, 0.5, 5.0)
        
        # Métriques
        mae = np.mean(np.abs(amp_pred - target_test))
        rmse = np.sqrt(np.mean((amp_pred - target_test) ** 2))
        corr = np.corrcoef(amp_pred, target_test)[0, 1]
        
        formula.mae = mae
        formula.rmse = rmse
        formula.corr = corr
        
        # Amélioration vs baseline
        improvement = ((baseline_mae - mae) / baseline_mae) * 100
        
        # Status
        if mae < baseline_mae and improvement > 10:
            status = "✅✅"
        elif mae < baseline_mae:
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {formula.name:40}")
        print(f"   MAE={mae:.3f} (vs baseline {baseline_mae:.3f}, {improvement:+.1f}%)")
        print(f"   RMSE={rmse:.3f}, Corr={corr:+.3f}")
        
        results.append({
            'formula': formula,
            'mae': mae,
            'rmse': rmse,
            'corr': corr,
            'improvement': improvement
        })
        
    except Exception as e:
        print(f"❌ {formula.name:40} : Erreur test - {e}")

# ============================================================================
# ÉTAPE 6 : SÉLECTION MEILLEURE FORMULE
# ============================================================================

print("\n" + "=" * 80)
print("SÉLECTION MEILLEURE FORMULE")
print("=" * 80)

if len(results) == 0:
    print("\n❌ ÉCHEC : Aucune formule testable")
    sys.exit(1)

# Trier par MAE
results_sorted = sorted(results, key=lambda x: x['mae'])
best = results_sorted[0]

print(f"\n🏆 MEILLEURE FORMULE : {best['formula'].name}")
print(f"\n   Équation : {best['formula'].name}")

# Afficher équation avec paramètres
formula_obj = best['formula']
if formula_obj.name == "F1: Linéaire simple":
    a, b = formula_obj.params
    print(f"   amp = {a:.3f} × R² + {b:.3f}")
    
elif formula_obj.name == "F2: Ratio proportionnel":
    k = formula_obj.params[0]
    print(f"   amp = {ref_amp:.3f} × (R² / {ref_r2:.3f})^{k:.3f}")
    
elif formula_obj.name == "F3: Delta additive":
    k = formula_obj.params[0]
    print(f"   amp = {ref_amp:.3f} + {k:.3f} × (R² - {ref_r2:.3f})")
    
elif formula_obj.name == "F4: Exponentielle":
    k = formula_obj.params[0]
    print(f"   amp = {ref_amp:.3f} × exp({k:.3f} × (R² - {ref_r2:.3f}))")
    
elif formula_obj.name == "F5: Linéaire dual (R²+amplitude)":
    a, b, c = formula_obj.params
    print(f"   amp = {a:.3f} × R² + {b:.4f} × amplitude + {c:.3f}")
    
elif formula_obj.name == "F6: Delta dual":
    k1, k2 = formula_obj.params
    print(f"   amp = {ref_amp:.3f} + {k1:.3f}×(R²-{ref_r2:.3f}) + {k2:.4f}×(amp-{ref_amplitude:.1f})")
    
elif formula_obj.name == "F7: Inverse (tendance forte → amp faible)":
    a, b = formula_obj.params
    print(f"   amp = {a:.3f} / (R² + 0.1) + {b:.3f}")

print(f"\n   Métriques :")
print(f"   - MAE                : {best['mae']:.3f}")
print(f"   - RMSE               : {best['rmse']:.3f}")
print(f"   - Corrélation        : {best['corr']:+.3f}")
print(f"   - vs Baseline (2.5)  : {best['improvement']:+.1f}%")

# ============================================================================
# ÉTAPE 7 : DÉCISION FINALE
# ============================================================================

print("\n" + "=" * 80)
print("DÉCISION FINALE")
print("=" * 80)

# Critères décision
mae_threshold = baseline_mae * 0.9  # 10% mieux que baseline
corr_threshold = 0.5

if best['mae'] < mae_threshold and best['corr'] > corr_threshold:
    decision = "VALIDÉE"
    print(f"\n✅✅ FORMULE VALIDÉE")
    print(f"\n   Critères satisfaits :")
    print(f"   ✅ MAE < baseline × 0.9 ({best['mae']:.3f} < {mae_threshold:.3f})")
    print(f"   ✅ Corrélation > 0.5 ({best['corr']:.3f})")
    print(f"\n   Amélioration : {best['improvement']:.1f}%")
    
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
    
    print(f"\n   RECOMMANDATION : Tester en production avec monitoring strict")
    
else:
    decision = "REJETÉE"
    print(f"\n❌ FORMULE REJETÉE")
    print(f"\n   Aucune amélioration vs baseline")
    print(f"   MAE formule : {best['mae']:.3f}")
    print(f"   MAE baseline: {baseline_mae:.3f}")
    print(f"   Dégradation : {best['improvement']:.1f}%")
    
    print(f"\n   RECOMMANDATION : Rester avec baseline amp=2.5")

# ============================================================================
# RÉSUMÉ COMPARATIF
# ============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ COMPARATIF TOUTES FORMULES")
print("=" * 80)

print(f"\n{'Formule':<40} {'MAE':>8} {'Amélioration':>12} {'Corr':>8}")
print("-" * 80)
print(f"{'BASELINE amp=2.5':<40} {baseline_mae:>8.3f} {'0.0%':>12} {'N/A':>8}")

for res in results_sorted:
    print(f"{res['formula'].name:<40} {res['mae']:>8.3f} {res['improvement']:>11.1f}% {res['corr']:>8.3f}")

print("\n" + "=" * 80)
print("FIN CALIBRATION")
print("=" * 80)

# Export formule gagnante
if decision in ["VALIDÉE", "PARTIELLE"]:
    print(f"\n💾 Formule sélectionnée :")
    print(f"   Nom : {best['formula'].name}")
    print(f"   Paramètres : {best['formula'].params}")
    print(f"   MAE : {best['mae']:.3f}")
    print(f"   Amélioration : {best['improvement']:.1f}%")
