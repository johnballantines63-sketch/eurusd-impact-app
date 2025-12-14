"""
SESSION 18 - VOLET 3 : PRÉPARATION MACHINE LEARNING
Objectif : Extraire features et structurer dataset pour ML futur
Focus : Prédire amplification optimale et identifier patterns prédictifs
Auteur : Claude
Date : 19 octobre 2025
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Connexion DB
db_path = Path('fx_impact_app/data/warehouse.duckdb')
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("🤖 VOLET 3 : PRÉPARATION MACHINE LEARNING")
print("=" * 80)

# ============================================================================
# PARTIE 1 : EXTRACTION FEATURES POUR ML
# ============================================================================

print("\n" + "=" * 80)
print("📊 PARTIE 1 : EXTRACTION FEATURES")
print("=" * 80)

query_ml_dataset = """
WITH event_details AS (
    SELECT 
        egi.time_group,
        egi.mfe_pips as target_impact,
        egi.reference_price,
        egi.num_events,
        
        -- Agrégations sur événements du groupe
        MAX(ef.empirical_score) as max_score,
        AVG(ef.empirical_score) as avg_score,
        SUM(ef.empirical_score) as sum_score,
        MIN(ef.empirical_score) as min_score,
        
        -- Surprises
        MAX(CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate) * 100
            ELSE 0 
        END) as max_surprise,
        AVG(CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate) * 100
            ELSE 0 
        END) as avg_surprise,
        
        -- Contexte temporel
        strftime(egi.time_group, '%H') as hour,
        strftime(egi.time_group, '%w') as day_of_week,
        strftime(egi.time_group, '%m') as month,
        strftime(egi.time_group, '%Y') as year,
        
        -- Pays dominants
        MAX(CASE WHEN e.country = 'US' THEN 1 ELSE 0 END) as has_us,
        MAX(CASE WHEN e.country = 'EU' THEN 1 ELSE 0 END) as has_eu,
        MAX(CASE WHEN e.country = 'GB' THEN 1 ELSE 0 END) as has_gb,
        MAX(CASE WHEN e.country = 'DE' THEN 1 ELSE 0 END) as has_de,
        MAX(CASE WHEN e.country = 'JP' THEN 1 ELSE 0 END) as has_jp,
        
        -- Types événements (features booléennes)
        MAX(CASE WHEN ef.category LIKE '%Employment%' THEN 1 ELSE 0 END) as has_employment,
        MAX(CASE WHEN ef.category LIKE '%Inflation%' THEN 1 ELSE 0 END) as has_inflation,
        MAX(CASE WHEN ef.category LIKE '%GDP%' THEN 1 ELSE 0 END) as has_gdp,
        MAX(CASE WHEN ef.category LIKE '%Interest%' THEN 1 ELSE 0 END) as has_interest,
        MAX(CASE WHEN ef.category LIKE '%Retail%' THEN 1 ELSE 0 END) as has_retail,
        MAX(CASE WHEN ef.category LIKE '%PMI%' THEN 1 ELSE 0 END) as has_pmi,
        MAX(CASE WHEN ef.category LIKE '%Consumer%' THEN 1 ELSE 0 END) as has_consumer,
        
        -- Composition
        STRING_AGG(DISTINCT e.country, ',') as countries,
        STRING_AGG(DISTINCT ef.category, ',') as categories
        
    FROM event_group_impacts egi
    INNER JOIN events e 
        ON strftime(e.ts_utc, '%Y-%m-%d %H:%M:00') = egi.time_group
    INNER JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE ef.empirical_score IS NOT NULL
        AND egi.mfe_pips IS NOT NULL
        AND egi.mfe_pips > 0
    GROUP BY egi.time_group, egi.mfe_pips, egi.reference_price, egi.num_events
)
SELECT * 
FROM event_details
ORDER BY time_group DESC
"""

df_ml = conn.execute(query_ml_dataset).df()

print(f"\n✅ Dataset ML extrait : {len(df_ml)} lignes")
print(f"\n📊 Statistiques des features :")
print(df_ml.describe())

# ============================================================================
# PARTIE 2 : FEATURES ENGINEERING AVANCÉES
# ============================================================================

print("\n" + "=" * 80)
print("🔧 PARTIE 2 : FEATURES ENGINEERING")
print("=" * 80)

# Convertir types
df_ml['hour'] = df_ml['hour'].astype(int)
df_ml['day_of_week'] = df_ml['day_of_week'].astype(int)
df_ml['month'] = df_ml['month'].astype(int)
df_ml['year'] = df_ml['year'].astype(int)

# Features calculées
df_ml['score_surprise_product'] = df_ml['max_score'] * df_ml['max_surprise']
df_ml['score_range'] = df_ml['max_score'] - df_ml['min_score']
df_ml['is_high_score'] = (df_ml['max_score'] >= 60).astype(int)
df_ml['is_high_surprise'] = (df_ml['max_surprise'] >= 10).astype(int)
df_ml['is_multi_country'] = (df_ml['countries'].str.count(',') >= 1).astype(int)

# Horaires trading importants
df_ml['is_london_open'] = ((df_ml['hour'] >= 8) & (df_ml['hour'] <= 16)).astype(int)
df_ml['is_ny_open'] = ((df_ml['hour'] >= 14) & (df_ml['hour'] <= 21)).astype(int)
df_ml['is_overlap'] = ((df_ml['hour'] >= 14) & (df_ml['hour'] <= 16)).astype(int)

# Target : Calculer l'amplification réelle observée
# Amplification = Impact réel / Impact base
df_ml['impact_base'] = -7.08 + 0.419 * df_ml['max_score']
df_ml['observed_amplification'] = df_ml['target_impact'] / df_ml['impact_base'].abs()

# Classer amplifications
df_ml['amplification_class'] = pd.cut(
    df_ml['observed_amplification'],
    bins=[0, 0.8, 1.2, 1.8, 2.5, 10],
    labels=['very_low', 'low', 'medium', 'high', 'very_high']
)

print("\n📊 Distribution amplification observée :")
print(df_ml['amplification_class'].value_counts())

# ============================================================================
# PARTIE 3 : CORRÉLATIONS ET INSIGHTS
# ============================================================================

print("\n" + "=" * 80)
print("📈 PARTIE 3 : CORRÉLATIONS ET INSIGHTS")
print("=" * 80)

# Colonnes numériques pour corrélation
numeric_cols = [
    'target_impact', 'num_events', 'max_score', 'avg_score', 'sum_score',
    'max_surprise', 'avg_surprise', 'score_surprise_product', 'score_range',
    'observed_amplification'
]

correlation_matrix = df_ml[numeric_cols].corr()

print("\n🎯 Top 10 corrélations avec target_impact :")
target_corr = correlation_matrix['target_impact'].sort_values(ascending=False)
print(target_corr.head(10))

print("\n🎯 Top 10 corrélations avec observed_amplification :")
amp_corr = correlation_matrix['observed_amplification'].sort_values(ascending=False)
print(amp_corr.head(10))

# ============================================================================
# PARTIE 4 : PATTERNS PRÉDICTIFS
# ============================================================================

print("\n" + "=" * 80)
print("🔍 PARTIE 4 : PATTERNS PRÉDICTIFS")
print("=" * 80)

# Pattern 1 : Impact par pays
print("\n📊 Impact moyen par présence de pays :")
for country_col in ['has_us', 'has_eu', 'has_gb', 'has_de', 'has_jp']:
    country = country_col.replace('has_', '').upper()
    avg_with = df_ml[df_ml[country_col] == 1]['target_impact'].mean()
    avg_without = df_ml[df_ml[country_col] == 0]['target_impact'].mean()
    print(f"  {country}: Avec = {avg_with:.1f} pips | Sans = {avg_without:.1f} pips")

# Pattern 2 : Impact par type événement
print("\n📊 Impact moyen par type d'événement :")
event_types = ['has_employment', 'has_inflation', 'has_gdp', 'has_interest', 
               'has_retail', 'has_pmi', 'has_consumer']

for event_col in event_types:
    event_type = event_col.replace('has_', '').capitalize()
    count = df_ml[df_ml[event_col] == 1].shape[0]
    if count > 0:
        avg = df_ml[df_ml[event_col] == 1]['target_impact'].mean()
        print(f"  {event_type}: {avg:.1f} pips (n={count})")

# Pattern 3 : Impact par heure
print("\n📊 Impact moyen par plage horaire :")
print(df_ml.groupby('hour')['target_impact'].agg(['mean', 'count']).round(1))

# Pattern 4 : Cas où amplification très haute (>2.5)
print("\n🔥 Cas amplification très haute (>2.5) :")
high_amp = df_ml[df_ml['observed_amplification'] > 2.5].copy()
if len(high_amp) > 0:
    print(f"  Nombre de cas : {len(high_amp)}")
    print(f"  Surprise moyenne : {high_amp['max_surprise'].mean():.1f}%")
    print(f"  Score moyen : {high_amp['max_score'].mean():.1f}")
    print(f"  Pays dominants : {high_amp['countries'].value_counts().head(5)}")

# Pattern 5 : Cas où amplification très basse (<0.8)
print("\n❄️ Cas amplification très basse (<0.8) :")
low_amp = df_ml[df_ml['observed_amplification'] < 0.8].copy()
if len(low_amp) > 0:
    print(f"  Nombre de cas : {len(low_amp)}")
    print(f"  Surprise moyenne : {low_amp['max_surprise'].mean():.1f}%")
    print(f"  Score moyen : {low_amp['max_score'].mean():.1f}")
    print(f"  Pays dominants : {low_amp['countries'].value_counts().head(5)}")

# ============================================================================
# PARTIE 5 : EXPORT DATASET ML
# ============================================================================

print("\n" + "=" * 80)
print("💾 PARTIE 5 : EXPORT DATASET ML")
print("=" * 80)

# Dataset complet
output_ml = 'ml_dataset_multi_events_session18.csv'
df_ml.to_csv(output_ml, index=False)
print(f"\n✅ Dataset ML complet exporté : {output_ml}")
print(f"   Lignes : {len(df_ml)}")
print(f"   Colonnes : {len(df_ml.columns)}")

# Dataset simplifié (features principales)
features_to_keep = [
    'time_group',
    'target_impact',
    'num_events',
    'max_score', 'avg_score', 'sum_score',
    'max_surprise', 'avg_surprise',
    'hour', 'day_of_week', 'month', 'year',
    'has_us', 'has_eu', 'has_gb', 'has_de', 'has_jp',
    'has_employment', 'has_inflation', 'has_gdp', 'has_interest',
    'is_high_score', 'is_high_surprise',
    'is_london_open', 'is_ny_open', 'is_overlap',
    'score_surprise_product',
    'observed_amplification',
    'amplification_class'
]

df_ml_simple = df_ml[features_to_keep].copy()
output_ml_simple = 'ml_dataset_simple_session18.csv'
df_ml_simple.to_csv(output_ml_simple, index=False)
print(f"✅ Dataset ML simplifié exporté : {output_ml_simple}")

# ============================================================================
# PARTIE 6 : RECOMMANDATIONS POUR ML
# ============================================================================

print("\n" + "=" * 80)
print("💡 PARTIE 6 : RECOMMANDATIONS MACHINE LEARNING")
print("=" * 80)

print("""
🎯 OBJECTIF ML RECOMMANDÉ :
   Prédire 'amplification_class' (classification)
   OU 'observed_amplification' (régression)

📊 FEATURES IMPORTANTES (basé sur corrélations) :
   - max_surprise (corrélation forte avec impact)
   - max_score (base de prédiction)
   - score_surprise_product (interaction)
   - has_us, has_eu (pays importants)
   - is_overlap (horaire important)

🤖 ALGORITHMES RECOMMANDÉS :
   1. Random Forest (classification ou régression)
      → Gère bien interactions entre features
      → Robuste aux outliers
      → Interprétable (feature importance)
   
   2. Gradient Boosting (XGBoost, LightGBM)
      → Très performant
      → Gère bien données déséquilibrées
   
   3. Neural Network (optionnel)
      → Si dataset grossit (>1000 lignes)
      → Peut capturer patterns complexes

📋 ÉTAPES SUIVANTES (Session ML future) :
   1. Split train/test (80/20) chronologique
   2. Normaliser features numériques
   3. Entraîner modèles multiples
   4. Valider sur événements récents (2025)
   5. Comparer vs formule V2 actuelle
   6. Intégrer meilleur modèle dans Planificateur

⚠️ ATTENTION :
   - Dataset actuel : {len(df_ml)} lignes
   - Recommandé : >500 pour ML robuste
   - Continuer à collecter données
   - Corriger données manquantes (estimate NULL)
""")

conn.close()

print("\n" + "=" * 80)
print("✅ VOLET 3 TERMINÉ !")
print("=" * 80)
