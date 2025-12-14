#!/usr/bin/env python3
"""
Validation direction avec test set plus large
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
import duckdb
from sklearn.metrics import accuracy_score, matthews_corrcoef, f1_score, confusion_matrix
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_DIR = Path(__file__).parent.parent / 'outputs'
DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
ALPHA_WEIGHTS_FILE = BASE_DIR / 'alpha_weights.csv'
EVENTS_FILE = BASE_DIR / 'events.csv'
DIRECTION_THRESHOLDS_FILE = BASE_DIR / 'direction_thresholds.json'
AMPLITUDE_CALIBRATION_FILE = BASE_DIR / 'amplitude_calibration.json'

# Configuration
TRAIN_SPLIT = 0.8  # 80% train, 20% test
MAX_TEST_DATES = 200  # Test set plus large
MIN_MOVEMENT_PIPS = 20  # Minimum pour considérer un mouvement significatif

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

def load_events_for_date(date_str: str) -> pd.DataFrame:
    """Charge événements pour une date"""
    if not DB_PATH.exists():
        return pd.DataFrame()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        query = """
        SELECT 
            e.event_key,
            e.ts_utc,
            e.actual,
            e.estimate,
            e.previous,
            ef.family,
            ef.empirical_score
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
        
        df = conn.execute(query, [date_str]).df()
        return df
    
    except Exception as e:
        print(f"⚠️  Erreur chargement {date_str}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def calculate_real_movement(date_str: str, horizon_hours: int = 1) -> tuple:
    """
    Calcule mouvement réel à partir des prix
    Retourne (movement_pips, direction)
    Utilise la même méthode que validate_on_new_dates.py
    """
    if not DB_PATH.exists():
        return None, None
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Trouver premier événement de la journée
        query_event = """
        SELECT MIN(ts_utc) as first_event_ts
        FROM events
        WHERE DATE(ts_utc) = ? AND country = 'US'
        """
        event_time = conn.execute(query_event, [date_str]).df()
        
        if len(event_time) == 0 or pd.isna(event_time.iloc[0]['first_event_ts']):
            return None, None
        
        event_ts = pd.to_datetime(event_time.iloc[0]['first_event_ts'])
        
        # Utiliser la même méthode que detect_movement_for_date
        start_time = event_ts - pd.Timedelta(minutes=5)
        end_time = event_ts + pd.Timedelta(minutes=120)
        
        query = """
        SELECT 
            ts_utc,
            close
        FROM prices_1m_v
        WHERE ts_utc >= ? AND ts_utc <= ?
        ORDER BY ts_utc
        """
        
        prices_df = conn.execute(query, [start_time, end_time]).df()
        
        if len(prices_df) < 10:
            return None, None
        
        # Convertir ts_utc
        prices_df['ts_utc'] = pd.to_datetime(prices_df['ts_utc'])
        prices_df = prices_df.set_index('ts_utc')
        
        # Normaliser event_time
        if hasattr(event_ts, 'tzinfo') and event_ts.tzinfo is not None:
            event_time_naive = event_ts.replace(tzinfo=None)
        else:
            event_time_naive = event_ts
        
        # Trouver index le plus proche de l'événement
        event_idx = prices_df.index.get_indexer([event_time_naive], method='nearest')[0]
        if event_idx < 0 or event_idx >= len(prices_df):
            return None, None
        
        # Prix de départ (close de la bougie juste avant)
        if event_idx > 0:
            start_price = float(prices_df.iloc[event_idx - 1]['close'])
        else:
            start_price = float(prices_df.iloc[event_idx]['close'])
        
        # Chercher pic dans les 60 minutes suivantes (1h horizon)
        window_df = prices_df.iloc[event_idx:event_idx+60]
        
        if len(window_df) == 0:
            return None, None
        
        # Créer high/low depuis close (approximation)
        window_df['high'] = window_df['close']
        window_df['low'] = window_df['close']
        
        # Pic haut et bas
        peak_high = float(window_df['high'].max())
        peak_low = float(window_df['low'].min())
        
        # Direction
        move_up = peak_high - start_price
        move_down = start_price - peak_low
        
        if move_up > move_down:
            direction = 'UP'
            peak_pips = move_up * 10000
        else:
            direction = 'DOWN'
            peak_pips = move_down * 10000
        
        return peak_pips, direction
    
    except Exception as e:
        # Silencieux pour éviter spam
        return None, None
    finally:
        conn.close()

def find_test_dates(max_dates: int = 200) -> List[str]:
    """Trouve dates avec événements pour test"""
    if not DB_PATH.exists():
        return []
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Trouver dates avec événements HIGH IMPACT
        query = """
        SELECT DISTINCT DATE(e.ts_utc) as date
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.country = 'US'
            AND ef.empirical_score IS NOT NULL
            AND ef.empirical_score > 40
            AND DATE(e.ts_utc) >= '2023-01-01'
        ORDER BY date DESC
        LIMIT ?
        """
        
        df_dates = conn.execute(query, [max_dates * 2]).df()  # Prendre plus pour filtrer
        
        dates = []
        for d in df_dates['date'].tolist():
            if isinstance(d, str):
                date_only = d.split()[0]
            elif hasattr(d, 'date'):
                date_only = str(d.date())
            else:
                date_only = str(d).split()[0]
            dates.append(date_only)
        
        return dates[:max_dates]
    
    finally:
        conn.close()

def main():
    print("="*80)
    print("VALIDATION DIRECTION - TEST SET LARGE")
    print("="*80)
    print()
    
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
    
    # Charger alpha et stats
    alpha_map = load_alpha_map(horizon='1h')
    stats_map = load_surprise_stats()
    
    print(f"✅ Alpha map chargé : {len(alpha_map)} événements")
    print(f"✅ Stats surprise chargées : {len(stats_map)} événements")
    print()
    
    # Trouver dates de test
    print("🔍 Recherche dates de test...")
    test_dates = find_test_dates(max_dates=MAX_TEST_DATES)
    print(f"   ✅ {len(test_dates)} dates trouvées")
    print()
    
    # Calculer prédictions et mouvements réels
    print("="*80)
    print("📊 CALCUL PRÉDICTIONS & MOUVEMENTS RÉELS")
    print("="*80)
    print()
    
    results = []
    
    for i, date_str in enumerate(test_dates):
        if (i + 1) % 50 == 0:
            print(f"   Traitement : {i+1}/{len(test_dates)} dates...")
        
        # Charger événements
        events_df = load_events_for_date(date_str)
        if len(events_df) == 0:
            continue
        
        # Calculer S
        S = calculate_direction_score_empirical(events_df, alpha_map, stats_map)
        
        # Prédiction avec seuil θ
        if S > theta_1h:
            direction_pred = 'UP'
        elif S < -theta_1h:
            direction_pred = 'DOWN'
        else:
            direction_pred = 'UNKNOWN'
        
        # Mouvement réel
        movement_pips, direction_real = calculate_real_movement(date_str, horizon_hours=1)
        
        if movement_pips is None or movement_pips < MIN_MOVEMENT_PIPS:
            continue
        
        results.append({
            'date': date_str,
            'score_S': S,
            'direction_predicted': direction_pred,
            'direction_real': direction_real,
            'movement_pips': movement_pips,
            'correct': direction_pred == direction_real if direction_pred != 'UNKNOWN' else None
        })
    
    print(f"   ✅ {len(results)} résultats valides")
    print()
    
    if len(results) == 0:
        print("❌ Aucun résultat valide")
        return
    
    df_results = pd.DataFrame(results)
    
    # Split train/test
    split_idx = int(len(df_results) * TRAIN_SPLIT)
    df_train = df_results.iloc[:split_idx].copy()
    df_test = df_results.iloc[split_idx:].copy()
    
    print(f"📅 Split : {len(df_train)} train, {len(df_test)} test")
    print()
    
    # ===== AVANT CALIBRATION (θ=0.0) =====
    print("="*80)
    print("📊 RÉSULTATS AVANT CALIBRATION (θ=0.0)")
    print("="*80)
    print()
    
    # Recalculer avec θ=0.0
    predictions_before = []
    for S in df_test['score_S'].values:
        if S > 0.0:
            pred = 'UP'
        elif S < 0.0:
            pred = 'DOWN'
        else:
            pred = 'UNKNOWN'
        predictions_before.append(pred)
    
    y_true = df_test['direction_real'].values
    y_pred_before = np.array(predictions_before)
    
    mask_before = y_pred_before != 'UNKNOWN'
    
    if mask_before.sum() > 0:
        y_true_before = y_true[mask_before]
        y_pred_before_filtered = y_pred_before[mask_before]
        
        y_true_bin_before = (y_true_before == 'UP').astype(int)
        y_pred_bin_before = (y_pred_before_filtered == 'UP').astype(int)
        
        acc_before = accuracy_score(y_true_bin_before, y_pred_bin_before) * 100
        mcc_before = matthews_corrcoef(y_true_bin_before, y_pred_bin_before)
        f1_before = f1_score(y_true_bin_before, y_pred_bin_before, zero_division=0)
        
        print(f"Test set ({mask_before.sum()}/{len(df_test)} prédictions valides, {mask_before.sum()/len(df_test)*100:.1f}% couverture) :")
        print(f"   Accuracy : {acc_before:.1f}%")
        print(f"   MCC      : {mcc_before:.3f}")
        print(f"   F1       : {f1_before:.3f}")
        print()
        
        cm_before = confusion_matrix(y_true_bin_before, y_pred_bin_before)
        if cm_before.shape == (2, 2):
            print(f"   Matrice de confusion :")
            print(f"      UP prédit UP   : {cm_before[1,1]}")
            print(f"      UP prédit DOWN : {cm_before[1,0]}")
            print(f"      DOWN prédit UP : {cm_before[0,1]}")
            print(f"      DOWN prédit DOWN : {cm_before[0,0]}")
    else:
        acc_before = 0.0
        mcc_before = 0.0
        f1_before = 0.0
        print("   ⚠️  Aucune prédiction valide")
    
    print()
    
    # ===== APRÈS CALIBRATION (θ calibré) =====
    print("="*80)
    print(f"📊 RÉSULTATS APRÈS CALIBRATION (θ={theta_1h:.2f})")
    print("="*80)
    print()
    
    y_pred_after = df_test['direction_predicted'].values
    mask_after = y_pred_after != 'UNKNOWN'
    
    if mask_after.sum() > 0:
        y_true_after = y_true[mask_after]
        y_pred_after_filtered = y_pred_after[mask_after]
        
        y_true_bin_after = (y_true_after == 'UP').astype(int)
        y_pred_bin_after = (y_pred_after_filtered == 'UP').astype(int)
        
        acc_after = accuracy_score(y_true_bin_after, y_pred_bin_after) * 100
        mcc_after = matthews_corrcoef(y_true_bin_after, y_pred_bin_after)
        f1_after = f1_score(y_true_bin_after, y_pred_bin_after, zero_division=0)
        
        print(f"Test set ({mask_after.sum()}/{len(df_test)} prédictions valides, {mask_after.sum()/len(df_test)*100:.1f}% couverture) :")
        print(f"   Accuracy : {acc_after:.1f}%")
        print(f"   MCC      : {mcc_after:.3f}")
        print(f"   F1       : {f1_after:.3f}")
        print()
        
        cm_after = confusion_matrix(y_true_bin_after, y_pred_bin_after)
        if cm_after.shape == (2, 2):
            print(f"   Matrice de confusion :")
            print(f"      UP prédit UP   : {cm_after[1,1]}")
            print(f"      UP prédit DOWN : {cm_after[1,0]}")
            print(f"      DOWN prédit UP : {cm_after[0,1]}")
            print(f"      DOWN prédit DOWN : {cm_after[0,0]}")
    else:
        acc_after = 0.0
        mcc_after = 0.0
        f1_after = 0.0
        print("   ⚠️  Aucune prédiction valide")
    
    print()
    
    # ===== COMPARAISON =====
    print("="*80)
    print("📈 COMPARAISON")
    print("="*80)
    print()
    
    delta_acc = acc_after - acc_before
    delta_mcc = mcc_after - mcc_before
    delta_f1 = f1_after - f1_before
    
    coverage_before = (mask_before.sum() / len(df_test)) * 100
    coverage_after = (mask_after.sum() / len(df_test)) * 100
    delta_coverage = coverage_after - coverage_before
    
    print(f"Accuracy : {acc_before:.1f}% → {acc_after:.1f}%  (Δ = {delta_acc:+.1f} points)")
    print(f"MCC      : {mcc_before:.3f} → {mcc_after:.3f}  (Δ = {delta_mcc:+.3f})")
    print(f"F1       : {f1_before:.3f} → {f1_after:.3f}  (Δ = {delta_f1:+.3f})")
    print(f"Couverture : {coverage_before:.1f}% → {coverage_after:.1f}%  (Δ = {delta_coverage:+.1f} points)")
    print()
    
    if delta_acc > 0:
        print(f"✅ Amélioration de {delta_acc:.1f} points en accuracy")
    elif delta_acc < 0:
        print(f"⚠️  Dégradation de {abs(delta_acc):.1f} points en accuracy")
    else:
        print("➡️  Pas de changement en accuracy")
    
    if delta_coverage < -10:
        print(f"⚠️  Réduction importante de couverture ({delta_coverage:.1f} points)")
    
    print()
    
    # Sauvegarder résultats
    output_file = BASE_DIR / 'validation_direction_large_testset.csv'
    df_results.to_csv(output_file, index=False)
    print(f"✅ Résultats sauvegardés : {output_file}")

if __name__ == '__main__':
    main()


