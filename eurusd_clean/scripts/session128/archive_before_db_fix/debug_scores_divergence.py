"""
DEBUG DIFFÉRENCES SCORES - LEFT JOIN vs MAPPING S127
====================================================

Comprendre pourquoi scores différents.

Investigation :
1. Format event_key dans event_families (DB)
2. Format event_key dans CSV scores
3. Processus matching mapping S127
4. Identifier source divergence

Auteur : André Valentin avec Claude  
Date : 12 novembre 2025 - Session 128 Phase 2 Debug
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(1, str(Path(__file__).parent.parent / 'session127'))

from src.config import DB_PATH
from utils_mapping_variants import strip_variant_suffix


def investigate_sources():
    """
    Investiguer sources scores : event_families vs CSV
    """
    print("\n" + "="*80)
    print("INVESTIGATION SOURCES SCORES")
    print("="*80)
    print()
    
    # Source 1 : event_families (DB)
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query_ef = """
    SELECT event_key, country, empirical_score
    FROM event_families
    WHERE country = 'US'
      AND (event_key LIKE '%inflation rate%' OR event_key LIKE '%jobless%')
    ORDER BY event_key
    LIMIT 20
    """
    
    df_ef = conn.execute(query_ef).df()
    conn.close()
    
    print("SOURCE 1 : event_families (DB)")
    print("-"*80)
    print(df_ef.to_string(index=False))
    print()
    
    # Source 2 : CSV scores
    scores_path = project_root / "scripts" / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
    df_csv = pd.read_csv(scores_path)
    
    df_csv_filtered = df_csv[
        (df_csv['country'] == 'US') & 
        (df_csv['event_key'].str.contains('inflation|jobless', case=False, na=False))
    ].head(20)
    
    print("SOURCE 2 : CSV scores")
    print("-"*80)
    print(df_csv_filtered[['event_key', 'country', 'empirical_score']].to_string(index=False))
    print()
    
    # Comparer formats
    print("="*80)
    print("ANALYSE FORMATS")
    print("="*80)
    print()
    
    ef_sample = df_ef['event_key'].iloc[0] if len(df_ef) > 0 else None
    csv_sample = df_csv_filtered['event_key'].iloc[0] if len(df_csv_filtered) > 0 else None
    
    print(f"Exemple event_families : '{ef_sample}'")
    print(f"Exemple CSV            : '{csv_sample}'")
    print()
    
    if ef_sample and csv_sample:
        ef_has_spaces = ' ' in str(ef_sample)
        csv_has_spaces = ' ' in str(csv_sample)
        
        print(f"event_families format  : {'espaces' if ef_has_spaces else 'underscores'}")
        print(f"CSV format             : {'espaces' if csv_has_spaces else 'underscores'}")
        print()
        
        if ef_has_spaces != csv_has_spaces:
            print("⚠️ PROBLÈME : Formats différents !")
        else:
            print("✅ Formats identiques")


def trace_mapping_process():
    """
    Tracer processus mapping pour un événement
    """
    print("\n" + "="*80)
    print("TRAÇAGE PROCESSUS MAPPING")
    print("="*80)
    print()
    
    # Charger sources
    scores_path = project_root / "scripts" / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
    mapping_path = Path(__file__).parent.parent / "session127" / "event_mapping_rules_complete.csv"
    
    df_scores = pd.read_csv(scores_path)
    df_mapping = pd.read_csv(mapping_path)
    
    # Test cas : inflation rate_mom
    test_key = 'inflation rate_mom'
    test_country = 'US'
    
    print(f"TEST CAS : event_key='{test_key}', country='{test_country}'")
    print()
    
    # Étape 1 : strip_variant_suffix
    base_key = strip_variant_suffix(test_key)
    print(f"ÉTAPE 1 - strip_variant_suffix() :")
    print(f"   Input  : '{test_key}'")
    print(f"   Output : '{base_key}'")
    print()
    
    # Étape 2 : Recherche directe
    direct_match = df_scores[
        (df_scores['event_key'] == test_key) &
        (df_scores['country'] == test_country)
    ]
    
    print(f"ÉTAPE 2 - Recherche directe (event_key exact) :")
    if len(direct_match) > 0:
        score = direct_match['empirical_score'].iloc[0]
        print(f"   ✅ TROUVÉ : score = {score:.2f}")
    else:
        print(f"   ❌ NON TROUVÉ")
    print()
    
    # Étape 3 : Recherche base (après strip)
    base_match = df_scores[
        (df_scores['event_key'] == base_key) &
        (df_scores['country'] == test_country)
    ]
    
    print(f"ÉTAPE 3 - Recherche base (après strip) :")
    if len(base_match) > 0:
        score = base_match['empirical_score'].iloc[0]
        print(f"   ✅ TROUVÉ : score = {score:.2f}")
    else:
        print(f"   ❌ NON TROUVÉ")
    print()
    
    # Étape 4 : Mapping variantes
    mapping_match = df_mapping[
        df_mapping['event_name'] == base_key
    ]
    
    print(f"ÉTAPE 4 - Mapping variantes :")
    if len(mapping_match) > 0:
        principal = mapping_match['event_key_principal'].iloc[0]
        print(f"   ✅ TROUVÉ mapping : '{base_key}' → '{principal}'")
        
        # Rechercher score principal
        principal_score = df_scores[
            (df_scores['event_key'] == principal) &
            (df_scores['country'] == test_country)
        ]
        
        if len(principal_score) > 0:
            score = principal_score['empirical_score'].iloc[0]
            print(f"   ✅ Score principal : {score:.2f}")
        else:
            print(f"   ❌ Score principal NON TROUVÉ")
    else:
        print(f"   ❌ Pas de mapping trouvé")
    print()
    
    # Comparer avec LEFT JOIN
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = """
    SELECT ef.empirical_score
    FROM event_families ef
    WHERE ef.event_key = ?
      AND ef.country = ?
    """
    
    result = conn.execute(query, [test_key, test_country]).fetchone()
    conn.close()
    
    print(f"COMPARAISON LEFT JOIN :")
    if result:
        leftjoin_score = result[0]
        print(f"   ✅ Score LEFT JOIN : {leftjoin_score:.2f}")
    else:
        print(f"   ❌ Pas de score LEFT JOIN")


def main():
    """
    Debug principal
    """
    print("="*80)
    print("DEBUG DIFFÉRENCES SCORES - LEFT JOIN vs MAPPING")
    print("="*80)
    
    investigate_sources()
    trace_mapping_process()
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print()
    print("À analyser :")
    print("1. event_families (DB) utilise quel format exactement ?")
    print("2. CSV scores utilise quel format ?")
    print("3. Pourquoi mapping trouve scores différents ?")
    print()


if __name__ == "__main__":
    main()
