"""
Script de recherche de dates candidates pour validation Double Wave
Session 66
Date: 24 octobre 2025

Objectif:
---------
Identifier 10-15 dates entre 2022-2025 avec conditions Double Wave potentielles:
- Surprise max ≥ 20% (ou ≥ 15% pour élargir recherche)
- Cluster ≥ 5 événements (ou ≥ 3 pour élargir)
- Au moins 1 événement HIGH importance (CPI, NFP, Fed)

Output:
-------
CSV avec dates candidates + métriques pour validation manuelle
"""

import duckdb
import sys
from pathlib import Path
from datetime import datetime

# Chemin base de données
DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"

def find_cpi_candidates(min_surprise=15.0, min_cluster=3):
    """
    Trouve les dates CPI US avec forte surprise et cluster significatif.
    """
    
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    WITH event_clusters AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) as max_surprise_pct,
            STRING_AGG(DISTINCT label, ' | ') as event_labels,
            MAX(CASE WHEN importance_n = 3 THEN 1 ELSE 0 END) as has_high_importance,
            MIN(ts_utc) as first_event_time
        FROM events
        WHERE country = 'US'
          AND (label LIKE '%CPI%' OR label LIKE '%Consumer Price%')
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
        event_labels
    FROM event_clusters
    ORDER BY max_surprise_pct DESC
    LIMIT 20
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return result


def find_nfp_candidates(min_surprise=15.0, min_cluster=3):
    """
    Trouve les dates NFP (Non-Farm Payroll) avec forte surprise.
    """
    
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    WITH event_clusters AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) as max_surprise_pct,
            STRING_AGG(DISTINCT label, ' | ') as event_labels,
            MAX(CASE WHEN importance_n = 3 THEN 1 ELSE 0 END) as has_high_importance,
            MIN(ts_utc) as first_event_time
        FROM events
        WHERE country = 'US'
          AND (label LIKE '%Non-Farm%' OR label LIKE '%NFP%' OR label LIKE '%Payroll%')
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
        event_labels
    FROM event_clusters
    ORDER BY max_surprise_pct DESC
    LIMIT 20
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return result


def find_fed_candidates(min_surprise=10.0, min_cluster=2):
    """
    Trouve les décisions Fed avec surprise (seuils plus bas car moins d'événements).
    """
    
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    WITH event_clusters AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) as max_surprise_pct,
            STRING_AGG(DISTINCT label, ' | ') as event_labels,
            MAX(CASE WHEN importance_n = 3 THEN 1 ELSE 0 END) as has_high_importance,
            MIN(ts_utc) as first_event_time
        FROM events
        WHERE country = 'US'
          AND (label LIKE '%Fed%Rate%' OR label LIKE '%FOMC%' OR label LIKE '%Interest Rate%')
          AND DATE(ts_utc) BETWEEN '2022-01-01' AND '2025-12-31'
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
          AND estimate != 0
        GROUP BY DATE(ts_utc), ts_utc
        HAVING MAX(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100) >= {min_surprise}
    )
    SELECT 
        event_date,
        first_event_time,
        num_events,
        ROUND(max_surprise_pct, 2) as max_surprise_pct,
        has_high_importance,
        event_labels
    FROM event_clusters
    ORDER BY max_surprise_pct DESC
    LIMIT 10
    """
    
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return result


def main():
    """
    Exécution principale : recherche tous types d'événements.
    """
    
    print("="*80)
    print("RECHERCHE DATES CANDIDATES DOUBLE WAVE")
    print("Session 66 - Validation étendue")
    print("="*80)
    print()
    
    # 1. CPI candidates
    print("1. Recherche CPI US (2022-2025)...")
    print("   Critères: Surprise ≥ 15%, Cluster ≥ 3")
    cpi_df = find_cpi_candidates(min_surprise=15.0, min_cluster=3)
    print(f"   ✅ {len(cpi_df)} dates CPI trouvées\n")
    
    if len(cpi_df) > 0:
        print("   Top 10 CPI:")
        print(cpi_df.head(10).to_string(index=False))
        print()
    
    # 2. NFP candidates
    print("2. Recherche NFP US (2022-2025)...")
    print("   Critères: Surprise ≥ 15%, Cluster ≥ 3")
    nfp_df = find_nfp_candidates(min_surprise=15.0, min_cluster=3)
    print(f"   ✅ {len(nfp_df)} dates NFP trouvées\n")
    
    if len(nfp_df) > 0:
        print("   Top 5 NFP:")
        print(nfp_df.head(5).to_string(index=False))
        print()
    
    # 3. Fed candidates
    print("3. Recherche Fed decisions (2022-2025)...")
    print("   Critères: Surprise ≥ 10%, Cluster ≥ 2")
    fed_df = find_fed_candidates(min_surprise=10.0, min_cluster=2)
    print(f"   ✅ {len(fed_df)} dates Fed trouvées\n")
    
    if len(fed_df) > 0:
        print("   Top 5 Fed:")
        print(fed_df.head(5).to_string(index=False))
        print()
    
    # 4. Consolidation et export
    print("4. Consolidation des résultats...")
    
    # Ajouter colonne type
    cpi_df['event_type'] = 'CPI'
    nfp_df['event_type'] = 'NFP'
    fed_df['event_type'] = 'FED'
    
    # Combiner tous les résultats
    import pandas as pd
    all_candidates = pd.concat([cpi_df, nfp_df, fed_df], ignore_index=True)
    
    # Trier par surprise décroissante
    all_candidates = all_candidates.sort_values('max_surprise_pct', ascending=False)
    
    # Ajouter colonne double_wave_criteria
    all_candidates['meets_double_wave'] = (
        (all_candidates['max_surprise_pct'] >= 20.0) & 
        (all_candidates['num_events'] >= 5) &
        (all_candidates['has_high_importance'] == 1)
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
    print(f"  - NFP: {len(nfp_df)}")
    print(f"  - FED: {len(fed_df)}")
    print()
    print(f"Dates remplissant critères Double Wave stricts:")
    print(f"  (Surprise ≥20%, Cluster ≥5, HIGH importance)")
    strict_matches = all_candidates[all_candidates['meets_double_wave'] == True]
    print(f"  ✅ {len(strict_matches)} dates")
    print()
    
    if len(strict_matches) > 0:
        print("Dates validées pour tests Double Wave:")
        print(strict_matches[['event_date', 'num_events', 'max_surprise_pct', 'event_type']].to_string(index=False))
    else:
        print("⚠️ Aucune date ne remplit les critères stricts.")
        print("   Recommandation: Tester avec critères élargis (Surprise ≥15%, Cluster ≥3)")
        relaxed_matches = all_candidates[
            (all_candidates['max_surprise_pct'] >= 15.0) & 
            (all_candidates['num_events'] >= 3)
        ]
        print(f"   Dates avec critères élargis: {len(relaxed_matches)}")
        print()
        print("   Top 10 dates recommandées:")
        print(relaxed_matches.head(10)[['event_date', 'num_events', 'max_surprise_pct', 'event_type']].to_string(index=False))
    
    print()
    print("="*80)
    print("PROCHAINES ÉTAPES")
    print("="*80)
    print("1. Ouvrir: data/double_wave_candidates_session66.csv")
    print("2. Sélectionner 10-15 dates à tester (priorité: meets_double_wave=True)")
    print("3. Pour chaque date:")
    print("   - Exécuter Planificateur V2")
    print("   - Récupérer données réelles (prices_1m)")
    print("   - Calculer métriques (MAE impact, MAE timing)")
    print("4. Documenter résultats dans tableau récapitulatif")
    print("="*80)


if __name__ == "__main__":
    main()
