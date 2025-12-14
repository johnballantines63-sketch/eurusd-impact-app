#!/usr/bin/env python3
"""
Pipeline Complet Session 75 V3 - OPTION B'
STRATÉGIE : V1 (seuil 80) + Features contextuels

AMÉLIORATIONS vs V1 :
- Même dataset robuste (seuil 80, top 2/semaine)
- + 4 features contextuels :
  1. time_of_day (session trading)
  2. day_of_week (liquidité)
  3. event_type (CPI/NFP/GDP/etc)
  4. country (US/EU/UK/JP/CH)

Gains attendus :
- R² : 0.705 → 0.75-0.78
- MAE : 7.7 → 6-7 pips
- Meilleure compréhension contexte
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
print("PIPELINE SESSION 75 V3 - OPTION B' (V1 + Features)")
print("="*80 + "\n")

DB_PATH = fx_impact_app_path / "data" / "warehouse.duckdb"

# =============================================================================
# PHASE 1 : SCANNER STRATIFIÉ (IDENTIQUE V1)
# =============================================================================

print("🔍 PHASE 1 : Scanner Mouvements Stratifié")
print("-" * 80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("   Scanner mouvements >80 pips, lookback 120min (2024-2025)...")

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
WHERE ABS(impact_pips) >= 80
ORDER BY datetime ASC
"""

df_all = conn.execute(query_scan).fetchdf()
print(f"   ✅ Mouvements totaux : {len(df_all)}")

# Stratification
df_all['datetime_parsed'] = pd.to_datetime(df_all['datetime'])
df_all['year'] = df_all['datetime_parsed'].dt.isocalendar().year
df_all['week'] = df_all['datetime_parsed'].dt.isocalendar().week

df_stratified = []
for (year, week), group in df_all.groupby(['year', 'week']):
    top_week = group.nlargest(2, 'abs_impact')  # Top 2 (V1)
    df_stratified.append(top_week)

df_movements = pd.concat(df_stratified, ignore_index=True)
df_movements = df_movements.sort_values('datetime').reset_index(drop=True)

print(f"   ✅ Après stratification : {len(df_movements)} mouvements")
print(f"   ✅ Dates uniques : {df_movements['date'].nunique()}")
print(f"   ✅ Semaines : {len(df_movements.groupby(['year', 'week']))}")

# Export Phase 1
output_movements = fx_impact_app_path / "data" / "movements_strong_session75_v3.csv"
df_movements[['date', 'time', 'datetime', 'price_start', 'price_peak', 
              'impact_pips', 'direction', 'abs_impact', 'year', 'week']].to_csv(output_movements, index=False)
print(f"   💾 Exporté : {output_movements.name}")

# =============================================================================
# PHASE 2 : CRÉER DATASET AVEC ÉVÉNEMENTS + FEATURES CONTEXTUELS
# =============================================================================

print(f"\n🔍 PHASE 2 : Créer Dataset avec Événements + Features")
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
        
        # NOUVEAU : Extraire event_type et country dominant
        event_titles = ' '.join(df_events['event_title'].fillna('').tolist()).lower()
        
        # Event type (priorité : CPI > NFP > GDP > Retail > PMI > Other)
        if 'cpi' in event_titles or 'inflation' in event_titles:
            event_type = 'CPI'
        elif 'nfp' in event_titles or 'employment' in event_titles or 'payroll' in event_titles:
            event_type = 'NFP'
        elif 'gdp' in event_titles:
            event_type = 'GDP'
        elif 'retail' in event_titles:
            event_type = 'Retail'
        elif 'pmi' in event_titles:
            event_type = 'PMI'
        else:
            event_type = 'Other'
        
        # Country dominant (mode)
        country_main = df_events['country'].mode()[0] if len(df_events) > 0 else 'Unknown'
        
    else:
        score_cumule = score_moyen = 0
        surprise_max = surprise_moyenne = surprise_cumule = 0
        ratio_concordance = 0.5
        coherence_famille = 0
        event_type = 'None'
        country_main = 'None'
    
    # NOUVEAU : Features contextuels
    hour_utc = datetime_utc.hour
    
    # Time of day (session trading)
    if 13 <= hour_utc <= 21:
        time_of_day = 'US'
    elif 7 <= hour_utc <= 16:
        time_of_day = 'EU'
    else:
        time_of_day = 'Asia'
    
    # Day of week (0=Lundi, 4=Vendredi)
    day_of_week = datetime_utc.weekday()
    
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
        'coherence_famille': coherence_famille,
        # NOUVEAUX FEATURES
        'time_of_day': time_of_day,
        'day_of_week': day_of_week,
        'event_type': event_type,
        'country': country_main
    })

conn.close()

df_dataset = pd.DataFrame(results)

print(f"   ✅ Dataset créé : {len(df_dataset)} mouvements")
print(f"   ✅ Avec événements : {(df_dataset['nb_events'] > 0).sum()} ({(df_dataset['nb_events'] > 0).sum() / len(df_dataset) * 100:.1f}%)")
print(f"   ✅ Sans événements : {(df_dataset['nb_events'] == 0).sum()} ({(df_dataset['nb_events'] == 0).sum() / len(df_dataset) * 100:.1f}%)")

# Distribution features
print(f"\n   📊 Distribution Features Contextuels :")
print(f"      time_of_day : {df_dataset['time_of_day'].value_counts().to_dict()}")
print(f"      event_type : {df_dataset[df_dataset['nb_events'] > 0]['event_type'].value_counts().to_dict()}")
print(f"      country : {df_dataset[df_dataset['nb_events'] > 0]['country'].value_counts().to_dict()}")

# Export Phase 2
output_dataset = fx_impact_app_path / "data" / "dataset_complete_session75_v3.csv"
df_dataset.to_csv(output_dataset, index=False)
print(f"   💾 Exporté : {output_dataset.name}")

# =============================================================================
# PHASE 3 : ANALYSE ML AVEC FEATURES
# =============================================================================

print(f"\n🔍 PHASE 3 : Analyse ML avec Features Contextuels")
print("-" * 80)

# Préparer données ML (seulement mouvements avec événements)
df_ml = df_dataset[df_dataset['nb_events'] > 0].copy()

if len(df_ml) < 10:
    print(f"   ⚠️  Trop peu de données ML ({len(df_ml)} points), analyse limitée")
else:
    print(f"   Dataset ML : {len(df_ml)} mouvements avec événements")
    
    # Encoder features catégoriels
    # time_of_day : US=2, EU=1, Asia=0
    time_of_day_map = {'Asia': 0, 'EU': 1, 'US': 2}
    df_ml['time_of_day_encoded'] = df_ml['time_of_day'].map(time_of_day_map)
    
    # event_type : CPI=5, NFP=4, GDP=3, Retail=2, PMI=1, Other=0
    event_type_map = {'Other': 0, 'PMI': 1, 'Retail': 2, 'GDP': 3, 'NFP': 4, 'CPI': 5}
    df_ml['event_type_encoded'] = df_ml['event_type'].map(event_type_map)
    
    # country : US=2, EU=1, Others=0
    country_map = {'US': 2, 'EU': 1}
    df_ml['country_encoded'] = df_ml['country'].map(country_map).fillna(0)
    
    # Features ML : 8 originaux + 4 nouveaux
    X_cols = ['nb_events', 'score_cumule', 'score_moyen', 'surprise_max', 
              'surprise_moyenne', 'surprise_cumule', 'ratio_concordance', 'coherence_famille',
              'time_of_day_encoded', 'day_of_week', 'event_type_encoded', 'country_encoded']
    y_col = 'impact_observed'
    
    X = df_ml[X_cols].fillna(0)
    y = df_ml[y_col]
    
    # Régression linéaire
    print(f"\n   📊 Régression Linéaire (12 features vs 8)...")
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
        marker = " 🆕" if col in ['time_of_day_encoded', 'day_of_week', 'event_type_encoded', 'country_encoded'] else ""
        print(f"      {col:25s} = {coef:8.3f}{marker}")
    
    # Corrélations
    print(f"\n   🔗 Corrélations avec impact :")
    for col in X_cols:
        corr = df_ml[[col, y_col]].corr().iloc[0, 1]
        marker = " 🆕" if col in ['time_of_day_encoded', 'day_of_week', 'event_type_encoded', 'country_encoded'] else ""
        print(f"      {col:25s} : {corr:6.3f}{marker}")
    
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
            print(f"         Event type dominant : {cluster_data['event_type'].mode()[0] if len(cluster_data) > 0 else 'N/A'}")
            print(f"         Session dominante : {cluster_data['time_of_day'].mode()[0] if len(cluster_data) > 0 else 'N/A'}")
    
    # Export résultats ML
    output_regression = fx_impact_app_path / "data" / "regression_results_session75_v3.txt"
    with open(output_regression, 'w') as f:
        f.write("REGRESSION LINÉAIRE - SESSION 75 V3 (Option B')\n")
        f.write("="*80 + "\n\n")
        f.write(f"CHANGEMENTS vs V1 :\n")
        f.write(f"- Dataset identique (seuil 80, top 2/semaine)\n")
        f.write(f"- + 4 features contextuels (time_of_day, day_of_week, event_type, country)\n\n")
        f.write(f"Dataset : {len(df_ml)} mouvements avec événements\n")
        f.write(f"Features : 12 (vs 8 en V1)\n")
        f.write(f"R² = {r2:.3f}\n")
        f.write(f"MAE = {mae:.1f} pips\n\n")
        f.write("Coefficients :\n")
        f.write(f"Intercept = {model.intercept_:.2f}\n")
        for col, coef in zip(X_cols, model.coef_):
            marker = " [NEW]" if col in ['time_of_day_encoded', 'day_of_week', 'event_type_encoded', 'country_encoded'] else ""
            f.write(f"{col:25s} = {coef:8.3f}{marker}\n")
    print(f"\n   💾 Résultats exportés : regression_results_session75_v3.txt")

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================

print(f"\n{'='*80}")
print(f"✅ PIPELINE SESSION 75 V3 (OPTION B') COMPLÉTÉ")
print(f"{'='*80}\n")

print(f"📊 Résumé Phases :")
print(f"   Phase 1 (Scanner) : {len(df_movements)} mouvements, {df_movements['date'].nunique()} dates")
print(f"   Phase 2 (Dataset) : {len(df_dataset)} lignes, {(df_dataset['nb_events'] > 0).sum()} avec événements")
if len(df_ml) >= 10:
    print(f"   Phase 3 (ML)      : R²={r2:.3f}, MAE={mae:.1f} pips")

print(f"\n📂 Fichiers créés (V3) :")
print(f"   1. movements_strong_session75_v3.csv")
print(f"   2. dataset_complete_session75_v3.csv")
print(f"   3. regression_results_session75_v3.txt")

print(f"\n🎯 Comparaison V1 vs V3 :")
print(f"   V1 (8 features) : R²=0.705, MAE=7.7 pips")
print(f"   V3 (12 features): R²={r2:.3f}, MAE={mae:.1f} pips")
if r2 > 0.705:
    improvement = ((r2 - 0.705) / 0.705) * 100
    print(f"   📈 Amélioration R² : +{improvement:.1f}%")
else:
    degradation = ((0.705 - r2) / 0.705) * 100
    print(f"   📉 Dégradation R² : -{degradation:.1f}%")
