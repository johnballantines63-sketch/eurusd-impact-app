"""
VALIDATION RAPIDE - Session 89
Test logique surprise_utils sans accès DB
"""

import sys
sys.path.insert(0, '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session89')

from surprise_utils import calculate_surprise_robust, get_surprise_source

print("="*80)
print("🧪 VALIDATION LOGIQUE - surprise_utils")
print("="*80)

# Cas de test représentatifs
test_cases = [
    {
        'name': 'Cas normal - estimate disponible',
        'actual': 3.5,
        'estimate': 3.0,
        'forecast': None,
        'previous': None,
        'expected_surprise': 16.67,
        'expected_source': 'estimate'
    },
    {
        'name': 'Fallback forecast - estimate=None',
        'actual': 3.5,
        'estimate': None,
        'forecast': 3.2,
        'previous': 3.1,
        'expected_surprise': 9.38,
        'expected_source': 'forecast'
    },
    {
        'name': 'Fallback previous - estimate & forecast=None',
        'actual': 3.5,
        'estimate': None,
        'forecast': None,
        'previous': 3.1,
        'expected_surprise': 12.90,
        'expected_source': 'previous'
    },
    {
        'name': 'Aucune référence - tout None',
        'actual': 3.5,
        'estimate': None,
        'forecast': None,
        'previous': None,
        'expected_surprise': 0.0,
        'expected_source': 'none'
    },
    {
        'name': 'estimate=0 → fallback',
        'actual': 3.5,
        'estimate': 0,
        'forecast': 3.2,
        'previous': None,
        'expected_surprise': 9.38,
        'expected_source': 'forecast'
    }
]

print("\n📋 TESTS DE VALIDATION :\n")

all_passed = True

for i, test in enumerate(test_cases, 1):
    surprise = calculate_surprise_robust(
        test['actual'],
        test['estimate'],
        test['forecast'],
        test['previous']
    )
    
    source = get_surprise_source(
        test['estimate'],
        test['forecast'],
        test['previous']
    )
    
    # Vérifications
    surprise_ok = abs(surprise - test['expected_surprise']) < 0.1
    source_ok = source == test['expected_source']
    
    status = "✅" if (surprise_ok and source_ok) else "❌"
    
    print(f"{status} Test {i}: {test['name']}")
    print(f"   Surprise: {surprise:.2f}% (attendu: {test['expected_surprise']:.2f}%)")
    print(f"   Source: {source} (attendu: {test['expected_source']})")
    
    if not (surprise_ok and source_ok):
        all_passed = False
        print("   ⚠️ ÉCHEC")
    
    print()

print("="*80)

if all_passed:
    print("✅✅✅ TOUS LES TESTS PASSENT - Logique validée !")
    print("\n🚀 Prêt pour tests avec vraies données :")
    print("   python test_amplification_0108.py")
    print("   python test_multi_dates.py")
else:
    print("❌ CERTAINS TESTS ÉCHOUENT - Corriger avant de continuer")

print("="*80)
