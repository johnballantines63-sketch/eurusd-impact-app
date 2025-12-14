#!/usr/bin/env python3
"""
Calibration V3 - Direction Thresholds & Amplitude Calibration

Objectif :
1. Calibrer θ direction (maximise MCC ou F1) par horizon
2. Calibrer amplitude avec k = median(|real| / |pred|)
3. Optionnel : Apprendre α séparés par régime (TREND/RANGE)
4. Générer fichiers de calibration

Date : 2025-12-08
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import matthews_corrcoef, f1_score, accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Config
BASE_DIR = Path(__file__).parent.parent / 'outputs'
ALPHA_WEIGHTS_FILE = BASE_DIR / 'alpha_weights.csv'
EVENTS_FILE = BASE_DIR / 'events.csv'
PRICES_FILE = BASE_DIR / 'prices_ohlc_m1.csv'
VALIDATION_RESULTS_FILE = BASE_DIR / 'validation_new_dates_results.csv'

OUTPUT_DIR = BASE_DIR
DIRECTION_THRESHOLDS_FILE = OUTPUT_DIR / 'direction_thresholds.json'
AMPLITUDE_CALIBRATION_FILE = OUTPUT_DIR / 'amplitude_calibration.json'
ALPHA_BY_REGIME_FILE = OUTPUT_DIR / 'alpha_by_regime.csv'
WALKFORWARD_V3_REPORT_FILE = OUTPUT_DIR / 'walkforward_v3_report.csv'

# Paramètres
HORIZONS = ['1h', '4h', '1j']  # 1j sera resamplé depuis 1h
TRAIN_SPLIT = 0.8  # 80% train, 20% test
THETA_RANGE = np.arange(-2.0, 2.1, 0.1)  # Range pour calibration θ

def load_historical_data():
    """Charge données historiques pour calibration"""
    print("="*80)
    print("📊 CHARGEMENT DONNÉES HISTORIQUES")
    print("="*80)
    print()
    
    # Charger résultats validation
    print(f"Lecture : {VALIDATION_RESULTS_FILE}")
    df_results = pd.read_csv(VALIDATION_RESULTS_FILE)
    df_results['date'] = pd.to_datetime(df_results['date'])
    print(f"   ✅ {len(df_results):,} résultats chargés")
    
    # Charger prix pour calculer mouvements futurs
    print(f"Lecture : {PRICES_FILE}")
    df_prices = pd.read_csv(PRICES_FILE)
    df_prices['ts_utc'] = pd.to_datetime(df_prices['ts_utc'])
    df_prices = df_prices.sort_values('ts_utc').reset_index(drop=True)
    print(f"   ✅ {len(df_prices):,} prix chargés")
    
    # Charger alpha weights
    print(f"Lecture : {ALPHA_WEIGHTS_FILE}")
    df_alpha = pd.read_csv(ALPHA_WEIGHTS_FILE)
    print(f"   ✅ {len(df_alpha):,} alpha weights chargés")
    
    # Charger stats surprise
    print(f"Lecture : {EVENTS_FILE}")
    df_events = pd.read_csv(EVENTS_FILE)
    print(f"   ✅ {len(df_events):,} événements chargés")
    print()
    
    return df_results, df_prices, df_alpha, df_events

def load_alpha_map(df_alpha, horizon='1h'):
    """Charge alpha map pour un horizon"""
    df_horizon = df_alpha[df_alpha['horizon'] == horizon].copy()
    alpha_map = {}
    for _, row in df_horizon.iterrows():
        event_key = str(row['event_key']).strip()
        weight = float(row['weight'])
        alpha_map[event_key] = weight
    return alpha_map

def load_surprise_stats(df_events):
    """Calcule (mu, sigma) des surprises par event_key"""
    df_events = df_events.copy()
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
    """
    Calcule score S = sum(alpha_e * z_e) pour prédiction directionnelle
    """
    S = 0.0
    
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
    
    return S

def detect_regime(df_prices, event_time):
    """Détecte régime TREND ou RANGE à partir des prix"""
    # Créer série H1
    df_prices['ts_h1'] = df_prices['ts_utc'].dt.floor('H')
    df_h1 = df_prices.groupby('ts_h1').agg({
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).reset_index()
    df_h1 = df_h1.sort_values('ts_h1').reset_index(drop=True)
    
    # Calculer EMA 200 sur H1
    df_h1['ema_200'] = df_h1['close'].ewm(span=200, adjust=False).mean()
    
    # Calculer slope EMA
    window_slope = 20
    df_h1['ema_slope'] = df_h1['ema_200'].diff(window_slope) / window_slope
    
    # Trouver régime au moment de l'événement
    event_h1 = event_time.floor('H')
    h1_row = df_h1[df_h1['ts_h1'] <= event_h1].iloc[-1] if len(df_h1[df_h1['ts_h1'] <= event_h1]) > 0 else None
    
    if h1_row is not None:
        slope = abs(h1_row['ema_slope'])
        return 'TREND' if slope > 0.0001 else 'RANGE'
    return 'RANGE'  # Default

def load_events_for_date(date_str, db_path=None):
    """Charge événements pour une date donnée"""
    if db_path is None:
        db_path = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
    
    import duckdb
    conn = duckdb.connect(str(db_path), read_only=True)
    
    query = f"""
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.country,
        e.actual,
        e.estimate,
        e.previous,
        ef.family,
        ef.empirical_score
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

def calibrate_direction_threshold(df_results, df_alpha, df_events, horizon='1h'):
    """
    Calibre θ pour maximiser MCC ou F1 sur train
    Recalcule réellement S pour chaque date
    """
    print(f"   Calibration θ pour horizon {horizon}...")
    
    # Charger alpha map et stats
    alpha_map = load_alpha_map(df_alpha, horizon=horizon)
    stats_map = load_surprise_stats(df_events)
    
    if len(alpha_map) == 0:
        print(f"      ⚠️  Aucun alpha weight pour {horizon}, utilisation θ=0.0")
        return 0.0
    
    # Split train/test
    split_idx = int(len(df_results) * TRAIN_SPLIT)
    df_train = df_results.iloc[:split_idx].copy()
    
    # Recalculer S pour chaque date du train
    scores_S = []
    directions_real_list = []
    
    db_path = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
    
    for _, row in df_train.iterrows():
        date_str = row['date']
        if isinstance(date_str, pd.Timestamp):
            date_str = date_str.strftime('%Y-%m-%d')
        
        # Charger événements pour cette date
        events_df = load_events_for_date(date_str, db_path)
        
        if len(events_df) > 0:
            # Calculer S réel
            S = calculate_direction_score_empirical(events_df, alpha_map, stats_map)
            scores_S.append(S)
            directions_real_list.append(row['direction_real'])
    
    if len(scores_S) < 10:
        print(f"      ⚠️  Pas assez de scores S calculés ({len(scores_S)}), utilisation θ=0.0")
        return 0.0
    
    scores_S = np.array(scores_S)
    directions_real_array = np.array(directions_real_list)
    
    # Trouver meilleur θ sur train
    best_theta = 0.0
    best_mcc = -1.0
    best_f1 = 0.0
    best_accuracy = 0.0
    
    for theta in THETA_RANGE:
        # Appliquer seuil θ
        predictions = []
        for S in scores_S:
            if S > theta:
                pred = 'UP'
            elif S < -theta:
                pred = 'DOWN'
            else:
                pred = 'UNKNOWN'
            predictions.append(pred)
        
        # Calculer métriques
        y_pred = np.array(predictions)
        
        # Filtrer UNKNOWN pour calcul métriques
        mask = y_pred != 'UNKNOWN'
        if mask.sum() >= 10:  # Minimum 10 échantillons
            y_true_filtered = directions_real_array[mask]
            y_pred_filtered = y_pred[mask]
            
            # Convertir en binaire pour métriques
            y_true_bin = (y_true_filtered == 'UP').astype(int)
            y_pred_bin = (y_pred_filtered == 'UP').astype(int)
            
            mcc = matthews_corrcoef(y_true_bin, y_pred_bin)
            f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
            accuracy = accuracy_score(y_true_bin, y_pred_bin)
            
            # Maximiser MCC (ou F1 si MCC égal)
            score = mcc if not np.isnan(mcc) else f1
            
            if score > best_mcc or (score == best_mcc and f1 > best_f1):
                best_mcc = score
                best_theta = theta
                best_f1 = f1
                best_accuracy = accuracy
    
    print(f"      ✅ Meilleur θ = {best_theta:.2f} (MCC={best_mcc:.3f}, F1={best_f1:.3f}, Acc={best_accuracy:.3f})")
    return best_theta

def calibrate_amplitude(df_results):
    """
    Calibre amplitude avec k = median(|real| / |pred|)
    """
    print("   Calibration amplitude...")
    
    # Calculer ratio pour chaque prédiction
    df_results = df_results.copy()
    df_results['ratio'] = df_results['impact_real'] / (df_results['impact_predicted'] + 1e-10)
    
    # Filtrer ratios extrêmes (outliers)
    q1 = df_results['ratio'].quantile(0.25)
    q3 = df_results['ratio'].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    df_filtered = df_results[
        (df_results['ratio'] >= lower_bound) & 
        (df_results['ratio'] <= upper_bound)
    ].copy()
    
    # k global
    k_global = df_filtered['ratio'].median()
    
    # k par mouvement class si disponible
    k_by_class = {}
    if 'movement_class' in df_filtered.columns:
        for class_name in df_filtered['movement_class'].unique():
            df_class = df_filtered[df_filtered['movement_class'] == class_name]
            if len(df_class) >= 5:  # Minimum 5 échantillons
                k_by_class[class_name] = float(df_class['ratio'].median())
    
    print(f"      ✅ k global = {k_global:.3f}")
    if k_by_class:
        print(f"      ✅ k par classe : {k_by_class}")
    
    return {
        'k_global': float(k_global),
        'k_by_class': k_by_class,
        'n_samples': len(df_filtered),
        'n_outliers': len(df_results) - len(df_filtered)
    }

def learn_alpha_by_regime(df_results, df_alpha, df_events, df_prices, horizon='1h'):
    """
    Apprend α séparés par régime TREND/RANGE avec Ridge Logistic
    """
    print(f"   Apprentissage α par régime pour {horizon}...")
    
    # Charger alpha map et stats
    alpha_map_base = load_alpha_map(df_alpha, horizon=horizon)
    stats_map = load_surprise_stats(df_events)
    
    if len(alpha_map_base) == 0:
        print(f"      ⚠️  Aucun alpha weight pour {horizon}")
        return None
    
    # Préparer données : pour chaque date, calculer features et détecter régime
    X_trend = []
    X_range = []
    y_trend = []
    y_range = []
    
    db_path = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
    
    # Split train/test
    split_idx = int(len(df_results) * TRAIN_SPLIT)
    df_train = df_results.iloc[:split_idx].copy()
    
    event_keys_sorted = sorted(set([k for k in alpha_map_base.keys()]))
    
    for _, row in df_train.iterrows():
        date_str = row['date']
        if isinstance(date_str, pd.Timestamp):
            date_str = date_str.strftime('%Y-%m-%d')
        
        # Charger événements
        events_df = load_events_for_date(date_str, db_path)
        if len(events_df) == 0:
            continue
        
        # Détecter régime
        event_ts_str = events_df['ts_utc'].iloc[0]
        event_time = pd.to_datetime(event_ts_str)
        regime = detect_regime(df_prices, event_time)
        
        # Calculer vecteur feature X (contributions alpha * z)
        x_vec = np.zeros(len(event_keys_sorted))
        
        for _, event_row in events_df.iterrows():
            actual = event_row.get('actual')
            estimate = event_row.get('estimate')
            family = str(event_row.get('family', 'Other')).strip()
            event_key = str(event_row.get('event_key', '')).strip().lower()
            
            if pd.isna(actual) or pd.isna(estimate):
                continue
            
            surprise = float(actual) - float(estimate)
            mu_sigma = stats_map.get(event_key)
            if mu_sigma is None:
                continue
            
            mu, sigma = mu_sigma
            if sigma == 0:
                continue
            
            z = (surprise - mu) / sigma
            sign = "pos" if z > 0 else "neg"
            alpha_key = f"{family}_surp_{sign}"
            
            if alpha_key in event_keys_sorted:
                idx = event_keys_sorted.index(alpha_key)
                x_vec[idx] += z  # Contribution z (alpha sera appris)
        
        # Direction réelle
        direction_real = row['direction_real']
        y = 1 if direction_real == 'UP' else 0
        
        # Séparer par régime
        if regime == 'TREND':
            X_trend.append(x_vec)
            y_trend.append(y)
        else:
            X_range.append(x_vec)
            y_range.append(y)
    
    if len(X_trend) < 10 or len(X_range) < 10:
        print(f"      ⚠️  Pas assez de données par régime (TREND: {len(X_trend)}, RANGE: {len(X_range)})")
        return None
    
    # Apprendre modèles séparés
    results = []
    
    for regime_name, X_regime, y_regime in [
        ('TREND', X_trend, y_trend),
        ('RANGE', X_range, y_range)
    ]:
        X_regime = np.array(X_regime)
        y_regime = np.array(y_regime)
        
        # Normaliser
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_regime)
        
        # Ridge Logistic
        model = LogisticRegression(penalty='l2', C=1.0, max_iter=1000, solver='lbfgs')
        model.fit(X_scaled, y_regime)
        
        # Stocker poids
        for idx, event_key in enumerate(event_keys_sorted):
            weight = model.coef_[0][idx] if idx < len(model.coef_[0]) else 0.0
            results.append({
                'horizon': horizon,
                'regime': regime_name,
                'event_key': event_key,
                'weight': weight,
                'intercept': model.intercept_[0],
                'n_samples': len(X_regime)
            })
        
        # Métriques
        y_pred = model.predict(X_scaled)
        acc = accuracy_score(y_regime, y_pred)
        print(f"      ✅ {regime_name}: {len(X_regime)} échantillons, Accuracy={acc:.3f}")
    
    return pd.DataFrame(results)

def main():
    print("="*80)
    print("CALIBRATION V3 - DIRECTION & AMPLITUDE")
    print("="*80)
    print()
    
    # 1. Charger données
    df_results, df_prices, df_alpha, df_events = load_historical_data()
    
    if len(df_results) == 0:
        print("❌ Aucune donnée de validation disponible")
        return
    
    # 2. Calibrer direction thresholds par horizon
    print("="*80)
    print("🎯 CALIBRATION SEUILS DIRECTION (θ)")
    print("="*80)
    print()
    
    direction_thresholds = {}
    
    for horizon in HORIZONS:
        theta = calibrate_direction_threshold(df_results, df_alpha, df_events, horizon=horizon)
        direction_thresholds[horizon] = float(theta)
    
    # Sauvegarder
    with open(DIRECTION_THRESHOLDS_FILE, 'w') as f:
        json.dump(direction_thresholds, f, indent=2)
    
    print()
    print(f"✅ Seuils direction sauvegardés : {DIRECTION_THRESHOLDS_FILE}")
    print()
    
    # 3. Calibrer amplitude
    print("="*80)
    print("📊 CALIBRATION AMPLITUDE (k)")
    print("="*80)
    print()
    
    amplitude_calibration = calibrate_amplitude(df_results)
    
    # Sauvegarder
    with open(AMPLITUDE_CALIBRATION_FILE, 'w') as f:
        json.dump(amplitude_calibration, f, indent=2)
    
    print()
    print(f"✅ Calibration amplitude sauvegardée : {AMPLITUDE_CALIBRATION_FILE}")
    print()
    
    # 4. Apprendre alpha par régime (optionnel)
    print("="*80)
    print("🔧 APPRENTISSAGE α PAR RÉGIME (OPTIONNEL)")
    print("="*80)
    print()
    
    alpha_by_regime = learn_alpha_by_regime(df_results, df_alpha, df_events, df_prices, horizon='1h')
    
    if alpha_by_regime is not None:
        df_alpha_regime = pd.DataFrame(alpha_by_regime)
        df_alpha_regime.to_csv(ALPHA_BY_REGIME_FILE, index=False)
        print(f"✅ Alpha par régime sauvegardé : {ALPHA_BY_REGIME_FILE}")
    else:
        print("⚠️  Alpha par régime non implémenté (nécessite accès clusters complets)")
    print()
    
    # 5. Générer rapport walk-forward V3
    print("="*80)
    print("📋 GÉNÉRATION RAPPORT WALK-FORWARD V3")
    print("="*80)
    print()
    
    # Appliquer calibrations et calculer métriques
    split_idx = int(len(df_results) * TRAIN_SPLIT)
    df_train = df_results.iloc[:split_idx].copy()
    df_test = df_results.iloc[split_idx:].copy()
    
    # Appliquer calibration amplitude
    k_global = amplitude_calibration['k_global']
    df_test['impact_predicted_calibrated'] = df_test['impact_predicted'] * k_global
    
    # Recalculer erreurs avec amplitude calibrée
    df_test['error_abs_calibrated'] = abs(df_test['impact_predicted_calibrated'] - df_test['impact_real'])
    df_test['error_pct_calibrated'] = (df_test['error_abs_calibrated'] / df_test['impact_real']) * 100
    
    # Métriques avec calibration
    mae_calibrated = df_test['error_abs_calibrated'].mean()
    mae_median_calibrated = df_test['error_abs_calibrated'].median()
    ratio_median_calibrated = np.median(df_test['impact_predicted_calibrated'] / df_test['impact_real'])
    
    # Direction avec seuil calibré
    theta_1h = direction_thresholds.get('1h', 0.0)
    # Note: Pour appliquer θ, il faudrait recalculer S pour chaque date
    # Pour l'instant, on utilise direction_predicted existant
    
    direction_accuracy_calibrated = df_test['direction_correct'].mean() * 100
    
    # Créer rapport
    report = {
        'horizon': ['1h'],  # Pour l'instant, on teste seulement 1h
        'train_samples': [len(df_train)],
        'test_samples': [len(df_test)],
        'theta_calibrated': [theta_1h],
        'k_global': [k_global],
        'mae_before_calibration': [df_test['error_abs'].mean()],
        'mae_after_calibration': [mae_calibrated],
        'mae_median_after': [mae_median_calibrated],
        'ratio_median_after': [ratio_median_calibrated],
        'direction_accuracy': [direction_accuracy_calibrated]
    }
    
    df_report = pd.DataFrame(report)
    df_report.to_csv(WALKFORWARD_V3_REPORT_FILE, index=False)
    
    print(f"✅ Rapport walk-forward V3 sauvegardé : {WALKFORWARD_V3_REPORT_FILE}")
    print()
    
    # Afficher résumé
    print("="*80)
    print("✅ CALIBRATION V3 TERMINÉE")
    print("="*80)
    print()
    print("📁 Fichiers générés :")
    print(f"   🎯 {DIRECTION_THRESHOLDS_FILE}")
    print(f"   📊 {AMPLITUDE_CALIBRATION_FILE}")
    if alpha_by_regime is not None:
        print(f"   🔧 {ALPHA_BY_REGIME_FILE}")
    print(f"   📋 {WALKFORWARD_V3_REPORT_FILE}")
    print()
    print("📊 Résultats calibration :")
    print(f"   θ (1h) : {theta_1h:.2f}")
    print(f"   k global : {k_global:.3f}")
    print(f"   MAE avant : {df_test['error_abs'].mean():.2f} pips")
    print(f"   MAE après : {mae_calibrated:.2f} pips")
    print(f"   Ratio médian après : {ratio_median_calibrated:.3f}")
    print()

if __name__ == '__main__':
    main()


