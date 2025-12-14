"""
SESSION 17 - EXTRACTION ÉTENDUE D'ÉVÉNEMENTS
Extraction de 120 événements supplémentaires pour validation formule V2
Échantillonnage stratifié par pays, type, année, surprise
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

# Connexion à la base de données
DB_PATH = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("📊 SESSION 17 - EXTRACTION ÉTENDUE D'ÉVÉNEMENTS")
print("=" * 80)
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Charger les événements Session 15 (à exclure)
# ════════════════════════════════════════════════════════════════

print("🔍 Chargement des événements Session 15 (à exclure)...")

session15_file = Path(__file__).parent / "extracted_events_session15.csv"
if session15_file.exists():
    session15_df = pd.read_csv(session15_file)
    # Créer un identifiant unique basé sur ts_utc + event_key + country
    session15_df['unique_id'] = (
        session15_df['ts_utc'].astype(str) + '_' + 
        session15_df['event_key'].astype(str) + '_' + 
        session15_df['country'].astype(str)
    )
    excluded_event_ids = set(session15_df['unique_id'].tolist())
    print(f"   ✅ {len(excluded_event_ids)} événements Session 15 chargés")
else:
    excluded_event_ids = set()
    print("   ⚠️ Fichier Session 15 non trouvé, aucune exclusion")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Statistiques disponibles
# ════════════════════════════════════════════════════════════════

print("📊 Analyse des événements disponibles...")
print()

query_stats = """
WITH usable_events AS (
    SELECT 
        e.*,
        ef.empirical_score,
        ef.avg_movement_pips,
        CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate) * 100.0
            ELSE NULL
        END as surprise_pct,
        CASE
            WHEN CAST(strftime(e.ts_utc, '%Y') AS INTEGER) = 2023 THEN '2023'
            WHEN CAST(strftime(e.ts_utc, '%Y') AS INTEGER) = 2024 THEN '2024'
            WHEN CAST(strftime(e.ts_utc, '%Y') AS INTEGER) = 2025 THEN '2025'
            ELSE 'other'
        END as year_group
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.actual IS NOT NULL
      AND e.estimate IS NOT NULL
      AND e.estimate != 0
      AND ef.empirical_score IS NOT NULL
      AND ef.empirical_score > 0
      AND e.importance = 'HIGH'
)
SELECT
    year_group,
    country,
    CASE
        WHEN surprise_pct < 5 THEN '0-5%'
        WHEN surprise_pct < 10 THEN '5-10%'
        WHEN surprise_pct < 20 THEN '10-20%'
        WHEN surprise_pct < 50 THEN '20-50%'
        ELSE '>50%'
    END as surprise_range,
    COUNT(*) as count
FROM usable_events
WHERE surprise_pct IS NOT NULL
  AND surprise_pct < 500  -- Exclure aberrations
GROUP BY year_group, country, surprise_range
ORDER BY year_group, country, surprise_range
"""

stats_df = conn.execute(query_stats).fetchdf()
print("📋 Événements disponibles par année/pays/surprise :")
print()
print(stats_df.to_string(index=False))
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Extraction stratifiée
# ════════════════════════════════════════════════════════════════

print("🎯 Extraction stratifiée de 120 événements supplémentaires...")
print()

# Définir les quotas par tranche
quotas = {
    '0-5%': 30,
    '5-10%': 30,
    '10-20%': 30,
    '20-50%': 30
}

# Définir les proportions par pays (approximatives)
country_weights = {
    'US': 0.40,
    'EU': 0.25,
    'GB': 0.15,
    'DE': 0.08,
    'IT': 0.07,
    'AU': 0.05
}

# Définir les proportions par année
year_weights = {
    '2023': 0.33,
    '2024': 0.33,
    '2025': 0.34
}

all_extracted = []

for surprise_range, quota in quotas.items():
    print(f"📌 Extraction tranche {surprise_range} (quota: {quota})...")
    
    # Requête pour cette tranche
    if surprise_range == '0-5%':
        condition = "surprise_pct < 5"
    elif surprise_range == '5-10%':
        condition = "surprise_pct >= 5 AND surprise_pct < 10"
    elif surprise_range == '10-20%':
        condition = "surprise_pct >= 10 AND surprise_pct < 20"
    elif surprise_range == '20-50%':
        condition = "surprise_pct >= 20 AND surprise_pct < 50"
    
    query_extract = f"""
    WITH usable_events AS (
        SELECT 
            e.ts_utc,
            e.country,
            e.event_key,
            e.event_title,
            e.actual,
            e.estimate,
            e.importance,
            ef.empirical_score,
            ef.avg_movement_pips,
            ef.event_type,
            CASE 
                WHEN e.estimate IS NOT NULL AND e.estimate != 0 
                THEN ABS((e.actual - e.estimate) / e.estimate) * 100.0
                ELSE NULL
            END as surprise_pct,
            CAST(strftime(e.ts_utc, '%Y') AS INTEGER) as year
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.actual IS NOT NULL
          AND e.estimate IS NOT NULL
          AND e.estimate != 0
          AND ef.empirical_score IS NOT NULL
          AND ef.empirical_score > 0
          AND e.importance = 'HIGH'
          AND {condition}
          AND surprise_pct < 500  -- Exclure aberrations
    )
    SELECT *
    FROM usable_events
    ORDER BY RANDOM()
    LIMIT {quota * 3}  -- Extraire plus pour pouvoir filtrer
    """
    
    df_tranche = conn.execute(query_extract).fetchdf()
    
    # Créer l'identifiant unique pour cette tranche
    df_tranche['unique_id'] = (
        df_tranche['ts_utc'].astype(str) + '_' + 
        df_tranche['event_key'].astype(str) + '_' + 
        df_tranche['country'].astype(str)
    )
    
    # Filtrer les événements déjà utilisés en Session 15
    df_tranche = df_tranche[~df_tranche['unique_id'].isin(excluded_event_ids)]
    
    # Échantillonner selon les pays (approximatif)
    sampled = []
    remaining_quota = quota
    
    # Prioriser les pays principaux
    for country, weight in country_weights.items():
        target = int(quota * weight)
        country_events = df_tranche[df_tranche['country'] == country]
        
        if len(country_events) >= target:
            selected = country_events.sample(n=min(target, remaining_quota), random_state=42)
            sampled.append(selected)
            remaining_quota -= len(selected)
    
    # Compléter avec les autres événements si besoin
    if remaining_quota > 0:
        used_ids = set()
        for df in sampled:
            used_ids.update(df['unique_id'].tolist())
        
        remaining_events = df_tranche[~df_tranche['unique_id'].isin(used_ids)]
        if len(remaining_events) > 0:
            additional = remaining_events.sample(n=min(remaining_quota, len(remaining_events)), random_state=42)
            sampled.append(additional)
    
    # Combiner
    if sampled:
        df_final = pd.concat(sampled, ignore_index=True)
        all_extracted.append(df_final)
        print(f"   ✅ {len(df_final)} événements extraits")
        
        # Statistiques de la tranche
        print(f"      Pays : {df_final['country'].value_counts().to_dict()}")
        print(f"      Années : {df_final['year'].value_counts().to_dict()}")
    else:
        print(f"   ⚠️ Aucun événement disponible")
    
    print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Combiner et sauvegarder
# ════════════════════════════════════════════════════════════════

if all_extracted:
    final_df = pd.concat(all_extracted, ignore_index=True)
    
    # Vérifier qu'on n'a pas de doublons avec Session 15
    conflicts = final_df['unique_id'].isin(excluded_event_ids).sum()
    if conflicts > 0:
        print(f"⚠️ {conflicts} doublons détectés avec Session 15, suppression...")
        final_df = final_df[~final_df['unique_id'].isin(excluded_event_ids)]
    
    # Sauvegarder
    output_file = Path(__file__).parent / "extracted_events_session17.csv"
    final_df.to_csv(output_file, index=False)
    
    print("=" * 80)
    print("✅ EXTRACTION TERMINÉE")
    print("=" * 80)
    print()
    print(f"📁 Fichier : {output_file.name}")
    print(f"📊 Total événements : {len(final_df)}")
    print()
    
    # Statistiques finales
    print("📈 STATISTIQUES FINALES :")
    print()
    
    print("Par tranche de surprise :")
    final_df['surprise_range'] = pd.cut(
        final_df['surprise_pct'],
        bins=[0, 5, 10, 20, 50],
        labels=['0-5%', '5-10%', '10-20%', '20-50%']
    )
    print(final_df['surprise_range'].value_counts().sort_index())
    print()
    
    print("Par pays :")
    print(final_df['country'].value_counts())
    print()
    
    print("Par année :")
    print(final_df['year'].value_counts().sort_index())
    print()
    
    print("Par type d'événement (top 10) :")
    print(final_df['event_type'].value_counts().head(10))
    print()
    
    # Statistiques globales
    print("📊 STATISTIQUES GLOBALES :")
    print(f"   Surprise moyenne : {final_df['surprise_pct'].mean():.2f}%")
    print(f"   Surprise médiane : {final_df['surprise_pct'].median():.2f}%")
    print(f"   Score empirique moyen : {final_df['empirical_score'].mean():.2f}")
    print(f"   Score empirique médian : {final_df['empirical_score'].median():.2f}")
    print()
    
    print("=" * 80)
    print("🎯 PROCHAINE ÉTAPE : Mesurer impacts avec formule V2")
    print("=" * 80)
    
else:
    print("❌ ERREUR : Aucun événement extrait")

conn.close()
