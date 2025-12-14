"""
VALIDATION MAPPING SESSION 127 - AVEC NOUVEAUX EVENT_KEY
=========================================================

Vérifie que mapping Session 127 fonctionne avec event_key ESPACES.

Tests :
1. Charger événements 11 septembre (event_key avec espaces)
2. Appliquer get_empirical_score_with_variants()
3. Comparer scores : LEFT JOIN vs Mapping S127
4. Vérifier compatibilité strip_variant_suffix()

Critères succès :
- Mapping trouve 100% scores
- Scores identiques LEFT JOIN = Mapping
- Pas de régression vs validation infrastructure

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 128 REPRISE Phase 2
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(1, str(Path(__file__).parent.parent / 'session127'))

from src.config import DB_PATH
from utils_mapping_variants import get_empirical_score_with_variants


def test_mapping_with_spaces():
    """
    Test mapping Session 127 avec event_key contenant espaces
    """
    print("\n" + "="*80)
    print("TEST MAPPING SESSION 127 - EVENT_KEY AVEC ESPACES")
    print("="*80)
    print()
    
    try:
        # Charger scores CSV
        scores_path = project_root / "scripts" / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
        mapping_path = Path(__file__).parent.parent / "session127" / "event_mapping_rules_complete.csv"
        
        if not scores_path.exists():
            print(f"❌ Fichier scores introuvable : {scores_path}")
            return False
        
        if not mapping_path.exists():
            print(f"❌ Fichier mapping introuvable : {mapping_path}")
            return False
        
        df_scores = pd.read_csv(scores_path)
        df_mapping = pd.read_csv(mapping_path)
        
        print(f"✅ Scores CSV chargé : {len(df_scores)} lignes")
        print(f"✅ Mapping rules chargé : {len(df_mapping)} mappings")
        print()
        
        # Charger événements 11 septembre (avec scores LEFT JOIN)
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        query = """
        SELECT 
            e.event_key,
            e.country,
            ef.empirical_score as score_leftjoin
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.ts_utc >= '2025-09-11 14:30:00+02:00'
            AND e.ts_utc < '2025-09-11 14:31:00+02:00'
            AND e.country = 'US'
            AND e.estimate IS NOT NULL
        ORDER BY e.event_key
        """
        
        df = conn.execute(query).fetchdf()
        conn.close()
        
        print(f"📊 Événements testés : {len(df)}")
        print()
        
        # Appliquer mapping Session 127
        results = []
        
        for idx, row in df.iterrows():
            event_key = row['event_key']
            country = row['country']
            score_leftjoin = row['score_leftjoin']
            
            # Appliquer mapping S127
            score_mapping, source = get_empirical_score_with_variants(
                event_key,
                country,
                df_scores,
                df_mapping
            )
            
            results.append({
                'event_key': event_key,
                'score_leftjoin': score_leftjoin,
                'score_mapping': score_mapping,
                'source': source,
                'match': abs(score_leftjoin - score_mapping) < 0.01 if score_leftjoin and score_mapping else False
            })
        
        df_results = pd.DataFrame(results)
        
        # Afficher résultats
        print("="*80)
        print("COMPARAISON SCORES : LEFT JOIN vs MAPPING S127")
        print("="*80)
        print()
        
        for idx, row in df_results.iterrows():
            match_str = "✅" if row['match'] else "❌"
            left_str = f"{row['score_leftjoin']:.2f}" if row['score_leftjoin'] else "NULL"
            map_str = f"{row['score_mapping']:.2f}" if row['score_mapping'] else "NULL"
            
            print(f"{match_str} {row['event_key']:<40}")
            print(f"   LEFT JOIN : {left_str:>8}")
            print(f"   MAPPING   : {map_str:>8} (source: {row['source']})")
            print()
        
        # Validation
        matches = df_results['match'].sum()
        total = len(df_results)
        
        print("="*80)
        print("RÉSUMÉ VALIDATION")
        print("="*80)
        print()
        print(f"📊 Scores identiques : {matches}/{total} ({matches/total*100:.0f}%)")
        print()
        
        if matches == total:
            print("✅ VALIDATION :")
            print("   ✅ 100% scores identiques → Mapping S127 compatible !")
            print("   ✅ Peut utiliser mapping dans Planificateur")
            return True
        elif matches / total > 0.9:
            print("⚠️ VALIDATION :")
            print(f"   ⚠️ {matches/total*100:.0f}% scores identiques")
            print("   ⚠️ Quelques différences mineures")
            return True
        else:
            print("❌ VALIDATION :")
            print(f"   ❌ Seulement {matches/total*100:.0f}% scores identiques")
            print("   ❌ Mapping S127 a des problèmes")
            return False
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strip_variant_suffix():
    """
    Test strip_variant_suffix() avec event_key ESPACES
    """
    print("\n" + "="*80)
    print("TEST strip_variant_suffix() - ESPACES")
    print("="*80)
    print()
    
    from utils_mapping_variants import strip_variant_suffix
    
    test_cases = [
        ('inflation rate_mom', 'inflation rate'),
        ('core inflation rate_yoy', 'core inflation rate'),
        ('gdp growth rate_qoq', 'gdp growth rate'),
        ('cpi', 'cpi'),
        ('continuing jobless claims', 'continuing jobless claims'),
    ]
    
    print("Test cases :")
    print()
    
    passed = 0
    for input_key, expected in test_cases:
        result = strip_variant_suffix(input_key)
        match = result == expected
        
        status = "✅" if match else "❌"
        print(f"{status} strip_variant_suffix('{input_key}')")
        print(f"   Attendu : '{expected}'")
        print(f"   Résultat : '{result}'")
        print()
        
        if match:
            passed += 1
    
    print(f"📊 Résultats : {passed}/{len(test_cases)} tests réussis")
    print()
    
    if passed == len(test_cases):
        print("✅ VALIDATION :")
        print("   ✅ strip_variant_suffix() fonctionne avec espaces")
        return True
    else:
        print("❌ VALIDATION :")
        print("   ❌ strip_variant_suffix() a des problèmes")
        return False


def main():
    """
    Test principal - Validation mapping Session 127
    """
    print("="*80)
    print("VALIDATION MAPPING SESSION 127 - NOUVEAUX EVENT_KEY")
    print("="*80)
    print()
    print("Objectif : Vérifier compatibilité mapping avec event_key ESPACES")
    print()
    
    results = {}
    
    # Test 1 : strip_variant_suffix
    results['strip_suffix'] = test_strip_variant_suffix()
    
    # Test 2 : Mapping complet
    results['mapping'] = test_mapping_with_spaces()
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ VALIDATION PHASE 2")
    print("="*80)
    print()
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"   {test_name:20} : {status}")
    
    print()
    print(f"📊 TOTAL : {passed}/{total} tests réussis ({passed/total*100:.0f}%)")
    print()
    
    if passed == total:
        print("🎉 MAPPING SESSION 127 VALIDÉ ✅✅✅")
        print("   → Compatible avec nouveaux event_key (espaces)")
        print("   → Peut continuer Phase 3-4 (objectifs Session 128)")
        return True
    else:
        print("❌ MAPPING SESSION 127 NON VALIDÉ")
        print("   → Incompatibilités détectées")
        print("   → Corrections nécessaires avant continuer")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
