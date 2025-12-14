#!/usr/bin/env python3
"""
VALIDATION RAPIDE PHASE 1 - SESSION 130
========================================

Teste infrastructure PHASE 1 sur dates connues avant scan complet.

Tests :
1. Connexion DB
2. Scanner sur 11 sept, 1er août, 5 sept
3. Classification patterns
4. Sélection cas référence

Si tests OK → lancer run_phase1.py pour scan complet

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import pytz

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scan_movements_2023_2025 import MovementScanner, DB_PATH, TZ_BERN

def test_db_connection():
    """Test 1 : Connexion DB"""
    print("\n" + "=" * 80)
    print("TEST 1 : CONNEXION DATABASE")
    print("=" * 80)
    
    try:
        scanner = MovementScanner(DB_PATH)
        scanner.connect()
        
        # Test query simple
        result = scanner.conn.execute("SELECT COUNT(*) FROM prices_bern").fetchone()
        n_prices = result[0]
        
        print(f"✅ Connexion réussie")
        print(f"   DB : {DB_PATH}")
        print(f"   Prix disponibles : {n_prices:,} lignes")
        
        # Test events
        result = scanner.conn.execute("SELECT COUNT(*) FROM events WHERE importance_n >= 2").fetchone()
        n_events = result[0]
        print(f"   Events MEDIUM+HIGH : {n_events:,}")
        
        scanner.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Échec connexion : {e}")
        return False


def test_scanner_known_dates():
    """Test 2 : Scanner sur dates connues"""
    print("\n" + "=" * 80)
    print("TEST 2 : SCANNER DATES CONNUES")
    print("=" * 80)
    
    scanner = MovementScanner(DB_PATH)
    scanner.connect()
    
    # Dates de référence
    test_cases = [
        {
            "date": "2025-09-11",
            "expected_pattern": "DoubleWave",
            "expected_impact_min": 50.0,
            "expected_impact_max": 65.0,
            "description": "11 septembre (référence Session 115)"
        },
        {
            "date": "2025-08-01",
            "expected_pattern": "SingleWave",
            "expected_impact_min": 150.0,
            "expected_impact_max": 200.0,
            "description": "1er août NFP (Single Wave Fort)"
        },
        {
            "date": "2025-09-05",
            "expected_pattern": "ZigZag",
            "expected_impact_min": 60.0,
            "expected_impact_max": 85.0,
            "description": "5 septembre NFP (ZigZag)"
        }
    ]
    
    results = []
    success_count = 0
    
    for test_case in test_cases:
        date_str = test_case["date"]
        print(f"\n📅 Test : {date_str} - {test_case['description']}")
        
        # Parse date
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
        
        # Scan
        movement = scanner.scan_date(date)
        
        if movement:
            pattern = movement["pattern"]
            impact = movement["impact_pips"]
            n_events = movement["n_events"]
            
            print(f"   ✅ Mouvement détecté")
            print(f"      Pattern : {pattern}")
            print(f"      Impact : {impact:.1f} pips")
            print(f"      Events : {n_events}")
            print(f"      Peak time : {movement['peak_time']}")
            
            # Validation pattern
            pattern_ok = test_case["expected_pattern"] in pattern
            print(f"      Pattern match : {'✅' if pattern_ok else '⚠️'} "
                  f"(attendu: {test_case['expected_pattern']})")
            
            # Validation impact
            impact_ok = (test_case["expected_impact_min"] <= impact <= 
                        test_case["expected_impact_max"])
            print(f"      Impact range : {'✅' if impact_ok else '⚠️'} "
                  f"(attendu: {test_case['expected_impact_min']}-{test_case['expected_impact_max']})")
            
            # Validation events
            events_ok = n_events > 0
            print(f"      Events présents : {'✅' if events_ok else '⚠️'}")
            
            if pattern_ok and impact_ok and events_ok:
                success_count += 1
                print(f"      🎉 TEST RÉUSSI")
            else:
                print(f"      ⚠️  TEST PARTIEL (détecté mais différences)")
            
            results.append(movement)
            
        else:
            print(f"   ❌ AUCUN MOUVEMENT DÉTECTÉ")
            print(f"      Vérifier :")
            print(f"      - Données prix disponibles ?")
            print(f"      - Seuil 35 pips correct ?")
            print(f"      - Baseline/lookahead corrects ?")
    
    scanner.disconnect()
    
    print(f"\n{'='*80}")
    print(f"RÉSULTATS TEST SCANNER")
    print(f"{'='*80}")
    print(f"Tests réussis : {success_count}/{len(test_cases)}")
    
    return success_count == len(test_cases), results


def test_classification(movements):
    """Test 3 : Classification patterns"""
    print("\n" + "=" * 80)
    print("TEST 3 : CLASSIFICATION PATTERNS")
    print("=" * 80)
    
    if not movements:
        print("❌ Aucun mouvement à classifier")
        return False
    
    print(f"Mouvements à classifier : {len(movements)}")
    
    pattern_counts = {}
    for m in movements:
        pattern = m["pattern"]
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    print(f"\nDistribution patterns :")
    for pattern, count in pattern_counts.items():
        print(f"   {pattern:<30s} : {count}")
    
    # Vérifier patterns attendus
    expected_patterns = ["DoubleWave", "SingleWave", "ZigZag"]
    found_patterns = [p for p in expected_patterns 
                     if any(p in pattern for pattern in pattern_counts.keys())]
    
    print(f"\nPatterns attendus trouvés : {len(found_patterns)}/{len(expected_patterns)}")
    for pattern in expected_patterns:
        found = any(pattern in p for p in pattern_counts.keys())
        status = "✅" if found else "❌"
        print(f"   {status} {pattern}")
    
    return len(found_patterns) >= 2  # Au moins 2/3 patterns


def test_reference_selection(movements):
    """Test 4 : Sélection cas référence"""
    print("\n" + "=" * 80)
    print("TEST 4 : SÉLECTION CAS RÉFÉRENCE")
    print("=" * 80)
    
    if not movements:
        print("❌ Aucun mouvement pour sélection")
        return False
    
    # Grouper par pattern
    patterns = {}
    for m in movements:
        pattern = m["pattern"]
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(m)
    
    print(f"Patterns disponibles : {len(patterns)}")
    
    # Simuler sélection référence
    references = {}
    for pattern, cases in patterns.items():
        # Filtrer cas avec events
        with_events = [c for c in cases if c["n_events"] > 0]
        
        if with_events:
            # Prendre meilleur cas (plus d'events)
            best = max(with_events, key=lambda c: c["n_events"])
            references[pattern] = best
            
            print(f"\n✅ {pattern}")
            print(f"   Cas disponibles : {len(cases)}")
            print(f"   Avec events : {len(with_events)}")
            print(f"   Référence : {best['date']}")
            print(f"   Impact : {best['impact_pips']:.1f} pips")
            print(f"   Events : {best['n_events']}")
        else:
            print(f"\n⚠️  {pattern}")
            print(f"   Cas disponibles : {len(cases)}")
            print(f"   Aucun avec events")
    
    # Vérifier 11 septembre sélectionné
    print(f"\n{'='*80}")
    print(f"VALIDATION 11 SEPTEMBRE")
    print(f"{'='*80}")
    
    sept_11_selected = False
    for pattern, ref in references.items():
        if ref["date"] == "2025-09-11":
            sept_11_selected = True
            print(f"✅ 11 septembre sélectionné comme référence {pattern}")
            break
    
    if not sept_11_selected:
        print(f"⚠️  11 septembre NON sélectionné comme référence")
        print(f"   Raison possible : autre cas avec plus d'events dans pattern")
    
    print(f"\nCas référence sélectionnés : {len(references)}")
    
    return len(references) >= 2  # Au moins 2 patterns avec référence


def main():
    """Lance tous les tests"""
    
    print("=" * 80)
    print("VALIDATION RAPIDE PHASE 1 - SESSION 130")
    print("=" * 80)
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 Objectif : Valider infrastructure avant scan complet 2023-2025")
    print()
    
    # Test 1 : DB
    test1_ok = test_db_connection()
    if not test1_ok:
        print("\n❌ VALIDATION ÉCHOUÉE - Problème connexion DB")
        return 1
    
    # Test 2 : Scanner
    test2_ok, movements = test_scanner_known_dates()
    if not test2_ok:
        print("\n⚠️  VALIDATION PARTIELLE - Certaines dates non détectées")
        print("   Continuer quand même ? (scanner peut fonctionner sur autres dates)")
    
    if not movements:
        print("\n❌ VALIDATION ÉCHOUÉE - Aucun mouvement détecté")
        return 1
    
    # Test 3 : Classification
    test3_ok = test_classification(movements)
    if not test3_ok:
        print("\n⚠️  VALIDATION PARTIELLE - Classification limitée")
    
    # Test 4 : Référence
    test4_ok = test_reference_selection(movements)
    if not test4_ok:
        print("\n⚠️  VALIDATION PARTIELLE - Peu de cas référence")
    
    # Résumé final
    print("\n" + "=" * 80)
    print("RÉSUMÉ VALIDATION")
    print("=" * 80)
    
    tests = [
        ("Connexion DB", test1_ok),
        ("Scanner dates", test2_ok),
        ("Classification", test3_ok),
        ("Cas référence", test4_ok)
    ]
    
    success = sum(1 for _, ok in tests if ok)
    
    for test_name, ok in tests:
        status = "✅" if ok else "⚠️"
        print(f"{status} {test_name}")
    
    print(f"\nTests réussis : {success}/{len(tests)}")
    
    if success >= 3:
        print("\n" + "=" * 80)
        print("✅✅✅ VALIDATION RÉUSSIE ✅✅✅")
        print("=" * 80)
        print()
        print("🚀 PRÊT À LANCER SCAN COMPLET")
        print()
        print("Commande :")
        print("   python scripts/session130/run_phase1.py")
        print()
        print("Durée estimée : ~45 minutes")
        print("Output : movements_2023_2025_complete.json (~100-150 mouvements)")
        print()
        return 0
    else:
        print("\n" + "=" * 80)
        print("⚠️  VALIDATION PARTIELLE")
        print("=" * 80)
        print()
        print("Certains tests échoués mais scanner peut fonctionner.")
        print("Vérifier logs ci-dessus et décider si continuer.")
        print()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
