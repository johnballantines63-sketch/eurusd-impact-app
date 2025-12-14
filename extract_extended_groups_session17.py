"""
SESSION 17 - EXTRACTION ÉTENDUE D'ÉVÉNEMENTS (VERSION CORRECTE)
Utilise la table event_group_impacts (groupes calculés en Session 8-9)
Extraction de 120 groupes supplémentaires pour validation formule V2
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Connexion à la base de données
DB_PATH = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("📊 SESSION 17 - EXTRACTION ÉTENDUE DE GROUPES D'ÉVÉNEMENTS")
print("=" * 80)
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Charger les événements Session 15 (à exclure)
# ════════════════════════════════════════════════════════════════

print("🔍 Chargement des événements Session 15 (à exclure)...")

session15_file = Path(__file__).parent / "extracted_events_session15.csv"
if session15_file.exists():
    session15_df = pd.read_csv(session15_file)
    # Convertir ts_utc en datetime puis extraire uniquement la partie date+heure (minute)
    # Format attendu : '2024-01-01 23:00:00'
    session15_df['ts_utc_parsed'] = pd.to_datetime(session15_df['ts_utc'], utc=True)
    excluded_timestamps = set(session15_df['ts_utc_parsed'].dt.floor('1min').dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
    print(f"   ✅ {len(excluded_timestamps)} timestamps Session 15 à exclure")
else:
    excluded_timestamps = set()
    print("   ⚠️ Fichier Session 15 non trouvé, aucune exclusion")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Exploration event_group_impacts
# ════════════════════════════════════════════════════════════════

print("📊 Analyse de la table event_group_impacts...")
print()

# Statistiques globales
stats_query = """
SELECT 
    COUNT(*) as total_groups,
    MIN(time_group) as first_date,
    MAX(time_group) as last_date,
    AVG(num_events) as avg_events_per_group,
    AVG(mfe_pips) as avg_mfe_pips,
    AVG(max_empirical_score) as avg_max_score,
    AVG(mean_empirical_score) as avg_mean_score
FROM event_group_impacts
"""

stats = conn.execute(stats_query).fetchdf()
print("📋 Statistiques globales :")
print(f"   Total groupes : {stats['total_groups'].iloc[0]:,}")
print(f"   Période : {stats['first_date'].iloc[0]} → {stats['last_date'].iloc[0]}")
print(f"   Événements/groupe (moy.) : {stats['avg_events_per_group'].iloc[0]:.2f}")
print(f"   MFE moyen : {stats['avg_mfe_pips'].iloc[0]:.2f} pips")
print(f"   Score max moyen : {stats['avg_max_score'].iloc[0]:.2f}")
print(f"   Score mean moyen : {stats['avg_mean_score'].iloc[0]:.2f}")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Préparer les données avec surprises
# ════════════════════════════════════════════════════════════════

print("🔧 Préparation des données avec calcul de surprise...")
print()

# Requête pour obtenir les groupes avec données de surprise
# On doit rejoindre avec la table events pour obtenir actual et estimate
query_prepare = """
WITH group_surprises AS (
    SELECT 
        g.time_group,
        g.num_events,
        g.max_empirical_score,
        g.mean_empirical_score,
        g.mfe_pips,
        g.event_keys,
        g.event_titles,
        g.countries,
        -- Obtenir les données de surprise depuis events
        -- On prend la surprise maximale du groupe
        (
            SELECT MAX(
                CASE 
                    WHEN e.estimate IS NOT NULL AND e.estimate != 0 
                    THEN ABS((e.actual - e.estimate) / e.estimate) * 100.0
                    ELSE 0
                END
            )
            FROM events e
            WHERE strftime(e.ts_utc, '%Y-%m-%d %H:%M:00') = strftime(g.time_group, '%Y-%m-%d %H:%M:00')
              AND e.actual IS NOT NULL
              AND e.estimate IS NOT NULL
              AND e.estimate != 0
        ) as max_surprise_pct,
        -- Année pour stratification
        CAST(strftime(g.time_group, '%Y') AS INTEGER) as year
    FROM event_group_impacts g
    WHERE g.mfe_pips IS NOT NULL
      AND g.max_empirical_score IS NOT NULL
      AND g.max_empirical_score > 0
)
SELECT *
FROM group_surprises
WHERE max_surprise_pct IS NOT NULL
  AND max_surprise_pct < 500  -- Exclure aberrations
ORDER BY time_group DESC
"""

all_groups_df = conn.execute(query_prepare).fetchdf()

print(f"📊 Groupes disponibles avec surprise : {len(all_groups_df):,}")
print()

# Exclure les timestamps de Session 15
# Convertir time_group en format comparable
all_groups_df['time_group_str'] = pd.to_datetime(all_groups_df['time_group']).dt.strftime('%Y-%m-%d %H:%M:%S')
all_groups_df = all_groups_df[~all_groups_df['time_group_str'].isin(excluded_timestamps)]

print(f"📊 Groupes après exclusion Session 15 : {len(all_groups_df):,}")
print()

# Statistiques par tranche de surprise
print("📈 Distribution par tranche de surprise :")
all_groups_df['surprise_range'] = pd.cut(
    all_groups_df['max_surprise_pct'],
    bins=[0, 5, 10, 20, 50, 500],
    labels=['0-5%', '5-10%', '10-20%', '20-50%', '>50%']
)
print(all_groups_df['surprise_range'].value_counts().sort_index())
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Extraction stratifiée de 120 groupes
# ════════════════════════════════════════════════════════════════

print("🎯 Extraction stratifiée de 120 groupes...")
print()

# Définir les quotas par tranche (30 par tranche)
quotas = {
    '0-5%': 30,
    '5-10%': 30,
    '10-20%': 30,
    '20-50%': 30
}

all_extracted = []

for surprise_range, quota in quotas.items():
    print(f"📌 Extraction tranche {surprise_range} (quota: {quota})...")
    
    # Filtrer cette tranche
    tranche_df = all_groups_df[all_groups_df['surprise_range'] == surprise_range].copy()
    
    if len(tranche_df) == 0:
        print(f"   ⚠️ Aucun groupe disponible pour cette tranche")
        print()
        continue
    
    # Échantillonner avec stratification par année si possible
    if len(tranche_df) >= quota:
        # Stratifier par année
        sampled_indices = []
        years_in_tranche = tranche_df['year'].unique()
        quota_per_year = quota // len(years_in_tranche)
        
        for year in years_in_tranche:
            year_df = tranche_df[tranche_df['year'] == year]
            n_sample = min(quota_per_year, len(year_df))
            if n_sample > 0:
                sampled = year_df.sample(n=n_sample, random_state=42)
                sampled_indices.extend(sampled.index.tolist())
        
        # Compléter si besoin
        remaining = quota - len(sampled_indices)
        if remaining > 0:
            not_sampled = tranche_df[~tranche_df.index.isin(sampled_indices)]
            if len(not_sampled) > 0:
                additional = not_sampled.sample(n=min(remaining, len(not_sampled)), random_state=42)
                sampled_indices.extend(additional.index.tolist())
        
        final_sample = tranche_df.loc[sampled_indices]
    else:
        # Prendre tous les groupes disponibles
        final_sample = tranche_df
    
    all_extracted.append(final_sample)
    
    print(f"   ✅ {len(final_sample)} groupes extraits")
    print(f"      Années : {final_sample['year'].value_counts().to_dict()}")
    print(f"      Pays : {final_sample['countries'].str.split('+').str[0].value_counts().head(3).to_dict()}")
    print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Combiner et sauvegarder
# ════════════════════════════════════════════════════════════════

if all_extracted:
    final_df = pd.concat(all_extracted, ignore_index=True)
    
    # Sélectionner les colonnes pertinentes
    output_df = final_df[[
        'time_group',
        'num_events',
        'event_keys',
        'event_titles',
        'countries',
        'max_empirical_score',
        'mean_empirical_score',
        'mfe_pips',
        'max_surprise_pct',
        'year'
    ]].copy()
    
    # Renommer pour cohérence
    output_df.rename(columns={
        'mfe_pips': 'impact_reel_pips',
        'max_surprise_pct': 'surprise_pct'
    }, inplace=True)
    
    # Sauvegarder
    output_file = Path(__file__).parent / "extracted_groups_session17.csv"
    output_df.to_csv(output_file, index=False)
    
    print("=" * 80)
    print("✅ EXTRACTION TERMINÉE")
    print("=" * 80)
    print()
    print(f"📁 Fichier : {output_file.name}")
    print(f"📊 Total groupes : {len(output_df)}")
    print()
    
    # Statistiques finales
    print("📈 STATISTIQUES FINALES :")
    print()
    
    print("Par tranche de surprise :")
    output_df['surprise_range'] = pd.cut(
        output_df['surprise_pct'],
        bins=[0, 5, 10, 20, 50],
        labels=['0-5%', '5-10%', '10-20%', '20-50%']
    )
    print(output_df['surprise_range'].value_counts().sort_index())
    print()
    
    print("Par année :")
    print(output_df['year'].value_counts().sort_index())
    print()
    
    print("Par nombre d'événements dans le groupe :")
    print(output_df['num_events'].value_counts().sort_index().head(10))
    print()
    
    # Statistiques globales
    print("📊 STATISTIQUES GLOBALES :")
    print(f"   Surprise moyenne : {output_df['surprise_pct'].mean():.2f}%")
    print(f"   Surprise médiane : {output_df['surprise_pct'].median():.2f}%")
    print(f"   Score max moyen : {output_df['max_empirical_score'].mean():.2f}")
    print(f"   Score max médian : {output_df['max_empirical_score'].median():.2f}")
    print(f"   Score mean moyen : {output_df['mean_empirical_score'].mean():.2f}")
    print(f"   Impact réel moyen : {output_df['impact_reel_pips'].mean():.2f} pips")
    print(f"   Impact réel médian : {output_df['impact_reel_pips'].median():.2f} pips")
    print()
    
    print("=" * 80)
    print("🎯 PROCHAINE ÉTAPE : Mesurer impacts avec formules V1 et V2")
    print("=" * 80)
    
else:
    print("❌ ERREUR : Aucun groupe extrait")

conn.close()
