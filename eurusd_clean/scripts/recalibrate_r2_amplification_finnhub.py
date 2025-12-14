"""
RECALIBRATION R² ↔ AMPLIFICATION - POST FINNHUB
================================================

Recalcule la corrélation R² ↔ amplification idéale avec les nouvelles données
(Finnhub + scores empiriques recalculés).

Auteur : André Valentin avec Claude
Date : 21 novembre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tqdm import tqdm
tqdm.write = lambda x: print(x)  # Pour afficher les logs dans tqdm

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from scipy.optimize import minimize_scalar
from core.r2_amplification_correlation import (
    calculate_r2_trend_before_event,
    calibrate_amplification_sigmoid,
    calibrate_amplification_linear,
    AMP_MIN,
    AMP_MAX
)
from core.formulas_validated import calculate_impact_d, calculate_adjusted_empirical_score
from core.event_utils import normalize_event_key_flexible

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔄 RECALIBRATION R² ↔ AMPLIFICATION - POST FINNHUB")
print("=" * 80)
print()

# ═══════════════════════════════════════════════════════════════
# CHARGER CLUSTERS HISTORIQUES (>= 7 événements)
# ═══════════════════════════════════════════════════════════════

print("1️⃣ Chargement clusters historiques...")
print("-" * 80)

df_cache = pd.read_csv(PROJECT_ROOT / 'data' / 'cache_clusters.csv')
df_patterns = pd.read_csv(PROJECT_ROOT / 'data' / 'cache_cluster_patterns.csv')

# Filtrer Double Wave avec >= 7 événements
merged = df_patterns.merge(
    df_cache[['cluster_signature', 'num_events_median', 'total_score_median']],
    on='cluster_signature',
    how='left'
)

df_dw = merged[
    (merged['pattern_type'].str.contains('DOUBLE', na=False)) &
    (merged['impact_median'].notna()) &
    (merged['num_events_median'] >= 7) &
    (merged['total_score_median'] > 0)
].copy()

print(f"   ✅ {len(df_dw)} clusters Double Wave (>= 7 événements) trouvés")
print()

# ═══════════════════════════════════════════════════════════════
# CHARGER DONNÉES POUR CHAQUE CLUSTER
# ═══════════════════════════════════════════════════════════════

print("2️⃣ Chargement données pour chaque cluster...")
print("-" * 80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger tous les scores empiriques en mémoire pour matching flexible
print("   📊 Chargement scores empiriques...")
query_scores = """
SELECT event_key, country, empirical_score
FROM event_families
WHERE empirical_score IS NOT NULL AND empirical_score > 0
"""
df_scores = conn.execute(query_scores).df()

# Créer un dictionnaire avec clés normalisées
scores_dict = {}
for _, row in df_scores.iterrows():
    key_normalized = normalize_event_key_flexible(row['event_key'])
    country = row['country'].upper()
    scores_dict[(key_normalized, country)] = row['empirical_score']

print(f"   ✅ {len(scores_dict)} scores chargés en mémoire")
print()

calibration_data = []

for idx, row in tqdm(df_dw.iterrows(), total=len(df_dw), desc="   Traitement"):
    cluster_sig = row.get('cluster_signature', '')
    if pd.isna(cluster_sig) or cluster_sig == '':
        continue
    
    # Extraire date/heure du cluster (approximatif depuis signature)
    # Pour l'instant, on va chercher dans le cache les dates où ce cluster s'est produit
    # On va utiliser une approche simplifiée : prendre la première date du cache
    
    # Pour simplifier, on va utiliser les données du cache directement
    # et chercher une date représentative dans la DB
    
    # TODO: Améliorer pour charger les dates réelles où le cluster s'est produit
    # Pour l'instant, on skip car on n'a pas les dates exactes dans le cache
    
    # Approche alternative : utiliser les mouvements Double Wave extraits
    # qui ont déjà les dates et impacts réels
    
print(f"   ⚠️  Approche simplifiée : utiliser mouvements Double Wave extraits")
print()

# Charger mouvements Double Wave avec dates réelles
doublewave_csv = PROJECT_ROOT / 'scripts' / 'session137' / 'doublewave_real_metrics_correct_workflow.csv'
if not doublewave_csv.exists():
    print(f"   ❌ Fichier {doublewave_csv} non trouvé")
    sys.exit(1)

df_movements = pd.read_csv(doublewave_csv)
df_movements_grouped = df_movements.groupby('movement_id').agg({
    'movement_datetime': 'first',
    'impact_pips': 'first',
    'num_events': 'first'
}).reset_index()

# Filtrer >= 7 événements
df_movements_filtered = df_movements_grouped[df_movements_grouped['num_events'] >= 7].copy()

print(f"   ✅ {len(df_movements_filtered)} mouvements Double Wave (>= 7 événements)")
print()

# ═══════════════════════════════════════════════════════════════
# CALCULER R² ET AMPLIFICATION IDÉALE
# ═══════════════════════════════════════════════════════════════

print("3️⃣ Calcul R² tendance et amplification idéale...")
print("-" * 80)

# Traiter tous les mouvements disponibles
n_test = len(df_movements_filtered)
print(f"   📊 Traitement de {n_test} mouvements")
print()

stats = {'total': 0, 'no_prices': 0, 'no_r2': 0, 'no_events': 0, 'no_scores': 0, 'no_impact_base': 0, 'success': 0}
counter = 0

for idx, row in tqdm(df_movements_filtered.head(n_test).iterrows(), total=n_test, desc="   Traitement"):
    stats['total'] += 1
    counter += 1
    is_first = (counter == 1)
    movement_id = row['movement_id']
    movement_datetime = pd.to_datetime(row['movement_datetime'])
    
    # Convertir en UTC si nécessaire (les données DB sont en UTC)
    if movement_datetime.tz is not None:
        movement_datetime_utc = movement_datetime.tz_convert('UTC').tz_localize(None)
    else:
        # Supposer UTC+1 (heure d'été Europe) et convertir
        movement_datetime_utc = movement_datetime - timedelta(hours=1)
    
    impact_real = row['impact_pips']
    num_events = int(row['num_events'])
    
    # Charger prix avant événement (utiliser datetime original pour prices_bern qui est en Bern time)
    start_time = movement_datetime - timedelta(days=30)
    end_time = movement_datetime
    
    query_prices = """
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime >= ? AND datetime < ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query_prices, [start_time, end_time]).df()
    
    if len(df_prices) < 60:
        stats['no_prices'] += 1
        if is_first:  # Debug pour premier cas
            print(f"      ⚠️  Pas assez de prix pour {movement_id} ({len(df_prices)} < 60)")
        continue
    
    # Calculer R² tendance
    r2_result = calculate_r2_trend_before_event(
        df_prices,
        movement_datetime,
        lookback_days=30
    )
    
    if r2_result is None:
        stats['no_r2'] += 1
        if is_first:  # Debug pour premier cas
            print(f"      ⚠️  Impossible de calculer R² pour {movement_id}")
        continue
    
    r2_trend = r2_result['r2']
    
    # Charger événements du cluster (en UTC) - fenêtre plus large
    window_start = movement_datetime_utc - timedelta(hours=2)  # 2h avant
    window_end = movement_datetime_utc + timedelta(hours=1)    # 1h après
    
    query_events = """
    SELECT 
        e.datetime_utc as ts_utc,
        e.event_name as event_key,
        e.country,
        e.actual,
        e.forecast as estimate
    FROM economic_events e
    WHERE e.datetime_utc >= ? AND e.datetime_utc <= ?
      AND e.actual IS NOT NULL
      AND e.forecast IS NOT NULL
      AND e.forecast != 0
    ORDER BY e.datetime_utc
    LIMIT ?
    """
    
    df_events = conn.execute(query_events, [window_start, window_end, num_events * 2]).df()  # Limite plus large
    
    # Ajouter scores empiriques avec matching flexible
    empirical_scores = []
    for _, row in df_events.iterrows():
        key_norm = normalize_event_key_flexible(str(row['event_key']))
        country_upper = str(row['country']).upper()
        score = scores_dict.get((key_norm, country_upper), 0.0)
        empirical_scores.append(score)
    df_events['empirical_score'] = empirical_scores
    
    if is_first:  # Debug pour premier cas
        print(f"      🔍 {movement_id} : {len(df_events)} événements trouvés dans fenêtre {window_start} - {window_end}")
        if len(df_events) > 0:
            print(f"         Exemples : {df_events[['event_key', 'country', 'actual', 'estimate']].head(3).to_string()}")
    
    if len(df_events) < num_events:
        stats['no_events'] += 1
        if is_first:  # Debug pour premier cas
            print(f"      ⚠️  Pas assez d'événements pour {movement_id} ({len(df_events)} < {num_events})")
        continue
    
    # Calculer score total ajusté
    adjusted_scores = []
    for _, event_row in df_events.iterrows():
        estimate = event_row['estimate']
        actual = event_row['actual']
        empirical_score = event_row['empirical_score']
        
        if pd.isna(estimate) or pd.isna(actual) or estimate == 0 or empirical_score == 0:
            continue
        
        surprise_pct = abs((actual - estimate) / abs(estimate)) * 100
        adjusted_score = calculate_adjusted_empirical_score(
            base_empirical_score=empirical_score,
            surprise_pct=surprise_pct
        )
        adjusted_scores.append(adjusted_score)
    
    if not adjusted_scores:
        stats['no_scores'] += 1
        if is_first:  # Debug pour premier cas
            print(f"      ⚠️  Aucun score ajusté pour {movement_id}")
        continue
    
    total_score = sum(adjusted_scores)
    mean_score = np.mean(adjusted_scores)
    
    # Calculer amplification idéale par optimisation
    # On cherche l'amplification qui donne impact_real avec calculate_impact_d
    def error_function(amp):
        impact_pred = calculate_impact_d(
            empirical_score=mean_score,
            num_events=len(adjusted_scores),
            amplification=amp,
            correction_factor=0.758
        )
        return abs(impact_pred - impact_real)
    
    try:
        result = minimize_scalar(error_function, bounds=(0.01, 10.0), method='bounded')
        amp_ideal = result.x
        
        # Vérifier que l'erreur est raisonnable
        error = error_function(amp_ideal)
        if error > 10.0:  # Erreur > 10 pips = pas fiable
            stats['no_impact_base'] += 1
            if is_first:
                print(f"      ⚠️  Erreur trop élevée pour {movement_id} (error={error:.2f} pips)")
            continue
    except Exception as e:
        stats['no_impact_base'] += 1
        if is_first:
            print(f"      ⚠️  Erreur optimisation pour {movement_id} : {e}")
        continue
    
    # Limiter à une plage raisonnable pour la calibration
    amp_ideal = max(AMP_MIN, min(AMP_MAX, amp_ideal))
    
    if idx == 0:  # Debug pour premier cas
        print(f"      ✅ Cas {movement_id} : R²={r2_trend:.4f}, Amp idéale={amp_ideal:.4f}, Impact réel={impact_real:.2f}, Impact base={impact_base:.2f}")
    
    calibration_data.append({
        'movement_id': movement_id,
        'date': movement_datetime.strftime('%Y-%m-%d'),
        'r2_trend': r2_trend,
        'amp_ideal': amp_ideal,
        'impact_real': impact_real,
        'num_events': len(adjusted_scores),
        'total_score': total_score
    })
    stats['success'] += 1

conn.close()

print()
print("   📊 Statistiques de traitement :")
print("-" * 80)
print(f"      Total traité : {stats['total']}")
print(f"      ❌ Pas assez de prix : {stats['no_prices']}")
print(f"      ❌ R² impossible : {stats['no_r2']}")
print(f"      ❌ Pas assez d'événements : {stats['no_events']}")
print(f"      ❌ Aucun score ajusté : {stats['no_scores']}")
print(f"      ❌ Impact base <= 0 : {stats['no_impact_base']}")
print(f"      ✅ Succès : {stats['success']}")
print()

if len(calibration_data) < 3:
    print(f"   ❌ Pas assez de données pour calibration ({len(calibration_data)} < 3)")
    print(f"   💡 Suggestion : Vérifier la vue 'events' et les scores empiriques")
    sys.exit(1)

print(f"   ✅ {len(calibration_data)} cas avec données complètes")
print()

# ═══════════════════════════════════════════════════════════════
# CALIBRATION
# ═══════════════════════════════════════════════════════════════

print("4️⃣ Calibration fonctions...")
print("-" * 80)

df_calib = pd.DataFrame(calibration_data)
r2_values = df_calib['r2_trend'].values
amp_ideal_values = df_calib['amp_ideal'].values

# Calibration sigmoid
func_sigmoid, metrics_sigmoid = calibrate_amplification_sigmoid(r2_values, amp_ideal_values)

# Calibration linear
func_linear, metrics_linear = calibrate_amplification_linear(r2_values, amp_ideal_values)

print("   📊 Résultats calibration :")
print("-" * 80)
print(f"   Sigmoid :")
if 'error' not in metrics_sigmoid:
    print(f"      R² fit : {metrics_sigmoid['r2_fit']:.4f}")
    print(f"      MAE : {metrics_sigmoid['mae']:.6f}")
    print(f"      Formule : {metrics_sigmoid['formula']}")
else:
    print(f"      ❌ Erreur : {metrics_sigmoid['error']}")

print()
print(f"   Linear :")
if 'error' not in metrics_linear:
    print(f"      R² fit : {metrics_linear['r2_fit']:.4f}")
    print(f"      MAE : {metrics_linear['mae']:.6f}")
    print(f"      Formule : {metrics_linear['formula']}")
else:
    print(f"      ❌ Erreur : {metrics_linear['error']}")

print()

# Sélectionner meilleur modèle
best_model = None
best_metrics = None
if 'error' not in metrics_sigmoid and 'error' not in metrics_linear:
    if metrics_sigmoid['r2_fit'] > metrics_linear['r2_fit']:
        best_model = ('sigmoid', func_sigmoid, metrics_sigmoid)
        best_metrics = metrics_sigmoid
    else:
        best_model = ('linear', func_linear, metrics_linear)
        best_metrics = metrics_linear
elif 'error' not in metrics_sigmoid:
    best_model = ('sigmoid', func_sigmoid, metrics_sigmoid)
    best_metrics = metrics_sigmoid
elif 'error' not in metrics_linear:
    best_model = ('linear', func_linear, metrics_linear)
    best_metrics = metrics_linear

if best_model:
    print(f"   ✅ Meilleur modèle : {best_model[0]}")
    print(f"      R² fit : {best_metrics['r2_fit']:.4f}")
    print(f"      MAE : {best_metrics['mae']:.6f}")
    print()

# ═══════════════════════════════════════════════════════════════
# SAUVEGARDER RÉSULTATS
# ═══════════════════════════════════════════════════════════════

output_dir = PROJECT_ROOT / 'scripts' / 'recalibration_r2_amplification'
output_dir.mkdir(exist_ok=True)

# Sauvegarder données calibration
df_calib.to_csv(output_dir / 'calibration_data.csv', index=False)

# Sauvegarder métriques
results = {
    'n_samples': len(calibration_data),
    'sigmoid': metrics_sigmoid if 'error' not in metrics_sigmoid else {'error': metrics_sigmoid['error']},
    'linear': metrics_linear if 'error' not in metrics_linear else {'error': metrics_linear['error']},
    'best_model': best_model[0] if best_model else None,
    'best_params': best_metrics.get('params') if best_model else None
}

import json
with open(output_dir / 'calibration_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"   ✅ Résultats sauvegardés dans {output_dir}")
print()

print("=" * 80)
print("✅ RECALIBRATION TERMINÉE")
print("=" * 80)
print()

