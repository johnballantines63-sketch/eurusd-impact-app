#!/usr/bin/env python3
"""
SESSION 127 - VALIDATION MAPPING VARIANTES
==========================================
Tests validation complets sur 5 familles HIGH/MED

Auteur : André Valentin
Date : 11 novembre 2025
"""
import sys
from pathlib import Path

# Ajouter répertoires au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1] / 'session126'))

import pandas as pd
from utils_mapping_variants import (
    get_empirical_score_with_variants,
    validate_variant_mapping,
    load_variant_mapping
)


def test_case(event_key: str, country: str, df_scores: pd.DataFrame, df_mapping: pd.DataFrame):
    """Test un cas et affiche résultats détaillés"""
    print(f"\n{'=' * 80}")
    print(f"TEST : {event_key} ({country})")
    print('=' * 80)
    
    result = validate_variant_mapping(event_key, country, df_scores, df_mapping)
    
    print(f"\nINPUT:")
    print(f"  event_key DB        : '{result['event_key']}'")
    print(f"  country DB          : '{result['country_code']}'")
    
    print(f"\nNORMALISATION:")
    print(f"  event_name CSV      : '{result['event_name']}'")
    print(f"  currency CSV        : '{result['currency_code']}'")
    
    if result['event_key_principal']:
        print(f"\nMAPPING VARIANTE:")
        print(f"  event_key_principal : '{result['event_key_principal']}'")
        
        if result['variant_info']:
            info = result['variant_info']
            print(f"  importance          : {info['importance']}")
            print(f"  num_variants        : {info['num_variants']}")
            print(f"  justification       : {info['justification']}")
    
    print(f"\nRÉSULTAT:")
    if result['score']:
        print(f"  ✅ SCORE TROUVÉ     : {result['score']:.2f}")
        print(f"  source              : {result['source']}")
    else:
        print(f"  ❌ SCORE INTROUVABLE")
        print(f"  source              : {result['source']}")
    
    return result


def main():
    print("=" * 80)
    print("SESSION 127 - VALIDATION MAPPING VARIANTES")
    print("=" * 80)
    print()
    
    # Charger données
    scores_path = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
    
    if not scores_path.exists():
        print(f"❌ Fichier scores introuvable : {scores_path}")
        return
    
    df_scores = pd.read_csv(scores_path)
    print(f"✅ Scores chargés : {len(df_scores)} lignes")
    
    try:
        df_mapping = load_variant_mapping()
        print(f"✅ Mapping chargé : {len(df_mapping)} mappings")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    
    print()
    
    # ========================================================================
    # TESTS CRITIQUES : 5 Familles
    # ========================================================================
    
    test_cases_critical = [
        # HIGH importance
        ('inflation rate', 'US', 'Variante MoM'),
        ('core inflation rate', 'US', 'Variante MoM'),
        ('gdp growth rate', 'US', 'Variante QoQ'),
        ('gross domestic product', 'US', 'Doublon GDP'),
        ('nonfarm productivity', 'US', 'Variante QoQ'),
        
        # MED importance (fréquents trading)
        ('retail sales', 'US', 'Variante MoM'),
        ('ppi', 'US', 'Variante MoM'),
        ('pce price index', 'US', 'Variante MoM'),
        
        # Direct (pas de variante)
        ('cpi', 'US', 'Direct'),
        ('non farm payrolls', 'US', 'Direct'),
        ('unemployment rate', 'US', 'Direct'),
    ]
    
    results = []
    for event_key, country, description in test_cases_critical:
        result = test_case(event_key, country, df_scores, df_mapping)
        results.append((event_key, result['score'] is not None, result['source'], description))
    
    # ========================================================================
    # SYNTHÈSE
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("SYNTHÈSE VALIDATION")
    print("=" * 80)
    print()
    
    success_count = sum(1 for _, found, _, _ in results if found)
    total = len(results)
    
    print(f"Tests réussis : {success_count}/{total} ({success_count/total*100:.1f}%)")
    print()
    
    print("DÉTAILS PAR CAS:")
    print("-" * 80)
    for event, found, source, desc in results:
        status = "✅" if found else "❌"
        print(f"  {status} {event:<35} [{source:>10}] - {desc}")
    
    print()
    
    # Statistiques par source
    sources = {'direct': 0, 'variant': 0, 'not_found': 0}
    for _, _, source, _ in results:
        sources[source] += 1
    
    print("STATISTIQUES PAR SOURCE:")
    print("-" * 80)
    print(f"  Direct (pas de variante)     : {sources['direct']}")
    print(f"  Variant (mapping Session 127): {sources['variant']}")
    print(f"  Not found (manquant)         : {sources['not_found']}")
    
    print()
    
    # ========================================================================
    # CRITÈRE SUCCÈS
    # ========================================================================
    
    print("=" * 80)
    print("CRITÈRE SUCCÈS SESSION 127")
    print("=" * 80)
    print()
    
    if success_count == total:
        print("✅✅✅ SUCCÈS COMPLET : Tous les tests passent !")
        print()
        print("IMPACT:")
        print(f"  - {sources['variant']} scores accessibles via mapping variantes")
        print(f"  - {sources['direct']} scores accessibles directement")
        print(f"  - 0 scores manquants (100% couverture)")
        return_code = 0
    elif success_count >= total * 0.9:
        print("✅ SUCCÈS PARTIEL : 90%+ tests passent")
        print()
        print(f"AVERTISSEMENT:")
        print(f"  - {sources['not_found']} scores manquants à investiguer")
        return_code = 0
    else:
        print("❌ ÉCHEC : <90% tests passent")
        print()
        print(f"ACTION REQUISE:")
        print(f"  - Vérifier {sources['not_found']} scores manquants")
        print(f"  - Vérifier mapping variantes")
        return_code = 1
    
    print()
    print("=" * 80)
    print("FIN VALIDATION")
    print("=" * 80)
    
    sys.exit(return_code)


if __name__ == "__main__":
    main()
