"""
Script de recherche de dates candidates pour validation Double Wave (CORRIGÉ)
Session 66
Date: 24 octobre 2025

CORRECTION: Utiliser event_title au lieu de label (label est toujours NULL)
"""

import duckdb
import sys
from pathlib import Path
from datetime import datetime

# Chemin base de données
DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"

def find_cpi_candidates(min_surprise=10.0, min_cluster=3):
    """
    Trouve les dates CPI US avec forte surprise et cluster significatif.
    CORRECTION: Utilise event_title au lieu de label
    """
    
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    WITH event_clusters AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) as max_surprise_pct,
            STRING_AGG(DISTINCT event_title, ' | ') as event_titles,
            MAX(CASE WHEN importance_n = 3 THEN 1 ELSE 0 END) as has_high_importance,
            MIN(ts_utc) as first_event_time
        FROM events
        WHERE country = 'US'
          AND (event_title LIKE '%CPI%' OR event_title LIKE '%Consumer Price%' OR event_title LIKE '%Inflation%')
          AND DATE(ts_utc) BETWEEN '2022-01-01' AND '2025-12-31'
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
          AND estimate != 0
        GROUP BY DATE(ts_utc), ts_utc
        HAVING COUNT(*) >= {min_cluster}
           AND MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) >= {min_surprise}
    )
    SELECT 
        event_date,
        first_event_time,
        num_events,
        ROUND(max_surprise_pct, 2) as max_surprise_pct,
        has_high_importance,
        event_titles
    FROM event_clusters
    ORDER BY max_surprise_pct DESC
    LIMIT 25
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return result


def find_employment_candidates(min_surprise=10.0, min_cluster=3):
    """
    Trouve les dates NFP/Employment avec forte surprise.
    CORRECTION: Utilise event_title au lieu de label
    """
    
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    WITH event_clusters AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) as max_surprise_pct,
            STRING_AGG(DISTINCT event_title, ' | ') as event_titles,
            MAX(CASE WHEN importance_n = 3 THEN 1 ELSE 0 END) as has_high_importance,
            MIN(ts_utc) as first_event_time
        FROM events
        WHERE country = 'US'
          AND (event_title LIKE '%Payroll%' 
               OR event_title LIKE '%Employment%' 
               OR event_title LIKE '%NFP%'
               OR event_title LIKE '%Jobs%'
               OR event_title LIKE '%Jobless%'
               OR event_title LIKE '%Unemployment%')
          AND DATE(ts_utc) BETWEEN '2022-01-01' AND '2025-12-31'
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
          AND estimate != 0
        GROUP BY DATE(ts_utc), ts_utc
        HAVING COUNT(*) >= {min_cluster}
           AND MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) >= {min_surprise}
    )
    SELECT 
        event_date,
        first_event_time,
        num_events,
        ROUND(max_surprise_pct, 2) as max_surprise_pct,
        has_high_importance,
        event_titles
    FROM event_clusters
    ORDER BY max_surprise_pct DESC
    LIMIT 25
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return result


def find_all_high_impact_clusters(min_surprise=15.0, min_cluster=5):
    """
    Trouve TOUTES les dates avec clusters importants, indépendamment du type.
    Stratégie: Chercher simplement par cluster size et surprise.
    """
    
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    WITH event_clusters AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) as max_surprise_pct,
            STRING_AGG(DISTINCT event_title, ' | ') as event_titles,
            MAX(CASE WHEN importance_n = 3 THEN 1 WHEN importance_n = 1 THEN 1 ELSE 0 END) as has_importance,
            MIN(ts_utc) as first_event_time
        FROM events
        WHERE country = 'US'
          AND DATE(ts_utc) BETWEEN '2022-01-01' AND '2025-12-31'
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
          AND estimate != 0
        GROUP BY DATE(ts_utc), ts_utc
        HAVING COUNT(*) >= {min_cluster}
           AND MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) >= {min_surprise}
    )
    SELECT 
        event_date,
        first_event_time,
        num_events,
        ROUND(max_surprise_pct, 2) as max_surprise_pct,
        has_importance,
        event_titles
    FROM event_clusters
    ORDER BY max_surprise_pct DESC
    LIMIT 30
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return result


def main():
    """
    Exécution principale : recherche tous types d'événements.
    """
    
    print("="*80)
    print("RECHERCHE DATES CANDIDATES DOUBLE WAVE (VERSION CORRIGÉE)")
    print("Session 66 - Validation étendue")
    print("CORRECTION: Utilisation event_title au lieu de label")
    print("="*80)
    print()
    
    # 1. CPI candidates
    print("1. Recherche CPI/Inflation US (2022-2025)...")
    print("   Critères: Surprise ≥ 10%, Cluster ≥ 3")
    cpi_df = find_cpi_candidates(min_surprise=10.0, min_cluster=3)
    print(f"   ✅ {len(cpi_df)} dates CPI trouvées\n")
    
    if len(cpi_df) > 0:
        print("   Top 10 CPI:")
        print(cpi_df.head(10).to_string(index=False))
        print()
    
    # 2. Employment/NFP candidates
    print("2. Recherche Employment/NFP US (2022-2025)...")
    print("   Critères: Surprise ≥ 10%, Cluster ≥ 3")
    employment_df = find_employment_candidates(min_surprise=10.0, min_cluster=3)
    print(f"   ✅ {len(employment_df)} dates Employment trouvées\n")
    
    if len(employment_df) > 0:
        print("   Top 10 Employment:")
        print(employment_df.head(10).to_string(index=False))
        print()
    
    # 3. Tous clusters importants (stratégie large)
    print("3. Recherche TOUS clusters importants (2022-2025)...")
    print("   Critères: Surprise ≥ 15%, Cluster ≥ 5 (tous types)")
    all_clusters_df = find_all_high_impact_clusters(min_surprise=15.0, min_cluster=5)
    print(f"   ✅ {len(all_clusters_df)} dates trouvées\n")
    
    if len(all_clusters_df) > 0:
        print("   Top 15 clusters:")
        print(all_clusters_df.head(15).to_string(index=False))
        print()
    
    # 4. Consolidation et export
    print("4. Consolidation des résultats...")
    
    # Ajouter colonne type
    if len(cpi_df) > 0:
        cpi_df['event_type'] = 'CPI'
    if len(employment_df) > 0:
        employment_df['event_type'] = 'Employment'
    if len(all_clusters_df) > 0:
        all_clusters_df['event_type'] = 'Mixed'
    
    # Combiner tous les résultats
    import pandas as pd
    all_candidates = pd.concat([cpi_df, employment_df, all_clusters_df], ignore_index=True)
    
    # Enlever doublons
    all_candidates = all_candidates.drop_duplicates(subset=['event_date', 'first_event_time'])
    
    # Trier par surprise décroissante
    all_candidates = all_candidates.sort_values('max_surprise_pct', ascending=False)
    
    # Ajouter colonne double_wave_criteria
    all_candidates['meets_double_wave'] = (
        (all_candidates['max_surprise_pct'] >= 20.0) & 
        (all_candidates['num_events'] >= 5) &
        (all_candidates['has_importance'] >= 1)
    )
    
    # Export CSV
    output_path = Path(__file__).parent.parent / "data" / "double_wave_candidates_session66.csv"
    all_candidates.to_csv(output_path, index=False)
    print(f"   ✅ Export CSV: {output_path}")
    print()
    
    # Statistiques finales
    print("="*80)
    print("STATISTIQUES")
    print("="*80)
    print(f"Total dates trouvées: {len(all_candidates)}")
    print(f"  - CPI: {len(cpi_df)}")
    print(f"  - Employment: {len(employment_df)}")
    print(f"  - Mixed: {len(all_clusters_df)}")
    print()
    print(f"Dates remplissant critères Double Wave stricts:")
    print(f"  (Surprise ≥20%, Cluster ≥5, Importance présente)")
    strict_matches = all_candidates[all_candidates['meets_double_wave'] == True]
    print(f"  ✅ {len(strict_matches)} dates")
    print()
    
    if len(strict_matches) > 0:
        print("Dates validées pour tests Double Wave:")
        print(strict_matches[['event_date', 'num_events', 'max_surprise_pct', 'event_type']].head(15).to_string(index=False))
    else:
        print("⚠️ Aucune date ne remplit les critères stricts.")
        print("   Recommandation: Utiliser critères élargis")
        relaxed_matches = all_candidates[
            (all_candidates['max_surprise_pct'] >= 15.0) & 
            (all_candidates['num_events'] >= 3)
        ]
        print(f"   Dates avec critères élargis (≥15%, ≥3): {len(relaxed_matches)}")
        print()
        print("   Top 15 dates recommandées:")
        if len(relaxed_matches) > 0:
            print(relaxed_matches.head(15)[['event_date', 'num_events', 'max_surprise_pct', 'event_type']].to_string(index=False))
    
    print()
    print("="*80)
    print("PROCHAINES ÉTAPES")
    print("="*80)
    print("1. Ouvrir: data/double_wave_candidates_session66.csv")
    print("2. Sélectionner 10-15 dates à tester")
    print("3. Pour chaque date:")
    print("   - Exécuter Planificateur V2")
    print("   - Récupérer données réelles (prices_1m)")
    print("   - Calculer métriques (MAE impact, MAE timing)")
    print("4. Documenter résultats dans SESSION66_VALIDATION_DOUBLE_WAVE.md")
    print("="*80)


if __name__ == "__main__":
    main()
