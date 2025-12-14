"""
ÉTAPE 3 : OPTIMISATION AMPLIFICATION DYNAMIQUE (SESSION 101) - CORRIGÉ
=======================================================================

Objectif : Trouver amplification optimale pour chaque date et créer formule dynamique

CORRECTION : Utiliser impact_pips_x (du CSV impacts, pas R²)

Date : 30 octobre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from scipy.optimize import minimize_scalar

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

print("="*80)
print("🎯 ÉTAPE 3 : OPTIMISATION AMPLIFICATION DYNAMIQUE (SESSION 101)")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"
SCRIPTS_DIR = Path(__file__).parent

# Fichiers input
IMPACTS_FILE = project_root / "eurusd_clean" / "scripts" / "session99" / "real_impacts_TIMEZONE_FIX_FINAL.csv"
R2_FILE = SCRIPTS_DIR / "r2_72h_results.csv"

print(f"\n📂 FICHIERS INPUT :")
print(f"   Impacts réels : {IMPACTS_FILE}")
print(f"   R² 72h        : {R2_FILE}")
print(f"   Base données  : {DB_PATH}")

# Vérifier fichiers
if not IMPACTS_FILE.exists():
    print(f"\n❌ ERREUR : {IMPACTS_FILE} n'existe pas")
    sys.exit(1)

if not R2_FILE.exists():
    print(f"\n❌ ERREUR : {R2_FILE} n'existe pas")
    sys.exit(1)

# ============================================================================
# CHARGEMENT DONNÉES
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 1 : Chargement données")
print(f"{'='*80}\n")

# Charger impacts réels
df_impacts = pd.read_csv(IMPACTS_FILE)
print(f"✅ {len(df_impacts)} impacts réels chargés")

# Dédupliquer
df_impacts = df_impacts.drop_duplicates(subset=['date'], keep='first')
print(f"✅ {len(df_impacts)} dates uniques après déduplication")

# Charger R² 72h
df_r2 = pd.read_csv(R2_FILE)
print(f"✅ {len(df_r2)} valeurs R² 72h chargées")

# Merger (colonnes dupliquées → _x, _y)
df_data = df_impacts.merge(df_r2[['date', 'r_squared_72h']], on='date', how='inner')
print(f"✅ {len(df_data)} dates avec impacts ET R² disponibles")

print(f"\n📋 Aperçu données :")
print(df_data[['date', 'impact_pips', 'r_squared_72h']].head(10).to_string(index=False))

# ============================================================================
# FONCTIONS PLANIFICATEUR
# ============================================================================

def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

def load_high_impact_events(date_str: str, conn) -> pd.DataFrame:
    """Charge événements HIGH (score > 40) comme Planificateur V2.6"""
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        e.actual,
        e.estimate,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query, [date_str]).df()
    return df_events

def calculate_planificateur_prediction(events_df: pd.DataFrame, amplification: float) -> float:
    """
    Calcule prédiction Planificateur V2.6 avec amplification donnée
    RÉPLIQUE EXACTE de calculate_planificateur_v26_prediction() Session 99
    """
    if events_df.empty:
        return 0.0
    
    # 1. Score moyen
    base_score_avg = events_df['empirical_score'].mean()
    
    # 2. Surprise MAX
    max_surprise = 0
    for _, event in events_df.iterrows():
        if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
            surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    # 3. Score ajusté (Session 55)
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score_avg,
        surprise_pct=max_surprise
    )
    
    # 4. Impact avec MULTI-EVENTS (Session 51)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(events_df),
        amplification=amplification
    )
    
    return impact

def find_optimal_amplification(events_df: pd.DataFrame, impact_real: float) -> dict:
    """Trouve amplification optimale minimisant erreur Planificateur"""
    def objective(amp):
        impact_pred = calculate_planificateur_prediction(events_df, amp)
        error = abs(impact_pred - impact_real)
        return error
    
    # Optimisation entre 0.5 et 5.0
    result = minimize_scalar(objective, bounds=(0.5, 5.0), method='bounded')
    
    amp_optimal = result.x
    error_optimal = result.fun
    
    # Calculer aussi erreur baseline (amp=2.5)
    impact_baseline = calculate_planificateur_prediction(events_df, 2.5)
    error_baseline = abs(impact_baseline - impact_real)
    
    return {
        'amp_optimal': amp_optimal,
        'error_optimal': error_optimal,
        'impact_pred_optimal': calculate_planificateur_prediction(events_df, amp_optimal),
        'error_baseline': error_baseline,
        'impact_pred_baseline': impact_baseline
    }

# ============================================================================
# PHASE 2 : OPTIMISATION PAR DATE
# ============================================================================

print(f"\n{'='*80}")
print(f"🔧 PHASE 2 : Optimisation amplification par date")
print(f"{'='*80}\n")

conn = get_db_connection()

results = []
errors = []

for idx, row in df_data.iterrows():
    date_str = row['date']
    impact_real = row['impact_pips']
    r_squared_72h = row['r_squared_72h']
    
    print(f"\n[{idx+1}/{len(df_data)}] {date_str}")
    print(f"   Impact réel : {impact_real:.1f} pips")
    print(f"   R² 72h      : {r_squared_72h:.3f}")
    
    # Charger événements
    events = load_high_impact_events(date_str, conn)
    
    if events.empty:
        print(f"   ❌ Aucun événement HIGH trouvé")
        errors.append({'date': date_str, 'error': 'NO_EVENTS'})
        continue
    
    print(f"   ✅ {len(events)} événement(s) HIGH chargé(s)")
    
    # Optimiser amplification
    opt_result = find_optimal_amplification(events, impact_real)
    
    amp_optimal = opt_result['amp_optimal']
    error_optimal = opt_result['error_optimal']
    error_baseline = opt_result['error_baseline']
    
    print(f"   🎯 Amp OPTIMALE  : {amp_optimal:.3f}")
    print(f"   📊 Impact prédit : {opt_result['impact_pred_optimal']:.1f} pips")
    print(f"   ✅ Erreur (opt)  : {error_optimal:.1f} pips")
    print(f"   📊 Erreur (2.5)  : {error_baseline:.1f} pips")
    
    if error_optimal < error_baseline:
        gain = error_baseline - error_optimal
        print(f"   💚 Optimale MEILLEURE : -{gain:.1f} pips")
    elif abs(error_optimal - error_baseline) < 0.1:
        print(f"   ⚪ Optimale = Baseline (amp=2.5 déjà optimal)")
    else:
        loss = error_optimal - error_baseline
        print(f"   🔴 Baseline MEILLEURE : +{loss:.1f} pips")
    
    results.append({
        'date': date_str,
        'impact_real': impact_real,
        'r_squared_72h': r_squared_72h,
        'num_events': len(events),
        'amp_optimal': amp_optimal,
        'impact_pred_optimal': opt_result['impact_pred_optimal'],
        'error_optimal': error_optimal,
        'amp_baseline': 2.5,
        'impact_pred_baseline': opt_result['impact_pred_baseline'],
        'error_baseline': error_baseline,
        'gain_vs_baseline': error_baseline - error_optimal
    })

conn.close()

# ============================================================================
# PHASE 3 : RÉGRESSION R² vs AMP OPTIMALE
# ============================================================================

print(f"\n{'='*80}")
print(f"📈 PHASE 3 : Régression R² 72h vs Amplification Optimale")
print(f"{'='*80}\n")

df_results = pd.DataFrame(results)

if len(df_results) == 0:
    print(f"❌ ERREUR : Aucun résultat disponible")
    sys.exit(1)

x = df_results['r_squared_72h'].values
y = df_results['amp_optimal'].values

# Corrélation
corr = np.corrcoef(x, y)[0, 1]
print(f"📊 Corrélation R² vs Amp Optimale : {corr:.3f}")

# Régression linéaire
x_mean = np.mean(x)
y_mean = np.mean(y)

numerator = np.sum((x - x_mean) * (y - y_mean))
denominator = np.sum((x - x_mean) ** 2)

if denominator == 0:
    print(f"\n❌ ERREUR : Impossible de calculer régression (variance R² nulle)")
    sys.exit(1)

a = numerator / denominator
b = y_mean - a * x_mean

print(f"\n📐 NOUVELLE FORMULE (calibrée Session 101) :")
print(f"   amplification = {a:.4f} × R²_72h + {b:.4f}")

print(f"\n📐 ANCIENNE FORMULE (Session 98 - impacts faux) :")
print(f"   amplification = 1.9938 × R²_72h + 1.4448")

# ============================================================================
# PHASE 4 : TEST NOUVELLE FORMULE VS BASELINE
# ============================================================================

print(f"\n{'='*80}")
print(f"🧪 PHASE 4 : Test nouvelle formule vs BASELINE amp=2.5")
print(f"{'='*80}\n")

conn = get_db_connection()

errors_new = []
errors_baseline = []

for _, row in df_data.iterrows():
    date_str = row['date']
    impact_real = row['impact_pips']
    r_squared_72h = row['r_squared_72h']
    
    events = load_high_impact_events(date_str, conn)
    if events.empty:
        continue
    
    # Nouvelle formule dynamique
    amp_new = a * r_squared_72h + b
    impact_pred_new = calculate_planificateur_prediction(events, amp_new)
    error_new = abs(impact_pred_new - impact_real)
    errors_new.append(error_new)
    
    # Baseline amp=2.5
    impact_pred_baseline = calculate_planificateur_prediction(events, 2.5)
    error_baseline = abs(impact_pred_baseline - impact_real)
    errors_baseline.append(error_baseline)

conn.close()

# Statistiques globales
mae_new = np.mean(errors_new)
mae_baseline = np.mean(errors_baseline)

print(f"📊 RÉSULTATS GLOBAUX ({len(errors_new)} dates) :\n")
print(f"   MAE BASELINE (amp=2.5)    : {mae_baseline:.2f} pips")
print(f"   MAE NOUVELLE (dynamique)  : {mae_new:.2f} pips")
print()

if mae_new < mae_baseline:
    improvement = ((mae_baseline - mae_new) / mae_baseline) * 100
    print(f"   ✅ AMÉLIORATION vs BASELINE : {improvement:.1f}%")
    
    if improvement > 10:
        print(f"   ✅✅ AMÉLIORATION SIGNIFICATIVE (>10%) → VALIDER formule dynamique")
    else:
        print(f"   ⚠️  AMÉLIORATION MODESTE (<10%) → Considérer garder amp=2.5")
else:
    degradation = ((mae_new - mae_baseline) / mae_baseline) * 100
    print(f"   ❌ DÉGRADATION vs BASELINE : +{degradation:.1f}%")
    print(f"   → REJETER formule dynamique, GARDER amp=2.5")

# ============================================================================
# PHASE 5 : SAUVEGARDE
# ============================================================================

print(f"\n{'='*80}")
print(f"💾 PHASE 5 : Sauvegarde résultats")
print(f"{'='*80}\n")

# Sauvegarder résultats détaillés
output_results = SCRIPTS_DIR / "step3_optimization_results.csv"
df_results.to_csv(output_results, index=False)
print(f"✅ Résultats détaillés : {output_results}")

# Sauvegarder formule
output_formula = SCRIPTS_DIR / "step3_formula_dynamique.txt"
with open(output_formula, 'w') as f:
    f.write("="*80 + "\n")
    f.write("FORMULE AMPLIFICATION DYNAMIQUE - SESSION 101\n")
    f.write("="*80 + "\n\n")
    f.write(f"amplification = {a:.4f} × R²_72h + {b:.4f}\n\n")
    f.write(f"Corrélation R² vs Amp Optimale : {corr:.3f}\n")
    f.write(f"MAE BASELINE (amp=2.5)         : {mae_baseline:.2f} pips\n")
    f.write(f"MAE NOUVELLE (dynamique)       : {mae_new:.2f} pips\n")
    
    if mae_new < mae_baseline:
        improvement = ((mae_baseline - mae_new) / mae_baseline) * 100
        f.write(f"AMÉLIORATION                   : {improvement:.1f}%\n\n")
        
        if improvement > 10:
            f.write("DÉCISION : ✅ VALIDER formule dynamique (amélioration >10%)\n")
        else:
            f.write("DÉCISION : ⚠️  Amélioration modeste (<10%), considérer garder amp=2.5\n")
    else:
        degradation = ((mae_new - mae_baseline) / mae_baseline) * 100
        f.write(f"DÉGRADATION                    : +{degradation:.1f}%\n\n")
        f.write("DÉCISION : ❌ REJETER formule dynamique, GARDER amp=2.5\n")

print(f"✅ Formule sauvegardée : {output_formula}")

# ============================================================================
# VALIDATION CAS RÉFÉRENCE
# ============================================================================

print(f"\n{'='*80}")
print(f"✅ VALIDATION CAS RÉFÉRENCE 11.09.2025")
print(f"{'='*80}\n")

ref_row = df_results[df_results['date'] == '2025-09-11']

if not ref_row.empty:
    ref = ref_row.iloc[0]
    
    print(f"📊 Impact réel                : {ref['impact_real']:.1f} pips")
    print(f"   R² 72h                     : {ref['r_squared_72h']:.3f}")
    print(f"   Amp optimale (scipy)       : {ref['amp_optimal']:.3f}")
    print(f"   Amp baseline               : 2.5")
    
    # Calculer amp dynamique avec formule
    amp_dynamic = a * ref['r_squared_72h'] + b
    print(f"   Amp dynamique (formule)    : {amp_dynamic:.3f}")
    
    print(f"\n📈 ERREURS :")
    print(f"   Optimale (scipy)  : {ref['error_optimal']:.1f} pips")
    print(f"   Baseline (2.5)    : {ref['error_baseline']:.1f} pips")
    
    if ref['error_baseline'] < 1:
        print(f"\n   ✅ Baseline validée : {ref['error_baseline']:.1f} pips (< 1 pip)")
else:
    print(f"⚠️ Date référence 2025-09-11 non trouvée")

print(f"\n{'='*80}")
print(f"✅ ÉTAPE 3 TERMINÉE")
print(f"{'='*80}")
