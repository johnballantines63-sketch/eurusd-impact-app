#!/usr/bin/env python3
"""
SESSION 107 - PHASE 2B CLUSTER #3 : ANALYSE COMPLÈTE R² 72H
========================================================================
Méthodologie complète Session 101 :
1. Calculer R² 72h (tendance AVANT événement)
2. Amplitude pré-événement (volatilité)
3. Durée/volatilité 72h
4. Régression : amp_optimal = f(surprise, R², amplitude, durée)
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import importlib.util
from datetime import datetime, timedelta

print("="*80)
print("SESSION 107 - PHASE 2B CLUSTER #3 : ANALYSE COMPLÈTE R² 72H")
print("="*80)
print()

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Load config - CHEMIN CORRIGÉ
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"  # ✅ CHEMIN CORRECT
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger résultats Phase 1
results_file = Path(__file__).parent.parent / "session106" / "phase1_cluster3_results_FINAL_CORRECTED.csv"
df = pd.read_csv(results_file)

print(f"✅ {len(df)} dates Cluster #3 chargées")
print()

# =============================================================================
# CALCUL R² 72H + AMPLITUDE + VOLATILITÉ
# =============================================================================

print("="*80)
print("CALCUL MÉTRIQUES PRÉ-ÉVÉNEMENT (72H)")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

metrics = []

for _, row in df.iterrows():
    date_str = row['date']
    
    print(f"📅 {date_str}")
    print("-"*80)
    
    # Timestamp événement (14:30 Bern → 12:30+02:00 DB)
    event_dt = pd.to_datetime(f"{date_str} 14:30:00+02:00")
    query_dt = event_dt - timedelta(hours=2)
    
    # Charger prix 72h AVANT l'événement
    start_dt = query_dt - timedelta(hours=72)
    
    query = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{start_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
      AND datetime < '{query_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).fetchdf()
    
    if len(df_prices) < 100:
        print(f"  ⚠️ Données insuffisantes : {len(df_prices)} points")
        print()
        continue
    
    print(f"  ✅ {len(df_prices)} bougies 1min chargées (72h)")
    
    # Convertir en numérique pour régression
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices['timestamp_numeric'] = (df_prices['datetime'] - df_prices['datetime'].iloc[0]).dt.total_seconds()
    
    # === 1. RÉGRESSION LINÉAIRE 72H (R²) ===
    X = df_prices['timestamp_numeric'].values
    y = df_prices['close'].values
    
    # Normaliser X
    X_mean = X.mean()
    X_std = X.std()
    X_norm = (X - X_mean) / X_std if X_std > 0 else X - X_mean
    
    # Régression
    X_norm_2d = X_norm.reshape(-1, 1)
    X_with_intercept = np.column_stack([np.ones(len(X_norm)), X_norm])
    
    try:
        coeffs = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
        intercept = coeffs[0]
        slope = coeffs[1]
        
        # Prédictions
        y_pred = intercept + slope * X_norm
        
        # R²
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - y.mean())**2)
        r2_72h = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        print(f"  📈 R² 72h : {r2_72h:.4f}")
        
    except Exception as e:
        print(f"  ❌ Erreur régression : {e}")
        r2_72h = 0
    
    # === 2. AMPLITUDE 72H (Volatilité) ===
    high_72h = df_prices['close'].max()
    low_72h = df_prices['close'].min()
    amplitude_72h = (high_72h - low_72h) * 10000  # en pips
    
    print(f"  📊 Amplitude 72h : {amplitude_72h:.2f} pips")
    
    # === 3. VOLATILITÉ (Écart-type) ===
    volatility_72h = df_prices['close'].std() * 10000  # en pips
    
    print(f"  📊 Volatilité 72h (std) : {volatility_72h:.2f} pips")
    
    # === 4. DIRECTION TENDANCE ===
    first_price = df_prices['close'].iloc[0]
    last_price = df_prices['close'].iloc[-1]
    trend_direction = 1 if last_price > first_price else -1
    trend_strength = abs(last_price - first_price) * 10000
    
    print(f"  📊 Tendance : {['DOWN','UP'][trend_direction>0]} ({trend_strength:.2f} pips)")
    
    print()
    
    # Stocker
    metrics.append({
        'date': date_str,
        'r2_72h': r2_72h,
        'amplitude_72h': amplitude_72h,
        'volatility_72h': volatility_72h,
        'trend_direction': trend_direction,
        'trend_strength': trend_strength,
        'num_points': len(df_prices)
    })

conn.close()

# =============================================================================
# FUSION AVEC RÉSULTATS PHASE 1
# =============================================================================

df_metrics = pd.DataFrame(metrics)
df_complete = df.merge(df_metrics, on='date', how='left')

print("="*80)
print("DONNÉES COMPLÈTES")
print("="*80)
print()

print(df_complete[['date', 'amp_optimal', 'max_surprise', 'r2_72h', 'amplitude_72h', 'volatility_72h']].to_string(index=False))
print()

# =============================================================================
# CORRÉLATIONS AVEC R² 72H
# =============================================================================

print("="*80)
print("CORRÉLATIONS amp_optimal vs MÉTRIQUES PRÉ-ÉVÉNEMENT")
print("="*80)
print()

# Variables à tester
new_vars = {
    'r2_72h': 'R² 72h',
    'amplitude_72h': 'Amplitude 72h (pips)',
    'volatility_72h': 'Volatilité 72h (pips)',
    'trend_strength': 'Force tendance (pips)'
}

correlations = {}

for var, label in new_vars.items():
    if var in df_complete.columns and not df_complete[var].isna().all():
        corr = df_complete['amp_optimal'].corr(df_complete[var])
        correlations[var] = corr
        
        # P-value
        n = len(df_complete[df_complete[var].notna()])
        if n > 2:
            t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2 + 1e-10)
            from scipy.stats import t as t_dist
            p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
        else:
            p_value = 1.0
        
        print(f"📊 {label} :")
        print(f"   Corrélation  : {corr:+.3f}")
        print(f"   P-value      : {p_value:.4f}")
        print(f"   Significatif : {'✅ Oui (p<0.05)' if p_value < 0.05 else '❌ Non (p≥0.05)'}")
        print()

# =============================================================================
# RÉGRESSION MULTIPLE COMPLÈTE
# =============================================================================

print("="*80)
print("RÉGRESSION MULTIPLE : TOUTES VARIABLES")
print("="*80)
print()

# Sélectionner features (sans NaN)
feature_cols = ['max_surprise', 'r2_72h', 'amplitude_72h', 'volatility_72h']
df_reg = df_complete[['amp_optimal', 'date'] + feature_cols].dropna()

print(f"Échantillon régression : {len(df_reg)} dates (après suppression NaN)")
print()

if len(df_reg) >= 3:
    X_multi = df_reg[feature_cols].values
    y_multi = df_reg['amp_optimal'].values
    
    # Régression
    X_with_intercept = np.column_stack([np.ones(len(X_multi)), X_multi])
    
    try:
        coeffs = np.linalg.lstsq(X_with_intercept, y_multi, rcond=None)[0]
        intercept = coeffs[0]
        betas = coeffs[1:]
        
        # Prédictions
        y_pred_multi = X_with_intercept @ coeffs
        
        # R² et MAE
        ss_res = np.sum((y_multi - y_pred_multi)**2)
        ss_tot = np.sum((y_multi - y_multi.mean())**2)
        r2_multi = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        mae_multi = np.mean(np.abs(y_multi - y_pred_multi))
        
        print("📊 Modèle : amp_optimal = β0 + β1×surprise + β2×R²_72h + β3×amplitude + β4×volatilité")
        print()
        print(f"Coefficients :")
        print(f"   Intercept (β0)      : {intercept:.4f}")
        for i, col in enumerate(feature_cols):
            print(f"   {col:20s} (β{i+1}) : {betas[i]:+.4f}")
        print()
        print(f"Métriques :")
        print(f"   R²              : {r2_multi:.3f}")
        print(f"   MAE             : {mae_multi:.3f}")
        print()
        
        # Prédictions par date
        df_reg['amp_predicted'] = y_pred_multi
        df_reg['amp_error'] = np.abs(df_reg['amp_predicted'] - df_reg['amp_optimal'])
        
        print("📊 Prédictions par date :")
        print("-"*80)
        for idx, row in df_reg.iterrows():
            print(f"   {row['date']} : "
                  f"amp_optimal={row['amp_optimal']:.3f} | "
                  f"predicted={row['amp_predicted']:.3f} | "
                  f"error={row['amp_error']:.3f}")
        print()
        
    except Exception as e:
        print(f"❌ Erreur régression : {e}")
        r2_multi = 0
        mae_multi = 999
        print()
else:
    print("❌ Échantillon trop petit pour régression")
    r2_multi = 0
    mae_multi = 999
    print()

# =============================================================================
# FORMULE SESSION 101 (RÉFÉRENCE)
# =============================================================================

print("="*80)
print("COMPARAISON AVEC FORMULE SESSION 101")
print("="*80)
print()

print("📊 Formule Session 101 (29 dates CPI) :")
print("   amplification = 0.5490 × R²_72h + 1.6988")
print("   MAE : 22.06 pips (vs 25.38 baseline)")
print("   Amélioration : 13.1%")
print()

# Appliquer formule Session 101 sur nos données
if 'r2_72h' in df_complete.columns:
    df_complete['amp_s101'] = 0.5490 * df_complete['r2_72h'] + 1.6988
    
    # Calculer erreur
    df_complete['error_s101'] = np.abs(df_complete['amp_s101'] - df_complete['amp_optimal'])
    
    mae_s101 = df_complete['error_s101'].mean()
    
    print(f"📊 Application Session 101 sur Cluster #3 :")
    print(f"   MAE : {mae_s101:.3f}")
    print()
    
    print("📊 Par date :")
    print("-"*80)
    for _, row in df_complete.iterrows():
        if pd.notna(row.get('r2_72h')):
            print(f"   {row['date']} : R²={row['r2_72h']:.4f} → "
                  f"amp_s101={row['amp_s101']:.3f} | "
                  f"amp_optimal={row['amp_optimal']:.3f} | "
                  f"error={row['error_s101']:.3f}")
    print()

# =============================================================================
# RECOMMANDATION FINALE
# =============================================================================

print("="*80)
print("RECOMMANDATION FINALE")
print("="*80)
print()

baseline_mae = df['error_baseline'].mean()

print("📊 Comparaison MAE :")
print(f"   Baseline fixe (amp=2.5)     : {baseline_mae:.2f} pips")
if 'mae_s101' in locals():
    print(f"   Formule Session 101 (R² seul) : {mae_s101:.2f} pips")
if r2_multi > 0:
    print(f"   Régression complète (4 vars)  : {mae_multi:.2f} pips")
print()

# Meilleure approche
best_approach = "Baseline 2.5"
best_mae = baseline_mae

if 'mae_s101' in locals() and mae_s101 < best_mae:
    best_approach = "Session 101 (R² 72h)"
    best_mae = mae_s101

if r2_multi > 0 and mae_multi < best_mae:
    best_approach = "Régression complète"
    best_mae = mae_multi

print(f"🎯 MEILLEURE APPROCHE : {best_approach}")
print(f"   MAE : {best_mae:.2f} pips")
print()

if best_approach == "Baseline 2.5":
    print("✅ RECOMMANDATION : Garder BASELINE FIXE 2.5")
    print("   - Simplicité")
    print("   - Performance acceptable")
    print("   - Pas de gain significatif avec modèles complexes")
elif len(df_reg) < 10:
    print("⚠️ ATTENTION : Échantillon trop petit (< 10 dates)")
    print("   - Risque overfitting élevé")
    print("   - Recommandation : Tester Cluster #1 (11 dates)")
    print("   - Décision finale après analyse multi-clusters")
else:
    print("✅ RECOMMANDATION : Modèle dynamique justifié")
    print(f"   - Amélioration significative vs baseline")
    print(f"   - Échantillon suffisant")

print()
print("="*80)
print("ANALYSE COMPLÈTE R² 72H TERMINÉE ✅")
print("="*80)

# Sauvegarder
output_file = Path(__file__).parent / "cluster3_complete_analysis.csv"
df_complete.to_csv(output_file, index=False)
print()
print(f"✅ Résultats sauvegardés : {output_file.name}")
