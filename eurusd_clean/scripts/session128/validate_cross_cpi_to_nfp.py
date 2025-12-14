#!/usr/bin/env python3
"""
SESSION 128 - VALIDATION CROISÉE : CPI → NFP
=============================================

ÉTAPE 5 Pipeline : Valider fonction amplification calibrée sur CPI
en la testant sur événements NFP.

Objectif : Vérifier si fonction est UNIVERSELLE ou spécifique CPI.

Process :
1. Charger fonction CPI calibrée
2. Trouver clusters NFP historiques
3. Calculer R² tendance pour chaque NFP
4. Prédire impact avec fonction CPI
5. Comparer avec baseline (amp=2.5)
6. Décision : EXCELLENT / GOOD / MODERATE / FAILED

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 128 Phase 5A
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import json
from sklearn.metrics import mean_absolute_error, r2_score

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH

print("="*80)
print("VALIDATION CROISÉE : CPI → NFP")
print("="*80)
print()

# ============================================================================
# ÉTAPE 1 : CHARGER FONCTION CALIBRÉE CPI
# ============================================================================

print("ÉTAPE 1 : CHARGEMENT FONCTION CPI")
print("-"*80)
print()

CALIBRATION_DIR = Path(__file__).parent / "calibration_results_adapted"
function_file = CALIBRATION_DIR / "amplification_function.py"
json_file = CALIBRATION_DIR / "amplification_function_calibrated.json"

if not function_file.exists():
    print(f"❌ Fonction non trouvée : {function_file}")
    sys.exit(1)

# Charger fonction
with open(function_file, 'r') as f:
    function_code = f.read()

# Extraire fonction dans namespace
exec(function_code)

# Charger métadonnées
with open(json_file, 'r') as f:
    calibration_meta = json.load(f)

print(f"✅ Fonction CPI chargée")
print(f"   Modèle : {calibration_meta['best_model']['name']}")
print(f"   Formule : {calibration_meta['best_model']['formula']}")
print(f"   Samples : {calibration_meta['statistics']['n_samples']}")
print()

# ============================================================================
# ÉTAPE 2 : TROUVER CLUSTERS NFP
# ============================================================================

print("="*80)
print("ÉTAPE 2 : RECHERCHE CLUSTERS NFP")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Chercher événements NFP (Non-Farm Payrolls)
nfp_events = [
    'nonfarm payrolls',
    'unemployment rate',
    'average hourly earnings_mom',
    'average hourly earnings_yoy',
    'labor force participation rate'
]

# Dates NFP typiques (1er vendredi du mois)
nfp_query = """
SELECT 
    DATE_TRUNC('day', ts_utc) as date,
    ts_utc,
    event_key,
    country,
    actual,
    estimate,
    previous
FROM events
WHERE country = 'US'
  AND event_key IN ({})
  AND ts_utc >= '2023-01-01'
  AND ts_utc < '2025-12-01'
ORDER BY ts_utc
""".format(','.join(f"'{e}'" for e in nfp_events))

df_nfp = conn.execute(nfp_query).fetchdf()

print(f"📊 Événements NFP trouvés : {len(df_nfp)}")
print()

if len(df_nfp) == 0:
    print("❌ Aucun événement NFP trouvé")
    conn.close()
    sys.exit(1)

# Grouper par dates (clusters)
nfp_clusters = []
for date, group in df_nfp.groupby('date'):
    nfp_clusters.append({
        'date': date,
        'cluster_time': group['ts_utc'].min(),
        'events': group.to_dict('records'),
        'n_events': len(group)
    })

print(f"📅 Clusters NFP identifiés : {len(nfp_clusters)}")
print()

print("Échantillon dates NFP :")
for cluster in nfp_clusters[:5]:
    print(f"  {cluster['date'].date()} | {cluster['n_events']} événements")
print()

# ============================================================================
# ÉTAPE 3 : CALCULER R² TENDANCE POUR CHAQUE NFP
# ============================================================================

print("="*80)
print("ÉTAPE 3 : CALCUL R² TENDANCES NFP")
print("="*80)
print()

def calculate_simple_r2_before_event(cluster_time, lookback_hours=168):
    """
    Calcule R² tendance simple avant événement.
    Prend les 7 derniers jours et fit régression linéaire.
    """
    # Charger prix 7 jours avant
    start_time = cluster_time - pd.Timedelta(hours=lookback_hours)
    
    # Convertir en Bern time
    cluster_bern = pd.to_datetime(cluster_time) + pd.Timedelta(hours=2)
    start_bern = cluster_bern - pd.Timedelta(hours=lookback_hours)
    
    start_str = start_bern.strftime('%Y-%m-%d %H:%M:%S') + '+02:00'
    cluster_str = cluster_bern.strftime('%Y-%m-%d %H:%M:%S') + '+02:00'
    
    query = f"""
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime >= '{start_str}'
      AND datetime < '{cluster_str}'
    ORDER BY datetime
    """
    
    try:
        df_prices = conn.execute(query).fetchdf()
        
        if len(df_prices) < 100:
            return None
        
        # Régression linéaire simple
        prices = df_prices['close'].values
        x = np.arange(len(prices))
        
        # Fit linéaire
        coeffs = np.polyfit(x, prices, 1)
        y_fit = np.polyval(coeffs, x)
        
        # R²
        ss_res = np.sum((prices - y_fit) ** 2)
        ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return max(0, r2)  # Borner à 0
        
    except Exception as e:
        print(f"  ⚠️ Erreur calcul R² : {e}")
        return None

# Calculer R² pour chaque cluster NFP
nfp_with_r2 = []

for idx, cluster in enumerate(nfp_clusters, 1):
    print(f"🔍 [{idx}/{len(nfp_clusters)}] {cluster['date'].date()} ... ", end='')
    
    r2 = calculate_simple_r2_before_event(cluster['cluster_time'])
    
    if r2 is not None:
        cluster['r2_trend'] = r2
        nfp_with_r2.append(cluster)
        print(f"✅ R²={r2:.4f}")
    else:
        print("⚠️ Pas de données prix")

print()
print(f"✅ {len(nfp_with_r2)} clusters NFP avec R²")
print()

if len(nfp_with_r2) < 3:
    print("❌ Pas assez de clusters NFP pour validation")
    conn.close()
    sys.exit(1)

# ============================================================================
# ÉTAPE 4 : PRÉDIRE IMPACT NFP AVEC FONCTION CPI
# ============================================================================

print("="*80)
print("ÉTAPE 4 : PRÉDICTIONS NFP")
print("="*80)
print()

# Charger scores empiriques
scores_query = """
SELECT event_key, country, empirical_score
FROM event_families
WHERE country = 'US'
"""

df_scores = conn.execute(scores_query).fetchdf()

print(f"📊 Scores empiriques chargés : {len(df_scores)}")
print()

predictions = []

for cluster in nfp_with_r2:
    cluster_time = cluster['cluster_time']
    r2_trend = cluster['r2_trend']
    
    # Charger événements avec scores
    events_data = []
    for event in cluster['events']:
        score_row = df_scores[
            (df_scores['event_key'] == event['event_key']) &
            (df_scores['country'] == event['country'])
        ]
        
        if len(score_row) > 0:
            events_data.append({
                'event_key': event['event_key'],
                'score': score_row.iloc[0]['empirical_score']
            })
    
    if len(events_data) == 0:
        continue
    
    total_score = sum(e['score'] for e in events_data)
    n_events = len(events_data)
    
    # Prédiction avec fonction CPI
    amp_from_cpi = calculate_amplification_from_r2(r2_trend)
    impact_pred_function = total_score * amp_from_cpi * np.sqrt(n_events)
    
    # Prédiction baseline (amp=2.5)
    amp_baseline = 2.5
    impact_pred_baseline = total_score * amp_baseline * np.sqrt(n_events)
    
    # Mesurer impact réel
    # Convertir en Bern time
    cluster_bern = pd.to_datetime(cluster_time) + pd.Timedelta(hours=2)
    time_start = cluster_bern - pd.Timedelta(minutes=5)
    time_end = cluster_bern + pd.Timedelta(hours=1)
    
    start_str = time_start.strftime('%Y-%m-%d %H:%M:%S') + '+02:00'
    end_str = time_end.strftime('%Y-%m-%d %H:%M:%S') + '+02:00'
    
    try:
        df_prices = conn.execute(f"""
            SELECT datetime, close, high, low
            FROM prices_bern
            WHERE datetime >= '{start_str}'
              AND datetime <= '{end_str}'
            ORDER BY datetime
        """).fetchdf()
        
        if len(df_prices) > 10:
            baseline_price = df_prices[df_prices['datetime'] < cluster_bern].iloc[-1]['close']
            after_prices = df_prices[df_prices['datetime'] > cluster_bern]
            
            max_high = after_prices['high'].max()
            min_low = after_prices['low'].min()
            
            impact_up = (max_high - baseline_price) * 10000
            impact_down = (baseline_price - min_low) * 10000
            
            impact_measured = max(impact_up, impact_down)
            
            predictions.append({
                'date': cluster['date'],
                'r2_trend': r2_trend,
                'amp_from_cpi': amp_from_cpi,
                'total_score': total_score,
                'n_events': n_events,
                'impact_measured': impact_measured,
                'impact_pred_function': impact_pred_function,
                'impact_pred_baseline': impact_pred_baseline,
                'error_function': abs(impact_pred_function - impact_measured),
                'error_baseline': abs(impact_pred_baseline - impact_measured)
            })
    except:
        pass

conn.close()

print(f"✅ {len(predictions)} prédictions NFP complétées")
print()

if len(predictions) < 3:
    print("❌ Pas assez de prédictions pour validation")
    sys.exit(1)

# ============================================================================
# ÉTAPE 5 : MÉTRIQUES & DÉCISION
# ============================================================================

print("="*80)
print("ÉTAPE 5 : MÉTRIQUES & DÉCISION")
print("="*80)
print()

df_pred = pd.DataFrame(predictions)

# Métriques
mae_function = df_pred['error_function'].mean()
mae_baseline = df_pred['error_baseline'].mean()

rmse_function = np.sqrt((df_pred['error_function'] ** 2).mean())
rmse_baseline = np.sqrt((df_pred['error_baseline'] ** 2).mean())

improvement_pct = ((mae_baseline - mae_function) / mae_baseline) * 100

print(f"📊 MÉTRIQUES VALIDATION CROISÉE CPI → NFP")
print("-"*80)
print()
print(f"   Clusters NFP testés : {len(predictions)}")
print()
print(f"   MAE Fonction CPI : {mae_function:.2f} pips")
print(f"   MAE Baseline     : {mae_baseline:.2f} pips")
print()
print(f"   RMSE Fonction    : {rmse_function:.2f} pips")
print(f"   RMSE Baseline    : {rmse_baseline:.2f} pips")
print()
print(f"   🎯 AMÉLIORATION : {improvement_pct:+.1f}%")
print()

# Décision
print("="*80)
print("DÉCISION AUTOMATIQUE")
print("="*80)
print()

if improvement_pct >= 50:
    decision = "EXCELLENT"
    recommendation = "✅✅ FONCTION UNIVERSELLE VALIDÉE"
    next_steps = [
        "Fonction CPI se généralise parfaitement aux NFP",
        "Peut être utilisée pour TOUS types d'événements HIGH",
        "Intégration Planificateur V2.5 recommandée"
    ]
elif improvement_pct >= 30:
    decision = "GOOD"
    recommendation = "✅ GÉNÉRALISATION PARTIELLE"
    next_steps = [
        "Fonction CPI améliore NFP significativement",
        "Tester sur 3ème famille (GDP/Retail Sales)",
        "Si >30% aussi → Fonction universelle validée"
    ]
elif improvement_pct >= 10:
    decision = "MODERATE"
    recommendation = "⚠️ AMÉLIORATION MODÉRÉE"
    next_steps = [
        "Généralisation limitée CPI → NFP",
        "Envisager fonction spécifique NFP",
        "Tester autres paramètres (window, lookback)"
    ]
else:
    decision = "FAILED"
    recommendation = "❌ PAS DE GÉNÉRALISATION"
    next_steps = [
        "Fonction CPI ne fonctionne pas pour NFP",
        "Calibration séparée nécessaire par famille",
        "Utiliser amplifications fixes (2.08, 1.84)"
    ]

print(f"🎯 DÉCISION : {decision}")
print()
print(f"   {recommendation}")
print()
print("   Prochaines étapes :")
for step in next_steps:
    print(f"   • {step}")
print()

# Sauvegarder résultats
OUTPUT_DIR = Path(__file__).parent / "validation_cross_cpi_nfp"
OUTPUT_DIR.mkdir(exist_ok=True)

# CSV prédictions
df_pred.to_csv(OUTPUT_DIR / "predictions_nfp.csv", index=False)

# JSON métriques
results = {
    'source_type': 'CPI',
    'target_type': 'NFP',
    'n_predictions': len(predictions),
    'metrics': {
        'mae_function': float(mae_function),
        'mae_baseline': float(mae_baseline),
        'rmse_function': float(rmse_function),
        'rmse_baseline': float(rmse_baseline),
        'improvement_pct': float(improvement_pct)
    },
    'decision': decision,
    'recommendation': recommendation,
    'next_steps': next_steps,
    'predictions': predictions
}

with open(OUTPUT_DIR / "validation_cross_results.json", 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"💾 Résultats sauvegardés : {OUTPUT_DIR.name}/")
print()

# Afficher échantillon prédictions
print("="*80)
print("ÉCHANTILLON PRÉDICTIONS")
print("="*80)
print()
print(df_pred[['date', 'impact_measured', 'impact_pred_function', 'error_function']].head(10).to_string(index=False))
print()

print("="*80)
print("✅ VALIDATION CROISÉE TERMINÉE")
print("="*80)
print()

sys.exit(0 if improvement_pct >= 10 else 1)
