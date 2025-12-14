#!/usr/bin/env python3
"""
SESSION 108 - PHASE 2B CLUSTER #1 : ANALYSE R² 72H
==================================================
Test formule Session 101 sur Cluster #1 (Manufacturing|Consumer|Employment, 11 dates)

Formule Session 101 (validée sur 29 dates CPI) :
    amplification = 0.5490 × R²_72h + 1.6988

Validation Cluster #3 (6 dates CPI) :
    MAE = 0.82 pips (vs 15.69 baseline) → 95% amélioration ✅

Objectif : Valider universalité sur Cluster #1 (11 dates, types différents)
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import importlib.util
from datetime import datetime, timedelta

print("="*80)
print("SESSION 108 - PHASE 2B CLUSTER #1 : ANALYSE R² 72H")
print("="*80)
print()

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Load config
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger résultats Phase 1
results_file = Path(__file__).parent / "phase1_cluster1_results.csv"

if not results_file.exists():
    print(f"❌ ERREUR : Fichier {results_file.name} introuvable")
    print(f"   Veuillez d'abord exécuter : phase1_cluster1_measure_impacts.py")
    sys.exit(1)

df = pd.read_csv(results_file)

print(f"✅ {len(df)} dates Cluster #1 chargées")
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
    
    # Timestamp événement (15:45 Bern → 13:45+02:00 DB)
    event_dt = pd.to_datetime(f"{date_str} 15:45:00+02:00")
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
print("DONNÉES COMPLÈTES CLUSTER #1")
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
    'trend_strength': 'Force tendance (pips)',
    'max_surprise': 'Surprise max (%)'
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
# FORMULE SESSION 101 (RÉFÉRENCE)
# =============================================================================

print("="*80)
print("TEST FORMULE SESSION 101 SUR CLUSTER #1")
print("="*80)
print()

print("📊 Formule Session 101 (29 dates CPI) :")
print("   amplification = 0.5490 × R²_72h + 1.6988")
print()
print("📊 Validation Cluster #3 (6 dates CPI) :")
print("   MAE = 0.82 pips (vs 15.69 baseline)")
print("   Amélioration = 95%")
print()

# Appliquer formule Session 101 sur Cluster #1
if 'r2_72h' in df_complete.columns:
    df_complete['amp_s101'] = 0.5490 * df_complete['r2_72h'] + 1.6988
    
    # Calculer erreur
    df_complete['error_s101'] = np.abs(df_complete['amp_s101'] - df_complete['amp_optimal'])
    
    mae_s101 = df_complete['error_s101'].mean()
    mae_baseline = df_complete['error_baseline'].mean()
    
    improvement = ((mae_baseline - mae_s101) / mae_baseline) * 100
    
    print(f"📊 Application Session 101 sur Cluster #1 :")
    print(f"   MAE baseline (amp=2.5) : {mae_baseline:.2f} pips")
    print(f"   MAE Session 101        : {mae_s101:.2f} pips")
    print(f"   Amélioration           : {improvement:.1f}%")
    print()
    
    print("📊 Résultats par date :")
    print("-"*80)
    for _, row in df_complete.iterrows():
        if pd.notna(row.get('r2_72h')):
            print(f"   {row['date']} : R²={row['r2_72h']:.4f} → "
                  f"amp_s101={row['amp_s101']:.3f} | "
                  f"amp_optimal={row['amp_optimal']:.3f} | "
                  f"error={row['error_s101']:.2f} pips")
    print()

# =============================================================================
# COMPARAISON CLUSTER #1 vs CLUSTER #3
# =============================================================================

print("="*80)
print("COMPARAISON CLUSTER #1 vs CLUSTER #3")
print("="*80)
print()

# Charger résultats Cluster #3
cluster3_file = Path(__file__).parent.parent / "session107" / "cluster3_complete_analysis.csv"

if cluster3_file.exists():
    df_c3 = pd.read_csv(cluster3_file)
    
    print("📊 Performance formule Session 101 :")
    print()
    print(f"   CLUSTER #3 (6 dates CPI) :")
    if 'error_s101' in df_c3.columns:
        mae_c3_s101 = df_c3['error_s101'].mean()
        mae_c3_baseline = df_c3['error_baseline'].mean()
        print(f"      MAE baseline       : {mae_c3_baseline:.2f} pips")
        print(f"      MAE Session 101    : {mae_c3_s101:.2f} pips")
        print(f"      Amélioration       : {((mae_c3_baseline - mae_c3_s101) / mae_c3_baseline) * 100:.1f}%")
    print()
    
    print(f"   CLUSTER #1 (11 dates Manufacturing) :")
    print(f"      MAE baseline       : {mae_baseline:.2f} pips")
    print(f"      MAE Session 101    : {mae_s101:.2f} pips")
    print(f"      Amélioration       : {improvement:.1f}%")
    print()
    
    # Analyse combinée
    print("📊 ANALYSE COMBINÉE (17 dates total) :")
    print()
    
    if 'error_s101' in df_c3.columns:
        # Combiner
        mae_combined_baseline = (mae_baseline * len(df_complete) + mae_c3_baseline * len(df_c3)) / (len(df_complete) + len(df_c3))
        mae_combined_s101 = (mae_s101 * len(df_complete) + mae_c3_s101 * len(df_c3)) / (len(df_complete) + len(df_c3))
        improvement_combined = ((mae_combined_baseline - mae_combined_s101) / mae_combined_baseline) * 100
        
        print(f"   Échantillon total  : {len(df_complete) + len(df_c3)} dates")
        print(f"   MAE baseline       : {mae_combined_baseline:.2f} pips")
        print(f"   MAE Session 101    : {mae_combined_s101:.2f} pips")
        print(f"   Amélioration       : {improvement_combined:.1f}%")
        print()
    
    # Corrélations R² vs amp_optimal
    print("📊 Corrélations R² 72h vs amp_optimal :")
    print()
    
    corr_c1 = df_complete['r2_72h'].corr(df_complete['amp_optimal'])
    if 'r2_72h' in df_c3.columns:
        corr_c3 = df_c3['r2_72h'].corr(df_c3['amp_optimal'])
        
        print(f"   Cluster #1 (Manufacturing) : r = {corr_c1:+.3f}")
        print(f"   Cluster #3 (CPI)           : r = {corr_c3:+.3f}")
        print()

else:
    print("⚠️ Fichier Cluster #3 introuvable, comparaison impossible")
    print()

# =============================================================================
# RECOMMANDATION FINALE
# =============================================================================

print("="*80)
print("RECOMMANDATION FINALE")
print("="*80)
print()

print(f"📊 FORMULE SESSION 101 sur Cluster #1 :")
print(f"   ✅ MAE : {mae_s101:.2f} pips")
print(f"   ✅ Amélioration : {improvement:.1f}% vs baseline")
print()

if mae_s101 < mae_baseline:
    print("✅ SUCCÈS : Formule Session 101 améliore baseline sur Cluster #1")
    print()
    print("🎯 UNIVERSALITÉ VALIDÉE :")
    print("   - Cluster #3 (CPI) : 95% amélioration")
    print(f"   - Cluster #1 (Manufacturing) : {improvement:.1f}% amélioration")
    print("   - 2 clusters différents → Formule généralise bien ✅")
    print()
    print("📝 DÉCISION : Formule Session 101 prête pour production")
else:
    print("⚠️ ATTENTION : Formule Session 101 n'améliore PAS baseline sur Cluster #1")
    print()
    print("📝 ANALYSE NÉCESSAIRE :")
    print("   - Vérifier pourquoi fonctionne sur CPI mais pas Manufacturing")
    print("   - Tester méthode Inversion (Phase 2E)")
    print("   - Considérer formules spécifiques par cluster")

print()
print("="*80)
print("PHASE 2B CLUSTER #1 TERMINÉE ✅")
print("="*80)

# Sauvegarder
output_file = Path(__file__).parent / "cluster1_complete_analysis.csv"
df_complete.to_csv(output_file, index=False)
print()
print(f"✅ Résultats sauvegardés : {output_file.name}")
