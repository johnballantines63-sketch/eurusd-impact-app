#!/usr/bin/env python3
"""
SESSION 125 - ÉTAPE 8 : CALIBRATION FONCTION AMPLIFICATION(R²)
===============================================================
Calibre la fonction amplification = f(R²) basée sur 29 clusters CPI

Workflow :
1. Charger résultats Étape 7 (R² pour chaque cluster)
2. Pour chaque cluster : calculer amplification idéale
3. Modéliser amplification = f(R²)
4. Valider qualité fit
5. Sauvegarder fonction calibrée
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import json
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_absolute_error
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import matplotlib.pyplot as plt

print("="*80)
print("SESSION 125 - ÉTAPE 8 : CALIBRATION AMPLIFICATION(R²)")
print("="*80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
TRENDS_PATH = Path(__file__).parent / "trend_analysis" / "trend_analysis_final.csv"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "calibration_results"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📁 Tendances : {TRENDS_PATH}")
print(f"📁 Scores : {SCORES_PATH}")
print()

# ============================================================================
# ÉTAPE 1 : CHARGER DONNÉES
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT DONNÉES")
print("="*80)
print()

# Charger résultats Étape 7
df_trends = pd.read_csv(TRENDS_PATH)
print(f"✅ {len(df_trends)} clusters avec tendances")
print()

# Charger scores empiriques
df_scores = pd.read_csv(SCORES_PATH)
print(f"✅ {len(df_scores)} familles avec scores")
print()

# ============================================================================
# ÉTAPE 2 : CALCULER AMPLIFICATION IDÉALE POUR CHAQUE CLUSTER
# ============================================================================

print("="*80)
print("ÉTAPE 2 : CALCUL AMPLIFICATIONS IDÉALES")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

calibration_data = []

for idx, row in df_trends.iterrows():
    cluster_time = pd.to_datetime(row['cluster_time'])
    impact_measured = row['impact_measured']
    trend_r2 = row['trend_r2']
    
    if pd.isna(impact_measured) or pd.isna(trend_r2):
        continue
    
    print(f"🔍 [{idx+1}/{len(df_trends)}] {cluster_time.date()} ... ", end='')
    
    # Charger événements cluster (±5 min)
    cluster_time_utc = cluster_time.tz_localize(None) if cluster_time.tzinfo else cluster_time
    
    time_start = cluster_time_utc - pd.Timedelta(minutes=5)
    time_end = cluster_time_utc + pd.Timedelta(minutes=5)
    
    try:
        df_events = conn.execute("""
            SELECT event_name, country
            FROM economic_events
            WHERE datetime_utc >= ? AND datetime_utc <= ?
              AND importance = 'HIGH'
        """, [str(time_start), str(time_end)]).df()
        
        if len(df_events) == 0:
            print("⚠️  Pas d'événements")
            continue
        
        # Mapper scores
        df_events = df_events.merge(
            df_scores[['event_name', 'country', 'empirical_score', 'sample_size']],
            on=['event_name', 'country'],
            how='left'
        )
        
        df_measurable = df_events[
            df_events['sample_size'].notna() & (df_events['sample_size'] > 0)
        ]
        
        if len(df_measurable) == 0:
            print("⚠️  Pas de scores")
            continue
        
        # Calculer amplification idéale
        total_score = df_measurable['empirical_score'].sum()
        n_events = len(df_measurable)
        surprise_factor = 1.0  # Pas de données actual/forecast
        
        # Formule : impact = score × amp × sqrt(n) × surprise
        # Donc : amp = impact / (score × sqrt(n) × surprise)
        
        denominator = total_score * np.sqrt(n_events) * surprise_factor
        
        if denominator > 0:
            amplification_ideal = impact_measured / denominator
            
            calibration_data.append({
                'cluster_time': str(cluster_time),
                'trend_r2': float(trend_r2),
                'impact_measured': float(impact_measured),
                'total_score': float(total_score),
                'n_events': int(n_events),
                'amplification_ideal': float(amplification_ideal),
                'trend_duration_hours': float(row['trend_duration_hours'])
            })
            
            print(f"✅ R²={trend_r2:.4f} → amp={amplification_ideal:.4f}")
        else:
            print("⚠️  Dénominateur=0")
            
    except Exception as e:
        print(f"❌ {str(e)[:40]}")

conn.close()

print()
print(f"✅ {len(calibration_data)} cas calibrés")
print()

if len(calibration_data) < 5:
    print("❌ Pas assez de données pour calibration")
    sys.exit(1)

# ============================================================================
# ÉTAPE 3 : MODÉLISATION AMPLIFICATION = f(R²)
# ============================================================================

print("="*80)
print("ÉTAPE 3 : MODÉLISATION f(R²)")
print("="*80)
print()

df_calib = pd.DataFrame(calibration_data)

# Données pour fit
X = df_calib['trend_r2'].values
y = df_calib['amplification_ideal'].values

print(f"📊 Données calibration :")
print(f"   N = {len(X)}")
print(f"   R² min = {X.min():.4f}, max = {X.max():.4f}")
print(f"   Amp min = {y.min():.4f}, max = {y.max():.4f}")
print()

# Tester plusieurs modèles
models = {}

# 1. Modèle linéaire : amp = a + b*R²
def linear_model(r2, a, b):
    return a + b * r2

try:
    popt_lin, _ = curve_fit(linear_model, X, y)
    y_pred_lin = linear_model(X, *popt_lin)
    r2_lin = r2_score(y, y_pred_lin)
    mae_lin = mean_absolute_error(y, y_pred_lin)
    
    models['linear'] = {
        'func': linear_model,
        'params': popt_lin,
        'r2': r2_lin,
        'mae': mae_lin,
        'formula': f"amp = {popt_lin[0]:.6f} + {popt_lin[1]:.6f} × R²"
    }
    
    print(f"✅ Modèle linéaire :")
    print(f"   {models['linear']['formula']}")
    print(f"   R² fit = {r2_lin:.4f}")
    print(f"   MAE = {mae_lin:.6f}")
    print()
except Exception as e:
    print(f"⚠️  Modèle linéaire échoué : {e}")

# 2. Modèle quadratique : amp = a + b*R² + c*R²²
def quadratic_model(r2, a, b, c):
    return a + b * r2 + c * r2**2

try:
    popt_quad, _ = curve_fit(quadratic_model, X, y)
    y_pred_quad = quadratic_model(X, *popt_quad)
    r2_quad = r2_score(y, y_pred_quad)
    mae_quad = mean_absolute_error(y, y_pred_quad)
    
    models['quadratic'] = {
        'func': quadratic_model,
        'params': popt_quad,
        'r2': r2_quad,
        'mae': mae_quad,
        'formula': f"amp = {popt_quad[0]:.6f} + {popt_quad[1]:.6f}×R² + {popt_quad[2]:.6f}×R²²"
    }
    
    print(f"✅ Modèle quadratique :")
    print(f"   {models['quadratic']['formula']}")
    print(f"   R² fit = {r2_quad:.4f}")
    print(f"   MAE = {mae_quad:.6f}")
    print()
except Exception as e:
    print(f"⚠️  Modèle quadratique échoué : {e}")

# 3. Modèle logarithmique : amp = a + b*log(R²+0.01)
def log_model(r2, a, b):
    return a + b * np.log(r2 + 0.01)

try:
    popt_log, _ = curve_fit(log_model, X, y)
    y_pred_log = log_model(X, *popt_log)
    r2_log = r2_score(y, y_pred_log)
    mae_log = mean_absolute_error(y, y_pred_log)
    
    models['logarithmic'] = {
        'func': log_model,
        'params': popt_log,
        'r2': r2_log,
        'mae': mae_log,
        'formula': f"amp = {popt_log[0]:.6f} + {popt_log[1]:.6f} × log(R²+0.01)"
    }
    
    print(f"✅ Modèle logarithmique :")
    print(f"   {models['logarithmic']['formula']}")
    print(f"   R² fit = {r2_log:.4f}")
    print(f"   MAE = {mae_log:.6f}")
    print()
except Exception as e:
    print(f"⚠️  Modèle logarithmique échoué : {e}")

# Choisir meilleur modèle
if models:
    best_model_name = max(models, key=lambda k: models[k]['r2'])
    best_model = models[best_model_name]
    
    print("="*80)
    print(f"🏆 MEILLEUR MODÈLE : {best_model_name.upper()}")
    print("="*80)
    print()
    print(f"   Formule : {best_model['formula']}")
    print(f"   R² fit  : {best_model['r2']:.4f}")
    print(f"   MAE     : {best_model['mae']:.6f}")
    print()

# ============================================================================
# ÉTAPE 4 : VISUALISATION
# ============================================================================

print("="*80)
print("ÉTAPE 4 : VISUALISATION")
print("="*80)
print()

if models:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1 : R² → Amplification
    ax1.scatter(X, y, alpha=0.6, s=100, label='Données réelles')
    
    x_smooth = np.linspace(X.min(), X.max(), 100)
    for name, model in models.items():
        y_smooth = model['func'](x_smooth, *model['params'])
        ax1.plot(x_smooth, y_smooth, label=f"{name} (R²={model['r2']:.3f})", linewidth=2)
    
    ax1.set_xlabel('R² Tendance', fontsize=12)
    ax1.set_ylabel('Amplification idéale', fontsize=12)
    ax1.set_title('Calibration : Amplification = f(R²)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2 : Impact prédit vs réel
    y_pred_best = best_model['func'](X, *best_model['params'])
    
    # Recalculer impacts prédits
    impacts_pred = []
    for _, row in df_calib.iterrows():
        amp_pred = best_model['func'](row['trend_r2'], *best_model['params'])
        impact_pred = row['total_score'] * amp_pred * np.sqrt(row['n_events'])
        impacts_pred.append(impact_pred)
    
    impacts_pred = np.array(impacts_pred)
    impacts_real = df_calib['impact_measured'].values
    
    ax2.scatter(impacts_real, impacts_pred, alpha=0.6, s=100)
    
    # Ligne identité
    max_val = max(impacts_real.max(), impacts_pred.max())
    ax2.plot([0, max_val], [0, max_val], 'r--', label='Parfait', linewidth=2)
    
    ax2.set_xlabel('Impact réel (pips)', fontsize=12)
    ax2.set_ylabel('Impact prédit (pips)', fontsize=12)
    ax2.set_title(f'Validation : R²={r2_score(impacts_real, impacts_pred):.3f}', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    plot_path = OUTPUT_DIR / "calibration_amplification_r2.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Graphique sauvegardé : {plot_path.name}")
    print()

# ============================================================================
# ÉTAPE 5 : SAUVEGARDER FONCTION CALIBRÉE
# ============================================================================

print("="*80)
print("ÉTAPE 5 : SAUVEGARDE")
print("="*80)
print()

if models:
    calibration_results = {
        'method': 'Calibration sur 29 clusters CPI identiques',
        'models': {
            name: {
                'formula': model['formula'],
                'parameters': model['params'].tolist(),
                'r2_fit': float(model['r2']),
                'mae': float(model['mae'])
            }
            for name, model in models.items()
        },
        'best_model': {
            'name': best_model_name,
            'formula': best_model['formula'],
            'parameters': best_model['params'].tolist()
        },
        'calibration_data': calibration_data,
        'statistics': {
            'n_samples': len(calibration_data),
            'r2_range': [float(X.min()), float(X.max())],
            'amp_range': [float(y.min()), float(y.max())],
            'correlation_r2_impact': float(df_calib['trend_r2'].corr(df_calib['impact_measured']))
        }
    }
    
    output_json = OUTPUT_DIR / "amplification_function_calibrated.json"
    with open(output_json, 'w') as f:
        json.dump(calibration_results, f, indent=2)
    
    print(f"💾 JSON : {output_json.name}")
    
    # CSV résumé
    df_calib.to_csv(OUTPUT_DIR / "calibration_data.csv", index=False)
    print(f"💾 CSV : calibration_data.csv")
    print()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("="*80)
print("RÉSUMÉ CALIBRATION")
print("="*80)
print()

print(f"📊 Échantillons : {len(calibration_data)}")
print()

if models:
    print(f"🏆 Meilleur modèle : {best_model_name}")
    print(f"   {best_model['formula']}")
    print()
    
    print(f"📈 Exemples prédiction :")
    for r2_test in [0.1, 0.3, 0.5, 0.7, 0.9]:
        amp_pred = best_model['func'](r2_test, *best_model['params'])
        print(f"   R² = {r2_test:.1f} → amp = {amp_pred:.4f}")
    print()

print("="*80)
print("ÉTAPE 8 TERMINÉE ✅")
print("="*80)
print()

print("🎯 PROCHAINE ÉTAPE :")
print("   9. Intégrer fonction dans Planificateur")
print("   10. Tester sur nouveaux événements")
