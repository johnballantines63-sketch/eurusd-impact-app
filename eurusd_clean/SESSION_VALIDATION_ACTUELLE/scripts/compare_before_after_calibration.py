#!/usr/bin/env python3
"""
Compare résultats avant/après calibration V3
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.metrics import accuracy_score, matthews_corrcoef, f1_score, confusion_matrix

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_DIR = Path(__file__).parent.parent / 'outputs'
RESULTS_FILE = BASE_DIR / 'validation_new_dates_results.csv'
DIRECTION_THRESHOLDS_FILE = BASE_DIR / 'direction_thresholds.json'
AMPLITUDE_CALIBRATION_FILE = BASE_DIR / 'amplitude_calibration.json'
ALPHA_WEIGHTS_FILE = BASE_DIR / 'alpha_weights.csv'
EVENTS_FILE = BASE_DIR / 'events.csv'

def load_alpha_map(horizon='1h'):
    """Charge alpha map"""
    df_alpha = pd.read_csv(ALPHA_WEIGHTS_FILE)
    df_horizon = df_alpha[df_alpha['horizon'] == horizon].copy()
    alpha_map = {}
    for _, row in df_horizon.iterrows():
        event_key = str(row['event_key']).strip()
        weight = float(row['weight'])
        alpha_map[event_key] = weight
    return alpha_map

def load_surprise_stats():
    """Calcule (mu, sigma) des surprises par event_key"""
    df_events = pd.read_csv(EVENTS_FILE)
    df_events['event_key'] = (
        df_events['event_key'].astype(str).str.strip().str.lower()
        .str.replace(r'\s+', ' ', regex=True).str.replace('-', ' ')
    )
    df_events['actual'] = pd.to_numeric(df_events['actual'], errors='coerce')
    df_events['estimate'] = pd.to_numeric(df_events['estimate'], errors='coerce')
    
    df_events = df_events.dropna(subset=['actual', 'estimate'])
    df_events['surprise'] = df_events['actual'] - df_events['estimate']
    
    stats = {}
    g = df_events.groupby('event_key')['surprise']
    mu = g.mean()
    sigma = g.std(ddof=0)
    for k in mu.index:
        s = float(sigma.loc[k])
        if s == 0 or np.isnan(s):
            continue
        stats[k] = (float(mu.loc[k]), s)
    return stats

def calculate_direction_score_empirical(events_df, alpha_map, stats_map):
    """Calcule score S = sum(alpha_e * z_e)"""
    S = 0.0
    used = 0
    
    for _, row in events_df.iterrows():
        actual = row.get('actual')
        estimate = row.get('estimate')
        family = str(row.get('family', 'Other')).strip()
        event_key = str(row.get('event_key', '')).strip().lower()
        
        if pd.isna(actual) or pd.isna(estimate):
            continue
        
        actual = float(actual)
        estimate = float(estimate)
        surprise = actual - estimate
        
        mu_sigma = stats_map.get(event_key)
        if mu_sigma is None:
            continue
        mu, sigma = mu_sigma
        if sigma == 0:
            continue
        
        z = (surprise - mu) / sigma
        sign = "pos" if z > 0 else "neg"
        
        alpha_key = f"{family}_surp_{sign}"
        alpha = float(alpha_map.get(alpha_key, 0.0))
        
        S += alpha * z
        used += 1
    
    return S if used > 0 else 0.0

def load_events_for_date(date_str):
    """Charge événements pour une date"""
    db_path = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
    import duckdb
    conn = duckdb.connect(str(db_path), read_only=True)
    
    query = f"""
    SELECT 
        e.event_key,
        e.ts_utc,
        e.actual,
        e.estimate,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
        AND e.country = 'US'
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).df()
    conn.close()
    return df

def main():
    print("="*80)
    print("COMPARAISON AVANT/APRÈS CALIBRATION V3")
    print("="*80)
    print()
    
    # Charger données
    df_results = pd.read_csv(RESULTS_FILE)
    df_results['date'] = pd.to_datetime(df_results['date'])
    
    # Charger calibrations
    with open(DIRECTION_THRESHOLDS_FILE, 'r') as f:
        direction_thresholds = json.load(f)
    
    with open(AMPLITUDE_CALIBRATION_FILE, 'r') as f:
        amplitude_calibration = json.load(f)
    
    theta_1h = direction_thresholds.get('1h', 0.0)
    k_global = amplitude_calibration.get('k_global', 1.0)
    
    print(f"📊 Paramètres de calibration :")
    print(f"   θ (1h) = {theta_1h:.2f}")
    print(f"   k global = {k_global:.3f}")
    print()
    
    # Split train/test (même que calibration)
    TRAIN_SPLIT = 0.8
    split_idx = int(len(df_results) * TRAIN_SPLIT)
    df_train = df_results.iloc[:split_idx].copy()
    df_test = df_results.iloc[split_idx:].copy()
    
    print(f"📅 Split : {len(df_train)} train, {len(df_test)} test")
    print()
    
    # ===== AVANT CALIBRATION =====
    print("="*80)
    print("📊 RÉSULTATS AVANT CALIBRATION")
    print("="*80)
    print()
    
    # Sur test set
    y_true_test = df_test['direction_real'].values
    y_pred_test_before = df_test['direction_predicted'].values
    
    # Filtrer UNKNOWN
    mask_before = y_pred_test_before != 'UNKNOWN'
    if mask_before.sum() > 0:
        y_true_before = y_true_test[mask_before]
        y_pred_before = y_pred_test_before[mask_before]
        
        y_true_bin_before = (y_true_before == 'UP').astype(int)
        y_pred_bin_before = (y_pred_before == 'UP').astype(int)
        
        acc_before = accuracy_score(y_true_bin_before, y_pred_bin_before) * 100
        mcc_before = matthews_corrcoef(y_true_bin_before, y_pred_bin_before)
        f1_before = f1_score(y_true_bin_before, y_pred_bin_before, zero_division=0)
        
        print(f"Test set ({mask_before.sum()} prédictions valides) :")
        print(f"   Accuracy : {acc_before:.1f}%")
        print(f"   MCC      : {mcc_before:.3f}")
        print(f"   F1       : {f1_before:.3f}")
        print()
        
        # Confusion matrix
        cm_before = confusion_matrix(y_true_bin_before, y_pred_bin_before)
        print(f"   Matrice de confusion :")
        print(f"      UP prédit UP   : {cm_before[1,1] if cm_before.shape == (2,2) else 'N/A'}")
        print(f"      UP prédit DOWN : {cm_before[1,0] if cm_before.shape == (2,2) else 'N/A'}")
        print(f"      DOWN prédit UP : {cm_before[0,1] if cm_before.shape == (2,2) else 'N/A'}")
        print(f"      DOWN prédit DOWN : {cm_before[0,0] if cm_before.shape == (2,2) else 'N/A'}")
    else:
        acc_before = 0.0
        mcc_before = 0.0
        f1_before = 0.0
        print("   ⚠️  Aucune prédiction valide")
    
    print()
    
    # ===== APRÈS CALIBRATION =====
    print("="*80)
    print("📊 RÉSULTATS APRÈS CALIBRATION")
    print("="*80)
    print()
    
    # Recalculer S pour chaque date du test avec seuil θ
    alpha_map = load_alpha_map(horizon='1h')
    stats_map = load_surprise_stats()
    
    predictions_after = []
    scores_S_after = []
    
    for _, row in df_test.iterrows():
        date_str = row['date']
        if isinstance(date_str, pd.Timestamp):
            date_str = date_str.strftime('%Y-%m-%d')
        
        # Charger événements
        events_df = load_events_for_date(date_str)
        
        if len(events_df) > 0:
            # Calculer S
            S = calculate_direction_score_empirical(events_df, alpha_map, stats_map)
            scores_S_after.append(S)
            
            # Appliquer seuil θ
            if S > theta_1h:
                pred = 'UP'
            elif S < -theta_1h:
                pred = 'DOWN'
            else:
                pred = 'UNKNOWN'
            
            predictions_after.append(pred)
        else:
            predictions_after.append('UNKNOWN')
            scores_S_after.append(0.0)
    
    # Métriques après calibration
    y_pred_test_after = np.array(predictions_after)
    mask_after = y_pred_test_after != 'UNKNOWN'
    
    if mask_after.sum() > 0:
        y_true_after = y_true_test[mask_after]
        y_pred_after = y_pred_test_after[mask_after]
        
        y_true_bin_after = (y_true_after == 'UP').astype(int)
        y_pred_bin_after = (y_pred_after == 'UP').astype(int)
        
        acc_after = accuracy_score(y_true_bin_after, y_pred_bin_after) * 100
        mcc_after = matthews_corrcoef(y_true_bin_after, y_pred_bin_after)
        f1_after = f1_score(y_true_bin_after, y_pred_bin_after, zero_division=0)
        
        print(f"Test set ({mask_after.sum()} prédictions valides) :")
        print(f"   Accuracy : {acc_after:.1f}%")
        print(f"   MCC      : {mcc_after:.3f}")
        print(f"   F1       : {f1_after:.3f}")
        print()
        
        # Confusion matrix
        cm_after = confusion_matrix(y_true_bin_after, y_pred_bin_after)
        print(f"   Matrice de confusion :")
        print(f"      UP prédit UP   : {cm_after[1,1] if cm_after.shape == (2,2) else 'N/A'}")
        print(f"      UP prédit DOWN : {cm_after[1,0] if cm_after.shape == (2,2) else 'N/A'}")
        print(f"      DOWN prédit UP : {cm_after[0,1] if cm_after.shape == (2,2) else 'N/A'}")
        print(f"      DOWN prédit DOWN : {cm_after[0,0] if cm_after.shape == (2,2) else 'N/A'}")
    else:
        acc_after = 0.0
        mcc_after = 0.0
        f1_after = 0.0
        print("   ⚠️  Aucune prédiction valide")
    
    print()
    
    # ===== COMPARAISON =====
    print("="*80)
    print("📈 AMÉLIORATION")
    print("="*80)
    print()
    
    delta_acc = acc_after - acc_before
    delta_mcc = mcc_after - mcc_before
    delta_f1 = f1_after - f1_before
    
    print(f"Accuracy : {acc_before:.1f}% → {acc_after:.1f}%  (Δ = {delta_acc:+.1f} points)")
    print(f"MCC      : {mcc_before:.3f} → {mcc_after:.3f}  (Δ = {delta_mcc:+.3f})")
    print(f"F1       : {f1_before:.3f} → {f1_after:.3f}  (Δ = {delta_f1:+.3f})")
    print()
    
    if delta_acc > 0:
        print(f"✅ Amélioration de {delta_acc:.1f} points en accuracy")
    elif delta_acc < 0:
        print(f"⚠️  Dégradation de {abs(delta_acc):.1f} points en accuracy")
    else:
        print("➡️  Pas de changement en accuracy")
    
    print()
    
    # Amplitude
    print("="*80)
    print("📊 CALIBRATION AMPLITUDE")
    print("="*80)
    print()
    
    mae_before = df_test['error_abs'].mean()
    df_test['impact_predicted_calibrated'] = df_test['impact_predicted'] * k_global
    df_test['error_abs_calibrated'] = abs(df_test['impact_predicted_calibrated'] - df_test['impact_real'])
    mae_after = df_test['error_abs_calibrated'].mean()
    
    ratio_before = np.median(df_test['impact_predicted'] / df_test['impact_real'])
    ratio_after = np.median(df_test['impact_predicted_calibrated'] / df_test['impact_real'])
    
    print(f"MAE avant  : {mae_before:.2f} pips")
    print(f"MAE après : {mae_after:.2f} pips  (Δ = {mae_after - mae_before:+.2f} pips)")
    print()
    print(f"Ratio médian avant  : {ratio_before:.3f}")
    print(f"Ratio médian après  : {ratio_after:.3f}")
    print()
    
    if mae_after < mae_before:
        improvement_pct = ((mae_before - mae_after) / mae_before) * 100
        print(f"✅ Réduction de {improvement_pct:.1f}% de l'erreur MAE")
    print()

if __name__ == '__main__':
    main()


