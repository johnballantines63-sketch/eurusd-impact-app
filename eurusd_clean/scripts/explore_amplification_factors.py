"""
Exploration des facteurs de corrélation pour l'amplification idéale
====================================================================

Explore différents facteurs qui pourraient mieux prédire l'amplification
idéale que le R² de la tendance :
- Volatilité pré-événement
- Surprise max
- Nombre d'événements
- Score total ajusté
- Direction du mouvement
- Etc.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from tqdm import tqdm

# Ajouter le chemin du projet
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from core.formulas_validated import calculate_impact_d, calculate_adjusted_empirical_score
from core.r2_amplification_correlation import calculate_r2_trend_before_event
from core.event_utils import normalize_event_key_flexible

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔍 EXPLORATION FACTEURS DE CORRÉLATION - AMPLIFICATION IDÉALE")
print("=" * 80)
print()

# 1️⃣ Charger les données de calibration existantes
print("1️⃣ Chargement données de calibration...")
print("-" * 80)
df_calibration = pd.read_csv(PROJECT_ROOT / 'scripts' / 'recalibration_r2_amplification' / 'calibration_data.csv')
print(f"   ✅ {len(df_calibration)} cas chargés")
print()

# 2️⃣ Charger les mouvements Double Wave pour enrichir
print("2️⃣ Chargement mouvements Double Wave...")
print("-" * 80)
df_movements = pd.read_csv(PROJECT_ROOT / 'scripts' / 'session137' / 'doublewave_real_metrics_correct_workflow.csv')
print(f"   ✅ {len(df_movements)} mouvements chargés")
print()

# 3️⃣ Charger les scores empiriques
print("3️⃣ Chargement scores empiriques...")
print("-" * 80)
conn = duckdb.connect(str(DB_PATH), read_only=True)
query_scores = """
SELECT event_key, country, empirical_score
FROM event_families
WHERE empirical_score IS NOT NULL AND empirical_score > 0
"""
df_scores = conn.execute(query_scores).df()
scores_dict = {}
for _, row in df_scores.iterrows():
    key_norm = normalize_event_key_flexible(str(row['event_key']))
    country_upper = str(row['country']).upper()
    scores_dict[(key_norm, country_upper)] = row['empirical_score']
print(f"   ✅ {len(scores_dict)} scores chargés")
print()

# 4️⃣ Enrichir les données avec les facteurs supplémentaires
print("4️⃣ Enrichissement des données...")
print("-" * 80)

enriched_data = []

for idx, row in tqdm(df_calibration.iterrows(), total=len(df_calibration), desc="   Traitement"):
    movement_id = row['movement_id']
    date_str = row['date']
    r2_trend = row['r2_trend']
    amp_ideal = row['amp_ideal']
    impact_real = row['impact_real']
    num_events = row['num_events']
    total_score = row['total_score']
    
    # Trouver le mouvement correspondant
    movement_row = df_movements[df_movements['movement_id'] == movement_id]
    if len(movement_row) == 0:
        continue
    
    movement_row = movement_row.iloc[0]
    movement_datetime = pd.to_datetime(movement_row['movement_datetime'])
    
    # Charger les prix pour calculer la volatilité
    start_time = movement_datetime - pd.Timedelta(days=30)
    end_time = movement_datetime
    
    query_prices = """
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime >= ? AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query_prices, [start_time, end_time]).df()
    if len(df_prices) < 60:
        continue
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices = df_prices.set_index('datetime')
    
    # Calculer volatilité (écart-type des rendements sur 30 jours)
    df_prices['returns'] = df_prices['close'].pct_change()
    volatility = df_prices['returns'].std() * 100  # En pourcentage
    
    # Charger les événements pour calculer surprise max
    window_start = movement_datetime - pd.Timedelta(hours=2)
    window_end = movement_datetime + pd.Timedelta(hours=1)
    
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
    LIMIT 20
    """
    
    df_events = conn.execute(query_events, [window_start, window_end]).df()
    
    if len(df_events) == 0:
        continue
    
    # Ajouter scores empiriques
    empirical_scores = []
    surprises_pct = []
    for _, evt_row in df_events.iterrows():
        key_norm = normalize_event_key_flexible(str(evt_row['event_key']))
        country_upper = str(evt_row['country']).upper()
        score = scores_dict.get((key_norm, country_upper), 0.0)
        empirical_scores.append(score)
        
        # Calculer surprise
        actual = evt_row['actual']
        estimate = evt_row['estimate']
        if estimate != 0:
            surprise_pct = abs((actual - estimate) / abs(estimate)) * 100
            surprises_pct.append(surprise_pct)
    
    surprise_max = max(surprises_pct) if surprises_pct else 0.0
    mean_empirical_score = np.mean(empirical_scores) if empirical_scores else 0.0
    
    # Direction du mouvement
    direction = movement_row.get('direction', 'UP')
    direction_numeric = 1 if direction == 'UP' else -1
    
    # Score total ajusté moyen
    mean_adjusted_score = total_score / num_events if num_events > 0 else 0.0
    
    enriched_data.append({
        'movement_id': movement_id,
        'date': date_str,
        'r2_trend': r2_trend,
        'amp_ideal': amp_ideal,
        'impact_real': impact_real,
        'num_events': num_events,
        'total_score': total_score,
        'volatility': volatility,
        'surprise_max': surprise_max,
        'mean_empirical_score': mean_empirical_score,
        'mean_adjusted_score': mean_adjusted_score,
        'direction_numeric': direction_numeric
    })

conn.close()

df_enriched = pd.DataFrame(enriched_data)
print(f"   ✅ {len(df_enriched)} cas enrichis")
print()

# 5️⃣ Analyser les corrélations
print("5️⃣ Analyse des corrélations...")
print("-" * 80)

factors = {
    'r2_trend': 'R² tendance',
    'volatility': 'Volatilité pré-événement',
    'surprise_max': 'Surprise max (%)',
    'num_events': 'Nombre d\'événements',
    'mean_empirical_score': 'Score empirique moyen',
    'mean_adjusted_score': 'Score ajusté moyen',
    'total_score': 'Score total',
    'impact_real': 'Impact réel (pips)',
    'direction_numeric': 'Direction (1=UP, -1=DOWN)'
}

correlations = {}
for factor, label in factors.items():
    if factor in df_enriched.columns:
        corr, p_value = pearsonr(df_enriched[factor], df_enriched['amp_ideal'])
        correlations[factor] = {
            'label': label,
            'correlation': corr,
            'p_value': p_value,
            'abs_corr': abs(corr)
        }

# Trier par corrélation absolue
sorted_correlations = sorted(correlations.items(), key=lambda x: x[1]['abs_corr'], reverse=True)

print("   Corrélations avec amplification idéale :")
print()
for factor, data in sorted_correlations:
    sig = "***" if data['p_value'] < 0.001 else "**" if data['p_value'] < 0.01 else "*" if data['p_value'] < 0.05 else ""
    print(f"   {data['label']:30s} : {data['correlation']:7.4f} (p={data['p_value']:.4f}) {sig}")
print()

# 6️⃣ Modèle de régression multiple
print("6️⃣ Modèle de régression multiple...")
print("-" * 80)

# Sélectionner les facteurs les plus corrélés (sauf amp_ideal et impact_real)
top_factors = [f for f, _ in sorted_correlations[:5] if f not in ['amp_ideal', 'impact_real']]

X = df_enriched[top_factors].values
y = df_enriched['amp_ideal'].values

model = LinearRegression()
model.fit(X, y)
y_pred = model.predict(X)

r2 = r2_score(y, y_pred)
mae = mean_absolute_error(y, y_pred)

print(f"   Facteurs utilisés : {', '.join([factors[f] for f in top_factors])}")
print(f"   R² : {r2:.4f}")
print(f"   MAE : {mae:.4f}")
print()
print("   Coefficients :")
for i, factor in enumerate(top_factors):
    print(f"     {factors[factor]:30s} : {model.coef_[i]:8.4f}")
print(f"     {'Intercept':30s} : {model.intercept_:8.4f}")
print()

# 7️⃣ Sauvegarder les résultats
print("7️⃣ Sauvegarde des résultats...")
print("-" * 80)

output_dir = PROJECT_ROOT / 'scripts' / 'exploration_amplification_factors'
output_dir.mkdir(exist_ok=True)

df_enriched.to_csv(output_dir / 'enriched_data.csv', index=False)

results = {
    'n_samples': len(df_enriched),
    'correlations': {k: {'label': v['label'], 'correlation': float(v['correlation']), 'p_value': float(v['p_value'])} 
                     for k, v in correlations.items()},
    'regression_model': {
        'factors': top_factors,
        'factor_labels': [factors[f] for f in top_factors],
        'coefficients': model.coef_.tolist(),
        'intercept': float(model.intercept_),
        'r2': float(r2),
        'mae': float(mae)
    }
}

import json
with open(output_dir / 'correlation_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"   ✅ Données enrichies sauvegardées : {output_dir / 'enriched_data.csv'}")
print(f"   ✅ Résultats sauvegardés : {output_dir / 'correlation_results.json'}")
print()

print("=" * 80)
print("✅ EXPLORATION TERMINÉE")
print("=" * 80)

