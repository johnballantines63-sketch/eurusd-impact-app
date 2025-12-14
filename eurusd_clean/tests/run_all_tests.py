#!/usr/bin/env python3
"""
Script de lancement de tous les tests
======================================

Lance tous les tests et affiche un résumé.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_test(test_file: str) -> tuple[bool, str]:
    """Lance un test et retourne (success, output)."""
    test_path = PROJECT_ROOT / "tests" / test_file
    if not test_path.exists():
        return False, f"Test file not found: {test_file}"
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Extraire seulement les lignes importantes (ignore warnings Streamlit)
        output_lines = []
        for line in result.stdout.split('\n') + result.stderr.split('\n'):
            if any(keyword in line for keyword in [
                'TEST', '✅', '❌', '📅', '📊', '📋', 'SUCCÈS', 'ÉCHEC', 
                'Échantillon', 'Format', 'Colonnes', 'Dict chargé', 'DataFrame'
            ]):
                if 'WARNING' not in line and 'Thread' not in line:
                    output_lines.append(line)
        
        output = '\n'.join(output_lines)
        success = result.returncode == 0
        
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"Timeout (>60s)"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Lance tous les tests."""
    tests = [
        "test_imports_streamlit.py",
        "test_load_day_events.py",
        "test_load_actuals_from_db.py",
    ]
    
    print("=" * 80)
    print("SUITE DE TESTS - Streamlit V3.2.1")
    print("=" * 80)
    print()
    
    results = []
    
    for test_file in tests:
        print(f"🧪 Running {test_file}...")
        success, output = run_test(test_file)
        results.append((test_file, success, output))
        
        if output:
            print(output)
            print()
    
    # Résumé
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_file, success, _ in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_file}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("✅ TOUS LES TESTS PASSENT")
        return 0
    else:
        print(f"❌ {total - passed} TEST(S) ÉCHOUÉ(S)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

