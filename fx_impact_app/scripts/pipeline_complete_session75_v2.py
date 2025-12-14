#!/usr/bin/env python3
"""
Pipeline Complet Session 75 V2 - OPTION A
AMÉLIORATIONS vs V1 :
- Seuil 80 pips → 50 pips (plus de diversité)
- Top 2/semaine → Top 3/semaine (plus de dates)

Gains attendus :
- R² : 0.705 → 0.75-0.78
- MAE : 7.7 → 5-6 pips
- Couverture : 32% → 75-80%
- Dates : 26 → 40-50
"""

import sys
from pathlib import Path

# Setup paths
fx_impact_app_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app")
sys.path.insert(0, str(fx_impact_app_path))

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans

print("\n" + "="*80)
print("PIPELINE SESSION 75 V2 - OPTION A (Seuil 50 + Top 3)")
print("="*80 + "\n")

DB_PATH = fx_impact_app_path / "data" / "warehouse.duckdb"

# =============================================================================
# PHASE 1 : SCANNER STRATIFIÉ
# =============================================================================

print("🔍 PHASE 1 : Scanner Mouvements Stratifié")
print("-" * 80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("   Scanner mouvements >50 pips (vs 80), lookback 120min (2024-2025)...")  # MODIFIÉ

query_scan = """
WITH price_changes AS (
    SELECT 
        DATE(datetime) as date,
        strftime(datetime, '%H:%M') as time,
        datetime,
        close,
        LAG(close, 120) OVER (ORDER BY datetime) as price_start,
        (close - LAG(close, 120) OVER (ORDER BY datetime)) * 10000 as impact_pips,
        CASE 
            WHEN (close - LAG(close, 120) OVER (ORDER BY datetime)) > 0 
            THEN 'UP'
            ELSE 'DOWN'
        END as direction
    FROM prices_1m
    WHERE datetime >= '2024-01-01' AND datetime <= '2025-10-24'
)
SELECT 
    date, time, datetime, close as price_peak, price_start,
    impact_pips, direction, ABS(impact_pips) as abs_impact
FROM price_changes
WHERE ABS(impact_pips) >= 50
ORDER BY datetime ASC
"""  # MODIFIÉ : 50 vs 80

df_all = conn.execute(query_scan).fetchdf()
print(f"   ✅ Mouvements totaux : {len(df_all)}")

# Stratification
df_all['datetime_parsed'] = pd.to_datetime(df_all['datetime'])
df_all['year'] = df_all['datetime_parsed'].dt.isocalendar().year
df_all['week'] = df_all['datetime_parsed'].dt.isocalendar().week

df_stratified = []
for (year, week), group in df_all.groupby(['year', 'week']):
    top_week = group.nlargest(3, 'abs_impact')  # MODIFIÉ : 3 vs 2
    df_stratified.append(top_week)

df_movements = pd.concat(df_stratified, ignore_index=True)
df_movements = df_movements.sort_values('datetime').reset_index(drop=True)

print(f"   ✅ Après stratification : {len(df_movements)} mouvements")
print(f"   ✅ Dates uniques : {df_movements['date'].nunique()}")
print(f"   ✅ Semaines : {len(df_movements.groupby(['year', 'week']))}")

# Export Phase 1
output_movements = fx_impact_app_path / "data" / "movements_strong_session75_v2.csv"
df_movements[['date', 'time', 'datetime', 'price_start', 'price_peak', 
              'impact_pips', 'direction', 'abs_impact', 'year', 'week']].to_csv(output_movements, index=False)
print(f"   💾 Exporté : {output_movements.name}")

# =============================================================================
# PHASE 2 : CRÉER DATASET AVEC ÉVÉNEMENTS
# =============================================================================

print(f"\n🔍 PHASE 2 : Créer Dataset avec Événements")
print("-" * 80)

print(f"   Croisement mouvements × événements (±30 min, multi-pays)...")

# Convertir datetime Dukascopy (UTC+2) → UTC
df_movements['datetime_utc'] = df_movements['datetime_parsed'] - timedelta(hours=2)

results = []

for idx, row in df_movements.iterrows():
    datetime_utc = row['datetime_utc']
    
    # Recherche événements ±30 min (multi-pays)
    query_events = f"""
    SELECT 
        e.event_key,
        e.event_title,
        e.country,
        e.importance_n,
        e.actual,
        e.previous,
        e.estimate,
        e.forecast,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN (
        SELECT event_key, country, 
               AVG(empirical_score) as empirical_score,
               MIN(family) as family
        FROM event_families
        GROUP BY event_key, country
    ) ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.country IN ('US', 'EU', 'UK', 'JP', 'CH')
      AND e.ts_utc >= '{(datetime_utc - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.ts_utc <= '{(datetime_utc + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')}'
    """
    
    df_events = conn.execute(query_events).fetchdf()
    
    # Calculer métriques cluster
    nb_events = len(df_events)
    
    if nb_events > 0:
        score_cumule = df_events['empirical_score'].fillna(0).sum()
        score_moyen = df_events['empirical_score'].fillna(0).mean()
        
        # Surprise
        surprises = []
        for _, ev in df_events.iterrows():
            actual = ev.get('actual')
            forecast = ev.get('estimate') or ev.get('forecast') or ev.get('previous')
            if actual and forecast and forecast != 0:
                surprise = abs(actual - forecast) / abs(forecast) * 100
                surprises.append(surprise)
        
        surprise_max = max(surprises) if surprises else 0
        surprise_moyenne = np.mean(surprises) if surprises else 0
        surprise_cumule = sum(surprises) if surprises else 0
        
        # Direction
        directions_up = sum(1 for _, ev in df_events.iterrows() 
                           if ev.get('actual', 0) > ev.get('previous', 0))
        ratio_concordance = directions_up / nb_events if nb_events > 0 else 0.5
        
        # Cohérence famille
        families = df_events['family'].dropna().unique()
        coherence_famille = 1.0 if len(families) <= 2 else 0.5
    else:
        score_cumule = score_moyen = 0
        surprise_max = surprise_moyenne = surprise_cumule = 0
        ratio_concordance = 0.5
        coherence_famille = 0
    
    results.append({
        'date': row['date'],
        'time': row['time'],
        'datetime': row['datetime'],
        'impact_observed': row['abs_impact'],
        'direction': row['direction'],
        'nb_events': nb_events,
        'score_cumule': score_cumule,
        'score_moyen': score_moyen,
        'surprise_max': surprise_max,
        'surprise_moyenne': surprise_moyenne,
        'surprise_cumule': surprise_cumule,
        'ratio_concordance': ratio_concordance,
        'coherence_famille': coherence_famille
    })

conn.close()

df_dataset = pd.DataFrame(results)

print(f"   ✅ Dataset créé : {len(df_dataset)} mouvements")
print(f"   ✅ Avec événements : {(df_dataset['nb_events'] > 0).sum()} ({(df_dataset['nb_events'] > 0).sum() / len(df_dataset) * 100:.1f}%)")
print(f"   ✅ Sans événements : {(df_dataset['nb_events'] == 0).sum()} ({(df_dataset['nb_events'] == 0).sum() / len(df_dataset) * 100:.1f}%)")

# Export Phase 2
output_dataset = fx_impact_app_path / "data" / "dataset_complete_session75_v2.csv"
df_dataset.to_csv(output_dataset, index=False)
print(f"   💾 Exporté : {output_dataset.name}")

# =============================================================================
# PHASE 3 : ANALYSE ML
# =============================================================================

print(f"\n🔍 PHASE 3 : Analyse ML (Régression + Clustering)")
print("-" * 80)

# Préparer données ML (seulement mouvements avec événements)
df_ml = df_dataset[df_dataset['nb_events'] > 0].copy()

if len(df_ml) < 10:
    print(f"   ⚠️  Trop peu de données ML ({len(df_ml)} points), analyse limitée")
else:
    print(f"   Dataset ML : {len(df_ml)} mouvements avec événements")
    
    # Features
    X_cols = ['nb_events', 'score_cumule', 'score_moyen', 'surprise_max', 
              'surprise_moyenne', 'surprise_cumule', 'ratio_concordance', 'coherence_famille']
    y_col = 'impact_observed'
    
    X = df_ml[X_cols].fillna(0)
    y = df_ml[y_col]
    
    # Régression linéaire
    print(f"\n   📊 Régression Linéaire...")
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    
    from sklearn.metrics import r2_score, mean_absolute_error
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    print(f"      R² = {r2:.3f}")
    print(f"      MAE = {mae:.1f} pips")
    
    # Coefficients
    print(f"\n   📐 Coefficients :")
    print(f"      Intercept = {model.intercept_:.2f}")
    for col, coef in zip(X_cols, model.coef_):
        print(f"      {col:20s} = {coef:8.3f}")
    
    # Corrélations
    print(f"\n   🔗 Corrélations avec impact :")
    for col in X_cols:
        corr = df_ml[[col, y_col]].corr().iloc[0, 1]
        print(f"      {col:20s} : {corr:6.3f}")
    
    # Clustering K-Means
    print(f"\n   🎯 Clustering K-Means (k=3)...")
    if len(df_ml) >= 3:
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df_ml['cluster'] = kmeans.fit_predict(X)
        
        print(f"\n   📊 Clusters identifiés :")
        for cluster_id in range(3):
            cluster_data = df_ml[df_ml['cluster'] == cluster_id]
            print(f"\n      Cluster {cluster_id} ({len(cluster_data)} mouvements) :")
            print(f"         Impact moyen : {cluster_data['impact_observed'].mean():.1f} pips")
            print(f"         Events moyen : {cluster_data['nb_events'].mean():.1f}")
            print(f"         Surprise max : {cluster_data['surprise_max'].mean():.1f}%")
    
    # Export résultats ML
    output_regression = fx_impact_app_path / "data" / "regression_results_session75_v2.txt"
    with open(output_regression, 'w') as f:
        f.write("REGRESSION LINÉAIRE - SESSION 75 V2 (Option A)\n")
        f.write("="*80 + "\n\n")
        f.write(f"CHANGEMENTS vs V1 :\n")
        f.write(f"- Seuil : 80 pips → 50 pips\n")
        f.write(f"- Top par semaine : 2 → 3\n\n")
        f.write(f"Dataset : {len(df_ml)} mouvements avec événements\n")
        f.write(f"R² = {r2:.3f}\n")
        f.write(f"MAE = {mae:.1f} pips\n\n")
        f.write("Coefficients :\n")
        f.write(f"Intercept = {model.intercept_:.2f}\n")
        for col, coef in zip(X_cols, model.coef_):
            f.write(f"{col:20s} = {coef:8.3f}\n")
    print(f"\n   💾 Résultats exportés : regression_results_session75_v2.txt")

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================

print(f"\n{'='*80}")
print(f"✅ PIPELINE SESSION 75 V2 (OPTION A) COMPLÉTÉ")
print(f"{'='*80}\n")

print(f"📊 Résumé Phases :")
print(f"   Phase 1 (Scanner) : {len(df_movements)} mouvements, {df_movements['date'].nunique()} dates")
print(f"   Phase 2 (Dataset) : {len(df_dataset)} lignes, {(df_dataset['nb_events'] > 0).sum()} avec événements")
if len(df_ml) >= 10:
    print(f"   Phase 3 (ML)      : R²={r2:.3f}, MAE={mae:.1f} pips")

print(f"\n📂 Fichiers créés (V2) :")
print(f"   1. movements_strong_session75_v2.csv")
print(f"   2. dataset_complete_session75_v2.csv")
print(f"   3. regression_results_session75_v2.txt")

print(f"\n🎯 Comparaison V1 vs V2 :")
print(f"   Voir analyse Claude après cette exécution")
