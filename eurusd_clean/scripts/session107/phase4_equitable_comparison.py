#!/usr/bin/env python3
"""
SESSION 111 - TEST ÉQUITABLE SESSION 101 vs INVERSION
======================================================
Compare les deux méthodes sur les MÊMES 17 dates

Session 101 : amp = 0.5490 × R²_72h + 1.6988
Inversion   : amp = 1.0736 × R²_inversion + 1.8859
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import duckdb
from scipy.stats import linregress
import sys

print("="*80)
print("SESSION 111 - TEST ÉQUITABLE : SESSION 101 vs INVERSION")
print("="*80)
print()
print("💡 OBJECTIF :")
print("   Comparer les deux méthodes sur les MÊMES 17 dates")
print("   pour décision équitable")
print()

# Setup
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import importlib.util
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger résultats combinés
combined_file = Path(__file__).parent / "phase3_combined_calibration.csv"
df = pd.read_csv(combined_file)

print(f"✅ {len(df)} dates chargées")
print()

# =============================================================================
# FONCTION CALCUL R² 72H (SESSION 101)
# =============================================================================

def calculate_r2_72h(conn, event_datetime_bern):
    """
    Calcul R² sur 72h avant événement (méthode Session 101)
    
    Fenêtre fixe : 72h avant événement
    """
    event_dt = pd.to_datetime(event_datetime_bern)
    query_dt = event_dt - timedelta(hours=2)  # Timezone correction
    
    # 72h avant
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
        return None
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # Régression linéaire
    df_prices['timestamp_numeric'] = (df_prices['datetime'] - df_prices['datetime'].iloc[0]).dt.total_seconds()
    X = df_prices['timestamp_numeric'].values
    y = df_prices['close'].values
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
        return r2
    except:
        return None

# =============================================================================
# CALCULER R² 72H POUR LES 17 DATES
# =============================================================================

print("="*80)
print("CALCUL R² 72H (SESSION 101) SUR 17 DATES")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

r2_72h_list = []

for _, row in df.iterrows():
    date_str = row['date']
    cluster = row['cluster']
    
    # Déterminer heure événement selon cluster
    if 'C3' in cluster:
        event_hour = 14  # CPI : 14:30
        event_minute = 30
    else:
        event_hour = 15  # Manufacturing : 15:45
        event_minute = 45
    
    event_datetime_bern = f"{date_str} {event_hour:02d}:{event_minute:02d}:00+02:00"
    
    print(f"📅 {date_str} ({cluster}) : ", end="")
    
    r2_72h = calculate_r2_72h(conn, event_datetime_bern)
    
    if r2_72h is not None:
        print(f"R² 72h = {r2_72h:.4f}")
        r2_72h_list.append(r2_72h)
    else:
        print("❌ Échec calcul")
        r2_72h_list.append(np.nan)

conn.close()

df['r2_72h'] = r2_72h_list

print()
print(f"✅ R² 72h calculé pour {df['r2_72h'].notna().sum()}/{len(df)} dates")
print()

# =============================================================================
# APPLIQUER FORMULE SESSION 101
# =============================================================================

print("="*80)
print("APPLICATION FORMULE SESSION 101")
print("="*80)
print()

# Formule Session 101 (calibrée sur 29 dates CPI)
SLOPE_S101 = 0.5490
INTERCEPT_S101 = 1.6988

df['amp_session101'] = SLOPE_S101 * df['r2_72h'] + INTERCEPT_S101

# Calculer impact prédit avec Session 101
df['impact_pred_session101'] = df['impact_pred_baseline'] * (df['amp_session101'] / 2.5)

# Erreurs
df['error_session101'] = abs(df['impact_pred_session101'] - df['impact_real'])

print(f"📐 FORMULE SESSION 101 :")
print(f"   amp = {SLOPE_S101:.4f} × R²_72h + {INTERCEPT_S101:.4f}")
print()

# =============================================================================
# COMPARAISON 3 MÉTHODES SUR 17 DATES
# =============================================================================

print("="*80)
print("COMPARAISON 3 MÉTHODES (MÊMES 17 DATES)")
print("="*80)
print()

# Filtrer dates valides (où toutes méthodes ont pu calculer)
df_valid = df[df['error_session101'].notna() & df['error_inversion'].notna()].copy()

n_valid = len(df_valid)

if n_valid == 0:
    print("❌ Aucune date avec toutes métriques valides")
    sys.exit(1)

print(f"📊 {n_valid} dates avec toutes métriques valides")
print()

# Statistiques par méthode
mae_baseline = df_valid['error_baseline'].mean()
mae_session101 = df_valid['error_session101'].mean()
mae_inversion = df_valid['error_inversion'].mean()

rmse_baseline = np.sqrt((df_valid['error_baseline']**2).mean())
rmse_session101 = np.sqrt((df_valid['error_session101']**2).mean())
rmse_inversion = np.sqrt((df_valid['error_inversion']**2).mean())

# Amélioration vs baseline
improv_s101 = (mae_baseline - mae_session101) / mae_baseline * 100
improv_inv = (mae_baseline - mae_inversion) / mae_baseline * 100

print("📊 MÉTHODE A : BASELINE FIXE (amp=2.5)")
print(f"   MAE  : {mae_baseline:.2f} pips")
print(f"   RMSE : {rmse_baseline:.2f} pips")
print()

print("📊 MÉTHODE B : SESSION 101 (R² 72h)")
print(f"   MAE  : {mae_session101:.2f} pips")
print(f"   RMSE : {rmse_session101:.2f} pips")
print(f"   Amélioration vs baseline : {improv_s101:+.1f}%")
print()

print("📊 MÉTHODE C : INVERSION (R² dynamique)")
print(f"   MAE  : {mae_inversion:.2f} pips")
print(f"   RMSE : {rmse_inversion:.2f} pips")
print(f"   Amélioration vs baseline : {improv_inv:+.1f}%")
print()

# Comparaison directe
print("🎯 COMPARAISON DIRECTE :")
print(f"   Session 101 vs Inversion : {mae_session101:.2f} vs {mae_inversion:.2f} pips")

if mae_session101 < mae_inversion:
    diff = mae_inversion - mae_session101
    pct = (diff / mae_inversion) * 100
    print(f"   ✅ Session 101 GAGNE de {diff:.2f} pips ({pct:.1f}%)")
elif mae_inversion < mae_session101:
    diff = mae_session101 - mae_inversion
    pct = (diff / mae_session101) * 100
    print(f"   ✅ Inversion GAGNE de {diff:.2f} pips ({pct:.1f}%)")
else:
    print(f"   🤝 ÉGALITÉ")

print()

# =============================================================================
# ANALYSE PAR CLUSTER
# =============================================================================

print("="*80)
print("ANALYSE PAR CLUSTER")
print("="*80)
print()

for cluster_name in ['C3_CPI', 'C1_Manufacturing']:
    df_cluster = df_valid[df_valid['cluster'] == cluster_name]
    
    if len(df_cluster) == 0:
        continue
    
    mae_base_c = df_cluster['error_baseline'].mean()
    mae_s101_c = df_cluster['error_session101'].mean()
    mae_inv_c = df_cluster['error_inversion'].mean()
    
    print(f"📊 {cluster_name} ({len(df_cluster)} dates) :")
    print(f"   Baseline     : {mae_base_c:.2f} pips")
    print(f"   Session 101  : {mae_s101_c:.2f} pips ({((mae_base_c-mae_s101_c)/mae_base_c*100):+.1f}%)")
    print(f"   Inversion    : {mae_inv_c:.2f} pips ({((mae_base_c-mae_inv_c)/mae_base_c*100):+.1f}%)")
    print()

# =============================================================================
# RÉSUMÉ PAR DATE
# =============================================================================

print("="*80)
print("RÉSUMÉ PAR DATE (17 DATES)")
print("="*80)
print()

print("Date       | Cluster | R²_72h | R²_inv | Base | S101 | Inv  | Gagnant")
print("-"*90)

for _, row in df_valid.sort_values('date').iterrows():
    cluster_short = row['cluster'].split('_')[0]
    
    # Déterminer gagnant
    errors = {
        'Base': row['error_baseline'],
        'S101': row['error_session101'],
        'Inv': row['error_inversion']
    }
    winner = min(errors, key=errors.get)
    
    print(f"{row['date']} | {cluster_short:3s} | {row['r2_72h']:6.4f} | {row['r2_inversion']:6.4f} | "
          f"{row['error_baseline']:5.1f} | {row['error_session101']:5.1f} | {row['error_inversion']:5.1f} | "
          f"{winner}")

print()

# =============================================================================
# DÉCISION FINALE ÉQUITABLE
# =============================================================================

print("="*80)
print("DÉCISION FINALE (TEST ÉQUITABLE)")
print("="*80)
print()

if mae_session101 < mae_inversion and improv_s101 > 10:
    print("✅ RECOMMANDATION : SESSION 101 (R² 72h)")
    print()
    print(f"   Formule : amp = {SLOPE_S101:.4f} × R²_72h + {INTERCEPT_S101:.4f}")
    print(f"   Amélioration : {improv_s101:+.1f}% vs baseline")
    print(f"   MAE : {mae_session101:.2f} pips")
elif mae_inversion < mae_session101 and improv_inv > 10:
    print("✅ RECOMMANDATION : INVERSION (R² dynamique)")
    print()
    print(f"   Formule : amp = 1.0736 × R²_inversion + 1.8859")
    print(f"   Amélioration : {improv_inv:+.1f}% vs baseline")
    print(f"   MAE : {mae_inversion:.2f} pips")
    print()
    print("   JUSTIFICATION :")
    print("   - Capte vraies inversions (pas fenêtre arbitraire)")
    print("   - Durée adaptative (29-119h)")
    print("   - 5 filtres anti-micro-pics")
elif max(improv_s101, improv_inv) > 10:
    print("⚠️ RECOMMANDATION : LES DEUX SE VALENT")
    print()
    print(f"   Session 101 : MAE {mae_session101:.2f} pips ({improv_s101:+.1f}%)")
    print(f"   Inversion   : MAE {mae_inversion:.2f} pips ({improv_inv:+.1f}%)")
    print()
    print("   Choisir selon préférence :")
    print("   - Session 101 : Plus simple (1 calcul)")
    print("   - Inversion : Plus conceptuel (structure marché)")
else:
    print("❌ RECOMMANDATION : CONSERVER BASELINE (amp=2.5)")
    print()
    print(f"   Améliorations insuffisantes (<10%)")
    print(f"   Session 101 : {improv_s101:+.1f}%")
    print(f"   Inversion   : {improv_inv:+.1f}%")

print()

# Sauvegarder
output_file = Path(__file__).parent / "phase4_equitable_comparison.csv"
df_valid.to_csv(output_file, index=False)

print("="*80)
print("COMPARAISON ÉQUITABLE TERMINÉE ✅")
print("="*80)
print()
print(f"✅ Résultats : {output_file.name}")
